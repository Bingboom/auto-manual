"""Characterize each consumer's frozen CSV policy, including intentional differences."""
from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from tools.csv_pages import BuildPaths, BuildSelector, CsvPageBuilder
from tools.csv_pages.renderers_lcd_icons import _collect_rows as lcd_rows
from tools.csv_pages.renderers_spec_parser import _pick_spec_lang_text
from tools.csv_pages.renderers_symbols import _collect_icon_rows
from tools.csv_pages.renderers_troubleshooting import _collect_rows as trouble_rows
from tools.idml.loaders import load_spec_annotations, load_spec_sections, load_symbols_rows

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "phase2"


def write_rows(root: Path, filename: str, rows: list[dict[str, str]]) -> None:
    with (root / filename).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dict.fromkeys(key for row in rows for key in row)))
        writer.writeheader()
        writer.writerows(rows)


class TestSnapshotConsumerPolicies(unittest.TestCase):
    def test_idml_spec_keeps_localized_then_source_without_english_fallback(self) -> None:
        row = {"document_key": "DEMO_JP", "Page": "specifications", "Is_Latest": "TRUE",
               "Section": "INPUT", "Row_label_source": "Source label", "Row_label_en": "English label",
               "Value_source": "100 V", "Value_en": "120 V", "Value_jp": "110 V", "Value_ja": "115 V"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for primary, secondary, expected in (("110 V", "115 V", "110 V"),
                                                  (" \t ", "115 V", "115 V"),
                                                  ("", "", "100 V")):
                row.update(Value_jp=primary, Value_ja=secondary)
                write_rows(root, "Spec_Master.csv", [row])
                result = load_spec_sections(root, "DEMO", "JP", "ja")
                self.assertEqual([("Source label", expected)], result[0]["rows"])
            row["Value_source"] = ""
            write_rows(root, "Spec_Master.csv", [row])
            self.assertEqual("", load_spec_sections(root, "DEMO", "JP", "ja")[0]["rows"][0][1])

    def test_idml_symbols_keep_single_suffix_and_per_cell_english_fallback(self) -> None:
        row = {"Is_Latest": "TRUE", "block_type": "signal_row", "order": "1",
               "label_ja": "Japanese label", "text_ja": "Japanese text",
               "label_en": "English label", "text_en": "English text"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_rows(root, "symbols_blocks.csv", [row])
            self.assertEqual([("English label", "English text")], load_symbols_rows(root, "ja")[0])
            row.update(label_jp="日本語", text_jp=" \t ")
            write_rows(root, "symbols_blocks.csv", [row])
            self.assertEqual([("日本語", "English text")], load_symbols_rows(root, "jp")[0])

    def test_csv_table_headers_choose_one_alias_before_per_cell_fallback(self) -> None:
        for collect, base, result_key, required in (
            (lcd_rows, "icon_desc", "description", {"icon_en": "Wi-Fi"}),
            (trouble_rows, "corrective_measures", "measures", {"error_code": "F0"}),
        ):
            row = {**required, "No.": "1", f"{base}_pt-BR": "", f"{base}_br": "Brazilian",
                   f"{base}_en": "English"}
            with self.subTest(base=base):
                self.assertEqual("English", collect([row], lang="br", vars_map={})[0][result_key])
                del row[f"{base}_pt-BR"]
                self.assertEqual("Brazilian", collect([row], lang="pt-BR", vars_map={})[0][result_key])
                row[f"{base}_pt-BR"] = " \t "
                with self.assertRaisesRegex(ValueError, "no matching rows"):
                    collect([row], lang="br", vars_map={})

    def test_csv_table_suffixes_use_table_metadata_not_global_aliases(self) -> None:
        row = {"No.": "1", "icon_en": "Wi-Fi", "icon_desc_en": "English",
               "icon_desc_uk": "wrong global alias", "icon_desc_ukr": "Українська",
               "icon_desc_ja": "wrong global alias", "icon_desc_jp": "日本語"}
        for lang, expected in (("uk", "Українська"), ("ukr", "Українська"),
                               ("ja", "日本語"), ("jp", "日本語")):
            self.assertEqual(expected, lcd_rows([row], lang=lang, vars_map={})[0]["description"])
        with self.assertRaisesRegex(ValueError, "missing language description column"):
            lcd_rows([{"icon_en": "Wi-Fi"}], lang="uk", vars_map={})
        with self.assertRaisesRegex(ValueError, "missing language corrective-measures column"):
            trouble_rows([{"error_code": "F0"}], lang="ja", vars_map={})

    def test_csv_symbols_missing_column_can_fall_back_but_empty_cell_is_error(self) -> None:
        row = {"block_type": "table_row", "symbol_key": "read_manual", "order": "1", "Market": "ALL",
               "Source_lang": "fr", "text_fr": "Source", "text_en": "English"}

        def text() -> str:
            groups = _collect_icon_rows([row], sku_id="", lang="ja", vars_map={})
            return next(item["text"] for group in groups.values() for item in group)

        self.assertEqual("Source", text())
        row["text_jp"] = "Historical"
        self.assertEqual("Historical", text())
        row["text_ja"] = ""
        with self.assertRaisesRegex(ValueError, "missing text_ja text"):
            text()
        row["text_ja"] = " \t "
        with self.assertRaisesRegex(ValueError, "missing text_ja text"):
            text()

    def test_csv_spec_source_language_policy_and_input_alias_order(self) -> None:
        row = {"Source_lang": "ja", "Value_source": "100 V", "Value_jp": "110 V",
               "Value_ja": "115 V", "Value_en": "120 V", "Value": "90 V", "last": "80 V"}
        for lang in ("en", "ja", "jp"):
            self.assertEqual("100 V", _pick_spec_lang_text(row, base="Value", lang=lang))
        row["Source_lang"] = "en"
        for lang, expected in (("ja", "115 V"), ("jp", "110 V")):
            self.assertEqual(expected, _pick_spec_lang_text(row, base="Value", lang=lang))
        row.update(Value_ja=" \t ", Value_jp="", Value_source="")
        self.assertEqual("90 V", _pick_spec_lang_text(row, base="Value", lang="ja", default_keys=["last"]))
        row["Value"] = ""
        self.assertEqual("80 V", _pick_spec_lang_text(row, base="Value", lang="ja", default_keys=["last"]))
        self.assertEqual("", _pick_spec_lang_text(row, base="Value", lang="ja"))

    def test_csv_trailer_canonical_column_raw_emptiness_and_no_english_fallback(self) -> None:
        read = CsvPageBuilder._localized_text_value
        row = {"Text_ja": "Japanese", "Text_jp": "Historical", "Text_en": "English"}
        self.assertEqual("Japanese", read(row, "jp"))
        row["Text_ja"] = ""
        self.assertEqual("Historical", read(row, "ja"))
        row["Text_ja"] = " \t "
        self.assertEqual(" \t ", read(row, "jp"))
        self.assertEqual("", read({"Text_en": "English"}, "ja"))
        self.assertEqual("bare", read({"Text_pt-BR": "", "pt-BR": "bare", "Text_br": "alias"}, "br"))
        self.assertEqual("legacy", read({"Text_": "legacy", "Text_en": "English"}, ""))

    def test_frozen_jp_and_french_builds_keep_content_order_units_and_annotations(self) -> None:
        paths = replace(BuildPaths.from_root(ROOT), page_registry=FIXTURES / "page_registry.csv",
                        page_blocks_dir=FIXTURES, spec_master_csv=FIXTURES / "Spec_Master.csv",
                        spec_footnotes_csv=FIXTURES / "Spec_Footnotes.csv",
                        spec_notes_csv=FIXTURES / "Spec_Notes.csv", spec_titles_csv=FIXTURES / "spec_titles.csv",
                        localized_copy_csv=FIXTURES / "Localized_Copy.csv")
        for region, lang, unit, labels in (
            ("JP", "ja", "1024Wh (20Ah/51.2V DC)", ("製品の名称", "型番", "定格容量")),
            ("US", "fr", "1024 Wh (20 Ah/51,2 V CC)", ("Nom du produit", "N° modèle", "Capacité")),
        ):
            with self.subTest(region=region), tempfile.TemporaryDirectory() as tmp:
                result = CsvPageBuilder(replace(paths, output_dir=Path(tmp))).build(
                    BuildSelector.from_args(models="JE-1000F", regions=region, langs=lang))
                self.assertEqual([], result.skipped_pages)
                self.assertEqual([f"{page}_{lang}.rst" for page in ("symbols", "lcd_icons", "troubleshooting", "spec")],
                                 [path.name for path in result.written_files])
                spec = result.written_files[-1].read_text(encoding="utf-8")
                self.assertIn(unit, spec)
                self.assertLess(spec.index(labels[0]), spec.index(labels[1]))
                self.assertLess(spec.index(labels[1]), spec.index(labels[2]))
                sections = load_spec_sections(FIXTURES, "JE-1000F", region, lang)
                self.assertEqual(list(labels), [label for label, _ in sections[0]["rows"][:3]])
                self.assertEqual(unit, sections[0]["rows"][2][1])
        # This fallback belongs to IDML annotations; CSV trailers stay empty.
        self.assertEqual(load_spec_annotations(FIXTURES, "JE-1000F", "US", "en"),
                         load_spec_annotations(FIXTURES, "JE-1000F", "US", "ja"))
