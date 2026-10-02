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
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup
from PIL import Image
import yaml

from tools.manual_ir import read_manual_ir
from tools.skeleton_resolve import (
    load_blueprint,
    load_region_profile,
    load_slot_templates,
    resolve_plan,
)
from tools.web_document_ir import render_document_fragments


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "config.bp-eu-en-web.yaml"
FORMAL_SOURCE = ROOT / "manual_sources" / "JBP-3600A" / "EU" / "en"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"
PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "eu-en-web.yaml"
MANIFEST = ROOT / "docs" / "manifests" / "manual_bp-eu-en-web.yaml"
ILLUSTRATIONS = ROOT / "docs" / "renderers" / "web" / "jbp3600a_eu_en_illustrations.json"
FROZEN_BP_EU_MANIFEST_SHA256 = (
    "e7908e1060bc8a61a0e5eff9c92a41e8158bf70afba5286c20266790050b18cd"
)


class Jbp3600aEuEnWebTests(unittest.TestCase):
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
                "JBP-3600A",
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
            raise AssertionError("JBP-3600A formal-source Web build failed:\n" + result.stdout + result.stderr)
        cls.package = (
            cls.staging
            / "docs"
            / "_build"
            / "JBP-3600A"
            / "EU"
            / "en"
            / "md"
        )
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_exact_target_uses_bp_intl_single_english_profile(self) -> None:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual([{"model": "JBP-3600A", "region": "EU"}], config["build"]["targets"])
        self.assertEqual(["en"], config["build"]["languages"])
        self.assertEqual("BP", config["build"]["skeleton_family"])
        self.assertEqual(
            "Jackery Explorer 3600 Plus",
            config["build"]["rst_substitutions"]["BP_HOST_PRODUCT_NAME"],
        )

        skeleton = ROOT / "docs" / "manifests" / "skeletons" / "bp-intl"
        blueprint = load_blueprint(skeleton / "blueprint.yaml")
        slots = load_slot_templates(skeleton / "slot_templates.yaml", blueprint)
        profile = load_region_profile(PROFILE, blueprint)
        resolved = resolve_plan(blueprint, slots, profile, manifest_id="manual_bp_eu_en_web")
        checked_in = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(checked_in, resolved)
        self.assertEqual(["en"], profile["language_set"])

    def test_formal_git_source_contains_only_target_values(self) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8-sig", newline="") as handle:
            spec_rows = [
                row for row in csv.DictReader(handle)
                if row["document_key"] == "JBP-3600A_EU"
            ]
        values = {row["Row_key"]: row["Value_source"] for row in spec_rows}
        self.assertEqual("Jackery Battery Pack 3600", values["product_name"])
        self.assertEqual("80 Ah/44.8 V DC (3584 Wh)", values["capacity"])
        self.assertEqual("36.4V-50.4V⎓100A Max", values["dc_expansion_port"])
        self.assertTrue(all(row["Model"] == "JBP-3600A" for row in spec_rows))
        self.assertNotIn("Jackery Battery Pack 2000", "\n".join(values.values()))

        source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("auto-manual-git-source/v1", source_manifest["schema_version"])
        self.assertEqual("operator-designated-native-artwork-git-input", source_manifest["source_role"])
        self.assertEqual(
            "manual_sources/JBP-3600A/EU/en/phase2",
            source_manifest["data_root"],
        )
        self.assertFalse(source_manifest["live_bitable_dependency"])
        for binding in [source_manifest["asset_recipe"],
                        source_manifest["web_illustration_manifest"],
                        *source_manifest["supplemental_asset_recipes"],
                        *source_manifest["shared_symbol_assets"]]:
            self.assertEqual(binding["sha256"],
                             hashlib.sha256((ROOT / binding["path"]).read_bytes()).hexdigest())
        for record in source_manifest["files"]:
            path = FORMAL_SOURCE / record["path"]
            data = path.read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())
        inventory = json.dumps(
            source_manifest["files"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        self.assertEqual(
            source_manifest["files_inventory_sha256"],
            hashlib.sha256(inventory).hexdigest(),
        )

    def test_packaged_symbols_reuse_transparent_shared_assets(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        expected = {entry["sha256"] for entry in manifest["shared_symbol_assets"]}
        soup = BeautifulSoup(self.html, "html.parser")
        images = soup.select(".hb-symbol-art")
        self.assertEqual(8, len(images))
        actual = set()
        for image in images:
            path = self.package / unquote(urlparse(image["src"]).path)
            self.assertTrue(path.resolve().is_relative_to(self.package.resolve()))
            actual.add(hashlib.sha256(path.read_bytes()).hexdigest())
            with Image.open(path) as icon:
                self.assertEqual("RGBA", icon.mode)
                alpha = icon.getchannel("A")
                self.assertEqual((0, 255), alpha.getextrema())
                for corner in ((0, 0), (icon.width - 1, 0),
                               (0, icon.height - 1), (icon.width - 1, icon.height - 1)):
                    self.assertEqual(0, alpha.getpixel(corner))
        self.assertEqual(expected, actual)

    def test_web_output_has_real_components_and_finished_target_art(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(3, len(soup.select(".hb-inbox-card")))
        self.assertIsNone(soup.select_one(".hb-inbox-tip"))
        self.assertEqual(
            {"inbox_unit_clean.png", "inbox_cable_clean.png", "inbox_manual_clean.png"},
            {Path(image["src"]).name for image in soup.select(".hb-inbox-art")},
        )
        self.assertIsNotNone(soup.select_one("table.lcd-text-only"))
        self.assertIsNotNone(soup.select_one('[data-component-id="HB-TABLE-TROUBLESHOOTING"]'))
        # The print (PDF page 11) sets one INPUT/OUTPUT PORTS table, so the
        # specification page has three compositions, not four.
        self.assertEqual(3, len(soup.select(".hb-spec-table-composition")))
        self.assertGreaterEqual(len(soup.select(".manual-finished-illustration")), 7)
        # The LCD adapter owns its image class; assert every finished asset by
        # its content-addressed URL, not only standalone figure CSS classes.
        provenance = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        image_sources = [str(image.get("src", "")) for image in soup.select("img")]
        for entry in provenance["illustrations"]:
            self.assertTrue(any(entry["sha256"] in src for src in image_sources), entry["path"])
        coverage = self.ir.metadata["web_figure_coverage"]
        self.assertEqual(9, len(coverage["slots"]))
        self.assertEqual({"finished-panel", "base-art-live-copy"},
                         {slot["status"] for slot in coverage["slots"]})
        self.assertIn("Jackery Explorer 3600 Plus", self.html)
        self.assertIn("F6-F9, FA, FC, FE", self.html)
        self.assertNotIn("Jackery Battery Pack 2000", self.html)

    def test_overview_headings_and_lcd_legend_stay_native(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        headings = [h.get_text(" ", strip=True) for h in soup.select("h1,h2,h3,h4")]
        self.assertEqual(1, headings.count("FRONT VIEW"))
        self.assertEqual(1, headings.count("LEFT SIDE VIEW"))
        for stem in ("overview_front", "overview_left", "lcd_annotated", "power_native", "lcd_control_clean", "clearance_native", "stacking_clean", "locking_native"):
            images = soup.select(f'img[data-web-finished-panel-path$="/{stem}.png"]')
            self.assertEqual(1, len(images), stem)
        self.assertFalse(any(
            t.get_text(" ", strip=True) == "POWER button LCD" for t in soup.select("table")
        ))
        self.assertFalse(any(
            t.get_text(" ", strip=True).startswith("Handle DC Expansion Port A")
            for t in soup.select("table")
        ))
        lcd = soup.select_one("table.lcd-text-only")
        self.assertIsNotNone(lcd)
        self.assertEqual(2, len(lcd.select("tbody tr")))
        self.assertFalse(lcd.select("img"))
        self.assertIn("Power Percentage/Fault Code", lcd.get_text())
        self.assertIn("Charging Indicator", lcd.get_text())
        self.assertIn("FF code", lcd.get_text())
        self.assertEqual(1, headings.count("POWER ON/OFF"))
        self.assertEqual(1, headings.count("LCD DISPLAY ON/OFF"))
        text = soup.get_text(" ", strip=True)
        self.assertEqual(1, text.count("When you press the main POWER button"))
        self.assertEqual(1, text.count("The product will automatically shut down"))
        connection_tables = soup.select("body > table.manual-callout-table")
        connection_text = " ".join(t.get_text(" ", strip=True) for t in connection_tables)
        self.assertEqual(1, connection_text.count("Ensure all products are powered off before connecting"))
        self.assertEqual(1, text.count("Please do not stack the product on the top"))
        self.assertFalse(any(
            block.get_text(" ", strip=True) == "On Press once Off Press and hold for 3 seconds"
            for block in soup.select(".line-block")
        ))

    def test_native_labels_and_css_clock_survive_component_binding(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        operation = soup.select_one('[data-web-replace-key="operation.main-power"]')
        self.assertIsNotNone(operation)
        self.assertEqual(["On", "Off"], [item.get_text(strip=True) for item in
                                        operation.select(".hb-operation-step-label")])
        duration = operation.select_one('.hb-operation-duration[data-duration-icon="clock"]')
        self.assertEqual("3s", duration.get_text(strip=True))
        self.assertFalse(duration.select("img,svg"))
        for key, labels in (
            ("reference.clearance", ["≥0.66 ft (≈200 mm)"] * 2),
            ("reference.locking", ["Lock", "Unlock", "1", "2", "1", "2"]),
        ):
            figure = soup.select_one(f'[data-web-replace-key="{key}"]')
            self.assertEqual(labels, [item.get_text(strip=True) for item in
                                     figure.select(".hb-reference-live-label")])
        slots = {item["slot_id"]: item["status"]
                 for item in self.ir.metadata["web_figure_coverage"]["slots"]}
        for key in ("operation.main-power", "reference.clearance", "reference.locking"):
            self.assertEqual("base-art-live-copy", slots[key])
        self.assertFalse(soup.select(".hb-auto-resume-table,.hb-key-combination-table"))

    def test_warranty_uses_shared_native_components(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(1, len(soup.select(".hb-warranty-intro-panel")))
        self.assertEqual(5, len(soup.select(".hb-warranty-card")))
        self.assertEqual(["3", "2"], [
            badge.get_text(strip=True) for badge in soup.select(".hb-warranty-year-badge")
        ])
        self.assertEqual(["Standard Warranty", "Extended Warranty"], [
            label.get_text(strip=True) for label in soup.select(".hb-warranty-period-label")
        ])
        self.assertIn("Jackery will repair or replace", soup.get_text())

    def test_public_ir_cold_replay_reads_no_rst_or_csv(self) -> None:
        script = r'''
from pathlib import Path
from unittest.mock import patch
import sys
original = Path.open
def guarded(path, *args, **kwargs):
    if path.suffix in {".rst", ".csv"}:
        raise AssertionError("source read during replay: " + str(path))
    return original(path, *args, **kwargs)
with patch.object(Path, "open", guarded):
    from tools.manual_ir import read_manual_ir
    from tools.web_document_ir import render_document_fragments
    package = Path(sys.argv[1])
    result = render_document_fragments(
        read_manual_ir(package / "manual.ir.json"), package_root=package
    )
    assert len(result) == 15
    markup = "\n".join(result)
    assert 'data-duration-icon="clock"' in markup
    assert 'data-web-replace-key="reference.locking"' in markup
'''
        subprocess.run(
            [sys.executable, "-c", script, str(self.package)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_public_ir_rejects_changed_packaged_asset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            copied = Path(td) / "package"
            shutil.copytree(self.package, copied)
            ir = read_manual_ir(copied / "manual.ir.json")
            relative = next(iter(ir.metadata["asset_sha256"]))
            (copied / relative).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "asset missing or changed"):
                render_document_fragments(ir, package_root=copied)

    def test_illustration_manifest_and_files_are_hash_locked(self) -> None:
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        self.assertEqual(("JBP-3600A", "EU", "en"), (
            manifest["model"], manifest["region"], manifest["language"]
        ))
        self.assertEqual(13, len(manifest["illustrations"]))
        for illustration in manifest["illustrations"]:
            path = ILLUSTRATIONS.parent / illustration["path"]
            self.assertEqual(
                illustration["sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )

    def test_existing_bp_eu_manifest_remains_frozen(self) -> None:
        existing = ROOT / "docs" / "manifests" / "manual_bp-eu.yaml"
        self.assertEqual(
            FROZEN_BP_EU_MANIFEST_SHA256,
            hashlib.sha256(existing.read_bytes()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
