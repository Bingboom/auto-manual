"""JE-1000H EU: symbol rows reuse shared Web variants (every symbol row in all nine locales)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.manual_ir.hashing import file_sha256
from tools.web.frozen_ai_web import replay_package
from tools.web.shared_symbol_assets import require_shared_symbol_binding

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / 'docs/renderers/web/assets/shared/symbols'
SIX_SOURCE = ROOT / 'manual_sources/JE-1000H/EU/en/2.0'
THREE = ROOT / 'manual_sources/JE-1000H/EU/three-language'
PACKAGE = THREE / 'git-20261026-8bcb378f-shared-symbols'
BASE = THREE / 'git-20261001-8bcb378f-temperature-web'
LANGUAGES = ('pt', 'nl', 'pl')
SIX_KEYS = {
    'read_manual': 'read-manual/book-information',
    'do_not_dismantle': 'do-not-dismantle/screwdriver-prohibited',
    'no_open_flame': 'no-open-flame/fire-match-prohibited',
    'keep_away_from_children': 'keep-away-from-children/adult-child-prohibited',
    'weee': 'weee/crossed-bin-bar',
    'warning_triangle': 'warning/outline-triangle-tinted',
    'li_ion': 'li-ion/recycle-li-ion-32-gray',
}


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def shared_entry(key: str) -> dict:
    (entry,) = [a for a in read(SHARED / 'manifest.json')['assets'] if a['key'] == key]
    return entry


def visible(path: Path) -> str:
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    for style in soup.find_all('style'):
        style.decompose()
    return ' '.join(soup.get_text(' ').split())


class SixLanguageSourceTests(unittest.TestCase):
    def test_symbol_rows_point_at_their_shared_variants(self):
        with (SIX_SOURCE / 'phase2/symbols_blocks.csv').open(encoding='utf-8', newline='') as handle:
            rows = {r['symbol_key']: r for r in csv.DictReader(handle) if r['Model'] == 'JE-1000H'}
        for symbol, key in SIX_KEYS.items():
            with self.subTest(symbol=symbol):
                entry = shared_entry(key)
                path = rows[symbol]['image_path']
                self.assertEqual(path, 'renderers/web/assets/shared/symbols/' + entry['path'])
                self.assertEqual(file_sha256(ROOT / 'docs' / path), entry['sha256'])

    def test_revision_record_names_every_replaced_row(self):
        revision = read(SIX_SOURCE / 'source_manifest.json')['shared_symbol_revision']
        self.assertEqual({r['symbol_key']: r['shared_symbol_key'] for r in revision['rows']}, SIX_KEYS)


class ThreeLanguagePackageTests(unittest.TestCase):
    def test_every_symbol_row_is_a_shared_variant(self):
        for language in LANGUAGES:
            ir = read(PACKAGE / 'web' / language / 'manual.ir.json')
            rows = ir['metadata']['shared_symbol_revision']['rows']
            spec = next(block['payload']['component_spec'] for page in ir['pages'] for block in page['blocks']
                        if (block['payload'].get('component_spec') or {}).get('component_id') == 'HB-TABLE-SYMBOL-ICON')
            self.assertEqual([r['asset_ref'] for r in rows], [a['asset_ref'] for a in spec['assets']])
            for row in rows:
                with self.subTest(language=language, key=row['shared_symbol_key']):
                    require_shared_symbol_binding(row, PACKAGE / 'web' / language / row['asset_ref'])
                    self.assertFalse((PACKAGE / 'web' / language / row['replaced_asset_ref']).exists())

    def test_every_row_is_admitted_against_the_revised_authority_ai(self):
        from tools.web.symbol_asset_admission import require_symbol_asset_admission
        manifest = read(PACKAGE / 'source_manifest.json')
        source = manifest['original_source']
        self.assertEqual(source['filename'], 'source/JE-1000H_修正版.ai')
        self.assertEqual(file_sha256(PACKAGE / source['filename']), source['sha256'])
        self.assertEqual(manifest['superseded_original_source']['sha256'][:8], '8bcb378f')
        for language in LANGUAGES:
            with self.subTest(language=language):
                report = require_symbol_asset_admission(PACKAGE / 'web' / language, PACKAGE, manifest, language)
                self.assertEqual(len(report), 7)
                waived = [r for r in report if 'glyph_waiver' in r]
                self.assertEqual([r['glyph_waiver'] for r in waived],
                                 [f'JE1000H-1465-{language.upper()}-SYMBOL-LI-ION'])

    def test_visible_text_matches_the_approved_package(self):
        for language in LANGUAGES:
            name = f'manual_je1000h_eu_{language}.md'
            with self.subTest(language=language):
                self.assertEqual(visible(PACKAGE / 'web' / language / name),
                                 visible(BASE / 'web' / language / name))

    def test_publication_follows_the_reviewed_markdown(self):
        approval = read(PACKAGE / 'approval.json')
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(approval['operator_quote'], '上线提交发布')
        self.assertEqual(approval['target']['languages'], list(LANGUAGES))
        reviewed = all(
            file_sha256(PACKAGE / 'web' / lang / f'manual_je1000h_eu_{lang}.md')
            == approval['reviewed_candidate']['markdown_sha256'][lang] for lang in LANGUAGES)
        self.assertEqual(manifest['publication_status'].startswith('operator-approved-git-only-release'), reviewed)
        for language in LANGUAGES:
            with self.subTest(language=language):
                metadata = read(PACKAGE / 'web' / language / 'manual.ir.json')['metadata']
                self.assertEqual(metadata['publication_eligible'], reviewed)
                self.assertEqual(metadata['pending_source_review'] == [], reviewed)
                self.assertEqual(metadata.get('operator_release_approval'), approval if reviewed else None)
        six = read(SIX_SOURCE / 'source_manifest.json')['shared_symbol_revision']
        self.assertEqual(six['operator_release_approval']['operator_quote'], '上线提交发布')
        self.assertEqual(six['status'], 'operator-approved-git-only-release')
        self.assertTrue(reviewed)

    def test_manifest_locks_inputs_and_cold_replay_is_stable(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        for record in manifest['inputs']:
            self.assertEqual(file_sha256(PACKAGE / record['path']), record['sha256'], record['path'])
        for language in LANGUAGES:
            with self.subTest(language=language), tempfile.TemporaryDirectory() as tmp:
                web = Path(tmp) / language
                shutil.copytree(PACKAGE / 'web' / language, web)
                name = f'manual_je1000h_eu_{language}.md'
                (web / name).unlink()
                replay_package(web)
                self.assertEqual(file_sha256(web / name), file_sha256(PACKAGE / 'web' / language / name))


if __name__ == '__main__':
    unittest.main()
