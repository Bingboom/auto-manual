from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.idml_rst_extract import _parse_text
from tools.web_presentation import load_web_manual_contract
from tools.word_bundle_html import _convert_rst_fragment_to_html
from tools.word_inbox_component import transform_word_inbox_html


ROOT = Path(__file__).resolve().parents[1]


def _rst_table(rows: list[list[str]]) -> str:
    return ".. list-table::\n\n" + "\n".join(
        "   * - " + "\n     - ".join(row) for row in rows
    )


class SignalWordDefinitionTableTests(unittest.TestCase):
    def test_distinct_signal_word_definitions_preserve_table_rows(self) -> None:
        for labels in (
            ("警告", "注意", "説明", "ヒント"),
            ("WARNING", "CAUTION", "NOTE", "TIP"),
            ("경고", "주의", "참고", "팁"),
        ):
            with self.subTest(labels=labels):
                rows = [[f"**{label}**", f"Definition {i}."] for i, label in enumerate(labels)]
                result = _parse_text(_rst_table(rows), {"latex"})
                self.assertEqual(len(result.blocks), 1)
                kind, payload = result.blocks[0]
                self.assertEqual(kind, "table")
                self.assertEqual(json.loads(payload), rows)

    def test_actual_jp_symbols_template_keeps_all_four_definitions(self) -> None:
        source = ROOT / "docs/templates/page_jp/01_meaning_of_symbols.rst"
        result = _parse_text(source.read_text(encoding="utf-8"), {"latex", "region_jp"})
        tables = [json.loads(payload) for kind, payload in result.blocks if kind == "table"]
        definitions = next(rows for rows in tables if rows[0][0] == "**警告**")
        self.assertEqual([row[0] for row in definitions], ["**警告**", "**注意**", "**説明**", "**ヒント**"])
        self.assertTrue(all(len(row) == 2 and row[1] for row in definitions))
        self.assertIn("死亡または重傷", definitions[0][1])

    def test_malformed_notice_or_definition_does_not_fall_back(self) -> None:
        cases = (
            [["**WARNING**"]],
            [["**WARNING**", ""]],
            [["**WARNING**", "Definition"], ["**CAUTION**", ""]],
            [["**WARNING**", "Definition"], ["**CAUTION**", "Body", "Extra"]],
            [["**WARNING**", "First"], ["**WARNING**", "Second"]],
            [["**WARNING**", "Definition"], ["Unrecognized", "Body"]],
        )
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaisesRegex(ValueError, "known notice label"):
                _parse_text(_rst_table(rows), {"latex"})


class PlainInventoryDocumentTests(unittest.TestCase):
    def _transform(self, fragment: str) -> str:
        return transform_word_inbox_html(
            fragment,
            source_path=Path("page/02_whats_in_the_box.rst"),
            config=load_web_manual_contract()["in_the_box"],
            language="ja",
        )

    def test_plain_inventory_preserves_exact_html_including_notes(self) -> None:
        fragment = (
            '<h1>Inventory</h1><table><tbody><tr>'
            '<td>Main <strong>unit</strong></td><td>Cable</td><td>Manual</td>'
            '</tr></tbody></table><p>First note.</p><p><strong>Second note.</strong></p>'
        )
        self.assertEqual(self._transform(fragment), fragment)

    def test_actual_jp_template_converts_with_all_items_and_notes(self) -> None:
        source = ROOT / "docs/templates/page_jp/02_whats_in_the_box.rst"
        text = source.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as td:
            html = _convert_rst_fragment_to_html(
                text, source, Path(td), presentation_profile="document", language="ja",
            )
        soup = BeautifulSoup(html, "html.parser")
        self.assertEqual([cell.get_text(" ", strip=True) for cell in soup.select("td")], ["本体", "AC充電ケーブル", "取扱説明書一式"])
        self.assertEqual(len(soup.select("img")), 0)
        self.assertIsNone(soup.select_one(".hb-inbox-word-tip"))
        paragraphs = [line.strip("*") for line in text.splitlines() if line.startswith(("※", "**"))]
        self.assertEqual(len(paragraphs), 4)
        for paragraph in paragraphs:
            self.assertIn(paragraph, soup.get_text(" ", strip=True))
        self.assertIn(paragraphs[-1], soup.select_one("strong").get_text())

    def test_illustrated_inbox_still_requires_tip(self) -> None:
        fragment = '<h1>Inventory</h1><table><tr>' + ''.join(
            f'<td><img src="{i}.png"/>Item {i}</td>' for i in range(3)
        ) + '</tr></table><p>Ordinary text is not a tip table.</p>'
        with self.assertRaisesRegex(RuntimeError, "missing its tip table"):
            self._transform(fragment)

    def test_tip_composition_still_requires_all_card_images(self) -> None:
        for image_count in (0, 2):
            fragment = '<h1>Inventory</h1><table><tr>' + ''.join(
                f'<td>{"<img src=art.png/>" if i < image_count else ""}Item {i}</td>'
                for i in range(3)
            ) + '</tr></table><table><tr><td>TIP</td><td>Body</td></tr></table>'
            with self.subTest(image_count=image_count), self.assertRaisesRegex(RuntimeError, "missing its image"):
                self._transform(fragment)

    def test_empty_or_malformed_inventory_does_not_bypass_validation(self) -> None:
        for cells in (("Unit", "Cable"), ("Unit", "Cable", "")):
            fragment = '<h1>Inventory</h1><table><tr>' + ''.join(
                f'<td>{label}</td>' for label in cells
            ) + '</tr></table><p>Note.</p>'
            with self.subTest(cells=cells), self.assertRaises(RuntimeError):
                self._transform(fragment)


if __name__ == "__main__":
    unittest.main()
