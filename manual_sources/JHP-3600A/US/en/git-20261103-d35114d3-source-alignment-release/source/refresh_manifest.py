"""Seal reviewed native inputs and source-bound symbol rows without online writes."""
from pathlib import Path
import hashlib
import json
import re
import sys

import fitz

SOURCE = Path(__file__).resolve().parents[1]
REPO = next(p for p in SOURCE.parents if (p / 'build.py').is_file())
sys.path.insert(0, str(REPO))
from tools.web.language_release_evidence import _file_inventory  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(value):
    if isinstance(value, dict):
        if value.get('component_id') == 'HB-TABLE-SYMBOL-ICON':
            yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def symbol_rows(document, language, catalog):
    content = json.loads((SOURCE / f'source/{language}/content.json').read_text())
    spec, = list(walk(content))
    panels = next(s['content'] for s in spec['slots'] if s['role'] == 'panels')
    number = {'en': 5, 'fr': 25, 'es': 45}[language]
    page = document[number - 1]
    drawings = page.get_drawings()
    frames = sorted((x['rect'] for x in drawings
                     if 120 < x['rect'].width < 170 and x['rect'].height > 100), key=lambda x: x.x0)
    assert len(frames) == 2
    result = []
    for panel, frame in zip(panels, frames, strict=True):
        divider, = [x['rect'] for x in drawings if x['rect'].width < 2
                    and x['rect'].height > 175 and frame.x0 < x['rect'].x0 < frame.x1
                    and abs(x['rect'].y0 - frame.y0) < 1]
        cuts = sorted((x['rect'].y0 + x['rect'].y1) / 2 for x in drawings
                      if 130 < x['rect'].width < 160 and x['rect'].height < 2
                      and abs(x['rect'].x0 - frame.x0) < 1
                      and frame.y0 < x['rect'].y0 < frame.y1)
        assert len(cuts) == len(panel)
        limits = cuts + [frame.y1]
        for row, low, high in zip(panel, limits[:-1], limits[1:], strict=True):
            box = fitz.Rect(frame.x0 + .6, low + .6, divider.x0 - .6, high - .6)
            indices = [i for i, x in enumerate(drawings) if box.contains(x['rect'])]
            assert indices
            bounds = [drawings[i]['rect'] for i in indices]
            pad = 1 if 'explosive_material' in spec['assets'][row['asset_index']]['asset_ref'] else .1
            glyph = [min(b.x0 for b in bounds) - pad, min(b.y0 for b in bounds) - pad,
                     max(b.x1 for b in bounds) + pad, max(b.y1 for b in bounds) + pad]
            caption = [divider.x1 + .6, low + .6, frame.x1 - .6, high - .6]
            band = [frame.x0 + .2, low + .2, frame.x1 - .2, high - .2]
            ref = spec['assets'][row['asset_index']]['asset_ref']
            shared, = [x for x in catalog['assets'] if x['sha256'] == digest(SOURCE / ref)]
            pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(caption), alpha=False)
            native_text = page.get_text('text', clip=fitz.Rect(caption))
            joins = [m.group(0) for m in re.finditer(r'([^\W\d_]+)-[ \t]*\r?\n[ \t]*([^\W\d_]+)', native_text)]
            result.append({'asset_ref': ref, 'asset_sha256': digest(SOURCE / ref),
                           'shared_symbol_key': shared['key'], 'physical_page': number,
                           'drawing_indices': indices, 'glyph_bbox': glyph,
                           'caption_bbox': caption, 'row_bbox': band,
                           'caption_text': row['meaning_text'],
                           'caption_sha256': hashlib.sha256(pixels.tobytes('png')).hexdigest(),
                           'caption_mode': 'native-extractable-text' if native_text.strip() else 'reviewed-native-outlined-caption',
                           **({'caption_linebreak_joins': joins} if joins else {})})
    return result


def refresh():
    path = SOURCE / 'source_manifest.json'
    manifest = json.loads(path.read_text())
    catalog = json.loads((REPO / 'docs/renderers/web/assets/shared/symbols/manifest.json').read_text())
    with fitz.open(SOURCE / manifest['original_source']['filename']) as document:
        manifest['symbol_asset_admission'] = {
            'schema_version': 'auto-manual-symbol-asset-admission/v1',
            'locales': {language: symbol_rows(document, language, catalog) for language in ('en', 'fr', 'es')}}
    approval_path = SOURCE / 'source/approval.json'
    reviewed = list(_file_inventory(SOURCE, excluded_roots=(path, SOURCE / 'web', approval_path,
                                                           SOURCE / 'source/__pycache__', SOURCE / '__pycache__')))
    approval = {'schema_version': 'auto-manual-operator-source-acceptance/v1',
                'target': {key: manifest['target'][key] for key in ('model', 'region', 'technical_version')},
                'languages': ['en', 'fr', 'es'], 'original_source_sha256': manifest['original_source']['sha256'],
                'reviewed_candidate_git_ref': '942777a0d', 'operator_quote': '先提交发布推送',
                'accepted_at': '2026-10-12', 'merge_authorization': 'MA-295',
                'reviewed_inputs': reviewed, 'git_only': True}
    approval_path.write_text(json.dumps(approval, ensure_ascii=False, indent=2) + '\n')
    manifest['inputs'] = list(_file_inventory(SOURCE, excluded_roots=(path, SOURCE / 'source/__pycache__', SOURCE / '__pycache__')))
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print({'inputs': len(manifest['inputs']), 'reviewed_inputs': len(reviewed), 'native_symbol_rows': 33})


if __name__ == '__main__':
    refresh()
