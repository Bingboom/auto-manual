from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from tools.component_specs.model import ComponentSpecError
from tools.component_specs.overview import (
    COMPOSITE_VARIANT,
    COMPONENT_ID,
    LIVE_VARIANT,
    overview_component_spec,
    overview_spec_from_blocks,
)
from tools.component_specs.overview_adapters import (
    idml_overview_projection,
    latex_overview_projection,
    web_overview_projection,
    word_overview_projection,
)
from tools.component_specs.overview_instance import (
    load_overview_instance_registry,
    resolve_overview_instance,
    validate_overview_instance_registry,
)
from tools.component_specs.projection import project_manual_ir_components
from tools.component_specs.registry import load_component_registry, validate_component_spec
from tools.component_specs.theme import load_manual_theme
from tools.manual_ir import ManualBlock, ManualIR, ManualPage
from tools.render_contract import load_render_contract
from tools.utils.path_utils import Paths


ROOT = Path(__file__).resolve().parents[1]
PATHS = Paths(root=ROOT)


class OverviewComponentSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_component_registry(PATHS.component_registry_contract)
        cls.theme = load_manual_theme(component_registry=cls.registry)
        cls.instance_registry = load_overview_instance_registry(
            PATHS.overview_component_instances_contract
        )
        cls.instance = resolve_overview_instance(
            model="JE-1000F",
            region="US",
            registry=cls.instance_registry,
        )

    def _views(self) -> list[dict[str, object]]:
        return [
            {
                "id": str(view["id"]),
                "title": f"{str(view['id']).upper()} VIEW",
                "image_ref": f"assets/{view['id']}.png",
                "alt": f"{view['id']} product view",
                "callouts": [
                    {
                        "id": str(callout["id"]),
                        "label": str(callout["id"]).replace("_", " ").title(),
                        "body": [f"Live {callout['id']} copy"],
                    }
                    for callout in view["callouts"]
                ],
            }
            for view in self.instance["views"]
        ]

    def _spec(self, *, variant: str = LIVE_VARIANT):
        return overview_component_spec(
            accessibility_label="PRODUCT OVERVIEW",
            views=self._views(),
            geometry_ref=str(self.instance["instance_id"]),
            source_ref="page/03_product_overview_placeholder.rst",
            language="en",
            variant=variant,
            registry=self.registry,
            theme=self.theme,
        )

    def test_registry_theme_style_and_instance_bind_all_four_renderers(self) -> None:
        self.assertEqual([], validate_overview_instance_registry(self.instance_registry))
        definition = self.registry["components"][COMPONENT_ID]
        self.assertEqual(
            {"web", "latex", "idml", "word"},
            set(definition["adapters"]),
        )
        self.assertEqual(
            [COMPONENT_ID],
            self.theme["component_roles"]["component.special.overview"][
                "component_ids"
            ],
        )
        style = load_render_contract(PATHS.manual_style_contract)["styles"][COMPONENT_ID]
        self.assertEqual("aligned", style["conformance"]["state"])
        self.assertEqual([], style["conformance"]["debt"])

    def test_target_resolution_is_exact_and_unknown_targets_fail_closed(self) -> None:
        self.assertEqual("je1000f-us-v1", self.instance["instance_id"])
        battery_pack = resolve_overview_instance(
            model="JBP-2000B",
            region="US",
            registry=self.instance_registry,
        )
        self.assertEqual("jbp2000b-us-v1", battery_pack["instance_id"])
        self.assertEqual(
            ["power", "lcd", "handle", "port_a", "port_b"],
            [
                callout["id"]
                for view in battery_pack["views"]
                for callout in view["callouts"]
            ],
        )
        self.assertEqual(
            self.instance,
            resolve_overview_instance(
                model=None,
                region=None,
                instance_id="je1000f-us-v1",
                registry=self.instance_registry,
            ),
        )
        with self.assertRaisesRegex(ComponentSpecError, "found 0"):
            resolve_overview_instance(
                model="JE-1000F",
                region="EU",
                registry=self.instance_registry,
            )
        with self.assertRaisesRegex(ComponentSpecError, "unknown overview instance"):
            resolve_overview_instance(
                model=None,
                region=None,
                instance_id="missing-target",
                registry=self.instance_registry,
            )

    def test_battery_pack_instance_projects_only_target_difference_slots(self) -> None:
        instance = resolve_overview_instance(
            model="JBP-2000B",
            region="US",
            registry=self.instance_registry,
        )
        blocks = [
            ("h1", "PRODUCT OVERVIEW"),
            ("h2", "FRONT VIEW"),
            ("image", "overview/jbp2000b/front_controls.png"),
            ("table", [["**POWER button**", "**LCD Display**"]]),
            ("h2", "LEFT SIDE VIEW"),
            ("image", "overview/jbp2000b/left_side_ports.png"),
            (
                "table",
                [
                    [
                        "**Handle**",
                        "**DC Expansion Port A** (Connect to Terminal A)",
                    ],
                    [
                        "",
                        "**DC Expansion Port B** (Connect to Terminal B)",
                    ],
                ],
            ),
        ]
        spec = overview_spec_from_blocks(
            blocks,
            instance=instance,
            source_ref="page/product_overview_en.rst",
            language="en",
        )
        projection = idml_overview_projection(spec, instance)

        self.assertEqual("jbp2000b-us-v1", projection["geometry_ref"])
        self.assertEqual(2, len(projection["views"]))
        self.assertEqual(
            [42.0, 365.5, 105.0, 12.0],
            projection["views"][0]["heading_text_rect"],
        )
        self.assertEqual(5, sum(len(view["callouts"]) for view in projection["views"]))
        self.assertEqual(5, len(projection["leaders"]))
        self.assertEqual(
            ["POWER button", "LCD Display", "Handle", "DC Expansion Port A", "DC Expansion Port B"],
            [
                callout["label"]
                for view in projection["views"]
                for callout in view["callouts"]
            ],
        )

    def test_two_variants_share_live_semantics_and_asset_roles(self) -> None:
        for variant in (LIVE_VARIANT, COMPOSITE_VARIANT):
            with self.subTest(variant=variant):
                spec = self._spec(variant=variant)
                self.assertEqual([], validate_component_spec(spec, self.registry))
                self.assertEqual(variant, spec.variant)
                self.assertEqual(["front_art", "right_art"], [a.role for a in spec.assets])
                self.assertEqual(15, sum(len(view["callouts"]) for view in spec.slot("views").content))
                self.assertNotIn("rect", spec.to_dict())

    def test_four_adapters_share_two_views_and_keep_geometry_target_scoped(self) -> None:
        spec = self._spec()
        web = web_overview_projection(spec, self.instance)
        latex = latex_overview_projection(spec, self.instance)
        idml = idml_overview_projection(spec, self.instance)
        word = word_overview_projection(spec, self.instance)
        self.assertEqual(2, len(web["views"]))
        self.assertEqual(15, sum(len(view["callouts"]) for view in web["views"]))
        self.assertEqual(2, len(latex["panels"]))
        self.assertEqual("HBOverviewPanel", latex["panels"][0]["macro"])
        self.assertEqual(16, len(idml["leaders"]))
        self.assertEqual(15, sum(leader["stroke_weight"] == 0.3 for leader in idml["leaders"]))
        self.assertEqual(1, sum(leader["stroke_weight"] == 0.6 for leader in idml["leaders"]))
        self.assertEqual("hb-overview-word-section", word["section_class"])
        self.assertNotIn("page", web)
        self.assertNotIn("page", word)

    def test_adapter_rejects_geometry_from_another_instance(self) -> None:
        wrong = deepcopy(self.instance)
        wrong["instance_id"] = "other-instance"
        with self.assertRaisesRegex(ComponentSpecError, "expected geometry instance"):
            web_overview_projection(self._spec(), wrong)

    def test_manual_ir_projects_overview_source_identity(self) -> None:
        source_ref = "page/03_product_overview_placeholder.rst"
        payloads: list[tuple[str, object]] = [
            ("h1", "PRODUCT OVERVIEW"),
            ("h2", "FRONT VIEW"),
            ("image", "front.png"),
            (
                "table",
                [
                    ["**Power Button**", "**LCD**"],
                    ["**DC 12 V Port**", "**LED Light Button**"],
                    ["**DC / USB Power Button**", "**LED Light**"],
                    ["**USB-C 30 W Output**", "**AC Power Button**"],
                    ["**USB-C 100 W Output**", "**AC Output**"],
                    ["**USB-A 18 W Output**"],
                ],
            ),
            ("table", [["**Total Output** 1500 W"]]),
            ("h2", "RIGHT SIDE VIEW"),
            ("image", "right.png"),
            (
                "table",
                [
                    ["**Handle**", "**AC Input** 100-120 V~"],
                    ["", "**DC Input** PV and Car"],
                ],
            ),
        ]
        blocks = tuple(
            ManualBlock(
                block_id=f"overview:block-{index}",
                source_ref=f"{source_ref}#block-{index}",
                kind=kind,
                payload=payload,
                content_sha256=f"{index:064x}",
            )
            for index, (kind, payload) in enumerate(payloads, start=1)
        )
        page = ManualPage(
            page_id="overview",
            source_ref=source_ref,
            source_path=source_ref,
            language="en",
            source_sha256="a" * 64,
            skipped_raw=0,
            blocks=blocks,
        )
        ir = ManualIR(
            model="JE-1000F",
            region="US",
            language="en",
            source="fixture",
            bundle_root="fixture",
            bundle_sha256="b" * 64,
            snapshot_sha256="c" * 64,
            layout_params_sha256="d" * 64,
            style_contract_sha256="e" * 64,
            content_sha256="f" * 64,
            pages=(page,),
        )
        spec = next(
            candidate
            for candidate in project_manual_ir_components(ir)
            if candidate.component_id == COMPONENT_ID
        )
        self.assertEqual(source_ref, spec.source_ref)
        self.assertEqual("en", spec.language)
        self.assertEqual(["front_art", "right_art"], [asset.role for asset in spec.assets])
        self.assertEqual(15, sum(len(view["callouts"]) for view in spec.slot("views").content))

    def test_idml_block_adapter_preserves_legacy_right_view_marker(self) -> None:
        blocks = [
            ("h1", "APERÇU DU PRODUIT"),
            ("h2", "VUE DE FACE"),
            ("image", "front.png"),
            (
                "table",
                [
                    ["**Power**", "**LCD**"],
                    ["**DC 12 V**", "**LED button**"],
                    ["**DC / USB**", "**LED**"],
                    ["**USB-C 30 W**", "**AC button**"],
                    ["**USB-C 100 W**"],
                    ["**USB-A 18 W**", "**AC Output**"],
                ],
            ),
            ("table", [["**Total Output**"]]),
            ("h2", "VUE LATÉRALE DROITE"),
            ("image", "right.png"),
            (
                "table",
                [
                    ["**Poignée** -"],
                    ["**Entrée CA** 100-120 V~", "**Entrée CC** PV et voiture"],
                ],
            ),
        ]
        spec = overview_spec_from_blocks(
            blocks,
            instance=self.instance,
            source_ref="page/p24_03_product_overview_placeholder.rst",
            language="fr",
        )
        right = spec.slot("views").content[1]
        self.assertEqual(["-"], right["callouts"][0]["body"])

if __name__ == "__main__":
    unittest.main()
