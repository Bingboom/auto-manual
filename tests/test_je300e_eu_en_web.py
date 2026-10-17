"""JE-300E EU English Git-only release: source identity, operator acceptance, word coverage, shared-IR replay, admissions."""
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
PACKAGE = ROOT / 'data/manual_sources/JE-300E/EU/en/git-20261016-50b910fd'
SOURCE_FILE = '55060100007 HTE147300A-EU-JAK-A0 说明书 RoHS REACH_修正.ai'
SOURCE_SHA = '50b910fdd761010f2e0609afae924e4cad2ca109c5a4717d99a4edf294672800'
MARKDOWN = PACKAGE / 'web/en/manual_je300e_eu_en.md'
APPROVED_STATUS = 'operator-approved-git-only-release'
PAGES = [3, *range(7, 25), 97]
# The cover, contents and the FR/ES/DE/IT bodies are not part of the English Web body.
CHAPTERS = [
    ('introduction', 'IMPORTANT'), ('safety', 'IMPORTANT SAFETY INFORMATION'),
    ('symbols', 'MEANING OF SYMBOLS'), ('in_the_box', "WHAT'S IN THE BOX"),
    ('product_overview', 'PRODUCT OVERVIEW'), ('lcd_display', 'LCD DISPLAY'), ('operations', 'OPERATIONS'),
    ('charging', 'CHARGING'), ('storage', 'STORAGE'), ('troubleshooting', 'TROUBLESHOOTING'),
    ('specifications', 'SPECIFICATIONS'), ('warranty', 'WARRANTY'), ('recycling', 'RETURN FOR RECYCLING SERVICE'),
    ('serial_number', 'HOW TO READ YOUR SERIAL NUMBER'), ('eu-declaration', 'EU Regulations'),
]
COMPONENTS = {
    'HB-CALLOUT-STRIP': 11, 'HB-SPECIAL-INBOX': 1, 'HB-SPECIAL-REFERENCE-FIGURE': 15, 'HB-TABLE-LCD-ICON': 1,
    'HB-TABLE-LCD-MODE': 1, 'HB-TABLE-REFERENCE': 1, 'HB-TABLE-SPEC': 4, 'HB-TABLE-SYMBOL-ICON': 1,
    'HB-TABLE-SYMBOL-SIGNAL': 1, 'HB-TABLE-TROUBLESHOOTING': 1, 'HB-WARRANTY-LEAD': 1,
    'HB-WARRANTY-SECTION': 5, 'HB-WARRANTY-YEARS': 1,
}
SHARED_SYMBOLS = 'docs/renderers/web/assets/shared/symbols/native-v1/'


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rebuild_module = load('je300e_eu_en_rebuild', PACKAGE / 'rebuild.py')


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


def rebuild(output: Path, root: Path | None = None) -> None:
    with redirect_stdout(io.StringIO()):
        if root is None:
            rebuild_module.rebuild(output)
        else:
            with mock.patch.object(rebuild_module, 'SOURCE_ROOT', root):
                rebuild_module.rebuild(output)


def link_or_copy(source: str, destination: str) -> None:
    """The 22.7 MB booklet is only read; a hard link spares the copy where the filesystem allows."""
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def page() -> BeautifulSoup:
    return BeautifulSoup(MARKDOWN.read_text(encoding='utf-8'), 'html.parser')


