"""FCC declarations must bind across targets and cannot silently downgrade."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from urllib.parse import unquote, urlparse
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tests.test_web_fcc_ir import HTML
from tools.component_specs.fcc_declaration import declares_fcc
from tools.manual_ir.whole_document_components import discover_registered_components
from tools.web.document_source import load_web_document
from tools.web.presentation import WebPresentationError, load_web_manual_contract, transform_web_fragment


class FccContentContractTests(unittest.TestCase):
    def test_unknown_model_and_arbitrary_filename_use_shared_component(self):
        html = HTML.replace('<li>Second measure.</li>', '<li>Second measure.</li><li>Third.</li><li>Fourth.</li>')
        path = Path('/tmp/unknown-model/safety_copy.rst')
        contract = load_web_manual_contract(model='NEW-UNLISTED', region='US')
        claims = discover_registered_components(
            BeautifulSoup(html, 'html.parser'), source_path=path, contract=contract,
            model='NEW-UNLISTED', region='US', language='en',
        )
        self.assertEqual([x.spec.component_id for x in claims], ['HB-SPECIAL-FCC'])
        self.assertTrue(claims[0].asset_paths[0][1].is_file())
        output = transform_web_fragment(html, source_path=path, model='NEW-UNLISTED', region='US', language='en')
        soup = BeautifulSoup(output, 'html.parser')
        self.assertEqual(len(soup.select('[data-component-id="HB-SPECIAL-FCC"]')), 1)
        self.assertEqual(len(soup.select('.hb-fcc-column')), 2)
        self.assertEqual(len(soup.select('.hb-fcc-column-right li')), 4)
        self.assertEqual(len(soup.select('.hb-fcc-composition img')), 1)

    def test_incomplete_source_fails_instead_of_plain_text(self):
        for html in ('<h1>FCC</h1><p>Incomplete</p>', '<div class="hb-source-fcc">Incomplete</div>',
                     '<p>This device complies with part 15 of the FCC Rules.</p>'):
            with self.subTest(html=html), self.assertRaisesRegex(WebPresentationError, 'FCC'):
                transform_web_fragment(html, source_path=Path('renamed.rst'), model='NEW', region='US', language='en')

    def test_completed_ir_cannot_hide_missing_component(self):
        for resolved in (set(), {'HB-SPECIAL-FCC'}):
            with self.subTest(resolved=resolved), self.assertRaisesRegex(ValueError, 'refusing plain-text fallback'):
                transform_web_fragment(HTML, source_path=Path('renamed.rst'), model='NEW', region='US',
                                       language='en', embedded_components_complete=True,
                                       resolved_component_ids=resolved)

    def test_ordinary_fcc_mention_is_not_a_declaration(self):
        config = load_web_manual_contract()['fcc']
        self.assertFalse(declares_fcc(BeautifulSoup('<p>See the FCC website.</p>', 'html.parser'), Path('intro.rst'), config))

    def test_whole_document_rejects_dropped_claim(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            page = root / 'renamed.rst'
            page.write_text('FCC\n===\n\nIncomplete source\n')
            target = SimpleNamespace(model='NEW-UNLISTED', region='US', lang='en', languages=('en',),
                                     bundle_dir=root, title='Test')
            with patch('tools.web.document_source.discover_registered_components', return_value=()), self.assertRaisesRegex(ValueError, 'refusing plain-text fallback'):
                load_web_document(target, page_paths=(page,), declarations={}, page_languages={page.name: 'en'},
                                  active_tags={'html'}, output_dir=root / 'output', composite_manifest=None)

    def test_noop_renderer_is_rejected(self):
        with patch('tools.web.presentation.transform_fcc'), self.assertRaisesRegex(ValueError, 'refusing plain-text fallback'):
            transform_web_fragment(HTML, source_path=Path('renamed.rst'), model='NEW', region='US', language='en')

    def test_unknown_target_whole_document_cold_replay(self):
        from tools.manual_ir import read_manual_ir
        from tools.web.document_ir import render_document_fragments
        rst = ('FCC\n===\n\n.. line-block::\n\n   Opening one.\n   Opening two.\n\n'
               'NOTE: Tested copy. If this equipment does cause harmful interference, try:\n\n'
               '- First.\n- Second.\n- Third.\n- Fourth.\n\nMODIFICATION: Change copy.\n')
        with TemporaryDirectory() as td:
            root = Path(td)
            page = root / 'arbitrary.rst'
            page.write_text(rst)
            target = SimpleNamespace(model='UNLISTED-999', region='US', lang='en', languages=('en',),
                                     bundle_dir=root, title='Test')
            output = root / 'output'
            load_web_document(target, page_paths=(page,), declarations={}, page_languages={page.name: 'en'},
                              active_tags={'html'}, output_dir=output, composite_manifest=None)
            page.unlink()
            with patch('tools.manual_ir.whole_document_components.parse_fcc_html', side_effect=AssertionError('source re-read')):
                fragments = render_document_fragments(read_manual_ir(output / 'manual.ir.json'), package_root=output)
            soup = BeautifulSoup(''.join(fragments), 'html.parser')
            self.assertEqual(len(soup.select('[data-component-id="HB-SPECIAL-FCC"]')), 1)
            self.assertEqual(len(soup.select('.hb-fcc-column')), 2)
            self.assertEqual(len(soup.select('.hb-fcc-column-right li')), 4)
            mark = soup.select_one('.hb-fcc-composition img')
            mark_path = Path(unquote(urlparse(mark['src']).path))
            self.assertTrue(mark_path.is_relative_to(output.resolve()))
            self.assertTrue(mark_path.is_file())


class CompactFccStatementTests(unittest.TestCase):
    def test_distinct_statement_heading_preserves_compact_source(self):
        config = load_web_manual_contract()['fcc']
        for heading in ('FCC COMPLIANCE STATEMENT', 'Installation'):
            html = f'<h1>{heading}</h1><p>This device complies with Part 15 of the FCC Rules.</p>'
            self.assertFalse(declares_fcc(BeautifulSoup(html, 'html.parser'), Path('legal_tail.rst'), config))
            self.assertEqual(html, transform_web_fragment(html, source_path=Path('legal_tail.rst'), model='NEW', region='EU', language='en'))
