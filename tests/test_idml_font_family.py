"""Primary IDML font-family token contract tests."""
from __future__ import annotations

import ast
import hashlib
import unittest
from pathlib import Path

from tools.idml.delivery import _FONT_ROWS, _fonts_manifest
from tools.idml.flow_idml import DEFAULT_STYLE_MAP, _flow_style_entries
from tools.idml.font_family import CJK_FONT_FAMILY_TOKEN, PRIMARY_FONT_FAMILY_TOKEN
from tools.idml.params import load_layout_params
from tools.idml.style_resources import fonts_xml
from tools.idml.styles import styles_xml


ROOT = Path(__file__).resolve().parents[1]


class IdmlFontFamilyTokenTest(unittest.TestCase):
    def test_default_font_outputs_remain_byte_identical(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        artifacts = {
            "styles": styles_xml(params),
            "fonts": fonts_xml(),
            "flow": _flow_style_entries(DEFAULT_STYLE_MAP),
            "manifest": _fonts_manifest(False),
        }
        expected = {
            "styles": "976fecc19b2e7173624d09bb5acf29ebfeccbb47cdb4e5172f7067fad529676d",
            "fonts": "a6ffc78a2bc432085da2dc64aec6b4b2f8b3db8bf0d6d453b0812f919f608762",
            "flow": "111c9d93d62ba1b250d743af51db9bfb8079c1a675201e96d895e1c18ceb4211",
            "manifest": "979a2f14eef398db91ec091c2f716fd40625e78ef0ab0b8563f201eff06169a4",
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
