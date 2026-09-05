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
from tools.web_presentation import (
    WebPresentationError, load_web_manual_contract, transform_web_fragment,
)
from tools.word_bundle_html import _convert_rst_fragment_to_html, build_word_bundle_html


def source_table(*, declared: bool = True, head: bool = True) -> str:
    header = '<tr><td><em>Code</em></td><td>Source measures</td></tr>'
    rows = (
        '<tr><td>E42</td><td><p>Long corrective measure.</p>'
        '<ol><li>Disconnect <strong>all</strong> loads.</li>'
        '<li>Wait, then <a href="#support">contact support</a>.</li></ol></td></tr>'
        '<tr><td>A7</td><td><div class="line-block"><div class="line">First.</div>'
        '<div class="line">Check V<sub>oc</sub>.</div></div></td></tr>'
    )
    cls = ' class="hb-troubleshooting-table"' if declared else ''
    content = f'<thead>{header}</thead><tbody>{rows}</tbody>' if head else f'<tbody>{header}{rows}</tbody>'
    return f'<table{cls}>{content}</table>'


class WebTroubleshootingTests(unittest.TestCase):
    def test_declarations_ignore_target_filename_counts_and_figure_grants(self) -> None:
        contract = copy.deepcopy(load_web_manual_contract())
        contract['figure_targets'] = []
        contract.pop('troubleshooting_table')
        for head in (True, False):
            for declared_page in (True, False):
                with self.subTest(head=head, declared_page=declared_page):
                    source = source_table(declared=not declared_page, head=head)
                    result = transform_web_fragment(
                        source, source_path=Path('renamed/appendix.rst'), contract=contract,
                        model='ANOTHER-MODEL', region='JP', declared_troubleshooting=declared_page,
                    )
                    soup = BeautifulSoup(result, 'html.parser')
                    self.assertEqual(['E42', 'A7'], [x.text for x in soup.select('tbody .hb-troubleshooting-code')])
                    self.assertEqual(['col', 'col'], [x['scope'] for x in soup.select('thead th')])
                    self.assertEqual('0', soup.figure['tabindex'])
                    self.assertEqual('Code / Source measures', soup.figure['aria-label'])
                    self.assertEqual(
                        list(BeautifulSoup(source, 'html.parser').stripped_strings), list(soup.stripped_strings)
                    )
                    self.assertEqual(2, len(soup.select('li')))
                    self.assertEqual(2, len(soup.select('.line')))
                    self.assertEqual('#support', soup.a['href'])
                    self.assertEqual('oc', soup.sub.text)
                    self.assertEqual(result, transform_web_fragment(result, source_path=Path('renamed.rst')))

    def test_missing_declaration_keeps_even_legacy_named_page_unchanged(self) -> None:
        source = source_table(declared=False)
        for region in ('US', 'JP'):
            path = Path(f'docs/_build/JE-1000F/{region}/rst/page/troubleshooting_en.rst')
            self.assertEqual(source, transform_web_fragment(source, source_path=path))

    def test_bad_declared_geometry_and_missing_or_ambiguous_page_table_fail(self) -> None:
        for source in (
            '', '<p>No table.</p>', source_table() * 2,
            source_table().replace('<td>E42</td>', ''),
            source_table().replace('<td>E42</td>', '<td colspan="2">E42</td>'),
            source_table().replace('<td>E42</td>', '<td rowspan="2">E42</td>'),
            source_table().replace('<td>E42</td>', '<td></td>'),
            '<table><tbody><tr><td>Code</td><td>Measures</td></tr></tbody></table>',
            '<table><tbody></tbody></table>',
            source_table().replace('</tbody>', '</tbody><tbody></tbody>'),
        ):
            with self.subTest(source=source), self.assertRaisesRegex(WebPresentationError, 'renamed.rst.*troubleshooting'):
                transform_web_fragment(source, source_path=Path('renamed.rst'), declared_troubleshooting=True)
        with self.assertRaisesRegex(WebPresentationError, 'declaration must be on a table'):
            transform_web_fragment('<div class="hb-troubleshooting-table"></div>', source_path=Path('renamed.rst'))

    def test_mixed_page_preserves_ordinary_table_and_unapproved_art(self) -> None:
        ordinary = BeautifulSoup(source_table(declared=False), 'html.parser').table
        art = '<img src="unapproved.png" alt="Original art"/>'
        result = transform_web_fragment(
            art + str(ordinary) + source_table(),
            source_path=Path('docs/_build/JE-1000F/JP/rst/page/03_product_overview_placeholder.rst'),
        )
        soup = BeautifulSoup(result, 'html.parser')
        self.assertEqual(ordinary, soup.table)
        self.assertEqual(BeautifulSoup(art, 'html.parser').img, soup.img)
        self.assertEqual(1, len(soup.select('figure.hb-troubleshooting-composition')))
        self.assertFalse(soup.select('.hb-composite-art, .hb-annotated-figure'))

    def test_bundle_maps_csv_semantics_once_using_renamed_slot_identity(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            pages = root / 'page'
            pages.mkdir()
            declared = pages / 'renamed_appendix.rst'
            ordinary = pages / 'troubleshooting_ja.rst'
            rst = '.. list-table::\n   :header-rows: 0\n\n   * - コード\n     - 対処方法\n   * - E42\n     - 再起動。\n'
            declared.write_text(rst, encoding='utf-8')
            ordinary.write_text(rst, encoding='utf-8')
            cfg = {'build': {'languages': ['ja']}, 'pages': [
                {'type': 'csv_page', 'source': 'phase2', 'page': 'troubleshooting',
                 'langs': ['ja'], 'slot_id': 'renamed_appendix'},
                {'type': 'rst_include', 'lang': 'ja', 'file': str(ordinary),
                 'slot_id': 'troubleshooting_ja'},
            ]}
            bundle = SimpleNamespace(
                bundle_dir=root, page_dir=pages, page_paths=(declared, ordinary),
                title='Manual', reference_doc=None, model='OTHER', region='JP',
                lang='ja', languages=('ja',),
            )
            with patch('tools.word_bundle_html.plan_materialized_pages', wraps=plan_materialized_pages) as planner:
                output, _, _ = build_word_bundle_html(
                    cfg, 'OTHER', 'JP', materialized_bundle=bundle,
                    output_dir=root / 'web', presentation_profile='web',
                )
                planner.assert_called_once()
            soup = BeautifulSoup(output.read_text(), 'html.parser')
            self.assertEqual(1, len(soup.select('figure.hb-troubleshooting-composition')))
            self.assertEqual(2, len(soup.select('table')))
            self.assertFalse(soup.select('table')[1].find('thead'))
            with patch('tools.word_bundle_html.plan_materialized_pages') as planner:
                output, _, _ = build_word_bundle_html(
                    cfg, 'OTHER', 'JP', materialized_bundle=bundle,
                    output_dir=root / 'document',
                )
                planner.assert_not_called()
            self.assertNotIn('hb-troubleshooting-table', output.read_text())

    def test_isolated_staged_myst_and_rst_share_web_rules(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            staged = root / 'staged'
            staged.mkdir()
            (staged / '_static').mkdir()
            self.assertTrue(pms.stage_component_extension(staged))
            pms.write_conf_py(staged, title='Independent')
            (staged / 'index.md').write_text(
                '# Manual\n\n```{troubleshooting}\n:headers: コード | 対処方法\n\n'
                'E42 | 1. **Wait**. / 2. Check V~oc~.\nA7 | Restart.\n```\n', encoding='utf-8',
            )
            env = dict(os.environ)
            env.pop('PYTHONPATH', None)
            command = [sys.executable, '-I', '-m', 'sphinx', '-W', '-b', 'html', str(staged), str(root / 'html')]
            built = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True)
            self.assertEqual(0, built.returncode, built.stdout + built.stderr)
            markdown = BeautifulSoup((root / 'html/index.html').read_text(), 'html.parser').select_one('figure.hb-troubleshooting-composition')
            rst = _convert_rst_fragment_to_html(
                '.. list-table::\n   :header-rows: 0\n\n'
                '   * - コード\n     - 対処方法\n   * - E42\n'
                '     - | 1. **Wait**.\n       | 2. Check V\\ :sub:`oc`.\n'
                '   * - A7\n     - Restart.\n', Path('renamed.rst'), root / 'assets',
                presentation_profile='web', declared_troubleshooting=True,
            )
            rst_figure = BeautifulSoup(rst, 'html.parser').figure
            self.assertEqual(list(markdown.stripped_strings), list(rst_figure.stripped_strings))
            for selector in ('col', '.hb-troubleshooting-code', '.hb-troubleshooting-measures'):
                self.assertEqual(
                    [[c for c in x.get('class', []) if c.startswith('hb-')] for x in markdown.select(selector)],
                    [[c for c in x.get('class', []) if c.startswith('hb-')] for x in rst_figure.select(selector)],
                )
            self.assertEqual(['col', 'col'], [x['scope'] for x in markdown.select('thead th')])
            self.assertEqual(rst_figure['aria-label'], markdown['aria-label'])
            self.assertEqual('0', markdown['tabindex'])
            # The standalone extension must reject malformed declared rows too.
            (staged / 'index.md').write_text('# Bad\n\n```{troubleshooting}\nE42 | Fix | Extra\n```\n')
            bad = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True)
            self.assertNotEqual(0, bad.returncode)
            self.assertIn('requires two unspanned cells', bad.stdout + bad.stderr)


if __name__ == '__main__':
    unittest.main()
