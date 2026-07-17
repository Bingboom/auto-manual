from __future__ import annotations

import unittest
from pathlib import Path

from tools.idml.latex_page_plan import (
    anchor_candidates,
    is_placed_page,
    map_pages,
    planned_span,
    validate_page_plan,
)
from tools.manual_ir import build_manual_ir
from tools.manual_ir.model import ManualBlock, ManualIR, ManualPage


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

    def test_placed_pages_are_flagged_and_skip_anchor_matching(self) -> None:
        placed_block = ManualBlock(
            block_id="b-0001",
            source_ref="page/cover-en.rst",
            kind="data",
            payload={"asset": "cover-en.pdf", "kind": "placed_pdf"},
            content_sha256="0" * 64,
        )
        cover = ManualPage(
            page_id="page-0001-cover-en",
            source_ref="page/cover-en.rst",
            source_path="page/cover-en.rst",
            language="en",
            source_sha256="0" * 64,
            skipped_raw=0,
            blocks=(placed_block,),
        )
        self.assertTrue(is_placed_page(cover))
        self.assertFalse(is_placed_page(self.ir.pages[0]))

        synthetic_ir = ManualIR(
            model=self.ir.model, region=self.ir.region, language=self.ir.language,
            source=self.ir.source, bundle_root=self.ir.bundle_root,
            bundle_sha256=self.ir.bundle_sha256, snapshot_sha256=self.ir.snapshot_sha256,
            layout_params_sha256=self.ir.layout_params_sha256,
            style_contract_sha256=self.ir.style_contract_sha256,
            content_sha256=self.ir.content_sha256,
            pages=(cover,) + self.ir.pages,
        )
        entries = map_pages(synthetic_ir, ["Synthetic cover", "PREFACE copy"])
        self.assertTrue(entries[0]["placed"])
        self.assertIsNone(entries[0]["latex_start_page"])
        self.assertEqual(0, entries[0]["candidate_count"])
        self.assertFalse(entries[1]["placed"])

    def test_story_span_uses_next_source_start(self) -> None:
        plan = {"pages": [
            {"source_path": "page/operations.rst", "latex_start_page": 10},
            {"source_path": "page/charging.rst", "latex_start_page": 14},
            {"source_path": "page/trouble.rst", "latex_start_page": 18},
            {"source_path": "page/spec.rst", "latex_start_page": 19},
        ]}
        self.assertEqual(9, planned_span(
            plan, ["operations", "charging", "trouble"], fallback=6))

    def test_approved_story_span_prefers_explicit_composition_page_count(self) -> None:
        plan = {
            "physical_page_count": 20,
            "pages": [
                {
                    "source_path": "page/operations.rst",
                    "latex_start_page": 10,
                    "composition_id": "operations-en",
                    "planned_page_count": 4,
                },
                {
                    "source_path": "page/ups.rst",
                    "latex_start_page": 16,
                    "composition_id": "ups-en",
                    "planned_page_count": 1,
                },
            ],
        }

        self.assertEqual(
            4,
            planned_span(plan, ["operations"], fallback=1),
        )

    def test_final_story_span_uses_physical_page_boundary(self) -> None:
        plan = {
            "physical_page_count": 20,
            "pages": [
                {"source_path": "page/warranty.rst", "latex_start_page": 17},
            ],
        }

        self.assertEqual(4, planned_span(plan, ["warranty"], fallback=1))

    def test_story_span_rejects_out_of_range_anchors(self) -> None:
        for start in (0, 21):
            with self.subTest(start=start):
                plan = {
                    "physical_page_count": 20,
                    "pages": [
                        {"source_path": "page/story.rst", "latex_start_page": start},
                    ],
                }

                self.assertEqual(
                    3,
                    planned_span(plan, ["story"], fallback=3),
                )

    def test_story_span_rejects_non_monotonic_anchors(self) -> None:
        plan = {
            "physical_page_count": 20,
            "pages": [
                {"source_path": "page/operations.rst", "latex_start_page": 10},
                {"source_path": "page/charging.rst", "latex_start_page": 9},
                {"source_path": "page/trouble.rst", "latex_start_page": 15},
            ],
        }

        self.assertEqual(
            6,
            planned_span(plan, ["operations", "charging"], fallback=6),
        )


if __name__ == "__main__":
    unittest.main()
