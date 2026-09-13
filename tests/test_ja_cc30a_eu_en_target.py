from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from tools.asset_registry import load_registry, resolve_asset
from tools.manual_ir import read_manual_ir
from tools.skeleton_resolve import (
    load_blueprint,
    load_product_plan,
    load_region_profile,
    load_slot_template_catalog,
    resolve_plan,
)
from tools.web_document_ir import render_document_fragments


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "config.charger-eu-en.yaml"
FIXTURE = ROOT / "data" / "manual_sources" / "ja_cc30a_eu_en"
RECIPE = ROOT / "data" / "asset_recipes" / "manual_ja_cc30a_eu_en_web.json"
ILLUSTRATIONS = ROOT / "docs" / "renderers" / "web" / "charger_eu_en_JA-CC30A_illustrations.json"
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "charger-intl"
REGION_PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "charger-eu-en.yaml"
PRODUCT_PLAN = ROOT / "docs" / "manifests" / "product_plans" / "ja_cc30a_eu.yaml"
SOURCE_MANIFEST = FIXTURE / "source_manifest.json"


class JaCc30aEuEnTargetTests(unittest.TestCase):
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
            [sys.executable, str(ROOT / "build.py"), "md", "--config", str(CONFIG),
             "--model", "JA-CC30A", "--region", "EU", "--lang", "en",
             "--data-root", str(FIXTURE), "--staging-root", str(cls.staging)],
            cwd=ROOT, env=env, check=False, capture_output=True, text=True,
        )
        if result.returncode:
            raise AssertionError("JA-CC30A Web fixture build failed:\n" + result.stdout + result.stderr)
        cls.package = cls.staging / "docs" / "_build" / "JA-CC30A" / "EU" / "en" / "md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_product_plan_selects_only_powered_accessory_slots(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slots, profiles = load_slot_template_catalog(SKELETON_DIR / "slot_templates.yaml", blueprint)
        plan = resolve_plan(
            blueprint, slots, load_region_profile(REGION_PROFILE, blueprint),
            manifest_id="manual_charger_eu_en_ja_cc30a",
            product_plan=load_product_plan(PRODUCT_PLAN, blueprint),
            slot_template_profiles=profiles,
        )
        self.assertEqual(
            ["disclaimer_en", "product_overview_en", "warning_en", "specifications_en",
             "box_contents_en", "using_product_en", "maintenance_en", "warranty_en", "legal_tail"],
            [page["slot_id"] for page in plan["pages"]],
        )
        serialized = json.dumps(plan).casefold()
        for forbidden in ("lcd", "ups", "app"):
            self.assertNotIn(forbidden, serialized)

    def test_spec_source_preserves_the_ai_values(self) -> None:
        with (FIXTURE / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(9, len(rows))
        self.assertEqual({"JA-CC30A_EU"}, {row["document_key"] for row in rows})
        values = {row["Row_label_source"]: row["Value_source"] for row in rows}
        self.assertEqual("Jackery Extreme Guard Carrying Bag (L Size)", values["Product Name"])
        self.assertEqual("−30°C to 85°C", values["Storage Temperature of Heating Module"])
        self.assertEqual("−20°C to 45°C", values["Operating Temperature of Heating Module"])
        self.assertEqual("20V⎓ 2.5A", values["Heating Module Input"])
        self.assertEqual("50W", values["Heating Module Power"])

    def test_recipe_registry_and_manifest_hashes_match(self) -> None:
        recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        source_hash = "0eb2b7ba99e9b5b941f147f3b3b60f89229b007af77fc80e7dc9451d7aaa50d3"
        self.assertEqual(source_hash, recipe["source"]["expected_sha256"])
        self.assertEqual(source_hash, manifest["source_artwork_sha256"])
        self.assertEqual(1, recipe["source"]["expected_page_count"])
        self.assertEqual(8, len(recipe["assets"]))
        self.assertEqual(8, len(manifest["illustrations"]))
        self.assertTrue(all(asset["build_eligible"] for asset in recipe["assets"]))
        self.assertTrue(all(asset["gate"]["status"] == "approved" for asset in recipe["assets"]))

        registry = load_registry(ROOT / "data" / "asset_registry.csv")
        for asset in recipe["assets"]:
            output = asset["outputs"][0]
            resolution = resolve_asset(
                registry, repo_root=ROOT, asset_key=asset["asset_key"],
                format_name="png", language="en", model="JA-CC30A", region="EU",
            )
            path = ROOT / resolution.path
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(output["expected_sha256"], resolution.declared_hash)
            self.assertEqual(output["expected_sha256"], digest)

    def test_source_snapshot_locks_ai_and_git_inputs(self) -> None:
        payload = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("auto-manual-git-source-snapshot/v1", payload["schema_version"])
        self.assertEqual("Li32wwM6MY", payload["authority"]["record_id"])
        self.assertEqual(
            "0eb2b7ba99e9b5b941f147f3b3b60f89229b007af77fc80e7dc9451d7aaa50d3",
            hashlib.sha256((FIXTURE / "JA-CC30A-eu-source.ai").read_bytes()).hexdigest(),
        )
        for entry in payload["files"]:
            self.assertEqual(
                entry["sha256"], hashlib.sha256((FIXTURE / entry["path"]).read_bytes()).hexdigest()
            )
        self.assertEqual(payload["assets"]["recipe_sha256"], hashlib.sha256(RECIPE.read_bytes()).hexdigest())
        self.assertEqual(
            payload["assets"]["illustration_manifest_sha256"],
            hashlib.sha256(ILLUSTRATIONS.read_bytes()).hexdigest(),
        )

    def test_runtime_is_semantic_and_uses_complete_finished_panels(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(9, len(self.ir.pages))
        self.assertEqual(3, len(soup.select(".hb-inbox-card")))
        self.assertEqual(1, len(soup.select(".hb-spec-table-composition")))
        self.assertEqual(8, len(soup.select(".manual-finished-illustration")))
        self.assertEqual(8, len(soup.find_all("img")))
        self.assertEqual("whole-document-components/v1", self.ir.metadata["projection"])
        text = soup.get_text(" ", strip=True)
        for required in (
            "Jackery Extreme Guard Carrying Bag (L Size)", "−30°C to 85°C",
            "20V⎓ 2.5A", "CLEANING AND MAINTENANCE", "2-YEAR LIMITED WARRANTY",
        ):
            self.assertIn(required, text)
        for forbidden in ("LCD DISPLAY", "UPS MODE", "APP CONTROL"):
            self.assertNotIn(forbidden, text.upper())

    def test_public_ir_cold_replay_and_asset_tamper_rejection(self) -> None:
        script = r'''
from pathlib import Path
from unittest.mock import patch
import sys
original = Path.open
def guarded(path, *args, **kwargs):
    if path.suffix in {".rst", ".csv"} or "contracts" in path.parts:
        raise AssertionError("source read during replay: " + str(path))
    return original(path, *args, **kwargs)
with patch.object(Path, "open", guarded):
    from tools.manual_ir import read_manual_ir
    from tools.web_document_ir import render_document_fragments
    package = Path(sys.argv[1])
    result = render_document_fragments(read_manual_ir(package / "manual.ir.json"), package_root=package)
    assert len(result) == 9
'''
        subprocess.run([sys.executable, "-c", script, str(self.package)], cwd=ROOT, check=True)
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
