"""Declared live operation panels survive IR replay without model admission."""
import html
import json
from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.operation_html import parse_declared_operations
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import html_to_flow_nodes
from tools.web.embedded_components import render_embedded_web_component


class DeclaredOperationTests(unittest.TestCase):
    def source(self):
        config = {
            'id': 'main-power', 'layout': 'status-right',
            'step_ids': ['on', 'off'], 'capture_following_lines': 2,
            'presentation_mode': 'base-art-live-copy',
            'steps_rect': [76, 17, 22, 33],
            'base_art_layout': {'art_sha256': 'a' * 64,
                                'step_anchors': [[76, 21], [76, 34]],
                                'step_width': 22, 'supporting_anchor': [43, 57, 52]},
        }
        return ('<img class="hb-source-operation" src="art.png" data-operation="'
                + html.escape(json.dumps(config), quote=True) + '">'
                '<div class="line-block"><div class="line">On: Press once</div>'
                '<div class="line">Off: Press and hold for 3s</div>'
                '<div class="line"><strong>Default standby time:</strong> 12 hours</div>'
                '<div class="line">App note.</div></div>')

    def test_cold_replay_preserves_live_copy_and_two_css_panels(self):
        soup = BeautifulSoup(self.source(), 'html.parser')
        spec, owned, _, discarded = next(parse_declared_operations(
            soup, source_path=Path('unlisted.rst'), language='en'))
        for tag in discarded:
            tag.extract()
        node = component_flow_node(spec, carrier_flow=html_to_flow_nodes(
            ''.join(str(tag) for tag in owned)))
        node = json.loads(json.dumps(node))
        result = render_embedded_web_component(
            node, source_path=Path('missing.rst'), model='UNLISTED', region='US',
            language='en', composite_manifest=None,
            contract={'figure_targets': [], 'operations': {'figures': []}},
        )
        rendered = BeautifulSoup(result, 'html.parser')
        self.assertEqual(len(rendered.select('[data-component-id="HB-SPECIAL-OPERATION"]')), 1)
        self.assertEqual(len(rendered.select('.hb-operation-supporting-panels > .line')), 2)
        self.assertEqual(rendered.get_text().count('12 hours'), 1)
        self.assertEqual(rendered.get_text().count('App note.'), 1)
        self.assertEqual(len(rendered.select('.hb-operation-step')), 2)
        self.assertEqual(rendered.img['src'], 'art.png')

    def test_missing_copy_is_rejected(self):
        soup = BeautifulSoup(self.source(), 'html.parser')
        soup.select_one('.line-block').decompose()
        with self.assertRaisesRegex(ValueError, 'followed by a line block'):
            list(parse_declared_operations(soup, source_path=Path('x.rst'), language='en'))
