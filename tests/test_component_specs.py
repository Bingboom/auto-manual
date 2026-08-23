from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from tools.component_specs.adapters import (
    idml_notice_payload,
    latex_callout_macro,
    web_callout_classes,
    word_callout_markup,
)
from tools.component_specs.callout import (
    COMPONENT_ID,
    callout_component_spec,
    callout_spec_from_legacy_notice,
)
from tools.component_specs.model import (
    ComponentAsset,
    ComponentSlot,
    ComponentSpec,
    ComponentSpecError,
)
from tools.component_specs.projection import project_manual_ir_components
from tools.component_specs.registry import (
    REGISTERED_ADAPTER_KEYS,
    load_component_registry,
    validate_component_registry,
    validate_component_spec,
)
from tools.manual_ir import ManualBlock, ManualIR, ManualPage
from tools.render_contract import load_render_contract
from tools.utils.path_utils import Paths


ROOT = Path(__file__).resolve().parents[1]
PATHS = Paths(root=ROOT)


class ComponentSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_component_registry(PATHS.component_registry_contract)

    def _spec(self, label: str, *, variant: str | None = None) -> ComponentSpec:
        return callout_component_spec(
            label=label,
            body="Keep **inline emphasis** and source copy.",
            items=("First item", "Nested detail"),
            source_ref="page/demo.rst#block-1",
            language="en",
            variant=variant,
            registry=self.registry,
        )

    def test_registry_path_and_four_renderer_bindings_are_valid(self) -> None:
        self.assertEqual(
            PATHS.renderer_contracts_dir / "component_registry.yaml",
            PATHS.component_registry_contract,
        )
        self.assertEqual([], validate_component_registry(self.registry))
        adapters = self.registry["components"][COMPONENT_ID]["adapters"]
        self.assertEqual(
            COMPONENT_ID,
            self.registry["components"][COMPONENT_ID]["style_id"],
        )
        self.assertEqual(set(REGISTERED_ADAPTER_KEYS), set(adapters))
        for renderer, binding in adapters.items():
            with self.subTest(renderer=renderer):
                self.assertIn(binding["key"], REGISTERED_ADAPTER_KEYS[renderer])

    def test_all_callout_variants_share_one_component_and_dispatch(self) -> None:
        expected = {
            "WARNING": ("warning", "HBWarningBlock"),
            "DANGER": ("danger", "HBWarningBlock"),
            "CAUTION": ("caution", "HBCautionBlock"),
            "NOTE": ("note", "HBNoteBlock"),
            "TIP": ("tip", "HBTipBlock"),
        }
        for label, (variant, macro) in expected.items():
            with self.subTest(label=label):
                spec = self._spec(label)
                self.assertEqual(COMPONENT_ID, spec.component_id)
                self.assertEqual(variant, spec.variant)
                self.assertEqual([], validate_component_spec(spec, self.registry))
                self.assertEqual(macro, latex_callout_macro(spec))
                self.assertEqual(
                    "manual-callout-table",
                    web_callout_classes(spec)["table"],
                )
                self.assertEqual(
                    "manual-callout-table",
                    word_callout_markup(spec)["table_class"],
                )
                self.assertEqual("notice", idml_notice_payload(spec)["kind"])

    def test_localized_labels_resolve_without_adapter_translation(self) -> None:
        for label, expected in (
            ("AVERTISSEMENT", "warning"),
            ("ATTENTION", "caution"),
            ("REMARQUE", "note"),
            ("CONSEJOS", "tip"),
            ("PELIGRO", "danger"),
            ("PRECAUCIÓN", "caution"),
            ("NOTES", "note"),
            ("REMARQUES", "note"),
            ("NOTAS", "note"),
            ("OBSERVACIONES", "note"),
            ("IMPORTANT", "note"),
        ):
            with self.subTest(label=label):
                spec = self._spec(label)
                self.assertEqual(expected, spec.variant)
                self.assertEqual(label, spec.slot("label").content)

    def test_unknown_ids_variants_slots_assets_and_adapter_keys_fail_closed(self) -> None:
        valid = self._spec("NOTE")
        unknown_id = ComponentSpec(
            component_id="HB-UNKNOWN",
            variant=valid.variant,
            source_ref=valid.source_ref,
            language=valid.language,
            slots=valid.slots,
            assets=(),
            token_roles=valid.token_roles,
        )
        self.assertIn("unknown component_id 'HB-UNKNOWN'", validate_component_spec(unknown_id, self.registry))

        unknown_variant = ComponentSpec(
            component_id=valid.component_id,
            variant="urgent",
            source_ref=valid.source_ref,
            language=valid.language,
            slots=valid.slots,
            assets=(),
            token_roles=valid.token_roles,
        )
        self.assertTrue(any("unknown variant 'urgent'" in issue for issue in validate_component_spec(unknown_variant, self.registry)))

        malformed_slots = ComponentSpec(
            component_id=valid.component_id,
            variant=valid.variant,
            source_ref=valid.source_ref,
            language=valid.language,
            slots=valid.slots + (ComponentSlot("mystery", "text", "x"),),
            assets=(ComponentAsset("icon", "asset.png", "exact"),),
            token_roles=valid.token_roles,
        )
        malformed_issues = validate_component_spec(malformed_slots, self.registry)
        self.assertTrue(any("unknown slot role 'mystery'" in issue for issue in malformed_issues))
        self.assertTrue(any("unknown asset role 'icon'" in issue for issue in malformed_issues))

        bad_registry = deepcopy(self.registry)
        bad_registry["components"][COMPONENT_ID]["adapters"]["web"]["key"] = "css_guess"
        self.assertTrue(any("css_guess" in issue for issue in validate_component_registry(bad_registry)))

        extra_renderer_registry = deepcopy(self.registry)
        extra_renderer_registry["components"][COMPONENT_ID]["adapters"]["canvas"] = {
            "capability": "rendered",
            "key": "canvas_callout",
        }
        self.assertTrue(
            any(
                "unknown renderer 'canvas'" in issue
                for issue in validate_component_registry(extra_renderer_registry)
            )
        )

    def test_deserialization_rejects_malformed_slots_assets_and_tokens(self) -> None:
        payload = self._spec("NOTE").to_dict()
        for field, malformed in (
            ("slots", ["not-a-slot"]),
            ("assets", ["not-an-asset"]),
            ("token_roles", [1]),
            ("metadata", []),
        ):
            with self.subTest(field=field):
                candidate = deepcopy(payload)
                candidate[field] = malformed
                with self.assertRaises(ComponentSpecError):
                    ComponentSpec.from_dict(candidate)

    def test_legacy_idml_payload_round_trips_without_geometry_change(self) -> None:
        payload = {
            "kind": "notice",
            "label": "Localized note",
            "texts": ["First", "Second"],
            "list": True,
            "body_width": 123.4,
            "layout_role": "charging_note",
        }
        spec = callout_spec_from_legacy_notice(
            payload,
            source_ref="page/08_charging_methods.rst#block-2",
            language="fr",
            registry=self.registry,
        )
        self.assertEqual("note", spec.variant)
        self.assertEqual(payload, idml_notice_payload(spec))

    def test_manual_ir_projection_preserves_source_ref_language_and_copy(self) -> None:
        payload = {
            "kind": "notice",
            "label": "CAUTION",
            "variant": "caution",
            "texts": ["Body", "Second"],
            "list": True,
        }
        block = ManualBlock(
            block_id="page-1:block-1",
            source_ref="page/06_ups_mode.rst#block-1",
            kind="component",
            payload=payload,
            content_sha256="a" * 64,
        )
        page = ManualPage(
            page_id="page-1",
            source_ref="page/06_ups_mode.rst",
            source_path="page/06_ups_mode.rst",
            language="es",
            source_sha256="b" * 64,
            skipped_raw=0,
            blocks=(block,),
        )
        ir = ManualIR(
            model="JE-1000F",
            region="US",
            language="en",
            source="fixture",
            bundle_root="fixture",
            bundle_sha256="c" * 64,
            snapshot_sha256="d" * 64,
            layout_params_sha256="e" * 64,
            style_contract_sha256="f" * 64,
            content_sha256="1" * 64,
            pages=(page,),
        )
        specs = project_manual_ir_components(ir)
        self.assertEqual(1, len(specs))
        self.assertEqual(block.source_ref, specs[0].source_ref)
        self.assertEqual("es", specs[0].language)
        self.assertEqual(["Body", "Second"], specs[0].slot("items").content)

    def test_component_capabilities_match_style_contract(self) -> None:
        style_contract = load_render_contract(PATHS.manual_style_contract)
        style = style_contract["styles"][COMPONENT_ID]
        adapters = self.registry["components"][COMPONENT_ID]["adapters"]
        component = self.registry["components"][COMPONENT_ID]
        self.assertEqual(style["variants"], component["variants"])
        self.assertEqual(COMPONENT_ID, component["style_id"])
        self.assertEqual(style["web"]["capability"], adapters["web"]["capability"])
        self.assertEqual(style["word"]["capability"], adapters["word"]["capability"])
        self.assertEqual(style["theme_token_roles"], self.registry["components"][COMPONENT_ID]["token_roles"])


if __name__ == "__main__":
    unittest.main()
