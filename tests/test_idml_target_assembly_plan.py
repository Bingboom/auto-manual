from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.idml.composition_plan import build_composition_plan
from tools.idml.target_assembly_plan import (
    WARRANTY_LAYOUT_VARIANTS,
    TargetAssemblyPlanError,
    normalize_target_assembly_plan,
)
from tools.manual_ir import ManualBlock, ManualIR, ManualPage


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = (
    ROOT
    / "docs"
    / "renderers"
    / "contracts"
    / "target_assembly"
    / "jbp2000b_us_v1_candidate.json"
)


def _payload() -> dict:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def _manual_ir(payload: dict) -> ManualIR:
    pages = []
    for index, entry in enumerate(payload["pages"], start=1):
        block_specs: list[tuple[str, str]] = []
        if entry["page_role"] == "connections":
            block_specs = [
                ("image", "asset-1.png"),
                ("image", "asset-2.png"),
            ]
        elif entry["page_role"] == "charging":
            block_specs = [
                ("h1", "CHARGING"),
                ("h2", "CHARGING VIA AC WALL OUTLET"),
                ("image", "asset-1.png"),
                (
                    "h2",
                    "CHARGING VIA SOLAR PANELS (SOLD SEPARATELY)",
                ),
                ("image", "asset-2.png"),
            ]
        blocks = tuple(
            ManualBlock(
                block_id=f"block-{index}-{block_index}",
                source_ref=entry["source_ref"],
                kind=kind,
                payload=value,
                content_sha256=f"{block_index:064x}",
            )
            for block_index, (kind, value) in enumerate(block_specs, start=1)
        )
        pages.append(
            ManualPage(
                page_id=f"page-{index}",
                source_ref=entry["source_ref"],
                source_path=entry["source_ref"],
                language=entry["language"],
                source_sha256=f"{index:064x}",
                skipped_raw=0,
                blocks=blocks,
            )
        )
    return ManualIR(
        model="JBP-2000B",
        region="US",
        language="en",
        source="test",
        bundle_root=".",
        bundle_sha256="0" * 64,
        snapshot_sha256="1" * 64,
        layout_params_sha256="2" * 64,
        style_contract_sha256="3" * 64,
        content_sha256="4" * 64,
        pages=tuple(pages),
    )


