"""The contents entry has one scale, and every segment language prints it.

The entry size and pitch used to be literals in three places -- the paragraph
style, the tab-and-folio run, and the frame-height formula `14.0 * count +
14.0`. They are one token each now (`type_toc_entry_font_size`,
`type_toc_entry_font_leading`), read per segment language through the same
cascade the rest of the renderer uses, so the frame can never again be sized on
a different number than the type. That mechanism is what this file keeps.

What it no longer keeps is a Japanese scale of its own. An earlier pass
measured the hand-made JP PDF -- 7.00 pt on a 16.00 pitch -- and declared two
`lang_jp_` rows to reproduce it. That forked the JP contents page off the shared
style to chase production error. The rows are gone; JP resolves to 6.50/14.00
like every other book, and the frame is 154.00 as it always was.

`_entry_typography` still shrinks a title too long for its column down to the
same 5.40 pt floor; the token is a cap, not a fixed size.
"""

from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path

from tools.idml.page_toc import (
    _ENTRY_LEADING_DEFAULT,
    _ENTRY_SIZE_DEFAULT,
    _entry_typography,
)
from tools.idml.params import load_layout_params
from tools.idml.styles import para_styles

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/layout_params.csv"
OVERLAY = ROOT / "data/layout_params.idml-compact.csv"

SHARED = (6.5, 14.0)
COLUMN = 305.61


def params():
    return load_layout_params(BASE, [OVERLAY])


def entry_style(language: str) -> tuple[float, float]:
    for name, size, leading, _weight, _kind in para_styles(params(), language):
        if name == "HB TOC Entry":
            return size, leading
    raise AssertionError("HB TOC Entry is missing from the style table")


class EverySegmentPrintsTheSharedScale(unittest.TestCase):
    def test_japanese_by_source_code_and_by_display_code(self) -> None:
        self.assertEqual(SHARED, entry_style("ja"))
        self.assertEqual(SHARED, entry_style("jp"))
        self.assertEqual(SHARED, entry_style("JP"))

    def test_every_language_in_the_family(self) -> None:
        for code in ("en", "fr", "es", "de", "it", "uk", "ko", "zh", "pt", ""):
            with self.subTest(language=code or "(none)"):
                self.assertEqual(SHARED, entry_style(code))

    def test_the_code_defaults_are_the_shared_values(self) -> None:
        self.assertEqual(SHARED, (_ENTRY_SIZE_DEFAULT, _ENTRY_LEADING_DEFAULT))

    def test_no_language_declares_an_entry_scale(self) -> None:
        rows: list[str] = []
        for path in (BASE, OVERLAY):
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows.extend(
                    (row.get("key") or "").strip() for row in csv.DictReader(handle)
                )
        for key in ("type_toc_entry_font_size", "type_toc_entry_font_leading"):
            pattern = re.compile(r"^lang_([a-z]{2})_" + re.escape(key) + r"$")
            declared = sorted(m.group(1) for m in map(pattern.match, rows) if m)
            with self.subTest(key=key):
                self.assertEqual([], declared)


class TheSizeIsACapNotAFixedSize(unittest.TestCase):
    def test_a_short_title_sets_at_the_cap(self) -> None:
        size, _scale = _entry_typography("主な仕様", COLUMN, cap=SHARED[0])
        self.assertAlmostEqual(SHARED[0], size, delta=0.01)

    def test_this_books_longest_title_does_not_shrink(self) -> None:
        longest = "製品の使用方法について"
        self.assertEqual(11, len(longest))
        size, _scale = _entry_typography(longest, COLUMN, cap=SHARED[0])
        self.assertAlmostEqual(SHARED[0], size, delta=0.01)

    def test_a_title_too_long_for_its_column_still_shrinks(self) -> None:
        size, _scale = _entry_typography("あ" * 200, COLUMN, cap=SHARED[0])
        self.assertLess(size, SHARED[0])

    def test_and_never_below_the_floor(self) -> None:
        size, _scale = _entry_typography("あ" * 5000, COLUMN, cap=SHARED[0])
        self.assertAlmostEqual(5.4, size, delta=0.01)


class TheBuiltContentsPage(unittest.TestCase):
    """Read out of the shipped IDML. Skipped on an unbuilt tree."""

    IDML = ROOT / "docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml"
    ENTRIES = 10

    def setUp(self) -> None:
        if not self.IDML.is_file():
            self.skipTest("JBP-2000B JP has not been built in this tree")
        import zipfile

        self.zip = zipfile.ZipFile(self.IDML)
        self.spread = self.zip.read("Spreads/Spread_sp_toc.xml").decode("utf-8")

    def test_the_titles_set_at_the_shared_size(self) -> None:
        story = self.zip.read("Stories/Story_st_toc_seg0_c0.xml").decode("utf-8")
        titles = {
            round(float(v), 2)
            for v in re.findall(r'PointSize="(6\.5\d*)"', story)
        }
        self.assertEqual({6.5}, titles)
        # The folio digits ride their own 7 pt run, as they always have.
        self.assertIn('PointSize="7"', story)

    def test_the_frame_is_sized_on_the_shared_pitch(self) -> None:
        for match in re.finditer(
            r"<TextFrame\b([^>]*)>(.*?)</TextFrame>", self.spread, re.S
        ):
            parent = re.search(r'ParentStory="(st_toc_seg[^"]+)"', match.group(1))
            if not parent:
                continue
            points = [
                tuple(float(v) for v in raw.split())
                for raw in re.findall(
                    r'<PathPointType Anchor="([-\d.]+ [-\d.]+)"', match.group(2)
                )
            ]
            ys = [p[1] for p in points]
            self.assertAlmostEqual(
                SHARED[1] * self.ENTRIES + SHARED[1], max(ys) - min(ys), delta=0.01
            )
            return
        self.fail("no contents entry frame in the built spread")

    def test_the_leaders_are_intact(self) -> None:
        self.assertNotIn("gl_toc_leader", self.spread)
        story = self.zip.read("Stories/Story_st_toc_seg0_c0.xml").decode("utf-8")
        self.assertEqual(self.ENTRIES, story.count('<Leader type="string">.</Leader>'))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
