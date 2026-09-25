from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.build_paths import resolve_web_illustration_manifest
from tools.manual_ir import read_manual_ir


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/config.eu-en.yaml"
FORMAL_SOURCE = ROOT / "manual_sources/JE-3600A/EU/en/2026-05-25"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
APP_RECIPE = ROOT / "data/asset_recipes/manual_je3600a_eu_web_app.json"
APP_PANEL = "assets/je3600a_eu_shared/app_connect_result.png"
LANGUAGES = ("en", "fr", "es")
# The control-panel button names each language block of the print uses (PDF
# pages 38/55/72/89). Without them the fr/es routes fell back to the English
# source names in the App page.
CONTROL_LABELS = {
    "main_power_button": {
        "fr": "Bouton d'alimentation principal",
        "es": "Botón de encendido principal",
        "de": "POWER-Taste",
        "it": "Pulsante di accensione principale",
    },
    "dc_usb_power_button": {
        "fr": "Bouton d'alimentation USB",
        "es": "Botón de energía USB",
        "de": "USB-Stromtaste",
        "it": "Pulsante Alimentazione USB",
    },
    "ac_power_button": {
        "fr": "Bouton d'alimentation CA",
        "es": "Botón de energía CA",
        "de": "AC-Ausgangstaste",
        "it": "Pulsante AC",
    },
}


def _build_web_package(tmp: Path, *, lang: str) -> Path:
    staging = tmp / "staging"
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
    result = subprocess.run(
        [
            sys.executable, str(ROOT / "build.py"), "md",
            "--config", str(ROOT / f"configs/config.eu-{lang}.yaml"), "--model", "JE-3600A",
            "--region", "EU", "--lang", lang,
            "--data-root", str(FORMAL_DATA_ROOT),
            "--staging-root", str(staging),
        ],
        cwd=ROOT, env=env, check=False, capture_output=True, text=True,
    )
    if result.returncode:
        raise AssertionError(f"JE-3600A/{lang} Web build failed:\n" + result.stdout + result.stderr)
    return staging / f"docs/_build/JE-3600A/EU/{lang}/md"


