"""Authored downloads retain both native copy columns on unlisted targets."""
import json
from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import html_to_flow_nodes
from tools.manual_ir.whole_document_components import _authored_claims
from tools.web.embedded_components import render_embedded_web_component


class DeclaredAppDownloadTests(unittest.TestCase):
    def source(self):
        return (
            '<h1>Application</h1><section><h2>Télécharger et se connecter</h2>'
            '<img class="hb-source-app-download" src="native-qr.png" '
            'data-app-download=\'{"artwork":{"store":"badges.png","qr":"native-qr.png"}}\'>'
            '<p>Recherchez <strong>Jackery</strong> dans les boutiques.</p>'
            '<p>Scannez le code QR.</p><aside>Keep this neighbor.</aside></section>'
        )

    def test_unlisted_target_cold_replay_keeps_native_columns_and_artwork(self):
        soup = BeautifulSoup(self.source(), 'html.parser')
        claims = _authored_claims(soup, Path('unlisted.rst'), 'fr', set())
        self.assertEqual(len(claims), 1)
        claim = claims[0]
        self.assertEqual(claim.spec.variant, 'download')
        carrier = ''.join(str(node) for node in claim.owned_nodes)
        self.assertNotIn('Keep this neighbor.', carrier)
        node = component_flow_node(claim.spec, carrier_flow=html_to_flow_nodes(carrier))
        output = render_embedded_web_component(
            json.loads(json.dumps(node)), source_path=Path('missing.rst'),
            model='UNLISTED', region='US', language='fr',
            composite_manifest=None, contract={},
        )
        result = BeautifulSoup(output, 'html.parser')
        columns = result.select('.hb-app-download-column')
        self.assertEqual(len(columns), 2)
        self.assertEqual([c.img['src'] for c in columns], ['badges.png', 'native-qr.png'])
        self.assertEqual([c.get_text(' ', strip=True) for c in columns],
                         ['Recherchez Jackery dans les boutiques.', 'Scannez le code QR.'])
        self.assertIsNotNone(columns[0].strong)

    def test_incomplete_artwork_binding_cannot_fall_back_to_qr_only(self):
        soup = BeautifulSoup(self.source().replace(',"qr":"native-qr.png"', ''), 'html.parser')
        with self.assertRaisesRegex(ValueError, 'store and QR artwork'):
            _authored_claims(soup, Path('unlisted.rst'), 'fr', set())

    def test_missing_native_column_is_rejected(self):
        soup = BeautifulSoup(self.source().replace('<p>Scannez le code QR.</p>', ''), 'html.parser')
        with self.assertRaisesRegex(ValueError, 'two column copies'):
            _authored_claims(soup, Path('unlisted.rst'), 'fr', set())
