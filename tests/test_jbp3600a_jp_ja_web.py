"""JBP-3600A JP Japanese Git-only release: sheet identity, word coverage, artwork, acceptance, shared-IR replay."""
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
PACKAGE = ROOT / 'data/manual_sources/JBP-3600A/JP/ja/git-20261014-56860f2f'
SOURCE_SHA = '56860f2f24a11f4a1ccc7fa8392299b6400b3aa36b669451c376fd310eb9160e'
MARKDOWN = PACKAGE / 'web/ja/manual_jbp3600a_jp_ja.md'
# Printed pages 01-10 (panels 3-12) in the order of the printed contents.
CHAPTERS = [
    ('safety', '安全上のご注意'), ('inbox', '同梱品'), ('overview', '各部の名称'), ('lcd', '液晶画面'),
    ('usage', '製品の使用方法について'), ('power-station', 'ポータブル電源との併用'), ('charging', '充電方法'),
    ('troubleshooting', 'トラブルシューティング'), ('specifications', '主な仕様'), ('warranty', '保証について'),
]
COMPONENTS = {'HB-CALLOUT-STRIP': 4, 'HB-SPECIAL-INBOX': 1, 'HB-SPECIAL-REFERENCE-FIGURE': 10,
              'HB-TABLE-TROUBLESHOOTING': 1, 'HB-WARRANTY-SECTION': 6}
# Cover, contents and the production metadata around the panels stay out of the Web body.
ABSENT = ['目次', 'お買い上げありがとうございます', '国内専用', 'HTP0113600A', '16-0102-000060', '第一次发行',
          '成品尺寸', '折页', '产品料号']
EXCLUDED = {'printed-cover', 'contents', 'production-metadata'}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rebuild_module = load('jbp3600a_jp_ja_rebuild', PACKAGE / 'rebuild.py')


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


def pymupdf_pinned() -> bool:
    try:
        import pymupdf
    except ImportError:  # pragma: no cover - repository dependency
        return False
    return tuple(pymupdf.version[:2]) == ('1.28.0', '1.29.0')


