from __future__ import annotations

import copy
from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.web_presentation import (
    WebPresentationError,
    is_web_entry_page,
    load_web_manual_contract,
    transform_web_fragment,
)


def declared_table(rows: str, title: str = "Source title") -> str:
    return (
        '<h2 class="hb-spec-section"><span class="hb-spec-bullet" aria-hidden="true">●</span>'
        f'<span class="hb-spec-section-text">{title}</span></h2>'
        f'<table class="manual-spec-table"><tbody>{rows}</tbody></table>'
    )


class WebSpecComponentTests(unittest.TestCase):
    def test_declared_sections_ignore_filename_target_and_legacy_page_counts(
        self,
    ) -> None:
        contract = copy.deepcopy(load_web_manual_contract())
        contract["figure_targets"] = []
        contract["specifications"] = {
            "source_patterns": [],
            "section_count": 99,
            "circled_reference_count": 99,
        }
        source = (
            "<h1>Manual</h1><p>Safety before.</p>"
            + declared_table(
                '<tr><td>Input①</td><td><a href="#note">100 V</a></td></tr>'
            )
            + declared_table(
                "<tr><td>Output</td><td><em>20 W</em><br/>10 W②</td></tr>", "Other"
            )
            + '<p id="note">① Footnote.</p><p>② Second note.</p><p>Safety after.</p>'
        )
        for path in (
            Path("renamed.rst"),
            Path("docs/_build/JE-1000F/JP/rst/page/appendix.rst"),
        ):
            with self.subTest(path=path):
                result = transform_web_fragment(
                    source, source_path=path, contract=contract
                )
                soup = BeautifulSoup(result, "html.parser")
                self.assertEqual(
                    2, len(soup.select("figure.hb-spec-table-composition"))
                )
                self.assertEqual(["①", "②"], [x.text for x in soup.select("sup")])
                self.assertEqual("#note", soup.select_one("td a")["href"])
                self.assertEqual("20 W", soup.select_one("td em").text)
                self.assertIsNotNone(soup.select_one("td br"))
                expected = BeautifulSoup(source, "html.parser")
                for bullet in expected.select(".hb-spec-bullet"):
                    bullet.decompose()
                self.assertEqual(
                    "".join(expected.stripped_strings), "".join(soup.stripped_strings)
                )

    def test_public_grouping_keeps_spans_continuations_and_existing_superscripts(
        self,
    ) -> None:
        source = declared_table(
            '<tr><td rowspan="2">Input</td><td>100 V<sup>①</sup></td></tr>'
            "<tr><td>200 V</td></tr>"
            "<tr><td>Output</td><td>20 W</td></tr><tr><td></td><td>30 W②</td></tr>"
        )
        result = transform_web_fragment(source, source_path=Path("arbitrary.rst"))
        soup = BeautifulSoup(result, "html.parser")
        self.assertEqual(["2", "2"], [x["rowspan"] for x in soup.select("th")])
        self.assertEqual(["Input", "Output"], [x.text for x in soup.select("th")])
        self.assertEqual(
            ["100 V①", "200 V", "20 W", "30 W②"], [x.text for x in soup.select("td")]
        )
        self.assertEqual(2, len(soup.select("sup")))
        self.assertFalse(soup.select("sup sup"))
        self.assertEqual(
            result, transform_web_fragment(result, source_path=Path("arbitrary.rst"))
        )

    def test_filename_or_table_shape_alone_does_not_declare_semantics(self) -> None:
        for source in (
            "<h2>Specifications</h2><table><tr><td>Item</td><td>Value</td></tr></table>",
            '<h2>主な仕様</h2><table class="manual-spec-table"><tbody>'
            "<tr><td>項目</td><td>値</td></tr></tbody></table>",
        ):
            for region in ("US", "JP"):
                path = Path(f"docs/_build/JE-1000F/{region}/rst/page/spec_ja.rst")
                self.assertEqual(
                    source, transform_web_fragment(source, source_path=path)
                )

    def test_declared_but_malformed_sections_fail_closed(self) -> None:
        sources = [
            declared_table("<tr><td>Value alone</td></tr>"),
            declared_table('<tr><td rowspan="2">Label</td><td>Value</td></tr>'),
            declared_table('<tr><td rowspan="0">Label</td><td>Value</td></tr>'),
            declared_table('<tr><td rowspan="x">Label</td><td>Value</td></tr>'),
            declared_table('<tr><td colspan="2">Label</td><td>Value</td></tr>'),
            declared_table('<tr><td>Label</td><td rowspan="2">Value</td></tr>'),
            declared_table("<tr><td>Label</td><td>Value</td><td>Extra</td></tr>"),
            declared_table("<tr><td></td><td>No initial label</td></tr>"),
            declared_table("<tr><td>Label</td><td>Value</td></tr>", ""),
            '<h2 class="hb-spec-section">Missing title span</h2>',
            declared_table("<tr><td>Label</td><td>Value</td></tr>").replace(
                'class="manual-spec-table"', ""
            ),
        ]
        for source in sources:
            with self.subTest(source=source), self.assertRaises(WebPresentationError):
                transform_web_fragment(source, source_path=Path("renamed.rst"))

    def test_semantics_do_not_open_figure_gate_on_mixed_page(self) -> None:
        image = '<img src="unapproved-overview.png" alt="Source art"/>'
        source = image + declared_table("<tr><td>Item</td><td>Value</td></tr>")
        path = Path(
            "docs/_build/JE-1000F/JP/rst/page/03_product_overview_placeholder.rst"
        )
        soup = BeautifulSoup(
            transform_web_fragment(source, source_path=path), "html.parser"
        )
        self.assertEqual(BeautifulSoup(image, "html.parser").img, soup.img)
        self.assertEqual(1, len(soup.select("figure.hb-spec-table-composition")))
        self.assertFalse(soup.select(".hb-annotated-figure, .hb-composite-art"))

    def test_manifest_entry_keeps_frozen_target_preface_rule(self) -> None:
        for region in ("US", "JP"):
            root = Path(f"docs/_build/JE-1000F/{region}/rst/page")
            self.assertTrue(is_web_entry_page(root / "00_preface.rst"))
            self.assertFalse(is_web_entry_page(root / "cover_jp.rst"))
            self.assertEqual(
                region == "JP", is_web_entry_page(root / "01_meaning_of_symbols.rst")
            )


if __name__ == "__main__":
    unittest.main()
