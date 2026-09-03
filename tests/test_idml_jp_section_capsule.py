"""The JP safety page sets its section heading in the shared subbar capsule.

The structural fact from the JP master: 「絵表示について」 is a section heading
inside running copy, and the house style sets such a heading in the subbar
capsule -- not the 20.07 pt chapter bar, not a plain paragraph. The build had
set it as a plain 8 pt `Heading2`. That mapping (heading -> capsule) is what a
master is for, and it is what this change keeps.

What the master is NOT for is geometry. An earlier pass measured the hand-made
JP PDF -- 13.91 tall, 7.00 pt, 7.30 inset, 10.42 / 2.61 of air -- and wrote six
`lang_jp_idml_section_capsule_*` rows to reproduce it. Those rows encoded human
production error as data and forked JP off the shared style. They are gone.
The capsule now reads the same tokens every other subbar reads:
`comp_subbar_height`, `type_subbar_font_size`, `type_subbar_font_leading`,
`comp_subbar_pad_lr`, and the pill's shared `idml_charging_emphasis_space_before`.

Two mechanisms carry it. The safety story already renders `component` blocks
inline, so a promoted heading needs no new sink; `render_emphasispill` already
anchors a rounded group in the flow, so it needed a variant, not an emitter.

Scope. `CompactSafetyPanel` is shared: BP@JP reaches it through
`add_safety_signals_page`, BP@US and BP@EU through `add_safety_symbols_page`.
The promotion is opt-in at the call site and only the signals page asks.
BP@US rebuilt before and after is content-identical across all 318 entries.

The pre-existing `full_width_subbar` variant stays untouched: no emitter reads
it, and honouring it would change JE-3000C KR.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from tools.idml.components.compact_safety_panel import CompactSafetyPanelData
from tools.idml.params import load_layout_params, param_pt

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs/renderers/contracts/target_assembly"
BASE = ROOT / "data/layout_params.csv"
OVERLAY = ROOT / "data/layout_params.idml-compact.csv"

BLOCKS = [
    ("h1", "使用上のご注意"),
    ("list", "・ある注意事項"),
    ("h2", "絵表示について"),
    ("body", "製品を安全に正しくお使いいただき"),
]


def params():
    return load_layout_params(BASE, [OVERLAY])


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
            BLOCKS, story_title="s", subbar_capsule=True
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

    def test_the_spec_carries_no_language(self) -> None:
        """A shared style has no per-language geometry to select."""
        data = CompactSafetyPanelData.from_blocks(
            BLOCKS, story_title="s", subbar_capsule=True
        )
        spec = json.loads(
            next(text for kind, text in data.body_blocks if kind == "component")
        )
        self.assertNotIn("language", spec)

    def test_nothing_else_moves_and_order_is_kept(self) -> None:
        data = CompactSafetyPanelData.from_blocks(
            BLOCKS, story_title="s", subbar_capsule=True
        )
        self.assertEqual(
            ["list", "component", "body"],
            [kind for kind, _ in data.body_blocks],
        )

    def test_a_page_without_a_heading_grows_no_capsule(self) -> None:
        plain = [("h1", "t"), ("body", "b")]
        data = CompactSafetyPanelData.from_blocks(
            plain, story_title="s", subbar_capsule=True
        )
        self.assertEqual((("body", "b"),), data.body_blocks)

    def test_only_the_first_heading_is_promoted(self) -> None:
        two = [("h1", "t"), ("h2", "one"), ("body", "b"), ("h2", "two")]
        data = CompactSafetyPanelData.from_blocks(
            two, story_title="s", subbar_capsule=True
        )
        self.assertEqual(
            ["component", "body", "h2"],
            [kind for kind, _ in data.body_blocks],
        )


class TheCapsuleIsTheSharedSubbar(unittest.TestCase):
    """No token of its own: the capsule is the subbar every book already has."""

    def test_no_language_declares_capsule_geometry(self) -> None:
        declared = sorted(
            key for key in params() if "_idml_section_capsule_" in key
        )
        self.assertEqual([], declared, "the capsule must not fork per language")

    def test_the_shared_subbar_tokens_are_what_it_reads(self) -> None:
        p = params()
        self.assertAlmostEqual(13.89, param_pt(p, "comp_subbar_height", 0.0), delta=0.02)
        self.assertAlmostEqual(8.0, param_pt(p, "type_subbar_font_size", 0.0), delta=0.01)
        self.assertAlmostEqual(9.6, param_pt(p, "type_subbar_font_leading", 0.0), delta=0.01)
        self.assertAlmostEqual(6.24, param_pt(p, "comp_subbar_pad_lr", 0.0), delta=0.02)

    def test_the_emitter_reads_those_tokens_and_no_language(self) -> None:
        source = (ROOT / "tools/idml/components/emphasis.py").read_text(encoding="utf-8")
        start = source.index("def _render_section_capsule(")
        end = source.index("def render_emphasispill(")
        body = source[start:end]
        for key in (
            "comp_subbar_height",
            "type_subbar_font_size",
            "type_subbar_font_leading",
            "comp_subbar_pad_lr",
        ):
            with self.subTest(key=key):
                self.assertIn(f'"{key}"', body)
        self.assertNotIn("lang_", body)
        self.assertNotIn("idml_section_capsule", body)


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
        self.flow = self.zip.read("Stories/Story_st_safety_info_ja.xml").decode("utf-8")

    def test_it_holds_the_heading(self) -> None:
        self.assertEqual(
            "絵表示について",
            "".join(re.findall(r"<Content>([^<]*)</Content>", self.story)),
        )

    def test_the_type_is_the_shared_subbar_size(self) -> None:
        self.assertEqual({"8"}, set(re.findall(r'PointSize="([\d.]+)"', self.story)))
        self.assertEqual(
            {"9.6"}, set(re.findall(r'<Leading type="unit">([\d.]+)<', self.story))
        )

    def test_the_type_is_bold(self) -> None:
        """`HB Emphasis Pill` is not in the Japanese weight map, so a CJK run
        arrives carrying Regular; the capsule asserts Bold over it."""
        self.assertEqual({"Bold"}, set(re.findall(r'FontStyle="([^"]+)"', self.story)))

    def test_the_inset_is_the_shared_pad(self) -> None:
        indents = {float(v) for v in re.findall(r'LeftIndent="([\d.]+)"', self.story)}
        self.assertEqual(1, len(indents))
        self.assertAlmostEqual(6.24, indents.pop(), delta=0.02)

    def test_the_air_is_the_pills_shared_air(self) -> None:
        match = re.search(r'SpaceBefore="([\d.]+)" SpaceAfter="([\d.]+)"', self.flow)
        self.assertIsNotNone(match)
        self.assertAlmostEqual(5.0, float(match.group(1)), delta=0.01)
        self.assertAlmostEqual(1.5, float(match.group(2)), delta=0.01)

    def test_it_is_a_stadium_at_the_subbar_height(self) -> None:
        found = []
        for match in re.finditer(
            r'<Rectangle\b[^>]*FillColor="Color/HB Brand Dark"[^>]*>(.*?)</Rectangle>',
            self.flow,
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
        self.assertAlmostEqual(13.89, max(ys) - min(ys), delta=0.02)
        self.assertAlmostEqual(312.09, max(xs) - min(xs), delta=0.05)

    def test_the_heading_paragraph_is_gone_from_the_flow(self) -> None:
        self.assertNotIn("ParagraphStyle/Heading2", self.flow)


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
