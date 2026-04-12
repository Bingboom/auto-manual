from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from integrations.openclaw.scripts.write_workflow_run_metadata import build_metadata, latest_publish_metadata


class TestOpenClawWorkflowRunMetadata(unittest.TestCase):
    def test_latest_publish_metadata_prefers_newest_built_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            releases_root = Path(tmpdir) / "reports" / "releases"
            older = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"
            newer = releases_root / "JE-1000F" / "JP" / "ja" / "latest" / "publish_meta.json"
            older.parent.mkdir(parents=True, exist_ok=True)
            newer.parent.mkdir(parents=True, exist_ok=True)
            older.write_text(
                '{\n  "built_at": "2026-04-10T09:00:00",\n  "document_link_url": "https://example.com/older"\n}\n',
                encoding="utf-8",
            )
            newer.write_text(
                '{\n  "built_at": "2026-04-10T10:00:00",\n  "document_link_url": "https://example.com/newer"\n}\n',
                encoding="utf-8",
            )

            selected = latest_publish_metadata(releases_root)

            self.assertIsNotNone(selected)
            assert selected is not None
            path, payload = selected
            self.assertEqual(path, newer)
            self.assertEqual(payload["document_link_url"], "https://example.com/newer")

    def test_build_metadata_includes_publish_metadata_and_run_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            releases_root = Path(tmpdir) / "reports" / "releases"
            meta_path = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            meta_path.write_text(
                (
                    '{\n'
                    '  "built_at": "2026-04-10T11:30:00",\n'
                    '  "document_link_url": "https://docs.example.com/doc",\n'
                    '  "html_index": "reports/releases/JE-1000F/US/en/latest/html/index.html",\n'
                    '  "word_output_path": "reports/releases/JE-1000F/US/en/versions/V1/manual.docx"\n'
                    '}\n'
                ),
                encoding="utf-8",
            )
            env = {
                "GITHUB_RUN_ID": "12345",
                "GITHUB_RUN_ATTEMPT": "2",
                "GITHUB_RUN_NUMBER": "88",
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_SERVER_URL": "https://github.example.com",
                "GITHUB_REF_NAME": "main",
            }

            payload = build_metadata(
                workflow_name="Feishu Build Queue",
                workflow_file=".github/workflows/feishu-build-queue.yml",
                queue_record_id="rec_publish",
                trigger_source="openclaw",
                openclaw_dispatch_nonce="nonce-123",
                artifact_names=["feishu-build-queue-output", "openclaw-run-metadata"],
                publish_url="https://manual.example.com/latest",
                failure_summary_path=None,
                releases_root=releases_root,
                env=env,
            )

            self.assertEqual(payload["workflow_name"], "Feishu Build Queue")
            self.assertEqual(payload["queue_record_id"], "rec_publish")
            self.assertEqual(payload["openclaw_dispatch_nonce"], "nonce-123")
            self.assertEqual(payload["publish_url"], "https://manual.example.com/latest")
            self.assertEqual(payload["document_link_url"], "https://docs.example.com/doc")
            self.assertTrue(
                str(payload["publish_metadata_path"]).replace("\\", "/").endswith(
                    "reports/releases/JE-1000F/US/en/latest/publish_meta.json"
                )
            )
            self.assertEqual(
                payload["run_url"],
                "https://github.example.com/owner/repo/actions/runs/12345",
            )
            self.assertEqual(
                payload["artifact_names"],
                ["feishu-build-queue-output", "openclaw-run-metadata"],
            )

    def test_build_metadata_includes_structured_failure_summary_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            failure_summary_path = root / ".tmp" / "openclaw" / "failure-summary.json"
            failure_summary_path.parent.mkdir(parents=True, exist_ok=True)
            failure_summary_path.write_text(
                (
                    '{\n'
                    '  "summary_code": "missing_spec_data",\n'
                    '  "summary_message": "缺少 JE-1000F_CN 的规格数据，无法进入 review。",\n'
                    '  "summary_next_step": "请先补齐 JE-1000F_CN 在 Spec_Master 中的规格数据，再重试。",\n'
                    '  "failure_count": 1,\n'
                    '  "failures": [\n'
                    '    {\n'
                    '      "code": "missing_spec_data",\n'
                    '      "target": "JE-1000F_CN"\n'
                    '    }\n'
                    '  ]\n'
                    '}\n'
                ),
                encoding="utf-8",
            )

            payload = build_metadata(
                workflow_name="Feishu Start Review",
                workflow_file=".github/workflows/feishu-start-review.yml",
                queue_record_id="rec_review",
                trigger_source="openclaw",
                openclaw_dispatch_nonce="nonce-456",
                artifact_names=["feishu-start-review-output", "openclaw-run-metadata"],
                publish_url="",
                failure_summary_path=failure_summary_path,
                releases_root=root / "reports" / "releases",
                env={},
            )

            self.assertIn("failure_summary", payload)
            failure_summary = payload["failure_summary"]
            assert isinstance(failure_summary, dict)
            self.assertEqual("missing_spec_data", failure_summary["summary_code"])
            self.assertEqual("缺少 JE-1000F_CN 的规格数据，无法进入 review。", failure_summary["summary_message"])
