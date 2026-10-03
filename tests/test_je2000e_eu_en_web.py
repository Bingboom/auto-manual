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
from tools.web.document_ir import render_document_fragments


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "config.eu-en.yaml"
FORMAL_SOURCE = ROOT / "manual_sources" / "JE-2000E" / "EU" / "en" / "2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"


def storage_labels(data_root: Path) -> dict[str, tuple[str, str]]:
    """Line order -> (Param_es, Param_de) of the storage temperature rows."""
    with (data_root / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
        return {row["Line_order"]: (row["Param_es"], row["Param_de"])
                for row in csv.DictReader(handle) if row["Row_key"] == "storage_temperature"}


# Each print block's storage durations; the es and de cells were once swapped.
STORAGE_LABELS = {"1": ("1 mes", "1 Monat"), "2": ("3 meses", "3 Monate"), "3": ("12 meses", "12 Monate")}
ILLUSTRATIONS = ROOT / "docs" / "renderers" / "web" / "je2000e_eu_en_illustrations.json"
APP_RECIPE = ROOT / "data" / "asset_recipes" / "manual_je2000e_eu_web_app.json"
SINGLE_LANGUAGES = ("fr", "es", "de", "it", "uk")
WEB_RECIPE = ROOT / "data" / "asset_recipes" / "manual_je2000e_eu_web.json"
# PDF pages of each language block of the V2.0 print. Each route crops its own
# block: the English block draws UK sockets, the fr-uk blocks EU sockets.
BLOCK_PAGES = {
    "fr": range(25, 44), "es": range(44, 63), "de": range(63, 82), "it": range(82, 101), "uk": range(101, 120),
}
BLOCK_CROPS = (
    "inbox_main", "inbox_cable", "inbox_manual", "overview_front", "overview_side", "lcd_map",
    "operation_power", "operation_ac", "operation_dc", "operation_energy", "operation_led",
    "operation_lcd", "ups", "extra_battery", "battery_pack_kit", "charging_ac", "charging_solar", "charging_car",
)
# These blocks print the battery-pack clearance label as "≥ 0,66 pies (200 mm)",
# the Spanish art reused with an imperial value. Their figure is the French
# block's copy of the same art, which reads "≥ 200 mm" (operator, 2026-09-26).
FRENCH_BATTERY_ART = ("es", "de", "it", "uk")
INBOX_SLOTS = {"inbox_main": "main_unit1.png", "inbox_cable": "ac_charging_cable.png", "inbox_manual": "manual_icon1.png"}
# The shared art the fr-uk routes (and the English in-box cards) showed before
# 2026-09-26: figures from the JE-1000F/US master (another product, US outlets).
SHARED_ART = (
    "in_the_box/main_unit1", "in_the_box/ac_charging_cable", "in_the_box/manual_icon1",
    "overview/front_product", "overview/right_side_ports", "lcd/lcd_map", "operation/main_power",
    "operation/ac_output", "operation/dc_usb_output", "operation/energy_saving", "operation/led_light",
    "operation/lcd_mode", "operation/ups_mode", "charging/ac_wall", "charging/solar_direct",
    "charging/solar_adapter", "charging/car_charge",
)


def shared_art_digests() -> set[str]:
    with (ROOT / "data" / "asset_registry.csv").open(encoding="utf-8", newline="") as handle:
        rows = {row["asset_key"]: row for row in csv.DictReader(handle)}
    digests = set()
    for key in SHARED_ART:
        found = re.findall(r"[0-9a-f]{64}", rows[key]["内容哈希"])
        assert found, key
        digests.update(found)
    return digests


def page_image_digests(html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    return {match.group(1) for image in soup.find_all("img")
            if (match := re.search(r"assets/ir/([0-9a-f]{64})/", str(image.get("src", ""))))}
# replaced source image -> reference id
APP_REFERENCES = {
    "add_device.png": "app-add-device",
    "connect_result.png": "app-connect-result",
}
# Routes whose add-device figure is their own print block's App screens plus
# its control-panel box. The box prints the button labels, so the page's four
# label lines become covered annotations (the figure's alt text). The uk block
# prints "AC1" for the AC2 button; its crop re-sets that one character from the
# print's own glyphs (see UK_LABEL_CORRECTION).
PANEL_LANGUAGES = ("en", "fr", "es", "de", "it", "uk")
COVERED_LABELS = {
    "en": "Main POWER Button AC1 Power Button AC2 Power Button DC / USB Power Button",
    "fr": "Bouton POWER principal Bouton CC / USB Bouton CA1 Bouton CA2",
    "es": "Botón POWER principal Botón CC / USB Botón CA1 Botón CA2",
    "de": "POWER-Taste AC1-Einschalttaste AC2-Einschalttaste DC / USB-Einschalttaste",
    "it": "Pulsante POWER principale Pulsante CA1 Pulsante CA2 Pulsante CC / USB",
    "uk": "Головна кнопка POWER Кнопка AC1 Кнопка AC2 Кнопка DC / USB",
}
# The uk crop's two corrective transforms on PDF page 118: remove the wrong "1"
# of the lower AC label (text only), then paint the "2" of the page's own "2.1"
# caption (same font, size and colour as the labels) where the "2" belongs.
UK_LABEL_CORRECTION = [
    {"op": "redact_text_region", "bbox_pt": [324.75, 400.3, 326.5, 406.8],
     "images": "preserve", "graphics": "preserve", "fill": None},
    {"op": "copy_pdf_region", "bbox_pt": [324.54, 399.94, 327.69, 407.14],
     "other_bbox_pt": [128.64, 344.21, 131.79, 351.41]},
]
# Button labels as every page of each print block names them (the German block
# never prints "Haupt-POWER-Taste", the Italian block's DC/USB button is "CC/USB",
# the Ukrainian block's DC/USB button carries no "POWER").
PRINT_BUTTON_LABELS = {
    ("main_power_button", "Value_de"): "POWER-Taste",
    ("dc_usb_power_button", "Value_it"): "Pulsante CC / USB",
    ("dc_usb_power_button", "Value_uk"): "Кнопка DC / USB",
}


def _expected_app_panel(lang: str, replaced: str) -> str:
    """The App recipe output that a route's App figure must bind."""
    if replaced == "add_device.png" and lang in PANEL_LANGUAGES:
        return f"docs/renderers/web/assets/je2000e_eu_{lang}/app_add_device_panel.png"
    return f"docs/renderers/web/assets/je2000e_eu_shared/app_{Path(replaced).stem}.png"


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
            "--config",
            str(config),
            "--model",
            "JE-2000E",
            "--region",
            "EU",
            "--lang",
            lang,
            "--data-root",
            str(FORMAL_DATA_ROOT),
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
            f"JE-2000E/{lang} formal-source Web build failed:\n" + result.stdout + result.stderr
        )
    return staging / "docs" / "_build" / "JE-2000E" / "EU" / lang / "md"


class Je2000eEuStorageLabelTests(unittest.TestCase):
    def test_storage_durations_follow_each_print_block(self) -> None:
        """es printed German '1 monat…' and de Spanish '1 mes…' until 2026-09-26."""
        self.assertEqual(STORAGE_LABELS, storage_labels(FORMAL_DATA_ROOT))


class Je2000eEuButtonLabelTests(unittest.TestCase):
    """The page names each button as its print block does, so text and figures agree."""

    def test_frozen_button_labels_follow_the_print(self) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = {row["Row_key"]: row for row in csv.DictReader(handle) if row["Section"] == "CONTROLS"}
        for (row_key, column), label in PRINT_BUTTON_LABELS.items():
            self.assertEqual(label, rows[row_key][column], (row_key, column))

    def test_model_templates_use_the_print_button_names(self) -> None:
        templates = ROOT / "docs" / "templates"
        german = (templates / "page_eu-de" / "05_operation_guide_je2000e.rst").read_text(encoding="utf-8")
        self.assertNotIn("Haupt-POWER-Taste", german)
        self.assertIn("   * - POWER-Taste + AC1-Einschalttaste", german)
        italian = (templates / "page_eu-it" / "05_operation_guide_je2000e.rst").read_text(encoding="utf-8")
        self.assertNotIn("Pulsante DC/USB", italian)
        self.assertEqual(2, italian.count("Pulsante CC/USB"))
        ukrainian = (templates / "page_shared" / "uk" / "12_app_setup_je2000e.rst").read_text(encoding="utf-8")
        # Notes 4.1/4.2 name the AC1 button, as the print (p119) and the de/it/en pages do.
        self.assertEqual(2, ukrainian.count("кнопку DC / USB + кнопку AC1,"))
        self.assertNotIn("кнопку AC,", ukrainian)
        with (FORMAL_DATA_ROOT / "lcd_icons_blocks.csv").open(encoding="utf-8", newline="") as handle:
            (energy,) = [row for row in csv.DictReader(handle) if row["icon_en"] == "Energy Saving Mode"]
        self.assertIn("premendo il pulsante CA o CC/USB:", energy["icon_desc_it"])

    def test_uk_panel_corrects_only_the_misprinted_label(self) -> None:
        """uk prints "Кнопка AC1" for the AC2 button; the crop re-sets that one character."""
        assets = {asset["asset_key"]: asset for asset in json.loads(APP_RECIPE.read_text(encoding="utf-8"))["assets"]}
        uk = assets["web/je2000e/eu/uk/app_add_device_panel"]
        italian = assets["web/je2000e/eu/it/app_add_device_panel"]
        self.assertEqual(118, uk["page"])
        # The same region as the es/de/it blocks, which lay the page out identically.
        self.assertEqual(italian["transforms"][0], uk["transforms"][0])
        self.assertEqual(UK_LABEL_CORRECTION, uk["transforms"][1:])
        # The App gate keeps every App crop quarantined in its recipe; the operator
        # accepted the corrected label (2026-09-27), so its registry row is finished
        # like the other five panels.
        self.assertEqual("quarantine", uk["gate"]["status"])
        with (ROOT / "data" / "asset_registry.csv").open(encoding="utf-8", newline="") as handle:
            statuses = {row["asset_key"]: row["状态"] for row in csv.DictReader(handle)}
        for lang in PANEL_LANGUAGES:
            self.assertEqual("✅成品", statuses[f"web/je2000e/eu/{lang}/app_add_device_panel"], lang)
        # No route binds the shared add-device screens any more.
        shared = "assets/je2000e_eu_shared/app_add_device.png"
        for lang in ("en", *SINGLE_LANGUAGES):
            manifest = json.loads((ILLUSTRATIONS.parent / f"je2000e_eu_{lang}_illustrations.json").read_text(encoding="utf-8"))
            self.assertNotIn(shared, [entry["path"] for entry in manifest["illustrations"]], lang)


class Je2000eEuEnWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.staging = Path(cls._tmp.name) / "staging"
        # This suite validates the upstream HTML/IR package, not Pandoc syntax.
        # Real Pandoc + Sphinx conversion is checked in target acceptance.
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
                "--config",
                str(CONFIG),
                "--model",
                "JE-2000E",
                "--region",
                "EU",
                "--lang",
                "en",
                "--data-root",
                str(FORMAL_DATA_ROOT),
                "--staging-root",
                str(cls.staging),
            ],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise AssertionError(
                "JE-2000E formal-source Web build failed:\n"
                + result.stdout
                + result.stderr
            )
        cls.package = cls.staging / "docs" / "_build" / "JE-2000E" / "EU" / "en" / "md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_frozen_source_matches_current_paper_manual(self) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        values = {
            (row["Row_key"], row["Slot_key"], row["Line_order"]): row["Value_source"]
            for row in rows
            if row["document_key"] == "JE-2000E_EU"
        }
        self.assertEqual("About 19.1 kg", values[("weight", "", "1")])
        self.assertEqual("10 ms", values[("ups_transfer_time", "value", "1")])
        self.assertEqual("16 V-60 V", values[("pv_input_range", "value", "1")])
        self.assertEqual("DC8020", values[("dc_input_connector", "value", "1")])
        self.assertEqual(
            "36.8 V-57.6 V⎓75 A max.",
            values[("dc_expansion_input", "", "1")],
        )
        self.assertEqual(
            "36.8 V-57.6 V⎓55 A max.",
            values[("dc_expansion_output", "", "1")],
        )

    def test_specification_ports_match_released_pdf(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        rows = [
            (cell.get_text(" ", strip=True),
             cell.parent.select_one("td").get_text(" ", strip=True))
            for cell in soup.select("th.hb-spec-label")
        ]
        output_start = next(i for i, (label, _) in enumerate(rows)
                            if label == "3 × AC Output")
        outputs = rows[output_start:output_start + 7]
        self.assertEqual(
            [label.rstrip("① ") for label, _ in outputs],
            ["3 × AC Output", "AC Output in Bypass Mode", "1 × USB-A Output",
             "1 × USB-C 30W Output", "1 × USB-C 140W Output",
             "1 × DC 12V Port", "1 × DC Expansion Port"],
        )
        self.assertEqual("230 V~ 50 Hz, 10 A max.", outputs[1][1])
        self.assertTrue(outputs[3][1].startswith("30 W max."))
        self.assertTrue(outputs[4][1].startswith("140 W max."))
        inputs = dict(rows[:output_start])
        self.assertEqual(
            "PV: 16 V-60 V⎓12 A, Double to 21 A / 800 W max. "
            "Car: 11 V-16 V⎓8 A max., Double to 8 A max.",
            inputs["2 × DC8020 Ports"],
        )
        self.assertEqual(2, inputs["1 × AC Input"].count(
            "220 V-240 V~ 50 Hz, 10 A max."))

    def test_source_manifest_locks_every_frozen_input(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(manifest["live_bitable_dependency"])
        self.assertEqual("V2.0-2026-08-03", manifest["authority"]["published_revision"])
        self.assertEqual(
            "734f89ad824d2436d2c79c7ac1231d2dc111dd83ef43e8ee6326674124c396d0",
            manifest["authority"]["published_pdf_sha256"],
        )
        for binding in ("asset_recipe", "app_asset_recipe", "web_illustration_manifest"):
            bound = manifest[binding]
            self.assertEqual(
                bound["sha256"],
                hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest(),
            )
        for record in manifest["files"]:
            data = (FORMAL_SOURCE / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())

    def test_web_output_is_target_isolated_and_complete(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(18, len(self.ir.pages))
        self.assertEqual(20, len(soup.select(".manual-finished-illustration")))
        # The shared LCD component must retain its original approved artwork's
        # provenance instead of silently losing it during semantic conversion.
        lcd_art = soup.select_one(".hb-lcd-mode-composition img.manual-finished-illustration")
        self.assertEqual("assets/je2000e_eu_en/operation_lcd.png", lcd_art["data-web-finished-panel-path"])
        self.assertEqual(hashlib.sha256((ROOT / "docs/renderers/web" / lcd_art["data-web-finished-panel-path"]).read_bytes()).hexdigest(),
                         lcd_art["data-web-finished-panel-sha256"])
        kit = soup.select_one('img[data-web-finished-panel-path="assets/je2000e_eu_en/battery_pack_kit.png"]')
        self.assertEqual("Jackery Battery Pack 2000, Expansion Cable, User Manual (sold separately)", kit["alt"])
        self.assertEqual([], [table for table in soup.find_all("table") if "Expansion Cable" in table.get_text()])
        # The in-box cards show the English block's crops (UK sockets), not the shared art.
        self.assertEqual(
            [f"assets/je2000e_eu_en/{name}.png" for name in INBOX_SLOTS],
            [card.select_one("img")["data-web-finished-panel-path"] for card in soup.select(".hb-inbox-card")],
        )
        self.assertEqual(set(), page_image_digests(self.html) & shared_art_digests())
        coverage = self.ir.metadata["web_figure_coverage"]
        self.assertEqual(13, coverage["summary"]["total"])
        self.assertEqual(0, coverage["summary"]["by_status"]["missing"])
        self.assertEqual(12, coverage["summary"]["by_status"]["finished-panel"])
        self.assertEqual(1, coverage["summary"]["by_status"]["editable-fallback"])
        self.assertEqual(3, len(soup.select(".hb-inbox-card")))
        self.assertIsNotNone(soup.select_one("figure.hb-lcd-mode-composition"))
        self.assertIsNotNone(soup.select_one("table.hb-lcd-mode-table"))
        for expected in (
            "Jackery Explorer 2000 Plus",
            "About 19.1 kg",
            "6000 cycles to 70%+ capacity",
            "2400 W rated total, 4800 W surge peak",
            "within 10 ms",
            "36.8 V-57.6 V⎓75 A max.",
            "36.8 V-57.6 V⎓55 A max.",
            "support up to 5 battery packs",
            "AC1 Power Button",
            "AC2 Power Button",
            "2011/65/EU",
        ):
            self.assertIn(expected, self.html)
        for forbidden in (
            "JE-2000F",
            "About 18.8 kg",
            "2200 W rated",
            "4000 cycles to 70%+ capacity",
            "|UPS_TRANSFER_TIME|",
            "|PV_INPUT_RANGE|",
            "|DC_INPUT_CONNECTOR|",
        ):
            self.assertNotIn(forbidden, self.html)

    def test_illustrations_are_hash_locked_and_use_source_crops(self) -> None:
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        recipe = json.loads((ROOT / manifest["recipe"]).read_text(encoding="utf-8"))
        self.assertEqual(20, len([asset for asset in recipe["assets"] if asset["scope"]["locales"] == ["en"]]))
        self.assertEqual(20 + len(BLOCK_CROPS) * len(SINGLE_LANGUAGES), len(recipe["assets"]))
        self.assertEqual(20, len(manifest["illustrations"]))
        for asset in recipe["assets"]:
            self.assertEqual([12], [output["scale"] for output in asset["outputs"]])
            if asset["asset_key"] == "web/je2000e/eu/en/connect_result":
                # App screens stay quarantined under the App/QR/URL/localized-UI
                # gate; the manifest is their only route onto the page.
                self.assertFalse(asset["build_eligible"])
                self.assertTrue(asset["visual_review_required"])
                self.assertEqual("quarantine", asset["gate"]["status"])
                self.assertIn("app-ui", asset["risk_tags"])
                continue
            self.assertTrue(asset["build_eligible"])
            self.assertFalse(asset["visual_review_required"])
            self.assertEqual("approved", asset["gate"]["status"])
        output_hashes: dict[str, dict[str, str]] = {}
        for illustration in manifest["illustrations"]:
            recipe_path = illustration.get("recipe", manifest["recipe"])
            if recipe_path not in output_hashes:
                bound = json.loads((ROOT / recipe_path).read_text(encoding="utf-8"))
                output_hashes[recipe_path] = {
                    output["path"]: output["expected_sha256"]
                    for asset in bound["assets"]
                    for output in asset["outputs"]
                }
            path = ILLUSTRATIONS.parent / illustration["path"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(illustration["sha256"], digest)
            self.assertEqual(
                digest,
                output_hashes[recipe_path][path.relative_to(ROOT).as_posix()],
            )
        # Only the add-device figure comes from the quarantined App recipe. The
        # approved crop it replaced held the control-panel box without the screens.
        self.assertEqual(
            ["add_device.png"],
            [
                item["replaces"][0]
                for item in manifest["illustrations"]
                if item.get("recipe") == APP_RECIPE.relative_to(ROOT).as_posix()
            ],
        )
        self.assertNotIn(
            "assets/je2000e_eu_en/control_panel.png",
            [item["path"] for item in manifest["illustrations"]],
        )

    def test_routes_bind_their_app_panels(self) -> None:
        """Each route binds its own block's add-device panel."""
        self.assertEqual(
            "9fc7acdaed25c3a219379f657d8b4166de599d779dc60af9fcad0bcfbf346cf3",
            hashlib.sha256(APP_RECIPE.read_bytes()).hexdigest(),
        )
        app_recipe = json.loads(APP_RECIPE.read_text(encoding="utf-8"))
        # Six per-language panels, the shared connect-result screens, and the
        # shared add-device screens that no route binds any more (uk's fallback).
        self.assertEqual(8, len(app_recipe["assets"]))
        assets = {}
        for asset in app_recipe["assets"]:
            # App screenshots stay quarantined in their recipe (the App/QR/URL/
            # localized-UI gate); the illustration manifests are their only
            # route onto the page.
            self.assertFalse(asset["build_eligible"])
            self.assertTrue(asset["visual_review_required"])
            self.assertEqual("quarantine", asset["gate"]["status"])
            self.assertIn("app-ui", asset["risk_tags"])
            (output,) = asset["outputs"]
            self.assertEqual(12, output["scale"])
            assets[output["path"]] = asset
        app_recipe_path = APP_RECIPE.relative_to(ROOT).as_posix()
        for lang in ("en", *SINGLE_LANGUAGES):
            path = resolve_web_illustration_manifest(
                ROOT / "configs" / f"config.eu-{lang}.yaml",
                repo_root=ROOT,
                model="JE-2000E",
                region="EU",
            )
            self.assertEqual(
                ILLUSTRATIONS.parent / f"je2000e_eu_{lang}_illustrations.json", path, lang
            )
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(lang, manifest["language"])
            app_items = [
                item for item in manifest["illustrations"] if item.get("recipe") == app_recipe_path
            ]
            # English keeps its own approved connect-result panel.
            expected = ["add_device.png"] if lang == "en" else sorted(APP_REFERENCES)
            self.assertEqual(expected, sorted(item["replaces"][0] for item in app_items), lang)
            for item in app_items:
                replaced = item["replaces"][0]
                panel = path.parent / item["path"]
                self.assertEqual(
                    _expected_app_panel(lang, replaced), panel.relative_to(ROOT).as_posix(), lang
                )
                asset = assets[_expected_app_panel(lang, replaced)]
                self.assertIn(lang, asset["scope"]["locales"], lang)
                self.assertEqual(asset["outputs"][0]["expected_sha256"], item["sha256"], lang)
                self.assertEqual(
                    item["sha256"], hashlib.sha256(panel.read_bytes()).hexdigest(), lang
                )
                self.assertEqual(asset["page"], item["source_page"], lang)
                self.assertEqual(asset["transforms"][0]["bbox_pt"], item["bbox_pt"], lang)
                self.assertTrue(item["consume_before_presentation"], lang)
                self.assertEqual(APP_REFERENCES[replaced], item["reference_id"], lang)
                covered = [binding["text"] for binding in item.get("covered_annotations", [])]
                if replaced == "add_device.png" and lang in PANEL_LANGUAGES:
                    self.assertEqual([COVERED_LABELS[lang]], covered, lang)
                else:
                    self.assertEqual([], covered, lang)

    def test_public_ir_replay_and_tamper_detection(self) -> None:
        fragments = render_document_fragments(self.ir, package_root=self.package)
        self.assertEqual(18, len(fragments))
        with tempfile.TemporaryDirectory() as td:
            copied = Path(td) / "package"
            shutil.copytree(self.package, copied)
            ir = read_manual_ir(copied / "manual.ir.json")
            relative = next(iter(ir.metadata["asset_sha256"]))
            (copied / relative).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "asset missing or changed"):
                render_document_fragments(ir, package_root=copied)



class Je2000eEuGermanAppPanelTests(unittest.TestCase):
    """The German route shows its print block's figures, App screens and control panel."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        package = _build_web_package(
            Path(cls._tmp.name), config=ROOT / "configs" / "config.eu-de.yaml", lang="de"
        )
        cls.html = (package / "manual_bundle.html").read_text(encoding="utf-8")
        cls.markdown = (package / "manual_je2000e_eu_de.md").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_app_figures_are_the_print_panels(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        expected = {
            "app-add-device": "assets/je2000e_eu_de/app_add_device_panel.png",
            "app-connect-result": "assets/je2000e_eu_shared/app_connect_result.png",
        }
        for reference_id, panel in expected.items():
            image = soup.select_one(
                f'img.manual-finished-illustration[data-reference-id="{reference_id}"]'
            )
            self.assertIsNotNone(image, reference_id)
            self.assertEqual(panel, image["data-web-finished-panel-path"])
        self.assertEqual(
            [],
            [
                image["src"]
                for image in soup.find_all("img")
                if Path(str(image.get("src", ""))).name in APP_REFERENCES
            ],
        )
        # The German block's control-panel box prints the button labels, so the
        # page's label lines move into the figure's alt text. The reference
        # sentence is translated per language and stays live text.
        add_device = soup.select_one('img[data-reference-id="app-add-device"]')
        self.assertEqual(COVERED_LABELS["de"], add_device["alt"])
        self.assertEqual(
            [],
            [
                node
                for node in soup.select(".line-block")
                if " ".join(node.get_text(" ", strip=True).split()) == COVERED_LABELS["de"]
            ],
        )
        self.assertIn("Die oben gezeigten Screenshots dienen nur als Referenz.", self.html)

    def test_page_names_the_main_button_as_the_print_does(self) -> None:
        """The German block's figures and text all say "POWER-Taste", so the page does too."""
        self.assertNotIn("Haupt-POWER-Taste", self.html)
        self.assertIn("Drücken Sie die POWER-Taste am Gerät", self.html)

    def test_every_figure_is_the_german_print_block(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        paths = [image["data-web-finished-panel-path"] for image in soup.select("img.manual-finished-illustration")]
        self.assertEqual(20, len(paths))
        # The LCD-mode crop retains its provenance inside the shared component.
        self.assertEqual(
            sorted(f"assets/je2000e_eu_de/{name}.png" for name in BLOCK_CROPS),
            sorted(path for path in paths if "/app_" not in path),
        )
        self.assertEqual(set(), page_image_digests(self.html) & shared_art_digests())
        # The battery-pack section showed the in-box unit as a placeholder.
        battery = soup.select_one('img[data-web-finished-panel-path="assets/je2000e_eu_de/extra_battery.png"]')
        self.assertIn("BATTERIEPACK", battery.find_parent("section").select_one("h1, h2").get_text().upper())
        # Copy printed in a crop moves into its alt text, as on English.
        front = soup.select_one('img[data-web-finished-panel-path="assets/je2000e_eu_de/overview_front.png"]')
        self.assertEqual([], front.find_parent("section").select(":scope > table"))
        car = soup.select_one('img[data-web-finished-panel-path="assets/je2000e_eu_de/charging_car.png"]')
        self.assertEqual("Fahrzeug *Das Autoladekabel ist separat erhältlich.", car["alt"])
        # The German block prints "≥ 0,66 pies (200 mm)"; the page shows the French block's copy.
        french = next(entry for entry in json.loads((ROOT / "docs/renderers/web/je2000e_eu_fr_illustrations.json")
                                                    .read_text(encoding="utf-8"))["illustrations"]
                      if entry["path"].endswith("/extra_battery.png"))
        self.assertEqual(french["sha256"], battery["data-web-finished-panel-sha256"])
        kit = soup.select_one('img[data-web-finished-panel-path="assets/je2000e_eu_de/battery_pack_kit.png"]')
        self.assertEqual("Jackery Battery Pack 2000, Verlängerungskabel, Benutzerhandbuch (separat erhältlich)", kit["alt"])
        self.assertEqual([], [table for table in soup.find_all("table") if "Verlängerungskabel" in table.get_text()])

    def test_callout_label_columns_share_the_page_width_reference(self) -> None:
        """Each label cell carries the page's labels, so all label columns share one width."""
        soup = BeautifulSoup(self.markdown, "html.parser")
        cells = soup.select("table.manual-callout-table td.manual-callout-label")
        self.assertGreater(len(cells), 3)
        references = {
            tuple(span.get_text() for span in cell.select("span.manual-callout-label-sizer")) for cell in cells
        }
        self.assertEqual({("WARNUNG", "VORSICHT", "HINWEIS")}, references)

    def test_operation_page_uses_the_english_compositions(self) -> None:
        """The model-specific operation page gets the LCD-mode, auto-resume and key-combination components."""
        soup = BeautifulSoup(self.html, "html.parser")
        lcd = soup.select_one('figure.hb-lcd-mode-composition[data-component-id="HB-TABLE-LCD-MODE"]')
        self.assertIsNotNone(lcd)
        german = next(entry for entry in json.loads((ROOT / "docs/renderers/web/je2000e_eu_de_illustrations.json")
                                                    .read_text(encoding="utf-8"))["illustrations"]
                      if entry["path"].endswith("/operation_lcd.png"))
        self.assertIn(german["sha256"], lcd.select_one("img")["src"])
        self.assertEqual(6, len(lcd.select("tr")))
        self.assertIsNotNone(soup.select_one(".hb-auto-resume-composition"))
        self.assertIsNotNone(soup.select_one(".hb-key-combination-composition"))


class Je2000eEuBlockIllustrationTests(unittest.TestCase):
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
                ROOT / "configs" / f"config.eu-{lang}.yaml", repo_root=ROOT, model="JE-2000E", region="EU",
            )
            cls.manifests[lang] = (path, json.loads(path.read_text(encoding="utf-8")))

    def entries(self, lang: str) -> dict[str, dict]:
        _, manifest = self.manifests[lang]
        return {Path(entry["path"]).stem: entry for entry in manifest["illustrations"]
                if entry["path"].startswith(f"assets/je2000e_eu_{lang}/") and "/app_" not in entry["path"]}

    def test_english_binds_its_in_box_crops(self) -> None:
        for name, replaced in INBOX_SLOTS.items():
            entry = self.english[name]
            (output,) = self.assets[f"web/je2000e/eu/en/{name}"]["outputs"]
            self.assertEqual([replaced], entry["replaces"])
            self.assertEqual(output["expected_sha256"], entry["sha256"])
            self.assertEqual(7, entry["source_page"])

    def test_each_route_binds_its_own_block_crops(self) -> None:
        for lang in SINGLE_LANGUAGES:
            path, manifest = self.manifests[lang]
            self.assertEqual(WEB_RECIPE.relative_to(ROOT).as_posix(), manifest["recipe"], lang)
            entries = self.entries(lang)
            self.assertEqual(sorted(BLOCK_CROPS), sorted(entries), lang)
            for name, entry in entries.items():
                asset = self.assets[f"web/je2000e/eu/{lang}/{name}"]
                (output,) = asset["outputs"]
                with self.subTest(lang=lang, name=name):
                    self.assertEqual(self.english[name]["replaces"], entry["replaces"])
                    self.assertEqual("approved", asset["gate"]["status"])
                    self.assertEqual([lang], asset["scope"]["locales"])
                    if lang in FRENCH_BATTERY_ART and name == "extra_battery":
                        french = self.assets["web/je2000e/eu/fr/extra_battery"]
                        self.assertEqual(french["page"], asset["page"])
                        self.assertEqual(french["transforms"], asset["transforms"])
                        self.assertEqual(french["outputs"][0]["expected_sha256"], output["expected_sha256"])
                    else:
                        self.assertIn(asset["page"], BLOCK_PAGES[lang])
                    self.assertEqual(asset["page"], entry["source_page"])
                    self.assertEqual(asset["transforms"][0]["bbox_pt"], entry["bbox_pt"])
                    file = path.parent / entry["path"]
                    self.assertEqual(output["path"], file.relative_to(ROOT).as_posix())
                    self.assertEqual(output["expected_sha256"], entry["sha256"])
                    self.assertEqual(entry["sha256"], hashlib.sha256(file.read_bytes()).hexdigest())

    def test_printed_copy_leaves_the_page_where_english_does(self) -> None:
        for lang in SINGLE_LANGUAGES:
            for name, entry in self.entries(lang).items():
                with self.subTest(lang=lang, name=name):
                    self.assertEqual(
                        bool(self.english[name].get("covered_annotations")), bool(entry.get("covered_annotations"))
                    )
                    self.assertNotIn("consume_before_presentation", entry)

    def test_battery_pack_section_uses_the_block_crop(self) -> None:
        # The fr-uk templates showed the in-box unit here; English already used its crop.
        for lang in ("en", *SINGLE_LANGUAGES):
            template = (ROOT / "docs" / "templates" / "page_shared" / lang / "charging.rst").read_text(encoding="utf-8")
            block = template.split("\n.. only::", 1)[0]
            self.assertIn(f".. image:: renderers/web/assets/je2000e_eu_{lang}/extra_battery.png", block, lang)
            self.assertNotIn("asset:in_the_box/main_unit1", block, lang)
        # pt-BR has no JE-2000E route; its copy of the block shows the English figure.
        template = (ROOT / "docs/templates/page_shared/pt-BR/charging.rst").read_text(encoding="utf-8")
        block = template.split("\n.. only::", 1)[0]
        self.assertIn(".. image:: renderers/web/assets/je2000e_eu_en/extra_battery.png", block)
        self.assertNotIn("asset:in_the_box/main_unit1", block)

    def test_package_kit_replaces_the_label_table(self) -> None:
        """The print shows the kit as a dashed box of pictures; the label-only table rendered an empty header row."""
        us_table = "   .. only:: region_us\n\n      .. list-table::\n         :header-rows: 0\n         :widths: 34 33 33\n"
        for lang in ("en", *SINGLE_LANGUAGES):
            template = (ROOT / "docs" / "templates" / "page_shared" / lang / "charging.rst").read_text(encoding="utf-8")
            block = template.split("\n.. only::", 1)[0]
            with self.subTest(lang=lang):
                self.assertEqual(1, block.count(f".. image:: renderers/web/assets/je2000e_eu_{lang}/battery_pack_kit.png"))
                # English, French and Spanish keep their US variant of the label table.
                self.assertEqual(1 if lang in ("en", "fr", "es") else 0, block.count(":widths: 34 33 33"))
                self.assertEqual(1 if lang in ("en", "fr", "es") else 0, block.count(us_table))


if __name__ == "__main__":
    unittest.main()
