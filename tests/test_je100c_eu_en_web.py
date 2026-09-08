from __future__ import annotations

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
CONFIG = ROOT / "configs" / "config.eu-en.yaml"
FORMAL_SOURCE = ROOT / "manual_sources" / "JE-100C" / "EU" / "en" / "2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"


class Je100cEuEnWebTests(unittest.TestCase):
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
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "build.py"),
                "md",
                "--config",
                str(CONFIG),
                "--model",
                "JE-100C",
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
            raise AssertionError("JE-100C formal-source Web build failed:\n" + result.stdout + result.stderr)
        cls.package = cls.staging / "docs" / "_build" / "JE-100C" / "EU" / "en" / "md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_source_manifest_locks_formal_inputs(self) -> None:
        manifest = json.loads((FORMAL_SOURCE / "source_manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["live_bitable_dependency"])
        self.assertEqual("V2.0-2026-08-03", manifest["authority"]["published_revision"])
        self.assertEqual(
            "012465a75b3af63e66be5b16d553f3a0aa014256ac4cc0502a0f85dd3419bc1c",
            manifest["authority"]["published_pdf_sha256"],
        )
        for binding in ("asset_recipe", "web_illustration_manifest"):
            bound = manifest[binding]
            self.assertEqual(bound["sha256"], hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest())
        for record in manifest["files"]:
            data = (FORMAL_SOURCE / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())

    def test_web_output_preserves_target_identity_and_exact_facts(self) -> None:
        for expected in (
            "Jackery Explorer 100D",
            "96Wh (5Ah/19.2V DC)",
            "855 g ± 10 g",
            "(118.7 ± 1) × (82.6 ± 0.5) × (85.68 ± 0.8) mm",
            "This product can be charged using 12V and 24V car chargers.",
            "2-year limited warranty",
        ):
            self.assertIn(expected, self.html)
        for forbidden in ("JE-1000", "Explorer 1000", "工作环境温度", "==MISSING:"):
            self.assertNotIn(forbidden, self.html)

    def test_shared_inbox_and_finished_figure_coverage(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        inbox = soup.select_one('[data-component-id="HB-SPECIAL-INBOX"]')
        self.assertIsNotNone(inbox)
        self.assertEqual(3, len(inbox.select(".hb-inbox-card")))
        coverage = self.ir.metadata["web_figure_coverage"]
        self.assertEqual(7, coverage["summary"]["total"])
        self.assertEqual(0, coverage["summary"]["by_status"]["missing"])
        self.assertEqual(7, coverage["summary"]["by_status"]["finished-panel"])
        self.assertEqual(13, len(soup.select("img.manual-finished-illustration")))

    def test_lcd_remains_device_art_plus_semantic_tables(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        lcd_heading = next(
            (heading for heading in soup.find_all("h1") if heading.get_text(" ", strip=True) == "LCD DISPLAY"),
            None,
        )
        self.assertIsNotNone(lcd_heading)
        nodes = []
        for sibling in lcd_heading.next_siblings:
            if getattr(sibling, "name", None) == "h1":
                break
            nodes.append(sibling)
        fragment = BeautifulSoup("".join(str(node) for node in nodes), "html.parser")
        self.assertGreaterEqual(len(fragment.select("img.manual-finished-illustration")), 3)
        tables = fragment.select("table")
        self.assertEqual(3, len(tables))
        text = " ".join(table.get_text(" ", strip=True) for table in tables)
        self.assertIn("Fault code", text)
        self.assertIn("Battery Health and Cycle Count", text)


if __name__ == "__main__":
    unittest.main()
