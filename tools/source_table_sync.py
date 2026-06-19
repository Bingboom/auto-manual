"""Approval-gated source-table sync (Milestone F, PR F6).

Turns Class D (data-origin) backport deltas into `source_table_change_request`s,
resolves each to an exact live Feishu `record_id` via the F1 sidecar
(exact-or-abstain), and applies **only human-approved** requests to Bitable
content fields, with GET-verify-after-write and delta-hash idempotency.

Hard boundaries (design `Feishu_Cloud_Doc_Backport_Design.md` §5.1 R9):

- **Human approval is mandatory.** `plan_apply` skips any request whose
  `delta_hash` is not in the approved set. An agent may propose/execute but never
  approve.
- **Exact-or-abstain.** A request without an exact `record_id`
  (`resolution_status != "resolved"`) is skipped, never guessed.
- **Content fields only.** Table schema changes are out of scope (operator-gated).
- **Idempotent.** A `delta_hash` already applied/seen is skipped.

Live writes require `lark-cli --as bot` and a populated `record_id` sidecar; the
default is dry-run (plan only) with no network access.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from tools.source_record_index import (
    load_index,
    resolve as _resolve_record,
    resolve_by_table as _resolve_by_table,
)

CHANGE_REQUEST_SCHEMA_VERSION = "source-table-change-request/v1"


class _Transport(Protocol):
    def upsert(self, *, table: str, record_id: str, field: str, value: Any) -> None: ...
    def get(self, *, table: str, record_id: str, field: str) -> Any: ...


def _resolve_record_id(source_ref: dict[str, Any], sidecar_index: dict[str, Any] | None) -> tuple[str | None, str]:
    if not sidecar_index:
        return None, "snapshot_only"
    kind = source_ref.get("kind")
    if kind:
        record_id, status = _resolve_record(sidecar_index, kind=str(kind), source_ref=source_ref)
        if record_id:
            return record_id, status
    # F2/F6 source_refs usually carry a table + keys but no kind.
    return _resolve_by_table(sidecar_index, source_ref)


def build_change_requests(
    diff_report: dict[str, Any], *, sidecar_index: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Build change requests from the Class D (source_table_suggestion) deltas."""
    requests: list[dict[str, Any]] = []
    for delta in diff_report.get("deltas") or []:
        if not isinstance(delta, dict) or delta.get("route_class") != "source_table_suggestion":
            continue
        source_ref = delta.get("source_ref") or {}
        record_id, status = _resolve_record_id(source_ref, sidecar_index)
        requests.append(
            {
                "schema_version": CHANGE_REQUEST_SCHEMA_VERSION,
                "delta_hash": delta.get("delta_hash"),
                "table": source_ref.get("table"),
                "field": source_ref.get("field"),
                "record_id": record_id,
                "resolution_status": status,
                "old_text": delta.get("old_text"),
                "new_text": delta.get("new_text"),
                "source_ref": source_ref,
                "blast_radius": list(source_ref.get("targets") or []),
                "external_write": False,
            }
        )
    return requests


def _ref(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "delta_hash": request.get("delta_hash"),
        "table": request.get("table"),
        "record_id": request.get("record_id"),
        "field": request.get("field"),
    }


def plan_apply(change_requests: list[dict[str, Any]], *, approved_hashes: set[str]) -> list[dict[str, Any]]:
    """Decide, per request, whether it would be applied — pure, no network.

    Encodes the R9 gates: human approval, exact-or-abstain, content-field, and
    delta-hash idempotency.
    """
    plan: list[dict[str, Any]] = []
    seen: set[str] = set()
    for request in change_requests:
        delta_hash = request.get("delta_hash")
        entry = _ref(request)
        if delta_hash in seen:
            plan.append({**entry, "action": "skip", "reason": "duplicate delta_hash (idempotent)"})
            continue
        if delta_hash:
            seen.add(delta_hash)
        if not delta_hash or delta_hash not in approved_hashes:
            plan.append({**entry, "action": "skip", "reason": "not approved by a human"})
            continue
        if request.get("resolution_status") != "resolved" or not request.get("record_id"):
            plan.append(
                {**entry, "action": "skip", "reason": f"record_id {request.get('resolution_status') or 'unresolved'} (exact-or-abstain)"}
            )
            continue
        if not request.get("table") or not request.get("field"):
            plan.append({**entry, "action": "skip", "reason": "missing table/field"})
            continue
        plan.append(
            {
                **entry,
                "action": "apply",
                "value": request.get("new_text"),
            }
        )
    return plan


def apply_change_requests(
    change_requests: list[dict[str, Any]],
    *,
    approved_hashes: set[str],
    transport: _Transport | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Apply approved+resolved requests. Dry-run unless write and a transport are
    given. Each live write is GET-verified after the upsert."""
    plan = plan_apply(change_requests, approved_hashes=approved_hashes)
    applied: list[dict[str, Any]] = []
    for entry in plan:
        if entry["action"] != "apply":
            continue
        if not (write and transport is not None):
            applied.append({**entry, "status": "planned"})
            continue
        transport.upsert(table=entry["table"], record_id=entry["record_id"], field=entry["field"], value=entry["value"])
        current = transport.get(table=entry["table"], record_id=entry["record_id"], field=entry["field"])
        verified = current == entry["value"]
        applied.append({**entry, "status": "written" if verified else "verify_failed", "verified": verified})
    return {
        "schema_version": CHANGE_REQUEST_SCHEMA_VERSION,
        "external_write": bool(write and transport is not None),
        "summary": {
            "total": len(change_requests),
            "apply": sum(1 for entry in plan if entry["action"] == "apply"),
            "skip": sum(1 for entry in plan if entry["action"] == "skip"),
            "written": sum(1 for entry in applied if entry.get("status") == "written"),
        },
        "plan": plan,
        "applied": applied,
    }


def build_change_request_report(
    diff_report: dict[str, Any], *, sidecar_index: dict[str, Any] | None = None
) -> dict[str, Any]:
    requests = build_change_requests(diff_report, sidecar_index=sidecar_index)
    resolved = sum(1 for request in requests if request.get("resolution_status") == "resolved")
    return {
        "schema_version": CHANGE_REQUEST_SCHEMA_VERSION,
        "run_id": diff_report.get("run_id"),
        "external_write": False,
        "summary": {"requests": len(requests), "resolved_record_ids": resolved},
        "requests": requests,
    }


def load_sidecar_index(data_root: Path | None) -> dict[str, Any] | None:
    return load_index(data_root) if data_root else None


def write_change_request_report(report: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "cloud_doc_backport_source_table_change_request.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
