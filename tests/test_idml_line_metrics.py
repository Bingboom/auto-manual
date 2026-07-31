from __future__ import annotations

import unittest

from tools.idml.line_metrics import (
    east_asian_width_units,
    estimated_line_count,
    estimated_text_width,
)
from tools.idml.story_estimates import paragraph_estimate


class IdmlLineMetricsTests(unittest.TestCase):
    def test_latin_estimate_preserves_legacy_capacity(self) -> None:
        # 104 pt / (0.52 * 10 pt) = 20 legacy characters per line.
        self.assertEqual(
            estimated_line_count("a" * 40, 104.0, point_size=10.0),
            2,
        )
        self.assertEqual(
            estimated_line_count("a" * 41, 104.0, point_size=10.0),
            3,
        )

    def test_wide_and_fullwidth_characters_use_full_em_width(self) -> None:
        self.assertAlmostEqual(east_asian_width_units("日本Ａ"), 3 / 0.52)
        self.assertAlmostEqual(
            estimated_text_width("日本Ａ", point_size=10.0),
            30.0,
        )
        self.assertEqual(
            estimated_line_count("日本語日本語", 20.8, point_size=10.0),
            3,
        )

    def test_combining_marks_do_not_consume_an_extra_glyph(self) -> None:
        decomposed = "e\u0301" * 20
        self.assertEqual(
            east_asian_width_units(decomposed),
            east_asian_width_units("e" * 20),
        )
        self.assertEqual(
            estimated_line_count(decomposed, 104.0, point_size=10.0),
            1,
        )
        self.assertEqual(east_asian_width_units("\ufe0f"), 0.0)

    def test_non_string_zero_is_not_treated_as_empty(self) -> None:
        self.assertEqual(east_asian_width_units(0), 1.0)

    def test_explicit_line_breaks_are_preserved(self) -> None:
        self.assertEqual(
            estimated_line_count("short\n短い", 104.0, point_size=10.0),
            2,
        )

    def test_ambiguous_width_stays_narrow_and_deterministic(self) -> None:
        # Greek alpha has East Asian Width A; the contract intentionally keeps
        # it narrow instead of allowing host locale/font choice to change it.
        self.assertEqual(east_asian_width_units("α"), 1.0)

    def test_story_height_budget_grows_for_same_count_cjk_copy(self) -> None:
        latin_height, latin_lines = paragraph_estimate(
            {}, "body", "body", "a" * 20, 100.0,
            is_preface=False,
            operation_spacing=None,
        )
        cjk_height, cjk_lines = paragraph_estimate(
            {}, "body", "body", "日" * 20, 100.0,
            is_preface=False,
            operation_spacing=None,
        )
        self.assertEqual(latin_lines, 1)
        self.assertEqual(cjk_lines, 2)
        self.assertGreater(cjk_height, latin_height)


if __name__ == "__main__":
    unittest.main()
