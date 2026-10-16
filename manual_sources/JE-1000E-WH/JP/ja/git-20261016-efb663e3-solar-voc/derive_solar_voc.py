"""Derive the SlimPower H1 (JE-1000E-WH / JP / ja) solar-Voc correction edition.

Run from the repository root:

    python manual_sources/JE-1000E-WH/JP/ja/git-20261016-efb663e3-solar-voc/derive_solar_voc.py

The approved Web edition ``../git-20261008-efb663e3-no-cover-reviewed`` (MA-277)
stays immutable. This script copies its PDF, artwork, provenance and
``source/`` tree byte-for-byte, applies the single text correction in
``CORRECTIONS`` to ``source/chapters.json`` and writes ``source_manifest.json``;
a second run leaves the tree unchanged. Hand-written ``README.md``,
``rebuild.py``, ``verify.py``, ``source/differences.md`` and (after acceptance)
``source/approval.json`` are not touched.

The correction replaces the two middle sentences of the solar-panel paragraph
(printed p.20). Panels reach the SlimPower H1 through the Jackery DC Input
Module, so the governing limit is the module's DC input voltage range
(16V～60V), not the H1's own DC input range. The opening accessory warning and
the closing disclaimer are kept. ``tests/test_jp_solar_voc.py`` proves the
rendered Markdown equals the approved Markdown with exactly this paragraph
replaced.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

PACKAGE = Path(__file__).resolve().parent
BASE = PACKAGE.parent / 'git-20261008-efb663e3-no-cover-reviewed'

CANDIDATE = 'review-candidate-no-release-authorization'
APPROVED = 'operator-approved-git-only-release'
STATUS = CANDIDATE
LANGUAGE = 'ja'
PDF = 'Jackery SlimPower H1取扱説明書V2.0-2026-07-29.pdf'
# Copied byte-for-byte; the base edition's scripts, docs, approval, validation and web are not.
COPIED = (PDF, 'artwork', 'asset_provenance.json', 'source')
# Native PDF block whose print lines the correction rewords (physical page, block index).
CORRECTED_NATIVE_BLOCKS = [(20, 5)]

# (source file, approved sentences, corrected sentences); each must match exactly once.
CORRECTIONS = [
    (
        'source/chapters.json',
        '特に、ソーラーパネルで充電する際は、Jackeryのソーラーパネルを使用することをお勧めします。'
        'ソーラーパネルの開放電圧（Voc）が、Jackery SlimPower H1のDC入力電圧範囲（36.8V~56V）'
        '内に収まっていることを確認してください。',
        '本製品の充電には、Jackery製ソーラーパネルの使用を推奨します。'
        '接続するソーラーパネルの開放電圧（Voc）が、Jackery DC Input ModuleのDC入力電圧範囲（16V～60V）'
        '内であることを確認してください。',
    ),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def copy_base() -> None:
    for name in COPIED:
        source = BASE / name
        paths = sorted(p for p in source.rglob('*') if p.is_file()) if source.is_dir() else [source]
        for path in paths:
            target = PACKAGE / path.relative_to(BASE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


def correct_sources() -> None:
    for relative, old, new in CORRECTIONS:
        text = (BASE / relative).read_text(encoding='utf-8')
        if text.count(old) != 1:
            raise SystemExit(f'{relative}: expected the approved sentences once, found {text.count(old)}')
        (PACKAGE / relative).write_text(text.replace(old, new), encoding='utf-8')
        json.loads((PACKAGE / relative).read_text(encoding='utf-8'))  # still valid JSON


def manifest() -> None:
    data = read(BASE / 'source_manifest.json')
    data['target']['technical_version'] = PACKAGE.name
    data['source_authority'] = (
        'Operator-designated Japanese PDF and the approved MA-277 Web edition '
        'git-20261008-efb663e3-no-cover-reviewed; solar-Voc text correction on operator instruction '
        '2026-10-15/16 (整段替换, 不删免责句, 保留这句). The printed source keeps its wording.')
    data['publication_eligible'] = STATUS == APPROVED
    data['publication_status'] = STATUS
    data['derived_from'] = {
        'package': BASE.name, 'authorization': 'MA-277',
        'manifest_sha256': sha256(BASE / 'source_manifest.json'),
    }
    data['text_corrections'] = [
        {'source': relative, 'approved': old, 'corrected': new,
         'native_blocks': [{'physical_page': page, 'block': block} for page, block in CORRECTED_NATIVE_BLOCKS],
         'reason': 'Solar panels connect through the Jackery DC Input Module; the panel Voc limit is '
                   "the module's DC input voltage range (16V～60V), not the SlimPower H1's own DC input range.",
         'instruction': 'operator, 2026-10-15/16: replace the paragraph (整段替换), keep the disclaimer '
                        '(不删免责句) and the opening accessory warning (保留这句); the printed source and its '
                        'native text stay unchanged'}
        for relative, old, new in CORRECTIONS
    ]
    data['pending_source_review'] = [] if data['publication_eligible'] else [
        'operator review of the solar-Voc text correction before Git-only release']
    data.pop('inputs', None)
    (PACKAGE / 'source_manifest.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Inventory every package file except the manifest itself (the base edition's convention).
    files = sorted(p for p in PACKAGE.rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts and p.name != 'source_manifest.json')
    data['inputs'] = [{'path': p.relative_to(PACKAGE).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
                      for p in files]
    (PACKAGE / 'source_manifest.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    copy_base()
    correct_sources()
    manifest()
    print(json.dumps({'package': PACKAGE.name, 'inputs': len(read(PACKAGE / 'source_manifest.json')['inputs'])},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
