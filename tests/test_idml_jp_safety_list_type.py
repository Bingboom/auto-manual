"""Japanese safety bullets are a CJK fitting row at the English value.

The compact safety list has a shared size (5.5/6.3) and a fitting row per
language, because the same style has to hold Romance-language copy that runs
long and CJK copy whose glyphs need more room than Latin at the same size:
en 6.0/6.8, fr and es 5.7, de and it 4.9, uk 4.7. That per-language row is the
one legitimate way a book departs from a shared value -- to fit, not to match a
picture.

An earlier pass declared the Japanese row at 7.00/11.50 because that is what
the hand-made JP PDF measured. A master is a structural key -- it says which
copy is a bullet list -- not a source of geometry; those two numbers were
production error written as data. The operator's ruling is that the Japanese
fitting row takes the English value, so the JP and EN rows are now identical
and this file pins that equality rather than any measurement.

Scope: `safety_story.py` builds `lang_<code>_idml_compact_safety_list_*` with
the shared value as the fallback, so nobody else's value moves.
"""

from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path

from tools.idml.params import load_layout_params, param_pt

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/layout_params.csv"
COMPACT = ROOT / "data/layout_params.idml-compact.csv"

SIZE_KEY = "idml_compact_safety_list_font_size"
LEADING_KEY = "idml_compact_safety_list_leading"


def params():
    return load_layout_params(BASE, (COMPACT,))


def declared(name: str) -> str:
    with COMPACT.open(encoding="utf-8") as handle:
        for row in csv.reader(handle):
            if row and row[0].strip() == name:
                return row[1].strip()
    return ""


class TheJapaneseRowIsTheEnglishRow(unittest.TestCase):
    def test_size_and_leading_equal_english(self) -> None:
        self.assertEqual(declared(f"lang_en_{SIZE_KEY}"), declared(f"lang_jp_{SIZE_KEY}"))
        self.assertEqual(
            declared(f"lang_en_{LEADING_KEY}"), declared(f"lang_jp_{LEADING_KEY}")
        )

    def test_which_is_six_on_six_point_eight(self) -> None:
        self.assertEqual("6.0", declared(f"lang_jp_{SIZE_KEY}"))
        self.assertEqual("6.8", declared(f"lang_jp_{LEADING_KEY}"))

    def test_the_row_is_justified_as_fitting_not_measurement(self) -> None:
        with COMPACT.open(encoding="utf-8") as handle:
            comments = {
                row[0].strip(): (row[3] if len(row) > 3 else "")
                for row in csv.reader(handle)
                if row
            }
        for key in (f"lang_jp_{SIZE_KEY}", f"lang_jp_{LEADING_KEY}"):
            with self.subTest(key=key):
                self.assertNotIn("measured from the JP master", comments[key])
                self.assertIn("English value", comments[key])

    def test_the_shared_default_is_untouched(self) -> None:
        self.assertEqual("5.5", declared(SIZE_KEY))
        self.assertEqual("6.3", declared(LEADING_KEY))


class Resolution(unittest.TestCase):
    """The cascade `safety_story.py` performs, exercised directly."""

    def resolve(self, key: str, language: str, default: float) -> float:
        resolved = params()
        return param_pt(
            resolved,
            f"lang_{language}_{key}",
            param_pt(resolved, key, default),
        )

    def test_japanese_resolves_to_the_english_metrics(self) -> None:
        self.assertAlmostEqual(6.0, self.resolve(SIZE_KEY, "jp", 5.0))
        self.assertAlmostEqual(6.8, self.resolve(LEADING_KEY, "jp", 5.8))
        self.assertAlmostEqual(
            self.resolve(SIZE_KEY, "en", 5.0), self.resolve(SIZE_KEY, "jp", 5.0)
        )

    def test_an_unnormalized_ja_falls_back(self) -> None:
        """`jp` is the live prefix -- the mistake #985 made in reverse."""
        self.assertAlmostEqual(5.5, self.resolve(SIZE_KEY, "ja", 5.0))

    def test_every_other_language_keeps_what_it_had(self) -> None:
        expected = {"en": 6.0, "fr": 5.7, "es": 5.7, "de": 4.9, "it": 4.9, "uk": 4.7}
        for language, size in expected.items():
            self.assertAlmostEqual(
                size, self.resolve(SIZE_KEY, language, 5.0), msg=language
            )

    def test_a_language_with_no_row_keeps_the_shared_value(self) -> None:
        for language in ("ko", "zh", "pt"):
            self.assertAlmostEqual(
                5.5, self.resolve(SIZE_KEY, language, 5.0), msg=language
            )


class BlastRadius(unittest.TestCase):
    def test_the_declaring_languages_are_the_expected_set(self) -> None:
        """A new language appearing here is a deliberate act, not a drift."""
        declaring = set()
        for table in (BASE, COMPACT):
            with table.open(encoding="utf-8") as handle:
                for row in csv.reader(handle):
                    if not row:
                        continue
                    m = re.fullmatch(
                        r"lang_([a-z]{2,3})_" + re.escape(SIZE_KEY), row[0].strip()
                    )
                    if m:
                        declaring.add(m.group(1))
        self.assertEqual({"en", "fr", "es", "de", "it", "uk", "jp"}, declaring)


class TheBuiltBullets(unittest.TestCase):
    IDML = ROOT / "docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml"

    def setUp(self) -> None:
        if not self.IDML.is_file():
            self.skipTest("JBP-2000B JP has not been built in this tree")
        import zipfile

        self.story = zipfile.ZipFile(self.IDML).read(
            "Stories/Story_st_safety_info_ja.xml"
        ).decode("utf-8")

    def test_the_list_runs_set_at_six_on_six_point_eight(self) -> None:
        lists = re.findall(
            r'AppliedParagraphStyle="ParagraphStyle/HB Safety List".*?</ParagraphStyleRange>',
            self.story,
            re.S,
        )
        self.assertTrue(lists)
        sizes = {v for block in lists for v in re.findall(r'PointSize="([\d.]+)"', block)}
        leads = {
            v for block in lists for v in re.findall(r'<Leading type="unit">([\d.]+)<', block)
        }
        self.assertEqual({"6"}, sizes)
        self.assertEqual({"6.8"}, leads)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
