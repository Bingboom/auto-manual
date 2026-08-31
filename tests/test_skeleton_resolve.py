from __future__ import annotations

import unittest
from pathlib import Path

from tools.config_pages import parse_config_pages_or_raise
from tools.skeleton_resolve import (
    SkeletonResolveError,
    build_header,
    emit_manifest_yaml,
    load_blueprint,
    load_region_profile,
    load_slot_templates,
    resolve_plan,
)

ROOT = Path(__file__).resolve().parents[1]
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "bp-intl"
REGION_PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "us.yaml"
COMMITTED = ROOT / "docs" / "manifests" / "manual_bp-us.yaml"


def _resolved_text() -> str:
    blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
    slot_templates = load_slot_templates(SKELETON_DIR / "slot_templates.yaml", blueprint)
    profile = load_region_profile(REGION_PROFILE, blueprint)
    plan = resolve_plan(blueprint, slot_templates, profile, manifest_id="manual_bp_us")
    return emit_manifest_yaml(
        plan, header=build_header(SKELETON_DIR, REGION_PROFILE, "manual_bp_us")
    )


class SkeletonResolveTests(unittest.TestCase):
    def test_committed_manifest_is_byte_identical_to_resolver_output(self) -> None:
        # Generate-then-verify: YAML stays the compatibility surface; the
        # committed file must be exactly what the carriers resolve to.
        self.assertEqual(_resolved_text(), COMMITTED.read_text(encoding="utf-8"))

    def test_blueprint_excludes_host_only_slots(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slot_ids = {slot["slot_id"] for slot in blueprint["slots"]}
        # 0/7 in the battery-pack corpus: these are host-line slots and their
        # presence here would print chapters the shipped books do not have.
        self.assertNotIn("app_setup", slot_ids)
        self.assertNotIn("user_maintenance_instructions", slot_ids)

    def test_capability_slots_carry_annotations_for_the_runtime_gate(self) -> None:
        # The resolver stamps capability annotations; the actual drop happens
        # at build time in filter_pages_by_capability via the all-FALSE row.
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slot_templates = load_slot_templates(SKELETON_DIR / "slot_templates.yaml", blueprint)
        profile = load_region_profile(REGION_PROFILE, blueprint)
        plan = resolve_plan(blueprint, slot_templates, profile, manifest_id="manual_bp_us")
        gated = {
            entry["slot_id"]: entry.get("capability")
            for entry in plan["pages"]
            if entry.get("capability")
        }
        for lang in profile["language_set"]:
            self.assertEqual("UPS功能", gated.get(f"ups_mode_{lang}"))
            self.assertEqual("加电包扩容", gated.get(f"extra_battery_{lang}"))

    def test_emitted_pages_parse_cleanly_with_unique_slot_ids(self) -> None:
        import yaml

        data = yaml.safe_load(COMMITTED.read_text(encoding="utf-8"))
        pages = parse_config_pages_or_raise(
            data["pages"], default_languages=["en", "fr", "es"], model="JBP-2000B"
        )
        slot_ids = [getattr(page, "slot_id", None) for page in pages]
        self.assertTrue(all(slot_ids), "every emitted entry must carry a slot_id")
        self.assertEqual(len(slot_ids), len(set(slot_ids)))

    def test_body_slots_expand_once_per_language_in_order(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slot_templates = load_slot_templates(SKELETON_DIR / "slot_templates.yaml", blueprint)
        profile = load_region_profile(REGION_PROFILE, blueprint)
        plan = resolve_plan(blueprint, slot_templates, profile, manifest_id="manual_bp_us")
        body_slots = [s["slot_id"] for s in blueprint["slots"] if s["block"] == "body"]
        for lang in profile["language_set"]:
            suffix = f"_{lang}"
            expanded = [
                e["slot_id"][: -len(suffix)]
                for e in plan["pages"]
                if e["slot_id"].endswith(suffix)
            ]
            for slot_id in body_slots:
                self.assertIn(slot_id, expanded, f"{slot_id} missing for {lang}")
            # blueprint order is preserved inside each language block
            positions = [expanded.index(s) for s in body_slots]
            self.assertEqual(positions, sorted(positions))

    def test_region_selects_one_terminal_slot_after_all_language_blocks(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slot_templates = load_slot_templates(SKELETON_DIR / "slot_templates.yaml", blueprint)
        profile = load_region_profile(REGION_PROFILE, blueprint)
        profile = {
            **profile,
            "language_set": ["en", "fr", "es", "de", "it", "uk"],
            "terminal_slots": ["regulatory_compliance"],
            "slot_overrides": {
                **profile["slot_overrides"],
                "regulatory_compliance": {
                    "file": "templates/page_bp/eu/99_regulatory_compliance.rst"
                },
            },
        }

        plan = resolve_plan(blueprint, slot_templates, profile, manifest_id="synthetic_bp_eu")

        slot_ids = [entry["slot_id"] for entry in plan["pages"]]
        self.assertEqual("regulatory_compliance", slot_ids[-1])
        self.assertEqual(1, slot_ids.count("regulatory_compliance"))
        self.assertNotIn("back_cover", slot_ids)
        for lang in profile["language_set"]:
            self.assertLess(slot_ids.index(f"warranty_{lang}"), len(slot_ids) - 1)

    def test_region_can_select_an_explicitly_empty_terminal_set(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slot_templates = load_slot_templates(SKELETON_DIR / "slot_templates.yaml", blueprint)
        profile = {**load_region_profile(REGION_PROFILE, blueprint), "terminal_slots": []}

        plan = resolve_plan(blueprint, slot_templates, profile, manifest_id="synthetic_no_tail")

        back_ids = {
            slot["slot_id"] for slot in blueprint["slots"] if slot["block"] == "back"
        }
        self.assertTrue(back_ids.isdisjoint(entry["slot_id"] for entry in plan["pages"]))


class ResolverGuardTests(unittest.TestCase):
    def test_boolean_like_language_survives_emit_round_trip(self) -> None:
        import yaml

        from tools.skeleton_resolve import _yaml_scalar

        # 'no' (Norwegian) must emit quoted so reparse stays a string.
        self.assertEqual('"no"', _yaml_scalar("no"))
        self.assertEqual("no", yaml.safe_load(_yaml_scalar("no")))
        self.assertEqual("en", _yaml_scalar("en"))
        self.assertEqual('"{model}/x"', _yaml_scalar("{model}/x"))

    def test_round_trip_gate_rejects_drifting_output(self) -> None:
        from tools.skeleton_resolve import SkeletonResolveError, _assert_round_trip

        with self.assertRaises(SkeletonResolveError):
            _assert_round_trip(
                "manifest_id: other\npages: []\n", {"manifest_id": "x", "pages": []}
            )

    def test_duplicate_language_set_rejected(self) -> None:
        import tempfile

        from tools.skeleton_resolve import SkeletonResolveError, load_region_profile

        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
            fh.write(
                "schema_version: skeleton-region-profile/v1\n"
                "region: US\n"
                "language_set: [en, fr, fr]\n"
                "primary_lang: en\n"
            )
            path = Path(fh.name)
        with self.assertRaises(SkeletonResolveError):
            load_region_profile(path, blueprint)

    def test_optional_requirement_is_accepted_for_product_plan_selection(self) -> None:
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
            fh.write(
                "schema_version: skeleton-blueprint/v1\n"
                "skeleton_id: t\n"
                "skeleton_family: BP\n"
                "house_style: INTL\n"
                "slots:\n"
                "  - slot_id: a\n"
                "    block: body\n"
                "    requirement: optional\n"
                "    presentation: chapter\n"
                "    toc: true\n"
            )
            path = Path(fh.name)
        blueprint = load_blueprint(path)
        self.assertEqual("optional", blueprint["slots"][0]["requirement"])

    def test_terminal_selection_rejects_body_and_unknown_slots(self) -> None:
        import tempfile

        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        for selected in ("warranty", "not_a_slot"):
            with self.subTest(selected=selected):
                with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
                    fh.write(
                        "schema_version: skeleton-region-profile/v1\n"
                        "region: synthetic\n"
                        "language_set: [en]\n"
                        "primary_lang: en\n"
                        f"terminal_slots: [{selected}]\n"
                    )
                    path = Path(fh.name)
                with self.assertRaisesRegex(
                    SkeletonResolveError, "non-back or unknown slots"
                ):
                    load_region_profile(path, blueprint)


if __name__ == "__main__":
    unittest.main()
