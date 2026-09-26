from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.build_paths import resolve_web_illustration_manifest
from tools.manual_ir import read_manual_ir
from tools.web_document_ir import render_document_fragments


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/config.eu-en.yaml"
FORMAL_SOURCE = ROOT / "manual_sources/JE-3000C/EU/en/2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"
ILLUSTRATIONS = ROOT / "docs/renderers/web/je3000c_eu_en_illustrations.json"
WEB_CSS = ROOT / "docs/renderers/contracts/web_manual.css"
APP_RECIPE = ROOT / "data/asset_recipes/manual_je3000c_eu_web_app.json"
SINGLE_LANGUAGES = ("fr", "es", "de", "it", "uk")
WEB_RECIPE = ROOT / "data/asset_recipes/manual_je3000c_eu_web.json"
# PDF pages of each language block of the V2.0 print; each route crops its own block
# (the English block draws UK sockets, the others EU sockets).
BLOCK_PAGES = {"fr": range(22, 38), "es": range(38, 54), "de": range(54, 70), "it": range(70, 86), "uk": range(86, 102)}
BLOCK_CROPS = (
    "inbox_unit", "inbox_cable", "inbox_manual", "overview_front", "overview_side", "lcd_map",
    "operation_power", "operation_ac", "operation_dc", "operation_energy", "operation_lcd",
    "ups", "charging_ac", "charging_solar", "charging_car",
)
# The shared art the fr-uk routes showed before 2026-09-25: JE-1000F figures from the
# JE-1000F/US master (another product, US outlets).
SHARED_ART = (
    "in_the_box/main_unit1", "in_the_box/ac_charging_cable", "in_the_box/manual_icon1",
    "in_the_box/main_unit", "overview/front_product", "overview/right_side_ports", "lcd/lcd_map",
    "operation/main_power", "operation/dc_usb_output", "operation/ac_output", "operation/energy_saving",
    "operation/lcd_mode", "operation/ups_mode", "charging/ac_wall", "charging/solar_direct",
    "charging/solar_adapter", "charging/car_charge",
)
# Print defects in the callout labels (de "DC-12V-Ausgangstaste" and a French label,
# fr "Oiture:"): these figures keep the page's corrected callout table (operator ruling).
KEEP_CALLOUT_TABLE = {("de", "overview_front"), ("fr", "overview_side")}
# The it/uk blocks print this panel's caption in English; the line is redacted.
ENGLISH_CAPTION = {"it", "uk"}


def shared_art_digests() -> set[str]:
    with (ROOT / "data/asset_registry.csv").open(encoding="utf-8", newline="") as handle:
        rows = {row["asset_key"]: row for row in csv.DictReader(handle)}
    digests = set()
    for key in SHARED_ART:
        found = re.findall(r"[0-9a-f]{64}", rows[key]["内容哈希"])
        assert found, key
        digests.update(found)
    return digests
# The control-panel button names each language block of the V2.0 print uses
# (PDF pages 36/52/68/84/100). Without them the fr-uk routes fell back to the
# English source names in the Product Overview, energy-saving and App pages.
CONTROL_LABELS = {
    "main_power_button": {
        "fr": "Bouton d'alimentation principal",
        "es": "Botón de encendido principal",
        "de": "POWER-Taste",
        "it": "Pulsante di accensione principale",
        "uk": "Кнопка POWER",
    },
    "dc_usb_power_button": {
        "fr": "Bouton d'alimentation CC/USB",
        "es": "Botón de energía CC/USB",
        "de": "DC/USB-Stromtaste",
        "it": "Pulsante Alimentazione DC/USB",
        "uk": "Кнопка живлення DC/USB",
    },
    "ac_power_button": {
        "fr": "Bouton d'alimentation CA",
        "es": "Botón de energía CA",
        "de": "AC-Ausgangstaste",
        "it": "Pulsante AC",
        "uk": "Кнопка живлення AC",
    },
}


