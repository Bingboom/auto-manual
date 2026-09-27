"""JE-3000C/EU Web specification tables follow the approved V2.0-2026-07-31 print.

Operator ruling of 2026-09-27: values, structure and labels follow the print (spec
pages at PDF 18/34/50/66/82/98), formatting keeps the house rules, and print defects
keep their reviewed wording. The 2026-09-15 revision is a separate item.
"""
from __future__ import annotations

import csv
from pathlib import Path
import unittest

from tools.csv_pages import renderers
from tools.csv_pages.builder import CsvPageBuilder


ROOT = Path(__file__).resolve().parents[1]
FORMAL_DATA_ROOT = ROOT / "manual_sources/JE-3000C/EU/en/2.0/phase2"
LANGS = ("en", "fr", "es", "de", "it", "uk")

# Page title and the first three section headings as each block prints them.
PRINTED_TITLES = {
    "de": ("TECHNISCHE DATEN", "ALLGEMEINE INFORMATIONEN", "EINGANGSANSCHLÜSSE", "AUSGANGSANSCHLÜSSE"),
    "it": ("SPECIFICHE TECNICHE", "INFORMAZIONI GENERALI", "PORTE IN INGRESSO", "PORTE IN USCITA"),
    "uk": ("ТЕХНІЧНІ ХАРАКТЕРИСТИКИ", "ЗАГАЛЬНА ІНФОРМАЦІЯ", "ВХІДНІ ПОРТИ", "ВИХІДНІ ПОРТИ"),
}
# Line 1 of the AC input row: the en/fr/es/de/it blocks print the bare value; the
# uk block prints its charge-mode label.
AC_INPUT_LINE_ONE = {
    ("en", "1 × AC Input"): "220 V-240 V~ 50 Hz, 10 A max.",
    ("fr", "1 × Entrée CA"): "220-240 V~ 50 Hz, 10 A max.",
    ("es", "1 × Entrada CA"): "220-240 V~ 50 Hz, 10 A máx.",
    ("de", "1 × AC-Eingang"): "220-240 V~ 50 Hz, 10 A max.",
    ("it", "1 × Ingresso CA"): "220-240 V~ 50 Hz, 10 A max.",
    ("uk", "1 вхід змінного струму"): "Режим заряджання: 220 В-240 В~ 50 Гц, 10 A макс.",
}
# English rows whose printed label or car prefix differed (PDF page 18). The
# printed "100W Max" / "18W Max" take the house unit spacing and "max.".
ENGLISH_ROWS = {
    "2 × DC8020 Ports": "Car: 12 V-16 V⎓8 A max., Double to 8 A max.\nPV: 16 V-60 V⎓12 A max., Double to 24 A / 1000 W max.",
    "2 × USB-C 100 W max.": "100 W max., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓3 A, 15 V⎓3 A, 20 V⎓5 A",
    "2 × USB-A 18 W max.": "18 W max., 5-6 V⎓3 A, 6-9 V⎓2 A, 9-12 V⎓1.5 A",
    "Charge Temperature": "0°C to 45°C",
    "Discharge Temperature": "-10°C to 45°C",
}
PRINTED_VALUES = {
    ("fr", "Capacité"): "3072 Wh (60 Ah/51,2 V DC)",
    ("es", "Capacidad"): "3072 Wh (60 Ah/51,2 V DC)",
}
FOOTNOTE_ONE = {
    "de": "① Das Produkt kann den Akku über die Steckdose aufladen und gleichzeitig Strom über die AC-Ausgangsports liefern.",
    "uk": "① Продукт може заряджати акумулятор від мережевої розетки змінного струму або ATS, "
    "одночасно подаючи живлення через вихідні порти змінного струму.",
}
# Print defects: the Web keeps the reviewed wording, not the printed text.
REVIEWED_WORDING = {
    ("fr", "2 × Ports DC8020"): "Voiture : 12 V-16 V⎓8 A max., double à 8 A max.",  # printed "Oiture:"
    ("es", "2 × Puertos DC8020"): "PV: 16-60 V⎓12 A, Doble a 24 A máx./1000 W máx.",  # printed "/400 W Máx"
    ("es", "2 × Salida USB-A 18W MAX"): "18 W máx., 5-6 V⎓3 A, 6-9 V⎓2 A, 9-12 V⎓1,5 A",  # printed "USB-C 18W"
    ("de", "2 × DC8020-Anschlüsse"): "Auto: 12-16 V⎓8 A max., Doppelanschluss 8 A max.",  # printed "Car:"
    ("de", "1 × DC 12 V-Anschluss"): "12 V⎓10 A max.",  # printed "DC-12V-Ausgangstaste"
    ("it", "1 × Ingresso CA"): "Modalità bypass①: 220-240 V~ 50 Hz, 10 A max.",  # printed "AC modalità bypass"
    ("it", "Durata del ciclo"): "4000 cicli fino al 70% di capacità",  # printed "fino all' 70%"
    ("uk", "2 виходи USB-A 18W MAX"): "18 Вт макс., 5-6 В⎓3 A, 6-9 В⎓2 A, 9-12 В⎓1,5 A",  # printed "2 вихід"
    ("uk", "Температура заряджання"): "від 0 °C до 45 °C",  # printed "заряджаннявід"
}
REVIEWED_HEADINGS = {"de": "UMGEBUNGSTEMPERATUR IM BETRIEB", "it": "TEMPERATURA OPERATIVA AMBIENTALE"}  # printed in English
REVIEWED_TRAILERS = {
    "fr": "※ USB Type-C® et USB-C® sont des marques déposées de USB Implementers Forum.",  # printed truncated
    "uk": "② Вказує, що два або більше вихідних портів змінного струму працюють разом.",  # printed without "струму"
}
TITLE_COPY_KEYS = {
    "spec.page_title": "SPECIFICATIONS",
    "spec.section.general_info": "GENERAL INFO",
    "spec.section.input_ports": "INPUT PORTS",
    "spec.section.output_ports": "OUTPUT PORTS",
    "spec.section.environmental_operating_temperature": "ENVIRONMENTAL OPERATING TEMPERATURE",
}


