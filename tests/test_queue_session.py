from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from tools.queue_contract import QueueRecord
from tools.queue_session import load_pending_queue_state


def _active_result() -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    return (
        "RUNNING | claim_token=claim-active | "
        f"claim_expires_at={expires_at.isoformat(timespec='seconds')}"
    )


class _Source:
    def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
        return [{"record_id": "rec_1", "fields": {"开始构建时间": None}}]


class QueueSessionTests(unittest.TestCase):
    def test_active_row_blocks_its_entire_document_group(self) -> None:
        records = [
            QueueRecord("rec_active", "doc", "JE-1000F_US", "1.0", "en", result_value=_active_result()),
            QueueRecord("rec_pending", "doc", "JE-1000F_US", "1.0", "fr"),
        ]

        state = load_pending_queue_state(
            source=_Source(),
            binding=SimpleNamespace(base_token="app", table_id="table", view_id="view"),
            immediate_only=False,
            workflow_action=None,
            record_id="rec_pending",
            select_pending_queue_records=lambda *_, **kwargs: (
                records if kwargs["record_id"] is None else [records[1]]
            ),
            group_pending_queue_records=lambda selected: [selected],
            available_field_names=lambda raw: {"开始构建时间"},
            build_started_at_field="开始构建时间",
            force_phase2_refresh_field="是否强制刷新数据",
            data_sync_field="data_sync",
            document_link_dd_field="Document link_dd",
            feishu_cloud_doc_field="飞书云文档",
            upload_dingtalk_field="是否上传钉钉",
        )

        self.assertIsNone(state)

    def test_active_group_does_not_block_independent_pending_group(self) -> None:
        active = QueueRecord("rec_active", "doc-a", "JE-1000F_US", "1.0", "en", result_value=_active_result())
        pending = QueueRecord("rec_pending", "doc-b", "JE-2000F_US", "1.0", "en")

        state = load_pending_queue_state(
            source=_Source(),
            binding=SimpleNamespace(base_token="app", table_id="table", view_id="view"),
            immediate_only=False,
            workflow_action=None,
            record_id=None,
            select_pending_queue_records=lambda *_, **__: [active, pending],
            group_pending_queue_records=lambda selected: [[selected[0]], [selected[1]]],
            available_field_names=lambda raw: {"开始构建时间"},
            build_started_at_field="开始构建时间",
            force_phase2_refresh_field="是否强制刷新数据",
            data_sync_field="data_sync",
            document_link_dd_field="Document link_dd",
            feishu_cloud_doc_field="飞书云文档",
            upload_dingtalk_field="是否上传钉钉",
        )

        self.assertIsNotNone(state)
        self.assertEqual([[pending]], state.pending_groups)


if __name__ == "__main__":
    unittest.main()
