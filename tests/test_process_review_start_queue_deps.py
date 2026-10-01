from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import replace
import io
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from tools import process_review_start_queue
from tools.phase2_support import LarkCliSource


class TestReviewQueueDefaultBoundaries(unittest.TestCase):
    def test_default_queue_client_keeps_empty_result_output(self) -> None:
        cfg = {"sync": {"phase2": {
            "provider": "lark_cli", "cli_bin": sys.executable,
            "base_token_env": "REVIEW_DEPS_TEST_BASE",
            "document_link": {"table_id_env": "REVIEW_DEPS_TEST_TABLE"},
        }}}
        output = io.StringIO()
        with mock.patch.dict(os.environ, {
            "REVIEW_DEPS_TEST_BASE": "app-test", "REVIEW_DEPS_TEST_TABLE": "tbl-test",
            "AUTO_MANUAL_LOG_LEVEL": "INFO",
        }), mock.patch.object(LarkCliSource, "fetch_records_with_ids", return_value=[]) as fetch:
            with redirect_stdout(output):
                result = process_review_start_queue.process_review_start_queue(
                    cfg=cfg, config_path=Path("config.yaml"), data_root=None, dry_run=True,
                )
        self.assertEqual(0, result)
        fetch.assert_called_once_with(base_token="app-test", table_id="tbl-test", view_id=None)
        self.assertEqual("[review-start] No pending review-start tasks found.\n", output.getvalue())

    def test_injected_runtime_dependencies_cover_client_snapshot_git_and_writeback(self) -> None:
        source = mock.Mock()
        source.fetch_records_with_ids.return_value = [{"record_id": "rec-test", "fields": {
            process_review_start_queue.DOCUMENT_KEY_FIELD: "M1_US",
            process_review_start_queue.WORKFLOW_ACTION_FIELD: "Start Review",
            process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
        }}]
        factory = mock.Mock(return_value=source)
        sync = mock.Mock()
        git = mock.Mock(return_value="")
        start_review = mock.Mock(return_value=("review/M1-US-test", "https://example.test/pr/1"))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "config.yaml"
            deps = replace(
                process_review_start_queue.default_review_start_deps(), root=root,
                source_factory=factory, cli_bin_fn=lambda cfg: "test-cli", phase2_identity_fn=lambda: "user",
                collect_preflight_errors_fn=lambda cfg, **kwargs: [],
                resolve_binding_fn=lambda cfg: SimpleNamespace(base_token="app-test", table_id="tbl-test", view_id=None),
                resolve_config_path_fn=lambda **kwargs: config_path,
                sync_snapshot_before_fn=sync, run_git_fn=git, start_review_for_record_fn=start_review,
                environ={"GITHUB_REPOSITORY": "test/repo", "GITHUB_TOKEN": "test-token"},
            )
            with redirect_stdout(io.StringIO()):
                result = process_review_start_queue.process_review_start_queue(
                    cfg={}, config_path=config_path, data_root="snapshot", dry_run=False, deps=deps,
                )
            self.assertEqual(0, result)
            factory.assert_called_once_with(cli_bin="test-cli", identity="user")
            source.fetch_records_with_ids.assert_called_once_with(
                base_token="app-test", table_id="tbl-test", view_id=None,
            )
            sync.assert_called_once_with(config_path=config_path, data_root="snapshot")
            git.assert_called_once_with(["fetch", "origin", "--prune"])
            self.assertEqual("rec-test", start_review.call_args.kwargs["record"].record_id)
            self.assertEqual(config_path, start_review.call_args.kwargs["build_config_path"])
            self.assertEqual("main", start_review.call_args.kwargs["base_ref"])
            source.upsert_record.assert_called_once_with(
                base_token="app-test", table_id="tbl-test", record_id="rec-test",
                record=deps.build_success_fields_fn(git_ref="review/M1-US-test", pr_url="https://example.test/pr/1"),
            )
