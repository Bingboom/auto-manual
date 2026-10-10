"""Apply the operator's batch-1465 release decisions to this frozen package.

Run from the repository root:

    python manual_sources/JE-2000F/EU/nine-language/git-20261010-1465-web/three-language/finalize_release.py

Operator decisions, 2026-10-10: “按波兰语的顺序调，译文直接用，上线提交发布”.

- pt and nl: in the UPS chapter the retained CAUTION callout moves before the
  WARNING callout, the order the single-copy Polish chapter already has. Blocks
  keep their bytes, ids and source refs; only their order changes.
- pt, nl, pl: the six supplied translations are used as delivered; each IR
  becomes publication-eligible and carries the hash-bound acceptance from
  ``approval.json``.

The MyST is replayed from the IR by the public renderer, then ``verification.json``
and ``source_manifest.json`` are refreshed. A second run leaves the tree unchanged.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parent
REPO = next(parent for parent in PACKAGE.parents if (parent / 'build.py').is_file())
sys.path.insert(0, str(REPO))

from tools.manual_ir import read_manual_ir  # noqa: E402
from tools.manual_ir.document import validate_document  # noqa: E402
from tools.manual_ir.hashing import value_sha256  # noqa: E402
from tools.web.frozen_ai_web import replay_package  # noqa: E402

LANGUAGES = ('pt', 'nl', 'pl')
# The UPS CAUTION label per language; it precedes the WARNING callout as in pl.
CAUTION = {'pt': 'CUIDADO', 'nl': 'OPGELET', 'pl': 'PRZESTROGA'}
WARNING = {'pt': 'AVISO', 'nl': 'WAARSCHUWING', 'pl': 'OSTRZEŻENIE'}
STATUS = 'operator-approved-git-only-release'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, data, *, sort_keys: bool = False) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=sort_keys) + '\n', encoding='utf-8')


def callout_label(block) -> str | None:
    spec = block['payload'].get('component_spec') or {}
    if spec.get('component_id') != 'HB-CALLOUT-STRIP':
        return None
    return next(slot['content'] for slot in spec['slots'] if slot['role'] == 'label')


def reorder_ups(raw, language: str) -> None:
    ups = next(page for page in raw['pages'] if page['page_id'] == 'ups')
    labels = [callout_label(block) for block in ups['blocks']]
    caution, warning = labels.index(CAUTION[language]), labels.index(WARNING[language])
    if labels.count(CAUTION[language]) != 1 or labels.count(WARNING[language]) != 1:
        raise SystemExit(f'{language}: expected one UPS caution and one warning, found {labels}')
    if caution > warning:
        block = ups['blocks'].pop(caution)
        ups['blocks'].insert(warning, block)


def rehash(raw) -> None:
    hashes = []
    for page in raw['pages']:
        for block in page['blocks']:
            if block['content_sha256'] != value_sha256({'kind': block['kind'], 'payload': block['payload']}):
                raise SystemExit(f"{block['block_id']}: block content changed")
            hashes.append(block['content_sha256'])
    raw['content_sha256'] = value_sha256({'page_ids': [p['page_id'] for p in raw['pages']], 'block_hashes': hashes})


def finalize_ir(language: str, approval) -> None:
    path = PACKAGE / 'web' / language / 'manual.ir.json'
    raw = read(path)
    reorder_ups(raw, language)
    rehash(raw)
    metadata = raw['metadata']
    metadata['publication_eligible'] = True
    metadata['pending_source_review'] = []
    metadata['batch_1465'] = {**metadata['batch_1465'], 'status': STATUS}
    metadata['operator_release_approval'] = approval
    write(path, raw, sort_keys=True)
    validate_document(read_manual_ir(path))
    replay_package(path.parent)


def visible(markdown: str) -> list[str]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(markdown, 'html.parser')
    for style in soup.find_all('style'):
        style.decompose()
    return sorted(''.join(soup.get_text('').replace('#', '').split()))


def main() -> None:
    approval = read(PACKAGE / 'approval.json')
    verification = read(PACKAGE / 'verification.json')
    for language in LANGUAGES:
        markdown = PACKAGE / 'web' / language / f'manual_je2000f_eu_{language}.md'
        before = visible(markdown.read_text(encoding='utf-8'))
        finalize_ir(language, approval)
        if visible(markdown.read_text(encoding='utf-8')) != before:
            raise SystemExit(f'{language}: visible text changed while reordering')
        verification[language].update(
            markdown_sha256=sha256(markdown),
            ups_callout_order=[CAUTION[language], WARNING[language]],
            publication_eligible=True,
        )
    write(PACKAGE / 'verification.json', verification)
    manifest = read(PACKAGE / 'source_manifest.json')
    manifest['revision_source']['status'] = STATUS
    manifest['publication_status'] = STATUS
    manifest['validation_boundary'] = (
        'Six PDF notice texts matched; strict IR and deterministic cold replay. Operator approved the '
        'translations as delivered and the Polish UPS callout order for pt/nl (approval.json); '
        'pending engineering merge, generated release PR and RTD readback.'
    )
    files = sorted(p for p in PACKAGE.rglob('*')
                   if p.is_file() and p.name != 'source_manifest.json' and '__pycache__' not in p.parts)
    manifest['inputs'] = [{'path': p.relative_to(PACKAGE).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
                          for p in files]
    write(PACKAGE / 'source_manifest.json', manifest)
    print(json.dumps({lang: verification[lang]['markdown_sha256'] for lang in LANGUAGES}))


if __name__ == '__main__':
    main()
