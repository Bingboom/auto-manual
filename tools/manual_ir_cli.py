#!/usr/bin/env python3
"""Build and validate a renderer-neutral manual IR sidecar."""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.manual_ir import build_manual_ir, validate_manual_ir, write_manual_ir
from tools.utils.path_utils import Paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--lang", default="en")
    parser.add_argument("--source", default="review")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--layout-params", type=Path)
    parser.add_argument("--style-contract", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    bundle_root = args.bundle_root.resolve()
    ir = build_manual_ir(
        root=ROOT,
        bundle_root=bundle_root,
        model=args.model,
        region=args.region,
        lang=args.lang,
        source=args.source,
        data_root=args.data_root,
        layout_params_csv=args.layout_params,
        style_contract_path=args.style_contract,
    )
    issues = validate_manual_ir(ir, require_zero_skipped_raw=args.strict)
    for issue in issues:
        print(f"[manual-ir] FAIL {issue}")
    out = args.out or Paths.manual_ir_json_for(bundle_root)
    if not issues:
        write_manual_ir(ir, out)
    print(
        f"[manual-ir] {'OK' if not issues else f'{len(issues)} issue(s)'}: "
        f"pages={len(ir.pages)} blocks={ir.metadata['block_count']} "
        f"sha256={ir.content_sha256} out={out}"
    )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
