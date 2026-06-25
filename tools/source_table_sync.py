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
import re
from pathlib import Path
from typing import Any, Protocol

from tools.source_record_index import (
    load_index,
    resolve as _resolve_record,
    resolve_by_table as _resolve_by_table,
)
from tools.token_resolution_map import split_cells

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


_WS_RE = re.compile(r"\s+")


def _norm(text: Any) -> str:
    return _WS_RE.sub(" ", str(text or "").strip())


def _atomic_values(text: Any) -> list[str]:
    """Normalized cell / ``<br/>``-joined / HTML ``<td>`` sub-values of a (possibly
    table-row) text, in order; the whole normalized text when there is no cell
    structure. Shares ``split_cells`` with the resolver so the cells aligned here are
    exactly the cells the value index matched against."""
    norm = _norm(text)
    if not norm:
        return []
    return split_cells(norm) or [norm]


def _resolve_written_value(old_normalized: Any, new_normalized: Any, matched_value: Any) -> str | None:
    """The precise NEW source value to write for a resolved Class D delta.

    For a whole-text / bare-value match (a body-copy paragraph or a bare cell), the new
    value is the whole new text. For a table-ROW delta, align the old and new cells /
    ``<br/>``-joined sub-values positionally and return the new sub-value at the position
    whose OLD sub equals the matched value **and** actually changed — so the write puts
    the new *cell* value (e.g. ``IN1 (DC 12V点烟口)``) into the cell field, not the whole
    row markup. Returns ``None`` (abstain) when the matched value is absent, the cell
    structure differs, or the changed position is ambiguous, so the write never guesses
    or corrupts the cell.
    """

    matched = _norm(matched_value)
    if not matched:
        return None
    if _norm(old_normalized) == matched:
        return _norm(new_normalized)
    old_subs = _atomic_values(old_normalized)
    new_subs = _atomic_values(new_normalized)
    if not old_subs or len(old_subs) != len(new_subs):
        return None
    changed = [new for old, new in zip(old_subs, new_subs) if old != new and old == matched]
    if len(changed) == 1:
        return changed[0]
    return None


# A Localized_Copy value's authoring home is Manual_Copy_Source.source_text — but
# ONLY for a source-language edit (the reviewed lang == the copy's Source_lang). A
# translation edit belongs in the Translation_Memory (out of F6 scope), so it
# abstains here rather than corrupting the source text.
COPY_ORIGIN_TABLE = "Localized_Copy"
COPY_AUTHORING_TABLE = "Manual_Copy_Source"
COPY_AUTHORING_FIELD = "source_text"

# A translation copy edit can't be written to source via F6 (its home is the
# Translation_Memory). It abstains with this status and is surfaced as a
# translation suggestion rather than silently skipped.
TRANSLATION_ABSTAIN_STATUS = "translation_abstain"


def _norm_lang(value: Any) -> str:
    return str(value or "").strip().lower()


def _copy_write_target(source_ref: dict[str, Any]) -> tuple[str, str] | None:
    """Return the writable ``(table, field)`` for a Localized_Copy-origin source_ref
    when it is a source-language edit, else ``None`` (translation -> abstain)."""
    lang = _norm_lang(source_ref.get("lang"))
    source_lang = _norm_lang(source_ref.get("source_lang"))
    if lang and source_lang and lang == source_lang:
        return COPY_AUTHORING_TABLE, COPY_AUTHORING_FIELD
    return None


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
        table = source_ref.get("table")
        field = source_ref.get("field")
        # Copy-origin write-target mapping (source-language only). The record_id
        # already resolves to the Manual_Copy_Source authoring row (F6 sidecar
        # redirect); rewrite table/field to that authoring source field. A
        # translation edit (or unknown source lang) is not writable via F6 and
        # abstains so plan_apply skips it instead of mis-writing text_<lang>.
        if table == COPY_ORIGIN_TABLE:
            target = _copy_write_target(source_ref)
            if target is None:
                # Translation edit -> not writable to source via F6; abstain and
                # surface as a translation suggestion (its home is the TM).
                record_id, status = None, TRANSLATION_ABSTAIN_STATUS
            elif record_id:
                # Source-language edit -> write the authoring source field.
                table, field = target
            # else: source-language edit whose record_id did not resolve -> leave
            # it as a normal unresolved request (NOT a translation suggestion).
        # Precise cell value to write: the matched OLD value resolved the record_id;
        # extract the corresponding NEW cell value so a table-row delta writes the cell
        # (e.g. `IN1 (DC 12V点烟口)`), not the whole row. None -> abstain (plan_apply skips).
        new_value = _resolve_written_value(
            delta.get("old_normalized"), delta.get("new_normalized"), source_ref.get("matched_value")
        )
        requests.append(
            {
                "schema_version": CHANGE_REQUEST_SCHEMA_VERSION,
                "delta_hash": delta.get("delta_hash"),
                "table": table,
                "field": field,
                "record_id": record_id,
                "resolution_status": status,
                "old_text": delta.get("old_text"),
                "new_text": delta.get("new_text"),
                "old_value": source_ref.get("matched_value"),
                "new_value": new_value,
                "source_ref": source_ref,
                "blast_radius": list(source_ref.get("targets") or []),
                "external_write": False,
            }
        )
    return requests


