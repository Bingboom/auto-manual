"""App download uses public IR while keeping its two live copy columns."""
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
    return {"image_key": "app/download", "artwork": {"store": "store.png", "qr": "qr.png"}}


def source(split=False):
    copies = '<p>Install <strong>App</strong> <a href="https://example.com">here</a><img src="extra.svg"/></p><p>Scan QR</p>'
    if split:
        copies = copies.replace('</p><p>', '\n')
    return ('<h1>App</h1><section id="download"><h2>Download &amp; login</h2>'
            '<img src="asset:app/download" alt="Stores" width="320"/>' + copies
            + '<aside>Keep me</aside></section><section><p>After</p></section>')


class WebAppDownloadIRTests(unittest.TestCase):
    def test_real_rst_emits_download_ir_in_three_languages(self):
        from tests.test_web_presentation import _web_fragment

        for name in ('12_app_setup_placeholder.rst', 'p34_12_app_setup_placeholder.rst', 'p50_12_app_setup_placeholder.rst'):
            with self.subTest(name=name), patch.object(builder, 'ManualIR', wraps=ManualIR) as emitted:
                output = _web_fragment(name)
                downloads = [c.kwargs for c in emitted.call_args_list
                             if c.kwargs['metadata']['projection'] == 'web-app-download']
                self.assertEqual(len(downloads), 1, 'actual caller must emit public App download IR')
                self.assertEqual((downloads[0]['model'], downloads[0]['region']), ('JE-1000F', 'US'))
                soup = BeautifulSoup(output, 'html.parser')
                self.assertEqual(len(soup.select('.hb-app-download-column')), 2)
                self.assertEqual(len(soup.select('.hb-app-download-semantic-art')), 1)

    def test_replay_needs_neither_source_nor_config_and_preserves_rich_copy(self):
        from tools.manual_ir.web_app_download import load_web_download_source
        from tools.web_app_download import render_download_ir

        for split in (False, True):
            with self.subTest(split=split), TemporaryDirectory() as td:
                path = Path(td) / 'app.html'
                html = source(split)
                path.write_text(html)
                settings = config()
                ir = build_manual_ir_from_source(load_web_download_source(
                    html, source_path=path, config=settings, language='fr', model='MODEL', region='EU',
                ))
                expected = render_download_ir(ir)
                self.assertEqual((ir.model, ir.region, ir.language), ('MODEL', 'EU', 'fr'))
                self.assertEqual(ir.bundle_sha256, sha256(html.encode()).hexdigest())
                self.assertEqual(set(ir.asset_refs), {'asset:app/download', 'store.png', 'qr.png', 'extra.svg'})
                saved = write_manual_ir(ir, Path(td) / 'ir.json')
                path.unlink()
                settings['artwork'].clear()
                self.assertEqual(render_download_ir(ir), expected)
                self.assertEqual(render_download_ir(read_manual_ir(saved)), expected)
                self.assertIn('<strong>App</strong>', expected)
                self.assertIn('<a href="https://example.com">here</a>', expected)
                self.assertIn('width="320"', expected)
                self.assertLess(expected.index('hb-app-download-column-store'), expected.index('hb-app-download-column-qr'))

    def test_application_preserves_neighbors_and_target_gate(self):
        from tools import web_app_download

        soup = BeautifulSoup(source(), 'html.parser')
        web_app_download.transform_app_download(soup, source_path=Path('app.html'), config=config(), error_type=WebPresentationError)
        self.assertIn('<h2>Download &amp; login</h2>', str(soup))
        self.assertIn('<aside>Keep me</aside>', str(soup))
        self.assertIn('<section><p>After</p></section>', str(soup))
        self.assertFalse(soup.select_one('#download').find_all('p', recursive=False))
        with patch.object(web_app_download, 'build_manual_ir_from_source') as assembler:
            output = transform_web_fragment(source(), source_path=Path('/tmp/docs/_review/OTHER/XX/page/12_app_setup_placeholder.rst'))
            assembler.assert_not_called()
            self.assertNotIn('hb-app-download-composition', output)

    def test_invalid_inputs_do_not_change_caller(self):
        from tools.web_app_download import transform_app_download

        html = source()
        for malformed in (html.replace('<h2>', '<h3>').replace('</h2>', '</h3>'),
                          html.replace('<h2>', '<h2>Duplicate</h2><h2>'),
                          html + html, html.replace('<p>Scan QR</p>', ''),
                          html.replace('Scan QR', ''), html.replace('<aside>', '<p>Third copy</p><aside>'),
                          html.replace('<img src="asset:app/download" alt="Stores" width="320"/>', ''),
                          html.replace('<img src="asset:app/download" alt="Stores" width="320"/>', '<p><img src="asset:app/download"/></p>'),
                          html.replace('src="extra.svg"', 'src=""')):
            with self.subTest(html=malformed):
                soup = BeautifulSoup(malformed, 'html.parser')
                before = str(soup)
                with self.assertRaises(WebPresentationError):
                    transform_app_download(soup, source_path=Path('app.html'), config=config(), error_type=WebPresentationError)
                self.assertEqual(str(soup), before)

    def test_corrupt_envelope_is_atomic(self):
        from tools import web_app_download

        def corrupt(source):
            return replace(build_manual_ir_from_source(source), content_sha256='0' * 64)

        soup = BeautifulSoup(source(), 'html.parser')
        before = str(soup)
        with patch.object(web_app_download, 'build_manual_ir_from_source', side_effect=corrupt):
            with self.assertRaisesRegex(WebPresentationError, 'Manual IR'):
                web_app_download.transform_app_download(soup, source_path=Path('app.html'), config=config(), error_type=WebPresentationError)
        self.assertEqual(str(soup), before)

    def test_rehashed_owned_payload_drift_is_rejected(self):
        from tools.manual_ir.web_app_download import load_web_download_source
        from tools.web_app_download import render_download_ir

        for change in ('text', 'order', 'assets', 'extra', 'kind', 'projection', 'binding', 'image'):
            with self.subTest(change=change):
                parsed = load_web_download_source(source(), source_path=Path('app.html'), config=config())
                payload = parsed.pages[0].blocks[0][1]
                if change == 'text':
                    payload['columns'][0]['text'] = 'Drift'
                elif change == 'order':
                    payload['columns'].reverse()
                elif change == 'assets':
                    payload['assets'] = []
                elif change == 'extra':
                    payload['ignored'] = 'Lost'
                elif change == 'projection':
                    parsed.metadata['projection'] = 'other'
                elif change == 'binding':
                    payload['artwork']['qr'] = ''
                elif change == 'image':
                    payload['semantic_image_html'] += '<p>Lost</p>'
                page = replace(parsed.pages[0], blocks=(('other' if change == 'kind' else 'web_app_download', payload),))
                ir = build_manual_ir_from_source(replace(parsed, pages=(page,)))
                self.assertEqual(validate_manual_ir(ir), [])
                with self.assertRaises(ValueError):
                    render_download_ir(ir)
