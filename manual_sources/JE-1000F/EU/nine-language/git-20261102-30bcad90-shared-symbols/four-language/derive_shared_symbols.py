"""Derive this sibling of ``git-20260930-c38415f5-shared-keys`` with shared symbols and a battery row.

Run from the repository root:

    python manual_sources/JE-1000F/EU/nine-language/git-20261102-30bcad90-shared-symbols/four-language/derive_shared_symbols.py

Operator request, 2026-11-02: 「先用修正版.ai 把荷波葡乌的电池图标补上」. The revised
AI has no battery row in any of its nine languages, so the operator chose
「网页版单独补（同英法）」: the Web adds the row, as it already does for en/fr/de/es/it.

- The authority for the symbol table is the batch-1465 revised AI
  ``source/JE-1000F_修正版.ai`` from the `发布文档管理` record of JE-1000F; the
  0923 AI (``c38415f5…``) stays as ``superseded_original_source``. All other copy
  is unchanged from the previous package.
- Each of the seven printed rows reuses its shared Web variant byte for byte
  (``SYMBOL_KEYS``) and is bound to its native glyph drawings inside the intake
  ``icon_bbox`` and to its caption pixels on the revised AI. Li-ion differs from
  every shared variant by the batch-1465 design variation and is admitted under
  trusted glyph waivers, as JE-1000H was.
- The eighth row is Web-only: ``battery-weee/crossed-bin-no-bar`` with the
  printed caption of a sibling EU Explorer manual (JE-2000F for pt/nl/pl, JE-3600A for
  uk), bound to that donor row through the trusted
  ``docs/renderers/contracts/symbol_web_only_rows.json``.
- Visible text changes only by the added caption; the MyST is replayed from the
  IR by the public renderer. Each IR becomes publication-eligible only while
  ``approval.json`` matches the replayed Markdown. A second run leaves the tree
  unchanged.
"""
from __future__ import annotations

import hashlib
import html
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

LANGUAGES = ('uk', 'pt', 'nl', 'pl')
TECHNICAL_VERSION = 'git-20261102-30bcad90-shared-symbols'
DERIVED_FROM = 'manual_sources/JE-1000F/EU/nine-language/git-20260930-c38415f5-shared-keys/four-language'
CANDIDATE = 'candidate; operator rendering review and release approval pending'
APPROVED = 'operator-approved-git-only-release'
AUTHORITY = {
    'filename': 'source/JE-1000F_修正版.ai',
    'sha256': '30bcad90ac8c130874db95c76666fb5c905cacc1b59073bd8f9d2db8d714eaf6',
    'physical_page_count': 161,
}
INTAKE_SYMBOLS = REPO / 'manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language/source/symbols.json'
# Existing frozen asset (same bytes in all four languages) -> shared variant.
SYMBOL_KEYS = {
    'assets/6749bd38fdd0_6749bd38fdd0_6749bd38fdd0_warning_triangle.png': 'warning/outline-triangle-tinted',
    'assets/89dae4b809de_89dae4b809de_89dae4b809de_read_manual.png': 'read-manual/book-information',
    'assets/76085a1e7008_76085a1e7008_76085a1e7008_do_not_dismantle.png': 'do-not-dismantle/screwdriver-prohibited',
    'assets/a8a846e9767a_a8a846e9767a_a8a846e9767a_no_open_flame.png': 'no-open-flame/fire-match-prohibited',
    'assets/114690be6f4d_114690be6f4d_114690be6f4d_keep_away_from_children.png':
        'keep-away-from-children/adult-child-prohibited',
    'assets/2a61fc0919cf_2a61fc0919cf_2a61fc0919cf_li_ion.png': 'li-ion/recycle-li-ion-native-dark',
    'assets/7e4de290ea13_7e4de290ea13_7e4de290ea13_weee.png': 'weee/crossed-bin-bar',
}
BATTERY_KEY = 'battery-weee/crossed-bin-no-bar'
JE2000F = 'manual_sources/JE-2000F/EU/nine-language/git-20261010-1465-web/three-language'
JE3600A = 'manual_sources/JE-3600A/EU/es/1465-20261010-r1'
# Printed battery row reused per language: (donor package, trusted entry id).
DONORS = {
    'uk': (JE3600A, 'JE1000F-EU-UK-WEB-BATTERY'),
    'pt': (JE2000F, 'JE1000F-EU-PT-WEB-BATTERY'),
    'nl': (JE2000F, 'JE1000F-EU-NL-WEB-BATTERY'),
    'pl': (JE2000F, 'JE1000F-EU-PL-WEB-BATTERY'),
}
# Donor rows no package binds yet: (physical page, glyph drawing indices). The
# JE-3600A AI carries the uk row also published on the JE-3600A uk Web page.
DONOR_GEOMETRY = {'uk': (94, [745, 746])}
DONOR_FIELDS = ('physical_page', 'drawing_indices', 'glyph_bbox', 'caption_bbox', 'row_bbox',
                'caption_text', 'caption_sha256', 'caption_linebreak_joins')
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


