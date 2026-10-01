from __future__ import annotations

import json
import sys
import unittest
from unittest.mock import patch

from tools.csv_pages import renderers_safety as safety


class TestCsvPageSafety(unittest.TestCase):
    def _blocks(self, metadata: str) -> list[dict[str, str]]:
        blocks = [
            {"block_type": kind, "text_en": kind}
            for kind in ("title_main", "warning_title", "title_operating", "lead_top", "save_title")
        ]
        blocks.extend([
            {"block_type": "list_item", "text_en": "First item", "meta_json": metadata,
             "block_id": "top-item", "__line__": "7"},
            {"block_type": "list_item", "text_en": "Last item",
             "meta_json": '{"list_part":"bottom"}'},
        ])
        return blocks

    def test_valid_metadata_preserves_content_and_rendered_output(self) -> None:
        blocks = self._blocks('{"list_part":"top"}')
        self.assertEqual(
            {
                "title_main": "title_main", "warning_title": "warning_title",
                "title_operating": "title_operating", "lead_top": "lead_top",
                "save_title": "save_title", "top_items": ["First item"],
                "bottom_items": ["Last item"],
            },
            safety.collect_safety_content(blocks, "demo", "en", {}),
        )
        self.assertEqual(
            "title_main\n- First item\n\n- Last item\n",
            safety.render_safety_page(
                "\n".join((safety.PH_TITLE_MAIN_HTML, safety.PH_TOP, safety.PH_BOTTOM)),
                blocks, "demo", "en", {},
            ),
        )

    def test_invalid_json_preserves_message_location_and_cause(self) -> None:
        for block_id, line in (("top-item", "7"), ("", "")):
            with self.subTest(block_id=block_id, line=line):
                blocks = self._blocks("{")
                blocks[-2].update(block_id=block_id, __line__=line)
                with self.assertRaises(ValueError) as caught:
                    safety.collect_safety_content(blocks, "demo", "en", {})
                self.assertEqual(
                    f"Invalid meta_json for block_id='{block_id or '?'}' line {line or '?'}: "
                    "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
                    str(caught.exception),
                )
                self.assertIsInstance(caught.exception.__cause__, json.JSONDecodeError)

    def test_integer_limit_preserves_value_error_message_and_cause(self) -> None:
        old_limit = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(640)
            with self.assertRaises(ValueError) as caught:
                safety.collect_safety_content(self._blocks("9" * 641), "demo", "en", {})
        finally:
            sys.set_int_max_str_digits(old_limit)
        self.assertEqual(
            "Invalid meta_json for block_id='top-item' line 7: "
            "Exceeds the limit (640 digits) for integer string conversion: value has 641 digits; "
            "use sys.set_int_max_str_digits() to increase the limit",
            str(caught.exception),
        )
        self.assertIs(type(caught.exception.__cause__), ValueError)

    def test_decoder_recursion_error_preserves_message_and_cause(self) -> None:
        # Decoder depth limits vary by Python build; freeze the boundary's wrapping.
        error = RecursionError("maximum recursion depth exceeded while decoding a JSON array from a unicode string")
        with patch.object(safety.json, "loads", side_effect=error):
            with self.assertRaises(ValueError) as caught:
                safety.collect_safety_content(self._blocks("[[]]"), "demo", "en", {})
        self.assertEqual(
            "Invalid meta_json for block_id='top-item' line 7: " + str(error),
            str(caught.exception),
        )
        self.assertIs(error, caught.exception.__cause__)

    def test_valid_non_object_json_keeps_unwrapped_attribute_error(self) -> None:
        with self.assertRaises(AttributeError) as caught:
            safety.collect_safety_content(self._blocks("[]"), "demo", "en", {})
        self.assertEqual("'list' object has no attribute 'get'", str(caught.exception))
        self.assertIsNone(caught.exception.__cause__)
