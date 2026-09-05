"""FCC public IR is consumed by the real Web path and replays without parsing."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools import web_fcc_component
from tools.manual_ir import build_manual_ir_from_source, read_manual_ir, validate_manual_ir, write_manual_ir
from tools.web_presentation import WebPresentationError, load_web_manual_contract, transform_web_fragment


HTML = ('<p id="before">Before</p><h1>FCC</h1>'
        '<div class="line-block"><div class="line">Opening one.</div>'
        '<div class="line">Opening two.</div></div>'
        '<p>NOTE: Tested copy. If this equipment does cause harmful interference, try:</p>'
        '<ul><li>First measure.</li><li>Second measure.</li></ul>'
        '<p>MODIFICATION: Change copy.</p>')


def config():
    return deepcopy(load_web_manual_contract()['fcc'])


class WebFccIRTests(unittest.TestCase):
    def test_real_rst_entrypoint_assembles_ir_for_three_locales(self) -> None:
        from tests.test_web_presentation import _web_fragment

        for name, language in (('01_fcc.rst', 'en'), ('p22_01_fcc.rst', 'fr'), ('p38_01_fcc.rst', 'es')):
            with self.subTest(name=name), patch.object(
                web_fcc_component, 'build_manual_ir_from_source',
                wraps=build_manual_ir_from_source, create=True,
            ) as assembler:
                output = _web_fragment(name)
                assembler.assert_called_once()
                source = assembler.call_args.args[0]
                self.assertEqual(source.metadata['projection'], 'web-fcc')
                self.assertEqual((source.model, source.region, source.language), ('JE-1000F', 'US', language))
                soup = BeautifulSoup(output, 'html.parser')
                self.assertEqual(len(soup.select('.hb-fcc-column')), 2)
                self.assertEqual(len(soup.select('.hb-fcc-column-right li')), 4)

    def test_serialized_replay_reads_no_source_or_parser_config(self) -> None:
        from tools.manual_ir import web_fcc
        from tools.web_fcc_component import render_fcc_ir

        with TemporaryDirectory() as td:
            source_path = Path(td) / '01_fcc.rst'
            source_path.write_text(HTML)
            settings = config()
            source = web_fcc.load_web_fcc_source(
                HTML, source_path=source_path, config=settings, language='en', model='MODEL', region='US',
            )
            ir = build_manual_ir_from_source(source)
            expected = render_fcc_ir(ir)
            self.assertEqual(ir.bundle_sha256, sha256(HTML.encode()).hexdigest())
            self.assertIsNone(ir.snapshot_sha256)
            self.assertEqual(set(ir.asset_refs), {settings['mark_asset_ref'], settings['mark_path']})
            saved = write_manual_ir(ir, Path(td) / 'ir.json')
            settings.clear()
            source_path.unlink()
            with patch.object(web_fcc, 'parse_fcc_html', side_effect=AssertionError('source re-read')):
                self.assertEqual(render_fcc_ir(read_manual_ir(saved)), expected)
                # A legitimate edited semantic slot drives output: no hidden HTML snapshot wins.
                source.pages[0].blocks[0][1]['component_spec']['slots'][1]['content'][0] = 'Revised opening.'
                revised = render_fcc_ir(build_manual_ir_from_source(source))
                self.assertIn('Revised opening.', revised)
                self.assertNotIn('Opening one.', revised)

    def test_source_config_identity_and_explicit_language_are_preserved(self) -> None:
        from tools.manual_ir.web_fcc import load_web_fcc_source

        settings = config()
        source = load_web_fcc_source(HTML, source_path=Path('renamed.rst'), config=settings, language='en')
        changed = deepcopy(settings)
        changed['mark_path'] = 'other-mark.png'
        other = load_web_fcc_source(HTML, source_path=Path('renamed.rst'), config=changed, language='en')
        self.assertEqual(source.language, 'en')
        self.assertNotEqual(source.style_contract_sha256, other.style_contract_sha256)

    def test_corruption_does_not_mutate_caller_and_target_gate_stays_closed(self) -> None:
        def corrupt(source):
            return replace(build_manual_ir_from_source(source), content_sha256='0' * 64)

        soup = BeautifulSoup(HTML, 'html.parser')
        original = str(soup)
        with patch.object(web_fcc_component, 'build_manual_ir_from_source', side_effect=corrupt):
            with self.assertRaisesRegex(WebPresentationError, 'Manual IR'):
                web_fcc_component.transform_fcc(
                    soup, source_path=Path('01_fcc.rst'), config=config(), language='en',
                    error_type=WebPresentationError,
                )
        self.assertEqual(str(soup), original)
        with patch.object(web_fcc_component, 'build_manual_ir_from_source') as assembler:
            output = transform_web_fragment(
                HTML, source_path=Path('/tmp/docs/_review/OTHER/XX/page/01_fcc.rst'),
                model='OTHER', region='XX', language='en',
            )
            assembler.assert_not_called()
            self.assertNotIn('hb-fcc-composition', output)

    def test_invalid_rehashed_owned_payload_is_rejected(self) -> None:
        from tools.manual_ir.web_fcc import load_web_fcc_source
        from tools.web_fcc_component import render_fcc_ir

        for change in ('column', 'binding', 'source', 'language', 'extra', 'kind', 'projection', 'hidden-slot'):
            with self.subTest(change=change):
                source = load_web_fcc_source(HTML, source_path=Path('01_fcc.rst'), config=config(), language='en')
                payload = source.pages[0].blocks[0][1]
                spec = payload['component_spec']
                if change == 'column':
                    spec['slots'][-1]['content'] = 999
                elif change == 'binding':
                    payload['mark_binding']['asset_ref'] = 'wrong-mark'
                elif change == 'source':
                    spec['source_ref'] = 'other.rst'
                elif change == 'language':
                    spec['language'] = 'fr'
                elif change == 'extra':
                    payload['ignored'] = 'Lost text'
                elif change == 'hidden-slot':
                    spec['slots'][0]['unexpected'] = 'Lost text'
                elif change == 'projection':
                    source.metadata['projection'] = 'other'
                page = replace(source.pages[0], blocks=(('other' if change == 'kind' else 'web_fcc', payload),))
                ir = build_manual_ir_from_source(replace(source, pages=(page,)))
                self.assertEqual(validate_manual_ir(ir), [])
                with self.assertRaises(ValueError):
                    render_fcc_ir(ir)

    def test_malformed_source_fails_before_dom_changes(self) -> None:
        for html in (HTML.replace('<h1>FCC</h1>', '<h2>FCC</h2>'),
                     HTML.replace('<p>MODIFICATION: Change copy.</p>', ''),
                     HTML.replace('<li>First measure.</li><li>Second measure.</li>', '')):
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                before = str(soup)
                with self.assertRaises(WebPresentationError):
                    web_fcc_component.transform_fcc(
                        soup, source_path=Path('01_fcc.rst'), config=config(), language='en',
                        error_type=WebPresentationError,
                    )
                self.assertEqual(str(soup), before)
