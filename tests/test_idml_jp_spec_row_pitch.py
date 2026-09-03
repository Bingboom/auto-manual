"""Japanese specification rows take the pitch their own master prints.

The shared `idml_compact_spec_table_row_height` is 11.0 pt and its comment says
it was measured from the battery-pack reference, but the JP master draws its
eleven rows at 14.95 pt with a 38.35 pt final multi-line row -- 188.34 pt of
shell against the 133.80 pt the build produced, or 71 percent. That was the
largest single geometry gap in the book.

The row-height key is already read per language: `spec_tables.py` builds
`lang_<code>_idml_compact_spec_table_row_height` with the shared value as the
fallback, and `lang_ko_idml_compact_spec_table_row_height` has been in the
Korean overlay for a while. So this is a data change, and BP@US and BP@EU --
which pin different masters -- keep the shared value.

The IDML goldens do not reach the compact specification table, so this is the
coverage for the change as well as for the isolation.
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

# Measured between the hairlines the master draws on reference page index 9:
# the lower stroked panel runs y 275.26..463.60 and holds eleven bands, ten at
# 14.95 pt and a final one at 38.35 pt. The panel is the specification table --
# its left column reads 認証 / 型番 / 定格容量 / バッテリータイプ / サイクル寿命 /
# サイズ&重量 / DC拡張ポート(入力) / (出力) / 充電温度 / 動作温度 / 保存温度.
MASTER_ORDINARY = 14.95
MASTER_MULTILINE = 38.35
MASTER_SHELL = 188.34

# Eleven rows, of which the last wraps -- the shape of the JP specification.
ROWS = [(f"label {n}", f"value {n}") for n in range(10)] + [
    ("保存温度", "-10℃〜45℃（最適：20℃〜30℃）で保管してください。長期保管の際は残量を確認してください。")
]


def params():
    return load_layout_params(BASE, (COMPACT,))


class DeclaredPitch(unittest.TestCase):
    def declared(self, name: str) -> str:
        with COMPACT.open(encoding="utf-8") as handle:
            for row in csv.reader(handle):
                if row and row[0].strip() == name:
                    return row[1].strip()
        return ""

    def test_the_measured_values_are_declared(self) -> None:
        self.assertEqual(
            str(MASTER_ORDINARY),
            self.declared("lang_jp_idml_compact_spec_table_row_height"),
        )
        self.assertEqual(
            str(MASTER_MULTILINE),
            self.declared("lang_jp_idml_compact_spec_table_multiline_min_height"),
        )

    def test_the_shared_default_is_untouched(self) -> None:
        """BP@US and BP@EU pin different masters and keep 11.0."""
        self.assertEqual("11.0", self.declared("idml_compact_spec_table_row_height"))
        self.assertEqual(
            "13.0", self.declared("idml_compact_spec_table_multiline_min_height")
        )


class ResolvedGeometry(unittest.TestCase):
    """Assert the resolution, not a total that depends on live source rows.

    The real specification rows live in `data/phase2`, which is a local mirror
    and not available to CI, so the shell total is verified by measuring the
    built IDML instead -- 187.8 pt against the master's 188.34 -- and recorded
    in the review ledger. What a test can own is which language resolves to
    which pitch.
    """

    def test_japanese_ordinary_rows_take_the_master_pitch(self) -> None:
        heights = spec_table_row_heights(
            ROWS, params(), density="compact", language="jp"
        )
        self.assertEqual(11, len(heights))
        for height in heights[:10]:
            self.assertAlmostEqual(MASTER_ORDINARY, height, delta=0.01)

    def test_japanese_multiline_minimum_resolves_to_the_master(self) -> None:
        self.assertAlmostEqual(
            MASTER_MULTILINE,
            param_pt(
                params(),
                "lang_jp_idml_compact_spec_table_multiline_min_height",
                0.0,
            ),
            delta=0.01,
        )

    def test_ten_master_rows_plus_the_multiline_row_reach_the_shell(self) -> None:
        """The arithmetic the two declared values are supposed to produce."""
        self.assertAlmostEqual(
            MASTER_SHELL, 10 * MASTER_ORDINARY + MASTER_MULTILINE, delta=1.0
        )

    def test_the_shell_still_fits_its_frame(self) -> None:
        """The spec frame is 245.8 pt and also carries the 20.1 pt H1 pill."""
        self.assertLess(10 * MASTER_ORDINARY + MASTER_MULTILINE + 20.1, 245.8)

    def test_an_unnormalized_ja_falls_back_to_the_shared_pitch(self) -> None:
        """The renderer passes the normalized code, so `jp` is the live prefix.

        Pins that a caller handing this sink `ja` gets the shared value rather
        than the Japanese one -- the mistake #985 made in the other direction.
        """
        resolved = params()
        as_ja = spec_table_row_heights(
            ROWS, resolved, density="compact", language="ja"
        )
        shared = spec_table_row_heights(
            ROWS, resolved, density="compact", language="en"
        )
        self.assertEqual(
            [round(h, 2) for h in shared], [round(h, 2) for h in as_ja]
        )


class OtherLanguagesAreUnaffected(unittest.TestCase):
    def test_every_other_language_keeps_the_shared_pitch(self) -> None:
        resolved = params()
        for language in ("en", "fr", "es", "de", "it", "uk", "zh"):
            heights = spec_table_row_heights(
                ROWS, resolved, density="compact", language=language
            )
            for height in heights[:10]:
                self.assertAlmostEqual(11.0, height, delta=0.01, msg=language)

    def test_korean_keeps_its_own_declared_pitch(self) -> None:
        """The precedent this change follows, still in force."""
        # The Korean overlay replaces the compact one rather than stacking on
        # it -- the loader refuses an overlay that redefines a key.
        korean = load_layout_params(BASE, (KOREAN,))
        heights = spec_table_row_heights(
            ROWS, korean, density="compact", language="ko"
        )
        for height in heights[:10]:
            self.assertAlmostEqual(12.2, height, delta=0.01)

    def test_only_japanese_and_korean_declare_a_row_pitch(self) -> None:
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
        self.assertEqual({"jp", "ko"}, declaring)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