def donor(language: str) -> dict:
    """The printed battery row of the donor manual, with its hash-bound source."""
    package, entry_id = DONORS[language]
    manifest = read(REPO / package / 'source_manifest.json')
    source = manifest['original_source']
    path = f"{package}/{source['filename']}"
    if sha256(REPO / path) != source['sha256']:
        raise SystemExit(f'{language}: donor source missing or changed')
    if language in DONOR_GEOMETRY:
        page_number, ids = DONOR_GEOMETRY[language]
        with fitz.open(REPO / path) as doc:
            page = doc[page_number - 1]
            drawings = page.get_drawings()
            glyph = fitz.Rect(drawings[ids[0]]['rect'])
            for k in ids[1:]:
                glyph |= drawings[k]['rect']
            middle = (glyph.y0 + glyph.y1) / 2
            (block,) = [b for b in page.get_text('blocks') if b[0] > glyph.x1 and b[1] <= middle <= b[3]
                        and b[0] - glyph.x1 < glyph.width * 2]
            if '-\n' in block[4]:
                raise SystemExit(f'{language}: donor caption has a line-end hyphen to bind')
            row = bind_row(page, list(glyph), ' '.join(block[4].split()))
        if row['drawing_indices'] != ids:
            raise SystemExit(f'{language}: donor glyph drawings differ: {row["drawing_indices"]}')
    else:
        (row,) = [r for r in manifest['symbol_asset_admission']['locales'][language]
                  if r['shared_symbol_key'] == BATTERY_KEY]
    return {'entry_id': entry_id, 'source': {'path': path, 'sha256': source['sha256']},
            **{k: row[k] for k in DONOR_FIELDS if k in row}}


def symbol_spec(raw):
    for page in raw['pages']:
        for block in page['blocks']:
            spec = block['payload'].get('component_spec') or {}
            if spec.get('component_id') == 'HB-TABLE-SYMBOL-ICON':
                return spec
    raise SystemExit('symbol table missing')


