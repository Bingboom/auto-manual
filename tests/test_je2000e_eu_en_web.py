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
FORMAL_SOURCE = ROOT / "manual_sources" / "JE-2000E" / "EU" / "en" / "2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"
ILLUSTRATIONS = ROOT / "docs" / "renderers" / "web" / "je2000e_eu_en_illustrations.json"


class Je2000eEuEnWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.staging = Path(cls._tmp.name) / "staging"
        env = {
            **os.environ,
            "AUTO_MANUAL_OSS_ARCHIVE_CONFIG": "off",
            "AUTO_MANUAL_PRESENTATION_PROFILE": "web",
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

    def test_source_manifest_locks_every_frozen_input(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(manifest["live_bitable_dependency"])
        self.assertEqual("V2.0-2026-08-03", manifest["authority"]["published_revision"])
        self.assertEqual(
            "734f89ad824d2436d2c79c7ac1231d2dc111dd83ef43e8ee6326674124c396d0",
            manifest["authority"]["published_pdf_sha256"],
        )
        for binding in ("asset_recipe", "web_illustration_manifest"):
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
        self.assertEqual(15, len(soup.select(".manual-finished-illustration")))
        coverage = self.ir.metadata["web_figure_coverage"]
        self.assertEqual(12, coverage["summary"]["total"])
        self.assertEqual(0, coverage["summary"]["by_status"]["missing"])
        self.assertEqual(11, coverage["summary"]["by_status"]["finished-panel"])
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
        self.assertEqual(19, len(recipe["assets"]))
        self.assertEqual(16, len(manifest["illustrations"]))
        output_hashes = {
            output["path"]: output["expected_sha256"]
            for asset in recipe["assets"]
            for output in asset["outputs"]
        }
        for asset in recipe["assets"]:
            self.assertTrue(asset["build_eligible"])
            self.assertFalse(asset["visual_review_required"])
            self.assertEqual("approved", asset["gate"]["status"])
            self.assertEqual([12], [output["scale"] for output in asset["outputs"]])
        for illustration in manifest["illustrations"]:
            path = ILLUSTRATIONS.parent / illustration["path"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(illustration["sha256"], digest)
            self.assertEqual(
                digest,
                output_hashes[path.relative_to(ROOT).as_posix()],
            )

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


if __name__ == "__main__":
    unittest.main()
