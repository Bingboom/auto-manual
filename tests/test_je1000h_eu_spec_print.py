"""JE-1000H/EU Web specification tables follow the approved print.

Operator ruling of 2026-09-27: values, structure and labels follow the print
(``Jackery Explorer 1000 Plus User Manual (JE-1000H) EUUK V2.0-2026-08-03.pdf``,
specification pages 19/36/53/70/87/104 for en/fr/es/de/it/uk); formatting keeps the
house rules, and where the print itself is wrong the reviewed wording stays.
"""
from __future__ import annotations

import csv
from pathlib import Path
import unittest

from tools.csv_pages.builder import BuildPaths, CsvPageBuilder
from tools.csv_pages.renderers_spec_parser import collect_spec_content


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "manual_sources/JE-1000H/EU/en/2.0/phase2"
LANGS = ("en", "fr", "es", "de", "it", "uk")
_ROW = "JE-1000H_EU__v2.0__specifications__"
AC_CHARGE = _ROW + "s02__r01__ac_input__main__l01"
AC_BYPASS = _ROW + "s02__r01__ac_input__main__l02"
USB_C_30W = _ROW + "s03__r03__usb_c__30w__l01"
USB_C_140W = _ROW + "s03__r03__usb_c__100w__l02"
DC_EXPANSION = (_ROW + "s02__r03__dc_expansion_input__main__l01",
                _ROW + "s02__r07__dc_expansion_output__main__l01")


def _value_column(lang: str) -> str:
    return "Value_source" if lang == "en" else f"Value_{lang}"


