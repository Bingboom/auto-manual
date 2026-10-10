"""JE-2000F EU pt/nl/pl batch-1465 release: acceptance, UPS callout order and cold replay."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.manual_ir.hashing import file_sha256
from tools.web.frozen_ai_web import replay_package

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'manual_sources/JE-2000F/EU/nine-language/git-20261010-1465-web/three-language'
LANGUAGES = ('pt', 'nl', 'pl')
UPS_ORDER = {'pt': ['CUIDADO', 'AVISO'], 'nl': ['OPGELET', 'WAARSCHUWING'], 'pl': ['PRZESTROGA', 'OSTRZEŻENIE']}


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def ups_labels(ir) -> list[str]:
    ups = next(page for page in ir['pages'] if page['page_id'] == 'ups')
    labels = []
    for block in ups['blocks']:
        spec = block['payload'].get('component_spec') or {}
        if spec.get('component_id') == 'HB-CALLOUT-STRIP':
            labels.append(next(s['content'] for s in spec['slots'] if s['role'] == 'label'))
    return labels


class Batch1465ReleaseTests(unittest.TestCase):
    def test_acceptance_is_bound_to_every_language(self):
        approval = read(PACKAGE / 'approval.json')
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(approval['operator_quote'], '上线提交发布')
        self.assertEqual(approval['target']['languages'], list(LANGUAGES))
        self.assertEqual(approval['reviewed_candidate']['batch_1465_changes_sha256'],
                         file_sha256(PACKAGE / 'batch_1465_changes.json'))
        self.assertEqual(manifest['publication_status'], 'operator-approved-git-only-release')
        for language in LANGUAGES:
            metadata = read(PACKAGE / 'web' / language / 'manual.ir.json')['metadata']
            self.assertTrue(metadata['publication_eligible'])
            self.assertEqual(metadata['operator_release_approval'], approval)
            self.assertEqual(metadata['batch_1465']['status'], 'operator-approved-git-only-release')

    def test_ups_caution_precedes_warning_in_every_language(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                labels = ups_labels(read(PACKAGE / 'web' / language / 'manual.ir.json'))
                self.assertEqual(labels, UPS_ORDER[language])

    def test_manifest_inventories_every_package_file(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        files = sorted(p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*')
                       if p.is_file() and p.name != 'source_manifest.json' and '__pycache__' not in p.parts)
        self.assertEqual([row['path'] for row in manifest['inputs']], files)
        for row in manifest['inputs']:
            self.assertEqual(file_sha256(PACKAGE / row['path']), row['sha256'], row['path'])

    def test_cold_replay_matches_committed_markdown(self):
        verification = read(PACKAGE / 'verification.json')
        for language in LANGUAGES:
            with self.subTest(language=language), tempfile.TemporaryDirectory() as temp:
                copy = Path(temp) / language
                shutil.copytree(PACKAGE / 'web' / language, copy)
                markdown = copy / f'manual_je2000f_eu_{language}.md'
                markdown.unlink()
                replay_package(copy)
                self.assertEqual(file_sha256(markdown), verification[language]['markdown_sha256'])
                self.assertEqual(markdown.read_bytes(),
                                 (PACKAGE / 'web' / language / markdown.name).read_bytes())


if __name__ == '__main__':
    unittest.main()