def _build_web_package(tmp: Path, *, config: Path, lang: str) -> Path:
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
            sys.executable,
            str(ROOT / "build.py"),
            "md",
            "--config", str(config),
            "--model", "JE-3000C",
            "--region", "EU",
            "--lang", lang,
            "--data-root", str(FORMAL_DATA_ROOT),
            "--staging-root", str(staging),
        ],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise AssertionError(f"JE-3000C/{lang} formal-source Web build failed:\n" + result.stdout + result.stderr)
    return staging / f"docs/_build/JE-3000C/EU/{lang}/md"


class Je3000cEuEnWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.staging = Path(cls._tmp.name) / "staging"
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
                sys.executable,
                str(ROOT / "build.py"),
                "md",
                "--config", str(CONFIG),
                "--model", "JE-3000C",
                "--region", "EU",
                "--lang", "en",
                "--data-root", str(FORMAL_DATA_ROOT),
                "--staging-root", str(cls.staging),
            ],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise AssertionError("JE-3000C formal-source Web build failed:\n" + result.stdout + result.stderr)
        cls.package = cls.staging / "docs/_build/JE-3000C/EU/en/md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_frozen_source_matches_current_pdf_facts(self) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = [row for row in csv.DictReader(handle) if row["document_key"] == "JE-3000C_EU"]
        values = {(row["Page"], row["Row_key"], row["Slot_key"], row["Line_order"]): row["Value_source"] for row in rows}
        self.assertEqual("3072 Wh (60 Ah / 51.2 V DC)", values[("specifications", "capacity", "", "1")])
        self.assertEqual("230 V~ 50 Hz, 15.6 A, 3600 W rated", values[("specifications", "ac_output", "", "1")])
        self.assertEqual("3600 W Rated, 7200 W Surge Peak", values[("specifications", "total_ac_output", "", "1")])
        self.assertEqual("10 ms", values[("ups_mode", "ups_transfer_time", "value", "1")])
        self.assertEqual("16V-60V", values[("charging_methods", "pv_input_range", "value", "1")])
        self.assertEqual("DC8020", values[("charging_methods", "dc_input_connector", "value", "1")])
        self.assertEqual("-20°C to 45°C (0-60 % RH)", values[("storage", "storage_temperature", "", "1")])

        with (FORMAL_DATA_ROOT / "lcd_icons_blocks.csv").open(encoding="utf-8", newline="") as handle:
            lcd = [(row["No."], row["icon_en"]) for row in csv.DictReader(handle)]
        self.assertEqual(("4", "Battery Saving Mode"), lcd[3])
        self.assertEqual(("23", "Output Voltage and Frequency"), lcd[-3])
        self.assertEqual(("25", "Remaining Discharge Time"), lcd[-1])
        with (FORMAL_DATA_ROOT / "troubleshooting_blocks.csv").open(encoding="utf-8", newline="") as handle:
            self.assertEqual(["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "FE"], [row["error_code"] for row in csv.DictReader(handle)])

    def test_source_manifest_locks_every_frozen_input(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(manifest["live_bitable_dependency"])
        self.assertEqual("V2.0-2026-07-31", manifest["authority"]["published_revision"])
        self.assertEqual("55fee5a2f7538e58ebce17fc2bcfe3b0e4a8959233251961f6122ef7f420602d", manifest["authority"]["published_pdf_sha256"])
        for binding in ("asset_recipe", "app_asset_recipe", "web_illustration_manifest"):
            bound = manifest[binding]
            self.assertEqual(bound["sha256"], hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest())
        for record in manifest["files"]:
            data = (FORMAL_SOURCE / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())

    def test_pv_maximum_qualifier_matches_released_pdf(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        label = next(cell for cell in soup.select("th.hb-spec-label")
                     if cell.get_text(strip=True) == "2 × DC8020 Ports")
        value = label.parent.select_one("td").get_text(" ", strip=True)
        self.assertIn("PV: 16 V-60 V⎓12 A max., Double to 24 A / 1000 W max.", value)
        self.assertNotIn("24 A max.", value)

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

    def test_inventory_digest_matches_canonical_file_records(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        inventory = json.dumps(manifest["files"], ensure_ascii=False,
                               sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(manifest["files_inventory_sha256"], hashlib.sha256(inventory).hexdigest())

    def test_web_output_uses_semantic_tables_and_current_target_only(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(17, len(self.ir.pages))
        self.assertEqual(17, len(soup.select(".manual-finished-illustration")))
        coverage = self.ir.metadata["web_figure_coverage"]["summary"]
        self.assertEqual(10, coverage["total"])
        self.assertEqual(0, coverage["by_status"]["missing"])
        self.assertEqual(9, coverage["by_status"]["finished-panel"])
        self.assertEqual(1, coverage["by_status"]["editable-fallback"])
        lcd = soup.select_one("figure.hb-lcd-mode-composition")
        self.assertIsNotNone(lcd)
        self.assertIsNotNone(lcd.select_one(".hb-lcd-mode-art-panel img"))
        self.assertIsNotNone(lcd.select_one("table.hb-lcd-mode-table"))
        resume = soup.select_one("figure.hb-auto-resume-composition")
        self.assertIsNotNone(resume)
        self.assertIsNotNone(resume.select_one("table.hb-auto-resume-table"))
        keys = soup.select_one("figure.hb-key-combination-composition")
        self.assertIsNotNone(keys)
        key_table = keys.select_one("table.hb-key-combination-table")
        self.assertIsNotNone(key_table)
        self.assertEqual(
            ["hb-key-col-buttons", "hb-key-col-operation", "hb-key-col-function"],
            [column.get("class", [""])[0] for column in key_table.select("col")],
        )
        self.assertEqual(3, len(key_table.select("tbody > tr")))
        self.assertEqual([], soup.select("#front-view > table"))
        self.assertEqual([], soup.select("#right-side-view > table"))
        text = soup.get_text(" ", strip=True)
        for expected in ("Jackery Explorer 3000", "3072 Wh", "3600 W Rated, 7200 W Surge Peak", "within 10 ms", "AC and DC Output Resume Function", "2011/65/EU"):
            self.assertIn(expected, text)
        for forbidden in ("JE-2000F", "2000 Plus", "AC1/2", "LED LIGHT ON/OFF", "Emergency Charging Mode", "|UPS_TRANSFER_TIME|", "|PV_INPUT_RANGE|", "|DC_INPUT_CONNECTOR|"):
            self.assertNotIn(forbidden, self.html)

    def test_illustration_recipe_and_files_are_approved_and_hash_locked(self) -> None:
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        recipe = json.loads((ROOT / manifest["recipe"]).read_text(encoding="utf-8"))
        self.assertEqual(18, len([asset for asset in recipe["assets"] if asset["scope"]["locales"] == ["en"]]))
        self.assertEqual(18 + len(BLOCK_CROPS) * len(SINGLE_LANGUAGES), len(recipe["assets"]))
        self.assertEqual(18, len(manifest["illustrations"]))
        outputs = {}
        app_panels = {"setup_download", "setup_add_device", "setup_connect_result"}
        for asset in recipe["assets"]:
            self.assertEqual([12], [output["scale"] for output in asset["outputs"]])
            for output in asset["outputs"]:
                outputs[output["path"]] = output["expected_sha256"]
            if asset["asset_key"].rsplit("/", 1)[-1] in app_panels:
                # App screens and the QR download panel stay quarantined under the
                # App/QR/URL/localized-UI gate; the manifest is their only route.
                self.assertFalse(asset["build_eligible"])
                self.assertTrue(asset["visual_review_required"])
                self.assertEqual("quarantine", asset["gate"]["status"])
                self.assertIn("app-ui", asset["risk_tags"])
                continue
            self.assertTrue(asset["build_eligible"])
            self.assertFalse(asset["visual_review_required"])
            self.assertEqual("approved", asset["gate"]["status"])
        for illustration in manifest["illustrations"]:
            path = ILLUSTRATIONS.parent / illustration["path"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(illustration["sha256"], digest)
            self.assertEqual(outputs[path.relative_to(ROOT).as_posix()], digest)

        side = next(
            illustration
            for illustration in manifest["illustrations"]
            if illustration["path"].endswith("overview_side.png")
        )
        self.assertEqual([27, 323, 342, 426], side["bbox_pt"])
        side_recipe = next(
            asset
            for asset in recipe["assets"]
            if asset["asset_key"] == "web/je3000c/eu/en/overview_side"
        )
        self.assertEqual(side["bbox_pt"], side_recipe["transforms"][0]["bbox_pt"])

        power = next(
            illustration
            for illustration in manifest["illustrations"]
            if illustration["path"].endswith("operation_power.png")
        )
        self.assertEqual([27, 70, 343, 241], power["bbox_pt"])
        power_recipe = next(
            asset
            for asset in recipe["assets"]
            if asset["asset_key"] == "web/je3000c/eu/en/operation_power"
        )
        self.assertEqual(power["bbox_pt"], power_recipe["transforms"][0]["bbox_pt"])

        dc = next(
            illustration
            for illustration in manifest["illustrations"]
            if illustration["path"].endswith("operation_dc.png")
        )
        dc_recipe = next(
            asset
            for asset in recipe["assets"]
            if asset["asset_key"] == "web/je3000c/eu/en/operation_dc"
        )
        self.assertEqual(dc["bbox_pt"], dc_recipe["transforms"][0]["bbox_pt"])
        self.assertEqual(
            ["crop", "whiteout", "whiteout", "whiteout", "whiteout", "whiteout"],
            [transform["op"] for transform in dc_recipe["transforms"]],
        )

        charging_ac = next(
            illustration
            for illustration in manifest["illustrations"]
            if illustration["path"].endswith("charging_ac.png")
        )
        self.assertEqual([27, 222, 342, 361], charging_ac["bbox_pt"])
        charging_ac_recipe = next(
            asset
            for asset in recipe["assets"]
            if asset["asset_key"] == "web/je3000c/eu/en/charging_ac"
        )
        self.assertEqual(
            charging_ac["bbox_pt"],
            charging_ac_recipe["transforms"][0]["bbox_pt"],
        )

        connect_result = next(
            illustration
            for illustration in manifest["illustrations"]
            if illustration["path"].endswith("setup_connect_result.png")
        )
        self.assertEqual([40, 143, 332, 315], connect_result["bbox_pt"])
        connect_result_recipe = next(
            asset
            for asset in recipe["assets"]
            if asset["asset_key"] == "web/je3000c/eu/en/setup_connect_result"
        )
        self.assertEqual(
            connect_result["bbox_pt"],
            connect_result_recipe["transforms"][0]["bbox_pt"],
        )
        css = WEB_CSS.read_text(encoding="utf-8")
        self.assertIn(
            '#dc-12v-usb-output-on-off > img[data-web-finished-panel-path="assets/je3000c_eu_en/operation_dc.png"]',
            css,
        )

    def test_single_language_routes_bind_the_one_shared_app_connect_panel(self) -> None:
        """The fr/es/de/it/uk blocks of the print place the same five bitmaps."""
        self.assertEqual(
            "c1ed0192e86930a9f899cb4c975a160bb1816922385e7c05fdcd87b28f6ffc0b",
            hashlib.sha256(APP_RECIPE.read_bytes()).hexdigest(),
        )
        app_recipe = json.loads(APP_RECIPE.read_text(encoding="utf-8"))
        self.assertEqual(6, len(app_recipe["assets"]))
        (asset,) = [
            item
            for item in app_recipe["assets"]
            if item["asset_key"] == "web/je3000c/eu/shared/app_connect_result"
        ]
        (output,) = asset["outputs"]
        # App screenshots stay quarantined in their recipe (the App/QR/URL/
        # localized-UI gate); the illustration manifests are their only
        # route onto the page. English keeps its own approved panel.
        self.assertFalse(asset["build_eligible"])
        self.assertTrue(asset["visual_review_required"])
        self.assertEqual("quarantine", asset["gate"]["status"])
        self.assertIn("app-ui", asset["risk_tags"])
        self.assertEqual(12, output["scale"])
        self.assertEqual(list(SINGLE_LANGUAGES), asset["scope"]["locales"])
        for lang in SINGLE_LANGUAGES:
            path = resolve_web_illustration_manifest(
                ROOT / f"configs/config.eu-{lang}.yaml",
                repo_root=ROOT,
                model="JE-3000C",
                region="EU",
            )
            self.assertEqual(ILLUSTRATIONS.parent / f"je3000c_eu_{lang}_illustrations.json", path, lang)
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(lang, manifest["language"])
            # The two App panels plus this block's own figure crops.
            self.assertEqual(2 + len(BLOCK_CROPS), len(manifest["illustrations"]), lang)
            (item,) = [
                entry for entry in manifest["illustrations"] if entry["replaces"] == ["connect_result.png"]
            ]
            panel = path.parent / item["path"]
            self.assertEqual(output["path"], panel.relative_to(ROOT).as_posix(), lang)
            self.assertEqual(output["expected_sha256"], item["sha256"], lang)
            self.assertEqual(item["sha256"], hashlib.sha256(panel.read_bytes()).hexdigest(), lang)
            self.assertEqual(asset["page"], item["source_page"], lang)
            self.assertEqual(asset["transforms"][0]["bbox_pt"], item["bbox_pt"], lang)
            self.assertEqual(APP_RECIPE.relative_to(ROOT).as_posix(), item["recipe"], lang)
            self.assertTrue(item["consume_before_presentation"], lang)
            self.assertEqual("app-connect-result", item["reference_id"], lang)

    def test_single_language_routes_bind_their_own_add_device_panel(self) -> None:
        """Each block prints the App screens with this model's control panel."""
        order = {
            "fr": ("main_power_button", "dc_usb_power_button", "ac_power_button"),
            "es": ("main_power_button", "dc_usb_power_button", "ac_power_button"),
            "de": ("main_power_button", "ac_power_button", "dc_usb_power_button"),
            "it": ("main_power_button", "ac_power_button", "dc_usb_power_button"),
            "uk": ("main_power_button", "ac_power_button", "dc_usb_power_button"),
        }
        assets = {
            item["asset_key"]: item
            for item in json.loads(APP_RECIPE.read_text(encoding="utf-8"))["assets"]
        }
        for lang in SINGLE_LANGUAGES:
            asset = assets[f"web/je3000c/eu/{lang}/app_add_device_panel"]
            (output,) = asset["outputs"]
            self.assertEqual("quarantine", asset["gate"]["status"], lang)
            self.assertEqual([lang], asset["scope"]["locales"], lang)
            self.assertEqual(12, output["scale"], lang)
            path = ILLUSTRATIONS.parent / f"je3000c_eu_{lang}_illustrations.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            (item,) = [
                entry for entry in manifest["illustrations"] if entry["replaces"] == ["add_device.png"]
            ]
            panel = path.parent / item["path"]
            self.assertEqual(output["path"], panel.relative_to(ROOT).as_posix(), lang)
            self.assertEqual(output["expected_sha256"], item["sha256"], lang)
            self.assertEqual(item["sha256"], hashlib.sha256(panel.read_bytes()).hexdigest(), lang)
            self.assertEqual(asset["page"], item["source_page"], lang)
            self.assertEqual(asset["transforms"][0]["bbox_pt"], item["bbox_pt"], lang)
            self.assertEqual(APP_RECIPE.relative_to(ROOT).as_posix(), item["recipe"], lang)
            self.assertTrue(item["consume_before_presentation"], lang)
            self.assertEqual("app-add-device", item["reference_id"], lang)
            text = " ".join(CONTROL_LABELS[row][lang] for row in order[lang])
            self.assertEqual([{"selector": ".line-block", "text": text}], item["covered_annotations"], lang)

    def test_public_ir_cold_replay_and_tamper_detection(self) -> None:
        self.assertEqual(17, len(render_document_fragments(self.ir, package_root=self.package)))
        with tempfile.TemporaryDirectory() as td:
            copied = Path(td) / "package"
            shutil.copytree(self.package, copied)
            ir = read_manual_ir(copied / "manual.ir.json")
            relative = next(iter(ir.metadata["asset_sha256"]))
            (copied / relative).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "asset missing or changed"):
                render_document_fragments(ir, package_root=copied)



class Je3000cEuFrenchAppPanelTests(unittest.TestCase):
    """The French route shows the print's App screens, not the JP screenshot."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        package = _build_web_package(
            Path(cls._tmp.name), config=ROOT / "configs/config.eu-fr.yaml", lang="fr"
        )
        cls.html = (package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_app_connect_result_is_the_shared_print_panel(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        panel = soup.select_one(
            'img.manual-finished-illustration[data-reference-id="app-connect-result"]'
        )
        self.assertIsNotNone(panel)
        self.assertEqual(
            "assets/je3000c_eu_shared/app_connect_result.png",
            panel["data-web-finished-panel-path"],
        )
        self.assertEqual(
            [],
            [
                image["src"]
                for image in soup.find_all("img")
                if str(image.get("src", "")).endswith("/connect_result.png")
            ],
        )
        self.assertIn("Les captures d'écran ci-dessus sont fournies à titre indicatif.", self.html)

    def test_add_device_is_the_french_print_panel(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        panel = soup.select_one(
            'img.manual-finished-illustration[data-reference-id="app-add-device"]'
        )
        self.assertIsNotNone(panel)
        self.assertEqual(
            "assets/je3000c_eu_fr/app_add_device_panel.png",
            panel["data-web-finished-panel-path"],
        )
        # The print's control panel carries the button names, so the page's
        # label lines move into the figure's alt text.
        self.assertEqual(
            " ".join(
                CONTROL_LABELS[row]["fr"]
                for row in ("main_power_button", "dc_usb_power_button", "ac_power_button")
            ),
            panel["alt"],
        )
        self.assertEqual([], soup.select(".hb-app-add-device-live-label"))
        self.assertIsNone(soup.select_one("figure.hb-app-add-device-composition"))
        for english in ("POWER Button", "POWER button", "AC power button", "DC / USB power button"):
            self.assertNotIn(english, self.html)

    def test_every_figure_is_the_french_print_block(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        finished = soup.select("img.manual-finished-illustration")
        self.assertEqual(17, len(finished))
        paths = {image["data-web-finished-panel-path"] for image in finished}
        for name in BLOCK_CROPS:
            self.assertIn(f"assets/je3000c_eu_fr/{name}.png", paths)
        digests = {match.group(1) for image in soup.find_all("img")
                   if (match := re.search(r"assets/ir/([0-9a-f]{64})/", str(image.get("src", ""))))}
        self.assertEqual(set(), digests & shared_art_digests())

        def section(name):
            image = soup.select_one(f'img[data-web-finished-panel-path="assets/je3000c_eu_fr/{name}.png"]')
            return image, image.find_parent("section")

        # The front view prints its callouts; the side view keeps the corrected table
        # because its print reads "Oiture:".
        _, front = section("overview_front")
        self.assertEqual([], front.select(":scope > table"))
        _, side = section("overview_side")
        self.assertIn("Voiture :", side.select_one(":scope > table").get_text(" ", strip=True))
        car, _ = section("charging_car")
        self.assertEqual("Véhicule；※Le câble de chargement de voiture est vendu séparément.", car["alt"])

    def test_no_emergency_charging_block(self) -> None:
        # JE-3000C has no Emergency Charging Mode (capability FALSE, absent from the print);
        # the car panel's "usage d'urgence" caution is a different sentence and stays.
        self.assertNotIn("Mode de charge d'urgence", self.html)
        self.assertIn("usage d'urgence uniquement", self.html)


class Je3000cEuBlockIllustrationTests(unittest.TestCase):
    """Each fr-uk route shows its own print block's figures, not the JE-1000F shared art."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.recipe = json.loads(WEB_RECIPE.read_text(encoding="utf-8"))
        cls.assets = {asset["asset_key"]: asset for asset in cls.recipe["assets"]}
        cls.english = {
            Path(entry["path"]).stem: entry
            for entry in json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))["illustrations"]
        }
        cls.manifests = {}
        for lang in SINGLE_LANGUAGES:
            path = resolve_web_illustration_manifest(
                ROOT / f"configs/config.eu-{lang}.yaml", repo_root=ROOT, model="JE-3000C", region="EU",
            )
            cls.manifests[lang] = (path, json.loads(path.read_text(encoding="utf-8")))

    def entries(self, lang: str) -> dict[str, dict]:
        _, manifest = self.manifests[lang]
        return {Path(entry["path"]).stem: entry for entry in manifest["illustrations"]
                if entry["path"].startswith(f"assets/je3000c_eu_{lang}/") and "/app_" not in entry["path"]}

    def test_each_route_binds_its_own_block_crops(self) -> None:
        for lang in SINGLE_LANGUAGES:
            path, manifest = self.manifests[lang]
            self.assertEqual(WEB_RECIPE.relative_to(ROOT).as_posix(), manifest["recipe"], lang)
            entries = self.entries(lang)
            self.assertEqual(sorted(BLOCK_CROPS), sorted(entries), lang)
            for name, entry in entries.items():
                asset = self.assets[f"web/je3000c/eu/{lang}/{name}"]
                (output,) = asset["outputs"]
                with self.subTest(lang=lang, name=name):
                    self.assertEqual(self.english[name]["replaces"], entry["replaces"])
                    self.assertEqual("approved", asset["gate"]["status"])
                    self.assertEqual([lang], asset["scope"]["locales"])
                    self.assertIn(asset["page"], BLOCK_PAGES[lang])
                    self.assertEqual(asset["page"], entry["source_page"])
                    self.assertEqual(asset["transforms"][0]["bbox_pt"], entry["bbox_pt"])
                    file = path.parent / entry["path"]
                    self.assertEqual(output["path"], file.relative_to(ROOT).as_posix())
                    self.assertEqual(output["expected_sha256"], entry["sha256"])
                    self.assertEqual(entry["sha256"], hashlib.sha256(file.read_bytes()).hexdigest())

    def test_printed_copy_leaves_the_page_once_except_print_defects(self) -> None:
        english = {name: len(entry.get("covered_annotations", [])) > 0 for name, entry in self.english.items()}
        for lang in SINGLE_LANGUAGES:
            for name, entry in self.entries(lang).items():
                with self.subTest(lang=lang, name=name):
                    covered = entry.get("covered_annotations", [])
                    if (lang, name) in KEEP_CALLOUT_TABLE:
                        self.assertEqual([], covered)
                        continue
                    self.assertEqual(english[name], bool(covered))
                    if covered:
                        # Registered components claim these nodes; consume them first.
                        self.assertTrue(entry["consume_before_presentation"])
            energy = self.assets[f"web/je3000c/eu/{lang}/operation_energy"]
            redactions = [t for t in energy["transforms"] if t["op"] == "redact_text_region"]
            selectors = [item["selector"].split(" > ", 1)[1] for item in self.entries(lang)["operation_energy"]["covered_annotations"]]
            if lang in ENGLISH_CAPTION:
                self.assertEqual(1, len(redactions), lang)
                self.assertEqual(["table"], selectors, lang)
            else:
                self.assertEqual([], redactions, lang)
                self.assertEqual([".line-block", "table"], selectors, lang)

    def test_dc_panels_get_the_english_panel_border(self) -> None:
        css = WEB_CSS.read_text(encoding="utf-8")
        for lang in SINGLE_LANGUAGES:
            self.assertIn(f'#furo-main-content img[data-web-finished-panel-path="assets/je3000c_eu_{lang}/operation_dc.png"]', css)


FIGURES = re.compile(r"\d+(?:[.,]\d+)?")
UNCLEAN = re.compile("[\x00-\x08\x0b-\x1fﬀ-ﬆ]")
LOCALIZED_SETTINGS = ("default_standby_duration", "energy_saving_auto_off_duration")


def frozen_rows(name: str) -> list[dict[str, str]]:
    with (FORMAL_DATA_ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Je3000cEuTranslatedCellTests(unittest.TestCase):
    """fr–uk specification, storage, overview, setting and footnote cells follow each print block."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = frozen_rows("Spec_Master.csv")
        cls.cells = {(row["Page"], row["Row_key"], row["Slot_key"], row["Line_order"]): row for row in cls.rows}

    def test_translated_cells_are_complete_and_clean(self) -> None:
        # 法–乌列曾整列为空，页面静默回落英文：规格表、储存、概览标注、待机时长都印英文
        checked = [row for row in self.rows
                   if row["Page"] in ("specifications", "storage")
                   or (row["Page"] == "Product overview" and row["Section"] != "CONTROLS")
                   or row["Row_key"] in LOCALIZED_SETTINGS]
        self.assertEqual(19 + 3 + 15 + 2, len(checked))
        for row in checked:
            source = row["Value_source"]
            for lang in SINGLE_LANGUAGES:
                value = row[f"Value_{lang}"]
                with self.subTest(row=row["spec_row_key"], lang=lang):
                    self.assertTrue(value)
                    self.assertNotRegex(value, UNCLEAN)
                    self.assertEqual(value.count("("), value.count(")"))
                    exempt = row["Row_key"] == "cell_chemistry" or (lang, row["Row_key"]) == ("uk", "dimensions")
                    if not exempt and not row["Slot_key"].endswith("label"):
                        self.assertEqual(FIGURES.findall(source.replace(",", ".")),
                                         FIGURES.findall(value.replace(",", ".")))
                        self.assertEqual(source.count("⎓"), value.count("⎓"))
                    if row["Page"] == "specifications":
                        self.assertTrue(row[f"Row_label_{lang}"])
                    if row["Page"] == "storage":
                        self.assertTrue(row[f"Param_{lang}"])
        for footnote in frozen_rows("Spec_Footnotes.csv"):
            for lang in SINGLE_LANGUAGES:
                with self.subTest(footnote=footnote["Footnote_id"], lang=lang):
                    self.assertTrue(footnote[f"Text_{lang}"])

    def test_cells_follow_each_print_block(self) -> None:
        expected = {
            ("specifications", "dc8020_ports", "", "1", "Value_fr"): "Voiture : 12 V-16 V⎓8 A max., double à 8 A max.",
            ("specifications", "dc8020_ports", "", "1", "Value_de"): "Auto: 12-16 V⎓8 A max., Doppelanschluss 8 A max.",
            ("specifications", "dc8020_ports", "", "2", "Value_es"): "PV: 16-60 V⎓12 A, Doble a 24 A máx./1000 W máx.",
            ("specifications", "usb_a", "", "1", "Row_label_es"): "2 × Salida USB-A 18W MAX",
            ("specifications", "dc12_port", "", "1", "Row_label_de"): "1 × DC 12 V-Anschluss",
            ("specifications", "ac_input", "", "2", "Param_it"): "Modalità bypass",
            ("specifications", "charging_temperature", "", "1", "Row_label_uk"): "Температура заряджання",
            ("specifications", "dimensions", "", "1", "Value_uk"): "435 × 326 × 281 мм",
            ("Product overview", "ac_input", "side.label", "1", "Value_fr"): "Entrée CA",
            ("Product overview", "dc12_port", "front.label", "1", "Value_de"): "12-V-DC-Anschluss",
            ("Product overview", "total_output", "front.spec", "1", "Value_fr"): "3600 W nominal, 7200 W crête",
            ("operation_guide", "energy_saving_ac_threshold", "value", "1", "Value_uk"): "25 Вт",
            ("operation_guide", "default_standby_duration", "value", "1", "Value_fr"): "2 heures",
        }
        for (*key, column), value in expected.items():
            with self.subTest(key=key, column=column):
                self.assertEqual(value, self.cells[tuple(key)][column])
        total = {row["Footnote_id"]: row for row in frozen_rows("Spec_Footnotes.csv")}["ac_total"]
        self.assertEqual("Вказує, що два або більше вихідних портів змінного струму працюють разом.", total["Text_uk"])


if __name__ == "__main__":
    unittest.main()
