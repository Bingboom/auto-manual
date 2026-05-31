from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_helpers import write_lines, write_text
from tools.translation_memory import (
    build_translation_memory_payload,
    collect_translation_memory_entries,
    query_translation_memory_entries,
    render_translation_prompt_context,
    render_translation_memory_payload,
    split_translation_units,
)

_LIVE_TM_SCRIPT_PATH = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "bitable-translation-memory" / "scripts" / "query_live_translation_memory.py"
_LIVE_TM_SPEC = importlib.util.spec_from_file_location("query_live_translation_memory", _LIVE_TM_SCRIPT_PATH)
if _LIVE_TM_SPEC is None or _LIVE_TM_SPEC.loader is None:
    raise RuntimeError(f"Unable to load {_LIVE_TM_SCRIPT_PATH}")
query_live_translation_memory = importlib.util.module_from_spec(_LIVE_TM_SPEC)
_LIVE_TM_SPEC.loader.exec_module(query_live_translation_memory)


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
            "symbol_key,image_path,text_en,text_fr,text_es,block_type,order,Market,Model,Source_lang",
            "warning_triangle,templates/symbols/warning_triangle.png,Warning and Caution Symbols.,Symboles d'avertissement et de prudence.,Símbolos de advertencia y precaución.,table_row,10,US,JE-1000F,en",
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


class TestLiveTranslationMemoryCache(unittest.TestCase):
    def test_live_translation_memory_should_reuse_recent_cached_snapshot(self) -> None:
        query_text = "Always follow these basic precautions when using this product."
        expected_translation = "Respectez toujours les précautions suivantes lors de l’utilisation du produit."
        rows = [
            {
                "record_id": "recvgEwBBuQ5J6",
                "en": query_text,
                "fr": expected_translation,
            }
        ]

        with tempfile.TemporaryDirectory() as td:
            cache_dir = Path(td)
            cache_key = query_live_translation_memory.build_cache_key(
                wiki_token=query_live_translation_memory.DEFAULT_WIKI_TOKEN,
                base_token=None,
                table_id=query_live_translation_memory.DEFAULT_TABLE_ID,
                view_id=query_live_translation_memory.DEFAULT_VIEW_ID,
                max_records=query_live_translation_memory.DEFAULT_MAX_RECORDS,
            )
            with mock.patch.object(query_live_translation_memory.time, "time", return_value=1000.0):
                query_live_translation_memory.save_cached_table_snapshot(
                    cache_dir=cache_dir,
                    cache_key=cache_key,
                    wiki_token=query_live_translation_memory.DEFAULT_WIKI_TOKEN,
                    table_id=query_live_translation_memory.DEFAULT_TABLE_ID,
                    view_id=query_live_translation_memory.DEFAULT_VIEW_ID,
                    max_records=query_live_translation_memory.DEFAULT_MAX_RECORDS,
                    language_fields=["en", "fr"],
                    rows=rows,
                )

            output = io.StringIO()
            with (
                mock.patch.object(query_live_translation_memory.time, "time", return_value=1001.0),
                mock.patch.object(query_live_translation_memory, "resolve_lark_cli", side_effect=AssertionError("cache hit should skip lark-cli")),
                contextlib.redirect_stdout(output),
            ):
                exit_code = query_live_translation_memory.main(
                    [
                        "--query-text",
                        query_text,
                        "--source-lang",
                        "en",
                        "--target-lang",
                        "fr",
                        "--limit",
                        "1",
                        "--cache-dir",
                        str(cache_dir),
                        "--cache-ttl-seconds",
                        "600",
                    ]
                )

            self.assertEqual(0, exit_code)
            rendered = output.getvalue()
            self.assertIn(expected_translation, rendered)
            self.assertIn("row_key=recvgEwBBuQ5J6", rendered)

    def test_live_translation_memory_should_ignore_expired_cached_snapshot(self) -> None:
        rows = [{"record_id": "rec1", "en": "Hello", "fr": "Bonjour"}]

        with tempfile.TemporaryDirectory() as td:
            cache_dir = Path(td)
            cache_key = query_live_translation_memory.build_cache_key(
                wiki_token=query_live_translation_memory.DEFAULT_WIKI_TOKEN,
                base_token=None,
                table_id=query_live_translation_memory.DEFAULT_TABLE_ID,
                view_id=query_live_translation_memory.DEFAULT_VIEW_ID,
                max_records=query_live_translation_memory.DEFAULT_MAX_RECORDS,
            )
            with mock.patch.object(query_live_translation_memory.time, "time", return_value=1000.0):
                query_live_translation_memory.save_cached_table_snapshot(
                    cache_dir=cache_dir,
                    cache_key=cache_key,
                    wiki_token=query_live_translation_memory.DEFAULT_WIKI_TOKEN,
                    table_id=query_live_translation_memory.DEFAULT_TABLE_ID,
                    view_id=query_live_translation_memory.DEFAULT_VIEW_ID,
                    max_records=query_live_translation_memory.DEFAULT_MAX_RECORDS,
                    language_fields=["en", "fr"],
                    rows=rows,
                )

            with mock.patch.object(query_live_translation_memory.time, "time", return_value=1701.0):
                cached = query_live_translation_memory.load_cached_table_snapshot(
                    cache_dir=cache_dir,
                    cache_key=cache_key,
                    max_age_seconds=600,
                )

            self.assertIsNone(cached)
