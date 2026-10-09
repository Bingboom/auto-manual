"""Derive the JBP-1000B-WH / JP / ja Web-layout edition from the approved native package.

Run from the repository root with the pinned dependencies (requirements.lock,
PyMuPDF 1.28.0 / MuPDF 1.29.0):

    python manual_sources/JBP-1000B-WH/JP/ja/git-20261009-3aa6c003-web-layout/derive_web_layout.py

The approved package ``../git-20261008-3aa6c003-native`` stays immutable. This
script rewrites only this package's copied inputs, ``source/`` data,
``source/presentation.css`` and ``source_manifest.json``; a second run leaves the
tree unchanged. Hand-written ``README.md`` and ``source/differences.md`` are not
touched. Visible Japanese copy is never edited: each rich-text change is checked
against the approved wording, and every ``*_text`` field keeps its approved value.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

PACKAGE = Path(__file__).resolve().parent
NATIVE = PACKAGE.parent / 'git-20261008-3aa6c003-native'
REPO = next(parent for parent in PACKAGE.parents if (parent / 'build.py').is_file())
sys.path.insert(0, str(REPO))

import pymupdf  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

from tools.asset_pipeline.extract import extract_artifacts  # noqa: E402
from tools.asset_pipeline.recipe import load_recipe  # noqa: E402
from tools.web.frozen_pdf_reference import labeled_artwork_node  # noqa: E402

STATUS = 'review-candidate-no-release-authorization'
# Steps the PDF prints side by side become one row figure, as on the page.
PAIRS = {
    'wood-3-4': ('wood-3', 'wood-4'),
    'concrete-4-5': ('concrete-4', 'concrete-5'),
    'concrete-6-7': ('concrete-6', 'concrete-7'),
    'concrete-8-9': ('concrete-8', 'concrete-9'),
}
COVER = 'cover-unit'  # the printed cover is not part of the Web edition
# Captions whose printed '*' recommendation note is a separate line.
NOTE_SPLITS = {'wood-5': 0, 'concrete-4': 0}
# Inputs copied byte-for-byte from the approved package.
UNCHANGED = ['rebuild.py', 'source/discovery.md', 'source/native_icon_recipe.json',
             'source/pdf_blocks.json', 'source/reuse.json', 'source/symbol_release_admission.json']
# Live labels that keep their shared/source sizing instead of print-relative type.
OWN_LABEL_SIZE = {'lcd-map', 'car-charge', 'power'}
GENERATED = '/* Live labels keep the print type size relative to each panel (generated from figures.json). */\n'


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def union(boxes):
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


def source_pdf(root: Path) -> Path:
    (pdf,) = root.glob('*.pdf')
    return pdf


# ---------------------------------------------------------------- inputs

def copy_unchanged() -> None:
    for relative in UNCHANGED:
        shutil.copyfile(NATIVE / relative, PACKAGE / relative)
    shutil.copyfile(source_pdf(NATIVE), PACKAGE / source_pdf(NATIVE).name)
    (PACKAGE / 'source/assets').mkdir(parents=True, exist_ok=True)
    obsolete = {COVER, *(slug for pair in PAIRS.values() for slug in pair)}
    for art in (NATIVE / 'source/assets').iterdir():
        if art.stem not in obsolete:
            shutil.copyfile(art, PACKAGE / 'source/assets' / art.name)
    for art in (PACKAGE / 'source/assets').iterdir():
        if art.stem in obsolete:
            art.unlink()


# --------------------------------------------------------------- figures

def label_rect(bbox, clip, align='left'):
    """Native package rule: 3% wrap allowance and a 12% x 5% minimum box."""
    cw, ch = clip[2] - clip[0], clip[3] - clip[1]
    x = (bbox[0] - clip[0]) / cw * 100
    y = (bbox[1] - clip[1]) / ch * 100
    w = (bbox[2] - bbox[0]) / cw * 100
    h = (bbox[3] - bbox[1]) / ch * 100
    grown = max(w + 3, 12)
    if align == 'right':  # right-aligned print callouts keep their right edge
        x = max(0.0, x + w - grown)
    return [max(0.0, x), max(0.0, y), min(grown, 100 - x), min(max(h, 5), 100 - y)]


def relayout(entry, align='left') -> None:
    entry['base_art_layout']['labels'] = [
        {'line': index, 'rect': label_rect(caption['bbox'], entry['clip_points'], align)}
        for index, caption in enumerate(entry['live_captions'])
    ]


def flat(value: str) -> str:
    return ''.join(value.split())


def split_note(entry, index, pdf_blocks) -> None:
    """Split a step caption at its printed '* 455 mm' note line."""
    caption = entry['live_captions'][index]
    star = caption['text'].index('*')
    step_text, note_text = caption['text'][:star].rstrip(), caption['text'][star:]
    box = caption['bbox']
    blocks = next(p['blocks'] for p in pdf_blocks if p['physical_page'] == entry['physical_page'])
    inside = [b for b in blocks if b['bbox'][0] >= box[0] - 1 and b['bbox'][2] <= box[2] + 1
              and b['bbox'][1] >= box[1] - 1 and b['bbox'][3] <= box[3] + 1 and flat(b['text'])]
    note = [b for b in inside if flat(b['text']).startswith('*')
            or (flat(b['text']) in flat(note_text) and flat(b['text']) not in flat(step_text))]
    step = [b for b in inside if b not in note]
    if flat(''.join(b['text'] for b in step)) != flat(step_text) or flat(''.join(b['text'] for b in note)) != flat(note_text):
        raise SystemExit(f"{entry['slug']}: printed step/note lines disagree with the caption")
    entry['live_captions'][index:index + 1] = [
        dict(caption, text=step_text, bbox=union([b['bbox'] for b in step])),
        dict(caption, text=note_text, bbox=union([b['bbox'] for b in note])),
    ]


def split_overview(entry, page) -> None:
    """The DC port callout prints a bold name and two 5 pt rating lines."""
    spans = [s for b in page.get_text('dict')['blocks'] for line in b.get('lines', [])
             for s in line['spans'] if s['text'].strip()]

    def middle(span):
        return (span['bbox'][1] + span['bbox'][3]) / 2

    first = entry['live_captions'][0]
    title = next(s for s in spans if s['text'] == 'DC 拡張ポート')
    rows = [('DC 拡張ポート', list(title['bbox']), title['size'])]
    for center in sorted(middle(s) for s in spans if s['size'] < 6 and s['text'].startswith('DC')
                         and s['bbox'][0] > 250 and s['bbox'][1] < first['bbox'][3]):
        parts = sorted((s for s in spans if abs(middle(s) - center) < 1.5 and 250 <= s['bbox'][0] <= 310),
                       key=lambda s: s['bbox'][0])
        rows.append((''.join(s['text'] for s in parts), union([s['bbox'] for s in parts]), parts[0]['size']))
    if flat(''.join(r[0] for r in rows)) != flat(first['text']):
        raise SystemExit('overview callout lines disagree with the caption')
    entry['live_captions'][0:1] = [dict(first, text=t, bbox=list(b), font_size=round(z, 2)) for t, b, z in rows]


def figures_and_recipe() -> None:
    figures = read(NATIVE / 'source/figures.json')
    recipe = read(NATIVE / 'source/asset_recipe.json')
    pdf_blocks = read(NATIVE / 'source/pdf_blocks.json')
    by_slug = {entry['slug']: entry for entry in figures}
    recipes = {asset['asset_key'].rsplit('/', 1)[-1]: asset for asset in recipe['assets']}
    for slug, index in NOTE_SPLITS.items():
        split_note(by_slug[slug], index, pdf_blocks)
        relayout(by_slug[slug])
    with pymupdf.open(source_pdf(NATIVE)) as pdf:
        split_overview(by_slug['overview'], pdf[by_slug['overview']['physical_page'] - 1])
    relayout(by_slug['overview'], align='right')

    out_figures, out_assets = [], []
    for entry in figures:
        slug = entry['slug']
        merged = next((m for m, pair in PAIRS.items() if slug in pair), None)
        if slug == COVER or (merged and slug != PAIRS[merged][0]):
            continue
        if merged is None:
            out_figures.append(entry)
            out_assets.append(recipes[slug])
            continue
        left, right = (by_slug[s] for s in PAIRS[merged])
        row = {
            'slug': merged,
            'physical_page': left['physical_page'],
            'clip_points': union([left['clip_points'], right['clip_points']]),
            'live_captions': deepcopy(left['live_captions']) + deepcopy(right['live_captions']),
            'sha256': None,
            'base_art_layout': deepcopy(left['base_art_layout']),
        }
        relayout(row)
        out_figures.append(row)
        transforms = recipes[left['slug']]['transforms'] + recipes[right['slug']]['transforms']
        if any(t['op'] not in {'crop', 'redact_text_region'} for t in transforms):
            raise SystemExit(f'{merged}: unexpected recipe transform')
        asset = deepcopy(recipes[left['slug']])
        asset['asset_key'] = asset['asset_key'].rsplit('/', 1)[0] + '/' + merged
        asset['transforms'] = [{'op': 'crop', 'bbox_pt': row['clip_points']}] + [
            t for t in transforms if t['op'] == 'redact_text_region']
        asset['outputs'] = [{'format': 'png', 'path': f'assets/{merged}.png', 'scale': 3}]
        out_assets.append(asset)
    recipe['assets'] = out_assets
    write(PACKAGE / 'source/figures.json', out_figures)
    write(PACKAGE / 'source/asset_recipe.json', recipe)


def render_assets() -> None:
    """Render every recipe output with the shared asset pipeline; install the new rows."""
    assets = PACKAGE / 'source/assets'
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'render'
        extract_artifacts(source_pdf(PACKAGE), load_recipe(PACKAGE / 'source/asset_recipe.json'), out)
        for path in (out / 'assets').iterdir():
            target = assets / path.name
            if path.stem in PAIRS:
                shutil.copyfile(path, target)
            elif target.read_bytes() != path.read_bytes():
                raise SystemExit(f'recipe output drifted from the approved art: {path.name}')
    figures = read(PACKAGE / 'source/figures.json')
    for entry in figures:
        (art,) = assets.glob(f"{entry['slug']}.*")
        entry['sha256'] = entry['base_art_layout']['art_sha256'] = sha256(art)
    write(PACKAGE / 'source/figures.json', figures)


# -------------------------------------------------------------- document

def text(value):
    return {'kind': 'text', 'text': value}


def strong(children):
    return {'kind': 'strong', 'children': children}


def with_class(node, *names):
    node['presentation'] = {'html': {'attributes': {'class': list(names)}}}
    return node


def page(doc, page_id):
    return next(p for p in doc['pages'] if p['page_id'] == page_id)


def slot(spec, role):
    return next(s for s in spec['slots'] if s['role'] == role)


def components(doc, component_id):
    for chapter in doc['pages']:
        for node in chapter['nodes']:
            spec = node.get('component_spec')
            if spec and spec['component_id'] == component_id:
                yield chapter, node, spec


def reference_node(figure):
    return labeled_artwork_node(figure, f"assets/{figure['slug']}.png", 'ja')


def structure(doc, policy, figures) -> None:
    doc['pages'] = [p for p in doc['pages'] if p['page_id'] != 'preface']
    for chapter in doc['pages']:  # chapters H1, sub-sections H2 (print TOC, JE-1000F JP Web)
        for node in chapter['nodes']:
            if node['kind'] == 'heading':
                node['level'] -= 1
    safety = page(doc, 'safety')['nodes'][1]
    safety['children'] = [strong(safety['children'])]
    for node in page(doc, 'symbols')['nodes']:  # pictogram bands belong to 使用上のご注意
        if node['kind'] == 'heading':
            node['level'] = 2
            node.setdefault('anchor', 'symbols-legend')
    stand = page(doc, 'stand')['nodes'][1]
    stand['children'] = [strong(stand['children'])]
    wood = page(doc, 'wall_wood')['nodes']
    if [n['kind'] for n in wood[:2]] != ['heading', 'paragraph']:
        raise SystemExit('wall_wood opening changed')
    wood[0]['level'] = 2  # the bracket lead opens the wall topic inside 縦置
    wood[1]['children'] = [strong(wood[1]['children'])]
    wood[0:2] = [wood[1], wood[0]]
    page(doc, 'wall_concrete')['nodes'][0]['level'] = 2

    for chapter in doc['pages']:
        nodes = chapter['nodes']
        for index in range(len(nodes) - 1, -1, -1):
            spec = nodes[index].get('component_spec') or {}
            if spec.get('component_id') != 'HB-SPECIAL-REFERENCE-FIGURE':
                continue
            identity = slot(spec, 'reference_id')['content']
            merged = next((m for m, pair in PAIRS.items() if identity in pair), None)
            if merged and identity == PAIRS[merged][1]:
                del nodes[index]
            elif merged:
                nodes[index] = reference_node(figures[merged])
            elif identity in NOTE_SPLITS or identity == 'overview':
                nodes[index] = reference_node(figures[identity])

    contact = page(doc, 'contact')['nodes']
    if contact[0]['kind'] != 'heading':
        raise SystemExit('contact opening changed')
    del contact[0]  # contact lines close the warranty card, as printed
    for node in contact:
        label, _, value = node['children'][0]['text'].partition(': ')
        node['children'] = [strong([text(label + ':')]), text(' ' + value)]
        with_class(node, 'jbp-contact-line')

    policy['expected_pages'].remove('preface')
    policy['expected_slots'].pop('preface')
    policy['chapters'] = [c for c in policy['chapters'] if c['id'] != 'preface']
    counts = {'wall_wood': 7, 'wall_concrete': 6}  # one figure per printed row
    for chapter in policy['chapters']:
        for requirement in chapter['requirements']:
            if chapter['id'] in counts and requirement['id'] == 'HB-SPECIAL-REFERENCE-FIGURE':
                requirement['minimum'] = counts[chapter['id']]


def same_copy(old_html: str, new_html: str) -> str:
    def words(value):
        return flat(BeautifulSoup(value, 'html.parser').get_text(''))
    if words(old_html) != words(new_html):
        raise SystemExit(f'approved copy changed:\n{old_html}\n{new_html}')
    return new_html


def warranty_blocks(title, blocks):
    def block(html, value):
        return {'kind': 'paragraph', 'text': value, 'html': html}

    out = []
    for item in blocks:
        value, html = item['text'], item['html']
        if value[:1] in {'※', '*'}:
            out.append(dict(item, html=same_copy(html, html.replace('<p>', '<p class="jbp-warranty-note">', 1))))
        elif title == '保証の適用範囲' and value[:2] in {'1.', '2.'}:
            head = '1. 購入チャネルについて' if value.startswith('1.') else '2. 保証提供地域'
            out += [block(f'<p>{head}</p>', head),
                    block(f'<p class="jbp-warranty-detail">{value[len(head):]}</p>', value[len(head):])]
        elif title == '保証内容' and value.startswith('3. 有償修理'):
            head, rest = '3. 有償修理', value[len('3. 有償修理'):]
            out += [block(f'<p><strong>{head}</strong></p>', head), block(f'<p>{rest}</p>', rest)]
        elif title == '保証内容' and value[:2] in {'1.', '2.'}:
            head, tail = value.split('（', 1)
            out.append(dict(item, html=same_copy(html, f'<p><strong>{head}</strong>（{tail}</p>')))
        elif title == '免責事項' and value.startswith('3. '):
            lines = ['3. 保証内容は、予告なく変更される場合がございます。あらかじめご了承ください。',
                     'Jackery 製品を安心してご使用いただくために、本保証書の内容をご確認のうえ、ご活用くださいますようお願いいたします。',
                     'ご不明点がございましたら、Jackery カスタマーサービスまでお問い合わせください。']
            if ''.join(lines) != value:
                raise SystemExit('免責事項 3 changed')
            out += [block(f'<p>{line}</p>', line) for line in lines]
        else:
            out.append(item)
    if flat(''.join(b['text'] for b in out)) != flat(''.join(b['text'] for b in blocks)):
        raise SystemExit(f'{title}: warranty copy changed')
    return out


def rich_text(doc) -> None:
    _, _, signal = next(components(doc, 'HB-TABLE-SYMBOL-SIGNAL'))
    for row in slot(signal, 'rows')['content']:
        row['show_icon'] = False  # the print signal words carry no pictogram
    _, _, icons = next(components(doc, 'HB-TABLE-SYMBOL-ICON'))
    breaks = {
        '充電式電池のリサイクルについて': ('<strong>充電式電池のリサイクルについて</strong><br/>', ['ています。', 'ください。']),
        'このシンボルは、': ('', ['示しています。', '役立ちます。']),
    }
    for panel in slot(icons, 'panels')['content']:
        for row in panel:
            for prefix, (head, ends) in breaks.items():
                if row['meaning_text'].startswith(prefix):
                    body = row['meaning_text'][len(prefix):] if head else row['meaning_text']
                    for end in ends:
                        body = body.replace(end, end + '<br/>', 1)
                    row['meaning_html'] = same_copy(row['meaning_html'], head + body)

    notes, disclaimer = page(doc, 'in_the_box')['nodes'][2:4]
    first, second = notes['children'][0]['text'].split('※  本拡張')
    page(doc, 'in_the_box')['nodes'][2] = with_class(
        {'kind': 'group', 'role': 'container', 'children': [
            {'kind': 'paragraph', 'children': [text(first.strip())]},
            {'kind': 'paragraph', 'children': [text('※  本拡張' + second)]},
        ]}, 'jbp-inbox-notes')
    disclaimer['children'] = [strong(disclaimer['children'])]
    with_class(disclaimer, 'jbp-inbox-disclaimer')

    _, _, lcd = next(components(doc, 'HB-TABLE-LCD-ICON'))
    lcd['metadata']['description_cell_layout'] = 'span-adjacent-equal'  # print merges ①/③ copy
    for row in slot(lcd, 'rows')['content']:
        row['number_html'] = f"<p>{row['number_text']}</p>"  # shared CSS circles the number
        if '\n' in row['description_html']:
            lines = []
            for line in row['description_html'].split('\n'):
                mark = next((m for m in ('オン:', 'オフ:', 'オン：', 'オフ：') if line.startswith(m)), '')
                lines.append(f'<strong>{mark}</strong>{line[len(mark):]}' if mark else line)
            row['description_html'] = same_copy(row['description_html'], '<br/>'.join(lines))

    _, _, troubleshooting = next(components(doc, 'HB-TABLE-TROUBLESHOOTING'))
    for row in slot(troubleshooting, 'rows')['content']:
        html = row['measures_html']
        for head in ('高温環境下で', '低温環境下で'):
            html = html.replace(f'<p>{head}</p>', f'<p><strong>{head}</strong></p>')
        row['measures_html'] = same_copy(row['measures_html'], html)

    _, _, lead = next(components(doc, 'HB-WARRANTY-LEAD'))
    old = slot(lead, 'lead')['content']
    slot(lead, 'lead')['content'] = same_copy(old, old.replace('ございます。本保証書', 'ございます。<br/>本保証書'))
    for _, _, section in components(doc, 'HB-WARRANTY-SECTION'):
        blocks = slot(section, 'blocks')
        blocks['content'] = warranty_blocks(slot(section, 'title')['content'], blocks['content'])


def document() -> None:
    doc = read(NATIVE / 'source/document.json')
    policy = read(NATIVE / 'source/admission.json')
    figures = {f['slug']: f for f in read(PACKAGE / 'source/figures.json')}
    structure(doc, policy, figures)
    rich_text(doc)
    write(PACKAGE / 'source/document.json', doc)
    write(PACKAGE / 'source/admission.json', policy)


# ------------------------------------------------------------ stylesheet

def leading(page, bbox, size):
    """Printed line pitch / font size of a multi-line caption, else None."""
    centers = sorted((s['bbox'][1] + s['bbox'][3]) / 2
                     for b in page.get_text('dict')['blocks'] for line in b.get('lines', [])
                     for s in line['spans']
                     if s['text'].strip() and s['bbox'][0] >= bbox[0] - 1 and s['bbox'][2] <= bbox[2] + 1
                     and s['bbox'][1] >= bbox[1] - 1 and s['bbox'][3] <= bbox[3] + 1)
    lines = []
    for center in centers:  # mixed fonts on one printed line differ slightly in box height
        if not lines or center - lines[-1] > size * 0.6:
            lines.append(center)
    return round((lines[-1] - lines[0]) / (len(lines) - 1) / size, 2) if len(lines) > 1 else None


def label_type_rules() -> str:
    rules = []
    with pymupdf.open(source_pdf(PACKAGE)) as pdf:
        for entry in read(PACKAGE / 'source/figures.json'):
            if entry['slug'] in OWN_LABEL_SIZE or not entry['live_captions']:
                continue
            width = entry['clip_points'][2] - entry['clip_points'][0]
            sizes = [round(c['font_size'] / width * 100, 3) for c in entry['live_captions']]
            common = Counter(sizes).most_common(1)[0][0]
            selector = (f'#furo-main-content .hb-reference-figure[data-reference-id="{entry["slug"]}"] '
                        '.hb-reference-live-label')
            rules.append(f'  {selector} {{ font-size: {common}cqw; }}')
            for index, (caption, size) in enumerate(zip(entry['live_captions'], sizes, strict=True)):
                parts = [f'font-size: {size}cqw'] if size != common else []
                ratio = leading(pdf[entry['physical_page'] - 1], caption['bbox'], caption['font_size'])
                if ratio:
                    parts.append(f'line-height: {ratio}')
                if parts:
                    rules.append(f'  {selector}[data-source-line="{index}"] {{ {"; ".join(parts)}; }}')
    return GENERATED + '@media (min-width: 761px) {\n' + '\n'.join(rules) + '\n}\n'


def stylesheet() -> None:
    """Keep the hand-written rules of source/presentation.css; regenerate the label type tail."""
    path = PACKAGE / 'source/presentation.css'
    authored = path.read_text(encoding='utf-8').split(GENERATED)[0].rstrip('\n')
    css = authored + '\n\n' + label_type_rules()
    if '</style' in css.lower() or '\n\n\n' in css:
        raise SystemExit('stylesheet would break the MyST carrier')
    path.write_text(css, encoding='utf-8')


# -------------------------------------------------------------- manifest

def manifest() -> None:
    data = read(NATIVE / 'source_manifest.json')
    data['target']['technical_version'] = PACKAGE.name
    data['publication_status'] = STATUS
    data['source_authority'] = (
        'Supplied original Japanese PDF visible content, physical pages 3–19. Web-layout candidate derived from '
        'the operator-approved native package git-20261008-3aa6c003-native (MA-275) on operator instruction '
        '2026-10-09 (「全部修，一次做完」「封面和目录 不用体现在web版面上」「你参考 资料库里 现有的je-1000f的日语网页说明书」); '
        'awaiting operator acceptance before any release.'
    )
    data['normalizations'] = [n for n in data['normalizations'] if not n.startswith('Web layout:')] + [
        'Web layout: printed cover (physical 1) and print TOC (physical 2) are not part of the Web edition.',
        'Web layout: chapter/sub-section hierarchy follows the print TOC and the reviewed JE-1000F JP Web manual.',
        'Web layout: steps printed side by side (wood 3–4, concrete 4–5, 6–7, 8–9) are one row figure each.',
    ]
    files = sorted([PACKAGE / 'rebuild.py', *(p for p in (PACKAGE / 'source').rglob('*') if p.is_file())],
                   key=lambda p: str(p.relative_to(PACKAGE)))
    data['inputs'] = [{'path': str(p.relative_to(PACKAGE)), 'size': p.stat().st_size, 'sha256': sha256(p)}
                      for p in files]
    write(PACKAGE / 'source_manifest.json', data)


def main() -> None:
    copy_unchanged()
    figures_and_recipe()
    render_assets()
    document()
    stylesheet()
    manifest()
    print(json.dumps({'package': PACKAGE.name, 'inputs': len(read(PACKAGE / 'source_manifest.json')['inputs'])}))


if __name__ == '__main__':
    main()