class TargetAssemblyPlanTests(unittest.TestCase):
    def test_symbols_is_a_registered_complete_component_composition(self) -> None:
        plan = build_composition_plan({
            "physical_page_count": 1,
            "pages": [{
                "source_ref": "page/symbols_ko.rst",
                "language": "ko",
                "page_role": "symbols",
                "composition_id": "ko_symbols",
                "composition_type": "symbols",
                "latex_start_page": 1,
                "planned_page_count": 1,
            }],
        })

        self.assertEqual("symbols", plan.compositions[0].composition_type)

    def test_overview_accepts_a_registered_component_instance_binding(self) -> None:
        payload = _payload()
        page = next(
            page for page in payload["pages"]
            if page["page_role"] == "product_overview"
            and page["language"] == "en"
        )
        page["composition_data"] = {
            "overview": {"instance_id": "je1000f-us-v1"}
        }

        plan = normalize_target_assembly_plan(
            payload,
            _manual_ir(payload),
            source_path=PLAN_PATH,
        )

        normalized = next(
            item for item in plan["pages"]
            if item["source_ref"] == page["source_ref"]
        )
        self.assertEqual(page["composition_data"], normalized["composition_data"])

    def test_inbox_accepts_target_image_width_profile(self) -> None:
        payload = _payload()
        page = next(
            page for page in payload["pages"]
            if page["page_role"] == "inbox"
            and page["language"] == "en"
        )
        page["composition_data"] = {
            "inbox": {
                "image_width_pt_by_language": {
                    "en": [66.0, 30.0, 40.0],
                }
            }
        }

        plan = normalize_target_assembly_plan(
            payload,
            _manual_ir(payload),
            source_path=PLAN_PATH,
        )

        normalized = next(
            item for item in plan["pages"]
            if item["source_ref"] == page["source_ref"]
        )
        self.assertEqual(page["composition_data"], normalized["composition_data"])

    def test_app_accepts_target_instance_data_for_shared_composition(self) -> None:
        payload = _payload()
        page = next(
            page for page in payload["pages"]
            if page["source_ref"] == "page/warranty_en.rst"
        )
        page.update({
            "source_ref": "page/12_app_setup_placeholder.rst",
            "page_role": "app_setup",
            "composition_id": "en_app",
            "composition_type": "app",
            "composition_data": {
                "app": {
                    "instance_id": "test-app-v1",
                    "control_image": "controls/test/panel.pdf",
                    "control_layout_variant": "embedded_leaders",
                    "figure_assets": {
                        "app_add_device": "app/test/add_device_textless.png",
                    },
                    "labels_by_role": {
                        "main_power": "POWER",
                        "dc_usb": "DC/USB",
                        "ac": "AC",
                    },
                }
            },
        })

        plan = normalize_target_assembly_plan(
            payload,
            _manual_ir(payload),
            source_path=PLAN_PATH,
        )

        normalized = next(
            item for item in plan["pages"]
            if item["source_ref"] == "page/12_app_setup_placeholder.rst"
        )
        self.assertEqual(page["composition_data"], normalized["composition_data"])

    def test_app_rejects_incomplete_control_label_roles(self) -> None:
        payload = _payload()
        page = next(
            page for page in payload["pages"]
            if page["source_ref"] == "page/warranty_en.rst"
        )
        page.update({
            "source_ref": "page/12_app_setup_placeholder.rst",
            "page_role": "app_setup",
            "composition_id": "en_app",
            "composition_type": "app",
            "composition_data": {
                "app": {
                    "instance_id": "test-app-v1",
                    "control_image": "controls/test/panel.pdf",
                    "control_layout_variant": "embedded_leaders",
                    "labels_by_role": {
                        "main_power": "POWER",
                        "ac": "AC",
                    },
                }
            },
        })

        with self.assertRaisesRegex(
            TargetAssemblyPlanError,
            "labels_by_role must contain exactly ac, dc_usb, and main_power",
        ):
            normalize_target_assembly_plan(
                payload,
                _manual_ir(payload),
                source_path=PLAN_PATH,
            )

    def test_connections_composition_accepts_shared_layout_variant(self) -> None:
        payload = _payload()
        page = next(
            page for page in payload["pages"]
            if page["source_ref"] == "page/connections_en.rst"
        )
        page["composition_data"] = {
            "connections": {
                "layout_variant": "notice_before_primary_figure",
                "image_role": "reference_measure",
            }
        }

        plan = normalize_target_assembly_plan(
            payload,
            _manual_ir(payload),
            source_path=PLAN_PATH,
        )

        normalized = next(
            item for item in plan["pages"]
            if item["source_ref"] == "page/connections_en.rst"
        )
        self.assertEqual(page["composition_data"], normalized["composition_data"])

    def test_connections_composition_rejects_page_specific_variant(self) -> None:
        payload = _payload()
        page = next(
            page for page in payload["pages"]
            if page["source_ref"] == "page/connections_en.rst"
        )
        page["composition_data"] = {
            "connections": {
                "layout_variant": "jbp_page_7",
                "image_role": "reference_measure",
            }
        }

        with self.assertRaisesRegex(
            TargetAssemblyPlanError,
            "connections.layout_variant must be notice_before_primary_figure",
        ):
            normalize_target_assembly_plan(
                payload,
                _manual_ir(payload),
                source_path=PLAN_PATH,
            )

    def test_jbp_candidate_normalizes_to_28_shared_compositions(self) -> None:
        payload = _payload()
        plan = normalize_target_assembly_plan(
            payload,
            _manual_ir(payload),
            source_path=PLAN_PATH,
        )

        self.assertEqual(plan["plan_source"], "target-assembly")
        self.assertEqual(plan["physical_page_count"], 28)
        self.assertEqual(plan["source_page_count"], 43)
        self.assertEqual(plan["composition_count"], 28)
        compositions = build_composition_plan(plan)
        by_id = {item.composition_id: item for item in compositions.compositions}
        self.assertEqual(
            by_id["en_fcc_inbox_overview"].composition_type,
            "fcc_inbox_overview",
        )
        self.assertEqual(
            by_id["en_charging"].source_refs,
            ("page/charging_en.rst",),
        )
        charging_pages = [
            page for page in plan["pages"]
            if page["page_role"] == "charging"
        ]
        self.assertEqual(3, len(charging_pages))
        for page in charging_pages:
            self.assertEqual(
                {
                    "image_role": "reference_measure",
                    "h2_suffix_pill_indices": [1],
                },
                page["composition_data"]["charging"],
            )
        connection_pages = [
            page for page in plan["pages"]
            if page["page_role"] == "connections"
        ]
        self.assertEqual(3, len(connection_pages))
        for page in connection_pages:
            self.assertEqual(
                {
                    "layout_variant": "notice_before_primary_figure",
                    "image_role": "reference_measure",
                },
                page["composition_data"]["connections"],
            )
        self.assertEqual(
            by_id["en_storage_specifications"].composition_type,
            "storage_specifications",
        )
        self.assertEqual(
            by_id["en_storage_specifications"].source_refs,
            (
                "page/storage_en.rst",
                "page/specifications_en.rst",
            ),
        )
        compact_spec_pages = [
            page for page in plan["pages"]
            if page["page_role"] == "spec"
        ]
        self.assertEqual(3, len(compact_spec_pages))
        for page in compact_spec_pages:
            spec = page["composition_data"]["specifications"]
            self.assertEqual("compact", spec["layout_variant"])
            self.assertEqual(
                [[0], [1, 2], [3]],
                [group["source_indices"] for group in spec["section_groups"]],
            )
        lcd_pages = [
            page for page in plan["pages"]
            if page["page_role"] == "lcd"
        ]
        self.assertEqual(3, len(lcd_pages))
        for page in lcd_pages:
            lcd = page["composition_data"]["lcd"]
            self.assertEqual("label_description", lcd["table_variant"])
            self.assertEqual("paired_cards", lcd["operation_panel_variant"])
            self.assertEqual([1, 2], [
                callout["row_index"] for callout in lcd["hero_callouts"]
            ])
            self.assertTrue(all(
                len(callout["leader_points"]) >= 2
                for callout in lcd["hero_callouts"]
            ))
        troubleshooting_pages = [
            page for page in plan["pages"]
            if page["page_role"] == "troubleshooting_data"
        ]
        self.assertEqual(3, len(troubleshooting_pages))
        self.assertTrue(all(
            page["composition_data"]["troubleshooting"][
                "connection_image_role"
            ] == "reference_measure"
            for page in troubleshooting_pages
        ))
        fr_warranty = next(
            page for page in plan["pages"]
            if page["source_ref"] == "page/warranty_fr.rst"
        )
        self.assertEqual(
            "multiline_lead",
            fr_warranty["composition_data"]["warranty"]["layout_variant"],
        )

    def test_candidate_remains_non_approved(self) -> None:
        payload = _payload()
        self.assertEqual(payload["status"], "candidate")
        self.assertFalse(payload["production_eligible"])
        self.assertNotIn("approval", payload)

    def test_flow_split_requires_the_second_connection_image(self) -> None:
        payload = _payload()
        ir = _manual_ir(payload)
        pages = list(ir.pages)
        connection_index = next(
            index
            for index, page in enumerate(pages)
            if page.source_ref == "page/connections_en.rst"
        )
        page = pages[connection_index]
        pages[connection_index] = ManualPage(
            page_id=page.page_id,
            source_ref=page.source_ref,
            source_path=page.source_path,
            language=page.language,
            source_sha256=page.source_sha256,
            skipped_raw=page.skipped_raw,
            blocks=page.blocks[:1],
        )
        ir = ManualIR(**{**ir.to_dict(), "pages": tuple(pages)})

        with self.assertRaisesRegex(
            TargetAssemblyPlanError,
            "cannot find image occurrence 2",
        ):
            normalize_target_assembly_plan(payload, ir, source_path=PLAN_PATH)

    def test_lcd_composition_data_rejects_out_of_page_geometry(self) -> None:
        payload = _payload()
        lcd_page = next(
            page for page in payload["pages"]
            if page["source_ref"] == "page/lcd_display_en.rst"
        )
        lcd_page["composition_data"]["lcd"]["hero_callouts"][0][
            "leader_points"
        ][0] = [-1, 72.5]

        with self.assertRaisesRegex(
            TargetAssemblyPlanError,
            "leader_points.*inside the reference page",
        ):
            normalize_target_assembly_plan(
                payload,
                _manual_ir(payload),
                source_path=PLAN_PATH,
            )

    def test_troubleshooting_composition_rejects_out_of_page_split(self) -> None:
        payload = _payload()
        page = next(
            page for page in payload["pages"]
            if page["source_ref"] == "page/troubleshooting_en.rst"
        )
        page["composition_data"]["troubleshooting"]["split"] = 999.0

        with self.assertRaisesRegex(
            TargetAssemblyPlanError,
            "troubleshooting.split.*inside the reference page",
        ):
            normalize_target_assembly_plan(
                payload,
                _manual_ir(payload),
                source_path=PLAN_PATH,
            )

    def test_charging_composition_rejects_unregistered_image_role(self) -> None:
        payload = _payload()
        page = next(
            page for page in payload["pages"]
            if page["source_ref"] == "page/charging_en.rst"
        )
        page["composition_data"]["charging"]["image_role"] = "jbp_large"

        with self.assertRaisesRegex(
            TargetAssemblyPlanError,
            "charging.image_role is invalid",
        ):
            normalize_target_assembly_plan(
                payload,
                _manual_ir(payload),
                source_path=PLAN_PATH,
            )

    def test_charging_composition_rejects_non_parenthesized_h2_selection(
        self,
    ) -> None:
        payload = _payload()
        page = next(
            page for page in payload["pages"]
            if page["source_ref"] == "page/charging_en.rst"
        )
        page["composition_data"]["charging"][
            "h2_suffix_pill_indices"
        ] = [0]

        with self.assertRaisesRegex(
            TargetAssemblyPlanError,
            "h2_suffix_pill_indices.*trailing parenthetical",
        ):
            normalize_target_assembly_plan(
                payload,
                _manual_ir(payload),
                source_path=PLAN_PATH,
            )

    def test_warranty_composition_rejects_unknown_layout_variant(self) -> None:
        payload = _payload()
        page = next(
            page for page in payload["pages"]
            if page["source_ref"] == "page/warranty_fr.rst"
        )
        page["composition_data"]["warranty"]["layout_variant"] = "jbp"

        with self.assertRaisesRegex(
            TargetAssemblyPlanError,
            "warranty.layout_variant must be one of bp_default, multiline_lead",
        ):
            normalize_target_assembly_plan(
                payload,
                _manual_ir(payload),
                source_path=PLAN_PATH,
            )

    def test_warranty_composition_accepts_every_registered_layout_variant(self) -> None:
        """A registered variant must load; an unregistered one must not.

        Each variant owns its own ``idml_warranty_variant_<name>_*`` token family,
        so the allowlist is the only thing standing between a typo and a page that
        silently renders with no correction at all.
        """
        for variant in sorted(WARRANTY_LAYOUT_VARIANTS):
            with self.subTest(layout_variant=variant):
                payload = _payload()
                page = next(
                    page for page in payload["pages"]
                    if page["source_ref"] == "page/warranty_fr.rst"
                )
                page["composition_data"]["warranty"]["layout_variant"] = variant

                plan = normalize_target_assembly_plan(
                    payload,
                    _manual_ir(payload),
                    source_path=PLAN_PATH,
                )
                self.assertTrue(plan)


if __name__ == "__main__":
    unittest.main()
