"""Replay the JE-3000A JP outlined-source transcription through the shared Web components.

The source-local input package is immutable. Use a new --output directory.
No live source, queue, asset or link service is read or written.

Symbol admission: the fixed ``require_symbol_asset_admission`` cannot read
this PDF (its shared vector selector refuses the page; see
``source_manifest.json:symbol_admission_blocker``). The replay still runs it
and requires exactly the recorded refusal, so a fixed selector cannot be
missed, and re-checks every symbol row against the source vector paths at the
fixed 2% tolerance with the package-local reference writer. The candidate is
never publication-eligible while the blocker or a pending row stands.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import fitz

SOURCE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = next(p for p in SOURCE_ROOT.parents if (p / 'build.py').is_file())
sys.path.insert(0, str(REPO_ROOT))

from tools.component_specs.registry import load_component_registry, registry_sha256  # noqa: E402
from tools.component_specs.theme import load_manual_theme, theme_sha256  # noqa: E402
from tools.manual_ir import ManualSource, SourcePage, V2_SCHEMA_VERSION, build_manual_ir_from_source, write_manual_ir  # noqa: E402
from tools.manual_ir.components import component_specs_in_flow  # noqa: E402
from tools.manual_ir.document import validate_document  # noqa: E402
from tools.manual_ir.hashing import file_sha256, value_sha256  # noqa: E402
from tools.markdown_bundle import _write_myst_sphinx_scaffold  # noqa: E402
from tools.web.frozen_ai_web import replay_package  # noqa: E402
from tools.web.presentation import load_web_manual_contract  # noqa: E402
from tools.web.prepared_style_audit import require_prepared_document_styles  # noqa: E402
from tools.web.shared_symbol_assets import require_shared_symbol_binding, require_usable_symbol_file  # noqa: E402
from tools.web.symbol_asset_admission import compare_symbol, require_symbol_asset_admission  # noqa: E402


def _derive_module():
    spec = importlib.util.spec_from_file_location('je3000a_jp_derive_assets', SOURCE_ROOT / 'derive_assets.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_symbols(output: Path, manifest: dict) -> dict:
    """Run the fixed admission, require the recorded blocker, then check every row locally."""
    blocker = manifest['symbol_admission_blocker']
    expected = {row['message'] for row in blocker['refusals']}
    try:
        require_symbol_asset_admission(output, SOURCE_ROOT, manifest, 'ja')
    except RuntimeError as exc:
        if not any(message in str(exc) for message in expected):
            raise
        refusal = str(exc)
    else:
        raise ValueError('fixed symbol admission now passes: drop symbol_admission_blocker and re-derive')
    derive = _derive_module()
    rows = manifest['symbol_asset_admission']['locales']['ja']
    report = []
    with fitz.open(SOURCE_ROOT / manifest['original_source']['filename']) as doc:
        for row in rows:
            candidate = output / row['asset_ref']
            data = candidate.read_bytes()
            if hashlib.sha256(data).hexdigest() != row['asset_sha256']:
                raise ValueError('symbol asset changed: ' + row['asset_ref'])
            require_usable_symbol_file(candidate)
            page = doc[row['physical_page'] - 1]
            pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(row['caption_bbox']), alpha=False)
            if hashlib.sha256(pixels.tobytes('png')).hexdigest() != row['caption_sha256']:
                raise ValueError('symbol caption pixels changed: ' + row['asset_ref'])
            native = derive.drawing_svg(page, row['drawing_indices'], row['glyph_bbox'])
            if row['shared_symbol_key'] is None:
                if data != native or row['asset_ref'] not in blocker['pending_rows']:
                    raise ValueError('pending symbol row must be the source vector paths: ' + row['asset_ref'])
                report.append({'asset_ref': row['asset_ref'], 'status': 'pending-shared-variant'})
                continue
            require_shared_symbol_binding(row, candidate)
            report.append({'asset_ref': row['asset_ref'], 'shared_symbol_key': row['shared_symbol_key'],
                           **compare_symbol(data, candidate.suffix, native)})
    return {'fixed_admission': 'blocked', 'refusal': refusal, 'local_rows': report}


def rebuild(output: Path) -> dict:
    if output.exists():
        raise ValueError('use an unused output directory')
    manifest = json.loads((SOURCE_ROOT / 'source_manifest.json').read_text())
    for base, rows in [(SOURCE_ROOT, manifest['inputs']), (REPO_ROOT, manifest['repo_inputs'])]:
        for row in rows:
            path = (base / row['path']).resolve()
            if not path.is_relative_to(base) or not path.is_file() or file_sha256(path) != row['sha256']:
                raise ValueError('input missing or changed: ' + row['path'])
    source = json.loads((SOURCE_ROOT / 'source/ja/content.json').read_text())
    if file_sha256(SOURCE_ROOT / manifest['original_source']['filename']) != source['source_sha256']:
        raise ValueError('authoritative PDF identity changed')
    approved = manifest['publication_status'] == 'operator-authorized-git-only-release'
    if approved:
        raise ValueError('release needs a reviewed source/approval.json and a cleared symbol admission blocker')
    shutil.copytree(SOURCE_ROOT / 'assets', output / 'assets')
    filename = 'manual_je3000a_jp_ja.md'
    _write_myst_sphinx_scaffold(output / filename, title=source['title'], presentation_profile='web')
    with (output / 'conf.py').open('a') as stream:
        stream.write("\nlanguage = 'ja'\n")
    shutil.copy2(SOURCE_ROOT / 'source/geometry.css', output / '_static/source_geometry.css')
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    contract = load_web_manual_contract(model=source['model'], region=source['region'])
    pages = tuple(SourcePage(page_id=ch['id'], source_ref='native-pdf/' + ch['id'],
                             source_path='source/ja/content.json#' + ch['id'], language='ja',
                             source_sha256=value_sha256(ch), blocks=tuple(('flow', flow) for flow in ch['nodes']))
                  for ch in source['chapters'])
    specs = component_specs_in_flow([block for page in pages for _, block in page.blocks])
    pending = ['Candidate pending operator review of the 1280/390 renders and source concerns',
               'Fixed symbol admission blocked: ' + '; '.join(r['message'] for r in manifest['symbol_admission_blocker']['refusals']),
               *('No admitted shared symbol variant: ' + ref for ref in manifest['symbol_admission_blocker']['pending_rows'])]
    metadata = {
        'projection': 'whole-document-components/v1', 'title': source['title'],
        'markdown_filename': filename, 'declared_languages': ['ja'],
        'publication_eligible': False, 'operator_source_acceptance': None,
        'pending_source_review': pending,
        'frozen_source_manifest': manifest,
        'source_authority': {'filename': manifest['original_source']['filename'], 'sha256': source['source_sha256'],
                             'physical_pages': list(range(2, 15))},
        'asset_sha256': {p.relative_to(output).as_posix(): file_sha256(p) for p in sorted((output / 'assets').rglob('*')) if p.is_file()},
        'component_registry': registry, 'component_registry_sha256': registry_sha256(registry),
        'manual_theme': theme, 'manual_theme_sha256': theme_sha256(theme),
        'web_contract': contract, 'composites': [], 'page_declarations': {},
        'frozen_stylesheet_sha256': file_sha256(output / '_static/web_manual.css'),
        'source_stylesheet': {'path': '_static/source_geometry.css', 'sha256': file_sha256(output / '_static/source_geometry.css')},
        'component_inventory': {identity: sum(s.component_id == identity for s in specs) for identity in sorted({s.component_id for s in specs})},
    }
    ir = build_manual_ir_from_source(ManualSource(model=source['model'], region=source['region'], language='ja',
        source='prepared-document', bundle_root='frozen-source', bundle_sha256=value_sha256(source), snapshot_sha256=None,
        layout_params_sha256=value_sha256({'layout': 'web'}), style_contract_sha256=value_sha256(contract),
        pages=pages, metadata=metadata, schema_version=V2_SCHEMA_VERSION))
    validate_document(ir)
    require_prepared_document_styles(ir.to_dict(), stylesheet=(SOURCE_ROOT / 'source/geometry.css').read_text(),
                                     exceptions=manifest.get('shared_component_exceptions', ()))
    write_manual_ir(ir, output / 'manual.ir.json')
    replay_package(output)
    symbols = check_symbols(output, manifest)
    result = {'output': str(output), 'chapters': len(pages), 'components': metadata['component_inventory'],
              'symbol_admission': symbols}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    rebuild(parser.parse_args().output.resolve())
