from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import replace
import inspect
import io
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from tools import process_build_queue, process_build_queue_services, queue_bound_runtime
from tools.process_build_queue_deps import default_queue_deps
from tools.phase2_support import LarkCliSource
from tools.utils.path_utils import PathSegments, review_dir_of


class TestBuildQueueDefaultBoundaries(unittest.TestCase):
    def test_snapshot_entry_keeps_keyword_only_contract_and_dynamic_runner(self) -> None:
        signature = inspect.signature(process_build_queue.sync_phase2_snapshot_before_queue)
        for name in ("config_path", "data_root"):
            self.assertEqual(inspect.Parameter.KEYWORD_ONLY, signature.parameters[name].kind)
            self.assertIs(inspect.Parameter.empty, signature.parameters[name].default)
        config_path = Path("configs/config.us-en.yaml")
        expected = [
            sys.executable, str(process_build_queue.ROOT / "build.py"), "sync-data",
            "--config", str(config_path), "--data-root", "snapshot",
        ]
        for _ in range(2):
            with mock.patch.object(queue_bound_runtime, "_run_command_impl") as runner:
                process_build_queue.sync_phase2_snapshot_before_queue(
                    config_path=config_path, data_root="snapshot",
                )
            self.assertEqual(mock.call(
                expected, cwd=process_build_queue.ROOT, prefix="[build-queue]", env=None,
                command_failure_message=queue_bound_runtime.command_failure_message,
            ), runner.call_args)

    def test_default_queue_client_fetches_without_changing_empty_result_output(self) -> None:
        cfg = {"sync": {"phase2": {
            "provider": "lark_cli", "cli_bin": sys.executable,
            "base_token_env": "QUEUE_DEPS_TEST_BASE",
            "document_link": {"table_id_env": "QUEUE_DEPS_TEST_TABLE"},
        }}}
        output = io.StringIO()
        with mock.patch.dict(os.environ, {
            "QUEUE_DEPS_TEST_BASE": "app-test", "QUEUE_DEPS_TEST_TABLE": "tbl-test",
            "AUTO_MANUAL_LOG_LEVEL": "INFO",
        }), mock.patch.object(LarkCliSource, "fetch_records_with_ids", return_value=[]) as fetch:
            with redirect_stdout(output):
                result = process_build_queue.process_build_queue(
                    cfg=cfg, config_path=Path("config.yaml"), data_root=None, dry_run=True,
                )
        self.assertEqual(0, result)
        fetch.assert_called_once_with(base_token="app-test", table_id="tbl-test", view_id=None)
        self.assertEqual("[build-queue] No pending build tasks found.\n", output.getvalue())


