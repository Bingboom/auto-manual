"""Replay the hash-pinned Japanese source flow with the shared Web consumer.

Run from the repository root with --output pointing to a new directory.
No phase2, queue, network, or online-table access is involved.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys

PACKAGE = Path(__file__).resolve().parent
REPO = next(p for p in PACKAGE.parents if (p / 'build.py').is_file())
sys.path.insert(0, str(REPO))

from tools.component_specs.registry import load_component_registry, registry_sha256
from tools.component_specs.theme import load_manual_theme, theme_sha256
from tools.manual_ir import V2_SCHEMA_VERSION, build_manual_ir_from_source, write_manual_ir
from tools.manual_ir.components import component_specs_in_flow
from tools.manual_ir.document import validate_document
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.manual_ir.source import ManualSource, SourcePage
from tools.markdown_bundle import _write_myst_sphinx_scaffold
from tools.web.frozen_ai_web import replay_package
from tools.web.prepared_style_audit import require_prepared_document_styles
from tools.web.presentation import load_web_manual_contract


def assemble(output: Path) -> dict:
    manifest = json.loads((PACKAGE / 'source_manifest.json').read_text())
    for entry in manifest['inputs']:
        # Frozen inputs are verified before any output is created.
        if (entry['path'].startswith('web/') and not entry['path'].startswith('web/ja/assets/')) or entry['path'].startswith('validation/'):
            continue
        path = PACKAGE / entry['path']
        if path.stat().st_size != entry['size'] or file_sha256(path) != entry['sha256']:
            raise ValueError('frozen input changed: ' + entry['path'])
    for entry in manifest['repo_inputs']:
        if file_sha256(REPO / entry['path']) != entry['sha256']:
            raise ValueError('shared input drift: ' + entry['path'])
    source = json.loads((PACKAGE / 'source/document.json').read_text())
    if file_sha256(PACKAGE / 'source/original.pdf') != source['source_sha256']:
        raise ValueError('original PDF identity changed')
    if output.exists():
        raise ValueError('output must be a new directory')
    output.mkdir(parents=True)
    shutil.copytree(PACKAGE / 'web/ja/assets', output / 'assets')
    filename = 'manual_je2000e_jp_ja.md'
    _write_myst_sphinx_scaffold(output / filename, title='Jackery ポータブル電源 2000 Plus', presentation_profile='web')
    with (output / 'conf.py').open('a') as stream:
        stream.write("\nlanguage = 'ja'\n")
    shutil.copyfile(PACKAGE / 'source/geometry.css', output / '_static/source_geometry.css')
    target = source['target']
    contract = load_web_manual_contract(model=target['model'], region=target['region'])
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    pages = tuple(SourcePage(**{k: v for k, v in page.items() if k != 'physical_pages'}) for page in source['pages'])
    specs = component_specs_in_flow([payload for page in pages for _, payload in page.blocks])
    assets = {path.relative_to(output).as_posix(): file_sha256(path) for path in (output / 'assets').rglob('*') if path.is_file()}
    metadata = {
        'projection': 'whole-document-components/v1',
        'web_source_normalization': 'preface-auto-resume/v1',
        'title': 'Jackery ポータブル電源 2000 Plus',
        'markdown_filename': filename,
        'declared_languages': ['ja'],
        'publication_eligible': False,
        'publication_status': 'candidate-pending-operator-review',
        'original_source_sha256': source['source_sha256'],
        'asset_sha256': assets,
        'component_registry': registry,
        'component_registry_sha256': registry_sha256(registry),
        'manual_theme': theme,
        'manual_theme_sha256': theme_sha256(theme),
        'web_contract': contract,
        'composites': [],
        'page_declarations': {},
        'source_stylesheet': {'path': '_static/source_geometry.css', 'sha256': file_sha256(output / '_static/source_geometry.css')},
        'component_inventory': dict(sorted(Counter(s.component_id for s in specs).items())),
        'frozen_stylesheet_sha256': file_sha256(output / '_static/web_manual.css'),
        'source_page_map': {p['page_id']: p['physical_pages'] for p in source['pages']},
    }
    manual_source = ManualSource(
        **target, source='prepared-document', bundle_root='frozen-source',
        bundle_sha256=value_sha256(source), snapshot_sha256=None,
        layout_params_sha256=value_sha256({'layout': 'web'}),
        style_contract_sha256=value_sha256(contract), pages=pages,
        metadata=metadata, schema_version=V2_SCHEMA_VERSION,
    )
    ir = build_manual_ir_from_source(manual_source)
    validate_document(ir)
    style = require_prepared_document_styles(ir.to_dict(), stylesheet=(PACKAGE / 'source/geometry.css').read_text(), exceptions=manifest.get('shared_component_exceptions', []))
    write_manual_ir(ir, output / 'manual.ir.json')
    replay_package(output)
    return {'components': metadata['component_inventory'], 'assets': len(assets), 'style_admission': style}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(assemble(args.output), ensure_ascii=False, indent=2))
