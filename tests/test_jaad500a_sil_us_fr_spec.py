"""French spec-label correction edition of JA-AD500A-SIL US: two labels of copy, shared styles, nothing else."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tests.historical_app_styles import pre_four_control_styles
from tools.manual_ir.hashing import file_sha256
from tools.web.prepared_style_audit import audit_prepared_package_locale
from tools.word.bundle_docx_pandoc import resolve_pandoc_binary

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'manual_sources/JA-AD500A-SIL/US/fr-es/git-20261019-28c58312-fr-spec'
BASE = ROOT / 'manual_sources/JA-AD500A-SIL/US/fr-es/git-20261016-28c58312-solar-voc'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render = load('jaad500a_us_fr_spec_render', PACKAGE / 'render.py')
derive = load('jaad500a_us_fr_spec_derive', PACKAGE / 'derive_fr_spec.py')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def tree(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): file_sha256(p) for p in root.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}


def squeeze(text: str) -> str:
    return ''.join(text.split())


def visible_copy(ir_path: Path) -> str:
    """Every text node of the IR flow in reading order, whitespace removed."""
    def texts(node):
        if isinstance(node, dict):
            for name, value in node.items():
                if name == 'text' and isinstance(value, str):
                    yield value
                else:
                    yield from texts(value)
        elif isinstance(node, list):
            for item in node:
                yield from texts(item)
    raw = read(ir_path)
    return squeeze(''.join(t for page in raw['pages'] for block in page['blocks'] for t in texts(block['payload'])))


class FrenchSpecLabelEditionTests(unittest.TestCase):
    def test_identity_lineage_and_acceptance(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        self.assertEqual(manifest['target']['technical_version'], PACKAGE.name)
        self.assertEqual(manifest['target']['languages'], ['fr'])
        self.assertEqual(manifest['original_source'], read(BASE / 'source_manifest.json')['original_source'])
        self.assertEqual(manifest['derived_from']['manifest_sha256'], file_sha256(BASE / 'source_manifest.json'))
        self.assertEqual(set(manifest['web_roots']), {'fr'})
        if manifest['publication_status'] == render.CANDIDATE:
            self.assertFalse(manifest['publication_eligible'])
            self.assertFalse((PACKAGE / 'source/approval.json').exists())
        else:
            self.assertTrue(manifest['publication_eligible'])
            approval = read(PACKAGE / 'source/approval.json')
            self.assertEqual(approval['target'], render.TARGET)
            self.assertEqual(approval, render.acceptance(PACKAGE, manifest))

    def test_derivation_is_reproducible(self):
        before = tree(PACKAGE)
        derive.main()
        self.assertEqual(before, tree(PACKAGE))

    def test_only_the_declared_french_files_differ_from_the_base(self):
        base = {p: h for p, h in tree(BASE).items()
                if p.startswith(('source/', 'assets/')) and not p.endswith('_es.rst')}
        mine = {p: h for p, h in tree(PACKAGE).items() if p.startswith(('source/', 'assets/'))}
        own = {'source/differences.md', 'source/presentation.css'} | ({'source/approval.json'} & set(mine))
        self.assertEqual(set(mine) - set(base), own - set(base))
        self.assertEqual(set(base) - set(mine), set(derive.NOT_COPIED) - own)
        pages = {name for name, _, _ in derive.CORRECTIONS} | set(derive.STYLED_PAGES)
        changed = {f'source/page/{name}' for name in pages} | own
        for path in sorted(set(mine) - changed):
            self.assertEqual(mine[path], base[path], path)
        for name in sorted(pages):
            self.assertEqual((PACKAGE / 'source/page' / name).read_text(encoding='utf-8'), derive.edited_page(name))

    def test_spec_labels_follow_the_module(self):
        spec = (PACKAGE / 'source/page/spec_fr.rst').read_text(encoding='utf-8')
        self.assertIn('<tr><th rowspan="2">Entrée CC</th><td>11 V–16 V', spec)
        self.assertIn('<tr><th>Sortie CC</th><td>42V–58V', spec)
        printed = (BASE / 'source/page/spec_fr.rst').read_text(encoding='utf-8')
        self.assertIn('<tr><th rowspan="2">Sortie CC</th><td>11 V–16 V', printed)

    def test_rendered_copy_is_the_base_copy_with_only_the_labels_swapped(self):
        base = visible_copy(BASE / 'web/fr/manual.ir.json')
        mine = visible_copy(PACKAGE / 'web/fr/manual.ir.json')
        expected = base.replace('SortieCC11V–16V', '\0').replace('EntréeCC42V–58V', 'SortieCC42V–58V')
        self.assertEqual(mine, expected.replace('\0', 'EntréeCC11V–16V'))
        self.assertNotEqual(mine, base)

    def test_french_locale_passes_the_shared_style_gate(self):
        manifest = read(PACKAGE / 'source_manifest.json')
        report = audit_prepared_package_locale(PACKAGE, PACKAGE / 'web/fr', manifest)
        self.assertEqual(report['issues'], [])
        self.assertEqual(report['declared_tables'], 1)

    @pre_four_control_styles
    def test_cold_render_matches_committed_web(self):
        # The prepared RST pipeline converts through Pandoc; the CI unit runner has none.
        try:
            subprocess.run([resolve_pandoc_binary(None), '--version'], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest('Pandoc unavailable')
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'source'
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns('web', '__pycache__'))
            report = render.render(source, 'fr', Path(temp) / 'out')
            self.assertEqual(tree(Path(temp) / 'out'), tree(PACKAGE / 'web/fr'))
            self.assertEqual(report['publication_eligible'], read(PACKAGE / 'source_manifest.json')['publication_eligible'])

    def test_release_inventory_covers_every_package_file(self):
        inventory = read(PACKAGE / 'frozen_source_manifest.json')['inputs']
        self.assertEqual([r['path'] for r in inventory],
                         sorted(p for p in tree(PACKAGE) if p != 'frozen_source_manifest.json'))


if __name__ == '__main__':
    unittest.main()
