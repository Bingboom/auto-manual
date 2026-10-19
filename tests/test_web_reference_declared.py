"""Explicit source figures reuse the existing reference component on cold replay."""
import html
import json
from pathlib import Path
import unittest
from bs4 import BeautifulSoup
from tools.component_specs.reference_figure_html import parse_declared_references
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import html_to_flow_nodes
from tools.web.embedded_components import render_embedded_web_component


class DeclaredReferenceTests(unittest.TestCase):
    def source(self):
        config = {'id': 'connection', 'web_replace_key': 'reference.connection',
                  'capture_following_lines': 3, 'presentation_mode': 'base-art-live-copy',
                  'base_art_layout': {'art_sha256': 'a' * 64, 'panel_top': 0,
                                      'panel_fill': '#ffffff', 'preserve_frame': True,
                                      'mobile_labels': 'overlay',
                                      'labels': [{'line': i, 'rect': [4 + i * 25, 3, 15, 4]}
                                                 for i in range(3)]}}
        return ('<img class="hb-source-reference" src="art.png" data-reference="'
                + html.escape(json.dumps(config), quote=True) + '"><div class="line-block">'
                + ''.join(f'<div class="line">Step {i}</div>' for i in range(1, 4)) + '</div>')

    def test_unknown_model_cold_replay_keeps_three_live_labels(self):
        soup = BeautifulSoup(self.source(), 'html.parser')
        spec, owned, _, _ = next(parse_declared_references(
            soup, source_path=Path('unlisted.rst'), language='en'))
        node = component_flow_node(spec, carrier_flow=html_to_flow_nodes(
            ''.join(str(tag) for tag in owned)))
        result = render_embedded_web_component(
            json.loads(json.dumps(node)), source_path=Path('missing.rst'), model='UNLISTED',
            region='US', language='en', composite_manifest=None, contract={})
        rendered = BeautifulSoup(result, 'html.parser')
        labels = rendered.select('.hb-reference-live-label')
        self.assertEqual([x.get_text() for x in labels], ['Step 1', 'Step 2', 'Step 3'])
        self.assertEqual(rendered.get_text().count('Step 1'), 1)
        self.assertIsNotNone(rendered.select_one('[data-mobile-labels="overlay"]'))

    def test_missing_label_rejected(self):
        soup = BeautifulSoup(self.source(), 'html.parser')
        soup.select('.line')[-1].decompose()
        with self.assertRaisesRegex(ValueError, 'expected 3'):
            list(parse_declared_references(soup, source_path=Path('x.rst'), language='en'))
