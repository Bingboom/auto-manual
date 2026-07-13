from __future__ import annotations

import unittest
from pathlib import Path

from tools.idml.latex_page_plan import anchor_candidates, map_pages, planned_span, validate_page_plan
from tools.manual_ir import build_manual_ir


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "tests" / "fixtures" / "idml_bundle"
DATA = ROOT / "tests" / "fixtures" / "phase2"


class LatexPagePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ir = build_manual_ir(
            root=ROOT, bundle_root=BUNDLE, model="JE-1000F", region="US",
            lang="en", source="test", data_root=DATA)

    def test_anchor_candidates_prioritize_visible_headings(self) -> None:
        page = next(page for page in self.ir.pages if page.source_path.endswith("symbols_en.rst"))
        self.assertEqual("meaning of symbols", anchor_candidates(page)[0])

    def test_standard_short_fcc_heading_is_a_page_anchor(self) -> None:
        page = next(page for page in self.ir.pages if page.source_path.endswith("01_fcc.rst"))
        self.assertEqual("fcc", anchor_candidates(page)[0])

    def test_mapping_is_monotonic_and_keeps_unmatched_pages_explicit(self) -> None:
        pdf_pages = [
            "Synthetic cover",
            "Preface copy",
            "IMPORTANT safety content",
            "MEANING OF SYMBOLS and warning copy",
            "FCC and product content",
        ]
        entries = map_pages(self.ir, pdf_pages)
        starts = [entry["latex_start_page"] for entry in entries
                  if entry["latex_start_page"] is not None]
        self.assertEqual(starts, sorted(starts))
        self.assertTrue(any(entry["latex_start_page"] is None for entry in entries))

    def test_validation_rejects_low_match_rate(self) -> None:
        issues = validate_page_plan({
            "schema_version": "latex-page-plan/v1",
            "physical_page_count": 2,
            "match_rate": 0.5,
            "pages": [],
        })
        self.assertTrue(any("match rate" in issue for issue in issues))

    def test_story_span_uses_next_source_start(self) -> None:
        plan = {"pages": [
            {"source_path": "page/operations.rst", "latex_start_page": 10},
            {"source_path": "page/charging.rst", "latex_start_page": 14},
            {"source_path": "page/trouble.rst", "latex_start_page": 18},
            {"source_path": "page/spec.rst", "latex_start_page": 19},
        ]}
        self.assertEqual(9, planned_span(
            plan, ["operations", "charging", "trouble"], fallback=6))


if __name__ == "__main__":
    unittest.main()