class TestBuildQueueInjectedBoundaries(unittest.TestCase):
    def test_default_dependencies_resolve_current_boundary_names(self) -> None:
        module = SimpleNamespace(
            LarkCliSource=mock.Mock(), _run_command=mock.Mock(),
            _prepare_git_ref_worktree=mock.Mock(), _remove_worktree=mock.Mock(),
        )
        first = default_queue_deps(module)
        module.LarkCliSource = mock.Mock()
        module._run_command = mock.Mock()
        module._prepare_git_ref_worktree = mock.Mock()
        module._remove_worktree = mock.Mock()
        second = default_queue_deps(module)
        for field, name in (
            ("source_factory", "LarkCliSource"), ("run_command", "_run_command"),
            ("prepare_git_ref_worktree", "_prepare_git_ref_worktree"),
            ("remove_worktree", "_remove_worktree"),
        ):
            self.assertIs(getattr(module, name), getattr(second, field))
            self.assertIsNot(getattr(first, field), getattr(second, field))

    def test_queue_uses_injected_client_and_propagates_fetch_failure(self) -> None:
        cfg = {"sync": {"phase2": {
            "provider": "lark_cli", "cli_bin": sys.executable,
            "base_token_env": "QUEUE_DEPS_TEST_BASE",
            "document_link": {"table_id_env": "QUEUE_DEPS_TEST_TABLE"},
        }}}
        source = mock.Mock()
        source.fetch_records_with_ids.return_value = []
        factory = mock.Mock(return_value=source)
        deps = replace(default_queue_deps(process_build_queue), source_factory=factory)
        with mock.patch.dict(os.environ, {
            "QUEUE_DEPS_TEST_BASE": "app-test", "QUEUE_DEPS_TEST_TABLE": "tbl-test",
            "AUTO_MANUAL_LOG_LEVEL": "INFO",
        }), redirect_stdout(io.StringIO()) as output:
            result = process_build_queue.process_build_queue(
                cfg=cfg, config_path=Path("config.yaml"), data_root=None, dry_run=True, deps=deps,
            )
            self.assertEqual(0, result)
            self.assertEqual("[build-queue] No pending build tasks found.\n", output.getvalue())
            source.fetch_records_with_ids.side_effect = RuntimeError("client unavailable")
            with self.assertRaisesRegex(RuntimeError, "client unavailable"):
                process_build_queue.process_build_queue(
                    cfg=cfg, config_path=Path("config.yaml"), data_root=None, dry_run=True, deps=deps,
                )
        self.assertEqual(2, factory.call_count)
        self.assertEqual(sys.executable, factory.call_args.kwargs["cli_bin"])
        source.fetch_records_with_ids.assert_called_with(
            base_token="app-test", table_id="tbl-test", view_id=None,
        )
        source.upsert_record.assert_not_called()

    def test_injected_git_and_command_boundaries_cleanup_on_build_failure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            worktree = Path(td)
            (review_dir_of(worktree / PathSegments.DOCS) / "M1" / "US").mkdir(parents=True)
            prepare = mock.Mock(return_value=worktree)
            remove = mock.Mock()
            runner = mock.Mock(side_effect=RuntimeError("injected command failed"))
            deps = replace(
                default_queue_deps(process_build_queue), run_command=runner,
                prepare_git_ref_worktree=prepare, remove_worktree=remove,
            )
            with self.assertRaisesRegex(RuntimeError, "injected command failed"):
                process_build_queue.build_document_for_task(
                    config_path=Path("configs/config.us-en.yaml"), model="M1", region="US",
                    data_root=None, doc_phase="draft", git_ref="main", deps=deps,
                )
            prepare.assert_called_once_with("main", prefer_local=False)
            remove.assert_called_once_with(worktree)
            runner.assert_called_once_with([
                sys.executable, str(worktree / "build.py"), "check",
                "--config", str(worktree / "configs/config.us-en.yaml"), "--model", "M1", "--region", "US",
                "--source", "review",
            ], cwd=worktree)

    def test_queue_forwards_injected_snapshot_and_build_callbacks(self) -> None:
        runner = mock.Mock(side_effect=RuntimeError("injected command failed"))
        deps = replace(default_queue_deps(process_build_queue), run_command=runner)

        def run_callbacks(**kwargs: object) -> int:
            for name, arguments in (
                ("sync_phase2_snapshot_before_queue", {"config_path": Path("config.yaml"), "data_root": None}),
                ("build_document_for_task", {
                    "config_path": Path("config.yaml"), "model": "M1", "region": "US",
                    "data_root": None, "doc_phase": "draft",
                }),
            ):
                with self.assertRaisesRegex(RuntimeError, "injected command failed"):
                    kwargs[name](**arguments)
            return 17

        with mock.patch.object(process_build_queue_services, "_process_build_queue_impl", side_effect=run_callbacks):
            result = process_build_queue.process_build_queue(
                cfg={}, config_path=Path("config.yaml"), data_root=None, dry_run=False, deps=deps,
            )
        self.assertEqual(17, result)
        self.assertEqual(["sync-data", "check"], [call.args[0][2] for call in runner.call_args_list])
