"""Apply the operator's batch-1465 release decisions to this frozen package.

Run from the repository root with requirements.lock (PyMuPDF 1.28.0):

    python manual_sources/JE-2000F/EU/nine-language/git-20261010-1465-web/three-language/finalize_release.py

Operator decisions, 2026-10-10: “按波兰语的顺序调，译文直接用，上线提交发布”, with the
batch-1465 authority file ``source/JE-2000F_修正版.ai`` supplied for release admission.

- pt and nl: in the UPS chapter the retained CAUTION callout moves before the
  WARNING callout, the order the single-copy Polish chapter already has. Blocks
  keep their bytes, ids and source refs; only their order changes.
- pt, nl, pl: the six supplied translations are used as delivered.
- Symbol tables (pp. 117/135/153): every glyph is bound to its native source row
  and replaced by the shared Web variant that passes the fixed native comparison
  (``SYMBOL_KEYS``). Captions and all other copy stay unchanged.
- The component inventory declaration is recomputed from the actual flow (pl
  gained one callout in the candidate without a declaration update).
- Each IR becomes publication-eligible with the hash-bound ``approval.json``.

The MyST is replayed from the IR by the public renderer, then ``verification.json``
and ``source_manifest.json`` are refreshed. A second run leaves the tree unchanged.
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
from tools.web.frozen_web_component_coverage import audit_frozen_component_coverage  # noqa: E402
from tools.web.symbol_asset_admission import SCHEMA as SYMBOL_SCHEMA, _reference, compare_symbol  # noqa: E402

LANGUAGES = ('pt', 'nl', 'pl')
# The UPS CAUTION label per language; it precedes the WARNING callout as in pl.
CAUTION = {'pt': 'CUIDADO', 'nl': 'OPGELET', 'pl': 'PRZESTROGA'}
WARNING = {'pt': 'AVISO', 'nl': 'WAARSCHUWING', 'pl': 'OSTRZEŻENIE'}
STATUS = 'operator-approved-git-only-release'
AUTHORITY = {
    'filename': 'source/JE-2000F_修正版.ai',
    'sha256': 'b6587afd053f92578c49eb7acff0dccabe10dc04a70bd178d60996419c9c82d7',
    'physical_page_count': 170,
}
SYMBOL_PAGES = {'pt': 117, 'nl': 135, 'pl': 153}
# Shared variant per symbol-table row (same row order in every language).
SYMBOL_KEYS = [
    'warning/outline-triangle-tinted',
    'read-manual/book-information',
    'do-not-dismantle/screwdriver-prohibited',
    'no-open-flame/crossed-fire-je2000f',
    'keep-away-from-children/h1-jp-native',
    'li-ion/htp017-recycle-li-ion',
    'battery-weee/crossed-bin-no-bar',
    'weee/crossed-bin-bar',
]
SHARED = REPO / 'docs/renderers/web/assets/shared/symbols'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, data, *, sort_keys: bool = False) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=sort_keys) + '\n', encoding='utf-8')


def norm(text: str) -> str:
    return re.sub(r'\s+', '', text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')).casefold()


# --------------------------------------------------------------- UPS order

def callout_label(block) -> str | None:
    spec = block['payload'].get('component_spec') or {}
    if spec.get('component_id') != 'HB-CALLOUT-STRIP':
        return None
    return next(slot['content'] for slot in spec['slots'] if slot['role'] == 'label')


def reorder_ups(raw, language: str) -> None:
    ups = next(page for page in raw['pages'] if page['page_id'] == 'ups')
    labels = [callout_label(block) for block in ups['blocks']]
    if labels.count(CAUTION[language]) != 1 or labels.count(WARNING[language]) != 1:
        raise SystemExit(f'{language}: expected one UPS caution and one warning, found {labels}')
    caution, warning = labels.index(CAUTION[language]), labels.index(WARNING[language])
    if caution > warning:
        ups['blocks'].insert(warning, ups['blocks'].pop(caution))


# ----------------------------------------------------------------- symbols

def symbol_spec(raw):
    for page in raw['pages']:
        for block in page['blocks']:
            spec = block['payload'].get('component_spec') or {}
            if spec.get('component_id') == 'HB-TABLE-SYMBOL-ICON':
                return spec
    raise SystemExit('symbol table missing')


def symbol_items(spec):
    panels = next(slot['content'] for slot in spec['slots'] if slot['role'] == 'panels')
    return [item for panel in panels for item in panel]


def caption_rect(words, meaning: str) -> fitz.Rect:
    want = norm(meaning)
    for i in range(len(words)):
        acc = ''
        for j in range(i, min(len(words), i + 160)):
            acc += norm(words[j][4])
            if not want.startswith(acc):
                break
            if acc == want:
                ws = words[i:j + 1]
                return fitz.Rect(min(w[0] for w in ws) - 0.5, min(w[1] for w in ws) - 0.5,
                                 max(w[2] for w in ws) + 0.5, max(w[3] for w in ws) + 0.5)
    raise SystemExit(f'caption not found in authority PDF: {meaning[:40]}')


def symbol_row(page, meaning: str) -> dict:
    """Bind one table row: its caption words, its row band and the glyph drawings in its symbol cell."""
    drawings = page.get_drawings()
    rules = sorted({round(d['rect'].y0, 1) for d in drawings
                    if d['rect'].height < 1.5 and d['rect'].width > 90 and d['rect'].y0 < 240})
    caption = caption_rect(page.get_text('words'), meaning)
    left = 33 if caption.x0 < 180 else 189
    right = caption.x0 - 3
    top = max([y for y in rules if y <= caption.y0 + 2], default=40)
    bottom = min([y for y in rules if y >= caption.y1 - 2], default=230)
    band = fitz.Rect(left, min(top, caption.y0), caption.x1 + 2, max(bottom, caption.y1))
    glyph_ids = [k for k, d in enumerate(drawings)
                 if d['rect'].x0 >= left and d['rect'].x1 <= right and d['rect'].y0 >= top - 0.1
                 and d['rect'].y1 <= bottom + 0.1 and d['rect'].width > 0.2
                 and d['rect'].width <= (right - left) * 0.85]
    if not glyph_ids:
        raise SystemExit(f'no glyph drawings for {meaning[:40]}')
    glyph = fitz.Rect(drawings[glyph_ids[0]]['rect'])
    for k in glyph_ids[1:]:
        glyph |= drawings[k]['rect']
    row = {
        'physical_page': page.number + 1,
        'glyph_bbox': [round(v, 2) for v in (glyph.x0 - 0.5, glyph.y0 - 0.5, glyph.x1 + 0.5, glyph.y1 + 0.5)],
        'drawing_indices': glyph_ids,
        'caption_bbox': [round(v, 2) for v in caption],
        'row_bbox': [round(v, 2) for v in band],
        'caption_text': meaning,
    }
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(row['caption_bbox']), alpha=False)
    row['caption_sha256'] = hashlib.sha256(pixels.tobytes('png')).hexdigest()
    return row


def shared_variant(key: str) -> tuple[Path, str]:
    (entry,) = [a for a in read(SHARED / 'manifest.json')['assets'] if a['key'] == key]
    path = SHARED / entry['path']
    if sha256(path) != entry['sha256']:
        raise SystemExit(f'shared variant changed: {key}')
    return path, entry['sha256']


def bind_symbols(raw, language: str, web: Path, doc) -> list[dict]:
    """Swap every symbol asset for its admitted shared variant; return the admission rows."""
    spec = symbol_spec(raw)
    items = symbol_items(spec)
    if len(items) != len(SYMBOL_KEYS):
        raise SystemExit(f'{language}: symbol table has {len(items)} rows')
    page = doc[SYMBOL_PAGES[language] - 1]
    rows, renames = [], {}
    for item, key in zip(items, SYMBOL_KEYS, strict=True):
        variant, digest = shared_variant(key)
        row = symbol_row(page, item['meaning_text'])
        reference = _reference(page, row, item['meaning_text'])
        comparison = compare_symbol(variant.read_bytes(), variant.suffix, reference)
        old = spec['assets'][item['asset_index']]['asset_ref']
        new = f'assets/{digest[:12]}_{variant.name}'
        target = web / new
        target.write_bytes(variant.read_bytes())
        if old != new:
            renames[old] = new
        rows.append({'asset_ref': new, **row, 'asset_sha256': digest, 'shared_symbol_key': key,
                     'comparison': comparison, 'decision': 'reuse-shared-variant-byte-identical'})
    text = json.dumps(raw, ensure_ascii=False)
    for old, new in renames.items():
        text = text.replace(f'"{old}"', f'"{new}"')
    raw.clear()
    raw.update(json.loads(text))
    assets = raw['metadata']['asset_sha256']
    for old, new in renames.items():
        assets.pop(old, None)
    for row in rows:
        assets[row['asset_ref']] = row['asset_sha256']
    raw['metadata']['asset_sha256'] = dict(sorted(assets.items()))
    remaining = json.dumps(raw, ensure_ascii=False)
    for old in renames:
        if f'"{old}"' not in remaining:
            (web / old).unlink(missing_ok=True)
    return rows


# ---------------------------------------------------------------- finalize

def rehash(raw) -> None:
    hashes = []
    for page in raw['pages']:
        for block in page['blocks']:
            block['content_sha256'] = value_sha256({'kind': block['kind'], 'payload': block['payload']})
            hashes.append(block['content_sha256'])
    raw['content_sha256'] = value_sha256({'page_ids': [p['page_id'] for p in raw['pages']], 'block_hashes': hashes})


def finalize_ir(language: str, approval, doc) -> list[dict]:
    web = PACKAGE / 'web' / language
    path = web / 'manual.ir.json'
    raw = read(path)
    reorder_ups(raw, language)
    rows = bind_symbols(raw, language, web, doc)
    rehash(raw)
    metadata = raw['metadata']
    metadata['publication_eligible'] = True
    metadata['pending_source_review'] = []
    metadata['batch_1465'] = {**metadata['batch_1465'], 'status': STATUS}
    metadata['operator_release_approval'] = approval
    # The batch-1465 candidate added a pl callout without updating this declaration.
    metadata['component_inventory'] = dict(sorted(audit_frozen_component_coverage(raw)['components'].items()))
    write(path, raw, sort_keys=True)
    validate_document(read_manual_ir(path))
    replay_package(web)
    return rows


def visible(markdown: str) -> list[str]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(markdown, 'html.parser')
    for style in soup.find_all('style'):
        style.decompose()
    return sorted(''.join(soup.get_text('').replace('#', '').split()))


def main() -> None:
    authority = PACKAGE / AUTHORITY['filename']
    if sha256(authority) != AUTHORITY['sha256']:
        raise SystemExit('authority source missing or changed')
    approval = read(PACKAGE / 'approval.json')
    verification = read(PACKAGE / 'verification.json')
    admission = {}
    with fitz.open(authority) as doc:
        if doc.page_count != AUTHORITY['physical_page_count']:
            raise SystemExit('authority page count changed')
        for language in LANGUAGES:
            markdown = PACKAGE / 'web' / language / f'manual_je2000f_eu_{language}.md'
            before = visible(markdown.read_text(encoding='utf-8'))
            admission[language] = finalize_ir(language, approval, doc)
            if visible(markdown.read_text(encoding='utf-8')) != before:
                raise SystemExit(f'{language}: visible text changed')
            verification[language].update(
                markdown_sha256=sha256(markdown),
                ups_callout_order=[CAUTION[language], WARNING[language]],
                symbol_admission_rows=len(admission[language]),
                publication_eligible=True,
            )
    write(PACKAGE / 'verification.json', verification)
    manifest = read(PACKAGE / 'source_manifest.json')
    if manifest['original_source']['sha256'] != AUTHORITY['sha256']:
        manifest['superseded_original_source'] = manifest['original_source']
    manifest['original_source'] = {**AUTHORITY, 'size_bytes': authority.stat().st_size,
                                   'role': 'batch-1465 revised AI (PDF-compatible); authority for the six notices and symbol rows'}
    manifest['revision_source']['status'] = STATUS
    manifest['publication_status'] = STATUS
    manifest['symbol_asset_admission'] = {'schema_version': SYMBOL_SCHEMA, 'locales': admission}
    manifest['validation_boundary'] = (
        'Six notice texts and every symbol-table row are bound to the batch-1465 revised AI; strict IR and '
        'deterministic cold replay. Operator approved the translations as delivered and the Polish UPS callout '
        'order for pt/nl (approval.json); pending engineering merge, generated release PR and RTD readback.'
    )
    files = sorted(p for p in PACKAGE.rglob('*')
                   if p.is_file() and p.name != 'source_manifest.json' and '__pycache__' not in p.parts)
    manifest['inputs'] = [{'path': p.relative_to(PACKAGE).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
                          for p in files]
    write(PACKAGE / 'source_manifest.json', manifest)
    print(json.dumps({lang: verification[lang]['markdown_sha256'] for lang in LANGUAGES}))


if __name__ == '__main__':
    main()
