"""JE-1000F EU uk/pt/nl/pl: shared symbol rows plus the Web-only battery row."""
from __future__ import annotations

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
NINE = ROOT / 'manual_sources/JE-1000F/EU/nine-language'
PACKAGE = NINE / 'git-20261102-30bcad90-shared-symbols/four-language'
BASE = NINE / 'git-20260930-c38415f5-shared-keys/four-language'
LANGUAGES = ('uk', 'pt', 'nl', 'pl')
BATTERY = 'battery-weee/crossed-bin-no-bar'
DONORS = {'uk': 'manual_sources/JE-3600A/EU/es/1465-20261010-r1/HTE139-EU-9国说明书-0924.ai',
          **{lang: 'manual_sources/JE-2000F/EU/nine-language/git-20261010-1465-web/three-language/'
                   'source/JE-2000F_修正版.ai' for lang in ('pt', 'nl', 'pl')}}


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def symbol_spec(ir: dict) -> dict:
    return next(block['payload']['component_spec'] for page in ir['pages'] for block in page['blocks']
                if (block['payload'].get('component_spec') or {}).get('component_id') == 'HB-TABLE-SYMBOL-ICON')


def visible(path: Path) -> str:
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    for style in soup.find_all('style'):
        style.decompose()
    return ' '.join(soup.get_text(' ').split())


class FourLanguagePackageTests(unittest.TestCase):
    def test_every_symbol_row_is_a_shared_variant_and_battery_comes_last(self):
        for language in LANGUAGES:
            ir = read(PACKAGE / 'web' / language / 'manual.ir.json')
            rows = ir['metadata']['shared_symbol_revision']['rows']
            spec = symbol_spec(ir)
            self.assertEqual([r['asset_ref'] for r in rows], [a['asset_ref'] for a in spec['assets']])
            self.assertEqual(rows[-1]['shared_symbol_key'], BATTERY)
            panels = next(slot['content'] for slot in spec['slots'] if slot['role'] == 'panels')
            self.assertEqual([len(panel) for panel in panels], [4, 4])
            for row in rows:
                with self.subTest(language=language, key=row['shared_symbol_key']):
                    require_shared_symbol_binding(row, PACKAGE / 'web' / language / row['asset_ref'])
                    if 'replaced_asset_ref' in row:
                        self.assertFalse((PACKAGE / 'web' / language / row['replaced_asset_ref']).exists())

    def test_every_row_is_admitted_against_the_revised_ai_or_its_donor_row(self):
        from tools.web.symbol_asset_admission import require_symbol_asset_admission
        manifest = read(PACKAGE / 'source_manifest.json')
        source = manifest['original_source']
        self.assertEqual(source['filename'], 'source/JE-1000F_修正版.ai')
        self.assertEqual(file_sha256(PACKAGE / source['filename']), source['sha256'])
        self.assertEqual(manifest['superseded_original_source']['sha256'][:8], 'c38415f5')
        for language in LANGUAGES:
            with self.subTest(language=language):
                report = require_symbol_asset_admission(PACKAGE / 'web' / language, PACKAGE, manifest, language)
                self.assertEqual(len(report), 8)
                self.assertEqual([r['glyph_waiver'] for r in report if 'glyph_waiver' in r],
                                 [f'JE1000F-1465-{language.upper()}-SYMBOL-LI-ION'])
                self.assertEqual([r['web_only_row'] for r in report if 'web_only_row' in r],
                                 [f'JE1000F-EU-{language.upper()}-WEB-BATTERY'])
                bound = manifest['symbol_asset_admission']['locales'][language][-1]
                self.assertEqual(bound['donor_source']['path'], DONORS[language])

    def test_visible_text_adds_only_the_donor_battery_caption(self):
        for language in LANGUAGES:
            name = f'manual_je1000f_eu_{language}.md'
            caption = read(PACKAGE / 'source_manifest.json')['symbol_asset_admission']['locales'][language][-1][
                'caption_text']
            with self.subTest(language=language):
                after = visible(PACKAGE / 'web' / language / name)
                before = visible(BASE / 'web' / language / name)
                self.assertIn(caption, after)
                self.assertNotIn(caption, before)
                self.assertEqual(sorted(after.replace(' ', '')),
                                 sorted(before.replace(' ', '') + caption.replace(' ', '')))

    def test_publication_follows_the_reviewed_markdown(self):
        approval = read(PACKAGE / 'approval.json')
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(approval['operator_quote'], '上线提交发布')
        self.assertEqual(approval['target']['languages'], list(LANGUAGES))
        reviewed = all(
            file_sha256(PACKAGE / 'web' / lang / f'manual_je1000f_eu_{lang}.md')
            == approval['reviewed_candidate']['markdown_sha256'][lang] for lang in LANGUAGES)
        self.assertTrue(reviewed)
        self.assertEqual(manifest['publication_status'], 'operator-approved-git-only-release')
        for language in LANGUAGES:
            with self.subTest(language=language):
                metadata = read(PACKAGE / 'web' / language / 'manual.ir.json')['metadata']
                self.assertTrue(metadata['publication_eligible'])
                self.assertEqual(metadata['pending_source_review'], [])
                self.assertEqual(metadata['operator_release_approval'], approval)

    def test_manifest_locks_inputs_and_cold_replay_is_stable(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        for record in manifest['inputs']:
            self.assertEqual(file_sha256(PACKAGE / record['path']), record['sha256'], record['path'])
        for language in LANGUAGES:
            with self.subTest(language=language), tempfile.TemporaryDirectory() as tmp:
                web = Path(tmp) / language
                shutil.copytree(PACKAGE / 'web' / language, web)
                name = f'manual_je1000f_eu_{language}.md'
                (web / name).unlink()
                replay_package(web)
                self.assertEqual(file_sha256(web / name), file_sha256(PACKAGE / 'web' / language / name))


if __name__ == '__main__':
    unittest.main()
