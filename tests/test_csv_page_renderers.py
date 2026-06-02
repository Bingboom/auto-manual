from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.csv_pages import renderers


class TestCsvPageRenderers(unittest.TestCase):
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
            vars_map=self._localized_copy_vars(),
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
                vars_map=self._localized_copy_vars(),
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
            vars_map=self._localized_copy_vars(),
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

    def test_render_spec_page_should_match_multiselect_model_cells(self) -> None:
        blocks = self._spec_master_blocks()
        for row in blocks:
            row["Region"] = "EU"
            row["Model"] = "JHP-1000A, JHP-2000A"

        out = renderers.render_spec_page(
            template=self._spec_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(model="JHP-2000A", region="EU"),
        )

        self.assertIn("Model No.", out)
        self.assertIn("Demo note", out)
        self.assertIn("Demo footnote text", out)
        self.assertIn(r"\HBSpecMarkerOne{}", out)

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
            vars_map=self._localized_copy_vars(),
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
            vars_map=self._localized_copy_vars(),
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
                vars_map=self._localized_copy_vars(),
            )

    def _symbols_template(self) -> str:
        return (
            renderers.PH_SYMBOLS_SIGNAL_SECTION_RST
            + "\n\n"
            + renderers.PH_SYMBOLS_ICON_TABLE_RST
            + "\n"
        )

    def _localized_copy_vars(self, **values: str) -> dict[str, str]:
        out = {"localized_copy_csv": str(self._localized_copy_fixture_path())}
        out.update(values)
        return out

    def _localized_copy_fixture_path(self) -> Path:
        cached = getattr(self, "_localized_copy_fixture", None)
        if cached is not None:
            return cached

        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        dst = Path(temp_dir.name) / "Localized_Copy.csv"
        src = Path(__file__).resolve().parents[1] / "data/phase2/Localized_Copy.csv"
        shutil.copyfile(src.with_name("Status_Words.csv"), dst.with_name("Status_Words.csv"))

        with src.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            rows = [
                dict(row)
                for row in reader
                if not (row.get("copy_key") or "").startswith("symbols.signal.")
            ]

        def row(
            copy_key: str,
            copy_type: str,
            text_en: str,
            *,
            text_fr: str | None = None,
            text_es: str | None = None,
            text_de: str | None = None,
        ) -> dict[str, str]:
            output = {column: "" for column in fieldnames}
            output.update(
                {
                    "copy_key": copy_key,
                    "page_id": "symbols",
                    "copy_type": copy_type,
                    "Region": "ALL",
                    "Model": "ALL",
                    "Source_lang": "en",
                    "Is_Latest": "TRUE",
                    "Version": "V1.0",
                    "text_en": text_en,
                    "text_zh": text_en,
                    "text_ja": text_en,
                    "text_fr": text_fr or text_en,
                    "text_es": text_es or text_en,
                    "text_pt-BR": text_en,
                    "text_de": text_de or text_en,
                    "text_it": text_en,
                    "text_uk": text_en,
                }
            )
            return output

        rows.extend(
            [
                row("symbols.signal.warning.label", "signal_label", "WARNING", text_fr="AVERTISSEMENT", text_es="ADVERTENCIA", text_de="WARNUNG"),
                row("symbols.signal.warning.meaning", "signal_meaning", "Data warning.", text_fr="Avertissement de donn茅es.", text_es="Advertencia desde datos.", text_de="Datenwarnung."),
                row("symbols.signal.caution.label", "signal_label", "CAUTION", text_fr="ATTENTION", text_es="PRECAUCI脫N", text_de="VORSICHT"),
                row("symbols.signal.caution.meaning", "signal_meaning", "Data caution.", text_fr="Attention de donn茅es.", text_es="Precauci贸n desde datos.", text_de="Datenvorsicht."),
                row("symbols.signal.note.label", "signal_label", "NOTE", text_fr="REMARQUE", text_es="NOTA", text_de="HINWEIS"),
                row("symbols.signal.note.meaning", "signal_meaning", "Data note.", text_fr="Remarque de donn茅es.", text_es="Nota desde datos.", text_de="Datenhinweis."),
                row("symbols.signal.tips.label", "signal_label", "TIP", text_fr="CONSEIL", text_es="CONSEJO", text_de="TIPP"),
                row("symbols.signal.tips.meaning", "signal_meaning", "Data tip.", text_fr="Conseil de donn茅es.", text_es="Consejo desde datos.", text_de="Datentipp."),
                row("symbols.signal.danger.label", "signal_label", "DANGER", text_fr="DANGER", text_es="PELIGRO", text_de="GEFAHR"),
            ]
        )

        with dst.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

        self._localized_copy_fixture = dst
        return dst

    def _symbols_blocks(self) -> list[dict[str, str]]:
        return [
            {
                "block_type": "table_row",
                "symbol_key": "warning_triangle",
                "image_path": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "order": "1",
                "Market": "Global",
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
                "Market": "Global",
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
                "Market": "Global",
                "Model": "",
                "Source_lang": "en",
                "enabled": "1",
                "text_en": "Do not dismantle.",
                "text_fr": "Ne démontez pas.",
                "text_es": "No desarme.",
            },
            {
                "block_type": "signal_row",
                "symbol_key": "WARNING",
                "image_path": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "order": "101",
                "Market": "Global",
                "Model": "",
                "Source_lang": "en",
                "enabled": "1",
                "text_en": "Data warning.",
                "text_fr": "Avertissement de données.",
                "text_es": "Advertencia desde datos.",
                "text_de": "Datenwarnung.",
            },
            {
                "block_type": "signal_row",
                "symbol_key": "CAUTION",
                "image_path": "templates/word_template/common_assets/symbols/warning_triangle.png",
                "order": "102",
                "Market": "Global",
                "Model": "",
                "Source_lang": "en",
                "enabled": "1",
                "text_en": "Data caution.",
                "text_fr": "Attention de données.",
                "text_es": "Precaución desde datos.",
                "text_de": "Datenvorsicht.",
            },
            {
                "block_type": "signal_row",
                "symbol_key": "NOTE",
                "image_path": "templates/word_template/common_assets/symbols/mandatory.png",
                "order": "103",
                "Market": "Global",
                "Model": "",
                "Source_lang": "en",
                "enabled": "1",
                "text_en": "Data note.",
                "text_fr": "Remarque de données.",
                "text_es": "Nota desde datos.",
                "text_de": "Datenhinweis.",
            },
            {
                "block_type": "signal_row",
                "symbol_key": "TIPS",
                "image_path": "templates/word_template/common_assets/symbols/mandatory.png",
                "order": "104",
                "Market": "Global",
                "Model": "",
                "Source_lang": "en",
                "enabled": "1",
                "text_en": "Data tip.",
                "text_fr": "Conseil de données.",
                "text_es": "Consejo desde datos.",
                "text_de": "Datentipp.",
            },
            {
                "block_type": "signal_row",
                "symbol_key": "DANGER",
                "order": "105",
                "Market": "Global",
                "Model": "",
                "Source_lang": "en",
                "enabled": "1",
                "label_en": "DANGER",
                "label_es": "PELIGRO",
            },
        ]

    def test_render_symbols_page_happy_path(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(),
        )
        self.assertNotIn("DANGER", out)
        self.assertNotIn("This device is intended for indoor use only", out)
        self.assertIn("MEANING OF SYMBOLS", out)
        self.assertIn("Data warning.", out)
        self.assertIn("read_manual_operator.png", out)
        self.assertIn("Do not dismantle.", out)
        self.assertIn("hb-warning-lockup", out)
        self.assertIn("<span>WARNING</span>", out)
        self.assertIn(":alt: warning_triangle", out)
        self.assertNotIn("Warning signal symbol.", out)
        self.assertNotIn("Warning symbol.", out)

    def test_render_symbols_page_should_not_render_safety_danger_notice(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(),
        )
        self.assertNotIn("**DANGER**", out)
        self.assertNotIn("This device is not waterproof or dustproof.", out)
        self.assertNotIn("\n- This device is intended for indoor use only", out)

    def test_render_symbols_page_should_not_render_user_maintenance_section(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(),
        )

        self.assertTrue(out.startswith("MEANING OF SYMBOLS\n==================\n\n.. only:: latex"))
        self.assertNotIn("\n|\n\n.. only:: latex", out)
        self.assertNotIn("USER MAINTENANCE INSTRUCTIONS", out)
        self.assertNotIn("During the lifecycle of energy storage products", out)
        self.assertIn("\n\n.. only:: not latex\n\n   .. list-table::", out)

    def test_render_symbols_page_should_seed_rst_title_hierarchy_with_page_title_only(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(),
        )

        page_title = "MEANING OF SYMBOLS\n=================="
        self.assertIn(page_title, out)
        self.assertNotIn("USER MAINTENANCE INSTRUCTIONS", out)
        self.assertNotIn(r"\section{MEANING OF SYMBOLS}", out)

    def test_render_symbols_page_emits_latex_notice_and_symbol_macros(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(),
        )

        self.assertNotIn(r"\HBNoticeBlock{DANGER}", out)
        self.assertIn(r"\HBSymbolTable{Symbol}{Meaning}{%", out)
        self.assertIn(r"\HBSymbolSignalRow{warning_triangle.png}{WARNING}{Data warning.}", out)
        self.assertIn(r"\HBSymbolIconRow{warning_triangle.png}{Warning symbol meaning.}", out)
        self.assertIn(".. only:: not latex", out)
        self.assertIn("hb-warning-lockup", out)

    def test_render_symbols_page_latex_image_args_use_basenames(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Figure"] = "data/phase2/_attachments/symbols/10_warning_triangle.png"
        blocks[1]["image_path"] = "custom/symbols/read_manual_operator.png"

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(),
        )

        self.assertIn(r"\HBSymbolIconRow{10_warning_triangle.png}{Warning symbol meaning.}", out)
        self.assertIn(r"\HBSymbolIconRow{read_manual_operator.png}{Read the manual.}", out)
        self.assertNotIn(r"\HBSymbolIconRow{data/phase2/_attachments", out)
        self.assertNotIn(r"\HBSymbolIconRow{custom/symbols", out)

    def test_render_symbols_page_uses_image_path_from_blocks(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["image_path"] = "custom/symbols/warning_triangle.png"
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(),
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
            vars_map=self._localized_copy_vars(),
        )

        self.assertIn("data/phase2/_attachments/symbols/10_warning_triangle.png", out)
        self.assertNotIn(r"\HBSymbolIconRow{warning_triangle.png}", out)

    def test_render_symbols_page_resolves_figure_attachment_json(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Figure"] = '{"file_token":"warning_token","name":"warning.svg"}'
        blocks[0]["image_path"] = "templates/word_template/common_assets/symbols/warning_triangle.png"

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(),
        )

        self.assertIn(".. image:: data/phase2/_attachments/symbols/warning_token.svg", out)

    def test_render_symbols_page_uses_language_specific_copy(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="fr",
            vars_map=self._localized_copy_vars(),
        )
        self.assertIn("SIGNIFICATION DES SYMBOLES", out)
        self.assertIn("Symbole", out)
        self.assertIn("Signification du symbole d'avertissement.", out)

    def test_render_symbols_page_should_not_render_french_danger_notice_copy(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="fr",
            vars_map=self._localized_copy_vars(),
        )
        self.assertIn("<span>AVERTISSEMENT</span>", out)
        self.assertIn("<span>ATTENTION</span>", out)
        self.assertNotIn(
            "Cet appareil est destiné à un usage intérieur uniquement (veuillez placer cet appareil dans un environnement intérieur similaire lors de son utilisation à l'extérieur, par exemple dans des VR résidentiels, des tentes, des chalets, etc.).",
            out,
        )
        self.assertNotIn(
            "※ Cet appareil n'est pas étanche ni résistant à la poussière. Éloignez-le de la pluie et des environnements humides pendant son utilisation.",
            out,
        )

    def test_render_symbols_page_should_not_render_spanish_danger_notice_copy(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="es",
            vars_map=self._localized_copy_vars(),
        )
        self.assertIn("<span>ADVERTENCIA</span>", out)
        self.assertNotIn("**DANGER**", out)
        self.assertNotIn(
            "Este dispositivo está diseñado únicamente para uso en interiores (coloque este dispositivo en un ambiente similar a interiores cuando lo use en exteriores, ej. autocaravanas, tiendas de campaña, cabañas, etc.).",
            out,
        )
        self.assertNotIn(
            "※ Este dispositivo no es resistente al agua ni al polvo. Manténgalo alejado de la lluvia y ambientes húmedos durante su uso.",
            out,
        )

    def test_render_symbols_page_uses_clean_spanish_signal_copy(self) -> None:
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=self._symbols_blocks(),
            sku_id="JB1000",
            lang="es",
            vars_map=self._localized_copy_vars(),
        )

        self.assertIn("SIGNIFICADO DE LOS SÍMBOLOS", out)
        self.assertIn("Símbolo", out)
        self.assertIn("Advertencia desde datos.", out)
        self.assertIn("Consejo desde datos.", out)
        self.assertNotIn("S铆mbolo", out)
        self.assertNotIn("Pr谩cticas", out)
        self.assertNotIn("informaci贸n", out)

    def test_render_symbols_page_can_source_signal_rows_from_symbols_blocks(self) -> None:
        blocks = [block for block in self._symbols_blocks() if block.get("block_type") != "signal_row"]
        blocks.extend(
            [
                {
                    "block_type": "signal_row",
                    "symbol_key": "WARNING",
                    "image_path": "templates/word_template/common_assets/symbols/warning_triangle.png",
                    "order": "1",
                    "Market": "EU",
                    "Model": "JE-1000F",
                    "Source_lang": "en",
                    "enabled": "1",
                    "text_en": "Data warning.",
                    "text_fr": "Avertissement de données.",
                    "text_es": "Advertencia desde datos.",
                },
                {
                    "block_type": "signal_row",
                    "symbol_key": "CAUTION",
                    "image_path": "templates/word_template/common_assets/symbols/warning_triangle.png",
                    "order": "2",
                    "Market": "EU",
                    "Model": "JE-1000F",
                    "Source_lang": "en",
                    "enabled": "1",
                    "text_en": "Data caution.",
                    "text_fr": "Attention de données.",
                    "text_es": "Precaución desde datos.",
                },
                {
                    "block_type": "signal_row",
                    "symbol_key": "NOTE",
                    "image_path": "templates/word_template/common_assets/symbols/mandatory.png",
                    "order": "3",
                    "Market": "EU",
                    "Model": "JE-1000F",
                    "Source_lang": "en",
                    "enabled": "1",
                    "text_en": "Data note.",
                    "text_fr": "Remarque de données.",
                    "text_es": "Nota desde datos.",
                },
                {
                    "block_type": "signal_row",
                    "symbol_key": "TIPS",
                    "image_path": "templates/word_template/common_assets/symbols/mandatory.png",
                    "order": "4",
                    "Market": "EU",
                    "Model": "JE-1000F",
                    "Source_lang": "en",
                    "enabled": "1",
                    "text_en": "Data tip.",
                    "text_fr": "Conseil de données.",
                    "text_es": "Consejo desde datos.",
                },
            ]
        )

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="es",
            vars_map=self._localized_copy_vars(model="JE-1000F", region="EU"),
        )

        self.assertIn("Advertencia desde datos.", out)
        self.assertIn("Consejo desde datos.", out)
        self.assertIn(r"\HBSymbolSignalRow{warning_triangle.png}{ADVERTENCIA}{Advertencia desde datos.}", out)
        self.assertIn("Significado del símbolo de advertencia.", out)
        self.assertNotIn("Prácticas peligrosas que pueden resultar en lesiones graves", out)

    def test_render_symbols_page_resolves_signal_labels_from_localized_copy(self) -> None:
        blocks = self._symbols_blocks()
        for block in blocks:
            if block.get("block_type") == "signal_row":
                block["label_en"] = f"ROW_{block['symbol_key']}"
                block["text_en"] = f"ROW_TEXT_{block['symbol_key']}"

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(),
        )

        self.assertIn(r"\HBSymbolSignalRow{warning_triangle.png}{WARNING}{Data warning.}", out)
        self.assertIn("<span>CAUTION</span>", out)
        self.assertNotIn("ROW_WARNING", out)
        self.assertNotIn("ROW_TEXT_WARNING", out)

    def test_render_symbols_page_filters_by_market_and_model(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Market"] = "US"
        blocks[0]["Model"] = "JE-1000F"
        blocks[0]["text_en"] = "US JE-1000F warning."
        blocks[1]["Market"] = "JP"
        blocks[1]["Model"] = "JE-9999X"
        blocks[1]["text_en"] = "SHOULD_NOT_RENDER"
        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(model="JE-1000F", region="US"),
        )
        self.assertIn("US JE-1000F warning.", out)
        self.assertNotIn("SHOULD_NOT_RENDER", out)

    def test_render_symbols_page_filters_inactive_rows(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Is_latest"] = "False"
        blocks[0]["text_en"] = "SHOULD_NOT_RENDER"
        blocks.append(
            {
                "block_type": "table_row",
                "symbol_key": "electric_shock",
                "image_path": "templates/word_template/common_assets/symbols/electric_shock.png",
                "order": "30",
                "Market": "Global",
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
            vars_map=self._localized_copy_vars(),
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
            vars_map=self._localized_copy_vars(region="EU"),
        )

        self.assertNotIn("US-only warning.", out)
        self.assertIn("Shared read manual.", out)
        self.assertIn("Do not dismantle.", out)

    def test_render_symbols_page_filters_by_space_separated_market(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Market"] = "US EU"
        blocks[0]["text_en"] = "Shared warning."
        blocks[1]["Market"] = "US"
        blocks[1]["text_en"] = "SHOULD_NOT_RENDER"

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(region="EU"),
        )

        self.assertIn("Shared warning.", out)
        self.assertNotIn("SHOULD_NOT_RENDER", out)

    def test_render_symbols_page_filters_by_market_json_list(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Market"] = '[{"text":"US"},{"text":"EU"}]'
        blocks[0]["text_en"] = "Shared warning."

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(region="EU"),
        )

        self.assertIn("Shared warning.", out)

    def test_render_symbols_page_uses_market_and_multi_model(self) -> None:
        blocks = self._symbols_blocks()
        blocks[0]["Market"] = "US, EU"
        blocks[0]["Model"] = "JE-1000F, JE-2000E"
        blocks[0]["text_de"] = "Gemeinsames EU-Symbol."
        blocks[1]["Market"] = "US"
        blocks[1]["Model"] = "JE-1000F, JE-2000E"
        blocks[1]["text_de"] = "SHOULD_NOT_RENDER"
        blocks[2]["Market"] = "US, EU"
        blocks[2]["Model"] = "JE-1000F"
        blocks[2]["text_de"] = "JE-1000F only."

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JE-2000E",
            lang="de",
            vars_map=self._localized_copy_vars(model="JE-2000E", region="EU"),
        )

        self.assertIn("Gemeinsames EU-Symbol.", out)
        self.assertNotIn("SHOULD_NOT_RENDER", out)
        self.assertNotIn("JE-1000F only.", out)

    def test_render_symbols_page_auto_distributes_unique_order_rows(self) -> None:
        blocks = self._symbols_blocks()
        rows = [
            ("warning_triangle", "1", "Order 1."),
            ("read_manual", "2", "Order 2."),
            ("electric_shock", "3", "Order 3."),
            ("do_not_dismantle", "4", "Order 4."),
            ("weee", "5", "Order 5."),
        ]
        table_blocks = [block for block in blocks if block.get("block_type") == "table_row"]
        for block, (symbol_key, order, text) in zip(table_blocks, rows):
            block["symbol_key"] = symbol_key
            block["order"] = order
            block["text_en"] = text
        for symbol_key, order, text in rows[len(table_blocks) :]:
            blocks.append(
                {
                    "block_type": "table_row",
                    "symbol_key": symbol_key,
                    "image_path": f"templates/word_template/common_assets/symbols/{symbol_key}.png",
                    "order": order,
                    "Market": "Global",
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
            vars_map=self._localized_copy_vars(),
        )

        order_positions = [out.index(f"Order {idx}.") for idx in range(1, 6)]
        self.assertLess(order_positions[0], order_positions[3])
        self.assertLess(order_positions[3], order_positions[1])
        self.assertLess(order_positions[1], order_positions[4])
        self.assertLess(order_positions[4], order_positions[2])

    def test_render_symbols_page_should_use_market_field(self) -> None:
        blocks = self._symbols_blocks()
        for block in blocks:
            block["Market"] = "EU"
            block["Model"] = "JE-1000F"

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(model="JE-1000F", region="EU"),
        )

        self.assertIn("Warning symbol meaning.", out)
        self.assertIn("Do not dismantle.", out)

    def test_render_symbols_page_should_normalize_document_key_style_target_model(self) -> None:
        blocks = self._symbols_blocks()
        for block in blocks:
            block["Market"] = "US"
            block["Model"] = "JE-1000F"

        out = renderers.render_symbols_page(
            template=self._symbols_template(),
            blocks=blocks,
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(model="JE-1000F_US", region="US"),
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
                "Market": "Global",
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
            vars_map=self._localized_copy_vars(),
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
                    "Market": "Global",
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
                    "Market": "Global",
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
                    "Market": "Global",
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
            vars_map=self._localized_copy_vars(),
        )

        self.assertEqual(2, out.count(".. list-table::"))
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
                vars_map=self._localized_copy_vars(),
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
                vars_map=self._localized_copy_vars(
                    model="JE-1000F",
                    variable_defaults_csv=str(defaults),
                    variable_lang_overrides_csv=str(overrides),
                ),
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

    def test_render_lcd_icons_page_emits_latex_macro_table_with_basename_images(self) -> None:
        blocks = [
            {
                "No.": "7",
                "Model": "JE-1000F",
                "Is_latest": "TRUE",
                "icon_en": "Battery 50% & AC",
                "icon_desc_en": "On: Charge_#1 & ready.\nOff: 0% $idle$.",
                "figure": "data/phase2/_attachments/lcd_icons/7_Battery_AC.png",
            }
        ]

        out = renderers.render_lcd_icons_page(
            template=self._lcd_template(),
            blocks=blocks,
            sku_id="",
            lang="en",
            vars_map=self._localized_copy_vars(model="JE-1000F"),
        )

        row_line = next(line for line in out.splitlines() if r"\HBLcdIconRow" in line)
        self.assertIn(".. only:: not latex", out)
        self.assertIn(".. list-table::", out)
        self.assertIn(".. only:: latex", out)
        self.assertIn(r"\begin{HBLcdIconTable}", out)
        self.assertIn(r"\end{HBLcdIconTable}", out)
        self.assertIn("{7_Battery_AC.png}", row_line)
        self.assertNotIn("data/phase2", row_line)
        self.assertIn(r"{Battery 50\% \& AC}", row_line)
        self.assertIn(
            r"{\textbf{On:} Charge\_\#1 \& ready. \newline \textbf{Off:} 0\% \$idle\$.}",
            row_line,
        )

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
                vars_map=self._localized_copy_vars(
                    model="JE-1000F_US",
                    region="US",
                    variable_defaults_csv=str(defaults),
                    variable_lang_overrides_csv=str(overrides),
                ),
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
            vars_map=self._localized_copy_vars(model="JE-1000F"),
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
            vars_map=self._localized_copy_vars(model="JE-1000F"),
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
            vars_map=self._localized_copy_vars(model="JE-1000F"),
        )

        self.assertIn("     - | **On:** Wi-Fi connected.", out)
        self.assertIn("       | **Blink:** Ready to connect to Wi-Fi.", out)
        self.assertIn("       | **Off:** Wi-Fi disconnected.", out)

    def test_render_lcd_icons_page_supports_zh_columns(self) -> None:
        blocks = [
            {
                "No.": "1",
                "Model": "JE-1000F",
                "Is_latest": "TRUE",
                "icon_en": "Wi-Fi",
                "icon_zh": "Wi-Fi",
                "icon_desc_zh": "点亮：Wi-Fi 已连接。\\n闪烁：准备连接 Wi-Fi。\\n熄灭：Wi-Fi 未连接。",
                "figure": "data/phase2/_attachments/lcd_icons/1_Wi-Fi.png",
            }
        ]

        out = renderers.render_lcd_icons_page(
            template=self._lcd_template(),
            blocks=blocks,
            sku_id="",
            lang="zh",
            vars_map=self._localized_copy_vars(model="JE-1000F"),
        )

        self.assertIn("显示屏界面", out)
        self.assertNotIn("LCD 图标示意图。", out)
        self.assertIn("     - | **点亮：** Wi-Fi 已连接。", out)
        self.assertIn("       | **闪烁：** 准备连接 Wi-Fi。", out)
        self.assertIn("       | **熄灭：** Wi-Fi 未连接。", out)

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
                vars_map=self._localized_copy_vars(
                    model="JE-1000F",
                    variable_defaults_csv=str(defaults),
                    variable_lang_overrides_csv=str(overrides),
                ),
            )
            ja_out = renderers.render_lcd_icons_page(
                template=self._lcd_template(),
                blocks=self._lcd_blocks(),
                sku_id="",
                lang="ja",
                vars_map=self._localized_copy_vars(
                    model="JE-1000F",
                    variable_defaults_csv=str(defaults),
                    variable_lang_overrides_csv=str(overrides),
                ),
            )
            uk_out = renderers.render_lcd_icons_page(
                template=self._lcd_template(),
                blocks=self._lcd_blocks(),
                sku_id="",
                lang="uk",
                vars_map=self._localized_copy_vars(
                    model="JE-1000F",
                    variable_defaults_csv=str(defaults),
                    variable_lang_overrides_csv=str(overrides),
                ),
            )

        self.assertIn("When the CA or CC/USB output is on:", fr_out)
        self.assertIn("液晶画面", ja_out)
        self.assertNotIn("LCDアイコンマップ。", ja_out)
        self.assertIn("AC_UKR / DC_UKR", uk_out)
        self.assertIn("ЕКРАН LCD", uk_out)
        self.assertNotIn("Заглушка схеми значків LCD.", uk_out)

    def test_render_lcd_icons_page_supports_pt_br_columns_and_br_variable_overrides(self) -> None:
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
                "Variable_key,lang,source_value,Value\n"
                "AC_POWER_BUTTON_LABEL,br,AC,CA\n"
                "DC_USB_POWER_BUTTON_LABEL,pt-BR,DC/USB,CC/USB\n",
                encoding="utf-8",
            )
            blocks = [
                {
                    "No.": "4",
                    "Model": "JE-1000F",
                    "Is_latest": "TRUE",
                    "icon_en": "Charging Plan",
                    "icon_pt-BR": "test",
                    "icon_desc_en": "Customizes the charging time of the {{PRODUCT_NAME}}.",
                    "icon_desc_pt-BR": "test",
                    "variable_keys": "PRODUCT_NAME",
                },
                {
                    "No.": "22",
                    "Model": "JE-1000F",
                    "Is_latest": "TRUE",
                    "icon_en": "Energy Saving Mode",
                    "icon_pt-BR": "Modo de economia de energia",
                    "icon_desc_en": "When the {{AC_POWER_BUTTON_LABEL}} or {{DC_USB_POWER_BUTTON_LABEL}} output is on.",
                    "icon_desc_pt-BR": (
                        "Quando a saída {{AC_POWER_BUTTON_LABEL}} ou {{DC_USB_POWER_BUTTON_LABEL}} estiver ligada:\n"
                        "Ligado: Modo de economia de energia ativado.\n"
                        "Desligado: Modo de economia de energia desativado."
                    ),
                    "variable_keys": "AC_POWER_BUTTON_LABEL, DC_USB_POWER_BUTTON_LABEL",
                }
            ]

            out = renderers.render_lcd_icons_page(
                template=self._lcd_template(),
                blocks=blocks,
                sku_id="",
                lang="pt-BR",
                vars_map=self._localized_copy_vars(
                    model="JE-1000F",
                    product_name="Jackery Explorer 1500",
                    variable_defaults_csv=str(defaults),
                    variable_lang_overrides_csv=str(overrides),
                ),
            )

        self.assertIn("TELA LCD", out)
        self.assertNotIn("Mapa de ícones da tela LCD.", out)
        self.assertIn("Modo de economia de energia", out)
        self.assertIn("Quando a saída CA ou CC/USB estiver ligada:", out)
        self.assertIn("| **Ligado:** Modo de economia de energia ativado.", out)
        self.assertIn("| **Desligado:** Modo de economia de energia desativado.", out)

    def _troubleshooting_template(self) -> str:
        return (
            "TROUBLESHOOTING\n"
            "===============\n\n"
            "Intro text owned by the RST template.\n\n"
            ".. list-table::\n"
            "   :header-rows: 1\n"
            "   :widths: 14 86\n\n"
            "   * - Error Code\n"
            "     - Corrective Measures\n"
            + renderers.PH_TROUBLESHOOTING_ROWS_RST
        )

    def test_render_troubleshooting_page_filters_region_and_preserves_multiline_rst(self) -> None:
        blocks = [
            {
                "No.": "",
                "Model": "",
                "Region": "",
                "Is_latest": "TRUE",
                "error_code": "",
                "corrective_measures_en": "",
            },
            {
                "No.": "2",
                "Model": "ALL",
                "Region": "US",
                "Is_latest": "TRUE",
                "error_code": "F7",
                "corrective_measures_en": (
                    "1. Remove all DC inputs from the product.\n"
                    "2. Check the open-circuit voltage (V\\ :sub:`oc`) of the connected solar panels."
                ),
            },
            {
                "No.": "1",
                "Model": "ALL",
                "Region": "US",
                "Is_latest": "TRUE",
                "error_code": "F0",
                "corrective_measures_en": "Restart the product.",
            },
            {
                "No.": "3",
                "Model": "ALL",
                "Region": "EU",
                "Is_latest": "TRUE",
                "error_code": "F8",
                "corrective_measures_en": "EU-only row.",
            },
            {
                "No.": "4",
                "Model": "ALL",
                "Region": "US",
                "Is_latest": "FALSE",
                "error_code": "FE",
                "corrective_measures_en": "Old row.",
            },
        ]

        out = renderers.render_troubleshooting_page(
            template=self._troubleshooting_template(),
            blocks=blocks,
            sku_id="",
            lang="en",
            vars_map={"model": "JE-1000F", "region": "US"},
        )

        self.assertIn("TROUBLESHOOTING\n===============", out)
        self.assertIn("   :header-rows: 1", out)
        self.assertLess(out.index("F0"), out.index("F7"))
        self.assertIn("     - | 1. Remove all DC inputs from the product.", out)
        self.assertIn("       | 2. Check the open-circuit voltage (V\\ :sub:`oc`) of the connected solar panels.", out)
        self.assertNotIn("EU-only row.", out)
        self.assertNotIn("Old row.", out)

    def test_render_troubleshooting_page_supports_pt_br_columns_and_region_alias(self) -> None:
        blocks = [
            {
                "No.": "1",
                "Model": "ALL",
                "Region": "br",
                "Is_latest": "TRUE",
                "error_code": "F0",
                "corrective_measures_en": "English fallback.",
                "corrective_measures_pt-BR": "Medida PT-BR.",
                "corrective_measures_br": "Medida BR.",
            }
        ]

        out = renderers.render_troubleshooting_page(
            template=self._troubleshooting_template(),
            blocks=blocks,
            sku_id="",
            lang="pt-BR",
            vars_map={"model": "JE-1000F", "region": "pt-BR"},
        )

        self.assertIn("F0", out)
        self.assertIn("Medida PT-BR.", out)
        self.assertNotIn("English fallback.", out)
        self.assertNotIn("Medida BR.", out)

    def test_collect_spec_content_supports_spec_master_schema(self) -> None:
        data = renderers.collect_spec_content(
            blocks=self._spec_master_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map=self._localized_copy_vars(),
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
            vars_map=self._localized_copy_vars(model="JHP-2000A"),
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
