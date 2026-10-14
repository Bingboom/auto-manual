"""JBP-3600A US English Git-only candidate: archived PDF identity, word coverage, shared-IR replay."""
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
PACKAGE = ROOT / 'data/manual_sources/JBP-3600A/US/en/git-20261014-16ae12b0'
PDF = 'Jackery Battery Pack 3600 User Manual.pdf'
SOURCE_SHA = '16ae12b0426828b921694a496ce699386d92165d5476a10dded83be1a893a91c'
MARKDOWN = PACKAGE / 'web/en/manual_jbp3600a_us_en.md'
# Printed English pages 01-08 (PDF 4-11); the cover, preface and contents are not in the Web body.
CHAPTERS = [
    ('safety', 'IMPORTANT SAFETY INFORMATION'), ('symbols', 'MEANING OF SYMBOLS'),
    ('in-the-box', "WHAT'S IN THE BOX"), ('product-overview', 'PRODUCT OVERVIEW'),
    ('lcd-display', 'LCD DISPLAY'), ('operations', 'OPERATIONS'), ('troubleshooting', 'TROUBLESHOOTING'),
    ('connections', 'CONNECTIONS'), ('charging', 'CHARGING'), ('storage', 'STORAGE'),
    ('specifications', 'SPECIFICATIONS'), ('warranty', 'WARRANTY'),
]
COMPONENTS = {'HB-CALLOUT-STRIP': 4, 'HB-SPECIAL-FCC': 1, 'HB-SPECIAL-INBOX': 1,
              'HB-SPECIAL-REFERENCE-FIGURE': 10, 'HB-TABLE-SPEC': 3, 'HB-TABLE-SYMBOL-ICON': 1,
              'HB-TABLE-SYMBOL-SIGNAL': 1, 'HB-TABLE-TROUBLESHOOTING': 1, 'HB-WARRANTY-LEAD': 1,
              'HB-WARRANTY-SECTION': 5, 'HB-WARRANTY-YEARS': 1}
# Pixel-identical artwork reused unchanged from the published JBP-3600A EU English Web manual.
EU_REUSE = {'lcd-display.png': 'lcd_annotated.png', 'power-on-off.png': 'power_annotated.png',
            'lcd-on-off.png': 'lcd_control_clean.png'}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rebuild_module = load('jbp3600a_us_en_rebuild', PACKAGE / 'rebuild.py')


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


def page() -> BeautifulSoup:
    return BeautifulSoup(MARKDOWN.read_text(encoding='utf-8'), 'html.parser')


