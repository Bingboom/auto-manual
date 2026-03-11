from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import build as build_cli


class TestBuildScript(unittest.TestCase):
    def test_build_docs_command_should_prepare_rst_for_all_targets_by_default(self) -> None:
        args = build_cli.parse_args(["rst"])

        cmd = build_cli.build_docs_command(args)

        self.assertEqual(
            [
                sys.executable,
                str(build_cli.ROOT / "tools" / "build_docs.py"),
                "--config",
                str(build_cli.ROOT / "config.yaml"),
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

    def test_clean_targets_for_config_should_honor_custom_docs_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "custom-docs"
            config_path = root / "config.custom.yaml"
            config_path.write_text(
                f"paths:\n  docs_dir: {docs_dir.as_posix()}\n",
                encoding="utf-8",
            )

            build_dir, params_tex = build_cli.clean_targets_for_config(config_path)

            self.assertEqual(docs_dir / "_build", build_dir)
            self.assertEqual(docs_dir / "renderers" / "latex" / "params.tex", params_tex)

    def test_collect_legacy_docs_output_dirs_should_find_legacy_generated_and_bundle_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            (docs_dir / "_build").mkdir(parents=True)
            (docs_dir / "templates").mkdir()
            (docs_dir / "generated" / "M1").mkdir(parents=True)
            legacy_region_dir = docs_dir / "M1" / "US"
            (legacy_region_dir / "page").mkdir(parents=True)
            (legacy_region_dir / "index.rst").write_text("", encoding="utf-8")

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
        self.assertEqual(build_cli.REVIEW_TRACKED_ROOT, args.tracked_root)
        self.assertEqual("HEAD~1", args.from_ref)
        self.assertEqual("HEAD", args.to_ref)
        self.assertEqual(build_cli.REVIEW_REPORT_DIR, args.report_dir)
        self.assertFalse(args.ignore_initial_adds)

    def test_run_diff_report_should_forward_config_to_tool(self) -> None:
        args = build_cli.parse_args(["diff-report", "--config", "config.ja.yaml"])
        seen: list[list[str]] = []
        original = build_cli.run_checked
        try:
            build_cli.run_checked = lambda cmd: seen.append(cmd)  # type: ignore[assignment]
            build_cli.run_diff_report(args)
        finally:
            build_cli.run_checked = original  # type: ignore[assignment]

        self.assertEqual(1, len(seen))
        self.assertIn("--config", seen[0])
        self.assertIn(str(build_cli.ROOT / "config.ja.yaml"), seen[0])

    def test_run_diff_report_should_forward_ignore_initial_adds_flag(self) -> None:
        args = build_cli.parse_args(["diff-report", "--ignore-initial-adds"])
        seen: list[list[str]] = []
        original = build_cli.run_checked
        try:
            build_cli.run_checked = lambda cmd: seen.append(cmd)  # type: ignore[assignment]
            build_cli.run_diff_report(args)
        finally:
            build_cli.run_checked = original  # type: ignore[assignment]

        self.assertEqual(1, len(seen))
        self.assertIn("--ignore-initial-adds", seen[0])

    def test_parse_args_should_support_review_and_check_actions(self) -> None:
        review_args = build_cli.parse_args(["review"])
        check_args = build_cli.parse_args(["check", "--config", "config.ja.yaml"])
        publish_args = build_cli.parse_args(["publish", "--model", "JE-1000F", "--region", "JP"])

        self.assertEqual("review", review_args.action)
        self.assertEqual("check", check_args.action)
        self.assertEqual("config.ja.yaml", check_args.config)
        self.assertEqual("publish", publish_args.action)
        self.assertEqual("JE-1000F", publish_args.model)
        self.assertEqual("JP", publish_args.region)

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

    def test_review_bundle_command_should_forward_refresh_existing_flag(self) -> None:
        args = build_cli.parse_args(["review", "--refresh-review"])

        cmd = build_cli.review_bundle_command(args)

        self.assertIn("--refresh-existing", cmd)

    def test_publish_should_require_explicit_model_and_region(self) -> None:
        args = build_cli.parse_args(["publish"])

        with self.assertRaisesRegex(RuntimeError, "publish requires --model and --region"):
            build_cli.run_publish(args)

    def test_publish_should_run_check_diff_report_and_word_from_review(self) -> None:
        args = build_cli.parse_args(["publish", "--config", "config.je1000f.jp.yaml", "--model", "JE-1000F", "--region", "JP"])
        seen: list[list[str]] = []
        original_validate = build_cli.run_validate
        original_run_checked = build_cli.run_checked
        try:
            build_cli.run_validate = lambda config_path: None  # type: ignore[assignment]
            build_cli.run_checked = lambda cmd: seen.append(cmd)  # type: ignore[assignment]
            build_cli.run_publish(args)
        finally:
            build_cli.run_validate = original_validate  # type: ignore[assignment]
            build_cli.run_checked = original_run_checked  # type: ignore[assignment]

        self.assertEqual(4, len(seen))
        self.assertEqual(str(build_cli.ROOT / "tools" / "build_docs.py"), seen[0][1])
        self.assertIn("--source", seen[0])
        self.assertIn("review", seen[0])
        self.assertIn("--prepare-only", seen[0])

        self.assertEqual(str(build_cli.ROOT / "tools" / "check_docs.py"), seen[1][1])

        self.assertEqual(str(build_cli.ROOT / "tools" / "diff_report.py"), seen[2][1])
        self.assertIn(str(build_cli.ROOT / "docs" / "_review" / "JE-1000F" / "JP"), seen[2])
        self.assertIn(str(build_cli.ROOT / "reports" / "version_tracking" / "JE-1000F" / "JP"), seen[2])

        self.assertEqual(str(build_cli.ROOT / "tools" / "build_docs.py"), seen[3][1])
        self.assertIn("--formats", seen[3])
        self.assertIn("word", seen[3])
        self.assertIn("--source", seen[3])
        self.assertIn("review", seen[3])


if __name__ == "__main__":
    unittest.main()
