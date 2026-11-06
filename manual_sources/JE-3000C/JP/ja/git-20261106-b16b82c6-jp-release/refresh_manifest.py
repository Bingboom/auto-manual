"""Bind this release's source manifest to its exact inputs.

Run from the repository root after ``derive_release.py``. It keeps the draft's
source identity and component evidence, records the operator's release
decisions, re-pins the shared repository inputs at the current commit, binds
every symbol-table row to its source glyph and shared asset, and rewrites the
input inventory.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parent
REPO = next(p for p in PACKAGE.parents if (p / 'build.py').is_file())
sys.path.insert(0, str(REPO))

from tools.web.language_release_evidence import _file_inventory  # noqa: E402
from tools.web.shared_symbol_assets import shared_symbol_file  # noqa: E402
import tools.web.symbol_asset_admission as admission  # noqa: E402

DRAFT = PACKAGE.parent / 'git-20261019-b16b82c6-jp-native'
MANIFEST = PACKAGE / 'source_manifest.json'
TABLE_PDF_SHA256 = 'b01379c09e5f51ebb0d05190192272a81e4ea7a96a468d79f5f155f93d056e86'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def library_key(path: Path) -> str:
    catalog = json.loads((REPO / 'docs/renderers/web/assets/shared/symbols/manifest.json').read_text())
    digest = sha256(path)
    keys = [row['key'] for row in catalog['assets'] if row['sha256'] == digest
            and sha256(shared_symbol_file(row['key'])) == digest]
    if len(keys) != 1:
        raise ValueError('symbol asset must match exactly one shared library entry: ' + path.name)
    return keys[0]


def main() -> None:
    manifest = json.loads((DRAFT / 'source_manifest.json').read_text(encoding='utf-8'))
    manifest['target']['technical_version'] = PACKAGE.name
    manifest['original_source']['filename'] = 'source/original.pdf'
    manifest['feishu_source'] = {
        'base': 'WGVwb2HctauRi7sEiKqcIzTRn1c',
        'table': 'tblGNcwO9pwxGO5s (说明书物料编码)',
        'record_id': 'reczz28SOwwEiFsd',
        'child_material_code': '16-0102-000341',
        'project': 'HTE156',
        'parent_material_code': '21-0001-000424',
        'attachment_name': '16-0102-000341 竖版竖版说明书 HTE1563000A-JP-JAK.pdf',
        'attachment_size': 7465254,
        'attachment_sha256': TABLE_PDF_SHA256,
        'equivalence': 'All 26 pages have identical extracted text and identical 50 dpi renders to '
                       'source/original.pdf (b16b82c6...); the files differ only in non-visible bytes. '
                       'The operator confirmed it is the same manual.',
    }
    manifest['route'] = 'JE-3000C/JP/ja/md'
    manifest['legacy_default'] = True
    manifest['revision_of'] = 'manual_sources/JE-3000C/JP/ja/git-20261019-b16b82c6-jp-native'
    manifest['operator_instruction'] = ('2026-11-06: 「只转这个 16-0102-000341 竖版竖版说明书 HTE1563000A-JP-JAK.pdf」'
                                        '「你直接把旧草稿发布了」「我来做视觉验收」; after reviewing the 1280/390 '
                                        'renders: 「2，上线提交发布：JE-3000C」')
    manifest['publication_status'] = 'operator-approved-git-only-release'
    manifest['publication_eligible'] = True
    manifest['pending_source_review'] = []
    manifest['source_errata'] = json.loads(
        (PACKAGE / 'web/ja/manual.ir.json').read_text(encoding='utf-8'))['metadata']['source_errata']
    manifest['validation_boundary'] = ('Draft content, layout and artwork unchanged except six symbol-table rows '
                                       'rebound to operator-confirmed canonicals and the approved footnote '
                                       'completion; strict Sphinx, cold replay, component, caption-frame and '
                                       'symbol admission pass; operator visual acceptance of 1280/390 renders.')
    manifest['repo_inputs'] = [{'path': row['path'], 'sha256': sha256(REPO / row['path'])}
                               for row in manifest['repo_inputs']]
    bindings = json.loads((PACKAGE / 'source/symbol-bindings.json').read_text(encoding='utf-8'))
    rows = []
    for row in bindings['rows']:
        asset = PACKAGE / 'web/ja' / row['asset_ref']
        rows.append({**row, 'asset_sha256': sha256(asset), 'shared_symbol_key': library_key(asset)})
    manifest['symbol_asset_admission'] = {'schema_version': admission.SCHEMA, 'locales': {'ja': rows}}
    report = admission.require_symbol_asset_admission(PACKAGE / 'web/ja', PACKAGE, manifest, 'ja')
    for row, result in zip(rows, report, strict=True):
        row.update({key: result[key] for key in ('max_mean_channel_error', 'canonical_group',
                                                 'canonical_decision') if key in result})
    manifest['inputs'] = []
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    manifest['inputs'] = list(_file_inventory(PACKAGE, excluded_roots=(MANIFEST,)))
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
