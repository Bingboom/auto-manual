from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_PREPROCESS_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "lark-tm-translation-preprocess"
    / "scripts"
    / "preprocess_lark_docx_with_tm.py"
)
_SPEC = importlib.util.spec_from_file_location("preprocess_lark_docx_with_tm", _PREPROCESS_SCRIPT_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Unable to load {_PREPROCESS_SCRIPT_PATH}")
preprocess_script = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = preprocess_script
_SPEC.loader.exec_module(preprocess_script)


class TestPreprocessLarkDocxWithTm(unittest.TestCase):
    def test_normalize_language_and_aliases(self) -> None:
        norm = preprocess_script.normalize_language

        # EU languages: nl, pl, pt
        self.assertEqual("nl", norm("nl"))
        self.assertEqual("nl", norm("Dutch"))
        self.assertEqual("pl", norm("pl"))
        self.assertEqual("pl", norm("Polish"))
        self.assertEqual("pt", norm("pt"))
        self.assertEqual("pt", norm("pt-pt"))
        self.assertEqual("pt", norm("Portuguese"))

        # Brazil Portuguese
        self.assertEqual("pt-br", norm("pt-br"))
        self.assertEqual("pt-br", norm("ptbr"))

        # Other standard languages
        self.assertEqual("de", norm("de"))
        self.assertEqual("fr", norm("French"))
        self.assertEqual("es", norm("Spanish"))
        self.assertEqual("it", norm("Italian"))
        self.assertEqual("ja", norm("ja"))
        self.assertEqual("ko", norm("ko"))
        self.assertEqual("zh", norm("zh"))
        self.assertEqual("zh-tw", norm("zh-TW"))

    def test_is_usable_tm_row_status_rules(self) -> None:
        is_usable = preprocess_script.is_usable_tm_row

        # Approved
        self.assertTrue(is_usable({"Status": "Approved"}))
        self.assertTrue(is_usable({"Status": "approved"}))
        self.assertTrue(is_usable({"status": {"name": "Approved"}}))
        self.assertTrue(is_usable({"Status": [{"name": "Approved"}]}))
        self.assertTrue(is_usable({"Status": ["Approved"]}))

        # Draft
        self.assertFalse(is_usable({"Status": "Draft"}, include_draft=False))
        self.assertTrue(is_usable({"Status": "Draft"}, include_draft=True))
        self.assertFalse(is_usable({"status": {"name": "Draft"}}, include_draft=False))
        self.assertTrue(is_usable({"status": {"name": "Draft"}}, include_draft=True))

        # Deprecated: always excluded
        self.assertFalse(is_usable({"Status": "Deprecated"}, include_draft=False))
        self.assertFalse(is_usable({"Status": "Deprecated"}, include_draft=True))
        self.assertFalse(is_usable({"status": {"name": "Deprecated"}}, include_draft=True))

        # Missing or empty status: backward compatibility
        self.assertTrue(is_usable({}))
        self.assertTrue(is_usable({"Status": ""}))
        self.assertTrue(is_usable({"Status": None}))
        self.assertTrue(is_usable({"status": ""}))

        # Unknown status: excluded
        self.assertFalse(is_usable({"Status": "Review"}))

    def test_build_pairs_with_status_filtering_and_eu_languages(self) -> None:
        rows = [
            {
                "record_id": "rec_app",
                "Status": "Approved",
                "en": "Solar panel",
                "nl": "Zonnepaneel",
                "pl": "Panel sloneczny",
                "pt": "Painel solar",
            },
            {
                "record_id": "rec_draft",
                "Status": "Draft",
                "en": "Power bank",
                "nl": "Powerbank",
                "pl": "Powerbank PL",
                "pt": "Bateria externa",
            },
            {
                "record_id": "rec_dep",
                "Status": "Deprecated",
                "en": "Old gadget",
                "nl": "Oud apparaat",
                "pl": "Stary gadzet",
                "pt": "Aparelho antigo",
            },
            {
                "record_id": "rec_legacy",
                "en": "Safety warning",
                "nl": "Veiligheidswaarschuwing",
                "pl": "Ostrzezenie o bezpieczenstwie",
                "pt": "Aviso de seguranca",
            },
        ]
        lang_fields = ["en", "nl", "pl", "pt"]

        # Default (include_draft=False): Approved + Legacy rows kept
        pairs_nl, _ = preprocess_script.build_pairs(
            rows, lang_fields, source_lang="en", target_lang="nl", include_draft=False
        )
        self.assertEqual(2, len(pairs_nl))
        self.assertEqual("Zonnepaneel", pairs_nl[0].target)
        self.assertEqual("Veiligheidswaarschuwing", pairs_nl[1].target)

        # With include_draft=True: Draft row included too (Deprecated still excluded)
        pairs_draft, _ = preprocess_script.build_pairs(
            rows, lang_fields, source_lang="en", target_lang="nl", include_draft=True
        )
        self.assertEqual(3, len(pairs_draft))
        self.assertEqual("Powerbank", pairs_draft[1].target)

        # Verify Portuguese pair
        pairs_pt, _ = preprocess_script.build_pairs(
            rows, lang_fields, source_lang="en", target_lang="pt", include_draft=False
        )
        self.assertEqual(2, len(pairs_pt))
        self.assertEqual("Painel solar", pairs_pt[0].target)

        # Verify Polish pair
        pairs_pl, _ = preprocess_script.build_pairs(
            rows, lang_fields, source_lang="en", target_lang="pl", include_draft=False
        )
        self.assertEqual(2, len(pairs_pl))
        self.assertEqual("Panel sloneczny", pairs_pl[0].target)

    def test_looks_like_language_heading_with_nl_and_pl(self) -> None:
        heading = preprocess_script.looks_like_language_heading
        self.assertTrue(heading("NL BELANGRIJK: Lees dit zorgvuldig"))
        self.assertTrue(heading("PL WAŻNE: Przeczytaj uważnie"))
        self.assertTrue(heading("PL WAZNE: Przeczytaj uważnie"))
        self.assertTrue(heading("PT IMPORTANTE: Leia com atenção"))
        self.assertTrue(heading("DE WICHTIG: Bitte lesen"))
        self.assertFalse(heading("This is normal text without language heading"))

    def test_parse_args_defaults_max_records_to_zero_and_include_draft(self) -> None:
        args = preprocess_script.parse_args(["--source-lang", "en", "--target-lang", "nl"])
        self.assertEqual(0, args.max_records)
        self.assertFalse(args.include_draft)

        args_with_draft = preprocess_script.parse_args(
            ["--source-lang", "en", "--target-lang", "nl", "--include-draft", "--max-records", "500"]
        )
        self.assertTrue(args_with_draft.include_draft)
        self.assertEqual(500, args_with_draft.max_records)


if __name__ == "__main__":
    unittest.main()
