from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from tools.word_bundle import derive_word_title, render_safety_word_html, resolve_reference_doc
from tools.word_bundle_html import (
    _convert_rst_fragment_to_html,
    _inject_img_dimensions,
    _rewrite_word_friendly_fragment,
)


class TestWordBundle(unittest.TestCase):
    def test_inject_img_dimensions_should_add_proportional_height_for_local_png(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image_path = root / "demo.png"
            image_path.write_bytes(
                b"\x89PNG\r\n\x1a\n"
                + b"\x00\x00\x00\rIHDR"
                + struct.pack(">II", 620, 486)
            )

            html = f'<img src="{image_path.resolve().as_uri()}" style="width: 40px;" />'
            out = _inject_img_dimensions(html)

            self.assertIn('width="40"', out)
            self.assertIn('height="31"', out)

    def test_resolve_reference_doc_supports_glob(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "EN-HomePower 2000 Plus User Manual.docx"
            target.write_text("demo", encoding="utf-8")

            resolved = resolve_reference_doc("EN-HomePower*.docx", root=root)
            self.assertEqual(target, resolved)

    def test_derive_word_title_prefers_configured_title(self) -> None:
        title = derive_word_title(
            {"word_title": "|PRODUCT_NAME| Guide"},
            None,
            {"PRODUCT_NAME": "HomePower 2000 Plus"},
            {},
        )
        self.assertEqual("HomePower 2000 Plus Guide", title)

    def test_render_safety_word_html_outputs_headings_and_lists(self) -> None:
        html = render_safety_word_html(
            {
                "title_main": "IMPORTANT SAFETY INFORMATION",
                "warning_title": "WARNING",
                "title_operating": "OPERATING INSTRUCTIONS",
                "lead_top": "Always follow these precautions.",
                "save_title": "SAVE THESE INSTRUCTIONS",
                "top_items": ["Top item"],
                "bottom_items": ["Bottom item"],
            }
        )
        self.assertIn("<h1>IMPORTANT SAFETY INFORMATION</h1>", html)
        self.assertIn("<h2>OPERATING INSTRUCTIONS</h2>", html)
        self.assertIn("<li>Top item</li>", html)

    def test_convert_rst_fragment_to_html_should_convert_safety_two_column_blocks(self) -> None:
        rst = """
.. only:: html

   .. raw:: html

      <div class="hb-safety">
        <h1 class="hb-h1-pill">IMPORTANT SAFETY INFORMATION</h1>
        <div class="hb-warning-box">
          <div class="hb-warning-row">
            <div class="hb-warning-text">Risk of fire.</div>
          </div>
        </div>
        <div class="hb-two-col">
          <p class="hb-lead">Always follow these basic precautions.</p>
          <ul class="hb-list">
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
            <li>Item 4</li>
          </ul>
        </div>
      </div>
"""
        with tempfile.TemporaryDirectory() as td:
            html = _convert_rst_fragment_to_html(
                rst,
                Path("safety_en.rst"),
                Path(td),
            )

        self.assertIn("manual-callout-table", html)
        self.assertIn("manual-two-col-table", html)
        self.assertIn("Always follow these basic precautions.", html)
        self.assertIn("Item 4", html)

    def test_convert_rst_fragment_to_html_should_render_spec_pages_via_word_html(self) -> None:
        rst = """
.. only:: html

   .. raw:: html

      <h1 class="hb-h1-pill">SPECIFICATIONS</h1>

   .. raw:: html

      <h2 class="hb-spec-section">● General Info</h2>

   .. list-table::
      :widths: 33 67
      :header-rows: 0

      * - Product Name
        - Jackery Explorer 1000
      * - Model No.
        - JE-1000F
"""
        with tempfile.TemporaryDirectory() as td:
            html = _convert_rst_fragment_to_html(
                rst,
                Path("spec_en.rst"),
                Path(td),
            )

        self.assertIn('<section class="manual-section spec-section">', html)
        self.assertIn("<h1>SPECIFICATIONS</h1>", html)
        self.assertIn('class="hb-spec-section"', html)
        self.assertIn('class="hb-spec-bullet"', html)
        self.assertIn("GENERAL INFO", html)
        self.assertIn('class="manual-table manual-spec-table"', html)
        self.assertIn("JE-1000F", html)

    def test_convert_rst_fragment_to_html_should_keep_preface_important_as_bold_paragraph(self) -> None:
        rst = """
**IMPORTANT**

Congratulations on your new manual.
"""
        with tempfile.TemporaryDirectory() as td:
            html = _convert_rst_fragment_to_html(
                rst,
                Path("00_preface.rst"),
                Path(td),
            )

        self.assertIn("<p><strong>IMPORTANT</strong></p>", html)
        self.assertNotIn("<h1>IMPORTANT</h1>", html)

    def test_rewrite_word_friendly_fragment_should_convert_cover_and_warning_box(self) -> None:
        fragment = (
            '<section class="manual-cover"><div class="cover-title">Demo Manual</div></section>'
            '<div class="hb-warning-box"><div class="hb-warning-row"><div class="hb-warning-lockup">!</div>'
            '<div class="hb-warning-text">Risk of fire.</div></div></div>'
        )

        out = _rewrite_word_friendly_fragment(fragment)

        self.assertIn("<h1>Demo Manual</h1>", out)
        self.assertIn("manual-callout-table", out)
        self.assertIn("<strong>WARNING</strong>", out)
        self.assertIn("Risk of fire.", out)

    def test_rewrite_word_friendly_fragment_should_convert_alert_paragraphs_into_tables(self) -> None:
        fragment = (
            "<p><strong>CAUTION</strong></p>"
            "<ul><li>Line 1</li><li>Line 2</li></ul>"
            "<h2>Next Section</h2>"
        )

        out = _rewrite_word_friendly_fragment(fragment)

        self.assertIn("manual-callout-table", out)
        self.assertIn("<strong>CAUTION</strong>", out)
        self.assertIn("<li>Line 1</li>", out)
        self.assertIn("<h2>Next Section</h2>", out)

    def test_rewrite_word_friendly_fragment_should_convert_alert_headings_into_tables(self) -> None:
        fragment = "<h2>DANGER</h2><ul><li>Indoor use only.</li></ul>"

        out = _rewrite_word_friendly_fragment(fragment)

        self.assertIn("manual-callout-table", out)
        self.assertIn("<strong>DANGER</strong>", out)
        self.assertIn("Indoor use only.", out)

    def test_rewrite_word_friendly_fragment_should_convert_nested_alert_blocks(self) -> None:
        fragment = (
            '<div class="hb-safety">'
            '<div class="hb-warning-box"><div class="hb-warning-text">Risk of fire.</div></div>'
            '<section id="danger"><h2>DANGER</h2><ul><li>Indoor use only.</li></ul></section>'
            "</div>"
        )

        out = _rewrite_word_friendly_fragment(fragment)

        self.assertEqual(2, out.count("manual-callout-table"))
        self.assertIn("Risk of fire.", out)
        self.assertIn("Indoor use only.", out)

    def test_rewrite_word_friendly_fragment_should_keep_following_strong_paragraph_outside_alert(self) -> None:
        fragment = (
            "<section>"
            "<p><strong>CAUTION</strong></p>"
            "<p>Use the official cable.</p>"
            "<p><strong>Emergency Charging Mode</strong></p>"
            "<p>Charge faster when needed.</p>"
            "</section>"
        )

        out = _rewrite_word_friendly_fragment(fragment)

        self.assertIn("manual-callout-table", out)
        self.assertIn("<strong>Emergency Charging Mode</strong>", out)
        self.assertIn("Charge faster when needed.", out)
        self.assertLess(
            out.index("manual-callout-table"),
            out.index("<strong>Emergency Charging Mode</strong>"),
        )

    def test_rewrite_word_friendly_fragment_should_stop_after_list_body(self) -> None:
        fragment = (
            "<section>"
            "<p><strong>NOTE</strong></p>"
            "<p>Choose a 2.4 GHz network.</p>"
            "<ul><li>5 GHz is not supported.</li></ul>"
            "<p>After setup, the Wi-Fi icon stays on.</p>"
            "</section>"
        )

        out = _rewrite_word_friendly_fragment(fragment)

        self.assertIn("manual-callout-table", out)
        self.assertIn("After setup, the Wi-Fi icon stays on.", out)
        self.assertLess(
            out.index("</table>"),
            out.index("After setup, the Wi-Fi icon stays on."),
        )

    def test_rewrite_word_friendly_fragment_should_nest_known_safety_subitems(self) -> None:
        fragment = (
            '<div class="hb-two-col">'
            '<ul class="hb-list">'
            '<li>Do not charge the battery in extremely hot or cold environments and strictly adhere to the product\'s specified operating temperature ranges:</li>'
            '<li>Charging temperature: -4°F to 113°F (-20°C to 45°C)</li>'
            '<li>Discharging temperature: -4°F to 113°F (-20°C to 45°C)</li>'
            '<li>To ensure proper air circulation, keep the product vents uncovered. The area where the product is used must have adequate airflow in a cool, dry environment to prevent overheating.</li>'
            '<li>Charging in damp or poorly ventilated spaces may cause safety hazards.</li>'
            '<li>Water can cause short circuits or damage to the charger, leading to safety risks.</li>'
            '<li>Unplug the power cord from a power outlet during a storm.</li>'
            '</ul>'
            '</div>'
        )

        out = _rewrite_word_friendly_fragment(fragment)

        self.assertEqual(2, out.count('class="hb-sublist"'))
        self.assertIn(
            "Do not charge the battery in extremely hot or cold environments and strictly adhere to the product's specified operating temperature ranges:<ul class=\"hb-sublist\">",
            out,
        )
        self.assertIn(
            "To ensure proper air circulation, keep the product vents uncovered. The area where the product is used must have adequate airflow in a cool, dry environment to prevent overheating.<ul class=\"hb-sublist\">",
            out,
        )

    def test_rewrite_word_friendly_fragment_should_balance_safety_columns_by_content_weight(self) -> None:
        long_item = " ".join(["Very long safety item."] * 30)
        fragment = (
            '<div class="hb-two-col">'
            '<p class="hb-lead">Always follow these basic precautions.</p>'
            '<ul class="hb-list">'
            '<li>Short item 1.</li>'
            '<li>Short item 2.</li>'
            '<li>Short item 3.</li>'
            f'<li>{long_item}</li>'
            '<li>Short item 4.</li>'
            '</ul>'
            '</div>'
        )

        out = _rewrite_word_friendly_fragment(fragment)

        self.assertIn("manual-two-col-table", out)
        right_col_start = out.index("</td><td")
        self.assertGreater(out.index(long_item), right_col_start)

    def test_rewrite_word_friendly_fragment_should_replace_signal_word_cells_with_banners(self) -> None:
        fragment = (
            "<h1>MEANING OF SYMBOLS</h1>"
            "<table><thead><tr><th><p>Symbol</p></th><th><p>Meaning</p></th></tr></thead>"
            "<tbody>"
            "<tr><td><img src=\"old-warning.png\" /><p><strong>WARNING</strong></p></td><td><p>Warn</p></td></tr>"
            "<tr><td><img src=\"old-caution.png\" /><p><strong>CAUTION</strong></p></td><td><p>Caution</p></td></tr>"
            "<tr><td><img src=\"old-note.png\" /><p><strong>NOTE</strong></p></td><td><p>Note</p></td></tr>"
            "<tr><td><img src=\"old-tip.png\" /><p><strong>TIP</strong></p></td><td><p>Tip</p></td></tr>"
            "</tbody></table>"
        )

        out = _rewrite_word_friendly_fragment(fragment)

        self.assertIn("warning_bar.png", out)
        self.assertIn("caution_bar.png", out)
        self.assertIn("note_bar.png", out)
        self.assertIn("tip_bar.png", out)
        self.assertNotIn("old-warning.png", out)
        self.assertNotIn("<strong>WARNING</strong>", out)


if __name__ == "__main__":
    unittest.main()
