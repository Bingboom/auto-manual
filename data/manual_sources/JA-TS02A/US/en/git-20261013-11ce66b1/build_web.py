#!/usr/bin/env python3
"""Replay this frozen English PDF intake through the shared MyST/Web scaffold."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import unicodedata

from tools.markdown_bundle import _write_myst_sphinx_scaffold

HERE = Path(__file__).resolve().parent
MAIN_HEADINGS = {
    'SAFETY INSTRUCTIONS', 'SPECIFICATIONS', 'PACKAGE LIST', 'WHAT YOU NEED',
    'PRODUCT OVERVIEW', 'PRE-INSTALLATION', 'INSTALLATION GUIDE',
    'INTERNET AND INITIALIZATION SETUP', 'JACKERY APP QUICK START GUIDE', 'WARRANTY',
}
SUB_HEADINGS = {
    'Disclaimer', 'Warning', 'Caution', 'FCC Statement', 'IC Warning',
    'IC RF Statement:', 'Meaning of symbols', 'Optionals', 'Dimensions',
    'With Deadfront Cover Installed', 'With Deadfront Cover Removed',
    'IoT Button with Indicator', 'Emergency Stop Button', 'LED Indicators',
    'Normal Backup Mode', 'UPS Mode', 'System Overview', 'Installation Location',
    'Surface Mounting', 'Locating STS Cable Entry', 'Electrical Connections',
    'Connecting the Grid Conductors', 'Connecting the Home Load Conductors',
    'Conductor Tightening Torque', 'Installing an Emergency Stop Button (Optional)',
    'Installing the Deadfront Cover', 'Connecting with Power Station', 'Energizing',
    'Locking the Panel', 'RECOMMENDED BREAKERS', 'To download the App and log in',
    'To add device', 'Voltage configuration', 'Edit circuit name', 'Dashboard',
    'Circuits', 'Working Modes', 'Set backup reserve', 'Automatic charging mode',
    'Self-powered mode', 'Charging-discharging plan', 'Backup-only mode',
    'Backup priority', 'Circuit priorities', 'UPS mode', 'Limited Warranty',
    'Warranty Period', 'Repair or replacement', 'Limited to Original Consumer Buyer',
    'Exclusions', 'Interpretation Rights',
}
APP_GROUPS = {20: [(68, 268)], 21: [(50, 266)], 22: [(49, 261), (296, 503)], 23: [(50, 257)]}


def read_json(name: str):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs() -> dict:
    manifest = read_json('source_manifest.json')
    for entry in manifest['inputs']:
        path = (HERE / entry['path']).resolve()
        if not path.is_relative_to(HERE) or not path.is_file():
            raise ValueError(f"missing or escaping frozen input: {entry['path']}")
        if path.stat().st_size != entry['size'] or sha(path) != entry['sha256']:
            raise ValueError(f"changed frozen input: {entry['path']}")
    original = hashlib.sha256()
    for part in manifest['original_source']['archive_parts']:
        original.update((HERE / part['path']).read_bytes())
    if original.hexdigest() != manifest['original_source']['sha256']:
        raise ValueError('original PDF archive SHA-256 changed')
    return manifest


def clean(raw: str) -> str:
    value = re.sub(r'(?<=\w)-\s*\n\s*(?=\w)', '', raw)
    return ' '.join(unicodedata.normalize('NFKC', value).split()).replace('approxi mately', 'approximately')


def owns(rect: list, bbox: list) -> bool:
    # Majority ownership avoids consuming a neighboring paragraph or heading.
    x0, y0, x1, y1 = bbox
    overlap = max(0, min(x1, rect[2]) - max(x0, rect[0])) * max(0, min(y1, rect[3]) - max(y0, rect[1]))
    return overlap > max((x1-x0)*(y1-y0), .001) * .5


def control(name: str, label: str) -> str:
    return f'<img class="source-inline-control" src="assets/inline-{name}.png" alt="{html.escape(label)}">'


def line_html(raw: str, number: int, y: float) -> str:
    text = html.escape(clean(raw))
    if number == 17 and 335 < y < 350:
        text = text.replace('Tap in', 'Tap ' + control('add-device', 'Add device') + ' in')
    if number == 18 and 278 < y < 292:
        if text.startswith('1. Tap'):
            text = text.replace('Tap in', 'Tap ' + control('settings', 'Settings') + ' in')
        elif text.startswith('2. Select'):
            text += ' ' + control('voltage-config', 'Voltage configuration')
    if number == 19 and 26 < y < 38:
        text = text.replace('Tap in', 'Tap ' + control('edit', 'Edit') + ' in')
        text = text.replace('the to', 'the ' + control('link-circuits', 'Link circuits') + ' to')
    if number == 19 and 38 < y < 52:
        text = text.replace('tap to', 'tap ' + control('save', 'Save') + ' to')
    if number == 19 and 353 < y < 368:
        text = text.replace('tap to', 'tap ' + control('edit-name', 'Edit circuit name') + ' to')
    return text


def figure(item: dict) -> str:
    labels = item.get('labels', '')
    mirror = ('<details class="source-labels"><summary>Figure labels</summary><p>' + html.escape(labels) + '</p></details>') if labels else ''
    return (f'<figure class="source-figure" style="--source-figure-width:{item["max_width"]}px">'
            f'<img src="{item["local_path"]}" alt="{html.escape(item["caption"])}" loading="eager">'
            f'<figcaption>{html.escape(item["caption"])}</figcaption>{mirror}</figure>')


def table(item: dict, symbols: list) -> str:
    rows = item['rows']
    header = rows[0]
    parts = [f'<div class="manual-table-scroll" role="region" tabindex="0" aria-label="{item["kind"]}"><table class="manual-table"><thead><tr>']
    parts += [f'<th scope="col">{html.escape(cell)}</th>' for cell in header]
    parts += ['</tr></thead><tbody>']
    for index, row in enumerate(rows[1:]):
        parts.append('<tr>')
        for col, cell in enumerate(row):
            if item['kind'] == 'symbols' and col == 0:
                asset = symbols[index]
                markup = f'<img class="source-symbol" src="{asset["local_path"]}" alt="{html.escape(asset["meaning"])}">'
            else:
                markup = html.escape(cell)
            tag = 'th scope="row"' if col == 0 else 'td'
            end = 'th' if col == 0 else 'td'
            parts.append(f'<{tag}>{markup}</{end}>')
        parts.append('</tr>')
    return ''.join(parts + ['</tbody></table></div>'])


def page_events(page: dict, figures: list, recoveries: list, symbols: list) -> list:
    number = page['physical_page']
    arts = [f for f in figures if f.get('physical_page') == number]
    consumed = [f['bbox'] for f in arts] + [t['bbox'] for t in page['tables']]
    lines = []
    for block in page['blocks']:
        for line in block['lines']:
            bbox = line['bbox']
            if (bbox[1] < 24 or bbox[1] > 503 or clean(line['raw_text']) in {'US', 'English', 'Model: JA-TS02A'}
                    or any(owns(r, bbox) for r in consumed)):
                continue
            if not clean(line['raw_text']):
                continue
            lines.append(line)
    # Parallel print columns may differ slightly in baseline; preserve step order.
    if number == 18:
        for line in lines:
            if clean(line['raw_text']).startswith('1. Tap'):
                line['bbox'] = [line['bbox'][0], 280, line['bbox'][2], line['bbox'][3]]
    lines += [{'bbox': r['bbox'], 'raw_text': r['text'], 'font_size': 7, 'bold': False}
              for r in recoveries if r['physical_page'] == number]
    callouts = []
    if number == 10:
        for rect in [[27, 76, 339, 105], [27, 188, 339, 245]]:
            members = [line for line in lines if owns(rect, line['bbox'])]
            body = [line for line in sorted(members, key=lambda v: v['bbox'][1]) if clean(line['raw_text']) != 'CAUTION']
            markup = ' '.join(html.escape(clean(line['raw_text'])) for line in body)
            callouts.append({'bbox': rect, 'kind': 'callout', 'html': '<div class="source-caution"><strong>CAUTION</strong><p>' + markup + '</p></div>'})
            lines = [line for line in lines if line not in members]
    events = callouts + [{'bbox': f['bbox'], 'html': figure(f), 'kind': 'figure'} for f in arts]
    events += [{'bbox': t['bbox'], 'html': table(t, symbols), 'kind': 'table'} for t in page['tables']]
    # Each complete line retains its source position while wrapped prose joins.
    for line in lines:
        text = clean(line['raw_text'])
        kind = 'main' if text in MAIN_HEADINGS else 'heading' if text in SUB_HEADINGS else 'line'
        markup = line_html(line['raw_text'], number, line['bbox'][1])
        if kind == 'main':
            markup = f'\n# {text}\n'
        elif kind == 'heading':
            markup = f'<h2>{markup}</h2>'
        events.append({'bbox': line['bbox'], 'html': markup, 'kind': kind, 'raw': line['raw_text']})
    return sorted(events, key=lambda e: (round(e['bbox'][1], 1), e['bbox'][0]))


def prose(events: list) -> str:
    chunks = []
    pending = []
    last = None
    def flush():
        if pending:
            value = ' '.join(pending)
            # Joining a print line ending in a split-word hyphen is formatting only.
            value = re.sub(r'(?<=\w)- (?=[a-z])', '', value).replace('approxi mately', 'approximately')
            chunks.append('<p>' + value + '</p>')
            pending.clear()
    for event in events:
        if event['kind'] != 'line':
            flush()
            chunks.append(event['html'])
            last = None
            continue
        raw = clean(event.get('raw', ''))
        starts_item = bool(re.match(r'^(?:\d+\.|[•*])\s*', raw))
        if last and (starts_item or abs(event['bbox'][0]-last['bbox'][0]) > 14
                     or event['bbox'][1]-last['bbox'][3] > 9):
            flush()
        pending.append(event['html'])
        last = event
    flush()
    return '\n\n'.join(chunks)


def format_page(page: dict, events: list) -> str:
    for low, high in APP_GROUPS.get(page['physical_page'], []):
        members = [e for e in events if low <= e['bbox'][1] < high]
        pictures = [e for e in members if e['kind'] == 'figure']
        if len(pictures) != 1:
            raise ValueError('App frame group no longer has one source screenshot')
        body = [e for e in members if e['kind'] != 'figure']
        group = {'bbox': [20, low, 345, high], 'kind': 'group',
                 'html': '<div class="source-app-row"><div>' + pictures[0]['html'] + '</div><div>' + prose(body) + '</div></div>'}
        events = [e for e in events if e not in members] + [group]
        events.sort(key=lambda e: (e['bbox'][1], e['bbox'][0]))
    return prose(events)


def build(output: Path) -> None:
    manifest = verify_inputs()
    if output.exists():
        raise ValueError('use a new output directory for cold replay')
    output.mkdir(parents=True)
    shutil.copytree(HERE / 'assets', output / 'assets')
    filename = 'manual_jats02a_us_en.md'
    path = output / filename
    _write_myst_sphinx_scaffold(path, title='Jackery Smart Transfer Switch — JA-TS02A', presentation_profile='web')
    with (output / 'conf.py').open('a', encoding='utf-8') as stream:
        stream.write("language = 'en'\nhtml_css_files += ['source_presentation.css']\n")
    shutil.copyfile(HERE / 'source/web_presentation.css', output / '_static/source_presentation.css')
    pages = read_json('source/native-pages.json')['pages']
    all_assets = read_json('source/figures.json')
    figures = [a for a in all_assets if a.get('physical_page')]
    symbols = [a for a in all_assets if a['slot'].startswith('symbol/')]
    recoveries = read_json('source/text-recovery.json')
    chunks = ['<div class="source-manual" lang="en">']
    for page in pages:
        events = page_events(page, figures, recoveries, symbols)
        chunks.append(format_page(page, events))
    chunks.append('</div>')
    # MyST headings must live outside a raw HTML block for navigation.
    text = '\n\n'.join(chunks).replace('<div class="source-manual" lang="en">\n\n', '').removesuffix('\n\n</div>')
    path.write_text(text + '\n', encoding='utf-8')
    summary = {'target': manifest['target'], 'body_page_count': len(pages),
               'chapter_count': sum(1 for line in text.splitlines() if line.startswith('# ')),
               'figure_count': len(figures), 'native_table_count': sum(len(p['tables']) for p in pages),
               'recovered_source_lines': len(recoveries)}
    (output / 'conversion-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output.resolve())
