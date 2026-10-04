"""Explicit QR download binding reuses the shared scan-sized component."""
from pathlib import Path
import unittest
from bs4 import BeautifulSoup
from tools.manual_ir.whole_document_components import _authored_claims
from tools.web.app_qr_component import render_qr_download


class DeclaredAppQrTests(unittest.TestCase):
    def test_arbitrary_source_binds_qr_variant(self):
        html = '<img class="hb-source-app-qr" src="qr.png" alt="App"><p>Scan to download.</p>'
        soup = BeautifulSoup(html, 'html.parser')
        claims = _authored_claims(soup, Path('new_product.rst'), 'en', set())
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].spec.variant, 'download-qr-only')
        output = BeautifulSoup(render_qr_download(claims[0].spec, html), 'html.parser')
        self.assertEqual(len(output.select('.hb-app-download-qr-only > .hb-app-download-art-qr')), 1)
        self.assertEqual(output.img['src'], 'qr.png')
        self.assertEqual(output.p.get_text(), 'Scan to download.')

    def test_missing_copy_is_rejected(self):
        soup = BeautifulSoup('<img class="hb-source-app-qr" src="qr.png">', 'html.parser')
        with self.assertRaisesRegex(ValueError, 'adjacent text-only copy'):
            _authored_claims(soup, Path('new_product.rst'), 'en', set())
