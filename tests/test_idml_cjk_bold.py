"""Emphasis must survive a fallback-font run, but only where the face exists.

Japanese labels authored as `**警告**` were rendering at body weight. The
fallback-font branch in `_style_range` hardcoded `FontStyle="Regular"` and sat
in front of the bold branch as an `elif`, so bold was dropped for every run that
needed a fallback face -- which is every CJK run. The same flattening reached
component headers through `drop_duplicate_font_style`, which keeps the last
`FontStyle` on a doubled attribute and therefore kept the fallback's Regular.

Weight is now requested only when the bundled family actually ships the face,
because asking InDesign for a missing face substitutes the whole run.
"""

from __future__ import annotations

import unittest
from dataclasses import replace

from tools.idml import inline_text
from tools.idml.font_family import (
    BULLET_FONT_FAMILY_TOKEN,
    CJK_FONT_FAMILY_TOKEN,
    JAPANESE_FONT_FAMILY_TOKEN,
    KOREAN_FONT_FAMILY_TOKEN,
    PRIMARY_FONT_FAMILY_TOKEN,
    IdmlFontFace,
    family_declares_style,
)


class FamilyDeclaresStyle(unittest.TestCase):
    def test_primary_family_declares_the_weights_it_ships(self) -> None:
        for style in ("Regular", "Medium", "Semibold", "Bold", "Heavy"):
            self.assertTrue(
                family_declares_style(PRIMARY_FONT_FAMILY_TOKEN.name, style), style
            )

    def test_regular_only_families_do_not_claim_bold(self) -> None:
        for token in (
            JAPANESE_FONT_FAMILY_TOKEN,
            KOREAN_FONT_FAMILY_TOKEN,
            CJK_FONT_FAMILY_TOKEN,
            BULLET_FONT_FAMILY_TOKEN,
        ):
            self.assertTrue(family_declares_style(token.name, "Regular"), token.name)
            self.assertFalse(family_declares_style(token.name, "Bold"), token.name)

    def test_unknown_family_declares_nothing(self) -> None:
        self.assertFalse(family_declares_style("No Such Family", "Bold"))

    def test_style_match_ignores_case(self) -> None:
        self.assertTrue(family_declares_style(PRIMARY_FONT_FAMILY_TOKEN.name, "bold"))


class BoldSurvivesFallbackRuns(unittest.TestCase):
    def test_latin_bold_is_unchanged(self) -> None:
        xml = inline_text._style_range("WARNING", bold=True, fallback_font=None)
        self.assertIn('FontStyle="Bold"', xml)

    def test_bold_is_kept_when_the_fallback_family_ships_the_face(self) -> None:
        xml = inline_text._style_range(
            "X", bold=True, fallback_font=PRIMARY_FONT_FAMILY_TOKEN.name
        )
        self.assertIn('FontStyle="Bold"', xml)
        self.assertNotIn('FontStyle="Regular"', xml)

    def test_bold_is_withheld_when_the_family_has_only_regular(self) -> None:
        """Withholding is deliberate: a missing face substitutes the whole run."""
        for token in (JAPANESE_FONT_FAMILY_TOKEN, KOREAN_FONT_FAMILY_TOKEN):
            xml = inline_text._style_range("保証", bold=True, fallback_font=token.name)
            self.assertIn('FontStyle="Regular"', xml, token.name)
            self.assertNotIn('FontStyle="Bold"', xml, token.name)

    def test_symbol_fallbacks_never_take_bold(self) -> None:
        xml = inline_text._style_range(
            "●", bold=True, fallback_font=BULLET_FONT_FAMILY_TOKEN.name
        )
        self.assertIn('FontStyle="Regular"', xml)
        self.assertNotIn('FontStyle="Bold"', xml)

    def test_unbolded_fallback_run_is_regular(self) -> None:
        xml = inline_text._style_range(
            "説明", bold=False, fallback_font=CJK_FONT_FAMILY_TOKEN.name
        )
        self.assertIn('FontStyle="Regular"', xml)

    def test_japanese_bold_flows_once_the_face_is_provisioned(self) -> None:
        """The gate is the only thing holding Japanese emphasis back.

        Provisioning a Bold face for the Japanese family must be sufficient to
        restore emphasis; nothing else in the run serializer should need to
        change. This pins that contract so a future font drop cannot silently
        fail to take effect.
        """
        bold_face = IdmlFontFace(
            resource_id="ff_hb_manual_sans_jp_b",
            name=f"{JAPANESE_FONT_FAMILY_TOKEN.name} Bold",
            postscript_name="HBManualSansJP-Bold",
            style_name="Bold",
            font_type="OpenTypeTT",
        )
        provisioned = replace(
            JAPANESE_FONT_FAMILY_TOKEN,
            faces=JAPANESE_FONT_FAMILY_TOKEN.faces + (bold_face,),
        )
        from tools.idml import font_family

        original = font_family._ALL_FAMILY_TOKENS
        # Substitute rather than append: the lookup returns on the first token
        # matching the family name, so an appended copy would never be reached.
        font_family._ALL_FAMILY_TOKENS = tuple(
            provisioned if token.name == JAPANESE_FONT_FAMILY_TOKEN.name else token
            for token in original
        )
        try:
            xml = inline_text._style_range(
                "保証期間", bold=True, fallback_font=JAPANESE_FONT_FAMILY_TOKEN.name
            )
        finally:
            font_family._ALL_FAMILY_TOKENS = original
        self.assertIn('FontStyle="Bold"', xml)


class DuplicateFontStyleCollapse(unittest.TestCase):
    def test_doubled_bold_collapses_to_bold(self) -> None:
        """Component Bold plus a Bold-capable fallback must stay bold.

        This is the component-header path. Before the gate it produced
        Bold + Regular and collapsed to Regular; with a Bold-capable family it
        produces Bold + Bold and must collapse to Bold.
        """
        xml = (
            '<CharacterStyleRange A="1" FontStyle="Bold" FontStyle="Bold">'
            "<Content>症状</Content></CharacterStyleRange>"
        )
        self.assertIn('FontStyle="Bold"', inline_text.drop_duplicate_font_style(xml))

    def test_single_font_style_is_untouched(self) -> None:
        xml = (
            '<CharacterStyleRange A="1" FontStyle="Regular">'
            "<Content>x</Content></CharacterStyleRange>"
        )
        self.assertEqual(xml, inline_text.drop_duplicate_font_style(xml))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
