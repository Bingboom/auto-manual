from __future__ import annotations

import unittest
from pathlib import Path
import tempfile

from tools.phase1 import renderers


class TestPhase1Renderers(unittest.TestCase):
    def test_latex_escape_should_escape_common_special_chars(self) -> None:
        text = r"50%_off #1 & more $x$ \\macro ~^"
        escaped = renderers.latex_arg_escape(text)

        # Desired: common LaTeX-sensitive characters are escaped.
        self.assertIn(r"\%", escaped)
        self.assertIn(r"\_", escaped)
        self.assertIn(r"\#", escaped)
        self.assertIn(r"\&", escaped)
        self.assertIn(r"\$", escaped)

    def _spec_template(self) -> str:
        return "\n".join(
            [
                renderers.PH_SPEC_TITLE_MAIN,
                renderers.PH_SPEC_TITLE_MAIN_HTML,
                renderers.PH_SPEC_SECTIONS_LATEX,
                renderers.PH_SPEC_NOTES_LATEX,
                renderers.PH_SPEC_FOOTNOTES_LATEX,
                renderers.PH_SPEC_SECTIONS_HTML,
                renderers.PH_SPEC_NOTES_HTML,
                renderers.PH_SPEC_FOOTNOTES_HTML,
            ]
        ) + "\n"

    def _spec_blocks(self) -> list[dict[str, str]]:
        return [
            {
                "block_type": "title_main",
                "order": "100",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "SPECIFICATIONS",
            },
            {
                "block_type": "section_title",
                "order": "110",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "GENERAL INFO",
            },
            {
                "block_type": "row_item",
                "order": "111",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "Product Name || Demo Product",
            },
            {
                "block_type": "row_item",
                "order": "112",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "Model No. || DEMO-1000",
            },
            {
                "block_type": "note_line",
                "order": "150",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "* Demo note line",
            },
            {
                "block_type": "footnote",
                "order": "160",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "(1) Demo footnote",
            },
        ]

    def test_render_spec_page_happy_path(self) -> None:
        out = renderers.render_spec_page(
            template=self._spec_template(),
            blocks=self._spec_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )
        self.assertIn("SPECIFICATIONS", out)
        self.assertIn("GENERAL INFO", out)
        self.assertIn("Product Name", out)
        self.assertIn("Demo footnote", out)
        self.assertIn('class="hb-spec-bullet"', out)
        self.assertIn('class="hb-spec-table"', out)
        self.assertIn('class="hb-spec-note" data-spec-trailer-kind="note"', out)
        self.assertIn('class="hb-spec-footnote" data-spec-trailer-kind="footnote"', out)
        self.assertLess(out.index("Demo note line"), out.index("Demo footnote"))

    def test_render_spec_page_row_without_delimiter_should_fail(self) -> None:
        blocks = self._spec_blocks()
        for row in blocks:
            if row.get("block_type") == "row_item":
                row["text_en"] = "bad row format"
                break

        with self.assertRaisesRegex(ValueError, "left \\|\\| right"):
            renderers.render_spec_page(
                template=self._spec_template(),
                blocks=blocks,
                sku_id="JB1000",
                lang="en",
                vars_map={},
            )

    def _spec_master_blocks(self) -> list[dict[str, str]]:
        blocks = [
            {
                "\u9879\u76ee\u4ee3\u7801": "HTE152-US",
                "Region": "US",
                "Source_lang": "en",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "GENERAL INFO",
                "Section_order": "1",
                "Row_key": "ac_input",
                "Row_label_source": "1 x AC Input",
                "Line_order": "1",
                "Param_source": "Charge Mode",
                "Value_source": "100V-120V~60Hz, 15A Max, 1750W Max",
                "row_order": "2",
                "page_title_en": "SPECIFICATIONS",
                "section_title_en": "GENERAL INFO",
                "sku_scope": "ALL",
                "enabled": "1",
            },
            {
                "\u9879\u76ee\u4ee3\u7801": "HTE152-US",
                "Region": "US",
                "Source_lang": "en",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "GENERAL INFO",
                "Section_order": "1",
                "Row_key": "ac_input",
                "Row_label_source": "1 x AC Input",
                "Line_order": "2",
                "Param_source": "Bypass Mode",
                "Value_source": "100V-120V~60Hz, 12A Max, 1440W",
                "Param_footnote_refs": "ac_bypass",
                "row_order": "2",
                "page_title_en": "",
                "section_title_en": "GENERAL INFO",
                "sku_scope": "ALL",
                "enabled": "1",
            },
            {
                "\u9879\u76ee\u4ee3\u7801": "HTE152-US",
                "Region": "US",
                "Source_lang": "en",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "GENERAL INFO",
                "Section_order": "1",
                "Row_key": "model_no",
                "Row_label_source": "Model No.",
                "Line_order": "1",
                "Param_source": "",
                "Value_source": "JHP-2000A",
                "row_order": "1",
                "page_title_en": "",
                "section_title_en": "GENERAL INFO",
                "sku_scope": "ALL",
                "enabled": "1",
                "custom_extra_column": "kept for forward compatibility",
            },
            {
                "\u9879\u76ee\u4ee3\u7801": "HTE152-US",
                "Region": "US",
                "Source_lang": "en",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "GENERAL INFO",
                "Section_order": "1",
                "Row_key": "ac_output_bypass",
                "Row_label_source": "AC Output in Bypass Mode",
                "Line_order": "1",
                "Param_source": "",
                "Value_source": "100V-120V~60Hz, 12A Max",
                "Row_label_footnote_refs": "ac_bypass",
                "row_order": "3",
                "page_title_en": "",
                "section_title_en": "GENERAL INFO",
                "sku_scope": "ALL",
                "enabled": "1",
            },
            {
                "\u9879\u76ee\u4ee3\u7801": "HTE152-US",
                "Region": "US",
                "Source_lang": "en",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "META",
                "Section_order": "90",
                "Row_key": "note_1",
                "Row_label_source": "NOTE",
                "Line_order": "1",
                "Param_source": "",
                "Value_source": "",
                "row_kind": "note",
                "note_id": "usb_type_c_trademark",
                "note_order": "1",
                "note_text_en": "* Demo note",
                "sku_scope": "ALL",
                "enabled": "1",
            },
            {
                "\u9879\u76ee\u4ee3\u7801": "HTE152-US",
                "Region": "US",
                "Source_lang": "en",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "META",
                "Section_order": "91",
                "Row_key": "fn_1",
                "Row_label_source": "FOOTNOTE",
                "Line_order": "1",
                "Param_source": "",
                "Value_source": "",
                "row_kind": "footnote",
                "footnote_id": "ac_bypass",
                "footnote_order": "1",
                "footnote_text_en": "Demo footnote text",
                "sku_scope": "ALL",
                "enabled": "1",
            },
        ]
        for row in blocks:
            row.setdefault("Model", "JHP-2000A")
        return blocks

    def test_render_spec_page_supports_spec_master_schema(self) -> None:
        out = renderers.render_spec_page(
            template=self._spec_template(),
            blocks=self._spec_master_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )
        self.assertIn("SPECIFICATIONS", out)
        self.assertIn("GENERAL INFO", out)
        self.assertIn("Model No.", out)
        self.assertIn("Charge Mode: 100V-120V\\textasciitilde{}60Hz, 15A Max, 1750W Max", out)
        self.assertIn("Demo note", out)
        self.assertIn('class="hb-spec-note" data-spec-trailer-kind="note"', out)
        self.assertIn('class="hb-spec-footnote" data-spec-trailer-kind="footnote"', out)
        self.assertLess(out.index("Demo note"), out.index("Demo footnote text"))
        self.assertIn("Demo footnote text", out)
        self.assertIn(r"\HBSpecMarkerOne{}", out)
        self.assertIn("<br/>", out)
        self.assertIn('class="hb-spec-table"', out)

        model_pos = out.find("Model No.")
        ac_pos = out.find("1 x AC Input")
        self.assertGreater(model_pos, -1)
        self.assertGreater(ac_pos, -1)

    def test_render_spec_page_should_fallback_to_sibling_region_footnote_definition(self) -> None:
        blocks = self._spec_master_blocks()
        for row in blocks:
            if row.get("footnote_id") == "ac_bypass":
                row["Region"] = "US"
            else:
                row["Region"] = "EU"

        out = renderers.render_spec_page(
            template=self._spec_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={"model": "JHP-2000A", "region": "EU"},
        )

        self.assertIn("Demo footnote text", out)
        self.assertIn(r"\HBSpecMarkerOne{}", out)
        self.assertIn('class="hb-spec-footnote" data-spec-trailer-kind="footnote"', out)

    def test_render_spec_page_should_use_source_columns_for_jp_source_language_rows(self) -> None:
        jp_row = dict(self._spec_master_blocks()[0])
        jp_row["Region"] = "JP"
        jp_row["Source_lang"] = "ja"
        jp_row["Row_label_source"] = "AC入力"
        jp_row["Param_source"] = "急速充電モード"
        jp_row["Value_source"] = "100V-120V~50/60Hz、15A Max、1450W"
        out = renderers.render_spec_page(
            template=self._spec_template(),
            blocks=[jp_row],
            sku_id="JB1000",
            lang="ja",
            vars_map={},
        )

        self.assertIn("AC入力", out)
        self.assertIn("急速充電モード: 100V-120V\\textasciitilde{}50/60Hz、15A Max、1450W", out)

    def test_render_spec_page_should_honor_explicit_source_lang_column(self) -> None:
        jp_row = dict(self._spec_master_blocks()[0])
        jp_row["Region"] = "US"
        jp_row["Source_lang"] = "ja"
        jp_row["Row_label_source"] = "AC入力"
        jp_row["Param_source"] = "急速充電モード"
        jp_row["Value_source"] = "100V-120V~50/60Hz、15A Max、1450W"
        out = renderers.render_spec_page(
            template=self._spec_template(),
            blocks=[jp_row],
            sku_id="JB1000",
            lang="ja",
            vars_map={},
        )

        self.assertIn("AC入力", out)
        self.assertIn("急速充電モード: 100V-120V\\textasciitilde{}50/60Hz、15A Max、1450W", out)

    def test_render_spec_page_rejects_unquoted_comma_overflow(self) -> None:
        blocks = self._spec_master_blocks()
        blocks[0][None] = [" 15A Max", " 1750W Max"]

        with self.assertRaisesRegex(ValueError, "unquoted commas|Quote the full cell value"):
            renderers.render_spec_page(
                template=self._spec_template(),
                blocks=blocks,
                sku_id="JB1000",
                lang="en",
                vars_map={},
            )

    def _symbols_template(self) -> str:
        return (
            renderers.PH_SYMBOLS_SIGNAL_SECTION_RST
            + "\n\n"
            + renderers.PH_SYMBOLS_ICON_TABLE_RST
            + "\n"
        )

    def _symbols_blocks(self) -> list[dict[str, str]]:
        return [
            {
                "block_type": "table_row",
                "symbol_key": "warning_triangle",
                "image_path": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "order": "1",
                "Region": "",
                "Model": "",
                "Source_lang": "en",
                "enabled": "1",
                "text_en": "Warning symbol meaning.",
                "text_fr": "Signification du symbole d'avertissement.",
                "text_es": "Significado del símbolo de advertencia.",
            },
            {
                "block_type": "table_row",
                "symbol_key": "read_manual",
                "image_path": "templates/word_template/common_assets/symbols/read_manual_operator.png",
                "order": "2",
                "Region": "",
                "Model": "",
                "Source_lang": "en",
                "enabled": "1",
                "text_en": "Read the manual.",
                "text_fr": "Lire le manuel.",
                "text_es": "Lea el manual.",
            },
            {
                "block_type": "table_row",
                "symbol_key": "do_not_dismantle",
                "image_path": "templates/word_template/common_assets/symbols/do_not_dismantle.png",
                "order": "3",
                "Region": "",
                "Model": "",
                "Source_lang": "en",
                "enabled": "1",
                "text_en": "Do not dismantle.",
                "text_fr": "Ne démontez pas.",
                "text_es": "No desarme.",
            },
        ]

    def test_render_symbols_page_happy_path(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )
        self.assertIn("DANGER", out)
        self.assertIn("MEANING OF SYMBOLS", out)
        self.assertIn("warning_bar.png", out)
        self.assertIn("read_manual_operator.png", out)
        self.assertIn("Do not dismantle.", out)

    def test_render_symbols_page_should_render_danger_notice_without_bullet_list(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )
        self.assertIn("**DANGER**", out)
        self.assertIn("※ This device is not waterproof or dustproof.", out)
        self.assertNotIn("\n- This device is intended for indoor use only", out)

    def test_render_symbols_page_should_insert_blank_line_before_danger_notice(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )

        self.assertTrue(out.startswith("|\n\n.. list-table::"))

    def test_render_symbols_page_uses_image_path_from_blocks(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["image_path"] = "custom/symbols/warning_triangle.png"
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )
        self.assertIn("custom/symbols/warning_triangle.png", out)

    def test_render_symbols_page_prefers_figure_attachment_path(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Figure"] = "data/phase2/_attachments/symbols/10_warning_triangle.png"
        blocks[0]["image_path"] = "templates/word_template/common_assets/symbols/warning_triangle.png"

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )

        self.assertIn("data/phase2/_attachments/symbols/10_warning_triangle.png", out)
        self.assertNotIn("templates/word_template/common_assets/symbols/warning_triangle.png", out)

    def test_render_symbols_page_resolves_figure_attachment_json(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Figure"] = '{"file_token":"warning_token","name":"warning.svg"}'
        blocks[0]["image_path"] = "templates/word_template/common_assets/symbols/warning_triangle.png"

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )

        self.assertIn(".. image:: data/phase2/_attachments/symbols/warning_token.svg", out)

    def test_render_symbols_page_uses_language_specific_copy(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="fr",
            vars_map={},
        )
        self.assertIn("SIGNIFICATION DES SYMBOLES", out)
        self.assertIn("Symbole", out)
        self.assertIn("Signification du symbole d'avertissement.", out)

    def test_render_symbols_page_should_match_french_danger_notice_copy(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="fr",
            vars_map={},
        )
        self.assertIn("**AVERTISSEMENT**", out)
        self.assertIn("**ATTENTION**", out)
        self.assertIn(
            "Cet appareil est destiné à un usage intérieur uniquement (veuillez placer cet appareil dans un environnement intérieur similaire lors de son utilisation à l'extérieur, par exemple dans des VR résidentiels, des tentes, des chalets, etc.).",
            out,
        )
        self.assertIn(
            "※ Cet appareil n'est pas étanche ni résistant à la poussière. Éloignez-le de la pluie et des environnements humides pendant son utilisation.",
            out,
        )

    def test_render_symbols_page_should_match_spanish_danger_notice_copy(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="es",
            vars_map={},
        )
        self.assertIn("**ADVERTENCIA**", out)
        self.assertNotIn("**PELIGRO**", out)
        self.assertIn(
            "Este dispositivo está diseñado únicamente para uso en interiores (coloque este dispositivo en un ambiente similar a interiores cuando lo use en exteriores, ej. autocaravanas, tiendas de campaña, cabañas, etc.).",
            out,
        )
        self.assertIn(
            "※ Este dispositivo no es resistente al agua ni al polvo. Manténgalo alejado de la lluvia y ambientes húmedos durante su uso.",
            out,
        )

    def test_render_symbols_page_filters_by_model_and_region(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Region"] = "US"
        blocks[0]["Model"] = "JE-1000F"
        blocks[0]["text_en"] = "US JE-1000F warning."
        blocks[1]["Region"] = "JP"
        blocks[1]["Model"] = "JE-9999X"
        blocks[1]["text_en"] = "SHOULD_NOT_RENDER"
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={"model": "JE-1000F", "region": "US"},
        )
        self.assertIn("US JE-1000F warning.", out)
        self.assertNotIn("SHOULD_NOT_RENDER", out)

    def test_render_symbols_page_filters_inactive_rows(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Is_Latest"] = "False"
        blocks[0]["text_en"] = "SHOULD_NOT_RENDER"
        blocks.append(
            {
                "block_type": "table_row",
                "symbol_key": "electric_shock",
                "image_path": "templates/word_template/common_assets/symbols/electric_shock.png",
                "order": "30",
                "Region": "",
                "Model": "",
                "Source_lang": "en",
                "enabled": "1",
                "text_en": "Active replacement.",
                "text_fr": "Remplacement actif.",
                "text_es": "Reemplazo activo.",
            }
        )

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )

        self.assertNotIn("SHOULD_NOT_RENDER", out)
        self.assertIn("Active replacement.", out)

    def test_render_symbols_page_filters_by_market(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Market"] = "US"
        blocks[0]["text_en"] = "US-only warning."
        blocks[1]["Market"] = "US, EU"
        blocks[1]["text_en"] = "Shared read manual."

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={"region": "EU"},
        )

        self.assertNotIn("US-only warning.", out)
        self.assertIn("Shared read manual.", out)
        self.assertIn("Do not dismantle.", out)

    def test_render_symbols_page_filters_by_market_json_list(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Market"] = '[{"text":"US"},{"text":"EU"}]'
        blocks[0]["text_en"] = "Shared warning."

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={"region": "EU"},
        )

        self.assertIn("Shared warning.", out)

    def test_render_symbols_page_auto_distributes_unique_order_rows(self) -> None:
        blocks = self._symbols_blocks()
        rows = [
            ("warning_triangle", "1", "Order 1."),
            ("read_manual", "2", "Order 2."),
            ("electric_shock", "3", "Order 3."),
            ("do_not_dismantle", "4", "Order 4."),
            ("weee", "5", "Order 5."),
        ]
        for block, (symbol_key, order, text) in zip(blocks, rows):
            block["symbol_key"] = symbol_key
            block["order"] = order
            block["text_en"] = text
        for symbol_key, order, text in rows[len(blocks) :]:
            blocks.append(
                {
                    "block_type": "table_row",
                    "symbol_key": symbol_key,
                    "image_path": f"templates/word_template/common_assets/symbols/{symbol_key}.png",
                    "order": order,
                    "Region": "",
                    "Model": "",
                    "Source_lang": "en",
                    "enabled": "1",
                    "text_en": text,
                    "text_fr": text,
                    "text_es": text,
                }
            )

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )

        order_positions = [out.index(f"Order {idx}.") for idx in range(1, 6)]
        self.assertLess(order_positions[0], order_positions[3])
        self.assertLess(order_positions[3], order_positions[1])
        self.assertLess(order_positions[1], order_positions[4])
        self.assertLess(order_positions[4], order_positions[2])

    def test_render_symbols_page_should_fallback_to_sibling_region_rows(self) -> None:
        blocks = self._symbols_blocks()
        for block in blocks:
            block["Region"] = "US"
            block["Model"] = "JE-1000F"

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={"model": "JE-1000F", "region": "EU"},
        )

        self.assertIn("Warning symbol meaning.", out)
        self.assertIn("Do not dismantle.", out)

    def test_render_symbols_page_should_normalize_document_key_style_target_model(self) -> None:
        blocks = self._symbols_blocks()
        for block in blocks:
            block["Region"] = "US"
            block["Model"] = "JE-1000F"

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={"model": "JE-1000F_US", "region": "US"},
        )

        self.assertIn("Warning symbol meaning.", out)
        self.assertIn("Do not dismantle.", out)

    def test_render_symbols_page_supports_weee2_symbol_asset(self) -> None:
        blocks = self._symbols_blocks()
        blocks.append(
            {
                "block_type": "table_row",
                "symbol_key": "weee2",
                "image_path": "templates/word_template/common_assets/symbols/weee2.png",
                "order": "4",
                "Region": "",
                "Model": "",
                "Source_lang": "en",
                "enabled": "1",
                "text_en": "Battery disposal meaning.",
                "text_fr": "Signification de mise au rebut des batteries.",
                "text_es": "Significado de eliminación de baterías.",
            }
        )

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )
        self.assertIn("weee2.png", out)
        self.assertIn("Battery disposal meaning.", out)

    def test_render_symbols_page_keeps_icon_table_as_single_table(self) -> None:
        blocks = self._symbols_blocks()
        blocks.extend(
            [
                {
                    "block_type": "table_row",
                    "symbol_key": "electric_shock",
                    "image_path": "templates/word_template/common_assets/symbols/electric_shock.png",
                    "order": "4",
                    "Region": "",
                    "Model": "",
                    "Source_lang": "en",
                    "enabled": "1",
                    "text_en": "Electric shock symbol meaning.",
                    "text_fr": "Signification du symbole de choc électrique.",
                    "text_es": "Significado del símbolo de descarga eléctrica.",
                },
                {
                    "block_type": "table_row",
                    "symbol_key": "weee2",
                    "image_path": "templates/word_template/common_assets/symbols/weee2.png",
                    "order": "5",
                    "Region": "",
                    "Model": "",
                    "Source_lang": "en",
                    "enabled": "1",
                    "text_en": "Battery disposal meaning.",
                    "text_fr": "Signification de mise au rebut des batteries.",
                    "text_es": "Significado de eliminación de baterías.",
                },
                {
                    "block_type": "table_row",
                    "symbol_key": "weee",
                    "image_path": "templates/word_template/common_assets/symbols/weee.png",
                    "order": "6",
                    "Region": "",
                    "Model": "",
                    "Source_lang": "en",
                    "enabled": "1",
                    "text_en": "WEEE disposal meaning.",
                    "text_fr": "Signification DEEE.",
                    "text_es": "Significado RAEE.",
                },
            ]
        )

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )

        self.assertEqual(3, out.count(".. list-table::"))
        self.assertIn("Electric shock symbol meaning.", out)
        self.assertIn("Battery disposal meaning.", out)
        self.assertIn("WEEE disposal meaning.", out)

    def test_render_symbols_page_rejects_unknown_symbol_key(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["symbol_key"] = "missing_symbol"

        with self.assertRaisesRegex(ValueError, "unknown symbols symbol_key"):
            renderers.render_symbols_page(
                template=self._symbols_template(),
                blocks=blocks,
                sku_id="JB1000",
                lang="en",
                vars_map={},
            )

    def _lcd_template(self) -> str:
        return (
            renderers.PH_LCD_ICONS_HEADING_RST
            + "\n\n"
            + renderers.PH_LCD_ICONS_IMAGE_ALT
            + "\n\n"
            + renderers.PH_LCD_ICONS_TABLE_RST
            + "\n"
        )

    def _lcd_blocks(self) -> list[dict[str, str]]:
        return [
            {
                "No.": "22",
                "Model": "JE-1000F",
                "Is_latest": "TRUE",
                "icon_en": "Energy Saving Mode",
                "icon_fr": "Mode economie d'energie",
                "icon_jp": "省エネモード",
                "icon_ukr": "Energy Saving Mode",
                "icon_desc_en": "When the {{AC_POWER_BUTTON_LABEL}} or {{DC_USB_POWER_BUTTON_LABEL}} output is on:\nOn: Enabled.\nOff: Disabled.",
                "icon_desc_fr": "When the {{AC_POWER_BUTTON_LABEL}} or {{DC_USB_POWER_BUTTON_LABEL}} output is on:\nOn: Enabled.\nOff: Disabled.",
                "icon_desc_jp": "{{AC_POWER_BUTTON_LABEL}} / {{DC_USB_POWER_BUTTON_LABEL}}",
                "icon_desc_ukr": "{{AC_POWER_BUTTON_LABEL}} / {{DC_USB_POWER_BUTTON_LABEL}}",
                "figure": "data/phase2/_attachments/lcd_icons/22_Energy_Saving_Mode.png",
                "variable_keys": "AC_POWER_BUTTON_LABEL, DC_USB_POWER_BUTTON_LABEL",
            },
            {
                "No.": "23",
                "Model": "OTHER-MODEL",
                "Is_latest": "TRUE",
                "icon_en": "SHOULD_NOT_RENDER",
                "icon_fr": "SHOULD_NOT_RENDER",
                "icon_ukr": "SHOULD_NOT_RENDER",
                "icon_desc_en": "SHOULD_NOT_RENDER",
                "icon_desc_fr": "SHOULD_NOT_RENDER",
                "icon_desc_ukr": "SHOULD_NOT_RENDER",
            },
        ]

    def test_render_lcd_icons_page_resolves_model_default_variables(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            defaults = Path(td) / "Variable_Defaults.csv"
            overrides = Path(td) / "Variable_Lang_Overrides.csv"
            defaults.write_text(
                "Variable_key,Model,Value,is_default\n"
                "AC_POWER_BUTTON_LABEL,JE-1000F,AC,FALSE\n"
                "AC_POWER_BUTTON_LABEL,,AC1/2,TRUE\n"
                "DC_USB_POWER_BUTTON_LABEL,,DC/USB,TRUE\n",
                encoding="utf-8",
            )
            overrides.write_text("Variable_key,lang,source_value,Value\n", encoding="utf-8")

            out = renderers.render_lcd_icons_page(
                template=self._lcd_template(),
                blocks=self._lcd_blocks(),
                sku_id="",
                lang="en",
                vars_map={
                    "model": "JE-1000F",
                    "variable_defaults_csv": str(defaults),
                    "variable_lang_overrides_csv": str(overrides),
                },
            )

        self.assertIn("LCD DISPLAY", out)
        self.assertIn("   :widths: 8 12 28 52", out)
        self.assertIn("     - .. image:: data/phase2/_attachments/lcd_icons/22_Energy_Saving_Mode.png", out)
        self.assertIn("          :alt: Energy Saving Mode", out)
        self.assertIn("          :width: 42px", out)
        self.assertIn("Energy Saving Mode", out)
        self.assertIn("When the AC or DC/USB output is on:", out)
        self.assertIn("     - | When the AC or DC/USB output is on:", out)
        self.assertIn("       | **On:** Enabled.", out)
        self.assertIn("       | **Off:** Disabled.", out)
        self.assertNotIn("SHOULD_NOT_RENDER", out)

    def test_render_lcd_icons_page_should_normalize_document_key_style_target_model(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            defaults = Path(td) / "Variable_Defaults.csv"
            overrides = Path(td) / "Variable_Lang_Overrides.csv"
            defaults.write_text(
                "Variable_key,Model,Value,is_default\n"
                "AC_POWER_BUTTON_LABEL,JE-1000F,AC,FALSE\n"
                "AC_POWER_BUTTON_LABEL,,AC1/2,TRUE\n"
                "DC_USB_POWER_BUTTON_LABEL,,DC/USB,TRUE\n",
                encoding="utf-8",
            )
            overrides.write_text("Variable_key,lang,source_value,Value\n", encoding="utf-8")

            out = renderers.render_lcd_icons_page(
                template=self._lcd_template(),
                blocks=self._lcd_blocks(),
                sku_id="",
                lang="en",
                vars_map={
                    "model": "JE-1000F_US",
                    "region": "US",
                    "variable_defaults_csv": str(defaults),
                    "variable_lang_overrides_csv": str(overrides),
                },
            )

        self.assertIn("Energy Saving Mode", out)
        self.assertNotIn("SHOULD_NOT_RENDER", out)

    def test_render_lcd_icons_page_resolves_figure_attachment_json(self) -> None:
        blocks = [
            {
                "No.": "1",
                "Model": "JE-1000F",
                "Is_latest": "TRUE",
                "icon_en": "Wi-Fi",
                "icon_desc_en": "On: Wi-Fi connected.",
                "figure": '{"file_token":"wifi_token","name":"wifi.svg"}',
            }
        ]

        out = renderers.render_lcd_icons_page(
            template=self._lcd_template(),
            blocks=blocks,
            sku_id="",
            lang="en",
            vars_map={"model": "JE-1000F"},
        )

        self.assertIn(".. image:: data/phase2/_attachments/lcd_icons/wifi_token.svg", out)

    def test_render_lcd_icons_page_flattens_multiline_image_alt(self) -> None:
        blocks = [
            {
                "No.": "8",
                "Model": "JE-1000F",
                "Is_latest": "TRUE",
                "icon_jp": "交流電源による出力マーク\n（正弦波)",
                "icon_desc_jp": "AC出力がオンになっています。",
                "figure": "data/phase2/_attachments/lcd_icons/ac_power.png",
            }
        ]

        out = renderers.render_lcd_icons_page(
            template=self._lcd_template(),
            blocks=blocks,
            sku_id="",
            lang="ja",
            vars_map={"model": "JE-1000F"},
        )

        self.assertIn("液晶画面\n========", out)
        self.assertIn(":alt: 交流電源による出力マーク （正弦波)", out)
        self.assertNotIn(":alt: 交流電源による出力マーク\n（正弦波)", out)
        self.assertIn("          :width: 42px", out)

    def test_render_lcd_icons_page_treats_literal_newline_marker_as_line_block(self) -> None:
        blocks = [
            {
                "No.": "1",
                "Model": "JE-1000F",
                "Is_latest": "TRUE",
                "icon_en": "Wi-Fi",
                "icon_desc_en": "On: Wi-Fi connected.\\nBlink: Ready to connect to Wi-Fi.\\nOff: Wi-Fi disconnected.",
            }
        ]

        out = renderers.render_lcd_icons_page(
            template=self._lcd_template(),
            blocks=blocks,
            sku_id="",
            lang="en",
            vars_map={"model": "JE-1000F"},
        )

        self.assertIn("     - | **On:** Wi-Fi connected.", out)
        self.assertIn("       | **Blink:** Ready to connect to Wi-Fi.", out)
        self.assertIn("       | **Off:** Wi-Fi disconnected.", out)

    def test_render_lcd_icons_page_applies_language_overrides_and_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            defaults = Path(td) / "Variable_Defaults.csv"
            overrides = Path(td) / "Variable_Lang_Overrides.csv"
            defaults.write_text(
                "Variable_key,Model,Value,is_default\n"
                "AC_POWER_BUTTON_LABEL,JE-1000F,AC,FALSE\n"
                "DC_USB_POWER_BUTTON_LABEL,,DC/USB,TRUE\n",
                encoding="utf-8",
            )
            overrides.write_text(
                "Variable_key,lang,source_value,Value,from_prefix,to_prefix\n"
                "AC_POWER_BUTTON_LABEL,fr,AC,CA,,\n"
                "DC_USB_POWER_BUTTON_LABEL,fr,DC/USB,CC/USB,,\n"
                "AC_POWER_BUTTON_LABEL,ukr,,,AC,AC_UKR\n"
                "DC_USB_POWER_BUTTON_LABEL,ukr,,,DC/USB,DC_UKR\n",
                encoding="utf-8",
            )

            fr_out = renderers.render_lcd_icons_page(
                template=self._lcd_template(),
                blocks=self._lcd_blocks(),
                sku_id="",
                lang="fr",
                vars_map={
                    "model": "JE-1000F",
                    "variable_defaults_csv": str(defaults),
                    "variable_lang_overrides_csv": str(overrides),
                },
            )
            ja_out = renderers.render_lcd_icons_page(
                template=self._lcd_template(),
                blocks=self._lcd_blocks(),
                sku_id="",
                lang="ja",
                vars_map={
                    "model": "JE-1000F",
                    "variable_defaults_csv": str(defaults),
                    "variable_lang_overrides_csv": str(overrides),
                },
            )
            uk_out = renderers.render_lcd_icons_page(
                template=self._lcd_template(),
                blocks=self._lcd_blocks(),
                sku_id="",
                lang="uk",
                vars_map={
                    "model": "JE-1000F",
                    "variable_defaults_csv": str(defaults),
                    "variable_lang_overrides_csv": str(overrides),
                },
            )

        self.assertIn("When the CA or CC/USB output is on:", fr_out)
        self.assertIn("液晶画面", ja_out)
        self.assertIn("LCDアイコンマップ。", ja_out)
        self.assertIn("AC_UKR / DC_UKR", uk_out)
        self.assertIn("ЕКРАН LCD", uk_out)
        self.assertIn("Заглушка схеми значків LCD.", uk_out)

    def test_collect_spec_content_supports_spec_master_schema(self) -> None:
        data = renderers.collect_spec_content(
            blocks=self._spec_master_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )
        self.assertEqual("SPECIFICATIONS", data["title_main"])
        self.assertEqual("GENERAL INFO", data["sections"][0]["title"])
        self.assertIn("Demo footnote text", data["footnotes"][0])

    def test_collect_spec_content_filters_by_model_when_model_column_exists(self) -> None:
        blocks = self._spec_master_blocks()
        blocks.append(
            {
                "\u9879\u76ee\u4ee3\u7801": "HTE152-US",
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "GENERAL INFO",
                "Section_order": "1",
                "Row_key": "model_no_alt",
                "Row_label_source": "Model Alt",
                "Line_order": "1",
                "Param_source": "",
                "Value_source": "SHOULD_NOT_BE_RENDERED",
                "row_order": "1.1",
                "section_title_en": "GENERAL INFO",
                "sku_scope": "ALL",
                "enabled": "1",
                "Model": "JHP-9999X",
            }
        )

        data = renderers.collect_spec_content(
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={"model": "JHP-2000A"},
        )
        joined = "\n".join("\n".join(str(x) for x in sec["rows"]) for sec in data["sections"])
        self.assertNotIn("SHOULD_NOT_BE_RENDERED", joined)

    def test_collect_spec_content_should_normalize_document_key_style_model_suffix(self) -> None:
        blocks = self._spec_master_blocks()
        for row in blocks:
            row["Region"] = "JP"

        data = renderers.collect_spec_content(
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={"model": "JHP-2000A_JP", "region": "JP"},
        )

        joined = "\n".join("\n".join(str(x) for x in sec["rows"]) for sec in data["sections"])
        self.assertIn("Model No.", joined)
        self.assertIn("JHP-2000A", joined)

    def test_collect_spec_content_supports_title_override_rows(self) -> None:
        blocks = self._spec_master_blocks()
        blocks.append(
            {
                "Page": "specifications",
                "Region": "US",
                "Model": "JHP-2000A",
                "row_kind": "title",
                "row_order": "0.1",
                "page_title_en": "MAIN SPECIFICATIONS",
                "Section": "GENERAL INFO",
                "section_title_en": "GENERAL INFORMATION",
                "Is_Latest": "TRUE",
                "enabled": "1",
            }
        )

        data = renderers.collect_spec_content(
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map={"model": "JHP-2000A", "region": "US"},
        )
        self.assertEqual("MAIN SPECIFICATIONS", data["title_main"])
        self.assertEqual("GENERAL INFORMATION", data["sections"][0]["title"])

    def test_collect_spec_content_applies_spec_titles_csv_map_for_region(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            titles_csv = Path(td) / "spec_titles.csv"
            titles_csv.write_text(
                "title_en,title_jp\n"
                "SPECIFICATIONS,涓汇仾浠曟\n"
                "GENERAL INFO,鍩烘湰鎯呭牨\n",
                encoding="utf-8",
            )

            data = renderers.collect_spec_content(
                blocks=self._spec_master_blocks(),
                sku_id="JB1000",
                lang="en",
                vars_map={
                    "model": "JHP-2000A",
                    "region": "US",
                    "title_lang": "jp",
                    "spec_titles_csv": str(titles_csv),
                },
            )
            self.assertEqual("涓汇仾浠曟", data["title_main"])
            self.assertEqual("鍩烘湰鎯呭牨", data["sections"][0]["title"])

    def test_collect_spec_content_uses_spec_titles_section_order_when_master_order_is_blank(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            titles_csv = Path(td) / "spec_titles.csv"
            titles_csv.write_text(
                "title_en,section_order,title_jp\n"
                "SPECIFICATIONS,,SPECIFICATIONS\n"
                "GENERAL INFO,1,GENERAL INFO\n"
                "OUTPUT PORTS,3,OUTPUT PORTS\n",
                encoding="utf-8",
            )

            blocks = [
                {
                    "Region": "US",
                    "Model": "JHP-2000A",
                    "Source_lang": "en",
                    "Is_Latest": "TRUE",
                    "Page": "specifications",
                    "Section": "OUTPUT PORTS",
                    "Section_order": "",
                    "Row_order": "1",
                    "Row_key": "ac_output",
                    "Row_label_source": "AC Output",
                    "Line_order": "1",
                    "Param_source": "",
                    "Value_source": "1800W",
                    "page_title_en": "SPECIFICATIONS",
                    "section_title_en": "OUTPUT PORTS",
                    "enabled": "1",
                },
                {
                    "Region": "US",
                    "Model": "JHP-2000A",
                    "Source_lang": "en",
                    "Is_Latest": "TRUE",
                    "Page": "specifications",
                    "Section": "GENERAL INFO",
                    "Section_order": "",
                    "Row_order": "1",
                    "Row_key": "product_name",
                    "Row_label_source": "Product Name",
                    "Line_order": "1",
                    "Param_source": "",
                    "Value_source": "Demo Product",
                    "section_title_en": "GENERAL INFO",
                    "enabled": "1",
                },
            ]

            data = renderers.collect_spec_content(
                blocks=blocks,
                sku_id="JB1000",
                lang="en",
                vars_map={
                    "model": "JHP-2000A",
                    "region": "US",
                    "spec_titles_csv": str(titles_csv),
                },
            )

            self.assertEqual(
                ["GENERAL INFO", "OUTPUT PORTS"],
                [section["title"] for section in data["sections"]],
            )

    def test_collect_spec_content_prefers_master_section_order_over_spec_titles(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            titles_csv = Path(td) / "spec_titles.csv"
            titles_csv.write_text(
                "title_en,section_order,title_jp\n"
                "SPECIFICATIONS,,SPECIFICATIONS\n"
                "GENERAL INFO,1,GENERAL INFO\n"
                "OUTPUT PORTS,3,OUTPUT PORTS\n",
                encoding="utf-8",
            )

            blocks = [
                {
                    "Region": "US",
                    "Model": "JHP-2000A",
                    "Source_lang": "en",
                    "Is_Latest": "TRUE",
                    "Page": "specifications",
                    "Section": "OUTPUT PORTS",
                    "Section_order": "1",
                    "Row_order": "1",
                    "Row_key": "ac_output",
                    "Row_label_source": "AC Output",
                    "Line_order": "1",
                    "Param_source": "",
                    "Value_source": "1800W",
                    "page_title_en": "SPECIFICATIONS",
                    "section_title_en": "OUTPUT PORTS",
                    "enabled": "1",
                },
                {
                    "Region": "US",
                    "Model": "JHP-2000A",
                    "Source_lang": "en",
                    "Is_Latest": "TRUE",
                    "Page": "specifications",
                    "Section": "GENERAL INFO",
                    "Section_order": "9",
                    "Row_order": "1",
                    "Row_key": "product_name",
                    "Row_label_source": "Product Name",
                    "Line_order": "1",
                    "Param_source": "",
                    "Value_source": "Demo Product",
                    "section_title_en": "GENERAL INFO",
                    "enabled": "1",
                },
            ]

            data = renderers.collect_spec_content(
                blocks=blocks,
                sku_id="JB1000",
                lang="en",
                vars_map={
                    "model": "JHP-2000A",
                    "region": "US",
                    "spec_titles_csv": str(titles_csv),
                },
            )

            self.assertEqual(
                ["OUTPUT PORTS", "GENERAL INFO"],
                [section["title"] for section in data["sections"]],
            )

if __name__ == "__main__":
    unittest.main()
