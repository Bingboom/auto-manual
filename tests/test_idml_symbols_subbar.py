"""The symbols page opens with a section capsule, not a chapter bar.

Reference page 3 sets 絵表示の説明 in a 313.1 x 13.9 pt dark stadium at radius
6.95 -- h/2 -- with reversed type. The build opened the page with the 20.1 pt
H1 bar, which the master keeps for chapter openers: page 2's 使用上のご注意 is
one, sharp on top and rounded south.

Nothing new was needed. `heading_bar_opts(2, ...)` asks for a `capsule_bg`,
`capsule_xml` draws that at radius = height / 2, and `comp_subbar_height` has
carried 13.9 all along -- the safety panel component already draws its own
subbar exactly this way. `SymbolIconsPanel` was the one place still asking for
a level-1 bar.

Scope: `SymbolIconsPanel` renders the `symbols_icons` composition, and one
contract declares it. BP@US and BP@EU render `safety_symbols`, JE-3000C KR
renders `symbols`; all four IDML goldens regenerate byte-identical.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.idml.page_objects import heading_bar_opts
from tools.idml.params import load_layout_params, param_pt

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs/renderers/contracts/target_assembly"

# Measured on reference page index 3: the capsule is 313.1 x 13.9 pt, fill
# (0.252, 0.25, 0.256) = HB Brand Dark, radius 6.88-6.92, and the type inside is
# 7.00 pt NotoSansCJKjp-Bold in white.
MASTER_HEIGHT = 13.9
MASTER_RADIUS = 6.95
MASTER_POINT_SIZE = 7.0
OVERLAY = ROOT / "data/layout_params.idml-compact.csv"
SIZE_KEY = "idml_compact_symbols_title_font_size"


class TheShapeTheMasterPrints(unittest.TestCase):
    def test_the_subbar_height_is_the_master_height(self) -> None:
        params = load_layout_params(ROOT / "data/layout_params.csv")
        self.assertAlmostEqual(
            MASTER_HEIGHT,
            param_pt(params, "comp_subbar_height", 0.0),
            delta=0.02,
        )

    def test_a_level_two_bar_is_a_capsule(self) -> None:
        """`capsule_bg` is what makes `capsule_xml` round it at h/2."""
        self.assertTrue(heading_bar_opts(2, (0, 0, 0, 0)).get("capsule_bg"))

    def test_a_level_one_bar_is_not(self) -> None:
        """The chapter opener keeps its own sharp-top treatment."""
        opts = heading_bar_opts(1, (0, 0, 0, 0))
        self.assertTrue(opts.get("h1_bar_bg"))
        self.assertNotIn("capsule_bg", opts)

    def test_half_the_master_height_is_the_master_radius(self) -> None:
        """A stadium's radius is h/2, which is why no radius token is needed."""
        self.assertAlmostEqual(MASTER_RADIUS, MASTER_HEIGHT / 2.0, delta=0.02)


class TheTypeInsideIt(unittest.TestCase):
    """The capsule's type is 7.00 pt, a point under the shared subbar size."""

    def test_the_japanese_row_carries_the_master_size(self) -> None:
        params = load_layout_params(ROOT / "data/layout_params.csv", [OVERLAY])
        self.assertAlmostEqual(
            MASTER_POINT_SIZE,
            param_pt(params, f"lang_jp_{SIZE_KEY}", 0.0),
            delta=0.01,
        )

    def test_the_shared_subbar_size_did_not_move(self) -> None:
        """`type_subbar_font_size` also feeds params.tex and every other book."""
        params = load_layout_params(ROOT / "data/layout_params.csv", [OVERLAY])
        self.assertAlmostEqual(
            8.0, param_pt(params, "type_subbar_font_size", 0.0), delta=0.01
        )

    def test_no_other_language_declares_the_override(self) -> None:
        """A row here would activate silently the moment the sink reads it."""
        params = load_layout_params(ROOT / "data/layout_params.csv", [OVERLAY])
        declared = sorted(
            key.split("_")[1]
            for key in params
            if key.startswith("lang_") and key.endswith(SIZE_KEY)
        )
        self.assertEqual(["jp"], declared)

    def test_the_fallback_is_the_shared_size(self) -> None:
        """A language with no row keeps whatever the book already printed."""
        params = load_layout_params(ROOT / "data/layout_params.csv", [OVERLAY])
        base = param_pt(params, "type_subbar_font_size", 6.6)
        self.assertAlmostEqual(
            base, param_pt(params, f"lang_en_{SIZE_KEY}", base), delta=0.01
        )


class Scope(unittest.TestCase):
    def test_one_contract_declares_the_symbols_icons_composition(self) -> None:
        """Pins that the capsule reaches exactly one book."""
        declaring = []
        for path in sorted(CONTRACTS.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for page in data.get("pages", []):
                if page.get("composition_type") == "symbols_icons":
                    declaring.append(path.stem)
        self.assertEqual(["jbp2000b_jp_v1_candidate"], sorted(set(declaring)))

    def test_the_other_books_render_other_symbol_compositions(self) -> None:
        """If these moved onto `symbols_icons`, they would inherit the capsule."""
        found: dict[str, set[str]] = {}
        for path in sorted(CONTRACTS.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for page in data.get("pages", []):
                kind = page.get("composition_type") or ""
                if "symbol" in kind or kind == "safety_signals":
                    found.setdefault(path.stem, set()).add(kind)
        self.assertEqual({"safety_symbols"}, found["jbp2000b_us_v1_candidate"])
        self.assertEqual({"safety_symbols"}, found["jbp2000b_eu_v1_candidate"])
        self.assertEqual({"symbols"}, found["je3000c_kr_v1_candidate"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
