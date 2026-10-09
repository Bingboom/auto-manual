"""Derive the JA-AD500A-SIL / JP / ja Web-layout edition from the approved package.

Run from the repository root:

    python manual_sources/JA-AD500A-SIL/JP/ja/git-20261009-ac3a1f82-web-layout/derive_web_layout.py

The approved package ``../git-20261008-ac3a1f82-reviewed`` stays immutable. This
script copies its PDF, recipe, page map and artwork byte-for-byte, rewrites the
prepared RST pages with the layout edits below and refreshes
``source_manifest.json``; a second run leaves the tree unchanged. Hand-written
``README.md``, ``render.py``, ``source/differences.md``,
``source/presentation.css`` and ``source/approval.json`` are not touched.

Every edit adds markup only (bold, line breaks, classes, inline styles) or
removes the printed cover lines listed in ``COVER_LINES``; each edit must match
the approved page exactly once. ``tests/test_jaad500a_sil_jp_web_layout.py``
proves that the rendered visible text equals the approved text minus the cover.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

PACKAGE = Path(__file__).resolve().parent
REVIEWED = PACKAGE.parent / 'git-20261008-ac3a1f82-reviewed'
REPO = next(parent for parent in PACKAGE.parents if (parent / 'build.py').is_file())
sys.path.insert(0, str(REPO))

from tools.asset_pipeline.extract import extract_artifacts  # noqa: E402
from tools.asset_pipeline.recipe import load_recipe  # noqa: E402

STATUS = 'review-candidate-no-release-authorization'
# Inputs copied byte-for-byte from the approved package.
UNCHANGED = [
    'source/original.pdf', 'source/native_pages.json', 'source/page/contact_ja.rst',
    *(f'assets/{p.name}' for p in sorted((REVIEWED / 'assets').iterdir()) if p.name != 'inbox-manual.png'),
]
# p.2: the approved crop [157, 80, 202, 146] cuts the booklet's right frame (drawing 2252,
# 157.63-203.39 x 79.92-146.01 pt). The re-crop keeps the whole frame plus its stroke.
INBOX_MANUAL = {'asset_key': 'web/ja-ad500a-sil/jp/ja/inbox-manual', 'bbox_pt': [157, 79, 204, 147],
                'sha256': 'f01512af441ad341022a4116ac908c865d15f29660688fc2801c8b46c7b4dcfa'}
# Printed cover (physical page 1) lines that are not part of the Web edition.
# The cover's support line repeats the back-cover contact line.
COVER_LINES = [
    '取扱説明書', 'Jackery DC Input Module', '型番:JA-AD500A-SIL', '国内専用/For use only in Japan',
    '写真はイメージです。実際の商品とは異なる場合があります。',
    'カスタマーサポート: jackery.jp@jackery.com',
]
LABEL = 'display:block;width:100%;text-align:right;font-size:clamp(12px,1.2em,18px);line-height:1.15'
RATING = 'display:block;width:100%;text-align:right;font-size:clamp(10px,0.95em,14px);line-height:1.15'
LED_HEAD = 'padding:0.25rem 0.6rem!important;text-align:left!important;border-bottom:1px solid var(--hb-line-soft)!important;'
LED_CELL = 'padding:0.25rem 0.6rem!important;text-align:left!important;'
NOTE = 'display:block;width:100%;text-align:right;font-size:clamp(10px,0.95em,14px);line-height:1.15">※ シガー'

# (page, approved fragment, Web-layout fragment, expected count); PDF page in comments.
EDITS = [
    # p.1 — the welcome lead is bold; the bullets are tight "・" lines.
    ('00_preface_ja.rst', 'お買い上げありがとうございます。\n\n- ',
     '.. class:: jpad-welcome-lead\n\n**お買い上げありがとうございます。**\n\n.. class:: jpad-tight\n\n- ', 1),
    # p.2 — the disclaimer under the in-box cards is bold.
    ('box_contents_ja.rst', '\n本機の仕様および外観は、改善のため予告なく変更することがあります。\n',
     '\n**本機の仕様および外観は、改善のため予告なく変更することがあります。**\n', 1),
    # p.3 — part names are bold; port ratings are small grey lines.
    ('product_overview_ja.rst', f'style="{LABEL}"', f'style="{LABEL};font-weight:700"', 3),
    ('product_overview_ja.rst', f'style="{RATING}"',
     f'style="{RATING.replace("0.95em,14px", "0.8em,12px")};color:#8a8a8a"', 2),
    # p.3 — LED table: grey header, centred cells.
    ('product_overview_ja.rst', f'style="{LED_HEAD}"',
     f'style="{LED_HEAD.replace("left", "center")}background:var(--hb-surface-strong)!important;"', 3),
    ('product_overview_ja.rst', f'style="{LED_CELL}"', f'style="{LED_CELL.replace("left", "center")}"', 12),
    # p.4 — the ※ note keeps its hanging indent; the accessory lines are tight.
    ('charging_ja.rst', '■ 必要なアクセサリー\n\n- ', '■ 必要なアクセサリー\n\n.. class:: jpad-tight\n\n- ', 1),
    ('charging_ja.rst', '\n※Jackery SolarSagaアダプター', '\n.. class:: jpad-hang\n\n※Jackery SolarSagaアダプター', 1),
    # p.5 — each printed line of the two connection notes is its own line.
    ('charging_ja.rst',
     '- 直接接続可能です。\n  追加のアクセサリーは不要です。\n  本製品のDC入力ポートは',
     '- | 直接接続可能です。\n  | 追加のアクセサリーは不要です。\n  | 本製品のDC入力ポートは', 1),
    ('charging_ja.rst',
     '- 別売りの「Jackery SolarSaga アダプター(Pro/Plus/New専用)」が必要です。\n'
     '  「Jackery SolarSaga アダプター(Pro/Plus/New専用)」（オス・メス）とも8020端子です。\n'
     '  ソーラーパネルの8020オス端子を',
     '- | 別売りの「Jackery SolarSaga アダプター(Pro/Plus/New専用)」が必要です。\n'
     '  |\n'
     '  | 「Jackery SolarSaga アダプター(Pro/Plus/New専用)」（オス・メス）とも8020端子です。\n'
     '  | ソーラーパネルの8020オス端子を', 1),
    # p.5 — 「例：」 is a bold sub-heading inside ご注意.
    ('charging_ja.rst', '\n       例：\n', '\n       **例：**\n', 1),
    # p.6 — the lead is bold and the five precautions sit in one grey panel.
    ('charging_ja.rst', '\nご使用の際は、以下にご注意ください：\n\n- 必ず',
     '\n**ご使用の際は、以下にご注意ください：**\n\n.. container:: jpad-panel\n\n   - 必ず', 1),
    ('charging_ja.rst', '\n- 車の充電ポート', '\n   - 車の充電ポート', 1),
    ('charging_ja.rst', '\n- ケーブルが確実に', '\n   - ケーブルが確実に', 1),
    ('charging_ja.rst', '\n- 悪路などで', '\n   - 悪路などで', 1),
    ('charging_ja.rst', '\n- 誤使用による', '\n   - 誤使用による', 1),
    # p.6 — the cable note capsule is left-aligned with a hanging ※.
    ('charging_ja.rst', NOTE, NOTE.replace('text-align:right', 'text-align:left;padding-left:1em;text-indent:-1em'), 1),
    # p.7 — the two print lines are one wrapped sentence pair (no inserted space).
    ('spec_ja.rst', '専用となります。\n他の機器には', '専用となります。他の機器には', 1),
    ('spec_ja.rst', '\n本製品はJackery SlimPower H1および', '\n.. class:: jpad-small\n\n本製品はJackery SlimPower H1および', 1),
    # p.7 — the ※ note keeps its hanging indent.
    ('warranty_ja.rst', '\n   ※ Jackery公式オンラインストア', '\n   .. class:: jpad-hang\n\n   ※ Jackery公式オンラインストア', 1),
    # p.7 — 購入チャネルについて and its detail are separate print lines.
    ('warranty_ja.rst', '   1. 購入チャネルについて\n      本保証は、',
     '   1. | 購入チャネルについて\n      | 本保証は、', 1),
    # p.8 — the proof note is a grey capsule.
    ('warranty_ja.rst', '\n   ※ ご提示がない場合', '\n   .. class:: jpad-note\n\n   ※ ご提示がない場合', 1),
    # p.8–9 — the three remedy headings are bold, their periods normal.
    ('warranty_ja.rst', '   1. 初期不良による交換（', '   1. **初期不良による交換**\\ （', 1),
    ('warranty_ja.rst', '   2. 無償修理（', '   2. **無償修理**\\ （', 1),
    ('warranty_ja.rst', '   3. 有償修理\n', '   3. **有償修理**\n', 1),
    # p.9 — the free-repair footnote is a grey capsule.
    ('warranty_ja.rst', '\n   \\* 無償修理の場合', '\n   .. class:: jpad-note\n\n   \\* 無償修理の場合', 1),
    # p.9 — the closing request keeps its print line break under item 3.
    ('warranty_ja.rst',
     '   Jackery製品を安心してご使用いただくために、本保証書の内容をご確認のうえ、ご活用くださいますようお願いいたします。\n'
     '   ご不明点がございましたら',
     '   .. class:: jpad-closing\n\n'
     '   | Jackery製品を安心してご使用いただくために、本保証書の内容をご確認のうえ、ご活用くださいますようお願いいたします。\n'
     '   | ご不明点がございましたら', 1),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def copy_unchanged() -> None:
    for relative in UNCHANGED:
        target = PACKAGE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REVIEWED / relative, target)


def recipe() -> None:
    data = read(REVIEWED / 'source/asset_recipe.json')
    (entry,) = [a for a in data['assets'] if a['asset_key'] == INBOX_MANUAL['asset_key']]
    (crop,) = [op for op in entry['transforms'] if op['op'] == 'crop']
    crop['bbox_pt'] = INBOX_MANUAL['bbox_pt']
    entry['outputs'][0]['expected_sha256'] = INBOX_MANUAL['sha256']
    (PACKAGE / 'source/asset_recipe.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def render_assets() -> None:
    """Render the recipe with the shared asset pipeline; every other output must equal the approved art."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'render'
        extract_artifacts(PACKAGE / 'source/original.pdf', load_recipe(PACKAGE / 'source/asset_recipe.json'), out)
        for path in sorted((out / 'assets').iterdir()):
            if path.name == 'inbox-manual.png':
                shutil.copyfile(path, PACKAGE / 'assets' / path.name)
            elif path.read_bytes() != (REVIEWED / 'assets' / path.name).read_bytes():
                raise SystemExit(f'recipe output drifted from the approved art: {path.name}')


