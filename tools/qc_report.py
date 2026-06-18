"""QC_Report writeback (Milestone F, PR F8).

Append/upsert `content_lint` findings to a Feishu `QC_Report` table, **idempotent
by `finding_hash`**, **dry-run by default**.

Boundaries (closed-loop QC plan M4):

- Creating the `QC_Report` table is a schema change → **operator-gated**; this
  writer only appends/upserts rows.
- It never touches per-content-row QC status fields (out of scope).
- Live writes need a `lark-cli`-backed transport; the default is dry-run (plan
  only) with no network access.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

QC_REPORT_ROW_SCHEMA_VERSION = "qc-report-row/v1"
QC_REPORT_WRITEBACK_SCHEMA_VERSION = "qc-report-writeback/v1"


class _Transport(Protocol):
    def append_row(self, *, row: dict[str, Any]) -> str: ...
    def list_finding_hashes(self) -> set[str]: ...


def build_qc_report_rows(findings: list[Any]) -> list[dict[str, Any]]:
    """Map content_lint findings to QC_Report rows (the M4 row contract)."""
    rows: list[dict[str, Any]] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        rows.append(
            {
                "schema_version": QC_REPORT_ROW_SCHEMA_VERSION,
                "run_id": finding.get("run_id"),
                "finding_hash": finding.get("finding_hash"),
                "severity": finding.get("severity"),
                "rule": finding.get("rule"),
                "source_ref": finding.get("source_ref"),
                "record_id": finding.get("record_id"),
                "resolution_status": finding.get("resolution_status"),
                "suggested_action": finding.get("suggested_action"),
            }
        )
    return rows


def _ref(row: dict[str, Any]) -> dict[str, Any]:
    return {"finding_hash": row.get("finding_hash"), "rule": row.get("rule"), "severity": row.get("severity")}


def plan_upsert(rows: list[dict[str, Any]], *, existing_hashes: "set[str] | frozenset[str]" = frozenset()) -> list[dict[str, Any]]:
    """Decide, per row, whether it would be written — idempotent by finding_hash."""
    plan: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        finding_hash = row.get("finding_hash")
        entry = _ref(row)
        if not finding_hash:
            plan.append({**entry, "action": "skip", "reason": "missing finding_hash"})
            continue
        if finding_hash in seen:
            plan.append({**entry, "action": "skip", "reason": "duplicate finding_hash (idempotent)"})
            continue
        seen.add(finding_hash)
        if finding_hash in existing_hashes:
            plan.append({**entry, "action": "skip", "reason": "already in QC_Report (idempotent)"})
            continue
        plan.append({**entry, "action": "upsert", "row": row})
    return plan


def upsert_qc_report(
    rows: list[dict[str, Any]],
    *,
    transport: _Transport | None = None,
    write: bool = False,
    existing_hashes: "set[str] | frozenset[str]" = frozenset(),
) -> dict[str, Any]:
    """Append/upsert rows. Dry-run unless write and a transport are given."""
    existing: set[str] = set(existing_hashes)
    if write and transport is not None:
        existing |= transport.list_finding_hashes()
    plan = plan_upsert(rows, existing_hashes=existing)
    applied: list[dict[str, Any]] = []
    for entry in plan:
        if entry["action"] != "upsert":
            continue
        if not (write and transport is not None):
            applied.append({"finding_hash": entry["finding_hash"], "status": "planned"})
            continue
        record_id = transport.append_row(row=entry["row"])
        applied.append({"finding_hash": entry["finding_hash"], "status": "written", "record_id": record_id})
    return {
        "schema_version": QC_REPORT_WRITEBACK_SCHEMA_VERSION,
        "external_write": bool(write and transport is not None),
        "summary": {
            "total": len(rows),
            "upsert": sum(1 for entry in plan if entry["action"] == "upsert"),
            "skip": sum(1 for entry in plan if entry["action"] == "skip"),
            "written": sum(1 for entry in applied if entry.get("status") == "written"),
        },
        "plan": plan,
        "applied": applied,
    }


def load_findings(path: Path) -> list[Any]:
    """Load content_lint findings from a findings.json report (or a bare list)."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload.get("findings") or []
    if isinstance(payload, list):
        return payload
    return []


def write_qc_report_writeback(report: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "qc_report_writeback.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