def bind_symbols(raw, web: Path, language: str) -> list[dict]:
    """Swap the printed rows to shared variants, append the battery row; return the binding rows."""
    replaced = read(PACKAGE / 'source_manifest.json')['derived_from']['replaced_sha256']
    targets = {}
    for old, key in SYMBOL_KEYS.items():
        variant, digest = shared_variant(key)
        targets[old] = (key, variant, digest, f'assets/{digest[:12]}_{variant.name}')
    current = {new: old for old, (_, _, _, new) in targets.items()}
    spec = symbol_spec(raw)
    rows, renames = [], {}
    for ref in [asset['asset_ref'] for asset in spec['assets']]:
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
    spec = symbol_spec(raw)
    variant, digest = shared_variant(BATTERY_KEY)
    battery = f'assets/{digest[:12]}_{variant.name}'
    (web / battery).write_bytes(variant.read_bytes())
    caption = donor(language)['caption_text']
    if battery not in [asset['asset_ref'] for asset in spec['assets']]:
        spec['assets'].append({'asset_ref': battery, 'locale_policy': 'exact', 'role': 'icons'})
        panels = next(slot['content'] for slot in spec['slots'] if slot['role'] == 'panels')
        panels[-1].append({'asset_index': len(spec['assets']) - 1, 'icon_alt': caption,
                           'meaning_html': html.escape(caption), 'meaning_text': caption})
    rows.append({'asset_ref': battery, 'asset_sha256': digest, 'shared_symbol_key': BATTERY_KEY,
                 'decision': 'web-only-row-reusing-donor-print-caption'})
    assets = raw['metadata']['asset_sha256']
    for row in rows:
        assets.pop(row.get('replaced_asset_ref'), None)
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
    markdown = web / f'manual_je1000f_eu_{language}.md'
    base = (REPO / DERIVED_FROM / 'web' / language / markdown.name).read_text(encoding='utf-8')
    expected = sorted(visible(base) + list(''.join(donor(language)['caption_text'].split())))
    raw = read(path)
    rows = bind_symbols(raw, web, language)
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
    if visible(markdown.read_text(encoding='utf-8')) != expected:
        raise SystemExit(f'{language}: visible text differs from the previous package plus the battery caption')
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
    # Hash exactly the stored (rounded) caption box; the gate re-renders that box.
    caption = fitz.Rect([round(v, 2) for v in caption_rect(page.get_text('words'), meaning)])
    band = fitz.Rect(min(glyph.x0, caption.x0) - 1, min(glyph.y0, caption.y0) - 1,
                     max(glyph.x1, caption.x1) + 1, max(glyph.y1, caption.y1) + 1)
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=caption, alpha=False)
    return {
        'physical_page': page.number + 1,
        'glyph_bbox': [round(v, 2) for v in (glyph.x0 - 0.5, glyph.y0 - 0.5, glyph.x1 + 0.5, glyph.y1 + 0.5)],
        'drawing_indices': ids,
        'caption_bbox': list(caption),
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
    """Bind every symbol-table row of one language, in component order."""
    intake = read(INTAKE_SYMBOLS)['locales'][language]
    raw = read(PACKAGE / 'web' / language / 'manual.ir.json')
    spec = symbol_spec(raw)
    panels = next(slot['content'] for slot in spec['slots'] if slot['role'] == 'panels')
    items = [item for panel in panels for item in panel]
    by_ref = {row['asset_ref']: row for row in revision_rows}
    page = doc[intake['pictogram_page'] - 1]
    printed, (battery,) = items[:-1], items[-1:]
    rows = []
    for item, pictogram in zip(printed, intake['pictograms'], strict=True):
        shared = by_ref[spec['assets'][item['asset_index']]['asset_ref']]
        rows.append({'asset_ref': shared['asset_ref'], 'asset_sha256': shared['asset_sha256'],
                     'shared_symbol_key': shared['shared_symbol_key'], 'source_icon_id': pictogram['icon_id'],
                     **bind_row(page, pictogram['icon_bbox'], item['meaning_text'])})
    shared = by_ref[spec['assets'][battery['asset_index']]['asset_ref']]
    row = donor(language)
    if shared['shared_symbol_key'] != BATTERY_KEY or row['caption_text'] != battery['meaning_text']:
        raise SystemExit(f'{language}: battery row differs from its donor')
    rows.append({'asset_ref': shared['asset_ref'], 'asset_sha256': shared['asset_sha256'],
                 'shared_symbol_key': BATTERY_KEY, 'source_icon_id': 'battery_weee',
                 'web_only_row': row.pop('entry_id'), 'donor_source': row.pop('source'), **row})
    return rows


def main() -> None:
    manifest = read(PACKAGE / 'source_manifest.json')
    previous = REPO / DERIVED_FROM
    if 'derived_from' not in manifest:
        manifest['previous_source'] = {'path': DERIVED_FROM, 'sha256': sha256(previous / 'source_manifest.json')}
        manifest['derived_from'] = {'package': DERIVED_FROM, 'replaced_sha256': {
            old: sha256(previous / 'web' / 'nl' / old) for old in SYMBOL_KEYS}}
        write(PACKAGE / 'source_manifest.json', manifest)
    approval_path = PACKAGE / 'approval.json'
    approval = read(approval_path) if approval_path.is_file() else None
    rows = {language: derive(language, None) for language in LANGUAGES}
    # The approval covers exactly the reviewed Markdown; anything else stays a candidate.
    if approval and all(sha256(PACKAGE / 'web' / lang / f'manual_je1000f_eu_{lang}.md')
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
                                           'authority for the printed symbol-table rows'}
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
        'request': 'Operator 2026-11-02: 「先用修正版.ai 把荷波葡乌的电池图标补上」.',
        'decisions': ['2026-11-02 「网页版单独补（同英法）」: the revised AI has no battery row in any language; '
                      'the Web adds it as for en/fr, with a printed sibling caption',
                      'Every row reuses a shared Web variant, as for JE-1000H; Li-ion is admitted under trusted '
                      'glyph waivers for the batch-1465 design variation'],
        'locales': rows,
    }
    files = sorted(p for p in PACKAGE.rglob('*')
                   if p.is_file() and p.name != 'source_manifest.json' and '__pycache__' not in p.parts)
    manifest['inputs'] = [{'path': p.relative_to(PACKAGE).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
                          for p in files]
    write(PACKAGE / 'source_manifest.json', manifest)
    print(json.dumps({lang: sha256(PACKAGE / 'web' / lang / f'manual_je1000f_eu_{lang}.md') for lang in LANGUAGES}))


if __name__ == '__main__':
    main()
