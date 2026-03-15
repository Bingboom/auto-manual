from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_build_docs_command_should_build_preview_into_isolated_root(self) -> None:
        args = build_cli.parse_args(
            ["preview", "--config", "config.yaml", "--model", "JE-1000F", "--region", "US", "--page", "05_operation_guide"]
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

    def test_clean_targets_for_config_should_honor_custom_docs_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "custom-docs"
            config_path = root / "config.custom.yaml"
            with mock.patch.object(build_cli, "load_config", return_value={"paths": {"docs_dir": docs_dir.as_posix()}}):
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
        self.assertIsNone(args.tracked_root)
        self.assertEqual("HEAD~1", args.from_ref)
        self.assertEqual("HEAD", args.to_ref)
        self.assertIsNone(args.report_dir)
        self.assertFalse(args.ignore_initial_adds)

    def test_parse_args_should_support_doctor_action(self) -> None:
        args = build_cli.parse_args(["doctor", "--config", "config.ja.yaml"])

        self.assertEqual("doctor", args.action)
        self.assertEqual("config.ja.yaml", args.config)

    def test_run_diff_report_should_forward_config_to_tool(self) -> None:
        args = build_cli.parse_args(["diff-report", "--config", "config.ja.yaml", "--model", "JE-1000F", "--region", "JP"])
        seen: list[list[str]] = []
        original = build_cli.run_checked
        original_targets = build_cli._resolve_diff_report_targets
        try:
            build_cli._resolve_diff_report_targets = lambda parsed_args: [("JE-1000F", "JP")]  # type: ignore[assignment]
            build_cli.run_checked = lambda cmd: seen.append(cmd)  # type: ignore[assignment]
            build_cli.run_diff_report(args)
        finally:
            build_cli._resolve_diff_report_targets = original_targets  # type: ignore[assignment]
            build_cli.run_checked = original  # type: ignore[assignment]

        self.assertEqual(1, len(seen))
        self.assertIn("--config", seen[0])
        self.assertIn(str(build_cli.ROOT / "config.ja.yaml"), seen[0])
        self.assertIn(str(build_cli.ROOT / "docs" / "_review" / "JE-1000F" / "JP"), seen[0])
        self.assertIn(str(build_cli.ROOT / "reports" / "version_tracking" / "JE-1000F" / "JP"), seen[0])

    def test_run_diff_report_should_forward_ignore_initial_adds_flag(self) -> None:
        args = build_cli.parse_args(["diff-report", "--ignore-initial-adds", "--model", "JE-1000F", "--region", "US"])
        seen: list[list[str]] = []
        original = build_cli.run_checked
        original_targets = build_cli._resolve_diff_report_targets
        try:
            build_cli._resolve_diff_report_targets = lambda parsed_args: [("JE-1000F", "US")]  # type: ignore[assignment]
            build_cli.run_checked = lambda cmd: seen.append(cmd)  # type: ignore[assignment]
            build_cli.run_diff_report(args)
        finally:
            build_cli._resolve_diff_report_targets = original_targets  # type: ignore[assignment]
            build_cli.run_checked = original  # type: ignore[assignment]

        self.assertEqual(1, len(seen))
        self.assertIn("--ignore-initial-adds", seen[0])

    def test_run_diff_report_should_derive_report_dir_from_explicit_tracked_root(self) -> None:
        args = build_cli.parse_args(
            [
                "diff-report",
                "--config",
                "config.yaml",
                "--tracked-root",
                "docs/_review/JE-3600A/EU",
            ]
        )
        seen: list[list[str]] = []
        original = build_cli.run_checked
        try:
            build_cli.run_checked = lambda cmd: seen.append(cmd)  # type: ignore[assignment]
            build_cli.run_diff_report(args)
        finally:
            build_cli.run_checked = original  # type: ignore[assignment]

        self.assertEqual(1, len(seen))
        self.assertIn(str(build_cli.ROOT / "docs" / "_review" / "JE-3600A" / "EU"), seen[0])
        self.assertIn(str(build_cli.ROOT / "reports" / "version_tracking" / "JE-3600A" / "EU"), seen[0])

    def test_run_diff_report_should_run_per_target_when_defaults_are_inferred(self) -> None:
        args = build_cli.parse_args(["diff-report", "--config", "config.yaml"])
        seen: list[list[str]] = []
        original = build_cli.run_checked
        original_targets = build_cli._resolve_diff_report_targets
        try:
            build_cli._resolve_diff_report_targets = lambda parsed_args: [("JE-1000F", "US"), ("JE-3600A", "EU")]  # type: ignore[assignment]
            build_cli.run_checked = lambda cmd: seen.append(cmd)  # type: ignore[assignment]
            build_cli.run_diff_report(args)
        finally:
            build_cli._resolve_diff_report_targets = original_targets  # type: ignore[assignment]
            build_cli.run_checked = original  # type: ignore[assignment]

        self.assertEqual(2, len(seen))
        self.assertIn(str(build_cli.ROOT / "docs" / "_review" / "JE-1000F" / "US"), seen[0])
        self.assertIn(str(build_cli.ROOT / "reports" / "version_tracking" / "JE-1000F" / "US"), seen[0])
        self.assertIn(str(build_cli.ROOT / "docs" / "_review" / "JE-3600A" / "EU"), seen[1])
        self.assertIn(str(build_cli.ROOT / "reports" / "version_tracking" / "JE-3600A" / "EU"), seen[1])

    def test_parse_args_should_support_review_and_check_actions(self) -> None:
        review_args = build_cli.parse_args(["review"])
        check_args = build_cli.parse_args(["check", "--config", "config.ja.yaml"])
        publish_args = build_cli.parse_args(["publish", "--model", "JE-1000F", "--region", "JP"])
        release_args = build_cli.parse_args(["release-manifest", "--model", "JE-1000F", "--region", "JP"])
        sync_args = build_cli.parse_args(["sync-review", "--sync-scope", "generated", "--page-file", "03_product_overview_placeholder.rst"])

        self.assertEqual("review", review_args.action)
        self.assertEqual("check", check_args.action)
        self.assertEqual("config.ja.yaml", check_args.config)
        self.assertEqual("publish", publish_args.action)
        self.assertEqual("JE-1000F", publish_args.model)
        self.assertEqual("JP", publish_args.region)
        self.assertEqual("release-manifest", release_args.action)
        self.assertEqual("sync-review", sync_args.action)
        self.assertEqual("generated", sync_args.sync_scope)
        self.assertEqual(["03_product_overview_placeholder.rst"], sync_args.page_file)

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

    def test_publish_should_require_explicit_model_and_region(self) -> None:
        args = build_cli.parse_args(["publish"])

        with self.assertRaisesRegex(RuntimeError, "publish requires --model and --region"):
            build_cli.run_publish(args)

    def test_publish_should_run_check_diff_report_and_word_from_review(self) -> None:
        args = build_cli.parse_args(["publish", "--config", "config.ja.yaml", "--model", "JE-1000F", "--region", "JP"])
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

        self.assertEqual(5, len(seen))
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

        self.assertEqual(str(build_cli.ROOT / "tools" / "release_manifest.py"), seen[4][1])
        self.assertIn("--model", seen[4])
        self.assertIn("JE-1000F", seen[4])
        self.assertIn("--region", seen[4])
        self.assertIn("JP", seen[4])

    def test_release_manifest_command_should_require_explicit_target(self) -> None:
        args = build_cli.parse_args(["release-manifest"])

        with self.assertRaisesRegex(RuntimeError, "release-manifest requires --model and --region"):
            build_cli.release_manifest_command(args)

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
        args = build_cli.parse_args(["doctor", "--config", "config.yaml"])
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
