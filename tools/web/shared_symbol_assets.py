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


GROUP_STATUSES = {'operator-confirmed', 'proposed'}


def _valid_group(group: dict, decisions: dict) -> bool:
    captions = group.get('captions', {})
    if (group.get('status') not in GROUP_STATUSES
            or not isinstance(group.get('legacy_variants'), list)
            or not isinstance(captions, dict)
            or any(not isinstance(v, list) or not all(isinstance(c, str) for c in v)
                   for v in captions.values())):
        return False
    if group['status'] != 'operator-confirmed':
        return True
    decision = decisions.get(group.get('decision'))
    return (decision is not None and bool(decision.get('date'))
            and any(q.get('quote') for q in decision.get('operator_quotes', [])))


def canonical_groups() -> dict[str, tuple[dict, str]]:
    """Map each grouped shared key to ``(group, role)``; role is canonical or legacy.

    Only ``operator-confirmed`` groups change admission. ``proposed`` groups are
    recorded suggestions. A confirmed group must cite a dated decision that
    carries the operator's own words; the catalog is rejected otherwise.
    """
    _, data = _catalog()
    decisions = {d.get('id'): d for d in data.get('canonical_decisions', [])}
    assets = {r['key'] for r in data['assets']}
    index: dict[str, tuple[dict, str]] = {}
    seen: set[str] = set()
    for group in data.get('canonical_groups', []):
        gid = group.get('id')
        if not gid or gid in seen or not _valid_group(group, decisions):
            raise ValueError(f'invalid shared symbol canonical group or undated operator decision: {gid}')
        seen.add(gid)
        for key, role in [(group.get('canonical'), 'canonical'),
                          *[(k, 'legacy') for k in group['legacy_variants']]]:
            if key not in assets or key in index:
                raise ValueError(f'symbol group {gid} names unknown or doubly grouped key: {key}')
            index[key] = (group, role)
    return index


def shared_symbol_file(key: str) -> Path:
    root, data = _catalog()
    (row,) = [r for r in data['assets'] if r['key'] == key]
    return root / _safe_relative(row['path'], field='shared symbol', source=root)


def canonical_decision(decision_id: str) -> dict:
    _, data = _catalog()
    (decision,) = [d for d in data.get('canonical_decisions', []) if d.get('id') == decision_id]
    return decision