class Je3600aEuEnWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        staging = Path(cls._tmp.name) / "staging"
        fake_bin = Path(cls._tmp.name) / "bin"
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
        result = subprocess.run(
            [
                sys.executable, str(ROOT / "build.py"), "md",
                "--config", str(CONFIG), "--model", "JE-3600A",
                "--region", "EU", "--lang", "en",
                "--data-root", str(FORMAL_DATA_ROOT),
                "--staging-root", str(staging),
            ],
            cwd=ROOT, env=env, check=False, capture_output=True, text=True,
        )
        if result.returncode:
            raise AssertionError("JE-3600A Web build failed:\n" + result.stdout + result.stderr)
        cls.package = staging / "docs/_build/JE-3600A/EU/en/md"
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.html, "html.parser")
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_published_target_facts_and_rows(self) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        values = {(row["Row_key"], row["Slot_key"]): row["Value_source"] for row in rows}
        self.assertEqual("JE-3600A", values[("model_no", "")])
        self.assertEqual("80 Ah / 44.8 V DC (3584 Wh)", values[("capacity", "")])
        self.assertEqual("6000 cycles to 70%+ capacity", values[("cycle_life", "")])
        self.assertEqual("10 ms", values[("ups_transfer_time", "value")])

        with (FORMAL_DATA_ROOT / "lcd_icons_blocks.csv").open(encoding="utf-8", newline="") as handle:
            lcd = list(csv.DictReader(handle))
        self.assertEqual(21, len(lcd))
        self.assertEqual("Wi-Fi", lcd[0]["icon_en"])
        self.assertEqual("Remaining Discharge Time", lcd[-1]["icon_en"])

        with (FORMAL_DATA_ROOT / "troubleshooting_blocks.csv").open(encoding="utf-8", newline="") as handle:
            codes = [row["error_code"] for row in csv.DictReader(handle)]
        self.assertEqual(["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "FA", "FC"], codes)

    def test_control_labels_follow_each_print_block(self) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = {
                row["Row_key"]: row
                for row in csv.DictReader(handle)
                if row["Row_key"] in CONTROL_LABELS and row["Slot_key"] == "label"
            }
        self.assertEqual(sorted(CONTROL_LABELS), sorted(rows))
        for row_key, labels in CONTROL_LABELS.items():
            for lang, label in labels.items():
                self.assertEqual(label, rows[row_key][f"Value_{lang}"], (row_key, lang))

    def test_source_manifest_locks_frozen_inputs(self) -> None:
        manifest = json.loads((FORMAL_SOURCE / "source_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("formal-published-source-audited-git-input", manifest["source_role"])
        self.assertEqual("bfbcc4377fb474952f5e0850818289449016c8df11b1df48aff192b646eedf6d", manifest["authority"]["published_pdf_sha256"])
        self.assertFalse(manifest["live_bitable_dependency"])
        for binding in ("asset_recipe", "app_asset_recipe", "web_illustration_manifest"):
            item = manifest[binding]
            self.assertEqual(item["sha256"], hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest())
        for item in manifest["files"]:
            data = (FORMAL_SOURCE / item["path"]).read_bytes()
            self.assertEqual(item["size"], len(data))
            self.assertEqual(item["sha256"], hashlib.sha256(data).hexdigest())

    def test_web_output_is_complete_and_target_clean(self) -> None:
        self.assertEqual(21, len(self.soup.select("table.lcd-text-only tbody tr")))
        self.assertEqual(12, len(self.soup.select(".hb-troubleshooting-table tbody tr")))
        self.assertEqual(1, len(self.soup.select("#lcd-screen table")))
        self.assertEqual(17, len(self.soup.select(".manual-finished-illustration")))
        self.assertIn("Jackery Battery Pack 3600 User Manual", self.html)
        self.assertIn("3600 W rated, 7200 W surge peak", self.html)
        for stale in ("Battery Pack 2000", "DC 12V/USB OUTPUT", "LED LIGHT ON/OFF", "AC1/2", "Emergency Charging Mode"):
            self.assertNotIn(stale, self.html)
        coverage = self.ir.metadata["web_figure_coverage"]["summary"]
        self.assertEqual(10, coverage["total"])
        self.assertEqual(10, coverage["by_status"]["finished-panel"])
        self.assertEqual(0, coverage["by_status"]["missing"])
        self.assertEqual(18, len(self.ir.pages))

    def test_app_connect_result_is_the_shared_print_panel(self) -> None:
        panel = self.soup.select_one('img.manual-finished-illustration[data-reference-id="app-connect-result"]')
        self.assertIsNotNone(panel)
        self.assertEqual(APP_PANEL, panel["data-web-finished-panel-path"])
        self.assertEqual([], [image["src"] for image in self.soup.find_all("img")
                              if str(image.get("src", "")).endswith("/connect_result.png")])
        self.assertIn("The screenshots are for reference only.", self.html)

    def test_published_routes_bind_the_one_shared_app_connect_panel(self) -> None:
        """The print's language blocks place the same App bitmaps."""
        self.assertEqual("6e666959bf1a0579d0116df50ff8235b95c8d3c67af159c8cfca8e6bc2ca113c",
                         hashlib.sha256(APP_RECIPE.read_bytes()).hexdigest())
        assets = json.loads(APP_RECIPE.read_text(encoding="utf-8"))["assets"]
        self.assertEqual(4, len(assets))
        (asset,) = [item for item in assets if item["asset_key"] == "web/je3600a/eu/shared/app_connect_result"]
        (output,) = asset["outputs"]
        # App screenshots stay quarantined in their recipe (the App/QR/URL/
        # localized-UI gate); the illustration manifests are their only route
        # onto the page.
        self.assertFalse(asset["build_eligible"])
        self.assertTrue(asset["visual_review_required"])
        self.assertEqual("quarantine", asset["gate"]["status"])
        self.assertIn("app-ui", asset["risk_tags"])
        self.assertEqual(12, output["scale"])
        self.assertEqual(list(LANGUAGES), asset["scope"]["locales"])
        for lang in LANGUAGES:
            path = resolve_web_illustration_manifest(
                ROOT / f"configs/config.eu-{lang}.yaml", repo_root=ROOT, model="JE-3600A", region="EU",
            )
            self.assertEqual(ROOT / f"docs/renderers/web/je3600a_eu_{lang}_illustrations.json", path, lang)
            manifest = json.loads(path.read_text(encoding="utf-8"))
            bound = [item for item in manifest["illustrations"] if "connect_result.png" in item["replaces"]]
            self.assertEqual(1, len(bound), lang)
            (item,) = bound
            self.assertEqual(APP_PANEL, item["path"], lang)
            self.assertEqual(output["path"], (path.parent / item["path"]).relative_to(ROOT).as_posix(), lang)
            self.assertEqual(output["expected_sha256"], item["sha256"], lang)
            self.assertEqual(item["sha256"], hashlib.sha256((path.parent / item["path"]).read_bytes()).hexdigest(), lang)
            self.assertEqual(asset["page"], item["source_page"], lang)
            self.assertEqual(asset["transforms"][0]["bbox_pt"], item["bbox_pt"], lang)
            self.assertEqual(APP_RECIPE.relative_to(ROOT).as_posix(), item["recipe"], lang)
            self.assertTrue(item["consume_before_presentation"], lang)
            self.assertEqual("app-connect-result", item["reference_id"], lang)


    def test_published_routes_bind_their_own_add_device_panel(self) -> None:
        """Each block prints the App screens with this model's control panel."""
        order = ("main_power_button", "dc_usb_power_button", "ac_power_button")
        assets = {item["asset_key"]: item for item in json.loads(APP_RECIPE.read_text(encoding="utf-8"))["assets"]}
        for lang in LANGUAGES:
            asset = assets[f"web/je3600a/eu/{lang}/app_add_device_panel"]
            (output,) = asset["outputs"]
            self.assertEqual("quarantine", asset["gate"]["status"], lang)
            self.assertEqual([lang], asset["scope"]["locales"], lang)
            self.assertEqual(12, output["scale"], lang)
            path = ROOT / f"docs/renderers/web/je3600a_eu_{lang}_illustrations.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            (item,) = [entry for entry in manifest["illustrations"] if entry["replaces"] == ["add_device.png"]]
            panel = path.parent / item["path"]
            self.assertEqual(output["path"], panel.relative_to(ROOT).as_posix(), lang)
            self.assertEqual(output["expected_sha256"], item["sha256"], lang)
            self.assertEqual(item["sha256"], hashlib.sha256(panel.read_bytes()).hexdigest(), lang)
            self.assertEqual(asset["page"], item["source_page"], lang)
            self.assertEqual(asset["transforms"][0]["bbox_pt"], item["bbox_pt"], lang)
            self.assertEqual(APP_RECIPE.relative_to(ROOT).as_posix(), item["recipe"], lang)
            if lang == "en":
                # The English page has no button-label lines to cover.
                self.assertNotIn("covered_annotations", item)
                continue
            self.assertTrue(item["consume_before_presentation"], lang)
            self.assertEqual("app-add-device", item["reference_id"], lang)
            text = " ".join(CONTROL_LABELS[row][lang] for row in order)
            self.assertEqual([{"selector": ".line-block", "text": text}], item["covered_annotations"], lang)


class Je3600aEuSpanishAppPanelTests(unittest.TestCase):
    """The Spanish route shows the print's App screens, not the JP screenshot."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        package = _build_web_package(Path(cls._tmp.name), lang="es")
        cls.html = (package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_app_connect_result_is_the_shared_print_panel(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        panel = soup.select_one('img.manual-finished-illustration[data-reference-id="app-connect-result"]')
        self.assertIsNotNone(panel)
        self.assertEqual(APP_PANEL, panel["data-web-finished-panel-path"])
        self.assertEqual([], [image["src"] for image in soup.find_all("img")
                              if str(image.get("src", "")).endswith("/connect_result.png")])
        self.assertIn("Las capturas de pantalla anteriores sirven solo de referencia.", self.html)

    def test_add_device_is_the_spanish_print_panel(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        panel = soup.select_one('img.manual-finished-illustration[data-reference-id="app-add-device"]')
        self.assertIsNotNone(panel)
        self.assertEqual("assets/je3600a_eu_es/app_add_device_panel.png", panel["data-web-finished-panel-path"])
        # The print's control panel carries the button names, so the page's
        # label lines move into the figure's alt text.
        self.assertEqual(
            " ".join(CONTROL_LABELS[row]["es"] for row in ("main_power_button", "dc_usb_power_button", "ac_power_button")),
            panel["alt"],
        )
        self.assertEqual([], soup.select(".hb-app-add-device-live-label"))
        self.assertIsNone(soup.select_one("figure.hb-app-add-device-composition"))
        self.assertIn("Presione una vez el botón de encendido principal del dispositivo", self.html)
        self.assertNotIn("el power button", self.html)


TRANSLATED_LOCALES = ("fr", "es")
FIGURES = re.compile(r"\d+(?:[.,]\d+)?")
UNCLEAN = re.compile("[\x00-\x08\x0b-\x1fﬀ-ﬆ]")


def frozen_rows(name: str) -> list[dict[str, str]]:
    with (FORMAL_DATA_ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Je3600aEuTranslatedCellTests(unittest.TestCase):
    """The fr/es LCD, fault, specification, storage and note cells follow each print block."""

    def test_translated_cells_are_complete_and_clean(self) -> None:
        # 西/法列曾整列为空，渲染静默回落英文（约 70 段）；逐格要求有值、干净，规格值与英文同数字
        cells = [(f"lcd {row['No.']}", row[f"{column}_{lang}"])
                 for row in frozen_rows("lcd_icons_blocks.csv")
                 for column in ("icon", "icon_desc") for lang in TRANSLATED_LOCALES]
        cells += [(f"fault {row['error_code']}", row[f"corrective_measures_{lang}"])
                  for row in frozen_rows("troubleshooting_blocks.csv") for lang in TRANSLATED_LOCALES]
        cells += [(f"note {row['Note_id']}", row[f"Text_{lang}"])
                  for row in frozen_rows("Spec_Notes.csv") for lang in TRANSLATED_LOCALES]
        cells += [(f"footnote {row['Footnote_id']}", row[f"Text_{lang}"])
                  for row in frozen_rows("Spec_Footnotes.csv") for lang in TRANSLATED_LOCALES]
        self.assertEqual(21 * 4 + 12 * 2 + 1 * 2 + 2 * 2, len(cells))
        for where, text in cells:
            with self.subTest(where=where):
                self.assertTrue(text.strip())
                self.assertNotRegex(text, UNCLEAN)
        spec = [row for row in frozen_rows("Spec_Master.csv") if row["Page"] in ("specifications", "storage")]
        self.assertEqual(24, len(spec))
        for row in spec:
            source = row["Value_source"]
            for lang in TRANSLATED_LOCALES:
                value = row[f"Value_{lang}"]
                with self.subTest(row=row["spec_row_key"], lang=lang):
                    if row["Row_key"] != "cell_chemistry":
                        self.assertEqual(FIGURES.findall(source.replace(",", ".")),
                                         FIGURES.findall(value.replace(",", ".")))
                    self.assertEqual(source.count("⎓"), value.count("⎓"))
                    self.assertEqual(value.count("("), value.count(")"))
                    self.assertNotRegex(value, UNCLEAN)
                    label_or_param = row[f"Row_label_{lang}" if row["Page"] == "specifications" else f"Param_{lang}"]
                    self.assertTrue(label_or_param)

    def test_cells_follow_each_print_block(self) -> None:
        lcd = {row["No."]: row for row in frozen_rows("lcd_icons_blocks.csv")}
        # 结构跟英文行：第 4 项合并两模式并删去 Off 句，第 19 项压成一行；第 18 项保留印刷的两句
        self.assertTrue(lcd["4"]["icon_desc_fr"].startswith("Mode d’Économie de Batterie : Limite la capacité"))
        self.assertNotIn("Éteint", lcd["4"]["icon_desc_fr"])
        self.assertNotIn("Apagado", lcd["4"]["icon_desc_es"])
        self.assertNotIn("\n", lcd["19"]["icon_desc_es"])
        self.assertEqual(1, lcd["18"]["icon_desc_fr"].count("\n"))
        self.assertIn("significativamente", lcd["3"]["icon_desc_es"])
        faults = {row["error_code"]: row for row in frozen_rows("troubleshooting_blocks.csv")}
        self.assertIn("Vérifiez si les entrées et sorties d'air", faults["F6"]["corrective_measures_fr"])
        self.assertIn("20 cm a ambos lados", faults["F6"]["corrective_measures_es"])
        spec = {}
        for row in frozen_rows("Spec_Master.csv"):
            spec.setdefault((row["Page"], row["Row_key"]), []).append(row)
        expected = {
            (("specifications", "ac_total_output"), 0, "Value_fr"): "3600 W nominal, 7200 W crête",
            (("specifications", "charging_temperature"), 0, "Row_label_es"): "Temperatura de carga",
            (("specifications", "model_no"), 0, "Row_label_es"): "Nº de modelo",
            (("specifications", "model_no"), 0, "Value_fr"): "JE-3600A",
            (("specifications", "capacity"), 0, "Value_fr"): "80 Ah / 44,8 V CC (3584 Wh)",
            (("specifications", "ac_input"), 1, "Param_fr"): "Mode dérivation",
            (("specifications", "dc8020_ports"), 1, "Value_es"): "16-60 V⎓12 A, Doble a 24 A máx./1000 W máx.",
            (("storage", "storage_temperature"), 0, "Param_es"): "1 mes",
            (("operation_guide", "default_standby_duration"), 0, "Value_fr"): "2 heures",
        }
        for (key, index, column), value in expected.items():
            with self.subTest(key=key, index=index, column=column):
                self.assertEqual(value, spec[key][index][column])
        note = frozen_rows("Spec_Notes.csv")[0]
        self.assertEqual("※ USB Type-C® et USB-C® sont des marques déposées de USB Implementers Forum.", note["Text_fr"])


if __name__ == "__main__":
    unittest.main()
