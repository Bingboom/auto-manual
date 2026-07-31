from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from tools.document_link_queue import scalar_text
from tools.queue_transitions import queue_claim_is_owned


@dataclass(frozen=True)
class QueueClaimAttempt:
    acquired: bool
    reason: str = ""


def acquire_verified_queue_claim(
    *,
    source: Any,
    base_token: str,
    table_id: str,
    records: Iterable[Any],
    claim_fields: dict[str, Any],
    result_field: str,
    claim_token: str,
) -> QueueClaimAttempt:
    claimed_records = tuple(records)
    for record in claimed_records:
        source.upsert_record(
            base_token=base_token,
            table_id=table_id,
            record_id=record.record_id,
            record=claim_fields,
        )

    raw_records = source.fetch_records_with_ids(
        base_token=base_token,
        table_id=table_id,
        view_id=None,
    )
    latest_by_id = {
        str(raw.get("record_id") or "").strip(): raw
        for raw in raw_records
        if isinstance(raw, dict)
    }
    for record in claimed_records:
        raw = latest_by_id.get(record.record_id)
        fields = raw.get("fields", {}) if isinstance(raw, dict) else {}
        result_value = scalar_text(fields.get(result_field)) if isinstance(fields, dict) else ""
        if not queue_claim_is_owned(result_value, claim_token=claim_token):
            return QueueClaimAttempt(
                acquired=False,
                reason=f"claim ownership changed before dispatch: record_id={record.record_id}",
            )
    return QueueClaimAttempt(acquired=True)
