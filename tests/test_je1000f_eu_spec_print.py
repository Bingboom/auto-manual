"""JE-1000F/EU Web specification tables follow the V2.0 EU-UK print.

The es/de/it routes build with ``--source review``, which regenerates their
spec page from the frozen phase2 cells; en/fr build ``review-asis`` from the
committed review pages. Values, structure and labels follow each print block
(PDF physical pages 19, 36, 53, 71 and 88); unit spacing, case, the decimal
comma, ``⎓`` and ``max.`` keep the house format. Print defects keep the
reviewed wording.
"""

from __future__ import annotations

import csv
from pathlib import Path
import re
import unittest

from tools.csv_pages import renderers
from tools.csv_pages.builder import BuildPaths, CsvPageBuilder


ROOT = Path(__file__).resolve().parents[1]
FORMAL_DATA_ROOT = ROOT / "manual_sources" / "JE-1000F" / "EU" / "en-fr" / "2.0" / "phase2"
REVIEW_PAGES = ROOT / "docs" / "_review" / "JE-1000F" / "EU" / "page"

# Each print block's specification table as the Web shows it (PDF pages 53,
# 71 and 88). Until 2026-09-27 these routes merged the two USB-C rows, lacked
# the bypass footnote and carried non-print labels and values. Print defects
# use the reviewed wording (see test_print_defects_keep_the_reviewed_wording).
PRINTED_TABLES: dict[str, list[tuple[str, list[tuple[str, str]]]]] = {
    "es": [
        ("INFORMACIÓN GENERAL", [
            ("Nombre del producto", "Jackery Explorer 1000"),
            ("N° de modelo", "JE-1000F"),
            ("Capacidad", "1024 Wh (20 Ah / 51,2 V DC)"),
            ("Química de las celdas", "LiFePO₄"),
            ("Peso", "Aproximadamente 10,6 kg"),
            ("Dimensiones", "31,4 x 20,1 x 23,4 cm"),
            ("Vida útil en ciclos", "4000 ciclos hasta conservar más del 70 % de capacidad"),
        ]),
        ("PUERTOS DE ENTRADA", [
            ("1 × Entrada CA", "Modo de carga: 220 V-240 V~ 50 Hz, 10 A máx."),
            ("2 × Puertos DC8020", "11 V-16 V⎓8 A máx., Doble a 8 A máx.\n"
                                   "16 V-60 V⎓12 A máx., Doble hasta 21 A / 400 W máx."),
        ]),
        ("PUERTOS DE SALIDA", [
            ("2 × Salidas CA", "230 V~ 50 Hz, 6,5 A máx., 1500 W Nominal por puerto, 1500 W en Total, "
                               "3000 W Pico de sobrecarga"),
            ("Salida de CA en modo bypass①", "220 V-240 V~ 50 Hz, 1500 W"),
            ("Salida USB-C 30 W", "30 W máx., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓2,5 A, 15 V⎓2 A, 20 V⎓1,5 A"),
            ("Salida USB-C 100 W", "100 W máx., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓3 A, 15 V⎓3 A, 20 V⎓5 A"),
            ("1 × Salida USB-A", "18 W máx., 5-6 V⎓3 A, 6-9 V⎓2 A, 9-12 V⎓1,5 A"),
            ("1 × Puerto CC 12 V", "12 V⎓10 A máx."),
        ]),
        ("TEMPERATURA DE FUNCIONAMIENTO", [
            ("Temperatura de carga", "0 °C a 45 °C"),
            ("Temperatura de descarga", "-10 °C a 45 °C"),
        ]),
    ],
    "de": [
        ("ALLGEMEINE INFORMATIONEN", [
            ("Produktname", "Jackery Explorer 1000"),
            ("Modellnummer", "JE-1000F"),
            ("Kapazität", "1024 Wh (20 Ah / 51,2 V DC)"),
            ("Zellchemie", "LiFePO₄"),
            ("Gewicht", "Etwa 10,6 kg"),
            ("Abmessungen", "31,4 x 20,1 x 23,4 cm"),
            ("Zykluslebensdauer", "4000 Zyklen bei über 70 % Restkapazität"),
        ]),
        ("EINGANGSANSCHLÜSSE", [
            ("1 × AC-Eingang", "Lademodus: 220-240 V~ 50 Hz, 10 A max."),
            ("2 × DC8020-Ports", "11–16 V⎓8 A max., bei Verwendung beider Eingänge bis zu 8 A max.\n"
                                 "16–60 V⎓12 A max., bei Verwendung beider Eingänge bis zu 21 A / 400 W max."),
        ]),
        ("AUSGANGSANSCHLÜSSE", [
            ("2 × AC-Ausgänge", "230 V~ 50 Hz, 6,5 A max., 1500 W Nennleistung pro Port, 1500 W insgesamt, "
                                "3000 W Spitzenleistung"),
            ("AC-Ausgang im Bypass-Modus①", "220 V-240 V~ 50 Hz, 1500 W"),
            ("1 × USB-C-Ausgang 30 W", "30 W max., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓2,5 A, 15 V⎓2 A, 20 V⎓1,5 A"),
            ("1 × USB-C-Ausgang 100 W", "100 W max., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓3 A, 15 V⎓3 A, 20 V⎓5 A"),
            ("1 × USB-A", "18 W max., 5-6 V⎓3 A, 6-9 V⎓2 A, 9-12 V⎓1,5 A"),
            ("1 × DC 12 V-Anschluss", "12 V⎓10 A max."),
        ]),
        ("UMGEBUNGSBETRIEBSTEMPERATUR", [
            ("Ladetemperatur", "von 0 °C bis 45 °C"),
            ("Entladetemperatur", "von -10 °C bis 45 °C"),
        ]),
    ],
    "it": [
        ("INFO GENERALI", [
            ("Nome del prodotto", "Jackery Explorer 1000"),
            ("Numero di modello", "JE-1000F"),
            ("Capacità", "1024 Wh (20 Ah / 51,2 V DC)"),
            ("Chimica delle celle", "LiFePO₄"),
            ("Peso", "Circa 10,6 kg"),
            ("Dimensioni", "31,4 x 20,1 x 23,4 cm"),
            ("Vita ciclica", "4000 cicli con capacità residua superiore al 70%"),
        ]),
        ("PORTE IN INGRESSO", [
            ("1 × Ingresso CA", "Modalità di ricarica: 220-240 V~ 50 Hz, 10 A max."),
            ("2 porte DC8020", "11 V-16 V⎓8 A max., fino a 8 A max. con doppio ingresso\n"
                               "16 V-60 V⎓12 A, fino a 21 A / 400 W max. con doppio ingresso"),
        ]),
        ("PORTE IN USCITA", [
            ("2 × uscite CA", "230 V~ 50 Hz, 6,5 A max., 1500 W nominali per porta, 1500 W totali, "
                              "3000 W di picco"),
            ("Uscita CA in modalità bypass①", "220 V-240 V~ 50 Hz, 1500 W"),
            ("1 × Uscita USB-C 30 W", "30 W max., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓2,5 A, 15 V⎓2 A, 20 V⎓1,5 A"),
            ("1 × Uscita USB-C 100 W", "100 W max., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓3 A, 15 V⎓3 A, 20 V⎓5 A"),
            ("1 × USB-A", "18 W max., 5-6 V⎓3 A, 6-9 V⎓2 A, 9-12 V⎓1,5 A"),
            ("1 × Porta CC 12 V", "12 V⎓10 A max."),
        ]),
        ("TEMPERATURA OPERATIVA AMBIENTALE", [
            ("Temperatura di ricarica", "da 0 °C a 45 °C"),
            ("Temperatura di scarica", "da -10 °C a 45 °C"),
        ]),
    ],
}

