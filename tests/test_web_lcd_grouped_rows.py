"""Authored LCD grouping preserves semantic rows and opt-in layout."""
from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.manual_table_html import parse_lcd_icon_html
from tools.web.manual_table_components import render_manual_table_component


class LcdGroupedRowsTests(unittest.TestCase):
    def render(self, classes):
        rows = [(2, 'Input', 'Alternates.'), (2, 'Time', 'Alternates.'),
                (4, 'Wi-Fi', 'Connected.'), (4, 'Bluetooth', 'Paired.'),
                (5, 'Output', 'Paired.')]
        markup = '<table class="' + classes + '"><tbody>' + ''.join(
            f'<tr><td><p>{n}</p></td><td><img src="icon.png"></td>'
            f'<td>{name}</td><td>{desc}</td></tr>' for n, name, desc in rows
        ) + '</tbody></table>'
        spec, _, _ = parse_lcd_icon_html(
            BeautifulSoup(markup, 'html.parser'), source_path=Path('lcd.rst'),
            declared_page=True, language='en',
        )
        return BeautifulSoup(render_manual_table_component(spec), 'html.parser')

    def test_explicit_grouping_preserves_icons_and_distinct_meanings(self):
        soup = self.render('hb-lcd-merge-number hb-lcd-merge-description')
        self.assertEqual(len(soup.select('img')), 5)
        self.assertEqual([x.get('rowspan', '1') for x in soup.select('.hb-lcd-number')],
                         ['2', '2', '1'])
        self.assertEqual([x.get('rowspan', '1') for x in soup.select('.hb-lcd-description')],
                         ['2', '1', '1', '1'])
        self.assertEqual(len(soup.select('thead')), 0)

    def test_legacy_rows_are_not_implicitly_merged(self):
        soup = self.render('')
        self.assertEqual(len(soup.select('.hb-lcd-number')), 5)
        self.assertEqual(len(soup.select('.hb-lcd-description')), 5)
        self.assertEqual(len(soup.select('[rowspan]')), 0)
