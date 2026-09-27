"""JE-2000E/EU specification tables follow each print block's spec page.

Authority: the V2.0-2026-08-03 EUUK print (SHA-256 734f89ad…), spec pages PDF 21/40/59/78/97/116
(en/fr/es/de/it/uk). Values, structure and labels follow the print; the frozen source keeps its
house format (a space between a number and its unit, ``: `` after a line prefix). Where the print is
wrong, the page keeps the reviewed wording.
"""

from __future__ import annotations

import csv
from pathlib import Path
import re
import unittest

from tools.csv_pages.builder import BuildPaths, CsvPageBuilder
from tools.csv_pages.renderers_spec_parser import collect_spec_content


ROOT = Path(__file__).resolve().parents[1]
FORMAL_DATA_ROOT = ROOT / "manual_sources" / "JE-2000E" / "EU" / "en" / "2.0" / "phase2"
LANGS = ("en", "fr", "es", "de", "it", "uk")
TRANSLATED = LANGS[1:]

# Section order of every block: general info, input ports, output ports, temperature.
GENERAL, INPUTS, OUTPUTS, TEMPERATURE = range(4)

MODEL_NO_LABELS = {
    "en": "Model No.", "fr": "N° modèle", "es": "N° de modelo",
    "de": "Modellnummer", "it": "Modello n.", "uk": "Номер моделі",
}
# Every block prints 19,1 kg; the translations held 18,8 kg until 2026-09-27.
WEIGHTS = {
    "en": "About 19.1 kg", "fr": "Environ 19,1 kg", "es": "Aproximadamente 19,1 kg",
    "de": "Etwa 19,1 kg", "it": "Circa 19,1 kg", "uk": "Близько 19,1 кг",
}
AC_INPUT_MODES = {
    "en": ("Charge Mode", "Bypass Mode①"),
    "fr": ("Mode charge", "Mode dérivation①"),
    "es": ("Modo de carga", "Modo bypass①"),
    "de": ("Lademodus", "Bypass-Modus①"),
    "it": ("Modalità di ricarica", "Modalità bypass①"),
    "uk": ("Режим заряджання", "Байпасний режим①"),
}
# The DC8020 lines in each block's printed order and wording. en and fr print PV first,
# es/de/it/uk the car line first. #1124 re-ordered only the English cells, so until
# 2026-09-27 the fr-uk lines carried the English PV/Car prefixes over the other port's rating.
DC8020_LINES = {
    "en": ["PV: 16 V-60 V⎓12 A, Double to 21 A / 800 W max.",
           "Car: 11 V-16 V⎓8 A max., Double to 8 A max."],
    "fr": ["PV: 16 V-60 V⎓12 A max., Double à 21 A / 800 W max.",
           "Voiture: 11 V-16 V⎓8 A max., Double à 8 A max."],
    "es": ["Coche: 11 V-16 V⎓8 A máx., Doble a 8 A máx.",
           "PV: 16 V-60 V⎓12 A, Doble hasta 21 A / 800 W máx."],
    "de": ["Auto: 11–16 V⎓8 A max., bei Verwendung beider Eingänge bis zu 8 A max.",
           "PV: 16–60 V⎓12 A, bei Verwendung beider Eingänge bis zu 21 A / 800 W max."],
    "it": ["Auto: 11 V-16 V⎓8 A max., fino a 8 A max. con doppio ingresso",
           "FV: 16 V-60 V⎓12 A, fino a 21 A / 800 W max. con doppio ingresso"],
    "uk": ["Автомобіль: 11–16 В⎓8 А макс., до 8 А макс. при використанні двох входів",
           "PV: 16–60 В⎓12 А, до 21 А / 800 Вт макс. при використанні двох входів"],
}
CAR_PREFIXES = {"Car", "Voiture", "Coche", "Auto", "Автомобіль"}
PV_PREFIXES = {"PV", "FV"}
# The output rows in print order: one row per USB-C port, three AC outputs in every block.
OUTPUT_LABELS = {
    "en": ["3 × AC Output", "AC Output in Bypass Mode①", "1 × USB-A Output", "1 × USB-C 30W Output",
           "1 × USB-C 140W Output", "1 × DC 12V Port", "1 × DC Expansion Port"],
    "fr": ["3 × Sortie CA", "Sortie CA en mode bypass①", "1 × Sortie USB-A", "1 × Sortie USB-C 30 W",
           "1 × Sortie USB-C 140 W", "1 × Port CC 12 V", "1 × Port d’extension CC"],
    "es": ["3 × Salidas CA", "Salida de CA en modo bypass①", "1 × Salida USB-A", "1 × Salida USB-C 30 W",
           "1 × Salida USB-C 140 W", "1 × Puerto DC 12 V", "1 × Puerto de expansión CC"],
    # The print sets "1 × USB-A -Ausgänge" (plural, stray space); the page keeps the reviewed label.
    "de": ["3 × AC-Ausgänge", "AC-Ausgang im Bypass-Modus①", "1 × USB-A-Ausgang", "1 × USB-C-Ausgang 30 W",
           "1 × USB-C-Ausgang 140 W", "1 × DC 12 V-Anschluss", "1 × DC-Erweiterungsanschluss"],
    "it": ["3 × Uscita CA", "Uscita CA in modalità bypass①", "1 × Uscita USB-A", "1 × Uscita USB-C 30 W",
           "1 × Uscita USB-C 140 W", "1 × Presa da 12 V CC", "1 × Porta di Espansione CC"],
    "uk": ["3 виходи змінного струму", "Вихід змінного струму у байпасному режимі①", "1 вихід USB-A 18 Вт",
           "Вихід USB-C 30 Вт", "Вихід USB-C 140 Вт", "Порт постійного струму 12 В",
           "1 порт розширення постійного струму"],
}
TEMPERATURE_LABELS = {
    "en": ["Charge Temperature", "Discharge Temperature"],
    "fr": ["Température de charge", "Température de décharge"],
    "es": ["Temperatura de carga", "Temperatura de descarga"],
    # The de table prints the typo "Ladtemperatur" (PDF page 78); its own prose prints
    # "Ladetemperatur" (page 75), the reviewed wording.
    "de": ["Ladetemperatur", "Entladetemperatur"],
    "it": ["Temperatura di carica", "Temperatura di scarica"],
    "uk": ["Температура заряджання", "Температура розряджання"],
}
# Page title and section headings (spec_titles.csv, kept equal to Localized_Copy.csv).
PRINTED_HEADINGS = {
    ("SPECIFICATIONS", "spec.page_title", "it"): "SPECIFICHE TECNICHE",
    ("SPECIFICATIONS", "spec.page_title", "uk"): "ТЕХНІЧНІ ХАРАКТЕРИСТИКИ",
    ("GENERAL INFO", "spec.section.general_info", "it"): "INFORMAZIONI GENERALI",
    ("INPUT PORTS", "spec.section.input_ports", "it"): "PORTE IN INGRESSO",
    ("OUTPUT PORTS", "spec.section.output_ports", "it"): "PORTE IN USCITA",
}
GERMAN_FOOTNOTE = (
    "① Das Produkt kann den Akku über die Steckdose aufladen und gleichzeitig Strom "
    "über die AC-Ausgangsanschlüsse liefern."
)
# The expansion-port cells (input, output) as each block prints them, with a decimal comma
# and the page's own units. The fr-uk cells were empty until 2026-09-27, so the page showed
# the English "36.8 V-57.6 V". The Italian input prints "36,8V-57,6V" and gains the house
# space; uk prints Cyrillic В with a Latin A, as most of its other amp values do.
EXPANSION_VALUES = {
    "en": ("36.8 V-57.6 V⎓75 A max.", "36.8 V-57.6 V⎓55 A max."),
    "fr": ("36,8 V-57,6 V⎓75 A max.", "36,8 V-57,6 V⎓55 A max."),
    "es": ("36,8 V-57,6 V⎓75 A máx.", "36,8 V-57,6 V⎓55 A máx."),
    "de": ("36,8 V-57,6 V⎓75 A max.", "36,8 V-57,6 V⎓55 A max."),
    "it": ("36,8 V-57,6 V⎓75 A max.", "36,8 V-57,6 V⎓55 A max."),
    "uk": ("36,8 В-57,6 В⎓75 A макс.", "36,8 В-57,6 В⎓55 A макс."),
}
# The de block prints the mixed pair EINGANGSPORTS / AUSGANGSPORTE (PDF page 78). The
# reviewed pair is the one the JE-1000H and JE-3600A EU prints set (PDF page 70 of each).
GERMAN_PORT_HEADINGS = {
    ("INPUT PORTS", "spec.section.input_ports"): "EINGANGSANSCHLÜSSE",
    ("OUTPUT PORTS", "spec.section.output_ports"): "AUSGANGSANSCHLÜSSE",
}
ENGLISH_DECIMAL = re.compile(r"\d\.\d")


