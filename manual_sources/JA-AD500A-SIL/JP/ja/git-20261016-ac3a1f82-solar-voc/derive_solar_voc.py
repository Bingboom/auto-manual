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

The correction replaces the two middle sentences of the solar-panel paragraph.
Panels reach the connected product through the Jackery DC Input Module, so the
governing limit is the module's DC input voltage range (16V～60V), not the
downstream SlimPower H1 / Battery Pack ranges the printed source cites. The
opening accessory warning and the closing disclaimer are kept.
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
STATUS = CANDIDATE
LANGUAGE = 'ja'
COPIED_ROOTS = ('source', 'assets')
# The base edition's own acceptance and change record do not carry over.
NOT_COPIED = {'source/approval.json', 'source/differences.md'}
HOST_RANGE_CONCERN = 'DC input 8A versus 12V/10A vehicle text; host ranges differ from module range'

# (prepared page, base sentence(s), corrected sentence(s)); each must match exactly once.
CORRECTIONS = [
    (
        'charging_ja.rst',
        'ソーラーパネルの開放電圧（Voc）が、Jackery SlimPower H1 のDC入力範囲（36.8V～56V）または '
        'Jackery Battery PackのDC入力範囲（40V～57.6V）内であることを確認してください。',
        'Jackery DC Input Moduleを介して接続した製品を充電する場合は、Jackery製ソーラーパネルの使用を推奨します。'
        '接続するソーラーパネルの開放電圧（Voc）が、本モジュールのDC入力電圧範囲（16V～60V）内であることを確認してください。',
    ),
]


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


def correct_pages() -> None:
    for name, old, new in CORRECTIONS:
        path = PACKAGE / 'source' / 'page' / name
        text = (BASE / 'source' / 'page' / name).read_text(encoding='utf-8')
        if text.count(old) != 1:
            raise SystemExit(f'{name}: expected the base sentence once, found {text.count(old)}')
        path.write_text(text.replace(old, new), encoding='utf-8')


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
                        '(不删免责句) and the opening accessory warning (保留这句); the printed source and its '
                        'transcription stay unchanged'}
        for name, old, new in CORRECTIONS
    ]
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
