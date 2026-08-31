from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import yaml

from tools.skeleton_resolve import (
    load_blueprint,
    load_region_profile,
    load_slot_templates,
    resolve_plan,
)


ROOT = Path(__file__).resolve().parents[1]
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "bp-intl"
EU_PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "eu.yaml"
EU_MANIFEST = ROOT / "docs" / "manifests" / "manual_bp-eu.yaml"
US_MANIFEST = ROOT / "docs" / "manifests" / "manual_bp-us.yaml"
US_CONFIG = ROOT / "configs" / "config.bp-us.yaml"
FROZEN_US_MANIFEST_SHA256 = (
    "94e7276ab3f20bbd804eb66864b360dd5780c886b3d29ed5377161162da5cc8b"
)


class BpIntlEuTargetTests(unittest.TestCase):
    def test_eu_profile_resolves_same_blueprint_with_six_languages(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slots = load_slot_templates(SKELETON_DIR / "slot_templates.yaml", blueprint)
        profile = load_region_profile(EU_PROFILE, blueprint)
        plan = resolve_plan(blueprint, slots, profile, manifest_id="manual_bp_eu")

        self.assertEqual("bp-intl", blueprint["skeleton_id"])
        self.assertEqual(["en", "fr", "es", "de", "it", "uk"], profile["language_set"])
        self.assertEqual(1, sum(p["slot_id"] == "regulatory_compliance" for p in plan["pages"]))
        self.assertFalse(any(p["slot_id"] == "back_cover" for p in plan["pages"]))
        self.assertFalse(any(str(p["slot_id"]).startswith("fcc") for p in plan["pages"]))

    def test_eu_config_binds_explorer_host_and_target_assets(self) -> None:
        config = yaml.safe_load(
            (ROOT / "configs" / "config.bp-eu.yaml").read_text(encoding="utf-8")
        )
        substitutions = config["build"]["rst_substitutions"]
        self.assertEqual("Jackery Explorer 2000 Plus", substitutions["BP_HOST_PRODUCT_NAME"])
        self.assertEqual("Explorer 2000 Plus", substitutions["BP_HOST_PRODUCT_SHORT_NAME"])
        for lang in ("DE", "IT", "UK"):
            self.assertEqual(
                f"asset:connections/jbp2000b/eu/locking_{lang.lower()}",
                substitutions[f"BP_CONNECTION_LOCKING_ASSET_{lang}"],
            )

    def test_same_host_uses_region_specific_product_names(self) -> None:
        eu_config = yaml.safe_load(
            (ROOT / "configs" / "config.bp-eu.yaml").read_text(encoding="utf-8")
        )
        us_config = yaml.safe_load(US_CONFIG.read_text(encoding="utf-8"))
        eu = eu_config["build"]["rst_substitutions"]
        us = us_config["build"]["rst_substitutions"]

        self.assertEqual("Jackery Explorer 2000 Plus", eu["BP_HOST_PRODUCT_NAME"])
        self.assertEqual("Explorer 2000 Plus", eu["BP_HOST_PRODUCT_SHORT_NAME"])
        self.assertEqual("Jackery HomePower 2000 Plus", us["BP_HOST_PRODUCT_NAME"])
        self.assertEqual("HomePower 2000 Plus", us["BP_HOST_PRODUCT_SHORT_NAME"])

    def test_resolved_manifest_has_no_target_logic(self) -> None:
        text = EU_MANIFEST.read_text(encoding="utf-8")
        self.assertNotIn("HomePower 2000 Plus", text)
        self.assertNotIn("JBP-2000B_EU", text)
        self.assertIn("templates/page_bp/intl/99_regulatory_compliance_eu.rst", text)

    def test_us_manifest_identity_remains_frozen(self) -> None:
        self.assertEqual(
            FROZEN_US_MANIFEST_SHA256,
            hashlib.sha256(US_MANIFEST.read_bytes()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
