from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable


def run_check_entry(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    collect_check_issues: Callable[..., list[Any]],
    repo_relative: Callable[[Path | None], str],
    printer: Callable[[str], None] = print,
    error_printer: Callable[[str], None] | None = None,
) -> int:
    error_out = error_printer or (lambda message: print(message, file=sys.stderr))

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = repo_root / cfg_path

    docs_build_dir = None
    if isinstance(args.docs_build_dir, str) and args.docs_build_dir.strip():
        docs_build_dir = Path(args.docs_build_dir.strip())
        if not docs_build_dir.is_absolute():
            docs_build_dir = repo_root / docs_build_dir

    try:
        issues = collect_check_issues(
            cfg_path=cfg_path,
            model=args.model,
            region=args.region,
            lang=getattr(args, "lang", None),
            all_targets=args.all_targets,
            data_root=args.data_root,
            docs_build_dir=docs_build_dir,
        )
    except RuntimeError as exc:
        error_out(f"[check] ERROR: {exc}")
        return 1

    if issues:
        for issue in issues:
            target_bits = [bit for bit in (issue.model, issue.region) if bit]
            target_text = "/".join(target_bits) if target_bits else "_shared/_default"
            lang_text = f" lang={issue.lang}" if issue.lang else ""
            path_text = f" path={repo_relative(issue.path)}" if issue.path else ""
            printer(f"[check] {issue.code} target={target_text}{lang_text}{path_text}: {issue.message}")
        error_out(f"[check] FAILED with {len(issues)} issue(s)")
        return 1

    printer("[check] OK")
    return 0