def preface(text: str) -> str:
    """Drop the printed cover block: the title and the cover lines before the welcome lead."""
    head, welcome = text.split('お買い上げありがとうございます。', 1)
    lines = [line for line in head.splitlines() if line.strip()]
    expected = ['.. _jp-00_preface_ja-1:', COVER_LINES[0], '=' * 30, *COVER_LINES[1:]]
    if lines != expected:
        raise SystemExit(f'preface cover block changed: {lines!r}')
    return 'お買い上げありがとうございます。' + welcome


def pages() -> None:
    page_dir = PACKAGE / 'source/page'
    page_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted((REVIEWED / 'source/page').glob('*.rst')):
        if f'source/page/{path.name}' in UNCHANGED:
            continue
        text = path.read_text(encoding='utf-8')
        if path.name == '00_preface_ja.rst':
            text = preface(text)
        for name, old, new, count in EDITS:
            if name != path.name:
                continue
            if text.count(old) != count:
                raise SystemExit(f'{name}: expected {count} approved fragment(s) {old[:40]!r}, found {text.count(old)}')
            text = text.replace(old, new)
        (page_dir / path.name).write_text(text, encoding='utf-8')


def manifest() -> None:
    data = read(REVIEWED / 'source_manifest.json')
    data['target']['technical_version'] = PACKAGE.name
    data['source_role'] = 'Git-only Japanese prepared native Web-layout edition of the approved release'
    data['publication_eligible'] = STATUS == 'operator-approved-git-only-release'
    data['publication_status'] = STATUS
    data['derived_from'] = {
        'package': REVIEWED.name, 'authorization': 'MA-272',
        'manifest_sha256': sha256(REVIEWED / 'source_manifest.json'),
    }
    data['source_authority'] = (
        'operator-designated Japanese PDF; original Japanese governs all technical/legal copy. Web-layout edition of '
        'the approved package git-20261008-ac3a1f82-reviewed (MA-272) on operator instruction 2026-10-09 '
        '(「开新窗口 把这个的版面也调整了」, applying the JBP-1000B-WH JP rules 「全部修，一次做完」'
        '「封面和目录 不用体现在web版面上」「你参考 资料库里 现有的je-1000f的日语网页说明书」).'
    )
    data['normalizations'] = [n for n in data['normalizations'] if not n.startswith('Web layout:')] + [
        'Web layout: printed cover identity lines (physical 1) are not part of the Web edition; '
        'the welcome lead and its four reader instructions remain at the top.',
        'Web layout: rich-text structure, print line breaks, grey panels/capsules and source.css follow the PDF; '
        'no Japanese wording is edited.',
    ]
    data['web_exclusions'] = [{'physical_page': 1, 'role': 'printed cover', 'lines': COVER_LINES}]
    data['pending_source_review'] = [] if data['publication_eligible'] else [
        'operator page-by-page review of the Web-layout candidate']
    for entry in data['repo_inputs']:
        entry['sha256'] = sha256(REPO / entry['path'])
    skip = {'README.md', 'source_manifest.json', 'frozen_source_manifest.json'}
    files = sorted(
        p for p in PACKAGE.rglob('*')
        if p.is_file() and p.name not in skip and '__pycache__' not in p.parts
        and p.relative_to(PACKAGE).parts[0] in {'render.py', 'derive_web_layout.py', 'assets', 'source'}
    )
    data['inputs'] = [{'path': p.relative_to(PACKAGE).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
                      for p in files]
    (PACKAGE / 'source_manifest.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    copy_unchanged()
    recipe()
    render_assets()
    pages()
    manifest()
    print(json.dumps({'package': PACKAGE.name, 'inputs': len(read(PACKAGE / 'source_manifest.json')['inputs'])}))


if __name__ == '__main__':
    main()
