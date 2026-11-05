"""Replay JE-1500D US outlined-source transcription through the shared Web components.

The source-local input package is immutable. Use a new --output directory.
No live source, queue, asset or link service is read or written.

Symbol rows whose shared variant is already in the catalog pass the shared
``require_symbol_asset_admission``. While a printed symbol is staged for the
operator's catalog decision (``source_manifest.json:staged_shared_symbols``),
the same source-bound checks run here, binding that row to its proposed
catalog entry instead of a catalog file.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

SOURCE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = next(p for p in SOURCE_ROOT.parents if (p / 'build.py').is_file())
sys.path.insert(0, str(REPO_ROOT))

import fitz  # noqa: E402

from tools.component_specs.registry import load_component_registry, registry_sha256  # noqa: E402
from tools.component_specs.theme import load_manual_theme, theme_sha256  # noqa: E402
from tools.manual_ir import (  # noqa: E402
    ManualSource, SourcePage, V2_SCHEMA_VERSION, build_manual_ir_from_source, read_manual_ir, write_manual_ir,
)
from tools.manual_ir.components import component_specs_in_flow  # noqa: E402
from tools.manual_ir.document import validate_document  # noqa: E402
from tools.manual_ir.hashing import file_sha256, value_sha256  # noqa: E402
from tools.markdown_bundle import _write_myst_sphinx_scaffold  # noqa: E402
from tools.web.frozen_ai_web import replay_package  # noqa: E402
from tools.web.presentation import load_web_manual_contract  # noqa: E402
from tools.web.prepared_style_audit import require_prepared_document_styles  # noqa: E402
from tools.web.shared_symbol_assets import require_shared_symbol_binding, require_usable_symbol_file  # noqa: E402
from tools.web.symbol_asset_admission import (  # noqa: E402
    SCHEMA, _component_rows, _reference, compare_symbol, require_symbol_asset_admission,
)

LANGUAGE = 'en'
CATALOG = REPO_ROOT / 'docs/renderers/web/assets/shared/symbols/manifest.json'


def staged_symbol_admission(output: Path, manifest: dict) -> list[dict]:
    """Shared admission checks with staged rows bound to their proposed catalog entry."""
    staged = {row['key']: row for row in manifest.get('staged_shared_symbols', [])}
    ir = read_manual_ir(output / 'manual.ir.json')
    specs = [s for page in ir.pages for block in page.blocks for s in component_specs_in_flow([block.payload])
             if s.component_id == 'HB-TABLE-SYMBOL-ICON']
    admission = manifest['symbol_asset_admission']
    rows = admission['locales'][LANGUAGE]
    expected = _component_rows(specs)
    if admission['schema_version'] != SCHEMA or [r['asset_ref'] for r in rows] != [ref for ref, _ in expected]:
        raise ValueError('symbol admission must cover every actual component row in order')
    source = manifest['original_source']
    report = []
    with fitz.open(SOURCE_ROOT / source['filename']) as doc:
        for row, (ref, meaning) in zip(rows, expected, strict=True):
            candidate = output / ref
            if file_sha256(candidate) != row['asset_sha256']:
                raise ValueError('symbol source/asset SHA-256 mismatch')
            require_usable_symbol_file(candidate)
            proposal = staged.get(row['shared_symbol_key'])
            if proposal is None:
                require_shared_symbol_binding(row, candidate)
            elif proposal['sha256'] != row['asset_sha256'] or proposal['provenance']['drawing_indices'] != row['drawing_indices']:
                raise ValueError('staged symbol differs from its proposed catalog row')
            reference = _reference(doc[row['physical_page'] - 1], row, meaning)
            result = {'asset_ref': ref, 'physical_page': row['physical_page'],
                      **compare_symbol(candidate.read_bytes(), candidate.suffix, reference)}
            if proposal is not None:
                result['staged_shared_symbol'] = proposal['key']
            report.append(result)
    return report


def rebuild(output: Path) -> None:
    if output.exists():
        raise ValueError('use an unused output directory')
    manifest = json.loads((SOURCE_ROOT / 'source_manifest.json').read_text())
    for base, rows in [(SOURCE_ROOT, manifest['inputs']), (REPO_ROOT, manifest['repo_inputs'])]:
        for row in rows:
            path = (base / row['path']).resolve()
            if not path.is_relative_to(base) or not path.is_file() or file_sha256(path) != row['sha256']:
                raise ValueError('input missing or changed: ' + row['path'])
    source = json.loads((SOURCE_ROOT / 'source/en/content.json').read_text())
    if file_sha256(SOURCE_ROOT / manifest['original_source']['filename']) != source['source_sha256']:
        raise ValueError('authoritative PDF identity changed')
    approved = manifest['publication_status'] == 'operator-authorized-git-only-release'
    approval = json.loads((SOURCE_ROOT / 'source/approval.json').read_text()) if approved else None
    if approved:
        if manifest.get('staged_shared_symbols'):
            raise ValueError('staged symbols must enter the shared catalog before release')
        reviewed = [r for r in manifest['inputs'] if not r['path'].startswith('web/') and r['path'] != 'source/approval.json']
        if (approval['source_sha256'] != source['source_sha256'] or approval['verified_inputs'] != reviewed
                or approval['target'] != manifest['target'] or not approval['operator_quote']):
            raise ValueError('release authority does not cover these source inputs')
    shutil.copytree(SOURCE_ROOT / 'assets', output / 'assets')
    filename = 'manual_je1500d_us_en.md'
    _write_myst_sphinx_scaffold(output / filename, title=source['title'], presentation_profile='web')
    with (output / 'conf.py').open('a') as stream:
        # Printed straight apostrophes stay straight in MyST headings too.
        stream.write(f"\nlanguage = '{LANGUAGE}'\nsmartquotes = False\n")
    shutil.copy2(SOURCE_ROOT / 'source/geometry.css', output / '_static/source_geometry.css')
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    contract = load_web_manual_contract(model=source['model'], region=source['region'])
    pages = tuple(SourcePage(page_id=ch['id'], source_ref='native-pdf/' + ch['id'],
                             source_path='source/en/content.json#' + ch['id'], language=LANGUAGE,
                             source_sha256=value_sha256(ch), blocks=tuple(('flow', flow) for flow in ch['nodes']))
                  for ch in source['chapters'])
    specs = component_specs_in_flow([block for page in pages for _, block in page.blocks])
    metadata = {
        'projection': 'whole-document-components/v1', 'title': source['title'],
        'markdown_filename': filename, 'declared_languages': [LANGUAGE],
        'publication_eligible': approved, 'operator_source_acceptance': approval,
        'pending_source_review': [] if approved else ['Operator review of the candidate, source concerns and staged shared symbols'],
        'frozen_source_manifest': manifest,
        'source_authority': {'filename': manifest['original_source']['filename'], 'sha256': source['source_sha256'], 'physical_pages': list(range(2, 21))},
        'asset_sha256': {p.relative_to(output).as_posix(): file_sha256(p) for p in sorted((output / 'assets').rglob('*')) if p.is_file()},
        'component_registry': registry, 'component_registry_sha256': registry_sha256(registry),
        'manual_theme': theme, 'manual_theme_sha256': theme_sha256(theme),
        'web_contract': contract, 'composites': [], 'page_declarations': {},
        'frozen_stylesheet_sha256': file_sha256(output / '_static/web_manual.css'),
        'source_stylesheet': {'path': '_static/source_geometry.css', 'sha256': file_sha256(output / '_static/source_geometry.css')},
        'component_inventory': {identity: sum(s.component_id == identity for s in specs) for identity in sorted({s.component_id for s in specs})},
    }
    ir = build_manual_ir_from_source(ManualSource(model=source['model'], region=source['region'], language=LANGUAGE,
        source='prepared-document', bundle_root='frozen-source', bundle_sha256=value_sha256(source), snapshot_sha256=None,
        layout_params_sha256=value_sha256({'layout': 'web'}), style_contract_sha256=value_sha256(contract),
        pages=pages, metadata=metadata, schema_version=V2_SCHEMA_VERSION))
    validate_document(ir)
    require_prepared_document_styles(ir.to_dict(), stylesheet=(SOURCE_ROOT / 'source/geometry.css').read_text(),
                                     exceptions=manifest.get('shared_component_exceptions', ()))
    write_manual_ir(ir, output / 'manual.ir.json')
    replay_package(output)
    catalog = {row['key'] for row in json.loads(CATALOG.read_text())['assets']}
    if any(row['key'] not in catalog for row in manifest.get('staged_shared_symbols', [])):
        symbols = staged_symbol_admission(output, manifest)
    else:
        symbols = require_symbol_asset_admission(output, SOURCE_ROOT, manifest, LANGUAGE)
    print(json.dumps({'output': str(output), 'chapters': len(pages), 'components': metadata['component_inventory'], 'symbol_admission': symbols}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    rebuild(parser.parse_args().output.resolve())
