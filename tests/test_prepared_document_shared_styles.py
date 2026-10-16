"""Shared-style gate for prepared-document Web packages: no source-drawn styles."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.utils.path_utils import PathSegments
from tools.web.prepared_style_audit import (
    audit_prepared_document_styles,
    audit_prepared_package_locale,
    load_baseline,
    paint_properties,
    require_prepared_style_admission,
    table_text_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
# Locales frozen before the gate (2026-10-16), including the four JA-AD500A-SIL
# solar-voc locales that landed on main the same day before the gate merged.
# The baseline may shrink, never grow: raising this number needs the operator's
# decision recorded in the PR.
BASELINE_LIMIT = 124
RELEASED_SOURCE_DRAWN = 'data/manual_sources/JE-3600A/JP/git-20261013-fd06cd04-web-layout/web/ja'


def prepared_locales():
    for ir in sorted([*ROOT.glob('data/manual_sources/**/web/*/' + PathSegments.MANUAL_IR_JSON),
                      *ROOT.glob('manual_sources/**/web/*/' + PathSegments.MANUAL_IR_JSON)]):
        raw = json.loads(ir.read_text(encoding='utf-8'))
        if raw.get('source') == 'prepared-document':
            yield ir.parent, raw


def manifest_of(web_root: Path) -> dict:
    path = web_root.parent.parent / 'source_manifest.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}


def node(kind, children=(), css=None, style=None, **fields):
    attributes = {}
    if css:
        attributes['class'] = css
    if style:
        attributes['style'] = style
    value = {'kind': kind, 'children': list(children), **fields}
    if attributes:
        value['presentation'] = {'html': {'attributes': attributes}}
    return value


def text(value):
    return {'kind': 'text', 'text': value}


def ir(*payloads, source='prepared-document'):
    return {'source': source, 'model': 'M', 'region': 'R', 'language': 'xx',
            'pages': [{'page_id': 'page-1', 'blocks': [{'block_id': f'b{i}', 'payload': p}
                                                        for i, p in enumerate(payloads)]}]}


TABLE = node('table', [node('table_body', [node('table_row', [node('table_cell', [text('A')], header=False)])])])


class AuditRuleTests(unittest.TestCase):
    def issues(self, *payloads, **kwargs):
        return audit_prepared_document_styles(ir(*payloads), **kwargs)['issues']

    def test_other_sources_are_not_governed(self):
        report = audit_prepared_document_styles(ir(TABLE, source='frozen-pdf-json'))
        self.assertFalse(report['applicable'])

    def test_source_classes_and_inline_styles_are_rejected(self):
        issues = self.issues(node('paragraph', [text('x')], css='ht-cell native-band'),
                             node('paragraph', [text('y')], style='color:red'))
        self.assertTrue(any("'ht-cell'" in issue for issue in issues))
        self.assertTrue(any("'native-band'" in issue for issue in issues))
        self.assertTrue(any('inline style' in issue for issue in issues))

    def test_shared_and_generic_classes_pass(self):
        self.assertEqual(self.issues(node('group', [text('x')], css='line-block container'),
                                     node('paragraph', [text('y')], css='manual-table')), [])

    def test_component_subtrees_belong_to_their_own_contract(self):
        component = {'kind': 'component', 'component_spec': {'component_id': 'HB-CALLOUT-STRIP'},
                     'carrier_flow': [node('table', css='ht-anything', style='color:red')]}
        self.assertEqual(self.issues(component), [])

    def test_a_table_outside_components_needs_a_declared_reason(self):
        self.assertTrue(any('table outside a shared component' in i for i in self.issues(TABLE)))
        row = {'language': 'xx', 'page_id': 'page-1', 'kind': 'table',
               'text_sha256': table_text_sha256(TABLE), 'reason': 'no shared component fits'}
        self.assertEqual(self.issues(TABLE, exceptions=[row]), [])
        with self.assertRaisesRegex(ValueError, 'needs a reason'):
            self.issues(TABLE, exceptions=[{**row, 'reason': ' '}])
        stale = self.issues(node('paragraph', [text('x')]), exceptions=[row])
        self.assertTrue(any('does not occur' in issue for issue in stale))

    def test_source_stylesheet_is_geometry_only(self):
        self.assertEqual(paint_properties('/* color: red */ .x { font-size: 2cqw; white-space: nowrap; }'), [])
        self.assertEqual(sorted(paint_properties('.x{background:#eee;border-radius:3px} .y{color:var(--a)}')),
                         ['background', 'border-radius', 'color'])
        issues = self.issues(node('paragraph', [text('x')]), stylesheet='.x { background-color: #eee; }')
        self.assertTrue(any('background-color is paint' in issue for issue in issues))


class RepositoryGateTests(unittest.TestCase):
    def test_every_prepared_locale_passes_or_is_an_unchanged_baseline_entry(self):
        baseline = {(row['web_root'], row['ir_content_sha256']) for row in load_baseline()['entries']}
        failures = []
        for web_root, raw in prepared_locales():
            if (str(web_root.relative_to(ROOT)), raw['content_sha256']) in baseline:
                continue
            report = audit_prepared_package_locale(web_root.parent.parent, web_root, manifest_of(web_root))
            if report['issues']:
                failures.append(f"{web_root.relative_to(ROOT)}: {report['issues'][:3]}")
        self.assertEqual(failures, [], 'source-drawn styles in a prepared-document package')

    def test_baseline_only_shrinks_and_every_entry_still_fails(self):
        entries = load_baseline()['entries']
        self.assertLessEqual(len(entries), BASELINE_LIMIT)
        self.assertEqual(len({row['web_root'] for row in entries}), len(entries))
        locales = {str(web_root.relative_to(ROOT)): (web_root, raw) for web_root, raw in prepared_locales()}
        for row in entries:
            with self.subTest(web_root=row['web_root']):
                self.assertIn(row['web_root'], locales, 'stale baseline entry: remove it')
                web_root, raw = locales[row['web_root']]
                self.assertEqual(raw['content_sha256'], row['ir_content_sha256'],
                                 're-frozen locale left the baseline: it must pass the gate')
                report = audit_prepared_package_locale(web_root.parent.parent, web_root, manifest_of(web_root))
                self.assertTrue(report['issues'], 'locale now passes: remove its baseline entry')

    def test_the_released_source_drawn_edition_is_caught(self):
        web_root = ROOT / RELEASED_SOURCE_DRAWN
        report = audit_prepared_package_locale(web_root.parent.parent, web_root, manifest_of(web_root))
        self.assertTrue(any("'ht-signal-table'" in issue for issue in report['issues']))
        self.assertTrue(any('table outside a shared component' in issue for issue in report['issues']))


class SealGateTests(unittest.TestCase):
    def test_seal_rejects_a_new_source_drawn_locale_and_admits_baseline_and_clean(self):
        with tempfile.TemporaryDirectory() as temp:
            web = Path(temp) / 'pkg' / 'web' / 'xx'
            web.mkdir(parents=True)
            raw = {**ir(node('paragraph', [text('x')], css='ht-cell')), 'content_sha256': 'f' * 64,
                   'metadata': {}}
            (web / PathSegments.MANUAL_IR_JSON).write_text(json.dumps(raw), encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'shared style admission failed'):
                require_prepared_style_admission(web, {})
            raw['pages'][0]['blocks'][0]['payload'] = node('paragraph', [text('x')])
            (web / PathSegments.MANUAL_IR_JSON).write_text(json.dumps(raw), encoding='utf-8')
            self.assertEqual(require_prepared_style_admission(web, {})['issues'], [])
        released = ROOT / RELEASED_SOURCE_DRAWN
        self.assertTrue(require_prepared_style_admission(released, manifest_of(released))['baseline'])


if __name__ == '__main__':
    unittest.main()
