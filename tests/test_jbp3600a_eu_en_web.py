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
FIXTURE = ROOT / "tests" / "fixtures" / "phase2"
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
                str(FIXTURE),
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
            raise AssertionError("JBP-3600A Web fixture build failed:\n" + result.stdout + result.stderr)
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

    def test_source_backed_fixture_contains_only_target_values(self) -> None:
        with (FIXTURE / "Spec_Master.csv").open(encoding="utf-8-sig", newline="") as handle:
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

    def test_web_output_has_real_components_and_finished_target_art(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(3, len(soup.select(".hb-inbox-card")))
        self.assertIsNone(soup.select_one(".hb-inbox-tip"))
        self.assertIsNotNone(soup.select_one('[data-component-id="HB-TABLE-LCD-ICON"]'))
        self.assertIsNotNone(soup.select_one('[data-component-id="HB-TABLE-TROUBLESHOOTING"]'))
        self.assertEqual(4, len(soup.select(".hb-spec-table-composition")))
        self.assertGreaterEqual(len(soup.select(".manual-finished-illustration")), 7)
        self.assertIn("Jackery Explorer 3600 Plus", self.html)
        self.assertIn("F6-F9, FA, FC, FE", self.html)
        self.assertNotIn("Jackery Battery Pack 2000", self.html)

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
        self.assertEqual(8, len(manifest["illustrations"]))
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
