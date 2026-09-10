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

from tools.manual_ir import read_manual_ir
from tools.web_document_ir import render_document_fragments


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/config.eu-en.yaml"
FORMAL_SOURCE = ROOT / "manual_sources/JE-3000C/EU/en/2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"
ILLUSTRATIONS = ROOT / "docs/renderers/web/je3000c_eu_en_illustrations.json"
WEB_CSS = ROOT / "docs/renderers/contracts/web_manual.css"


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
        for binding in ("asset_recipe", "web_illustration_manifest"):
            bound = manifest[binding]
            self.assertEqual(bound["sha256"], hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest())
        for record in manifest["files"]:
            data = (FORMAL_SOURCE / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())

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
        self.assertEqual(18, len(recipe["assets"]))
        self.assertEqual(18, len(manifest["illustrations"]))
        outputs = {}
        for asset in recipe["assets"]:
            self.assertTrue(asset["build_eligible"])
            self.assertFalse(asset["visual_review_required"])
            self.assertEqual("approved", asset["gate"]["status"])
            self.assertEqual([12], [output["scale"] for output in asset["outputs"]])
            for output in asset["outputs"]:
                outputs[output["path"]] = output["expected_sha256"]
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
        css = WEB_CSS.read_text(encoding="utf-8")
        self.assertIn(
            '#dc-12v-usb-output-on-off > img[data-web-finished-panel-path="assets/je3000c_eu_en/operation_dc.png"]',
            css,
        )

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


if __name__ == "__main__":
    unittest.main()
