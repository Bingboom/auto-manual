"""Signal-word legend consumers validate IR before changing source tables."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools import web_symbol_components
from tools.manual_ir import build_manual_ir_from_source, read_manual_ir, validate_manual_ir, write_manual_ir
from tools.web_presentation import WebPresentationError, transform_web_fragment


TABLE = ('<table style="width:100%"><thead><tr><th>Signal</th><th>Meaning</th></tr></thead>'
         '<tbody><tr><td><span class="hb-warning-lockup"><span aria-hidden="true">!</span>'
         '<span>WARNING</span></span></td><td><p>Keep <strong>dry</strong>.</p>'
         '<ul><li><a href="https://example.com">Read first</a></li>'
         '<li><img src="warning.svg"/>Safe use</li></ul></td></tr>'
         '<tr><td><span class="hb-warning-lockup"><span>TIP</span></span></td>'
         '<td>Helpful copy.</td></tr></tbody></table>')
ORDINARY = '<table id="ordinary"><tr><td>Unrelated</td></tr></table>'


class WebSignalIRTests(unittest.TestCase):
    def test_real_rst_entrypoint_assembles_ir_in_three_languages(self) -> None:
        from tests.test_web_presentation import _web_fragment

        for language in ('en', 'fr', 'es'):
            with self.subTest(language=language), patch.object(
                web_symbol_components, 'build_manual_ir_from_source',
                wraps=build_manual_ir_from_source, create=True,
            ) as assembler:
                output = _web_fragment(f'symbols_{language}.rst')
                assembler.assert_called_once()
                source = assembler.call_args.args[0]
                self.assertEqual(source.metadata['projection'], 'web-symbol-signals')
                self.assertEqual((source.model, source.region, source.language), ('JE-1000F', 'US', language))
                self.assertEqual(len(BeautifulSoup(output, 'html.parser').select('.hb-signal-badge')), 4)

    def test_serialized_replay_preserves_rich_meanings_and_assets(self) -> None:
        from tools.manual_ir.web_symbols import load_web_signal_source
        from tools.web_symbol_components import render_signal_ir

        with TemporaryDirectory() as td:
            path = Path(td) / 'symbols.html'
            path.write_text(TABLE)
            source = load_web_signal_source(
                TABLE, source_path=path, expected_body_rows=2, language='ja', model='MODEL', region='JP',
            )
            ir = build_manual_ir_from_source(source)
            expected = render_signal_ir(ir)
            self.assertEqual((ir.model, ir.region, ir.language), ('MODEL', 'JP', 'ja'))
            self.assertEqual(ir.bundle_sha256, sha256(TABLE.encode()).hexdigest())
            self.assertEqual(ir.asset_refs, ('warning.svg',))
            self.assertIsNone(ir.snapshot_sha256)
            saved = write_manual_ir(ir, Path(td) / 'ir.json')
            path.unlink()
            output = render_signal_ir(read_manual_ir(saved))
            self.assertEqual(output, expected)
            self.assertIn('<p>Keep <strong>dry</strong>.</p>', output)
            self.assertIn('<a href="https://example.com">Read first</a>', output)
            self.assertIn('<li><img src="warning.svg"/>Safe use</li>', output)

    def test_actual_application_preserves_surrounding_tables_and_target_gate(self) -> None:
        print_table = TABLE.replace('<thead>', '\n<colgroup><col/></colgroup>\n<thead>')
        soup = BeautifulSoup('<h1>Symbols</h1>' + ORDINARY + print_table + '<p>After</p>', 'html.parser')
        web_symbol_components.transform_symbol_signal_table(
            soup, source_path=Path('symbols.html'), expected_body_rows=2,
            language='en', model='MODEL', region='US', error_type=WebPresentationError,
        )
        self.assertIn(ORDINARY, str(soup))
        self.assertIn('</colgroup>\n\n<thead>', str(soup))
        self.assertIn('<h1>Symbols</h1>', str(soup))
        self.assertIn('<p>After</p>', str(soup))
        self.assertEqual(len(soup.select('.hb-symbol-signal-composition')), 1)
        with patch.object(web_symbol_components, 'build_manual_ir_from_source') as assembler:
            result = transform_web_fragment(
                TABLE, source_path=Path('/tmp/docs/_review/OTHER/XX/page/symbols_en.rst'),
                model='OTHER', region='XX', language='en',
            )
            assembler.assert_not_called()
            self.assertNotIn('hb-symbol-signal-composition', result)

    def test_corrupt_envelope_fails_before_caller_mutation(self) -> None:
        def corrupt(source):
            return replace(build_manual_ir_from_source(source), content_sha256='0' * 64)

        soup = BeautifulSoup(TABLE, 'html.parser')
        before = str(soup)
        with patch.object(web_symbol_components, 'build_manual_ir_from_source', side_effect=corrupt):
            with self.assertRaisesRegex(WebPresentationError, 'Manual IR'):
                web_symbol_components.transform_symbol_signal_table(
                    soup, source_path=Path('symbols.html'), expected_body_rows=2, error_type=WebPresentationError,
                )
        self.assertEqual(str(soup), before)

    def test_rehashed_owned_payload_drift_is_rejected(self) -> None:
        from tools.manual_ir.web_symbols import load_web_signal_source
        from tools.web_symbol_components import render_signal_ir

        for change in ('labels', 'meanings', 'assets', 'count', 'kind', 'projection', 'extra'):
            with self.subTest(change=change):
                source = load_web_signal_source(TABLE, source_path=Path('symbols.html'), expected_body_rows=2)
                payload = source.pages[0].blocks[0][1]
                if change in ('labels', 'meanings'):
                    payload[change][0] = 'Different copy'
                elif change == 'assets':
                    payload['assets'] = []
                elif change == 'count':
                    payload['expected_body_rows'] = True
                elif change == 'projection':
                    source.metadata['projection'] = 'other'
                elif change == 'extra':
                    payload['ignored'] = 'Lost copy'
                page = replace(source.pages[0], blocks=((
                    'other' if change == 'kind' else 'web_signal_table', payload,
                ),))
                ir = build_manual_ir_from_source(replace(source, pages=(page,)))
                self.assertEqual(validate_manual_ir(ir), [])
                with self.assertRaises(ValueError):
                    render_signal_ir(ir)

    def test_malformed_last_label_and_geometry_leave_caller_unchanged(self) -> None:
        for html in (TABLE.replace('<span>TIP</span>', '<span>TIP</span><span>Extra</span>'),
                     TABLE.replace('<th>Signal', '<th colspan="2">Signal'),
                     TABLE.replace('</tbody>', '<tr></tr></tbody>'),
                     TABLE.replace('Helpful copy.', '<table><tr><td>Nested copy.</td></tr></table>'),
                     TABLE + TABLE):
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                before = str(soup)
                with self.assertRaises(WebPresentationError):
                    web_symbol_components.transform_symbol_signal_table(
                        soup, source_path=Path('symbols.html'), expected_body_rows=2, error_type=WebPresentationError,
                    )
                self.assertEqual(str(soup), before)
