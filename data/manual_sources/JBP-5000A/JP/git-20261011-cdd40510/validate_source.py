"""Check source-line provenance, rendered native copy, tables and asset closure."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
import fitz

PACKAGE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value):
    return ''.join(value.split())


def validate(output):
    ledger = json.loads((PACKAGE / 'source/ja/coverage.json').read_text())
    pages = json.loads((PACKAGE / 'source/native_pages.json').read_text())
    content = json.loads((PACKAGE / 'source/ja/content.json').read_text())
    manifest = json.loads((PACKAGE / 'source_manifest.json').read_text())
    original = next(PACKAGE.glob('*.pdf'))
    if digest(original) != content['source_sha256'] or len(fitz.open(original)) != 10:
        raise ValueError('native PDF identity changed')
    if manifest['target']['model'] != 'JBP-5000A' or content['language'] != 'ja':
        raise ValueError('native target identity changed')
    native = {line['id']: line for page in pages[1:10]
              for block in page['blocks'] for line in block['lines']}
    selected = [identity for entry in ledger['selections'] for identity in entry['line_ids']]
    if ledger['unmapped'] or len(selected) != len(set(selected)) or set(selected) != set(native):
        raise ValueError('source body coverage is incomplete or repeated')
    for entry in ledger['selections']:
        if entry['text'] != ''.join(native[i]['text'].strip() for i in entry['line_ids']):
            raise ValueError('native words changed: ' + str(entry['line_ids']))
    page = output / 'manual_jbp5000a_jp_ja.html'
    soup = BeautifulSoup(page.read_text(), 'html.parser')
    main = soup.select_one('[role=main]')
    for hidden in main.select('[hidden], [aria-hidden=true], script, style'):
        hidden.decompose()
    corpus = normalized(main.get_text())
    live = [v for v in ledger['selections'] if v['purpose'].startswith('live')]
    missing = [v for v in live if normalized(v.get('rendered_text', v['text'])) not in corpus]
    if missing:
        raise ValueError('rendered native copy missing: ' + json.dumps(missing, ensure_ascii=False))
    ids = [e['id'] for e in soup.select('[id]')]
    if len(ids) != len(set(ids)):
        raise ValueError('repeated HTML anchor')
    if len(content['chapters']) != 9 or any(
        soup.find(id='native-' + ch['id']) is None for ch in content['chapters']
    ):
        raise ValueError('native chapters missing')
    for component, count in [('HB-TABLE-LCD-ICON', 2)]:
        table = main.select_one(f'[data-component-id="{component}"]')
        if table is None or len(table.select('tbody > tr')) != count:
            raise ValueError('native table row inventory changed: ' + component)
    specs = main.select('.hb-spec-table')
    if len(specs) != 1 or len(specs[0].select('tbody > tr')) != 12:
        raise ValueError('native specification inventory changed')
    references = main.select('figure[data-reference-id]')
    if len(references) != 12 or len(main.select('.hb-reference-live-label')) != 27:
        raise ValueError('native figure/caption inventory changed')
    decisions = json.loads((PACKAGE / 'source/asset_decisions.json').read_text())
    for row in decisions:
        if row.get('final_path') and digest(PACKAGE / row['final_path']) == row.get('prior_candidate_sha256'):
            raise ValueError('superseded artwork restored')
        if row.get('final_path') and digest(PACKAGE / row['final_path']) != row['sha256']:
            raise ValueError('artwork decision hash changed')
    for image in main.select('img'):
        parsed = urlsplit(image['src'])
        if parsed.scheme:
            raise ValueError('unexpected external artwork')
        path = output / unquote(parsed.path)
        original = PACKAGE / 'assets' / path.name
        if not path.is_file() or not original.is_file() or digest(path) != digest(original):
            raise ValueError('consumed artwork missing or changed: ' + image['src'])
    report = {'model': 'JBP-5000A', 'region': 'JP', 'language': 'ja',
              'body_lines': len(native), 'live_selections': len(live), 'missing_copy': 0,
              'chapters': 9, 'reference_figures': 12, 'live_labels': 27,
              'loaded_asset_bindings': len(main.select('img')), 'passed': True}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    validate(args.output.resolve())
