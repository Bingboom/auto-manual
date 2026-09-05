"""The JP warranty pages set in the shared warranty style.

The house style has one warranty type scale and every book prints it: body and
notes 6.00/6.00, list items 6.00/7.20, lead-in 7.00/8.20, section titles
8.00/8.80, with the BP variant's shared 7.0 pt rendered leading. An earlier pass
measured the hand-made JP PDF instead -- 7.00 pt DemiLight at 9.00, lead at
11.00, titles at 7.58 -- and wrote six `lang_jp_` rows to reproduce it. That
forked JP off the shared style to chase production error. The rows are gone and
this file now pins the opposite: Japanese resolves to exactly what English does.

Two mechanisms from that pass stay, because they are correct regardless of the
values: `para_styles` takes a language and reads the warranty roles through
`lsz`, so a genuine CJK fitting row could be declared later without dead-row
risk; and `_section_body` resolves size and leadings through the same cascade
the style uses, so the height estimate can never budget for a different type
than the page prints. `sz` stays language-blind on purpose -- pointing `lsz` at
a key another language already declares (the spec family) would move four
shipped books.

Fit at the shared scale, by the builder's own line estimator: every one of the
seven panels holds its copy (tightest cmp2 at +4.54 pt), and the story threads
across its two 473.669 pt frames with the break after 購入証明について and
about 101 pt to spare -- against 3.29 pt at the measured scale.

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

# The shared warranty scale: (size, leading) per paragraph style.
SHARED = {
    "HB Warranty Body": (6.0, 6.0),
    "HB Warranty List": (6.0, 7.2),
    "HB Warranty Note": (6.0, 7.2),
    "HB Warranty Lead": (7.0, 8.2),
    "HB Warranty Title": (8.0, 8.8),
}

# Keys the style table reads through `lsz`. A language row on any of these is
# a deliberate fitting decision, never a copy of a master.
SCOPED_KEYS = (
    "type_warranty_body_font_size",
    "type_warranty_body_font_leading",
    "idml_warranty_body_font_leading",
    "type_warranty_lead_font_size",
    "type_warranty_lead_font_leading",
    "idml_warranty_title_font_size",
    "type_warranty_title_font_leading",
    "idml_warranty_variant_bp_default_body_font_leading",
)


def params():
    return load_layout_params(BASE, [OVERLAY])


def styles_for(language: str) -> dict[str, tuple[float, float]]:
    return {
        name: (size, leading)
        for name, size, leading, _weight, _kind in para_styles(params(), language)
    }


def language_rows() -> dict[str, str]:
    rows: dict[str, str] = {}
    for path in (BASE, OVERLAY):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                key = (row.get("key") or "").strip()
                if key:
                    rows[key] = (row.get("value") or "").strip()
    return rows


class JapaneseIsTheSharedStyle(unittest.TestCase):
    def test_every_warranty_role_is_the_shared_value(self) -> None:
        got = styles_for("ja")
        for name, (size, leading) in SHARED.items():
            with self.subTest(style=name):
                self.assertAlmostEqual(size, got[name][0], delta=0.01)
                self.assertAlmostEqual(leading, got[name][1], delta=0.01)

    def test_japanese_equals_english_exactly(self) -> None:
        en, ja = styles_for("en"), styles_for("ja")
        for name in SHARED:
            with self.subTest(style=name):
                self.assertEqual(en[name], ja[name])

    def test_and_so_does_every_other_language(self) -> None:
        english = styles_for("en")
        for code in ("jp", "fr", "es", "de", "it", "uk", "ko", "zh", "pt", ""):
            with self.subTest(language=code or "(none)"):
                got = styles_for(code)
                for name in SHARED:
                    self.assertEqual(english[name], got[name])

    def test_japanese_declares_none_of_the_scoped_warranty_keys(self) -> None:
        """A JP row here would be the book forking off the shared style again.

        Other languages may carry a fitting row -- Italian's 6.2 pt variant
        leading predates this work and is the legitimate pattern -- so the
        assertion is about Japanese, not about the table being empty.
        """
        rows = language_rows()
        for key in SCOPED_KEYS:
            pattern = re.compile(r"^lang_([a-z]{2})_" + re.escape(key) + r"$")
            declared = sorted(m.group(1) for m in map(pattern.match, rows) if m)
            with self.subTest(key=key):
                self.assertNotIn("jp", declared, f"{key}: {declared}")
                self.assertNotIn("ja", declared, f"{key}: {declared}")

    def test_the_only_preexisting_fitting_row_is_italian(self) -> None:
        rows = language_rows()
        declared = sorted(
            k.split("_")[1]
            for k in rows
            if re.fullmatch(
                r"lang_[a-z]{2}_idml_warranty_variant_bp_default_body_font_leading", k
            )
        )
        self.assertEqual(["it"], declared)

    def test_the_shared_variant_leading_is_the_only_one(self) -> None:
        self.assertAlmostEqual(
            7.0,
            param_pt(params(), "idml_warranty_variant_bp_default_body_font_leading", 0.0),
            delta=0.01,
        )


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
    """A panel budgeted for one type size that prints another would overset."""

    def test_the_estimate_uses_the_same_cascade_as_the_style(self) -> None:
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
    FRAME = 473.669
    CAPACITY = 2 * FRAME

    def setUp(self) -> None:
        if not self.IDML.is_file():
            self.skipTest("JBP-2000B JP has not been built in this tree")
        import zipfile

        self.zip = zipfile.ZipFile(self.IDML)
        self.story = self.zip.read("Stories/Story_st_warranty_ja.xml").decode("utf-8")

    def test_the_styles_print_the_shared_values(self) -> None:
        styles = self.zip.read("Resources/Styles.xml").decode("utf-8")
        for name, (size, leading) in SHARED.items():
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

    def _walk(self):
        """Yield (name, step) for every block in the threaded story."""
        frames = {}
        for match in re.finditer(
            r"<TextFrame\b([^>]*)>(.*?)</TextFrame>", self.story, re.S
        ):
            parent = re.search(r'ParentStory="([^"]+)"', match.group(1))
            points = [
                tuple(float(v) for v in raw.split())
                for raw in re.findall(
                    r'<PathPointType Anchor="([-\d.]+ [-\d.]+)"', match.group(2)
                )
            ]
            if parent and points:
                ys = [p[1] for p in points]
                frames[parent.group(1)] = max(ys) - min(ys)
        for index, match in enumerate(
            re.finditer(
                r"<ParagraphStyleRange\b([^>]*)>(.*?)</ParagraphStyleRange>",
                self.story,
                re.S,
            )
        ):
            attrs, body = match.group(1), match.group(2)
            before = re.search(r'SpaceBefore="([\d.]+)"', attrs)
            after = re.search(r'SpaceAfter="([\d.]+)"', attrs)
            height, name = 0.0, f"block{index}"
            rect = re.search(
                r'<Rectangle\b[^>]*Self="(bg_warranty_[^"]+)"(.*?)</Rectangle>',
                body,
                re.S,
            )
            if rect:
                points = [
                    tuple(float(v) for v in raw.split())
                    for raw in re.findall(
                        r'<PathPointType Anchor="([-\d.]+ [-\d.]+)"', rect.group(2)
                    )
                ]
                ys = [p[1] for p in points]
                height = max(ys) - min(ys)
                name = rect.group(1).replace("bg_warranty_st_warranty_ja_", "")
            else:
                for key, value in frames.items():
                    if ("h1pill" in key and index == 0) or (
                        "warranty_lead" in key and index == 1
                    ):
                        height = value
            yield name, (
                (float(before.group(1)) if before else 0.0)
                + height
                + (float(after.group(1)) if after else 0.0)
            )

    def test_seven_panels_and_the_story_fits_with_room(self) -> None:
        steps = list(self._walk())
        self.assertEqual(7, sum(1 for name, _ in steps if name.startswith("cmp")))
        total = sum(step for _, step in steps)
        self.assertLess(total, self.CAPACITY)
        # Shared scale: 498.13 of panels; roughly 590 of 947 with lead and pill.
        self.assertGreater(self.CAPACITY - total, 300.0)

    def test_the_break_falls_after_the_fifth_section_with_room(self) -> None:
        """Page one holds 保証期間 through 購入証明について; page two the rest.

        At the shared scale this break carries about 100 pt of margin, against
        the 3.29 pt it was pushed to when the measured JP scale was in force.
        """
        cumulative, page, placed, margin_before_break = 0.0, 1, {}, None
        for name, step in self._walk():
            if cumulative + step > self.FRAME * page:
                margin_before_break = self.FRAME * page - cumulative
                page += 1
                cumulative = self.FRAME * (page - 1)
            cumulative += step
            placed[name] = page
        for panel in ("cmp2", "cmp3", "cmp4", "cmp5", "cmp6"):
            self.assertEqual(1, placed[panel], f"{panel} left page one")
        for panel in ("cmp7", "cmp8"):
            self.assertEqual(2, placed[panel], f"{panel} climbed onto page one")
        self.assertIsNotNone(margin_before_break)
        self.assertGreater(margin_before_break, 50.0)


class TheSeventhSectionFittingRow(unittest.TestCase):
    """A budget/render mismatch, compensated where it bites and named as such.

    `_section_body` budgets body lines at `idml_warranty_body_font_leading`
    (6.0) while the BP variant renders them at 7.0. Sections 1-6 absorb the
    1 pt/line deficit through the shared `panel_height_adjust_1..6` slack;
    there is no `_7`, and only the JP book has a seventh section, so 免責事項
    overset by 5.00 pt at shared values. The measured JP leading rows had
    masked that by making budget equal render. This row compensates it
    honestly -- a fitting row, not a measurement -- until the budget is fixed
    to read the rendered leading, at which point the row must go.
    """

    KEY = "lang_jp_idml_warranty_panel_height_adjust_7"

    def test_the_row_exists_at_the_fitting_value(self) -> None:
        self.assertAlmostEqual(5.5, param_pt(params(), self.KEY, 0.0), delta=0.01)

    def test_it_is_justified_as_compensation_not_measurement(self) -> None:
        with OVERLAY.open(encoding="utf-8-sig", newline="") as handle:
            comment = next(
                (row.get("comment") or "")
                for row in csv.DictReader(handle)
                if (row.get("key") or "").strip() == self.KEY
            )
        self.assertIn("budget/render mismatch", comment)
        self.assertIn("not a measurement", comment)
        self.assertNotIn("master", comment.lower())

    def test_no_shared_seventh_row_exists(self) -> None:
        """The shared table stops at six because the reference book has six."""
        rows = language_rows()
        self.assertNotIn("idml_warranty_panel_height_adjust_7", rows)
        others = sorted(
            k.split("_")[1]
            for k in rows
            if re.fullmatch(r"lang_[a-z]{2}_idml_warranty_panel_height_adjust_7", k)
        )
        self.assertEqual(["jp"], others)


class TheBuiltSeventhSection(unittest.TestCase):
    """cmp8 must hold its copy, counting forced breaks and paragraph air."""

    IDML = ROOT / "docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml"

    def setUp(self) -> None:
        if not self.IDML.is_file():
            self.skipTest("JBP-2000B JP has not been built in this tree")
        import zipfile

        self.zip = zipfile.ZipFile(self.IDML)

    def test_every_warranty_body_frame_holds_its_rendered_copy(self) -> None:
        from tools.idml.line_metrics import estimated_line_count

        parent = self.zip.read("Stories/Story_st_warranty_ja.xml").decode("utf-8")
        frames = {}
        for match in re.finditer(r"<TextFrame\b([^>]*)>(.*?)</TextFrame>", parent, re.S):
            owner = re.search(r'ParentStory="(st_anchor_warranty_body_[^"]+)"', match.group(1))
            if not owner:
                continue
            pts = [
                tuple(float(v) for v in raw.split())
                for raw in re.findall(r'<PathPointType Anchor="([-\d.]+ [-\d.]+)"', match.group(2))
            ]
            frames[owner.group(1)] = (
                max(p[0] for p in pts) - min(p[0] for p in pts),
                max(p[1] for p in pts) - min(p[1] for p in pts),
            )
        self.assertEqual(7, len(frames))
        for sid, (width, height) in sorted(frames.items()):
            story = self.zip.read(f"Stories/Story_{sid}.xml").decode("utf-8")
            need = 0.0
            for para in re.finditer(
                r"<ParagraphStyleRange\b([^>]*)>(.*?)</ParagraphStyleRange>", story, re.S
            ):
                attrs, body = para.group(1), para.group(2)
                if not "".join(re.findall(r"<Content>([^<]*)</Content>", body)).strip():
                    continue
                style = re.search(r'ParagraphStyle/([^"]+)"', attrs).group(1)
                lead_attr = re.search(r'Leading="([\d.]+)"', attrs)
                lead_inline = re.search(r'<Leading type="unit">([\d.]+)<', body)
                leading = (
                    float(lead_attr.group(1))
                    if lead_attr
                    else float(lead_inline.group(1))
                    if lead_inline
                    else (7.2 if "List" in style else 6.0)
                )
                before = re.search(r'SpaceBefore="([\d.]+)"', attrs)
                after = re.search(r'SpaceAfter="([\d.]+)"', attrs)
                indent = re.search(r'LeftIndent="([\d.]+)"', attrs)
                measure = width - (float(indent.group(1)) if indent else 0.0)
                lines = 0
                for segment in re.split(r"<Br/>", body):
                    text = "".join(re.findall(r"<Content>([^<]*)</Content>", segment)).strip()
                    if text:
                        lines += estimated_line_count(
                            text, measure, point_size=6.0,
                            narrow_width_ratio=0.50, minimum_narrow_chars=8,
                        )
                need += max(lines, 1) * leading
                need += float(before.group(1)) if before else 0.0
                need += float(after.group(1)) if after else 0.0
            with self.subTest(panel=sid.split("_cmp")[-1]):
                self.assertLessEqual(need, height + 0.01, f"{sid}: {need:.2f} > {height:.3f}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
