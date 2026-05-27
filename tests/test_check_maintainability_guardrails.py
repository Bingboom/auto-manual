from __future__ import annotations

import unittest

from tests.test_helpers import temp_test_root, write_lines
from tools import check_maintainability_guardrails as guardrails


class TestCheckMaintainabilityGuardrails(unittest.TestCase):
    def test_collect_hotspot_failures_returns_empty_within_threshold(self) -> None:
        with temp_test_root() as root:
            write_lines(root / "build.py", ["print('ok')"])

            failures = guardrails.collect_hotspot_failures(
                root,
                thresholds={"build.py": 5},
            )

        self.assertEqual([], failures)

    def test_collect_hotspot_failures_reports_threshold_regression(self) -> None:
        with temp_test_root() as root:
            write_lines(root / "tools" / "build_docs.py", ["line 1", "line 2", "line 3"])

            failures = guardrails.collect_hotspot_failures(
                root,
                thresholds={"tools/build_docs.py": 2},
            )

        self.assertEqual(1, len(failures))
        self.assertEqual("tools/build_docs.py", failures[0].path)
        self.assertEqual(3, failures[0].actual_lines)
        self.assertEqual(2, failures[0].max_lines)

    def test_collect_hotspot_failures_requires_expected_file(self) -> None:
        with temp_test_root() as root:
            with self.assertRaisesRegex(RuntimeError, "Guardrail target does not exist"):
                guardrails.collect_hotspot_failures(
                    root,
                    thresholds={"tools/process_build_queue.py": 10},
                )

    def test_collect_content_source_failures_blocks_legacy_tool_copy_constants(
        self,
    ) -> None:
        with temp_test_root() as root:
            write_lines(
                root / "tools" / "csv_pages" / "renderers_example.py",
                [
                    "LANG_COPY = {",
                    "    'en': {'title': 'Safety Instructions'},",
                    "}",
                    "_SIGNAL_WORDS = {'en': {'warning': 'WARNING'}}",
                ],
            )

            failures = guardrails.collect_content_source_failures(root)

        self.assertEqual(
            [
                "python-content-copy-constant",
                "python-content-copy-constant",
            ],
            [failure.rule for failure in failures],
        )
        self.assertEqual("tools/csv_pages/renderers_example.py", failures[0].path)
        self.assertEqual(1, failures[0].line_number)
        self.assertEqual("LANG_COPY", failures[0].text)

    def test_collect_content_source_failures_blocks_config_visible_copy(
        self,
    ) -> None:
        with temp_test_root() as root:
            write_lines(
                root / "config.demo.yaml",
                [
                    "build:",
                    "  languages: [en, fr]",
                    "  output_title: User Manual",
                ],
            )

            failures = guardrails.collect_content_source_failures(root)

        self.assertEqual(1, len(failures))
        self.assertEqual("config.demo.yaml", failures[0].path)
        self.assertEqual(3, failures[0].line_number)
        self.assertEqual("yaml-visible-copy", failures[0].rule)

    def test_collect_content_source_failures_blocks_recipe_sentence_default(
        self,
    ) -> None:
        with temp_test_root() as root:
            write_lines(
                root
                / "docs"
                / "templates"
                / "recipes"
                / "us-en"
                / "12_app_setup.yaml",
                [
                    "steps:",
                    "  - key: app_add_device",
                    "    default: Click the Add device button.",
                ],
            )

            failures = guardrails.collect_content_source_failures(root)

        self.assertEqual(1, len(failures))
        self.assertEqual(
            "docs/templates/recipes/us-en/12_app_setup.yaml",
            failures[0].path,
        )
        self.assertEqual(3, failures[0].line_number)
        self.assertEqual("recipe-sentence-default", failures[0].rule)

    def test_collect_content_source_failures_allows_source_files_and_cli_help(
        self,
    ) -> None:
        with temp_test_root() as root:
            write_lines(
                root / "data" / "phase2" / "page_copy.csv",
                ["page_id,lang,copy_key,text", "symbols,en,title,Safety Instructions"],
            )
            write_lines(
                root / "docs" / "templates" / "page_us-en" / "symbols.rst",
                ["Safety Instructions"],
            )
            write_lines(
                root / "tools" / "cli.py",
                ["parser.add_argument('--title', help='Output title for debug reports')"],
            )
            write_lines(
                root / "config.demo.yaml",
                ["build:", "  languages: [en, fr]"],
            )

            failures = guardrails.collect_content_source_failures(root)

        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
