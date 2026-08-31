from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.idml.composition_plan import build_composition_plan
from tools.idml.target_assembly_plan import (
    OPERATION_LAYOUT_VARIANTS,
    WARRANTY_LAYOUT_VARIANTS,
    TargetAssemblyPlanError,
    _PAGE_KEYS,
    _validate_composition_data,
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
KR_PLAN_PATH = (
    ROOT
    / "docs"
    / "renderers"
    / "contracts"
    / "target_assembly"
    / "je3000c_kr_v1_candidate.json"
)

# The four KR source pages whose plan rules address block identity. Every count
# here is forced by a validator against the shipped contract, not chosen: the
# operation page needs h2 occurrence 6 for its flow_split, h2 occurrence 4 for
# its page_break and four image blocks for its four image_refs; ups_mode and
# charging need one image each (charging also h1 occurrence 1 for its
# page_break); charging_methods needs two images. Every other page carries no
# blocks because no KR rule reads one.
_KR_BLOCK_KINDS: dict[str, tuple[str, ...]] = {
    "page/05_operation_guide_placeholder.rst": (
        "h2",
        "image",
        "h2",
        "image",
        "h2",
        "image",
        "h2",
        "h2",
        "h2",
        "image",
    ),
    "page/06_ups_mode.rst": ("h1", "image"),
    "page/charging.rst": ("h1", "image"),
    "page/08_charging_methods.rst": ("h1", "image", "image"),
}


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


def _kr_payload() -> dict:
    return json.loads(KR_PLAN_PATH.read_text(encoding="utf-8"))


def _kr_manual_ir(payload: dict) -> ManualIR:
    pages = []
    for index, entry in enumerate(payload["pages"], start=1):
        kinds = _KR_BLOCK_KINDS.get(entry["source_ref"], ())
        blocks = tuple(
            ManualBlock(
                block_id=f"block-{index}-{block_index}",
                source_ref=entry["source_ref"],
                kind=kind,
                payload=f"{kind}-{block_index}",
                content_sha256=f"{block_index:064x}",
            )
            for block_index, kind in enumerate(kinds, start=1)
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
        model="JE-3000C",
        region="KR",
        language="ko",
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
    def test_symbols_accepts_target_declared_column_split(self) -> None:
        issues = _validate_composition_data(
            [{
                "source_ref": "page/symbol_meaning_en.rst",
                "page_role": "symbols",
                "composition_type": "safety_symbols",
                "composition_data": {"symbols": {"left_count": 6}},
            }],
            {},
            _manual_ir(_payload()),
        )

        self.assertEqual([], issues)

    def test_inbox_accepts_shared_compact_with_tip_variant(self) -> None:
        issues = _validate_composition_data(
            [{
                "source_ref": "page/02_whats_in_the_box.rst",
                "page_role": "inbox",
                "composition_type": "inbox_overview",
                "composition_data": {
                    "inbox": {"layout_variant": "compact_with_tip"},
                },
            }],
            {},
            _manual_ir(_payload()),
        )

        self.assertEqual([], issues)

    def test_operation_accepts_the_registered_guidance_stack_variant(self) -> None:
        """Every registered operation variant must validate clean.

        ``guidance_stack`` is the only name the promotion in
        ``oppanel.promote_operation_guidance_stack`` knows how to wrap. A name
        added to the frozenset without that wiring would pass validation here
        and then render loose blocks instead of one guidance card, so this
        iterates the vocabulary rather than pinning a single literal.
        """
        for variant in sorted(OPERATION_LAYOUT_VARIANTS):
            with self.subTest(layout_variant=variant):
                issues = _validate_composition_data(
                    [{
                        "source_ref": "page/05_operation_guide_placeholder.rst",
                        "page_role": "operation_guide",
                        "composition_type": "operation",
                        "composition_data": {
                            "operation": {"layout_variant": variant},
                        },
                    }],
                    {},
                    _kr_manual_ir(_kr_payload()),
                )

                self.assertEqual([], issues)

    def test_operation_rejects_a_page_specific_variant(self) -> None:
        """A per-page variant name is a target leaking geometry into the plan.

        The allowlist is the only thing between a typo (or a smuggled
        ``kr_page_7``) and an operation page that renders with no correction at
        all, so an unregistered name must be reported, not ignored.
        """
        issues = _validate_composition_data(
            [{
                "source_ref": "page/05_operation_guide_placeholder.rst",
                "page_role": "operation_guide",
                "composition_type": "operation",
                "composition_data": {
                    "operation": {"layout_variant": "kr_page_7"},
                },
            }],
            {},
            _kr_manual_ir(_kr_payload()),
        )

        self.assertEqual(
            [
                "page/05_operation_guide_placeholder.rst.composition_data"
                ".operation.layout_variant must be one of guidance_stack"
            ],
            issues,
        )

    def test_operation_variant_requires_an_operation_composition(self) -> None:
        """Operation data must not ride on a non-operation composition.

        Only the operation compositor reads ``operation.layout_variant``; if the
        host guard is dropped, the key is silently inert on any other page and
        the plan claims a layout nothing applies.
        """
        issues = _validate_composition_data(
            [{
                "source_ref": "page/05_operation_guide_placeholder.rst",
                "page_role": "operation_guide",
                "composition_type": "lcd_operations",
                "composition_data": {
                    "operation": {"layout_variant": "guidance_stack"},
                },
            }],
            {},
            _kr_manual_ir(_kr_payload()),
        )

        self.assertEqual(
            [
                "page/05_operation_guide_placeholder.rst.composition_data"
                ".operation requires an operation composition"
            ],
            issues,
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

    def test_kr_candidate_normalizes_to_13_shared_compositions(self) -> None:
        """The shipped KR contract must still project onto the shared vocabulary.

        Until now the committed JE-3000C plan was only checked for its page
        keys; nothing normalized it. A renamed page role, a re-paginated
        ``start_page``, an added page or a composition type dropped from
        ``composition_plan.REGISTRY`` would ship silently and only surface as a
        CompositionPlanError during a real KR build.
        """
        payload = _kr_payload()
        plan = normalize_target_assembly_plan(
            payload,
            _kr_manual_ir(payload),
            source_path=KR_PLAN_PATH,
        )

        self.assertEqual(plan["plan_source"], "target-assembly")
        self.assertEqual(plan["physical_page_count"], 18)
        self.assertEqual(plan["source_page_count"], 18)
        self.assertEqual(plan["composition_count"], 13)
        compositions = build_composition_plan(plan)
        by_id = {item.composition_id: item for item in compositions.compositions}
        self.assertEqual(
            by_id["ko_inbox_overview"].source_refs,
            (
                "page/02_whats_in_the_box.rst",
                "page/03_product_overview_placeholder.rst",
            ),
        )
        self.assertEqual(
            by_id["ko_ups_charging"].composition_type,
            "ups_charging",
        )
        self.assertEqual(
            by_id["ko_ups_charging"].source_refs,
            (
                "page/06_ups_mode.rst",
                "page/charging.rst",
            ),
        )
        self.assertEqual(
            by_id["ko_storage_troubleshooting"].source_refs,
            (
                "page/09_storage_and_maintenance.rst",
                "page/troubleshooting_ko.rst",
            ),
        )
        self.assertEqual(3, by_id["ko_operation"].page_count)
        operation_page = next(
            page for page in plan["pages"]
            if page["source_ref"] == "page/05_operation_guide_placeholder.rst"
        )
        self.assertEqual(
            "guidance_stack",
            operation_page["composition_data"]["operation"]["layout_variant"],
        )
        spec_page = next(
            page for page in plan["pages"]
            if page["page_role"] == "spec"
        )
        self.assertEqual(
            {"layout_variant": "compact", "annotation_order": [1, 2, 0]},
            spec_page["composition_data"]["specifications"],
        )

    def test_kr_candidate_remains_non_approved(self) -> None:
        """The KR target is a candidate until an operator approves the proof.

        Flipping ``production_eligible`` or adding an ``approval`` block here
        would let an unreviewed layout be discovered as an approved reference.
        """
        payload = _kr_payload()
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

    def test_pages_fail_closed_on_unknown_keys(self) -> None:
        """A declared rule the normalizer drops is a contract that lies.

        flow_prefix shipped exactly this way: declared in the KR plan,
        silently dropped by the fixed normalization key list, never executed.
        Unknown page keys must fail validation instead.
        """
        payload = _payload()
        payload["pages"][0]["flow_prefix"] = {
            "until_kind": "image",
            "occurrence": 1,
            "head_composition_id": "anything",
        }

        with self.assertRaisesRegex(
            TargetAssemblyPlanError,
            r"unknown page keys \['flow_prefix'\]",
        ):
            normalize_target_assembly_plan(
                payload,
                _manual_ir(payload),
                source_path=PLAN_PATH,
            )

    def test_assets_reject_the_removed_image_roles_field(self) -> None:
        payload = _payload()
        page = next(
            page for page in payload["pages"]
            if page["source_ref"] == "page/charging_en.rst"
        )
        page["composition_data"]["assets"] = {
            "image_refs": [],
            "image_roles": ["full_measure"],
        }

        with self.assertRaisesRegex(
            TargetAssemblyPlanError,
            "assets must contain exactly image_refs",
        ):
            normalize_target_assembly_plan(
                payload,
                _manual_ir(payload),
                source_path=PLAN_PATH,
            )

    def test_committed_plans_carry_no_dead_vocabulary(self) -> None:
        """Every committed candidate stays inside the executable vocabulary."""
        plans_dir = PLAN_PATH.parent
        dead_fields = {"flow_prefix", "image_roles", "control_layout_variant"}
        for plan_path in sorted(plans_dir.glob("*.json")):
            payload = json.loads(plan_path.read_text(encoding="utf-8"))
            for page in payload.get("pages", []):
                with self.subTest(plan=plan_path.name, page=page.get("source_ref")):
                    self.assertLessEqual(set(page), _PAGE_KEYS)
                    text = json.dumps(page, ensure_ascii=False)
                    for field in dead_fields:
                        self.assertNotIn(f'"{field}"', text)

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
