from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.signal_words import get_safety_warning_label, get_signal_word, get_symbols_notice_label, signal_label_entries


class TestSignalWords(unittest.TestCase):
    def test_signal_words_should_resolve_from_symbols_blocks_signal_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "symbols_blocks.csv"
            path.write_text(
                "\n".join(
                    [
                        "symbol_key,block_type,order,Market,Model,Source_lang,Is_Latest,label_fr,label_de,label_zh,label_es",
                        "warning,signal_row,1,ALL,ALL,en,TRUE,AVERTISSEMENT_BASE,WARNUNG_BASE,警告,ADVERTENCIA",
                        "tips,signal_row,2,ALL,ALL,en,TRUE,CONSEILS_BASE,TIPP_BASE,提示,CONSEJO",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual("AVERTISSEMENT_BASE", get_signal_word("fr", "warning", symbols_blocks_csv=path))
            self.assertEqual("TIPP_BASE", get_signal_word("de", "tip", symbols_blocks_csv=path))
            self.assertEqual("WARNING", get_signal_word("unknown", "warning", symbols_blocks_csv=path))
            self.assertEqual("警告", get_safety_warning_label("zh", symbols_blocks_csv=path))
            self.assertIn(
                ("warning", "ADVERTENCIA"),
                {(entry.key, entry.label) for entry in signal_label_entries(symbols_blocks_csv=path, lang="es")},
            )

    def test_signal_words_should_prefer_generated_localized_copy_labels(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            symbols_blocks = root / "symbols_blocks.csv"
            symbols_blocks.write_text(
                "\n".join(
                    [
                        "symbol_key,block_type,order,Market,Model,Source_lang,Is_Latest,label_fr,label_es",
                        "warning,signal_row,1,ALL,ALL,en,TRUE,AVERTISSEMENT_BASE,ADVERTENCIA_BASE",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            localized_copy = root / "Localized_Copy.csv"
            localized_copy.write_text(
                "\n".join(
                    [
                        "copy_key,page_id,copy_type,Region,Model,Source_lang,Is_Latest,Version,text_en,text_zh,text_ja,text_fr,text_es,text_pt-BR,text_de,text_it,text_uk,notes",
                        "symbols.signal.warning.label,symbols,signal_label,ALL,ALL,en,TRUE,V1.0,WARNING,WARNING,WARNING,AVERTISSEMENT_COPY,ADVERTENCIA_COPY,WARNING,WARNING,WARNING,WARNING,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual("AVERTISSEMENT_COPY", get_signal_word("fr", "warning", symbols_blocks_csv=symbols_blocks))
            self.assertIn(
                ("warning", "AVERTISSEMENT_COPY"),
                {(entry.key, entry.label) for entry in signal_label_entries(symbols_blocks_csv=symbols_blocks, lang="fr")},
            )

    def test_signal_words_should_resolve_danger_signal_row(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "symbols_blocks.csv"
            path.write_text(
                "\n".join(
                    [
                        "symbol_key,block_type,order,Market,Model,Source_lang,Is_Latest,label_en,label_es",
                        "danger,signal_row,5,ALL,ALL,en,TRUE,DANGER,PELIGRO",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual("DANGER", get_symbols_notice_label("en", symbols_blocks_csv=path))
            self.assertIn(
                ("danger", "PELIGRO"),
                {(entry.key, entry.label) for entry in signal_label_entries(symbols_blocks_csv=path, lang="es")},
            )

    def test_signal_words_should_fail_when_signal_row_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "symbols_blocks.csv"
            path.write_text(
                "symbol_key,block_type,order,Market,Model,Source_lang,Is_Latest\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(KeyError, "symbol_key=warning"):
                get_signal_word("en", "warning", symbols_blocks_csv=path)

    def test_symbols_notice_should_require_danger_row_in_symbols_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "symbols_blocks.csv"
            path.write_text(
                "symbol_key,block_type,order,Market,Model,Source_lang,Is_Latest\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(KeyError, "symbol_key=danger"):
                get_symbols_notice_label("en", symbols_blocks_csv=path)

    def test_signal_words_should_reject_unknown_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported signal word key"):
            get_signal_word("en", "headline")


if __name__ == "__main__":
    unittest.main()
