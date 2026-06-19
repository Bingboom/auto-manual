"""Approval-gated Translation_Memory write-back (Milestone F follow-up).

A reviewer-edited *translated* copy value abstains at the F6 source-table boundary
(its home is the Translation_Memory, not the authoring source text). This module
turns those translation suggestions into TM content writes:

- resolve each to an exact live TM record by ``(target-language column, old
  translation)`` — **exact-or-abstain** (0 or >1 matches abstain);
- apply **only human-approved** suggestions, with GET-verify-after-write and
  idempotency (a record whose column already equals the new text is ``already``).

TM is shared across every model, so this is the **widest blast radius** write in
the backport system. It follows the same R9 gates as ``source_table_sync``: human
approval is mandatory (an agent may propose/execute, never approve), the match is
exact-or-abstain, and the default is dry-run (plan only, no network).
"""

from __future__ import annotations

import re
from typing import Any, Protocol

from tools.manual_copy_source import TM_LANGUAGE_FIELDS

TM_APPLY_SCHEMA_VERSION = "translation-suggestion-apply/v1"

_WS_RE = re.compile(r"\s+")


def _norm(text: Any) -> str:
    return _WS_RE.sub(" ", str(text if text is not None else "").strip())


def tm_column_for_lang(lang: Any) -> str:
    """Map a lang code (e.g. ``it``/``ja``/``pt-BR``) to its TM column name."""
    normalized = str(lang or "").strip().casefold().replace("_", "-")
    return TM_LANGUAGE_FIELDS.get(normalized, str(lang or "").strip())


class _TmTransport(Protocol):
    def list_records(self) -> list[dict[str, Any]]: ...
    def write(self, *, record_id: str, field: str, value: Any) -> None: ...
    def get(self, *, record_id: str, field: str) -> Any: ...


def _resolve_tm_record(
    records: list[dict[str, Any]], *, field: str, text: Any
) -> tuple[str | None, str]:
    """Resolve ``(field, text)`` to an exact TM ``record_id`` — exact-or-abstain.

    A translation's old value equals the TM record's target-language column (the
    rendered Localized_Copy is derived from it), so matching the old translation
    locates the record. 0 matches -> ``unresolved``; >1 distinct -> ``ambiguous``.
    """
    target = _norm(text)
    if not field or not target:
        return None, "unresolved"
    matches: set[str] = set()
    for record in records:
        if _norm((record.get("fields") or {}).get(field)) == target:
            record_id = record.get("record_id")
            if record_id:
                matches.add(str(record_id))
    if len(matches) == 1:
        return next(iter(matches)), "resolved"
    if not matches:
        return None, "unresolved"
    return None, "ambiguous"


def _entry(suggestion: dict[str, Any]) -> dict[str, Any]:
    return {
        "delta_hash": suggestion.get("delta_hash"),
        "copy_key": suggestion.get("copy_key"),
        "lang": suggestion.get("lang"),
    }


def plan_translation_writes(
    suggestions: list[dict[str, Any]],
    *,
    approved_hashes: set[str],
    records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Decide, per suggestion, whether it would be written — pure, no network.

    Encodes the R9 gates: human approval, known target language, non-empty new
    translation, and (when ``records`` are supplied) exact-or-abstain resolution +
    delta-hash idempotency.
    """
    plan: list[dict[str, Any]] = []
    seen: set[str] = set()
    for suggestion in suggestions:
        delta_hash = suggestion.get("delta_hash")
        entry = _entry(suggestion)
        if delta_hash in seen:
            plan.append({**entry, "action": "skip", "reason": "duplicate delta_hash (idempotent)"})
            continue
        if delta_hash:
            seen.add(delta_hash)
        if not delta_hash or delta_hash not in approved_hashes:
            plan.append({**entry, "action": "skip", "reason": "not approved by a human"})
            continue
        field = tm_column_for_lang(suggestion.get("lang"))
        if not field:
            plan.append({**entry, "action": "skip", "reason": "unknown target language"})
            continue
        new_text = suggestion.get("new_text")
        if not _norm(new_text):
            plan.append({**entry, "action": "skip", "reason": "empty new translation"})
            continue
        if records is None:
            # Dry-run without a transport cannot resolve a live TM record id.
            plan.append(
                {**entry, "action": "apply", "field": field, "value": new_text, "record_id": None, "resolution_status": "deferred"}
            )
            continue
        record_id, status = _resolve_tm_record(records, field=field, text=suggestion.get("old_text"))
        if status == "resolved":
            plan.append(
                {**entry, "action": "apply", "field": field, "value": new_text, "record_id": record_id, "resolution_status": "resolved"}
            )
            continue
        # Old translation not found — maybe this edit was already applied. If the
        # NEW text uniquely matches a record, treat it as already-applied (no-op),
        # not a confusing "unresolved", so re-approving is cleanly idempotent.
        already_id, already_status = _resolve_tm_record(records, field=field, text=new_text)
        if already_status == "resolved":
            plan.append(
                {**entry, "action": "already", "field": field, "value": new_text, "record_id": already_id, "resolution_status": "already"}
            )
            continue
        plan.append({**entry, "action": "skip", "reason": f"old translation {status} in TM (exact-or-abstain)"})
    return plan


def apply_translation_suggestions(
    suggestions: list[dict[str, Any]],
    *,
    approved_hashes: set[str],
    transport: _TmTransport | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Apply approved+resolved translation suggestions to the TM. Dry-run unless
    ``write`` and a ``transport`` are given. Each live write is GET-verified and
    idempotent (a record already equal to the new text is ``already``)."""
    records = transport.list_records() if transport is not None else None
    plan = plan_translation_writes(suggestions, approved_hashes=approved_hashes, records=records)
    applied: list[dict[str, Any]] = []
    for entry in plan:
        if entry["action"] == "already":
            applied.append({**entry, "status": "already", "verified": True})
            continue
        if entry["action"] != "apply":
            continue
        if not (write and transport is not None and entry.get("record_id")):
            applied.append({**entry, "status": "planned"})
            continue
        try:
            current = transport.get(record_id=entry["record_id"], field=entry["field"])
            if _norm(current) == _norm(entry["value"]):
                applied.append({**entry, "status": "already", "verified": True})
                continue
            transport.write(record_id=entry["record_id"], field=entry["field"], value=entry["value"])
            verify = transport.get(record_id=entry["record_id"], field=entry["field"])
            ok = _norm(verify) == _norm(entry["value"])
            applied.append({**entry, "status": "written" if ok else "verify_failed", "verified": ok})
        except Exception as exc:  # isolate one write's failure from the batch
            applied.append({**entry, "status": "error", "error": str(exc)})
    return {
        "schema_version": TM_APPLY_SCHEMA_VERSION,
        "external_write": bool(write and transport is not None),
        "summary": {
            "total": len(suggestions),
            "apply": sum(1 for entry in plan if entry["action"] == "apply"),
            "skip": sum(1 for entry in plan if entry["action"] == "skip"),
            "written": sum(1 for entry in applied if entry.get("status") == "written"),
            "already": sum(1 for entry in applied if entry.get("status") == "already"),
            "verify_failed": sum(1 for entry in applied if entry.get("status") == "verify_failed"),
            "error": sum(1 for entry in applied if entry.get("status") == "error"),
        },
        "plan": plan,
        "applied": applied,
    }
