"""Solar-Voc correction editions of the JA-AD500A-SIL US manuals: one paragraph, nothing else."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools.manual_ir.hashing import file_sha256
from tools.word.bundle_docx_pandoc import resolve_pandoc_binary

ROOT = Path(__file__).resolve().parents[1]
US = ROOT / 'manual_sources/JA-AD500A-SIL/US'
EDITIONS = {
    'en': {
        'package': US / 'en/git-20261016-a6d1659e-solar-voc',
        'reviewed': US / 'en/git-20261006-a6d1659e-reviewed',
        'authorization': 'MA-259',
        'languages': ('en',),
        'source': 'source/original.ai',
    },
    'fr-es': {
        'package': US / 'fr-es/git-20261016-28c58312-solar-voc',
        'reviewed': US / 'fr-es/git-20261007-28c58312-reviewed',
        'authorization': 'MA-262',
        'languages': ('fr', 'es'),
        'source': 'source/original.pdf',
    },
}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


for key, edition in EDITIONS.items():
    slug = key.replace('-', '_')
    edition['render'] = load(f'jaad500a_us_{slug}_voc_render', edition['package'] / 'render.py')
    edition['derive'] = load(f'jaad500a_us_{slug}_voc_derive', edition['package'] / 'derive_solar_voc.py')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def as_markdown(rst_paragraph: str) -> str:
    """The prepared RST paragraph as the shared Web pipeline emits it (inline subscript only)."""
    return rst_paragraph.replace('V\\ :sub:`oc`', 'V<sub>oc</sub>')


def markdown_name(lang: str) -> str:
    return f'manual_jaad500asil_us_{lang}.md'


def render_language(edition: dict, source: Path, lang: str, output: Path) -> dict:
    if edition['languages'] == ('en',):
        return edition['render'].render(source, output)
    return edition['render'].render(source, lang, output)


def pandoc_available() -> bool:
    try:
        subprocess.run([resolve_pandoc_binary(None), '--version'], check=True, capture_output=True)
    except (OSError, RuntimeError, subprocess.CalledProcessError):
        return False
    return True


class SolarVocEditionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, edition: dict) -> Path:
        dest = self.root / 'source'
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(edition['package'], dest, ignore=shutil.ignore_patterns('web', '__pycache__'))
        return dest

    def test_identity_lineage_and_candidate_status(self):
        for key, edition in EDITIONS.items():
            with self.subTest(edition=key):
                package, reviewed = edition['package'], edition['reviewed']
                manifest = read(package / 'source_manifest.json')
                base = read(reviewed / 'source_manifest.json')
                self.assertEqual(manifest['target']['technical_version'], package.name)
                self.assertEqual(manifest['original_source'], base['original_source'])
                self.assertEqual(file_sha256(package / edition['source']), base['original_source']['sha256'])
                self.assertEqual(manifest['derived_from'], {
                    'package': reviewed.name, 'authorization': edition['authorization'],
                    'manifest_sha256': file_sha256(reviewed / 'source_manifest.json')})
                self.assertEqual(manifest['web_roots'] if 'web_roots' in manifest else {'en': 'web/en'},
                                 {lang: f'web/{lang}' for lang in edition['languages']})
                if manifest['publication_status'] == edition['render'].CANDIDATE:
                    self.assertFalse(manifest['publication_eligible'])
                    self.assertFalse((package / 'source/approval.json').exists())
                    self.assertTrue(manifest['pending_source_review'])
                else:
                    approval = read(package / 'source/approval.json')
                    self.assertEqual(manifest['publication_status'], edition['render'].APPROVED)
                    self.assertTrue(manifest['publication_eligible'])
                    self.assertTrue(approval['operator_quote'])
                    self.assertEqual(approval['target'], edition['render'].TARGET)
                    self.assertEqual(approval['reviewed_inputs'], [
                        r for r in manifest['inputs']
                        if r['path'].startswith(('source/', 'assets/')) and r['path'] != 'source/approval.json'])

    def test_derivation_is_reproducible(self):
        for key, edition in EDITIONS.items():
            with self.subTest(edition=key):
                package = edition['package']
                before = {p: file_sha256(p) for p in package.rglob('*')
                          if p.is_file() and '__pycache__' not in p.parts}
                edition['derive'].main()
                after = {p: file_sha256(p) for p in package.rglob('*')
                         if p.is_file() and '__pycache__' not in p.parts}
                self.assertEqual(before, after)

    def test_only_the_declared_pages_differ_from_the_approved_inputs(self):
        for key, edition in EDITIONS.items():
            with self.subTest(edition=key):
                package, reviewed = edition['package'], edition['reviewed']
                corrected = {f'source/page/{name}' for name, _, _ in edition['derive'].CORRECTIONS}
                approved = {p.relative_to(reviewed).as_posix() for root in ('source', 'assets')
                            for p in (reviewed / root).rglob('*') if p.is_file()}
                mine = {p.relative_to(package).as_posix() for root in ('source', 'assets')
                        for p in (package / root).rglob('*') if p.is_file()}
                self.assertEqual(mine - approved, {'source/differences.md'})
                self.assertEqual(approved - mine, set())
                for relative in sorted(approved - corrected):
                    self.assertEqual((package / relative).read_bytes(), (reviewed / relative).read_bytes(), relative)
                for name, old, new in edition['derive'].CORRECTIONS:
                    page = f'source/page/{name}'
                    text = (reviewed / page).read_text(encoding='utf-8')
                    self.assertEqual(text.count(old), 1, page)
                    self.assertEqual((package / page).read_text(encoding='utf-8'), text.replace(old, new), page)
                    self.assertNotIn('36.8', new)
                    self.assertIn('16', new)
                    self.assertIn('60', new)

    def test_rendered_markdown_is_the_approved_markdown_with_only_the_paragraph_replaced(self):
        for key, edition in EDITIONS.items():
            corrections = {name.split('_')[-1].split('.')[0]: (old, new)
                           for name, old, new in edition['derive'].CORRECTIONS}
            for lang in edition['languages']:
                with self.subTest(edition=key, language=lang):
                    old, new = corrections[lang]
                    approved = (edition['reviewed'] / f'web/{lang}' / markdown_name(lang)).read_text(encoding='utf-8')
                    candidate = (edition['package'] / f'web/{lang}' / markdown_name(lang)).read_text(encoding='utf-8')
                    self.assertEqual(approved.count(as_markdown(old)), 1)
                    self.assertEqual(candidate, approved.replace(as_markdown(old), as_markdown(new)))

    def test_cold_render_matches_committed_web(self):
        # The prepared RST pipeline converts through Pandoc; the CI unit runner has none.
        if not pandoc_available():
            self.skipTest('Pandoc unavailable')
        for key, edition in EDITIONS.items():
            source = self.fixture(edition)
            manifest = read(source / 'source_manifest.json')
            for lang in edition['languages']:
                with self.subTest(edition=key, language=lang):
                    out = self.root / f'{key}-{lang}'
                    report = render_language(edition, source, lang, out)
                    frozen = edition['package'] / f'web/{lang}'
                    self.assertEqual(
                        {str(p.relative_to(out)): file_sha256(p) for p in out.rglob('*') if p.is_file()},
                        {str(p.relative_to(frozen)): file_sha256(p) for p in frozen.rglob('*') if p.is_file()})
                    self.assertEqual(report['publication_eligible'], manifest['publication_eligible'])
                    self.assertEqual(read(out / 'manual.ir.json')['metadata']['publication_eligible'],
                                     manifest['publication_eligible'])

    def test_changed_or_unlisted_inputs_are_rejected_before_output(self):
        for key, edition in EDITIONS.items():
            lang = edition['languages'][0]
            corrected = f"source/page/{edition['derive'].CORRECTIONS[0][0]}"
            for relative in [corrected, 'assets/solar.png']:
                with self.subTest(edition=key, relative=relative):
                    source = self.fixture(edition)
                    path = source / relative
                    path.write_bytes(path.read_bytes() + b' ')
                    with self.assertRaisesRegex(ValueError, 'frozen source input changed'):
                        render_language(edition, source, lang, self.root / 'out')
                    self.assertFalse((self.root / 'out').exists())
            with self.subTest(edition=key, relative='unlisted'):
                source = self.fixture(edition)
                (source / 'source/page/extra.rst').write_text('x\n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'manifest does not cover every input'):
                    render_language(edition, source, lang, self.root / 'out')

    def test_candidate_cannot_carry_or_claim_acceptance(self):
        for key, edition in EDITIONS.items():
            with self.subTest(edition=key):
                source = self.fixture(edition)
                manifest = read(source / 'source_manifest.json')
                if manifest['publication_status'] != edition['render'].CANDIDATE:
                    self.skipTest('edition already accepted')
                manifest['publication_eligible'] = True
                (source / 'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False),
                                                             encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'carries no release acceptance'):
                    render_language(edition, source, edition['languages'][0], self.root / 'out')

    def test_release_manifest_inventories_every_package_file(self):
        for key, edition in EDITIONS.items():
            with self.subTest(edition=key):
                package = edition['package']
                release = read(package / 'frozen_source_manifest.json')
                files = sorted(p.relative_to(package).as_posix() for p in package.rglob('*')
                               if p.is_file() and '__pycache__' not in p.parts
                               and p.name != 'frozen_source_manifest.json')
                self.assertEqual([r['path'] for r in release['inputs']], files)
                for record in release['inputs']:
                    self.assertEqual(file_sha256(package / record['path']), record['sha256'], record['path'])

    def test_corrections_are_recorded_in_the_manifest(self):
        for key, edition in EDITIONS.items():
            with self.subTest(edition=key):
                manifest = read(edition['package'] / 'source_manifest.json')
                self.assertEqual(
                    [(r['page'], r['approved'], r['corrected']) for r in manifest['text_corrections']],
                    [(f'source/page/{name}', old, new) for name, old, new in edition['derive'].CORRECTIONS])
                for concern in manifest.get('source_concerns', []):
                    if 'Voc' in concern['issue']:
                        self.assertIn('corrected in this edition', concern['disposition'])


if __name__ == '__main__':
    unittest.main()
