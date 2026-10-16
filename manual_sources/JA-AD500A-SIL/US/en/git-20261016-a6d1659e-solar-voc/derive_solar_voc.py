"""Derive the JA-AD500A-SIL / US / en solar-Voc correction edition from the approved package.

Run from the repository root:

    python manual_sources/JA-AD500A-SIL/US/en/git-20261016-a6d1659e-solar-voc/derive_solar_voc.py

The approved package ``../git-20261006-a6d1659e-reviewed`` (MA-259) stays
immutable. This script copies its ``source/`` and ``assets/`` trees
byte-for-byte, applies the single text correction in ``CORRECTIONS`` to the
prepared charging page and refreshes ``source_manifest.json``; a second run
leaves the tree unchanged. Hand-written ``README.md``, ``render.py``,
``source/differences.md`` and (after acceptance) ``source/approval.json`` are
not touched.

The correction replaces the solar-panel Voc paragraph only. Panels reach the
connected product through the Jackery DC Input Module, so the governing limit
is the module's DC input voltage range (16V–60V), not the downstream
FridgeGuard / Battery Pack ranges the printed source cites. The disclaimer
sentence is kept. ``tests/test_jaad500a_sil_us_solar_voc.py`` proves the
rendered Markdown equals the approved Markdown with exactly this paragraph
replaced.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

PACKAGE = Path(__file__).resolve().parent
REVIEWED = PACKAGE.parent / 'git-20261006-a6d1659e-reviewed'
REPO = next(parent for parent in PACKAGE.parents if (parent / 'build.py').is_file())

CANDIDATE = 'review-candidate-no-release-authorization'
APPROVED = 'operator-approved-git-only-release'
STATUS = CANDIDATE
LANGUAGE = 'en'
# Copied byte-for-byte; the correction applies on top of the copy.
COPIED_ROOTS = ('source', 'assets')

# (prepared page, approved paragraph, corrected paragraph); each must match exactly once.
CORRECTIONS = [
    (
        'charging_en.rst',
        'It is recommended to use the Jackery solar panel to charge the product. Ensure that the '
        'open-circuit voltage (V\\ :sub:`oc`) of the solar panel is within the DC input range '
        '(36.8V–56V) of the Jackery FridgeGuard or the DC input range (40V–57.6V) of the Jackery '
        'Battery Pack. Jackery is not responsible for any damage or loss resulting from the use of '
        'third-party solar panels.',
        'It is recommended to use Jackery solar panels to charge the connected product through the '
        'Jackery DC Input Module. Ensure that the open-circuit voltage (V\\ :sub:`oc`) of the '
        "connected solar panels is within the module's DC input voltage range (16V–60V). Jackery is "
        'not responsible for any damage or loss resulting from the use of third-party solar panels.',
    ),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def copy_approved() -> None:
    for root in COPIED_ROOTS:
        for path in sorted((REVIEWED / root).rglob('*')):
            if path.is_file():
                target = PACKAGE / path.relative_to(REVIEWED)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)


def correct_pages() -> None:
    for name, old, new in CORRECTIONS:
        path = PACKAGE / 'source' / 'page' / name
        text = (REVIEWED / 'source' / 'page' / name).read_text(encoding='utf-8')
        if text.count(old) != 1:
            raise SystemExit(f'{name}: expected the approved paragraph once, found {text.count(old)}')
        path.write_text(text.replace(old, new), encoding='utf-8')


def manifest() -> None:
    data = read(REVIEWED / 'source_manifest.json')
    data['target']['technical_version'] = PACKAGE.name
    data['source_role'] = 'Git-only English solar-Voc correction edition of the approved release'
    data['publication_eligible'] = STATUS == APPROVED
    data['publication_status'] = STATUS
    data['derived_from'] = {
        'package': REVIEWED.name, 'authorization': 'MA-259',
        'manifest_sha256': sha256(REVIEWED / 'source_manifest.json'),
    }
    data['text_corrections'] = [
        {'page': f'source/page/{name}', 'approved': old, 'corrected': new,
         'reason': 'Solar panels connect through the Jackery DC Input Module; the panel Voc limit is '
                   "the module's DC input voltage range (16V–60V), not the downstream FridgeGuard / "
                   'Battery Pack ranges cited by the printed source.',
         'instruction': 'operator, 2026-10-15: replace the paragraph (整段替换), keep the disclaimer '
                        '(不删免责句); the printed source and its transcription stay unchanged'}
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
    copy_approved()
    correct_pages()
    manifest()
    if (PACKAGE / 'web' / LANGUAGE).is_dir():
        release_manifest()
    print(json.dumps({'package': PACKAGE.name, 'inputs': len(read(PACKAGE / 'source_manifest.json')['inputs'])}))


if __name__ == '__main__':
    main()
