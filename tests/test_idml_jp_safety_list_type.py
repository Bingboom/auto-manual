"""Japanese safety bullets take the size and pitch their own master prints.

The master sets the eleven 「使用上のご注意」 bullets at 7.00 pt on an 11.50 pt
pitch, full measure. The build set the same eleven items at 5.50/6.30 -- a
1.50 pt size gap on the largest single-page text population in the book.

The key was already read per language: `safety_story.py` builds
`lang_<code>_idml_compact_safety_list_font_size` and `..._leading` with the
shared value as the fallback, and en/fr/es/de/it/uk each already declare their
own. Japanese was simply missing from a table every other language is in, so
this is a data change and nobody else's value moves.

Two earlier readings of this same role were wrong, which is why the pairing is
pinned here rather than trusted: the first concluded the master has no bullet
list at all (it has eleven, at x 28.34), the second concluded the build sets
them in two columns (`column_measure` in safety_story.py feeds the components
inside the story, not the bullets, which run the full 312.09 pt measure).
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

# Measured on reference page index 2: eleven 「・」 bullets at x 28.34, seventeen
# composed lines, baselines 79.03..263.04 with every delta 11.50 (one 11.51).
# The size is confirmed on both axes -- glyph bbox height 19.992 = 7.0 x 2.856
# and a full-width advance of exactly 7.00 pt -- so it is not a text-matrix
# artefact.
MASTER_SIZE = 7.0
MASTER_LEADING = 11.5

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


class DeclaredMetrics(unittest.TestCase):
    def test_the_measured_values_are_declared(self) -> None:
        self.assertEqual(str(MASTER_SIZE), declared(f"lang_jp_{SIZE_KEY}"))
        self.assertEqual(str(MASTER_LEADING), declared(f"lang_jp_{LEADING_KEY}"))

    def test_the_shared_default_is_untouched(self) -> None:
        """BP@US and BP@EU read the shared value and keep it."""
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

    def test_japanese_takes_the_master_metrics(self) -> None:
        self.assertAlmostEqual(MASTER_SIZE, self.resolve(SIZE_KEY, "jp", 5.0))
        self.assertAlmostEqual(
            MASTER_LEADING, self.resolve(LEADING_KEY, "jp", 5.8)
        )

    def test_an_unnormalized_ja_falls_back(self) -> None:
        """`jp` is the live prefix -- the mistake #985 made in reverse."""
        self.assertAlmostEqual(5.5, self.resolve(SIZE_KEY, "ja", 5.0))

    def test_every_other_language_keeps_what_it_had(self) -> None:
        expected = {
            "en": 6.0,
            "fr": 5.7,
            "es": 5.7,
            "de": 4.9,
            "it": 4.9,
            "uk": 4.7,
        }
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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