def spec_content(lang: str, data_root: Path | None = None) -> dict[str, object]:
    """The spec page content the Web build renders from the frozen source."""
    root = data_root or FORMAL_DATA_ROOT
    paths = BuildPaths(
        root=ROOT,
        page_registry=root / "page_registry.csv",
        page_blocks_dir=root,
        template_dir=ROOT / "docs" / "templates",
        output_dir=ROOT / "docs" / "generated",
        spec_master_csv=root / "Spec_Master.csv",
        spec_footnotes_csv=root / "Spec_Footnotes.csv",
        spec_notes_csv=root / "Spec_Notes.csv",
        spec_titles_csv=root / "spec_titles.csv",
        localized_copy_csv=root / "Localized_Copy.csv",
    )
    blocks = CsvPageBuilder(paths)._load_page_blocks("spec")
    return collect_spec_content(
        blocks, "", lang,
        {"model": "JE-2000E", "region": "EU", "lang": lang, "spec_titles_csv": str(root / "spec_titles.csv")},
    )


def _rows(name: str) -> list[dict[str, str]]:
    with (FORMAL_DATA_ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Je2000eEuSpecPrintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = {lang: spec_content(lang) for lang in LANGS}

    def section(self, lang: str, index: int) -> list[tuple[str, str]]:
        sections = self.content[lang]["sections"]
        assert isinstance(sections, list)
        return list(sections[index]["rows"])

    def test_general_info_labels_and_weight(self) -> None:
        for lang in LANGS:
            with self.subTest(lang=lang):
                rows = dict(self.section(lang, GENERAL))
                self.assertEqual("JE-2000E", rows.get(MODEL_NO_LABELS[lang]), sorted(rows))
                self.assertIn(WEIGHTS[lang], rows.values())
                self.assertNotIn("18,8", " ".join(rows.values()))

    def test_ac_input_modes_use_the_print_wording(self) -> None:
        for lang, modes in AC_INPUT_MODES.items():
            with self.subTest(lang=lang):
                (_label, value), _dc8020, _expansion = self.section(lang, INPUTS)
                self.assertEqual(list(modes), [line.split(": ", 1)[0] for line in value.splitlines()])

    def test_dc8020_lines_follow_each_block(self) -> None:
        for lang, expected in DC8020_LINES.items():
            with self.subTest(lang=lang):
                _ac_input, (_label, value), _expansion = self.section(lang, INPUTS)
                self.assertEqual(expected, value.splitlines())
                for line in value.splitlines():
                    prefix, rating = line.split(": ", 1)
                    # Car ports take 11-16 V at 8 A, PV ports 16-60 V at 12 A.
                    if prefix in CAR_PREFIXES:
                        self.assertTrue(rating.startswith("11"), line)
                    else:
                        self.assertIn(prefix, PV_PREFIXES)
                        self.assertTrue(rating.startswith("16"), line)
                        self.assertIn("12", rating.split(",", 1)[0])

    def test_output_rows_follow_the_print(self) -> None:
        for lang, labels in OUTPUT_LABELS.items():
            with self.subTest(lang=lang):
                rows = self.section(lang, OUTPUTS)
                self.assertEqual(labels, [label for label, _value in rows])
                usb_c_30, usb_c_140 = rows[3][1], rows[4][1]
                # Each USB-C port has its own single-line row (the fr-uk rows used to merge).
                self.assertNotIn("\n", usb_c_30 + usb_c_140)
                self.assertRegex(usb_c_30, r"^30 (W|Вт) ")
                self.assertRegex(usb_c_140, r"^140 (W|Вт) ")

    def test_temperature_labels(self) -> None:
        for lang, labels in TEMPERATURE_LABELS.items():
            with self.subTest(lang=lang):
                self.assertEqual(labels, [label for label, _value in self.section(lang, TEMPERATURE)])

    def test_titles_follow_the_print(self) -> None:
        self.assertEqual("SPECIFICHE TECNICHE", self.content["it"]["title_main"])
        self.assertEqual("ТЕХНІЧНІ ХАРАКТЕРИСТИКИ", self.content["uk"]["title_main"])
        italian = [section["title"] for section in self.content["it"]["sections"]]
        self.assertEqual(
            ["INFORMAZIONI GENERALI", "PORTE IN INGRESSO", "PORTE IN USCITA", "TEMPERATURA OPERATIVA AMBIENTALE"],
            italian,
        )
        titles = {row["title_en"]: row for row in _rows("spec_titles.csv")}
        copy = {row["copy_key"]: row for row in _rows("Localized_Copy.csv")}
        for (title_key, copy_key, lang), heading in PRINTED_HEADINGS.items():
            with self.subTest(title=title_key, lang=lang):
                self.assertEqual(heading, titles[title_key][f"title_{lang}"])
                self.assertEqual(heading, copy[copy_key][f"text_{lang}"])

    def test_german_footnote_follows_the_print(self) -> None:
        self.assertEqual([GERMAN_FOOTNOTE], self.content["de"]["footnotes"])

    def test_print_defects_keep_the_reviewed_wording(self) -> None:
        """Seven print defects the page already corrected stay corrected."""
        # fr prints the trademark note in English and numbers its only footnote "① 1.".
        self.assertEqual(
            ["※ USB Type-C® et USB-C® sont des marques déposées de USB Implementers Forum."],
            self.content["fr"]["notes"],
        )
        (french_footnote,) = self.content["fr"]["footnotes"]
        self.assertTrue(french_footnote.startswith("① Le produit"))
        # de prints the Spanish "máx." on its bypass output and a garbled temperature heading.
        self.assertEqual("230 V~ 50 Hz, 10 A max.", self.section("de", OUTPUTS)[1][1])
        self.assertEqual("UMGEBUNGSTEMPERATUR IM BETRIEB", self.content["de"]["sections"][TEMPERATURE]["title"])
        # it prints the English "2 × DC8020 Ports"; uk repeats its AC-input label on this row.
        self.assertEqual("2 porte DC8020", self.section("it", INPUTS)[1][0])
        self.assertEqual("2 порти DC8020", self.section("uk", INPUTS)[1][0])

    def test_translated_routes_print_no_english_prefix(self) -> None:
        for lang in TRANSLATED:
            with self.subTest(lang=lang):
                _ac_input, (_label, value), _expansion = self.section(lang, INPUTS)
                self.assertNotIn("Car:", value)

    def test_expansion_ports_follow_each_block(self) -> None:
        for lang, (value_in, value_out) in EXPANSION_VALUES.items():
            with self.subTest(lang=lang):
                self.assertEqual(value_in, self.section(lang, INPUTS)[2][1])
                self.assertEqual(value_out, self.section(lang, OUTPUTS)[6][1])

    def test_translated_values_use_a_decimal_comma(self) -> None:
        """No fr-uk specification value keeps an English decimal point."""
        for lang in TRANSLATED:
            with self.subTest(lang=lang):
                values = [value for section in self.content[lang]["sections"] for _label, value in section["rows"]]
                self.assertEqual([], [value for value in values if ENGLISH_DECIMAL.search(value)])

    def test_german_port_headings_use_the_reviewed_pair(self) -> None:
        german = [section["title"] for section in self.content["de"]["sections"]]
        self.assertEqual(
            ["ALLGEMEINE INFORMATIONEN", "EINGANGSANSCHLÜSSE", "AUSGANGSANSCHLÜSSE", "UMGEBUNGSTEMPERATUR IM BETRIEB"],
            german,
        )
        titles = {row["title_en"]: row for row in _rows("spec_titles.csv")}
        copy = {row["copy_key"]: row for row in _rows("Localized_Copy.csv")}
        for (title_key, copy_key), heading in GERMAN_PORT_HEADINGS.items():
            with self.subTest(heading=heading):
                self.assertEqual(heading, titles[title_key]["title_de"])
                self.assertEqual(heading, copy[copy_key]["text_de"])


if __name__ == "__main__":
    unittest.main()
