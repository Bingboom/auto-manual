"""Japanese specification rows take the shared pitch.

The shared `idml_compact_spec_table_row_height` is 11.0 pt and the multi-line
minimum 13.0. An earlier pass measured 14.95 / 38.35 between the hairlines of
the hand-made JP PDF and declared two `lang_jp_` rows to reproduce it -- a 71
percent taller shell, chasing production error rather than fitting text. Those
rows are gone.

The fitting question was asked properly before removing them: at the shared
pitch every specification cell holds its 6.0 pt / 6.6 pt text by the builder's
line model, the tightest at 0.49 pt of slack, and the multi-line rows resolve
to 23.8 rather than the 13.0 minimum. If InDesign's composer shows overset on
the acceptance open, the right answer is a fitting row derived from the text's
need -- not a measurement of someone else's layout.

`spec_tables.py` builds `lang_<code>_idml_compact_spec_table_row_height` with
the shared value as the fallback; the Korean overlay's 12.2 remains the one
declared fitting row, and that precedent is untouched.
"""

from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path

from tools.idml.params import load_layout_params, param_pt
from tools.idml.spec_tables import spec_table_row_heights

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/layout_params.csv"
COMPACT = ROOT / "data/layout_params.idml-compact.csv"
KOREAN = ROOT / "data/layout_params.idml-je3000c-kr.csv"

SHARED_ORDINARY = 11.0
SHARED_MULTILINE_MIN = 13.0

ROWS = [(f"label {n}", f"value {n}") for n in range(10)] + [
    ("保存温度", "-10℃〜45℃（最適：20℃〜30℃）で保管してください。長期保管の際は残量を確認してください。")
]


def params():
    return load_layout_params(BASE, (COMPACT,))


def declared(name: str) -> str:
    with COMPACT.open(encoding="utf-8") as handle:
        for row in csv.reader(handle):
            if row and row[0].strip() == name:
                return row[1].strip()
    return ""


class TheSharedPitch(unittest.TestCase):
    def test_the_shared_values_are_declared(self) -> None:
        self.assertEqual("11.0", declared("idml_compact_spec_table_row_height"))
        self.assertEqual("13.0", declared("idml_compact_spec_table_multiline_min_height"))

    def test_japanese_declares_no_pitch_of_its_own(self) -> None:
        self.assertEqual("", declared("lang_jp_idml_compact_spec_table_row_height"))
        self.assertEqual(
            "", declared("lang_jp_idml_compact_spec_table_multiline_min_height")
        )


class ResolvedGeometry(unittest.TestCase):
    def test_japanese_ordinary_rows_take_the_shared_pitch(self) -> None:
        heights = spec_table_row_heights(ROWS, params(), density="compact", language="jp")
        self.assertEqual(11, len(heights))
        for height in heights[:10]:
            self.assertAlmostEqual(SHARED_ORDINARY, height, delta=0.01)

    def test_japanese_equals_english(self) -> None:
        resolved = params()
        jp = spec_table_row_heights(ROWS, resolved, density="compact", language="jp")
        en = spec_table_row_heights(ROWS, resolved, density="compact", language="en")
        self.assertEqual([round(h, 2) for h in en], [round(h, 2) for h in jp])

    def test_the_multiline_minimum_resolves_to_the_shared_value(self) -> None:
        self.assertAlmostEqual(
            SHARED_MULTILINE_MIN,
            param_pt(
                params(),
                "lang_jp_idml_compact_spec_table_multiline_min_height",
                param_pt(params(), "idml_compact_spec_table_multiline_min_height", 0.0),
            ),
            delta=0.01,
        )


class OtherLanguagesAreUnaffected(unittest.TestCase):
    def test_every_language_keeps_the_shared_pitch(self) -> None:
        resolved = params()
        for language in ("en", "fr", "es", "de", "it", "uk", "zh", "jp"):
            heights = spec_table_row_heights(
                ROWS, resolved, density="compact", language=language
            )
            for height in heights[:10]:
                self.assertAlmostEqual(11.0, height, delta=0.01, msg=language)

    def test_korean_keeps_its_own_declared_fitting_pitch(self) -> None:
        """The one legitimate fitting row, and the precedent for any future one."""
        korean = load_layout_params(BASE, (KOREAN,))
        heights = spec_table_row_heights(ROWS, korean, density="compact", language="ko")
        for height in heights[:10]:
            self.assertAlmostEqual(12.2, height, delta=0.01)

    def test_only_korean_declares_a_row_pitch(self) -> None:
        """Pins the blast radius across all three layout tables."""
        declaring = set()
        for table in (BASE, COMPACT, KOREAN):
            with table.open(encoding="utf-8") as handle:
                for row in csv.reader(handle):
                    if not row:
                        continue
                    m = re.fullmatch(
                        r"lang_([a-z]{2,3})_idml_compact_spec_table_"
                        r"(row_height|multiline_min_height)",
                        row[0].strip(),
                    )
                    if m:
                        declaring.add(m.group(1))
        self.assertEqual({"ko"}, declaring)


class TheBuiltTable(unittest.TestCase):
    IDML = ROOT / "docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml"

    def setUp(self) -> None:
        if not self.IDML.is_file():
            self.skipTest("JBP-2000B JP has not been built in this tree")
        import zipfile

        self.story = zipfile.ZipFile(self.IDML).read(
            "Stories/Story_st_anchor_spec_jp0.xml"
        ).decode("utf-8")

    def test_ordinary_rows_are_the_shared_height(self) -> None:
        heights = sorted(
            {float(h) for h in re.findall(r'SingleRowHeight="([\d.]+)"', self.story)}
        )
        self.assertIn(11.0, heights)
        self.assertNotIn(14.95, heights)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
