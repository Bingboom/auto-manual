from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.projection import project_manual_ir_components
from tools.component_specs.registry import load_component_registry, validate_component_spec
from tools.component_specs.spec_table import (
    COMPONENT_ID,
    idml_spec_table_rows,
    latex_spec_table_rows,
    spec_table_component_spec,
    web_spec_table_projection,
    word_spec_table_projection,
)
from tools.component_specs.theme import load_manual_theme, validate_manual_theme
from tools.render_contract import load_layout_tokens, load_render_contract
from tools.manual_ir import ManualBlock, ManualIR, ManualPage
from tools.utils.path_utils import Paths


ROOT = Path(__file__).resolve().parents[1]
PATHS = Paths(root=ROOT)


class SpecTableComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_component_registry(PATHS.component_registry_contract)
        cls.layout_tokens = load_layout_tokens(PATHS.layout_params_csv)
        cls.theme = load_manual_theme(
            PATHS.manual_theme_contract,
            component_registry=cls.registry,
            layout_token_names=cls.layout_tokens,
        )

    def _spec(self):
        return spec_table_component_spec(
            section_title="INPUT PORTS",
            rows=(
                ("1 × AC Input", "Charge Mode: 100-120 V~ 60 Hz, 15 A max."),
                ("", "Bypass Mode①: 100-120 V~ 60 Hz, 12 A max."),
                (
                    "2 × DC8020 Ports",
                    "11 V-16 V⎓8 A max.\\n16 V-60 V⎓12 A max.",
                ),
            ),
            source_ref="spec_en.rst#input-ports",
            language="en",
            registry=self.registry,
            theme=self.theme,
        )

    def test_theme_path_and_registry_projection_are_valid(self) -> None:
        self.assertEqual(
            PATHS.renderer_contracts_dir / "manual_theme.yaml",
            PATHS.manual_theme_contract,
        )
        self.assertEqual(
            [],
            validate_manual_theme(
                self.theme,
                component_registry=self.registry,
                layout_token_names=self.layout_tokens,
            ),
        )
        self.assertEqual(
            "hb-manual-default",
            load_render_contract(PATHS.manual_style_contract)["theme_id"],
        )
        self.assertEqual(
            set(self.registry["components"]),
            {
                component_id
                for projection in self.theme["component_roles"].values()
                for component_id in projection["component_ids"]
            },
        )

    def test_theme_roles_have_four_bindings_and_live_consumers(self) -> None:
        consumed = {
            role
            for projection in self.theme["component_roles"].values()
            for role in projection["theme_roles"]
        }
        self.assertEqual(set(self.theme["roles"]), consumed)
        for role, definition in self.theme["roles"].items():
            with self.subTest(role=role):
                self.assertEqual(
                    {"web", "latex", "idml", "word"},
                    set(definition["bindings"]),
                )

    def test_theme_rejects_orphans_geometry_and_unknown_layout_tokens(self) -> None:
        orphan = deepcopy(self.theme)
        orphan["roles"]["surface.unused"] = deepcopy(
            orphan["roles"]["surface.paper"]
        )
        self.assertTrue(
            any(
                "surface.unused" in issue and "no component consumer" in issue
                for issue in validate_manual_theme(
                    orphan,
                    component_registry=self.registry,
                    layout_token_names=self.layout_tokens,
                )
            )
        )

        geometry = deepcopy(self.theme)
        geometry["roles"]["radius.panel"]["x"] = 12
        self.assertTrue(
            any(
                "unsupported keys ['x']" in issue
                for issue in validate_manual_theme(
                    geometry,
                    component_registry=self.registry,
                    layout_token_names=self.layout_tokens,
                )
            )
        )

        missing_token = deepcopy(self.theme)
        missing_token["roles"]["border.strong"]["bindings"]["latex"][
            "name"
        ] = "missing_table_rule"
        self.assertTrue(
            any(
                "unknown layout token 'missing_table_rule'" in issue
                for issue in validate_manual_theme(
                    missing_token,
                    component_registry=self.registry,
                    layout_token_names=self.layout_tokens,
                )
            )
        )

    def test_structured_rows_preserve_rowspan_multiline_and_references(self) -> None:
        spec = self._spec()
        self.assertEqual(COMPONENT_ID, spec.component_id)
        self.assertEqual([], validate_component_spec(spec, self.registry))
        groups = spec.slot("rows").content
        self.assertEqual(2, len(groups))
        self.assertEqual(2, groups[0]["label_rowspan"])
        self.assertEqual(["①"], groups[0]["values"][1]["references"])
        self.assertEqual(1, groups[1]["label_rowspan"])
        self.assertIn("\\n", groups[1]["values"][0]["text"])

        malformed = spec.to_dict()
        malformed["slots"][1]["content"][0]["label_rowspan"] = 99
        issues = validate_component_spec(
            ComponentSpec.from_dict(malformed),
            self.registry,
        )
        self.assertTrue(any("label_rowspan must equal value count" in issue for issue in issues))

    def test_four_renderer_adapters_preserve_existing_semantics(self) -> None:
        spec = self._spec()
        expected_rows = [
            ("1 × AC Input", "Charge Mode: 100-120 V~ 60 Hz, 15 A max."),
            ("", "Bypass Mode①: 100-120 V~ 60 Hz, 12 A max."),
            (
                "2 × DC8020 Ports",
                "11 V-16 V⎓8 A max.\\n16 V-60 V⎓12 A max.",
            ),
        ]
        self.assertEqual(expected_rows, latex_spec_table_rows(spec))
        self.assertEqual(expected_rows, idml_spec_table_rows(spec))
        web = web_spec_table_projection(spec)
        self.assertEqual("hb-spec-table-composition", web["composition_class"])
        self.assertIn("hb-spec-table", web["table_classes"])
        word = word_spec_table_projection(spec)
        self.assertEqual("INPUT PORTS", word["title"])
        self.assertEqual(2, word["groups"][0]["label_rowspan"])

    def test_all_four_sections_share_one_component_contract(self) -> None:
        titles = (
            "GENERAL INFO",
            "INPUT PORTS",
            "OUTPUT PORTS",
            "ENVIRONMENTAL OPERATING TEMPERATURE",
        )
        specs = [
            spec_table_component_spec(
                section_title=title,
                rows=((f"Label {index}", f"Value {index}"),),
                source_ref=f"spec_en.rst#section-{index}",
                language="en",
                registry=self.registry,
                theme=self.theme,
            )
            for index, title in enumerate(titles, start=1)
        ]
        self.assertEqual([COMPONENT_ID] * 4, [spec.component_id for spec in specs])
        self.assertEqual(list(titles), [spec.slot("section_title").content for spec in specs])

        style = load_render_contract(PATHS.manual_style_contract)["styles"][COMPONENT_ID]
        adapters = self.registry["components"][COMPONENT_ID]["adapters"]
        self.assertEqual(style["theme_token_roles"], ["component.table.spec"])
        self.assertEqual(style["web"]["capability"], adapters["web"]["capability"])
        self.assertEqual(style["word"]["capability"], adapters["word"]["capability"])

    def test_manual_ir_spec_section_projects_source_identity_and_language(self) -> None:
        block = ManualBlock(
            block_id="page-1:block-1",
            source_ref="page/spec_fr.rst#block-1",
            kind="data",
            payload={
                "kind": "spec_section",
                "title": "PORTS D’ENTRÉE",
                "rows": [["1 × Entrée CA", "Mode de charge"]],
            },
            content_sha256="a" * 64,
        )
        page = ManualPage(
            page_id="page-1",
            source_ref="page/spec_fr.rst",
            source_path="page/spec_fr.rst",
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

    def test_web_theme_bindings_preserve_container_width_and_mobile_overflow(self) -> None:
        css = (PATHS.renderer_contracts_dir / "web_manual.css").read_text(
            encoding="utf-8"
        )
        for definition in self.theme["roles"].values():
            binding = definition["bindings"]["web"]
            self.assertIn(binding["name"], css)
        self.assertIn(".hb-spec-table-composition", css)
        self.assertIn("max-width: var(--hb-component-band-max)", css)
        self.assertIn("overflow-x: auto", css)
        self.assertIn("min-width: 36rem", css)

    def test_table_source_rejects_orphan_blank_and_wide_rows(self) -> None:
        for rows in ((('', 'value'),), (("label", "value", "extra"),)):
            with self.subTest(rows=rows), self.assertRaises(ComponentSpecError):
                spec_table_component_spec(
                    section_title="GENERAL",
                    rows=rows,
                    source_ref="fixture",
                    language="en",
                    registry=self.registry,
                    theme=self.theme,
                )


if __name__ == "__main__":
    unittest.main()
