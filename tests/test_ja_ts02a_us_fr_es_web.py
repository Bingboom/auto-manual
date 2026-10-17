"""JA-TS02A US French and Spanish Git-only candidate: source identity, word coverage, admissions, shared-IR replay."""
from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from bs4 import BeautifulSoup

from tools.manual_ir.hashing import file_sha256
from tools.utils.path_utils import PathSegments

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'data/manual_sources/JA-TS02A/US/added-locales/git-20261014-11ce66b1'
ENGLISH = ROOT / 'data/manual_sources/JA-TS02A/US/en/git-20261013-11ce66b1'
SOURCE_SHA = '11ce66b135c5a1b1141c33e4368552124f24757db78d0890a0cdfe3e4f14bff3'
LANGUAGES = ('fr', 'es')
PAGES = {'fr': list(range(25, 47)), 'es': list(range(47, 70))}
# Same chapters, in the English edition's order; titles as printed in each language.
CHAPTERS = {
    'fr': ['CONSIGNES DE SÉCURITÉ', 'SPÉCIFICATIONS', 'LISTE DES PAQUETS', 'CE DONT VOUS AVEZ BESOIN',
           'APERÇU DU PRODUIT', 'PRÉ-INSTALLATION', "GUIDE D'INSTALLATION",
           'UTILISATION DE L’APPLICATION JACKERY', "GUIDE DE DÉMARRAGE RAPIDE DE L'APPLICATION JACKERY", 'GARANTIE'],
    'es': ['INSTRUCCIONES DE SEGURIDAD', 'ESPECIFICACIONES', 'LISTA DE PAQUETES', 'LO QUE NECESITAS',
           'DESCRIPCIÓN DEL PRODUCTO', 'PRE-INSTALACIÓN', 'GUÍA DE INSTALACIÓN',
           'USO DE LA APLICACIÓN DE JACKERY', 'GUÍA DE INICIO RÁPIDO DE LA APLICACIÓN JACKERY', 'GARANTÍA'],
}
CHAPTER_IDS = ['safety', 'specifications', 'package-list', 'what-you-need', 'product-overview', 'pre-installation',
               'installation-guide', 'internet-setup', 'app-quick-start', 'warranty']
# The prints set the recommended-breakers title as a subheading of the installation guide (decision D2).
BREAKERS = {'fr': 'Briseurs recommandés', 'es': 'Disyuntores Recomendados'}
# English has five callout strips; the French and Spanish prints set the deadfront warning as a plain line.
COMPONENTS = {'HB-CALLOUT-STRIP': 4, 'HB-SPECIAL-APP': 1, 'HB-SPECIAL-REFERENCE-FIGURE': 30,
              'HB-TABLE-SPEC': 1, 'HB-WARRANTY-LEAD': 1, 'HB-WARRANTY-SECTION': 6}
# Plain shared tables (no shared component fits), declared with their reasons in the manifest.
PLAIN_TABLES = ['safety', 'what-you-need', 'product-overview', 'installation-guide']
STYLE_BASELINE = ROOT / 'docs/renderers/contracts/prepared_style_baseline.json'
JOINS = {'fr': [['domes-', 'tique'], ['automatique-', 'ment'], ['immédi-', 'atement'], ['alimenta', 'tion']],
         'es': [['concesion-', 'ario'], ['recomien-', 'da'], ['instruc-', 'ciones']]}
SHARED_PANELS = {('fr', 'deadfront-installation'), ('fr', 'iot-pairing'), ('es', 'app-store-badges')}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rebuild_module = load('ja_ts02a_us_fr_es_rebuild', PACKAGE / 'rebuild.py')


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def inventory(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): file_sha256(p)
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def shared_inputs_drifted() -> list[str]:
    """The package pins its shared renderers and English inputs; rebuilding against newer ones is refused."""
    return [row['path'] for row in read(PACKAGE / 'source_manifest.json')['repo_inputs']
            if not (ROOT / row['path']).is_file() or file_sha256(ROOT / row['path']) != row['sha256']]


def rebuild(output: Path, language: str) -> None:
    with redirect_stdout(io.StringIO()):
        rebuild_module.rebuild(output, language)


def page(language: str) -> BeautifulSoup:
    path = PACKAGE / f'web/{language}/manual_jats02a_us_{language}.md'
    return BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')


