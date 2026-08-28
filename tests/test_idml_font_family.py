"""Primary IDML font-family token contract tests."""
from __future__ import annotations

import ast
import hashlib
import unittest
from pathlib import Path

from tools.idml.delivery import _FONT_ROWS, _fonts_manifest
from tools.idml.flow_idml import DEFAULT_STYLE_MAP, _flow_style_entries
from tools.idml.font_family import (
    CIRCLED_NUMBER_FONT_FAMILY_TOKEN,
    CJK_FONT_FAMILY_TOKEN,
    KOREAN_FONT_FAMILY_TOKEN,
    PRIMARY_FONT_FAMILY_TOKEN,
    SYMBOL_FONT_FAMILY_TOKEN,
)
from tools.idml.params import load_layout_params
from tools.idml.style_resources import fonts_xml
from tools.idml.styles import styles_xml


ROOT = Path(__file__).resolve().parents[1]


class IdmlFontFamilyTokenTest(unittest.TestCase):
    def test_default_font_outputs_are_stable(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        artifacts = {
            "styles": styles_xml(params),
            "fonts": fonts_xml(),
            "fonts_ko": fonts_xml("ko"),
            "flow": _flow_style_entries(DEFAULT_STYLE_MAP),
            "manifest": _fonts_manifest(False),
        }
        expected = {
            "styles": "8a697432cd63084047142685060429eea6257a56e1fc3a8d6fe434362bafe316",
            "fonts": "09eac1cc0235a6321d7efff2771d48b6404a56e8a960471f66f4882dd690975d",
            "fonts_ko": "9553baefc211261034e83b98818745c81ff4da87d3743c073761fbc90c5e220f",
            "flow": "111c9d93d62ba1b250d743af51db9bfb8079c1a675201e96d895e1c18ceb4211",
            "manifest": "dbd80f1f24fd17fe24a7478cecf94942f0611a6a92134b08b431dee429122085",
        }
        actual = {
            name: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for name, text in artifacts.items()
        }
        self.assertEqual(expected, actual)

    def test_one_token_drives_styles_resources_and_delivery(self) -> None:
        family = PRIMARY_FONT_FAMILY_TOKEN.name
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        self.assertIn(
            f'<AppliedFont type="string">{family}</AppliedFont>',
            styles_xml(params),
        )
        self.assertIn(
            f'<AppliedFont type="string">{family}</AppliedFont>',
            _flow_style_entries(DEFAULT_STYLE_MAP),
        )
        self.assertIn(
            f'<FontFamily Self="{PRIMARY_FONT_FAMILY_TOKEN.resource_id}" '
            f'Name="{family}">',
            fonts_xml(),
        )
        self.assertEqual(PRIMARY_FONT_FAMILY_TOKEN.delivery_row, _FONT_ROWS[0])

    def test_cjk_token_drives_resources_and_delivery_without_byte_drift(self) -> None:
        family = CJK_FONT_FAMILY_TOKEN.name
        self.assertIn(
            f'<FontFamily Self="{CJK_FONT_FAMILY_TOKEN.resource_id}" '
            f'Name="{family}">',
            fonts_xml(),
        )
        self.assertEqual(CJK_FONT_FAMILY_TOKEN.delivery_row, _FONT_ROWS[1])

    def test_windows_symbol_tokens_drive_resources_and_delivery(self) -> None:
        fonts = fonts_xml()
        for index, token in enumerate(
            (SYMBOL_FONT_FAMILY_TOKEN, CIRCLED_NUMBER_FONT_FAMILY_TOKEN),
            start=2,
        ):
            with self.subTest(family=token.name):
                self.assertIn(
                    f'<FontFamily Self="{token.resource_id}" '
                    f'Name="{token.name}">',
                    fonts,
                )
                self.assertEqual(token.delivery_row, _FONT_ROWS[index])
        self.assertNotIn("Apple Symbols", fonts)
        self.assertNotIn("Apple SD Gothic Neo", fonts)

    def test_korean_family_is_declared_only_in_korean_packages(self) -> None:
        family_decl = (
            f'<FontFamily Self="{KOREAN_FONT_FAMILY_TOKEN.resource_id}" '
            f'Name="{KOREAN_FONT_FAMILY_TOKEN.name}">'
        )
        self.assertNotIn(family_decl, fonts_xml())
        self.assertNotIn(family_decl, fonts_xml("ja"))
        self.assertIn(family_decl, fonts_xml("ko"))
        self.assertIn(family_decl, fonts_xml("ko-KR"))
        self.assertEqual(KOREAN_FONT_FAMILY_TOKEN.delivery_row, _FONT_ROWS[4])

    def test_hangul_routes_to_the_korean_text_face_not_the_symbol_face(self) -> None:
        from tools.idml.inline_text import _fallback_font

        self.assertEqual(KOREAN_FONT_FAMILY_TOKEN.name, _fallback_font("한"))
        self.assertEqual(KOREAN_FONT_FAMILY_TOKEN.name, _fallback_font("ㄱ"))
        self.assertEqual(CJK_FONT_FAMILY_TOKEN.name, _fallback_font("日"))
        self.assertEqual(CJK_FONT_FAMILY_TOKEN.name, _fallback_font("、"))
        self.assertIsNone(_fallback_font("A"))

    def test_authority_modules_do_not_repeat_primary_family_literal(self) -> None:
        for relative_path in (
            "tools/idml/styles.py",
            "tools/idml/style_resources.py",
            "tools/idml/delivery.py",
            "tools/idml/flow_idml.py",
        ):
            tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
            literals = [
                node.value
                for node in ast.walk(tree)
                if isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and "Gilroy" in node.value
            ]
            self.assertEqual([], literals, relative_path)


if __name__ == "__main__":
    unittest.main()
