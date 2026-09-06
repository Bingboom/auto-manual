from __future__ import annotations

from copy import deepcopy
import json
import unittest

from bs4 import BeautifulSoup

from tools.manual_ir.flow import (
    FLOW_SCHEMA_VERSION,
    flow_nodes_to_html,
    html_to_flow_nodes,
    strip_presentation_hints,
    validate_flow_node,
)


MARKUP = """
<h1 id="intro" class="hb-title">Introduction</h1>
<p>Read <strong>carefully</strong>, <em>then</em> open
<a href="#details" class="reference">details</a><br/>H<sub>2</sub>O.</p>
<section id="details"><h2>Details</h2>
<ul class="simple"><li>One</li><li>Two</li></ul>
<ol><li>First</li></ol>
<table class="manual-table" style="width: 100%"><thead><tr>
<th scope="col">Name</th><th scope="col">Value</th></tr></thead>
<tbody><tr><th scope="row" rowspan="2">Input</th><td>100 V</td></tr>
<tr><td>200 V</td></tr></tbody></table>
<figure><img src="assets/unit.png" alt="Unit" aria-hidden="false"
class="manual-finished-illustration" data-proof="approved" style="width: 100%"/>
<figcaption>Product view</figcaption></figure></section>
""".strip()


def _walk(node):
    yield node
    for child in node.get("children", []):
        yield from _walk(child)


class ManualIRFlowTests(unittest.TestCase):
    def test_html_maps_to_renderer_neutral_semantics_without_serialized_tags(self) -> None:
        nodes = html_to_flow_nodes(MARKUP)
        encoded = json.dumps(nodes, ensure_ascii=False, sort_keys=True)
        self.assertNotIn('"type"', encoded)
        self.assertNotIn('"tag"', encoded)

        kinds = {node["kind"] for root in nodes for node in _walk(root)}
        self.assertTrue(
            {
                "heading",
                "paragraph",
                "strong",
                "emphasis",
                "link",
                "line_break",
                "subscript",
                "section",
                "list",
                "list_item",
                "table",
                "table_head",
                "table_body",
                "table_row",
                "table_cell",
                "figure",
                "image",
                "caption",
                "text",
            }.issubset(kinds)
        )

        heading = nodes[0]
        self.assertEqual(("heading", 1, "intro"), (
            heading["kind"], heading["level"], heading["anchor"]
        ))
        link = next(node for root in nodes for node in _walk(root) if node["kind"] == "link")
        image = next(node for root in nodes for node in _walk(root) if node["kind"] == "image")
        cell = next(
            node for root in nodes for node in _walk(root)
            if node["kind"] == "table_cell" and node.get("row_span") == 2
        )
        self.assertEqual("#details", link["target"])
        self.assertEqual(("assets/unit.png", "Unit", False), (
            image["source"], image["alt"], image["hidden"]
        ))
        self.assertEqual((True, "row", 2), (
            cell["header"], cell["scope"], cell["row_span"]
        ))

        image_hints = image["presentation"]["html"]["attributes"]
        self.assertEqual(
            {
                "class": ["manual-finished-illustration"],
                "data-proof": "approved",
                "style": "width: 100%",
            },
            image_hints,
        )
        for root in nodes:
            for candidate in _walk(root):
                hint_attributes = (
                    candidate.get("presentation", {})
                    .get("html", {})
                    .get("attributes", {})
                )
                for semantic_key in (
                    "src",
                    "alt",
                    "href",
                    "id",
                    "rowspan",
                    "scope",
                    "aria-hidden",
                ):
                    self.assertNotIn(semantic_key, hint_attributes)

    def test_web_round_trip_is_stable_but_semantics_survive_without_hints(self) -> None:
        nodes = html_to_flow_nodes(MARKUP)
        self.assertEqual(
            str(BeautifulSoup(MARKUP, "html.parser")),
            flow_nodes_to_html(nodes),
        )

        neutral = strip_presentation_hints(nodes)
        self.assertNotIn("presentation", json.dumps(neutral))
        replay = BeautifulSoup(flow_nodes_to_html(neutral), "html.parser")
        self.assertEqual("Introduction", replay.h1.get_text(strip=True))
        self.assertEqual("#details", replay.a["href"])
        self.assertEqual(["One", "Two"], [item.get_text(strip=True) for item in replay.ul.find_all("li")])
        self.assertEqual("2", replay.select_one("th[rowspan]")["rowspan"])
        self.assertEqual("assets/unit.png", replay.img["src"])
        self.assertEqual("Unit", replay.img["alt"])
        self.assertFalse(replay.img.has_attr("class"))

    def test_flow_validation_rejects_unknown_shapes_and_semantic_hint_conflicts(self) -> None:
        node = html_to_flow_nodes('<img src="assets/unit.png" alt="Unit">')[0]
        self.assertEqual([], validate_flow_node(node))
        cases = []

        unknown = deepcopy(node)
        unknown["kind"] = "html_div"
        cases.append((unknown, "unknown kind"))

        missing = deepcopy(node)
        del missing["source"]
        cases.append((missing, "source"))

        conflict = deepcopy(node)
        conflict.setdefault("presentation", {}).setdefault("html", {}).setdefault(
            "attributes", {}
        )["src"] = "other.png"
        cases.append((conflict, "semantic attribute"))

        extra = deepcopy(node)
        extra["html"] = {"tag": "img"}
        cases.append((extra, "unknown field"))

        bad_version = deepcopy(node)
        bad_version["schema_version"] = "manual-flow/v3"
        cases.append((bad_version, "schema_version"))

        for candidate, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                issues = validate_flow_node(candidate)
                self.assertTrue(any(diagnostic in issue for issue in issues), issues)

    def test_unknown_html_element_fails_instead_of_becoming_an_opaque_dom_node(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported document content"):
            html_to_flow_nodes("<video></video>")

    def test_every_root_records_the_flow_schema(self) -> None:
        nodes = html_to_flow_nodes("<p>One</p><p>Two</p>")
        self.assertEqual(
            [FLOW_SCHEMA_VERSION, FLOW_SCHEMA_VERSION],
            [node["schema_version"] for node in nodes],
        )

    def test_empty_fragment_keeps_one_neutral_block_and_replays_empty(self) -> None:
        nodes = html_to_flow_nodes("")
        self.assertEqual(({
            "schema_version": FLOW_SCHEMA_VERSION,
            "kind": "text",
            "text": "",
        },), nodes)
        self.assertEqual("", flow_nodes_to_html(nodes))

    def test_fields_are_strict_and_list_start_preserves_html_integer(self) -> None:
        node = html_to_flow_nodes('<ol start="-2"><li>Earlier</li></ol>')[0]
        self.assertEqual(-2, node["start"])
        self.assertEqual(
            str(BeautifulSoup('<ol start="-2"><li>Earlier</li></ol>', "html.parser")),
            flow_nodes_to_html((node,)),
        )

        image = html_to_flow_nodes('<img src="assets/unit.png">')[0]
        cases = []
        text_with_ignored_anchor = {
            "schema_version": FLOW_SCHEMA_VERSION,
            "kind": "text",
            "text": "copy",
            "anchor": "ignored",
        }
        cases.append((text_with_ignored_anchor, "unknown field"))

        uppercase_conflict = deepcopy(image)
        uppercase_conflict["presentation"] = {
            "html": {"attributes": {"SRC": "other.png"}}
        }
        cases.append((uppercase_conflict, "semantic attribute"))

        for candidate, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                issues = validate_flow_node(candidate)
                self.assertTrue(any(diagnostic in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
