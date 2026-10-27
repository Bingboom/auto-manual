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
  returns the package to candidate until it is approved again.
- Authority: the batch-1465 revised AI ``source/JE-1000H_修正版.ai`` from the
  `发布文档管理` record of JE-1000H (HTE159) replaces the original 0928 AI as
  the symbol authority. Each row is bound to its native glyph drawings inside
  the intake ``icon_bbox`` (``git-20260930-8bcb378f-intake/source/symbols.json``)
  and to its caption pixels, and the bound shared variant is compared with the
  native glyph (``symbol_asset_admission``). The Li-ion row differs from every
  shared variant by a design variation; the operator ruled 「要允许误差 这个误差
  就是人工引入的 你需要处理成共用的」, recorded in the trusted
  ``docs/renderers/contracts/symbol_glyph_waivers.json``.

The MyST is replayed from the IR by the public renderer. A second run leaves the
tree unchanged.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

PACKAGE = Path(__file__).resolve().parent
REPO = next(parent for parent in PACKAGE.parents if (parent / 'build.py').is_file())
sys.path.insert(0, str(REPO))

import fitz  # noqa: E402

from tools.manual_ir import read_manual_ir  # noqa: E402
from tools.manual_ir.document import validate_document  # noqa: E402
from tools.manual_ir.hashing import value_sha256  # noqa: E402
from tools.web.frozen_ai_web import replay_package  # noqa: E402
from tools.web.symbol_asset_admission import SCHEMA as SYMBOL_SCHEMA, require_symbol_asset_admission  # noqa: E402

LANGUAGES = ('pt', 'nl', 'pl')
TECHNICAL_VERSION = 'git-20261026-8bcb378f-shared-symbols'
DERIVED_FROM = 'manual_sources/JE-1000H/EU/three-language/git-20261001-8bcb378f-temperature-web'
CANDIDATE = 'candidate; operator rendering review and release approval pending'
APPROVED = 'operator-approved-git-only-release'
AUTHORITY = {
    'filename': 'source/JE-1000H_修正版.ai',
    'sha256': 'ffbad263b763f60b34df14beabc5afaaf68b9bb8c9b64332f29ce2bc93281fa4',
    'physical_page_count': 161,
}
INTAKE_SYMBOLS = REPO / 'manual_sources/JE-1000H/EU/three-language/git-20260930-8bcb378f-intake/source/symbols.json'
# Existing frozen asset (same bytes in all three languages) -> shared variant.
SYMBOL_KEYS = {
    'assets/e36930ae4711_symbol-read_manual.png': 'read-manual/book-information',
    'assets/2c7663a3294d_symbol-do_not_disassemble.png': 'do-not-dismantle/screwdriver-prohibited',
    'assets/5bb172a98c92_symbol-keep_away_from_fire.png': 'no-open-flame/fire-match-prohibited',
    'assets/8936085b3f6f_symbol-keep_away_from_children.png': 'keep-away-from-children/adult-child-prohibited',
    'assets/9a9a245fe848_symbol-general_warning.png': 'warning/outline-triangle-tinted',
    'assets/11f1a73a4cb5_symbol-lithium_battery.png': 'li-ion/recycle-li-ion-native-dark',
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
    # A rerun finds the shared refs already in place, including an earlier variant choice.
    current = {row['asset_ref']: row['replaced_asset_ref']
               for row in raw['metadata'].get('shared_symbol_revision', {}).get('rows', [])}
    current.update({new: old for old, (_, _, _, new) in targets.items()})
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
    for old in [*SYMBOL_KEYS, *renames]:
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


def bind_row(page, icon_bbox, meaning: str) -> dict:
    """Bind one table row: the native glyph drawings inside its intake icon box and its caption."""
    box = fitz.Rect(icon_bbox) + (-1.5, -1.5, 1.5, 1.5)
    drawings = page.get_drawings()
    ids = [k for k, d in enumerate(drawings)
           if box.contains(d['rect']) and d['rect'].width > 0.2
           and not (d['rect'].height < 1.5 and d['rect'].width > 90)]
    if not ids:
        raise SystemExit(f'no glyph drawings for {meaning[:40]}')
    glyph = fitz.Rect(drawings[ids[0]]['rect'])
    for k in ids[1:]:
        glyph |= drawings[k]['rect']
    caption = caption_rect(page.get_text('words'), meaning)
    band = fitz.Rect(min(glyph.x0, caption.x0) - 1, min(glyph.y0, caption.y0) - 1,
                     max(glyph.x1, caption.x1) + 1, max(glyph.y1, caption.y1) + 1)
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=caption, alpha=False)
    return {
        'physical_page': page.number + 1,
        'glyph_bbox': [round(v, 2) for v in (glyph.x0 - 0.5, glyph.y0 - 0.5, glyph.x1 + 0.5, glyph.y1 + 0.5)],
        'drawing_indices': ids,
        'caption_bbox': [round(v, 2) for v in caption],
        'row_bbox': [round(v, 2) for v in band],
        'caption_text': meaning,
        'caption_sha256': hashlib.sha256(pixels.tobytes('png')).hexdigest(),
    }


