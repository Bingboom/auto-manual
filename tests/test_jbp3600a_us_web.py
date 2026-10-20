"""JBP-3600A US EN/FR/ES Git-only release: archived PDF identity, word coverage, acceptance, shared-IR replay."""
from __future__ import annotations

from contextlib import redirect_stdout
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
PACKAGE = ROOT / 'data/manual_sources/JBP-3600A/US/git-20261014-16ae12b0'
PDF = 'Jackery Battery Pack 3600 User Manual.pdf'
SOURCE_SHA = '16ae12b0426828b921694a496ce699386d92165d5476a10dded83be1a893a91c'
LANGUAGES = ('en', 'fr', 'es')
OFFSET = {'en': 0, 'fr': 8, 'es': 16}
# Printed bodies only (EN PDF 4-11, FR 12-19, ES 20-27); cover, preface and contents stay out.
# Chapter set follows the JBP-2000B / JBP-3600A EU Web manuals; the US print sets
# TROUBLESHOOTING before CONNECTIONS, and the operator kept the print order (2026-10-14).
CHAPTER_IDS = ['safety', 'symbols', 'in-the-box', 'product-overview', 'lcd-display', 'operations',
               'troubleshooting', 'connections', 'charging', 'storage', 'specifications', 'warranty']
TITLES = {
    'en': ['IMPORTANT SAFETY INFORMATION', 'MEANING OF SYMBOLS', "WHAT'S IN THE BOX", 'PRODUCT OVERVIEW',
           'LCD DISPLAY', 'OPERATIONS', 'TROUBLESHOOTING', 'CONNECTIONS', 'CHARGING', 'STORAGE',
           'SPECIFICATIONS', 'WARRANTY'],
    'fr': ['INFORMATIONS DE SÉCURITÉ IMPORTANTES', 'SIGNIFICATION DES SYMBOLES', 'CONTENU DE LA BOÎTE',
           'APERÇU DU PRODUIT', 'AFFICHAGE LCD', 'FONCTIONNEMENT', 'DÉPANNAGE', 'CONNEXIONS', 'CHARGE',
           'STOCKAGE', 'SPÉCIFICATIONS', 'GARANTIE'],
    'es': ['INFORMACIÓN IMPORTANTE DE SEGURIDAD', 'SIGNIFICADO DE LOS SÍMBOLOS', 'CONTENIDO DE LA CAJA',
           'DESCRIPCIÓN GENERAL DEL PRODUCTO', 'PANTALLA LCD', 'OPERACIONES', 'RESOLUCIÓN DE PROBLEMAS',
           'CONEXIONES', 'CARGANDO', 'ALMACENAMIENTO', 'ESPECIFICACIONES', 'GARANTÍA'],
}
CALLOUTS = {'en': ['NOTE', 'CAUTION', 'NOTES', 'Warning'],
            'fr': ['Remarques', 'Important', 'Remarques', 'Avertissement'],
            'es': ['NOTA', 'PRECAUCIÓN', 'Observaciones', 'Advertencia']}
COMPONENTS = {'HB-CALLOUT-STRIP': 4, 'HB-SPECIAL-FCC': 1, 'HB-SPECIAL-INBOX': 1,
              'HB-SPECIAL-REFERENCE-FIGURE': 10, 'HB-TABLE-REFERENCE': 1, 'HB-TABLE-SPEC': 3,
              'HB-TABLE-SYMBOL-ICON': 1, 'HB-TABLE-SYMBOL-SIGNAL': 1, 'HB-TABLE-TROUBLESHOOTING': 1,
              'HB-WARRANTY-LEAD': 1, 'HB-WARRANTY-SECTION': 5, 'HB-WARRANTY-YEARS': 1}
RECOVERIES = {'en': 48, 'fr': 59, 'es': 61}
JOINS = {'en': [], 'fr': [['conformé-', 'ment']],
         'es': [['comunica-', 'ciones'], ['completa-', 'mente'], ['completa-', 'mente']]}
# Pixel-identical artwork reused unchanged from the published JBP-3600A EU English Web manual.
EU_REUSE = {'lcd-display.png': 'lcd_annotated.png', 'power-on-off.png': 'power_annotated.png',
            'lcd-on-off.png': 'lcd_control_clean.png'}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rebuild_module = load('jbp3600a_us_rebuild', PACKAGE / 'rebuild.py')


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def inventory(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): file_sha256(p)
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def shared_inputs_drifted() -> list[str]:
    """The package pins its shared renderers; rebuilding against newer ones is refused."""
    return [row['path'] for row in read(PACKAGE / 'source_manifest.json')['repo_inputs']
            if not (ROOT / row['path']).is_file() or file_sha256(ROOT / row['path']) != row['sha256']]


