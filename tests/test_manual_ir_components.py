from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.callout import callout_component_spec
from tools.component_specs.fcc import fcc_component_spec
from tools.component_specs.projection import project_manual_ir_components
from tools.manual_ir import (
    V2_SCHEMA_VERSION,
    ManualSource,
    SourcePage,
    build_manual_ir_from_source,
)
from tools.manual_ir.components import (
    component_flow_node,
    component_specs_in_flow,
)
from tools.manual_ir.flow import (
    FLOW_V1_SCHEMA_VERSION,
    FLOW_V2_SCHEMA_VERSION,
    flow_nodes_to_html,
    html_to_flow_nodes,
    validate_flow_node,
)


class ManualIREmbeddedComponentTests(unittest.TestCase):
    def _callout(self):
        return callout_component_spec(
            label="CAUTION",
            body="Keep <em>rich</em> source copy.",
            items=(),
            source_ref="page/operations.rst#callout-1",
            language="en",
        )

    def _carrier(self):
        return html_to_flow_nodes(
            '<table class="manual-callout-table"><tbody><tr>'
            '<td class="manual-callout-label">CAUTION</td>'
            '<td class="manual-callout-body">Keep <em>rich</em> source copy.</td>'
            "</tr></tbody></table>"
        )

    def test_v2_component_node_is_nested_and_traversed_in_document_order(self):
        first = self._callout()
        second = callout_component_spec(
            label="NOTE",
            body="Second",
            items=(),
            source_ref="page/operations.rst#callout-2",
            language="en",
        )
        root = {
            "schema_version": FLOW_V2_SCHEMA_VERSION,
            "kind": "section",
            "children": [
                {"kind": "paragraph", "children": [{"kind": "text", "text": "Before"}]},
                component_flow_node(first, carrier_flow=self._carrier()),
                {"kind": "paragraph", "children": [{"kind": "text", "text": "Between"}]},
                component_flow_node(second),
            ],
        }

        self.assertEqual([], validate_flow_node(root))
        self.assertEqual(
            [first.source_ref, second.source_ref],
            [spec.source_ref for spec in component_specs_in_flow((root,))],
        )

        def render(node):
            spec = node["component_spec"]
            return f'<aside data-component-id="{spec["component_id"]}">{spec["source_ref"]}</aside>'

        replay = BeautifulSoup(
            flow_nodes_to_html((root,), component_renderer=render),
            "html.parser",
        )
        self.assertEqual(
            ["Before", first.source_ref, "Between", second.source_ref],
            [child.get_text(strip=True) for child in replay.section.find_all(recursive=False)],
        )

    def test_v1_rejects_components_and_v2_requires_registered_semantics(self):
        node = component_flow_node(self._callout(), root=True)
        self.assertEqual(FLOW_V2_SCHEMA_VERSION, node["schema_version"])
        self.assertEqual([], validate_flow_node(node))

        legacy = deepcopy(node)
        legacy["schema_version"] = FLOW_V1_SCHEMA_VERSION
        self.assertTrue(any("component" in issue for issue in validate_flow_node(legacy)))

        malformed = deepcopy(node)
        malformed["component_spec"]["component_id"] = "HB-NOT-REGISTERED"
        self.assertTrue(any("HB-NOT-REGISTERED" in issue for issue in validate_flow_node(malformed)))

        with self.assertRaisesRegex(ValueError, "component renderer"):
            flow_nodes_to_html((node,))

    def test_component_assets_join_the_manual_asset_union(self):
        spec = fcc_component_spec(
            accessibility_label="FCC",
            opening_copy=("Opening",),
            left_blocks=({"kind": "paragraph", "label": "", "text": "Left"},),
            right_blocks=({"kind": "paragraph", "label": "", "text": "Right"},),
            source_ref="page/fcc.rst",
            language="en",
            mark_asset_ref="assets/ir/fcc.png",
        )
        source = ManualSource(
            model="JE-1000F",
            region="US",
            language="en",
            source="fixture",
            bundle_root="fixture",
            bundle_sha256="a" * 64,
            snapshot_sha256=None,
            layout_params_sha256="b" * 64,
            style_contract_sha256="c" * 64,
            pages=(
                SourcePage(
                    page_id="fcc.rst",
                    source_ref="fcc.rst",
                    source_path=str(Path("page/fcc.rst")),
                    language="en",
                    source_sha256="d" * 64,
                    blocks=(("flow", component_flow_node(spec, root=True)),),
                ),
            ),
            metadata={"projection": "whole-document-components/v1"},
            schema_version=V2_SCHEMA_VERSION,
        )

        ir = build_manual_ir_from_source(source)
        self.assertEqual(("assets/ir/fcc.png",), ir.asset_refs)
        self.assertEqual(
            [spec.to_dict()],
            [candidate.to_dict() for candidate in project_manual_ir_components(ir)],
        )

    def test_duplicate_source_identity_and_nested_component_carrier_fail(self):
        spec = self._callout()
        duplicated = {
            "schema_version": FLOW_V2_SCHEMA_VERSION,
            "kind": "section",
            "children": [component_flow_node(spec), component_flow_node(spec)],
        }
        with self.assertRaisesRegex(ValueError, "duplicate embedded component"):
            component_specs_in_flow((duplicated,))

        nested = component_flow_node(spec, root=True)
        nested["carrier_flow"] = [component_flow_node(spec)]
        self.assertTrue(
            any("carrier cannot contain components" in issue for issue in validate_flow_node(nested))
        )


if __name__ == "__main__":
    unittest.main()
