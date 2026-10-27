"""Derive this sibling of ``git-20261001-8bcb378f-temperature-web`` with shared symbol glyphs.

Run from the repository root:

    python manual_sources/JE-1000H/EU/three-language/git-20261026-8bcb378f-shared-symbols/derive_shared_symbols.py

Operator request, 2026-10-26: 「这个 JE-1000H的图标 改成共用图标」 for the read-manual,
do-not-dismantle, keep-away-from-fire and keep-away-from-children rows; then
“nl/pl/pt 也改”. The approved source package stays untouched; this copy differs
only in its symbol assets: 「那三行也换成共用图标」 (2026-10-27) extends the swap
from the four marked rows to the warning, Li-ion and WEEE rows, so every
symbol-table row is a shared variant.

- Each of the seven rows reuses the selected shared Web variant byte for byte
  (``SYMBOL_KEYS``).
- Captions and all other copy stay unchanged; the visible text is checked.
- The operator reviewed the 1280/390 renderings and decided 「上线提交发布」
  (``approval.json``); each IR becomes publication-eligible only while the
  approval's Markdown hashes match the replayed Markdown, so a later change
  returns the package to candidate until it is approved again. Native
  symbol admission against the HTE159 authority AI, which is not committed
  here, is still enforced when the release is sealed.

The MyST is replayed from the IR by the public renderer. A second run leaves the
tree unchanged.
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
TECHNICAL_VERSION = 'git-20261026-8bcb378f-shared-symbols'
DERIVED_FROM = 'manual_sources/JE-1000H/EU/three-language/git-20261001-8bcb378f-temperature-web'
CANDIDATE = 'candidate; operator rendering review, release approval and native admission pending'
APPROVED = 'operator-approved-git-only-release; native symbol admission pending at seal'
# Existing frozen asset (same bytes in all three languages) -> shared variant.
SYMBOL_KEYS = {
    'assets/e36930ae4711_symbol-read_manual.png': 'read-manual/book-information',
    'assets/2c7663a3294d_symbol-do_not_disassemble.png': 'do-not-dismantle/screwdriver-prohibited',
    'assets/5bb172a98c92_symbol-keep_away_from_fire.png': 'no-open-flame/fire-match-prohibited',
    'assets/8936085b3f6f_symbol-keep_away_from_children.png': 'keep-away-from-children/adult-child-prohibited',
    'assets/9a9a245fe848_symbol-general_warning.png': 'warning/outline-triangle-tinted',
    'assets/11f1a73a4cb5_symbol-lithium_battery.png': 'li-ion/recycle-li-ion',
    'assets/40529e39bab8_symbol-weee.png': 'weee/crossed-bin-bar',
}
SHARED = REPO / 'docs/renderers/web/assets/shared/symbols'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, data, *, sort_keys: bool = False) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=sort_keys) + '\n', encoding='utf-8')


def shared_variant(key: str) -> tuple[Path, str]:
    (entry,) = [a for a in read(SHARED / 'manifest.json')['assets'] if a['key'] == key]
    path = SHARED / entry['path']
    if sha256(path) != entry['sha256']:
        raise SystemExit(f'shared variant changed: {key}')
    return path, entry['sha256']


def symbol_spec(raw):
    for page in raw['pages']:
        for block in page['blocks']:
            spec = block['payload'].get('component_spec') or {}
            if spec.get('component_id') == 'HB-TABLE-SYMBOL-ICON':
                return spec
    raise SystemExit('symbol table missing')


def bind_symbols(raw, web: Path) -> list[dict]:
    """Swap the selected symbol assets for their shared variants; return the binding rows."""
    replaced = read(PACKAGE / 'source_manifest.json')['derived_from']['replaced_sha256']
    targets = {}
    for old, key in SYMBOL_KEYS.items():
        variant, digest = shared_variant(key)
        targets[old] = (key, variant, digest, f'assets/{digest[:12]}_{variant.name}')
    # A rerun finds the shared refs already in place.
    current = {new: old for old, (_, _, _, new) in targets.items()}
    rows, renames = [], {}
    for ref in (asset['asset_ref'] for asset in symbol_spec(raw)['assets']):
        old = ref if ref in targets else current.get(ref)
        if old is None:
            continue
        key, variant, digest, new = targets[old]
        (web / new).write_bytes(variant.read_bytes())
        if ref != new:
            renames[ref] = new
        rows.append({'replaced_asset_ref': old, 'replaced_sha256': replaced[old],
                     'asset_ref': new, 'asset_sha256': digest, 'shared_symbol_key': key,
                     'decision': 'reuse-shared-variant-byte-identical'})
    if len(rows) != len(SYMBOL_KEYS):
        raise SystemExit(f'expected {len(SYMBOL_KEYS)} symbol rows, bound {len(rows)}')
    text = json.dumps(raw, ensure_ascii=False)
    for old, new in renames.items():
        text = text.replace(f'"{old}"', f'"{new}"')
    raw.clear()
    raw.update(json.loads(text))
    assets = raw['metadata']['asset_sha256']
    for row in rows:
        assets.pop(row['replaced_asset_ref'], None)
        assets[row['asset_ref']] = row['asset_sha256']
    raw['metadata']['asset_sha256'] = dict(sorted(assets.items()))
    remaining = json.dumps(raw, ensure_ascii=False)
    for old in SYMBOL_KEYS:
        if f'"{old}"' not in remaining:
            (web / old).unlink(missing_ok=True)
    return rows


def rehash(raw) -> None:
    hashes = []
    for page in raw['pages']:
        for block in page['blocks']:
            block['content_sha256'] = value_sha256({'kind': block['kind'], 'payload': block['payload']})
            hashes.append(block['content_sha256'])
    raw['content_sha256'] = value_sha256({'page_ids': [p['page_id'] for p in raw['pages']], 'block_hashes': hashes})


def visible(markdown: str) -> list[str]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(markdown, 'html.parser')
    for style in soup.find_all('style'):
        style.decompose()
    return sorted(''.join(soup.get_text('').replace('#', '').split()))


def derive(language: str, approval: dict | None) -> list[dict]:
    web = PACKAGE / 'web' / language
    path = web / 'manual.ir.json'
    markdown = web / f'manual_je1000h_eu_{language}.md'
    before = visible(markdown.read_text(encoding='utf-8'))
    raw = read(path)
    rows = bind_symbols(raw, web)
    rehash(raw)
    metadata = raw['metadata']
    metadata['publication_eligible'] = approval is not None
    metadata['pending_source_review'] = [] if approval else [
        'operator review of the 1280/390 renderings and release approval',
        'native symbol admission of the shared variants against the HTE159 authority AI',
    ]
    if approval:
        metadata['operator_release_approval'] = approval
    else:
        metadata.pop('operator_release_approval', None)
    metadata['shared_symbol_revision'] = {'derived_from': DERIVED_FROM,
                                          'status': APPROVED if approval else CANDIDATE, 'rows': rows}
    write(path, raw, sort_keys=True)
    validate_document(read_manual_ir(path))
    replay_package(web)
    if visible(markdown.read_text(encoding='utf-8')) != before:
        raise SystemExit(f'{language}: visible text changed')
    return rows


def main() -> None:
    manifest = read(PACKAGE / 'source_manifest.json')
    derived = manifest.setdefault('derived_from', {'package': DERIVED_FROM, 'replaced_sha256': {}})
    base = REPO / DERIVED_FROM / 'web' / 'nl'
    for old in SYMBOL_KEYS:
        derived['replaced_sha256'].setdefault(old, sha256(base / old))
    write(PACKAGE / 'source_manifest.json', manifest)
    approval_path = PACKAGE / 'approval.json'
    approval = read(approval_path) if approval_path.is_file() else None
    rows = {language: derive(language, None) for language in LANGUAGES}
    # The approval covers exactly the reviewed Markdown; anything else stays a candidate.
    if approval and all(sha256(PACKAGE / 'web' / lang / f'manual_je1000h_eu_{lang}.md')
                        == approval['reviewed_candidate']['markdown_sha256'][lang] for lang in LANGUAGES):
        rows = {language: derive(language, approval) for language in LANGUAGES}
    else:
        approval = None
    manifest = read(PACKAGE / 'source_manifest.json')
    manifest['target']['technical_version'] = TECHNICAL_VERSION
    manifest['publication_status'] = APPROVED if approval else CANDIDATE
    manifest['shared_symbol_revision'] = {
        'request': 'Operator 2026-10-26: 「这个 JE-1000H的图标 改成共用图标」; 「nl/pl/pt 也改」.',
        'decisions': ['2026-10-26 「这个 JE-1000H的图标 改成共用图标」: four marked rows',
                      '2026-10-27 「那三行也换成共用图标」: warning, Li-ion and WEEE rows'],
        'locales': rows,
    }
    files = sorted(p for p in PACKAGE.rglob('*')
                   if p.is_file() and p.name != 'source_manifest.json' and '__pycache__' not in p.parts)
    manifest['inputs'] = [{'path': p.relative_to(PACKAGE).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
                          for p in files]
    write(PACKAGE / 'source_manifest.json', manifest)
    print(json.dumps({lang: sha256(PACKAGE / 'web' / lang / f'manual_je1000h_eu_{lang}.md') for lang in LANGUAGES}))


if __name__ == '__main__':
    main()
