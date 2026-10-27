"""Replay the JE-1000D US text-layer transcription through the shared Web components.

The source-local input package is immutable. Use a new --output directory.
No live source, queue, asset or link service is read or written.
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
from tools.web.symbol_asset_admission import require_symbol_asset_admission  # noqa: E402


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
        reviewed = [r for r in manifest['inputs'] if not r['path'].startswith('web/') and r['path'] != 'source/approval.json']
        if (approval['source_sha256'] != source['source_sha256'] or approval['verified_inputs'] != reviewed
                or approval['target'] != manifest['target'] or not approval['operator_quote']):
            raise ValueError('release authority does not cover these source inputs')
    shutil.copytree(SOURCE_ROOT / 'assets', output / 'assets')
    filename = 'manual_je1000d_us_en.md'
    _write_myst_sphinx_scaffold(output / filename, title=source['title'], presentation_profile='web')
    with (output / 'conf.py').open('a') as stream:
        stream.write("\nlanguage = 'en'\nsmartquotes = False\n")
    shutil.copy2(SOURCE_ROOT / 'source/geometry.css', output / '_static/source_geometry.css')
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    contract = load_web_manual_contract(model=source['model'], region=source['region'])
    pages = tuple(SourcePage(page_id=ch['id'], source_ref='native-pdf/' + ch['id'],
                             source_path='source/en/content.json#' + ch['id'], language='en',
                             source_sha256=value_sha256(ch), blocks=tuple(('flow', flow) for flow in ch['nodes']))
                  for ch in source['chapters'])
    specs = component_specs_in_flow([block for page in pages for _, block in page.blocks])
    metadata = {
        'projection': 'whole-document-components/v1', 'title': source['title'],
        'markdown_filename': filename, 'declared_languages': ['en'],
        'publication_eligible': approved, 'operator_source_acceptance': approval,
        'pending_source_review': [] if approved else ['Local source parity and browser validation in progress'],
        'frozen_source_manifest': manifest,
        'source_authority': {'filename': manifest['original_source']['filename'], 'sha256': source['source_sha256'], 'physical_pages': list(range(2, 14))},
        'asset_sha256': {p.relative_to(output).as_posix(): file_sha256(p) for p in sorted((output / 'assets').rglob('*')) if p.is_file()},
        'component_registry': registry, 'component_registry_sha256': registry_sha256(registry),
        'manual_theme': theme, 'manual_theme_sha256': theme_sha256(theme),
        'web_contract': contract, 'composites': [], 'page_declarations': {},
        'frozen_stylesheet_sha256': file_sha256(output / '_static/web_manual.css'),
        'source_stylesheet': {'path': '_static/source_geometry.css', 'sha256': file_sha256(output / '_static/source_geometry.css')},
        'component_inventory': {identity: sum(s.component_id == identity for s in specs) for identity in sorted({s.component_id for s in specs})},
    }
    ir = build_manual_ir_from_source(ManualSource(model=source['model'], region=source['region'], language='en',
        source='prepared-document', bundle_root='frozen-source', bundle_sha256=value_sha256(source), snapshot_sha256=None,
        layout_params_sha256=value_sha256({'layout': 'web'}), style_contract_sha256=value_sha256(contract),
        pages=pages, metadata=metadata, schema_version=V2_SCHEMA_VERSION))
    validate_document(ir)
    require_prepared_document_styles(ir.to_dict(), stylesheet=(SOURCE_ROOT / 'source/geometry.css').read_text(),
                                     exceptions=manifest.get('shared_component_exceptions', ()))
    write_manual_ir(ir, output / 'manual.ir.json')
    replay_package(output)
    symbols = require_symbol_asset_admission(output, SOURCE_ROOT, manifest, 'en')
    print(json.dumps({'output': str(output), 'chapters': len(pages), 'components': metadata['component_inventory'], 'symbol_admission': symbols}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    rebuild(parser.parse_args().output.resolve())