def collect_translation_suggestions(change_requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Translation copy edits that abstain at the F6 write boundary.

    A reviewer-edited translated copy value can't be written to source via F6 (its
    home is the Translation_Memory), but it should NOT be silently dropped — it is
    surfaced as a suggestion so the message layer can reply the proposed
    translation change for a human (or a future TM sync) to act on.
    """
    suggestions: list[dict[str, Any]] = []
    for request in change_requests:
        if request.get("resolution_status") != TRANSLATION_ABSTAIN_STATUS:
            continue
        source_ref = request.get("source_ref") or {}
        suggestions.append(
            {
                "delta_hash": request.get("delta_hash"),
                "copy_key": source_ref.get("copy_key"),
                "lang": source_ref.get("lang"),
                "source_lang": source_ref.get("source_lang"),
                "old_text": request.get("old_text"),
                "new_text": request.get("new_text"),
                "routing_hint": "translation_memory",
            }
        )
    return suggestions


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
        # Write the precise cell value, never the whole-row text. A row-granularity delta
        # whose changed cell could not be aligned has new_value=None and abstains here
        # (exact-or-abstain on the value), so the write never corrupts the cell.
        value = request.get("new_value")
        if value is None or value == "":
            plan.append({**entry, "action": "skip", "reason": "precise cell value not resolved (abstain)"})
            continue
        plan.append({**entry, "action": "apply", "value": value, "old_value": request.get("old_value")})
    return plan


def apply_change_requests(
    change_requests: list[dict[str, Any]],
    *,
    approved_hashes: set[str],
    transport: _Transport | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Apply approved+resolved requests. Dry-run unless write and a transport are given.

    Each live write GET-checks the cell FIRST (drift guard): if it already holds the
    target value the write is skipped (``already_applied``, idempotent); if it holds
    anything other than the expected ``old_value`` the request **abstains**
    (``drift_abstained``) rather than clobber an externally-changed cell; otherwise it
    upserts and GET-verifies the result.
    """
    plan = plan_apply(change_requests, approved_hashes=approved_hashes)
    applied: list[dict[str, Any]] = []
    for entry in plan:
        if entry["action"] != "apply":
            continue
        if not (write and transport is not None):
            applied.append({**entry, "status": "planned"})
            continue
        # Per-request isolation: a missing table binding, a transport error, or a
        # network failure for ONE approved request must not abort the rest of the
        # batch nor leave the run half-reported. The bad request is recorded as
        # `error` and the loop continues. (E.g. a Localized_Copy-origin request
        # whose table has no writable binding lands here and is skipped safely.)
        target = entry["value"]
        expected_old = entry.get("old_value")
        try:
            current_before = transport.get(table=entry["table"], record_id=entry["record_id"], field=entry["field"])
        except Exception as exc:  # isolate one request's failure from the batch
            applied.append({**entry, "status": "error", "error": str(exc)})
            continue
        if _norm(current_before) == _norm(target):
            # The cell already holds the target value — idempotent, nothing to write.
            applied.append({**entry, "status": "already_applied", "verified": True})
            continue
        if expected_old is not None and _norm(current_before) != _norm(expected_old):
            # The live cell drifted from the expected old value (someone else changed it,
            # or the snapshot is stale) — abstain rather than overwrite. Exact-or-abstain.
            applied.append({**entry, "status": "drift_abstained", "verified": False, "current": current_before})
            continue
        try:
            transport.upsert(
                table=entry["table"], record_id=entry["record_id"], field=entry["field"], value=target
            )
            current = transport.get(table=entry["table"], record_id=entry["record_id"], field=entry["field"])
        except Exception as exc:  # isolate one request's failure from the batch
            applied.append({**entry, "status": "error", "error": str(exc)})
            continue
        verified = _norm(current) == _norm(target)
        applied.append({**entry, "status": "written" if verified else "verify_failed", "verified": verified})
    translation_suggestions = collect_translation_suggestions(change_requests)
    return {
        "schema_version": CHANGE_REQUEST_SCHEMA_VERSION,
        "external_write": bool(write and transport is not None),
        "summary": {
            "total": len(change_requests),
            "apply": sum(1 for entry in plan if entry["action"] == "apply"),
            "skip": sum(1 for entry in plan if entry["action"] == "skip"),
            "written": sum(1 for entry in applied if entry.get("status") == "written"),
            "already_applied": sum(1 for entry in applied if entry.get("status") == "already_applied"),
            "drift_abstained": sum(1 for entry in applied if entry.get("status") == "drift_abstained"),
            "verify_failed": sum(1 for entry in applied if entry.get("status") == "verify_failed"),
            "error": sum(1 for entry in applied if entry.get("status") == "error"),
            "translation_suggestions": len(translation_suggestions),
        },
        "plan": plan,
        "applied": applied,
        "translation_suggestions": translation_suggestions,
    }


