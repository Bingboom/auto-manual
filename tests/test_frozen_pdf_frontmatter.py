"""Source structure survives native intake instead of flattening into prose."""
from copy import deepcopy
from pathlib import Path
import json
from types import SimpleNamespace
import unittest

from tools.web.frozen_ai_flow import flow_text, heading
from tools.web.frozen_ai_source import FrozenBook
from tools.web.frozen_pdf_frontmatter import preface_flow, safety_flow, template_heading_levels

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'manual_sources/JE-1000F/EU/nine-language/git-20260928-c38415f5-native-ir/four-language/source'


class FrozenPdfFrontmatterTests(unittest.TestCase):
    def test_four_prefaces_recover_source_label_and_four_paragraphs(self):
        for lang in ('uk', 'pt', 'nl', 'pl'):
            with self.subTest(language=lang):
                data = json.loads((SOURCE / f'{lang}.json').read_text())
                raw = data['front_back']['locales'][lang]['preface']['text']
                nodes = preface_flow(raw, lambda value: value)
                self.assertEqual(5, len(nodes))
                self.assertEqual('strong', nodes[0]['children'][0]['kind'])
                self.assertEqual(raw.splitlines()[-1], flow_text(nodes[0]))
                self.assertTrue(flow_text(nodes[-1]).startswith('*'))
                self.assertEqual(1, sum(flow_text(n).count('support.jackery.com') for n in nodes))
                self.assertFalse(any('— ' + lang in flow_text(n) for n in nodes))

    def test_four_safety_sections_keep_warning_eight_precautions_and_maintenance(self):
        for lang in ('uk', 'pt', 'nl', 'pl'):
            with self.subTest(language=lang):
                data = json.loads((SOURCE / f'{lang}.json').read_text())
                book = SimpleNamespace(**data, language=lang, correct=lambda value: value,
                                       assets={'symbol.general_warning': {'asset_ref': 'assets/warning.png'}})
                book.page = lambda number: next(p for p in book.source['pages'] if p['physical_page'] == number)
                book.starts = lambda: FrozenBook.starts(book)
                before = deepcopy(book.source)
                nodes = safety_flow(book)
                self.assertEqual('HB-CALLOUT-STRIP', nodes[0]['component_spec']['component_id'])
                label = nodes[0]['carrier_flow'][0]['children'][0]['children'][0]['children'][0]
                self.assertEqual('assets/warning.png', label['children'][1]['source'])
                self.assertEqual('strong', nodes[1]['children'][0]['kind'])
                self.assertEqual(8, len(nodes[2]['children']))
                self.assertEqual(3, len(nodes[2]['children'][6]['children']))
                self.assertEqual('heading', nodes[3]['kind'])
                self.assertEqual(before, book.source)
                self.assertEqual(1, template_heading_levels(nodes[3])['level'])

    def test_template_heading_projection_preserves_semantics_and_component_ownership(self):
        source = heading('Chapter', level=2, anchor='charging')
        projected = template_heading_levels(source)
        self.assertEqual(1, projected['level'])
        self.assertEqual(2, source['level'])
        self.assertEqual('charging', projected['anchor'])
        component = {'kind': 'component', 'carrier_flow': [source]}
        self.assertEqual(component, template_heading_levels(component))
