from __future__ import annotations

import copy
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools import plain_markdown_site as pms
from tools.gen_index_bundle import plan_materialized_pages
from tools.web_presentation import WebPresentationError, load_web_manual_contract, transform_web_fragment
from tools.word_bundle_html import build_word_bundle_html


def _table(declared: bool = True) -> str:
    cls = ' class="hb-lcd-icon-table"' if declared else ''
    return (
        f'<table{cls}><tbody><tr><td>1</td><td><img src="icon.png" alt="Wireless"/></td>'
        '<td>接続状態</td><td><div class="line-block"><div class="line">点灯: 接続。</div>'
        '<div class="line">消灯: 未接続。</div></div><ul><li><strong>Keep</strong> this.</li>'
        '</ul></td></tr></tbody></table>'
    )


class WebLcdTests(unittest.TestCase):
    def test_semantics_ignore_target_filename_and_artwork_grants(self) -> None:
        contract = copy.deepcopy(load_web_manual_contract())
        contract['figure_targets'] = []
        self.assertNotIn('lcd_icon_table', contract)
        for page in (True, False):
            source = _table(not page)
            with self.subTest(page=page):
                output = transform_web_fragment(
                    source, source_path=Path('renamed.rst'), model='OTHER', region='JP',
                    contract=contract, declared_lcd_icons=page,
                )
                soup = BeautifulSoup(output, 'html.parser')
                self.assertEqual(list(BeautifulSoup(source, 'html.parser').stripped_strings), list(soup.stripped_strings))
                self.assertEqual(soup.img['src'], 'icon.png')
                self.assertEqual(soup.img['alt'], 'Wireless')
                self.assertEqual(len(soup.select('.line')), 2)
                self.assertEqual(len(soup.select('li strong')), 1)
                self.assertEqual(soup.figure['tabindex'], '0')
                self.assertEqual(output, transform_web_fragment(output, source_path=Path('again.rst')))

    def test_undeclared_table_and_unapproved_artwork_remain_unchanged(self) -> None:
        source = _table(False)
        self.assertEqual(source, transform_web_fragment(
            source, source_path=Path('docs/_build/JE-1000F/US/rst/page/lcd_icons_en.rst'),
        ))
        art = '<img src="original.png" alt="Original art"/>'
        result = transform_web_fragment(
            art + source + _table(),
            source_path=Path('docs/_build/JE-1000F/JP/rst/page/03_product_overview_placeholder.rst'),
        )
        soup = BeautifulSoup(result, 'html.parser')
        self.assertEqual(soup.table, BeautifulSoup(source, 'html.parser').table)
        self.assertEqual(soup.img, BeautifulSoup(art, 'html.parser').img)
        self.assertEqual(len(soup.select('figure.hb-lcd-table-composition')), 1)
        self.assertFalse(soup.select('.hb-annotated-figure, .hb-composite-art'))

    def test_incomplete_declared_tables_fail_without_truncation(self) -> None:
        for source in (
            '', _table() * 2, _table().replace('<td>1</td>', ''),
            _table().replace('<td>1</td>', '<td></td>'),
            _table().replace('<td>1</td>', '<td colspan="2">1</td>'),
            _table().replace('<td>1</td>', '<td rowspan="2">1</td>'),
            _table().replace('src="icon.png"', 'src=""'),
            _table().replace('</tbody>', '</tbody><tbody></tbody>'),
            _table().replace('</tr>', '<td>Extra</td></tr>'),
            '<table><tbody></tbody></table>',
        ):
            with self.subTest(source=source), self.assertRaisesRegex(WebPresentationError, 'renamed.rst.*LCD'):
                transform_web_fragment(source, source_path=Path('renamed.rst'), declared_lcd_icons=True)
        with self.assertRaisesRegex(WebPresentationError, 'declaration must be on a table'):
            transform_web_fragment('<div class="hb-lcd-icon-table"></div>', source_path=Path('renamed.rst'))

    def test_bundle_uses_csv_identity_for_renamed_slot_once(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            pages = root / 'page'
            pages.mkdir()
            (pages / "icon.png").write_bytes(b"frozen test icon")
            declared, ordinary = pages / 'status_legend.rst', pages / 'lcd_icons_ja.rst'
            rst = ('.. list-table::\n\n   * - 1\n     - .. image:: icon.png\n'
                   '          :alt: Wireless\n     - 状態\n     - | 点灯: 接続。\n       | 消灯: 未接続。\n')
            for path in (declared, ordinary):
                path.write_text(rst, encoding='utf-8')
            cfg = {'build': {'languages': ['ja']}, 'pages': [
                {'type': 'csv_page', 'source': 'phase2', 'page': 'lcd_icons',
                 'langs': ['ja'], 'slot_id': 'status_legend'},
                {'type': 'rst_include', 'lang': 'ja', 'file': str(ordinary), 'slot_id': 'lcd_icons_ja'},
            ]}
            bundle = SimpleNamespace(
                bundle_dir=root, page_dir=pages, page_paths=(declared, ordinary),
                title='Manual', reference_doc=None, model='OTHER', region='JP', lang='ja', languages=('ja',),
            )
            with patch('tools.word_bundle_html.plan_materialized_pages', wraps=plan_materialized_pages) as planner:
                output, _, _ = build_word_bundle_html(
                    cfg, 'OTHER', 'JP', materialized_bundle=bundle,
                    output_dir=root / 'web', presentation_profile='web',
                )
                planner.assert_called_once()
            soup = BeautifulSoup(output.read_text(), 'html.parser')
            self.assertEqual(len(soup.select('figure.hb-lcd-table-composition')), 1)
            self.assertEqual(len(soup.select('table')), 2)
            self.assertEqual(len(soup.select('.hb-lcd-description .line')), 2)
            with patch('tools.word_bundle_html.plan_materialized_pages') as planner:
                output, _, _ = build_word_bundle_html(cfg, 'OTHER', 'JP', materialized_bundle=bundle, output_dir=root / 'doc')
                planner.assert_not_called()
            self.assertNotIn('hb-lcd-icon-table', output.read_text())

    def test_standalone_myst_uses_same_projection_and_rejects_extra_cells(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            staged = root / 'staged'
            staged.mkdir()
            (staged / '_static').mkdir()
            self.assertTrue(pms.stage_component_extension(staged))
            pms.write_conf_py(staged, title='LCD')
            source = '# Manual\n\n```{lcd-icons} 状態\n1 | ![Wireless](icon.png) | Wi-Fi | On: **Connected**. / Off: Disconnected.\n```\n'
            (staged / 'index.md').write_text(source)
            env = dict(os.environ)
            env.pop('PYTHONPATH', None)
            cmd = [sys.executable, '-I', '-m', 'sphinx', '-W', '-b', 'html', str(staged), str(root / 'html')]
            built = subprocess.run(cmd, cwd=root, env=env, text=True, capture_output=True)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            soup = BeautifulSoup((root / 'html/index.html').read_text(), 'html.parser')
            table = soup.select_one('figure.hb-lcd-table-composition')
            self.assertEqual(table['tabindex'], '0')
            self.assertEqual(table['aria-label'], '状態')
            self.assertEqual(len(table.select('col')), 4)
            self.assertEqual(len(table.select('.line')), 2)
            self.assertEqual(table.strong.text, 'Connected')
            (staged / 'index.md').write_text(source.replace('Disconnected.\n', 'Disconnected. | Extra\n'))
            bad = subprocess.run(cmd, cwd=root, env=env, text=True, capture_output=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn('requires four cells', bad.stdout + bad.stderr)


if __name__ == '__main__':
    unittest.main()
