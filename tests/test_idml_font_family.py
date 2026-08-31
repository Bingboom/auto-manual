"""Primary IDML font-family token contract tests."""
from __future__ import annotations

import ast
import hashlib
import unittest
from pathlib import Path

from tools.idml.delivery import _FONT_ROWS, _fonts_manifest
from tools.idml.flow_idml import DEFAULT_STYLE_MAP, _flow_style_entries
from tools.idml.font_family import (
    BULLET_FONT_FAMILY_TOKEN,
    CIRCLED_NUMBER_FONT_FAMILY_TOKEN,
    CJK_FONT_FAMILY_TOKEN,
    KOREAN_FONT_FAMILY_TOKEN,
    PRIMARY_FONT_FAMILY_TOKEN,
    SYMBOL_FONT_FAMILY_TOKEN,
    TEXT_SYMBOL_FONT_FAMILY_TOKEN,
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
            "fonts": "7bef8c30988b0b8ceabb67734943995a172b2428fdc2c8772d67ac4afff16407",
            "fonts_ko": "319a2447dfeeea2e261f8c4fba614f1cacea844fee9989a6e4ef919bc3833f33",
            "flow": "111c9d93d62ba1b250d743af51db9bfb8079c1a675201e96d895e1c18ceb4211",
            "manifest": "11debfec1dfbb6cf041f57d213c12970e2c1982bc6cad89205b564218b08d5d5",
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

    def test_portable_symbol_tokens_drive_resources_and_delivery(self) -> None:
        fonts = fonts_xml()
        for index, token in enumerate(
            (
                TEXT_SYMBOL_FONT_FAMILY_TOKEN,
                SYMBOL_FONT_FAMILY_TOKEN,
                BULLET_FONT_FAMILY_TOKEN,
            ),
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
        self.assertNotIn("Segoe UI Symbol", fonts)
        self.assertNotIn("Yu Gothic", fonts)
        self.assertIs(
            CIRCLED_NUMBER_FONT_FAMILY_TOKEN,
            SYMBOL_FONT_FAMILY_TOKEN,
        )

    def test_korean_family_is_declared_only_in_korean_packages(self) -> None:
        family_decl = (
            f'<FontFamily Self="{KOREAN_FONT_FAMILY_TOKEN.resource_id}" '
            f'Name="{KOREAN_FONT_FAMILY_TOKEN.name}">'
        )
        self.assertNotIn(family_decl, fonts_xml())
        self.assertNotIn(family_decl, fonts_xml("ja"))
        self.assertIn(family_decl, fonts_xml("ko"))
        self.assertIn(family_decl, fonts_xml("ko-KR"))
        self.assertEqual(KOREAN_FONT_FAMILY_TOKEN.delivery_row, _FONT_ROWS[5])

    def test_hangul_routes_to_the_korean_text_face_not_the_symbol_face(self) -> None:
        from tools.idml.inline_text import _fallback_font

        self.assertEqual(KOREAN_FONT_FAMILY_TOKEN.name, _fallback_font("한"))
        self.assertEqual(KOREAN_FONT_FAMILY_TOKEN.name, _fallback_font("ㄱ"))
        self.assertEqual(CJK_FONT_FAMILY_TOKEN.name, _fallback_font("日"))
        self.assertEqual(CJK_FONT_FAMILY_TOKEN.name, _fallback_font("、"))
        self.assertIsNone(_fallback_font("A"))

    def test_contact_icons_route_to_one_bundled_portable_face(self) -> None:
        from tools.idml.inline_text import _fallback_font

        for icon in "☎✉◉":
            with self.subTest(icon=icon):
                self.assertEqual(
                    BULLET_FONT_FAMILY_TOKEN.name,
                    _fallback_font(icon),
                )

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
