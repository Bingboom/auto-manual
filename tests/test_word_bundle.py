from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from tools.word_bundle import derive_word_title, render_safety_word_html, render_spec_word_html, resolve_reference_doc
from tools.word_bundle_html import (
    _build_word_only_tags,
    _convert_rst_fragment_to_html,
    _inject_img_dimensions,
    _rewrite_word_friendly_fragment,
)
from tools.word_bundle_html_rewrite import _extract_spec_word_data


class TestWordBundle(unittest.TestCase):
    def _write_alert_labels_symbols_blocks(self, root: Path) -> Path:
        path = root / "symbols_blocks.csv"
        path.write_text(
            "\n".join(
                [
                    "page_id,symbol_key,block_type,order,Region,Model,Source_lang,Is_Latest,label_en,aliases_en,label_fr,aliases_es,aliases_de,aliases_it,aliases_uk,aliases_jp,aliases_zh",
                    "symbols,warning,signal_row,1,all,,en,TRUE,WARNING,,AVERTISSEMENT,ADVERTENCIA,WARNUNG,AVVERTENZA,ПОПЕРЕДЖЕННЯ,警告,警告",
                    "symbols,danger,alert_label_row,2,all,,en,TRUE,DANGER,,DANGER,PELIGRO,GEFAHR,PERICOLO,НЕБЕЗПЕКА,危険,危险",
                    "symbols,caution,signal_row,3,all,,en,TRUE,CAUTION,,ATTENTION,PRECAUCIÓN,VORSICHT,ATTENZIONE,УВАГА,ご注意,注意",
                    "symbols,note,signal_row,4,all,,en,TRUE,NOTE,,REMARQUE,NOTA,HINWEIS,NOTA,ПРИМІТКА,備考,提示;说明;备注;備註",
                    "symbols,tips,signal_row,5,all,,en,TRUE,TIP,TIPS,CONSEIL;CONSEILS,CONSEJO;CONSEJOS,TIPP,SUGGERIMENTO,ПОРАДИ,,",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return path

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

    def test_render_spec_word_html_should_reject_ambiguous_trailer_order(self) -> None:
        with self.assertRaisesRegex(ValueError, "spec trailer order must come from the upstream HTML fragment"):
            render_spec_word_html(
                {
                    "title_main": "SPECIFICATIONS",
                    "sections": [
                        {
                            "title": "Environmental Operating Temperature",
                            "rows": [
                                ("Charging Temperature", "-4°F to 113°F / -20°C to 45°C"),
                                ("Discharging Temperature", "-4°F to 113°F / -20°C to 45°C"),
                            ],
                        }
                    ],
                    "notes": ["※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."],
                    "footnotes": [
                        "① The product can charge the battery from the AC wall outlet while delivering power through the AC output ports."
                    ],
                }
            )

    def test_convert_rst_fragment_to_html_should_keep_spec_trailer_order_from_html(self) -> None:
        rst = """
.. only:: html

   .. raw:: html

      <h1 class="hb-h1-pill">SPECIFICATIONS</h1>

   .. raw:: html

      <h2 class="hb-spec-section"><span class="hb-spec-bullet" aria-hidden="true">&#9679;</span><span class="hb-spec-section-text">ENVIRONMENTAL OPERATING TEMPERATURE</span></h2>
      <table class="hb-spec-table">
        <tbody>
          <tr>
            <th scope="row" class="hb-spec-label">Charging Temperature</th>
            <td class="hb-spec-value">-4°F to 113°F / -20°C to 45°C</td>
          </tr>
        </tbody>
      </table>
      <p class="hb-spec-note" data-spec-trailer-kind="note">※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.</p>
      <p class="hb-spec-footnote" data-spec-trailer-kind="footnote">① The product can charge the battery from the AC wall outlet while delivering power through the AC output ports.</p>
"""
        with tempfile.TemporaryDirectory() as td:
            html = _convert_rst_fragment_to_html(
                rst,
                Path("spec_en.rst"),
                Path(td),
            )

        self.assertIn('class="manual-spec-trailer-spacer"', html)
        self.assertIn(
            '<p class="manual-spec-note">※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.</p>',
            html,
        )
        self.assertIn(
            '<p class="manual-spec-footnote">① The product can charge the battery from the AC wall outlet while delivering power through the AC output ports.</p>',
            html,
        )
        self.assertLess(
            html.find("※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."),
            html.find(
                "① The product can charge the battery from the AC wall outlet while delivering power through the AC output ports."
            ),
        )

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

    def test_convert_rst_fragment_to_html_should_keep_troubleshooting_steps_plain_in_tables(self) -> None:
        rst = """
TROUBLESHOOTING
===============

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Error Code
     - Corrective Measures
   * - F6
     - | 1. Wait for the grid to normalize.
       | 2. Check the air intake and exhaust vents.
"""
        with tempfile.TemporaryDirectory() as td:
            html = _convert_rst_fragment_to_html(
                rst,
                Path("10_troubleshooting.rst"),
                Path(td),
            )

        self.assertIn("1. Wait for the grid to normalize.", html)
        self.assertIn("2. Check the air intake and exhaust vents.", html)
        self.assertIn("line-block", html)
        self.assertNotIn("<ol", html)

    def test_convert_rst_fragment_to_html_should_render_spec_pages_via_word_html(self) -> None:
        rst = """
.. only:: html

   .. raw:: html

      <h1 class="hb-h1-pill">SPECIFICATIONS</h1>

   .. raw:: html

      <h2 class="hb-spec-section">鈼?General Info</h2>

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

    def test_extract_spec_word_data_should_preserve_multiline_spec_values(self) -> None:
        fragment = (
            "<h1>SPECIFICATIONS</h1>"
            "<h2>● INPUT PORTS</h2>"
            "<table><tbody>"
            "<tr>"
            "<td>1 × AC Input</td>"
            "<td>Charge Mode: 100V-120V~60Hz, 15A Max<br/>Bypass Mode①: 100V-120V~60Hz, 12A Max</td>"
            "</tr>"
            "</tbody></table>"
        )

        data = _extract_spec_word_data(fragment)

        self.assertIsNotNone(data)
        assert data is not None
        self.assertEqual(
            "Charge Mode: 100V-120V~60Hz, 15A Max\nBypass Mode①: 100V-120V~60Hz, 12A Max",
            data["sections"][0]["rows"][0][1],
        )

    def test_extract_spec_word_data_should_preserve_trailer_kind_from_html_metadata(self) -> None:
        fragment = (
            "<h1>SPECIFICATIONS</h1>"
            "<h2>● ENVIRONMENTAL OPERATING TEMPERATURE</h2>"
            "<table><tbody>"
            "<tr><td>Charging Temperature</td><td>-4°F to 113°F / -20°C to 45°C</td></tr>"
            "</tbody></table>"
            '<p class="hb-spec-note" data-spec-trailer-kind="note">※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.</p>'
            '<p class="hb-spec-footnote" data-spec-trailer-kind="footnote">① The product can charge the battery from the AC wall outlet while delivering power through the AC output ports.</p>'
        )

        data = _extract_spec_word_data(fragment)

        self.assertIsNotNone(data)
        assert data is not None
        self.assertEqual(
            [
                ("note", "※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."),
                (
                    "footnote",
                    "① The product can charge the battery from the AC wall outlet while delivering power through the AC output ports.",
                ),
            ],
            data["trailers"],
        )
        self.assertEqual(
            ["※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."],
            data["notes"],
        )
        self.assertEqual(
            ["① The product can charge the battery from the AC wall outlet while delivering power through the AC output ports."],
            data["footnotes"],
        )

    def test_convert_rst_fragment_to_html_should_split_multiline_spec_values_into_rowspan_rows(self) -> None:
        rst = """
.. only:: html

   .. raw:: html

      <h1 class="hb-h1-pill">SPECIFICATIONS</h1>

   .. raw:: html

      <h2 class="hb-spec-section"><span class="hb-spec-bullet" aria-hidden="true">&#9679;</span><span class="hb-spec-section-text">INPUT PORTS</span></h2>
      <table class="hb-spec-table">
        <tbody>
          <tr>
            <th scope="row" class="hb-spec-label">1 × AC Input</th>
            <td class="hb-spec-value">Charge Mode: 100V-120V~60Hz, 15A Max<br/>Bypass Mode①: 100V-120V~60Hz, 12A Max</td>
          </tr>
          <tr>
            <th scope="row" class="hb-spec-label">2 × DC8020 Ports</th>
            <td class="hb-spec-value">11V-16V⎓8A Max, Double to 8A Max<br/>16V-60V⎓12A Max, Double to 21A / 400W Max</td>
          </tr>
        </tbody>
      </table>
"""
        with tempfile.TemporaryDirectory() as td:
            html = _convert_rst_fragment_to_html(
                rst,
                Path("spec_en.rst"),
                Path(td),
            )

        self.assertIn('rowspan="2"', html)
        self.assertIn("Charge Mode: 100V-120V~60Hz, 15A Max", html)
        self.assertIn("Bypass Mode①: 100V-120V~60Hz, 12A Max", html)
        self.assertIn("16V-60V⎓12A Max, Double to 21A / 400W Max", html)
        self.assertNotIn("MaxBypass", html)
        self.assertNotIn("Max16V-60V", html)

    def test_build_word_only_tags_should_normalize_target_context(self) -> None:
        tags = _build_word_only_tags(model="JE-2000E", region="US", lang="en")

        self.assertIn("html", tags)
        self.assertIn("model_je_2000e", tags)
        self.assertIn("region_us", tags)
        self.assertIn("lang_en", tags)

    def test_convert_rst_fragment_to_html_should_filter_only_blocks_by_tags(self) -> None:
        rst = """
.. only:: model_je_2000e and region_us and lang_en

   .. raw:: html

      <p>Keep model/region/lang.</p>

.. only:: model_je_1000f

   .. raw:: html

      <p>Drop model mismatch.</p>

.. only:: model_je_1000f or region_us

   .. raw:: html

      <p>Keep or expression.</p>

.. only:: not model_je_1000f and region_us

   .. raw:: html

      <p>Keep not expression.</p>

.. only:: html

   .. raw:: html

      <p>Keep html block.</p>
"""
        with tempfile.TemporaryDirectory() as td:
            html = _convert_rst_fragment_to_html(
                rst,
                Path("charging.rst"),
                Path(td),
                active_tags=_build_word_only_tags(model="JE-2000E", region="US", lang="en"),
            )

        self.assertIn("Keep model/region/lang.", html)
        self.assertIn("Keep or expression.", html)
        self.assertIn("Keep not expression.", html)
        self.assertIn("Keep html block.", html)
        self.assertNotIn("Drop model mismatch.", html)

    def test_convert_rst_fragment_to_html_should_keep_heading_after_only_block(self) -> None:
        rst = """
WARRANTY
========

.. only:: region_us

   Repair or replacement
   ---------------------

   The repaired product assumes the remaining warranty of the original date of purchase.

.. only:: region_eu

   Exchange
   --------

   A replacement product assumes the remaining warranty of the original product.

Limited to Original Consumer Buyer
----------------------------------

The warranty is limited to the original consumer purchaser.
"""
        with tempfile.TemporaryDirectory() as td:
            html = _convert_rst_fragment_to_html(
                rst,
                Path("11_warranty.rst"),
                Path(td),
                active_tags=_build_word_only_tags(model="JE-1000F", region="US", lang="en"),
            )

        # The section title following the kept only-block must stay a heading,
        # not get absorbed into the block's last paragraph with its underline
        # leaking through as literal dashes.
        self.assertIn("<h2>Limited to Original Consumer Buyer</h2>", html)
        self.assertNotIn("----", html)
        self.assertIn("Repair or replacement", html)
        self.assertNotIn("A replacement product", html)
        self.assertLess(
            html.index("original date of purchase."),
            html.index("Limited to Original Consumer Buyer"),
        )

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

        with tempfile.TemporaryDirectory() as td:
            symbols_blocks = self._write_alert_labels_symbols_blocks(Path(td))
            out = _rewrite_word_friendly_fragment(fragment, symbols_blocks_csv=symbols_blocks)

        self.assertIn("<h1>Demo Manual</h1>", out)
        self.assertIn("manual-callout-table", out)
        self.assertIn("<strong>!</strong>", out)
        self.assertNotIn("<strong>WARNING</strong>", out)
        self.assertIn("Risk of fire.", out)

    def test_rewrite_word_friendly_fragment_should_not_synthesize_french_warning_box_label(self) -> None:
        fragment = (
            '<div class="hb-warning-box"><div class="hb-warning-row">'
            '<div class="hb-warning-text">Consultez les consignes de sécurité avant utilisation.</div>'
            '</div></div>'
        )

        out = _rewrite_word_friendly_fragment(fragment, lang="fr")

        self.assertNotIn("<strong>AVERTISSEMENT</strong>", out)
        self.assertNotIn("<strong>WARNING</strong>", out)
        self.assertIn("Consultez les consignes de sécurité avant utilisation.", out)

    def test_rewrite_word_friendly_fragment_should_preserve_source_warning_lockup(self) -> None:
        fragment = (
            '<div class="hb-warning-box"><div class="hb-warning-row">'
            '<div class="hb-warning-lockup">ADVERTENCIA</div>'
            '<div class="hb-warning-text">Consulte las instrucciones de seguridad antes de usarlo.</div>'
            '</div></div>'
        )

        out = _rewrite_word_friendly_fragment(fragment, lang="es")

        self.assertIn("<strong>ADVERTENCIA</strong>", out)
        self.assertNotIn("<strong>WARNING</strong>", out)
        self.assertIn("Consulte las instrucciones de seguridad antes de usarlo.", out)

    def test_rewrite_word_friendly_fragment_should_dedupe_warning_text_matching_label(self) -> None:
        fragment = (
            '<div class="hb-warning-box"><div class="hb-warning-row">'
            '<div class="hb-warning-text">WARNING</div>'
            '</div></div>'
        )

        out = _rewrite_word_friendly_fragment(fragment, lang="en")

        self.assertEqual(1, out.count("WARNING"))
        self.assertIn("<strong>WARNING</strong>", out)

    def test_rewrite_word_friendly_fragment_should_dedupe_localized_warning_text_matching_label(self) -> None:
        fragment = (
            '<div class="hb-warning-box"><div class="hb-warning-row">'
            '<div class="hb-warning-text">ADVERTENCIA</div>'
            '</div></div>'
        )

        with tempfile.TemporaryDirectory() as td:
            symbols_blocks = self._write_alert_labels_symbols_blocks(Path(td))
            out = _rewrite_word_friendly_fragment(fragment, lang="es", symbols_blocks_csv=symbols_blocks)

        self.assertEqual(1, out.count("ADVERTENCIA"))
        self.assertIn("<strong>ADVERTENCIA</strong>", out)

    def test_convert_rst_fragment_to_html_should_not_infer_warning_box_label_from_source_name(self) -> None:
        rst = """
.. only:: html

   .. raw:: html

      <div class="hb-warning-box">
        <div class="hb-warning-row">
          <div class="hb-warning-text">Consulte las instrucciones antes de usarlo.</div>
        </div>
      </div>
"""
        with tempfile.TemporaryDirectory() as td:
            html = _convert_rst_fragment_to_html(
                rst,
                Path("safety_es.rst"),
                Path(td),
            )

        self.assertNotIn("<strong>ADVERTENCIA</strong>", html)
        self.assertIn("Consulte las instrucciones antes de usarlo.", html)

    def test_rewrite_word_friendly_fragment_should_convert_alert_paragraphs_into_tables(self) -> None:
        fragment = (
            "<p><strong>CAUTION</strong></p>"
            "<ul><li>Line 1</li><li>Line 2</li></ul>"
            "<h2>Next Section</h2>"
        )

        with tempfile.TemporaryDirectory() as td:
            symbols_blocks = self._write_alert_labels_symbols_blocks(Path(td))
            out = _rewrite_word_friendly_fragment(fragment, symbols_blocks_csv=symbols_blocks)

        self.assertIn("manual-callout-table", out)
        self.assertIn("<strong>CAUTION</strong>", out)
        self.assertIn("<li>Line 1</li>", out)
        self.assertIn("<h2>Next Section</h2>", out)

    def test_rewrite_word_friendly_fragment_should_convert_alert_headings_into_tables(self) -> None:
        fragment = "<h2>DANGER</h2><ul><li>Indoor use only.</li></ul>"

        with tempfile.TemporaryDirectory() as td:
            symbols_blocks = self._write_alert_labels_symbols_blocks(Path(td))
            out = _rewrite_word_friendly_fragment(fragment, symbols_blocks_csv=symbols_blocks)

        self.assertIn("manual-callout-table", out)
        self.assertIn("<strong>DANGER</strong>", out)
        self.assertIn("Indoor use only.", out)

    def test_rewrite_word_friendly_fragment_should_convert_two_column_alert_tables(self) -> None:
        fragment = (
            "<table><colgroup><col /><col /></colgroup><tbody><tr>"
            "<td><p><strong>CAUTION</strong></p></td>"
            "<td><ul><li><p>Use a compliant cable.</p></li><li><p>Do not start the car.</p></li></ul></td>"
            "</tr></tbody></table>"
            '<p><img src="lcd_mode.png" alt="LCD display mode placeholder."></p>'
        )

        out = _rewrite_word_friendly_fragment(fragment)

        self.assertIn("manual-callout-table", out)
        self.assertIn("manual-callout-label", out)
        self.assertIn("border:1px solid #000", out)
        self.assertNotIn("#f3c27b", out)
        self.assertIn("<strong>CAUTION</strong>", out)
        self.assertIn("Use a compliant cable.", out)
        self.assertNotIn("<colgroup>", out)

    def test_rewrite_word_friendly_fragment_should_convert_localized_alert_tables(self) -> None:
        fragment = (
            "<table><tbody><tr>"
            "<td><p><strong>PRECAUCIÓN</strong></p></td>"
            "<td><p>Use un cable compatible.</p></td>"
            "</tr></tbody></table>"
            "<table><tbody><tr>"
            "<td><p><strong>PELIGRO</strong></p></td>"
            "<td><p>Solo para uso en interiores.</p></td>"
            "</tr></tbody></table>"
            "<table><tbody><tr>"
            "<td><p><strong>注意</strong>：</p></td>"
            "<td><p>请使用合规线缆。</p></td>"
            "</tr></tbody></table>"
            "<table><tbody><tr>"
            "<td><p>ご注意</p></td>"
            "<td><p>安全基準を満たすケーブルを使用してください。</p></td>"
            "</tr></tbody></table>"
        )

        with tempfile.TemporaryDirectory() as td:
            symbols_blocks = self._write_alert_labels_symbols_blocks(Path(td))
            out = _rewrite_word_friendly_fragment(fragment, symbols_blocks_csv=symbols_blocks)

        self.assertEqual(4, out.count("manual-callout-table"))
        self.assertIn("<strong>PRECAUCIÓN</strong>", out)
        self.assertIn("<strong>PELIGRO</strong>", out)
        self.assertIn("<strong>注意</strong>", out)
        self.assertIn("<strong>ご注意</strong>", out)

    def test_convert_rst_fragment_to_html_should_convert_two_column_alert_list_tables(self) -> None:
        rst = """
DC OUTPUT
=========

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **CAUTION**
     -
       - Use a compliant cable.
       - Do not start the car while charging.
"""
        with tempfile.TemporaryDirectory() as td:
            html = _convert_rst_fragment_to_html(
                rst,
                Path("05_operation_guide_placeholder.rst"),
                Path(td),
            )

        self.assertIn("manual-callout-table", html)
        self.assertIn("<strong>CAUTION</strong>", html)
        self.assertIn("Use a compliant cable.", html)

    def test_rewrite_word_friendly_fragment_should_convert_nested_alert_blocks(self) -> None:
        fragment = (
            '<div class="hb-safety">'
            '<div class="hb-warning-box"><div class="hb-warning-text">Risk of fire.</div></div>'
            '<section id="danger"><h2>DANGER</h2><ul><li>Indoor use only.</li></ul></section>'
            "</div>"
        )

        with tempfile.TemporaryDirectory() as td:
            symbols_blocks = self._write_alert_labels_symbols_blocks(Path(td))
            out = _rewrite_word_friendly_fragment(fragment, symbols_blocks_csv=symbols_blocks)

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

        with tempfile.TemporaryDirectory() as td:
            symbols_blocks = self._write_alert_labels_symbols_blocks(Path(td))
            out = _rewrite_word_friendly_fragment(fragment, symbols_blocks_csv=symbols_blocks)

        self.assertIn("warning_bar.png", out)
        self.assertIn("caution_bar.png", out)
        self.assertIn("note_bar.png", out)
        self.assertIn("tip_bar.png", out)
        self.assertNotIn("old-warning.png", out)
        self.assertNotIn("<strong>WARNING</strong>", out)
        self.assertNotIn("manual-callout-table", out)


if __name__ == "__main__":
    unittest.main()
