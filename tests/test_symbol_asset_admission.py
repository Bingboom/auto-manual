"""Regression: names/semantics and an alpha channel do not establish reuse."""
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import fitz
from PIL import Image, ImageDraw

from tools.asset_pipeline.native_svg import native_symbol_svg
from tools.manual_ir import ManualSource, SourcePage, V2_SCHEMA_VERSION, build_manual_ir_from_source, write_manual_ir
from tools.web.symbol_asset_admission import SCHEMA, _reference, _render, _text, compare_symbol, require_symbol_asset_admission

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
        self.catalog_extra = {}
        patcher = patch('tools.web.shared_symbol_assets._catalog', side_effect=lambda: (
            self.md, {'assets': [{'key': r['shared_symbol_key'], 'path': r['asset_ref'],
                                 'sha256': r['asset_sha256']} for r in self.rows]
                      + self.catalog_extra.get('assets', []),
                      'withdrawn': withdrawn,
                      **{k: v for k, v in self.catalog_extra.items() if k != 'assets'}}))
        patcher.start()
        self.addCleanup(patcher.stop)

    def check(self):
        return require_symbol_asset_admission(self.md, self.root, self.manifest, 'en')

    def reviewed_caption(self):
        from tools.manual_ir.hashing import value_sha256

        meaning = 'Read the user manual.'
        path = self.md / 'manual.ir.json'
        raw = json.loads(path.read_text())
        block = raw['pages'][0]['blocks'][0]
        slots = block['payload']['component_spec']['slots']
        item = next(s['content'] for s in slots if s['role'] == 'panels')[0][0]
        item.update(meaning_text=meaning, meaning_html=meaning, icon_alt=meaning)
        block['content_sha256'] = value_sha256({'kind': block['kind'], 'payload': block['payload']})
        raw['content_sha256'] = value_sha256({
            'page_ids': [p['page_id'] for p in raw['pages']],
            'block_hashes': [block['content_sha256']],
        })
        path.write_text(json.dumps(raw))
        self.rows[0]['caption_text'] = meaning
        return {'id': 'reviewed-caption', 'physical_page': 1,
                'caption_sha256': self.rows[0]['caption_sha256'],
                'source_caption': 'Read the manual.', 'reviewed_caption': meaning,
                'status': 'operator-approved', 'operator_decision': 'Use reviewed wording.'}

    def test_candidate_cannot_approve_its_own_caption_erratum(self):
        erratum = self.reviewed_caption()
        self.manifest['symbol_caption_errata'] = [erratum]
        with self.assertRaisesRegex(RuntimeError, 'source PDF row text'):
            self.check()

    def test_trusted_caption_erratum_keeps_real_source_and_glyph_checks(self):
        erratum = self.reviewed_caption()
        with patch('tools.web.symbol_asset_admission._caption_errata', return_value=[erratum]):
            self.assertEqual(self.check()[0]['caption_erratum'], 'reviewed-caption')
            self.replace((self.md / self.rows[1]['asset_ref']).read_bytes())
            with self.assertRaisesRegex(RuntimeError, 'glyph/background differs'):
                self.check()

    def test_trusted_caption_erratum_rejects_changed_approval_or_source_text(self):
        erratum = self.reviewed_caption()
        for field, value, error in [
            ('operator_decision', '', 'reviewed source binding'),
            ('reviewed_caption', 'Ignore the manual.', 'reviewed source binding'),
            ('caption_sha256', '0' * 64, 'source PDF row text'),
            ('source_caption', 'Electric shock.', 'source PDF row text'),
        ]:
            with self.subTest(field=field), patch(
                'tools.web.symbol_asset_admission._caption_errata',
                return_value=[{**erratum, field: value}],
            ), self.assertRaisesRegex(RuntimeError, error):
                self.check()

    def glyph_waiver(self, **changes):
        row = self.rows[0]
        return {'id': 'reviewed-variation', 'physical_page': row['physical_page'],
                'drawing_indices': row['drawing_indices'], 'shared_symbol_key': row['shared_symbol_key'],
                'asset_sha256': row['asset_sha256'], 'max_mean_channel_error': 0.025,
                'status': 'operator-approved', 'operator_decision': 'Design variation; reuse shared glyph.',
                **changes}

    def test_trusted_glyph_waiver_admits_only_its_reviewed_variation(self):
        def error(candidate, suffix, reference):
            return 0.024 if candidate == (self.md / self.rows[0]['asset_ref']).read_bytes() else 0.0
        with patch('tools.web.symbol_asset_admission._symbol_error', side_effect=error):
            with self.assertRaisesRegex(RuntimeError, 'glyph/background differs'):
                self.check()
            self.manifest['symbol_glyph_waivers'] = [self.glyph_waiver()]
            with self.assertRaisesRegex(RuntimeError, 'glyph/background differs'):
                self.check()  # a candidate manifest cannot approve its own waiver
            with patch('tools.web.symbol_asset_admission._glyph_waivers', return_value=[self.glyph_waiver()]):
                self.assertEqual(self.check()[0]['glyph_waiver'], 'reviewed-variation')
            for changes, message in [
                ({'status': 'proposed'}, 'beyond its reviewed waiver'),
                ({'operator_decision': ''}, 'beyond its reviewed waiver'),
                ({'max_mean_channel_error': 0.02}, 'beyond its reviewed waiver'),
                ({'max_mean_channel_error': 0.5}, 'beyond its reviewed waiver'),
                ({'asset_sha256': '0' * 64}, 'glyph/background differs'),
                ({'drawing_indices': [0]}, 'glyph/background differs'),
            ]:
                with self.subTest(changes=changes), patch(
                    'tools.web.symbol_asset_admission._glyph_waivers',
                    return_value=[self.glyph_waiver(**changes)],
                ), self.assertRaisesRegex(RuntimeError, message):
                    self.check()

    def test_glyph_waiver_ceiling_rejects_a_substituted_glyph(self):
        self.replace((self.md / self.rows[1]['asset_ref']).read_bytes())
        waiver = self.glyph_waiver(max_mean_channel_error=0.03)
        with patch('tools.web.symbol_asset_admission._glyph_waivers', return_value=[waiver]), \
                self.assertRaisesRegex(RuntimeError, 'beyond its reviewed waiver'):
            self.check()

    def canonical_group(self, *, status='operator-confirmed', captions=None, rival=None):
        """Group fixture-0 (canonical) with a legacy copy of fixture-1's glyph."""
        legacy = self.md / 'assets/legacy.svg'
        legacy.write_bytes((self.md / self.rows[1]['asset_ref']).read_bytes())
        assets = [{'key': 'fixture-legacy', 'path': 'assets/legacy.svg',
                   'sha256': hashlib.sha256(legacy.read_bytes()).hexdigest()}]
        groups = [{'id': 'read', 'meaning': 'read', 'status': status, 'canonical': 'fixture-0',
                   'legacy_variants': ['fixture-legacy'],
                   'captions': {'en': ['Read the manual.'] if captions is None else captions},
                   'decision': 'SCG-TEST'}]
        if rival:
            groups.append({'id': 'rival', 'meaning': 'rival', 'status': 'proposed',
                           'canonical': 'fixture-1', 'legacy_variants': [],
                           'captions': {'en': ['Read the manual.']}, 'decision': None})
        self.catalog_extra = {'assets': assets, 'canonical_groups': groups, 'canonical_decisions': [
            {'id': 'SCG-TEST', 'date': '2026-11-03', 'operator_quotes': [{'quote': 'same icon'}]}]}

    def far_from_print(self, value=0.4):
        """Row 0 prints a design variation far beyond the 0.03 waiver ceiling."""
        canonical = (self.md / self.rows[0]['asset_ref']).read_bytes()
        return patch('tools.web.symbol_asset_admission._symbol_error',
                     side_effect=lambda c, s, r: value if c == canonical else 0.0)

    def test_confirmed_canonical_admits_its_group_printed_row_without_ceiling(self):
        self.canonical_group()
        with self.far_from_print():
            report = self.check()
        self.assertEqual((report[0]['canonical_group'], report[0]['canonical_decision']), ('read', 'SCG-TEST'))
        self.assertEqual(report[0]['max_mean_channel_error'], 0.4)
        self.assertNotIn('canonical_group', report[1])

    def test_canonical_release_needs_confirmed_group_and_listed_caption(self):
        for kwargs in [{'status': 'proposed'}, {'captions': ['Electric shock.']}, {'captions': []}]:
            with self.subTest(**kwargs):
                self.canonical_group(**kwargs)
                with self.far_from_print(), self.assertRaisesRegex(RuntimeError, 'glyph/background differs'):
                    self.check()

    def test_ungrouped_symbols_keep_fixed_tolerance_and_waiver_ceiling(self):
        self.canonical_group()
        row = self.rows[1]
        other = (self.md / row['asset_ref']).read_bytes()
        with patch('tools.web.symbol_asset_admission._symbol_error',
                   side_effect=lambda c, s, r: 0.025 if c == other else 0.0), \
                self.assertRaisesRegex(RuntimeError, 'glyph/background differs'):
            self.check()

    def test_confirmed_group_legacy_variant_cannot_be_bound(self):
        self.canonical_group()
        row = self.rows[0]
        canonical = self.md / 'assets/canonical.svg'
        canonical.write_bytes((self.md / row['asset_ref']).read_bytes())
        self.catalog_extra['assets'] = [{'key': 'fixture-0', 'path': 'assets/canonical.svg',
                                         'sha256': row['asset_sha256']}]
        legacy = (self.md / 'assets/legacy.svg').read_bytes()
        row.update(shared_symbol_key='fixture-legacy', asset_sha256=hashlib.sha256(legacy).hexdigest())
        (self.md / row['asset_ref']).write_bytes(legacy)
        with self.assertRaisesRegex(RuntimeError, 'legacy variant fixture-legacy of canonical group read; bind fixture-0'):
            self.check()

    def test_shared_caption_must_print_nearer_the_claimed_group(self):
        self.canonical_group(rival=True)
        with self.far_from_print(), self.assertRaisesRegex(RuntimeError, 'nearer symbol group rival'):
            self.check()  # rival canonical prints at 0.0, the claimed group at 0.4

    def test_confirmed_group_requires_dated_operator_words(self):
        from tools.web.shared_symbol_assets import canonical_groups
        self.canonical_group()
        self.catalog_extra['canonical_decisions'][0]['operator_quotes'] = []
        with self.assertRaisesRegex(ValueError, 'undated operator decision'):
            canonical_groups()
        self.canonical_group()
        self.catalog_extra['canonical_groups'][0]['legacy_variants'] = ['fixture-0']
        with self.assertRaisesRegex(ValueError, 'doubly grouped'):
            canonical_groups()

    def test_unbound_printed_word_split_and_inline_hyphens_remain_significant(self):
        self.assertNotEqual(_text('recyclingcen-\ntrum'), _text('recyclingcentrum'))
        self.assertNotEqual(_text('Li-ion'), _text('Liion'))

    def test_trusted_erratum_requires_exact_source_linebreak_binding(self):
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
            row['caption_text'] = 'Read the user manual.'
            erratum = {'physical_page': 1, 'caption_sha256': row['caption_sha256'],
                       'source_caption': 'Read the manual.',
                       'reviewed_caption': row['caption_text'],
                       'status': 'operator-approved', 'operator_decision': 'Use reviewed wording.'}
            with self.assertRaisesRegex(ValueError, 'source PDF row text'):
                _reference(page, row, row['caption_text'], erratum)
            row['caption_linebreak_joins'] = ['man-\nual']
            reference = _reference(page, row, row['caption_text'], erratum)
            compare_symbol((self.md / row['asset_ref']).read_bytes(), '.svg', reference)
            row['caption_linebreak_joins'] = ['wrong-\nword']
            with self.assertRaisesRegex(ValueError, 'one exact source linebreak'):
                _reference(page, row, row['caption_text'], erratum)

    def replace(self, data, suffix='.svg'):
        row = self.rows[0]
        row['asset_sha256'] = hashlib.sha256(data).hexdigest()
        # Keep actual IR ref unchanged: format comes from the real component asset.
        self.assertEqual(suffix, '.svg')
        (self.md / row['asset_ref']).write_bytes(data)

    def web_only(self, **changes):
        """Drop row 2 from the target print; reuse it from a donor print instead."""
        donor = self.root / 'donors/sibling.pdf'
        donor.parent.mkdir()
        donor.write_bytes(self.pdf.read_bytes())
        with fitz.open() as doc:
            page = doc.new_page(width=240, height=150)
            page.draw_rect((10, 10, 50, 140), color=None, fill=(.8, .8, .8))
            page.draw_polyline([(20, 35), (20, 20), (30, 22), (40, 20), (40, 35), (30, 37), (20, 35)], width=2)
            page.draw_line((30, 22), (30, 37), width=2)
            page.insert_text((65, 30), 'Read the manual.', fontsize=10)
            doc.save(self.pdf)
        target_sha = hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        donor_sha = hashlib.sha256(donor.read_bytes()).hexdigest()
        self.manifest['original_source']['sha256'] = target_sha
        row = self.rows[1]
        row.update(web_only_row='sibling-row', donor_source={'path': 'donors/sibling.pdf', 'sha256': donor_sha})
        return {'id': 'sibling-row', 'source_sha256': target_sha, 'model': 'TEST', 'region': 'US', 'language': 'en',
                'shared_symbol_key': row['shared_symbol_key'], 'asset_sha256': row['asset_sha256'],
                'donor': {'source_path': 'donors/sibling.pdf', 'source_sha256': donor_sha, 'physical_page': 1,
                          'drawing_indices': row['drawing_indices'], 'caption_sha256': row['caption_sha256']},
                'status': 'operator-approved', 'operator_decision': 'Web adds the row the print lacks.', **changes}

    def check_with_ledger(self, entries):
        contracts = self.root / 'contracts'
        contracts.mkdir(exist_ok=True)
        (contracts / 'symbol_web_only_rows.json').write_text(json.dumps(
            {'schema_version': 'auto-manual-symbol-web-only-rows/v1', 'entries': entries}))
        paths = SimpleNamespace(root=self.root, renderer_contracts_dir=contracts)
        with patch('tools.web.symbol_asset_admission.get_paths', return_value=paths):
            return self.check()

    def test_web_only_row_requires_a_trusted_entry(self):
        entry = self.web_only()
        marker = self.rows[1].pop('web_only_row')
        with self.assertRaisesRegex(RuntimeError, 'no source drawings'):
            self.check_with_ledger([])  # the target print has no such row
        self.rows[1]['web_only_row'] = marker
        with self.assertRaisesRegex(RuntimeError, 'requires one trusted entry'):
            self.check_with_ledger([])
        self.manifest['symbol_web_only_rows'] = [entry]
        with self.assertRaisesRegex(RuntimeError, 'requires one trusted entry'):
            self.check_with_ledger([])  # a candidate manifest cannot approve its own row
        with self.assertRaisesRegex(RuntimeError, 'requires one trusted entry'):
            self.check_with_ledger([entry, entry])
        report = self.check_with_ledger([entry])
        self.assertNotIn('web_only_row', report[0])
        self.assertEqual(report[1]['web_only_row'], 'sibling-row')
        self.assertEqual(report[1]['donor_source_sha256'], entry['donor']['source_sha256'])

    def test_web_only_entry_binds_target_approval_and_donor_row(self):
        entry = self.web_only()
        donor = entry['donor']
        for changes, message in [
            ({'status': 'proposed'}, 'reviewed entry'),
            ({'operator_decision': ''}, 'reviewed entry'),
            ({'asset_sha256': '0' * 64}, 'reviewed entry'),
            ({'donor': {**donor, 'caption_sha256': '0' * 64}}, 'reviewed entry'),
            ({'donor': {**donor, 'drawing_indices': [0]}}, 'reviewed entry'),
            ({'donor': {**donor, 'source_path': 'source.pdf'}}, 'reviewed entry'),
            ({'language': 'fr'}, 'requires one trusted entry'),
            ({'source_sha256': '0' * 64}, 'requires one trusted entry'),
        ]:
            with self.subTest(changes=changes), self.assertRaisesRegex(RuntimeError, message):
                self.check_with_ledger([{**entry, **changes}])
        # Repointing both the row and its entry at the target print still fails:
        # that print has no such row.
        target = {'path': 'source.pdf', 'sha256': self.manifest['original_source']['sha256']}
        self.rows[1]['donor_source'] = target
        with self.assertRaisesRegex(RuntimeError, 'no source drawings'):
            self.check_with_ledger([{**entry, 'donor': {**donor, 'source_path': target['path'],
                                                         'source_sha256': target['sha256']}}])

    def test_web_only_row_keeps_donor_glyph_and_caption_checks(self):
        entry = self.web_only()
        donor = self.root / entry['donor']['source_path']
        original = donor.read_bytes()
        donor.write_bytes(self.pdf.read_bytes())
        with self.assertRaisesRegex(RuntimeError, 'SHA-256 mismatch'):
            self.check_with_ledger([entry])  # changed donor bytes
        donor.write_bytes(original)
        self.assertEqual(len(self.check_with_ledger([entry])), 2)
        row = self.rows[1]
        data = (self.md / self.rows[0]['asset_ref']).read_bytes()
        row['asset_sha256'] = hashlib.sha256(data).hexdigest()
        (self.md / row['asset_ref']).write_bytes(data)
        with self.assertRaisesRegex(RuntimeError, 'glyph/background differs'):
            self.check_with_ledger([{**entry, 'asset_sha256': row['asset_sha256']}])

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
