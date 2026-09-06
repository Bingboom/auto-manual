from __future__ import annotations

import csv
import hashlib
import json
import unittest
from pathlib import Path

import yaml

from tools.asset_registry import load_registry, resolve_asset
from tools.skeleton_resolve import (
    load_blueprint,
    load_region_profile,
    load_slot_templates,
    resolve_plan,
)


ROOT = Path(__file__).resolve().parents[1]
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "charger-intl"
PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "charger-eu-en.yaml"
CONFIG = ROOT / "configs" / "config.charger-eu-en.yaml"
FIXTURE = ROOT / "tests" / "fixtures" / "ja_ad01a_eu_en"
ASSET_RECIPE = ROOT / "data" / "asset_recipes" / "manual_ja_ad01a_eu_en_web.json"
ILLUSTRATION_MANIFEST = (
    ROOT / "docs" / "renderers" / "web" / "ja_ad01a_eu_en_illustrations.json"
)


class JaAd01aEuEnTargetTests(unittest.TestCase):
    def test_charger_skeleton_is_compact_and_target_agnostic(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slots = load_slot_templates(SKELETON_DIR / "slot_templates.yaml", blueprint)
        profile = load_region_profile(PROFILE, blueprint)
        plan = resolve_plan(
            blueprint,
            slots,
            profile,
            manifest_id="manual_charger_eu_en",
        )

        slot_ids = [page["slot_id"] for page in plan["pages"]]
        self.assertEqual(
            [
                "box_contents_en",
                "product_overview_en",
                "specifications_en",
                "using_product_en",
                "warning_en",
                "warranty_en",
                "legal_tail",
            ],
            slot_ids,
        )
        self.assertEqual("CHARGER", blueprint["skeleton_family"])
        self.assertFalse(any("lcd" in slot or "ups" in slot or "app" in slot for slot in slot_ids))
        self.assertNotIn("JA-AD01A", (SKELETON_DIR / "blueprint.yaml").read_text())

    def test_config_binds_only_the_eu_english_target_and_box_entry(self) -> None:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        build = config["build"]
        self.assertEqual(["en"], build["languages"])
        self.assertEqual([{"model": "JA-AD01A", "region": "EU"}], build["targets"])
        self.assertEqual(["box_contents*"], build["web_entry_source_patterns"])
        self.assertEqual(
            "docs/renderers/web/ja_ad01a_eu_en_illustrations.json",
            config["paths"]["web_illustration_manifest"],
        )

    def test_spec_fixture_preserves_source_values_without_invented_totals(self) -> None:
        with (FIXTURE / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(21, len(rows))
        self.assertEqual({"JA-AD01A_EU"}, {row["document_key"] for row in rows})
        text = "\n".join(
            f'{row["Row_label_source"]} {row["Param_source"]} {row["Value_source"]}'
            for row in rows
        )
        for expected in (
            "100-240V~50/60Hz, 1.8A Max",
            "20V⎓ 5A",
            "20V⎓ 3.25A",
            "5V-11V⎓ 2.7A",
            "20V⎓ 4.35A",
            "USB-C2+USB-A output  5V⎓ 3A",
        ):
            self.assertIn(expected, text)
        self.assertNotIn("Combined", text)
        self.assertNotIn("102W Max", text)
        self.assertTrue(all(not row["Param_source"].endswith(":") for row in rows))

    def test_source_copy_retains_warning_warranty_and_legal_tail(self) -> None:
        warning = (ROOT / "docs" / "templates" / "page_charger" / "en" / "safety_warning.rst").read_text(encoding="utf-8")
        warranty = (ROOT / "docs" / "templates" / "page_charger" / "en" / "warranty.rst").read_text(encoding="utf-8")
        legal = (ROOT / "docs" / "templates" / "page_charger" / "en" / "legal_tail.rst").read_text(encoding="utf-8")

        self.assertEqual(11, warning.count("<li>"))
        self.assertIn("The max ambient temperature should not exceed 25°C.", warning)
        self.assertIn("For indoor use only.", warning)
        self.assertIn("must be paired with a 100W charging cable", warning)
        self.assertIn("24 months from the date of purchase", warranty)
        self.assertIn("hello.eu@jackery.com", warranty)
        self.assertIn("JACKERY TECHNOLOGY GMBH", legal)
        self.assertIn("L LAB CORPORATION (HUIZHOU)LIMITED", legal)
        self.assertNotIn("QR", warning + warranty + legal)

    def test_recipe_and_web_manifest_bind_verified_assets(self) -> None:
        recipe = json.loads(ASSET_RECIPE.read_text(encoding="utf-8"))
        manifest = json.loads(ILLUSTRATION_MANIFEST.read_text(encoding="utf-8"))
        source_hash = "0252cb5db68fb67b3fe0947824de4655e13e26f90b3dde1f6bada3b64aa390fc"
        self.assertEqual(source_hash, recipe["source"]["expected_sha256"])
        self.assertEqual(source_hash, manifest["source_pdf_sha256"])
        quarantined = {
            page["page"]
            for page in recipe["page_catalog"]
            if page["gate"]["status"] == "quarantine"
        }
        self.assertEqual({1, 9}, quarantined)

        registry = load_registry(ROOT / "data" / "asset_registry.csv")
        for asset in recipe["assets"]:
            output = asset["outputs"][0]
            resolution = resolve_asset(
                registry,
                repo_root=ROOT,
                asset_key=asset["asset_key"],
                format_name="png",
                language="en",
                model="JA-AD01A",
                region="EU",
            )
            path = ROOT / resolution.path
            self.assertTrue(path.is_file())
            self.assertEqual(output["expected_sha256"], resolution.declared_hash)
            self.assertEqual(
                output["expected_sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )

        manifest_assets = {
            item["path"]: item["sha256"] for item in manifest["illustrations"]
        }
        self.assertEqual(
            {
                "assets/ja_ad01a_eu_en/product_overview.png": "d05f6b83b300a74601b84d82705d771def9e701682d5bc0fcc22b697a649af7f",
                "assets/ja_ad01a_eu_en/using_product.png": "e72a51b3fe88ee3ec0a029c171935d753daa1d4e45be7765e957dc62aa5b38a8",
            },
            manifest_assets,
        )


if __name__ == "__main__":
    unittest.main()
