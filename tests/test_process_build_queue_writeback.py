import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tools import process_build_queue


class ProcessBuildQueueWritebackTests(unittest.TestCase):
    def test_build_success_fields_should_write_local_path_and_drive_url_and_clear_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx"
            drive_url = "https://test-degwga5x6ex8.feishu.cn/file/file_token_123"
            built_at = datetime(2026, 4, 1, 12, 34, 56)

            fields = process_build_queue.build_success_fields(
                version="1.0",
                word_output_path=word_path,
                document_link_url=drive_url,
                built_at=built_at,
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                data_sync_status="skipped",
            )

        self.assertEqual(
            word_path.resolve(strict=False).as_posix(),
            fields[process_build_queue.DOCUMENT_DIRECTORY_FIELD],
        )
        self.assertEqual(drive_url, fields[process_build_queue.DOCUMENT_LINK_FIELD])
        self.assertNotIn(process_build_queue.DOCUMENT_LINK_DD_FIELD, fields)
        self.assertEqual(["已构建"], fields[process_build_queue.TRIGGER_FIELD])
        self.assertFalse(fields[process_build_queue.IMMEDIATE_TRIGGER_FIELD])
        self.assertFalse(fields[process_build_queue.FORCE_PHASE2_REFRESH_FIELD])
        self.assertEqual("skipped", fields[process_build_queue.DATA_SYNC_FIELD])
        self.assertIn("SUCCESS", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("data_sync=skipped", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("workflow_action=Build Draft Package", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("version=1.0", fields[process_build_queue.RESULT_FIELD])

    def test_build_started_fields_should_write_datetime_millis(self) -> None:
        started_at = datetime(2026, 4, 1, 14, 55, 6)

        fields = process_build_queue.build_started_fields(
            started_at=started_at,
            version="1.0",
            workflow_action="Build Draft Package",
            data_sync_status="skipped",
        )

        self.assertEqual(
            int(started_at.timestamp() * 1000),
            fields[process_build_queue.BUILD_STARTED_AT_FIELD],
        )
        self.assertIn("RUNNING", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("started_at=2026-04-01T14:55:06", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("workflow_action=Build Draft Package", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("data_sync=skipped", fields[process_build_queue.RESULT_FIELD])

    def test_build_failure_writeback_fields_should_preserve_latest_local_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "docs" / "_build" / "JE-1000F" / "JP" / "word" / "manual_je1000f_jp.docx"
            fields = process_build_queue.build_failure_writeback_fields(
                version="1.0",
                message="permission | Permission denied [99991679]",
                workflow_action="Publish",
                doc_phase="Publish",
                data_sync_status="failed",
                word_output_path=word_path,
                document_link_url="https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
            )

        self.assertEqual(
            word_path.resolve(strict=False).as_posix(),
            fields[process_build_queue.DOCUMENT_DIRECTORY_FIELD],
        )
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
            fields[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertNotIn(process_build_queue.DOCUMENT_LINK_DD_FIELD, fields)
        self.assertFalse(fields[process_build_queue.IMMEDIATE_TRIGGER_FIELD])
        self.assertFalse(fields[process_build_queue.FORCE_PHASE2_REFRESH_FIELD])
        self.assertEqual("failed", fields[process_build_queue.DATA_SYNC_FIELD])
        self.assertIn("FAILED", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("data_sync=failed", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("workflow_action=Publish", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("latest_drive_link_preserved", fields[process_build_queue.RESULT_FIELD])


if __name__ == "__main__":
    unittest.main()
