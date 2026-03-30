from __future__ import annotations

import unittest
from pathlib import Path
import tempfile

from tools.phase1 import renderers


class TestPhase1Renderers(unittest.TestCase):
    def _template(self) -> str:
        return "\n".join(
            [
                renderers.PH_TITLE_MAIN,
                renderers.PH_WARNING_TITLE,
                renderers.PH_TITLE_OPERATING,
                renderers.PH_LEAD_TOP,
                renderers.PH_SAVE_TITLE,
                renderers.PH_TOP,
                renderers.PH_BOTTOM,
            ]
        ) + "\n"

    def _blocks(self) -> list[dict[str, str]]:
        return [
            {
                "block_type": "title_main",
                "order": "1",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "IMPORTANT SAFETY INFORMATION",
            },
            {
                "block_type": "warning_title",
                "order": "2",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "WARNING TITLE",
            },
            {
                "block_type": "title_operating",
                "order": "3",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "OPERATING INSTRUCTIONS",
            },
            {
                "block_type": "lead_top",
                "order": "4",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "Lead paragraph",
            },
            {
                "block_type": "save_title",
                "order": "5",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "SAVE THESE INSTRUCTIONS",
            },
            {
                "block_type": "list_item",
                "order": "6",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": '{"list_part": "top"}',
                "text_en": "Top list item",
            },
            {
                "block_type": "list_item",
                "order": "7",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": '{"list_part": "bottom"}',
                "text_en": "Bottom list item",
            },
        ]

    def test_render_safety_page_happy_path(self) -> None:
        out = renderers.render_safety_page(
            template=self._template(),
            blocks=self._blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )
        self.assertIn("IMPORTANT SAFETY INFORMATION", out)
        self.assertIn("Top list item", out)
        self.assertIn("Bottom list item", out)

    def test_latex_escape_should_escape_common_special_chars(self) -> None:
        text = r"50%_off #1 & more $x$ \\macro ~^"
        escaped = renderers.latex_arg_escape(text)

        # Desired: common LaTeX-sensitive characters are escaped.
        self.assertIn(r"\%", escaped)
        self.assertIn(r"\_", escaped)
        self.assertIn(r"\#", escaped)
        self.assertIn(r"\&", escaped)
        self.assertIn(r"\$", escaped)

    def test_invalid_meta_json_should_fail_fast_with_clear_error(self) -> None:
        blocks = self._blocks()
        # Break top list metadata to reproduce silent-fail path.
        for row in blocks:
            if row.get("block_type") == "list_item" and "Top" in row.get("text_en", ""):
                row["meta_json"] = "{bad-json"

        with self.assertRaisesRegex(ValueError, "meta_json|json|line"):
            renderers.render_safety_page(
                template=self._template(),
                blocks=blocks,
                sku_id="JB1000",
                lang="en",
                vars_map={},
            )

    def _spec_template(self) -> str:
        return "\n".join(
            [
                renderers.PH_SPEC_TITLE_MAIN,
                renderers.PH_SPEC_TITLE_MAIN_HTML,
                renderers.PH_SPEC_SECTIONS_LATEX,
                renderers.PH_SPEC_FOOTNOTES_LATEX,
                renderers.PH_SPEC_NOTES_LATEX,
                renderers.PH_SPEC_SECTIONS_HTML,
                renderers.PH_SPEC_FOOTNOTES_HTML,
                renderers.PH_SPEC_NOTES_HTML,
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
        self.assertIn('class="hb-spec-note"', out)
        self.assertIn('class="hb-spec-footnote"', out)
        self.assertLess(out.index("Demo footnote"), out.index("Demo note line"))

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
                "Param_source": "Bypass Mode (1)",
                "Value_source": "100V-120V~60Hz, 12A Max, 1440W",
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
                "Section": "META",
                "Section_order": "90",
                "Row_key": "note_1",
                "Row_label_source": "NOTE",
                "Line_order": "1",
                "Param_source": "",
                "Value_source": "",
                "row_kind": "note",
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
                "footnote_mark": "",
                "footnote_text_en": "(1) Demo footnote text",
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
        self.assertIn("(1) Demo footnote text", out)
        self.assertIn("<br/>", out)
        self.assertIn('class="hb-spec-table"', out)

        model_pos = out.find("Model No.")
        ac_pos = out.find("1 x AC Input")
        self.assertGreater(model_pos, -1)
        self.assertGreater(ac_pos, -1)

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
                "column_group": "left",
                "symbol_key": "warning_triangle",
                "image_path": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "order": "10",
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
                "column_group": "left",
                "symbol_key": "read_manual",
                "image_path": "templates/word_template/common_assets/symbols/read_manual_operator.png",
                "order": "20",
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
                "column_group": "right",
                "symbol_key": "do_not_dismantle",
                "image_path": "templates/word_template/common_assets/symbols/do_not_dismantle.png",
                "order": "10",
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

    def test_render_symbols_page_filters_by_model_and_region(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Region"] = "US"
        blocks[0]["Model"] = "JE-1000F"
        blocks[0]["text_en"] = "US JE-1000F warning."
        blocks[1]["Region"] = "EU"
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

    def test_render_symbols_page_supports_weee2_symbol_asset(self) -> None:
        blocks = self._symbols_blocks()
        blocks.append(
            {
                "block_type": "table_row",
                "column_group": "right",
                "symbol_key": "weee2",
                "image_path": "templates/word_template/common_assets/symbols/weee2.png",
                "order": "20",
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


    def test_collect_safety_content_returns_structured_lists(self) -> None:
        data = renderers.collect_safety_content(
            blocks=self._blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )
        self.assertEqual("IMPORTANT SAFETY INFORMATION", data["title_main"])
        self.assertEqual(["Top list item"], data["top_items"])
        self.assertEqual(["Bottom list item"], data["bottom_items"])

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

if __name__ == "__main__":
    unittest.main()
