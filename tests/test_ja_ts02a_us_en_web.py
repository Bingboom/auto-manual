"""JA-TS02A US English Git-only release: archived PDF identity, word coverage, acceptance, shared-IR replay."""
from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
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
PACKAGE = ROOT / 'data/manual_sources/JA-TS02A/US/en/git-20261013-11ce66b1'
SOURCE_SHA = '11ce66b135c5a1b1141c33e4368552124f24757db78d0890a0cdfe3e4f14bff3'
MARKDOWN = PACKAGE / 'web/en/manual_jats02a_us_en.md'
APPROVED_STATUS = 'operator-approved-git-only-release'
ACCEPTANCE = {'operator_quote': '上线，授权你合入', 'merge_authorization': 'MA-302'}
# Print pages 01-22 (PDF 3-24); the cover and contents are not part of the Web body.
CHAPTERS = [
    ('safety', 'SAFETY INSTRUCTIONS'), ('specifications', 'SPECIFICATIONS'), ('package-list', 'PACKAGE LIST'),
    ('what-you-need', 'WHAT YOU NEED'), ('product-overview', 'PRODUCT OVERVIEW'),
    ('pre-installation', 'PRE-INSTALLATION'), ('installation-guide', 'INSTALLATION GUIDE'),
    ('recommended-breakers', 'RECOMMENDED BREAKERS'), ('internet-setup', 'INTERNET AND INITIALIZATION SETUP'),
    ('app-quick-start', 'JACKERY APP QUICK START GUIDE'), ('warranty', 'WARRANTY'),
]
COMPONENTS = {'HB-CALLOUT-STRIP': 5, 'HB-SPECIAL-APP': 1, 'HB-SPECIAL-REFERENCE-FIGURE': 30,
              'HB-WARRANTY-LEAD': 1, 'HB-WARRANTY-SECTION': 6}
# The former bespoke adapter and its stylesheet are gone; the page replays through shared components.
REMOVED = ['build_web.py', 'source/web_presentation.css', 'source/native-pages.json']
SHARED_SYMBOLS = {
    'symbol_warning_triangle.svg': 'docs/renderers/web/assets/shared/symbols/native-v1/symbol_warning_triangle.svg',
    'symbol_electric_shock.svg': 'docs/renderers/web/assets/shared/symbols/native-v1/symbol_electric_shock.svg',
    'symbol_read_manual.svg': 'docs/renderers/web/assets/shared/symbols/native-v1/symbol_read_manual.svg',
    'symbol_grounding.png': 'docs/templates/word_template/common_assets/symbols/grounding.png',
}
SOURCE_GLYPHS = {'symbol_warning_triangle_yellow.svg', 'symbol_ingestion_hazard.svg'}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rebuild_module = load('ja_ts02a_us_en_rebuild', PACKAGE / 'rebuild.py')


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


def rebuild(output: Path) -> None:
    with redirect_stdout(io.StringIO()):
        rebuild_module.rebuild(output)


def link_or_copy(source: str, destination: str) -> None:
    """The 94 MB archive parts are only read; a hard link spares the copy where the filesystem allows."""
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def page() -> BeautifulSoup:
    return BeautifulSoup(MARKDOWN.read_text(encoding='utf-8'), 'html.parser')


