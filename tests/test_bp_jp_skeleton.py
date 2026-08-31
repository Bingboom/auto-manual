from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.config_pages import parse_config_pages_or_raise
from tools.idml_rst_extract import extract_page
from tools.skeleton_resolve import (
    SkeletonResolveError,
    build_header,
    emit_manifest_yaml,
    load_blueprint,
    load_product_plan,
    load_region_profile,
    load_slot_template_catalog,
    resolve_plan,
)


ROOT = Path(__file__).resolve().parents[1]
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "bp-jp"
REGION_PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "jp.yaml"
COMMITTED = ROOT / "docs" / "manifests" / "manual_bp-jp.yaml"
TARGET_PRODUCT_PLAN = (
    ROOT / "docs" / "manifests" / "product_plans" / "jbp2000b_jp.yaml"
)
TARGET_MANIFEST = ROOT / "docs" / "manifests" / "manual_bp-jp-jbp2000b.yaml"
TARGET_ASSEMBLY = (
    ROOT
    / "docs"
    / "renderers"
    / "contracts"
    / "target_assembly"
    / "jbp2000b_jp_v1_candidate.json"
)


def _carriers() -> tuple[
    dict,
    dict,
    dict,
    dict,
]:
    blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
    slots, profiles = load_slot_template_catalog(
        SKELETON_DIR / "slot_templates.yaml", blueprint
    )
    region = load_region_profile(REGION_PROFILE, blueprint)
    return blueprint, slots, profiles, region


def _resolve(name: str, product_plan: dict) -> dict:
    blueprint, slots, profiles, region = _carriers()
    return resolve_plan(
        blueprint,
        slots,
        region,
        manifest_id=name,
        product_plan=product_plan,
        slot_template_profiles=profiles,
    )


def _semantic_ids(plan: dict) -> list[str]:
    result: list[str] = []
    for entry in plan["pages"]:
        slot_id = entry["slot_id"]
        result.append(slot_id[:-3] if slot_id.endswith("_ja") else slot_id)
    return result


