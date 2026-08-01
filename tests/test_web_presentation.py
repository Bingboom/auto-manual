from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.web_presentation import (
    WebPresentationError,
    protect_web_callouts_for_pandoc,
    protect_web_figures_for_pandoc,
    protect_web_inline_controls_for_pandoc,
    restore_web_callouts_after_pandoc,
    restore_web_figures_after_pandoc,
    restore_web_inline_controls_after_pandoc,
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
            active_tags={"region_us"},
        )
    return transform_web_fragment(document_fragment, source_path=source_path)


class WebPresentationTests(unittest.TestCase):
    def test_web_preface_hides_language_inventory_but_keeps_live_copy(self) -> None:
        output = _web_fragment("00_preface.rst")
        soup = BeautifulSoup(output, "html.parser")

        self.assertNotIn("English / French / Spanish", soup.get_text(" ", strip=True))
        self.assertEqual(
            "IMPORTANT",
            soup.find("strong").get_text(" ", strip=True),
        )
        self.assertIn("Congratulations on your new Jackery Explorer 1000", output)

    def test_pandoc_guard_restores_all_semantic_callout_types(self) -> None:
        callouts = "".join(
            (
                '<table class="manual-callout-table"><tbody><tr>'
                f'<td class="manual-callout-label"><p><strong>{label}</strong></p></td>'
                '<td class="manual-callout-body"><p>Body</p></td>'
                "</tr></tbody></table>"
            )
            for label in ("WARNING", "DANGER", "CAUTION", "NOTE")
        )

        protected_html, placeholders = protect_web_callouts_for_pandoc(
            f"<h1>Safety</h1>{callouts}<p>After</p>"
        )

        self.assertNotIn("manual-callout-table", protected_html)
        self.assertEqual(4, len(placeholders))
        pandoc_output = "# Safety\n\n" + "\n\n".join(placeholders) + "\n"
        restored = restore_web_callouts_after_pandoc(pandoc_output, placeholders)
        soup = BeautifulSoup(restored, "html.parser")
        tables = soup.select("table.manual-callout-table")
        self.assertEqual(4, len(tables))
        self.assertEqual(
            ["WARNING", "DANGER", "CAUTION", "NOTE"],
            [table.select_one(".manual-callout-label").get_text(strip=True) for table in tables],
        )
        self.assertTrue(all(table.select_one(".manual-callout-body") for table in tables))
        self.assertNotIn("<colgroup", restored)
        self.assertNotIn("<thead", restored)

    def test_pandoc_callout_guard_fails_closed_on_placeholder_drift(self) -> None:
        table = (
            '<table class="manual-callout-table"><tbody><tr>'
            '<td class="manual-callout-label">WARNING</td>'
            '<td class="manual-callout-body">Body</td>'
            "</tr></tbody></table>"
        )
        _protected_html, placeholders = protect_web_callouts_for_pandoc(table)
        token = next(iter(placeholders))

        with self.assertRaises(WebPresentationError):
            restore_web_callouts_after_pandoc("token was dropped", placeholders)
        with self.assertRaises(WebPresentationError):
            restore_web_callouts_after_pandoc(f"{token}\n{token}", placeholders)

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

    def test_pandoc_guard_restores_inbox_composition(self) -> None:
        figure = (
            '<figure class="hb-inbox-composition"><ol class="hb-inbox-grid">'
            '<li class="hb-inbox-card">Unit</li></ol></figure>'
        )
        protected_html, placeholders = protect_web_figures_for_pandoc(figure)

        self.assertNotIn("hb-inbox-grid", protected_html)
        token = next(iter(placeholders))
        restored = restore_web_figures_after_pandoc(token, placeholders)
        self.assertIn('class="hb-inbox-composition"', restored)
        self.assertIn('class="hb-inbox-card"', restored)

    def test_pandoc_guard_restores_reference_figure(self) -> None:
        figure = (
            '<figure class="hb-reference-figure hb-has-composite-art">'
            '<div class="hb-composite-stage"><img src="car.png" /></div>'
            '<div class="hb-reference-semantic">Vehicle</div></figure>'
        )
        protected_html, placeholders = protect_web_figures_for_pandoc(figure)

        self.assertNotIn("hb-reference-semantic", protected_html)
        token = next(iter(placeholders))
        restored = restore_web_figures_after_pandoc(token, placeholders)
        self.assertIn('class="hb-reference-figure hb-has-composite-art"', restored)
        self.assertIn('class="hb-reference-semantic"', restored)

    def test_pandoc_guard_restores_app_download_composition(self) -> None:
        figure = (
            '<figure class="hb-app-download-composition">'
            '<div class="hb-app-download-grid">Copy</div>'
            '<div class="hb-app-download-semantic">Source</div></figure>'
        )
        protected_html, placeholders = protect_web_figures_for_pandoc(figure)

        self.assertNotIn("hb-app-download-grid", protected_html)
        token = next(iter(placeholders))
        restored = restore_web_figures_after_pandoc(token, placeholders)
        self.assertIn('class="hb-app-download-composition"', restored)
        self.assertIn('class="hb-app-download-grid"', restored)

    def test_pandoc_guard_restores_app_add_device_composition(self) -> None:
        figure = (
            '<figure class="hb-app-add-device-composition">'
            '<img class="hb-app-add-device-phone-art" src="phones.png" />'
            '<span class="hb-app-add-device-live-label">Main Power Button</span>'
            "</figure>"
        )
        protected_html, placeholders = protect_web_figures_for_pandoc(figure)

        self.assertNotIn("hb-app-add-device-live-label", protected_html)
        token = next(iter(placeholders))
        restored = restore_web_figures_after_pandoc(token, placeholders)
        self.assertIn('class="hb-app-add-device-composition"', restored)
        self.assertIn('class="hb-app-add-device-live-label"', restored)

    def test_pandoc_guard_restores_fcc_composition(self) -> None:
        figure = (
            '<figure class="hb-fcc-composition"><div class="hb-fcc-grid">'
            '<div class="hb-fcc-column">FCC copy</div></div></figure>'
        )
        protected_html, placeholders = protect_web_figures_for_pandoc(figure)

        self.assertNotIn("hb-fcc-grid", protected_html)
        token = next(iter(placeholders))
        restored = restore_web_figures_after_pandoc(token, placeholders)
        self.assertIn('class="hb-fcc-composition"', restored)
        self.assertIn('class="hb-fcc-grid"', restored)

    def test_pandoc_guard_restores_lcd_table_composition(self) -> None:
        figure = (
            '<figure class="hb-lcd-table-composition">'
            '<table class="hb-lcd-icon-table"><tbody><tr>'
            '<td>1</td><td>icon</td><td>Wi-Fi</td>'
            '<td><div class="line-block"><div class="line">On</div></div></td>'
            "</tr></tbody></table></figure>"
        )
        protected_html, placeholders = protect_web_figures_for_pandoc(figure)

        self.assertNotIn("hb-lcd-icon-table", protected_html)
        token = next(iter(placeholders))
        restored = restore_web_figures_after_pandoc(token, placeholders)
        self.assertIn('class="hb-lcd-table-composition"', restored)
        self.assertIn('class="hb-lcd-icon-table"', restored)

    def test_pandoc_guard_restores_symbol_pair_composition(self) -> None:
        figure = (
            '<figure class="hb-symbol-pair-composition">'
            '<div class="hb-symbol-pair-grid"><div class="hb-symbol-panel">'
            '<table class="hb-symbol-panel-table"><tbody><tr>'
            '<td><img src="warning.png" /></td><td>Warning</td>'
            "</tr></tbody></table></div></div></figure>"
        )
        protected_html, placeholders = protect_web_figures_for_pandoc(figure)

        self.assertNotIn("hb-symbol-panel-table", protected_html)
        token = next(iter(placeholders))
        restored = restore_web_figures_after_pandoc(token, placeholders)
        self.assertIn('class="hb-symbol-pair-composition"', restored)
        self.assertIn('class="hb-symbol-panel-table"', restored)

    def test_pandoc_guard_restores_governed_data_table_compositions(self) -> None:
        figures = (
            '<figure class="hb-troubleshooting-composition">'
            '<table class="hb-troubleshooting-table"><tbody><tr>'
            '<td class="hb-troubleshooting-code">F6</td>'
            '<td class="hb-troubleshooting-measures"><div class="line-block">'
            '<div class="line">1. First</div><div class="line">2. Second</div>'
            "</div></td></tr></tbody></table></figure>"
            '<figure class="hb-spec-table-composition">'
            '<table class="hb-spec-table"><tbody><tr>'
            '<th class="hb-spec-label">Product</th>'
            '<td class="hb-spec-value">Explorer</td>'
            "</tr></tbody></table></figure>"
        )

        protected_html, placeholders = protect_web_figures_for_pandoc(figures)

        self.assertEqual(2, len(placeholders))
        self.assertNotIn("hb-troubleshooting-table", protected_html)
        self.assertNotIn("hb-spec-table", protected_html)
        restored = restore_web_figures_after_pandoc(
            "\n\n".join(placeholders),
            placeholders,
        )
        self.assertIn('class="hb-troubleshooting-composition"', restored)
        self.assertIn('<div class="line">2. Second</div>', restored)
        self.assertIn('class="hb-spec-table-composition"', restored)
        self.assertIn('class="hb-spec-value"', restored)

    def test_pandoc_guard_restores_all_warranty_compositions(self) -> None:
        figures = (
            '<figure class="hb-warranty-intro-composition">'
            '<div class="hb-warranty-intro-panel">Notice</div></figure>'
            '<figure class="hb-warranty-card" data-warranty-card-index="1">'
            '<p>Limited warranty copy</p></figure>'
            '<figure class="hb-warranty-period-card">'
            '<div class="hb-warranty-period-grid">'
            '<span class="hb-warranty-year-badge">3</span></div></figure>'
        )

        protected_html, placeholders = protect_web_figures_for_pandoc(figures)

        self.assertEqual(3, len(placeholders))
        self.assertNotIn("hb-warranty-intro-panel", protected_html)
        self.assertNotIn("hb-warranty-period-grid", protected_html)
        restored = restore_web_figures_after_pandoc(
            "\n\n".join(placeholders),
            placeholders,
        )
        self.assertIn('class="hb-warranty-intro-composition"', restored)
        self.assertIn('class="hb-warranty-card"', restored)
        self.assertIn('class="hb-warranty-period-card"', restored)
        self.assertIn('class="hb-warranty-year-badge"', restored)

    def test_pandoc_guard_restores_auto_resume_table_composition(self) -> None:
        figure = (
            '<figure class="hb-auto-resume-composition">'
            '<table class="hb-auto-resume-table"><thead><tr>'
            '<th>Auto</th><th>Not auto</th></tr></thead><tbody><tr>'
            '<td>On</td><td>Off</td></tr></tbody></table></figure>'
        )
        protected_html, placeholders = protect_web_figures_for_pandoc(figure)

        self.assertNotIn("hb-auto-resume-table", protected_html)
        token = next(iter(placeholders))
        restored = restore_web_figures_after_pandoc(token, placeholders)
        self.assertIn('class="hb-auto-resume-composition"', restored)
        self.assertIn('class="hb-auto-resume-table"', restored)

    def test_pandoc_guard_restores_lcd_mode_composition(self) -> None:
        figure = (
            '<figure class="hb-lcd-mode-composition">'
            '<div class="hb-lcd-mode-art-panel"><img src="lcd.png" /></div>'
            '<div class="hb-lcd-mode-table-panel">'
            '<table class="hb-lcd-mode-table"><tr><td>Turn on</td></tr></table>'
            "</div></figure>"
        )
        protected_html, placeholders = protect_web_figures_for_pandoc(figure)

        self.assertNotIn("hb-lcd-mode-table", protected_html)
        token = next(iter(placeholders))
        restored = restore_web_figures_after_pandoc(token, placeholders)
        self.assertIn('class="hb-lcd-mode-composition"', restored)
        self.assertIn('class="hb-lcd-mode-table"', restored)

    def test_pandoc_guard_preserves_inline_add_device_control(self) -> None:
        source = (
            '<p>2.1 Click the button <span class="hb-inline-add-device-icon" '
            'role="img" aria-label="Add device">+</span> to add your device.</p>'
        )
        protected_html, placeholders = protect_web_inline_controls_for_pandoc(source)

        self.assertNotIn("hb-inline-add-device-icon", protected_html)
        token = next(iter(placeholders))
        pandoc_output = f"2.1 Click the button {token} to add your device."
        restored = restore_web_inline_controls_after_pandoc(pandoc_output, placeholders)
        self.assertIn('class="hb-inline-add-device-icon"', restored)
        self.assertIn('aria-label="Add device"', restored)

    def test_pandoc_guard_preserves_semantic_subscript(self) -> None:
        source = "<p>Open-circuit voltage V<sub>oc</sub>.</p>"
        protected_html, placeholders = protect_web_inline_controls_for_pandoc(source)

        self.assertNotIn("<sub>oc</sub>", protected_html)
        token = next(iter(placeholders))
        pandoc_output = f"Open-circuit voltage V{token}."
        restored = restore_web_inline_controls_after_pandoc(pandoc_output, placeholders)
        self.assertIn("V<sub>oc</sub>", restored)
        self.assertNotIn("V~oc~", restored)

    def test_pandoc_guard_preserves_semantic_superscript(self) -> None:
        source = '<p>Bypass Mode<sup class="hb-spec-reference">①</sup>.</p>'
        protected_html, placeholders = protect_web_inline_controls_for_pandoc(source)

        self.assertNotIn("<sup", protected_html)
        token = next(iter(placeholders))
        pandoc_output = f"Bypass Mode{token}."
        restored = restore_web_inline_controls_after_pandoc(
            pandoc_output,
            placeholders,
        )
        self.assertIn('<sup class="hb-spec-reference">①</sup>', restored)
        self.assertNotIn("^①^", restored)

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

    def test_overview_uses_localized_composite_artwork_with_semantic_fallback(self) -> None:
        localized_sources = {
            "en": "03_product_overview_placeholder.rst",
            "fr": "p24_03_product_overview_placeholder.rst",
            "es": "p40_03_product_overview_placeholder.rst",
        }

        for language, source_name in localized_sources.items():
            with self.subTest(language=language):
                transformed_html = _web_fragment(source_name)
                soup = BeautifulSoup(transformed_html, "html.parser")
                figures = soup.select("figure.hb-annotated-figure.hb-has-composite-art")
                self.assertEqual(2, len(figures))
                self.assertTrue(
                    all(
                        figure.select_one(".hb-composite-stage .hb-composite-art")
                        for figure in figures
                    )
                )
                self.assertEqual(
                    15,
                    len(soup.select(".hb-annotated-stage .hb-figure-callout")),
                )
                extension = "svg" if language == "en" else "png"
                self.assertIn(
                    f"product_overview_front_{language}.{extension}",
                    transformed_html,
                )
                self.assertIn(
                    f"product_overview_right_{language}.{extension}",
                    transformed_html,
                )

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

    def test_auto_resume_table_uses_template_grid_across_locales(self) -> None:
        localized_sources = {
            "en": "05_operation_guide_placeholder.rst",
            "fr": "p26_05_operation_guide_placeholder.rst",
            "es": "p42_05_operation_guide_placeholder.rst",
        }

        for language, source_name in localized_sources.items():
            with self.subTest(language=language):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                composition = soup.select_one("figure.hb-auto-resume-composition")
                self.assertIsNotNone(composition)
                table = (
                    composition.select_one("table.hb-auto-resume-table")
                    if composition
                    else None
                )
                self.assertIsNotNone(table)
                self.assertEqual(2, len(table.select("col.hb-auto-resume-col")))
                self.assertEqual(2, len(table.select("thead > tr > th")))
                rows = table.select("tbody > tr") if table else []
                self.assertEqual(4, len(rows))
                spanning_cell = rows[1].find("td", recursive=False)
                self.assertEqual("2", str(spanning_cell.get("rowspan", "")))
                self.assertIn("hb-auto-resume-left", spanning_cell.get("class", []))
                self.assertEqual(1, len(rows[2].find_all("td", recursive=False)))
                continuation_cell = rows[2].find("td", recursive=False)
                self.assertIn(
                    "hb-auto-resume-right",
                    continuation_cell.get("class", []) if continuation_cell else [],
                )

    def test_lcd_mode_uses_live_template_composition_across_locales(self) -> None:
        localized_sources = {
            "en": ("05_operation_guide_placeholder.rst", "Shortly On"),
            "fr": ("p26_05_operation_guide_placeholder.rst", "Allumer en discontinu"),
            "es": ("p42_05_operation_guide_placeholder.rst", "En breve"),
        }

        for language, (source_name, first_state) in localized_sources.items():
            with self.subTest(language=language):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                composition = soup.select_one("figure.hb-lcd-mode-composition")
                self.assertIsNotNone(composition)
                self.assertIsNotNone(composition.select_one(".hb-lcd-mode-art-panel"))
                image = composition.select_one("img.hb-lcd-mode-art")
                self.assertIsNotNone(image)
                table = composition.select_one("table.hb-lcd-mode-table")
                self.assertIsNotNone(table)
                self.assertIsNone(table.select_one("img"))
                self.assertEqual(3, len(table.select("colgroup > col")))
                rows = table.select("tr") if table else []
                self.assertEqual([3, 2, 2, 3, 2, 2], [len(row.select("td")) for row in rows])
                states = table.select("td.hb-lcd-mode-state") if table else []
                self.assertEqual(2, len(states))
                self.assertTrue(all(str(state.get("rowspan", "")) == "3" for state in states))
                self.assertEqual(first_state, states[0].get_text(" ", strip=True))
                self.assertFalse(any(cell.get("style") for cell in table.select("td")))

    def test_inbox_uses_pdf_card_composition_across_locales(self) -> None:
        localized = {
            "02_whats_in_the_box.rst": ("TIP", "AC Charging Cable"),
            "p23_02_whats_in_the_box.rst": ("CONSEILS", "Câble de charge CA"),
            "p39_02_whats_in_the_box.rst": ("CONSEJOS", "Cable de carga de CA"),
        }

        for source_name, (tip_label, cable_label) in localized.items():
            with self.subTest(source=source_name):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                composition = soup.select_one("figure.hb-inbox-composition")
                self.assertIsNotNone(composition)
                cards = composition.select(".hb-inbox-grid > .hb-inbox-card") if composition else []
                self.assertEqual(3, len(cards))
                self.assertEqual(
                    ["1", "2", "3"],
                    [str(card["data-item-number"]) for card in cards],
                )
                self.assertEqual(3, len(composition.select(".hb-inbox-art")))
                self.assertIn(cable_label, cards[1].get_text(" ", strip=True))
                self.assertEqual(
                    tip_label,
                    composition.select_one(".hb-inbox-tip-label").get_text(" ", strip=True),
                )
                self.assertIsNotNone(composition.select_one(".hb-inbox-tip-body"))
                self.assertIsNone(composition.find("table"))
                self.assertIsNone(composition.find("colgroup"))

    def test_fcc_uses_live_two_column_pdf_composition_across_locales(self) -> None:
        localized = {
            "01_fcc.rst": "If this equipment does cause harmful interference",
            "p22_01_fcc.rst": "Si cet équipement trouble la réception",
            "p38_01_fcc.rst": "Si este aparato causa interferencias dañinas",
        }

        for source_name, right_column_start in localized.items():
            with self.subTest(source=source_name):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                composition = soup.select_one("figure.hb-fcc-composition")
                self.assertIsNotNone(composition)
                self.assertEqual(2, len(composition.select(".hb-fcc-column")))
                self.assertIn(
                    "fcc_mark.png",
                    str(composition.select_one(".hb-fcc-mark").get("src", ""))
                    if composition
                    else "",
                )
                right = composition.select_one(".hb-fcc-column-right") if composition else None
                self.assertIn(
                    right_column_start,
                    right.get_text(" ", strip=True) if right else "",
                )
                self.assertEqual(4, len(right.select("li")) if right else 0)
                heading = composition.find_previous("h1") if composition else None
                self.assertEqual("FCC", heading.get_text(" ", strip=True) if heading else "")

    def test_lcd_icons_use_searchable_four_column_pdf_grid(self) -> None:
        soup = BeautifulSoup(_web_fragment("lcd_icons_en.rst"), "html.parser")
        composition = soup.select_one("figure.hb-lcd-table-composition")

        self.assertIsNotNone(composition)
        table = composition.select_one("table.hb-lcd-icon-table") if composition else None
        self.assertIsNotNone(table)
        rows = table.select("tbody > tr") if table else []
        self.assertGreater(len(rows), 20)
        self.assertTrue(all(len(row.find_all("td", recursive=False)) == 4 for row in rows))
        first_lines = rows[0].select(".hb-lcd-description .line") if rows else []
        self.assertEqual(3, len(first_lines))
        self.assertEqual(
            ["On: Wi-Fi connected.", "Blink: Ready to connect to Wi-Fi.", "Off: Wi-Fi disconnected."],
            [line.get_text(" ", strip=True) for line in first_lines],
        )
        self.assertIsNone(table.find("col", attrs={"style": re.compile("width:")}))

    def test_troubleshooting_uses_searchable_pdf_grid_across_locales(self) -> None:
        expected_codes = [
            "F0",
            "F1",
            "F2",
            "F3",
            "F4",
            "F5",
            "F6",
            "F7",
            "F8",
            "F9",
            "FE",
        ]
        for source_name in (
            "troubleshooting_en.rst",
            "troubleshooting_fr.rst",
            "troubleshooting_es.rst",
        ):
            with self.subTest(source=source_name):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                composition = soup.select_one("figure.hb-troubleshooting-composition")
                self.assertIsNotNone(composition)
                table = (
                    composition.select_one("table.hb-troubleshooting-table")
                    if composition
                    else None
                )
                self.assertIsNotNone(table)
                self.assertEqual(2, len(table.select("colgroup > col")))
                self.assertIsNotNone(table.select_one("col.hb-troubleshooting-col-code"))
                self.assertIsNotNone(
                    table.select_one("col.hb-troubleshooting-col-measures")
                )
                self.assertEqual(2, len(table.select("thead > tr > th")))
                rows = table.select("tbody > tr") if table else []
                self.assertEqual(11, len(rows))
                self.assertEqual(
                    expected_codes,
                    [
                        row.select_one("td.hb-troubleshooting-code").get_text(
                            " ", strip=True
                        )
                        for row in rows
                    ],
                )
                self.assertEqual(
                    5,
                    len(rows[6].select("td.hb-troubleshooting-measures .line")),
                )
                self.assertEqual(
                    3,
                    len(rows[7].select("td.hb-troubleshooting-measures .line")),
                )
                self.assertIsNotNone(rows[7].select_one("sub"))
                self.assertIsNone(table.find("col", attrs={"style": re.compile("width:")}))
                self.assertFalse(
                    any(cell.get("style") for cell in table.select("th, td"))
                )

    def test_specifications_use_pdf_tables_without_duplicate_bullets(self) -> None:
        for source_name in ("spec_en.rst", "spec_fr.rst", "spec_es.rst"):
            with self.subTest(source=source_name):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                compositions = soup.select("figure.hb-spec-table-composition")
                self.assertEqual(4, len(compositions))
                references = soup.select("table.hb-spec-table sup.hb-spec-reference")
                self.assertEqual(2, len(references))
                self.assertEqual(["①", "①"], [node.get_text() for node in references])
                self.assertFalse(soup.select(".hb-spec-bullet"))
                headings = soup.find_all("h2")
                self.assertEqual(4, len(headings))
                self.assertTrue(all("●" not in heading.get_text() for heading in headings))
                for composition in compositions:
                    table = composition.select_one("table.hb-spec-table")
                    self.assertIsNotNone(table)
                    self.assertIsNotNone(table.select_one("col.hb-spec-col-label"))
                    self.assertIsNotNone(table.select_one("col.hb-spec-col-value"))
                    rows = table.select("tbody > tr")
                    self.assertTrue(rows)
                    self.assertFalse(table.select("thead"))
                    self.assertTrue(
                        all(
                            len(row.select("td.hb-spec-value")) == 1 for row in rows
                        )
                    )
                    labels = table.select("th.hb-spec-label[scope='row']")
                    self.assertTrue(labels)
                    self.assertEqual(
                        len(rows),
                        sum(int(label.get("rowspan", "1")) for label in labels),
                    )
                    self.assertFalse(
                        any(cell.get("style") for cell in table.select("th, td"))
                    )

    def test_meaning_symbols_use_independent_pdf_panels_across_locales(self) -> None:
        localized = {
            "symbols_en.rst": ("Heavy object", "This symbol indicates that the product shall"),
            "symbols_fr.rst": ("Objet lourd", "Ce symbole indique que le produit ne doit"),
            "symbols_es.rst": ("Objeto pesado", "Este símbolo indica que el producto no debe"),
        }

        for source_name, (heavy_object, weee_copy) in localized.items():
            with self.subTest(source=source_name):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                composition = soup.select_one("figure.hb-symbol-pair-composition")
                self.assertIsNotNone(composition)
                panels = composition.select(".hb-symbol-pair-grid > .hb-symbol-panel")
                self.assertEqual(2, len(panels))
                tables = composition.select("table.hb-symbol-panel-table")
                self.assertEqual(2, len(tables))
                self.assertTrue(
                    all(len(table.select("thead > tr > th")) == 2 for table in tables)
                )
                self.assertEqual(6, len(tables[0].select("tbody > tr")))
                self.assertEqual(5, len(tables[1].select("tbody > tr")))
                self.assertIn(heavy_object, tables[0].get_text(" ", strip=True))
                self.assertNotIn(heavy_object, tables[1].get_text(" ", strip=True))
                self.assertNotIn(weee_copy, tables[0].get_text(" ", strip=True))
                self.assertIn(weee_copy, tables[1].get_text(" ", strip=True))
                self.assertEqual(11, len(composition.select("img.hb-symbol-art")))
                self.assertTrue(
                    all(
                        not any(image.get(attribute) for attribute in ("style", "width", "height"))
                        for image in composition.select("img.hb-symbol-art")
                    )
                )
                self.assertFalse(
                    any(
                        len(row.find_all(["td", "th"], recursive=False)) == 4
                        for table in soup.find_all("table")
                        for row in table.find_all("tr")
                    )
                )

    def test_operation_panels_use_localized_pdf_composites_with_semantic_fallback(self) -> None:
        localized_sources = {
            "en": "05_operation_guide_placeholder.rst",
            "fr": "p26_05_operation_guide_placeholder.rst",
            "es": "p42_05_operation_guide_placeholder.rst",
        }
        operation_ids = (
            "main-power",
            "ac-output",
            "dc-usb-output",
            "energy-saving",
            "led-light",
        )

        for language, source_name in localized_sources.items():
            with self.subTest(language=language):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                figures = soup.select("figure.hb-operation-figure.hb-has-composite-art")
                self.assertEqual(5, len(figures))
                for operation_id in operation_ids:
                    figure = soup.select_one(
                        f'.hb-operation-figure[data-operation-id="{operation_id}"]'
                    )
                    self.assertIsNotNone(figure)
                    composite = figure.select_one(
                        ".hb-composite-stage .hb-composite-art"
                    ) if figure else None
                    self.assertIsNotNone(composite)
                    self.assertIn(
                        f"operation_{operation_id.replace('-', '_')}_{language}",
                        str(composite.get("src", "")) if composite else "",
                    )
                    self.assertIsNotNone(
                        figure.select_one(".hb-operation-stage .hb-operation-steps")
                        if figure
                        else None
                    )

                main_power = soup.select_one(
                    '.hb-operation-figure[data-operation-id="main-power"]'
                )
                self.assertEqual(
                    3,
                    len(
                        main_power.select(".hb-operation-supporting-copy > .line")
                        if main_power
                        else []
                    ),
                )
                led_light = soup.select_one(
                    '.hb-operation-figure[data-operation-id="led-light"]'
                )
                self.assertIsNotNone(
                    led_light.select_one(".hb-operation-prerequisite")
                    if led_light
                    else None
                )

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
                supporting_copy = (
                    figure.select_one(".hb-operation-supporting-copy") if figure else None
                )
                self.assertIsNotNone(supporting_copy)
                self.assertIn(
                    standby_copy,
                    supporting_copy.get_text(" ", strip=True) if supporting_copy else "",
                )
                self.assertEqual(
                    3,
                    len(
                        supporting_copy.find_all(class_="line", recursive=False)
                        if supporting_copy
                        else []
                    ),
                )
                self.assertIn(standby_copy, transformed)

        self.assertEqual(ids_by_locale["en"], ids_by_locale["fr"])
        self.assertEqual(ids_by_locale["en"], ids_by_locale["es"])

    def test_charging_car_uses_localized_pdf_panel_without_baking_in_heading(self) -> None:
        localized = {
            "en": ("08_charging_methods.rst", "Vehicle", "CAUTION"),
            "fr": ("p29_08_charging_methods.rst", "Véhicule", "ATTENTION"),
            "es": ("p45_08_charging_methods.rst", "Vehículo", "PRECAUCIÓN"),
        }

        for language, (source_name, vehicle_label, caution_label) in localized.items():
            with self.subTest(language=language):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                figure = soup.select_one(
                    'figure.hb-reference-figure[data-reference-id="charging-car"]'
                )
                self.assertIsNotNone(figure)
                self.assertIn(
                    f"charging_car_{language}",
                    str(figure.select_one(".hb-composite-art").get("src", ""))
                    if figure
                    else "",
                )
                semantic = figure.select_one(".hb-reference-semantic") if figure else None
                self.assertIsNotNone(semantic)
                self.assertIn(
                    vehicle_label,
                    semantic.get_text(" ", strip=True) if semantic else "",
                )
                self.assertEqual(
                    2,
                    len(semantic.select(".hb-reference-labels > .line"))
                    if semantic
                    else 0,
                )
                heading = figure.find_previous("h2") if figure else None
                self.assertIsNotNone(heading)
                self.assertNotIn(
                    heading.get_text(" ", strip=True) if heading else "",
                    str(figure),
                )
                following_callout = figure.find_next("table") if figure else None
                self.assertIn(
                    caution_label,
                    following_callout.get_text(" ", strip=True)
                    if following_callout
                    else "",
                )

    def test_app_add_device_uses_shared_art_with_live_localized_labels(self) -> None:
        localized = {
            "en": (
                "12_app_setup_placeholder.rst",
                ["Main Power Button", "DC/USB Power Button", "AC Power Button"],
            ),
            "fr": (
                "p34_12_app_setup_placeholder.rst",
                ["Bouton POWER", "Bouton d’alimentation CC/USB", "Bouton d’alimentation CA"],
            ),
            "es": (
                "p50_12_app_setup_placeholder.rst",
                ["Botón de encendido", "Botón de energía CC / USB", "Botón Power CA"],
            ),
        }
        artwork_by_locale: dict[str, tuple[str, str]] = {}

        for language, (source_name, expected_labels) in localized.items():
            with self.subTest(language=language):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                figure = soup.select_one(
                    'figure.hb-app-add-device-composition[data-reference-id="app-add-device"]'
                )
                self.assertIsNotNone(figure)
                phone_art = figure.select_one(".hb-app-add-device-phone-art") if figure else None
                control_art = figure.select_one(".hb-app-add-device-control-art") if figure else None
                self.assertIsNotNone(phone_art)
                self.assertIsNotNone(control_art)
                artwork_by_locale[language] = (
                    str(phone_art.get("src", "")) if phone_art else "",
                    str(control_art.get("src", "")) if control_art else "",
                )
                self.assertEqual("asset:app/add_device", artwork_by_locale[language][0])
                self.assertIn("app_control_panel", artwork_by_locale[language][1])
                self.assertNotIn("front_controls", artwork_by_locale[language][1])
                self.assertEqual(
                    expected_labels,
                    [
                        label.get_text(" ", strip=True)
                        for label in figure.select(".hb-app-add-device-live-label")
                    ]
                    if figure
                    else [],
                )
                self.assertEqual(
                    ["2.1", "2.2"],
                    [item.get_text(strip=True) for item in figure.select(".hb-reference-caption")]
                    if figure
                    else [],
                )
                self.assertIsNone(figure.select_one(".hb-composite-art") if figure else None)
                self.assertIsNone(figure.select_one(".hb-reference-semantic") if figure else None)
                preceding_copy = figure.find_previous("p") if figure else None
                self.assertTrue(
                    preceding_copy.get_text(" ", strip=True).startswith("2.2")
                    if preceding_copy
                    else False
                )
                following_block = figure.find_next_sibling() if figure else None
                following_copy = (
                    following_block.find(class_="line")
                    if isinstance(following_block, Tag)
                    else None
                )
                self.assertTrue(
                    following_copy.get_text(" ", strip=True).startswith("2.3")
                    if following_copy
                    else False
                )
        self.assertEqual(artwork_by_locale["en"], artwork_by_locale["fr"])
        self.assertEqual(artwork_by_locale["en"], artwork_by_locale["es"])

    def test_app_connect_result_uses_shared_step_caption_rule(self) -> None:
        localized = (
            "12_app_setup_placeholder.rst",
            "p34_12_app_setup_placeholder.rst",
            "p50_12_app_setup_placeholder.rst",
        )
        for source_name in localized:
            with self.subTest(source=source_name):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                figure = soup.select_one(
                    'figure.hb-reference-figure[data-reference-id="app-connect-result"]'
                )
                self.assertIsNotNone(figure)
                self.assertIn(
                    "connect_result_je1000f_us",
                    str(figure.select_one(".hb-composite-art").get("src", ""))
                    if figure
                    else "",
                )
                captions = figure.select(".hb-reference-caption") if figure else []
                self.assertEqual(["2.3", "2.4", "2.5"], [item.get_text(strip=True) for item in captions])
                self.assertEqual(
                    "phone-triple",
                    figure.select_one("figcaption").get("data-caption-layout")
                    if figure and figure.select_one("figcaption")
                    else None,
                )
                semantic = figure.select_one(".hb-reference-semantic") if figure else None
                self.assertIsNotNone(semantic)
                semantic_alt = (
                    semantic.select_one("img").get("alt", "")
                    if semantic and semantic.select_one("img")
                    else ""
                )
                self.assertTrue(semantic_alt)
                following_copy = figure.find_next_sibling() if figure else None
                self.assertTrue(
                    following_copy.get_text(" ", strip=True)
                    if isinstance(following_copy, Tag)
                    else ""
                )

    def test_app_add_device_renders_localized_inline_plus_control(self) -> None:
        localized = {
            "12_app_setup_placeholder.rst": (
                "button",
                "Add device",
                "2.1 Click the + button to add your device.",
            ),
            "p34_12_app_setup_placeholder.rst": (
                "bouton",
                "Ajouter un appareil",
                "2.1 Cliquez sur le bouton + pour ajouter un appareil.",
            ),
            "p50_12_app_setup_placeholder.rst": (
                "botón",
                "Añadir dispositivo",
                "2.1 Haga clic en el botón + .",
            ),
        }

        for source_name, (button_term, removed_label, expected_copy) in localized.items():
            with self.subTest(source=source_name):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                icon = soup.select_one(".hb-inline-add-device-icon")
                self.assertIsNotNone(icon)
                self.assertEqual("+", icon.get_text(strip=True) if icon else "")
                self.assertEqual(removed_label, icon.get("aria-label") if icon else None)
                paragraph = icon.find_parent("p") if icon else None
                self.assertTrue(
                    paragraph.get_text(" ", strip=True).startswith("2.1")
                    if paragraph
                    else False
                )
                visible_copy = paragraph.get_text(" ", strip=True) if paragraph else ""
                self.assertIn(button_term, visible_copy)
                self.assertIn("+", visible_copy)
                self.assertNotIn(removed_label, visible_copy)
                self.assertEqual(expected_copy, visible_copy)
                self.assertIsNone(paragraph.find("strong") if paragraph else None)

    def test_app_download_uses_two_live_copy_columns_across_locales(self) -> None:
        localized = {
            "12_app_setup_placeholder.rst": (
                "Search for \"Jackery\"",
                "Alternatively, scan the QR code",
            ),
            "p34_12_app_setup_placeholder.rst": (
                "Recherchez « Jackery »",
                "Vous pouvez également scanner",
            ),
            "p50_12_app_setup_placeholder.rst": (
                "Buscar \"Jackery\"",
                "Alternativamente, escanee el código QR",
            ),
        }

        artwork_by_locale: dict[str, tuple[str, str]] = {}
        for source_name, expected_columns in localized.items():
            with self.subTest(source=source_name):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")
                composition = soup.select_one("figure.hb-app-download-composition")
                self.assertIsNotNone(composition)
                self.assertEqual(2, len(composition.select(".hb-app-download-column")))
                self.assertEqual(2, len(composition.select("img.hb-app-download-art")))
                store_art = composition.select_one(".hb-app-download-art-store")
                qr_art = composition.select_one(".hb-app-download-art-qr")
                self.assertIsNotNone(store_art)
                self.assertIsNotNone(qr_art)
                artwork_by_locale[source_name] = (
                    str(store_art.get("src", "")) if store_art else "",
                    str(qr_art.get("src", "")) if qr_art else "",
                )
                self.assertNotEqual(*artwork_by_locale[source_name])
                self.assertIsNotNone(composition.select_one(".hb-app-download-semantic-art"))
                columns = composition.select(".hb-app-download-copy") if composition else []
                self.assertEqual(2, len(columns))
                for expected, column in zip(expected_columns, columns, strict=True):
                    self.assertIn(expected, column.get_text(" ", strip=True))
                self.assertIsNone(composition.find("h2"))
                heading = composition.find_previous("h2") if composition else None
                self.assertIsNotNone(heading)
                section = composition.find_parent("section") if composition else None
                self.assertEqual(0, len(section.find_all("p", recursive=False)) if section else -1)
        paths = list(artwork_by_locale.values())
        self.assertTrue(paths)
        self.assertTrue(all(pair == paths[0] for pair in paths[1:]))

    def test_warranty_uses_live_pdf_derived_cards_across_locales(self) -> None:
        localized = {
            "11_warranty.rst": (
                ["YEARS", "YEARS"],
                ["Standard Warranty", "Extended Warranty"],
            ),
            "p33_11_warranty.rst": (
                ["ANS", "ANS"],
                ["Garantie standard", "Garantie prolongée"],
            ),
            "p49_11_warranty.rst": (
                ["AÑOS", "AÑOS"],
                ["Garantía Estándar", "Garantía extendida"],
            ),
        }

        for source_name, (expected_units, expected_labels) in localized.items():
            with self.subTest(source=source_name):
                soup = BeautifulSoup(_web_fragment(source_name), "html.parser")

                self.assertEqual(1, len(soup.select("figure.hb-warranty-intro-composition")))
                self.assertEqual(1, len(soup.select(".hb-warranty-intro-panel")))
                self.assertEqual(1, len(soup.select(".hb-warranty-local-note")))
                self.assertEqual(5, len(soup.select("figure.hb-warranty-card")))
                self.assertEqual(1, len(soup.select("figure.hb-warranty-period-card")))
                self.assertEqual(6, len(soup.find_all("h2")))
                self.assertEqual(
                    ["3", "2"],
                    [node.get_text(" ", strip=True) for node in soup.select(".hb-warranty-year-badge")],
                )
                self.assertEqual(
                    expected_units,
                    [node.get_text(" ", strip=True) for node in soup.select(".hb-warranty-years-unit")],
                )
                self.assertEqual(
                    expected_labels,
                    [node.get_text(" ", strip=True) for node in soup.select(".hb-warranty-period-label")],
                )
                self.assertTrue(
                    all(node.get_text(" ", strip=True) for node in soup.select(".hb-warranty-period-copy"))
                )
                self.assertEqual(4, len(soup.select("figure.hb-warranty-card li")))
                email_link = soup.find("a", href="mailto:hello@jackery.com")
                self.assertIsNotNone(email_link)
                self.assertEqual("hello@jackery.com", email_link.get_text(strip=True))
                self.assertEqual(0, len(soup.find_all("table")))
                self.assertEqual(0, len(soup.find_all("colgroup")))
                self.assertNotIn("width: 50%", str(soup))

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
