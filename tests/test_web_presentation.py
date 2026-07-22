from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from tools.web_presentation import (
    protect_web_figures_for_pandoc,
    restore_web_figures_after_pandoc,
    transform_web_fragment,
)
from tools.word_bundle_html import _convert_rst_fragment_to_html


_ANNOTATED_FIGURE_RE = re.compile(
    r"<figure\b[^>]*class=[\"'][^\"']*\bhb-annotated-figure\b[^\"']*[\"'][^>]*>",
    re.IGNORECASE,
)
ROOT = Path(__file__).resolve().parents[1]
REVIEW_PAGES = ROOT / "docs" / "_review" / "JE-1000F" / "US" / "page"


def _web_fragment(source_name: str) -> str:
    source_path = REVIEW_PAGES / source_name
    with tempfile.TemporaryDirectory() as td:
        document_fragment = _convert_rst_fragment_to_html(
            source_path.read_text(encoding="utf-8"),
            source_path,
            Path(td),
        )
    return transform_web_fragment(document_fragment, source_path=source_path)


class WebPresentationTests(unittest.TestCase):
    def test_pandoc_guard_restores_raw_nested_figure_markup(self) -> None:
        figure = (
            '<figure class="hb-annotated-figure" data-figure-id="demo">'
            '<div class="hb-figure-callout" data-callout-id="demo.label">Label</div>'
            '<svg class="hb-leader-layer"><polyline points="0,0 1,1" /></svg>'
            "</figure>"
        )
        protected_html, placeholders = protect_web_figures_for_pandoc(
            f"<h1>Before</h1>{figure}<p>After</p>"
        )

        self.assertNotIn("hb-figure-callout", protected_html)
        self.assertEqual(1, len(placeholders))
        token = next(iter(placeholders))
        restored = restore_web_figures_after_pandoc(f"# Before\n\n{token}\n\nAfter\n", placeholders)
        self.assertIn('data-callout-id="demo.label"', restored)
        self.assertIn('<svg class="hb-leader-layer">', restored)

    def test_overview_callouts_are_semantically_stable_across_locales(self) -> None:
        localized = {
            "en": {
                "overview.front.power": "POWER Button",
                "overview.front.lcd": "LCD",
                "overview.front.dc12": "DC 12 V Port",
                "overview.right.handle": "Handle",
                "overview.right.dc_input": "DC Input",
                "overview.right.ac_input": "AC Input",
            },
            "fr": {
                "overview.front.power": "Bouton d'alimentation",
                "overview.front.lcd": "LCD",
                "overview.front.dc12": "Port 12 V CC",
                "overview.right.handle": "Poignée",
                "overview.right.dc_input": "Entrée CC",
                "overview.right.ac_input": "Entrée CA",
            },
            "es": {
                "overview.front.power": "Botón de encendido",
                "overview.front.lcd": "LCD",
                "overview.front.dc12": "Puerto CC 12 V",
                "overview.right.handle": "Asa",
                "overview.right.dc_input": "Entrada de CC",
                "overview.right.ac_input": "Entrada de CA",
            },
        }
        source_names = {
            "en": "03_product_overview_placeholder.rst",
            "fr": "p24_03_product_overview_placeholder.rst",
            "es": "p40_03_product_overview_placeholder.rst",
        }
        ids_by_locale: dict[str, list[str]] = {}

        for language, expected_callouts in localized.items():
            with self.subTest(language=language):
                transformed_html = _web_fragment(source_names[language])
                soup = BeautifulSoup(transformed_html, "html.parser")
                callout_ids = [
                    str(tag["data-callout-id"])
                    for tag in soup.select(".hb-figure-callout[data-callout-id]")
                ]
                ids_by_locale[language] = callout_ids

                self.assertEqual(15, len(callout_ids))
                self.assertEqual(15, len(set(callout_ids)))
                self.assertRegex(transformed_html, _ANNOTATED_FIGURE_RE)
                self.assertRegex(transformed_html, r"<svg\b")
                self.assertIn("hb-leader-layer", transformed_html)
                self.assertIn("front_controls", transformed_html)
                for callout_id, expected_copy in expected_callouts.items():
                    callout = soup.select_one(
                        f'.hb-figure-callout[data-callout-id="{callout_id}"]'
                    )
                    self.assertIsNotNone(callout)
                    self.assertIn(
                        expected_copy,
                        callout.get_text(" ", strip=True) if callout else "",
                    )

        self.assertEqual(ids_by_locale["en"], ids_by_locale["fr"])
        self.assertEqual(ids_by_locale["en"], ids_by_locale["es"])

    def test_operation_figure_keeps_prerequisite_image_and_steps_together(self) -> None:
        transformed = _web_fragment("05_operation_guide_placeholder.rst")

        soup = BeautifulSoup(transformed, "html.parser")
        operation_tag = soup.select_one('.hb-operation-figure[data-operation-id="ac-output"]')
        self.assertIsNotNone(operation_tag)
        operation_figure = str(operation_tag) if operation_tag else ""
        self.assertIn('data-operation-id="ac-output"', operation_figure)
        self.assertIn("Prerequisite", operation_figure)
        self.assertIn("The product is powered on.", operation_figure)
        self.assertIn("ac_output", operation_figure)
        self.assertIn("line-block", operation_figure)
        self.assertIn("Press once", operation_figure)
        self.assertNotIn("USB-C 100W", operation_figure)
        self.assertIn("USB-C 100W", transformed)

    def test_operation_steps_share_semantics_without_swallowing_locale_notes(self) -> None:
        localized = {
            "en": (
                "05_operation_guide_placeholder.rst",
                "Default standby time",
                [1, 1],
            ),
            "fr": (
                "p26_05_operation_guide_placeholder.rst",
                "Temps de veille par défaut",
                [1, 1],
            ),
            "es": (
                "p42_05_operation_guide_placeholder.rst",
                "Tiempo de espera predeterminado",
                [2, 2],
            ),
        }
        ids_by_locale: dict[str, list[str]] = {}

        for language, (source_name, standby_copy, expected_line_counts) in localized.items():
            with self.subTest(language=language):
                transformed = _web_fragment(source_name)
                soup = BeautifulSoup(transformed, "html.parser")
                figure = soup.select_one(
                    '.hb-operation-figure[data-operation-id="main-power"]'
                )
                self.assertIsNotNone(figure)
                steps = figure.select(".hb-operation-step") if figure else []
                ids_by_locale[language] = [str(step["data-callout-id"]) for step in steps]

                self.assertEqual(["on", "off"], [str(step["data-step-id"]) for step in steps])
                self.assertEqual(
                    expected_line_counts,
                    [len(step.find_all(class_="line", recursive=False)) for step in steps],
                )
                self.assertNotIn(standby_copy, figure.get_text(" ", strip=True) if figure else "")
                self.assertIn(standby_copy, transformed)

        self.assertEqual(ids_by_locale["en"], ids_by_locale["fr"])
        self.assertEqual(ids_by_locale["en"], ids_by_locale["es"])

    def test_unmatched_page_is_returned_unchanged(self) -> None:
        source_html = '<h1>WARRANTY</h1><p id="term">Keep this text byte-for-byte.</p>'

        self.assertEqual(
            source_html,
            transform_web_fragment(source_html, source_path=Path("11_warranty.rst")),
        )

    def test_same_named_page_for_unsupported_target_keeps_plain_source_html(self) -> None:
        source_html = (
            '<section><h2>PRODUCT OVERVIEW</h2>'
            '<img src="assets/overview/front_controls.png" />'
            "</section>"
        )

        self.assertEqual(
            source_html,
            transform_web_fragment(
                source_html,
                source_path=Path(
                    "/repo/docs/_review/OTHER-MODEL/EU/page/03_product_overview_placeholder.rst"
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
