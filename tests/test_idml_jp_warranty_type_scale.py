"""The JP warranty pages take their master's type scale.

Measured over the master's two warranty pages (PyMuPDF indices 10 and 11):
1056 characters of body and list copy set in NotoSansJP-DemiLight at **7.00 pt**,
list items stepping 41.1 / 50.1 / 59.1 / 68.1 = **9.00 pt**, the page-10 lead-in
stepping 51.6 / 62.6 / 73.6 = **11.00 pt**, and the section titles 保証期間 /
保証内容 in NotoSansJP-Bold at **7.58 pt**. The build ran 6.00/7.20 for body and
list, 6.00/6.00 for the notes, 7.00/8.20 for the lead and 8.00 for the titles.

This is the largest single type population in the book, and §4c had withheld it
on the reasoning that raising type oversets frames whose heights are data
tokens. That is not true of these panels: `_section_body` **computes** each
panel's height from `type_warranty_body_font_size` and the two leadings, so the
panels self-size. What the estimate must not do is read different values from
the ones the paragraph style prints -- so it now resolves them through the same
language cascade.

Two mechanisms had to change and both are guarded here:

`para_styles` had no language at all, which is why a `lang_jp_type_*` row would
have been a dead row. It takes one now, and only the roles listed below read it
through `lsz`. Pointing `lsz` at a key that already carries another language's
row would activate a shipped book -- the spec family's fr/es/de/it rows are the
live example -- so a test pins that no other language declares these.

`_language_param` in warranty.py read `ctx.language` raw. That is the writer's
source code "ja" while every layout row is keyed on the phase2 suffix "jp", so
it looked up a prefix nothing declares. Normalizing costs nothing: no
`lang_ja_` row exists anywhere in the repo.

Scope: BP@US rebuilt before and after is content-identical across all 318
entries.
"""

from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path

from tools.idml.params import load_layout_params, param_pt
from tools.idml.styles import para_styles

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/layout_params.csv"
OVERLAY = ROOT / "data/layout_params.idml-compact.csv"

# style -> (built before, master)
MASTER = {
    "HB Warranty Body": ((6.0, 6.0), (7.0, 9.0)),
    "HB Warranty List": ((6.0, 7.2), (7.0, 9.0)),
    "HB Warranty Note": ((6.0, 7.2), (7.0, 9.0)),
    "HB Warranty Lead": ((7.0, 8.2), (7.0, 11.0)),
    "HB Warranty Title": ((8.0, 8.8), (7.58, 8.8)),
}

SCOPED_KEYS = (
    "type_warranty_body_font_size",
    "type_warranty_body_font_leading",
    "idml_warranty_body_font_leading",
    "type_warranty_lead_font_size",
    "type_warranty_lead_font_leading",
    "idml_warranty_title_font_size",
    "type_warranty_title_font_leading",
)


def params():
    return load_layout_params(BASE, [OVERLAY])


def styles_for(language: str) -> dict[str, tuple[float, float]]:
    return {
        name: (size, leading)
        for name, size, leading, _weight, _kind in para_styles(params(), language)
    }


class TheJapaneseBookTakesTheMastersScale(unittest.TestCase):
    def test_every_warranty_role_lands_on_its_master_value(self) -> None:
        got = styles_for("ja")
        for name, (_before, (size, leading)) in MASTER.items():
            with self.subTest(style=name):
                self.assertAlmostEqual(size, got[name][0], delta=0.01)
                self.assertAlmostEqual(leading, got[name][1], delta=0.01)

    def test_the_source_code_resolves_like_the_row_prefix(self) -> None:
        """The writer says "ja"; the rows say "jp". Both must land."""
        self.assertEqual(styles_for("ja"), styles_for("jp"))


class NoOtherBookMoves(unittest.TestCase):
    def test_english_keeps_exactly_what_it_printed(self) -> None:
        got = styles_for("en")
        for name, ((size, leading), _master) in MASTER.items():
            with self.subTest(style=name):
                self.assertAlmostEqual(size, got[name][0], delta=0.01)
                self.assertAlmostEqual(leading, got[name][1], delta=0.01)

    def test_so_does_every_other_language_in_the_family(self) -> None:
        english = styles_for("en")
        for code in ("fr", "es", "de", "it", "uk", "ko", "zh", "pt"):
            with self.subTest(language=code):
                got = styles_for(code)
                for name in MASTER:
                    self.assertEqual(english[name], got[name])

    def test_declaring_no_language_is_the_shared_table(self) -> None:
        self.assertEqual(styles_for(""), styles_for("en"))

    def test_only_japanese_declares_any_of_the_scoped_keys(self) -> None:
        """A row here for another language would activate a shipped book."""
        rows: dict[str, str] = {}
        for path in (BASE, OVERLAY):
            with path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    key = (row.get("key") or "").strip()
                    if key:
                        rows[key] = (row.get("value") or "").strip()
        for key in SCOPED_KEYS:
            pattern = re.compile(r"^lang_([a-z]{2})_" + re.escape(key) + r"$")
            declared = sorted(
                m.group(1) for m in (pattern.match(k) for k in rows) if m
            )
            with self.subTest(key=key):
                self.assertIn(declared, ([], ["jp"]), f"{key}: {declared}")


