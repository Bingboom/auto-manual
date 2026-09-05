"""Real symbol-pair rendering consumes public IR without changing its neighbor."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools.manual_ir import ManualIR, builder, build_manual_ir_from_source, read_manual_ir, validate_manual_ir, write_manual_ir
from tools.web_presentation import WebPresentationError, transform_web_fragment


def matrix():
    rows = ['<tr><th>Symbol</th><th>Meaning</th><th>Icon</th><th>Description</th></tr>']
    for index in range(6):
        meaning = (f'<p>Left <strong>{index}</strong></p>'
                   '<ul><li><a href="https://example.com">Read first</a></li></ul>')
        if index == 0:
            meaning += '<img src="detail.svg"/>'
        right = (f'<td><img src="right-{index}.svg"/></td><td>Right {index}</td>'
                 if index < 5 else '<td></td><td></td>')
        rows.append(f'<tr><td><img src="left-{index}.svg" width="30"/></td><td>{meaning}</td>{right}</tr>')
    return '<table>' + ''.join(rows) + '</table>'


class WebSymbolPairIRTests(unittest.TestCase):
    def test_real_rst_emits_pair_ir_in_three_languages(self) -> None:
        from tests.test_web_presentation import _web_fragment

        for language in ('en', 'fr', 'es'):
            with self.subTest(language=language), patch.object(builder, 'ManualIR', wraps=ManualIR) as emitted:
                output = _web_fragment(f'symbols_{language}.rst')
                pairs = [call.kwargs for call in emitted.call_args_list
                         if call.kwargs['metadata']['projection'] == 'web-symbol-pairs']
                self.assertEqual(len(pairs), 1, 'public assembler must emit the pair projection')
                self.assertEqual((pairs[0]['model'], pairs[0]['region'], pairs[0]['language']), ('JE-1000F', 'US', language))
                soup = BeautifulSoup(output, 'html.parser')
                self.assertEqual(len(soup.select('.hb-signal-badge')), 4)
                panels = soup.select('.hb-symbol-panel-table')
                self.assertEqual([len(panel.select('tbody > tr')) for panel in panels], [6, 5])

    def test_serialized_replay_preserves_order_rich_cells_and_assets(self) -> None:
        from tools.manual_ir.web_symbols import load_web_pair_source
        from tools.web_symbol_pairs import render_pair_ir

        html = matrix()
        with TemporaryDirectory() as td:
            path = Path(td) / 'matrix.html'
            path.write_text(html)
            ir = build_manual_ir_from_source(load_web_pair_source(
                html, source_path=path, language='ja', model='MODEL', region='JP',
            ))
            expected = render_pair_ir(ir)
            self.assertEqual(ir.bundle_sha256, sha256(html.encode()).hexdigest())
            self.assertIsNone(ir.snapshot_sha256)
            self.assertEqual((ir.model, ir.region, ir.language), ('MODEL', 'JP', 'ja'))
            self.assertEqual(set(ir.asset_refs), {'detail.svg', *(f'left-{i}.svg' for i in range(6)), *(f'right-{i}.svg' for i in range(5))})
            saved = write_manual_ir(ir, Path(td) / 'ir.json')
            path.unlink()
            output = render_pair_ir(read_manual_ir(saved))
            self.assertEqual(output, expected)
            soup = BeautifulSoup(output, 'html.parser')
            panels = soup.select('.hb-symbol-panel-table')
            self.assertEqual([image['src'] for image in panels[0].select('img.hb-symbol-art')], [f'left-{i}.svg' for i in range(6)])
            self.assertEqual([image['src'] for image in panels[1].select('img.hb-symbol-art')], [f'right-{i}.svg' for i in range(5)])
            self.assertIn('<p>Left <strong>0</strong></p>', output)
            self.assertIn('<a href="https://example.com">Read first</a>', output)
            self.assertIsNotNone(soup.select_one('img[src="detail.svg"]'))

    def test_application_keeps_other_content_and_target_gate(self) -> None:
        from tools import web_symbol_pairs

        ordinary = '<table id="ordinary"><tr><td>Other</td></tr></table>'
        soup = BeautifulSoup('<h1>Symbols</h1>' + ordinary + matrix() + '<p>After</p>', 'html.parser')
        web_symbol_pairs.transform_symbol_pairs(soup, source_path=Path('matrix.html'), error_type=WebPresentationError)
        self.assertIn(ordinary, str(soup))
        self.assertIn('<h1>Symbols</h1>', str(soup))
        self.assertIn('<p>After</p>', str(soup))
        with patch.object(web_symbol_pairs, 'build_manual_ir_from_source') as assembler:
            result = transform_web_fragment(matrix(), source_path=Path('/tmp/docs/_review/OTHER/XX/page/symbols_en.rst'))
            assembler.assert_not_called()
            self.assertNotIn('hb-symbol-pair-composition', result)

    def test_corrupt_envelope_leaves_caller_unchanged(self) -> None:
        from tools import web_symbol_pairs

        def corrupt(source):
            return replace(build_manual_ir_from_source(source), content_sha256='0' * 64)

        soup = BeautifulSoup(matrix(), 'html.parser')
        before = str(soup)
        with patch.object(web_symbol_pairs, 'build_manual_ir_from_source', side_effect=corrupt):
            with self.assertRaisesRegex(WebPresentationError, 'Manual IR'):
                web_symbol_pairs.transform_symbol_pairs(soup, source_path=Path('matrix.html'), error_type=WebPresentationError)
        self.assertEqual(str(soup), before)

    def test_rehashed_owned_payload_drift_is_rejected(self) -> None:
        from tools.manual_ir.web_symbols import load_web_pair_source
        from tools.web_symbol_pairs import render_pair_ir

        for change in ('meaning', 'icon', 'assets', 'kind', 'projection', 'extra'):
            with self.subTest(change=change):
                source = load_web_pair_source(matrix(), source_path=Path('matrix.html'))
                payload = source.pages[0].blocks[0][1]
                if change in ('meaning', 'icon'):
                    payload['panels'][0][0][change] = 'Different'
                elif change == 'assets':
                    payload['assets'] = []
                elif change == 'projection':
                    source.metadata['projection'] = 'other'
                elif change == 'extra':
                    payload['ignored'] = 'Lost content'
                page = replace(source.pages[0], blocks=(('other' if change == 'kind' else 'web_symbol_pairs', payload),))
                ir = build_manual_ir_from_source(replace(source, pages=(page,)))
                self.assertEqual(validate_manual_ir(ir), [])
                with self.assertRaises(ValueError):
                    render_pair_ir(ir)

    def test_invalid_geometry_assets_and_discarded_content_are_atomic(self) -> None:
        from tools.web_symbol_pairs import transform_symbol_pairs

        html = matrix()
        for malformed in (html + html, html.replace('<th>Symbol', '<th colspan="2">Symbol'),
                          html.replace('</table>', '<tr></tr></table>'),
                          html.replace('src="left-0.svg"', 'src=""'),
                          html.replace('<td></td><td></td>', '<td>Lost</td><td></td>'),
                          html.replace('src="left-0.svg"', 'src="left-0.svg"/><img src="extra.svg"'),
                          '<table><tr><td>' + html + '</td></tr></table>'):
            with self.subTest(html=malformed):
                soup = BeautifulSoup(malformed, 'html.parser')
                before = str(soup)
                with self.assertRaises(WebPresentationError):
                    transform_symbol_pairs(soup, source_path=Path('matrix.html'), error_type=WebPresentationError)
                self.assertEqual(str(soup), before)
