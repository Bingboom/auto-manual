from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools import audit_code_copy


class TestAuditCodeCopy(unittest.TestCase):
    def test_audit_should_find_manual_copy_and_exclude_tooling_noise(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            renderer = root / "tools" / "csv_pages" / "renderers_symbols.py"
            renderer.parent.mkdir(parents=True)
            renderer.write_text(
                "\n".join(
                    [
                        "from dataclasses import dataclass",
                        "@dataclass(frozen=True)",
                        "class SymbolAsset:",
                        "    path: str",
                        "    alt: str",
                        "SYMBOL_ASSETS = {",
                        "    'warning': SymbolAsset(",
                        "        path='templates/word_template/common_assets/symbols/warning.png',",
                        "        alt='Warning symbol.',",
                        "    ),",
                        "}",
                        "LANG_COPY = {",
                        "    'en': {",
                        "        'page_title': 'MEANING OF SYMBOLS',",
                        "        'header_symbol': 'Symbol',",
                        "        'header_meaning': 'Meaning',",
                        "        'signal_rows': [",
                        "            {'meaning': 'Hazardous practices that may result in severe injury.'},",
                        "        ],",
                        "    },",
                        "}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            signal_words = root / "tools" / "signal_words.py"
            signal_words.write_text(
                "_SIGNAL_WORDS = {'de': {'danger': 'GEFAHR'}}\n",
                encoding="utf-8",
            )
            html_rewrite = root / "tools" / "word_bundle_html_rewrite.py"
            html_rewrite.write_text(
                "def build_alt(label):\n"
                "    return f'{label} banner placeholder.'\n",
                encoding="utf-8",
            )
            cli = root / "tools" / "build_cli.py"
            cli.write_text(
                "import argparse\n"
                "parser = argparse.ArgumentParser(description='Cross-platform build entrypoint.')\n"
                "parser.add_argument('--config', help='Config YAML path')\n",
                encoding="utf-8",
            )
            test_file = root / "tests" / "test_copy.py"
            test_file.parent.mkdir()
            test_file.write_text("TEXT = 'PRODUCT OVERVIEW'\n", encoding="utf-8")

            findings = audit_code_copy.audit_paths(root, scan_roots=("tools",))

            texts = {item.text for item in findings}
            self.assertIn("Warning symbol.", texts)
            self.assertIn("MEANING OF SYMBOLS", texts)
            self.assertIn("Symbol", texts)
            self.assertIn("Meaning", texts)
            self.assertIn("Hazardous practices that may result in severe injury.", texts)
            self.assertIn("GEFAHR", texts)
            self.assertIn("{label} banner placeholder.", texts)
            self.assertNotIn("banner", texts)
            self.assertNotIn("Config YAML path", texts)
            self.assertNotIn("PRODUCT OVERVIEW", texts)
            self.assertTrue(all(item.priority == "P0" for item in findings))
            by_text = {item.text: item for item in findings}
            self.assertEqual("alt_text", by_text["Warning symbol."].content_role)
            self.assertEqual("symbols", by_text["MEANING OF SYMBOLS"].page_or_surface)
            self.assertEqual("en", by_text["MEANING OF SYMBOLS"].source_lang)
            self.assertEqual("page_title", by_text["MEANING OF SYMBOLS"].source_key)
            self.assertEqual("phase2_blocks", by_text["Hazardous practices that may result in severe injury."].recommended_owner)
            self.assertEqual("signal_word", by_text["GEFAHR"].content_role)

    def test_classification_should_route_report_ui_to_keep_in_code(self) -> None:
        classification = audit_code_copy.classify_string(
            rel_path="tools/diff_report_render.py",
            line=58,
            context="write_html_report",
            text="Search rows",
        )

        self.assertIsNotNone(classification)
        assert classification is not None
        self.assertEqual("report_ui", classification.copy_kind)
        self.assertEqual("keep_in_code", classification.recommended_owner)
        self.assertEqual("P1", classification.priority)
        self.assertEqual("report_ui", classification.content_role)

    def test_classification_should_ignore_report_markup_and_filenames(self) -> None:
        for text in ("<div class='card'>Search rows</div>", "report-index.html", "if (searchInput) {"):
            with self.subTest(text=text):
                classification = audit_code_copy.classify_string(
                    rel_path="tools/diff_report_render.py",
                    line=58,
                    context="write_html_report",
                    text=text,
                )
                self.assertIsNone(classification)

    def test_live_symbols_renderer_should_not_report_manual_copy(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        findings = audit_code_copy.audit_paths(
            repo_root,
            scan_roots=("tools/csv_pages/renderers_symbols.py",),
        )

        self.assertEqual([], findings)

    def test_live_signal_words_should_not_report_manual_copy(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        findings = audit_code_copy.audit_paths(
            repo_root,
            scan_roots=("tools/signal_words.py",),
        )

        self.assertEqual([], findings)

    def test_write_csv_should_use_stable_field_order(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "inventory.csv"
            finding = audit_code_copy.AuditFinding(
                file="tools/signal_words.py",
                line=8,
                symbol_or_context="_SIGNAL_WORDS",
                text="WARNING",
                copy_kind="manual_output",
                recommended_owner="localized_copy",
                priority="P0",
                reason="manual notice/signal word in Python",
            )

            audit_code_copy.write_csv([finding], path)

            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(list(audit_code_copy.FIELDNAMES), reader.fieldnames)
                rows = list(reader)
            self.assertEqual("WARNING", rows[0]["text"])
            self.assertIn("operator_decision", rows[0])
            self.assertIn("rst_template_option", rows[0])

    def test_write_summary_should_include_counts_and_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "summary.md"
            finding = audit_code_copy.AuditFinding(
                file="tools/signal_words.py",
                line=8,
                symbol_or_context="_SIGNAL_WORDS",
                text="WARNING",
                copy_kind="manual_output",
                recommended_owner="localized_copy",
                priority="P0",
                reason="manual notice/signal word in Python",
            )

            audit_code_copy.write_summary([finding], path)

            text = path.read_text(encoding="utf-8")
            self.assertIn("Total findings: 1", text)
            self.assertIn("P0 Migration Candidates", text)
            self.assertIn("Localized_Copy.csv", text)


if __name__ == "__main__":
    unittest.main()
