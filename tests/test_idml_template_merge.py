#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract for baking the export into the designer template package.

tools/idml/template_merge.merge_into_template swaps the template's
style/colour/font Resources into our self-contained export so the result opens
pre-styled (no InCopy Place). The invariants that make that safe:

- the template's Styles.xml / Fonts.xml replace ours wholesale;
- colours our content references but the template lacks are injected into the
  template's Graphic.xml (so no reference dangles);
- mimetype stays first and stored; everything else (Spreads/Stories/…) is ours.
"""
from __future__ import annotations

import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from idml.template_merge import merge_into_template  # noqa: E402

_PKG = (
    "Resources/Styles.xml", "Resources/Graphic.xml", "Resources/Fonts.xml",
    "Spreads/Spread_a.xml", "Stories/Story_a.xml", "designmap.xml",
)


def _write_idml(path: Path, styles: str, graphic: str, fonts: str,
                story: str, spread: str = "<spread/>") -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package",
                   compress_type=zipfile.ZIP_STORED)
        z.writestr("Resources/Styles.xml", styles)
        z.writestr("Resources/Graphic.xml", graphic)
        z.writestr("Resources/Fonts.xml", fonts)
        z.writestr("Spreads/Spread_a.xml", spread)
        z.writestr("Stories/Story_a.xml", story)
        z.writestr("designmap.xml", "<designmap/>")


class TemplateMergeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        self.ours = self.tmp / "ours.idml"
        self.tpl = self.tmp / "tpl.idml"
        self.out = self.tmp / "out.idml"
        # ours: a body style + a brand swatch used by the story
        _write_idml(
            self.ours,
            styles='<idPkg:Styles xmlns:idPkg="x"><RootParagraphStyleGroup>'
                   '<ParagraphStyle Self="ParagraphStyle/正文" Name="正文" PointSize="99"/>'
                   '</RootParagraphStyleGroup><RootObjectStyleGroup>'
                   '<ObjectStyle Self="ObjectStyle/HB Rounded Table Outer" '
                   'Name="HB Rounded Table Outer"/>'
                   '</RootObjectStyleGroup></idPkg:Styles>',
            graphic='<idPkg:Graphic xmlns:idPkg="x">'
                    '<Color Self="Color/HB Bg K05" Name="HB Bg K05" ColorValue="0 0 0 5"/>'
                    '</idPkg:Graphic>',
            fonts='<idPkg:Fonts xmlns:idPkg="x"><FontFamily Name="Ours"/></idPkg:Fonts>',
            story='<Story>'
                  # non-cell reference to the brand swatch -> drives injection
                  '<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/正文" '
                  'ParagraphShadingColor="Color/HB Bg K05">'
                  # a real (non-self-closing) cell carrying local overrides
                  '<Table AppliedTableStyle="TableStyle/正文表格">'
                  '<Cell Self="c0" Name="0:0" RowSpan="1" ColumnSpan="1" '
                  'AppliedCellStyle="CellStyle/$ID/[None]" FillColor="Color/黑色" '
                  'TopInset="3" LeftInset="4" TopEdgeStrokeWeight="0">hello</Cell>'
                  '</Table></ParagraphStyleRange></Story>',
            spread='<Spread><Rectangle Self="r0" ContentType="Unassigned" '
                   'AppliedObjectStyle="ObjectStyle/HB Rounded Table Outer" '
                   'FillColor="Color/HB Bg K05"/></Spread>',
        )
        # template: same-named body style but the DESIGNER definition (7pt),
        # and no HB Bg K05 swatch
        _write_idml(
            self.tpl,
            styles='<idPkg:Styles xmlns:idPkg="x"><RootParagraphStyleGroup>'
                   '<ParagraphStyle Self="ParagraphStyle/正文" Name="正文" PointSize="7"/>'
                   '</RootParagraphStyleGroup><RootObjectStyleGroup>'
                   '<ObjectStyle Self="ObjectStyle/$ID/[None]" Name="$ID/[None]"/>'
                   '</RootObjectStyleGroup></idPkg:Styles>',
            graphic='<idPkg:Graphic xmlns:idPkg="x">'
                    '<Color Self="Color/黑色" Name="黑色" ColorValue="0 0 0 100"/>'
                    '</idPkg:Graphic>',
            fonts='<idPkg:Fonts xmlns:idPkg="x"><FontFamily Name="Designer"/></idPkg:Fonts>',
            story='<Story/>',
        )

    def test_merge_adopts_template_and_injects_missing_color(self) -> None:
        res = merge_into_template(self.ours, self.tpl, self.out)
        self.assertEqual(res["injected_colors"], ["Color/HB Bg K05"])
        self.assertEqual(res["unresolved_colors"], [])
        with zipfile.ZipFile(self.out) as z:
            names = z.namelist()
            styles = z.read("Resources/Styles.xml").decode()
            graphic = z.read("Resources/Graphic.xml").decode()
            fonts = z.read("Resources/Fonts.xml").decode()
            story = z.read("Stories/Story_a.xml").decode()
        # template style definition wins (7pt), not ours (99pt)
        self.assertIn('PointSize="7"', styles)
        self.assertNotIn('PointSize="99"', styles)
        # object styles referenced by our spread are merged into the
        # template style resource instead of dangling after replacement.
        self.assertIn('Self="ObjectStyle/HB Rounded Table Outer"', styles)
        # template fonts adopted
        self.assertIn("Designer", fonts)
        self.assertNotIn("Ours", fonts)
        # missing brand swatch injected, template swatch kept
        self.assertIn('Self="Color/HB Bg K05"', graphic)
        self.assertIn('Self="Color/黑色"', graphic)
        # our content preserved verbatim
        self.assertIn('AppliedParagraphStyle="ParagraphStyle/正文"', story)
        # cell overrides stripped so template region cell styles govern; Self /
        # Name / content kept, fill+inset gone
        self.assertNotIn("FillColor", story.split("<Cell", 1)[1].split(">", 1)[0])
        self.assertNotIn("Inset", story)
        self.assertIn('TopEdgeStrokeWeight="0"', story)
        self.assertIn('<Cell Self="c0" Name="0:0"', story)
        self.assertIn(">hello</Cell>", story)
        # mimetype first and stored
        self.assertEqual(names[0], "mimetype")
        with zipfile.ZipFile(self.out) as z:
            self.assertEqual(z.getinfo("mimetype").compress_type, zipfile.ZIP_STORED)

    def test_every_reference_resolves_after_merge(self) -> None:
        merge_into_template(self.ours, self.tpl, self.out)
        import re
        with zipfile.ZipFile(self.out) as z:
            styles = z.read("Resources/Styles.xml").decode()
            graphic = z.read("Resources/Graphic.xml").decode()
            story = z.read("Stories/Story_a.xml").decode()
            spread = z.read("Spreads/Spread_a.xml").decode()
        defined_p = set(re.findall(r'<ParagraphStyle\b[^>]*?\bSelf="([^"]*)"', styles))
        defined_c = set(re.findall(r'<Color\b[^>]*?\bSelf="([^"]*)"', graphic))
        defined_o = set(re.findall(r'<ObjectStyle\b[^>]*?\bSelf="([^"]*)"', styles))
        used_p = set(re.findall(r'AppliedParagraphStyle="([^"]*)"', story))
        used_c = set(re.findall(r'FillColor="([^"]*)"', story))
        used_o = set(re.findall(r'AppliedObjectStyle="([^"]*)"', spread))
        self.assertEqual(used_p - defined_p, set())
        self.assertEqual(used_c - defined_c, set())
        self.assertEqual(used_o - defined_o, set())


if __name__ == "__main__":
    unittest.main()
