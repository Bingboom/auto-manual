"""Solar-Voc correction editions of the JA-AD500A-SIL and SlimPower H1 JP manuals: one paragraph of copy, nothing else."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tests.historical_app_styles import pre_four_control_styles
from tools.manual_ir.hashing import file_sha256
from tools.word.bundle_docx_pandoc import resolve_pandoc_binary

ROOT = Path(__file__).resolve().parents[1]
AD500A = ROOT / 'manual_sources/JA-AD500A-SIL/JP/ja'
H1 = ROOT / 'manual_sources/JE-1000E-WH/JP/ja'
AD500A_PACKAGE = AD500A / 'git-20261016-ac3a1f82-solar-voc'
AD500A_BASE = AD500A / 'git-20261009-ac3a1f82-web-layout'
H1_PACKAGE = H1 / 'git-20261016-efb663e3-solar-voc'
H1_BASE = H1 / 'git-20261008-efb663e3-no-cover-reviewed'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ad500a_render = load('jaad500a_jp_voc_render', AD500A_PACKAGE / 'render.py')
ad500a_derive = load('jaad500a_jp_voc_derive', AD500A_PACKAGE / 'derive_solar_voc.py')
h1_rebuild = load('h1_jp_voc_rebuild', H1_PACKAGE / 'rebuild.py')
h1_derive = load('h1_jp_voc_derive', H1_PACKAGE / 'derive_solar_voc.py')

EDITIONS = {
    'ad500a': {'package': AD500A_PACKAGE, 'base': AD500A_BASE, 'derive': ad500a_derive,
               'markdown': 'manual_jaad500asil_jp_ja.md', 'status': ad500a_render},
    'h1': {'package': H1_PACKAGE, 'base': H1_BASE, 'derive': h1_derive,
           'markdown': 'manual.md', 'status': h1_rebuild},
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def tree(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): file_sha256(p) for p in root.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}


def rebuild_h1(source: Path, output: Path) -> None:
    # Invoke the same CLI main in-process so its historical stylesheet dependency
    # can be isolated without altering the immutable rebuild script.
    with mock.patch.object(sys, 'argv', [str(source / 'rebuild.py'), '--output', str(output)]):
        h1_rebuild.main()


def squeeze(text: str) -> str:
    return ''.join(text.split())


def visible_copy(ir_path: Path) -> str:
    """Every text node of the IR flow in reading order, whitespace removed."""
    def texts(node):
        if isinstance(node, dict):
            for name, value in node.items():
                if name == 'text' and isinstance(value, str):
                    yield value
                else:
                    yield from texts(value)
        elif isinstance(node, list):
            for item in node:
                yield from texts(item)
    raw = read(ir_path)
    return squeeze(''.join(t for page in raw['pages'] for block in page['blocks'] for t in texts(block['payload'])))


class JapaneseSolarVocEditionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, package: Path) -> Path:
        dest = self.root / 'source'
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(package, dest, ignore=shutil.ignore_patterns('web', 'evidence', '__pycache__'))
        return dest

    def test_identity_lineage_and_candidate_status(self):
        for key, edition in EDITIONS.items():
            with self.subTest(edition=key):
                package, base = edition['package'], edition['base']
                manifest = read(package / 'source_manifest.json')
                self.assertEqual(manifest['target']['technical_version'], package.name)
                self.assertEqual(manifest['original_source'], read(base / 'source_manifest.json')['original_source'])
                self.assertEqual(manifest['derived_from']['package'], base.name)
                self.assertEqual(manifest['derived_from']['manifest_sha256'], file_sha256(base / 'source_manifest.json'))
                status = edition['status']
                if manifest['publication_status'] == status.CANDIDATE:
                    self.assertFalse(manifest['publication_eligible'])
                    self.assertFalse((package / 'source/approval.json').exists())
                    self.assertTrue(manifest['pending_source_review'])
                else:
                    self.assertEqual(manifest['publication_status'], status.APPROVED)
                    self.assertTrue(manifest['publication_eligible'])
                    self.assertTrue(read(package / 'source/approval.json')['operator_quote'])

    def test_derivation_is_reproducible(self):
        for key, edition in EDITIONS.items():
            with self.subTest(edition=key):
                before = tree(edition['package'])
                edition['derive'].main()
                self.assertEqual(before, tree(edition['package']))

    def test_ad500a_only_the_declared_page_differs_from_the_base(self):
        base = {p: h for p, h in tree(AD500A_BASE).items() if p.startswith(('source/', 'assets/'))}
        mine = {p: h for p, h in tree(AD500A_PACKAGE).items() if p.startswith(('source/', 'assets/'))}
        # Both editions carry their own change record and acceptance; the base's are not copied.
        own = {'source/differences.md'} | ({'source/approval.json'} & set(mine))
        self.assertEqual(set(mine) - set(base), set())
        self.assertEqual(set(base) - set(mine), set(ad500a_derive.NOT_COPIED) - own)
        pages = {name for name, _, _ in ad500a_derive.CORRECTIONS} | set(ad500a_derive.STYLED_PAGES)
        changed = {f'source/page/{name}' for name in pages} | own | {'source/presentation.css'}
        for path in sorted(set(mine) - changed):
            self.assertEqual(mine[path], base[path], path)
        for name in sorted(pages):
            self.assertEqual((AD500A_PACKAGE / 'source/page' / name).read_text(encoding='utf-8'),
                             ad500a_derive.edited_page(name), name)
        self.assertEqual((AD500A_PACKAGE / 'source/presentation.css').read_text(encoding='utf-8'),
                         ad500a_derive.PRESENTATION_CSS)

    def test_h1_only_chapters_differ_from_the_base(self):
        copied = ('Jackery SlimPower H1', 'artwork/', 'asset_provenance.json', 'source/')
        base = {p: h for p, h in tree(H1_BASE).items() if p.startswith(copied)}
        mine = {p: h for p, h in tree(H1_PACKAGE).items() if p.startswith(copied)}
        self.assertEqual(set(mine) - set(base), {'source/differences.md'} | ({'source/approval.json'} & set(mine)))
        self.assertEqual(set(base) - set(mine), set())
        for path in sorted(set(base) - {'source/chapters.json'}):
            self.assertEqual(mine[path], base[path], path)
        (relative, old, new), = h1_derive.CORRECTIONS
        text = (H1_BASE / relative).read_text(encoding='utf-8')
        self.assertEqual(text.count(old), 1)
        self.assertEqual((H1_PACKAGE / relative).read_text(encoding='utf-8'), text.replace(old, new))

    def test_rendered_copy_is_the_base_copy_with_only_the_paragraph_replaced(self):
        for key, edition in EDITIONS.items():
            with self.subTest(edition=key):
                (_, old, new), = edition['derive'].CORRECTIONS
                base = (edition['base'] / 'web/ja' / edition['markdown']).read_text(encoding='utf-8')
                mine = (edition['package'] / 'web/ja' / edition['markdown']).read_text(encoding='utf-8')
                self.assertEqual(base.count(old), 1)
                if key == 'h1':
                    self.assertEqual(mine, base.replace(old, new))
                else:
                    # The AD500A edition is also restyled on shared classes (shared-style gate):
                    # its visible copy, not its markup, equals the base with the paragraph replaced.
                    self.assertEqual(visible_copy(edition['package'] / 'web/ja/manual.ir.json'),
                                     visible_copy(edition['base'] / 'web/ja/manual.ir.json').replace(
                                         squeeze(old), squeeze(new)))
                self.assertNotIn('36.8V', new)
                self.assertIn('16V～60V', new)
                # The contradicting opening accessory warning is dropped; the closing disclaimer stays.
                self.assertNotIn('Jackeryブランド以外の付属品を使用して充電しないでください。', mine)
                self.assertIn(new + '他社ソーラーパネルで充電することによる損失について、当社は一切の責任を負いません。', mine)

    @pre_four_control_styles
    def test_ad500a_cold_render_matches_committed_web(self):
        # The prepared RST pipeline converts through Pandoc; the CI unit runner has none.
        try:
            subprocess.run([resolve_pandoc_binary(None), '--version'], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest('Pandoc unavailable')
        source = self.fixture(AD500A_PACKAGE)
        report = ad500a_render.render(source, self.root / 'out')
        self.assertEqual(tree(self.root / 'out'), tree(AD500A_PACKAGE / 'web/ja'))
        self.assertEqual(report['publication_eligible'], read(AD500A_PACKAGE / 'source_manifest.json')['publication_eligible'])

    @pre_four_control_styles
    def test_h1_cold_replay_matches_committed_web(self):
        rebuild_h1(H1_PACKAGE, self.root / 'out')
        self.assertEqual(tree(self.root / 'out'), tree(H1_PACKAGE / 'web/ja'))
        metadata = read(self.root / 'out/manual.ir.json')['metadata']
        manifest = read(H1_PACKAGE / 'source_manifest.json')
        self.assertEqual(metadata['publication_eligible'], manifest['publication_eligible'])

    def test_changed_or_unlisted_inputs_are_rejected(self):
        for relative in ['source/page/charging_ja.rst', 'source/presentation.css']:
            with self.subTest(edition='ad500a', relative=relative):
                source = self.fixture(AD500A_PACKAGE)
                path = source / relative
                path.write_bytes(path.read_bytes() + b' ')
                with self.assertRaisesRegex(ValueError, 'frozen source input changed'):
                    ad500a_render.render(source, self.root / 'out')
                self.assertFalse((self.root / 'out').exists())
        for relative in ['source/chapters.json', 'artwork/solar.png']:
            with self.subTest(edition='h1', relative=relative):
                source = self.fixture(H1_PACKAGE)
                path = source / relative
                path.write_bytes(path.read_bytes() + b' ')
                with self.assertRaisesRegex(ValueError, 'frozen source input changed'):
                    h1_rebuild.validate_inputs(source, read(source / 'source_manifest.json'), None)
        with self.subTest(edition='h1', relative='unlisted'):
            source = self.fixture(H1_PACKAGE)
            manifest = read(source / 'source_manifest.json')
            manifest['inputs'] = [r for r in manifest['inputs'] if not r['path'].startswith('web/')]
            (source / 'source/extra.json').write_text('{}\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'manifest does not cover every input'):
                h1_rebuild.validate_inputs(source, manifest, None)

    def test_candidate_cannot_carry_or_claim_acceptance(self):
        for key, edition in EDITIONS.items():
            with self.subTest(edition=key):
                source = self.fixture(edition['package'])
                manifest = read(source / 'source_manifest.json')
                if manifest['publication_status'] != edition['status'].CANDIDATE:
                    self.skipTest('edition already accepted')
                manifest['publication_eligible'] = True
                with self.assertRaisesRegex(ValueError, 'carries no release acceptance'):
                    edition['status'].acceptance(source, manifest)

    def test_release_inventories_cover_every_package_file(self):
        for key, edition, name in [('ad500a', EDITIONS['ad500a'], 'frozen_source_manifest.json'),
                                   ('h1', EDITIONS['h1'], 'source_manifest.json')]:
            with self.subTest(edition=key):
                package = edition['package']
                inventory = read(package / name)['inputs']
                self.assertEqual([r['path'] for r in inventory], sorted(p for p in tree(package) if p != name))
                for record in inventory:
                    self.assertEqual(file_sha256(package / record['path']), record['sha256'], record['path'])

    def test_corrections_are_recorded_in_the_manifest(self):
        for key, edition in EDITIONS.items():
            with self.subTest(edition=key):
                manifest = read(edition['package'] / 'source_manifest.json')
                self.assertEqual([(r['approved'], r['corrected']) for r in manifest['text_corrections']],
                                 [(old, new) for _, old, new in edition['derive'].CORRECTIONS])


if __name__ == '__main__':
    unittest.main()
