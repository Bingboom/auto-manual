"""The symbols page opens with a section capsule, not a chapter bar.

The structural fact from the JP master: 絵表示の説明 is a section heading, and
the house style sets a section heading in the subbar capsule -- radius h/2,
reversed type -- where a chapter opener (page 2's 使用上のご注意) takes the
20.1 pt H1 bar. The build opened the page with the H1 bar. That mapping is the
change.

Nothing new was needed for it. `heading_bar_opts(2, ...)` asks for a
`capsule_bg`, `capsule_xml` draws that at radius = height / 2, and
`comp_subbar_height` has carried 13.9 all along -- the safety panel component
already draws its own subbar exactly this way. `SymbolIconsPanel` was the one
place still asking for a level-1 bar.

The type inside it is the shared `type_subbar_font_size`. An earlier pass had
measured 7.00 pt off the hand-made JP PDF and declared a
`lang_jp_idml_compact_symbols_title_font_size` row to reproduce it; that was
production error written as data, and it is gone.

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
OVERLAY = ROOT / "data/layout_params.idml-compact.csv"

SUBBAR_HEIGHT = 13.9
SUBBAR_RADIUS = 6.95
SUBBAR_SIZE = 8.0


def params():
    return load_layout_params(ROOT / "data/layout_params.csv", [OVERLAY])


class TheShapeOfASectionCapsule(unittest.TestCase):
    def test_the_subbar_height_is_the_capsule_height(self) -> None:
        self.assertAlmostEqual(
            SUBBAR_HEIGHT,
            param_pt(params(), "comp_subbar_height", 0.0),
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

    def test_half_the_height_is_the_radius(self) -> None:
        """A stadium's radius is h/2, which is why no radius token is needed."""
        self.assertAlmostEqual(SUBBAR_RADIUS, SUBBAR_HEIGHT / 2.0, delta=0.02)


class TheTypeInsideIt(unittest.TestCase):
    """The capsule's type is the shared subbar size -- every book, one value."""

    def test_the_shared_subbar_size(self) -> None:
        self.assertAlmostEqual(
            SUBBAR_SIZE, param_pt(params(), "type_subbar_font_size", 0.0), delta=0.01
        )

    def test_no_language_declares_a_title_size_of_its_own(self) -> None:
        """A row here would fork one book off the shared style."""
        declared = sorted(
            key for key in params()
            if key.startswith("lang_") and key.endswith("idml_compact_symbols_title_font_size")
        )
        self.assertEqual([], declared)

    def test_the_panel_reads_the_shared_size_directly(self) -> None:
        source = (ROOT / "tools/idml/components/symbol_sections.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('param_pt(writer.params, "type_subbar_font_size"', source)
        self.assertNotIn("idml_compact_symbols_title_font_size", source)


class TheBuiltTitle(unittest.TestCase):
    IDML = ROOT / "docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml"

    def setUp(self) -> None:
        if not self.IDML.is_file():
            self.skipTest("JBP-2000B JP has not been built in this tree")
        import zipfile

        self.zip = zipfile.ZipFile(self.IDML)

    def test_the_title_sets_at_the_shared_subbar_size(self) -> None:
        import re

        story = self.zip.read("Stories/Story_st_jp_symbols_icons_title.xml").decode(
            "utf-8"
        )
        self.assertEqual({"8"}, set(re.findall(r'PointSize="([\d.]+)"', story)))


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
