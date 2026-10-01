"""Native source completeness through the existing solar CLI, IR and Web lane."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unicodedata
import unittest

from bs4 import BeautifulSoup

from tools.manual_ir import read_manual_ir
from tools.prepared_component_coverage import audit_prepared_component_coverage
from tools.prepared_component_policy import resolve_prepared_component_policy
from tools.web_component_admission import require_fresh_component_admission
from tools.web_document_ir import render_document_fragments

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'data/manual_sources/JS-100I/EU/added-locales/2026-09-28'
LANGUAGES = ('fr', 'es', 'de', 'it', 'uk', 'pt', 'nl', 'pl')


def normalized(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKC', value).casefold() if c.isalnum())


class SolarJs100iEuLocalesTest(unittest.TestCase):
    def test_source_inventory_pins_all_inputs(self) -> None:
        manifest = json.loads((SNAPSHOT / 'source_manifest.json').read_text())
        self.assertEqual(manifest['languages'], list(LANGUAGES))
        for entry in manifest['files']:
            path = ROOT / entry['path']
            self.assertEqual(entry['sha256'], hashlib.sha256(path.read_bytes()).hexdigest(), str(path))
        self.assertEqual(manifest['duplicate_pages']['de'], {'kept': 34, 'omitted': 35})

    def test_every_language_has_its_own_copy_specifications_and_artwork(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / 'staging'
            fake_bin = Path(tmp) / 'bin'
            fake_bin.mkdir()
            pandoc = fake_bin / 'pandoc'
            pandoc.write_text(
                '#!/usr/bin/env python3\nfrom pathlib import Path\nimport sys\n'
                'if "--list-output-formats" in sys.argv:\n'
                '    print("myst"); raise SystemExit(0)\n'
                'Path(sys.argv[sys.argv.index("-o") + 1]).write_text(Path(sys.argv[1]).read_text())\n'
            )
            pandoc.chmod(0o755)
            env = {**os.environ, 'AUTO_MANUAL_PRESENTATION_PROFILE': 'web',
                   'PATH': str(fake_bin) + os.pathsep + os.environ.get('PATH', '')}
            for lang in LANGUAGES:
                with self.subTest(language=lang):
                    result = subprocess.run(
                        [sys.executable, 'build.py', 'md', '--config',
                         'configs/config.solar-eu-multilingual.yaml', '--model', 'JS-100I',
                         '--region', 'EU', '--lang', lang, '--data-root',
                         str(SNAPSHOT / 'phase2' / lang), '--staging-root', str(staging)],
                        cwd=ROOT, env=env, text=True, capture_output=True, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    package = staging / 'docs/_build/JS-100I/EU' / lang / 'md'
                    ir = read_manual_ir(package / 'manual.ir.json')
                    self.assertEqual((ir.language, len(ir.pages), len(ir.asset_refs)), (lang, 9, 22))
                    soup = BeautifulSoup(
                        ''.join(render_document_fragments(ir, package_root=package)), 'html.parser'
                    )
                    source = json.loads((SNAPSHOT / 'source' / f'{lang}.json').read_text())
                    text = normalized(soup.get_text(' ', strip=True))
                    for key in ('spec_notes', 'contact_body', 'customer_body', 'legal'):
                        self.assertIn(normalized(source[key]), text, key)
                    for key in ('unfold', 'fold'):
                        for caption in source[key]:
                            self.assertIn(normalized(caption), text, caption)
                    rows = soup.select('table.hb-spec-table tr')
                    self.assertEqual(len(rows), 21)
                    for rendered, expected in zip(rows, source['spec_rows']):
                        cells = rendered.select('th, td')
                        self.assertEqual(
                            [normalized(cell.get_text()) for cell in cells],
                            [normalized(expected['Row_label_source']), normalized(expected['Value_source'])],
                        )
                    self.assertEqual(len(soup.select('.hb-inbox-card')), 5)
                    self.assertEqual(ir.metadata['illustration_provenance']['language'], lang)
                    # Retain both the source error and its visible connector correction.
                    self.assertIn('USB-C', soup.get_text())
                    self.assertTrue(source['device_port_labels'])
                    admission = require_fresh_component_admission(
                        package, model='JS-100I', region='EU', language=lang,
                    )
                    self.assertEqual(admission['issues'], [])
                    self.assertEqual(len(admission['legacy_debt']), 1)
                    self.assertEqual(admission['legacy_debt'][0]['category'], 'warranty-intake')
                    # The source-authored warranty is exact bounded debt, not a
                    # blanket permission to publish changed legal copy.
                    raw = ir.to_dict()
                    warranty = next(p for p in raw['pages'] if p['page_id'] == f'warranty_{lang}.rst')
                    warranty['blocks'] = []
                    policy = resolve_prepared_component_policy(
                        model='JS-100I', region='EU', language=lang,
                    )
                    self.assertTrue(audit_prepared_component_coverage(raw, policy)['issues'])


if __name__ == '__main__':
    unittest.main()
