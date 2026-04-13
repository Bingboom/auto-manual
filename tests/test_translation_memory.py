from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_helpers import write_lines, write_text
from tools.translation_memory import (
    build_translation_memory_payload,
    collect_translation_memory_entries,
    query_translation_memory_entries,
    render_translation_prompt_context,
    render_translation_memory_payload,
    split_translation_units,
)


def _write_phase2_fixture(root: Path) -> Path:
    config_path = root / "config.test.yaml"
    write_text(
        config_path,
        "paths:\n"
        "  structured_data_dir: data/phase2\n",
    )
    phase2_dir = root / "data" / "phase2"
    write_lines(
        phase2_dir / "Spec_Master.csv",
        [
            "document_key,Region,Is_Latest,Page,Section,Section_order,Row_order,Row_key,Slot_key,Row_label_source,Row_label_footnote_refs,Line_order,Param_source,Param_footnote_refs,Value_source,Value_footnote_refs,Row_label_fr,Param_fr,Value_fr,Row_label_es,Model,Param_es,Value_es,Source_lang",
            "JE-1000F_US,US,TRUE,operation_guide,OUTPUT PORTS,3,1,usb_c_high_power_port,label,USB-C 100W Port,,1,Charging power,,100W,,Port USB-C 100 W,Puissance de charge,100 W,Puerto USB-C de 100 W,JE-1000F,Potencia de carga,100 W,en",
        ],
    )
    write_lines(
        phase2_dir / "spec_titles.csv",
        [
            "title_en,section_order,title_zh,title_jp,title_fr,title_es",
            "OUTPUT PORTS,3,输出端口,出力ポート,PORTS DE SORTIE,PUERTOS DE SALIDA",
        ],
    )
    write_lines(
        phase2_dir / "Spec_Notes.csv",
        [
            "Note_id,Region,Model,Source_lang,Is_Latest,Page,Note_order,Text_en,Text_fr,Text_es,Text_ja,Enabled",
            "note_usb,US,JE-1000F,en,TRUE,operation_guide,1,Keep the port dry,Gardez le port au sec,Mantenga seco el puerto,,TRUE",
        ],
    )
    write_lines(
        phase2_dir / "Spec_Footnotes.csv",
        [
            "Footnote_id,Region,Model,Source_lang,Is_Latest,Page,Footnote_order,Text_en,Text_fr,Text_es,Text_ja,Enabled",
            "footnote_usb,US,JE-1000F,en,TRUE,operation_guide,1,Use certified cable,Utilisez un câble certifié,Use un cable certificado,,TRUE",
        ],
    )
    write_lines(
        phase2_dir / "row_key_mapping.csv",
        [
            "Row_label_source,Line_order,Row_key,Remark",
            "USB-C 100W Port,1,usb_c_high_power_port,charging port",
        ],
    )
    write_lines(
        phase2_dir / "symbols_blocks.csv",
        [
            "page_id,image_path,symbol_key,text_en,text_fr,text_es,enabled,block_type,column_group,order,Region,Model,Source_lang",
            "symbols,templates/symbols/warning_triangle.png,warning_triangle,Warning and Caution Symbols.,Symboles d'avertissement et de prudence.,Símbolos de advertencia y precaución.,TRUE,table_row,left,10,US,JE-1000F,en",
        ],
    )
    return config_path


class TestTranslationMemory(unittest.TestCase):
    def test_collect_translation_memory_entries_should_build_entries_from_phase2_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = _write_phase2_fixture(root)

            entries, snapshot_root = collect_translation_memory_entries(
                config_path=config_path,
                repo_root=root,
                model="JE-1000F",
                region="US",
            )

            self.assertEqual(root / "data" / "phase2", snapshot_root)
            self.assertTrue(any(entry.table == "spec-master" and entry.entry_type == "row-label" for entry in entries))
            self.assertTrue(any(entry.table == "spec-notes" for entry in entries))
            self.assertTrue(any(entry.table == "symbols-blocks" for entry in entries))

    def test_query_translation_memory_entries_should_match_aliases_and_preferred_language(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = _write_phase2_fixture(root)
            entries, _ = collect_translation_memory_entries(
                config_path=config_path,
                repo_root=root,
                model="JE-1000F",
                region="US",
            )

            matched = query_translation_memory_entries(
                entries,
                query_text="charging port",
                preferred_lang="fr",
                tables=["spec-master"],
                limit=3,
            )

            self.assertGreaterEqual(len(matched), 1)
            self.assertEqual("spec-master", matched[0].table)
            self.assertEqual("usb_c_high_power_port", matched[0].row_key)
            self.assertTrue(any(entry.translations.get("fr") == "Port USB-C 100 W" for entry in matched))

    def test_build_translation_memory_payload_should_render_prompt_ready_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = _write_phase2_fixture(root)

            payload = build_translation_memory_payload(
                config_path=config_path,
                repo_root=root,
                model="JE-1000F",
                region="US",
                query_text="USB-C 100W Port",
                preferred_lang="fr",
                tables=["spec-master", "spec-titles"],
                limit=4,
            )
            rendered = render_translation_memory_payload(payload)

            self.assertEqual("data/phase2", payload["snapshot_root"])
            self.assertGreaterEqual(payload["match_count"], 1)
            self.assertIn("Translation Memory Context", rendered)
            self.assertIn("Port USB-C 100 W", rendered)
            self.assertIn("preferred_lang", rendered)

    def test_query_translation_memory_entries_should_respect_source_and_target_language(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = _write_phase2_fixture(root)
            entries, _ = collect_translation_memory_entries(
                config_path=config_path,
                repo_root=root,
                model="JE-1000F",
                region="US",
            )

            matched = query_translation_memory_entries(
                entries,
                query_text="Charging power",
                source_lang="en",
                target_lang="es",
                tables=["spec-master"],
                limit=3,
            )

            self.assertGreaterEqual(len(matched), 1)
            self.assertTrue(all(entry.translations.get("es") for entry in matched))
            self.assertEqual("Potencia de carga", matched[0].translations["es"])

    def test_split_translation_units_should_split_multiline_paragraph(self) -> None:
        units = split_translation_units("WARNING\nRead all the instructions before use. Keep the port dry.")

        self.assertEqual(
            [
                "WARNING",
                "Read all the instructions before use.",
                "Keep the port dry.",
            ],
            units,
        )

    def test_render_translation_prompt_context_should_include_units_and_candidates(self) -> None:
        rendered = render_translation_prompt_context(
            query_text="Read all the instructions before use.",
            source_lang="en",
            target_lang="fr",
            memory_source="lark-base:tbl/view",
            unit_matches=[
                {
                    "source_unit": "Read all the instructions before use.",
                    "match_count": 1,
                    "entries": [
                        {
                            "source_text": "Read all the instructions before use.",
                            "row_key": "rec_123",
                            "translations": {
                                "en": "Read all the instructions before use.",
                                "fr": "Lisez toutes les instructions avant utilisation.",
                            },
                        }
                    ],
                }
            ],
        )

        self.assertIn("OpenClaw Translation Prompt Context", rendered)
        self.assertIn("Source language: `en`", rendered)
        self.assertIn("Target language: `fr`", rendered)
        self.assertIn("Lisez toutes les instructions avant utilisation.", rendered)
