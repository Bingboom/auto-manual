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
CONFIG = ROOT / "configs" / "config.eu-en.yaml"
FORMAL_SOURCE = ROOT / "manual_sources" / "JE-2000F" / "EU" / "en" / "2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"
ILLUSTRATIONS = (
    ROOT / "docs" / "renderers" / "web" / "je2000f_eu_en_illustrations.json"
)


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
        self.assertEqual(
            "6b4af85236ccfee0f4d24ad55ee8b24684d023982b5da216023d4f716f183f3d",
            manifest["authority"]["published_pdf_sha256"],
        )
        for record in manifest["files"]:
            data = (FORMAL_SOURCE / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())

    def test_web_output_has_complete_finished_figure_coverage(self) -> None:
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
        coverage = self.ir.metadata["web_figure_coverage"]
        self.assertEqual(12, coverage["summary"]["total"])
        self.assertEqual(0, coverage["summary"]["by_status"]["missing"])
        self.assertEqual(12, coverage["summary"]["by_status"]["finished-panel"])
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

    def test_illustration_recipe_manifest_and_files_are_hash_locked(self) -> None:
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        recipe = json.loads(
            (ROOT / manifest["recipe"]).read_text(encoding="utf-8")
        )
        self.assertEqual(14, len(manifest["illustrations"]))
        self.assertEqual(14, len(recipe["assets"]))
        for asset in recipe["assets"]:
            self.assertTrue(asset["build_eligible"])
            self.assertFalse(asset["visual_review_required"])
            self.assertEqual("approved", asset["gate"]["status"])
        for illustration in manifest["illustrations"]:
            path = ILLUSTRATIONS.parent / illustration["path"]
            self.assertEqual(
                illustration["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
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
