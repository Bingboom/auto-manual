"""Web-layout edition of the JHP-5000C US manuals: print layout, unchanged copy, acceptance and replay."""
from __future__ import annotations

from collections import Counter
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest import mock

from bs4 import BeautifulSoup

from tools.manual_ir.hashing import file_sha256
from tools.utils.path_utils import PathSegments

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'data/manual_sources/JHP-5000C/US/git-20261010-051169dd-web-layout'
APPROVED = PACKAGE.parent / 'git-20261009-051169dd'
PDF = 'Jackery HomePower 5000 Plus.pdf'
SOURCE_SHA = '051169dd15831f5670ada665146c3499e71e415c092a379fd782578bb517c26a'
LANGUAGES = ('en', 'fr', 'es')
APPROVED_STATUS = 'operator-approved-git-only-release'
# The print TOC (physical p3) lists these 14 chapters; the Web uses each chapter's
# own page heading (the French TOC shortens the AC ESS title).
PRINT_CHAPTERS = {
    'en': ['IMPORTANT SAFETY INFORMATION', "WHAT'S IN THE BOX", 'PRODUCT OVERVIEW', 'LCD DISPLAY',
           'OPERATIONS', 'TROUBLESHOOTING', 'UNINTERRUPTIBLE POWER SUPPLY (UPS)', 'CONNECTIONS',
           'CHARGING', 'STORAGE', 'APP SETUP', 'WARRANTY', 'SPECIFICATIONS',
           'SMART HOME BACKUP SYSTEM (AC ESS) INSTALLATION GUIDE'],
    'fr': ['INSTRUCTIONS DE SÉCURITÉ IMPORTANTES', 'CONTENU DE LA BOÎTE', 'APERÇU DU PRODUIT', 'ÉCRAN LCD',
           'FONCTIONNEMENT', 'DÉPANNAGE', 'ALIMENTATION SANS INTERRUPTION (ASI)', 'CONNEXIONS',
           'RECHARGE', 'STOCKAGE', 'CONFIGURATION DE L’APPLICATION', 'GARANTIE', 'SPÉCIFICATIONS',
           'GUIDE D’INSTALLATION DU SYSTÈME DE SAUVEGARDE DOMESTIQUE INTELLIGENT (AC ESS)'],
    'es': ['INSTRUCCIONES DE SEGURIDAD IMPORTANTES', 'CONTENIDO DEL PAQUETE', 'DESCRIPCIÓN GENERAL DEL PRODUCTO',
           'PANTALLA LCD', 'OPERACIONES', 'RESOLUCIÓN DE PROBLEMAS',
           'FUENTE DE ALIMENTACIÓN ININTERRUMPIDA (UPS)', 'CONNECTIONS', 'CARGANDO', 'ALMACENAMIENTO',
           'CONFIGURACIÓN DE LA APLICACIÓN', 'GARANTÍA', 'ESPECIFICACIONES',
           'GUÍA DE INSTALACIÓN DEL SISTEMA DE RESPALDO INTELIGENTE PARA EL HOGAR (AC ESS)'],
}
# Layout-only differences every locale shares: the LCD glossary prints one number
# for two equal adjacent entries (12, 13, 20), and numbered notes and steps are
# list items whose numbers the browser draws.
LAYOUT_REMOVED = ['12', '13', '20', *['1.'] * 7, *['2.'] * 7, *['3.'] * 3]
# Visible text that differs from the approved edition, beyond moves within the
# page: each entry is one listed copy restoration (web_layout.json).
COPY_DELTA = {
    'en': {
        'removed': ['EN',  # p2 badge prints US
                    'DANGER',  # p4 label repeated at the end of its body
                    'FCC', 'CONTACT US'],  # p5, p76 print no such titles
        'added': ['US',
                  # p5: the WARNING meaning was missing and the other rows shifted up
                  'Hazardous practices that may result in severe injury, death, and/or property damage.',
                  'Note'],
    },
    'fr': {
        'removed': ['DANGER', 'FCC', 'CONTACTEZ-NOUS', 'ATTENTION'],
        'added': ['MISE EN GARDE',  # p29 signal words, as for English
                  'Pratiques dangereuses pouvant entraîner des blessures graves, la mort et/ou des dommages matériels.',
                  'Remarque'],
    },
    'es': {
        'removed': ['PELIGRO', 'FCC', 'CONTÁCTENOS',
                    '*'],  # p54: painted over by the note box in print
        'added': ['Prácticas peligrosas que pueden resultar en lesiones personales y/o daños a la propiedad.',  # p53
                  'Nota',
                  'aplicación conectada.'],  # p69 line the intake took for the folio
    },
}
RESTORATIONS = {
    'en': [('preface', 'print-badge'), ('symbols', 'signal-word-meanings'), ('fcc', 'unprinted-title'),
           ('safety', 'duplicated-callout-label'), ('charging', 'misplaced-callout-label'),
           ('ess-battery', 'model-label-placement'), ('specifications', 'registered-mark-position'),
           ('ess-host', 'registered-mark-position'), ('contact', 'unprinted-title')],
    'fr': [('symbols', 'signal-word-meanings'), ('fcc', 'unprinted-title'), ('safety', 'duplicated-callout-label'),
           ('charging', 'misplaced-callout-label'), ('lcd', 'lcd-name-word-boundary'),
           ('warranty', 'warranty-title-body-boundary'), ('ess-battery', 'model-label-placement'),
           ('specifications', 'hazard-note-out-of-spec-row'), ('contact', 'unprinted-title')],
    'es': [('symbols', 'signal-word-meanings'), ('fcc', 'unprinted-title'), ('safety', 'duplicated-callout-label'),
           ('operations', 'misplaced-callout-label'), ('charging', 'misplaced-callout-label'),
           ('ups', 'title-tail'), ('inbox', 'hidden-print-glyph'), ('lcd', 'lcd-name-word-boundary'),
           ('warranty', 'warranty-title-body-boundary'), ('warranty', 'warranty-title-body-boundary'),
           ('ess-battery', 'model-label-placement'), ('specifications', 'hazard-note-out-of-spec-row'),
           ('specifications', 'registered-mark-position'), ('ess-host', 'registered-mark-position'),
           ('app', 'folio-swallowed-line'), ('contact', 'unprinted-title')],
}
# Approved art this edition re-acquires: the overview frames grow to whole paths and
# the FR/ES car panels keep their plug cable.
REFRAMED_ART = {'overview-front.svg', 'overview-left.svg', 'overview-right.svg', 'car-fr.svg', 'car-es.svg'}
SHARED_SYMBOLS = {
    'warning_triangle_dark.svg': 'docs/templates/word_template/common_assets/symbols/warning_triangle_dark.svg',
    'warning_triangle_white.svg': 'docs/templates/word_template/common_assets/symbols/warning_triangle_white.svg',
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rebuild_module = load('jhp5000c_us_layout_rebuild', PACKAGE / 'rebuild.py')


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def markdown(directory: Path, language: str) -> str:
    return (directory / 'web' / language / f'manual_jhp5000c_us_{language}.md').read_text(encoding='utf-8')


def visible_characters(text: str) -> Counter:
    soup = BeautifulSoup(text, 'html.parser')
    for style in soup.find_all('style'):
        style.decompose()
    return Counter(''.join(soup.get_text('').replace('#', '').split()))


def characters(values) -> Counter:
    return Counter(''.join(''.join(values).split()))


def inventory(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): file_sha256(p)
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def shared_inputs_drifted() -> list[str]:
    """The edition pins its shared renderers; rebuilding against newer ones is refused."""
    return [row['path'] for row in read(PACKAGE / 'source_manifest.json')['repo_inputs']
            if not (ROOT / row['path']).is_file() or file_sha256(ROOT / row['path']) != row['sha256']]


def rebuild(output: Path, language: str) -> None:
    with redirect_stdout(io.StringIO()):
        rebuild_module.rebuild(output, language)


class WebLayoutEditionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def require_pinned_shared_inputs(self):
        drifted = shared_inputs_drifted()
        if drifted:
            self.skipTest(f'shared inputs changed since this edition was frozen: {drifted[:3]}')

    def fixture(self) -> Path:
        """A source copy without the frozen web/ outputs, rebound to that tree."""
        dest = self.root / 'source'
        shutil.copytree(PACKAGE, dest, ignore=shutil.ignore_patterns('web', '__pycache__'))
        manifest = read(dest / 'source_manifest.json')
        manifest['inputs'] = [row for row in manifest['inputs'] if not row['path'].startswith('web/')]
        write(dest / 'source_manifest.json', manifest)
        return dest

    def reseal(self, source: Path) -> None:
        manifest = read(source / 'source_manifest.json')
        for row in manifest['inputs']:
            path = source / row['path']
            row.update(sha256=file_sha256(path), size=path.stat().st_size)
        write(source / 'source_manifest.json', manifest)

    def test_identity_lineage_and_candidate_status(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['target'], {'model': 'JHP-5000C', 'region': 'US',
                                              'technical_version': PACKAGE.name, 'languages': list(LANGUAGES)})
        self.assertEqual(manifest['derived_from'], {'technical_version': APPROVED.name,
                                                    'path': APPROVED.relative_to(ROOT).as_posix(),
                                                    'derivation': 'derive_web_layout.py'})
        self.assertEqual(manifest['original_source']['sha256'], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / PDF), SOURCE_SHA)
        self.assertEqual(manifest['web_roots'], {language: f'web/{language}' for language in LANGUAGES})
        self.assertNotIn('publication_authorization', manifest)  # MA-279 covers the approved edition only
        files = sorted(path for path in inventory(PACKAGE) if path != 'source_manifest.json')
        self.assertEqual(sorted(row['path'] for row in manifest['inputs']), files)
        accepted = manifest.get('publication_status') == APPROVED_STATUS
        for language in LANGUAGES:
            metadata = read(PACKAGE / 'web' / language / PathSegments.MANUAL_IR_JSON)['metadata']
            self.assertIs(metadata['publication_eligible'], accepted)
            self.assertEqual(bool(metadata['pending_source_review']), not accepted)
        if not accepted:
            self.assertNotIn('publication_status', manifest)
            self.assertFalse((PACKAGE / 'source/approval.json').exists())
            return
        approval = read(PACKAGE / 'source/approval.json')
        self.assertEqual(approval['operator_quote'], '上线提交发布')
        self.assertEqual(approval['reviewed_inputs'], [
            row for row in manifest['inputs']
            if not row['path'].startswith('web/') and row['path'] != 'source/approval.json'])

    def test_frozen_web_is_the_cold_replay(self):
        self.require_pinned_shared_inputs()
        for language in LANGUAGES:
            with self.subTest(language=language):
                output = self.root / language
                rebuild(output, language)
                self.assertEqual(inventory(output), inventory(PACKAGE / 'web' / language))

    def test_frozen_web_passes_the_release_admissions(self):
        self.require_pinned_shared_inputs()
        from tools.web.caption_frame_admission import require_caption_frame_admission
        from tools.web.component_admission import require_fresh_component_admission
        from tools.web.frozen_source_evidence import _locale_inventory, _source
        from tools.web.language_release_evidence import _file_inventory, require_publishable_manual_ir
        from tools.web.symbol_asset_admission import require_symbol_asset_admission

        path = PACKAGE / 'source_manifest.json'
        manifest = read(path)
        # Sealing copies the package without bytecode caches (loading rebuild.py here writes one).
        caches = tuple(PACKAGE.rglob('__pycache__'))
        self.assertEqual(_file_inventory(PACKAGE, excluded_roots=(path, *caches)), _source(manifest, path, 'en')[1])
        for language in LANGUAGES:
            with self.subTest(language=language):
                target, inputs, root = _source(manifest, path, language)
                web = PACKAGE / root
                self.assertEqual(_file_inventory(web), _locale_inventory(inputs, root))
                require_fresh_component_admission(web, model='JHP-5000C', region='US', language=language)
                require_symbol_asset_admission(web, PACKAGE, manifest, language)
                require_caption_frame_admission(web)
                if manifest.get('publication_status') == APPROVED_STATUS:
                    require_publishable_manual_ir(web)
                else:
                    with self.assertRaisesRegex(RuntimeError, 'pending source review'):
                        require_publishable_manual_ir(web)

    def test_acceptance_covers_exactly_the_reviewed_source(self):
        self.require_pinned_shared_inputs()
        source = self.fixture()
        (source / 'source/approval.json').unlink(missing_ok=True)  # start from the unaccepted sources
        manifest = read(source / 'source_manifest.json')
        manifest['inputs'] = [row for row in manifest['inputs'] if row['path'] != 'source/approval.json']
        manifest['publication_status'] = APPROVED_STATUS
        write(source / 'source_manifest.json', manifest)
        with mock.patch.object(rebuild_module, 'SOURCE_ROOT', source):
            with self.assertRaisesRegex(ValueError, 'operator acceptance does not cover'):
                rebuild(self.root / 'missing', 'en')
            self.assertFalse((self.root / 'missing').exists())
            approval = {
                'target': {key: manifest['target'][key] for key in ('model', 'region', 'technical_version')},
                'original_source_sha256': SOURCE_SHA,
                'reviewed_inputs': [row for row in manifest['inputs'] if row['path'] != 'source/approval.json'],
                'operator_quote': '上线提交发布',
                'merge_authorization': 'operator review and merge of the engineering PR',
            }
            write(source / 'source/approval.json', approval)
            rebuild(self.root / 'accepted', 'en')
            metadata = read(self.root / 'accepted' / PathSegments.MANUAL_IR_JSON)['metadata']
            self.assertTrue(metadata['publication_eligible'])
            self.assertEqual(metadata['pending_source_review'], [])
            self.assertEqual(metadata['operator_source_acceptance'], approval)
            css = source / 'source/presentation.css'
            css.write_text(css.read_text(encoding='utf-8') + '\nbody { color: red; }\n', encoding='utf-8')
            self.reseal(source)
            with self.assertRaisesRegex(ValueError, 'operator acceptance does not cover'):
                rebuild(self.root / 'changed', 'en')
            self.assertFalse((self.root / 'changed').exists())

    def test_changed_inputs_are_rejected_before_output(self):
        for relative in ['source/en/content.json', 'assets/power.svg', 'source/presentation.css']:
            with self.subTest(relative=relative):
                source = self.fixture()
                path = source / relative
                path.write_bytes(path.read_bytes() + b' ')
                with mock.patch.object(rebuild_module, 'SOURCE_ROOT', source):
                    with self.assertRaisesRegex(ValueError, re.escape('input changed: ' + relative)):
                        rebuild(self.root / 'output', 'en')
                self.assertFalse((self.root / 'output').exists())
                shutil.rmtree(source)

    def test_navigation_is_the_print_table_of_contents(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                text = markdown(PACKAGE, language)
                self.assertNotRegex(text, r'(?m)^# ')  # no printed cover title
                titles = []
                for match in re.finditer(r'(?m)^## (.+)$', text):
                    soup = BeautifulSoup(match.group(1), 'html.parser')
                    titles.append((soup.select_one('.hb-heading-title') or soup).get_text(' ', strip=True))
                self.assertEqual(titles, PRINT_CHAPTERS[language])
                self.assertNotIn('TABLE OF CONTENTS', text)
                self.assertIn('<span class="hb-preface-region">', text)

    def test_visible_copy_is_the_approved_copy_plus_listed_restorations(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                approved = visible_characters(markdown(APPROVED, language))
                delta = COPY_DELTA[language]
                expected = approved - characters(LAYOUT_REMOVED + delta['removed']) + characters(delta['added'])
                self.assertEqual(visible_characters(markdown(PACKAGE, language)), expected)
                restorations = read(PACKAGE / f'source/{language}/web_layout.json')['copy_restorations']
                self.assertEqual([(r['chapter'], r['kind']) for r in restorations], RESTORATIONS[language])
                self.assertTrue(all({'approved', 'pdf'} <= set(r) for r in restorations))

    def test_warranty_paragraphs_keep_their_sentence_breaks(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                soup = BeautifulSoup(markdown(PACKAGE, language), 'html.parser')
                for card in soup.select('figure.hb-warranty-card'):
                    blocks = card.find_all('p', recursive=False)
                    texts = [card.get_text()] if not blocks else [p.get_text() for p in blocks]
                    for value in texts:
                        self.assertNotRegex(value, r'[.:;][A-ZÀ-Ý]')

    def test_each_locale_carries_only_its_own_artwork(self):
        stylesheet = (PACKAGE / 'source/presentation.css').read_text(encoding='utf-8')
        for language in LANGUAGES:
            with self.subTest(language=language):
                content = (PACKAGE / f'source/{language}/content.json').read_text(encoding='utf-8')
                expected = set(rebuild_module.ASSET_REFERENCE.findall(content + stylesheet))
                assets = PACKAGE / 'web' / language / 'assets'
                self.assertEqual({p.name for p in assets.iterdir()}, expected)
                for path in assets.iterdir():
                    self.assertEqual(path.read_bytes(), (PACKAGE / 'assets' / path.name).read_bytes(), path.name)
                others = [code for code in ('fr', 'es') if code != language]
                self.assertFalse([p.name for p in assets.iterdir() if p.stem.endswith(tuple('-' + c for c in others))])

    def test_artwork_is_approved_or_recorded(self):
        for art in (APPROVED / 'assets').iterdir():
            mine = PACKAGE / 'assets' / art.name
            if art.name in REFRAMED_ART:
                self.assertNotEqual(mine.read_bytes(), art.read_bytes(), art.name)
            else:
                self.assertEqual(mine.read_bytes(), art.read_bytes(), art.name)
        decisions = read(PACKAGE / 'source/asset_decisions.json')
        recorded = {d['final_path']: d['sha256'] for d in decisions
                    if 'final_path' in d and 'sha256' in d and not d.get('superseded_by_web_layout')}
        added = {p.name for p in (PACKAGE / 'assets').iterdir()} - {p.name for p in (APPROVED / 'assets').iterdir()}
        for name in sorted(added | REFRAMED_ART - {'overview-front.svg', 'overview-left.svg', 'overview-right.svg'}):
            self.assertEqual(recorded.get('assets/' + name), file_sha256(PACKAGE / 'assets' / name), name)
        reused = {d['slot']: d['candidate'] for d in decisions
                  if d.get('slot') in SHARED_SYMBOLS and d.get('decision') == 'reuse byte-identical'}
        self.assertEqual(reused, SHARED_SYMBOLS)
        for name, origin in SHARED_SYMBOLS.items():
            self.assertEqual((PACKAGE / 'assets' / name).read_bytes(), (ROOT / origin).read_bytes(), name)
        for figure in read(PACKAGE / 'source/figures.json'):
            for language, name in figure.get('locale_art', {}).items():
                self.assertEqual(name, f"{figure['id']}-{language}.svg")
                self.assertTrue((PACKAGE / 'assets' / name).is_file(), name)

    def test_derivation_is_reproducible(self):
        try:
            import pymupdf
        except ImportError:  # pragma: no cover - repository dependency
            self.skipTest('PyMuPDF unavailable')
        if tuple(pymupdf.version[:2]) != ('1.28.0', '1.29.0'):
            self.skipTest('native art is validated for PyMuPDF 1.28.0 / MuPDF 1.29.0 (requirements.lock)')
        self.require_pinned_shared_inputs()
        derive_module = load('jhp5000c_us_layout_derive', PACKAGE / 'derive_web_layout.py')
        source = self.root / 'derived'
        shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns('web', '__pycache__'))
        with mock.patch.object(derive_module, 'HERE', source), redirect_stdout(io.StringIO()):
            derive_module.main()
        frozen = {path: digest for path, digest in inventory(PACKAGE).items() if not path.startswith('web/')}
        self.assertEqual(inventory(source), frozen)


if __name__ == '__main__':
    unittest.main()
