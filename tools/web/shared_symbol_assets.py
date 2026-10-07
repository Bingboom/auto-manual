"""One reusable Web symbol entrypoint; withdrawn bytes stay history-only."""
from __future__ import annotations

import json
from pathlib import Path

from tools.utils.path_utils import PathSegments, get_paths
from tools.web.language_release_evidence import _safe_relative, _sha256


def _catalog() -> tuple[Path, dict]:
    paths = get_paths()
    root = paths.docs_dir / PathSegments.RENDERERS / PathSegments.WEB / PathSegments.ASSETS / 'shared' / 'symbols'
    data = json.loads((root / 'manifest.json').read_text())
    if data.get('schema_version') != 'auto-manual-shared-web-symbols/v1':
        raise ValueError('unsupported shared Web symbol catalog')
    return root, data


def require_usable_symbol_file(path: Path) -> None:
    _, data = _catalog()
    digest = _sha256(path)
    blocked = next((r for r in data['withdrawn'] if r['sha256'] == digest), None)
    if blocked:
        raise ValueError('withdrawn Web symbol bytes: ' + blocked['reason'] +
                         '; select a checked variant from shared/symbols/manifest.json')


def require_shared_symbol_binding(row: dict, path: Path) -> None:
    """Frozen copies must be byte-identical to the selected reusable variant."""
    root, data = _catalog()
    key = row['shared_symbol_key']
    matches = [r for r in data['assets'] if r['key'] == key]
    if len(matches) != 1:
        raise ValueError('symbol requires one explicit shared glyph variant')
    selected = matches[0]
    source = root / _safe_relative(selected['path'], field='shared symbol', source=root)
    if (source.is_symlink() or not source.resolve().is_relative_to(root.resolve())
            or not source.is_file() or _sha256(source) != selected['sha256']
            or _sha256(path) != selected['sha256']):
        raise ValueError('symbol must reuse shared variant bytes unchanged')
