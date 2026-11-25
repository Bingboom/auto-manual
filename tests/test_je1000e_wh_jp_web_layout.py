"""SlimPower H1 JP Web-layout edition: copy unchanged, layout-only differences declared."""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'manual_sources/JE-1000E-WH/JP/ja'
APPROVED = BASE / 'git-20261016-efb663e3-solar-voc'
EDITION = BASE / 'git-20261125-efb663e3-web-layout'
CIRCLED = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫'


def visible(markdown: str, *, circled_lcd: bool = False) -> str:
    """Whitespace-free visible copy of a generated manual.md (styles, tags and MyST markers removed)."""
    value = re.sub(r'<style.*?</style>', '', markdown, flags=re.S)
    value = re.sub(r'^```\{raw\} html\n|^```$', '', value, flags=re.M)
    if circled_lcd:
        value = re.sub(r'(class="hb-lcd-number">)(\d+)(<)',
                       lambda m: m.group(1) + CIRCLED[int(m.group(2)) - 1] + m.group(3), value)
    value = re.sub(r'<[^>]+>', '', value)
    value = re.sub(r'^#+ ', '', value, flags=re.M)
    value = re.sub(r'\{[a-z-]+\}`[^`]*`|^\(.*\)=$', '', value, flags=re.M)
    return ''.join(value.split())


class WebLayoutEditionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.approved = (APPROVED / 'web/ja/manual.md').read_text(encoding='utf-8')
        cls.edition = (EDITION / 'web/ja/manual.md').read_text(encoding='utf-8')
        cls.manifest = json.loads((EDITION / 'source_manifest.json').read_text(encoding='utf-8'))

    def test_copy_equals_approved_except_declared_differences(self):
        expected = visible(self.approved, circled_lcd=True)
        for old, new in [
            ('2.1/2.2', '2.12.2'),  # caption row: the joining slash was never printed
            ('2.3/2.4/2.5', '2.32.42.5'),
            ('オン3秒間長押し', 'オン3秒間長押し3s'),  # printed duration beside the clock
        ]:
            self.assertEqual(expected.count(old), 1, old)
            expected = expected.replace(old, new)
        # The 保証期間 badges ("3 年間 保証期間", "2 年間 保証期間") are not printed; the card title is.
        badges = re.search(r'3年間保証期間(1\.保証期間は.*?)2年間保証期間(2\.また、.*?確認ください。)', expected)
        self.assertIsNotNone(badges)
        expected = expected.replace(badges.group(0), '保証期間' + badges.group(1) + badges.group(2))
        self.assertEqual(visible(self.edition), expected)

    def test_acceptance_and_derivation(self):
        self.assertEqual(self.manifest['publication_status'], 'operator-approved-git-only-release')
        self.assertTrue(self.manifest['publication_eligible'])
        self.assertEqual(self.manifest['derived_from']['package'], APPROVED.name)
        approval = json.loads((EDITION / 'source/approval.json').read_text(encoding='utf-8'))
        self.assertEqual((approval['operator_quote'], approval['merge_authorization']), ('上线', 'MA-487'))
        ir = json.loads((EDITION / 'web/ja/manual.ir.json').read_text(encoding='utf-8'))
        self.assertTrue(ir['metadata']['publication_eligible'])

    def test_layout_markup(self):
        md = self.edition
        self.assertIn('<strong>火のそばや炎天下の車内、熱器具の周辺など高温（45℃以上）になる場所で使用したり、放置しない'
                      '</strong><br/>発熱や発火、破裂する原因になります。', md)
        self.assertNotRegex(md, r'^## 基本情報', 'specification groups stay sub-sections')
        self.assertRegex(md, r'(?m)^# 主な仕様$')
        self.assertIn('hb-lcd-mode-portrait', md)
        self.assertNotIn('hb-warranty-years', md)
        for slug in ('overview', 'power', 'stand_prepare', 'wood_prepare', 'concrete_prepare',
                     'app-phones', 'app-result'):
            self.assertIn(f'data-reference-id="{slug}"', md)

    def test_package_css_adds_no_paint(self):
        from tools.web.prepared_style_audit import paint_properties

        approved = (APPROVED / 'source/presentation.css').read_text(encoding='utf-8')
        edition = (EDITION / 'source/presentation.css').read_text(encoding='utf-8')
        self.assertTrue(edition.startswith(approved.rstrip('\n')))
        self.assertEqual(paint_properties(edition[len(approved):]), [])


if __name__ == '__main__':
    unittest.main()
