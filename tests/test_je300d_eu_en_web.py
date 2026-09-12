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
SOURCE_ROOT = ROOT / "manual_sources/JE-300D/EU/en/candidate-2025-10-24"
DATA_ROOT = SOURCE_ROOT / "phase2"
SOURCE_MANIFEST = SOURCE_ROOT / "source_manifest.json"
ILLUSTRATIONS = ROOT / "docs/renderers/web/je300d_eu_en_illustrations.json"


class Je300dEuEnWebTests(unittest.TestCase):
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
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "build.py"),
                "md",
                "--config",
                str(CONFIG),
                "--model",
                "JE-300D",
                "--region",
                "EU",
                "--lang",
                "en",
                "--data-root",
                str(DATA_ROOT),
                "--staging-root",
                str(cls.staging),
            ],
            cwd=ROOT,
            env={
                **os.environ,
                "AUTO_MANUAL_OSS_ARCHIVE_CONFIG": "off",
                "AUTO_MANUAL_PRESENTATION_PROFILE": "web",
                "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
            },
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        cls.package = cls.staging / "docs/_build/JE-300D/EU/en/md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_git_frozen_candidate_source_and_bindings(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("operator-designated-candidate-ai-source", manifest["source_role"])
        self.assertIsNone(manifest["authority"]["published_revision"])
        self.assertEqual("QviOQihBNj", manifest["authority"]["demand_record_id"])
        self.assertFalse(manifest["live_bitable_dependency"])
        self.assertEqual(
            "53209e53bb5ca5bcfa08c8eeeedd9c7ee6cc2c0cd226e6c7c776bb68421f78bc",
            manifest["authority"]["source_attachment_sha256"],
        )
        for binding in ("page_manifest", "asset_recipe", "web_illustration_manifest"):
            record = manifest[binding]
            self.assertEqual(
                record["sha256"], hashlib.sha256((ROOT / record["path"]).read_bytes()).hexdigest()
            )
        for record in manifest["files"]:
            data = (SOURCE_ROOT / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())

    def test_web_output_preserves_exact_target_facts_and_scope(self) -> None:
        for expected in (
            "Jackery Explorer 300D",
            "JE-300D",
            "15Ah / 19.2V DC (288 Wh)",
            "About 2.5 kg",
            "11.86 × 12.02 × 18.3 cm",
            "4000 cycles to 70%+ capacity",
            "USB-C CHARGING (140W MAX)",
            "SOLAR CHARGING (100W MAX)",
            "CAR CHARGING (96W MAX)",
            "3 YEARS",
            "2 YEARS",
            "LVD Directive 2014/35/EU",
        ):
            self.assertIn(expected, self.html)
        for forbidden in (
            "JE-3000C",
            "Jackery Explorer 3000",
            "AC OUTPUT ON/OFF",
            "UPS MODE",
            "Jackery App",
            "CONNECT TO BATTERY PACK",
            "==MISSING:",
        ):
            self.assertNotIn(forbidden, self.html)

    def test_semantic_lcd_tables_and_finished_panel_coverage(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(14, len(self.ir.pages))
        self.assertEqual(14, len(soup.select("img.manual-finished-illustration")))
        coverage = self.ir.metadata["web_figure_coverage"]
        self.assertEqual(11, coverage["summary"]["total"])
        self.assertEqual(0, coverage["summary"]["by_status"]["missing"])
        self.assertEqual(11, coverage["summary"]["by_status"]["finished-panel"])

        lcd = soup.select_one("table.lcd-text-only")
        self.assertIsNotNone(lcd)
        self.assertEqual(11, len(lcd.select("tbody > tr")))
        lcd_text = lcd.get_text(" ", strip=True)
        self.assertIn("USB-C Charging Indicator", lcd_text)
        self.assertIn("High Temperature Indicator", lcd_text)
        self.assertIn("Low Temperature Indicator", lcd_text)
        self.assertIsNotNone(
            soup.select_one('[data-web-finished-panel-path$="/lcd_map.png"]')
        )

        lcd_control = soup.select_one("#lcd-screen-on-off")
        self.assertIsNotNone(lcd_control)
        self.assertEqual(1, len(lcd_control.select("img.manual-finished-illustration")))
        self.assertEqual(1, len(lcd_control.select("table")))
        self.assertIn("2 minutes of inactivity", lcd_control.get_text(" ", strip=True))

    def test_recipe_manifest_assets_and_csv_registry_agree(self) -> None:
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        recipe = json.loads((ROOT / manifest["recipe"]).read_text(encoding="utf-8"))
        self.assertEqual(14, len(manifest["illustrations"]))
        self.assertEqual(14, len(recipe["assets"]))
        output_hashes = {
            output["path"]: output["expected_sha256"]
            for asset in recipe["assets"]
            for output in asset["outputs"]
        }
        for asset in recipe["assets"]:
            self.assertTrue(asset["build_eligible"])
            self.assertFalse(asset["visual_review_required"])
            self.assertEqual("approved", asset["gate"]["status"])
        for illustration in manifest["illustrations"]:
            path = ILLUSTRATIONS.parent / illustration["path"]
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(illustration["sha256"], actual)
            self.assertEqual(actual, output_hashes[path.relative_to(ROOT).as_posix()])

        with (ROOT / "data/asset_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = [
                row
                for row in csv.DictReader(handle)
                if row["asset_key"].startswith("web/je300d/eu/en/")
            ]
        self.assertEqual(14, len(rows))
        self.assertTrue(all(row["状态"] == "✅成品" for row in rows))
        self.assertTrue(all("未写线上 Base" in row["备注"] for row in rows))

    def test_batch_snapshot_keeps_independent_and_composite_counts_separate(self) -> None:
        snapshot = json.loads((SOURCE_ROOT / "scope-snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(38, snapshot["counts"]["rows"])
        self.assertEqual(21, snapshot["counts"]["independent_with_ai"])
        self.assertEqual(16, snapshot["counts"]["completed_engineering"])
        self.assertEqual(5, snapshot["counts"]["remaining_independent"])
        self.assertEqual(2, snapshot["counts"]["composite"])
        review = (ROOT / "code-as-doc/reviews/je300d_eu_en_web_intake_2026-09.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("composite rows are explicitly excluded", review)

    def test_public_ir_replay_and_tamper_detection(self) -> None:
        self.assertEqual(14, len(render_document_fragments(self.ir, package_root=self.package)))
        with tempfile.TemporaryDirectory() as temp_dir:
            copied = Path(temp_dir) / "package"
            shutil.copytree(self.package, copied)
            ir = read_manual_ir(copied / "manual.ir.json")
            relative = next(iter(ir.metadata["asset_sha256"]))
            (copied / relative).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "asset missing or changed"):
                render_document_fragments(ir, package_root=copied)


if __name__ == "__main__":
    unittest.main()
