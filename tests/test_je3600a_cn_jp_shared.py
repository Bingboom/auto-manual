"""Shared-component editions of the JE-3600A CN and JP manuals: shared styles, unchanged copy, admission and replay."""
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
BASE = ROOT / 'data/manual_sources/JE-3600A'
APPROVED_STATUS = 'operator-approved-git-only-release'
CANDIDATE_STATUS = 'git-only-source-candidate'
EDITIONS = {
    'JP': {
        'package': BASE / 'JP/git-20261015-fd06cd04-shared',
        'base': BASE / 'JP/git-20261013-fd06cd04-web-layout',
        'language': 'ja',
        'pdf': 'Jackery ポータブル電源 3600 Plus 取扱説明書.pdf',
        'source_sha': 'fd06cd04653d0c336dfa119ccfb29cbee79fecf4508feee9ccda61df5eeb8dd6',
        'markdown': 'manual_je3600a_jp_ja.md',
        # Header rows the shared symbol tables add (1 signal + 5 two-panel tables), the signal
        # badges' ⚠, the repeated LCD numbers ④ ⑲ and the App inline control's ＋.
        'added': Counter({'記': 11, '号': 11, '意': 11, '味': 11, '⚠': 2, '4': 1, '9': 1, '+': 1}),
        # Inbox numbers drawn by the shared cards (1 cancels with the repeated 19), and the
        # "Li-ion" caption that the shared recycling symbol carries in its artwork.
        'removed': Counter({'2': 1, '3': 1, 'L': 1, 'i': 2, '-': 1, 'o': 1, 'n': 1}),
        'components': {'HB-CALLOUT-STRIP': 16, 'HB-SPECIAL-APP': 2, 'HB-SPECIAL-INBOX': 1,
                       'HB-SPECIAL-REFERENCE-FIGURE': 21, 'HB-TABLE-KEY-COMBINATIONS': 1, 'HB-TABLE-LCD-ICON': 1,
                       'HB-TABLE-LCD-MODE': 1, 'HB-TABLE-SPEC': 4, 'HB-TABLE-SYMBOL-ICON': 5,
                       'HB-TABLE-SYMBOL-SIGNAL': 1, 'HB-TABLE-TROUBLESHOOTING': 1, 'HB-WARRANTY-SECTION': 6},
        'symbol_rows': (18, 11),
    },
    'CN': {
        'package': BASE / 'CN/git-20261015-caa5370a-shared',
        'base': BASE / 'CN/git-20261013-caa5370a-web-layout',
        'language': 'zh',
        'pdf': '电小二户外电源 3600 Plus.pdf',
        'source_sha': 'caa5370acac00f053f8a62b02ea0cd60b5efe4fd5c7e7be56c65cc97493681bb',
        'markdown': 'manual_je3600a_cn_zh.md',
        'added': Counter({'4': 1, '9': 1, '+': 1}),
        # Inbox numbers, and the LCD-mode header row 分类 / 操作 / 说明 the shared table does not carry.
        'removed': Counter({'2': 1, '3': 1, '分': 1, '类': 1, '操': 1, '作': 1, '说': 1, '明': 1}),
        'components': {'HB-CALLOUT-STRIP': 16, 'HB-SPECIAL-APP': 2, 'HB-SPECIAL-INBOX': 1,
                       'HB-SPECIAL-REFERENCE-FIGURE': 20, 'HB-TABLE-KEY-COMBINATIONS': 1, 'HB-TABLE-LCD-ICON': 1,
                       'HB-TABLE-LCD-MODE': 1, 'HB-TABLE-SPEC': 4, 'HB-TABLE-TROUBLESHOOTING': 1},
        'symbol_rows': (0, 0),
    },
}
SHARED_FILES = ('derive_shared.py', 'rebuild.py', 'source/refresh_manifest.py', 'source/symbol_admission.py')


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REBUILD = {region: load(f'je3600a_{region.lower()}_shared_rebuild', edition['package'] / 'rebuild.py')
           for region, edition in EDITIONS.items()}


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def markdown(directory: Path, edition: dict) -> str:
    return (directory / 'web' / edition['language'] / edition['markdown']).read_text(encoding='utf-8')


def visible_characters(text: str) -> Counter:
    soup = BeautifulSoup(text, 'html.parser')
    for style in soup.find_all('style'):
        style.decompose()
    return Counter(''.join(soup.get_text('').replace('#', '').split()))


def inventory(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): file_sha256(p)
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def shared_inputs_drifted(package: Path) -> list[str]:
    return [row['path'] for row in read(package / 'source_manifest.json')['repo_inputs']
            if not (ROOT / row['path']).is_file() or file_sha256(ROOT / row['path']) != row['sha256']]


def rebuild(region: str, output: Path) -> None:
    with redirect_stdout(io.StringIO()):
        REBUILD[region].rebuild(output, EDITIONS[region]['language'])


def components(content: dict) -> Counter:
    return Counter(re.findall(r'"component_id": "([A-Z0-9-]+)"', json.dumps(content)))


class SharedComponentEditionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def require_pinned_shared_inputs(self, region: str):
        drifted = shared_inputs_drifted(EDITIONS[region]['package'])
        if drifted:
            self.skipTest(f'shared inputs changed since this edition was frozen: {drifted[:3]}')

    def fixture(self, region: str) -> Path:
        dest = self.root / region / 'source'
        shutil.copytree(EDITIONS[region]['package'], dest, ignore=shutil.ignore_patterns('web', '__pycache__'))
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

    def reseal(self, source: Path) -> None:
        manifest = read(source / 'source_manifest.json')
        for row in manifest['inputs']:
            path = source / row['path']
            row.update(sha256=file_sha256(path), size=path.stat().st_size)
        write(source / 'source_manifest.json', manifest)

    def test_identity_lineage_and_candidate_status(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                package, language = edition['package'], edition['language']
                manifest = read(package / 'source_manifest.json')
                self.assertEqual(manifest['target'], {'model': 'JE-3600A', 'region': region,
                                                      'technical_version': package.name, 'languages': [language]})
                self.assertEqual(manifest['derived_from'], {
                    'technical_version': edition['base'].name,
                    'path': edition['base'].relative_to(ROOT).as_posix(),
                    'derivation': 'derive_shared.py'})
                self.assertEqual(manifest['original_source']['sha256'], edition['source_sha'])
                self.assertEqual(file_sha256(package / edition['pdf']), edition['source_sha'])
                files = sorted(path for path in inventory(package) if path != 'source_manifest.json')
                self.assertEqual(sorted(row['path'] for row in manifest['inputs']), files)
                accepted = manifest['publication_status'] == APPROVED_STATUS
                metadata = read(package / 'web' / language / PathSegments.MANUAL_IR_JSON)['metadata']
                self.assertIs(metadata['publication_eligible'], accepted)
                if not accepted:
                    self.assertEqual(manifest['publication_status'], CANDIDATE_STATUS)
                    self.assertFalse((package / 'source/approval.json').exists())

    def test_editions_share_one_derivation(self):
        for relative in SHARED_FILES:
            with self.subTest(relative=relative):
                self.assertEqual((EDITIONS['JP']['package'] / relative).read_bytes(),
                                 (EDITIONS['CN']['package'] / relative).read_bytes())

    def test_frozen_web_is_the_cold_replay(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                self.require_pinned_shared_inputs(region)
                output = self.root / region
                rebuild(region, output)
                self.assertEqual(inventory(output), inventory(edition['package'] / 'web' / edition['language']))

    def test_no_source_drawn_styles_remain(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                package, language = edition['package'], edition['language']
                content = (package / f'source/{language}/content.json').read_text(encoding='utf-8')
                self.assertNotRegex(content, r'\bht-[a-z]')
                self.assertNotIn('"style"', content)
                css = (package / 'source/presentation.css').read_text(encoding='utf-8')
                self.assertNotRegex(css, r'(?i)\b(color|background|border|fill|box-shadow)\s*:')
                self.assertNotRegex(markdown(package, edition), r'class="[^"]*\bht-')

    def test_shared_component_inventory(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                content = read(edition['package'] / f"source/{edition['language']}/content.json")
                self.assertEqual(dict(components(content)), edition['components'])

    def test_frozen_web_passes_the_release_admissions(self):
        from tools.web.caption_frame_admission import require_caption_frame_admission
        from tools.web.component_admission import require_fresh_component_admission
        from tools.web.language_release_evidence import require_publishable_manual_ir

        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                self.require_pinned_shared_inputs(region)
                web = edition['package'] / 'web' / edition['language']
                require_fresh_component_admission(web, model='JE-3600A', region=region,
                                                  language=edition['language'])
                require_caption_frame_admission(web)
                with self.assertRaisesRegex(RuntimeError, 'pending source review'):
                    require_publishable_manual_ir(web)

    def test_symbol_admission_is_recorded_not_waived(self):
        from tools.web.symbol_asset_admission import require_symbol_asset_admission

        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                self.require_pinned_shared_inputs(region)
                package, language = edition['package'], edition['language']
                manifest = read(package / 'source_manifest.json')
                report = read(package / 'audit/symbol-admission.json')
                admitted, blocked = edition['symbol_rows']
                self.assertEqual(Counter(row['status'] for row in report),
                                 Counter({k: v for k, v in (('admitted', admitted), ('blocked', blocked)) if v}))
                rows = manifest['symbol_asset_admission']['locales'][language]
                self.assertEqual([r['asset_ref'] for r in rows], [r['asset_ref'] for r in report])
                web = package / 'web' / language
                if blocked:
                    with self.assertRaisesRegex(RuntimeError, 'symbol asset admission failed'):
                        require_symbol_asset_admission(web, package, manifest, language)
                else:
                    self.assertEqual(require_symbol_asset_admission(web, package, manifest, language), [])

    def test_acceptance_covers_exactly_the_reviewed_source(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                self.require_pinned_shared_inputs(region)
                source = self.fixture(region)
                manifest = read(source / 'source_manifest.json')
                manifest['publication_status'] = APPROVED_STATUS
                write(source / 'source_manifest.json', manifest)
                module = REBUILD[region]
                with mock.patch.object(module, 'SOURCE_ROOT', source):
                    with self.assertRaisesRegex(ValueError, 'operator acceptance does not cover'):
                        rebuild(region, self.root / region / 'missing')
                    self.assertFalse((self.root / region / 'missing').exists())
                    approval = {
                        'target': {key: manifest['target'][key] for key in ('model', 'region', 'technical_version')},
                        'original_source_sha256': edition['source_sha'],
                        'reviewed_inputs': manifest['inputs'],
                        'operator_quote': 'operator acceptance',
                        'merge_authorization': 'operator review and merge of the engineering PR',
                    }
                    write(source / 'source/approval.json', approval)
                    rebuild(region, self.root / region / 'accepted')
                    metadata = read(self.root / region / 'accepted' / PathSegments.MANUAL_IR_JSON)['metadata']
                    self.assertTrue(metadata['publication_eligible'])
                    css = source / 'source/presentation.css'
                    css.write_text(css.read_text(encoding='utf-8') + '\nbody { color: red; }\n', encoding='utf-8')
                    self.reseal(source)
                    with self.assertRaisesRegex(ValueError, 'operator acceptance does not cover'):
                        rebuild(region, self.root / region / 'changed')
                    self.assertFalse((self.root / region / 'changed').exists())

    def test_changed_inputs_are_rejected_before_output(self):
        for region, edition in EDITIONS.items():
            for relative in [f"source/{edition['language']}/content.json", 'assets/lcd-wifi.png',
                             'source/presentation.css']:
                with self.subTest(region=region, relative=relative):
                    source = self.fixture(region)
                    path = source / relative
                    path.write_bytes(path.read_bytes() + b' ')
                    with mock.patch.object(REBUILD[region], 'SOURCE_ROOT', source):
                        with self.assertRaisesRegex(ValueError, re.escape('input changed: ' + relative)):
                            rebuild(region, self.root / region / 'output')
                    self.assertFalse((self.root / region / 'output').exists())
                    shutil.rmtree(source)

    def test_navigation_is_unchanged(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                def titles(directory):
                    return re.findall(r'(?m)^# (.+)$', markdown(directory, edition))
                self.assertEqual(titles(edition['package']), titles(edition['base']))

    def test_visible_copy_is_the_released_copy_with_listed_changes(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                released = visible_characters(markdown(edition['base'], edition))
                shared = visible_characters(markdown(edition['package'], edition))
                self.assertEqual(shared - released, edition['added'])
                self.assertEqual(released - shared, edition['removed'])

    def test_each_locale_carries_only_its_referenced_artwork(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                package = edition['package']
                text = ((package / f"source/{edition['language']}/content.json").read_text(encoding='utf-8')
                        + (package / 'source/presentation.css').read_text(encoding='utf-8'))
                expected = set(re.findall(r'assets/([A-Za-z0-9_.-]+)', text))
                self.assertEqual({p.name for p in (package / 'assets').iterdir()}, expected)
                web_assets = package / 'web' / edition['language'] / 'assets'
                self.assertEqual({p.name for p in web_assets.iterdir()}, expected)
                for path in web_assets.iterdir():
                    self.assertEqual(path.read_bytes(), (package / 'assets' / path.name).read_bytes(), path.name)

    def test_artwork_is_the_released_artwork_or_a_viewbox_crop_of_it(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                package, base = edition['package'], edition['base'] / 'assets'
                for path in (package / 'assets').iterdir():
                    original = base / path.name
                    if original.exists():
                        self.assertEqual(path.read_bytes(), original.read_bytes(), path.name)
                        continue
                    stem = re.sub(r'-(crop|card-\d|store|qr)$', '', path.stem)
                    source = (base / f'{stem}.svg').read_text(encoding='utf-8')
                    cropped = path.read_text(encoding='utf-8')
                    # Only the root element's width, height and viewBox differ.
                    self.assertEqual(cropped[cropped.index('>') + 1:], source[source.index('>') + 1:], path.name)

    def test_derivation_is_reproducible(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                self.require_pinned_shared_inputs(region)
                package = edition['package']
                source = self.root / region / 'derived'
                shutil.copytree(package, source, ignore=shutil.ignore_patterns('web', '__pycache__'))
                module = load(f'je3600a_{region.lower()}_shared_derive', package / 'derive_shared.py')
                with mock.patch.object(module, 'HERE', source), redirect_stdout(io.StringIO()):
                    module.derive()
                frozen = {path: digest for path, digest in inventory(package).items() if not path.startswith('web/')}
                self.assertEqual(inventory(source), frozen)


if __name__ == '__main__':
    unittest.main()
