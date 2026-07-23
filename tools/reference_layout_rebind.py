#!/usr/bin/env python3
"""Atomically rebind an approved reference-layout plan to a Manual IR."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.idml.reference_layout_plan import ReferenceLayoutPlanError  # noqa: E402
from tools.idml.reference_layout_rebind import rebind_reference_layout_plan  # noqa: E402
from tools.manual_ir import read_manual_ir  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan",
        type=Path,
        required=True,
        help="approved reference-layout plan JSON to refresh",
    )
    parser.add_argument(
        "--manual-ir",
        type=Path,
        required=True,
        help="validated manual.ir.json supplying the new binding",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="atomically replace the plan after validation (default: dry-run)",
    )
    args = parser.parse_args(argv)

    try:
        ir = read_manual_ir(args.manual_ir.resolve())
        result = rebind_reference_layout_plan(
            args.plan,
            ir,
            write=args.write,
        )
    except (OSError, ValueError, ReferenceLayoutPlanError) as exc:
        print(f"[reference-layout-rebind] ERROR: {exc}", file=sys.stderr)
        return 1

    action = "WROTE" if result.wrote else "DRY-RUN OK"
    changed_identity = ",".join(result.changed_identity_fields) or "none"
    print(
        f"[reference-layout-rebind] {action}: {result.plan_path} | "
        f"source_identity={changed_identity} "
        f"page_bindings={result.changed_page_bindings} "
        "composition_map=unchanged validation=passed"
    )
    if not result.wrote:
        print("[reference-layout-rebind] no files changed; pass --write to commit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
