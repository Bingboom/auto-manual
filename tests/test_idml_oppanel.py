"""Tests for the operation-panel detection pass (tools/idml/oppanel.py)."""
from __future__ import annotations

import json
import unittest

from tools.idml.oppanel import parse_rows, transform


class ParseRowsTest(unittest.TestCase):
    def test_colon_form(self) -> None:
        self.assertEqual(
            [("On", "Press once."), ("Off", "Press and hold for 3s.")],
            parse_rows("On: Press once.\nOff: Press and hold for 3s."),
        )

    def test_bold_label_form(self) -> None:
        self.assertEqual(
            [("On", "Press once"), ("Off", "Press once")],
            parse_rows("**On**\nPress once\n**Off**\nPress once"),
        )

    def test_localized_labels(self) -> None:
        self.assertEqual(
            [("Marche", "appuyez une fois"), ("Arrêt", "appuyez une fois")],
            parse_rows("**Marche**\nappuyez une fois\n**Arrêt**\nappuyez une fois"),
        )

    def test_non_panel_body_returns_none(self) -> None:
        self.assertIsNone(parse_rows("Just a paragraph of text."))
        self.assertIsNone(parse_rows("On: only one row"))


class TransformTest(unittest.TestCase):
    def test_image_plus_rows_with_prereq_becomes_component(self) -> None:
        blocks = [
            ("h2", "AC OUTPUT ON/OFF"),
            ("body", "**Prerequisite**: The product is powered on."),
            ("image", "_assets/x/ac_output.png"),
            ("body", "**On**\nPress once\n**Off**\nPress once"),
            ("body", "Trailing paragraph."),
        ]
        out = transform(blocks)
        kinds = [k for k, _ in out]
        self.assertEqual(["h2", "component", "body"], kinds)
        spec = json.loads(out[1][1])
        self.assertEqual("oppanel", spec["kind"])
        self.assertEqual("_assets/x/ac_output.png", spec["image"])
        self.assertTrue(spec["prereq"].startswith("Prerequisite"))
        self.assertEqual([["On", "Press once"], ["Off", "Press once"]], spec["rows"])

    def test_flattened_langtag_becomes_component(self) -> None:
        blocks = [
            ("body", "**IMPORTANT**"),
            ("body", "Congratulations."),
            ("body", "**FR IMPORTANT**"),
            ("body", "Félicitations."),
        ]
        out = transform(blocks)
        self.assertEqual(["component", "body", "component", "body"],
                         [k for k, _ in out])
        first = json.loads(out[0][1])
        self.assertEqual({"kind": "langtag", "lang": "EN", "texts": ["IMPORTANT"]}, first)
        second = json.loads(out[2][1])
        self.assertEqual("FR", second["lang"])

    def test_warranty_years_table_becomes_component(self) -> None:
        rows = [[
            "**3 YEARS** **Standard Warranty** The standard warranty period is 36 months.",
            "**2 YEARS** **Extended Warranty** To activate, register your product online.",
        ]]
        out = transform([("table", str(rows))])
        self.assertEqual("component", out[0][0])
        spec = json.loads(out[0][1])
        self.assertEqual("warrantyyears", spec["kind"])
        self.assertEqual(
            [("3", "YEARS", "Standard Warranty"), ("2", "YEARS", "Extended Warranty")],
            [(i["number"], i["unit"], i["label"]) for i in spec["items"]],
        )

    def test_charging_emphasis_uses_structure_not_rendered_wording(self) -> None:
        blocks = [
            ("h1", "CHARGING"),
            ("body", "**Green first:** Introductory copy."),
            ("body", "**Localized source sentence.**"),
            ("component", json.dumps({"kind": "notice", "label": "NOTE"})),
        ]
        out = transform(blocks)
        self.assertEqual("component", out[2][0])
        self.assertEqual("emphasispill", json.loads(out[2][1])["kind"])
        self.assertEqual(["Localized source sentence."], json.loads(out[2][1])["texts"])

    def test_warranty_page_groups_source_sections(self) -> None:
        blocks = [
            ("h1", "WARRANTY"),
            ("body", "**Purchase channel.**"),
            ("body", "*Local-law note."),
            ("h2", "Limited Warranty"),
            ("body", "Warranty copy."),
        ]
        out = transform(blocks)
        self.assertEqual(["h1", "component", "warrantynote", "component"],
                         [kind for kind, _ in out])
        self.assertEqual("warrantylead", json.loads(out[1][1])["kind"])
        section = json.loads(out[3][1])
        self.assertEqual("warrantysection", section["kind"])
        self.assertEqual("Limited Warranty", section["title"])

    def test_ordinary_table_is_untouched(self) -> None:
        blocks = [("table", str([["Header", "Value"], ["A", "B"]]))]
        self.assertEqual(blocks, transform(blocks))

    def test_plain_image_is_untouched(self) -> None:
        blocks = [("image", "_assets/x/solar.png"), ("body", "A caption line.")]
        self.assertEqual(blocks, transform(blocks))


if __name__ == "__main__":
    unittest.main()
