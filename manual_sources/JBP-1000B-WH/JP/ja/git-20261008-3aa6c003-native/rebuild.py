"""Replay the source-local JP candidate through existing shared IR components.

No original PDF, live Base, phase2 registration or target-specific renderer is
needed for cold reconstruction. Source hashes and trusted applicability are
checked before any output is written.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import shutil
import sys

REPO = next(parent for parent in Path(__file__).resolve().parents if (parent / 'build.py').is_file())
sys.path.insert(0, str(REPO))

from tools.component_specs.registry import load_component_registry, registry_sha256  # noqa: E402
from tools.component_specs.theme import load_manual_theme, theme_sha256  # noqa: E402
from tools.manual_ir import ManualSource, SourcePage, V2_SCHEMA_VERSION, build_manual_ir_from_source, write_manual_ir  # noqa: E402
from tools.manual_ir.document import validate_document  # noqa: E402
from tools.manual_ir.hashing import file_sha256, value_sha256  # noqa: E402
from tools.prepared_component_coverage import audit_prepared_component_coverage  # noqa: E402
from tools.web.frozen_ai_flow import root  # noqa: E402
from tools.web.frozen_ai_web import replay_package  # noqa: E402
from tools.markdown_bundle import _write_myst_sphinx_scaffold  # noqa: E402
from tools.utils.path_utils import PathSegments  # noqa: E402
from tools.web.caption_frame_admission import require_caption_frame_admission  # noqa: E402
from tools.web.presentation import load_web_manual_contract  # noqa: E402


def rebuild(source: Path, output: Path):
    manifest = json.loads((source / 'source_manifest.json').read_text())
    actual_inputs = {str(path.relative_to(source)) for path in (source / 'source').rglob('*') if path.is_file()} | {'rebuild.py'}
    if {record['path'] for record in manifest['inputs']} != actual_inputs:
        raise ValueError('source manifest does not cover every input')
    for record in manifest['inputs']:
        path = source / record['path']
        if not path.resolve().is_relative_to(source.resolve()) or path.is_symlink():
            raise ValueError('unsafe source input: ' + record['path'])
        if file_sha256(path) != record['sha256'] or path.stat().st_size != record['size']:
            raise ValueError('frozen source input changed: ' + record['path'])
    if output.exists():
        raise ValueError('use a new candidate directory: ' + str(output))
    doc = json.loads((source / 'source/document.json').read_text())
    policy = json.loads((source / 'source/admission.json').read_text())
    if doc['target'] != policy['target']:
        raise ValueError('source identity disagrees with trusted admission')
    target = doc['target']
    if any(manifest['target'][key] != target[key] for key in ('model', 'region')):
        raise ValueError('source identity disagrees with manifest')
    if manifest['target']['languages'] != [target['language']]:
        raise ValueError('source language disagrees with manifest')
    approved = manifest.get('publication_status') == 'operator-approved-git-only-release'
    approval = None
    if approved:
        approval = json.loads((source / 'source/approval.json').read_text())
        reviewed_inputs = [record for record in manifest['inputs']
                           if record['path'].startswith('source/')
                           and record['path'] != 'source/approval.json']
        if (approval.get('target') != target
                or approval.get('original_source_sha256') != manifest['original_source']['sha256']
                or approval.get('reviewed_inputs') != reviewed_inputs
                or not approval.get('operator_quote') or not approval.get('merge_authorization')):
            raise ValueError('operator acceptance does not cover these source inputs')
    output.mkdir(parents=True)
    for path in (source / 'source/assets').iterdir():
        destination = output / 'assets' / path.name
        destination.parent.mkdir(exist_ok=True)
        shutil.copyfile(path, destination)
    filename = 'manual_jbp1000bwh_jp_ja.md'
    _write_myst_sphinx_scaffold(output / filename, title=doc['title'], presentation_profile='web')
    with (output / 'conf.py').open('a') as stream:
        stream.write("\nlanguage = 'ja'\n")
    shutil.copyfile(source / 'source/presentation.css', output / '_static/source.css')
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    contract = load_web_manual_contract(model=target['model'], region=target['region'])
    pages = tuple(SourcePage(
        page_id=p['page_id'], source_ref='ja/' + p['page_id'],
        source_path='source/document.json#' + p['page_id'], language='ja',
        source_sha256=file_sha256(source / 'source/document.json'),
        blocks=tuple(('flow', root(n)) for n in p['nodes']),
    ) for p in doc['pages'])
    metadata = {
        'projection': 'whole-document-components/v1',
        'web_source_normalization': 'native-pdf-visible-copy/v1',
        'source_stylesheet': {'path': '_static/source.css', 'sha256': file_sha256(output / '_static/source.css')},
        'title': doc['title'], 'markdown_filename': filename,
        'publication_eligible': approved,
        'pending_source_review': [] if approved else [
            'Candidate requires operator acceptance and separate merge/release authorization.'
        ],
        'operator_source_acceptance': approval,
        'declared_languages': ['ja'], 'frozen_source_manifest': manifest,
        'asset_sha256': {str(p.relative_to(output)): file_sha256(p) for p in (output / 'assets').iterdir()},
        'component_registry': registry, 'component_registry_sha256': registry_sha256(registry),
        'manual_theme': theme, 'manual_theme_sha256': theme_sha256(theme),
        'web_contract': contract, 'composites': [], 'page_declarations': {},
        'page_slots': {p['page_id']: p['page_id'] for p in doc['pages']},
        'frozen_stylesheet_sha256': file_sha256(output / '_static/web_manual.css'),
        'source_page_map': {p['page_id']: p['physical_pages'] for p in doc['pages']},
    }
    source_input = ManualSource(**target, source='prepared-document', bundle_root='frozen-source',
        bundle_sha256=value_sha256(manifest), snapshot_sha256=None,
        layout_params_sha256=value_sha256({'layout': 'web'}),
        style_contract_sha256=value_sha256(contract), pages=pages,
        metadata=metadata, schema_version=V2_SCHEMA_VERSION)
    ir = build_manual_ir_from_source(source_input)
    validate_document(ir)
    report = audit_prepared_component_coverage(ir.to_dict(), policy)
    if report['issues']:
        raise ValueError('shared source admission failed: ' + '; '.join(report['issues']))
    ir = replace(ir, metadata={**ir.metadata, 'shared_component_coverage': report})
    write_manual_ir(ir, output / PathSegments.MANUAL_IR_JSON)
    caption_report = require_caption_frame_admission(output)
    (output / 'caption-frame-report.json').write_text(json.dumps(caption_report, ensure_ascii=False, indent=2) + '\n')
    replay_package(output)
    (output / 'admission-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(rebuild(args.source, args.output), ensure_ascii=False, indent=2))
