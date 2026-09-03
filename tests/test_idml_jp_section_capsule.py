"""The JP safety page sets its section heading in the capsule its master prints.

Reference page index 2 puts 「絵表示について」 inside a 313.07 x 13.91 pt dark
stadium -- fill (0.2519, 0.2495, 0.2560) = HB Brand Dark, a six-item
line/curve path, radius = height/2 -- holding 7.00 pt reversed CJKjp-Bold
inset 7.30 pt from the capsule's left edge. That is the same chrome the
symbols page carries as a page title, and a different object from the 20.07 pt
`lclllc` chapter bar the master uses for chapter openers.

The build set it as a plain 8 pt `Heading2` paragraph in the running copy.

Two things had to be true for the fix to be small. The safety story already
renders `component` blocks inline, so a promoted heading needs no new sink;
and `render_emphasispill` already anchors a rounded group in the flow, so it
needed a variant rather than a new emitter.

Scope is the delicate part. `CompactSafetyPanel` is shared: BP@JP reaches it
through `add_safety_signals_page`, BP@US and BP@EU through
`add_safety_symbols_page`. So the promotion is opt-in at the call site --
`from_blocks(..., subbar_capsule=True)` -- and only the signals page asks.
`safety_signals` is declared by one contract.

The pre-existing `full_width_subbar` variant is deliberately left alone. It is
passed by `prose_flow.py`'s maintenance promotion and read by nobody, so that
bar renders text-fitted today; honouring it would change JE-3000C KR, whose
contract is the only one declaring `preface_safety_maintenance`.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.idml.components.compact_safety_panel import CompactSafetyPanelData
from tools.idml.params import load_layout_params, param_pt

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs/renderers/contracts/target_assembly"
OVERLAY = ROOT / "data/layout_params.idml-compact.csv"

# Measured on reference page index 2 with PyMuPDF.
MASTER = {
    "width": 313.07,
    "height": 13.91,
    "font_size": 7.0,
    "text_inset": 7.30,
    # Centre-to-centre against the neighbouring 11.50 pt lines, less half of
    # each box: 23.12 - (5.75 + 6.955) and 15.31 - (6.955 + 5.75).
    "space_before": 10.42,
    "space_after": 2.61,
}

BLOCKS = [
    ("h1", "使用上のご注意"),
    ("list", "・ある注意事項"),
    ("h2", "絵表示について"),
    ("body", "製品を安全に正しくお使いいただき"),
]


def params():
    return load_layout_params(ROOT / "data/layout_params.csv", [OVERLAY])


class ThePromotionIsOptIn(unittest.TestCase):
    def test_the_default_leaves_every_block_alone(self) -> None:
        """BP@US and BP@EU reach this same constructor."""
        data = CompactSafetyPanelData.from_blocks(BLOCKS, story_title="s")
        self.assertEqual(
            tuple(b for b in BLOCKS if b[0] != "h1"), data.body_blocks
        )
        self.assertIn(("h2", "絵表示について"), data.body_blocks)

    def test_opting_in_replaces_the_heading_with_a_capsule(self) -> None:
        data = CompactSafetyPanelData.from_blocks(
            BLOCKS, story_title="s", subbar_capsule=True, language="jp"
        )
        kinds = [kind for kind, _ in data.body_blocks]
        self.assertNotIn("h2", kinds)
        self.assertIn("component", kinds)
        spec = json.loads(
            next(text for kind, text in data.body_blocks if kind == "component")
        )
        self.assertEqual("emphasispill", spec["kind"])
        self.assertEqual("section_capsule", spec["layout_variant"])
        self.assertEqual(["絵表示について"], spec["texts"])

    def test_the_language_travels_on_the_spec(self) -> None:
        """The writer's own tag is the source code (ja), not the row prefix (jp)."""
        data = CompactSafetyPanelData.from_blocks(
            BLOCKS, story_title="s", subbar_capsule=True, language="jp"
        )
        spec = json.loads(
            next(text for kind, text in data.body_blocks if kind == "component")
        )
        self.assertEqual("jp", spec["language"])

    def test_nothing_else_moves_and_order_is_kept(self) -> None:
        data = CompactSafetyPanelData.from_blocks(
            BLOCKS, story_title="s", subbar_capsule=True, language="jp"
        )
        self.assertEqual(
            ["list", "component", "body"],
            [kind for kind, _ in data.body_blocks],
        )

    def test_a_page_without_a_heading_grows_no_capsule(self) -> None:
        plain = [("h1", "t"), ("body", "b")]
        data = CompactSafetyPanelData.from_blocks(
            plain, story_title="s", subbar_capsule=True, language="jp"
        )
        self.assertEqual((("body", "b"),), data.body_blocks)

    def test_only_the_first_heading_is_promoted(self) -> None:
        two = [("h1", "t"), ("h2", "one"), ("body", "b"), ("h2", "two")]
        data = CompactSafetyPanelData.from_blocks(
            two, story_title="s", subbar_capsule=True, language="jp"
        )
        self.assertEqual(
            ["component", "body", "h2"],
            [kind for kind, _ in data.body_blocks],
        )


