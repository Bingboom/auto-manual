"""Prepare this JSG bundle from its source-checked Japanese transcription.

The included-station semantic reference is hash pinned in source/reference.json.
The bundle additions and corrections are explicit source transcriptions below;
no values are inferred from its SKU or another model. Shared constructors and
renderers own the presentation. Nothing grants publication authorization.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

SOURCE = Path(__file__).resolve().parent
ROOT = next(p for p in SOURCE.parents if (p / 'build.py').is_file())
sys.path.insert(0, str(ROOT))

from tools.component_specs.app import app_qr_download_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.web.frozen_ai_flow import heading, node, root  # noqa: E402


def read_pinned(reference):
    path = ROOT / reference['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != reference['sha256']:
        raise ValueError('reviewed reference changed: ' + reference['path'])
    return path


def spec_id(flow):
    spec = flow.get('component_spec', {})
    return spec.get('component_id')


def ref_id(flow):
    slots = flow.get('component_spec', {}).get('slots', [])
    return next((s['content'] for s in slots if s['role'] == 'reference_id'), None)


def prepare():
    manifest = json.loads((SOURCE / 'source_manifest.json').read_text())
    reference = json.loads((SOURCE / 'source/reference.json').read_text())
    incoming = json.loads((SOURCE / 'source/additions.json').read_text())
    spec = importlib.util.spec_from_file_location('frozen_jp_flow_kit', read_pinned(reference['kit']))
    kit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kit)
    b = kit.Book(SOURCE, manifest['target']['model'], 'JP', 'ja', incoming['title'])
    content = deepcopy(json.loads(read_pinned(reference['content']).read_text()))
    # Flatten reused small-icon asset locations without changing any bytes.
    raw = json.dumps(content, ensure_ascii=False)
    for nested in sorted(set(re.findall(r'assets/[A-Za-z0-9_.\-/]+', raw))):
        if '/' in nested[len('assets/'):]:
            raw = raw.replace(nested, 'assets/' + Path(nested).name)
    content = json.loads(raw)
    # Bind the six rows to the fresh source-bound canonical symbol decisions.
    symbols = json.loads((SOURCE / 'source/symbols.json').read_text())
    raw = json.dumps(content, ensure_ascii=False)
    old = next(n['component_spec']['assets'] for c in content['chapters']
               for n in c['nodes'] if spec_id(n) == 'HB-TABLE-SYMBOL-ICON')
    for previous, current in zip(old, symbols, strict=True):
        raw = raw.replace(previous['asset_ref'], current['local_path'])
    content = json.loads(raw)
    # Current source physical8 has ON in all three default energy-mode cells.
    raw = json.dumps(content, ensure_ascii=False)
    if raw.count('OFF（dispalyに') != 3:
        raise ValueError('reviewed old energy-table shape changed')
    content = json.loads(raw.replace('OFF（dispalyに', 'ON（dispalyに'))
    chapters = {c['id']: c for c in content['chapters']}
    # Source p12–14 and p17 use the current common Japanese safety/disclaimer
    # text, not the older JE-240A reference's amended 45°C/600Plus clauses.
    common = json.loads(read_pinned(reference['app_content']).read_text())
    for key, title in [('safety', '7.安全上のご注意'), ('disclaimer', '10.免責事項')]:
        chapters[key] = deepcopy(next(c for c in common['chapters'] if c['id'] == key))
        chapters[key]['title'] = title
        chapters[key]['nodes'][0] = root(heading(title, level=2, anchor='native-' + key))
    for key, pages in incoming['page_map'].items():
        chapters[key]['pages'] = pages

    # Current bundle p9–10 has no UPS paragraph; the station-only reference did.
    if manifest['target']['model'] == 'JSG-2404A':
        chapters['usage']['nodes'] = [n for n in chapters['usage']['nodes']
            if 'UPS機能:' not in json.dumps(n, ensure_ascii=False)]

    # Cover identity/logo/art is omitted; all substantive copy remains native.
    preface = {'id': 'preface', 'title': 'お買い上げありがとうございます。', 'pages': [1], 'nodes': [
        root(kit.P('国内専用/For use only in Japan')),
        root(kit.P('カスタマーサポート:jackery.jp@jackery.com')),
        root(heading('お買い上げありがとうございます。', level=2, anchor='native-preface')),
        *[root(kit.P(v)) for v in incoming['preface']],
    ]}
    b.chapter('solar_unfolding', 'ソーラーパネル取扱説明書：', [4, 5])
    for i in range(1, 6):
        b.h(str(i) + ' ' + b.figures[f'unfold-{i}']['caption'])
        b.figure(f'unfold-{i}')
    unfolding = b.chapters[-1]

    # New solar specification rows are read from this bundle's own p6.
    b.chapter('solar_specification', incoming['solar_spec_title'], [6])
    b.comp(spec_table_component_spec, kit.spec_carrier, section_title=incoming['solar_spec_title'], rows=incoming['solar_spec_rows'])
    solar_nodes = b.chapters[-1]['nodes'][1:]
    solar_nodes.append(root(kit.P('STC (1000W/m², 25°C, AM 1.5).')))
    station_spec = chapters['specifications']['nodes']
    trademark = next(i for i, n in enumerate(station_spec) if 'USB Implementers Forum' in json.dumps(n, ensure_ascii=False))
    station_spec[trademark + 1:trademark + 1] = solar_nodes

    # The bundle overview includes both the station and the unfolded panel.
    b.chapter('product_overview', chapters['product_overview']['title'], [7])
    b.figure('overview')
    chapters['product_overview']['nodes'] = b.chapters[-1]['nodes']

    b.chapter('charging', chapters['charging']['title'], incoming['page_map']['charging'])
    b.figure('charging-solar')
    solar_figure = b.chapters[-1]['nodes'][-1]
    charging = chapters['charging']['nodes']
    if manifest['target']['model'] == 'JSG-2404A':
        # Explicit differences from the station-only reference, read on p10–12.
        b.chapter('charging_caution', 'ご注意', [10])
        b.callout('ご注意', kit.UL(*incoming['charging_caution']), variant='caution')
        charging[5] = b.chapters[-1]['nodes'][-1]
        charging[13] = root(heading('Jackery SolarSaga 40 Mini 接続説明', level=4))
        charging[14] = root(kit.P(incoming['solar_connection']))
        charging[17] = root(kit.P(incoming['car_charging']))
        charging[20:] = [root(kit.P(v)) for v in incoming['charging_safety']]
    for i, n in enumerate(charging):
        if ref_id(n) in ('charging-solar', 'solar-charge'):
            charging[i] = solar_figure

    # New SolarSaga40Mini precautions are appended after the station's own copy.
    cautions = chapters['usage_precautions']
    cautions['nodes'] += [root(heading('使用上のご注意 (SolarSaga 40 Mini)', level=3)),
                          root(kit.P('**※ご使用の前に取扱説明書をよくお読みになり正しくお使いください。**')),
                          root(kit.UL(*incoming['solar_precautions']))]

    # Eight source items; preserve the bundle's printed heading numbering.
    if manifest['target']['model'] == 'JSG-2404A':
        chapters['in_the_box']['title'] = '8.同梱品'
    b.chapter('in_the_box', chapters['in_the_box']['title'], [17])
    cards = [{'image_ref': 'assets/' + filename, 'label': label, 'alt': label}
             for filename, label in incoming['inbox']]
    b.comp(inbox_component_spec, kit.inbox_carrier, accessibility_label=chapters['in_the_box']['title'],
           cards=cards, tip_label='', tip_body='', require_tip=False)
    b.add(kit.P('※付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。'))
    chapters['in_the_box']['nodes'] = b.chapters[-1]['nodes']

    # Source App instructions are identical to the 300Plus reference on p18–19;
    # its old unheaded download notice moves to the actual back cover location.
    app = deepcopy(json.loads(read_pinned(reference['app_content']).read_text()))
    app = next(c for c in app['chapters'] if c['id'] == 'app_setup')
    app['pages'] = [18, 19, 20]
    # Both current bundle sources stop after the owner-sharing sentence on p18.
    app = json.loads(json.dumps(app, ensure_ascii=False).replace(
        '詳細は、「機器共有」をご参照ください。', ''))
    app['nodes'] = [n for n in app['nodes']
                    if not (spec_id(n) == 'HB-SPECIAL-APP'
                            and n['component_spec']['variant'] == 'download-qr-only')]
    b.chapter('back_cover_app', 'Jackery APP', [20])
    notice = incoming['app_notice']
    badges = incoming['badges']
    b.comp(app_qr_download_component_spec,
           lambda spec: [node('image', source=badges, alt='App Store / Google Play'), kit.P(notice)],
           label='App Store / Google Play', paragraph={'text': notice, 'html': notice}, image_ref=badges)
    b.figure('app-qr')
    app['nodes'] += b.chapters[-1]['nodes'][1:]
    chapters['app_setup'] = app

    final = [preface, unfolding] + [chapters[c['id']] for c in content['chapters']]
    result = {'title': incoming['title'], 'model': manifest['target']['model'], 'region': 'JP', 'language': 'ja',
              'source_sha256': manifest['original_source']['sha256'],
              'transcription': 'source-checked Japanese outlined PDF transcription; reference copy retained only where verified',
              'chapters': final}
    # Printed block references bind this original PDF, not a donor booklet’s pages.
    page_map = json.loads((SOURCE / 'source/block_pages.json').read_text())
    for chapter in final:
        spans = page_map[chapter['id']]
        if len(spans) != len(chapter['nodes']):
            raise ValueError('reviewed source-page map changed: ' + chapter['id'])
        for index, flow in enumerate(chapter['nodes']):
            if spec := flow.get('component_spec'):
                pages = ','.join(str(page) for page in spans[index])
                spec['source_ref'] = ('original.pdf#physical-pages=' + pages
                                      + '&block=' + chapter['id'] + '/' + str(index))

    destination = SOURCE / 'source/ja/content.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'model': result['model'], 'chapters': len(final)}, ensure_ascii=False))


if __name__ == '__main__':
    prepare()
