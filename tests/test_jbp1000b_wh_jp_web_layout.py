"""Web-layout candidate of the JP pack: print structure, unchanged copy and replay."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.manual_ir.hashing import file_sha256
from tools.utils.path_utils import PathSegments
from tools.web.frozen_ai_web import replay_package

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'manual_sources/JBP-1000B-WH/JP/ja/git-20261009-3aa6c003-web-layout'
NATIVE = ROOT / 'manual_sources/JBP-1000B-WH/JP/ja/git-20261008-3aa6c003-native'
SOURCE_SHA = '3aa6c0039b413716274089e5335dc2ce5853264dca4d7b0a6e5e110b6b0b302c'
MARKDOWN = 'manual_jbp1000bwh_jp_ja.md'
CHAPTERS = [
    'safety', 'symbols', 'in_the_box', 'product_overview', 'lcd_display', 'operations',
    'placement', 'stand', 'wall_wood', 'wall_concrete', 'connection', 'charging',
    'troubleshooting', 'specifications', 'warranty', 'contact',
]
# The printed table of contents (physical page 2) lists exactly these chapters.
PRINT_TOC = [
    '使用上のご注意', '同梱品', '各部の名称', '液晶画面', '製品の使用方法について',
    'Jackery Battery Pack と 本体の設置方法', '縦置', 'ポータブル電源との併用', '充電方法',
    'トラブルシューティング', '主な仕様', '保証について',
]
PAIRS = {
    'wood-3-4': ('wood-3', 'wood-4'),
    'concrete-4-5': ('concrete-4', 'concrete-5'),
    'concrete-6-7': ('concrete-6', 'concrete-7'),
    'concrete-8-9': ('concrete-8', 'concrete-9'),
}
module_spec = importlib.util.spec_from_file_location('jp_layout_rebuild', PACKAGE / 'rebuild.py')
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


def visible_characters(markdown: str) -> Counter:
    soup = BeautifulSoup(markdown, 'html.parser')
    for style in soup.find_all('style'):
        style.decompose()
    return Counter(''.join(soup.get_text('').replace('#', '').split()))


def headings(markdown: str):
    return [(len(m.group(1)), m.group(2)) for m in re.finditer(r'^(#+) (.+)$', markdown, re.M)]


class WebLayoutCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self):
        dest = self.root / 'source'
        shutil.copytree(PACKAGE, dest, ignore=shutil.ignore_patterns('web', '__pycache__', '*.pdf'))
        return dest

    def test_candidate_identity_status_and_applicability(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        doc = read(PACKAGE / 'source/document.json')
        policy = read(PACKAGE / 'source/admission.json')
        self.assertEqual(manifest['original_source']['sha256'], SOURCE_SHA)
        self.assertEqual(manifest['target']['technical_version'], PACKAGE.name)
        self.assertEqual(manifest['publication_status'], 'review-candidate-no-release-authorization')
        self.assertFalse((PACKAGE / 'source/approval.json').exists())
        self.assertEqual(doc['target'], {'model': 'JBP-1000B-WH', 'region': 'JP', 'language': 'ja'})
        self.assertEqual([p['page_id'] for p in doc['pages']], CHAPTERS)
        self.assertEqual(policy['expected_pages'], CHAPTERS)
        self.assertEqual(policy['legacy_debt'], [])

    def test_cold_rebuild_matches_frozen_candidate_and_stays_unpublishable(self):
        source = self.fixture()
        a, b = self.root / 'a', self.root / 'b'
        report = rebuild_module.rebuild(source, a)
        rebuild_module.rebuild(source, b)
        self.assertEqual(report['issues'], [])
        files = {str(p.relative_to(a)): file_sha256(p) for p in a.rglob('*') if p.is_file()}
        self.assertEqual(files, {str(p.relative_to(b)): file_sha256(p) for p in b.rglob('*') if p.is_file()})
        frozen = PACKAGE / 'web/ja'
        self.assertEqual(files, {str(p.relative_to(frozen)): file_sha256(p) for p in frozen.rglob('*') if p.is_file()})
        before = (a / MARKDOWN).read_bytes()
        replay_package(a)
        self.assertEqual(before, (a / MARKDOWN).read_bytes())
        metadata = read(a / PathSegments.MANUAL_IR_JSON)['metadata']
        self.assertFalse(metadata['publication_eligible'])
        self.assertTrue(metadata['pending_source_review'])
        self.assertIsNone(metadata['operator_source_acceptance'])

    def test_tampering_and_unlisted_inputs_are_rejected_before_output(self):
        for relative in ['source/document.json', 'source/assets/concrete-4-5.png', 'source/presentation.css']:
            with self.subTest(relative=relative):
                source = self.fixture()
                path = source / relative
                path.write_bytes(path.read_bytes() + b' ')
                out = self.root / 'output'
                with self.assertRaisesRegex(ValueError, 'frozen source input changed'):
                    rebuild_module.rebuild(source, out)
                self.assertFalse(out.exists())
                shutil.rmtree(source)
        source = self.fixture()
        (source / 'source/assets/unlisted.svg').write_text('<svg />')
        with self.assertRaisesRegex(ValueError, 'manifest does not cover every input'):
            rebuild_module.rebuild(source, self.root / 'output')

    def test_missing_installation_row_fails_independent_admission(self):
        source = self.fixture()
        doc = read(source / 'source/document.json')
        chapter = next(p for p in doc['pages'] if p['page_id'] == 'wall_concrete')
        chapter['nodes'].pop()
        (source / 'source/document.json').write_text(json.dumps(doc, ensure_ascii=False))
        reseal_fixture(source)
        with self.assertRaisesRegex(ValueError, 'shared source admission failed'):
            rebuild_module.rebuild(source, self.root / 'output')

    def test_navigation_follows_the_print_table_of_contents(self):
        markdown = (PACKAGE / 'web/ja' / MARKDOWN).read_text(encoding='utf-8')
        found = headings(markdown)
        self.assertEqual([title for level, title in found if level == 1], PRINT_TOC)
        self.assertEqual(found[0], (1, '使用上のご注意'))  # no printed cover in the Web edition
        nested = {title: [] for title in PRINT_TOC}
        chapter = None
        for level, title in found:
            if level == 1:
                chapter = title
            else:
                nested[chapter].append(title)
        self.assertEqual(nested['使用上のご注意'], ['絵表示について', '絵表示の説明'])
        self.assertEqual(nested['縦置'], ['木製の壁の場合。', 'コンクリート壁面の場合'])
        self.assertEqual(nested['主な仕様'], ['基本情報', '入力/出カポート', '温度範囲'])
        self.assertEqual(nested['保証について'][-1], '免責事項')
        self.assertNotIn('お問い合わせ', [title for _, title in found])
        self.assertIn('<p class="jbp-contact-line"><strong>カスタマーサポート:</strong>', markdown)

    def test_visible_copy_is_the_approved_copy_without_cover(self):
        native = (NATIVE / 'web/ja' / MARKDOWN).read_text(encoding='utf-8')
        candidate = (PACKAGE / 'web/ja' / MARKDOWN).read_text(encoding='utf-8')
        cover = next(p for p in read(NATIVE / 'source/document.json')['pages'] if p['page_id'] == 'preface')

        def texts(node):
            if node.get('kind') == 'text':
                yield node['text']
            for child in node.get('children', []):
                yield from texts(child)

        removed = Counter(''.join(''.join(t for n in cover['nodes'] for t in texts(n)).split()))
        removed.update('お問い合わせ')  # the contact lines no longer carry their own heading
        specs = [n['component_spec'] for p in read(NATIVE / 'source/document.json')['pages']
                 for n in p['nodes'] if n['kind'] == 'component']
        signal = next(s for s in specs if s['component_id'] == 'HB-TABLE-SYMBOL-SIGNAL')
        signal_rows = next(s['content'] for s in signal['slots'] if s['role'] == 'rows')
        removed.update('⚠' * sum(row['show_icon'] for row in signal_rows))  # print words carry no pictogram
        lcd = next(s for s in specs if s['component_id'] == 'HB-TABLE-LCD-ICON')
        rows = next(s['content'] for s in lcd['slots'] if s['role'] == 'rows')
        for previous, row in zip(rows, rows[1:], strict=False):  # print merges equal adjacent descriptions
            if (previous['number_text'], previous['description_text']) == (row['number_text'], row['description_text']):
                removed.update(''.join(row['description_text'].split()))
        self.assertEqual(visible_characters(candidate), visible_characters(native) - removed)

    def test_print_rows_are_union_crops_of_the_approved_panels(self):
        native_recipe = {a['asset_key'].rsplit('/', 1)[-1]: a for a in read(NATIVE / 'source/asset_recipe.json')['assets']}
        recipe = {a['asset_key'].rsplit('/', 1)[-1]: a for a in read(PACKAGE / 'source/asset_recipe.json')['assets']}
        figures = {f['slug']: f for f in read(PACKAGE / 'source/figures.json')}
        native_figures = {f['slug']: f for f in read(NATIVE / 'source/figures.json')}
        for merged, (left, right) in PAIRS.items():
            with self.subTest(merged=merged):
                crops = [native_recipe[s]['transforms'][0]['bbox_pt'] for s in (left, right)]
                union = [min(c[0] for c in crops), min(c[1] for c in crops), max(c[2] for c in crops), max(c[3] for c in crops)]
                self.assertEqual(recipe[merged]['transforms'][0], {'op': 'crop', 'bbox_pt': union})
                redactions = [t for s in (left, right) for t in native_recipe[s]['transforms'][1:]]
                self.assertEqual(recipe[merged]['transforms'][1:], redactions)
                self.assertNotIn(left, recipe)
                self.assertNotIn(right, recipe)
                printed = ''.join(c['text'] for s in (left, right) for c in native_figures[s]['live_captions'])
                self.assertEqual(''.join(c['text'] for c in figures[merged]['live_captions']).replace(' ', ''),
                                 printed.replace(' ', ''))
                self.assertEqual(figures[merged]['sha256'], file_sha256(PACKAGE / f'source/assets/{merged}.png'))
        self.assertNotIn('cover-unit', recipe)
        self.assertEqual(set(recipe), set(figures))

    def test_unchanged_art_and_shared_marks_are_byte_identical(self):
        obsolete = {'cover-unit', *(s for pair in PAIRS.values() for s in pair)}
        for art in (NATIVE / 'source/assets').iterdir():
            if art.stem not in obsolete:
                self.assertEqual((PACKAGE / 'source/assets' / art.name).read_bytes(), art.read_bytes(), art.name)
        for entry in read(PACKAGE / 'source/reuse.json').values():
            origin = ROOT / entry['source_path']
            if origin.is_file():
                self.assertEqual(file_sha256(origin), entry['sha256'])
        self.assertEqual(read(PACKAGE / 'source_manifest.json')['symbol_asset_admission'],
                         read(NATIVE / 'source_manifest.json')['symbol_asset_admission'])

    def test_recipe_reproduces_every_packaged_art_file(self):
        try:
            import pymupdf
        except ImportError:  # pragma: no cover - repository dependency
            self.skipTest('PyMuPDF unavailable')
        if tuple(pymupdf.version[:2]) != ('1.28.0', '1.29.0'):
            self.skipTest('asset recipe is validated for PyMuPDF 1.28.0 / MuPDF 1.29.0 (requirements.lock)')
        from tools.asset_pipeline.extract import extract_artifacts
        from tools.asset_pipeline.recipe import load_recipe

        out = self.root / 'render'
        extract_artifacts(next(PACKAGE.glob('*.pdf')), load_recipe(PACKAGE / 'source/asset_recipe.json'), out)
        rendered = {p.name: p.read_bytes() for p in (out / 'assets').iterdir()}
        figures = read(PACKAGE / 'source/figures.json')
        self.assertEqual(set(rendered), {next((PACKAGE / 'source/assets').glob(f"{f['slug']}.*")).name for f in figures})
        for name, data in rendered.items():
            self.assertEqual((PACKAGE / 'source/assets' / name).read_bytes(), data, name)


if __name__ == '__main__':
    unittest.main()