class Je1000hEuSpecTablePrintTests(unittest.TestCase):
    """The spec page as the build assembles it: Spec_Master plus the footnote and note rows."""

    @classmethod
    def setUpClass(cls) -> None:
        with (DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            cls.rows = {row["spec_row_key"]: row for row in csv.DictReader(handle)}
        paths = BuildPaths(
            root=ROOT,
            page_registry=DATA_ROOT / "page_registry.csv",
            page_blocks_dir=DATA_ROOT,
            template_dir=ROOT / "docs/templates",
            output_dir=ROOT / "docs/generated",
            spec_master_csv=DATA_ROOT / "Spec_Master.csv",
            spec_footnotes_csv=DATA_ROOT / "Spec_Footnotes.csv",
            spec_notes_csv=DATA_ROOT / "Spec_Notes.csv",
        )
        blocks = CsvPageBuilder(paths)._load_page_blocks("spec")
        cls.tables: dict[str, dict[str, list[tuple[str, str]]]] = {}
        for lang in LANGS:
            content = collect_spec_content([dict(row) for row in blocks], "", lang,
                                           {"model": "JE-1000H", "region": "EU"})
            cls.tables[lang] = {str(section["title"]): section["rows"] for section in content["sections"]}

    def _row(self, lang: str, section: str, label: str) -> list[str]:
        values = [value for row_label, value in self.tables[lang][section] if row_label == label]
        self.assertEqual(1, len(values), (lang, section, label))
        return values[0].split("\n")

    def test_only_the_ukrainian_ac_input_prints_a_charge_mode_label(self) -> None:
        # PDF pages 19/36/53/70/87 print the bare value; page 104 prints «Режим заряджання:»
        row = self.rows[AC_CHARGE]
        self.assertEqual("", row["Param_source"])
        for lang in LANGS:
            label, value = self.tables[lang]["INPUT PORTS"][0]
            first = value.split("\n")[0]
            with self.subTest(lang=lang):
                self.assertEqual(row["Row_label_source" if lang == "en" else f"Row_label_{lang}"], label)
                if lang == "uk":
                    self.assertEqual("Режим заряджання", row["Param_uk"])
                    self.assertEqual("Режим заряджання: 220 В-240 В~ 50 Гц, 10 A макс.", first)
                else:
                    self.assertEqual("", row.get(f"Param_{lang}", ""))
                    self.assertEqual(row[_value_column(lang)], first)

    def test_bypass_lines_keep_each_block_parameter_and_italian_prints_ac(self) -> None:
        # PDF page 87 prints «AC modalità bypass¹»; the other blocks are unchanged
        expected = {
            "en": "Bypass Mode①: 220V-240V~50Hz, 7.83A",
            "fr": "Mode dérivation①: 220 V-240 V~ 50 Hz, 7,83 A",
            "es": "Modo de derivación①: 220 V-240 V~ 50 Hz, 7,83 A",
            "de": "Bypassmodus①: 220 V-240 V~ 50 Hz, 7,83 A",
            "it": "AC modalità bypass①: 220 V-240 V~ 50 Hz, 7,83 A",
            "uk": "Байпасний режим①: 220 В-240 В~ 50 Гц, 7,83 A",
        }
        self.assertEqual("AC modalità bypass", self.rows[AC_BYPASS]["Param_it"])
        for lang, line in expected.items():
            with self.subTest(lang=lang):
                self.assertEqual(line, self.tables[lang]["INPUT PORTS"][0][1].split("\n")[1])

    def test_english_dc_expansion_rows_read_port_in_both_tables(self) -> None:
        # PDF page 19 labels both the input and the output row «1 × DC Expansion Port»
        for key in DC_EXPANSION:
            self.assertEqual("1 × DC Expansion Port", self.rows[key]["Row_label_source"])
        self.assertEqual(["36.8V-56V⎓59A Max"], self._row("en", "INPUT PORTS", "1 × DC Expansion Port"))
        self.assertEqual(["36.8V-56V⎓36A Max"], self._row("en", "OUTPUT PORTS", "1 × DC Expansion Port"))
        labels = [label for section in self.tables["en"].values() for label, _value in section]
        self.assertFalse([label for label in labels if "Expansion Input" in label or "Expansion Output" in label])

    def test_ukrainian_usb_c_ports_are_the_two_printed_rows(self) -> None:
        # PDF page 104: «виходи USB-C 30W» | «30 Вт макс., …» and «виходи USB-C 140W» | «140 Вт макс., …»
        self.assertEqual(
            [
                "3 виходи змінного струму",
                "Загальний вихід змінного струму②",
                "Вихід змінного струму у байпасному режимі①",
                "виходи USB-C 30W",
                "виходи USB-C 140W",
                "1 вихід USB-A 18W",
                "Порт постійного струму 12 В",
                "1 порт розширення постійного струму",
            ],
            [label for label, _value in self.tables["uk"]["OUTPUT PORTS"]],
        )
        for label, key in (("виходи USB-C 30W", USB_C_30W), ("виходи USB-C 140W", USB_C_140W)):
            with self.subTest(label=label):
                self.assertEqual([self.rows[key]["Value_uk"]], self._row("uk", "OUTPUT PORTS", label))

    def test_other_blocks_keep_one_usb_c_row_with_two_power_lines(self) -> None:
        # en/fr/es/de/it print one «2 × …USB-C» row with a «USB-C 30W:» / «USB-C 140W:» line each
        parents = {"en": ("2 × USB-C", "USB-C"), "fr": ("2 × Sortie USB-C", "Sortie USB-C"),
                   "es": ("2 × Salida USB-C", "Salida USB-C"), "de": ("2 × USB-C-Ausgang", "USB-C"),
                   "it": ("2 × Uscita USB-C", "USB-C")}
        for lang, (label, port) in parents.items():
            lines = self._row(lang, "OUTPUT PORTS", label)
            with self.subTest(lang=lang):
                self.assertEqual(2, len(lines))
                self.assertTrue(lines[0].startswith(f"{port} 30W: 30"), lines[0])
                self.assertTrue(lines[1].startswith(f"{port} 140W: 140"), lines[1])

    def test_line_text_uk_only_carries_the_two_ukrainian_usb_c_lines(self) -> None:
        # Spec_Master's line_text_* is the rendered line, bypassing Param_* + Value_*. An empty
        # Param_uk alone would fall back to the English Param_source, so the value-only printed
        # line is set explicitly; it must repeat Value_uk, which the figure checks cover.
        filled = {key for key, row in self.rows.items() if row.get("line_text_uk")}
        self.assertEqual({USB_C_30W, USB_C_140W}, filled)
        for key in filled:
            row = self.rows[key]
            with self.subTest(row=key):
                self.assertEqual(row["Value_uk"], row["line_text_uk"])
                self.assertEqual("", row["Param_uk"])
                self.assertEqual(row["Row_label_uk"], "виходи " + row["Param_source"])

    def test_print_defects_keep_the_reviewed_wording(self) -> None:
        # The print's defects stay corrected: French «Oiture:», the de/it USB-C label printed in
        # French, the German 12 V «Ausgangstaste», and the Ukrainian «у байпасному режим».
        self.assertTrue(self._row("fr", "INPUT PORTS", "2 × Ports DC8020")[0].startswith("Voiture : "))
        self._row("de", "OUTPUT PORTS", "2 × USB-C-Ausgang")
        self._row("de", "OUTPUT PORTS", "1 × DC 12 V-Anschluss")
        self._row("it", "OUTPUT PORTS", "2 × Uscita USB-C")
        self._row("uk", "OUTPUT PORTS", "Вихід змінного струму у байпасному режимі①")
        for lang in ("de", "it"):
            labels = [label for section in self.tables[lang].values() for label, _value in section]
            with self.subTest(lang=lang):
                self.assertFalse([label for label in labels if "Sortie" in label or "Ausgangstaste" in label])


if __name__ == "__main__":
    unittest.main()
