from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from tools.queue_claims import acquire_verified_queue_claim
from tools.queue_contract import RESULT_FIELD
from tools.queue_transitions import QueueTransitionFields, build_running_transition


@dataclass(frozen=True)
class _Record:
    record_id: str


class _SharedSource:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {
            "rec_1": {"record_id": "rec_1", "fields": {RESULT_FIELD: ""}},
        }
        self.before_fetch: Callable[[], None] | None = None
        self.fetch_view_ids: list[str | None] = []

    def upsert_record(self, *, record_id: str, record: dict[str, Any], **_: Any) -> dict[str, Any]:
        self.records[record_id]["fields"].update(record)
        return {"ok": True}

    def fetch_records_with_ids(self, *, view_id: str | None, **_: Any) -> list[dict[str, Any]]:
        self.fetch_view_ids.append(view_id)
        callback = self.before_fetch
        self.before_fetch = None
        if callback:
            callback()
        return list(self.records.values())


def _claim_fields(token: str, *, now: datetime) -> dict[str, Any]:
    return build_running_transition(
        fields=QueueTransitionFields(result_field=RESULT_FIELD),
        started_at=now,
        claim_token=token,
        claim_expires_at=now + timedelta(hours=2),
        normalize_workflow_action=lambda value: str(value) if value else None,
        normalize_doc_phase=lambda value: str(value) if value else None,
        workflow_action_label=lambda value: str(value) if value else None,
    )


class QueueClaimTests(unittest.TestCase):
    def test_claim_reads_back_without_pending_view_and_acquires(self) -> None:
        source = _SharedSource()
        now = datetime.now(timezone.utc)

        result = acquire_verified_queue_claim(
            source=source,
            base_token="app",
            table_id="table",
            records=[_Record("rec_1")],
            claim_fields=_claim_fields("claim-a", now=now),
            result_field=RESULT_FIELD,
            claim_token="claim-a",
        )

        self.assertTrue(result.acquired)
        self.assertEqual([None], source.fetch_view_ids)

    def test_overlapping_dispatch_allows_only_latest_verified_token(self) -> None:
        source = _SharedSource()
        now = datetime.now(timezone.utc)
        contender_result = None

        def run_contender() -> None:
            nonlocal contender_result
            contender_result = acquire_verified_queue_claim(
                source=source,
                base_token="app",
                table_id="table",
                records=[_Record("rec_1")],
                claim_fields=_claim_fields("claim-b", now=now),
                result_field=RESULT_FIELD,
                claim_token="claim-b",
            )

        source.before_fetch = run_contender
        first_result = acquire_verified_queue_claim(
            source=source,
            base_token="app",
            table_id="table",
            records=[_Record("rec_1")],
            claim_fields=_claim_fields("claim-a", now=now),
            result_field=RESULT_FIELD,
            claim_token="claim-a",
        )

        self.assertIsNotNone(contender_result)
        self.assertTrue(contender_result.acquired)
        self.assertFalse(first_result.acquired)
        self.assertIn("ownership changed", first_result.reason)


if __name__ == "__main__":
    unittest.main()