class TheDeclaredGeometryIsTheMasters(unittest.TestCase):
    def test_height(self) -> None:
        self.assertAlmostEqual(
            MASTER["height"],
            param_pt(params(), "lang_jp_idml_section_capsule_height", 0.0),
            delta=0.01,
        )

    def test_font_size(self) -> None:
        self.assertAlmostEqual(
            MASTER["font_size"],
            param_pt(params(), "lang_jp_idml_section_capsule_font_size", 0.0),
            delta=0.01,
        )

    def test_text_inset(self) -> None:
        self.assertAlmostEqual(
            MASTER["text_inset"],
            param_pt(params(), "lang_jp_idml_section_capsule_text_inset", 0.0),
            delta=0.01,
        )

    def test_the_rhythm_around_it(self) -> None:
        self.assertAlmostEqual(
            MASTER["space_before"],
            param_pt(params(), "lang_jp_idml_section_capsule_space_before", 0.0),
            delta=0.01,
        )
        self.assertAlmostEqual(
            MASTER["space_after"],
            param_pt(params(), "lang_jp_idml_section_capsule_space_after", 0.0),
            delta=0.01,
        )

    def test_a_stadium_needs_no_radius_token(self) -> None:
        """`anchored_panel_group_paragraph` is handed height/2."""
        self.assertAlmostEqual(6.955, MASTER["height"] / 2.0, delta=0.01)

    def test_no_other_language_declares_the_capsule(self) -> None:
        declared = sorted({
            key.split("_")[1]
            for key in params()
            if key.startswith("lang_") and "_idml_section_capsule_" in key
        })
        self.assertEqual(["jp"], declared)


class TheBuiltCapsule(unittest.TestCase):
    """Read out of the shipped IDML, not the code.

    Skipped where the book has not been built, so the suite stays green on a
    clean checkout; it is the operator-facing assertion, run after a build.
    """

    IDML = ROOT / "docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml"
    STORY = (
        "Stories/Story_st_anchor_section_capsule_"
        "st_safety_info_ja_cmp12.xml"
    )

    def setUp(self) -> None:
        if not self.IDML.is_file():
            self.skipTest("JBP-2000B JP has not been built in this tree")
        import zipfile

        self.zip = zipfile.ZipFile(self.IDML)
        if self.STORY not in self.zip.namelist():
            self.skipTest("build predates the section capsule")
        self.story = self.zip.read(self.STORY).decode("utf-8")

    def test_it_holds_the_heading(self) -> None:
        import re

        self.assertEqual(
            "絵表示について",
            "".join(re.findall(r"<Content>([^<]*)</Content>", self.story)),
        )

    def test_the_type_is_the_masters_size(self) -> None:
        import re

        self.assertEqual(
            {"7"}, set(re.findall(r'PointSize="([\d.]+)"', self.story))
        )

    def test_the_type_is_bold_like_the_master(self) -> None:
        """`HB Emphasis Pill` is not in the Japanese weight map, so a CJK run
        arrives carrying Regular; the capsule asserts Bold over it."""
        import re

        self.assertEqual(
            {"Bold"}, set(re.findall(r'FontStyle="([^"]+)"', self.story))
        )

    def test_it_is_a_stadium_at_the_masters_measure(self) -> None:
        import re

        body = self.zip.read("Stories/Story_st_safety_info_ja.xml").decode("utf-8")
        found = []
        for match in re.finditer(
            r'<Rectangle\b[^>]*FillColor="Color/HB Brand Dark"[^>]*>(.*?)</Rectangle>',
            body,
            re.S,
        ):
            points = [
                tuple(float(v) for v in raw.split())
                for raw in re.findall(
                    r'<PathPointType Anchor="([-\d.]+ [-\d.]+)"', match.group(1)
                )
            ]
            if points:
                found.append(points)
        self.assertEqual(1, len(found), "expected exactly one capsule")
        points = found[0]
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        self.assertEqual(8, len(points), "a stadium carries eight anchors")
        self.assertAlmostEqual(MASTER["height"], max(ys) - min(ys), delta=0.02)
        # The build's measure is 312.09 against the master's 313.07 bar -- a
        # page-measure difference that predates this change.
        self.assertAlmostEqual(312.09, max(xs) - min(xs), delta=0.05)

    def test_the_heading_paragraph_is_gone_from_the_flow(self) -> None:
        body = self.zip.read("Stories/Story_st_safety_info_ja.xml").decode("utf-8")
        self.assertNotIn("ParagraphStyle/Heading2", body)


class Scope(unittest.TestCase):
    def _declaring(self, composition: str) -> list[str]:
        found = []
        for path in sorted(CONTRACTS.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for page in data.get("pages", []):
                if page.get("composition_type") == composition:
                    found.append(path.stem.replace("_v1_candidate", ""))
        return sorted(set(found))

    def test_one_contract_declares_the_signals_page(self) -> None:
        self.assertEqual(["jbp2000b_jp"], self._declaring("safety_signals"))

    def test_the_other_books_take_the_symbols_page_instead(self) -> None:
        """That call site does not opt in, which is what keeps them still."""
        self.assertEqual(
            ["jbp2000b_eu", "jbp2000b_us"], self._declaring("safety_symbols")
        )

    def test_the_korean_maintenance_variant_is_a_different_name(self) -> None:
        """Renaming either would silently move JE-3000C KR."""
        source = (ROOT / "tools/idml/prose_flow.py").read_text(encoding="utf-8")
        self.assertIn('"layout_variant": "full_width_subbar"', source)
        self.assertNotIn("section_capsule", source)
        self.assertEqual(
            ["je3000c_kr"], self._declaring("preface_safety_maintenance")
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
