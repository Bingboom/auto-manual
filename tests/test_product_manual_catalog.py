from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".agents" / "skills" / "product-manual-catalog" / "scripts" / "query_product_manuals.py"
)
_SPEC = importlib.util.spec_from_file_location("query_product_manuals", _SCRIPT_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Unable to load {_SCRIPT_PATH}")
query_product_manuals = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(query_product_manuals)


class TestProductManualCatalogArgs(unittest.TestCase):
    def test_search_flag_sets_query(self) -> None:
        # Regression: --search must not be clobbered to None by the absent
        # positional's default (they previously shared an argparse dest).
        self.assertEqual("HTE153", query_product_manuals.parse_args(["--search", "HTE153"]).query)

    def test_positional_sets_query(self) -> None:
        self.assertEqual("HTE153", query_product_manuals.parse_args(["HTE153"]).query)

    def test_query_defaults_to_none(self) -> None:
        self.assertIsNone(query_product_manuals.parse_args([]).query)


class TestProductManualCatalogMatching(unittest.TestCase):
    def test_matches_project_code_field(self) -> None:
        # The 项目 (project) column must be searchable, e.g. HTE153 -> JE-1000F row.
        row = {"产品型号": "JE-1000F", "项目": "HTE153"}
        self.assertTrue(query_product_manuals.matches(row, "HTE153"))
        self.assertTrue(query_product_manuals.matches(row, "je-1000f"))
        self.assertFalse(query_product_manuals.matches(row, "JBP-2000B"))

    def test_project_and_business_no_are_rendered(self) -> None:
        # Regression: a result block must surface the project code so a project
        # lookup is verifiable in the output.
        self.assertIn("项目", query_product_manuals.DETAIL_FIELDS)
        self.assertIn("业务号", query_product_manuals.DETAIL_FIELDS)
        rendered = query_product_manuals.render_record_markdown(
            {"产品型号": "JE-1000F", "项目": "HTE153", "业务号": "Doc-016"}
        )
        self.assertIn("HTE153", rendered)


if __name__ == "__main__":
    unittest.main()
