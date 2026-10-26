"""JS-CONNECTION-GUIDE JP connection guide Git-only Web package: frozen inputs, verbatim copy and replay."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.manual_ir.hashing import file_sha256
from tools.word.bundle_docx_pandoc import resolve_pandoc_binary

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'manual_sources/JS-CONNECTION-GUIDE/JP/ja/git-20261026-bc35fd65-connection-guide'
SOURCE_SHA = 'bc35fd6518769bd26c88fee088cc3a748c0ef680f4419682bede0f62738f8821'
MARKDOWN = 'manual_jsconnectionguide_jp_ja.md'
# The Japanese face prints one heading, kept verbatim (「Genarator」 is a source concern).
CHAPTERS = ['Jackery Solar Genarator 接続ガイド']


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render_module = load('js_connection_guide_jp_render', PACKAGE / 'render.py')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def visible_text(markdown: str) -> str:
    soup = BeautifulSoup(markdown, 'html.parser')
    for node in soup.find_all(['style', 'script']):
        node.decompose()
    return soup.get_text('\n')


class JSConnectionGuideJPWebTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def fixture(self) -> Path:
        source = self.root / 'package'
        shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns('web', 'evidence', '__pycache__'))
        return source

    def test_identity_and_original_source(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['target']['model'], 'JS-CONNECTION-GUIDE')
        self.assertEqual(manifest['target']['region'], 'JP')
        self.assertEqual(manifest['target']['languages'], ['ja'])
        self.assertEqual(manifest['original_source']['sha256'], SOURCE_SHA)
        self.assertEqual(manifest['identity']['part_number'], '38-0001-000716')
        self.assertEqual(manifest['target']['technical_version'], 'git-20261026-bc35fd65')
        self.assertEqual(manifest['route']['route'], 'JS-CONNECTION-GUIDE/JP/ja/md')
        self.assertEqual(file_sha256(PACKAGE / 'source/original.pdf'), SOURCE_SHA)
        self.assertIsNone(manifest['printed_manual_version'])
        self.assertFalse(manifest['live_bitable_dependency'])
        if manifest['publication_status'] == render_module.CANDIDATE:
            self.assertFalse(manifest['publication_eligible'])
            self.assertFalse((PACKAGE / 'source/approval.json').exists())
        else:
            self.assertEqual(manifest['publication_status'], render_module.APPROVED)
            self.assertTrue(manifest['publication_eligible'])
            self.assertIsNotNone(render_module.acceptance(PACKAGE, manifest))

    def test_release_manifest_inventories_every_package_file(self):
        release = read(PACKAGE / 'frozen_source_manifest.json')
        files = sorted(p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*')
                       if p.is_file() and '__pycache__' not in p.parts and p.name != 'frozen_source_manifest.json')
        self.assertEqual([r['path'] for r in release['inputs']], files)
        for record in release['inputs']:
            self.assertEqual(file_sha256(PACKAGE / record['path']), record['sha256'], record['path'])
        reviewed = read(PACKAGE / 'source_manifest.json')
        self.assertEqual({k: v for k, v in release.items() if k != 'inputs'},
                         {k: v for k, v in reviewed.items() if k != 'inputs'})

    def test_artwork_decisions_bind_every_asset(self):
        decisions = read(PACKAGE / 'source/asset_decisions.json')['extractions']
        assets = sorted(p.relative_to(PACKAGE).as_posix() for p in (PACKAGE / 'assets').iterdir())
        self.assertEqual(sorted(r['path'] for r in decisions), assets)
        for record in decisions:
            self.assertEqual(file_sha256(PACKAGE / record['path']), record['sha256'], record['path'])

    def test_navigation_is_the_single_print_heading(self):
        markdown = (PACKAGE / 'web/ja' / MARKDOWN).read_text(encoding='utf-8')
        self.assertEqual(re.findall(r'^#+ (.+)$', markdown, re.M), CHAPTERS)

    def test_only_the_japanese_face_is_on_the_web(self):
        text = visible_text((PACKAGE / 'web/ja' / MARKDOWN).read_text(encoding='utf-8'))
        for foreign in ('Connection Guide', 'Guide de connexion', 'Guía de conexión', 'Guia de conexão',
                        '38-0001-000716', '深圳市华宝新能源'):
            self.assertNotIn(foreign, text)
        excluded = [line for line in read(PACKAGE / 'source/transcription.json')['lines']
                    if line['disposition'] == 'web-excluded']
        self.assertTrue(any(line['panel'] == 'international' for line in excluded))
        self.assertTrue(all(line.get('reason') for line in excluded))

    def test_compatibility_table_is_native_text(self):
        soup = BeautifulSoup((PACKAGE / 'web/ja' / MARKDOWN).read_text(encoding='utf-8'), 'html.parser')
        (table,) = soup.find_all('table')
        rows = table.find_all('tr')
        self.assertEqual([cell.get_text(strip=True) for cell in rows[0].find_all('th')],
                         ['ポータブル電源の型番', 'DC入力'])
        ports = [row.find_all('td')[1] for row in rows[1:]]
        self.assertEqual([cell.find('strong').get_text() for cell in ports], ['USB-C', 'DC7909', 'DC8020'])
        self.assertEqual([len(row.find_all(class_='line')) for row in rows[1:]], [3, 5, 11])
        self.assertEqual([cell.img['src'].rsplit('/', 1)[-1] for cell in ports],
                         ['port-usb-c.png', 'port-dc7909.png', 'port-dc8020.png'])
        exceptions = read(PACKAGE / 'source_manifest.json')['shared_component_exceptions']
        self.assertEqual([(row['kind'], row['page_id']) for row in exceptions], [('table', '01_connection_guide_ja.rst')])

    def test_figure_labels_bind_the_extracted_art(self):
        markdown = (PACKAGE / 'web/ja' / MARKDOWN).read_text(encoding='utf-8')
        soup = BeautifulSoup(markdown, 'html.parser')
        decisions = {r['path'].rsplit('/', 1)[-1]: r for r in read(PACKAGE / 'source/asset_decisions.json')['extractions']}
        figures = soup.find_all('figure', attrs={'data-component-id': 'HB-SPECIAL-REFERENCE-FIGURE'})
        self.assertEqual([f['data-reference-id'] for f in figures], ['connection-dc7909', 'connection-dc8020'])
        for figure in figures:
            name = figure['data-reference-id'] + '.png'
            spec = json.loads(figure.img['data-reference'])
            self.assertEqual(spec['base_art_layout']['art_sha256'], decisions[name]['sha256'])
            labels = [span.get_text() for span in figure.find_all(class_='hb-reference-live-label')]
            self.assertEqual(labels, [label['text'] for label in decisions[name]['live_labels']])

    def test_live_copy_is_the_transcribed_print_in_reading_order(self):
        text = visible_text((PACKAGE / 'web/ja' / MARKDOWN).read_text(encoding='utf-8'))
        transcription = read(PACKAGE / 'source/transcription.json')
        self.assertEqual(transcription['source_sha256'], SOURCE_SHA)
        position = 0
        for line in transcription['lines']:
            if line['disposition'] != 'live':
                continue
            found = text.find(line['text'], position)
            self.assertGreaterEqual(found, 0, f"{line['text']!r} missing after offset {position}")
            position = found + len(line['text'])

    def test_in_art_copy_stays_in_the_listed_artwork(self):
        markdown = (PACKAGE / 'web/ja' / MARKDOWN).read_text(encoding='utf-8')
        soup = BeautifulSoup(markdown, 'html.parser')
        assets = {r['path'] for r in read(PACKAGE / 'source/asset_decisions.json')['extractions']}
        figure_text = '\n'.join(f.get_text('\n') for f in soup.find_all('figure'))
        for line in read(PACKAGE / 'source/transcription.json')['lines']:
            if line['disposition'] == 'in-art':
                self.assertIn(line['asset'], assets)
                self.assertNotIn(line['text'], figure_text.split('\n'))

    def test_changed_or_unlisted_inputs_are_rejected_before_output(self):
        for relative in ['source/page/01_connection_guide_ja.rst', 'source/presentation.css', 'assets/connection-dc7909.png']:
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
        manifest = read(source / 'source_manifest.json')
        if manifest['publication_status'] != render_module.APPROVED:
            self.skipTest('edition not yet accepted')
        css = source / 'source/presentation.css'
        css.write_text(css.read_text(encoding='utf-8') + '\n#x { width: 1rem; }\n', encoding='utf-8')
        for record in manifest['inputs']:
            path = source / record['path']
            record.update(sha256=file_sha256(path), size=path.stat().st_size)
        (source / 'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'operator acceptance does not cover'):
            render_module.render(source, self.root / 'out')
        self.assertFalse((self.root / 'out').exists())

    def test_cold_render_matches_committed_web(self):
        # The prepared RST pipeline converts through Pandoc; the CI unit runner has none.
        try:
            subprocess.run([resolve_pandoc_binary(None), '--version'], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest('Pandoc unavailable')
        source = self.fixture()
        out = self.root / 'out'
        report = render_module.render(source, out)
        files = {str(p.relative_to(out)): file_sha256(p) for p in out.rglob('*') if p.is_file()}
        frozen = PACKAGE / 'web/ja'
        self.assertEqual(files, {str(p.relative_to(frozen)): file_sha256(p) for p in frozen.rglob('*') if p.is_file()})
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(report['publication_eligible'], manifest['publication_eligible'])


if __name__ == '__main__':
    unittest.main()
