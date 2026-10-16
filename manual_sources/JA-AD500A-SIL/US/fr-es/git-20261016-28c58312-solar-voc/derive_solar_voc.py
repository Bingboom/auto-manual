"""Derive the JA-AD500A-SIL / US / fr+es solar-Voc correction edition from the approved package.

Run from the repository root:

    python manual_sources/JA-AD500A-SIL/US/fr-es/git-20261016-28c58312-solar-voc/derive_solar_voc.py

The approved package ``../git-20261007-28c58312-reviewed`` (MA-262) stays
immutable. This script copies its ``source/`` and ``assets/`` trees
byte-for-byte, applies the text corrections in ``CORRECTIONS`` to the prepared
French and Spanish charging pages and refreshes ``source_manifest.json``; a
second run leaves the tree unchanged. Hand-written ``README.md``,
``render.py``, ``source/differences.md`` and (after acceptance)
``source/approval.json`` are not touched.

``source/native_copy.json`` stays the verbatim transcription of the printed PDF
and keeps the printed wording. ``tests/test_jaad500a_sil_us_solar_voc.py``
proves the rendered Markdown equals the approved Markdown with exactly these
paragraphs replaced.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

PACKAGE = Path(__file__).resolve().parent
REVIEWED = PACKAGE.parent / 'git-20261007-28c58312-reviewed'
REPO = next(parent for parent in PACKAGE.parents if (parent / 'build.py').is_file())

CANDIDATE = 'review-candidate-no-release-authorization'
APPROVED = 'operator-approved-git-only-release'
STATUS = CANDIDATE
LANGUAGES = ('fr', 'es')
# Copied byte-for-byte; the corrections apply on top of the copy.
COPIED_ROOTS = ('source', 'assets')
VOC_CONCERN = 'PV Voc guidance refers to downstream FridgeGuard/Battery Pack ranges'

# (prepared page, approved paragraph, corrected paragraph); each must match exactly once.
CORRECTIONS = [
    (
        'charging_fr.rst',
        'Il est recommandé d’utiliser le panneau solaire Jackery pour charger le Jackery FridgeGuard et '
        'Jackery Battery Pack. Assurez-vous que la tension en circuit ouvert (Voc) du panneau solaire se '
        'situe dans la plage d’entrée CC (36.8 V–56 V) du Jackery FridgeGuard ou dans la plage d’entrée CC '
        '(40 V–57.6 V) du Jackery Battery Pack. Jackery décline toute responsabilité en cas de pertes '
        'causées par l’utilisation de panneaux solaires d’autres marques.',
        'Il est recommandé d’utiliser des panneaux solaires Jackery pour charger le produit connecté via le '
        'Jackery DC Input Module. Assurez-vous que la tension en circuit ouvert (Voc) des panneaux solaires '
        'connectés se situe dans la plage de tension d’entrée CC du module (16 V–60 V). Jackery décline toute '
        'responsabilité en cas de pertes causées par l’utilisation de panneaux solaires d’autres marques.',
    ),
    (
        'charging_es.rst',
        'Se recomienda usar el panel solar Jackery para cargar el Jackery Battery Pack y Jackery FridgeGuard. '
        'Asegúrese de que el voltaje de circuito abierto (Voc) del panel solar esté dentro del rango de entrada '
        'de CC (36.8 V–56 V) del Jackery FridgeGuard o del rango de entrada de CC (40 V–57.6 V) del Jackery '
        'Battery Pack. Jackery no se hace responsable de pérdidas causadas por el uso de paneles solares de '
        'otras marcas.',
        'Se recomienda usar paneles solares Jackery para cargar el producto conectado a través del Jackery DC '
        'Input Module. Asegúrese de que el voltaje en circuito abierto (Voc) de los paneles solares conectados '
        'esté dentro del rango de voltaje de entrada de CC del módulo (16 V–60 V). Jackery no se hace '
        'responsable de pérdidas causadas por el uso de paneles solares de otras marcas.',
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
    data['source_role'] = 'Git-only French/Spanish solar-Voc correction edition of the approved release'
    data['publication_eligible'] = STATUS == APPROVED
    data['publication_status'] = STATUS
    data['derived_from'] = {
        'package': REVIEWED.name, 'authorization': 'MA-262',
        'manifest_sha256': sha256(REVIEWED / 'source_manifest.json'),
    }
    (concern,) = [c for c in data['source_concerns'] if c['issue'] == VOC_CONCERN]
    concern['disposition'] = ("corrected in this edition's prepared pages on operator instruction "
                              '2026-10-15; native_copy.json keeps the printed wording')
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
    if all((PACKAGE / 'web' / lang).is_dir() for lang in LANGUAGES):
        release_manifest()
    print(json.dumps({'package': PACKAGE.name, 'inputs': len(read(PACKAGE / 'source_manifest.json')['inputs'])}))


if __name__ == '__main__':
    main()
