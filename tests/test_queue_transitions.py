import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from typing import Any

from tools.document_link_actions import normalize_doc_phase, normalize_workflow_action, workflow_action_label
from tools.queue_contract import (
    BUILD_STARTED_AT_FIELD,
    DATA_SYNC_FIELD,
    DOCUMENT_DIRECTORY_FIELD,
    FEISHU_CLOUD_DOC_FIELD,
    DOCUMENT_LINK_DD_FIELD,
    DOCUMENT_LINK_FIELD,
    DONE_TRIGGER_VALUE,
    FAILED_PREFIX,
    FORCE_PHASE2_REFRESH_FIELD,
    IMMEDIATE_TRIGGER_FIELD,
    RESULT_FIELD,
    RUNNING_PREFIX,
    SUCCESS_PREFIX,
    TRIGGER_FIELD,
)
from tools.queue_transitions import (
    QueueTransitionFields,
    append_writeback_failed,
    build_failure_writeback_transition,
    build_running_transition,
    build_success_transition,
)


def _fields(*, document_link_dd_field: str = "", feishu_cloud_doc_field: str = "") -> QueueTransitionFields:
    return QueueTransitionFields(
        result_field=RESULT_FIELD,
        build_started_at_field=BUILD_STARTED_AT_FIELD,
        document_directory_field=DOCUMENT_DIRECTORY_FIELD,
        document_link_field=DOCUMENT_LINK_FIELD,
        document_link_dd_field=document_link_dd_field,
        feishu_cloud_doc_field=feishu_cloud_doc_field,
        trigger_field=TRIGGER_FIELD,
        done_trigger_value=DONE_TRIGGER_VALUE,
        immediate_trigger_field=IMMEDIATE_TRIGGER_FIELD,
        force_phase2_refresh_field=FORCE_PHASE2_REFRESH_FIELD,
        data_sync_field=DATA_SYNC_FIELD,
        running_prefix=RUNNING_PREFIX,
        success_prefix=SUCCESS_PREFIX,
        failed_prefix=FAILED_PREFIX,
    )


def _label(value: Any) -> str | None:
    return workflow_action_label(value)


class QueueTransitionTests(unittest.TestCase):
    def test_running_transition_writes_claim_fields_only(self) -> None:
        started_at = datetime(2026, 5, 8, 9, 10, 11)

        payload = build_running_transition(
            fields=_fields(),
            started_at=started_at,
            version="1.0",
            workflow_action="Build Draft Package",
            data_sync_status="skipped",
            normalize_workflow_action=normalize_workflow_action,
            normalize_doc_phase=normalize_doc_phase,
            workflow_action_label=_label,
        )

        self.assertEqual(int(started_at.timestamp() * 1000), payload[BUILD_STARTED_AT_FIELD])
        self.assertIn("RUNNING", payload[RESULT_FIELD])
        self.assertIn("started_at=2026-05-08T09:10:11", payload[RESULT_FIELD])
        self.assertIn("workflow_action=Build Draft Package", payload[RESULT_FIELD])
        self.assertIn("data_sync=skipped", payload[RESULT_FIELD])
        self.assertNotIn(TRIGGER_FIELD, payload)
        self.assertNotIn(IMMEDIATE_TRIGGER_FIELD, payload)

    def test_success_transition_clears_triggers_and_writes_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "manual.docx"
            payload = build_success_transition(
                fields=_fields(document_link_dd_field=DOCUMENT_LINK_DD_FIELD),
                version="1.0",
                word_output_path=word_path,
                document_link_url="https://example.com/manual.docx",
                document_link_dd_url="https://alidocs.dingtalk.com/i/nodes/abc",
                feishu_cloud_doc_url="https://example.com/docx/cloud",
                built_at=datetime(2026, 5, 8, 9, 30, 0),
                workflow_action="draft",
                data_sync_status="refreshed",
                status_notes=("published_artifact=docx",),
                workflow_action_label=_label,
            )

        self.assertEqual(word_path.resolve(strict=False).as_posix(), payload[DOCUMENT_DIRECTORY_FIELD])
        self.assertEqual("https://example.com/manual.docx", payload[DOCUMENT_LINK_FIELD])
        self.assertEqual("https://alidocs.dingtalk.com/i/nodes/abc", payload[DOCUMENT_LINK_DD_FIELD])
        self.assertEqual([DONE_TRIGGER_VALUE], payload[TRIGGER_FIELD])
        self.assertFalse(payload[IMMEDIATE_TRIGGER_FIELD])
        self.assertFalse(payload[FORCE_PHASE2_REFRESH_FIELD])
        self.assertEqual("refreshed", payload[DATA_SYNC_FIELD])
        self.assertIn("SUCCESS", payload[RESULT_FIELD])
        self.assertIn("published_artifact=docx", payload[RESULT_FIELD])

    def test_success_transition_can_write_feishu_cloud_doc_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "manual.docx"
            payload = build_success_transition(
                fields=_fields(feishu_cloud_doc_field=FEISHU_CLOUD_DOC_FIELD),
                version="1.0",
                word_output_path=word_path,
                document_link_url="https://example.com/manual.docx",
                feishu_cloud_doc_url="https://example.com/docx/cloud",
                built_at=datetime(2026, 5, 8, 9, 30, 0),
                workflow_action="draft",
                workflow_action_label=_label,
            )

        self.assertEqual("https://example.com/docx/cloud", payload[FEISHU_CLOUD_DOC_FIELD])

    def test_failure_transition_preserves_latest_outputs_without_marking_done(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "manual.docx"
            payload = build_failure_writeback_transition(
                fields=_fields(),
                version="1.0",
                message="permission denied",
                workflow_action="publish",
                data_sync_status="failed",
                word_output_path=word_path,
                document_link_url="https://example.com/latest.pdf",
                document_link_dd_url=None,
                workflow_action_label=_label,
            )

        self.assertEqual(word_path.resolve(strict=False).as_posix(), payload[DOCUMENT_DIRECTORY_FIELD])
        self.assertEqual("https://example.com/latest.pdf", payload[DOCUMENT_LINK_FIELD])
        self.assertFalse(payload[IMMEDIATE_TRIGGER_FIELD])
        self.assertFalse(payload[FORCE_PHASE2_REFRESH_FIELD])
        self.assertEqual("failed", payload[DATA_SYNC_FIELD])
        self.assertIn("FAILED", payload[RESULT_FIELD])
        self.assertIn("latest_drive_link_preserved", payload[RESULT_FIELD])
        self.assertNotIn(TRIGGER_FIELD, payload)

    def test_writeback_failed_note_is_appended_to_failure_summary(self) -> None:
        self.assertEqual(
            "Publish JE-1000F_JP: permission denied | writeback_failed=unknown field",
            append_writeback_failed("Publish JE-1000F_JP: permission denied", RuntimeError("unknown field")),
        )


if __name__ == "__main__":
    unittest.main()