def caption_rect(words, meaning: str) -> fitz.Rect:
    want = re.sub(r'\s+', '', meaning).casefold()
    for i in range(len(words)):
        acc = ''
        for j in range(i, min(len(words), i + 160)):
            acc += re.sub(r'\s+', '', words[j][4]).casefold()
            if not want.startswith(acc):
                break
            if acc == want:
                found = words[i:j + 1]
                return fitz.Rect(min(w[0] for w in found) - 0.5, min(w[1] for w in found) - 0.5,
                                 max(w[2] for w in found) + 0.5, max(w[3] for w in found) + 0.5)
    raise SystemExit(f'caption not found in authority AI: {meaning[:40]}')


def admission_rows(language: str, doc, revision_rows: list[dict]) -> list[dict]:
    """Bind every symbol-table row of one language to the authority AI, in component order."""
    intake = read(INTAKE_SYMBOLS)['locales'][language]
    raw = read(PACKAGE / 'web' / language / 'manual.ir.json')
    spec = symbol_spec(raw)
    panels = next(slot['content'] for slot in spec['slots'] if slot['role'] == 'panels')
    items = [item for panel in panels for item in panel]
    by_ref = {row['asset_ref']: row for row in revision_rows}
    page = doc[intake['pictogram_page'] - 1]
    rows = []
    for item, pictogram in zip(items, intake['pictograms'], strict=True):
        shared = by_ref[spec['assets'][item['asset_index']]['asset_ref']]
        rows.append({'asset_ref': shared['asset_ref'], 'asset_sha256': shared['asset_sha256'],
                     'shared_symbol_key': shared['shared_symbol_key'], 'source_icon_id': pictogram['icon_id'],
                     **bind_row(page, pictogram['icon_bbox'], item['meaning_text'])})
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
    authority = PACKAGE / AUTHORITY['filename']
    if sha256(authority) != AUTHORITY['sha256']:
        raise SystemExit('authority AI missing or changed')
    if manifest['original_source']['sha256'] != AUTHORITY['sha256']:
        manifest['superseded_original_source'] = manifest['original_source']
    manifest['original_source'] = {**AUTHORITY, 'size_bytes': authority.stat().st_size,
                                   'role': 'batch-1465 revised AI (PDF-compatible) from the 发布文档管理 record; '
                                           'authority for the symbol-table rows'}
    with fitz.open(authority) as doc:
        if doc.page_count != AUTHORITY['physical_page_count']:
            raise SystemExit('authority page count changed')
        locales = {lang: admission_rows(lang, doc, rows[lang]) for lang in LANGUAGES}
    manifest['symbol_asset_admission'] = {'schema_version': SYMBOL_SCHEMA, 'locales': locales}
    for lang in LANGUAGES:
        report = require_symbol_asset_admission(PACKAGE / 'web' / lang, PACKAGE, manifest, lang)
        for row, result in zip(locales[lang], report, strict=True):
            row['comparison'] = {k: v for k, v in result.items() if k not in ('asset_ref', 'physical_page')}
    manifest['target']['technical_version'] = TECHNICAL_VERSION
    manifest['publication_status'] = APPROVED if approval else CANDIDATE
    manifest['shared_symbol_revision'] = {
        'request': 'Operator 2026-10-26: 「这个 JE-1000H的图标 改成共用图标」; 「nl/pl/pt 也改」.',
        'decisions': ['2026-10-26 「这个 JE-1000H的图标 改成共用图标」: four marked rows',
                      '2026-10-27 「那三行也换成共用图标」: warning, Li-ion and WEEE rows',
                      '2026-10-27 「要允许误差 这个误差 就是人工引入的 你需要处理成共用的」: '
                      'Li-ion uses the closest shared variant under a trusted glyph waiver'],
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
