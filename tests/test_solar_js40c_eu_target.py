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
CONFIG = ROOT / "configs" / "config.solar-eu-en.yaml"
SOURCE_ROOT = ROOT / "data" / "manual_sources" / "JS-40C" / "EU" / "en" / "2026-08-30"
DATA_ROOT = SOURCE_ROOT / "phase2"
SOURCE_MANIFEST = SOURCE_ROOT / "source_manifest.json"
RECIPE = ROOT / "data" / "asset_recipes" / "manual_js40c_eu_en_web.json"
ILLUSTRATIONS = ROOT / "docs" / "renderers" / "web" / "js40c_eu_en_illustrations.json"
MANIFEST = ROOT / "docs" / "manifests" / "manual_solar-eu-en-JS-40C.yaml"
SKELETON = ROOT / "docs" / "manifests" / "skeletons" / "solar-intl"
PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "solar-eu-en.yaml"
PRODUCT_PLAN = ROOT / "docs" / "manifests" / "product_plans" / "js40c_eu.yaml"


class SolarJs40cEuTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.staging = Path(cls.temp.name) / "staging"
        fake_bin = Path(cls.temp.name) / "bin"
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
                "JS-40C",
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
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise AssertionError(
                "JS-40C frozen-source build failed:\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        cls.package = cls.staging / "docs" / "_build" / "JS-40C" / "EU" / "en" / "md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.html, "html.parser")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_product_plan_selects_js40c_storage_shape(self) -> None:
        blueprint = load_blueprint(SKELETON / "blueprint.yaml")
        slots, slot_profiles = load_slot_template_catalog(
            SKELETON / "slot_templates.yaml", blueprint
        )
        profile = load_region_profile(PROFILE, blueprint)
        product_plan = load_product_plan(PRODUCT_PLAN, blueprint)
        plan = resolve_plan(
            blueprint,
            slots,
            profile,
            manifest_id="manual_solar_eu_en_js40c",
            product_plan=product_plan,
            slot_template_profiles=slot_profiles,
        )
        self.assertEqual(plan, yaml.safe_load(MANIFEST.read_text(encoding="utf-8")))
        self.assertEqual(
            [
                "safety_tips_en",
                "box_contents_en",
                "product_views_en",
                "charging_connections_en",
                "angle_and_device_en",
                "storage_en",
                "specifications_en",
                "warranty_en",
            ],
            [page["slot_id"] for page in plan["pages"]],
        )
        serialized = json.dumps(plan)
        for forbidden in ("unfolding", "folding", "lcd", "ups", "app"):
            self.assertNotIn(forbidden, serialized.casefold())

    def test_shared_family_config_resolves_both_solar_targets(self) -> None:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(
            [
                {"model": "JS-100I", "region": "EU"},
                {"model": "JS-40C", "region": "EU"},
                {"model": "JS-100F", "region": "EU"},
                {"model": "JS-200E", "region": "EU"},
            ],
            config["build"]["targets"],
        )
        self.assertEqual(
            "docs/manifests/manual_solar-eu-en-JS-40C.yaml",
            config["paths"]["page_manifests"]["JS-40C_EU"],
        )
        self.assertEqual(
            "docs/renderers/web/js40c_eu_en_illustrations.json",
            config["paths"]["web_illustration_manifests"]["JS-40C_EU"],
        )

    def test_source_snapshot_and_exact_spec_values_are_pinned(self) -> None:
        payload = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("auto-manual-git-source-snapshot/v1", payload["schema_version"])
        self.assertEqual("1OUQt6g91M", payload["authority"]["dingtalk_record"])
        self.assertEqual(
            "c5963d37311614f9fc5c9ae40c4da74a71cc53da8e36a92e60a7ff3f25854df9",
            payload["authority"]["source_master_sha256"],
        )
        inventory = []
        for entry in payload["files"]:
            source = SOURCE_ROOT / entry["path"]
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(entry["sha256"], digest, entry["path"])
            inventory.append(f"{digest}  {source.name}\n")
        snapshot = hashlib.sha256("".join(sorted(inventory)).encode()).hexdigest()
        self.assertEqual(payload["build_input"]["snapshot_sha256"], snapshot)

        with (DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        values = {row["Row_key"]: row["Value_source"] for row in rows}
        self.assertEqual("STC*: 42 W ± 5% / BNPI*: 47 W ± 5%", values["maximum_power"])
        self.assertEqual("STC*: 1.9 A ± 5% / BNPI*: 2.12 A ± 5%", values["maximum_power_current"])
        self.assertEqual("IEC TS 63163 Consumer Product Category 1", values["photovoltaic_consumer_products"])
        self.assertEqual("5 V⎓3 A", values["usb_c_output"])

    def test_recipe_registry_and_illustration_hashes_match(self) -> None:
        recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
        illustrations = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        self.assertEqual(18, len(recipe["assets"]))
        self.assertEqual(18, len(illustrations["illustrations"]))
        self.assertTrue(all(asset["gate"]["status"] == "approved" for asset in recipe["assets"]))
        registry = load_registry(ROOT / "data" / "asset_registry.csv")
        for asset in recipe["assets"]:
            output = asset["outputs"][0]
            resolution = resolve_asset(
                registry,
                repo_root=ROOT,
                asset_key=asset["asset_key"],
                format_name="png",
                language="en",
                model="JS-40C",
                region="EU",
            )
            file = ROOT / resolution.path
            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            self.assertEqual(output["expected_sha256"], digest)
            self.assertEqual(output["expected_sha256"], resolution.declared_hash)

    def test_runtime_embeds_shared_semantic_components_and_finished_art(self) -> None:
        self.assertEqual("manual-ir/v2", self.ir.schema_version)
        self.assertEqual(8, len(self.ir.pages))
        self.assertEqual(7, len(self.soup.select(".hb-inbox-card")))
        self.assertEqual(3, len(self.soup.select(".hb-spec-table-composition")))
        self.assertEqual(1, len(self.soup.select('[data-component-id="HB-WARRANTY-YEARS"]')))
        self.assertEqual(2, len(self.soup.select('[data-component-id="HB-WARRANTY-SECTION"]')))
        self.assertEqual(18, len(self.soup.select("img.manual-finished-illustration")))
        text = self.soup.get_text(" ", strip=True)
        for required in (
            "Jackery SolarSaga 40 Air",
            "Multifunctional Solar Charging Cable (1.8 m)",
            "DC8020 to USB-C Adapter Cable (17 cm)",
            "SOLAR PANEL STORAGE",
            "IEC TS 63163 Consumer Product Category 1",
            "1 YEAR",
            "2 YEARS",
        ):
            self.assertIn(required, text)
        for forbidden in ("JS-100I", "SolarSaga 100 Air", "LCD DISPLAY", "UPS MODE", "APP CONTROL"):
            self.assertNotIn(forbidden, text.upper() if forbidden.isupper() else text)

    def test_public_ir_cold_replays_without_source_or_contract_reads(self) -> None:
        relocated = Path(self.temp.name) / "relocated"
        shutil.copytree(self.package, relocated)
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
    rendered = render_document_fragments(read_manual_ir(package / "manual.ir.json"), package_root=package)
    assert len(rendered) == 8
    assert "Jackery SolarSaga 40 Air" in "".join(rendered)
'''
        subprocess.run(
            [sys.executable, "-c", script, str(relocated)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_public_ir_rejects_tampered_packaged_art(self) -> None:
        relocated = Path(self.temp.name) / "tampered"
        shutil.copytree(self.package, relocated)
        ir = read_manual_ir(relocated / "manual.ir.json")
        (relocated / ir.asset_refs[0]).write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "asset missing or changed"):
            render_document_fragments(ir, package_root=relocated)


if __name__ == "__main__":
    unittest.main()