class TheSpecFamilyStaysOffTheCascade(unittest.TestCase):
    """The keys that would move four shipped books if `lsz` reached them."""

    COLLIDING = (
        "type_spec_label_font_size",
        "type_spec_label_font_leading",
        "type_spec_value_font_size",
        "type_spec_value_font_leading",
        "type_spec_note_font_size",
        "type_spec_note_font_leading",
        "type_list_font_leading",
    )

    def test_they_still_carry_other_languages_rows(self) -> None:
        p = params()
        self.assertAlmostEqual(
            5.6, param_pt(p, "lang_de_type_spec_label_font_size", 0.0), delta=0.01
        )
        self.assertAlmostEqual(
            5.9, param_pt(p, "lang_fr_type_spec_value_font_size", 0.0), delta=0.01
        )

    def test_the_style_table_still_reads_them_language_blind(self) -> None:
        """If one of these moved onto `lsz`, German and French would shift."""
        source = (ROOT / "tools/idml/styles.py").read_text(encoding="utf-8")
        for key in self.COLLIDING:
            with self.subTest(key=key):
                self.assertNotIn(f'lsz("{key}"', source)

    def test_and_the_style_table_proves_it_by_not_moving(self) -> None:
        de = styles_for("de")
        en = styles_for("en")
        for name in ("HB Spec Label", "HB Spec Value"):
            if name in de:
                self.assertEqual(en[name], de[name])


class TheHeightEstimateReadsWhatTheStylePrints(unittest.TestCase):
    """A panel sized for 6.00 pt type that prints 7.00 pt would overset."""

    def test_the_estimate_uses_the_language_cascade(self) -> None:
        source = (ROOT / "tools/idml/components/warranty.py").read_text(
            encoding="utf-8"
        )
        for key in (
            "type_warranty_body_font_size",
            "idml_warranty_body_font_leading",
            "type_warranty_body_font_leading",
        ):
            with self.subTest(key=key):
                self.assertIn(f'_language_param(ctx, "{key}"', source)

    def test_the_cascade_normalizes_the_language(self) -> None:
        source = (ROOT / "tools/idml/components/warranty.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("normalize_lang(ctx.language)", source)


class TheBuiltPages(unittest.TestCase):
    """Read out of the shipped IDML. Skipped on an unbuilt tree."""

    IDML = ROOT / "docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml"
    # Two threaded frames of 473.67 pt each.
    CAPACITY = 947.34

    def setUp(self) -> None:
        if not self.IDML.is_file():
            self.skipTest("JBP-2000B JP has not been built in this tree")
        import zipfile

        self.zip = zipfile.ZipFile(self.IDML)
        self.story = self.zip.read(
            "Stories/Story_st_warranty_ja.xml"
        ).decode("utf-8")

    def test_the_styles_print_the_master_values(self) -> None:
        styles = self.zip.read("Resources/Styles.xml").decode("utf-8")
        for name, (_before, (size, leading)) in MASTER.items():
            match = re.search(
                r'<ParagraphStyle\b[^>]*Self="ParagraphStyle/'
                + re.escape(name)
                + r'".*?</ParagraphStyle>',
                styles,
                re.S,
            )
            self.assertIsNotNone(match, name)
            block = match.group(0)
            with self.subTest(style=name):
                self.assertIn(f'PointSize="{size:g}"', block)
                self.assertIn(f"<Leading type=\"unit\">{leading:g}<", block)

    def test_the_panels_self_sized_and_the_story_still_fits(self) -> None:
        total = 0.0
        panels = 0
        for match in re.finditer(
            r"<ParagraphStyleRange\b([^>]*)>(.*?)</ParagraphStyleRange>",
            self.story,
            re.S,
        ):
            attrs, body = match.group(1), match.group(2)
            before = re.search(r'SpaceBefore="([\d.]+)"', attrs)
            after = re.search(r'SpaceAfter="([\d.]+)"', attrs)
            heights = []
            for rect in re.finditer(
                r"<Rectangle\b[^>]*>(.*?)</Rectangle>", body, re.S
            ):
                points = [
                    tuple(float(v) for v in raw.split())
                    for raw in re.findall(
                        r'<PathPointType Anchor="([-\d.]+ [-\d.]+)"', rect.group(1)
                    )
                ]
                if points:
                    ys = [p[1] for p in points]
                    heights.append(max(ys) - min(ys))
            if heights:
                panels += 1
            total += max(heights, default=0.0)
            total += float(before.group(1)) if before else 0.0
            total += float(after.group(1)) if after else 0.0
        # The h1 pill and the lead-in are text frames, not rectangles.
        for match in re.finditer(
            r"<TextFrame\b([^>]*)>(.*?)</TextFrame>", self.story, re.S
        ):
            parent = re.search(r'ParentStory="([^"]+)"', match.group(1))
            if not parent or not (
                "h1pill" in parent.group(1) or "warranty_lead" in parent.group(1)
            ):
                continue
            points = [
                tuple(float(v) for v in raw.split())
                for raw in re.findall(
                    r'<PathPointType Anchor="([-\d.]+ [-\d.]+)"', match.group(2)
                )
            ]
            if points:
                ys = [p[1] for p in points]
                total += max(ys) - min(ys)
        self.assertEqual(7, panels, "the master pins seven warranty panels")
        self.assertLess(
            total,
            self.CAPACITY,
            f"warranty story {total:.2f} pt exceeds its two frames",
        )
        # Measured 766.42 at the master's scale, against 498.13 of panels
        # before. Guard the margin rather than the exact figure.
        self.assertGreater(self.CAPACITY - total, 60.0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
