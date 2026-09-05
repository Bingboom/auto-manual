"""Real App control caller, replay integrity and atomic source application."""
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


def config():
    return {'add_device_paragraph_prefix': '2.1', 'button_terms': ['button', 'bouton', 'botón'], 'accessible_label': 'Fallback'}


def paragraph():
    return '<p id="add">2.1 Press the <strong>Add device</strong> button, <em>then</em> <a href="https://example.com">continue</a>.<img src="extra.svg"/></p>'


class WebAppControlIRTests(unittest.TestCase):
    def test_real_rst_caller_emits_control_ir_for_three_locales(self):
        from tests.test_web_presentation import _web_fragment

        for name in ('12_app_setup_placeholder.rst', 'p34_12_app_setup_placeholder.rst', 'p50_12_app_setup_placeholder.rst'):
            with self.subTest(name=name), patch.object(builder, 'ManualIR', wraps=ManualIR) as emitted:
                output = _web_fragment(name)
                controls = [c.kwargs for c in emitted.call_args_list
                            if c.kwargs['metadata']['projection'] == 'web-app-control']
                self.assertEqual(len(controls), 1, 'actual App control caller must emit public IR')
                self.assertEqual((controls[0]['model'], controls[0]['region']), ('JE-1000F', 'US'))
                self.assertEqual(len(BeautifulSoup(output, 'html.parser').select('.hb-inline-add-device-icon')), 1)
                self.assertEqual(sum(c.kwargs['metadata']['projection'] == 'web-app-download' for c in emitted.call_args_list), 1)

    def test_serialized_replay_preserves_language_label_rich_copy_and_assets(self):
        from tools.manual_ir.web_app_controls import load_web_control_source
        from tools.web_app_controls import render_control_ir

        for language, term, label in (('en', 'button', 'Add device'), ('fr', 'bouton', 'Ajouter'), ('es', 'botón', 'Añadir')):
            with self.subTest(language=language), TemporaryDirectory() as td:
                html = paragraph().replace('button', term).replace('Add device', label)
                path = Path(td) / 'page.html'
                path.write_text(html)
                settings = config()
                ir = build_manual_ir_from_source(load_web_control_source(html, source_path=path, config=settings, language=language, model='MODEL', region='EU'))
                self.assertEqual((ir.model, ir.region, ir.language), ('MODEL', 'EU', language))
                self.assertEqual(ir.bundle_sha256, sha256(html.encode()).hexdigest())
                self.assertEqual(ir.asset_refs, ('extra.svg',))
                expected = render_control_ir(ir)
                saved = write_manual_ir(ir, Path(td) / 'ir.json')
                path.unlink()
                settings.clear()
                self.assertEqual(render_control_ir(read_manual_ir(saved)), expected)
                soup = BeautifulSoup(expected, 'html.parser')
                self.assertEqual(soup.span['aria-label'], label)
                self.assertEqual(soup.span.get_text(), '+')
                self.assertEqual(soup.span['role'], 'img')
                self.assertEqual(soup.p['id'], 'add')
                self.assertIn('<em>then</em>', expected)
                self.assertIn('<a href="https://example.com">continue</a>', expected)
                self.assertIsNotNone(soup.select_one('img[src="extra.svg"]'))
                self.assertIsNone(soup.strong)

    def test_application_preserves_other_paragraphs_and_target_gate(self):
        from tools import web_app_controls

        html = '<h2>Title</h2><p>Before</p>' + paragraph() + '<p>After</p>'
        soup = BeautifulSoup(html, 'html.parser')
        web_app_controls.transform_app_control(soup, source_path=Path('app.html'), config=config(), error_type=WebPresentationError)
        self.assertIn('<h2>Title</h2><p>Before</p>', str(soup))
        self.assertIn('<p>After</p>', str(soup))
        with patch.object(web_app_controls, 'build_manual_ir_from_source') as assembler:
            output = transform_web_fragment(html, source_path=Path('/tmp/docs/_review/OTHER/XX/page/12_app_setup_placeholder.rst'))
            assembler.assert_not_called()
            self.assertNotIn('hb-inline-add-device-icon', output)

    def test_malformed_input_does_not_mutate_caller(self):
        from tools.web_app_controls import transform_app_control

        html = paragraph()
        for malformed in (html+html, html.replace('2.1', '2.2'), html.replace('button', 'thing'),
                          html.replace('Add device', ''), html.replace('<strong>', '<b>').replace('</strong>', '</b>'),
                          html.replace('</strong>', '</strong><strong>Duplicate</strong>'),
                          html.replace('Add device', 'Add <img src="lost.svg"/>'),
                          html.replace('src="extra.svg"', 'src=""')):
            with self.subTest(html=malformed):
                soup = BeautifulSoup(malformed, 'html.parser')
                before = str(soup)
                with self.assertRaises(WebPresentationError):
                    transform_app_control(soup, source_path=Path('app.html'), config=config(), error_type=WebPresentationError)
                self.assertEqual(str(soup), before)

    def test_corrupt_envelope_does_not_mutate_caller(self):
        from tools import web_app_controls

        def corrupt(source):
            return replace(build_manual_ir_from_source(source), content_sha256='0'*64)

        soup = BeautifulSoup(paragraph(), 'html.parser')
        before = str(soup)
        with patch.object(web_app_controls, 'build_manual_ir_from_source', side_effect=corrupt):
            with self.assertRaisesRegex(WebPresentationError, 'Manual IR'):
                web_app_controls.transform_app_control(soup, source_path=Path('app.html'), config=config(), error_type=WebPresentationError)
        self.assertEqual(str(soup), before)

    def test_rehashed_owned_payload_drift_is_rejected(self):
        from tools.manual_ir.web_app_controls import load_web_control_source
        from tools.web_app_controls import render_control_ir

        for change in ('label', 'assets', 'extra', 'paragraph', 'projection', 'kind'):
            with self.subTest(change=change):
                source = load_web_control_source(paragraph(), source_path=Path('app.html'), config=config())
                payload = source.pages[0].blocks[0][1]
                if change == 'label':
                    payload['label'] = 'Drift'
                elif change == 'assets':
                    payload['assets'] = []
                elif change == 'extra':
                    payload['ignored'] = 'Lost'
                elif change == 'paragraph':
                    payload['paragraph_html'] += '<p>Lost</p>'
                elif change == 'projection':
                    source.metadata['projection'] = 'other'
                page = replace(source.pages[0], blocks=(('other' if change == 'kind' else 'web_app_control', payload),))
                ir = build_manual_ir_from_source(replace(source, pages=(page,)))
                self.assertEqual(validate_manual_ir(ir), [])
                with self.assertRaises(ValueError):
                    render_control_ir(ir)
