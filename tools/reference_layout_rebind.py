#!/usr/bin/env python3
"""Atomically rebind an approved reference-layout plan to a Manual IR."""
from __future__ import annotations

import argparse
import json
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
from tools.manual_ir import ManualIR, read_manual_ir  # noqa: E402
from tools.utils.path_utils import PathSegments  # noqa: E402


REGISTRY_PATH = (
    ROOT
    / PathSegments.DOCS
    / PathSegments.RENDERERS
    / PathSegments.CONTRACTS
    / PathSegments.REFERENCE_LAYOUT_REGISTRY_JSON
)


def _registered_plan_paths(registry_path: Path) -> list[Path]:
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReferenceLayoutPlanError(f"cannot read reference-layout registry {registry_path}: {exc}") from exc
    entries = registry.get("plans") if isinstance(registry, dict) else None
    if not isinstance(entries, list) or not entries:
        raise ReferenceLayoutPlanError(f"reference-layout registry has no plans: {registry_path}")
    paths: list[Path] = []
    for index, entry in enumerate(entries):
        raw_path = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ReferenceLayoutPlanError(f"reference-layout registry plan {index} has no path")
        path = Path(raw_path)
        if not path.is_absolute():
            path = ROOT / path
        paths.append(path.resolve())
    return paths


def _run_one(
    plan_path: Path,
    ir: ManualIR,
    *,
    write: bool = False,
    content_approval: dict[str, str] | None = None,
) -> tuple[bool, str]:
    try:
        result = rebind_reference_layout_plan(
            plan_path,
            ir,
            write=write,
            content_approval=content_approval,
        )
    except (OSError, ValueError, ReferenceLayoutPlanError) as exc:
        print(f"[reference-layout-rebind] ERROR: {plan_path} | {exc}")
        return False, str(exc)

    action = "WROTE" if result.wrote else "DRY-RUN OK"
    changed_identity = ",".join(result.changed_identity_fields) or "none"
    print(
        f"[reference-layout-rebind] {action}: {result.plan_path} | "
        f"source_identity={changed_identity} "
        f"page_bindings={result.changed_page_bindings} "
        f"content_reapproved={'yes' if result.content_reapproved else 'no'} "
        "composition_map=unchanged validation=passed"
    )
    return True, ""


def _run_all_registered(manual_ir: Path, registry_path: Path) -> int:
    try:
        ir = read_manual_ir(manual_ir.resolve())
        plan_paths = _registered_plan_paths(registry_path.resolve())
    except (OSError, ValueError, ReferenceLayoutPlanError) as exc:
        print(f"[reference-layout-rebind] ERROR: {exc}", file=sys.stderr)
        return 1

    passed = 0
    for plan_path in plan_paths:
        ok, _ = _run_one(plan_path, ir)
        passed += int(ok)
    failed = len(plan_paths) - passed
    print(
        f"[reference-layout-rebind] ALL-REGISTERED: plans={len(plan_paths)} "
        f"passed={passed} failed={failed} write=disabled"
    )
    return 0 if failed == 0 else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--plan",
        type=Path,
        help="approved reference-layout plan JSON to refresh",
    )
    selection.add_argument(
        "--all-registered",
        action="store_true",
        help="dry-run every plan listed in the reference-layout registry",
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
    parser.add_argument(
        "--approve-content-change",
        action="store_true",
        help="allow an operator-reviewed manual_content_sha256 change",
    )
    parser.add_argument("--approved-by", help="content-change approver")
    parser.add_argument("--approved-at", help="content approval RFC3339 timestamp")
    parser.add_argument("--approval-method", help="recorded content review method")
    parser.add_argument(
        "--registry",
        type=Path,
        default=REGISTRY_PATH,
        help="reference-layout registry JSON used by --all-registered",
    )
    args = parser.parse_args(argv)

    approval_values = (args.approved_by, args.approved_at, args.approval_method)
    if args.approve_content_change:
        if not all(value and value.strip() for value in approval_values):
            parser.error(
                "--approve-content-change requires --approved-by, "
                "--approved-at, and --approval-method"
            )
        content_approval = {
            "status": "approved",
            "approved_by": args.approved_by.strip(),
            "approved_at": args.approved_at.strip(),
            "method": args.approval_method.strip(),
        }
    else:
        if any(approval_values):
            parser.error("approval metadata requires --approve-content-change")
        content_approval = None

    if args.all_registered:
        if args.write or content_approval is not None:
            parser.error(
                "--all-registered is ordinary dry-run only; pass --plan "
                "explicitly before writing or approving content"
            )
        return _run_all_registered(args.manual_ir, args.registry)

    try:
        ir = read_manual_ir(args.manual_ir.resolve())
        ok, _ = _run_one(
            args.plan,
            ir,
            write=args.write,
            content_approval=content_approval,
        )
    except (OSError, ValueError, ReferenceLayoutPlanError) as exc:
        print(f"[reference-layout-rebind] ERROR: {exc}", file=sys.stderr)
        return 1
    if not ok:
        return 1
    if not args.write:
        print("[reference-layout-rebind] no files changed; pass --write to commit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
