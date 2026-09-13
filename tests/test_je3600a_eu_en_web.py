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

from tools.manual_ir import read_manual_ir


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/config.eu-en.yaml"
FORMAL_SOURCE = ROOT / "manual_sources/JE-3600A/EU/en/2026-05-25"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"


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

    def test_source_manifest_locks_frozen_inputs(self) -> None:
        manifest = json.loads((FORMAL_SOURCE / "source_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("formal-published-source-audited-git-input", manifest["source_role"])
        self.assertEqual("bfbcc4377fb474952f5e0850818289449016c8df11b1df48aff192b646eedf6d", manifest["authority"]["published_pdf_sha256"])
        self.assertFalse(manifest["live_bitable_dependency"])
        for binding in ("asset_recipe", "web_illustration_manifest"):
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
        self.assertEqual(16, len(self.soup.select(".manual-finished-illustration")))
        self.assertIn("Jackery Battery Pack 3600 User Manual", self.html)
        self.assertIn("3600 W rated, 7200 W surge peak", self.html)
        for stale in ("Battery Pack 2000", "DC 12V/USB OUTPUT", "LED LIGHT ON/OFF", "AC1/2", "Emergency Charging Mode"):
            self.assertNotIn(stale, self.html)
        coverage = self.ir.metadata["web_figure_coverage"]["summary"]
        self.assertEqual(10, coverage["total"])
        self.assertEqual(10, coverage["by_status"]["finished-panel"])
        self.assertEqual(0, coverage["by_status"]["missing"])
        self.assertEqual(18, len(self.ir.pages))


if __name__ == "__main__":
    unittest.main()