class Je300eEuEnWebTests(unittest.TestCase):
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
        shutil.copytree(PACKAGE, dest, ignore=shutil.ignore_patterns('web', '__pycache__', '*.ai'))
        link_or_copy(str(PACKAGE / SOURCE_FILE), str(dest / SOURCE_FILE))
        manifest = read(dest / 'source_manifest.json')
        manifest['inputs'] = [row for row in manifest['inputs'] if not row['path'].startswith('web/')]
        write(dest / 'source_manifest.json', manifest)
        return dest

    def test_identity_and_archive(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['target'], {'model': 'JE-300E', 'region': 'EU', 'languages': ['en'],
                                              'technical_version': PACKAGE.name,
                                              'printed_manual_version': 'HTE147300A-EU-JAK-A0'})
        self.assertTrue(PACKAGE.name.endswith('-' + SOURCE_SHA[:8]))
        original = manifest['original_source']
        self.assertEqual((original['filename'], original['sha256']), (SOURCE_FILE, SOURCE_SHA))
        data = (PACKAGE / SOURCE_FILE).read_bytes()
        self.assertLessEqual(len(data), 32 * 1024 * 1024)
        self.assertEqual(hashlib.sha256(data).hexdigest(), SOURCE_SHA)
        # An added-locales package pins this repository path instead of copying the booklet.
        part, = original['archive_parts']
        self.assertEqual((ROOT / part['path']).resolve(), (PACKAGE / SOURCE_FILE).resolve())
        self.assertEqual(part['sha256'], SOURCE_SHA)
        self.assertEqual(read(PACKAGE / 'source/en/content.json')['source_sha256'], SOURCE_SHA)
        self.assertEqual(manifest['included_pages']['en']['physical_pages'], PAGES)
        self.assertEqual(manifest['web_roots'], {'en': 'web/en'})
        files = sorted(path for path in inventory(PACKAGE) if path != 'source_manifest.json')
        self.assertEqual(sorted(row['path'] for row in manifest['inputs']), files)

    def test_the_operator_acceptance_binds_every_source_input(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['publication_status'], APPROVED_STATUS)
        approval = read(PACKAGE / 'source/approval.json')
        self.assertEqual(approval['target'], {key: manifest['target'][key]
                                              for key in ('model', 'region', 'technical_version')})
        self.assertEqual(approval['languages'], ['en'])
        self.assertEqual(approval['original_source_sha256'], SOURCE_SHA)
        # Everything but the frozen web/ outputs and the acceptance itself.
        self.assertEqual(approval['reviewed_inputs'],
                         [row for row in manifest['inputs']
                          if not row['path'].startswith('web/') and row['path'] != 'source/approval.json'])
        self.assertEqual((approval['operator_quote'], approval['merge_authorization']), ('做完直接发布', 'MA-313'))
        metadata = read(PACKAGE / 'web/en' / PathSegments.MANUAL_IR_JSON)['metadata']
        self.assertIs(metadata['publication_eligible'], True)
        self.assertEqual(metadata['pending_source_review'], [])
        self.assertEqual(metadata['operator_source_acceptance'], approval)

    def test_every_english_word_in_scope_is_classified(self):
        coverage = read(PACKAGE / 'source/en/coverage.json')
        self.assertEqual([int(p) for p in coverage['pages']], PAGES)
        self.assertEqual(coverage['pages']['3'], [0, 0, 369, 170])  # English half of the front matter
        for key in ['unmapped', 'duplicate_live_copy', 'unused_split_words']:
            self.assertEqual(coverage[key], [], key)
        self.assertEqual(read(PACKAGE / 'source/unmapped.json'), [])
        self.assertEqual([join[:2] for join in coverage['word_joins']], [['organiza-', 'tions']])
        self.assertEqual([s[1] for s in coverage['overlay_splices']], ['®', '®'])
        self.assertTrue(coverage['print_line_breaks'])
        purposes = {s['purpose'].split('/')[0] for s in coverage['selections']}
        self.assertLessEqual(purposes, {'live-copy', 'embedded-art', 'native-symbol', 'native-lcd-icon',
                                        'native-glyph', 'printed-badge', 'printed-folio',
                                        'shared-inbox-live-ordinal'})

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
            intake = load('je300e_eu_en_intake', PACKAGE / 'source/intake.py')
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

    def test_changed_inputs_are_rejected_before_output(self):
        for relative in ['source/en/content.json', 'assets/symbol_weee.png', 'source/presentation.css']:
            with self.subTest(relative=relative):
                source = self.fixture()
                path = source / relative
                data = path.read_bytes()
                path.unlink()
                path.write_bytes(data + b' ')
                with self.assertRaisesRegex(ValueError, re.escape('input changed: ' + relative)):
                    rebuild(self.root / 'output', source)
                self.assertFalse((self.root / 'output').exists())
                shutil.rmtree(source)

    def test_an_acceptance_that_misses_an_input_is_refused_before_output(self):
        source = self.fixture()
        path = source / 'source/approval.json'
        approval = read(path)
        approval['reviewed_inputs'] = approval['reviewed_inputs'][1:]
        write(path, approval)
        manifest = read(source / 'source_manifest.json')
        row = next(row for row in manifest['inputs'] if row['path'] == 'source/approval.json')
        row.update(size=path.stat().st_size, sha256=file_sha256(path))
        write(source / 'source_manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'operator acceptance does not cover these source inputs'):
            rebuild(self.root / 'output', source)
        self.assertFalse((self.root / 'output').exists())

    def test_the_accepted_edition_passes_the_release_admissions(self):
        """D12 enrolled this source in the shared contract; the accepted edition passes every release admission."""
        self.require_pinned_shared_inputs()
        from tools.web.caption_frame_admission import require_caption_frame_admission
        from tools.web.component_admission import require_fresh_component_admission
        from tools.web.language_release_evidence import require_publishable_manual_ir
        from tools.web.symbol_asset_admission import require_symbol_asset_admission

        contract = read(ROOT / 'docs/renderers/contracts/prepared_component_admission.json')
        proposal = read(PACKAGE / 'audit/proposed-component-admission.json')
        self.assertEqual(proposal['source_sha256'], SOURCE_SHA)
        self.assertEqual(contract['source_profiles'][SOURCE_SHA], proposal['source_profile'])
        web = PACKAGE / 'web/en'
        report = require_fresh_component_admission(web, model='JE-300E', region='EU', language='en')
        self.assertEqual(report['issues'], [])
        self.assertEqual(len(require_symbol_asset_admission(web, PACKAGE, read(PACKAGE / 'source_manifest.json'), 'en')), 8)
        require_caption_frame_admission(web)
        require_publishable_manual_ir(web)

    def test_shared_styles_only(self):
        from tools.web.prepared_style_audit import audit_prepared_package_locale

        manifest = read(PACKAGE / 'source_manifest.json')
        report = audit_prepared_package_locale(PACKAGE, PACKAGE / 'web/en', manifest)
        self.assertTrue(report['applicable'])
        self.assertEqual(report['issues'], [])
        self.assertNotIn('shared_component_exceptions', manifest)
        content = (PACKAGE / 'source/en/content.json').read_text(encoding='utf-8')
        self.assertNotRegex(content, r'"class": "[^"]*\b(?:ht|native)-')
        self.assertEqual(report['declared_tables'], 0)  # every table is a shared component
        self.assertNotIn('"style"', content)

    def test_chapters_follow_the_print(self):
        content = read(PACKAGE / 'source/en/content.json')
        self.assertEqual([(c['id'], c['title']) for c in content['chapters']], CHAPTERS)
        text = MARKDOWN.read_text(encoding='utf-8')
        self.assertNotRegex(text, r'(?m)^# ')  # no printed cover title
        self.assertEqual(re.findall(r'(?m)^## (.+)$', text), [title for _, title in CHAPTERS])
        for absent in ['TABLE OF CONTENTS', 'USER MANUAL', 'Félicitations', 'WICHTIGE']:
            self.assertNotIn(absent, text)
        self.assertIn('USB Type-C® and USB-C® are registered trademarks', text)
        self.assertIn('organizations for sorting', text)

    def test_shared_components_carry_the_page(self):
        metadata = read(PACKAGE / 'web/en' / PathSegments.MANUAL_IR_JSON)['metadata']
        self.assertEqual(metadata['component_inventory'], COMPONENTS)
        self.assertEqual(metadata['page_slots'], {cid: 'native/' + cid for cid, _ in CHAPTERS})
        self.assertEqual(metadata['frozen_source_manifest']['original_source']['sha256'], SOURCE_SHA)
        soup = page()
        self.assertFalse(soup.select('figcaption'))  # the print has no figure captions
        self.assertEqual(len(soup.select('figure.hb-warranty-card')), 5)
        # Operator D6: the print's F0-F3 code cells beside one merged measure become one row per code.
        content = read(PACKAGE / 'source/en/content.json')
        rows = next(slot['content'] for ch in content['chapters'] for node in ch['nodes']
                    if node.get('kind') == 'component'
                    and node['component_spec']['component_id'] == 'HB-TABLE-TROUBLESHOOTING'
                    for slot in node['component_spec']['slots'] if slot['role'] == 'rows')
        self.assertEqual([row['code_text'] for row in rows], [f'F{i}' for i in range(10)])
        self.assertEqual({row['measures_text'] for row in rows[:4]}, {'Restart the product.'})

    def test_artwork_is_recorded_shared_or_native(self):
        content = (PACKAGE / 'source/en/content.json').read_text(encoding='utf-8')
        stylesheet = (PACKAGE / 'source/presentation.css').read_text(encoding='utf-8')
        referenced = set(rebuild_module.ASSET_REFERENCE.findall(content + stylesheet))
        package_assets = {p.name for p in (PACKAGE / 'assets').iterdir()}
        self.assertEqual(referenced, package_assets)
        served = PACKAGE / 'web/en/assets'
        self.assertEqual({p.name for p in served.iterdir()}, referenced)
        records = [*read(PACKAGE / 'source/figures.json'), *read(PACKAGE / 'source/symbols.json'),
                   *read(PACKAGE / 'source/glyphs.json')]
        recorded = {r['local_path']: r['sha256'] for r in records}
        for name in sorted(package_assets):
            self.assertEqual(recorded.get('assets/' + name), file_sha256(PACKAGE / 'assets' / name), name)
            self.assertEqual((served / name).read_bytes(), (PACKAGE / 'assets' / name).read_bytes(), name)
        for row in read(PACKAGE / 'source/symbols.json'):
            self.assertTrue(row['shared_path'].startswith(SHARED_SYMBOLS))
            self.assertEqual((PACKAGE / row['local_path']).read_bytes(), (ROOT / row['shared_path']).read_bytes())
            self.assertLessEqual(row['glyph_comparison']['max_mean_channel_error'], 0.02)
        decisions = read(PACKAGE / 'audit/asset-decisions.json')
        self.assertEqual(sorted(d['final']['path'] for d in decisions), sorted(recorded))


if __name__ == '__main__':
    unittest.main()
