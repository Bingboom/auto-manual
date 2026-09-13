from __future__ import annotations

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
FORMAL_SOURCE = ROOT / "manual_sources/JE-500A/EU/en/2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"
ILLUSTRATIONS = ROOT / "docs/renderers/web/je500a_eu_en_illustrations.json"


class Je500aEuEnWebTests(unittest.TestCase):
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
                "--config", str(CONFIG),
                "--model", "JE-500A",
                "--region", "EU",
                "--lang", "en",
                "--data-root", str(FORMAL_DATA_ROOT),
                "--staging-root", str(cls.staging),
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
            raise AssertionError("JE-500A frozen-source Web build failed:\n" + result.stdout + result.stderr)
        cls.package = cls.staging / "docs/_build/JE-500A/EU/en/md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_source_manifest_locks_every_frozen_input(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(manifest["live_bitable_dependency"])
        self.assertEqual("YndMj49yWjP03jNjCDojvAQdJ3pmz5aA", manifest["authority"]["base_token"])
        self.assertEqual("97v7518", manifest["authority"]["table_id"])
        self.assertEqual("xF8IUxGEbx", manifest["authority"]["record_id"])
        self.assertEqual(
            "c85b8da316fd7b13e3e77e311df76c389234495f38f454019a88f61b6812d12f",
            manifest["authority"]["source_sha256"],
        )
        self.assertEqual(14, manifest["authority"]["english_body_panels"]["count"])
        for binding in ("asset_recipe", "web_illustration_manifest"):
            bound = manifest[binding]
            self.assertEqual(bound["sha256"], hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest())
        for record in manifest["files"]:
            data = (FORMAL_SOURCE / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())

    def test_output_preserves_target_facts_and_excludes_foreign_identity(self) -> None:
        for expected in (
            "Jackery Explorer 500",
            "JE-500A",
            "20Ah/25.6V DC (512 Wh)",
            "500W Rated, 1000W Surge peak",
            "6000 cycles to 70%+ capacity",
            "within 10 ms",
            "3 YEARS - Standard Warranty",
            "2 YEARS - Extended Warranty",
        ):
            self.assertIn(expected, self.html)
        for forbidden in (
            "JE-1000F", "JE-1000H", "JE-2000E", "JE-2000F", "JE-100C",
            "Explorer 100D", "Explorer 1000", "Explorer 2000", "==MISSING:",
        ):
            self.assertNotIn(forbidden, self.html)

    def test_semantic_components_and_lcd_ownership(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(13, len(self.ir.pages))
        self.assertEqual(16, len(soup.select("img.manual-finished-illustration")))
        coverage = self.ir.metadata["web_figure_coverage"]
        self.assertEqual(11, coverage["summary"]["total"])
        self.assertEqual(11, coverage["summary"]["by_status"]["finished-panel"])
        self.assertEqual(0, coverage["summary"]["by_status"]["missing"])
        inbox = soup.select_one('[data-component-id="HB-SPECIAL-INBOX"]')
        self.assertIsNotNone(inbox)
        self.assertEqual(3, len(inbox.select(".hb-inbox-card")))

        lcd_heading = next(
            (heading for heading in soup.find_all("h1") if heading.get_text(" ", strip=True) == "LCD DISPLAY"),
            None,
        )
        self.assertIsNotNone(lcd_heading)
        lcd_nodes = []
        for sibling in lcd_heading.next_siblings:
            if getattr(sibling, "name", None) == "h1":
                break
            lcd_nodes.append(sibling)
        lcd = BeautifulSoup("".join(str(node) for node in lcd_nodes), "html.parser")
        self.assertEqual(1, len(lcd.select("img.manual-finished-illustration")))
        self.assertEqual(1, len(lcd.select("table")))
        self.assertIn("Remaining Battery Percentage", lcd.get_text(" ", strip=True))

        operation_heading = next(
            (heading for heading in soup.find_all("h1") if heading.get_text(" ", strip=True) == "OPERATIONS"),
            None,
        )
        self.assertIsNotNone(operation_heading)
        operation_nodes = []
        for sibling in operation_heading.next_siblings:
            if getattr(sibling, "name", None) == "h1":
                break
            operation_nodes.append(sibling)
        operation = BeautifulSoup("".join(str(node) for node in operation_nodes), "html.parser")
        self.assertEqual(1, len(operation.select("table")))
        self.assertIn("Always-on Display Mode", operation.get_text(" ", strip=True))
        self.assertGreaterEqual(len(soup.select(".admonition.note")), 2)
        self.assertGreaterEqual(len(soup.select(".admonition.caution")), 5)

    def test_illustrations_are_hash_locked_and_recipe_approved(self) -> None:
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        recipe = json.loads((ROOT / manifest["recipe"]).read_text(encoding="utf-8"))
        self.assertEqual(16, len(manifest["illustrations"]))
        self.assertEqual(16, len(recipe["assets"]))
        output_hashes = {
            output["path"]: output["expected_sha256"]
            for asset in recipe["assets"] for output in asset["outputs"]
        }
        for asset in recipe["assets"]:
            self.assertTrue(asset["build_eligible"])
            self.assertFalse(asset["visual_review_required"])
            self.assertEqual("approved", asset["gate"]["status"])
        for illustration in manifest["illustrations"]:
            path = ILLUSTRATIONS.parent / illustration["path"]
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(illustration["sha256"], actual)
            self.assertEqual(actual, output_hashes[path.relative_to(ILLUSTRATIONS.parent).as_posix()])

    def test_public_ir_cold_replay_and_tamper_rejection(self) -> None:
        self.assertEqual(13, len(render_document_fragments(self.ir, package_root=self.package)))
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
