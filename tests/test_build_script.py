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
        self.assertIn("--formats", cmd)
        self.assertIn("pdf", cmd)
        self.assertNotIn("--clean", cmd)
        self.assertNotIn("--no-open", cmd)

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
        self.assertEqual("docs/_build/JE-1000F", args.tracked_root)
        self.assertEqual("HEAD~1", args.from_ref)
        self.assertEqual("HEAD", args.to_ref)
        self.assertEqual("reports/version_tracking/JE-1000F", args.report_dir)


if __name__ == "__main__":
    unittest.main()
