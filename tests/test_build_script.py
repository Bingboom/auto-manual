from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build as build_cli
from tests.test_helpers import patch_module_attrs, temp_test_root, write_text


class TestBuildScript(unittest.TestCase):
    def test_build_docs_command_should_prepare_rst_for_all_targets_by_default(self) -> None:
        args = build_cli.parse_args(["rst"])

        cmd = build_cli.build_docs_command(args)

        self.assertEqual(
            [
                sys.executable,
                str(build_cli.ROOT / "tools" / "build_docs.py"),
                "--config",
                str(build_cli.ROOT / "config.us.yaml"),
                "--all-targets",
                "--source",
                "auto",
                "--prepare-only",
                "--clean",
                "--no-open",
            ],
            cmd,
        )

    def test_build_docs_command_should_map_html_and_all_actions_to_formats(self) -> None:
        html_args = build_cli.parse_args(["html", "--config", "config.ja.yaml"])
        all_args = build_cli.parse_args(["all"])

        html_cmd = build_cli.build_docs_command(html_args)
        all_cmd = build_cli.build_docs_command(all_args)

        self.assertIn("--formats", html_cmd)
        self.assertIn("html", html_cmd)
        self.assertIn("--formats", all_cmd)
        self.assertIn(build_cli.ALL_OUTPUT_FORMATS, all_cmd)

    def test_build_docs_command_should_switch_to_single_target_when_model_or_region_is_given(self) -> None:
        args = build_cli.parse_args(["pdf", "--model", "JE-2000F", "--region", "US", "--open", "--no-clean"])

        cmd = build_cli.build_docs_command(args)

        self.assertNotIn("--all-targets", cmd)
        self.assertIn("--model", cmd)
        self.assertIn("JE-2000F", cmd)
        self.assertIn("--region", cmd)
        self.assertIn("US", cmd)
        self.assertIn("--source", cmd)
        self.assertIn("auto", cmd)
        self.assertIn("--formats", cmd)
        self.assertIn("pdf", cmd)
        self.assertNotIn("--clean", cmd)
        self.assertNotIn("--no-open", cmd)

    def test_build_docs_command_should_forward_source_override(self) -> None:
        args = build_cli.parse_args(["word", "--source", "review"])

        cmd = build_cli.build_docs_command(args)

        self.assertIn("--source", cmd)
        self.assertIn("review", cmd)

    def test_build_docs_command_should_build_preview_into_isolated_root(self) -> None:
        args = build_cli.parse_args(
            ["preview", "--config", "config.us.yaml", "--model", "JE-1000F", "--region", "US", "--page", "05_operation_guide"]
        )

        cmd = build_cli.build_docs_command(args)

        self.assertIn("--prepare-only", cmd)
        self.assertIn("--page-selector", cmd)
        self.assertIn("05_operation_guide", cmd)
        self.assertIn("--output-root", cmd)
        self.assertIn("--skip-root-index", cmd)

    def test_build_docs_command_should_require_explicit_preview_scope(self) -> None:
        args = build_cli.parse_args(["preview", "--model", "JE-1000F", "--region", "US"])

        with self.assertRaisesRegex(RuntimeError, "preview requires --page"):
            build_cli.build_docs_command(args)

    def test_build_docs_command_should_force_runtime_prepare_only_for_fast(self) -> None:
        args = build_cli.parse_args(["fast", "--source", "review", "--model", "JE-1000F", "--region", "US"])

        cmd = build_cli.build_docs_command(args)

        self.assertIn("--prepare-only", cmd)
        self.assertIn("--source", cmd)
        self.assertIn("runtime", cmd)
        self.assertNotIn("--clean", cmd)

    def test_build_docs_command_should_forward_data_root(self) -> None:
        args = build_cli.parse_args(["rst", "--data-root", "data/phase2"])

        cmd = build_cli.build_docs_command(args)

        self.assertIn("--data-root", cmd)
        self.assertIn("data/phase2", cmd)

    def test_build_docs_command_should_redirect_outputs_into_staging_root(self) -> None:
        args = build_cli.parse_args(
            ["word", "--model", "JE-1000F", "--region", "US", "--staging-root", ".tmp/staging"]
        )

        cmd = build_cli.build_docs_command(args)

        self.assertIn("--output-base-root", cmd)
        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "docs" / "_build"), cmd)
        self.assertIn("--skip-root-index", cmd)

    def test_clean_targets_for_config_should_honor_custom_docs_dir(self) -> None:
        with temp_test_root() as root:
            docs_dir = root / "custom-docs"
            config_path = root / "config.custom.yaml"
            with mock.patch.object(build_cli, "load_config", return_value={"paths": {"docs_dir": docs_dir.as_posix()}}):
                build_dir, params_tex = build_cli.clean_targets_for_config(config_path)

            self.assertEqual(docs_dir / "_build", build_dir)
            self.assertEqual(docs_dir / "renderers" / "latex" / "params.tex", params_tex)

    def test_collect_legacy_docs_output_dirs_should_find_legacy_generated_and_bundle_dirs(self) -> None:
        with temp_test_root() as root:
            docs_dir = root / "docs"
            (docs_dir / "_build").mkdir(parents=True)
            (docs_dir / "templates").mkdir()
            (docs_dir / "generated" / "M1").mkdir(parents=True)
            legacy_region_dir = docs_dir / "M1" / "US"
            (legacy_region_dir / "page").mkdir(parents=True)
            write_text(legacy_region_dir / "index.rst", "")

            legacy_dirs = build_cli.collect_legacy_docs_output_dirs(docs_dir)

            self.assertEqual(
                {
                    docs_dir / "generated",
                    docs_dir / "M1",
                },
                set(legacy_dirs),
            )

    def test_parse_args_should_support_diff_report_defaults(self) -> None:
        args = build_cli.parse_args(["diff-report"])

        self.assertEqual("diff-report", args.action)
        self.assertIsNone(args.tracked_root)
        self.assertEqual("HEAD~1", args.from_ref)
        self.assertEqual("HEAD", args.to_ref)
        self.assertIsNone(args.report_dir)
        self.assertTrue(args.ignore_initial_adds)

    def test_parse_args_should_support_doctor_action(self) -> None:
        args = build_cli.parse_args(["doctor", "--config", "config.ja.yaml"])

        self.assertEqual("doctor", args.action)
        self.assertEqual("config.ja.yaml", args.config)

    def test_run_diff_report_should_forward_config_to_tool(self) -> None:
        args = build_cli.parse_args(["diff-report", "--config", "config.ja.yaml", "--model", "JE-1000F", "--region", "JP"])
        seen: list[list[str]] = []
        with patch_module_attrs(
            build_cli,
            _resolve_diff_report_targets=lambda parsed_args: [("JE-1000F", "JP")],
            run_checked=lambda cmd: seen.append(cmd),
        ):
            build_cli.run_diff_report(args)

        self.assertEqual(1, len(seen))
        self.assertIn("--config", seen[0])
        self.assertIn(str(build_cli.ROOT / "config.ja.yaml"), seen[0])
        self.assertIn(str(build_cli.ROOT / "docs" / "_review" / "JE-1000F" / "JP"), seen[0])
        self.assertIn(str(build_cli.ROOT / "reports" / "version_tracking" / "JE-1000F" / "JP"), seen[0])

    def test_run_diff_report_should_not_forward_any_initial_adds_override_by_default(self) -> None:
        args = build_cli.parse_args(["diff-report", "--model", "JE-1000F", "--region", "US"])
        seen: list[list[str]] = []
        with patch_module_attrs(
            build_cli,
            _resolve_diff_report_targets=lambda parsed_args: [("JE-1000F", "US")],
            run_checked=lambda cmd: seen.append(cmd),
        ):
            build_cli.run_diff_report(args)

        self.assertEqual(1, len(seen))
        self.assertNotIn("--ignore-initial-adds", seen[0])
        self.assertNotIn("--include-initial-adds", seen[0])

    def test_run_diff_report_should_forward_include_initial_adds_flag(self) -> None:
        args = build_cli.parse_args(["diff-report", "--include-initial-adds", "--model", "JE-1000F", "--region", "US"])
        seen: list[list[str]] = []
        with patch_module_attrs(
            build_cli,
            _resolve_diff_report_targets=lambda parsed_args: [("JE-1000F", "US")],
            run_checked=lambda cmd: seen.append(cmd),
        ):
            build_cli.run_diff_report(args)

        self.assertEqual(1, len(seen))
        self.assertIn("--include-initial-adds", seen[0])

    def test_run_diff_report_should_forward_data_root(self) -> None:
        args = build_cli.parse_args(["diff-report", "--data-root", "data/phase2", "--model", "JE-1000F", "--region", "US"])
        seen: list[list[str]] = []
        with patch_module_attrs(
            build_cli,
            _resolve_diff_report_targets=lambda parsed_args: [("JE-1000F", "US")],
            run_checked=lambda cmd: seen.append(cmd),
        ):
            build_cli.run_diff_report(args)

        self.assertEqual(1, len(seen))
        self.assertIn("--data-root", seen[0])
        self.assertIn("data/phase2", seen[0])

    def test_run_diff_report_should_redirect_default_report_dir_into_staging_root(self) -> None:
        args = build_cli.parse_args(
            ["diff-report", "--model", "JE-1000F", "--region", "US", "--staging-root", ".tmp/staging"]
        )
        seen: list[list[str]] = []
        with patch_module_attrs(
            build_cli,
            _resolve_diff_report_targets=lambda parsed_args: [("JE-1000F", "US")],
            run_checked=lambda cmd: seen.append(cmd),
        ):
            build_cli.run_diff_report(args)

        self.assertEqual(1, len(seen))
        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "reports" / "version_tracking" / "JE-1000F" / "US"), seen[0])

    def test_run_diff_report_should_derive_report_dir_from_explicit_tracked_root(self) -> None:
        args = build_cli.parse_args(
            [
                "diff-report",
                "--config",
                "config.us.yaml",
                "--tracked-root",
                "docs/_review/JE-1000F/JP",
            ]
        )
        seen: list[list[str]] = []
        with patch_module_attrs(build_cli, run_checked=lambda cmd: seen.append(cmd)):
            build_cli.run_diff_report(args)

        self.assertEqual(1, len(seen))
        self.assertIn(str(build_cli.ROOT / "docs" / "_review" / "JE-1000F" / "JP"), seen[0])
        self.assertIn(str(build_cli.ROOT / "reports" / "version_tracking" / "JE-1000F" / "JP"), seen[0])

    def test_run_diff_report_should_run_per_target_when_defaults_are_inferred(self) -> None:
        args = build_cli.parse_args(["diff-report", "--config", "config.us.yaml"])
        seen: list[list[str]] = []
        with patch_module_attrs(
            build_cli,
            _resolve_diff_report_targets=lambda parsed_args: [("JE-1000F", "US"), ("JE-1000F", "JP")],
            run_checked=lambda cmd: seen.append(cmd),
        ):
            build_cli.run_diff_report(args)

        self.assertEqual(2, len(seen))
        self.assertIn(str(build_cli.ROOT / "docs" / "_review" / "JE-1000F" / "US"), seen[0])

    def test_process_review_start_queue_command_should_forward_record_id_and_data_root(self) -> None:
        args = build_cli.parse_args(
            [
                "process-review-start-queue",
                "--config",
                "config.us.yaml",
                "--data-root",
                ".tmp/review-start/phase2",
                "--record-id",
                "rec_init_1",
                "--dry-run",
            ]
        )

        cmd = build_cli.process_review_start_queue_command(args)

        self.assertEqual(str(build_cli.ROOT / "tools" / "process_review_start_queue.py"), cmd[1])
        self.assertIn("--config", cmd)
        self.assertIn(str(build_cli.ROOT / "config.us.yaml"), cmd)
        self.assertIn("--data-root", cmd)
        self.assertIn(".tmp/review-start/phase2", cmd)
        self.assertIn("--record-id", cmd)
        self.assertIn("rec_init_1", cmd)
        self.assertIn("--dry-run", cmd)

    def test_process_build_queue_command_should_ignore_doc_phase_when_workflow_action_is_present(self) -> None:
        args = build_cli.parse_args(
            ["process-build-queue", "--workflow-action", "publish", "--doc-phase", "draft"]
        )

        cmd = build_cli.process_build_queue_command(args)

        self.assertIn("--workflow-action", cmd)
        self.assertIn("publish", cmd)
        self.assertNotIn("--doc-phase", cmd)

    def test_parse_args_should_support_review_and_check_actions(self) -> None:
        review_args = build_cli.parse_args(["review"])
        check_args = build_cli.parse_args(["check", "--config", "config.ja.yaml"])
        queue_args = build_cli.parse_args(
            ["process-build-queue", "--dry-run", "--workflow-action", "build-draft-package", "--record-id", "rec_123"]
        )
        listener_args = build_cli.parse_args(["listen-build-queue", "--config", "config.us.yaml"])
        publish_args = build_cli.parse_args(["publish", "--model", "JE-1000F", "--region", "JP"])
        release_args = build_cli.parse_args(["release-manifest", "--model", "JE-1000F", "--region", "JP"])
        sync_args = build_cli.parse_args(["sync-review", "--sync-scope", "generated", "--page-file", "03_product_overview_placeholder.rst"])
        sync_data_args = build_cli.parse_args(["sync-data", "--table", "spec_master", "--dry-run"])

        self.assertEqual("review", review_args.action)
        self.assertEqual("check", check_args.action)
        self.assertEqual("config.ja.yaml", check_args.config)
        self.assertEqual("process-build-queue", queue_args.action)
        self.assertTrue(queue_args.dry_run)
        self.assertEqual("build-draft-package", queue_args.workflow_action)
        self.assertEqual("rec_123", queue_args.record_id)
        self.assertEqual("listen-build-queue", listener_args.action)
        self.assertEqual("publish", publish_args.action)
        self.assertEqual("JE-1000F", publish_args.model)
        self.assertEqual("JP", publish_args.region)
        self.assertEqual("release-manifest", release_args.action)
        self.assertEqual("sync-review", sync_args.action)
        self.assertEqual("generated", sync_args.sync_scope)
        self.assertEqual(["03_product_overview_placeholder.rst"], sync_args.page_file)
        self.assertEqual("sync-data", sync_data_args.action)
        self.assertEqual(["spec_master"], sync_data_args.table)
        self.assertTrue(sync_data_args.dry_run)

    def test_review_and_check_commands_should_forward_targets_like_build_actions(self) -> None:
        review_args = build_cli.parse_args(["review"])
        check_args = build_cli.parse_args(["check", "--model", "JE-2000F", "--region", "JP"])

        review_cmd = build_cli.review_bundle_command(review_args)
        check_cmd = build_cli.check_docs_command(check_args)

        self.assertEqual(str(build_cli.ROOT / "tools" / "review_bundle.py"), review_cmd[1])
        self.assertIn("--all-targets", review_cmd)
        self.assertEqual(str(build_cli.ROOT / "tools" / "check_docs.py"), check_cmd[1])
        self.assertIn("--model", check_cmd)
        self.assertIn("JE-2000F", check_cmd)
        self.assertIn("--region", check_cmd)
        self.assertIn("JP", check_cmd)

    def test_sync_review_command_should_forward_staged_docs_build_dir(self) -> None:
        args = build_cli.parse_args(
            ["sync-review", "--model", "JE-1000F", "--region", "JP", "--staging-root", ".tmp/staging"]
        )

        cmd = build_cli.sync_review_command(args)

        self.assertIn("--docs-build-dir", cmd)
        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "docs" / "_build"), cmd)

    def test_run_check_should_forward_explicit_review_source_to_rst_build(self) -> None:
        args = build_cli.parse_args(["check", "--config", "config.us.yaml", "--model", "JE-1000F", "--region", "US", "--source", "review"])
        seen: list[list[str]] = []
        with patch_module_attrs(
            build_cli,
            run_validate=lambda *argv, **kwargs: None,
            run_checked=lambda cmd: seen.append(cmd),
            _review_sync_target_args=lambda parsed_args: [parsed_args],
        ):
            build_cli.run_check(args)

        self.assertEqual(4, len(seen))
        self.assertEqual(str(build_cli.ROOT / "tools" / "build_docs.py"), seen[0][1])
        self.assertIn("--source", seen[0])
        self.assertIn("runtime", seen[0])
        self.assertIn("--prepare-only", seen[0])
        self.assertEqual(str(build_cli.ROOT / "tools" / "sync_review.py"), seen[1][1])
        self.assertEqual(str(build_cli.ROOT / "tools" / "build_docs.py"), seen[2][1])
        self.assertIn("--source", seen[2])
        self.assertIn("review", seen[2])
        self.assertEqual(str(build_cli.ROOT / "tools" / "check_docs.py"), seen[3][1])

    def test_maybe_sync_review_before_build_should_skip_when_no_review_bundle_exists(self) -> None:
        args = build_cli.parse_args(["word", "--config", "config.us.yaml", "--model", "JE-1000F", "--region", "US", "--source", "review"])
        seen: list[list[str]] = []
        with patch_module_attrs(
            build_cli,
            run_checked=lambda cmd: seen.append(cmd),
            _review_sync_target_args=lambda parsed_args: [],
        ):
            build_cli.maybe_sync_review_before_build(args)

        self.assertEqual([], seen)

    def test_review_bundle_command_should_forward_refresh_existing_flag(self) -> None:
        args = build_cli.parse_args(["review", "--refresh-review"])

        cmd = build_cli.review_bundle_command(args)

        self.assertIn("--refresh-existing", cmd)

    def test_run_validate_should_include_spec_master_validation(self) -> None:
        seen: list[list[str]] = []
        with patch_module_attrs(build_cli, run_checked=lambda cmd: seen.append(cmd)):
            build_cli.run_validate(build_cli.ROOT / "config.us.yaml")

        self.assertEqual(3, len(seen))
        self.assertEqual(str(build_cli.ROOT / "tools" / "validate_config.py"), seen[0][1])
        self.assertEqual(str(build_cli.ROOT / "tools" / "validate_layout_params.py"), seen[1][1])
        self.assertEqual(str(build_cli.ROOT / "tools" / "validate_spec_master.py"), seen[2][1])

    def test_run_validate_should_forward_data_root_to_spec_master_validation(self) -> None:
        seen: list[list[str]] = []
        with patch_module_attrs(build_cli, run_checked=lambda cmd: seen.append(cmd)):
            build_cli.run_validate(build_cli.ROOT / "config.us.yaml", data_root="data/phase2")

        self.assertEqual(3, len(seen))
        self.assertEqual(str(build_cli.ROOT / "tools" / "validate_spec_master.py"), seen[2][1])
        self.assertIn("--data-root", seen[2])
        self.assertIn("data/phase2", seen[2])

    def test_sync_review_command_should_forward_scope_and_page_files(self) -> None:
        args = build_cli.parse_args(
            [
                "sync-review",
                "--model",
                "JE-1000F",
                "--region",
                "JP",
                "--sync-scope",
                "generated",
                "--page-file",
                "03_product_overview_placeholder.rst",
            ]
        )

        cmd = build_cli.sync_review_command(args)

        self.assertEqual(str(build_cli.ROOT / "tools" / "sync_review.py"), cmd[1])
        self.assertIn("--sync-scope", cmd)
        self.assertIn("generated", cmd)
        self.assertIn("--page-file", cmd)
        self.assertIn("03_product_overview_placeholder.rst", cmd)

    def test_sync_data_command_should_forward_tables_and_dry_run(self) -> None:
        args = build_cli.parse_args(
            [
                "sync-data",
                "--config",
                "config.us.yaml",
                "--data-root",
                "data/phase2",
                "--table",
                "spec_master",
                "--dry-run",
            ]
        )

        cmd = build_cli.sync_data_command(args)

        self.assertEqual(str(build_cli.ROOT / "tools" / "sync_data.py"), cmd[1])
        self.assertIn("--data-root", cmd)
        self.assertIn("data/phase2", cmd)
        self.assertIn("--table", cmd)
        self.assertIn("spec_master", cmd)
        self.assertIn("--dry-run", cmd)

    def test_sync_data_command_should_reject_target_scoped_flags(self) -> None:
        args = build_cli.parse_args(["sync-data", "--model", "JE-1000F"])

        with self.assertRaisesRegex(RuntimeError, "sync-data does not accept --model or --region"):
            build_cli.sync_data_command(args)

    def test_process_build_queue_command_should_forward_data_root_and_dry_run(self) -> None:
        args = build_cli.parse_args(
            [
                "process-build-queue",
                "--config",
                "config.us.yaml",
                "--data-root",
                "data/phase2",
                "--workflow-action",
                "publish",
                "--record-id",
                "rec_456",
                "--dry-run",
            ]
        )

        cmd = build_cli.process_build_queue_command(args)

        self.assertEqual(str(build_cli.ROOT / "tools" / "process_build_queue.py"), cmd[1])
        self.assertIn("--data-root", cmd)
        self.assertIn("data/phase2", cmd)
        self.assertIn("--workflow-action", cmd)
        self.assertIn("publish", cmd)
        self.assertIn("--record-id", cmd)
        self.assertIn("rec_456", cmd)
        self.assertIn("--dry-run", cmd)

    def test_process_build_queue_command_should_reject_doc_phase_only_filter(self) -> None:
        args = build_cli.parse_args(["process-build-queue", "--doc-phase", "draft"])

        with self.assertRaisesRegex(RuntimeError, "--doc-phase is no longer supported"):
            build_cli.process_build_queue_command(args)

    def test_process_build_queue_command_should_reject_target_scoped_flags(self) -> None:
        args = build_cli.parse_args(["process-build-queue", "--model", "JE-1000F"])

        with self.assertRaisesRegex(RuntimeError, "process-build-queue does not accept --model or --region"):
            build_cli.process_build_queue_command(args)

    def test_listen_build_queue_command_should_forward_data_root(self) -> None:
        args = build_cli.parse_args(
            [
                "listen-build-queue",
                "--config",
                "config.us.yaml",
                "--data-root",
                "data/phase2",
            ]
        )

        cmd = build_cli.listen_build_queue_command(args)

        self.assertEqual(str(build_cli.ROOT / "tools" / "listen_build_queue.py"), cmd[1])
        self.assertIn("--data-root", cmd)
        self.assertIn("data/phase2", cmd)

    def test_listen_build_queue_command_should_reject_target_scoped_flags(self) -> None:
        args = build_cli.parse_args(["listen-build-queue", "--region", "US"])

        with self.assertRaisesRegex(RuntimeError, "listen-build-queue does not accept --model or --region"):
            build_cli.listen_build_queue_command(args)

    def test_publish_should_require_explicit_model_and_region(self) -> None:
        args = build_cli.parse_args(["publish"])

        with self.assertRaisesRegex(RuntimeError, "publish requires --model and --region"):
            build_cli.run_publish(args)

    def test_publish_should_run_check_diff_report_and_word_from_review(self) -> None:
        args = build_cli.parse_args(["publish", "--config", "config.ja.yaml", "--model", "JE-1000F", "--region", "JP"])
        seen: list[list[str]] = []
        original_validate = build_cli.run_validate
        original_run_checked = build_cli.run_checked
        original_review_sync_targets = build_cli._review_sync_target_args
        try:
            build_cli.run_validate = lambda config_path: None  # type: ignore[assignment]
            build_cli.run_checked = lambda cmd: seen.append(cmd)  # type: ignore[assignment]
            build_cli._review_sync_target_args = lambda parsed_args: [parsed_args]  # type: ignore[assignment]
            build_cli.run_publish(args)
        finally:
            build_cli.run_validate = original_validate  # type: ignore[assignment]
            build_cli.run_checked = original_run_checked  # type: ignore[assignment]
            build_cli._review_sync_target_args = original_review_sync_targets  # type: ignore[assignment]

        self.assertEqual(7, len(seen))
        self.assertEqual(str(build_cli.ROOT / "tools" / "build_docs.py"), seen[0][1])
        self.assertIn("--source", seen[0])
        self.assertIn("runtime", seen[0])
        self.assertIn("--prepare-only", seen[0])
        self.assertEqual(str(build_cli.ROOT / "tools" / "sync_review.py"), seen[1][1])

        self.assertEqual(str(build_cli.ROOT / "tools" / "build_docs.py"), seen[2][1])
        self.assertIn("--source", seen[2])
        self.assertIn("review", seen[2])
        self.assertIn("--prepare-only", seen[2])

        self.assertEqual(str(build_cli.ROOT / "tools" / "check_docs.py"), seen[3][1])

        self.assertEqual(str(build_cli.ROOT / "tools" / "diff_report.py"), seen[4][1])
        self.assertIn(str(build_cli.ROOT / "docs" / "_review" / "JE-1000F" / "JP"), seen[4])
        self.assertIn(str(build_cli.ROOT / "reports" / "version_tracking" / "JE-1000F" / "JP"), seen[4])

        self.assertEqual(str(build_cli.ROOT / "tools" / "build_docs.py"), seen[5][1])
        self.assertIn("--formats", seen[5])
        self.assertIn("word", seen[5])
        self.assertIn("--source", seen[5])
        self.assertIn("review", seen[5])

        self.assertEqual(str(build_cli.ROOT / "tools" / "release_manifest.py"), seen[6][1])
        self.assertIn("--model", seen[6])
        self.assertIn("JE-1000F", seen[6])
        self.assertIn("--region", seen[6])
        self.assertIn("JP", seen[6])

    def test_release_manifest_command_should_require_explicit_target(self) -> None:
        args = build_cli.parse_args(["release-manifest"])

        with self.assertRaisesRegex(RuntimeError, "release-manifest requires --model and --region"):
            build_cli.release_manifest_command(args)

    def test_release_manifest_command_should_forward_data_root(self) -> None:
        args = build_cli.parse_args(["release-manifest", "--model", "JE-1000F", "--region", "JP", "--data-root", "data/phase2"])

        cmd = build_cli.release_manifest_command(args)

        self.assertIn("--data-root", cmd)
        self.assertIn("data/phase2", cmd)

    def test_release_manifest_command_should_forward_staging_roots(self) -> None:
        args = build_cli.parse_args(
            ["release-manifest", "--model", "JE-1000F", "--region", "JP", "--staging-root", ".tmp/staging"]
        )

        cmd = build_cli.release_manifest_command(args)

        self.assertIn("--docs-build-dir", cmd)
        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "docs" / "_build"), cmd)
        self.assertIn("--releases-root", cmd)
        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "reports" / "releases"), cmd)

    def test_release_manifest_command_should_redirect_outputs_into_staging_root(self) -> None:
        args = build_cli.parse_args(
            ["release-manifest", "--model", "JE-1000F", "--region", "JP", "--staging-root", ".tmp/staging"]
        )

        cmd = build_cli.release_manifest_command(args)

        self.assertIn("--docs-build-dir", cmd)
        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "docs" / "_build"), cmd)
        self.assertIn("--releases-root", cmd)
        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "reports" / "releases"), cmd)

    def test_check_docs_command_should_redirect_bundle_root_into_staging_root(self) -> None:
        args = build_cli.parse_args(["check", "--model", "JE-1000F", "--region", "US", "--staging-root", ".tmp/staging"])

        cmd = build_cli.check_docs_command(args)

        self.assertIn("--docs-build-dir", cmd)
        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "docs" / "_build"), cmd)

    def test_publish_should_scope_review_and_report_dirs_by_lang_when_enabled(self) -> None:
        args = build_cli.parse_args(["publish", "--config", "config.us-es.yaml", "--model", "JE-1000F", "--region", "US"])
        seen: list[list[str]] = []
        original_validate = build_cli.run_validate
        original_run_checked = build_cli.run_checked
        original_load_config = build_cli.load_config
        original_review_sync_targets = build_cli._review_sync_target_args
        try:
            build_cli.run_validate = lambda config_path: None  # type: ignore[assignment]
            build_cli.run_checked = lambda cmd: seen.append(cmd)  # type: ignore[assignment]
            build_cli._review_sync_target_args = lambda parsed_args: [parsed_args]  # type: ignore[assignment]
            build_cli.load_config = lambda config_path: {  # type: ignore[assignment]
                "build": {
                    "languages": ["es"],
                    "include_lang_in_output_path": True,
                }
            }
            build_cli.run_publish(args)
        finally:
            build_cli.run_validate = original_validate  # type: ignore[assignment]
            build_cli.run_checked = original_run_checked  # type: ignore[assignment]
            build_cli.load_config = original_load_config  # type: ignore[assignment]
            build_cli._review_sync_target_args = original_review_sync_targets  # type: ignore[assignment]

        self.assertEqual(7, len(seen))
        self.assertEqual(str(build_cli.ROOT / "tools" / "diff_report.py"), seen[4][1])
        self.assertIn(str(build_cli.ROOT / "docs" / "_review" / "JE-1000F" / "US" / "es"), seen[4])
        self.assertIn(str(build_cli.ROOT / "reports" / "version_tracking" / "JE-1000F" / "US" / "es"), seen[4])
        self.assertEqual(str(build_cli.ROOT / "tools" / "release_manifest.py"), seen[6][1])

    def test_publish_should_redirect_generated_outputs_into_staging_root(self) -> None:
        args = build_cli.parse_args(
            ["publish", "--config", "config.ja.yaml", "--model", "JE-1000F", "--region", "JP", "--staging-root", ".tmp/staging"]
        )
        seen: list[list[str]] = []
        original_validate = build_cli.run_validate
        original_run_checked = build_cli.run_checked
        original_review_sync_targets = build_cli._review_sync_target_args
        try:
            build_cli.run_validate = lambda *argv, **kwargs: None  # type: ignore[assignment]
            build_cli.run_checked = lambda cmd: seen.append(cmd)  # type: ignore[assignment]
            build_cli._review_sync_target_args = lambda parsed_args: [parsed_args]  # type: ignore[assignment]
            build_cli.run_publish(args)
        finally:
            build_cli.run_validate = original_validate  # type: ignore[assignment]
            build_cli.run_checked = original_run_checked  # type: ignore[assignment]
            build_cli._review_sync_target_args = original_review_sync_targets  # type: ignore[assignment]

        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "docs" / "_build"), seen[0])
        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "docs" / "_build"), seen[2])
        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "reports" / "version_tracking" / "JE-1000F" / "JP"), seen[4])
        self.assertIn("--docs-build-dir", seen[6])
        self.assertIn(str(build_cli.ROOT / ".tmp" / "staging" / "reports" / "releases"), seen[6])

    def test_collect_doctor_findings_should_require_word_com_for_windows_bundle(self) -> None:
        args = build_cli.parse_args(["doctor", "--config", "config.ja.yaml", "--model", "JE-1000F", "--region", "JP"])
        cfg = {
            "build": {
                "languages": ["ja"],
                "default_model": "JE-2000F",
                "default_region": "JP",
                "word_source": "bundle",
            },
            "paths": {
                "layout_params_csv": "data/layout_params.csv",
            },
        }

        with mock.patch.object(build_cli, "_is_windows_platform", return_value=True), \
            mock.patch.object(build_cli, "load_config", return_value=cfg), \
            mock.patch.object(build_cli, "resolve_layout_params_csv", return_value=build_cli.ROOT / "data" / "layout_params.csv"), \
            mock.patch.object(build_cli, "_doctor_import", return_value=(True, "")), \
            mock.patch.object(build_cli, "_resolve_doctor_target", return_value=("JE-1000F", "JP")), \
            mock.patch.object(build_cli, "_check_word_com_available", return_value=(False, "Word COM unavailable")), \
            mock.patch.object(build_cli, "_find_xelatex", return_value="C:\\tex\\xelatex.exe"), \
            mock.patch.object(build_cli, "clean_targets_for_config", return_value=(build_cli.ROOT / "docs" / "_build", build_cli.ROOT / "docs" / "renderers" / "latex" / "params.tex")), \
            mock.patch("build.shutil.which", return_value=None), \
            mock.patch("tools.validate_config.load_yaml", return_value=cfg), \
            mock.patch("tools.validate_config.validate", return_value=[]), \
            mock.patch("tools.validate_layout_params.validate", return_value=[]):
            findings = build_cli._collect_doctor_findings(args)

        areas = {(finding.area, finding.level, finding.message) for finding in findings}
        self.assertIn(("word.runtime", "ERROR", "Word COM unavailable"), areas)

    def test_collect_doctor_findings_should_flag_missing_params_tex_for_latex_pdf(self) -> None:
        args = build_cli.parse_args(["doctor", "--config", "config.us.yaml"])
        cfg = {
            "build": {
                "languages": ["en"],
                "default_model": "JE-2000F",
                "default_region": "US",
                "word_source": "bundle",
            },
            "pdf": {
                "mode": "latex",
            },
            "paths": {
                "layout_params_csv": "data/layout_params.csv",
            },
            "tools": {
                "patch_fonts": "tools/patch_latex_fonts.py",
            },
        }

        with tempfile.TemporaryDirectory() as td:
            temp_root = Path(td)
            missing_params = temp_root / "docs" / "renderers" / "latex" / "params.tex"
            patch_fonts = temp_root / "tools" / "patch_latex_fonts.py"
            patch_fonts.parent.mkdir(parents=True, exist_ok=True)
            patch_fonts.write_text("# stub", encoding="utf-8")

            with mock.patch.object(build_cli, "_is_windows_platform", return_value=False), \
                mock.patch.object(build_cli, "_doctor_import", return_value=(True, "")), \
                mock.patch.object(build_cli, "_resolve_doctor_target", return_value=("JE-2000F", "US")), \
                mock.patch.object(build_cli, "_find_xelatex", return_value=None), \
                mock.patch.object(build_cli, "resolve_layout_params_csv", return_value=temp_root / "data" / "layout_params.csv"), \
                mock.patch.object(build_cli, "clean_targets_for_config", return_value=(temp_root / "docs" / "_build", missing_params)), \
                mock.patch.object(build_cli, "resolve_path_from_root", side_effect=lambda raw: patch_fonts if raw == "tools/patch_latex_fonts.py" else build_cli.ROOT / raw), \
                mock.patch("build.shutil.which", return_value=None), \
                mock.patch("tools.validate_config.load_yaml", return_value=cfg), \
                mock.patch("tools.validate_config.validate", return_value=[]), \
                mock.patch("tools.validate_layout_params.validate", return_value=[]):
                findings = build_cli._collect_doctor_findings(args)

        levels_by_area = {(finding.area, finding.level) for finding in findings}
        self.assertIn(("pdf.xelatex", "ERROR"), levels_by_area)
        self.assertIn(("pdf.params_tex", "ERROR"), levels_by_area)


if __name__ == "__main__":
    unittest.main()
