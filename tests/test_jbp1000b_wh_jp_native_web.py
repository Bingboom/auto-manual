"""Source fidelity, independent admission and offline replay of the JP pack."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.manual_ir.hashing import file_sha256
from tools.web.frozen_ai_web import replay_package
from tools.utils.path_utils import PathSegments

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'manual_sources/JBP-1000B-WH/JP/ja/git-20261008-3aa6c003-native'
SOURCE_SHA = '3aa6c0039b413716274089e5335dc2ce5853264dca4d7b0a6e5e110b6b0b302c'
CHAPTERS = [
    'preface', 'safety', 'symbols', 'in_the_box', 'product_overview',
    'lcd_display', 'operations', 'placement', 'stand', 'wall_wood',
    'wall_concrete', 'connection', 'charging', 'troubleshooting',
    'specifications', 'warranty', 'contact',
]
module_spec = importlib.util.spec_from_file_location('jp_pack_rebuild', PACKAGE / 'rebuild.py')
assert module_spec and module_spec.loader
rebuild_module = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(rebuild_module)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def reseal_fixture(source):
    manifest_path = source / 'source_manifest.json'
    manifest = read(manifest_path)
    for record in manifest['inputs']:
        path = source / record['path']
        record.update(sha256=file_sha256(path), size=path.stat().st_size)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')


class NativePackWebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self):
        dest = self.root / 'source'
        shutil.copytree(PACKAGE, dest, ignore=shutil.ignore_patterns('web', 'evidence', '__pycache__', '*.pdf'))
        return dest

    def test_exact_source_and_native_applicability(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        doc = read(PACKAGE / 'source/document.json')
        policy = read(PACKAGE / 'source/admission.json')
        self.assertEqual(manifest['original_source']['sha256'], SOURCE_SHA)
        self.assertEqual(doc['target'], {'model': 'JBP-1000B-WH', 'region': 'JP', 'language': 'ja'})
        self.assertEqual([p['page_id'] for p in doc['pages']], CHAPTERS)
        self.assertEqual(policy['expected_pages'], CHAPTERS)
        self.assertEqual(policy['legacy_debt'], [])
        self.assertEqual(manifest['publication_status'], 'operator-approved-git-only-release')

    def test_cold_rebuild_without_pdf_is_deterministic(self):
        source = self.fixture()
        self.assertFalse(list(source.rglob('*.pdf')))
        a, b = self.root / 'a', self.root / 'b'
        report = rebuild_module.rebuild(source, a)
        rebuild_module.rebuild(source, b)
        self.assertEqual(report['issues'], [])
        files = {str(p.relative_to(a)): file_sha256(p) for p in a.rglob('*') if p.is_file()}
        self.assertEqual(files, {str(p.relative_to(b)): file_sha256(p) for p in b.rglob('*') if p.is_file()})
        frozen = PACKAGE / 'web/ja'
        self.assertEqual(files, {str(p.relative_to(frozen)): file_sha256(p) for p in frozen.rglob('*') if p.is_file()})
        before = (a / 'manual_jbp1000bwh_jp_ja.md').read_bytes()
        replay_package(a)
        self.assertEqual(before, (a / 'manual_jbp1000bwh_jp_ja.md').read_bytes())
        ir = read(a / PathSegments.MANUAL_IR_JSON)
        self.assertTrue(ir['metadata']['publication_eligible'])
        self.assertEqual(ir['metadata']['pending_source_review'], [])
        self.assertEqual(ir['metadata']['operator_source_acceptance']['operator_quote'], '上线提交发布')

    def test_acceptance_cannot_cover_resealed_changed_source(self):
        source = self.fixture()
        (source / 'source/presentation.css').write_text('body { color: red; }')
        reseal_fixture(source)
        with self.assertRaisesRegex(ValueError, 'operator acceptance does not cover'):
            rebuild_module.rebuild(source, self.root / 'output')
        self.assertFalse((self.root / 'output').exists())

    def test_text_and_art_tampering_rejected_before_output(self):
        for relative in ['source/document.json', 'source/assets/overview.png']:
            with self.subTest(relative=relative):
                source = self.fixture()
                path = source / relative
                path.write_bytes(path.read_bytes() + b' ')
                out = self.root / 'output'
                with self.assertRaisesRegex(ValueError, 'frozen source input changed'):
                    rebuild_module.rebuild(source, out)
                self.assertFalse(out.exists())
                shutil.rmtree(source)

    def test_unlisted_asset_is_rejected_before_output(self):
        source = self.fixture()
        (source / 'source/assets/unlisted.svg').write_text('<svg />')
        output = self.root / 'output'
        with self.assertRaisesRegex(ValueError, 'manifest does not cover every input'):
            rebuild_module.rebuild(source, output)
        self.assertFalse(output.exists())

    def test_identity_mismatch_is_rejected_after_reseal(self):
        source = self.fixture()
        doc = read(source / 'source/document.json')
        doc['target']['model'] = 'JBP-2000B'
        (source / 'source/document.json').write_text(json.dumps(doc))
        reseal_fixture(source)
        with self.assertRaisesRegex(ValueError, 'source identity disagrees'):
            rebuild_module.rebuild(source, self.root / 'output')

    def test_missing_installation_step_fails_independent_admission(self):
        source = self.fixture()
        manifest = read(source / 'source_manifest.json')
        manifest['publication_status'] = 'review-candidate-no-release-authorization'
        (source / 'source_manifest.json').write_text(json.dumps(manifest))
        doc = read(source / 'source/document.json')
        chapter = next(p for p in doc['pages'] if p['page_id'] == 'wall_concrete')
        chapter['nodes'].pop()
        (source / 'source/document.json').write_text(json.dumps(doc))
        reseal_fixture(source)
        with self.assertRaisesRegex(ValueError, 'shared source admission failed'):
            rebuild_module.rebuild(source, self.root / 'output')

    def test_source_anomalies_and_visible_layer_are_preserved(self):
        doc = read(PACKAGE / 'source/document.json')
        out = self.root / 'web'
        rebuild_module.rebuild(PACKAGE, out)
        body = (out / 'manual_jbp1000bwh_jp_ja.md').read_text()
        for value in ['Jackery SlimPower H1は充電状態', '-20°C～45°C', '入力/出カポート', 'LiFePO₄', '20Ah / 51.2Vdc (1024 Wh)']:
            self.assertIn(value, body)
        self.assertNotIn('WARNING Ensure all products', body)
        operation = next(p for p in doc['pages'] if p['page_id'] == 'operations')
        spec = next(n['component_spec'] for n in operation['nodes'] if n.get('component_spec', {}).get('component_id') == 'HB-SPECIAL-OPERATION')
        steps = next(s['content'] for s in spec['slots'] if s['role'] == 'steps')
        self.assertEqual([(s['parts'][0]['text'], s['parts'][1]['text']) for s in steps], [('オフ', '1回押す'), ('オン', '3秒')])

    def test_shared_assets_are_byte_identical_and_native_marks_retained(self):
        for entry in read(PACKAGE / 'source/reuse.json').values():
            origin = ROOT / entry['source_path']
            if origin.is_file():
                self.assertEqual(file_sha256(origin), entry['sha256'])
                self.assertEqual((PACKAGE / 'source' / entry['path']).read_bytes(), origin.read_bytes())
        native = read(PACKAGE / 'source/native_icon_recipe.json')
        self.assertEqual({r['slug'] for r in native}, {'charge', 'ring', 'dc', 'error', 'li_ion', 'connected-batteries'})
