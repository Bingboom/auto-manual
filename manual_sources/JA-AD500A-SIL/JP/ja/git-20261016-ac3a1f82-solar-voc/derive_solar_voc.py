"""Derive the JA-AD500A-SIL / JP / ja solar-Voc correction edition from the live Web-layout edition.

Run from the repository root:

    python manual_sources/JA-AD500A-SIL/JP/ja/git-20261016-ac3a1f82-solar-voc/derive_solar_voc.py

The approved Web-layout edition ``../git-20261009-ac3a1f82-web-layout`` stays
immutable. This script copies its ``source/`` and ``assets/`` trees
byte-for-byte (except that edition's own ``source/approval.json`` and
``source/differences.md``), applies the single text correction in
``CORRECTIONS`` to the prepared charging page and refreshes
``source_manifest.json``; a second run leaves the tree unchanged. Hand-written
``README.md``, ``render.py``, ``source/differences.md`` and (after acceptance)
``source/approval.json`` are not touched.

The correction replaces the first two sentences of the solar-panel paragraph.
Panels reach the connected product through the Jackery DC Input Module, so the
governing limit is the module's DC input voltage range (16V～60V), not the
downstream SlimPower H1 / Battery Pack ranges the printed source cites. The
opening accessory warning is dropped on operator instruction (it contradicted
the recommendation and the disclaimer); the closing disclaimer is kept.
``tests/test_jp_solar_voc.py`` proves the rendered Markdown equals the base
edition's Markdown with exactly this paragraph replaced.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

PACKAGE = Path(__file__).resolve().parent
BASE = PACKAGE.parent / 'git-20261009-ac3a1f82-web-layout'
REPO = next(parent for parent in PACKAGE.parents if (parent / 'build.py').is_file())

CANDIDATE = 'review-candidate-no-release-authorization'
APPROVED = 'operator-approved-git-only-release'
STATUS = APPROVED
LANGUAGE = 'ja'
COPIED_ROOTS = ('source', 'assets')
# The base edition's own acceptance and change record do not carry over.
NOT_COPIED = {'source/approval.json', 'source/differences.md'}
HOST_RANGE_CONCERN = 'DC input 8A versus 12V/10A vehicle text; host ranges differ from module range'

# (prepared page, base sentence(s), corrected sentence(s)); each must match exactly once.
CORRECTIONS = [
    (
        'charging_ja.rst',
        'Jackeryブランド以外の付属品を使用して充電しないでください。'
        'ソーラーパネルの開放電圧（Voc）が、Jackery SlimPower H1 のDC入力範囲（36.8V～56V）または '
        'Jackery Battery PackのDC入力範囲（40V～57.6V）内であることを確認してください。',
        'Jackery DC Input Moduleを介して接続した製品を充電する場合は、Jackery製ソーラーパネルの使用を推奨します。'
        '接続するソーラーパネルの開放電圧（Voc）が、本モジュールのDC入力電圧範囲（16V～60V）内であることを確認してください。',
    ),
]


LED_TABLE_START = '.. raw:: html\n\n   <div class="table-wrapper docutils" style='
LED_TABLE = '''.. container:: hb-source-status

   .. list-table::
      :header-rows: 1
      :widths: auto
      :class: hb-source-status-table

      * - LEDライトの状態
        - ライトの色
        - 製品の状態
      * - 点滅
        - 緑色
        - 充電中
      * - 点灯
        - 赤色
        - 異常状態
      * - 点灯
        - 緑色
        - 接続成功、充電準備完了
      * - 消灯
        - なし
        - 電源オフ
'''
CONTACT = '''.. raw:: html

   <div class="hb-text-panel">
   <p><strong>公式サイト: <a href="https://www.jackery.jp">https://www.jackery.jp</a></strong></p>
   <p><strong>カスタマーサポート: <a href="mailto:jackery.jp@jackery.com">jackery.jp@jackery.com</a></strong></p>
   <p><strong>お問い合わせ電話番号: <a href="tel:05031989007">050-3198-9007</a></strong></p>
   </div>
   <p><img alt="原稿裏表紙のQRコード" src="../../assets/contact-qr.png"/></p>
'''
# The prepared-document shared-style gate (#1556) admits a re-frozen locale only without
# source-drawn styles: page-local classes, inline styles and stylesheet paint give way to
# shared theme classes; copy is unchanged. (prepared page, base markup, shared markup);
# each base markup must match exactly once.
STYLE_EDITS = [
    ('00_preface_ja.rst', '.. class:: jpad-welcome-lead\n\n', ''),
    ('00_preface_ja.rst', '.. class:: jpad-tight\n\n', ''),
    ('charging_ja.rst', '.. class:: jpad-tight\n\n', ''),
    ('charging_ja.rst', '.. class:: jpad-hang\n\n', ''),
    ('charging_ja.rst', '.. container:: jpad-panel\n', '.. container:: hb-text-panel\n'),
    ('spec_ja.rst', '.. class:: jpad-small\n', '.. class:: manual-spec-note\n'),
    ('product_overview_ja.rst', '<div style="width:min(100%,40rem);margin-inline:auto"><img', '<img'),
    ('product_overview_ja.rst', 'プラグ</span></div></div></div>', 'プラグ</span></div></div>'),
]
# Whole blocks rebuilt on shared classes: (page, start marker, replacement up to end of page).
STYLE_BLOCKS = [
    ('product_overview_ja.rst', LED_TABLE_START, LED_TABLE),
    ('contact_ja.rst', '.. raw:: html\n\n   <div class="hb-manual-page-end">', CONTACT),
]
STYLED_PAGES = sorted({name for name, _, _ in STYLE_EDITS} | {name for name, _, _ in STYLE_BLOCKS})
# The LED status table has no shared component; it is a plain table on the shared status-table classes.
LED_TABLE_EXCEPTION = {
    'language': LANGUAGE, 'page_id': 'product_overview_ja.rst', 'kind': 'table',
    'text_sha256': '7410f90222f775cd54decfa20f107c35a8f73f326520548687d7d7c2bf6b1f38',
    'reason': 'module LED status/colour/meaning table: no shared ComponentSpec covers an LED-state table; '
              'it uses the shared hb-source-status-table classes',
}
PRESENTATION_CSS = '''/* JA-AD500A-SIL JP solar-Voc edition: page-local geometry only.
   Colours, borders and panels come from the shared Web theme (prepared-document shared-style gate). */

/* Print bullets are "・" lines, as in the PDF. */
#furo-main-content ul > li { list-style-type: "・"; }
#furo-main-content ul { padding-left: 1.2rem; }

/* p.3: the product overview figure keeps its print width. */
#furo-main-content .hb-reference-figure[data-reference-id="product-overview"] { width: min(100%, 40rem); margin-inline: auto; }

/* p.3: LED status table columns follow the print. */
#furo-main-content table.hb-source-status-table { min-width: 0; }
#furo-main-content table.hb-source-status-table :is(th, td) { text-align: center; }
#furo-main-content table.hb-source-status-table tr > :nth-child(1) { width: 25%; }
#furo-main-content table.hb-source-status-table tr > :nth-child(2) { width: 20%; }

/* p.5: connection notes keep their print lines; continuation lines are indented. */
#furo-main-content li > .line-block { margin: 0 0 .4rem; }
#furo-main-content li > .line-block > .line + .line { padding-left: .9em; }
#furo-main-content li > .line-block > .line:has(> br:only-child) { height: .45rem; overflow: hidden; }

/* p.5–6: the ご注意 label is large print type; 「例：」 is a bold sub-heading. */
#furo-main-content .manual-callout-label p { font-size: 1.3rem; }
#furo-main-content .manual-callout-body > p > strong { font-size: 1.05rem; }

/* p.6: the five car-charging precautions sit in one shared text panel. */
#furo-main-content div.hb-text-panel { margin: .4rem 0 1.2rem; }
#furo-main-content div.hb-text-panel ul { margin: 0; }
#furo-main-content div.hb-text-panel li > p { margin: .1rem 0; }

/* p.7: "170 x 90 x 52" keeps the printed letter x (no contextual × substitution). */
#furo-main-content .hb-spec-value { font-variant-ligatures: no-contextual; font-feature-settings: "calt" 0; }

/* p.7–9: warranty notes and lines keep the print spacing. */
#furo-main-content .hb-warranty-intro-panel p + p,
#furo-main-content .hb-warranty-local-note p { margin-top: .2rem; }
#furo-main-content .hb-warranty-card p.jpad-note { margin: .5rem 0 0; font-size: .84rem; }
#furo-main-content .hb-warranty-card li > .line-block { margin: 0; }
#furo-main-content .hb-warranty-card li > .line-block > .line + .line { padding-left: 0; }

/* p.8–9: 保証内容 numbers and remedy headings are bold, each remedy a separate block. */
#furo-main-content figure[aria-label="保証内容"] > ol { padding-left: 1.3rem; }
#furo-main-content figure[aria-label="保証内容"] > ol > li::marker { font-weight: 700; }
#furo-main-content figure[aria-label="保証内容"] > ol > li + li { margin-top: .9rem; }
#furo-main-content figure[aria-label="保証内容"] > ol > li > ul { margin-top: .15rem; }
#furo-main-content figure[aria-label="免責事項"] .jpad-closing { margin: 0 0 0 1.3rem; }

/* p.9: the back-cover QR code keeps its print size. */
#furo-main-content img[alt="原稿裏表紙のQRコード"] { width: 96px !important; height: auto; margin: 1rem 0; }
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def copy_base() -> None:
    for root in COPIED_ROOTS:
        for path in sorted((BASE / root).rglob('*')):
            relative = path.relative_to(BASE).as_posix()
            if path.is_file() and relative not in NOT_COPIED:
                target = PACKAGE / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)


def edited_page(name: str) -> str:
    """The base page with its text correction and shared-style edits applied."""
    text = (BASE / 'source' / 'page' / name).read_text(encoding='utf-8')
    for page, old, new in [*CORRECTIONS, *STYLE_EDITS]:
        if page == name:
            if text.count(old) != 1:
                raise SystemExit(f'{name}: expected the base text once, found {text.count(old)}')
            text = text.replace(old, new)
    for page, start, block in STYLE_BLOCKS:
        if page == name:
            if text.count(start) != 1:
                raise SystemExit(f'{name}: expected the base block once, found {text.count(start)}')
            text = text[:text.index(start)] + block
    return text


def correct_pages() -> None:
    for name in sorted({name for name, _, _ in CORRECTIONS} | set(STYLED_PAGES)):
        (PACKAGE / 'source' / 'page' / name).write_text(edited_page(name), encoding='utf-8')
    (PACKAGE / 'source' / 'presentation.css').write_text(PRESENTATION_CSS, encoding='utf-8')


def manifest() -> None:
    data = read(BASE / 'source_manifest.json')
    data['target']['technical_version'] = PACKAGE.name
    data['source_role'] = 'Git-only Japanese solar-Voc correction edition of the approved Web-layout edition'
    data['publication_eligible'] = STATUS == APPROVED
    data['publication_status'] = STATUS
    data['derived_from'] = {
        'package': BASE.name,
        'authorization': 'operator review and merge of #1467 (AGENTS.md §8.6); base approval MA-272',
        'manifest_sha256': sha256(BASE / 'source_manifest.json'),
    }
    (concern,) = [c for c in data['source_concerns'] if c['issue'] == HOST_RANGE_CONCERN]
    concern['disposition'] = ('solar Voc host ranges corrected in this edition on operator instruction 2026-10-16; '
                              'the 8A versus 12V/10A vehicle text is preserved verbatim; '
                              'native_pages.json keeps the printed wording')
    data['text_corrections'] = [
        {'page': f'source/page/{name}', 'approved': old, 'corrected': new,
         'reason': 'Solar panels connect through the Jackery DC Input Module; the panel Voc limit is '
                   "the module's DC input voltage range (16V～60V), not the downstream SlimPower H1 / "
                   'Battery Pack ranges cited by the printed source.',
         'instruction': 'operator, 2026-10-15/16: replace the paragraph (整段替换), keep the disclaimer '
                        '(不删免责句); the opening accessory warning is dropped (删掉第①句, 2026-10-16); the printed source and its '
                        'transcription stay unchanged'}
        for name, old, new in CORRECTIONS
    ]
    data['shared_component_exceptions'] = [LED_TABLE_EXCEPTION]
    data['style_migration'] = {
        'gate': 'prepared-document-shared-styles/v1',
        'pages': [f'source/page/{name}' for name in STYLED_PAGES],
        'stylesheet': 'source/presentation.css',
        'reason': 're-frozen for the solar-Voc correction, the locale must pass the shared-style gate: '
                  'page-local classes, inline styles and stylesheet paint replaced by shared theme classes; '
                  'visible copy unchanged',
        'instruction': 'operator, 2026-10-16: 889 日规 也要删掉第一句 (fix the inherited style issues)',
    }
    data['pending_source_review'] = [] if data['publication_eligible'] else [
        'operator review of the solar-Voc text correction before Git-only release']
    for entry in data['repo_inputs']:
        entry['sha256'] = sha256(REPO / entry['path'])
    files = sorted(
        p for p in PACKAGE.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts
        and p.relative_to(PACKAGE).parts[0] in {'render.py', 'derive_solar_voc.py', *COPIED_ROOTS}
    )
    data['inputs'] = [{'path': p.relative_to(PACKAGE).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
                      for p in files]
    (PACKAGE / 'source_manifest.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def release_manifest() -> None:
    """Inventory every package file for the Git-only release (seal_frozen_web_evidence)."""
    data = read(PACKAGE / 'source_manifest.json')
    files = sorted(
        p for p in PACKAGE.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.name != 'frozen_source_manifest.json'
    )
    data['inputs'] = [{'path': p.relative_to(PACKAGE).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
                      for p in files]
    (PACKAGE / 'frozen_source_manifest.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    copy_base()
    correct_pages()
    manifest()
    if (PACKAGE / 'web' / LANGUAGE).is_dir():
        release_manifest()
    print(json.dumps({'package': PACKAGE.name, 'inputs': len(read(PACKAGE / 'source_manifest.json')['inputs'])}))


if __name__ == '__main__':
    main()
