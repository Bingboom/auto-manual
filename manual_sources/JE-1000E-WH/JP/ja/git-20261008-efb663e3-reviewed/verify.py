"""Independent native-line coverage, cold replay and rejection checks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from bs4 import BeautifulSoup
from rebuild import admit, validate_inputs


def normalized(value):
    return re.sub(r'\s', '', value.replace('\uf6b3', '2').replace('\uf6b7', '6'))


def inventory(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--pdf', type=Path, help='also verify native symbol paths/transparency')
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    read = lambda name: json.loads((package / name).read_text())
    manifest = read('source_manifest.json')
    validate_inputs(package, manifest, args.pdf)
    native = read('source/native-text.json')
    soup = BeautifulSoup(args.html.read_text(), 'html.parser')
    article = soup.select_one('article')
    assert article is not None, 'missing semantic article'
    for link in article.select('.headerlink'):
        link.decompose()
    body = normalized(article.get_text())
    missing = []
    checked = 0
    plus = 0
    for record in read('source/dispositions.json'):
        if record['role'] != 'selectable-semantic-copy':
            continue
        page, block = record['physical_page'], record['block']
        for line in native['pages'][page - 1]['blocks'][block]['text'].splitlines():
            line = re.sub(r'^[•・■]\s*', '', line.strip())
            # The native vector circled-plus has no Unicode in extracted text.
            if (page, block) == (25, 8):
                line = line.replace('        ', ' + ')
                plus += 1
            if len(normalized(line)) < 3:
                continue
            checked += 1
            if normalized(line) not in body:
                missing.append({'page': page, 'block': block, 'line': line})
    assert not missing, missing
    required = read('source/admission.json')
    for anchor in required['chapters']:
        assert article.find(id=anchor) is not None, anchor
    panels = article.select('.hb-symbol-panel')
    assert len(panels) == 2
    expected_icons = [['unplug', 'do_not_dismantle', 'no_wet_hands', 'warning_triangle',
                       'read_manual', 'no_open_flame', 'keep_away_from_children'],
                      ['mandatory', 'keep_dry', 'prohibited', 'battery_recycle', 'weee']]
    for panel, expected in zip(panels, expected_icons, strict=True):
        assert [Path(i['src']).name for i in panel.select('img')] == [
            f'symbol-{name}.svg' for name in expected], 'native safety order changed'
    assert len(article.select('img[src="assets/symbol-battery_recycle.svg"]')) == 1
    warnings = article.select('table.manual-callout-table')
    assert any(len(w.select('li')) == 5 for w in warnings), 'abnormal conditions lost'
    symbol_report = []
    if args.pdf:
        import fitz
        from tools.asset_pipeline.native_svg import native_symbol_svg
        from tools.web.symbol_asset_admission import compare_symbol
        with fitz.open(args.pdf) as pdf:
            for binding in read('source/symbol-bindings.json'):
                reference = native_symbol_svg(pdf[binding['physical_page'] - 1],
                                              binding['drawing_indices'], binding['glyph_bbox'])
                asset = args.html.parent / binding['asset_ref']
                symbol_report.append({'asset': binding['asset_ref'],
                                      **compare_symbol(asset.read_bytes(), asset.suffix, reference)})
    image_count = 0
    for image in article.find_all('img'):
        source = image.get('src', '')
        assert source and not source.startswith(('http:', 'https:', 'data:')), source
        assert (args.html.parent / source).is_file(), source
        image_count += 1
    for asset in read('source/asset-recipe.json')['assets']:
        assert asset['gate']['status'] == 'quarantine'
        assert not asset['build_eligible'] and asset['visual_review_required']
    rejections = []
    with tempfile.TemporaryDirectory(prefix='h1-verify-') as temp:
        temp = Path(temp)
        for index in (1, 2):
            output = temp / f'cold-{index}'
            subprocess.run([sys.executable, str(package / 'rebuild.py'), '--output', str(output)],
                           check=True, stdout=subprocess.DEVNULL)
        assert inventory(temp / 'cold-1') == inventory(temp / 'cold-2'), 'cold replay differs'
        frozen = package / 'web/ja'
        if frozen.exists():
            assert inventory(frozen) == inventory(temp / 'cold-1'), 'frozen Web differs from cold replay'
        altered = temp / 'altered'
        shutil.copytree(package, altered, ignore=shutil.ignore_patterns('web', 'validation', '__pycache__'))
        path = altered / 'source/chapters.json'
        path.write_text(path.read_text().replace('JE-1000E-WH', 'WRONG-MODEL', 1))
        try:
            validate_inputs(altered, manifest, None)
        except ValueError as error:
            rejections.append(str(error))
        else:
            raise AssertionError('source tampering accepted')
        chapters = read('source/chapters.json')
        try:
            admit(chapters[:-1], required)
        except ValueError as error:
            rejections.append(str(error))
        else:
            raise AssertionError('missing chapter accepted')
        chapters[0]['blocks'].append({'schema_version': 'manual-flow/v2', 'kind': 'image',
                                      'source': 'unbound.png', 'alt': 'unbound'})
        try:
            admit(chapters, required)
        except ValueError as error:
            rejections.append(str(error))
        else:
            raise AssertionError('unbound image accepted')
    print(json.dumps({'native_lines_checked': checked, 'missing': missing,
                      'vector_plus_recoveries': plus, 'chapter_anchors': len(required['chapters']),
                      'local_image_elements': image_count, 'cold_replay_identical': True,
                      'source_symbol_comparisons': symbol_report,
                      'frozen_web_identical': frozen.exists(), 'rejections': rejections},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