class Jbp3600aJpJaWebTests(unittest.TestCase):
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
        self.assertEqual({k: manifest['target'][k] for k in ('model', 'region', 'languages', 'technical_version',
                                                             'printed_manual_version')},
                         {'model': 'JBP-3600A', 'region': 'JP', 'languages': ['ja'],
                          'technical_version': PACKAGE.name, 'printed_manual_version': 'V0.1'})
        self.assertEqual(manifest['target']['internal_code'], 'HTP0113600A')
        original = manifest['original_source']
        self.assertEqual(original['sha256'], SOURCE_SHA)
        digest = hashlib.sha256()
        for part in original['archive_parts']:
            data = (PACKAGE / part['path']).read_bytes()
            self.assertLessEqual(len(data), 32 * 1024 * 1024)
            digest.update(data)
        self.assertEqual(digest.hexdigest(), SOURCE_SHA)
        self.assertEqual(read(PACKAGE / 'source/ja/content.json')['source_sha256'], SOURCE_SHA)
        self.assertEqual(manifest['included_pages']['ja']['panels'], list(range(3, 13)))
        self.assertEqual(len(manifest['panel_grid']['origins']), 12)
        self.assertEqual(manifest['web_roots'], {'ja': 'web/ja'})
        files = sorted(path for path in inventory(PACKAGE) if path != 'source_manifest.json')
        self.assertEqual(sorted(row['path'] for row in manifest['inputs']), files)

    def test_the_operator_acceptance_binds_every_source_input(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['publication_status'], 'operator-approved-git-only-release')
        approval = read(PACKAGE / 'source/approval.json')
        self.assertEqual(approval['target'], {key: manifest['target'][key]
                                              for key in ('model', 'region', 'technical_version')})
        self.assertEqual(approval['original_source_sha256'], SOURCE_SHA)
        # Everything but the frozen web/ outputs and the acceptance itself.
        self.assertEqual(approval['reviewed_inputs'],
                         [row for row in manifest['inputs']
                          if not row['path'].startswith('web/') and row['path'] != 'source/approval.json'])
        self.assertEqual((approval['operator_quote'], approval['merge_authorization']),
                         ('合入了，上线授权你合入', 'MA-303'))
        metadata = read(PACKAGE / 'web/ja' / PathSegments.MANUAL_IR_JSON)['metadata']
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
        for dependency in manifest['repo_inputs']:
            current = ROOT / dependency['path']
            dependency.update(size=current.stat().st_size, sha256=file_sha256(current))
        write(source / 'source_manifest.json', manifest)
        with mock.patch.object(rebuild_module, 'SOURCE_ROOT', source):
            with self.assertRaisesRegex(ValueError, 'operator acceptance does not cover these source inputs'):
                rebuild(self.root / 'output')
        self.assertFalse((self.root / 'output').exists())

    def test_every_word_on_the_sheet_is_classified(self):
        coverage = read(PACKAGE / 'source/ja/coverage.json')
        self.assertEqual(coverage['panels'], list(range(1, 13)))
        self.assertEqual(coverage['classified_word_count'], coverage['sheet_word_count'])
        for key in ['unmapped', 'duplicate_live_copy', 'unused_recoveries']:
            self.assertEqual(coverage[key], [], key)
        self.assertEqual(read(PACKAGE / 'source/unmapped.json'), [])
        self.assertTrue(coverage['print_line_breaks'])
        purposes = {s['purpose'].split('/')[0] for s in coverage['selections']}
        self.assertLessEqual(purposes, {'live-copy', 'embedded-art', 'printed-folio', 'component-number',
                                        *EXCLUDED})
        # Cover and contents panels, and everything outside the panels, are only ever excluded.
        for selection in coverage['selections']:
            if selection['panel'] in (0, 1, 2):
                self.assertIn(selection['purpose'].split('/')[0], EXCLUDED, selection['bbox'])

    def test_intake_reproduces_the_frozen_source(self):
        if not pymupdf_pinned():
            self.skipTest('geometry is validated for PyMuPDF 1.28.0 / MuPDF 1.29.0 (requirements.lock)')
        source = self.fixture()
        saved_path, saved_native = list(sys.path), sys.modules.get('native')
        try:
            native = load('native', PACKAGE / 'source/native.py')
            native.SOURCE = source
            sys.modules['native'] = native  # intake.py imports its sibling by this name
            intake = load('jbp3600a_jp_ja_intake', PACKAGE / 'source/intake.py')
            with redirect_stdout(io.StringIO()):
                self.assertEqual(intake.make(), [])
        finally:
            sys.path[:] = saved_path
            if saved_native is None:
                sys.modules.pop('native', None)
            else:
                sys.modules['native'] = saved_native
        for relative in ['source/ja/content.json', 'source/ja/coverage.json']:
            self.assertEqual((source / relative).read_bytes(), (PACKAGE / relative).read_bytes(), relative)

    def test_frozen_web_is_the_cold_replay(self):
        self.require_pinned_shared_inputs()
        output = self.root / 'ja'
        rebuild(output)
        self.assertEqual(inventory(output), inventory(PACKAGE / 'web/ja'))

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
        self.assertEqual(_file_inventory(PACKAGE, excluded_roots=(path, *caches)), _source(manifest, path, 'ja')[1])
        _, inputs, root = _source(manifest, path, 'ja')
        web = PACKAGE / root
        self.assertEqual(_file_inventory(web), _locale_inventory(inputs, root))
        require_fresh_component_admission(web, model='JBP-3600A', region='JP', language='ja')
        require_symbol_asset_admission(web, PACKAGE, manifest, 'ja')
        require_caption_frame_admission(web)
        require_publishable_manual_ir(web)

    def test_changed_inputs_are_rejected_before_output(self):
        for relative in ['source/ja/content.json', 'assets/signal-triangle.svg', 'source/presentation.css']:
            with self.subTest(relative=relative):
                source = self.fixture()
                path = source / relative
                path.write_bytes(path.read_bytes() + b' ')
                with mock.patch.object(rebuild_module, 'SOURCE_ROOT', source):
                    with self.assertRaisesRegex(ValueError, re.escape('input changed: ' + relative)):
                        rebuild(self.root / 'output')
                self.assertFalse((self.root / 'output').exists())
                shutil.rmtree(source)

    def test_a_changed_pdf_is_rejected_before_output(self):
        source = self.fixture()
        part = source / 'source/pdf-archive/part-001.bin'
        data = bytearray(part.read_bytes())
        data[-2] ^= 1
        part.write_bytes(bytes(data))
        with mock.patch.object(rebuild_module, 'SOURCE_ROOT', source):
            with self.assertRaisesRegex(ValueError, 'authoritative PDF identity changed'):
                rebuild(self.root / 'output')
        self.assertFalse((self.root / 'output').exists())

    def test_chapters_follow_the_print(self):
        content = read(PACKAGE / 'source/ja/content.json')
        self.assertEqual([(c['id'], c['title']) for c in content['chapters']], CHAPTERS)
        text = MARKDOWN.read_text(encoding='utf-8')
        self.assertNotRegex(text, r'(?m)^# ')  # no printed cover title
        self.assertEqual(re.findall(r'(?m)^## (.+)$', text), [title for _, title in CHAPTERS])
        visible = page().get_text()
        for absent in ABSENT:
            self.assertNotIn(absent, visible)
        # Japanese wraps join without a space; print breaks stay line breaks.
        self.assertIn('お子様から目を離さないようにしてください。', visible)
        self.assertIn('1 年間 0~25°C', visible)

    def test_shared_components_carry_the_page(self):
        metadata = read(PACKAGE / 'web/ja' / PathSegments.MANUAL_IR_JSON)['metadata']
        self.assertEqual(metadata['component_inventory'], COMPONENTS)
        soup = page()
        self.assertFalse(soup.select('figcaption'))  # the print has no figure captions
        labels = [c.get_text(strip=True) for c in soup.select('table.manual-callout-table td.manual-callout-label')]
        self.assertEqual(labels, ['説明', 'ご注意', 'ご注意', '警告'])
        lockups = soup.select('table.hb-source-warning-lockup .hb-warning-lockup img')
        self.assertEqual([img['src'] for img in lockups], ['assets/signal-triangle.svg'])
        self.assertEqual(len(soup.select('figure.hb-warranty-card')), 6)
        self.assertEqual(soup.select_one('img.native-inline-glyph')['src'], 'assets/inline-connected-batteries.svg')

    def test_labelled_figures_carry_live_labels_on_text_free_art(self):
        soup = page()
        records = {r['slot']: r for r in read(PACKAGE / 'source/figures.json')}
        live = {slot: r for slot, r in records.items() if r.get('live_labels')}
        self.assertEqual(set(live), {'overview', 'lcd-map', 'power-on-off', 'clearance', 'locking',
                                     'ac-charging', 'solar-charging'})
        for slot, record in live.items():
            figure = soup.select_one(f'figure[data-reference-id="{slot}"]')
            self.assertIn('hb-base-art-live-copy', figure['class'], slot)
            labels = [label.get_text(strip=True) for label in figure.select('.hb-reference-live-label')]
            self.assertEqual(sorted(labels), sorted(label['text'] for label in record['live_labels']), slot)
            self.assertEqual(record['acquisition']['kind'], 'textless-crop')
        # Left label column first, then the right one.
        overview = soup.select_one('figure[data-reference-id="overview"]')
        self.assertEqual([label.get_text(strip=True) for label in overview.select('.hb-reference-live-label')][-2:],
                         ['主電源ボタン', 'ディスプレイ'])

    def test_tables_keep_the_print_structure(self):
        soup = page()
        signal = soup.select_one('table.native-signal')
        self.assertIsNone(signal.find('thead'))
        self.assertEqual([c.get_text(strip=True) for c in signal.select('td.native-signal-label')],
                         ['警告', '注意', '説明', 'ヒント'])
        self.assertEqual(len(soup.select('table.native-symbols tbody > tr')), 8)
        # The shared troubleshooting table (JBP-2000B reference) carries the print's own header row.
        trouble = soup.select_one('table.hb-troubleshooting-table')
        self.assertEqual([c.get_text(strip=True) for c in trouble.select('thead th')], ['エラーコード', '対処方法'])
        self.assertEqual(len(trouble.select('tbody > tr')), 13)
        spec = soup.select_one('table.native-spec')
        self.assertIsNone(spec.find('thead'))
        self.assertEqual(len(spec.select('tbody > tr')), 10)
        self.assertEqual(spec.select_one('sub').get_text(), '4')
        self.assertEqual(len(spec.select('tbody > tr')[-1].select('br')), 2)

    def test_artwork_is_recorded_reused_or_extracted(self):
        content = (PACKAGE / 'source/ja/content.json').read_text(encoding='utf-8')
        stylesheet = (PACKAGE / 'source/presentation.css').read_text(encoding='utf-8')
        referenced = set(rebuild_module.ASSET_REFERENCE.findall(content + stylesheet))
        package_assets = {p.name for p in (PACKAGE / 'assets').iterdir()}
        self.assertEqual(referenced, package_assets)
        served = PACKAGE / 'web/ja/assets'
        self.assertEqual({p.name for p in served.iterdir()}, referenced)
        records = read(PACKAGE / 'source/figures.json')
        for record in records:
            path = PACKAGE / record['local_path']
            self.assertEqual(file_sha256(path), record['sha256'], record['slot'])
            if record['acquisition']['kind'] == 'reuse':
                self.assertEqual(path.read_bytes(), (ROOT / record['acquisition']['from']).read_bytes(), record['slot'])
        self.assertEqual({'assets/' + name for name in package_assets}, {r['local_path'] for r in records})
        decisions = read(PACKAGE / 'audit/asset-decisions.json')
        self.assertEqual([d['slot'] for d in decisions], [r['slot'] for r in records])

    def test_extracted_artwork_reproduces(self):
        if not pymupdf_pinned():
            self.skipTest('rendering is validated for PyMuPDF 1.28.0 / MuPDF 1.29.0 (requirements.lock)')
        extract = load('jbp3600a_jp_ja_extract', PACKAGE / 'source/extract_assets.py')
        with redirect_stdout(io.StringIO()):
            self.assertEqual(extract.main(True), [])


if __name__ == '__main__':
    unittest.main()
