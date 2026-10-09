"""Web-layout edition of the JA-AD500A-SIL JP manual: print layout, unchanged copy and replay."""
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

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'manual_sources/JA-AD500A-SIL/JP/ja/git-20261009-ac3a1f82-web-layout'
REVIEWED = ROOT / 'manual_sources/JA-AD500A-SIL/JP/ja/git-20261008-ac3a1f82-reviewed'
SOURCE_SHA = 'ac3a1f820d94277f6c1a667bafddfa930363b1d74fb084eb7bed43b1c3749777'
MARKDOWN = 'manual_jaad500asil_jp_ja.md'
# The print chapters (dark bars) of the PDF; the cover has no Web chapter.
CHAPTERS = ['同梱品', '各部の名称', '接続', '主な仕様', '保証について']


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render_module = load('jaad500a_jp_layout_render', PACKAGE / 'render.py')
derive_module = load('jaad500a_jp_layout_derive', PACKAGE / 'derive_web_layout.py')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def visible_characters(markdown: str) -> Counter:
    soup = BeautifulSoup(markdown, 'html.parser')
    for style in soup.find_all('style'):
        style.decompose()
    return Counter(''.join(soup.get_text('').replace('#', '').split()))


def reseal(source: Path) -> None:
    path = source / 'source_manifest.json'
    manifest = read(path)
    for record in manifest['inputs']:
        file = source / record['path']
        record.update(sha256=file_sha256(file), size=file.stat().st_size)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


class WebLayoutEditionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self):
        dest = self.root / 'source'
        shutil.copytree(PACKAGE, dest, ignore=shutil.ignore_patterns('web', 'evidence', '__pycache__'))
        return dest

    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['original_source']['sha256'], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / 'source/original.pdf'), SOURCE_SHA)
        self.assertEqual(manifest['target']['technical_version'], PACKAGE.name)
        self.assertEqual(manifest['derived_from']['package'], REVIEWED.name)
        self.assertEqual(manifest['derived_from']['manifest_sha256'], file_sha256(REVIEWED / 'source_manifest.json'))
        if manifest['publication_status'] == render_module.CANDIDATE:
            self.assertFalse(manifest['publication_eligible'])
            self.assertFalse((PACKAGE / 'source/approval.json').exists())
        else:
            approval = read(PACKAGE / 'source/approval.json')
            self.assertEqual(approval['operator_quote'], '上线提交发布')
            self.assertEqual(manifest['publication_status'], render_module.APPROVED)
            self.assertTrue(manifest['publication_eligible'])
            self.assertEqual(approval['target'], {'model': 'JA-AD500A-SIL', 'region': 'JP', 'language': 'ja'})
            self.assertEqual(approval['reviewed_inputs'], [
                r for r in manifest['inputs']
                if r['path'].startswith(('source/', 'assets/')) and r['path'] != 'source/approval.json'])

    def test_derivation_is_reproducible(self):
        before = {p: file_sha256(p) for p in PACKAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        derive_module.main()
        after = {p: file_sha256(p) for p in PACKAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.assertEqual(before, after)

    def test_artwork_is_the_approved_artwork_except_the_inbox_manual_recrop(self):
        for art in (REVIEWED / 'assets').iterdir():
            mine = PACKAGE / 'assets' / art.name
            if art.name == 'inbox-manual.png':
                self.assertNotEqual(file_sha256(mine), file_sha256(art))
                self.assertEqual(file_sha256(mine), derive_module.INBOX_MANUAL['sha256'])
            else:
                self.assertEqual(mine.read_bytes(), art.read_bytes(), art.name)

    def test_cold_render_matches_committed_web(self):
        source = self.fixture()
        a, b = self.root / 'a', self.root / 'b'
        report = render_module.render(source, a)
        render_module.render(source, b)
        files = {str(p.relative_to(a)): file_sha256(p) for p in a.rglob('*') if p.is_file()}
        self.assertEqual(files, {str(p.relative_to(b)): file_sha256(p) for p in b.rglob('*') if p.is_file()})
        frozen = PACKAGE / 'web/ja'
        self.assertEqual(files, {str(p.relative_to(frozen)): file_sha256(p) for p in frozen.rglob('*') if p.is_file()})
        metadata = read(a / 'manual.ir.json')['metadata']
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(report['publication_eligible'], manifest['publication_eligible'])
        self.assertEqual(metadata['publication_eligible'], manifest['publication_eligible'])
        self.assertEqual(metadata['source_stylesheet']['sha256'], file_sha256(PACKAGE / 'source/presentation.css'))

    def test_changed_or_unlisted_inputs_are_rejected_before_output(self):
        for relative in ['source/page/warranty_ja.rst', 'source/presentation.css', 'assets/solar.png']:
            with self.subTest(relative=relative):
                source = self.fixture()
                path = source / relative
                path.write_bytes(path.read_bytes() + b' ')
                with self.assertRaisesRegex(ValueError, 'frozen source input changed'):
                    render_module.render(source, self.root / 'out')
                self.assertFalse((self.root / 'out').exists())
                shutil.rmtree(source)
        source = self.fixture()
        (source / 'source/page/extra.rst').write_text('x\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'manifest does not cover every input'):
            render_module.render(source, self.root / 'out')

    def test_candidate_cannot_carry_or_claim_acceptance(self):
        source = self.fixture()
        manifest = read(source / 'source_manifest.json')
        if manifest['publication_status'] != render_module.CANDIDATE:
            self.skipTest('edition already accepted')
        manifest['publication_eligible'] = True
        (source / 'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'carries no release acceptance'):
            render_module.render(source, self.root / 'out')

    def test_acceptance_cannot_cover_resealed_changed_source(self):
        source = self.fixture()
        if read(source / 'source_manifest.json')['publication_status'] != render_module.APPROVED:
            self.skipTest('edition not yet accepted')
        css = source / 'source/presentation.css'
        css.write_text(css.read_text(encoding='utf-8') + '\nbody { color: red; }\n', encoding='utf-8')
        reseal(source)
        with self.assertRaisesRegex(ValueError, 'operator acceptance does not cover'):
            render_module.render(source, self.root / 'out')
        self.assertFalse((self.root / 'out').exists())

    def test_release_manifest_inventories_every_package_file(self):
        release = read(PACKAGE / 'frozen_source_manifest.json')
        files = sorted(p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*')
                       if p.is_file() and '__pycache__' not in p.parts and p.name != 'frozen_source_manifest.json')
        self.assertEqual([r['path'] for r in release['inputs']], files)
        for record in release['inputs']:
            self.assertEqual(file_sha256(PACKAGE / record['path']), record['sha256'], record['path'])
        self.assertEqual(release['web_roots'], {'ja': 'web/ja'})

    def test_navigation_is_the_print_chapters_without_cover(self):
        markdown = (PACKAGE / 'web/ja' / MARKDOWN).read_text(encoding='utf-8')
        top = re.findall(r'^# (.+)$', markdown, re.M)
        self.assertEqual(top, CHAPTERS)
        self.assertNotIn('取扱説明書\n', markdown.split('# 同梱品')[0])
        self.assertIn('<strong>お買い上げありがとうございます。</strong>', markdown)

    def test_visible_copy_is_the_approved_copy_without_cover(self):
        approved = (REVIEWED / 'web/ja' / MARKDOWN).read_text(encoding='utf-8')
        candidate = (PACKAGE / 'web/ja' / MARKDOWN).read_text(encoding='utf-8')
        removed = Counter(''.join(''.join(derive_module.COVER_LINES).split()))
        self.assertEqual(visible_characters(candidate), visible_characters(approved) - removed)
        # Order is kept too: the approved text minus the cover lines, in sequence.
        def flat(markdown):
            soup = BeautifulSoup(markdown, 'html.parser')
            for style in soup.find_all('style'):
                style.decompose()
            return ''.join(soup.get_text('').replace('#', '').split())
        expected = flat(approved)
        for line in derive_module.COVER_LINES:
            expected = expected.replace(''.join(line.split()), '', 1)
        self.assertEqual(flat(candidate), expected)


if __name__ == '__main__':
    unittest.main()