class JbpUsEnWebTests(unittest.TestCase):
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

    def test_identity_and_archive(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['target'], {'model': 'JBP-3600A', 'region': 'US', 'languages': ['en'],
                                              'technical_version': PACKAGE.name, 'printed_manual_version': None})
        original = manifest['original_source']
        self.assertEqual((original['filename'], original['sha256']), (PDF, SOURCE_SHA))
        self.assertEqual(file_sha256(PACKAGE / PDF), SOURCE_SHA)
        self.assertLessEqual((PACKAGE / PDF).stat().st_size, 32 * 1024 * 1024)
        self.assertEqual(read(PACKAGE / 'source/en/content.json')['source_sha256'], SOURCE_SHA)
        self.assertEqual(manifest['included_pages']['en']['physical_pages'], list(range(4, 12)))
        self.assertEqual(manifest['web_roots'], {'en': 'web/en'})
        files = sorted(path for path in inventory(PACKAGE) if path != 'source_manifest.json')
        self.assertEqual(sorted(row['path'] for row in manifest['inputs']), files)

    def test_candidate_is_not_publishable(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['publication_status'], 'git-only-source-candidate')
        self.assertFalse((PACKAGE / 'source/approval.json').exists())
        metadata = read(PACKAGE / 'web/en' / PathSegments.MANUAL_IR_JSON)['metadata']
        self.assertIs(metadata['publication_eligible'], False)
        self.assertTrue(metadata['pending_source_review'])
        self.assertIsNone(metadata['operator_source_acceptance'])

    def test_every_english_body_word_is_classified(self):
        coverage = read(PACKAGE / 'source/en/coverage.json')
        self.assertEqual(coverage['pages'], list(range(4, 12)))
        for key in ['unmapped', 'duplicate_live_copy', 'unused_recoveries', 'unused_split_words']:
            self.assertEqual(coverage[key], [], key)
        self.assertEqual(read(PACKAGE / 'source/unmapped.json'), [])
        self.assertTrue(coverage['print_line_breaks'])
        purposes = {s['purpose'].split('/')[0] for s in coverage['selections']}
        self.assertLessEqual(purposes, {'live-copy', 'embedded-art', 'native-symbol', 'printed-folio',
                                        'shared-inbox-live-ordinal'})
        # Outlined print lines are restored once each, with their glyph-path boxes.
        recoveries = read(PACKAGE / 'source/text-recovery.json')
        self.assertEqual(len(recoveries), 48)
        self.assertEqual({r['physical_page'] for r in recoveries}, {4, 5, 6, 7, 8, 10, 11})

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
            intake = load('jbp3600a_us_en_intake', PACKAGE / 'source/intake.py')
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

    def test_frozen_web_passes_the_admissions(self):
        self.require_pinned_shared_inputs()
        from tools.web.caption_frame_admission import require_caption_frame_admission
        from tools.web.component_admission import require_fresh_component_admission
        from tools.web.frozen_source_evidence import _locale_inventory, _source
        from tools.web.language_release_evidence import _file_inventory
        from tools.web.symbol_asset_admission import require_symbol_asset_admission

        path = PACKAGE / 'source_manifest.json'
        manifest = read(path)
        caches = tuple(PACKAGE.rglob('__pycache__'))
        self.assertEqual(_file_inventory(PACKAGE, excluded_roots=(path, *caches)), _source(manifest, path, 'en')[1])
        _, inputs, root = _source(manifest, path, 'en')
        web = PACKAGE / root
        self.assertEqual(_file_inventory(web), _locale_inventory(inputs, root))
        require_fresh_component_admission(web, model='JBP-3600A', region='US', language='en')
        self.assertEqual(len(require_symbol_asset_admission(web, PACKAGE, manifest, 'en')), 11)
        require_caption_frame_admission(web)

    def test_changed_inputs_are_rejected_before_output(self):
        for relative in ['source/en/content.json', 'assets/clearance.png', 'source/presentation.css', PDF]:
            with self.subTest(relative=relative):
                source = self.fixture()
                path = source / relative
                data = path.read_bytes()
                path.unlink()
                path.write_bytes(data + b' ')
                with mock.patch.object(rebuild_module, 'SOURCE_ROOT', source):
                    with self.assertRaises(ValueError):
                        rebuild(self.root / 'output')
                self.assertFalse((self.root / 'output').exists())
                shutil.rmtree(source)

    def test_chapters_follow_the_print(self):
        content = read(PACKAGE / 'source/en/content.json')
        self.assertEqual([(c['id'], c['title']) for c in content['chapters']], CHAPTERS)
        text = MARKDOWN.read_text(encoding='utf-8')
        self.assertNotRegex(text, r'(?m)^# ')  # no printed cover title
        self.assertEqual(re.findall(r'(?m)^## (.+)$', text), [title for _, title in CHAPTERS])
        for absent in ['TABLE OF CONTENTS', 'Félicitations', 'Felicidades', 'Figure labels', '## FCC']:
            self.assertNotIn(absent, text)

    def test_shared_components_carry_the_page(self):
        metadata = read(PACKAGE / 'web/en' / PathSegments.MANUAL_IR_JSON)['metadata']
        self.assertEqual(metadata['component_inventory'], COMPONENTS)
        soup = page()
        self.assertFalse(soup.select('figcaption'))  # the print has no figure captions
        labels = [c.get_text(' ', strip=True) for c in soup.select('td.manual-callout-label')]
        self.assertEqual(labels, ['NOTE', 'CAUTION', 'NOTES', 'Warning'])
        # The FCC figure sits in a source group so the MEANING OF SYMBOLS heading stays visible.
        self.assertIsNotNone(soup.select_one('div.native-fcc > figure.hb-fcc-composition'))
        self.assertEqual(len(soup.select('div.native-fcc .hb-fcc-column-right li')), 4)

    def test_print_line_breaks_and_bold_survive(self):
        soup = page()
        safety = soup.find(string=re.compile('Please read all instructions')).find_parent('p')
        self.assertEqual(len(safety.find_all('br')), 8)  # nine printed statements, wraps joined
        self.assertIn('non-professional product manufacturers.', safety.get_text())
        self.assertEqual(soup.find('strong').get_text(), 'The basic safety precautions should be followed '
                                                         'when using this product, including:')
        codes = [td.decode_contents() for td in soup.select('td.hb-troubleshooting-code')]
        self.assertIn('<strong>F6-F9,</strong><br/><strong>FA, FC, FE</strong>', codes)
        icon = soup.select_one('td.manual-callout-body img.native-inline-control')
        self.assertEqual(icon['src'], 'assets/inline-connection-icon.svg')

    def test_artwork_is_recorded_reused_or_extracted(self):
        content = (PACKAGE / 'source/en/content.json').read_text(encoding='utf-8')
        stylesheet = (PACKAGE / 'source/presentation.css').read_text(encoding='utf-8')
        referenced = set(rebuild_module.ASSET_REFERENCE.findall(content + stylesheet))
        package_assets = {p.name for p in (PACKAGE / 'assets').iterdir()}
        self.assertEqual(referenced, package_assets)
        served = PACKAGE / 'web/en/assets'
        self.assertEqual({p.name for p in served.iterdir()}, referenced)
        for path in served.iterdir():
            self.assertEqual(path.read_bytes(), (PACKAGE / 'assets' / path.name).read_bytes(), path.name)
        records = [*read(PACKAGE / 'source/figures.json'), *read(PACKAGE / 'source/symbols.json'),
                   *read(PACKAGE / 'source/glyphs.json')]
        recorded = {r['local_path']: r['sha256'] for r in records}
        for name in sorted(package_assets):
            self.assertEqual(recorded.get('assets/' + name), file_sha256(PACKAGE / 'assets' / name), name)
        for row in records:
            if 'shared_path' in row:
                self.assertEqual((PACKAGE / row['local_path']).read_bytes(), (ROOT / row['shared_path']).read_bytes())
                self.assertLessEqual(row['glyph_comparison']['max_mean_channel_error'], 0.02)
        eu = ROOT / 'docs/renderers/web/assets/jbp3600a_eu_en'
        for name, origin in EU_REUSE.items():
            self.assertEqual((PACKAGE / 'assets' / name).read_bytes(), (eu / origin).read_bytes(), name)
        decisions = read(PACKAGE / 'audit/asset-decisions.json')
        self.assertEqual(sorted(d['local_path'] for d in decisions), sorted(recorded))


if __name__ == '__main__':
    unittest.main()
