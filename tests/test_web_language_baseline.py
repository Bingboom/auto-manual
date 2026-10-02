"""Independent approved contracts must reject self-consistent candidate drift."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.manual_ir.hashing import file_sha256
from tools.prepared_component_policy import POLICY_SCHEMA
from tools.web_language_baseline import (
    audit_language_baseline, baseline_trial, candidate_language_baseline,
    require_language_baseline, review_digest,
)
from tools.web_language_structure import digest, summarize_language_structure


class LanguageBaselineTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'art.png').write_bytes(b'test-only artwork')
        self.page_map = {'operation.rst': 'operation'}
        self.component_map = {'power': 'power', 'reset': 'reset'}
        self.raw = {
            'model': 'TEST', 'region': 'EU', 'language': 'en', 'metadata': {},
            'snapshot_sha256': 'a' * 64, 'content_sha256': 'b' * 64,
            'pages': [{'page_id': 'operation.rst', 'blocks': [
                {'payload': self.component(ref)} for ref in ('power', 'reset')]}],
        }
        self.entry = candidate_language_baseline(
            self.raw, self.root, revision='test-v1', page_map=self.page_map,
            source_sha256='c' * 64, component_map=self.component_map,
        )
        self.entry['locales']['en']['source_pages'] = [7, 8]
        for decision in self.entry['asset_decisions'].values():
            decision.update(source_ref='shared/test-art', content_mode='textless',
                            text_owner='html', frame_policy='css', leader_policy='preserve',
                            applicability='TEST/EU/en,fr')
        self.entry['status'] = 'approved'
        self.entry['review_sha256'] = review_digest(self.entry)
        evidence = {'path': 'art.png', 'sha256': file_sha256(self.root / 'art.png')}
        # Explicit test-only simulated operator confirmation; no production approval.
        self.entry['approval'] = {
            'operator': 'TEST ONLY', 'record': 'test-only://confirmation',
            'desktop': evidence, 'mobile': evidence,
            **{k: self.entry[k] for k in ('ir_content_sha256', 'structure_sha256', 'review_sha256')},
        }
        self.entry['locales']['fr'] = deepcopy(self.entry['locales']['en'])
        self.raw['language'] = 'fr'
        self.raw['metadata']['language_baseline'] = {
            'revision': self.entry['revision'], 'sha256': self.entry['structure_sha256'],
        }

    @staticmethod
    def component(ref):
        return {'kind': 'component', 'component_spec': {
            'source_ref': ref, 'component_id': 'HB-TABLE-SPEC', 'variant': 'vertical',
            'slots': [{'role': 'rows', 'content_kind': 'table_rows',
                       'content': [{'label': 'Voltage', 'value': '230 V', 'rowspan': 1}]}],
            'assets': [{'role': 'artwork', 'locale_policy': 'shared', 'asset_ref': 'art.png'}],
            'metadata': {'presentation_mode': 'base-art-live-copy'},
        }}

    def audit(self, raw=None, entry=None):
        return audit_language_baseline(raw or self.raw, self.root, entry or self.entry,
                                       evidence_root=self.root)

    def test_native_text_and_long_copy_keep_structure(self):
        raw = deepcopy(self.raw)
        row = raw['pages'][0]['blocks'][0]['payload']['component_spec']['slots'][0]['content'][0]
        row['label'] = 'Tension nominale ' * 100
        row['value'] = '230 V — texte original français'
        self.assertEqual(self.audit(raw)['status'], 'verified')

    def test_mutations_fail_even_with_recomputed_candidate_hashes(self):
        def change_spec(raw, key, value):
            raw['pages'][0]['blocks'][0]['payload']['component_spec'][key] = value
        mutations = {
            'delete component': lambda r: r['pages'][0]['blocks'].pop(),
            'swap identical-shaped slots': lambda r: r['pages'][0]['blocks'].reverse(),
            'variant': lambda r: change_spec(r, 'variant', 'horizontal'),
            'ordinary table': lambda r: r['pages'][0]['blocks'][0].update(payload={'kind': 'table'}),
            'table merge': lambda r: change_spec(r, 'slots', [
                {'role': 'rows', 'content_kind': 'table_rows', 'content': [{'rowspan': 2}]}]),
            'remove baseline marker': lambda r: r['metadata'].clear(),
            'wrong model': lambda r: r.update(model='OTHER'),
            'wrong region': lambda r: r.update(region='UK'),
            'unmapped language': lambda r: r.update(language='ja'),
            'new snapshot': lambda r: r.update(snapshot_sha256='d' * 64),
            'presentation': lambda r: change_spec(r, 'metadata', {'presentation_mode': 'finished-panel'}),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                raw = deepcopy(self.raw)
                mutate(raw)
                raw['content_sha256'] = digest(raw['pages'])
                self.assertEqual(self.audit(raw)['status'], 'blocked')

    def test_recut_asset_rehashed_candidate_is_rejected(self):
        (self.root / 'art.png').write_bytes(b'recut image or wrong regional/language image')
        # Preserve evidence separately so this checks the artwork delta itself.
        (self.root / 'evidence').write_bytes(b'test-only artwork')
        for viewport in ('desktop', 'mobile'):
            self.entry['approval'][viewport] = {'path': 'evidence', 'sha256': file_sha256(self.root / 'evidence')}
        raw = deepcopy(self.raw)
        raw['metadata']['asset_sha256'] = {'art.png': file_sha256(self.root / 'art.png')}
        raw['content_sha256'] = digest(raw['pages'])
        result = self.audit(raw)
        self.assertEqual(result['status'], 'blocked')
        self.assertTrue(any(d['path'].endswith('/sha256') for d in result['differences']))

    def test_same_asset_bytes_can_be_packaged_under_another_path(self):
        (self.root / 'copy.png').write_bytes((self.root / 'art.png').read_bytes())
        raw = deepcopy(self.raw)
        raw['pages'][0]['blocks'][0]['payload']['component_spec']['assets'][0]['asset_ref'] = 'copy.png'
        self.assertEqual(self.audit(raw)['status'], 'verified')

    def test_approval_and_decisions_cannot_drift(self):
        for mutate in (
            lambda e: e.update(status='candidate'),
            lambda e: e.update(approval=None),
            lambda e: e['approval'].update(ir_content_sha256='e' * 64),
            lambda e: e.update(source_sha256='d' * 64),
            lambda e: e['asset_decisions'].clear(),
            lambda e: e['approval']['mobile'].update(path='missing.png'),
        ):
            entry = deepcopy(self.entry)
            mutate(entry)
            self.assertEqual(self.audit(entry=entry)['status'], 'blocked')

    def test_exact_source_reviewed_difference_and_stale_rules(self):
        raw = deepcopy(self.raw)
        raw['pages'][0]['blocks'][0]['payload']['component_spec']['variant'] = 'horizontal'
        delta = self.audit(raw)['differences'][0]
        entry = deepcopy(self.entry)
        rule = {k: delta[k] for k in ('path', 'expected_sha256', 'actual_sha256')}
        rule.update(reason='Native table grouping', approval_record='test-only review',
                    source_ref='original.pdf#page=8', source_sha256='c' * 64, source_pages=[8])
        entry['locales']['fr']['differences'] = [rule]
        self.assertEqual(self.audit(raw, entry)['status'], 'verified')
        self.assertEqual(self.audit(entry=entry)['status'], 'blocked')
        rule['source_sha256'] = 'e' * 64
        self.assertEqual(self.audit(raw, entry)['status'], 'blocked')
        rule['path'] = '/pages/*'
        self.assertEqual(self.audit(raw, entry)['status'], 'blocked')

    def test_referenced_assets_cannot_escape_package(self):
        raw = deepcopy(self.raw)
        raw['pages'][0]['blocks'][0]['payload']['component_spec']['assets'][0]['asset_ref'] = '../outside.png'
        self.assertEqual(self.audit(raw)['status'], 'blocked')

    def test_trusted_contract_enrollment_not_candidate_metadata(self):
        path = self.root / 'contract.json'
        path.write_text(json.dumps({'schema_version': POLICY_SCHEMA}))
        self.assertEqual(require_language_baseline(self.raw, self.root, contract_path=path)['status'], 'not_enrolled')
        entry = deepcopy(self.entry)
        entry['status'] = 'candidate'
        path.write_text(json.dumps({'schema_version': POLICY_SCHEMA, 'language_baselines': {'TEST/EU': entry}}))
        self.raw['metadata'].clear()
        with self.assertRaisesRegex(ValueError, 'not operator-approved'):
            require_language_baseline(self.raw, self.root, contract_path=path)

    def test_candidate_trial_cannot_approve_or_rewrite(self):
        before = deepcopy(self.raw)
        report = baseline_trial(self.raw, self.root, self.entry, page_map=self.page_map,
                                component_map=self.component_map)
        self.assertFalse(report['publication_eligible'])
        self.assertEqual(report['differences'], [])
        self.assertEqual(before, self.raw)

    def test_semantic_mappings_are_exact_and_unique(self):
        for mapping in ({}, {'power': 'x', 'reset': 'x'}, {'power': 'x'}):
            with self.assertRaises(ValueError):
                summarize_language_structure(self.raw, self.root, self.page_map, mapping)

    def test_relocated_build_references_preserve_semantic_slots(self):
        raw = deepcopy(self.raw)
        for block in raw['pages'][0]['blocks']:
            spec = block['payload']['component_spec']
            spec['source_ref'] = '/new/build/location/' + spec['source_ref']
        self.assertEqual(self.audit(raw)['status'], 'verified')

    def test_wrong_component_language_is_rejected(self):
        raw = deepcopy(self.raw)
        raw['pages'][0]['blocks'][0]['payload']['component_spec']['language'] = 'ja'
        self.assertEqual(self.audit(raw)['status'], 'blocked')

    def test_approved_image_difference_is_exact_and_source_bound(self):
        (self.root / 'localized.png').write_bytes(b'native dense-label illustration')
        raw = deepcopy(self.raw)
        raw['pages'][0]['blocks'][0]['payload']['component_spec']['assets'][0]['asset_ref'] = 'localized.png'
        result = self.audit(raw)
        entry = deepcopy(self.entry)
        entry['locales']['fr']['differences'] = [
            {**{k: d[k] for k in ('path', 'expected_sha256', 'actual_sha256')},
             'reason': 'French dense labels preserved', 'approval_record': 'test only',
             'source_ref': 'native.ai#page=8', 'source_sha256': 'c' * 64, 'source_pages': [8]}
            for d in result['differences']
        ]
        self.assertEqual(self.audit(raw, entry)['status'], 'verified')
        (self.root / 'localized.png').write_bytes(b'another unreviewed crop')
        self.assertEqual(self.audit(raw, entry)['status'], 'blocked')

    def test_historical_replay_skips_new_gate(self):
        from tools.web_component_admission import require_fresh_component_admission
        with patch('tools.web_component_admission.require_language_baseline', side_effect=AssertionError):
            self.assertIsNone(require_fresh_component_admission(
                self.root, model='TEST', region='EU', language='fr', stored=True))


if __name__ == '__main__':
    unittest.main()
