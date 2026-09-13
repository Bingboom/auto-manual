from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup
import yaml

from tools.config_loader import load_config_mapping
from tools.gen_index_bundle import plan_materialized_pages
from tools.manual_ir import read_manual_ir
from tools.skeleton_resolve import (
    emit_manifest_yaml,
    load_blueprint,
    load_product_plan,
    load_region_profile,
    load_slot_template_catalog,
    resolve_plan,
)
from tools.web_document_ir import render_document_fragments


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "config.eu-en.yaml"
FORMAL_SOURCE = ROOT / "manual_sources" / "JE-2000F" / "EU" / "en" / "2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"
ILLUSTRATIONS = (
    ROOT / "docs" / "renderers" / "web" / "je2000f_eu_en_illustrations.json"
)
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "main-intl"
REGION_PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "main-eu-en.yaml"
PRODUCT_PLAN = ROOT / "docs" / "manifests" / "product_plans" / "je2000f_eu.yaml"
RESOLVED_MANIFEST = ROOT / "docs" / "manifests" / "manual_main-eu-en.yaml"


class Je2000fEuEnWebTests(unittest.TestCase):
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
                "--config",
                str(CONFIG),
                "--model",
                "JE-2000F",
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
                "JE-2000F formal-source Web build failed:\n"
                + result.stdout
                + result.stderr
            )
        cls.package = (
            cls.staging / "docs" / "_build" / "JE-2000F" / "EU" / "en" / "md"
        )
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_main_intl_three_layer_plan_is_the_target_manifest_authority(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slots, slot_profiles = load_slot_template_catalog(
            SKELETON_DIR / "slot_templates.yaml",
            blueprint,
        )
        profile = load_region_profile(REGION_PROFILE, blueprint)
        product_plan = load_product_plan(PRODUCT_PLAN, blueprint)
        plan = resolve_plan(
            blueprint,
            slots,
            profile,
            manifest_id="manual_main_eu_en",
            product_plan=product_plan,
            slot_template_profiles=slot_profiles,
        )
        expected = emit_manifest_yaml(
            plan,
            header=["Resolved Manifest — main-intl + main-eu-en + je2000f_eu."],
        )

        self.assertEqual("main-intl", blueprint["skeleton_id"])
        self.assertEqual("MAIN", blueprint["skeleton_family"])
        self.assertEqual("INTL", blueprint["house_style"])
        self.assertNotIn("JE-2000F", (SKELETON_DIR / "blueprint.yaml").read_text())
        self.assertEqual(expected, RESOLVED_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            [
                "preface_important",
                "safety_info_en",
                "user_maintenance_instructions_en",
                "symbol_meaning_en",
                "box_contents_en",
                "product_overview_en",
                "lcd_display_en",
                "operation_en",
                "ups_mode_en",
                "extra_battery_en",
                "charging_intro_en",
                "charging_methods_en",
                "storage_en",
                "troubleshooting_en",
                "specifications_en",
                "warranty_en",
                "app_setup_en",
                "regulatory_compliance",
            ],
            [page["slot_id"] for page in plan["pages"]],
        )
        self.assertNotIn(
            "model_overrides",
            yaml.safe_load(RESOLVED_MANIFEST.read_text(encoding="utf-8")),
        )

    def test_shared_config_binds_only_this_target_and_preserves_page_names(self) -> None:
        config = load_config_mapping(CONFIG)
        self.assertEqual(
            "docs/manifests/manual_main-eu-en.yaml",
            config["paths"]["page_manifests"]["JE-2000F_EU"],
        )
        planned = plan_materialized_pages(
            config,
            model="JE-2000F",
            region="EU",
            langs=["en"],
            root=ROOT,
        )
        self.assertEqual(
            [
                "00_preface.rst",
                "safety_en.rst",
                "01_user_maintenance_instructions.rst",
                "symbols_en.rst",
                "02_whats_in_the_box.rst",
                "03_product_overview_placeholder.rst",
                "lcd_icons_en.rst",
                "05_operation_guide_placeholder.rst",
                "06_ups_mode.rst",
                "charging.rst",
                "08_charging_methods.rst",
                "09_storage_and_maintenance.rst",
                "troubleshooting_en.rst",
                "spec_en.rst",
                "11_warranty.rst",
                "12_app_setup_placeholder.rst",
                "99_regulatory_compliance.rst",
            ],
            [page.file_name for page in planned],
        )
        self.assertEqual(
            [page.file_name for page in planned],
            [page.page_id for page in self.ir.pages],
        )

    def test_frozen_source_matches_published_target_facts(self) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        values = {
            (row["Row_key"], row["Slot_key"]): row["Value_source"]
            for row in rows
            if row["document_key"] == "JE-2000F_EU"
        }
        self.assertEqual(
            "4000 cycles to 70%+ capacity", values[("cycle_life", "")]
        )
        self.assertEqual(
            "220 V-240 V ~ 50 Hz, 2200 W max.",
            values[("ac_output_bypass", "")],
        )
        self.assertEqual("10 ms", values[("ups_transfer_time", "value")])
        self.assertEqual("16V-60V", values[("pv_input_range", "value")])
        self.assertEqual("DC8020", values[("dc_input_connector", "value")])

        with (FORMAL_DATA_ROOT / "lcd_icons_blocks.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            lcd = [(row["No."], row["icon_en"]) for row in csv.DictReader(handle)]
        self.assertEqual(
            [
                ("17", "Battery Power Indicator"),
                ("18", "Low Battery Indicator"),
                ("19", "Remaining Battery Percentage"),
                ("20", "Discharge Timer"),
                ("21", "Energy Saving Mode"),
                ("22", "High Temperature Indicator"),
                ("22", "Low Temperature Indicator"),
                ("23", "Fault code"),
                ("24", "Output Power"),
                ("25", "Remaining Discharge Time"),
            ],
            lcd[16:],
        )

        with (FORMAL_DATA_ROOT / "troubleshooting_blocks.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            codes = [row["error_code"] for row in csv.DictReader(handle)]
        self.assertEqual(
            ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "FE"],
            codes,
        )

    def test_source_manifest_locks_every_frozen_input(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(manifest["live_bitable_dependency"])
        self.assertEqual("V2.0-2026-08-04", manifest["authority"]["published_revision"])
        self.assertEqual(
            "Jackery Explorer 2000 User Manual (JE-2000F) EUUK V2.0-2026-08-04.pdf",
            manifest["authority"]["published_pdf_name"],
        )
        self.assertEqual(
            "6b4af85236ccfee0f4d24ad55ee8b24684d023982b5da216023d4f716f183f3d",
            manifest["authority"]["published_pdf_sha256"],
        )
        for binding in (
            "asset_recipe",
            "corrective_asset_recipe",
            "web_illustration_manifest",
        ):
            bound = manifest[binding]
            self.assertEqual(
                bound["sha256"],
                hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest(),
                binding,
            )
        for record in manifest["files"]:
            data = (FORMAL_SOURCE / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())

    def test_web_output_has_complete_figure_coverage(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        inbox = soup.select_one('[data-component-id="HB-SPECIAL-INBOX"]')
        self.assertIsNotNone(inbox)
        self.assertEqual(
            ["1", "2", "3"],
            [
                str(card["data-item-number"])
                for card in inbox.select(".hb-inbox-card")
            ],
        )
        auto_resume = soup.select_one("figure.hb-auto-resume-composition")
        self.assertIsNotNone(auto_resume)
        self.assertIsNotNone(
            auto_resume.select_one("table.hb-auto-resume-table")
            if auto_resume
            else None
        )
        lcd_mode = soup.select_one("figure.hb-lcd-mode-composition")
        self.assertIsNotNone(lcd_mode)
        self.assertIsNotNone(
            lcd_mode.select_one(".hb-lcd-mode-art-panel img") if lcd_mode else None
        )
        self.assertIsNotNone(
            lcd_mode.select_one("table.hb-lcd-mode-table") if lcd_mode else None
        )
        app_add_device = soup.select_one(
            'img.manual-finished-illustration[data-reference-id="app-add-device"]'
        )
        self.assertIsNotNone(app_add_device)
        self.assertTrue(
            str(app_add_device["data-web-finished-panel-path"]).endswith(
                "/app_control_panel.png"
            )
        )
        self.assertEqual(
            "Main POWER Button AC Power Button DC / USB Power Button",
            app_add_device.get("alt"),
        )
        self.assertEqual([], soup.select(".hb-app-add-device-live-label"))
        coverage = self.ir.metadata["web_figure_coverage"]
        self.assertEqual(12, coverage["summary"]["total"])
        self.assertEqual(0, coverage["summary"]["by_status"]["missing"])
        self.assertEqual(11, coverage["summary"]["by_status"]["finished-panel"])
        self.assertEqual(1, coverage["summary"]["by_status"]["editable-fallback"])
        self.assertEqual(
            ["semantic.lcd-mode-composition"],
            [
                slot["slot_id"]
                for slot in coverage["slots"]
                if slot["status"] == "editable-fallback"
            ],
        )
        self.assertEqual(14, len(soup.select(".manual-finished-illustration")))
        self.assertEqual(17, len(self.ir.pages))
        for expected in (
            "4000 cycles to 70%+ capacity",
            "220 V-240 V ~ 50 Hz, 2200 W max.",
            "within 10 ms",
            "AC and DC Output Resume Function",
            "2412-2472 MHz",
            "2011/65/EU",
        ):
            self.assertIn(expected, self.html)
        self.assertNotIn("|UPS_TRANSFER_TIME|", self.html)
        self.assertNotIn("|PV_INPUT_RANGE|", self.html)
        self.assertNotIn("|DC_INPUT_CONNECTOR|", self.html)
        self.assertNotIn("2000 Plus", self.html)
        self.assertNotIn("AC1/2", self.html)
        self.assertIn(
            "When the AC or DC output is turned on by pressing the AC or DC/USB power button:",
            self.html,
        )

    def test_finished_text_bearing_illustrations_consume_covered_copy(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual([], soup.select("#front-view > table"))
        self.assertEqual([], soup.select("#right-side-view > table"))
        self.assertIsNone(soup.select_one("#ac-output-on-off > .line-block"))
        self.assertNotIn(
            "Prerequisite : The product is powered on.",
            soup.select_one("#ac-output-on-off").get_text(" ", strip=True),
        )
        self.assertNotIn(
            "On Press once Off Press once",
            soup.select_one("#dc-12v-usb-output-on-off").get_text(" ", strip=True),
        )
        self.assertNotIn(
            "Prerequisite : The product is powered on.",
            soup.select_one("#dc-12v-usb-output-on-off").get_text(" ", strip=True),
        )
        self.assertIsNone(soup.select_one("#energy-saving-mode > .line-block"))
        self.assertIsNone(soup.select_one("#led-light-on-off > .line-block"))
        self.assertNotIn(
            "The LED light has two modes:",
            soup.select_one("#led-light-on-off").get_text(" ", strip=True),
        )
        self.assertNotIn(
            "Connect the AC charging cable to the AC input port",
            soup.select_one("#charging-via-ac-wall-outlet").get_text(
                " ", strip=True
            ),
        )
        self.assertNotIn(
            "Vehicle",
            [
                node.get_text(" ", strip=True)
                for node in soup.select(
                    "#charging-via-a-car-charger-sold-separately "
                    "> .line-block > .line"
                )
            ],
        )
        power_copy = soup.select_one("#power-on-off").get_text(" ", strip=True)
        self.assertNotIn("On: Press once.", power_copy)
        self.assertNotIn("Default standby time:", power_copy)
        self.assertNotIn(
            "When Energy Saving Mode is enabled, the product will automatically "
            "shut down after 12 hours",
            power_copy,
        )
        energy_copy = soup.select_one("#energy-saving-mode").get_text(" ", strip=True)
        self.assertNotIn("To disable the energy saving mode", energy_copy)
        self.assertNotIn("When powering low-power devices", energy_copy)
        car_copy = soup.select_one(
            "#charging-via-a-car-charger-sold-separately"
        ).get_text(" ", strip=True)
        self.assertNotIn("The car charging cable is sold separately", car_copy)
        for path in (
            "overview_front.png",
            "overview_side.png",
            "operation_power.png",
            "operation_ac.png",
            "operation_dc.png",
            "operation_energy.png",
            "operation_led.png",
            "charging_car.png",
            "app_control_panel.png",
        ):
            image = soup.select_one(
                f'[data-web-finished-panel-path$="/{path}"]'
            )
            self.assertIsNotNone(image, path)
            self.assertTrue(str(image.get("alt") or "").strip(), path)

    def test_illustration_recipe_manifest_and_files_are_hash_locked(self) -> None:
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        original_recipe_path = ROOT / manifest["recipe"]
        original_recipe = json.loads(
            original_recipe_path.read_text(encoding="utf-8")
        )
        correction_recipe = json.loads(
            (ROOT / manifest["correction_recipe"]).read_text(encoding="utf-8")
        )
        self.assertEqual(
            "986b3c5d5588b43d791e1e52860ddba97f52b2d5faee93652d8d7e9df89b3c29",
            hashlib.sha256(original_recipe_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            "a8a202b0a44a3646bfea9c4279947eab98b32ff03c4715c16445bf52c8f15de6",
            hashlib.sha256(
                (ROOT / manifest["correction_recipe"]).read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(15, len(manifest["illustrations"]))
        self.assertEqual(14, len(original_recipe["assets"]))
        self.assertEqual(11, len(correction_recipe["assets"]))
        for asset in original_recipe["assets"] + correction_recipe["assets"]:
            self.assertTrue(asset["build_eligible"])
            self.assertFalse(asset["visual_review_required"])
            self.assertEqual("approved", asset["gate"]["status"])
        for asset in correction_recipe["assets"]:
            self.assertEqual([12], [output["scale"] for output in asset["outputs"]])
        output_hashes = {
            output["path"]: output["expected_sha256"]
            for recipe in (original_recipe, correction_recipe)
            for asset in recipe["assets"]
            for output in asset["outputs"]
        }
        for illustration in manifest["illustrations"]:
            path = ILLUSTRATIONS.parent / illustration["path"]
            self.assertEqual(
                illustration["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )
            self.assertEqual(
                illustration["sha256"],
                output_hashes[path.relative_to(ROOT).as_posix()],
            )

    def test_public_ir_replay_and_tamper_detection(self) -> None:
        fragments = render_document_fragments(self.ir, package_root=self.package)
        self.assertEqual(17, len(fragments))
        with tempfile.TemporaryDirectory() as td:
            copied = Path(td) / "package"
            shutil.copytree(self.package, copied)
            ir = read_manual_ir(copied / "manual.ir.json")
            relative = next(iter(ir.metadata["asset_sha256"]))
            (copied / relative).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "asset missing or changed"):
                render_document_fragments(ir, package_root=copied)


if __name__ == "__main__":
    unittest.main()
