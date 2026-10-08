"""BP and accessory EU Web specification pages follow their approved prints.

Operator ruling 2026-09-27: values, structure and labels follow the print, and
formatting keeps the house rules. Every expectation below names its PDF page:

- JBP-2000B EUUK V2.0-2026-09-11: pages 12/20/28/36/44 (en/fr/es/de/it).
- JBP-3600A EUUK V2.0-2026-08-04: page 11 (en).
- JA-AD600A operator AI HTO814-EU-9国语言-0924 (1).ai: physical page 4 (en).
- JS-100I EUUK V2.0-2026-04-01: page 11 (en).
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.csv_pages.renderers_spec_parser import collect_spec_content


ROOT = Path(__file__).resolve().parents[1]
JBP2000B = ROOT / "manual_sources" / "JBP-2000B" / "EU" / "en" / "2.0"
JBP3600A = ROOT / "manual_sources" / "JBP-3600A" / "EU" / "en"
JA_AD600A = ROOT / "data" / "manual_sources" / "ja_ad600a_eu_en"
SOLAR = ROOT / "data" / "manual_sources"
JS100I = SOLAR / "JS-100I" / "EU" / "en" / "2.0" / "phase2"
JS100F = SOLAR / "JS-100F" / "EU" / "en" / "1.0" / "phase2"
JS200E = SOLAR / "JS-200E" / "EU" / "en" / "2.0" / "phase2"

# One INPUT/OUTPUT PORTS section per print block: (title, input row, output row).
JBP2000B_PORTS = {
    "en": ("INPUT/OUTPUT PORTS", "DC Expansion Port (Input)", "DC Expansion Port (Output)"),
    "fr": ("PORTS D’ENTRÉE/SORTIE", "Port d’extension CC (Entrée)", "Port d’extension CC (Sortie)"),
    "es": ("PUERTOS DE ENTRADA/SALIDA", "Puerto de Expansión de CC (Entrada)", "Puerto de Expansión de CC (Salida)"),
    "de": ("EINGANGS-/AUSGANGSANSCHLÜSSE", "DC-Erweiterungsanschluss (Eingang)", "DC-Erweiterungsanschluss (Ausgang)"),
    "it": ("PORTE DI INGRESSO/USCITA", "Porta di espansione CC (Ingresso)", "Porta di espansione CC (Uscita)"),
}
JBP2000B_PAGE_TITLES = {
    "en": "SPECIFICATIONS",
    "fr": "SPÉCIFICATIONS",
    "es": "ESPECIFICACIONES",
    "de": "TECHNISCHE DATEN",
    "it": "SPECIFICHE TECNICHE",
}


def spec_content(data_root: Path, model: str, lang: str) -> dict[str, object]:
    with (data_root / "Spec_Master.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return collect_spec_content(
        rows,
        "",
        lang,
        {"model": model, "region": "EU", "spec_titles_csv": str(data_root / "spec_titles.csv")},
    )


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class BatteryPackSpecPrintTests(unittest.TestCase):
    def test_jbp2000b_prints_one_ports_section_in_every_language(self) -> None:
        for lang, (title, input_label, output_label) in JBP2000B_PORTS.items():
            with self.subTest(lang=lang):
                sections = spec_content(JBP2000B / "phase2", "JBP-2000B", lang)["sections"]
                self.assertEqual(3, len(sections))
                ports = sections[1]
                self.assertEqual(title, ports["title"])
                self.assertEqual([input_label, output_label], [row[0] for row in ports["rows"]])

    def test_jbp2000b_page_titles_and_italian_section_follow_the_print(self) -> None:
        for lang, title in JBP2000B_PAGE_TITLES.items():
            with self.subTest(lang=lang):
                self.assertEqual(title, spec_content(JBP2000B / "phase2", "JBP-2000B", lang)["title_main"])
        italian = spec_content(JBP2000B / "phase2", "JBP-2000B", "it")
        self.assertEqual("INFORMAZIONI GENERALI", italian["sections"][0]["title"])

    def test_jbp2000b_italian_cycle_life_and_german_ranges(self) -> None:
        italian = dict(spec_content(JBP2000B / "phase2", "JBP-2000B", "it")["sections"][0]["rows"])
        self.assertEqual("6000 cicli fino al 70% di capacità", italian["Durata del ciclo"])
        german = spec_content(JBP2000B / "phase2", "JBP-2000B", "de")["sections"][2]["rows"]
        # The print's "-10°C und 45°C" is a defect; the reviewed range word is
        # "bis", as the same page's storage bullets print it.
        self.assertEqual(
            [("Ladetemperatur", "-10°C bis 45°C"), ("Entladetemperatur", "-10°C bis 45°C")],
            german,
        )

    def test_jbp3600a_prints_iec_code_and_expansion_port_labels(self) -> None:
        content = spec_content(JBP3600A / "phase2", "JBP-3600A", "en")
        sections = content["sections"]
        self.assertEqual(
            ["GENERAL INFO", "INPUT/OUTPUT PORTS", "ENVIRONMENTAL OPERATING TEMPERATURE"],
            [section["title"] for section in sections],
        )
        general = dict(sections[0]["rows"])
        self.assertEqual("IFpR41/136[14S4P]M/-20+40/90", general["IEC Code"])
        self.assertNotIn("Secondary Li-ion Battery", general)
        self.assertEqual(
            [
                ("DC Expansion Port (Input)", "36.4V-50.4V⎓60A Max"),
                ("DC Expansion Port (Output)", "36.4V-50.4V⎓100A Max"),
            ],
            sections[1]["rows"],
        )

    def test_merged_section_title_is_one_dictionary_row_in_both_sources(self) -> None:
        for source in (JBP2000B, JBP3600A):
            with self.subTest(source=source.relative_to(ROOT).as_posix()):
                titles = {row["title_en"]: row for row in csv_rows(source / "phase2" / "spec_titles.csv")}
                self.assertNotIn("INPUT PORTS", titles)
                self.assertNotIn("OUTPUT PORTS", titles)
                merged = titles["INPUT/OUTPUT PORTS"]
                self.assertEqual("2", merged["section_order"])
                copy = {row["copy_key"]: row for row in csv_rows(source / "phase2" / "Localized_Copy.csv")}
                self.assertNotIn("spec.section.input_ports", copy)
                self.assertNotIn("spec.section.output_ports", copy)
                localized = copy["spec.section.input_output_ports"]
                for lang, (title, _input, _output) in JBP2000B_PORTS.items():
                    self.assertEqual(title, localized[f"text_{lang}"])
                    if lang != "en":
                        self.assertEqual(title, merged[f"title_{lang}"])
                authored = {row["copy_key"]: row for row in csv_rows(source / "phase2" / "Manual_Copy_Source.csv")}
                self.assertEqual("INPUT/OUTPUT PORTS", authored["spec.section.input_output_ports"]["source_text"])
                self.assertNotIn("spec.section.output_ports", authored)

    def test_jbp2000b_frozen_data_matches_its_manifest(self) -> None:
        manifest = json.loads((JBP2000B / "source_manifest.json").read_text(encoding="utf-8"))
        prefix = "manual_sources/JBP-2000B/EU/en/2.0/phase2/"
        entries = [entry for entry in manifest["files"] if entry["path"].startswith(prefix)]
        self.assertGreaterEqual(len(entries), 20)
        for entry in entries:
            data = (ROOT / entry["path"]).read_bytes()
            self.assertEqual(entry["size_bytes"], len(data), entry["path"])
            self.assertEqual(entry["sha256"], hashlib.sha256(data).hexdigest(), entry["path"])


class AccessorySpecHeadingTests(unittest.TestCase):
    def test_ja_ad600a_page_title_is_the_printed_heading(self) -> None:
        content = spec_content(JA_AD600A, "JA-AD600A", "en")
        # Current operator source retains its eight chapter numbers on the Web.
        self.assertEqual("2. TECHNICAL SPECIFICATIONS", content["title_main"])
        rows = [row for section in content["sections"] for row in section["rows"]]
        self.assertEqual(13, len(rows))
        self.assertEqual(("Product Name", "Jackery DC-DC Charger"), rows[0])

    def test_js100i_page_title_is_the_printed_heading(self) -> None:
        content = spec_content(JS100I, "JS-100I", "en")
        self.assertEqual("TECHNICAL PARAMETERS", content["title_main"])
        self.assertEqual(
            ["BASIC INFORMATION", "ELECTRICAL DATA", "MULTIFUNCTIONAL ADAPTER"],
            [section["title"] for section in content["sections"]],
        )

    def test_heading_override_is_per_model_data(self) -> None:
        # JS-100F and JS-200E carry an inert TECHNICAL PARAMETERS spec_titles row
        # and have no approved print; the JS-100I override must not reach them.
        for data_root, model in ((JS100F, "JS-100F"), (JS200E, "JS-200E")):
            with self.subTest(model=model):
                self.assertEqual("SPECIFICATIONS", spec_content(data_root, model, "en")["title_main"])


class Jbp2000bWebBuildTests(unittest.TestCase):
    """The frozen-source Web build renders the printed de/it specification pages."""

    LANGS = ("de", "it")

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp.name)
        fake_bin = tmp / "bin"
        fake_bin.mkdir()
        fake_pandoc = fake_bin / "pandoc"
        fake_pandoc.write_text(
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            "import sys\n"
            "if '--list-output-formats' in sys.argv:\n"
            "    print('myst')\n"
            "    raise SystemExit(0)\n"
            "source = Path(sys.argv[1])\n"
            "target = Path(sys.argv[sys.argv.index('-o') + 1])\n"
            "target.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')\n",
            encoding="utf-8",
        )
        fake_pandoc.chmod(0o755)
        env = {
            **os.environ,
            "AUTO_MANUAL_OSS_ARCHIVE_CONFIG": "off",
            "AUTO_MANUAL_PRESENTATION_PROFILE": "web",
            "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
        }
        cls.html: dict[str, str] = {}
        for lang in cls.LANGS:
            staging = tmp / f"staging-{lang}"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "build.py"),
                    "md",
                    "--config",
                    str(ROOT / "configs" / f"config.bp-eu-{lang}.yaml"),
                    "--model",
                    "JBP-2000B",
                    "--region",
                    "EU",
                    "--lang",
                    lang,
                    "--data-root",
                    str(JBP2000B / "phase2"),
                    "--staging-root",
                    str(staging),
                ],
                cwd=ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode:
                raise AssertionError(
                    f"JBP-2000B/EU/{lang} frozen-source Web build failed:\n"
                    + result.stdout
                    + result.stderr
                )
            package = staging / "docs" / "_build" / "JBP-2000B" / "EU" / lang / "md"
            cls.html[lang] = (package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_spec_page_has_the_printed_heading_and_three_tables(self) -> None:
        general = {"de": "ALLGEMEINE INFORMATIONEN", "it": "INFORMAZIONI GENERALI"}
        temperature = {"de": "UMGEBUNGSTEMPERATUR IM BETRIEB", "it": "TEMPERATURA OPERATIVA AMBIENTALE"}
        for lang in self.LANGS:
            with self.subTest(lang=lang):
                soup = BeautifulSoup(self.html[lang], "html.parser")
                h1 = [heading.get_text(" ", strip=True) for heading in soup.select("h1")]
                self.assertIn(JBP2000B_PAGE_TITLES[lang], h1)
                self.assertNotIn("Spezifikationen", h1)
                compositions = soup.select("figure.hb-spec-table-composition")
                self.assertEqual(
                    [general[lang], JBP2000B_PORTS[lang][0], temperature[lang]],
                    [figure.get("aria-label") for figure in compositions],
                )
                ports = [
                    row.select_one("th").get_text(" ", strip=True)
                    for row in compositions[1].select("tbody tr")
                ]
                self.assertEqual(list(JBP2000B_PORTS[lang][1:]), ports)


if __name__ == "__main__":
    unittest.main()
