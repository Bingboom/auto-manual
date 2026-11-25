"""Derive the SlimPower H1 (JE-1000E-WH / JP / ja) Web-layout edition.

Run from the repository root with the pinned dependencies (requirements.lock,
PyMuPDF 1.28.0 / MuPDF 1.29.0) and the original PDF available locally:

    python manual_sources/JE-1000E-WH/JP/ja/git-20261125-efb663e3-web-layout/derive_web_layout.py --pdf <original.pdf>

The PDF must match the SHA-256 in the package's source pointer (the Feishu
attachment the pointer names). The approved solar-Voc edition
``../git-20261016-efb663e3-solar-voc`` (MA-312) stays immutable. This script
copies its pointer, artwork, provenance, ``source/`` tree, ``rebuild.py`` and
``verify.py`` byte-for-byte, then applies the layout changes in ``LAYOUT`` to
``source/chapters.json``, re-renders the art listed in ``ART`` with the shared
asset pipeline, regenerates the generated tail of ``source/presentation.css``
and writes ``source_manifest.json``. A second run leaves the tree unchanged.
Hand-written ``README.md`` and ``source/differences.md`` are not touched.

Visible Japanese copy is never edited. Every change only splits, groups or
marks up approved text (bold leads, print line breaks, list items, heading
levels, label geometry); ``tests/test_je1000e_wh_jp_web_layout.py`` proves the
visible text equals the approved text apart from the declared differences.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

PACKAGE = Path(__file__).resolve().parent
BASE = PACKAGE.parent / 'git-20261016-efb663e3-solar-voc'
REPO = next(parent for parent in PACKAGE.parents if (parent / 'build.py').is_file())
sys.path.insert(0, str(REPO))

CANDIDATE = 'review-candidate-no-release-authorization'
APPROVED = 'operator-approved-git-only-release'
STATUS = APPROVED  # operator 2026-11-25 「上线」 after reviewing candidate 95d63489 (MA-487)
PDF = 'Jackery SlimPower H1取扱説明書V2.0-2026-07-29.pdf'
PDF_SHA256 = 'efb663e3b22fec90bb8d4f602cb830471360034d9ead9293168f708ce937c3be'
# Copied byte-for-byte; the base edition's derivation script, docs, approval and web are not.
COPIED = (f'{PDF}.source-pointer.json', 'artwork', 'asset_provenance.json', 'source',
          'rebuild.py', 'verify.py')
NOT_COPIED = {'source/approval.json', 'source/differences.md'}  # acceptance and the hand-written record


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


# ------------------------------------------------------------------ copy

def copy_base() -> None:
    for name in COPIED:
        source = BASE / name
        paths = sorted(p for p in source.rglob('*') if p.is_file()) if source.is_dir() else [source]
        for path in paths:
            relative = path.relative_to(BASE).as_posix()
            if relative in NOT_COPIED or '__pycache__' in path.parts:
                continue
            target = PACKAGE / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


# -------------------------------------------------------------- chapters

def chapter(chapters: list[dict], page_id: str) -> dict:
    (found,) = [c for c in chapters if c['page_id'] == page_id]
    return found


def leaves(value) -> str:
    """Visible copy of flow nodes, whitespace removed (the copy-preservation invariant)."""
    if isinstance(value, list):
        return ''.join(leaves(v) for v in value)
    if not isinstance(value, dict):
        return ''
    if value.get('kind') == 'text':
        return ''.join(value['text'].split())
    if value.get('kind') == 'component':
        return leaves(value.get('carrier_flow', []))
    return ''.join(leaves(child) for child in value.get('children', []))


def same_copy(where: str, before, after) -> None:
    if leaves(before) != leaves(after):
        raise SystemExit(f'{where}: layout change altered the visible copy')


def text(value: str) -> dict:
    return {'kind': 'text', 'text': value}


def strong(value: str) -> dict:
    return {'kind': 'strong', 'children': [text(value)]}


def brk() -> dict:
    return {'kind': 'line_break'}


def paragraph(*children: dict) -> dict:
    return {'kind': 'paragraph', 'children': list(children)}


def bullet_list(items: list[str]) -> dict:
    return {'kind': 'list', 'ordered': False,
            'children': [{'kind': 'list_item', 'children': [text(item)]} for item in items]}


def split_at(value: str, count: int) -> tuple[str, str]:
    """Split ``value`` after ``count`` non-whitespace characters."""
    seen = 0
    for index, char in enumerate(value):
        if not char.isspace():
            seen += 1
            if seen == count:
                return value[:index + 1], value[index + 1:]
    raise SystemExit(f'cannot split {value!r} after {count} characters')


def bold_runs(pdf, pages) -> list[str]:
    """Whitespace-free text of each consecutive run of bold body spans on the pages."""
    runs = []
    for number in pages:
        for block in pdf[number - 1].get_text('dict')['blocks']:
            current = ''
            for line in block.get('lines', []):
                for span in line['spans']:
                    value = ''.join(span['text'].split())
                    if not value:
                        continue
                    if span['flags'] & 16 and span['size'] < 9:
                        current += value
                    elif current:
                        runs.append(current)
                        current = ''
            if current:
                runs.append(current)
    return runs


def bold_lead(value: str, runs: list[str]) -> list[dict]:
    """Mark the printed bold lead of one item; a regular remainder follows a print line break."""
    flat = ''.join(value.split())
    lead = max((run for run in runs if len(run) >= 4 and flat.startswith(run)), key=len, default='')
    if not lead:
        return [text(value)]
    head, rest = split_at(value, len(lead))
    return [strong(head.strip())] + ([brk(), text(rest.strip())] if rest.strip() else [])


def callout_parts(block: dict) -> tuple[dict, list[dict]]:
    spec = block['component_spec']
    slots = {slot['role']: slot['content'] for slot in spec['slots']}
    body = block['carrier_flow'][0]['children'][0]['children'][0]['children'][1]['children']
    return {'label': slots['label'], 'variant': spec['variant'], 'language': spec['language'],
            'source_ref': spec['source_ref']}, body


def rebuild_callout(block: dict, body: list[dict]) -> dict:
    from tools.web.frozen_ai_flow import callout

    meta, old_body = callout_parts(block)
    same_copy(meta['source_ref'], old_body, body)
    node = callout(meta['label'], body, variant=meta['variant'], language=meta['language'],
                   source_ref=meta['source_ref'])
    return {'schema_version': 'manual-flow/v2', **node}


def find_component(chapters: list[dict], page_id: str, source_ref: str) -> int:
    blocks = chapter(chapters, page_id)['blocks']
    (index,) = [i for i, b in enumerate(blocks) if b.get('kind') == 'component'
                and b['component_spec']['source_ref'] == source_ref]
    return index


# Safety pictogram tables print a bold lead and a regular explanation per item (p4-p5).
SAFETY_CALLOUTS = ('ja/p4/notice-12', 'ja/p4/notice-11', 'ja/p5/notice-5')


def safety_bold_leads(chapters: list[dict], context: dict) -> None:
    runs = bold_runs(context['pdf'], (4, 5))
    blocks = chapter(chapters, 'safety')['blocks']
    for ref in SAFETY_CALLOUTS:
        index = find_component(chapters, 'safety', ref)
        _, body = callout_parts(blocks[index])
        new_body = [paragraph(*bold_lead(item['children'][0]['text'], runs))
                    if item['kind'] == 'paragraph' and len(item['children']) == 1 else deepcopy(item)
                    for item in body]
        if not any(child['kind'] == 'strong' for item in new_body for child in item.get('children', [])):
            raise SystemExit(f'{ref}: no printed bold lead matched')
        blocks[index] = rebuild_callout(blocks[index], new_body)


# Callouts whose printed items run into one paragraph: (page, source_ref, item marker).
MARKED_ITEMS = [
    ('installation', 'ja/p12/notice-7', '・'),
    ('charging', 'ja/p18/notice-9', '•'),
    ('charging', 'ja/p18/notice-11', '•'),
    ('maintenance', 'ja/p20/notice-7', '·'),
]


def marked_items(chapters: list[dict], context: dict) -> None:
    """One printed line per marked item; the printed marker stays part of the copy."""
    for page_id, ref, marker in MARKED_ITEMS:
        blocks = chapter(chapters, page_id)['blocks']
        index = find_component(chapters, page_id, ref)
        _, body = callout_parts(blocks[index])
        (only,) = body
        value = only['children'][0]['text']
        parts = [marker + part for part in value.split(marker)[1:]]
        if value.split(marker)[0].strip() or len(parts) < 2:
            raise SystemExit(f'{ref}: expected marker-led items')
        blocks[index] = rebuild_callout(blocks[index], [paragraph(text(p.strip())) for p in parts])


# ----------------------------------------------------- live-label figures
#
# Each figure is a textless source-local crop of the JP print panel with its
# printed lines as live labels at their print position and type size. The
# reused US-edition art for power / stand / wood / concrete preparation drew a
# different composition, so the JP labels fell on the wrong objects; the
# overview and App rows keep their source crops but gain print geometry.
# label: (printed lines, align, bold). ``panel_label`` moves a printed panel
# caption that the approved edition promoted to a heading back into its panel.

FIGURES = {
    # The ⎓ DC symbols print as separate text spans; the live label carries them.
    'overview': {'page': 8, 'clip': [27, 57, 344, 287], 'labels': [
        (['DC 拡張ポート端子'], 'right', True),
        (['DC入力: 36.8V-56V⎓最大24A，最大500W', 'DC出力: 36.8V-56V⎓最大24A'], 'right', False),
        (['サーモベント@left'], 'left', True),
        (['サーモベント@right'], 'right', True),
        (['主電源ボタン'], 'left', True),
        (['LCD ディスプレイ'], 'left', True),
        (['AC 入力ポート'], 'right', True),
        (['100V-120V~ 50/60Hz,', '最大15A'], 'right', False),
        (['AC 出力ポート'], 'right', True),
        (['100V~50/60Hz，8A，800W'], 'right', False)]},
    # The standby note stays a paragraph after the figure; its empty print bubble is whited out.
    'power': {'page': 10, 'clip': [29, 309, 343, 490], 'whiteout': [[133, 402, 329, 476]], 'labels': [
        (['オフ'], 'left', True), (['1回押す'], 'left', False),
        (['オン'], 'left', True), (['3秒間長押し'], 'left', False), (['3s'], 'left', False)]},
    'stand_prepare': {'page': 12, 'clip': [29.4, 289.3, 251.7, 376.3], 'panel_label': '設置前の準備。',
                      'labels': [(['設置前の準備。'], 'left', False)]},
    'wood_prepare': {'page': 13, 'clip': [28.3, 329, 346, 498], 'panel_label': '取付前の準備。', 'labels': [
        (['取付前の準備。'], 'left', False), (['別売'], 'left', True),
        (['壁の中にある細い柱(間柱)'], 'left', False)]},
    'concrete_prepare': {'page': 15, 'clip': [26.6, 211, 340, 370], 'panel_label': '取付前の準備：',
                         'labels': [(['取付前の準備：'], 'left', False), (['別売'], 'left', True)]},
    'app-phones': {'page': 25, 'clip': [94, 229, 257, 387], 'redact': [94, 370.5, 257, 387],
                   'caption_paragraph': '2.1 / 2.2',
                   'labels': [(['2.1'], 'center', False), (['2.2'], 'center', False)]},
    'app-result': {'page': 26, 'clip': [55, 156, 316, 318], 'redact': [55, 303.5, 316, 318],
                   'caption_paragraph': '2.3 / 2.4 / 2.5',
                   'labels': [(['2.3'], 'center', False), (['2.4'], 'center', False), (['2.5'], 'center', False)]},
}


def print_lines(page, clip) -> list[dict]:
    """Printed text lines inside ``clip`` with geometry, size and weight."""
    found = []
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            for span in line['spans']:
                if not span['text'].strip():
                    continue
                box = span['bbox']
                if clip[0] - 1 <= box[0] and box[2] <= clip[2] + 1 and clip[1] - 1 <= box[1] and box[3] <= clip[3] + 1:
                    found.append({'text': span['text'].strip(), 'bbox': list(box), 'size': span['size'],
                                  'bold': bool(span['flags'] & 16)})
    merged: list[dict] = []  # spans sharing a baseline are one printed line
    for item in sorted(found, key=lambda s: (round(s['bbox'][3]), s['bbox'][0])):
        last = merged[-1] if merged else None
        if last and abs(last['bbox'][3] - item['bbox'][3]) < 1 and -1 < item['bbox'][0] - last['bbox'][2] < 6:
            last['text'] += item['text']
            last['bbox'] = [min(last['bbox'][0], item['bbox'][0]), min(last['bbox'][1], item['bbox'][1]),
                            max(last['bbox'][2], item['bbox'][2]), max(last['bbox'][3], item['bbox'][3])]
        else:
            merged.append(dict(item))
    return merged


def pick_line(lines: list[dict], wanted: str, used: set[int]) -> dict:
    name, _, side = wanted.partition('@')
    hits = [i for i, line in enumerate(lines) if i not in used
            and ''.join(line['text'].split()) == ''.join(name.replace('⎓', '').split())]
    if side:
        hits.sort(key=lambda i: lines[i]['bbox'][0], reverse=side == 'right')
    if not hits:
        raise SystemExit(f'printed line {wanted!r} not found in the figure clip')
    used.add(hits[0])
    return lines[hits[0]]


def label_rect(box, clip, align, size, first_center) -> list[float]:
    cw, ch = clip[2] - clip[0], clip[3] - clip[1]
    top = first_center - 0.58 * size  # CSS line box (line-height 1.16) centred on the printed line
    x, y = (box[0] - clip[0]) / cw * 100, (top - clip[1]) / ch * 100
    w = (box[2] - box[0]) / cw * 100
    grown = max(w + 4, 6)
    if align == 'right':
        x = x + w - grown
    elif align == 'center':
        x = x + w / 2 - grown / 2
    x = min(max(0.0, x), 100 - grown)
    return [round(x, 3), round(max(0.0, y), 3), round(min(grown, 100.0), 3), 0]


def figure_block(chapters: list[dict], slug: str) -> tuple[list[dict], int]:
    for item in chapters:
        for index, block in enumerate(item['blocks']):
            if (block.get('kind') == 'component'
                    and block['component_spec']['component_id'] == 'HB-SPECIAL-REFERENCE-FIGURE'
                    and {s['role']: s['content'] for s in block['component_spec']['slots']}.get('reference_id') == slug):
                return item['blocks'], index
    raise SystemExit(f'figure {slug!r} not found')


def labelled_figures(chapters: list[dict], context: dict) -> None:
    pdf = context['pdf']
    context['label_css'] = []
    for slug, plan in FIGURES.items():
        blocks, index = figure_block(chapters, slug)
        block = blocks[index]
        clip = plan['clip']
        lines = print_lines(pdf[plan['page'] - 1], clip)
        used: set[int] = set()
        labels = []
        for wanted, align, bold in plan['labels']:
            picked = [pick_line(lines, w, used) for w in wanted]
            copy = [w.partition('@')[0] for w in wanted]  # approved wording; the PDF gives geometry only
            html_lines = [('<strong>%s</strong>' if bold else '%s') % c for c in copy]
            box = [min(p['bbox'][0] for p in picked), min(p['bbox'][1] for p in picked),
                   max(p['bbox'][2] for p in picked), max(p['bbox'][3] for p in picked)]
            labels.append({'html': '<br/>'.join(html_lines), 'text': '\n'.join(copy),
                           'rect': label_rect(box, clip, align, picked[0]['size'],
                                              (picked[0]['bbox'][1] + picked[0]['bbox'][3]) / 2), 'align': align,
                           'size': round(picked[0]['size'] / (clip[2] - clip[0]) * 100, 3),
                           'rows': len(picked)})
        # Copy invariant: the figure's captions (plus a moved panel heading / caption row) are unchanged.
        spec = block['component_spec']
        slots = {s['role']: s for s in spec['slots']}
        before = [c['text'] for c in slots['captions']['content']] if 'captions' in slots else []
        moved_before = []
        if plan.get('panel_label'):
            heading = blocks[index - 1]
            if heading.get('kind') != 'heading' or leaves(heading) != ''.join(plan['panel_label'].split()):
                raise SystemExit(f'{slug}: expected the promoted panel heading before the figure')
            moved_before.append(plan['panel_label'])
        if plan.get('caption_paragraph'):
            caption = blocks[index - 1]
            if caption.get('kind') != 'paragraph' or leaves(caption) != ''.join(plan['caption_paragraph'].split()):
                raise SystemExit(f'{slug}: expected the caption paragraph before the figure')
        context.setdefault('figure_copy', {})[slug] = {
            'before': moved_before + before, 'after': [label['text'] for label in labels]}
        captions = [{'html': label['html'], 'text': label['text'].replace('\n', ' ')} for label in labels]
        wanted_slots = {'caption_mode': ('inline_text', 'live'), 'caption_layout': ('inline_text', 'equal'),
                        'captions': ('ordered_labels', captions)}
        for role, (kind, content) in wanted_slots.items():
            if role in slots:
                slots[role]['content'] = content
            else:
                spec['slots'].append({'role': role, 'content_kind': kind, 'content': content})
        meta = spec['metadata']
        meta.update({'capture_following_lines': len(labels), 'captions_embedded': False,
                     'captions_origin': 'carrier', 'caption_centers_pct': None,
                     'presentation_mode': 'base-art-live-copy', 'image_key': slug,
                     'base_art_layout': {'art_sha256': None, 'panel_top': 0, 'panel_fill': '#ffffff',
                                         'preserve_frame': True, 'mobile_labels': 'stack',
                                         'labels': [{'line': i, 'rect': label['rect']} for i, label in enumerate(labels)]}})
        art = f'assets/{slug}.png'
        block['carrier_flow'] = [
            {'kind': 'image', 'source': art, 'alt': slug},
            {'kind': 'group', 'role': 'container',
             'presentation': {'html': {'attributes': {'class': 'line-block'}}},
             'children': [{'kind': 'group', 'role': 'container',
                           'presentation': {'html': {'attributes': {'class': 'line'}}},
                           'children': _label_inline(label['html'])} for label in labels]}]
        if plan.get('panel_label') or plan.get('caption_paragraph'):
            del blocks[index - 1]
        context.setdefault('recipes', {})[slug] = plan
        selector = f'#furo-main-content .hb-reference-figure[data-reference-id="{slug}"] .hb-reference-live-label'
        share = round((clip[2] - clip[0]) / PRINT_COLUMN_PT * 100, 1)
        if share < 90:
            centred = '; margin-inline: auto' if slug.startswith('app-') else ''
            context['label_css'].append(
                f'  #furo-main-content .hb-reference-figure[data-reference-id="{slug}"] '
                f'{{ max-width: {share}%{centred}; }}')
        sizes = [label['size'] for label in labels]
        common = max(set(sizes), key=sizes.count)
        context['label_css'].append(f'  {selector} {{ font-size: {common}cqw; }}')
        for i, label in enumerate(labels):
            parts = [f'font-size: {label["size"]}cqw'] if label['size'] != common else []
            if label['align'] == 'right':
                parts += ['justify-content: flex-end', 'text-align: right']
            elif label['align'] == 'center':
                parts += ['justify-content: center', 'text-align: center']
            if parts:
                context['label_css'].append(f'  {selector}[data-source-line="{i}"] {{ {"; ".join(parts)}; }}')


def _label_inline(html: str) -> list[dict]:
    nodes: list[dict] = []
    for index, part in enumerate(html.split('<br/>')):
        if index:
            nodes.append(brk())
        bold = re.fullmatch(r'<strong>(.*)</strong>', part)
        nodes.append(strong(bold.group(1)) if bold else text(part))
    return nodes


# ---------------------------------------------------------- text structure

def block_text(block: dict) -> str:
    return leaves(block)


def find_block(blocks: list[dict], kind: str, starts: str) -> int:
    hits = [i for i, b in enumerate(blocks) if b.get('kind') == kind
            and block_text(b).startswith(''.join(starts.split()))]
    if len(hits) != 1:
        raise SystemExit(f'expected one {kind} starting {starts!r}, found {len(hits)}')
    return hits[0]


def as_heading(block: dict, level: int) -> dict:
    return {'kind': 'heading', 'level': level, 'children': deepcopy(block['children']),
            'schema_version': 'manual-flow/v2'}


# Printed hierarchy (p12-p13, p25-p26): bold "●" lead sentences are sub-headings, the wall types
# sit under them, and the App 4.1 / 4.2 titles sit under "4. ご確認".
HEADINGS = [
    ('installation', 'paragraph', 'スタンドに取り付けられた', 3),
    ('installation', 'paragraph', 'Jackery Wall-Mounted Bracket', 3),
    ('installation', 'heading', '木製の壁の場合', 4),
    ('installation', 'heading', 'コンクリート壁面の場合', 4),
    ('app-setup', 'heading', '4.1 Wi-Fi', 4),
    ('app-setup', 'heading', '4.2 Wi-Fi', 4),
]


def heading_levels(chapters: list[dict], context: dict) -> None:
    for page_id, kind, starts, level in HEADINGS:
        blocks = chapter(chapters, page_id)['blocks']
        index = find_block(blocks, kind, starts)
        before = deepcopy(blocks[index])
        blocks[index] = as_heading(blocks[index], level)
        same_copy(starts, before, blocks[index])
    # App 4.1 / 4.2 bodies print as bulleted items.
    blocks = chapter(chapters, 'app-setup')['blocks']
    for starts in ('Wi-FiとBluetoothはデバイスと連動', 'デバイスの電源を切った状態で、POWER'):
        index = find_block(blocks, 'paragraph', starts)
        before = deepcopy(blocks[index])
        blocks[index] = {'kind': 'list', 'ordered': False, 'schema_version': 'manual-flow/v2',
                         'children': [{'kind': 'list_item', 'children': deepcopy(before['children'])}]}
        same_copy(starts, before, blocks[index])
    # The "■" usage-precaution titles print as bold lines inside one framed box, not as headings.
    blocks = chapter(chapters, 'usage-precautions')['blocks']
    for index, block in enumerate(blocks):
        if block.get('kind') == 'heading' and block_text(block).startswith('■'):
            title = ''.join(c['text'] for c in block['children'] if c.get('kind') == 'text')
            blocks[index] = {'kind': 'paragraph', 'schema_version': 'manual-flow/v2', 'children': [strong(title)]}
            same_copy(title, block, blocks[index])


# Printed line starts inside run-on paragraphs: (page, paragraph start, [text that starts a printed line]).
PRINT_BREAKS = [
    ('usage-precautions', 'Jackery SlimPower H1は、定格出力800W', ['定格出力800Wは、一定', '800Wの出力を超えた場合は']),
    ('ups', 'これらの機器でご使用を希望', ['また、複数の高負荷機器', '※記載の手順に従わずに', 'UPS として使用している際は']),
    ('charging', 'コンセントからJackery SlimPower H1本体', ['コンセントの定格電流を超えると', '必ず壁面のコンセント']),
    ('maintenance', '防虫ネットは定期的に清掃', ['シリコンカバーを取り外して']),
]


def with_breaks(value: str, markers: list[str]) -> list[dict]:
    nodes: list[dict] = []
    rest = value
    for marker in markers:
        if rest.count(marker) != 1:
            raise SystemExit(f'print line start {marker!r} must occur exactly once')
        head, tail = rest.split(marker)
        nodes += [text(head.rstrip()), brk()]
        rest = marker + tail
    return nodes + [text(rest)]


def print_breaks(chapters: list[dict], context: dict) -> None:
    for page_id, starts, markers in PRINT_BREAKS:
        blocks = chapter(chapters, page_id)['blocks']
        index = find_block(blocks, 'paragraph', starts)
        (only,) = blocks[index]['children']
        before = deepcopy(blocks[index])
        blocks[index] = {**blocks[index], 'children': with_breaks(only['text'], markers)}
        same_copy(starts, before, blocks[index])


def app_note_items(chapters: list[dict], context: dict) -> None:
    """The bind note prints its two connection methods as bulleted items (p26)."""
    blocks = chapter(chapters, 'app-setup')['blocks']
    index = find_component(chapters, 'app-setup', 'ja/p26/notice-21')
    _, body = callout_parts(blocks[index])
    (only,) = body
    value = only['children'][0]['text']
    lead, items = value.split('：', 1)
    first, second = items.split('。', 1)
    blocks[index] = rebuild_callout(blocks[index], [paragraph(text(lead + '：')),
                                                    bullet_list([first + '。', second])])


def respec(block: dict, slots: dict) -> None:
    """Replace slot contents and re-validate the spec through the shared registry."""
    from tools.component_specs.model import ComponentSpec
    from tools.manual_ir.components import require_valid_component_spec

    for slot in block['component_spec']['slots']:
        if slot['role'] in slots:
            slot['content'] = slots[slot['role']]
    require_valid_component_spec(ComponentSpec.from_dict(block['component_spec']))


def html_breaks(value: str, pattern: str) -> str:
    """Insert print line breaks before each regex match after the first character."""
    return re.sub(pattern, lambda m: ('<br/>' if m.start() else '') + m.group(0), value)


def troubleshooting_steps(chapters: list[dict], context: dict) -> None:
    """Numbered measures and the FF temperature cases print one per line (p21)."""
    blocks = chapter(chapters, 'troubleshooting')['blocks']
    (index,) = [i for i, b in enumerate(blocks) if b.get('kind') == 'component'
                and b['component_spec']['component_id'] == 'HB-TABLE-TROUBLESHOOTING']
    slots = {s['role']: s['content'] for s in blocks[index]['component_spec']['slots']}
    rows = deepcopy(slots['rows'])
    for row in rows:
        value = row['measures_html']
        value = html_breaks(value, r'(?<!\d)\d\.\s?(?=\S)|低温環境下で')
        row['measures_html'] = value.replace('<br/>低温環境下で', '<br/><br/>低温環境下で')
        if ''.join(re.sub(r'<br/>', '', row['measures_html']).split()) != ''.join(row['measures_text'].split()):
            raise SystemExit(f"troubleshooting {row['code_text']}: copy changed")
    respec(blocks[index], {'rows': rows})


# LCD icon descriptions: printed status leads are bold and start a line (p9-p10).
LCD_LEADS = r'(点灯時：|消灯時：|オン[：:]|オフ[：:]|点滅[：:])'
CIRCLED = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫'


def lcd_rows(chapters: list[dict], context: dict) -> None:
    blocks = chapter(chapters, 'lcd-display')['blocks']
    (index,) = [i for i, b in enumerate(blocks) if b.get('kind') == 'component'
                and b['component_spec']['component_id'] == 'HB-TABLE-LCD-ICON']
    slots = {s['role']: s['content'] for s in blocks[index]['component_spec']['slots']}
    rows = deepcopy(slots['rows'])
    for row in rows:
        value = row['description_html'].replace('<br/>', '')
        value = re.sub(LCD_LEADS, lambda m: f'<strong>{m.group(1)}</strong>', value)
        value = re.sub(r'(?<!^)(<strong>)', r'<br/>\1', value)
        if re.sub(r'<[^>]+>', '', value) != re.sub(r'<[^>]+>', '', row['description_html']):
            raise SystemExit(f"LCD row {row['number_text']}: copy changed")
        row['description_html'] = value
        number = int(row['number_text'])
        row['number_html'] = row['number_text'] = CIRCLED[number - 1]  # the LCD map's printed numbers
    respec(blocks[index], {'rows': rows})


def warranty_layout(chapters: list[dict], context: dict) -> None:
    """Warranty items print one per line; ※ notes and sub-items keep the printed order (p23-p24)."""
    blocks = chapter(chapters, 'warranty')['blocks']
    for index, block in enumerate(blocks):
        if block.get('kind') != 'component' or block['component_spec']['component_id'] != 'HB-WARRANTY-SECTION':
            continue
        slots = {s['role']: s['content'] for s in block['component_spec']['slots']}
        new_blocks = []
        for item in slots['blocks']:
            if item['kind'] != 'paragraph':
                new_blocks.append(item)
                continue
            html = item['html']
            # numbered items, "・" items and the indented detail after a numbered title start lines
            html = re.sub(r'(?<=[^>])(?<![\d.])(\d\.\s?(?=[^\d\s]))', r'<br/>\1', html)
            # "・" starts an item only after an item end; inside a phrase it joins words (故障・損傷).
            html = re.sub(r'(?:(?<=こと)|(?<=。)|(?<=）)|(?<=製品)|(?<=場合))・', '<br/>・', html)
            html = re.sub(r'(について|地域)\s{3,}', r'\1<br/>', html)
            html = re.sub(r'(有償修理)(?=以下に該当)', r'\1<br/>', html)
            if re.sub(r'<[^>]+>|\s', '', html) != re.sub(r'<[^>]+>|\s', '', item['html']):
                raise SystemExit('warranty: copy changed')
            new_blocks.append({**item, 'html': html})
        respec(block, {'blocks': new_blocks})
    warranty_period_card(blocks)


def warranty_period_card(blocks: list[dict]) -> None:
    """The print boxes 保証期間 like every other section; the numeric badges are not printed."""
    from tools.component_specs.warranty import warranty_section_component_spec
    from tools.manual_ir.components import component_flow_node

    (years,) = [i for i, b in enumerate(blocks) if b.get('kind') == 'component'
                and b['component_spec']['component_id'] == 'HB-WARRANTY-YEARS']
    spec = blocks[years]['component_spec']
    slots = {s['role']: s['content'] for s in spec['slots']}
    note = blocks[years + 1]
    if note.get('kind') != 'paragraph' or not block_text(note).startswith('※'):
        raise SystemExit('expected the ※ purchase-channel note after the warranty periods')
    items = [{'kind': 'paragraph', 'html': period['body_html'], 'text': period['body_text']}
             for period in slots['periods']]
    note_text = ''.join(c['text'] for c in note['children'] if c.get('kind') == 'text')
    items.append({'kind': 'paragraph', 'html': f'<p>{note_text}</p>', 'text': note_text})
    for block in blocks:  # later sections move down one place
        if block.get('kind') == 'component' and block['component_spec']['component_id'] == 'HB-WARRANTY-SECTION':
            respec(block, {'section_index': {s['role']: s['content'] for s in block['component_spec']['slots']}
                           ['section_index'] + 1})
    card = component_flow_node(warranty_section_component_spec(
        title=slots['title'], section_index=1, blocks=items, source_ref=spec['source_ref'],
        language=spec['language']), root=True)
    heading = {'kind': 'heading', 'level': 3, 'children': [text(slots['title'])], 'schema_version': 'manual-flow/v2'}
    blocks[years:years + 2] = [heading, card]


def spec_group_level(chapters: list[dict], context: dict) -> None:
    """Chapters are the document's top level, as in the shared Web manuals.

    The shared specification renderer emits its group titles one level below a
    chapter (``##``); with chapters at ``##`` they became chapters of their own.
    Every flow heading moves up one level; the rendered chapter/section look is
    unchanged and the specification groups become sub-sections of 主な仕様.
    """
    for item in chapters:
        for block in item['blocks']:
            if block.get('kind') == 'heading':
                if block['level'] < 2:
                    raise SystemExit('unexpected top-level heading in the approved chapters')
                block['level'] -= 1


def lcd_mode_portrait(chapters: list[dict], context: dict) -> None:
    """The LCD screen prints a narrow device drawing beside a wide matrix: the shared portrait layout."""
    from tools.component_specs.model import ComponentSpec
    from tools.manual_ir.components import require_valid_component_spec

    blocks = chapter(chapters, 'operations')['blocks']
    (index,) = [i for i, b in enumerate(blocks) if b.get('kind') == 'component'
                and b['component_spec']['component_id'] == 'HB-TABLE-LCD-MODE']
    blocks[index]['component_spec']['metadata']['artwork_layout'] = 'portrait'
    require_valid_component_spec(ComponentSpec.from_dict(blocks[index]['component_spec']))


LAYOUT: list = [  # (name, function(chapters, context)) applied in order
    ('safety pictogram items: printed bold lead, then the explanation on its own line', safety_bold_leads),
    ('callout items printed one per line (・ / • / · markers kept)', marked_items),
    ('labelled figures: JP print crops with live labels at print position, size, weight and alignment',
     labelled_figures),
    ('printed heading hierarchy: lead sentences, wall types, App 4.1/4.2, usage ■ titles', heading_levels),
    ('printed line starts inside run-on paragraphs', print_breaks),
    ('App bind note: two bulleted connection methods', app_note_items),
    ('troubleshooting measures: one numbered step per line', troubleshooting_steps),
    ('LCD icon table: circled numbers, bold status leads on their own lines', lcd_rows),
    ('warranty sections: one item per line; 保証期間 printed as a section card', warranty_layout),
    ('LCD screen: shared portrait layout (narrow device drawing, wide matrix)', lcd_mode_portrait),
    ('chapters at the top heading level; specification groups become sub-sections of 主な仕様',
     spec_group_level),
]


def apply_layout(context: dict) -> list[str]:
    chapters = read(BASE / 'source/chapters.json')
    applied = []
    for name, change in LAYOUT:
        change(chapters, context)
        applied.append(name)
    write(PACKAGE / 'source/chapters.json', chapters)
    admission(chapters)
    return applied


def admission(chapters: list[dict]) -> None:
    """Recount the shared components the edition binds (the 保証期間 badges became a section card)."""
    from collections import Counter

    from tools.manual_ir.components import component_specs_in_flow

    data = read(BASE / 'source/admission.json')
    counts = Counter(spec.component_id for spec in component_specs_in_flow(
        [b for p in chapters for b in p['blocks']]))
    data['components'] = {key: counts[key] for key in data['components'] if counts[key]} | {
        key: value for key, value in counts.items() if key not in data['components']}
    data['scope'] = (data['scope'] + '; Web-layout edition 2026-11-25: print layout corrections against the '
                     'same PDF, copy unchanged except the declared differences')
    write(PACKAGE / 'source/admission.json', data)


# ------------------------------------------------------------------- art

# Crop-only art whose crop took in a print card border: slug -> corrected crop (pt).
RECROPS = {'inbox-cable': [108, 309, 176, 382]}
PRINT_COLUMN_PT = 313.0  # printed text column width (pt) that full-width panels span

REASON = ('Reused or approved art did not carry the JP print composition, so live JP labels fell on the '
          'wrong objects (operator screenshots 2026-11-25); source-local textless crop of the same JP panel '
          'with every printed line kept as a live label at its print position.')


def render_figures(context: dict) -> None:
    """Re-render the labelled figures from the JP print with the shared asset pipeline."""
    import tempfile

    from tools.asset_pipeline.extract import extract_artifacts
    from tools.asset_pipeline.recipe import load_recipe

    recipe_path = PACKAGE / 'source/asset-recipe.json'
    recipe = read(BASE / 'source/asset-recipe.json')
    by_output = {asset['outputs'][0]['path']: asset for asset in recipe['assets']}
    plans = context['recipes']
    for slug, plan in plans.items():
        transforms = [{'op': 'crop', 'bbox_pt': plan['clip']}]
        transforms += [{'op': 'whiteout', 'bbox_pt': box} for box in plan.get('whiteout', [])]
        if plan.get('redact'):
            transforms.append({'op': 'redact_text_region', 'bbox_pt': plan['redact'], 'graphics': 'preserve',
                               'images': 'preserve', 'fill': None})
        else:
            transforms.append({'op': 'redact_text', 'graphics': 'preserve', 'images': 'preserve', 'fill': None})
        entry = {'asset_key': f'web/je1000e-wh/jp/ja/{slug}', 'page': plan['page'], 'build_eligible': False,
                 'scope': {'models': ['JE-1000E-WH'], 'regions': ['JP'], 'locales': ['ja']},
                 'text_policy': 'localized-full-page' if slug.startswith('app-') else 'fixed-product-markings',
                 'visual_review_required': True, 'transforms': transforms,
                 'outputs': [{'format': 'png', 'path': f'artwork/{slug}.png', 'scale': 3}],
                 'gate': {'status': 'quarantine',
                          'reasons': ['Candidate source-local extraction only; no registry promotion authorized.']},
                 'risk_tags': ['app-ui'] if slug.startswith('app-') else []}
        by_output[f'artwork/{slug}.png'] = entry
    for slug, clip in RECROPS.items():
        asset = by_output[f'artwork/{slug}.png']
        (crop,) = [t for t in asset['transforms'] if t['op'] == 'crop']
        crop['bbox_pt'] = clip
        asset['outputs'][0].pop('expected_sha256', None)
    recipe['assets'] = sorted(by_output.values(), key=lambda a: a['outputs'][0]['path'])
    write(recipe_path, recipe)
    with tempfile.TemporaryDirectory() as tmp:
        extract_artifacts(context['pdf_path'], load_recipe(recipe_path), Path(tmp))
        for asset in recipe['assets']:
            output = asset['outputs'][0]
            rendered = Path(tmp) / output['path']
            target = PACKAGE / output['path']
            slug = Path(output['path']).stem
            if slug in plans or slug in RECROPS:
                shutil.copyfile(rendered, target)
                output['expected_sha256'] = sha256(target)
            elif sha256(rendered) != output.get('expected_sha256'):
                raise SystemExit(f'recipe output drifted from the approved art: {output["path"]}')
    write(recipe_path, recipe)
    provenance = read(BASE / 'asset_provenance.json')
    for slug, plan in plans.items():
        asset = by_output[f'artwork/{slug}.png']
        provenance[slug] = {
            'path': f'artwork/{slug}.png', 'sha256': sha256(PACKAGE / f'artwork/{slug}.png'),
            'decision': 'source-local-extraction', 'source_pdf_sha256': PDF_SHA256,
            'physical_page': plan['page'], 'clip_points': plan['clip'], 'transforms': asset['transforms'],
            'identity_review': REASON,
            'background_policy': 'preserve the complete native panel; text-only removal with no fill',
            'previous': {k: v for k, v in read(BASE / 'asset_provenance.json').get(slug, {}).items()
                         if k in {'path', 'sha256', 'decision', 'source_path'}},
        }
    for slug, clip in RECROPS.items():
        provenance[slug] = {**provenance[slug], 'sha256': sha256(PACKAGE / f'artwork/{slug}.png'),
                            'clip_points': clip, 'transforms': by_output[f'artwork/{slug}.png']['transforms'],
                            'recrop_reason': 'the previous crop took in the printed card border as a stray line'}
    write(PACKAGE / 'asset_provenance.json', provenance)
    chapters = read(PACKAGE / 'source/chapters.json')
    for slug in plans:
        blocks, index = figure_block(chapters, slug)
        layout = blocks[index]['component_spec']['metadata']['base_art_layout']
        layout['art_sha256'] = provenance[slug]['sha256']
        blocks[index]['component_spec']['metadata']['source_fragment_sha256'] = fragment_sha256(blocks[index])
    write(PACKAGE / 'source/chapters.json', chapters)


def fragment_sha256(block: dict) -> str:
    """The shared renderer's own source-fragment hash for a rebuilt reference figure."""
    from tools.component_specs.model import ComponentSpec
    from tools.web import composite_presentation
    from tools.web.embedded_components import _carrier_html
    from tools.web.reference_figure_component import render_reference_figure_component

    captured: dict[str, str] = {}
    original = composite_presentation.WebCompositeContext._append

    def record(self, **fields):
        captured['sha256'] = fields['source_fragment_sha256']
        return original(self, **fields)

    composite_presentation.WebCompositeContext._append = record
    try:
        spec = ComponentSpec.from_dict(block['component_spec'])
        try:
            render_reference_figure_component(spec, _carrier_html(block), source_path=PACKAGE / 'source',
                                              model='JE-1000E-WH', region='JP', language='ja')
        except ValueError as error:
            if 'source-fragment hash disagrees' not in str(error):
                raise
    finally:
        composite_presentation.WebCompositeContext._append = original
    return captured['sha256']


# ------------------------------------------------------------ stylesheet

GENERATED = '/* Generated by derive_web_layout.py: live labels keep the print type size, weight and alignment. */\n'


def stylesheet(context: dict, authored: str) -> None:
    css = read_text(BASE / 'source/presentation.css').rstrip('\n') + '\n\n' + authored.strip('\n') + '\n\n'
    css += GENERATED + '@media (min-width: 761px) {\n' + '\n'.join(context['label_css']) + '\n}\n'
    if '</style' in css.lower() or '\n\n\n' in css:
        raise SystemExit('stylesheet would break the MyST carrier')
    from tools.web.prepared_style_audit import paint_properties

    added = css[len(read_text(BASE / 'source/presentation.css')):]
    if paint_properties(added):
        raise SystemExit(f'package CSS may only set geometry, not paint: {paint_properties(added)}')
    (PACKAGE / 'source/presentation.css').write_text(css, encoding='utf-8')


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


# Hand-written geometry for this page (no paint: colours, borders and fills stay shared).
AUTHORED_CSS = '''
/* Web-layout edition (2026-11-25): geometry only. Japanese headings keep their printed case. */
#furo-main-content h1, #furo-main-content h2:not(.hb-spec-section), #furo-main-content h3:not(.hb-spec-section),
#furo-main-content .hb-subbar { text-transform: none; }
/* The back-cover QR code prints small at the bottom right of the last page. */
#furo-main-content .hb-reference-figure[data-reference-id="back-qr"] { max-width: 8rem; margin-inline-start: auto; }
'''


# -------------------------------------------------------------- manifest

def manifest(applied: list[str]) -> None:
    data = read(BASE / 'source_manifest.json')
    data['target']['technical_version'] = PACKAGE.name
    data['source_authority'] = (
        'Operator-designated Japanese PDF and the approved MA-312 Web edition '
        'git-20261016-efb663e3-solar-voc; Web-layout corrections against the same PDF on operator '
        'instruction 2026-11-25 (「这个卫士1代 有些版面 要调整的 你调整一下」). The printed source keeps its wording.')
    data['publication_eligible'] = STATUS == APPROVED
    data['publication_status'] = STATUS
    data['revision_of'] = f'manual_sources/JE-1000E-WH/JP/ja/{BASE.name}'
    data['derived_from'] = {
        'package': BASE.name, 'authorization': 'MA-312',
        'manifest_sha256': sha256(BASE / 'source_manifest.json'),
    }
    data['layout_changes'] = applied
    data['pending_source_review'] = [] if data['publication_eligible'] else [
        'operator review of the Web-layout corrections before Git-only release']
    data.pop('inputs', None)
    write(PACKAGE / 'source_manifest.json', data)
    files = sorted(p for p in PACKAGE.rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts and p.name != 'source_manifest.json')
    data['inputs'] = [{'path': p.relative_to(PACKAGE).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
                      for p in files]
    write(PACKAGE / 'source_manifest.json', data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--pdf', type=Path, required=True)
    args = parser.parse_args()
    if sha256(args.pdf) != PDF_SHA256:
        raise SystemExit('the --pdf file is not the designated original')
    import pymupdf

    copy_base()
    context = {'pdf_path': args.pdf.resolve()}
    with pymupdf.open(args.pdf) as pdf:
        context['pdf'] = pdf
        applied = apply_layout(context)
    render_figures(context)
    stylesheet(context, AUTHORED_CSS)
    manifest(applied)
    print(json.dumps({'package': PACKAGE.name, 'changes': applied,
                      'inputs': len(read(PACKAGE / 'source_manifest.json')['inputs'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
