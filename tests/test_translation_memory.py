from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_helpers import write_lines, write_text
from tools.translation_memory import (
    _row_matches,
    build_translation_memory_payload,
    collect_translation_memory_entries,
    normalize_language,
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
    def test_normalize_language_should_support_taiwan_traditional_chinese(self) -> None:
        self.assertEqual("zh-tw", normalize_language("zh-TW"))
        self.assertEqual("zh-tw", normalize_language("zh-Hant"))
        self.assertEqual("zh", normalize_language("zh-CN"))

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


class TestRowMatches(unittest.TestCase):
    def test_multi_value_model_cell_matches_any_listed_model(self) -> None:
        row = {"Model": "JE-1000F, JE-2000E, JE-2000F", "Region": ""}
        self.assertTrue(_row_matches(row, model="JE-1000F", region=None))
        self.assertTrue(_row_matches(row, model="JE-2000F", region=None))

    def test_model_not_in_multi_value_cell_is_excluded(self) -> None:
        row = {"Model": "JE-1000F, JE-2000E", "Region": ""}
        self.assertFalse(_row_matches(row, model="JE-9999Z", region=None))

    def test_all_sentinel_and_blank_cells_match_every_target(self) -> None:
        self.assertTrue(_row_matches({"Model": "ALL", "Region": "ALL"}, model="JE-1000F", region="US"))
        self.assertTrue(_row_matches({"Model": "", "Region": ""}, model="JE-1000F", region="US"))

    def test_multi_value_region_cell_matches_per_token(self) -> None:
        row = {"Model": "", "Region": "US, EU"}
        self.assertTrue(_row_matches(row, model=None, region="EU"))
        self.assertFalse(_row_matches(row, model=None, region="JP"))

    def test_matching_is_case_insensitive(self) -> None:
        self.assertTrue(_row_matches({"Model": "je-1000f", "Region": ""}, model="JE-1000F", region=None))


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
            # Default invocation (sentence scope, no explicit ids, no wiki fallback
            # since the G4 convergence) keys the cache on the table-name selector
            # with wiki_token=None, matching what main() computes below. A recent
            # cache hit must work with NO base binding at all.
            cache_key = query_live_translation_memory.build_cache_key(
                wiki_token=None,
                base_token=None,
                table_id="name:Translation_Memory",
                view_id="auto",
                max_records=query_live_translation_memory.DEFAULT_MAX_RECORDS,
            )
            with mock.patch.object(query_live_translation_memory.time, "time", return_value=1000.0):
                query_live_translation_memory.save_cached_table_snapshot(
                    cache_dir=cache_dir,
                    cache_key=cache_key,
                    wiki_token=None,
                    table_id="name:Translation_Memory",
                    view_id="auto",
                    max_records=query_live_translation_memory.DEFAULT_MAX_RECORDS,
                    language_fields=["en", "fr"],
                    rows=rows,
                )

            output = io.StringIO()
            with (
                mock.patch.dict(os.environ, {query_live_translation_memory.ENV_BASE_TOKEN_VAR: ""}),
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
                wiki_token=query_live_translation_memory.ARCHIVE_WIKI_TOKEN,
                base_token=None,
                table_id="name:Translation_Memory",
                view_id="auto",
                max_records=query_live_translation_memory.DEFAULT_MAX_RECORDS,
            )
            with mock.patch.object(query_live_translation_memory.time, "time", return_value=1000.0):
                query_live_translation_memory.save_cached_table_snapshot(
                    cache_dir=cache_dir,
                    cache_key=cache_key,
                    wiki_token=query_live_translation_memory.ARCHIVE_WIKI_TOKEN,
                    table_id="name:Translation_Memory",
                    view_id="auto",
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

    def test_is_usable_tm_row_status_filtering(self) -> None:
        is_usable = query_live_translation_memory.is_usable_tm_row

        # Approved rows (str, dict, list)
        self.assertTrue(is_usable({"Status": "Approved"}))
        self.assertTrue(is_usable({"Status": "approved"}))
        self.assertTrue(is_usable({"status": {"name": "Approved"}}))
        self.assertTrue(is_usable({"Status": [{"name": "Approved"}]}))
        self.assertTrue(is_usable({"Status": ["Approved"]}))

        # Draft rows
        self.assertFalse(is_usable({"Status": "Draft"}, include_draft=False))
        self.assertTrue(is_usable({"Status": "Draft"}, include_draft=True))
        self.assertFalse(is_usable({"status": {"name": "Draft"}}, include_draft=False))
        self.assertTrue(is_usable({"status": {"name": "Draft"}}, include_draft=True))

        # Deprecated rows are ALWAYS excluded
        self.assertFalse(is_usable({"Status": "Deprecated"}, include_draft=False))
        self.assertFalse(is_usable({"Status": "Deprecated"}, include_draft=True))
        self.assertFalse(is_usable({"status": {"name": "Deprecated"}}, include_draft=True))

        # Missing or empty status (legacy fixtures / tables)
        self.assertTrue(is_usable({}))
        self.assertTrue(is_usable({"Status": ""}))
        self.assertTrue(is_usable({"Status": None}))
        self.assertTrue(is_usable({"status": ""}))

        # Unknown non-empty status
        self.assertFalse(is_usable({"Status": "Review"}))
        self.assertFalse(is_usable({"Status": "Pending"}))

    def test_build_sentence_pair_entries_supports_eu_languages_and_draft_toggle(self) -> None:
        rows = [
            {
                "record_id": "rec_app",
                "Status": "Approved",
                "en": "Solar generator",
                "nl": "Zonnegenerator",
                "pl": "Generator sloneczny",
                "pt": "Gerador solar",
            },
            {
                "record_id": "rec_draft",
                "Status": "Draft",
                "en": "Portable power station",
                "nl": "Draagbare krachtcentrale",
            },
            {
                "record_id": "rec_dep",
                "Status": "Deprecated",
                "en": "Old battery",
                "nl": "Oude batterij",
            },
            {
                "record_id": "rec_legacy",
                "en": "Clean energy",
                "nl": "Schone energie",
                "pl": "Czysta energia",
                "pt": "Energia limpa",
            },
        ]
        lang_fields = ["en", "nl", "pl", "pt"]

        self.assertIn("nl", query_live_translation_memory.LIVE_TM_LANGUAGE_FIELDS)
        self.assertIn("pl", query_live_translation_memory.LIVE_TM_LANGUAGE_FIELDS)
        self.assertIn("pt", query_live_translation_memory.LIVE_TM_LANGUAGE_FIELDS)

        # By default (include_draft=False): rec_app and rec_legacy kept; rec_draft and rec_dep excluded
        entries_default = query_live_translation_memory.build_sentence_pair_entries(
            rows, language_fields=lang_fields, include_draft=False
        )
        keys_default = [e.row_key for e in entries_default]
        self.assertEqual(["rec_app", "rec_legacy"], keys_default)
        self.assertEqual("Zonnegenerator", entries_default[0].translations.get("nl"))
        self.assertEqual("Generator sloneczny", entries_default[0].translations.get("pl"))
        self.assertEqual("Gerador solar", entries_default[0].translations.get("pt"))

        # With include_draft=True: rec_draft also kept; rec_dep still excluded
        entries_with_draft = query_live_translation_memory.build_sentence_pair_entries(
            rows, language_fields=lang_fields, include_draft=True
        )
        keys_draft = [e.row_key for e in entries_with_draft]
        self.assertEqual(["rec_app", "rec_draft", "rec_legacy"], keys_draft)

    def test_list_records_pagination_unlimited_and_capped(self) -> None:
        def make_page(page_idx: int, page_size: int, has_more: bool) -> dict:
            return {
                "ok": True,
                "data": {
                    "fields": ["en", "fr"],
                    "record_id_list": [f"rec_{page_idx}_{i}" for i in range(page_size)],
                    "data": [["Hello", "Bonjour"] for _ in range(page_size)],
                    "has_more": has_more,
                },
            }

        # Case 1: max_records = 0 (unlimited pagination past 2000 rows, e.g. 11 pages of 200 = 2200 rows)
        page_calls = []

        def fake_run_unlimited(cmd: list[str]) -> dict:
            page_calls.append(cmd)
            current_page = len(page_calls) - 1
            has_more = current_page < 10
            return make_page(current_page, 200, has_more)

        with mock.patch.object(query_live_translation_memory, "run_lark_json", side_effect=fake_run_unlimited):
            rows = query_live_translation_memory.list_records(
                cli="lark-cli",
                base_token="base123",
                table_id="tbl123",
                view_id="vew123",
                max_records=0,
            )
        self.assertEqual(2200, len(rows))
        self.assertEqual(11, len(page_calls))

        # Case 2: max_records = 50 (explicit positive cap)
        capped_calls = []

        def fake_run_capped(cmd: list[str]) -> dict:
            capped_calls.append(cmd)
            return make_page(0, 50, True)

        with mock.patch.object(query_live_translation_memory, "run_lark_json", side_effect=fake_run_capped):
            rows = query_live_translation_memory.list_records(
                cli="lark-cli",
                base_token="base123",
                table_id="tbl123",
                view_id="vew123",
                max_records=50,
            )
        self.assertEqual(50, len(rows))
        self.assertEqual(1, len(capped_calls))
        # Ensure limit passed in cmd was 50
        limit_idx = capped_calls[0].index("--limit")
        self.assertEqual("50", capped_calls[0][limit_idx + 1])

    def test_live_tm_eu_pt_nl_pl_zh_tw_columns_and_manifest_parity(self) -> None:
        import json
        from tools import lang_asset_sweep
        from tools.translation_memory import normalize_language, query_translation_memory_entries

        self.assertEqual(normalize_language("eu-pt"), "pt")
        self.assertEqual(normalize_language("pt"), "pt")
        self.assertEqual(normalize_language("nl"), "nl")
        self.assertEqual(normalize_language("pl"), "pl")
        self.assertEqual(normalize_language("zh-TW"), "zh-tw")
        self.assertEqual(lang_asset_sweep.LANG_ALIASES.get("eu-pt"), "pt")
        self.assertEqual(lang_asset_sweep.LANG_ALIASES.get("nl"), "nl")
        self.assertEqual(lang_asset_sweep.LANG_ALIASES.get("pl"), "pl")

        fake_table_get = {
            "ok": True,
            "data": {
                "fields": [
                    {"name": "en", "type": "text"},
                    {"name": "nl", "type": "text"},
                    {"name": "pl", "type": "text"},
                    {"name": "eu-pt", "type": "text"},
                    {"name": "pt-BR", "type": "text"},
                    {"name": "zh-TW", "type": "text"},
                    {"name": "eu-pt维护Log (AI)", "type": "text"},
                ]
            },
        }
        with mock.patch.object(query_live_translation_memory, "run_lark_json", return_value=fake_table_get):
            fields = query_live_translation_memory.get_table_language_fields(
                cli="lark-cli", base_token="base123", table_id="tbl123"
            )
        self.assertEqual(["en", "nl", "pl", "eu-pt", "pt-BR", "zh-TW"], fields)

        entries = query_live_translation_memory.build_sentence_pair_entries(
            [
                {
                    "record_id": "rec_eu",
                    "Status": "Approved",
                    "en": "Read all instructions before use.",
                    "nl": "Lees alle instructies voor gebruik.",
                    "pl": "Przeczytaj wszystkie instrukcje przed użyciem.",
                    "eu-pt": "Leia todas as instruções antes de usar.",
                    "zh-TW": "使用前請閱讀所有說明。",
                }
            ],
            language_fields=fields,
            include_draft=False,
        )
        self.assertEqual(1, len(entries))
        self.assertEqual("Leia todas as instruções antes de usar.", entries[0].translations.get("pt"))
        self.assertEqual("使用前請閱讀所有說明。", entries[0].translations.get("zh-tw"))

        for ask in ("pt", "eu-pt"):
            matched = query_translation_memory_entries(
                entries,
                query_text="Read all instructions before use.",
                source_lang="en",
                target_lang=ask,
            )
            self.assertEqual(1, len(matched))
            self.assertEqual("Leia todas as instruções antes de usar.", matched[0].translations.get("pt"))

        manifest_path = Path(__file__).resolve().parents[1] / "bitable_schema" / "tm_base_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        tables = {t["name"]: {f["name"] for f in t["fields"]} for t in manifest["tables"]}
        self.assertEqual({"Translation_Memory", "Terms", "语料核验任务"}, set(tables))
        for table_name in ("Translation_Memory", "Terms"):
            self.assertTrue({"en", "nl", "pl", "eu-pt", "pt-BR", "zh-TW", "Status", "Asset_ID"}.issubset(tables[table_name]))
        self.assertTrue({"nl维护Log (AI)", "pl维护Log (AI)", "eu-pt维护Log (AI)", "zh-TW维护Log (AI)"}.issubset(tables["Translation_Memory"]))

