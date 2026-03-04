from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.phase1.builder import BuildPaths, Phase1Builder, _normalize_content_blocks


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

    def test_spec_master_rows_can_be_detected(self) -> None:
        rows = [
            {
                "Section": "GENERAL INFO",
                "Row_key": "product_name",
                "Line_order": "1",
                "Value_en": "Demo",
            }
        ]
        self.assertTrue(Phase1Builder._looks_like_spec_master_rows(rows))

    def test_load_spec_prefers_draft_tool_master(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft_csv = root / "tools" / "Draft-tool" / "data" / "Spec_Master.csv"
            phase1_csv = root / "data" / "phase1" / "Spec_Master.csv"
            draft_csv.parent.mkdir(parents=True, exist_ok=True)
            phase1_csv.parent.mkdir(parents=True, exist_ok=True)

            csv_head = "Section,Row_key,Line_order,Value_en\n"
            draft_csv.write_text(
                csv_head + "GENERAL INFO,draft_row,1,draft\n",
                encoding="utf-8",
            )
            phase1_csv.write_text(
                csv_head + "GENERAL INFO,phase_row,1,phase\n",
                encoding="utf-8",
            )

            paths = BuildPaths(
                root=root,
                page_registry=root / "dummy_registry.csv",
                content_blocks=root / "dummy_content.csv",
                product_variables=root / "dummy_vars.csv",
                template_dir=root / "docs" / "templates",
                output_dir=root / "docs" / "generated",
            )
            builder = Phase1Builder(paths)
            rows = builder._load_page_blocks("spec", default_blocks=[])
            self.assertEqual("draft_row", rows[0]["Row_key"])


if __name__ == "__main__":
    unittest.main()