class BpJpSkeletonTests(unittest.TestCase):
    def test_core_manifest_is_byte_identical_and_uses_stable_slot_ids(self) -> None:
        blueprint, slots, profiles, region = _carriers()
        plan = resolve_plan(
            blueprint,
            slots,
            region,
            manifest_id="manual_bp_jp",
            slot_template_profiles=profiles,
        )
        emitted = emit_manifest_yaml(
            plan,
            header=build_header(SKELETON_DIR, REGION_PROFILE, "manual_bp_jp"),
        )
        self.assertEqual(COMMITTED.read_text(encoding="utf-8"), emitted)
        self.assertEqual(
            [
                "cover",
                "safety_info",
                "box_contents",
                "product_overview",
                "lcd_display",
                "operation",
                "connections",
                "charging",
                "specifications",
                "warranty",
            ],
            _semantic_ids(plan),
        )

        import yaml

        parsed = yaml.safe_load(emitted)
        pages = parse_config_pages_or_raise(
            parsed["pages"], default_languages=["ja"], model="SYNTHETIC-BP-JP"
        )
        slot_ids = [page.slot_id for page in pages]
        self.assertEqual(len(slot_ids), len(set(slot_ids)))

    def test_three_audited_books_resolve_from_data_only(self) -> None:
        cases = {
            "htp015": (
                {
                    "house_style_version": "jp-v2",
                    "enabled_optional_slots": [
                        "toc",
                        "symbol_meaning",
                        "installation",
                        "troubleshooting",
                    ],
                    "terminal_slots": ["back_cover"],
                },
                [
                    "cover",
                    "toc",
                    "safety_info",
                    "symbol_meaning",
                    "box_contents",
                    "product_overview",
                    "lcd_display",
                    "operation",
                    "installation",
                    "connections",
                    "charging",
                    "troubleshooting",
                    "specifications",
                    "warranty",
                    "back_cover",
                ],
            ),
            "htp017": (
                {
                    "house_style_version": "jp-v2",
                    "enabled_optional_slots": [
                        "toc",
                        "symbol_meaning",
                        "troubleshooting",
                    ],
                    "terminal_slots": [],
                },
                [
                    "cover",
                    "toc",
                    "safety_info",
                    "symbol_meaning",
                    "box_contents",
                    "product_overview",
                    "lcd_display",
                    "operation",
                    "connections",
                    "charging",
                    "troubleshooting",
                    "specifications",
                    "warranty",
                ],
            ),
            "htp007": (
                {
                    "house_style_version": "jp-v1",
                    "enabled_optional_slots": [],
                    "terminal_slots": [],
                },
                [
                    "cover",
                    "specifications",
                    "box_contents",
                    "product_overview",
                    "lcd_display",
                    "operation",
                    "connections",
                    "charging",
                    "warranty",
                    "safety_info",
                ],
            ),
        }
        for name, (product_plan, expected) in cases.items():
            with self.subTest(name=name):
                self.assertEqual(expected, _semantic_ids(_resolve(name, product_plan)))

    def test_house_style_version_selects_carriers_without_changing_slot_ids(self) -> None:
        plan = _resolve(
            "synthetic_jp_v1",
            {
                "house_style_version": "jp-v1",
                "enabled_optional_slots": [],
                "terminal_slots": [],
            },
        )
        entries = {entry["slot_id"]: entry for entry in plan["pages"]}
        self.assertEqual(
            "templates/page_bp/ja/01_safety_v1.rst",
            entries["safety_info_ja"]["file"],
        )
        self.assertEqual(
            "templates/page_bp/ja/11_warranty_v1.rst",
            entries["warranty_ja"]["file"],
        )

    def test_optional_back_slot_has_one_selector(self) -> None:
        with self.assertRaisesRegex(SkeletonResolveError, "only through terminal_slots"):
            _resolve(
                "bad_back_selector",
                {
                    "house_style_version": "jp-v2",
                    "enabled_optional_slots": ["back_cover"],
                    "terminal_slots": [],
                },
            )

    def test_declared_order_profiles_require_the_carrier_profile_catalog(self) -> None:
        blueprint, slots, _, region = _carriers()
        with self.assertRaisesRegex(SkeletonResolveError, "slot-template profile catalog"):
            resolve_plan(
                blueprint,
                slots,
                region,
                manifest_id="missing_catalog",
            )

    def test_unknown_style_and_non_optional_selection_fail_closed(self) -> None:
        for product_plan, message in (
            (
                {
                    "house_style_version": "model-specific",
                    "enabled_optional_slots": [],
                    "terminal_slots": [],
                },
                "declared order profile",
            ),
            (
                {
                    "house_style_version": "jp-v2",
                    "enabled_optional_slots": ["charging"],
                    "terminal_slots": [],
                },
                "required, capability, or unknown",
            ),
        ):
            with self.subTest(product_plan=product_plan):
                with self.assertRaisesRegex(SkeletonResolveError, message):
                    _resolve("bad_plan", product_plan)

    def test_product_plan_file_schema_normalizes_to_api_input(self) -> None:
        blueprint, _, _, _ = _carriers()
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
            fh.write(
                "schema_version: skeleton-product-plan/v1\n"
                "plan_id: synthetic-v2\n"
                "house_style_version: jp-v2\n"
                "enabled_optional_slots: [toc, symbol_meaning, troubleshooting]\n"
                "terminal_slots: []\n"
            )
            path = Path(fh.name)
        plan = load_product_plan(path, blueprint)
        self.assertEqual("jp-v2", plan["house_style_version"])
        self.assertEqual([], plan["terminal_slots"])
        resolved = _resolve("loaded_plan", plan)
        self.assertIn("toc", _semantic_ids(resolved))

    def test_jbp2000b_target_manifest_is_generated_from_its_product_plan(self) -> None:
        blueprint, slots, profiles, region = _carriers()
        product_plan = load_product_plan(TARGET_PRODUCT_PLAN, blueprint)
        plan = resolve_plan(
            blueprint,
            slots,
            region,
            manifest_id="manual_bp_jp_jbp2000b",
            product_plan=product_plan,
            slot_template_profiles=profiles,
        )
        emitted = emit_manifest_yaml(
            plan,
            header=[
                "Resolved Manifest — generated from the BP@JP skeleton and target Product Plan. Do not hand-edit.",
                "Sources: docs/manifests/skeletons/bp-jp/{blueprint.yaml,slot_templates.yaml}",
                "         + docs/manifests/region_profiles/jp.yaml",
                "         + docs/manifests/product_plans/jbp2000b_jp.yaml",
            ],
        )
        self.assertEqual(TARGET_MANIFEST.read_text(encoding="utf-8"), emitted)
        self.assertEqual(
            [
                "cover",
                "toc",
                "safety_info",
                "symbol_meaning",
                "box_contents",
                "product_overview",
                "lcd_display",
                "operation",
                "connections",
                "charging",
                "troubleshooting",
                "specifications",
                "warranty",
            ],
            _semantic_ids(plan),
        )

    def test_jbp2000b_target_assembly_is_twelve_pages_and_ten_compositions(
        self,
    ) -> None:
        import json

        assembly = json.loads(TARGET_ASSEMBLY.read_text(encoding="utf-8"))
        compositions = {
            page["composition_id"]
            for page in assembly["pages"]
        }

        self.assertEqual(12, assembly["physical_page_count"])
        self.assertEqual(10, len(compositions))
        self.assertEqual(
            12,
            max(
                page["start_page"] + page["page_count"] - 1
                for page in assembly["pages"]
            ),
        )
        self.assertNotIn(
            "back_cover",
            {page["page_role"] for page in assembly["pages"]},
        )
        connections = next(
            page for page in assembly["pages"]
            if page["page_role"] == "connections"
        )
        self.assertEqual(
            {
                "layout_variant": "stacking_guide",
                "image_role": "reference_measure",
            },
            connections["composition_data"]["connections"],
        )
        specifications = next(
            page for page in assembly["pages"]
            if page["page_role"] == "spec"
        )
        self.assertEqual(
            246.0,
            specifications["composition_data"]["specifications"]["split"],
        )

    def test_jbp2000b_jp_fixture_preserves_htp017_spec_evidence(self) -> None:
        with (ROOT / "tests" / "fixtures" / "phase2" / "Spec_Master.csv").open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            rows = [
                row
                for row in csv.DictReader(handle)
                if row.get("document_key") == "JBP-2000B_JP"
                and row.get("Page") == "specifications"
                and row.get("Is_Latest") == "TRUE"
            ]
        values = {
            (row["Section"], row["Row_key"]): (
                row["Row_label_source"],
                row["Value_source"],
            )
            for row in rows
        }
        self.assertEqual(
            ("バッテリータイプ", "LiFePO4 (リン酸鉄リチウムイオン電池)"),
            values[("GENERAL INFO", "cell_chemistry")],
        )
        self.assertEqual(
            ("サイズ & 重量", "約365 × 255 × 191 mm (約 14.8kg)"),
            values[("GENERAL INFO", "weight")],
        )
        self.assertEqual(
            ("DC 拡張ポート (入力)", "36.8V-57.6V⎓最大 75A"),
            values[("INPUT PORTS", "dc_expansion_port")],
        )
        self.assertEqual(
            ("充電温度", "-10°C~45°C"),
            values[("ENVIRONMENTAL OPERATING TEMPERATURE", "charging_temperature")],
        )

    def test_jbp2000b_jp_fixture_keeps_certification_and_host_note_as_data(self) -> None:
        with (ROOT / "tests" / "fixtures" / "phase2" / "Spec_Notes.csv").open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            notes = {
                row["Note_id"]: row["Text_ja"]
                for row in csv.DictReader(handle)
                if row.get("Model") == "JBP-2000B" and row.get("Region") == "JP"
            }
        self.assertEqual("認証：UN38.3", notes["certification_un38_3"])
        self.assertEqual(
            "本製品はJackery ポータブル電源 2000 Plus 専用となります。"
            "他の機器には接続しないでください。",
            notes["bp_host_compatibility"],
        )

    def test_jbp2000b_jp_troubleshooting_is_target_data_not_us_retagging(self) -> None:
        with (
            ROOT / "tests" / "fixtures" / "phase2" / "troubleshooting_blocks.csv"
        ).open(encoding="utf-8-sig", newline="") as handle:
            rows = [
                row
                for row in csv.DictReader(handle)
                if row.get("Model") == "JBP-2000B"
            ]
        jp_rows = [row for row in rows if row.get("Region") == "JP"]
        us_rows = [row for row in rows if row.get("Region") == "US"]
        self.assertEqual(
            ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "FA", "FC", "FF"],
            [row["error_code"] for row in jp_rows],
        )
        self.assertEqual(13, len(jp_rows))
        self.assertEqual(7, len(us_rows))
        self.assertTrue(all(not row.get("corrective_measures_jp") for row in us_rows))

    def test_jp_safety_signal_table_is_strict_manual_ir_data(self) -> None:
        result = extract_page(
            ROOT / "docs" / "templates" / "page_bp" / "ja" / "01_safety.rst",
            {"latex", "idml", "lang_ja", "region_jp"},
        )
        payloads = [
            block
            for kind, block in result.blocks
            if kind == "data"
        ]
        self.assertEqual(1, len(payloads))
        import json

        payload = json.loads(payloads[0])
        self.assertEqual("symbol_signals", payload["kind"])
        self.assertEqual(
            ["warning", "caution", "note", "tips"],
            [row["signal_key"] for row in payload["rows"]],
        )
        self.assertEqual(
            ["警告", "注意", "説明", "ヒント"],
            [row["label"] for row in payload["rows"]],
        )

    def test_blueprint_keeps_fragments_and_host_topics_out_of_slot_universe(self) -> None:
        blueprint, _, _, _ = _carriers()
        slot_ids = {slot["slot_id"] for slot in blueprint["slots"]}
        self.assertEqual([["lcd_display", "operation"]], blueprint["co_page_groups"])
        for absent in (
            "battery_recycling",
            "preface_important",
            "storage",
            "ups_mode",
            "extra_battery",
            "regulatory_compliance",
            "app_setup",
        ):
            self.assertNotIn(absent, slot_ids)

    def test_generic_resolver_contains_no_audited_target_branch(self) -> None:
        source = (ROOT / "tools" / "skeleton_resolve.py").read_text(encoding="utf-8")
        for target_literal in ("JBP-2000B_JP", "HTP015", "HTP007", "HTP017"):
            self.assertNotIn(target_literal, source)


if __name__ == "__main__":
    unittest.main()
