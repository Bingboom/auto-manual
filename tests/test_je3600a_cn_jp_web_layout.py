"""Web-layout editions of the JE-3600A CN and JP manuals: print layout, unchanged copy, acceptance and replay."""
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

from tests.historical_app_styles import pre_four_control_styles
from tools.manual_ir.hashing import file_sha256
from tools.utils.path_utils import PathSegments

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/manual_sources/JE-3600A'
APPROVED_STATUS = 'operator-approved-git-only-release'
# The reviewed intake read this label from under the parallel-connection drawing; the
# print paints it over (CN p13, JP p18), so the Web edition drops it.
HIDDEN = ['Jackery Explorer 2000 Plus']
# The printed JP cover (p1) is not part of the Web edition (「封面和目录 不用体现在web版面上」).
JP_COVER = [
    'Jackery ポータブル電源 3600 Plus', '国内専用/For use only in Japan',
    'カスタマーサポート: jackery.jp@jackery.com', 'お買い上げありがとうございます。',
    'ご使用の前にこの「取扱説明書」をよくお読みのうえ、正しくお使いください。',
    '特に「安全上のご注意」は、必ずお読みいただき、安全にお使いください。',
    'お読みになったあとは、すぐに取り出せる場所に大切に保管してください。',
    '本製品の取扱説明書は随時更新されますので、最新の取扱説明書は公式サイトでご確認ください。',
]
EDITIONS = {
    'JP': {
        'package': BASE / 'JP/git-20261013-fd06cd04-web-layout',
        'approved': BASE / 'JP/git-20261012-fd06cd04-reviewed',
        'language': 'ja',
        'pdf': 'Jackery ポータブル電源 3600 Plus 取扱説明書.pdf',
        'source_sha': 'fd06cd04653d0c336dfa119ccfb29cbee79fecf4508feee9ccda61df5eeb8dd6',
        'markdown': 'manual_je3600a_jp_ja.md',
        # The print TOC (physical p2) lists exactly these chapters.
        'chapters': ['安全上のご注意', '使用上のご注意', '免責事項', '同梱品', '各部の名称', '液晶画面', '使い方',
                     'UPS 機能', '接続', '充電方法', 'トラブルシューティング', '主な仕様', '保証について',
                     'Jackeryアプリ ユーザーマニュアル'],
        'removed': JP_COVER + HIDDEN,
        'restorations': {'print-wrap-space': 153, 'inline-glyph-placeholder': 2, 'print-order': 1,
                         'print-icon-position': 1, 'hidden-print-text': 1},
    },
    'CN': {
        'package': BASE / 'CN/git-20261013-caa5370a-web-layout',
        'approved': BASE / 'CN/git-20261012-caa5370a-reviewed',
        'language': 'zh',
        'pdf': '电小二户外电源 3600 Plus.pdf',
        'source_sha': 'caa5370acac00f053f8a62b02ea0cd60b5efe4fd5c7e7be56c65cc97493681bb',
        'markdown': 'manual_je3600a_cn_zh.md',
        # The CN print has no TOC; these are its dark title bands, in page order.
        'chapters': ['使用注意安全事项', '包装清单', '产品介绍', '显示屏界面', '产品使用', '不间断电源（UPS）', '连接',
                     '并机连接', '充电方式', '存储', '故障处理', '技术参数', 'APP操作说明书'],
        'removed': HIDDEN,
        'restorations': {'print-wrap-space': 41, 'inline-glyph-placeholder': 2, 'hidden-print-text': 1},
    },
}
# Each edition replaces eight LCD glyphs it reused from another model with this print's own.
NATIVE_LCD_GLYPHS = 8
LCD_ROWS = 24
SHARED_TRIANGLE = 'docs/renderers/web/assets/shared/symbols/native-v1/symbol_warning_triangle.svg'
SHARED_FILES = ('derive_web_layout.py', 'rebuild.py', 'source/refresh_manifest.py')


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REBUILD = {region: load(f'je3600a_{region.lower()}_layout_rebuild', edition['package'] / 'rebuild.py')
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


def characters(values) -> Counter:
    return Counter(''.join(''.join(values).split()))


def inventory(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): file_sha256(p)
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def shared_inputs_drifted(package: Path) -> list[str]:
    """The editions pin their shared renderers; rebuilding against newer ones is refused."""
    return [row['path'] for row in read(package / 'source_manifest.json')['repo_inputs']
            if not (ROOT / row['path']).is_file() or file_sha256(ROOT / row['path']) != row['sha256']]


def rebuild(region: str, output: Path) -> None:
    with redirect_stdout(io.StringIO()):
        REBUILD[region].rebuild(output, EDITIONS[region]['language'])


class WebLayoutEditionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def require_pinned_shared_inputs(self, region: str):
        drifted = shared_inputs_drifted(EDITIONS[region]['package'])
        if drifted:
            self.skipTest(f'shared inputs changed since this edition was frozen: {drifted[:3]}')

    def fixture(self, region: str) -> Path:
        """A source copy without the frozen web/ outputs, rebound to that tree."""
        dest = self.root / region / 'source'
        shutil.copytree(EDITIONS[region]['package'], dest, ignore=shutil.ignore_patterns('web', '__pycache__'))
        manifest = read(dest / 'source_manifest.json')
        manifest['inputs'] = [row for row in manifest['inputs'] if not row['path'].startswith('web/')]
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
                    'technical_version': edition['approved'].name,
                    'path': edition['approved'].relative_to(ROOT).as_posix(),
                    'derivation': 'derive_web_layout.py'})
                self.assertEqual(manifest['original_source']['sha256'], edition['source_sha'])
                self.assertEqual(file_sha256(package / edition['pdf']), edition['source_sha'])
                self.assertEqual(manifest['web_roots'], {language: f'web/{language}'})
                files = sorted(path for path in inventory(package) if path != 'source_manifest.json')
                self.assertEqual(sorted(row['path'] for row in manifest['inputs']), files)
                accepted = manifest.get('publication_status') == APPROVED_STATUS
                metadata = read(package / 'web' / language / PathSegments.MANUAL_IR_JSON)['metadata']
                self.assertIs(metadata['publication_eligible'], accepted)
                self.assertEqual(bool(metadata['pending_source_review']), not accepted)
                if not accepted:
                    self.assertNotIn('publication_status', manifest)
                    self.assertFalse((package / 'source/approval.json').exists())
                    continue
                approval = read(package / 'source/approval.json')
                self.assertEqual(approval['operator_quote'], '上线发布')
                self.assertEqual(approval['reviewed_source_commit'], '16368b7')
                self.assertEqual(approval['target'], {key: manifest['target'][key]
                                                      for key in ('model', 'region', 'technical_version')})
                self.assertEqual(approval['reviewed_inputs'], [
                    row for row in manifest['inputs']
                    if not row['path'].startswith('web/') and row['path'] != 'source/approval.json'])

    def test_editions_share_one_derivation(self):
        for relative in SHARED_FILES:
            with self.subTest(relative=relative):
                self.assertEqual((EDITIONS['JP']['package'] / relative).read_bytes(),
                                 (EDITIONS['CN']['package'] / relative).read_bytes())

    @pre_four_control_styles
    def test_frozen_web_is_the_cold_replay(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                self.require_pinned_shared_inputs(region)
                output = self.root / region
                rebuild(region, output)
                self.assertEqual(inventory(output), inventory(edition['package'] / 'web' / edition['language']))

    def test_frozen_web_passes_the_release_admissions(self):
        from tools.web.caption_frame_admission import require_caption_frame_admission
        from tools.web.component_admission import require_fresh_component_admission
        from tools.web.frozen_source_evidence import _locale_inventory, _source
        from tools.web.language_release_evidence import _file_inventory, require_publishable_manual_ir
        from tools.web.symbol_asset_admission import require_symbol_asset_admission

        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                self.require_pinned_shared_inputs(region)
                package, language = edition['package'], edition['language']
                path = package / 'source_manifest.json'
                manifest = read(path)
                # Sealing copies the package without bytecode caches (loading rebuild.py here writes one).
                caches = tuple(package.rglob('__pycache__'))
                target, inputs, root = _source(manifest, path, language)
                self.assertEqual(_file_inventory(package, excluded_roots=(path, *caches)), inputs)
                web = package / root
                self.assertEqual(_file_inventory(web), _locale_inventory(inputs, root))
                require_fresh_component_admission(web, model='JE-3600A', region=region, language=language)
                require_symbol_asset_admission(web, package, manifest, language)
                require_caption_frame_admission(web)
                if manifest.get('publication_status') == APPROVED_STATUS:
                    require_publishable_manual_ir(web)
                else:
                    with self.assertRaisesRegex(RuntimeError, 'pending source review'):
                        require_publishable_manual_ir(web)

    def test_acceptance_covers_exactly_the_reviewed_source(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                self.require_pinned_shared_inputs(region)
                source = self.fixture(region)
                (source / 'source/approval.json').unlink(missing_ok=True)  # start from the unaccepted sources
                manifest = read(source / 'source_manifest.json')
                manifest['inputs'] = [row for row in manifest['inputs'] if row['path'] != 'source/approval.json']
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
                        'reviewed_inputs': [row for row in manifest['inputs'] if row['path'] != 'source/approval.json'],
                        'operator_quote': 'operator acceptance',
                        'merge_authorization': 'operator review and merge of the engineering PR',
                    }
                    write(source / 'source/approval.json', approval)
                    rebuild(region, self.root / region / 'accepted')
                    metadata = read(self.root / region / 'accepted' / PathSegments.MANUAL_IR_JSON)['metadata']
                    self.assertTrue(metadata['publication_eligible'])
                    self.assertEqual(metadata['pending_source_review'], [])
                    self.assertEqual(metadata['operator_source_acceptance'], approval)
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

    def test_navigation_is_the_print_chapters(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                titles = [match.group(1).strip() for match in re.finditer(r'(?m)^# (.+)$',
                                                                           markdown(edition['package'], edition))]
                self.assertEqual(titles, edition['chapters'])

    def test_visible_copy_is_the_reviewed_copy_minus_listed_restorations(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                reviewed = visible_characters(markdown(edition['approved'], edition))
                expected = reviewed - characters(edition['removed'])
                self.assertEqual(visible_characters(markdown(edition['package'], edition)), expected)
                layout = read(edition['package'] / f"source/{edition['language']}/web_layout.json")
                restorations = layout['copy_restorations']
                self.assertEqual(Counter(r['kind'] for r in restorations), Counter(edition['restorations']))
                self.assertTrue(all({'chapter', 'approved', 'pdf'} <= set(r) for r in restorations))
                hidden = [r for r in restorations if r['kind'] == 'hidden-print-text']
                self.assertEqual([r['approved'] for r in hidden], HIDDEN)

    def test_lcd_glossary_is_one_table_at_print_scale(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                soup = BeautifulSoup(markdown(edition['package'], edition), 'html.parser')
                tables = soup.select('table.ht-lcd-icons')
                self.assertEqual(len(tables), 1)  # the print splits it at page breaks
                self.assertEqual(len(tables[0].select('tr')), LCD_ROWS)
                icons = tables[0].select('td.ht-lcd-icon img')
                self.assertEqual(len(icons), LCD_ROWS)
                for icon in icons:  # print height relative to the 7 pt table text
                    self.assertRegex(icon.get('style', ''), r'^height:\d+\.\d\dem;width:auto$', icon['src'])
                native = [icon['src'] for icon in icons if icon['src'].endswith('-native.svg')]
                self.assertEqual(len(native), NATIVE_LCD_GLYPHS)

    def test_each_locale_carries_only_its_referenced_artwork(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                package = edition['package']
                text = ((package / f"source/{edition['language']}/content.json").read_text(encoding='utf-8')
                        + (package / 'source/presentation.css').read_text(encoding='utf-8'))
                expected = set(re.findall(r'assets/([A-Za-z0-9_.-]+)', text))
                assets = package / 'web' / edition['language'] / 'assets'
                self.assertEqual({p.name for p in assets.iterdir()}, expected)
                for path in assets.iterdir():
                    self.assertEqual(path.read_bytes(), (package / 'assets' / path.name).read_bytes(), path.name)

    def test_artwork_is_reviewed_or_recorded(self):
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                package, approved = edition['package'], edition['approved']
                for art in (approved / 'assets').iterdir():
                    self.assertEqual((package / 'assets' / art.name).read_bytes(), art.read_bytes(), art.name)
                records = read(package / 'assets_manifest.json')
                self.assertEqual(records[:len(read(approved / 'assets_manifest.json'))],
                                 read(approved / 'assets_manifest.json'))
                recorded = {r['asset']: r['sha256'] for r in records[len(read(approved / 'assets_manifest.json')):]}
                added = {p.name for p in (package / 'assets').iterdir()} - {p.name for p in (approved / 'assets').iterdir()}
                self.assertEqual(set(recorded), added)
                for name in sorted(added):
                    self.assertEqual(recorded[name], file_sha256(package / 'assets' / name), name)
                copy = package / 'assets/shared-symbol_warning_triangle.svg'
                if copy.exists():
                    self.assertEqual(copy.read_bytes(), (ROOT / SHARED_TRIANGLE).read_bytes())

    def test_derivation_is_reproducible(self):
        try:
            import pymupdf
        except ImportError:  # pragma: no cover - repository dependency
            self.skipTest('PyMuPDF unavailable')
        if tuple(pymupdf.version[:2]) != ('1.28.0', '1.29.0'):
            self.skipTest('native art is validated for PyMuPDF 1.28.0 / MuPDF 1.29.0 (requirements.lock)')
        for region, edition in EDITIONS.items():
            with self.subTest(region=region):
                self.require_pinned_shared_inputs(region)
                package = edition['package']
                derive_module = load(f'je3600a_{region.lower()}_layout_derive', package / 'derive_web_layout.py')
                source = self.root / region / 'derived'
                shutil.copytree(package, source, ignore=shutil.ignore_patterns('web', '__pycache__'))
                with mock.patch.object(derive_module, 'HERE', source), redirect_stdout(io.StringIO()):
                    derive_module.main()
                frozen = {path: digest for path, digest in inventory(package).items() if not path.startswith('web/')}
                self.assertEqual(inventory(source), frozen)


if __name__ == '__main__':
    unittest.main()
