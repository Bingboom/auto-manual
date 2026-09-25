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
FORMAL_SOURCE = ROOT / "manual_sources/JE-1000H/EU/en/2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"
ILLUSTRATIONS = ROOT / "docs/renderers/web/je1000h_eu_en_illustrations.json"
# 同一源 PDF 的六个语言块各出一套成品整图；非英语套系尚未接入 config 目标。
MANUAL_LOCALES = ("en", "fr", "es", "de", "it", "uk")


class Je1000hEuEnWebTests(unittest.TestCase):
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
                "--model", "JE-1000H",
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
            raise AssertionError(result.stdout + result.stderr)
        cls.package = cls.staging / "docs/_build/JE-1000H/EU/en/md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_frozen_source_matches_published_target_facts(self) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        values = {
            (row["Row_key"], row["Slot_key"], row["Line_order"]): row["Value_source"]
            for row in rows if row["document_key"] == "JE-1000H_EU"
        }
        expected = {
            ("capacity", "", "1"): "1024 Wh (20Ah/51.2V DC)",
            ("cycle_life", "", "1"): "6000 cycles to 70%+ capacity",
            ("ac_output", "", "1"): "230V~50Hz, 7.83A, 1800W Rated",
            ("ac_output_bypass", "", "1"): "220V-240V~50Hz, 7.83A",
            ("dc_expansion_input", "", "1"): "36.8V-56V⎓59A Max",
            ("dc_expansion_output", "", "1"): "36.8V-56V⎓36A Max",
        }
        for key, value in expected.items():
            self.assertEqual(value, values[key])

        with (FORMAL_DATA_ROOT / "lcd_icons_blocks.csv").open(encoding="utf-8", newline="") as handle:
            lcd = list(csv.DictReader(handle))
        self.assertEqual(27, len(lcd))
        self.assertEqual("Connected Batteries", lcd[20]["icon_en"])
        self.assertEqual(["23", "23"], [lcd[22]["No."], lcd[23]["No."]])

        with (FORMAL_DATA_ROOT / "troubleshooting_blocks.csv").open(encoding="utf-8", newline="") as handle:
            codes = [row["error_code"] for row in csv.DictReader(handle)]
        self.assertEqual(
            ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "FC", "FE"],
            codes,
        )

    def test_source_manifest_locks_every_frozen_input(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(manifest["live_bitable_dependency"])
        self.assertEqual("V2.0-2026-08-03", manifest["authority"]["published_revision"])
        self.assertEqual(
            "07e9ac4b9faabd0852f61702df06f2837caa952c2fa28151b599ad930b1c0bcc",
            manifest["authority"]["published_pdf_sha256"],
        )
        for binding in ("asset_recipe", "web_illustration_manifest"):
            bound = manifest[binding]
            self.assertEqual(bound["sha256"], hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest())
        for record in manifest["files"]:
            data = (FORMAL_SOURCE / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())
        inventory = json.dumps(manifest["files"], ensure_ascii=False,
                               sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(manifest["files_inventory_sha256"], hashlib.sha256(inventory).hexdigest())

    def test_ac_total_output_and_footnote_match_released_pdf(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        labels = {cell.get_text("", strip=True): cell.parent
                  for cell in soup.select("th.hb-spec-label")}
        self.assertIn("AC Total Output②", labels)
        total = labels["AC Total Output②"]
        self.assertEqual("1800W Rated, 3600W Surge peak", total.select_one("td").get_text(strip=True))
        self.assertEqual([], labels["3 × AC"].select("sup"))

    def test_usb_parent_and_power_labels_match_released_pdf(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        labels = [cell for cell in soup.select("th.hb-spec-label")
                  if cell.get_text(strip=True) == "2 × USB-C"]
        self.assertEqual(1, len(labels))
        value = labels[0].parent.select_one("td")
        text = value.get_text("\n", strip=True)
        self.assertIn("USB-C 30W: 30W Max", text)
        self.assertIn("USB-C 140W: 140W Max", text)
        self.assertLess(text.index("USB-C 30W:"), text.index("USB-C 140W:"))

    def test_web_output_is_complete_semantic_and_target_local(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        coverage = self.ir.metadata["web_figure_coverage"]
        self.assertEqual(12, coverage["summary"]["total"])
        self.assertEqual(0, coverage["summary"]["by_status"]["missing"])
        self.assertEqual(21, len(soup.select(".manual-finished-illustration")))
        self.assertEqual(18, len(self.ir.pages))
        lcd = soup.select_one("table.lcd-text-only")
        self.assertIsNotNone(lcd)
        self.assertEqual(27, len(lcd.select("tbody > tr")))
        self.assertIsNotNone(soup.select_one('[data-web-finished-panel-path$="/lcd_map.png"]'))
        self.assertEqual([], soup.select("#front-view > table"))
        self.assertEqual([], soup.select("#left-and-right-side-view > table"))
        for ident in ("power-on-off", "ac-output-on-off", "led-light-on-off"):
            self.assertEqual(1, len(soup.select(f"#{ident} > img.manual-finished-illustration")))
        for value in (
            "1024 Wh (20Ah/51.2V DC)",
            "6000 cycles to 70%+ capacity",
            "36.8V-56V⎓59A Max",
            "36.8V-56V⎓36A Max",
            "within 10 ms",
            "USB-C 140W",
            "3 YEARS Standard Warranty",
            "2 YEARS Extended Warranty",
            "https://de.jackery.com/pages/user-guides",
        ):
            self.assertIn(value, self.html)
        for forbidden in (
            "JE-2000F", "JE-2000E", "Jackery Explorer 2000 ",
            "4000 cycles", "4400 W", "USB-C 100W", "2011/65/EU",
        ):
            self.assertNotIn(forbidden, self.html)

    def test_illustration_files_match_recipe_and_manifest(self) -> None:
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        recipe = json.loads((ROOT / manifest["recipe"]).read_text(encoding="utf-8"))
        self.assertEqual(21, len(manifest["illustrations"]))
        self.assertEqual(21 * len(MANUAL_LOCALES), len(recipe["assets"]))
        output_hashes = {
            output["path"]: output["expected_sha256"]
            for asset in recipe["assets"] for output in asset["outputs"]
        }
        app_panels = {"download_panel", "control_panel", "connect_result_panel"}
        for asset in recipe["assets"]:
            if asset["asset_key"].rsplit("/", 1)[-1] in app_panels:
                # App screens and the QR download panel stay quarantined under the
                # App/QR/URL/localized-UI gate; the manifests are their only route.
                self.assertFalse(asset["build_eligible"])
                self.assertTrue(asset["visual_review_required"])
                self.assertEqual("quarantine", asset["gate"]["status"])
                self.assertIn("app-ui", asset["risk_tags"])
                continue
            self.assertTrue(asset["build_eligible"])
            self.assertFalse(asset["visual_review_required"])
            self.assertEqual("approved", asset["gate"]["status"])
        self.assertEqual(
            len(app_panels) * len(MANUAL_LOCALES),
            sum(asset["gate"]["status"] == "quarantine" for asset in recipe["assets"]),
        )
        for illustration in manifest["illustrations"]:
            path = ILLUSTRATIONS.parent / illustration["path"]
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(illustration["sha256"], actual)
            self.assertEqual(actual, output_hashes[path.relative_to(ROOT).as_posix()])

    def test_every_locale_binds_its_own_finished_panels(self) -> None:
        """每种语言都有整套成品整图，且互不共用文件。"""
        recipe_assets = json.loads(
            (ROOT / json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))["recipe"])
            .read_text(encoding="utf-8")
        )["assets"]
        by_locale: dict[str, dict[str, str]] = {}
        for asset in recipe_assets:
            locale, = asset["scope"]["locales"]
            self.assertEqual(["JE-1000H"], asset["scope"]["models"])
            self.assertEqual(["EU"], asset["scope"]["regions"])
            output, = asset["outputs"]
            by_locale.setdefault(locale, {})[Path(output["path"]).name] = \
                output["expected_sha256"]
        self.assertEqual(set(MANUAL_LOCALES), set(by_locale))
        english = by_locale["en"]
        english_entries = json.loads(
            (ROOT / "docs/renderers/web/je1000h_eu_en_illustrations.json")
            .read_text(encoding="utf-8")
        )["illustrations"]
        for locale in MANUAL_LOCALES:
            self.assertEqual(set(english), set(by_locale[locale]), locale)
            illustrations = ROOT / f"docs/renderers/web/je1000h_eu_{locale}_illustrations.json"
            manifest = json.loads(illustrations.read_text(encoding="utf-8"))
            self.assertEqual(locale, manifest["language"])
            bound = {Path(entry["path"]).stem for entry in manifest["illustrations"]}
            # 每种语言都绑满 21 张：JE-1000H 现在有按语言的 07_extra_battery 模板，
            # battery_pack 不再缺宿主。任何语言掉一张这里就会红。
            self.assertEqual(
                {Path(e["path"]).stem for e in english_entries}, bound, locale
            )
            self.assertEqual(21, len(manifest["illustrations"]), locale)
            for entry in manifest["illustrations"]:
                self.assertEqual(
                    by_locale[locale][Path(entry["path"]).name], entry["sha256"]
                )
                self.assertEqual(
                    entry["sha256"],
                    hashlib.sha256(
                        (illustrations.parent / entry["path"]).read_bytes()
                    ).hexdigest(),
                )
            if locale != "en":
                # 各语块版式不同（英规插座 vs 欧规插座、本地化标注），成品图必须各自独立
                shared = {
                    name for name, digest in by_locale[locale].items()
                    if english[name] == digest
                }
                self.assertEqual(set(), shared, f"{locale} reuses English artwork")

    def test_public_ir_replay_and_tamper_detection(self) -> None:
        self.assertEqual(18, len(render_document_fragments(self.ir, package_root=self.package)))
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