def rebuild(output: Path, language: str = 'en') -> None:
    with redirect_stdout(io.StringIO()):
        rebuild_module.rebuild(output, language)


def markdown(language: str) -> Path:
    return PACKAGE / f'web/{language}/manual_jbp3600a_us_{language}.md'


def page(language: str) -> BeautifulSoup:
    return BeautifulSoup(markdown(language).read_text(encoding='utf-8'), 'html.parser')


class JbpUsWebTests(unittest.TestCase):
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
        # Isolate negative fixtures from the App stylesheet registration change.
        # Historical manifests and their cold-replay drift checks stay untouched.
        for row in manifest['repo_inputs']:
            if row['path'] == 'tools/web/stylesheets.py':
                path = ROOT / row['path']
                row.update(sha256=file_sha256(path), size=path.stat().st_size)
        write(dest / 'source_manifest.json', manifest)
        return dest

    def test_identity_and_archive(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['target'], {'model': 'JBP-3600A', 'region': 'US', 'languages': list(LANGUAGES),
                                              'technical_version': PACKAGE.name, 'printed_manual_version': None})
        original = manifest['original_source']
        self.assertEqual((original['filename'], original['sha256']), (PDF, SOURCE_SHA))
        self.assertEqual(file_sha256(PACKAGE / PDF), SOURCE_SHA)
        self.assertLessEqual((PACKAGE / PDF).stat().st_size, 32 * 1024 * 1024)
        self.assertEqual(manifest['web_roots'], {lang: 'web/' + lang for lang in LANGUAGES})
        for lang in LANGUAGES:
            pages = list(range(4 + OFFSET[lang], 12 + OFFSET[lang]))
            self.assertEqual(manifest['included_pages'][lang]['physical_pages'], pages)
            self.assertEqual(read(PACKAGE / f'source/{lang}/content.json')['source_sha256'], SOURCE_SHA)
        files = sorted(path for path in inventory(PACKAGE) if path != 'source_manifest.json')
        self.assertEqual(sorted(row['path'] for row in manifest['inputs']), files)

    def test_the_operator_acceptance_binds_every_source_input(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['publication_status'], 'operator-approved-git-only-release')
        approval = read(PACKAGE / 'source/approval.json')
        self.assertEqual(approval['target'], {key: manifest['target'][key]
                                              for key in ('model', 'region', 'technical_version')})
        self.assertEqual(approval['languages'], list(LANGUAGES))
        self.assertEqual(approval['original_source_sha256'], SOURCE_SHA)
        # Everything but the frozen web/ outputs and the acceptance itself.
        self.assertEqual(approval['reviewed_inputs'],
                         [row for row in manifest['inputs']
                          if not row['path'].startswith('web/') and row['path'] != 'source/approval.json'])
        self.assertEqual((approval['operator_quote'], approval['merge_authorization']),
                         ('合入了，上线授权你合入', 'MA-303'))
        for lang in LANGUAGES:
            with self.subTest(language=lang):
                metadata = read(PACKAGE / f'web/{lang}' / PathSegments.MANUAL_IR_JSON)['metadata']
                self.assertIs(metadata['publication_eligible'], True)
                self.assertEqual(metadata['pending_source_review'], [])
                self.assertEqual(metadata['operator_source_acceptance'], approval)

    def test_an_acceptance_that_misses_an_input_is_refused_before_output(self):
        source = self.fixture()
        path = source / 'source/approval.json'
        approval = read(path)
        approval['reviewed_inputs'] = approval['reviewed_inputs'][1:]
        write(path, approval)
        manifest = read(source / 'source_manifest.json')
        row = next(row for row in manifest['inputs'] if row['path'] == 'source/approval.json')
        row.update(size=path.stat().st_size, sha256=file_sha256(path))
        # This negative fixture targets acceptance, not historical shared-input drift.
        # Rebind only its temporary manifest; frozen production inputs stay unchanged.
        symbols = ROOT / 'docs/renderers/web/assets/shared/symbols/manifest.json'
        dependency = next(row for row in manifest['repo_inputs']
                          if row['path'] == symbols.relative_to(ROOT).as_posix())
        dependency.update(size=symbols.stat().st_size, sha256=file_sha256(symbols))
        write(source / 'source_manifest.json', manifest)
        for lang in LANGUAGES:
            with self.subTest(language=lang):
                with mock.patch.object(rebuild_module, 'SOURCE_ROOT', source):
                    with self.assertRaisesRegex(ValueError, 'operator acceptance does not cover these source inputs'):
                        rebuild(self.root / 'output', lang)
                self.assertFalse((self.root / 'output').exists())

    def test_every_body_word_is_classified(self):
        self.assertEqual(read(PACKAGE / 'source/unmapped.json'), {})
        recoveries = read(PACKAGE / 'source/text-recovery.json')
        for lang in LANGUAGES:
            with self.subTest(language=lang):
                coverage = read(PACKAGE / f'source/{lang}/coverage.json')
                self.assertEqual(coverage['pages'], list(range(4 + OFFSET[lang], 12 + OFFSET[lang])))
                for key in ['unmapped', 'duplicate_live_copy', 'unused_recoveries', 'unused_split_words']:
                    self.assertEqual(coverage[key], [], key)
                self.assertTrue(coverage['print_line_breaks'])
                self.assertEqual([join[:2] for join in coverage['word_joins']], JOINS[lang])
                purposes = {s['purpose'].split('/')[0] for s in coverage['selections']}
                self.assertLessEqual(purposes, {'live-copy', 'embedded-art', 'native-symbol', 'printed-folio',
                                                'shared-inbox-live-ordinal', 'invisible-print-text'})
                # Outlined print lines are restored once each, with their glyph-path boxes.
                self.assertEqual(len([r for r in recoveries if r['language'] == lang]), RECOVERIES[lang])

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
            intake = load('jbp3600a_us_intake', PACKAGE / 'source/intake.py')
            with redirect_stdout(io.StringIO()):
                for lang in LANGUAGES:
                    self.assertEqual(intake.make(lang), [], lang)
        finally:
            sys.path[:] = saved_path
            if saved_native is None:
                sys.modules.pop('native', None)
            else:
                sys.modules['native'] = saved_native
        for lang in LANGUAGES:
            for name in ['content.json', 'coverage.json']:
                relative = f'source/{lang}/{name}'
                self.assertEqual((source / relative).read_bytes(), (PACKAGE / relative).read_bytes(), relative)

    def test_frozen_web_is_the_cold_replay(self):
        self.require_pinned_shared_inputs()
        for lang in LANGUAGES:
            with self.subTest(language=lang):
                output = self.root / lang
                rebuild(output, lang)
                self.assertEqual(inventory(output), inventory(PACKAGE / f'web/{lang}'))

    def test_frozen_web_passes_the_admissions(self):
        self.require_pinned_shared_inputs()
        from tools.web.caption_frame_admission import require_caption_frame_admission
        from tools.web.component_admission import require_fresh_component_admission
        from tools.web.frozen_source_evidence import _locale_inventory, _source
        from tools.web.language_release_evidence import _file_inventory, require_publishable_manual_ir
        from tools.web.symbol_asset_admission import require_symbol_asset_admission

        path = PACKAGE / 'source_manifest.json'
        manifest = read(path)
        caches = tuple(PACKAGE.rglob('__pycache__'))
        self.assertEqual(_file_inventory(PACKAGE, excluded_roots=(path, *caches)), _source(manifest, path, 'en')[1])
        for lang in LANGUAGES:
            with self.subTest(language=lang):
                _, inputs, root = _source(manifest, path, lang)
                web = PACKAGE / root
                self.assertEqual(_file_inventory(web), _locale_inventory(inputs, root))
                require_fresh_component_admission(web, model='JBP-3600A', region='US', language=lang)
                self.assertEqual(len(require_symbol_asset_admission(web, PACKAGE, manifest, lang)), 11)
                require_caption_frame_admission(web)
                require_publishable_manual_ir(web)

    def test_changed_inputs_are_rejected_before_output(self):
        for relative in ['source/fr/content.json', 'assets/es-clearance.png', 'source/presentation.css', PDF]:
            with self.subTest(relative=relative):
                source = self.fixture()
                path = source / relative
                data = path.read_bytes()
                path.unlink()
                path.write_bytes(data + b' ')
                with mock.patch.object(rebuild_module, 'SOURCE_ROOT', source):
                    with self.assertRaises(ValueError):
                        rebuild(self.root / 'output', 'fr')
                self.assertFalse((self.root / 'output').exists())
                shutil.rmtree(source)

    def test_chapters_follow_the_print(self):
        for lang in LANGUAGES:
            with self.subTest(language=lang):
                content = read(PACKAGE / f'source/{lang}/content.json')
                self.assertEqual([(c['id'], c['title']) for c in content['chapters']],
                                 list(zip(CHAPTER_IDS, TITLES[lang], strict=True)))
                text = markdown(lang).read_text(encoding='utf-8')
                self.assertNotRegex(text, r'(?m)^# ')  # no printed cover title
                self.assertEqual(re.findall(r'(?m)^## (.+)$', text), TITLES[lang])
                for absent in ['TABLE OF CONTENTS', 'TABLE DES MATIÈRES', 'ÍNDICE', 'Figure labels', '## FCC']:
                    self.assertNotIn(absent, text)
        # Operator decision 「按印刷顺序」: troubleshooting stays before connections.
        self.assertLess(CHAPTER_IDS.index('troubleshooting'), CHAPTER_IDS.index('connections'))

    def test_shared_components_carry_the_page(self):
        for lang in LANGUAGES:
            with self.subTest(language=lang):
                metadata = read(PACKAGE / f'web/{lang}' / PathSegments.MANUAL_IR_JSON)['metadata']
                self.assertEqual(metadata['component_inventory'], COMPONENTS)
                soup = page(lang)
                self.assertFalse(soup.select('figcaption'))  # the print has no figure captions
                labels = [c.get_text(' ', strip=True) for c in soup.select('td.manual-callout-label')]
                self.assertEqual(labels, CALLOUTS[lang])
                # The FCC figure sits in a source group so the symbols heading stays visible.
                self.assertIsNotNone(soup.select_one('div.native-fcc > figure.hb-fcc-composition'))
                self.assertEqual(len(soup.select('div.native-fcc .hb-fcc-column-right li')), 4)
                # Layout follows the JBP-2000B / JBP-3600A EU Web manuals: stacked views, shared LCD table.
                self.assertIsNotNone(soup.select_one('figure.hb-reference-lcd-descriptions'))
                self.assertFalse(soup.select('.native-frame, .native-panel, .native-views'))
                icon = soup.select_one('td.manual-callout-body img.native-inline-control')
                self.assertEqual(icon['src'], 'assets/inline-connection-icon.svg')

    def test_print_line_breaks_and_bold_survive(self):
        soup = page('en')
        safety = soup.find(string=re.compile('Please read all instructions')).find_parent('p')
        self.assertEqual(len(safety.find_all('br')), 8)  # nine printed statements, wraps joined
        self.assertIn('non-professional product manufacturers.', safety.get_text())
        self.assertEqual(soup.find('strong').get_text(), 'The basic safety precautions should be followed '
                                                         'when using this product, including:')
        lcd = soup.select_one('figure.hb-reference-lcd-descriptions')
        self.assertEqual(lcd.select_one('td').decode_contents(),
                         '<strong>Power Percentage/</strong><br/><strong>Fault Code</strong>')
        for lang in LANGUAGES:
            codes = [td.decode_contents() for td in page(lang).select('td.hb-troubleshooting-code')]
            self.assertIn('<strong>F6-F9,</strong><br/><strong>FA, FC, FE</strong>', codes, lang)
        # Printed list marks only where the print sets them: FR exclusions, EN/ES storage.
        self.assertEqual(len(page('fr').select('figure.hb-warranty-card ul li')), 4)
        self.assertFalse(page('en').select('figure.hb-warranty-card ul li'))
        self.assertIn('MODIFICATION:', page('fr').select_one('.hb-fcc-column-right strong').get_text())

    def test_artwork_is_recorded_reused_or_extracted(self):
        stylesheet = (PACKAGE / 'source/presentation.css').read_text(encoding='utf-8')
        referenced = set()
        for lang in LANGUAGES:
            content = (PACKAGE / f'source/{lang}/content.json').read_text(encoding='utf-8')
            used = set(rebuild_module.ASSET_REFERENCE.findall(content + stylesheet))
            served = PACKAGE / f'web/{lang}/assets'
            self.assertEqual({p.name for p in served.iterdir()}, used, lang)
            for path in served.iterdir():
                self.assertEqual(path.read_bytes(), (PACKAGE / 'assets' / path.name).read_bytes(), path.name)
            referenced |= used
        package_assets = {p.name for p in (PACKAGE / 'assets').iterdir()}
        self.assertEqual(referenced, package_assets)
        records = [*read(PACKAGE / 'source/figures.json'), *read(PACKAGE / 'source/symbols.json'),
                   *read(PACKAGE / 'source/glyphs.json')]
        for row in records:
            self.assertEqual(row['sha256'], file_sha256(PACKAGE / row['local_path']), row['local_path'])
            if 'shared_path' in row:
                self.assertEqual((PACKAGE / row['local_path']).read_bytes(), (ROOT / row['shared_path']).read_bytes())
                self.assertLessEqual(row['glyph_comparison']['max_mean_channel_error'], 0.02)
            if row.get('decision', '').startswith('share the English panel'):
                self.assertLessEqual(row['differing_pixel_share'], 0.001)
        eu = ROOT / 'docs/renderers/web/assets/jbp3600a_eu_en'
        for name, origin in EU_REUSE.items():
            self.assertEqual((PACKAGE / 'assets' / name).read_bytes(), (eu / origin).read_bytes(), name)
        decisions = read(PACKAGE / 'audit/asset-decisions.json')
        self.assertEqual(sorted({d['local_path'] for d in decisions}), sorted({r['local_path'] for r in records}))


if __name__ == '__main__':
    unittest.main()
