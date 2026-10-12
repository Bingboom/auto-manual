"""Regression: names/semantics and an alpha channel do not establish reuse."""
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fitz
from PIL import Image, ImageDraw

from tools.asset_pipeline.native_svg import native_symbol_svg
from tools.manual_ir import ManualSource, SourcePage, V2_SCHEMA_VERSION, build_manual_ir_from_source, write_manual_ir
from tools.web.symbol_asset_admission import SCHEMA, _reference, _render, compare_symbol, require_symbol_asset_admission

PACKAGE = Path(__file__).resolve().parents[1] / 'data/manual_sources/JHP-3600C/US/en/git-20261005-31fd0692'


class SymbolAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.md = self.root / 'web'
        (self.md / 'assets').mkdir(parents=True)
        self.pdf = self.root / 'source.pdf'
        with fitz.open() as doc:
            page = doc.new_page(width=240, height=150)
            page.draw_rect((10, 10, 50, 140), color=None, fill=(.8, .8, .8))
            # Two visibly different original vector glyphs; separate caption rows.
            page.draw_polyline([(20, 35), (20, 20), (30, 22), (40, 20), (40, 35), (30, 37), (20, 35)], width=2)
            page.draw_line((30, 22), (30, 37), width=2)
            page.insert_text((65, 30), 'Read the manual.', fontsize=10)
            page.draw_polyline([(22, 95), (34, 78), (29, 95), (38, 95), (25, 112), (30, 95)], color=None, fill=(0, 0, 0), closePath=True)
            page.insert_text((65, 100), 'Electric shock.', fontsize=10)
            doc.save(self.pdf)
        content = json.loads((PACKAGE / 'source/content.json').read_text())
        spec = deepcopy(next(n['component_spec'] for ch in content['chapters'] for n in ch['nodes']
                             if n.get('component_spec', {}).get('component_id') == 'HB-TABLE-SYMBOL-ICON'))
        spec['assets'] = spec['assets'][:2]
        panels = next(slot for slot in spec['slots'] if slot['role'] == 'panels')
        panels['content'] = [[deepcopy(panels['content'][0][0])], [deepcopy(panels['content'][0][1])]]
        self.rows = []
        with fitz.open(self.pdf) as doc:
            page = doc[0]
            for i, (meaning, box, caption, band) in enumerate([
                ('Read the manual.', [18, 18, 42, 39], [60, 12, 220, 44], [10, 10, 230, 48]),
                ('Electric shock.', [15, 73, 45, 117], [60, 80, 220, 120], [10, 70, 230, 130]),
            ]):
                indices = [j for j, d in enumerate(page.get_drawings()) if fitz.Rect(box).contains(d['rect'])]
                svg = native_symbol_svg(page, indices, box)
                ref = f'assets/icon{i}.svg'
                (self.md / ref).write_bytes(svg)
                spec['assets'][i]['asset_ref'] = ref
                item = panels['content'][i][0]
                item.update(asset_index=i, meaning_text=meaning, meaning_html=meaning, icon_alt=meaning)
                self.rows.append({'asset_ref': ref, 'asset_sha256': hashlib.sha256(svg).hexdigest(),
                                  'shared_symbol_key': f'fixture-{i}',
                                  'physical_page': 1, 'drawing_indices': indices, 'glyph_bbox': box,
                                  'caption_bbox': caption, 'row_bbox': band, 'caption_text': meaning,
                                  'caption_sha256': hashlib.sha256(page.get_pixmap(
                                      matrix=fitz.Matrix(4, 4), clip=fitz.Rect(caption), alpha=False).tobytes('png')).hexdigest()})
        node = {'kind': 'component', 'schema_version': 'manual-flow/v2', 'component_spec': spec}
        ir = build_manual_ir_from_source(ManualSource(
            model='TEST', region='US', language='en', source='prepared-document', bundle_root='source',
            bundle_sha256='a' * 64, snapshot_sha256=None, layout_params_sha256='b' * 64,
            style_contract_sha256='c' * 64, schema_version=V2_SCHEMA_VERSION,
            pages=(SourcePage(page_id='symbols', source_ref='source:1', source_path='source.pdf',
                              language='en', source_sha256='d' * 64, blocks=(('flow', node),)),),
        ))
        write_manual_ir(ir, self.md / 'manual.ir.json')
        self.manifest = {'original_source': {'filename': 'source.pdf', 'sha256': hashlib.sha256(self.pdf.read_bytes()).hexdigest()},
                         'symbol_asset_admission': {'schema_version': SCHEMA, 'locales': {'en': self.rows}}}

        # Stub only the reusable catalog boundary; the source PDF, actual IR,
        # glyph rendering, file/hash checks and withdrawal rules remain real.
        withdrawn = json.loads((Path(__file__).resolve().parents[1] /
                               'docs/renderers/web/assets/shared/symbols/manifest.json').read_text())['withdrawn']
        patcher = patch('tools.web.shared_symbol_assets._catalog', side_effect=lambda: (
            self.md, {'assets': [{'key': r['shared_symbol_key'], 'path': r['asset_ref'],
                                 'sha256': r['asset_sha256']} for r in self.rows], 'withdrawn': withdrawn}))
        patcher.start()
        self.addCleanup(patcher.stop)

    def check(self):
        return require_symbol_asset_admission(self.md, self.root, self.manifest, 'en')

    def replace(self, data, suffix='.svg'):
        row = self.rows[0]
        row['asset_sha256'] = hashlib.sha256(data).hexdigest()
        # Keep actual IR ref unchanged: format comes from the real component asset.
        self.assertEqual(suffix, '.svg')
        (self.md / row['asset_ref']).write_bytes(data)

    def test_withdrawn_legacy_bytes_fail_after_rename(self):
        from tools.web.shared_symbol_assets import require_usable_symbol_file
        old = Path(__file__).resolve().parents[1] / 'docs/templates/word_template/common_assets/symbols/electric_shock.png'
        renamed = self.md / 'assets/new-name.png'
        renamed.write_bytes(old.read_bytes())
        with self.assertRaisesRegex(ValueError, 'withdrawn Web symbol bytes'):
            require_usable_symbol_file(renamed)

    def test_shared_binding_rejects_private_redraw_or_changed_bytes(self):
        from tools.web.shared_symbol_assets import require_shared_symbol_binding
        file = self.md / 'assets/redrawn.svg'
        file.write_bytes((self.md / self.rows[1]['asset_ref']).read_bytes())
        with self.assertRaisesRegex(ValueError, 'reuse shared variant bytes unchanged'):
            require_shared_symbol_binding(self.rows[0], file)
        with self.assertRaisesRegex(ValueError, 'explicit shared glyph variant'):
            require_shared_symbol_binding({**self.rows[0], 'shared_symbol_key': 'guess-by-name'}, file)

    def test_native_transparent_assets_pass(self):
        self.assertEqual(len(self.check()), 2)

    def test_source_bound_linebreak_join_preserves_native_caption(self):
        with fitz.open(self.pdf) as doc:
            page = doc[0]
            row = deepcopy(self.rows[0])
            page.add_redact_annot(fitz.Rect(row['caption_bbox']))
            page.apply_redactions(images=0, graphics=0)
            page.insert_text((65, 24), 'Read the man-', fontsize=10)
            page.insert_text((65, 36), 'ual.', fontsize=10)
            row['caption_sha256'] = hashlib.sha256(page.get_pixmap(
                matrix=fitz.Matrix(4, 4), clip=fitz.Rect(row['caption_bbox']),
                alpha=False).tobytes('png')).hexdigest()
            with self.assertRaisesRegex(ValueError, 'meaning differs'):
                _reference(page, row, 'Read the manual.')
            row['caption_linebreak_joins'] = ['man-\nual']
            reference = _reference(page, row, 'Read the manual.')
            compare_symbol((self.md / row['asset_ref']).read_bytes(), '.svg', reference)
            for joins in (['man-ual'], ['wrong-\nword'], ['man-\nual', 'man-\nual'], 'man-\nual'):
                row['caption_linebreak_joins'] = joins
                with self.subTest(joins=joins), self.assertRaisesRegex(ValueError, 'caption'):
                    _reference(page, row, 'Read the manual.')
            row['caption_linebreak_joins'] = ['man-\nual']
            row['caption_text'] = 'Read the wrong manual.'
            with self.assertRaisesRegex(ValueError, 'meaning differs'):
                _reference(page, row, 'Read the wrong manual.')
            row['caption_text'] = 'Read the manual.'
            row['caption_sha256'] = 'a' * 64
            with self.assertRaisesRegex(ValueError, 'caption pixels'):
                _reference(page, row, 'Read the manual.')

    def test_missing_or_incomplete_admission_is_rejected(self):
        self.manifest.pop('symbol_asset_admission')
        with self.assertRaisesRegex(RuntimeError, 'source-bound'):
            self.check()
        self.manifest['symbol_asset_admission'] = {'schema_version': SCHEMA, 'locales': {'en': self.rows[:1]}}
        with self.assertRaisesRegex(RuntimeError, 'every actual component row'):
            self.check()

    def test_gray_rgb_png_and_rgba_rectangle_fail_even_when_hashes_match(self):
        reference = (self.md / self.rows[0]['asset_ref']).read_bytes()
        for mode in ('RGB', 'RGBA'):
            image = Image.new(mode, (120, 120), '#dddddd')
            ImageDraw.Draw(image).line((20, 20, 100, 100), fill='black', width=5)
            stream = BytesIO()
            image.save(stream, format='PNG')
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'opaque backdrop'):
                compare_symbol(stream.getvalue(), '.png', reference)

    def test_inset_gray_rectangle_with_transparent_border_fails_glyph_check(self):
        reference = (self.md / self.rows[0]['asset_ref']).read_bytes()
        image = Image.new('RGBA', (120, 120))
        ImageDraw.Draw(image).rectangle((5, 5, 114, 114), fill='#ddd')
        stream = BytesIO()
        image.save(stream, format='PNG')
        with self.assertRaisesRegex(ValueError, 'glyph/background differs'):
            compare_symbol(stream.getvalue(), '.png', reference)

    def test_transparent_wrong_glyph_is_rejected_after_rehash(self):
        self.replace((self.md / self.rows[1]['asset_ref']).read_bytes())
        with self.assertRaisesRegex(RuntimeError, 'glyph/background differs'):
            self.check()

    def test_rebound_wrong_source_row_cannot_match_meaning(self):
        self.rows[0].update({key: self.rows[1][key] for key in (
            'drawing_indices', 'glyph_bbox', 'caption_bbox', 'row_bbox', 'caption_text', 'caption_sha256')})
        with self.assertRaisesRegex(RuntimeError, 'meaning differs'):
            self.check()

    def test_tampered_source_caption_hash_page_and_drawing_selection_fail(self):
        for key, value, message in [('caption_sha256', 'a' * 64, 'caption pixels'),
                                     ('physical_page', 9, 'outside authoritative'),
                                     ('drawing_indices', [0], 'every drawing')]:
            original = self.rows[0][key]
            self.rows[0][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError, message):
                self.check()
            self.rows[0][key] = original
        self.pdf.write_bytes(b'altered')
        with self.assertRaisesRegex(RuntimeError, 'SHA-256 mismatch'):
            self.check()

    def test_traversal_and_symlink_rejected(self):
        self.manifest['original_source']['filename'] = '../source.pdf'
        with self.assertRaisesRegex(RuntimeError, 'unsafe'):
            self.check()
        self.manifest['original_source']['filename'] = 'alias.pdf'
        (self.root / 'alias.pdf').symlink_to(self.pdf)
        with self.assertRaisesRegex(RuntimeError, 'escapes'):
            self.check()

    def test_original_pdf_group_opacity_is_preserved(self):
        # Real source has group opacity that get_drawings() omits. Replaying
        # only flattened shapes would darken the triangle's inner fill.
        with fitz.open(next(PACKAGE.glob('*.pdf'))) as doc:
            row = json.loads((PACKAGE / 'source/symbol_asset_admission.json').read_text())['locales']['en'][0]
            svg = native_symbol_svg(doc[4], row['drawing_indices'], row['glyph_bbox'])
        alpha = _render(svg, '.svg').getchannel('A')
        self.assertTrue(any(45 <= a <= 60 for a in alpha.getdata()))

    def test_valid_png_with_different_resolution_and_invisible_rgb_passes(self):
        reference = (self.md / self.rows[0]['asset_ref']).read_bytes()
        image = _render(reference, '.svg')
        pixels = list(image.getdata())
        image.putdata([(255, 0, 255, 0) if a == 0 else (r, g, b, a) for r, g, b, a in pixels])
        stream = BytesIO()
        image.resize((image.width * 2, image.height * 2)).save(stream, format='PNG')
        compare_symbol(stream.getvalue(), '.png', reference)

    def test_seal_calls_gate_before_creating_evidence(self):
        from tools.web.frozen_source_evidence import seal_frozen_web_evidence
        from tools.web.language_release_evidence import _file_inventory
        payload = {**self.manifest, 'schema_version': 'auto-manual-frozen-web-source/v1',
                   'target': {'model': 'TEST', 'region': 'US', 'languages': ['en'], 'technical_version': 'test'},
                   'web_roots': {'en': 'web'}, 'inputs': list(_file_inventory(self.root))}
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(payload))
        self.replace((self.md / self.rows[1]['asset_ref']).read_bytes())
        payload['symbol_asset_admission'] = self.manifest['symbol_asset_admission']
        manifest.write_text(json.dumps(payload))
        with patch('tools.web.frozen_source_evidence.require_publishable_manual_ir'), \
                self.assertRaisesRegex(RuntimeError, 'glyph/background differs'):
            seal_frozen_web_evidence(source_manifest_path=manifest, source_root=self.root, language='en',
                                     markdown_dir=self.md, markdown_name='manual.md', html_dir=self.root / 'html',
                                     evidence_dir=self.root / 'evidence', git_ref='test')
        self.assertFalse((self.root / 'evidence').exists())
