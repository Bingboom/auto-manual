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

    def test_plain_image_is_untouched(self) -> None:
        blocks = [("image", "_assets/x/solar.png"), ("body", "A caption line.")]
        self.assertEqual(blocks, transform(blocks))


if __name__ == "__main__":
    unittest.main()
