"""The JP contents page takes its master's entry scale.

Master page index 1 sets all ten entries in NotoSansJP-Medium at **7.00 pt**,
stepping 86.4 / 102.4 / 118.4 / 134.4 = **16.00 pt**. The build set them at
6.50 on a 14.00 pitch, with the tab-and-folio run pinned at a literal 6.5 while
the folio digits already printed at 7.

The page's title (22.25) and range (9.00) already matched the master and are
untouched.

The pitch was a literal in three places -- the paragraph style, the tab run,
and the frame-height formula `14.0 * count + 14.0` -- so the entries frame is
sized on the same number that sets the type. All three now read one token, and
the frame grows with the pitch: 10 x 16 + 16 = 176.00 pt against the 154.00 it
was. The contents page carries nothing below the entries, so the growth
collides with nothing.

A segment resolves its own scale from its own language, because a book's
contents page can carry several: BP@EU prints six segments. The header carries
the display code ("JP"), so it goes through `normalize_lang` to reach the
phase2 suffix the rows are keyed on. A segment whose language declares nothing
keeps 6.50/14.00 exactly -- BP@US rebuilt before and after is content-identical
across all 318 entries.

`_entry_typography` still shrinks a title too long for its column, down to the
same 5.40 pt floor; the declared size is a cap, not a fixed size. None of this
book's ten titles is long enough to shrink: the longest is eleven characters
against a 297.61 pt measure.
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
from tools.idml.params import load_layout_params, param_pt
from tools.idml.styles import para_styles

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/layout_params.csv"
OVERLAY = ROOT / "data/layout_params.idml-compact.csv"

MASTER_SIZE = 7.0
MASTER_PITCH = 16.0
BUILT_BEFORE = (6.5, 14.0)
# The widest column this book sets an entry in.
COLUMN = 305.61


def params():
    return load_layout_params(BASE, [OVERLAY])


def entry_style(language: str) -> tuple[float, float]:
    for name, size, leading, _weight, _kind in para_styles(params(), language):
        if name == "HB TOC Entry":
            return size, leading
    raise AssertionError("HB TOC Entry is missing from the style table")


class TheJapaneseContentsPage(unittest.TestCase):
    def test_the_entry_takes_the_masters_size_and_pitch(self) -> None:
        size, leading = entry_style("ja")
        self.assertAlmostEqual(MASTER_SIZE, size, delta=0.01)
        self.assertAlmostEqual(MASTER_PITCH, leading, delta=0.01)

    def test_the_display_code_resolves_like_the_source_code(self) -> None:
        """The segment header carries "JP"; the writer carries "ja"."""
        self.assertEqual(entry_style("JP"), entry_style("ja"))

    def test_the_rows_carry_the_measured_values(self) -> None:
        p = params()
        self.assertAlmostEqual(
            MASTER_SIZE,
            param_pt(p, "lang_jp_type_toc_entry_font_size", 0.0),
            delta=0.01,
        )
        self.assertAlmostEqual(
            MASTER_PITCH,
            param_pt(p, "lang_jp_type_toc_entry_font_leading", 0.0),
            delta=0.01,
        )


class NoOtherContentsPageMoves(unittest.TestCase):
    def test_english_keeps_what_it_printed(self) -> None:
        self.assertEqual(BUILT_BEFORE, entry_style("en"))

    def test_so_does_every_segment_language_in_the_family(self) -> None:
        for code in ("fr", "es", "de", "it", "uk", "ko", "zh", "pt"):
            with self.subTest(language=code):
                self.assertEqual(BUILT_BEFORE, entry_style(code))

    def test_declaring_nothing_is_what_the_literals_were(self) -> None:
        self.assertEqual(BUILT_BEFORE, entry_style(""))
        self.assertEqual(
            BUILT_BEFORE, (_ENTRY_SIZE_DEFAULT, _ENTRY_LEADING_DEFAULT)
        )

    def test_only_japanese_declares_either_key(self) -> None:
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
                self.assertEqual(["jp"], declared)


class TheSizeIsACapNotAFixedSize(unittest.TestCase):
    def test_a_short_title_sets_at_the_declared_size(self) -> None:
        size, _scale = _entry_typography("主な仕様", COLUMN, cap=MASTER_SIZE)
        self.assertAlmostEqual(MASTER_SIZE, size, delta=0.01)

    def test_this_books_longest_title_does_not_shrink(self) -> None:
        longest = "製品の使用方法について"
        self.assertEqual(11, len(longest))
        size, _scale = _entry_typography(longest, COLUMN, cap=MASTER_SIZE)
        self.assertAlmostEqual(MASTER_SIZE, size, delta=0.01)

    def test_a_title_too_long_for_its_column_still_shrinks(self) -> None:
        size, _scale = _entry_typography("あ" * 200, COLUMN, cap=MASTER_SIZE)
        self.assertLess(size, MASTER_SIZE)

    def test_and_never_below_the_floor(self) -> None:
        size, _scale = _entry_typography("あ" * 5000, COLUMN, cap=MASTER_SIZE)
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

    def test_every_run_sets_at_the_masters_size(self) -> None:
        story = self.zip.read("Stories/Story_st_toc_seg0_c0.xml").decode("utf-8")
        sizes = {
            round(float(v), 2)
            for v in re.findall(r'PointSize="([\d.]+)"', story)
        }
        self.assertEqual({MASTER_SIZE}, sizes)

    def test_the_frame_grew_with_the_pitch(self) -> None:
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
                MASTER_PITCH * self.ENTRIES + MASTER_PITCH,
                max(ys) - min(ys),
                delta=0.01,
            )
            return
        self.fail("no contents entry frame in the built spread")

    def test_the_leaders_survived_the_change(self) -> None:
        self.assertEqual(self.ENTRIES, self.spread.count("gl_toc_leader"))

    def test_nothing_sits_below_the_entries_to_collide_with(self) -> None:
        bottoms = []
        for match in re.finditer(
            r"<(TextFrame|Rectangle|Polygon)\b([^>]*)>(.*?)</\1>", self.spread, re.S
        ):
            self_id = re.search(r'Self="([^"]+)"', match.group(2))
            points = [
                tuple(float(v) for v in raw.split())
                for raw in re.findall(
                    r'<PathPointType Anchor="([-\d.]+ [-\d.]+)"', match.group(3)
                )
            ]
            if not points or not self_id:
                continue
            ys = [p[1] for p in points]
            bottoms.append((max(ys), self_id.group(1)))
        lowest = max(bottoms)
        self.assertIn("toc_seg", lowest[1], f"something sits lower: {lowest}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
