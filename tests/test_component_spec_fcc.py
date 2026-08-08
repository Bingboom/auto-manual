from __future__ import annotations

from pathlib import Path
import unittest

from tools.component_specs.fcc import (
    COMPONENT_ID,
    DEFAULT_MARK_ASSET_REF,
    fcc_component_spec,
    fcc_spec_from_legacy_payload,
)
from tools.component_specs.fcc_adapters import (
    idml_fcc_payload,
    latex_fcc_projection,
    web_fcc_projection,
    word_fcc_projection,
)
from tools.component_specs.model import ComponentSpecError
from tools.component_specs.projection import project_manual_ir_components
from tools.component_specs.registry import load_component_registry, validate_component_spec
from tools.component_specs.theme import load_manual_theme
from tools.manual_ir import ManualBlock, ManualIR, ManualPage
from tools.render_contract import load_render_contract
from tools.utils.path_utils import Paths


ROOT = Path(__file__).resolve().parents[1]
PATHS = Paths(root=ROOT)


class FccComponentSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_component_registry(PATHS.component_registry_contract)
        cls.theme = load_manual_theme(component_registry=cls.registry)

    def _legacy_spec(self, language: str = "en"):
        labels = {
            "en": ("NOTE:", "MODIFICATION:"),
            "fr": ("REMARQUE :", "MODIFICATION :"),
            "es": ("NOTA:", "MODIFICACIÓN:"),
        }
        note, modification = labels[language]
        payload = {
            "kind": "fcc",
            "texts": [
                "Opening condition one.\nOpening condition two.\n\n"
                f"{note} Tested copy.\nProtection copy.",
                "Corrective measures intro.\n\n"
                "• First measure.\n\n"
                "• Second measure.\n\n"
                f"{modification} Change copy.",
            ],
        }
        return payload, fcc_spec_from_legacy_payload(
            payload,
            source_ref=f"page/{language}_fcc.rst#block-2",
            language=language,
            registry=self.registry,
            theme=self.theme,
        )

    def test_registry_theme_and_style_bind_all_four_renderers(self) -> None:
        definition = self.registry["components"][COMPONENT_ID]
        self.assertEqual(COMPONENT_ID, definition["style_id"])
        self.assertEqual(
            {"web", "latex", "idml", "word"},
            set(definition["adapters"]),
        )
        self.assertEqual(
            [COMPONENT_ID],
            self.theme["component_roles"]["component.special.fcc"]["component_ids"],
        )
        style = load_render_contract(PATHS.manual_style_contract)["styles"][COMPONENT_ID]
        self.assertEqual(
            definition["adapters"]["web"]["capability"],
            style["web"]["capability"],
        )
        self.assertEqual(
            definition["adapters"]["word"]["capability"],
            style["word"]["capability"],
        )
        self.assertEqual("aligned", style["conformance"]["state"])
        self.assertEqual([], style["conformance"]["debt"])

    def test_legacy_payload_preserves_source_order_and_shared_asset_role(self) -> None:
        payload, spec = self._legacy_spec()
        self.assertEqual([], validate_component_spec(spec, self.registry))
        self.assertEqual(COMPONENT_ID, spec.component_id)
        self.assertEqual("two-column", spec.variant)
        self.assertEqual(["Opening condition one.", "Opening condition two."], spec.slot("opening_copy").content)
        self.assertEqual(2, spec.slot("column_break").content)
        self.assertEqual("compliance_mark", spec.assets[0].role)
        self.assertEqual(DEFAULT_MARK_ASSET_REF, spec.assets[0].asset_ref)
        self.assertEqual(payload, idml_fcc_payload(spec))

    def test_four_adapters_share_semantics_but_keep_renderer_geometry(self) -> None:
        payload, spec = self._legacy_spec()
        web = web_fcc_projection(spec)
        latex = latex_fcc_projection(spec)
        word = word_fcc_projection(spec)
        self.assertEqual("hb-fcc-composition", web["composition_class"])
        self.assertEqual("HBFccBlock", latex["macro"])
        self.assertEqual(payload["texts"], latex["arguments"])
        self.assertEqual("hb-fcc-word-table", word["table_class"])
        self.assertEqual(2, len(web["left_blocks"]))
        self.assertEqual(3, len(web["right_blocks"]))
        self.assertEqual(web["opening_copy"], word["opening_copy"])
        self.assertNotIn("geometry", spec.to_dict())

    def test_three_languages_keep_labels_lists_and_column_break(self) -> None:
        for language in ("en", "fr", "es"):
            with self.subTest(language=language):
                _, spec = self._legacy_spec(language)
                projection = web_fcc_projection(spec)
                left = projection["left_blocks"]
                right = projection["right_blocks"]
                self.assertEqual("paragraph", left[0]["kind"])
                self.assertTrue(left[0]["label"])
                self.assertEqual("list", right[1]["kind"])
                self.assertEqual(2, len(right[1]["items"]))
                self.assertTrue(right[2]["label"].casefold().startswith("modific"))

    def test_malformed_column_break_and_blocks_fail_closed(self) -> None:
        with self.assertRaises(ComponentSpecError):
            fcc_component_spec(
                accessibility_label="FCC",
                opening_copy=("Opening",),
                left_blocks=({"kind": "paragraph", "label": "", "text": "Left"},),
                right_blocks=({"kind": "video", "url": "unsafe"},),
                source_ref="page/fcc.rst#block-2",
                language="en",
                registry=self.registry,
                theme=self.theme,
            )

    def test_manual_ir_projects_fcc_source_identity_and_language(self) -> None:
        payload, _ = self._legacy_spec("fr")
        block = ManualBlock(
            block_id="page-1:block-2",
            source_ref="page/p22_01_fcc.rst#block-2",
            kind="component",
            payload=payload,
            content_sha256="a" * 64,
        )
        page = ManualPage(
            page_id="page-1",
            source_ref="page/p22_01_fcc.rst",
            source_path="page/p22_01_fcc.rst",
            language="fr",
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
        self.assertEqual(COMPONENT_ID, specs[0].component_id)
        self.assertEqual(block.source_ref, specs[0].source_ref)
        self.assertEqual("fr", specs[0].language)


if __name__ == "__main__":
    unittest.main()
