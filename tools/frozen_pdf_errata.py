"""Apply operator-approved, exact-field errata before shared component mapping."""
from copy import deepcopy


def apply_native_errata(data, ledger, language, source_sha256):
    result = deepcopy(data)
    seen = set()
    for entry in ledger.get('entries', []):
        bindings = entry.get('native_bindings', [])
        if entry.get('locale') != language or not bindings:
            continue
        if (entry.get('status') != 'operator-approved'
                or not entry.get('operator_decision')
                or entry.get('source_sha256') != source_sha256):
            raise ValueError('native erratum requires approval and matching source SHA-256')
        for binding in bindings:
            path = binding['path']
            identity = tuple(path)
            if (not path or path[0] not in {'source', 'records'}
                    or path[-1] == 'raw_text' or identity in seen):
                raise ValueError('unsupported or duplicate native erratum field')
            seen.add(identity)
            target = result
            try:
                for key in path[:-1]:
                    target = target[key]
                before = target[path[-1]]
            except (KeyError, IndexError, TypeError) as exc:
                raise ValueError('native erratum field no longer exists') from exc
            after = binding['corrected_text']
            if (not isinstance(before, str) or before != binding['source_text']
                    or not isinstance(after, str) or not after or before == after):
                raise ValueError('native erratum exact source text changed')
            target[path[-1]] = after
            result['provenance']['corrections_applied'].append({
                'erratum_id': entry['id'], 'field': '/'.join(map(str, path)),
                'physical_page': binding['physical_page'], 'before': before,
                'after': after, 'reason': entry['reason'],
                'operator_decision': entry['operator_decision'],
            })
    return result
