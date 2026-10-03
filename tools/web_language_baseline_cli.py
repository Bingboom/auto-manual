"""Review-only CLI: generate, compare or bind existing IR; never approve it."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

from tools.manual_ir import read_manual_ir
from tools.manual_ir.hashing import file_sha256
from tools.web_language_baseline import (
    audit_language_baseline, baseline_trial, candidate_language_baseline, review_digest,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('candidate', 'trial', 'audit', 'bind'))
    parser.add_argument('--ir', type=Path, required=True)
    parser.add_argument('--record', type=Path, help='Existing reviewed baseline JSON')
    parser.add_argument('--mapping', type=Path, help='Explicit page_map and component_map JSON')
    parser.add_argument('--source', type=Path, help='Original English AI/PDF (candidate only)')
    parser.add_argument('--revision', help='Candidate review revision')
    parser.add_argument('--output', type=Path, required=True, help='New output file; never overwritten')
    args = parser.parse_args(argv)
    raw = read_manual_ir(args.ir).to_dict()
    root = args.ir.parent
    if args.action == 'candidate':
        if not all((args.mapping, args.source, args.revision)):
            parser.error('candidate requires --mapping, --source and --revision')
        mapping = json.loads(args.mapping.read_text())
        result = candidate_language_baseline(raw, root, revision=args.revision,
                                            source_sha256=file_sha256(args.source), **mapping)
        result['review_sha256'] = review_digest(result)
    else:
        if not args.record:
            parser.error('--record is required')
        entry = json.loads(args.record.read_text())
        if args.action == 'trial':
            if not args.mapping:
                parser.error('trial requires --mapping')
            result = baseline_trial(raw, root, entry, **json.loads(args.mapping.read_text()))
        else:
            candidate = deepcopy(raw)
            if args.action == 'bind':
                candidate['metadata']['language_baseline'] = {
                    'revision': entry['revision'], 'sha256': entry['structure_sha256'],
                }
            result = audit_language_baseline(candidate, root, entry)
            if args.action == 'bind' and not result['issues']:
                result = candidate
    # Exclusive create preserves existing review records and generated artifacts.
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return 1 if result.get('issues') else 0


if __name__ == '__main__':
    raise SystemExit(main())
