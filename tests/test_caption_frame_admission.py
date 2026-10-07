"""Actual caption-region pixels, fresh-seal admission and bounded false positives."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import hashlib
import html
import json

from bs4 import BeautifulSoup
from tools.component_specs.reference_figure_html import parse_declared_references
from tools.manual_ir.components import component_flow_node

from PIL import Image, ImageDraw

from tools.web.caption_frame_admission import check_caption_frames, require_caption_frame_admission
from tools.web.frozen_source_evidence import seal_frozen_web_evidence


class CaptionFrameAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'art.png'
        self.layout = {'panel_fill': '#ebeded',
                       'labels': [{'line': 0, 'rect': [50, 70, 45, 15], 'fill': '#ffffff'}]}

    def art(self, baked=False, transparent=False):
        image = Image.new('RGBA', (400, 200), (235, 237, 237, 0 if transparent else 255))
        draw = ImageDraw.Draw(image)
        # White housing belongs to the artwork, outside the caption region.
        draw.rounded_rectangle((20, 20, 120, 170), radius=5, fill='white', outline='black')
        if baked:
            draw.rounded_rectangle((200, 140, 380, 170), radius=15, fill='white')
        image.save(self.path)

    def test_empty_capsule_and_capsule_with_residual_text_rejected(self):
        self.art(baked=True)
        with self.assertRaisesRegex(ValueError, 'baked caption frame'):
            check_caption_frames(self.path, self.layout)
        with Image.open(self.path) as image:
            ImageDraw.Draw(image).text((220, 148), 'old', fill='black')
            image.save(self.path)
        with self.assertRaisesRegex(ValueError, 'baked caption frame'):
            check_caption_frames(self.path, self.layout)

    def test_gray_panel_white_product_and_transparent_art_pass(self):
        for transparent in (False, True):
            self.art(transparent=transparent)
            self.assertEqual('passed', check_caption_frames(self.path, self.layout)[0]['status'])

    def test_same_tone_is_explicitly_visual_review_and_no_fill_has_no_gate(self):
        self.art(baked=True)
        layout = deepcopy(self.layout)
        layout['panel_fill'] = '#ffffff'
        self.assertEqual('same-tone-visual-review', check_caption_frames(self.path, layout)[0]['status'])
        del layout['labels'][0]['fill']
        self.assertEqual([], check_caption_frames(self.path, layout))

    def test_actual_component_cannot_hide_baked_frame_or_change_hash(self):
        self.art(baked=True)
        layout = {**self.layout, 'art_sha256': hashlib.sha256(self.path.read_bytes()).hexdigest(),
                  'panel_top': 0}
        config = {'id': 'caption', 'web_replace_key': 'reference.caption',
                  'capture_following_lines': 1, 'presentation_mode': 'base-art-live-copy',
                  'base_art_layout': layout}
        soup = BeautifulSoup('<img class="hb-source-reference" src="art.png" data-reference="'
                             + html.escape(json.dumps(config), quote=True)
                             + '"><div class="line-block"><div class="line">Caption</div></div>',
                             'html.parser')
        spec, _, _, _ = next(parse_declared_references(soup, source_path=Path('source.json'), language='en'))
        node = component_flow_node(spec)
        ir = SimpleNamespace(pages=[SimpleNamespace(blocks=[SimpleNamespace(payload=node)])])
        with patch('tools.web.caption_frame_admission.read_manual_ir', return_value=ir):
            with self.assertRaisesRegex(RuntimeError, 'baked caption frame'):
                require_caption_frame_admission(self.path.parent)
            self.art()
            with self.assertRaisesRegex(RuntimeError, 'SHA-256 differs'):
                require_caption_frame_admission(self.path.parent)
            node['component_spec']['metadata']['base_art_layout']['art_sha256'] = hashlib.sha256(
                self.path.read_bytes()).hexdigest()
            self.assertEqual('passed', require_caption_frame_admission(self.path.parent)[0]['labels'][0]['status'])

    def test_fresh_seal_invokes_gate_before_creating_evidence(self):
        with (patch('tools.web.frozen_source_evidence.require_publishable_manual_ir'),
              patch('tools.web.frozen_source_evidence._load_object', return_value={}),
              patch('tools.web.frozen_source_evidence._source',
                    return_value=({'model': 'X', 'region': 'US'}, (), Path('web/en'))),
              patch('tools.web.frozen_source_evidence.require_fresh_component_admission'),
              patch('tools.web.frozen_source_evidence.require_symbol_asset_admission'),
              patch('tools.web.frozen_source_evidence.require_caption_frame_admission',
                    side_effect=RuntimeError('baked caption frame'))):
            evidence = Path(self.tmp.name) / 'evidence'
            with self.assertRaisesRegex(RuntimeError, 'baked caption frame'):
                seal_frozen_web_evidence(source_manifest_path=self.path, source_root=self.path.parent,
                                         language='en', markdown_dir=self.path.parent,
                                         markdown_name='manual.md', html_dir=self.path.parent,
                                         evidence_dir=evidence, git_ref='abc')
            self.assertFalse(evidence.exists())
