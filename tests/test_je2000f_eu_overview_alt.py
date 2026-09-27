"""JE-2000F/EU product-overview alt text says what the approved print says.

Every language block of the print (``Jackery Explorer 2000 User Manual
(JE-2000F) EUUK V2.0-2026-08-04.pdf``, front view on PDF pages
8/24/40/56/72/88, printed 3/19/35/51/67/83) labels the AC output with its
voltage, frequency and rating only. No block gives it a current; the surge
peak belongs to the separate Total Output callout. The Web keeps the figure's
callout copy as the finished image's alt text: the product-overview table
rows of the frozen ``Spec_Master.csv`` render the copy, and
``docs/renderers/web/je2000f_eu_<lang>_illustrations.json`` binds it by exact
text before the build consumes it.

The en print's right-side drawing labels the AC inlet ``AC 100V-120V 15A
MAX``, a US rating. That figure stays as printed; no Web text repeats it.
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "manual_sources" / "JE-2000F" / "EU" / "en" / "2.0" / "phase2"
WEB = ROOT / "docs" / "renderers" / "web"
OVERVIEW_ROW = "JE-2000F_EU__v1.0__Product_overview__"
LANGUAGES = ("en", "fr", "es", "de", "it", "uk")

# Front view of each print block: (AC output label, AC output callout), in
# house formatting. The PDF page is the block's product overview.
PRINTED_AC_OUTPUT = {
    "en": ("AC Output", "230 V~ 50 Hz, 2200 W Rated"),
    "fr": ("Sortie CA", "230 V~ 50 Hz, 2200 W Nominal"),
    "es": ("Salida de CA", "230 V~ 50 Hz, 2200 W Nominal"),
    "de": ("AC-Ausgang", "230 V~ 50 Hz, 2200 W Nennleistung"),
    "it": ("Uscita CA", "230 V~ 50 Hz, 2200 W nominali"),
    "uk": ("Вихід змінного струму", "230 В~ 50 Гц, 2200 Вт ном. потужності"),
}
PRINT_PAGES = {"en": 8, "fr": 24, "es": 40, "de": 56, "it": 72, "uk": 88}
AC_OUTPUT_LABEL = "s03__r04__ac_output__front.label__l01"
AC_OUTPUT_SPEC = "s03__r04__ac_output__front.spec__l01"
AC_INPUT_SPEC = "s02__r02__ac_input__side.spec__l01"
TOTAL_OUTPUT_SPEC = "s03__r05__total_output__front.spec__l01"

TEN_AMPS = re.compile(r"\b10\s?[AА]\b")
US_AC_RATING = re.compile(r"100\s?[VВ]?\s?[-–]\s?120|\b15\s?[AА]\b")


def _column(lang: str) -> str:
    return "Value_source" if lang == "en" else f"Value_{lang}"


def _overview_cell(suffix: str, lang: str) -> str:
    with (DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
        (row,) = [
            row for row in csv.DictReader(handle) if row["spec_row_key"] == OVERVIEW_ROW + suffix
        ]
    return row[_column(lang)]


def _front_view_entry(lang: str) -> dict:
    manifest = json.loads(
        (WEB / f"je2000f_eu_{lang}_illustrations.json").read_text(encoding="utf-8")
    )
    (entry,) = [
        item for item in manifest["illustrations"] if item["replaces"] == ["front_product.jpg"]
    ]
    return entry


def _after_label(text: str, label: str) -> str:
    """Return the copy after the AC output label, which occurs once."""
    marker = f" {label} "
    if text.count(marker) != 1:
        raise AssertionError(f"{label!r} must occur once in {text!r}")
    return text.split(marker, 1)[1]


class Je2000fEuOverviewAltSourceTests(unittest.TestCase):
    def test_frozen_callout_cells_hold_the_printed_text(self) -> None:
        for lang, (label, callout) in PRINTED_AC_OUTPUT.items():
            with self.subTest(lang=lang):
                self.assertEqual(label, _overview_cell(AC_OUTPUT_LABEL, lang))
                self.assertEqual(callout, _overview_cell(AC_OUTPUT_SPEC, lang))

    def test_ac_output_callout_has_no_current_and_no_peak(self) -> None:
        for lang in LANGUAGES:
            callout = _overview_cell(AC_OUTPUT_SPEC, lang)
            with self.subTest(lang=lang):
                self.assertIsNone(TEN_AMPS.search(callout), callout)
                self.assertNotIn("4400", callout)
                self.assertRegex(callout, r"^230 (V~ 50 Hz|В~ 50 Гц), 2200 (W|Вт) ")
                # The peak stays in the Total Output callout, as printed.
                self.assertIn("4400", _overview_cell(TOTAL_OUTPUT_SPEC, lang))

    def test_each_manifest_binds_the_printed_callout(self) -> None:
        for lang, (label, callout) in PRINTED_AC_OUTPUT.items():
            entry = _front_view_entry(lang)
            front, total = [binding["text"] for binding in entry["covered_annotations"]]
            with self.subTest(lang=lang):
                self.assertEqual(PRINT_PAGES[lang], entry["source_page"])
                self.assertEqual(callout, _after_label(front, label))
                self.assertIsNone(TEN_AMPS.search(_after_label(front, label)))
                self.assertTrue(total.endswith(_overview_cell(TOTAL_OUTPUT_SPEC, lang)), total)


def _build_web_page(tmp: Path, lang: str) -> str:
    staging = tmp / "staging"
    fake_bin = tmp / "bin"
    fake_bin.mkdir(parents=True)
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
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "build.py"),
            "md",
            "--config", str(ROOT / "configs" / f"config.eu-{lang}.yaml"),
            "--model", "JE-2000F",
            "--region", "EU",
            "--lang", lang,
            "--data-root", str(DATA_ROOT),
            "--staging-root", str(staging),
        ],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise AssertionError(
            f"JE-2000F/{lang} formal-source Web build failed:\n" + result.stdout + result.stderr
        )
    package = staging / "docs" / "_build" / "JE-2000F" / "EU" / lang / "md"
    return (package / "manual_bundle.html").read_text(encoding="utf-8")


class Je2000fEuOverviewAltRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.pages = {
            lang: BeautifulSoup(_build_web_page(Path(cls._tmp.name) / lang, lang), "html.parser")
            for lang in LANGUAGES
        }

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _finished(self, lang: str, name: str):
        (image,) = self.pages[lang].select(f'img[data-web-finished-panel-path$="/{name}"]')
        return image

    def test_front_view_alt_says_what_the_print_says(self) -> None:
        for lang, (label, callout) in PRINTED_AC_OUTPUT.items():
            front, total = self._finished(lang, "overview_front.png")["alt"].split("；")
            with self.subTest(lang=lang):
                self.assertEqual(callout, _after_label(front, label))
                self.assertTrue(total.endswith(_overview_cell(TOTAL_OUTPUT_SPEC, lang)), total)

    def test_no_figure_text_repeats_a_value_the_spec_table_corrected(self) -> None:
        """No alt or aria-label repeats 6000 cycles, a 10 A AC/bypass output or the US inlet."""
        for lang in LANGUAGES:
            soup = self.pages[lang]
            with self.subTest(lang=lang):
                labels = [
                    str(node[attribute])
                    for attribute in ("alt", "aria-label")
                    for node in soup.find_all(attrs={attribute: True})
                ]
                self.assertEqual([], [text for text in labels if "6000" in text])
                self.assertEqual([], [text for text in labels if US_AC_RATING.search(text)])
                # The print gives 10 A to the DC 12 V port (front view) and the
                # AC input (right side view) only.
                front = self._finished(lang, "overview_front.png")["alt"]
                self.assertEqual(
                    ["⎓"], [front[match.start() - 1] for match in TEN_AMPS.finditer(front)]
                )
                side = self._finished(lang, "overview_side.png")["alt"]
                ac_input = _overview_cell(AC_INPUT_SPEC, lang)
                self.assertIn(ac_input, side)
                self.assertEqual(1, len(TEN_AMPS.findall(side)))
                self.assertEqual(1, len(TEN_AMPS.findall(ac_input)))
                others = [
                    str(image.get("alt", ""))
                    for image in soup.find_all("img")
                    if not str(image.get("data-web-finished-panel-path", "")).endswith(
                        ("/overview_front.png", "/overview_side.png")
                    )
                ]
                self.assertEqual([], [text for text in others if TEN_AMPS.search(text)])


if __name__ == "__main__":
    unittest.main()
