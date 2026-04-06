from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.validate_spec_master_runtime import collect_spec_master_validation_issues
from tools.validate_spec_master_shared import ROOT, _repo_relative


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Validate target-bound Spec_Master selectors used by the manual pipeline.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    ap.add_argument("--model", default=None, help="Single target model override")
    ap.add_argument("--region", default=None, help="Single target region override")
    ap.add_argument("--all-targets", action="store_true", help="Validate all build targets from the config")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path

    try:
        issues = collect_spec_master_validation_issues(
            cfg_path=cfg_path,
            model=args.model,
            region=args.region,
            all_targets=args.all_targets,
            data_root=args.data_root,
        )
    except RuntimeError as exc:
        print(f"[validate_spec_master] ERROR: {exc}", file=sys.stderr)
        return 1

    if issues:
        for issue in issues:
            target_bits = [bit for bit in (issue.model, issue.region) if bit]
            target_text = "/".join(target_bits) if target_bits else "_shared/_default"
            lang_text = f" lang={issue.lang}" if issue.lang else ""
            path_text = f" path={_repo_relative(issue.path)}" if issue.path else ""
            line_text = f" line={issue.line}" if issue.line is not None else ""
            print(f"[validate_spec_master] {issue.code} target={target_text}{lang_text}{path_text}{line_text}: {issue.message}")
        print(f"[validate_spec_master] FAILED with {len(issues)} issue(s)", file=sys.stderr)
        return 1

    print("[validate_spec_master] OK")
    return 0