def _rows(name: str) -> list[dict[str, str]]:
    with (FORMAL_DATA_ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _spec_page(lang: str) -> dict:
    blocks = _rows("Spec_Master.csv")
    blocks += CsvPageBuilder._normalize_spec_footnote_rows(_rows("Spec_Footnotes.csv"))
    blocks += CsvPageBuilder._normalize_spec_note_rows(_rows("Spec_Notes.csv"))
    return renderers.collect_spec_content(
        blocks=blocks,
        sku_id="JE-3000C_EU",
        lang=lang,
        vars_map={
            "model": "JE-3000C",
            "region": "EU",
            "spec_titles_csv": str(FORMAL_DATA_ROOT / "spec_titles.csv"),
        },
    )


class Je3000cEuSpecPrintTests(unittest.TestCase):
    """The frozen source renders the 07-31 print's spec tables on all six routes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pages = {lang: _spec_page(lang) for lang in LANGS}
        cls.rows = {
            lang: {label: value for section in page["sections"] for label, value in section["rows"]}
            for lang, page in cls.pages.items()
        }

    def test_titles_follow_the_print(self) -> None:
        for lang, (title, *sections) in PRINTED_TITLES.items():
            with self.subTest(lang=lang):
                page = self.pages[lang]
                self.assertEqual(title, page["title_main"])
                self.assertEqual(sections, [section["title"] for section in page["sections"]][:3])

    def test_ac_input_line_one_has_no_charge_mode_label_except_uk(self) -> None:
        for (lang, label), line in AC_INPUT_LINE_ONE.items():
            with self.subTest(lang=lang):
                self.assertEqual(line, self.rows[lang][label].split("\n")[0])

    def test_english_labels_follow_the_print(self) -> None:
        for label, value in ENGLISH_ROWS.items():
            with self.subTest(label=label):
                self.assertEqual(value, self.rows["en"].get(label))
        for label in ("2 × USB-C", "2 × USB-A", "Charging Temperature", "Discharging Temperature"):
            self.assertNotIn(label, self.rows["en"])

    def test_values_and_footnote_one_follow_the_print(self) -> None:
        for (lang, label), value in PRINTED_VALUES.items():
            self.assertEqual(value, self.rows[lang][label], lang)
        for lang, footnote in FOOTNOTE_ONE.items():
            self.assertEqual(footnote, self.pages[lang]["footnotes"][0], lang)

    def test_print_defects_keep_the_reviewed_wording(self) -> None:
        for (lang, label), value in REVIEWED_WORDING.items():
            with self.subTest(lang=lang, label=label):
                self.assertIn(value, self.rows[lang][label])
        for lang, heading in REVIEWED_HEADINGS.items():
            self.assertEqual(heading, self.pages[lang]["sections"][3]["title"], lang)
        for lang, trailer in REVIEWED_TRAILERS.items():
            page = self.pages[lang]
            self.assertIn(trailer, [*page["notes"], *page["footnotes"]], lang)

    def test_localized_copy_mirrors_the_spec_titles(self) -> None:
        titles = {row["title_en"]: row for row in _rows("spec_titles.csv")}
        copy = {row["copy_key"]: row for row in _rows("Localized_Copy.csv")}
        for key, title in TITLE_COPY_KEYS.items():
            for lang in LANGS[1:]:
                with self.subTest(key=key, lang=lang):
                    self.assertEqual(titles[title][f"title_{lang}"], copy[key][f"text_{lang}"])


if __name__ == "__main__":
    unittest.main()