def build_change_request_report(
    diff_report: dict[str, Any], *, sidecar_index: dict[str, Any] | None = None
) -> dict[str, Any]:
    requests = build_change_requests(diff_report, sidecar_index=sidecar_index)
    resolved = sum(1 for request in requests if request.get("resolution_status") == "resolved")
    translation_suggestions = collect_translation_suggestions(requests)
    return {
        "schema_version": CHANGE_REQUEST_SCHEMA_VERSION,
        "run_id": diff_report.get("run_id"),
        "external_write": False,
        "summary": {
            "requests": len(requests),
            "resolved_record_ids": resolved,
            "translation_suggestions": len(translation_suggestions),
        },
        "requests": requests,
        "translation_suggestions": translation_suggestions,
    }


def load_sidecar_index(data_root: Path | None) -> dict[str, Any] | None:
    return load_index(data_root) if data_root else None


def write_change_request_report(report: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "cloud_doc_backport_source_table_change_request.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_change_requests(report_path: Path) -> tuple[list[dict[str, Any]], str | None]:
    """Load the change-request report and return ``(requests, run_id)``.

    The report's ``requests`` list is exactly the shape ``apply_change_requests``
    consumes, so no reconstruction is needed.
    """
    payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("source-table change-request report must be a JSON object")
    requests = payload.get("requests")
    if not isinstance(requests, list):
        raise RuntimeError("source-table change-request report has no 'requests' list")
    return requests, payload.get("run_id")


def load_translation_suggestions(report_path: Path) -> list[dict[str, Any]]:
    """Load the change-request report's ``translation_suggestions`` (the abstained
    translation copy edits whose home is the TM). Returns ``[]`` when absent."""
    payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return []
    items = payload.get("translation_suggestions")
    return items if isinstance(items, list) else []


def source_table_apply_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        "# Cloud-doc backport — source-table apply",
        "",
        f"- Run ID: `{report.get('run_id') or 'n/a'}`",
        f"- External write: **{'yes' if report.get('external_write') else 'no (dry-run)'}**",
        f"- Approved hashes: {report.get('approved_count', 0)}",
        (
            f"- Plan: apply {summary.get('apply', 0)}, skip {summary.get('skip', 0)} "
            f"/ written {summary.get('written', 0)}, verify_failed {summary.get('verify_failed', 0)}, "
            f"error {summary.get('error', 0)}"
        ),
        "",
    ]
    applied = report.get("applied") or []
    if applied:
        lines.append("## Applied / planned")
        lines.append("")
        for entry in applied:
            status = entry.get("status", "?")
            detail = f" — {entry['error']}" if entry.get("error") else ""
            lines.append(
                f"- `{status}` {entry.get('table')}::{entry.get('field')} "
                f"record `{entry.get('record_id')}` (delta `{entry.get('delta_hash')}`){detail}"
            )
        lines.append("")
    skips = [entry for entry in (report.get("plan") or []) if entry.get("action") == "skip"]
    if skips:
        lines.append("## Skipped (gated)")
        lines.append("")
        for entry in skips:
            lines.append(f"- {entry.get('table')}::{entry.get('field')} (delta `{entry.get('delta_hash')}`) — {entry.get('reason')}")
        lines.append("")
    translation = report.get("translation_suggestions") or []
    if translation:
        lines.append("## Translation suggestions (route to Translation_Memory)")
        lines.append("")
        lines.append("These translated copy edits cannot be written to source via F6; act on them in the TM:")
        lines.append("")
        for item in translation:
            lines.append(
                f"- `{item.get('copy_key')}` [{item.get('lang')}] (delta `{item.get('delta_hash')}`): "
                f"{item.get('old_text')!r} → {item.get('new_text')!r}"
            )
        lines.append("")
    tm_apply = report.get("translation_apply") or {}
    tm_summary = tm_apply.get("summary") or {}
    if tm_apply:
        lines.append("## Translation_Memory writes")
        lines.append("")
        lines.append(
            f"- {'WRITE' if tm_apply.get('external_write') else 'dry-run'}: "
            f"apply {tm_summary.get('apply', 0)}, skip {tm_summary.get('skip', 0)} / "
            f"written {tm_summary.get('written', 0)}, already {tm_summary.get('already', 0)}, "
            f"verify_failed {tm_summary.get('verify_failed', 0)}, error {tm_summary.get('error', 0)}"
        )
        for entry in tm_apply.get("applied") or []:
            status = entry.get("status", "?")
            detail = f" — {entry['error']}" if entry.get("error") else ""
            lines.append(
                f"- `{status}` `{entry.get('copy_key')}` [{entry.get('lang')}] → TM `{entry.get('field')}` "
                f"record `{entry.get('record_id')}` (delta `{entry.get('delta_hash')}`){detail}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_source_table_apply_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_source_table_apply.json"
    markdown_path = out_dir / "cloud_doc_backport_source_table_apply.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(source_table_apply_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