# The print's bypass footnote in each block (the renderer adds the marker).
PRINTED_BYPASS_FOOTNOTES = {
    "es": "El producto puede cargar la batería desde una toma de corriente CA mientras suministra "
          "energía a través de los puertos de salida CA.",
    "de": "Das Produkt kann den Akku über die Steckdose aufladen und gleichzeitig Strom über die "
          "AC-Ausgangsanschlüsse liefern.",
    "it": "Il prodotto può caricare la batteria dalla presa a muro CA mentre fornisce energia "
          "tramite le porte di uscita CA.",
}


def _rows(name: str) -> list[dict[str, str]]:
    with (FORMAL_DATA_ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _spec_content(lang: str) -> dict[str, object]:
    """The spec content the --source review build renders for ``lang``."""
    paths = BuildPaths(
        root=ROOT,
        page_registry=FORMAL_DATA_ROOT / "page_registry.csv",
        page_blocks_dir=FORMAL_DATA_ROOT,
        template_dir=ROOT / "docs" / "templates",
        output_dir=ROOT / "docs" / "generated",
        spec_master_csv=FORMAL_DATA_ROOT / "Spec_Master.csv",
        spec_footnotes_csv=FORMAL_DATA_ROOT / "Spec_Footnotes.csv",
        spec_notes_csv=FORMAL_DATA_ROOT / "Spec_Notes.csv",
        spec_titles_csv=FORMAL_DATA_ROOT / "spec_titles.csv",
        localized_copy_csv=FORMAL_DATA_ROOT / "Localized_Copy.csv",
    )
    return renderers.collect_spec_content(
        blocks=CsvPageBuilder(paths)._load_page_blocks("spec"),
        sku_id="JE-1000F_EU",
        lang=lang,
        vars_map={
            "model": "JE-1000F",
            "region": "EU",
            "spec_titles_csv": str(FORMAL_DATA_ROOT / "spec_titles.csv"),
        },
    )


def _carriers(page: str) -> tuple[str, str]:
    """(LaTeX carrier, HTML carrier) of a committed review spec page."""
    text = (REVIEW_PAGES / page).read_text(encoding="utf-8")
    latex, html = text.split(".. only:: html", 1)
    return latex, html


class Je1000fEuSpecPrintTests(unittest.TestCase):
    def test_review_built_routes_render_each_print_blocks_table(self) -> None:
        for lang, expected in PRINTED_TABLES.items():
            with self.subTest(lang=lang):
                data = _spec_content(lang)
                sections = [
                    (section["title"], [tuple(row) for row in section["rows"]])
                    for section in data["sections"]
                ]
                self.assertEqual(expected, sections)
                self.assertEqual([f"① {PRINTED_BYPASS_FOOTNOTES[lang]}"], data["footnotes"])
                self.assertEqual(1, len(data["notes"]))
                self.assertTrue(str(data["notes"][0]).startswith("※ USB Type-C®"))

    def test_bypass_footnote_cells_hold_the_printed_sentence_without_a_marker(self) -> None:
        (footnote,) = [row for row in _rows("Spec_Footnotes.csv") if row["Footnote_id"] == "ac_bypass"]
        for lang, text in PRINTED_BYPASS_FOOTNOTES.items():
            self.assertEqual(text, footnote[f"Text_{lang}"], lang)
        (bypass,) = [row for row in _rows("Spec_Master.csv") if row["Row_key"] == "ac_output_bypass"]
        self.assertEqual("ac_bypass", bypass["Row_label_footnote_refs"])

    def test_print_defects_keep_the_reviewed_wording(self) -> None:
        def cells(lang: str) -> list[tuple[str, str]]:
            return [tuple(row) for section in _spec_content(lang)["sections"] for row in section["rows"]]

        # The IT block prints 60 Hz on its AC input and output rows; every
        # other block, and the IT bypass row, print 50 Hz.
        italian = dict(cells("it"))
        self.assertIn("50 Hz", italian["1 × Ingresso CA"])
        self.assertIn("50 Hz", italian["2 × uscite CA"])
        self.assertFalse([value for value in italian.values() if "60 Hz" in value])
        # The DE block prints the Spanish "máx." in its USB rows.
        german = cells("de")
        self.assertFalse([value for _label, value in german if "máx" in value])
        # The DE table prints "Ladtemperatur"; the DE block's running text
        # (PDF page 67) spells "Ladetemperatur".
        self.assertIn(("Ladetemperatur", "von 0 °C bis 45 °C"), german)
        self.assertFalse([label for label, _value in german if label == "Ladtemperatur"])
        # The DE block mixes two nouns in its port headings, EINGANGSPORTS /
        # AUSGANGSPORTE (PDF page 71). The JE-1000H and JE-3600A EU prints set
        # EINGANGSANSCHLÜSSE / AUSGANGSANSCHLÜSSE (PDF page 70 of each).
        german_titles = [section["title"] for section in _spec_content("de")["sections"]]
        self.assertEqual(["EINGANGSANSCHLÜSSE", "AUSGANGSANSCHLÜSSE"], german_titles[1:3])
        self.assertFalse({"EINGANGSPORTS", "AUSGANGSPORTE"} & set(german_titles))

    def test_port_headings_match_their_non_rendering_twins(self) -> None:
        headings = {
            # Printed on PDF page 88.
            "it": ("PORTE IN INGRESSO", "PORTE IN USCITA"),
            # The reviewed pair for the DE block's print defect (page 71).
            "de": ("EINGANGSANSCHLÜSSE", "AUSGANGSANSCHLÜSSE"),
        }
        for lang, (input_heading, output_heading) in headings.items():
            with self.subTest(lang=lang):
                titles = {row["title_en"]: row[f"title_{lang}"] for row in _rows("spec_titles.csv")}
                copy = {row["copy_key"]: row[f"text_{lang}"] for row in _rows("Localized_Copy.csv")}
                self.assertEqual(input_heading, titles["INPUT PORTS"])
                self.assertEqual(output_heading, titles["OUTPUT PORTS"])
                self.assertEqual(titles["INPUT PORTS"], copy["spec.section.input_ports"])
                self.assertEqual(titles["OUTPUT PORTS"], copy["spec.section.output_ports"])

    def test_french_review_page_follows_the_print(self) -> None:
        latex, html = _carriers("spec_fr.rst")
        for carrier in (latex, html):
            self.assertIn("N° modèle", carrier)
            self.assertNotIn("N° de modèle", carrier)
            self.assertIn("1024 Wh (20 Ah / 51,2 V DC)", carrier)
            self.assertNotIn("V CC)", carrier)
        # PDF page 36 prints the ① bypass footnote before the ※ note.
        self.assertLess(
            html.index('data-spec-trailer-kind="footnote">① Le produit'),
            html.index('data-spec-trailer-kind="note">※ USB Type-C®'),
        )
        self.assertLess(
            latex.index(r"\HBTypeSpecNote{\HBSpecMarkerOne{} Le produit"),
            latex.index(r"\HBTypeSpecNote{※ USB Type-C®"),
        )
        # Each trailer keeps its own spacing token; the page end stays last.
        self.assertEqual(
            ["footnotes", "notes"],
            re.findall(r"HBcomp_spec_(notes|footnotes)_before", latex),
        )
        self.assertGreater(latex.index(r"\HBSpecPageEnd"), latex.index(r"\HBTypeSpecNote{※"))

    def test_english_review_page_keeps_the_english_print_order(self) -> None:
        # PDF page 19 prints the ※ note before the ① footnote.
        _latex, html = _carriers("spec_en.rst")
        self.assertLess(
            html.index('data-spec-trailer-kind="note">※'),
            html.index('data-spec-trailer-kind="footnote">①'),
        )


if __name__ == "__main__":
    unittest.main()
