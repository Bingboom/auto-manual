from __future__ import annotations

import unittest

from tools.phase1.builder import _normalize_content_blocks


class TestPhase1BuilderNormalization(unittest.TestCase):
    def test_compact_schema_can_be_normalized(self) -> None:
        rows = [
            {
                "id": "1.0",
                "part": "title_main",
                "text_en": "MAIN",
            },
            {
                "id": "2.0",
                "part": "top",
                "text_en": "Top item",
            },
        ]

        out = _normalize_content_blocks(rows)
        self.assertEqual(2, len(out))
        self.assertEqual("safety", out[0]["page_id"])
        self.assertEqual("title_main", out[0]["block_type"])
        self.assertEqual("list_item", out[1]["block_type"])

    def test_unknown_part_should_raise_instead_of_silent_drop(self) -> None:
        rows = [
            {
                "id": "9.0",
                "part": "unknown_part",
                "text_en": "bad",
            }
        ]

        with self.assertRaises(ValueError):
            _normalize_content_blocks(rows)


if __name__ == "__main__":
    unittest.main()
