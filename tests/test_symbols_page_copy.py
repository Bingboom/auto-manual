from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.symbols_page_copy import load_symbols_page_copy_map, require_symbols_page_copy


class SymbolsPageCopyTests(unittest.TestCase):
    def test_load_symbols_page_copy_map_uses_language_column(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "symbols_page_copy.csv"
            path.write_text(
                "\n".join(
                    [
                        "copy_key,en,fr,es,de,it,uk",
                        "header_symbol,EN_SYMBOL,FR_SYMBOL,ES_SYMBOL,DE_SYMBOL,IT_SYMBOL,UK_SYMBOL",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual(
                "ES_SYMBOL",
                load_symbols_page_copy_map("es", csv_path=str(path))["header_symbol"],
            )

    def test_load_symbols_page_copy_map_falls_back_to_en(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "symbols_page_copy.csv"
            path.write_text(
                "\n".join(
                    [
                        "copy_key,en,fr,es,de,it,uk",
                        "signal_label.tips,TIP,,,,,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual(
                "TIP",
                load_symbols_page_copy_map("pt-BR", csv_path=str(path))["signal_label.tips"],
            )

    def test_require_symbols_page_copy_fails_fast_for_missing_key(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "symbols_page_copy.csv"
            path.write_text("copy_key,en,fr,es,de,it,uk\nheader_symbol,Symbol,,,,,\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "header_meaning"):
                require_symbols_page_copy(
                    "en",
                    ["header_symbol", "header_meaning"],
                    csv_path=str(path),
                )


if __name__ == "__main__":
    unittest.main()
