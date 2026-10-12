"""Explicit LCD mode carriers work independently of legacy chapter names."""
from pathlib import Path
import unittest
from bs4 import BeautifulSoup
from tools.manual_ir.whole_document_components import _authored_claims
from tools.web.lcd_mode_component import render_lcd_mode_component


class DeclaredLcdModeTests(unittest.TestCase):
    def markup(self):
        rows = []
        for i in range(6):
            cells = '<td rowspan="6"><img src="device.png" alt="Device"></td>' if i == 0 else ''
            if i in (0, 3):
                cells += '<td rowspan="3">Mode</td>'
            rows.append('<tr>' + cells + '<td>Action</td><td>Instruction</td></tr>')
        return '<table class="hb-source-lcd-mode hb-lcd-mode-portrait"><tbody>' + ''.join(rows) + '</tbody></table>'

    def test_unknown_source_uses_shared_component(self):
        soup = BeautifulSoup(self.markup(), 'html.parser')
        claims = _authored_claims(soup, Path('unknown_manual.rst'), 'en', set())
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].spec.component_id, 'HB-TABLE-LCD-MODE')
        result = BeautifulSoup(render_lcd_mode_component(claims[0].spec), 'html.parser')
        self.assertEqual(len(result.select('.hb-lcd-mode-portrait')), 1)
        self.assertEqual(len(result.select('td[rowspan="3"]')), 2)
        self.assertEqual(len(result.select('tbody tr')), 6)
        self.assertEqual(len(result.select('thead')), 0)

    def test_missing_artwork_fails(self):
        soup = BeautifulSoup(self.markup(), 'html.parser')
        soup.img.decompose()
        with self.assertRaisesRegex(ValueError, 'exactly one artwork'):
            _authored_claims(soup, Path('unknown_manual.rst'), 'en', set())
