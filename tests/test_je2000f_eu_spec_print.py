"""JE-2000F/EU Web specification tables follow the approved print.

Operator ruling of 2026-09-27: values, structure and labels follow the print
(``Jackery Explorer 2000 User Manual (JE-2000F) EUUK V2.0-2026-08-04.pdf``,
specification pages PDF 18/34/50/66/82/98, printed 13/29/45/61/77/93).
Formatting keeps the house rules. Where the print itself is wrong, the
reviewed wording is used.
"""
from __future__ import annotations

import csv
from pathlib import Path
import re
import unittest

from tools.csv_pages import renderers


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "manual_sources" / "JE-2000F" / "EU" / "en" / "2.0" / "phase2"
SPEC_ROW = "JE-2000F_EU__v1.0__specifications__"
LANGUAGES = ("en", "fr", "es", "de", "it", "uk")
TRANSLATED = ("fr", "es", "de", "it", "uk")

CYCLE_LIFE = "s01__r07__cycle_life__main__l01"
AC_OUTPUT = "s03__r01__ac_output__main__l01"
BYPASS_OUTPUT = "s03__r02__ac_output_bypass__main__l01"

# Each cell as the print sets it, in house formatting (unit spacing and the
# DC symbol as elsewhere on the Web).
PRINTED_CELLS = {
    # Every block prints 4000 cycles.
    (CYCLE_LIFE, "Value_fr"): "Capacité de 4000 cycles à 70 % ou plus",
    (CYCLE_LIFE, "Value_es"): "4000 ciclos de carga hasta 70 % + de capacidad",
    (CYCLE_LIFE, "Value_de"): "4000 Zyklen bei über 70 % Restkapazität",
    (CYCLE_LIFE, "Value_it"): "4000 cicli con capacità residua superiore al 70%",
    (CYCLE_LIFE, "Value_uk"): "4000 циклів до 70%+ ємності",
    # No block prints "10 A max." for the 3 × AC outputs.
    (AC_OUTPUT, "Value_fr"): "230 V~ 50 Hz, 2200 W nominal au total, 4400 W pointe de surtension",
    (AC_OUTPUT, "Value_es"): "230 V~ 50 Hz, 2200 W Nominal en Total, 4400 W Pico de sobrecarga",
    (AC_OUTPUT, "Value_de"): "230 V~ 50 Hz, 2200 W Nennleistung insgesamt, 4400 W Spitzenleistung",
    (AC_OUTPUT, "Value_it"): "230 V~ 50 Hz, 2200 W nominali totali, 4400 W di picco",
    (AC_OUTPUT, "Value_uk"): (
        "230 В~ 50 Гц, номінальна потужність 2200 Вт загалом, пікова потужність 4400 Вт"
    ),
    # Every block rates the bypass output at 2200 W max., not 10 A.
    (BYPASS_OUTPUT, "Value_fr"): "220 V-240 V~ 50 Hz, 2200 W max.",
    (BYPASS_OUTPUT, "Value_es"): "220 V-240 V~ 50 Hz, 2200 W máx.",
    (BYPASS_OUTPUT, "Value_de"): "220 V-240 V~ 50 Hz, 2200 W max.",
    (BYPASS_OUTPUT, "Value_it"): "220 V-240 V~ 50 Hz, 2200 W max.",
    (BYPASS_OUTPUT, "Value_uk"): "220 В-240 В~ 50 Гц, 2200 Вт макс.",
    # The it block prints the energy first, like the other blocks.
    ("s01__r03__capacity__main__l01", "Value_it"): "2048 Wh (40 Ah / 51,2 V ⎓)",
    # Labels: en "Car:" (PDF pages 18 and 8); fr labels (PDF page 34).
    ("s02__r02__dc8020_ports__main__l01", "Value_source"): (
        "Car: 11 V-16 V⎓8 A max., Double to 8 A max."
    ),
    ("s01__r02__model_no__main__l02", "Row_label_fr"): "N° modèle",
    (AC_OUTPUT, "Row_label_fr"): "3 × Sortie CA",
    # Print defects in the specification block use the print's own wording
    # elsewhere: de charging note (PDF page 63), it charging note (page 79).
    ("s04__r01__charging_temperature__main__l01", "Row_label_de"): "Ladetemperatur",
    ("s04__r02__discharging_temperature__main__l01", "Row_label_it"): "Temperatura di scarica",
}

# The print's EINGANGSPORTS / AUSGANGSPORTE (PDF page 66) mix two nouns. The
# reviewed wording is the one the JE-1000H and JE-3600A EU prints set (PDF
# page 70 of each).
# (spec_titles.csv title_en, Localized_Copy.csv copy_key) -> heading
GERMAN_PORT_HEADINGS = {
    ("INPUT PORTS", "spec.section.input_ports"): "EINGANGSANSCHLÜSSE",
    ("OUTPUT PORTS", "spec.section.output_ports"): "AUSGANGSANSCHLÜSSE",
}
TEN_AMPS = re.compile(r"\b10 [AА]\b")


