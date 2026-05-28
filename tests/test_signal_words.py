from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.signal_words import get_signal_word, load_signal_words_map, require_signal_words


class SignalWordsTests(unittest.TestCase):
    def test_load_signal_words_map_uses_language_column(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "signal_words.csv"
            path.write_text(
                "\n".join(
                    [
                        "copy_key,en,fr,es,pt-BR,ja,zh,de,it,uk",
                        "warning,EN_WARNING,FR_WARNING,ES_WARNING,BR_WARNING,JA_WARNING,ZH_WARNING,DE_WARNING,IT_WARNING,UK_WARNING",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual("BR_WARNING", load_signal_words_map("pt-BR", csv_path=str(path))["warning"])

    def test_get_signal_word_falls_back_to_en(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "signal_words.csv"
            path.write_text(
                "\n".join(
                    [
                        "copy_key,en,fr,es,pt-BR,ja,zh,de,it,uk",
                        "tips,TIP,,,,,,,,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual("TIP", get_signal_word("ja", "tips", csv_path=str(path)))

    def test_require_signal_words_fails_fast_for_missing_key(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "signal_words.csv"
            path.write_text(
                "copy_key,en,fr,es,pt-BR,ja,zh,de,it,uk\nwarning,WARNING,,,,,,,,\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "caution"):
                require_signal_words("en", ["warning", "caution"], csv_path=str(path))


if __name__ == "__main__":
    unittest.main()
