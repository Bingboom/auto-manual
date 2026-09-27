"""JE-3600A/EU specification footnote marks sit where the print sets them.

Every language block of the released print (Jackery Explorer 3600 Plus User
Manual-EU-UK-2026-05-25, PDF pages 19/36/53) sets ① after the AC input's
bypass-mode name and on the "AC Output in Bypass Mode" label, and ② on the
"AC Total Output" label. Until 2026-09-27 the en/fr/es Web pages put ① and ②
at the end of the values, and the bypass-output row had no mark at all.
"""
from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

from bs4 import BeautifulSoup

from tests.test_je3600a_eu_en_web import FORMAL_DATA_ROOT, LANGUAGES, _build_web_package


REF_COLUMNS = ("Row_label_footnote_refs", "Param_footnote_refs", "Value_footnote_refs")
# The frozen specification rows that carry a footnote reference, keyed by
# (Row_key, Param_source). The other EU frozen sources use the same columns for
# the rows they share (JE-1000F/JE-1000H/JE-2000E/JE-2000F/JE-3000C).
PRINT_ANCHORED_REFS = {
    ("ac_input", "Bypass Mode"): {"Param_footnote_refs": "ac_bypass"},
    ("ac_total_output", ""): {"Row_label_footnote_refs": "ac_total"},
    ("ac_output_bypass", ""): {"Row_label_footnote_refs": "ac_bypass"},
}
MARK = '<sup class="hb-spec-reference">{}</sup>'
ONE, TWO = MARK.format("①"), MARK.format("②")
# Per route: the label and value cells (inner HTML) of the three marked rows.
PRINTED_CELLS = {
    "en": [
        ("1 × AC Input",
         f"Charge Mode: 220-240 V~ 50 Hz, 10 A max.<br/>Bypass Mode{ONE}: 220-240 V~ 50 Hz, 10 A max."),
        (f"AC Total Output{TWO}", "3600 W rated, 7200 W surge peak"),
        (f"AC Output in Bypass Mode{ONE}", "220-240 V~ 50 Hz, 10 A max."),
    ],
    "fr": [
        ("1 × Entrée CA",
         f"Mode charge: 220-240 V~ 50 Hz, 10 A max.<br/>Mode dérivation{ONE}: 220-240 V~ 50 Hz, 10 A max."),
        (f"Sortie totale CA{TWO}", "3600 W nominal, 7200 W crête"),
        (f"Sortie CA en mode dérivation{ONE}", "220-240 V~ 50 Hz, 10 A max."),
    ],
    "es": [
        ("1 × Entrada CA",
         f"Modo de carga: 220-240 V~ 50 Hz, 10 A máx.<br/>Modo bypass{ONE}: 220-240 V~ 50 Hz, 10 A máx."),
        (f"CA Salida total{TWO}", "3600 W nominales, 7200 W pico de sobretensión"),
        (f"Salida de CA en modo bypass{ONE}", "220-240 V~ 50 Hz, 10 A máx."),
    ],
}


class Je3600aEuSpecFootnoteSourceTests(unittest.TestCase):
    def test_only_the_print_anchored_cells_carry_footnote_refs(self) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = [row for row in csv.DictReader(handle) if row["Page"] == "specifications"]
        refs = {
            (row["Row_key"], row["Param_source"]): {column: row[column] for column in REF_COLUMNS if row[column]}
            for row in rows
            if any(row[column] for column in REF_COLUMNS)
        }
        self.assertEqual(PRINT_ANCHORED_REFS, refs)


class Je3600aEuSpecFootnoteWebTests(unittest.TestCase):
    """The en/fr/es Web pages set the marks on the printed anchors, and each footnote once."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.soups = {}
        for lang in LANGUAGES:
            root = Path(cls._tmp.name) / lang
            root.mkdir()
            package = _build_web_package(root, lang=lang)
            html = (package / "manual_bundle.html").read_text(encoding="utf-8")
            cls.soups[lang] = BeautifulSoup(html, "html.parser")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_marks_sit_on_the_printed_labels_and_mode_names(self) -> None:
        for lang in LANGUAGES:
            rows = [
                (row.select_one("th.hb-spec-label"), row.select_one("td.hb-spec-value"))
                for row in self.soups[lang].select("table.hb-spec-table tbody tr")
            ]
            cells = [(th.decode_contents(), td.decode_contents()) for th, td in rows]
            with self.subTest(lang=lang):
                for printed in PRINTED_CELLS[lang]:
                    self.assertIn(printed, cells)
                marked = [cell for cell in cells if "hb-spec-reference" in "".join(cell)]
                self.assertEqual(PRINTED_CELLS[lang], marked)

    def test_each_footnote_renders_once(self) -> None:
        # ① now has two references (the AC input and the bypass-output label).
        with (FORMAL_DATA_ROOT / "Spec_Footnotes.csv").open(encoding="utf-8", newline="") as handle:
            texts = {row["Footnote_id"]: row for row in csv.DictReader(handle)}
        for lang in LANGUAGES:
            footnotes = [p.get_text() for p in self.soups[lang].select("p.hb-spec-footnote")]
            with self.subTest(lang=lang):
                self.assertEqual(
                    [f"① {texts['ac_bypass'][f'Text_{lang}']}", f"② {texts['ac_total'][f'Text_{lang}']}"],
                    footnotes,
                )


if __name__ == "__main__":
    unittest.main()
