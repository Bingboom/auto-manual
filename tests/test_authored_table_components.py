"""Actual small-product sources preserve their table semantics in shared IR."""
from copy import deepcopy
from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.authored_tables_html import parse_authored_tables
from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.reference_table import reference_table_projection
from tools.manual_ir.whole_document_components import discover_registered_components
from tools.web.presentation import load_web_manual_contract
from tools.web.reference_table_component import render_reference_table_component
from tools.word_bundle_html import _publish_rst_fragment_to_html, _rewrite_word_friendly_fragment

ROOT = Path(__file__).resolve().parents[1]


def _source(model, stem):
    path = ROOT / "docs/templates" / f"page_{model.lower().replace('-', '')}_eu-en" / f"{stem}_en.rst"
    html = _rewrite_word_friendly_fragment(
        _publish_rst_fragment_to_html(path.read_text(), path, active_tags={"region_eu"}), lang="en",
    )
    return path, BeautifulSoup(html, "html.parser")


class AuthoredTableComponentsTests(unittest.TestCase):
    def test_authored_signal_roles_preserve_unregistered_printed_labels(self):
        markup = '<h1>Symbols</h1><table class="hb-source-signals"><thead><tr><th>Label</th><th>Meaning</th></tr></thead><tbody>'
        for variant in ("warning", "caution", "note", "tip"):
            markup += f'<tr><td><span class="hb-signal-{variant}">Source label</span></td><td>Meaning</td></tr>'
        markup += '</tbody></table>'
        soup = BeautifulSoup(markup, "html.parser")
        spec = parse_authored_tables(soup, source_path=Path("symbols.rst"), language="pl")[0][0]
        self.assertEqual([True, True, False, False], [r["show_icon"] for r in spec.slot("rows").content])
        self.assertTrue(all(r["label"] == "Source label" for r in spec.slot("rows").content))
        soup.select_one("span")["class"].append("hb-signal-note")
        with self.assertRaisesRegex(ValueError, "conflicting semantic roles"):
            parse_authored_tables(soup, source_path=Path("symbols.rst"), language="pl")

    def test_all_real_tables_are_bound_and_reference_cells_preserved(self):
        for model, expected in (("JE-100C", 12), ("JE-300D", 9), ("JE-500A", 8)):
            with self.subTest(model=model):
                total = 0
                for stem in ("spec", "lcd_display", "operation", "symbol_meaning", "troubleshooting"):
                    if model == "JE-100C" and stem == "troubleshooting":
                        continue
                    path, soup = _source(model, stem)
                    claims = discover_registered_components(
                        soup, source_path=path, model=model, region="EU", language="en",
                        contract=load_web_manual_contract(model=model, region="EU"),
                    )
                    table_claims = [c for c in claims if c.spec.component_id.startswith("HB-TABLE-")]
                    total += len(table_claims)
                    for claim in table_claims:
                        if claim.spec.component_id != "HB-TABLE-REFERENCE":
                            continue
                        before = claim.owned_nodes[0]
                        after = BeautifulSoup(render_reference_table_component(claim.spec), "html.parser").table
                        self.assertEqual(
                            [c.decode_contents() for c in before.select("td,th")],
                            [c.decode_contents() for c in after.select("td,th")],
                        )
                        for renderer in ("web", "idml", "word", "latex"):
                            self.assertEqual(claim.spec.variant, reference_table_projection(claim.spec, renderer)["variant"])
                self.assertEqual(expected, total)

    def test_source_fault_table_has_three_columns_and_no_fabricated_numbers(self):
        path, soup = _source("JE-100C", "lcd_display")
        claims = discover_registered_components(
            soup, source_path=path, model="JE-100C", region="EU", language="en",
            contract=load_web_manual_contract(model="JE-100C", region="EU"),
        )
        self.assertEqual(4, len(claims))
        fault = claims[1].spec
        self.assertEqual("icon-catalog-unnumbered", fault.variant)
        self.assertEqual(3, len(fault.assets))
        self.assertTrue(all("number_text" not in row for row in fault.slot("rows").content))

    def test_undeclared_tables_are_not_classified_by_shape(self):
        markup = '<h1>LCD</h1><table><tr><td>1</td><td>Name</td><td>Meaning</td></tr></table>'
        self.assertEqual((), parse_authored_tables(BeautifulSoup(markup, "html.parser"), source_path=Path("lcd.rst"), language="en"))

    def test_malformed_declared_table_fails_without_mutating_source(self):
        for change in ("span", "extra-cell", "missing-head", "conflicting-role", "image"):
            with self.subTest(change=change):
                path, soup = _source("JE-500A", "lcd_display")
                if change == "span":
                    soup.td["rowspan"] = "2"
                elif change == "extra-cell":
                    soup.tr.append(soup.new_tag("td"))
                elif change == "missing-head":
                    soup.thead.unwrap()
                elif change == "conflicting-role":
                    soup.table["class"].append("hb-source-signals")
                else:
                    soup.td.append(soup.new_tag("img", src="invented.png"))
                before = str(soup)
                with self.assertRaises((ValueError, ComponentSpecError)):
                    parse_authored_tables(soup, source_path=path, language="en")
                self.assertEqual(before, str(soup))

    def test_replay_rejects_drifted_cells_and_column_geometry(self):
        path, soup = _source("JE-500A", "lcd_display")
        spec = parse_authored_tables(soup, source_path=path, language="en")[0][0]
        for mutation in ("text", "columns"):
            data = deepcopy(spec.to_dict())
            row = next(s for s in data["slots"] if s["role"] == "rows")["content"][0]
            if mutation == "text":
                row[0]["text"] = "WRONG"
            else:
                row.pop()
            with self.assertRaises((ValueError, ComponentSpecError)):
                render_reference_table_component(ComponentSpec.from_dict(data))


if __name__ == "__main__":
    unittest.main()
