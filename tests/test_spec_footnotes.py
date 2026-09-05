from __future__ import annotations

import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.csv_pages import renderers_spec_parser as csv_spec
from tools.idml import loaders
from tools.utils import spec_footnotes


class SpecFootnoteTests(unittest.TestCase):
    def test_marker_order_preserves_truncation_and_boundary_policy(self) -> None:
        for order, expected in ((-1, ''), (0, ''), (0.9, ''), (1, '①'), (1.9, '①'),
                                (10, '⑩'), (10.9, '⑩'), (11, '(11)'), (30, '(30)')):
            with self.subTest(order=order):
                self.assertEqual(spec_footnotes.footnote_marker_for_order(order), expected)

    def test_reference_order_missing_ids_and_empty_copy_are_preserved(self) -> None:
        refs = spec_footnotes.parse_footnote_refs(' second,first,second, ,unknown,First ')
        self.assertEqual(refs, ['second', 'first', 'unknown', 'First'])
        markers = {'first': '①', 'second': '②', 'First': '(11)'}
        self.assertEqual(spec_footnotes.append_footnote_markers('value', refs, markers), 'value②①(11)')
        self.assertEqual(spec_footnotes.append_footnote_markers('', refs, markers), '')
        self.assertEqual(spec_footnotes.append_footnote_markers(' ', refs, markers), ' ②①(11)')
        self.assertEqual(spec_footnotes.append_footnote_markers('value', ['unknown'], markers), 'value')
        self.assertEqual(spec_footnotes.parse_footnote_refs(''), [])
        self.assertEqual(spec_footnotes.parse_footnote_refs('a;b'), ['a;b'])

    def test_both_real_readers_use_the_shared_rules(self) -> None:
        for caller in (loaders, csv_spec):
            for name in ('footnote_marker_for_order', 'parse_footnote_refs', 'append_footnote_markers'):
                self.assertIs(getattr(caller, '_' + name), getattr(spec_footnotes, name))
        common = {'Model': 'DEMO', 'Region': 'US', 'Enabled': 'TRUE', 'Is_Latest': 'TRUE'}
        row = {**common, 'document_key': 'DEMO_US', 'Page': 'specifications',
               'Section': 'GENERAL', 'Row_key': 'output', 'Row_order': '1', 'Line_order': '1',
               'Row_label_source': 'Output', 'Row_label_en': 'Output', 'Value_source': '100 W',
               'Value_en': '100 W', 'Value_footnote_refs': 'b,a,b,missing'}
        footnotes = [{**common, 'Page': 'specifications', 'Footnote_id': key,
                      'Footnote_order': str(order), 'footnote_text_en': 'Footnote '+key}
                     for key, order in [('a', 1), ('b', 2)]]
        with TemporaryDirectory() as td:
            root = Path(td)
            for name, rows in [('Spec_Master.csv', [row]), ('Spec_Footnotes.csv', footnotes)]:
                with (root / name).open('w', encoding='utf-8', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
            with patch.object(loaders, '_append_footnote_markers', wraps=spec_footnotes.append_footnote_markers) as called:
                result = loaders.load_spec_sections(root, 'DEMO', 'US')
                self.assertIn('100 W②①', str(result))
                self.assertGreater(called.call_count, 0)
            with patch.object(csv_spec, '_append_footnote_markers', wraps=spec_footnotes.append_footnote_markers) as called:
                result = csv_spec.collect_spec_content([row, *footnotes], '', 'en', {'model': 'DEMO', 'region': 'US'})
                self.assertIn('100 W②①', str(result))
                self.assertGreater(called.call_count, 0)


if __name__ == '__main__':
    unittest.main()