class JaTs02aUsFrEsWebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def require_pinned_shared_inputs(self):
        drifted = shared_inputs_drifted()
        if drifted:
            self.skipTest(f'shared inputs changed since this candidate was frozen: {drifted[:3]}')

    def fixture(self) -> Path:
        """A source copy without the frozen web/ outputs, rebound to that tree."""
        dest = self.root / 'source'
        shutil.copytree(PACKAGE, dest, ignore=shutil.ignore_patterns('web', '__pycache__'))
        manifest = read(dest / 'source_manifest.json')
        manifest['inputs'] = [row for row in manifest['inputs'] if not row['path'].startswith('web/')]
        write(dest / 'source_manifest.json', manifest)
        return dest

    def test_identity_reuses_the_english_archive_without_a_copy(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['target'], {'model': 'JA-TS02A', 'region': 'US', 'languages': ['fr', 'es'],
                                              'technical_version': PACKAGE.name,
                                              'printed_manual_version': 'JAK-UM-V1.0'})
        self.assertEqual(manifest['web_roots'], {'fr': 'web/fr', 'es': 'web/es'})
        # The D2 revision changes source inputs, so the 2026-10-14 acceptance (MA-307) no longer covers them.
        self.assertEqual(manifest['publication_status'], 'git-only-source-candidate')
        self.assertFalse((PACKAGE / 'source/approval.json').exists())
        original = manifest['original_source']
        self.assertEqual(original['sha256'], SOURCE_SHA)
        digest = hashlib.sha256()
        for part in original['archive_parts']:
            self.assertTrue(part['path'].startswith(ENGLISH.relative_to(ROOT).as_posix() + '/source/pdf-archive/'))
            digest.update((ROOT / part['path']).read_bytes())
        self.assertEqual(digest.hexdigest(), SOURCE_SHA)
        pinned = {row['path'] for row in manifest['repo_inputs']}
        self.assertLessEqual({part['path'] for part in original['archive_parts']}, pinned)
        self.assertFalse([p for p in PACKAGE.rglob('*') if p.suffix.lower() in {'.pdf', '.bin'}])
        for language in LANGUAGES:
            self.assertEqual(manifest['included_pages'][language]['physical_pages'], PAGES[language])
            self.assertEqual(read(PACKAGE / f'source/{language}/content.json')['source_sha256'], SOURCE_SHA)
        files = sorted(path for path in inventory(PACKAGE) if path != 'source_manifest.json')
        self.assertEqual(sorted(row['path'] for row in manifest['inputs']), files)

    def test_the_english_edition_is_untouched(self):
        manifest = read(ENGLISH / 'source_manifest.json')
        self.assertEqual(manifest['web_roots'], {'en': 'web/en'})
        files = {path: sha for path, sha in inventory(ENGLISH).items() if path != 'source_manifest.json'}
        self.assertEqual({row['path']: row['sha256'] for row in manifest['inputs']}, files)

    def test_candidate_is_not_publishable_before_operator_acceptance(self):
        from tools.web.language_release_evidence import require_publishable_manual_ir
        for language in LANGUAGES:
            with self.subTest(language=language):
                metadata = read(PACKAGE / f'web/{language}' / PathSegments.MANUAL_IR_JSON)['metadata']
                self.assertIs(metadata['publication_eligible'], False)
                self.assertTrue(metadata['pending_source_review'])
                self.assertIsNone(metadata['operator_source_acceptance'])
                with self.assertRaises(Exception):
                    require_publishable_manual_ir(PACKAGE / f'web/{language}')

    def test_every_body_word_is_classified(self):
        self.assertEqual(read(PACKAGE / 'source/unmapped.json'), {'fr': [], 'es': []})
        for language in LANGUAGES:
            coverage = read(PACKAGE / f'source/{language}/coverage.json')
            self.assertEqual(coverage['pages'], PAGES[language])
            for key in ['unmapped', 'duplicate_live_copy', 'unused_recoveries', 'unused_split_words']:
                self.assertEqual(coverage[key], [], f'{language} {key}')
            self.assertEqual([join[:2] for join in coverage['word_joins']], JOINS[language])
            self.assertTrue(coverage['print_line_breaks'])
            purposes = {s['purpose'].split('/')[0] for s in coverage['selections']}
            self.assertLessEqual(purposes, {'live-copy', 'embedded-art', 'native-symbol', 'printed-badge',
                                            'printed-folio', 'printed-header', 'duplicate-print-page'})
        self.assertEqual(read(PACKAGE / 'source/es/coverage.json')['duplicate_pages'], {'65': 64})

    def test_intake_reproduces_the_frozen_source(self):
        try:
            import pymupdf
        except ImportError:  # pragma: no cover - repository dependency
            self.skipTest('PyMuPDF unavailable')
        if tuple(pymupdf.version[:2]) != ('1.28.0', '1.29.0'):
            self.skipTest('word geometry is validated for PyMuPDF 1.28.0 / MuPDF 1.29.0 (requirements.lock)')
        source = self.fixture()
        saved_path, saved_native = list(sys.path), sys.modules.get('native')
        try:
            native = load('native', PACKAGE / 'source/native.py')
            native.SOURCE = source
            sys.modules['native'] = native  # intake.py imports its sibling by this name
            intake = load('ja_ts02a_us_fr_es_intake', PACKAGE / 'source/intake.py')
            with redirect_stdout(io.StringIO()):
                for language in LANGUAGES:
                    self.assertEqual(intake.make(language), [], language)
        finally:
            sys.path[:] = saved_path
            if saved_native is None:
                sys.modules.pop('native', None)
            else:
                sys.modules['native'] = saved_native
        for language in LANGUAGES:
            for name in ['content.json', 'coverage.json']:
                relative = f'source/{language}/{name}'
                self.assertEqual((source / relative).read_bytes(), (PACKAGE / relative).read_bytes(), relative)

    def test_frozen_web_is_the_cold_replay(self):
        self.require_pinned_shared_inputs()
        for language in LANGUAGES:
            output = self.root / language
            rebuild(output, language)
            self.assertEqual(inventory(output), inventory(PACKAGE / f'web/{language}'), language)

    def test_frozen_web_passes_the_release_admissions(self):
        self.require_pinned_shared_inputs()
        from tools.web.caption_frame_admission import require_caption_frame_admission
        from tools.web.component_admission import require_fresh_component_admission
        from tools.web.frozen_source_evidence import _locale_inventory, _source
        from tools.web.language_release_evidence import _file_inventory
        from tools.web.symbol_asset_admission import require_symbol_asset_admission

        path = PACKAGE / 'source_manifest.json'
        manifest = read(path)
        caches = tuple(PACKAGE.rglob('__pycache__'))
        for language in LANGUAGES:
            with self.subTest(language=language):
                target, inputs, root = _source(manifest, path, language)
                self.assertEqual(_file_inventory(PACKAGE, excluded_roots=(path, *caches)), inputs)
                web = PACKAGE / root
                self.assertEqual(_file_inventory(web), _locale_inventory(inputs, root))
                require_fresh_component_admission(web, model='JA-TS02A', region='US', language=language)
                require_symbol_asset_admission(web, PACKAGE, manifest, language)
                require_caption_frame_admission(web)

    def test_every_symbol_passes_the_glyph_gate_against_its_own_page(self):
        import fitz
        from tools.asset_pipeline.native_svg import native_symbol_svg
        from tools.web.symbol_asset_admission import compare_symbol

        original = read(PACKAGE / 'source_manifest.json')['original_source']
        data = b''.join((ROOT / part['path']).read_bytes() for part in original['archive_parts'])
        rows = read(PACKAGE / 'source/symbols.json')
        self.assertEqual(sorted({(r['language'], r['key']) for r in rows}),
                         sorted((lang, key) for lang in LANGUAGES for key in [
                             'caution', 'electric-shock', 'grounding', 'ingestion-hazard', 'lockup-installation-location',
                             'lockup-surface-mounting', 'read-manual']))
        with fitz.open(stream=data, filetype='pdf') as doc:
            for row in rows:
                with self.subTest(language=row['language'], key=row['key']):
                    reference = native_symbol_svg(doc[row['physical_page'] - 1], row['drawing_indices'], row['glyph_bbox'])
                    asset = PACKAGE / f"web/{row['language']}" / row['local_path']
                    self.assertEqual(file_sha256(asset), row['sha256'])
                    compare_symbol(asset.read_bytes(), asset.suffix, reference)
                    self.assertIn(row['local_path'], (PACKAGE / f"source/{row['language']}/content.json").read_text())

    def test_changed_inputs_are_rejected_before_output(self):
        for relative in ['source/fr/content.json', 'assets/symbol_grounding-print.svg', 'source/presentation.css']:
            with self.subTest(relative=relative):
                source = self.fixture()
                path = source / relative
                data = path.read_bytes()
                path.unlink()
                path.write_bytes(data + b' ')
                with mock.patch.object(rebuild_module, 'SOURCE_ROOT', source):
                    with self.assertRaisesRegex(ValueError, re.escape('input changed: ' + relative)):
                        rebuild(self.root / 'output', 'fr')
                self.assertFalse((self.root / 'output').exists())
                shutil.rmtree(source)

    def test_chapters_follow_the_english_edition(self):
        for language in LANGUAGES:
            content = read(PACKAGE / f'source/{language}/content.json')
            self.assertEqual([c['id'] for c in content['chapters']], CHAPTER_IDS)
            self.assertEqual([c['title'] for c in content['chapters']], CHAPTERS[language])
            text = (PACKAGE / f'web/{language}/manual_jats02a_us_{language}.md').read_text(encoding='utf-8')
            self.assertNotRegex(text, r'(?m)^# ')  # no printed cover title
            self.assertEqual(re.findall(r'(?m)^## (.+)$', text), CHAPTERS[language])
            # A subheading of the installation guide, at the level of Energizing and Locking the Panel.
            guide = next(c for c in content['chapters'] if c['id'] == 'installation-guide')
            headings = [(n['level'],
                         ''.join(t.get('text', '') for t in n.get('children', [])))
                        for n in guide['nodes'] if n.get('kind') == 'heading']
            self.assertEqual(headings[-1], (4, BREAKERS[language]))

    def test_shared_components_carry_the_page(self):
        for language in LANGUAGES:
            metadata = read(PACKAGE / f'web/{language}' / PathSegments.MANUAL_IR_JSON)['metadata']
            self.assertEqual(metadata['component_inventory'], COMPONENTS)
            soup = page(language)
            self.assertFalse(soup.select('figcaption'))
            lockups = soup.select('table.hb-source-warning-lockup .hb-warning-lockup img')
            self.assertEqual([img['src'] for img in lockups], ['assets/symbol_warning_triangle_yellow.svg'] * 2)
            self.assertEqual(len(soup.select('table.manual-callout-table.hb-callout-label-shaded')), 2)
            self.assertEqual(len(soup.select('figure.hb-warranty-card')), 6)

    def test_tables_keep_the_print_spans(self):
        for language in LANGUAGES:
            soup = page(language)
            spec = soup.select_one('table.hb-spec-table')
            self.assertEqual(len(spec.select('tbody > tr')), 17)
            plain = [t for t in soup.select('table') if t.get('class') == ['manual-table']]
            self.assertEqual(len(plain), 4)
            symbols, cables, led, torque = plain
            self.assertEqual(len(symbols.select('tbody img')), 4)
            self.assertEqual(cables.select_one('thead th')['colspan'], '2')
            self.assertEqual([cell['rowspan'] for cell in cables.select('td[rowspan]')], ['4'] * 4)
            self.assertEqual([cell['rowspan'] for cell in led.select('td[rowspan]')], ['3', '3', '3', '2'])
            self.assertEqual(len(torque.select('thead th')), 6)
            self.assertEqual(len(torque.select('tbody > tr')), 4)

    def test_only_shared_styles_pass_the_prepared_document_gate(self):
        from tools.web.prepared_style_audit import audit_prepared_package_locale, require_prepared_style_admission
        manifest = read(PACKAGE / 'source_manifest.json')
        declared = manifest['shared_component_exceptions']
        self.assertEqual([(row['language'], row['page_id']) for row in declared],
                         [(language, page_id) for language in LANGUAGES for page_id in PLAIN_TABLES])
        self.assertTrue(all(row['reason'].strip() for row in declared))
        roots = {row['web_root'] for row in read(STYLE_BASELINE)['entries']}
        for language in LANGUAGES:
            with self.subTest(language=language):
                web = PACKAGE / f'web/{language}'
                report = audit_prepared_package_locale(PACKAGE, web, manifest)
                self.assertEqual((report['issues'], report['declared_tables']), ([], 4))
                self.assertNotIn(web.relative_to(ROOT).as_posix(), roots)  # not a baseline entry
                self.assertNotIn('baseline', require_prepared_style_admission(web, manifest))
                classes = {c for tag in page(language).find_all(class_=True) for c in tag['class']}
                self.assertFalse({c for c in classes if c.startswith('native-')})
        self.assertIn(ENGLISH.relative_to(ROOT).as_posix() + '/web/en', roots)  # English stays as released

    def test_artwork_is_shared_with_english_or_cut_per_language(self):
        english = {r['slot']: r for r in read(ENGLISH / 'source/figures.json')}
        records = read(PACKAGE / 'source/figures.json')
        self.assertEqual(len(records), 64)
        for r in records:
            with self.subTest(language=r['language'], slot=r['slot']):
                self.assertEqual(file_sha256(PACKAGE / r['local_path']), r['sha256'])
                if (r['language'], r['slot']) in SHARED_PANELS:
                    self.assertLessEqual(r['english_differing_pixel_share'], 0.001)
                    self.assertEqual(r['sha256'], english[r['slot']]['sha256'])
                else:
                    self.assertGreater(r['english_differing_pixel_share'], 0.001)
                    self.assertEqual(r['local_path'], f"assets/{r['language']}-{r['slot']}.png")
        controls = {c['slot']: c for c in read(ENGLISH / 'source/inline-controls.json')}
        for c in read(PACKAGE / 'source/inline-controls.json'):
            self.assertEqual(c['sha256'], controls[c['slot']]['sha256'])
        package = {p.name for p in (PACKAGE / 'assets').iterdir()}
        served = {p.name for lang in LANGUAGES for p in (PACKAGE / f'web/{lang}/assets').iterdir()}
        self.assertEqual(served, package)
        for language in LANGUAGES:
            for path in (PACKAGE / f'web/{language}/assets').iterdir():
                self.assertEqual(path.read_bytes(), (PACKAGE / 'assets' / path.name).read_bytes(), path.name)


if __name__ == '__main__':
    unittest.main()