def _rows(name: str) -> list[dict[str, str]]:
    with (DATA_ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _spec_row(suffix: str) -> dict[str, str]:
    (row,) = [row for row in _rows("Spec_Master.csv") if row["spec_row_key"] == SPEC_ROW + suffix]
    return row


def _rendered(lang: str) -> dict[str, object]:
    return renderers.collect_spec_content(
        blocks=_rows("Spec_Master.csv"),
        sku_id="JE-2000F_EU",
        lang=lang,
        vars_map={
            "model": "JE-2000F",
            "region": "EU",
            "spec_titles_csv": str(DATA_ROOT / "spec_titles.csv"),
        },
    )


def _values_by_row_key(lang: str) -> dict[str, str]:
    """Map each rendered row of one language back to its Spec_Master Row_key."""
    column = "Row_label_source" if lang == "en" else f"Row_label_{lang}"
    keys = {
        row[column]: row["Row_key"]
        for row in _rows("Spec_Master.csv")
        if row["Page"] == "specifications" and row["document_key"] == "JE-2000F_EU"
    }
    values: dict[str, str] = {}
    for section in _rendered(lang)["sections"]:
        for label, value in section["rows"]:
            values.setdefault(keys[label], value)
    return values


class Je2000fEuSpecPrintTests(unittest.TestCase):
    def test_frozen_cells_hold_the_printed_text(self) -> None:
        for (suffix, column), printed in PRINTED_CELLS.items():
            with self.subTest(row=suffix, column=column):
                self.assertEqual(printed, _spec_row(suffix)[column])

    def test_every_table_prints_4000_cycles_and_the_printed_ac_ratings(self) -> None:
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                values = _values_by_row_key(lang)
                self.assertIn("4000", values["cycle_life"])
                self.assertEqual([], [text for text in values.values() if "6000" in text])
                self.assertIsNone(TEN_AMPS.search(values["ac_output"]), values["ac_output"])
                self.assertIn("2200", values["ac_output"])
                self.assertIsNone(TEN_AMPS.search(values["ac_output_bypass"]))
                self.assertRegex(values["ac_output_bypass"], r"2200 (W|Вт) (max|máx|макс)\.$")
                # The print keeps 10 A on both AC input lines (charge and bypass mode).
                self.assertEqual(2, len(TEN_AMPS.findall(values["ac_input"])), values["ac_input"])

    def test_labels_follow_the_print(self) -> None:
        english = _values_by_row_key("en")
        self.assertTrue(english["dc8020_ports"].startswith("Car: 11 V-16 V⎓8 A max."))
        self.assertNotIn("Vehicle", english["dc8020_ports"])
        french = [label for section in _rendered("fr")["sections"] for label, _ in section["rows"]]
        self.assertIn("N° modèle", french)
        self.assertIn("3 × Sortie CA", french)
        self.assertNotIn("N° de modèle", french)
        self.assertNotIn("3 × Sorties CA", french)

    def test_german_port_headings_use_one_reviewed_noun(self) -> None:
        titles = {row["title_en"]: row["title_de"] for row in _rows("spec_titles.csv")}
        copy = {row["copy_key"]: row["text_de"] for row in _rows("Localized_Copy.csv")}
        rendered = [section["title"] for section in _rendered("de")["sections"]]
        for (title_key, copy_key), heading in GERMAN_PORT_HEADINGS.items():
            with self.subTest(section=title_key):
                self.assertEqual(heading, titles[title_key])
                self.assertEqual(heading, copy[copy_key])
                self.assertIn(heading, rendered)
        self.assertNotIn("EINGANGSPORTS", rendered)
        self.assertNotIn("AUSGANGSPORTE", rendered)

    def test_temperature_labels_use_the_reviewed_wording(self) -> None:
        expected = {
            "de": ["Ladetemperatur", "Entladetemperatur"],
            "it": ["Temperatura di ricarica", "Temperatura di scarica"],
        }
        for lang, labels in expected.items():
            with self.subTest(lang=lang):
                sections = _rendered(lang)["sections"]
                self.assertEqual(labels, [label for label, _ in sections[-1]["rows"]])

    def test_reviewed_web_wording_is_kept(self) -> None:
        # The en print's singular "Dimension" is a typo; every other block and
        # the rest of the manual use the plural.
        self.assertEqual("Dimensions", _spec_row("s01__r06__dimensions__main__l01")["Row_label_source"])
        # The fr print detaches the minus sign ("- 10 °C"); the Web keeps the
        # corrected value that the fr charging note (PDF page 31) prints.
        self.assertEqual(
            "-10 °C à 45 °C",
            _spec_row("s04__r02__discharging_temperature__main__l01")["Value_fr"],
        )


if __name__ == "__main__":
    unittest.main()