class JaTs02aUsEnWebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def require_pinned_shared_inputs(self):
        drifted = shared_inputs_drifted()
        if drifted:
            self.skipTest(f'shared inputs changed since this draft was frozen: {drifted[:3]}')

    def fixture(self) -> Path:
        """A source copy without the frozen web/ outputs, rebound to that tree."""
        dest = self.root / 'source'
        shutil.copytree(PACKAGE, dest, ignore=shutil.ignore_patterns('web', '__pycache__', 'pdf-archive'))
        shutil.copytree(PACKAGE / 'source/pdf-archive', dest / 'source/pdf-archive', copy_function=link_or_copy)
        manifest = read(dest / 'source_manifest.json')
        manifest['inputs'] = [row for row in manifest['inputs'] if not row['path'].startswith('web/')]
        write(dest / 'source_manifest.json', manifest)
        return dest

    def test_identity_and_archive(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['target'], {'model': 'JA-TS02A', 'region': 'US', 'languages': ['en'],
                                              'technical_version': PACKAGE.name,
                                              'printed_manual_version': 'JAK-UM-V1.0'})
        original = manifest['original_source']
        self.assertEqual(original['sha256'], SOURCE_SHA)
        digest = hashlib.sha256()
        for part in original['archive_parts']:
            data = (PACKAGE / part['path']).read_bytes()
            self.assertLessEqual(len(data), 32 * 1024 * 1024)
            digest.update(data)
        self.assertEqual(digest.hexdigest(), SOURCE_SHA)
        self.assertEqual(read(PACKAGE / 'source/en/content.json')['source_sha256'], SOURCE_SHA)
        self.assertEqual(manifest['included_pages']['en']['physical_pages'], list(range(3, 25)))
        self.assertEqual(manifest['web_roots'], {'en': 'web/en'})
        files = sorted(path for path in inventory(PACKAGE) if path != 'source_manifest.json')
        self.assertEqual(sorted(row['path'] for row in manifest['inputs']), files)
        for relative in REMOVED:
            self.assertFalse((PACKAGE / relative).exists(), relative)

    def test_the_operator_acceptance_binds_every_source_input(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['publication_status'], APPROVED_STATUS)
        approval = read(PACKAGE / 'source/approval.json')
        self.assertEqual(approval['target'], {key: manifest['target'][key]
                                              for key in ('model', 'region', 'technical_version')})
        self.assertEqual(approval['original_source_sha256'], SOURCE_SHA)
        # Everything but the frozen web/ outputs and the acceptance itself.
        self.assertEqual(approval['reviewed_inputs'],
                         [row for row in manifest['inputs']
                          if not row['path'].startswith('web/') and row['path'] != 'source/approval.json'])
        self.assertEqual({key: approval[key] for key in ACCEPTANCE}, ACCEPTANCE)
        metadata = read(PACKAGE / 'web/en' / PathSegments.MANUAL_IR_JSON)['metadata']
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
        with mock.patch.object(rebuild_module, 'SOURCE_ROOT', source):
            with self.assertRaisesRegex(ValueError, 'operator acceptance does not cover these source inputs'):
                rebuild(self.root / 'output')
        self.assertFalse((self.root / 'output').exists())

    def test_every_english_body_word_is_classified(self):
        coverage = read(PACKAGE / 'source/en/coverage.json')
        self.assertEqual(coverage['pages'], list(range(3, 25)))
        for key in ['unmapped', 'duplicate_live_copy', 'unused_recoveries', 'unused_split_words']:
            self.assertEqual(coverage[key], [], key)
        self.assertEqual(read(PACKAGE / 'source/unmapped.json'), [])
        self.assertEqual([join[:2] for join in coverage['word_joins']],
                         [['consump-', 'tion'], ['approxi', 'mately']])
        self.assertTrue(coverage['print_line_breaks'])
        purposes = {s['purpose'].split('/')[0] for s in coverage['selections']}
        self.assertLessEqual(purposes, {'live-copy', 'embedded-art', 'native-symbol', 'printed-badge',
                                        'printed-folio', 'printed-header'})

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
            intake = load('ja_ts02a_us_en_intake', PACKAGE / 'source/intake.py')
            with redirect_stdout(io.StringIO()):
                self.assertEqual(intake.make(), [])
        finally:
            sys.path[:] = saved_path
            if saved_native is None:
                sys.modules.pop('native', None)
            else:
                sys.modules['native'] = saved_native
        for relative in ['source/en/content.json', 'source/en/coverage.json']:
            self.assertEqual((source / relative).read_bytes(), (PACKAGE / relative).read_bytes(), relative)

    def test_frozen_web_is_the_cold_replay(self):
        self.require_pinned_shared_inputs()
        output = self.root / 'en'
        rebuild(output)
        self.assertEqual(inventory(output), inventory(PACKAGE / 'web/en'))

    def test_frozen_web_passes_the_release_admissions(self):
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
        target, inputs, root = _source(manifest, path, 'en')
        web = PACKAGE / root
        self.assertEqual(_file_inventory(web), _locale_inventory(inputs, root))
        require_fresh_component_admission(web, model='JA-TS02A', region='US', language='en')
        require_symbol_asset_admission(web, PACKAGE, manifest, 'en')
        require_caption_frame_admission(web)
        require_publishable_manual_ir(web)

    def test_changed_inputs_are_rejected_before_output(self):
        for relative in ['source/en/content.json', 'assets/symbol_warning_triangle_yellow.svg',
                         'source/presentation.css']:
            with self.subTest(relative=relative):
                source = self.fixture()
                path = source / relative
                data = path.read_bytes()
                path.unlink()
                path.write_bytes(data + b' ')
                with mock.patch.object(rebuild_module, 'SOURCE_ROOT', source):
                    with self.assertRaisesRegex(ValueError, re.escape('input changed: ' + relative)):
                        rebuild(self.root / 'output')
                self.assertFalse((self.root / 'output').exists())
                shutil.rmtree(source)

    def test_chapters_follow_the_print(self):
        content = read(PACKAGE / 'source/en/content.json')
        self.assertEqual([(c['id'], c['title']) for c in content['chapters']], CHAPTERS)
        text = MARKDOWN.read_text(encoding='utf-8')
        self.assertNotRegex(text, r'(?m)^# ')  # no printed cover title
        self.assertEqual(re.findall(r'(?m)^## (.+)$', text), [title for _, title in CHAPTERS])
        for absent in ['TABLE OF CONTENTS', 'Figure labels', 'IC RF STATEMENT', '### Circuit priorities']:
            self.assertNotIn(absent, text)

    def test_shared_components_carry_the_page(self):
        metadata = read(PACKAGE / 'web/en' / PathSegments.MANUAL_IR_JSON)['metadata']
        self.assertEqual(metadata['component_inventory'], COMPONENTS)
        soup = page()
        self.assertFalse(soup.select('figcaption'))  # the print has no figure captions
        lockups = soup.select('table.hb-source-warning-lockup .hb-warning-lockup img')
        self.assertEqual([img['src'] for img in lockups], ['assets/symbol_warning_triangle_yellow.svg'] * 3)
        self.assertEqual(len(soup.select('table.manual-callout-table.hb-callout-label-shaded')), 2)
        self.assertEqual(len(soup.select('figure.hb-warranty-card')), 6)

    def test_tables_keep_the_print_spans(self):
        soup = page()
        spec = soup.select_one('table.native-spec-rules')
        self.assertIsNone(spec.find('thead'))
        self.assertEqual(len(spec.select('tbody > tr')), 17)
        cables = soup.select_one('table.native-cables')
        self.assertEqual(cables.select_one('thead th')['colspan'], '2')
        self.assertEqual([cell['rowspan'] for cell in cables.select('td[rowspan]')], ['4'] * 4)
        self.assertEqual(len(cables.select('td.native-wire')), 8)  # the emergency-stop row prints "/"
        led = soup.select_one('table.native-led')
        self.assertEqual([cell['rowspan'] for cell in led.select('td[rowspan]')], ['3', '3', '3', '2'])
        self.assertEqual(len(led.select('tbody > tr')), 11)
        torque = soup.select_one('table.native-torque')
        self.assertEqual(len(torque.select('thead th')), 6)
        self.assertEqual(len(torque.select('tbody > tr')), 4)

    def test_artwork_is_recorded_shared_or_native(self):
        content = (PACKAGE / 'source/en/content.json').read_text(encoding='utf-8')
        stylesheet = (PACKAGE / 'source/presentation.css').read_text(encoding='utf-8')
        referenced = set(rebuild_module.ASSET_REFERENCE.findall(content + stylesheet))
        package_assets = {p.name for p in (PACKAGE / 'assets').iterdir()}
        self.assertEqual(referenced, package_assets)
        served = PACKAGE / 'web/en/assets'
        self.assertEqual({p.name for p in served.iterdir()}, referenced)
        for path in served.iterdir():
            self.assertEqual(path.read_bytes(), (PACKAGE / 'assets' / path.name).read_bytes(), path.name)
        records = read(PACKAGE / 'source/figures.json') + read(PACKAGE / 'source/inline-controls.json')
        recorded = {r['local_path']: r['sha256'] for r in records if 'local_path' in r}
        for name in sorted(package_assets):
            self.assertEqual(recorded.get('assets/' + name), file_sha256(PACKAGE / 'assets' / name), name)
        for name, origin in SHARED_SYMBOLS.items():
            self.assertEqual((PACKAGE / 'assets' / name).read_bytes(), (ROOT / origin).read_bytes(), name)
        glyphs = {r['local_path'].removeprefix('assets/') for r in records
                  if r.get('decision') == 'native-source-glyph'}
        self.assertEqual(glyphs, SOURCE_GLYPHS)


if __name__ == '__main__':
    unittest.main()
