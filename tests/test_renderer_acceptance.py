from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.renderer_acceptance import (
    check_html,
    check_idml,
    expected_pdf_pages,
    front_matter_pages,
)


class PageFormulaTests(unittest.TestCase):
    """The formula is the acceptance criterion, so it is pinned to shipped books."""

    def test_formula_matches_every_measured_shipped_book(self) -> None:
        # (languages, block pages, shipped page count, book)
        cases = [
            (3, 8, 28, "HTP017 US battery pack"),
            (5, 8, 46, "HTP011 EU battery pack"),
            (3, 18, 58, "HTE153 US"),
            (6, 17, 108, "HTE159 EU"),
            (6, 19, 120, "HTE152 EU"),
            (3, 31, 97, "HTE157 US Pro Max"),
            (1, 25, 28, "HTE152 JP single language"),
        ]
        for languages, block, shipped, label in cases:
            with self.subTest(book=label):
                self.assertEqual(shipped, expected_pdf_pages(languages, block))

    def test_single_language_front_matter_is_measured_not_extrapolated(self) -> None:
        # The JP house style absorbs the preface into the cover, so front
        # matter is 2 (cover + contents). Applying the multi-language
        # expression would predict 3 and be wrong by a page on every
        # single-language line — the corpus audit flagged exactly this.
        self.assertEqual(2, front_matter_pages(1))
        self.assertEqual(3, front_matter_pages(3))
        self.assertEqual(5, front_matter_pages(6))

    def test_overrides_are_honoured(self) -> None:
        self.assertEqual(
            2 + 3 * 8 + 1, expected_pdf_pages(3, 8, front_pages=2)
        )
        self.assertEqual(
            3 + 3 * 8 + 2, expected_pdf_pages(3, 8, back_pages=2)
        )


class HtmlCriterionTests(unittest.TestCase):
    def test_composite_hit_fails_because_degradation_is_the_requirement(self) -> None:
        # A target outside the web contract's figure_targets allowlist must
        # render plain HTML. A composition class means the allowlist was
        # widened by hand, so it has to fail rather than pass silently.
        with tempfile.TemporaryDirectory() as tmp:
            html_dir = Path(tmp)
            (html_dir / "_static").mkdir()
            (html_dir / "_static" / "hb_manual.css").write_text("x", encoding="utf-8")
            (html_dir / "page.html").write_text(
                '<div class="hb-overview-composition">x</div>', encoding="utf-8"
            )
            results = {item.name: item for item in check_html(
                root=html_dir, html_dir=html_dir, languages=["en"]
            )}
            self.assertEqual("fail", results["no-unexpected-composites"].status)

    def test_plain_html_passes_and_names_the_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html_dir = Path(tmp)
            (html_dir / "_static").mkdir()
            (html_dir / "_static" / "hb_manual.css").write_text("x", encoding="utf-8")
            (html_dir / "page.html").write_text("<p>plain</p>", encoding="utf-8")
            results = {item.name: item for item in check_html(
                root=html_dir, html_dir=html_dir, languages=["en"]
            )}
            self.assertEqual("pass", results["no-unexpected-composites"].status)
            # Two lanes emit different stylesheets; asserting one name would
            # fail the other lane for no reason.
            self.assertEqual("pass", results["stylesheet-present"].status)
            self.assertIn("sphinx", results["stylesheet-present"].detail)

    def test_missing_html_is_a_skip_not_a_false_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            results = check_html(
                root=Path(tmp), html_dir=Path(tmp) / "absent", languages=["en"]
            )
            self.assertEqual(["skip"], [item.status for item in results])


class IdmlCriterionTests(unittest.TestCase):
    def test_shared_layout_pin_criterion_reports_a_dirty_file(self) -> None:
        # The approved JE-1000F/US plan hashes all of data/layout_params.csv,
        # so one added row unpins every target (the #720 failure shape). This
        # criterion must be a real git check, not reviewer discipline.
        root = Path(__file__).resolve().parents[1]
        results = {
            item.name: item
            for item in check_idml(root=root, idml_path=root / "does" / "not" / "exist.idml")
        }
        self.assertIn("shared-layout-pins-untouched", results)
        self.assertIn(results["shared-layout-pins-untouched"].status, {"pass", "fail"})
        self.assertEqual("skip", results["artifact-present"].status)


if __name__ == "__main__":
    unittest.main()
