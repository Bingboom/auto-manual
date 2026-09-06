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
CONFIG = ROOT / "configs" / "config.solar-eu-en.yaml"
MANIFEST = ROOT / "docs" / "manifests" / "manual_solar-eu-en.yaml"
ILLUSTRATIONS = ROOT / "docs" / "renderers" / "web" / "js100i_eu_en_illustrations.json"
DATA_ROOT = ROOT / "tests" / "fixtures" / "js100i_eu_en_phase2"
SKELETON = ROOT / "docs" / "manifests" / "skeletons" / "solar-intl"
PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "solar-eu-en.yaml"


class SolarJs100iEuTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.staging = Path(cls.temp.name) / "staging"
        env = dict(os.environ)
        env["AUTO_MANUAL_PRESENTATION_PROFILE"] = "web"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "build.py"),
                "md",
                "--config",
                str(CONFIG),
                "--model",
                "JS-100I",
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
            check=True,
            capture_output=True,
            text=True,
        )
        cls.package = cls.staging / "docs" / "_build" / "JS-100I" / "EU" / "en" / "md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.markdown = (cls.package / "manual_js100i_eu_en.md").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_category_skeleton_resolves_exact_web_body_order(self) -> None:
        blueprint = load_blueprint(SKELETON / "blueprint.yaml")
        slots = load_slot_templates(SKELETON / "slot_templates.yaml", blueprint)
        profile = load_region_profile(PROFILE, blueprint)
        plan = resolve_plan(blueprint, slots, profile, manifest_id="manual_solar_eu_en")

        self.assertEqual("solar-intl", blueprint["skeleton_id"])
        self.assertEqual(
            [
                "safety_tips_en",
                "box_contents_en",
                "product_views_en",
                "unfolding_en",
                "folding_en",
                "charging_connections_en",
                "angle_and_device_en",
                "specifications_en",
                "warranty_en",
            ],
            [page["slot_id"] for page in plan["pages"]],
        )
        committed = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(plan, committed)

    def test_config_declares_safety_as_web_entry_and_true_target(self) -> None:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual([{"model": "JS-100I", "region": "EU"}], config["build"]["targets"])
        self.assertIn("safety_tips*", config["build"]["web_entry_source_patterns"])
        self.assertEqual(str(MANIFEST.relative_to(ROOT)), config["paths"]["page_manifest"])

    def test_build_starts_at_safety_and_has_no_power_station_only_chapters(self) -> None:
        self.assertEqual("manual-ir/v2", self.ir.schema_version)
        self.assertEqual("JS-100I", self.ir.model)
        self.assertEqual("EU", self.ir.region)
        self.assertEqual("en", self.ir.language)
        self.assertEqual("safety_tips_en.rst", self.ir.pages[0].page_id)
        page_ids = [page.page_id for page in self.ir.pages]
        self.assertEqual(9, len(page_ids))
        self.assertFalse(any("cover" in page or "toc" in page for page in page_ids))
        for forbidden in ("LCD DISPLAY", "UPS MODE", "APP CONTROL"):
            self.assertNotIn(forbidden, self.markdown.upper())

    def test_complete_copy_components_and_five_item_inbox_are_present(self) -> None:
        for required in (
            "SAFETY TIPS",
            "WHAT'S IN THE BOX",
            'data-card-count="5"',
            'data-inbox-variant="responsive-card-grid"',
            "DC8020--DC7909 Adapter",
            "SUN ANGLE INDICATOR",
            "STC*: 100 W ± 5% / BNPI*: 110 W ± 5%",
            "IEC TS 63163 Consumer Product Category 2",
            "2 YEARS --- Extended Warranty",
            "hello.eu@jackery.com",
        ):
            self.assertIn(required, self.markdown)
        self.assertEqual(13, len(self.ir.asset_refs))
        provenance = self.ir.metadata["illustration_provenance"]
        self.assertEqual("web-illustrations/v1", provenance["schema_version"])
        self.assertEqual(13, len(provenance["illustrations"]))

    def test_illustration_manifest_binds_target_source_and_exact_asset_hashes(self) -> None:
        payload = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        self.assertEqual(
            ("JS-100I", "EU", "en"),
            (payload["model"], payload["region"], payload["language"]),
        )
        self.assertEqual(
            "cec27af653d9f5da11d641e2431ddc0b71ced186bbadfd9594fa8cd9c96e1596",
            payload["source_pdf_sha256"],
        )
        self.assertEqual(
            "5d7ded6ba7810505cfb4c91b128a71cbef16a0e11aae720cdbd887559224b96a",
            payload["source_master_sha256"],
        )
        for entry in payload["illustrations"]:
            asset = ILLUSTRATIONS.parent / entry["path"]
            self.assertEqual(entry["sha256"], hashlib.sha256(asset.read_bytes()).hexdigest())

    def test_public_ir_cold_replays_without_rst_or_csv_reads(self) -> None:
        relocated = Path(self.temp.name) / "relocated"
        shutil.copytree(self.package, relocated)
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
    rendered = render_document_fragments(
        read_manual_ir(package / "manual.ir.json"), package_root=package
    )
    assert len(rendered) == 9
    assert "Jackery SolarSaga 100 Air" in "".join(rendered)
'''
        subprocess.run(
            [sys.executable, "-c", script, str(relocated)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_public_ir_fails_closed_when_packaged_art_changes(self) -> None:
        relocated = Path(self.temp.name) / "tampered"
        shutil.copytree(self.package, relocated)
        ir = read_manual_ir(relocated / "manual.ir.json")
        (relocated / ir.asset_refs[0]).write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "asset missing or changed"):
            render_document_fragments(ir, package_root=relocated)


if __name__ == "__main__":
    unittest.main()
