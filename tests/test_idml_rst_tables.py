from __future__ import annotations

import json
import unittest

from tools.idml_rst_extract import _parse_text
from tools.idml_rst_tables import parse_list_table


class ListTableParserTests(unittest.TestCase):
    def test_plain_two_column_rows_keep_their_columns(self) -> None:
        rows = parse_list_table([
            "   :header-rows: 0",
            "",
            "   * - First label",
            "     - First value",
            "       continued",
            "   * - Second label",
            "     - Second value",
        ])

        self.assertEqual(
            rows,
            [
                ["First label", "First value continued"],
                ["Second label", "Second value"],
            ],
        )

    def test_nested_bullets_stay_inside_the_second_cell(self) -> None:
        rows = parse_list_table([
            "   * - **CAUTION**",
            "     -",
            "       - First item.",
            "         First item continuation.",
            "       - Second item.",
        ])

        self.assertEqual(
            rows,
            [[
                "**CAUTION**",
                "- First item.\nFirst item continuation.\n- Second item.",
            ]],
        )

    def test_korean_notice_keeps_clean_label_and_all_nested_items(self) -> None:
        result = _parse_text(
            """
.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **주의**
     -
       - 첫 번째 주의 사항입니다.
       - 두 번째 주의 사항입니다.
       - 세 번째 주의 사항입니다.
""",
            {"latex"},
        )

        self.assertEqual(len(result.blocks), 1)
        kind, raw_payload = result.blocks[0]
        self.assertEqual(kind, "component")
        payload = json.loads(raw_payload)
        self.assertEqual(payload["kind"], "notice")
        self.assertEqual(payload["label"], "주의")
        self.assertEqual(payload["variant"], "caution")
        self.assertTrue(payload["list"])
        self.assertEqual(
            payload["texts"],
            [
                "첫 번째 주의 사항입니다.",
                "두 번째 주의 사항입니다.",
                "세 번째 주의 사항입니다.",
            ],
        )


if __name__ == "__main__":
    unittest.main()
