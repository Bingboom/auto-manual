#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.diff_report_fields import (  # noqa: E402
    collect_field_diff_rows,
    collect_page_diff_rows,
    derive_lang_from_page_key,
    load_config,
    resolve_data_path,
    resolve_spec_paths,
)
from tools.diff_report_git import (  # noqa: E402
    build_report_base_name,
    collect_diff_rows,
    detect_initial_baseline,
    extract_bundle_fields,
    git_show_text,
    git_tree_has_entries,
    parse_name_status,
    parse_numstat,
    pathspec_from_root,
    run_git,
    sanitize_token,
)
from tools.diff_report_models import (  # noqa: E402
    DiffRow,
    FieldDiffRow,
    FieldEntry,
    GeneratedReports,
    PageDiffRow,
    PlaceholderValueSource,
    ResolvedFieldEntry,
    SpecFieldSource,
)
from tools.diff_report_render import write_csv_report, write_html_report, write_index_report  # noqa: E402
from tools.diff_report_reports import generate_diff_report  # noqa: E402


def resolve_path_from_root(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (ROOT / path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Export git diff under a tracked docs subtree to CSV/HTML.")
    ap.add_argument("--tracked-root", default="docs/_review/JE-1000F", help="Tracked subtree root")
    ap.add_argument("--config", default="config.us.yaml", help="Config YAML path for resolving source CSV metadata")
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    ap.add_argument("--from-ref", default="HEAD~1", help="Git from ref")
    ap.add_argument("--to-ref", default="HEAD", help="Git to ref")
    ap.set_defaults(ignore_initial_adds=True)
    ap.add_argument(
        "--ignore-initial-adds",
        dest="ignore_initial_adds",
        action="store_true",
        help="When the tracked subtree is first introduced, ignore the initial all-Added diff rows in generated reports (default)",
    )
    ap.add_argument(
        "--include-initial-adds",
        dest="ignore_initial_adds",
        action="store_false",
        help="When the tracked subtree is first introduced, keep the initial all-Added diff rows in generated reports",
    )
    ap.add_argument(
        "--output-dir",
        default="reports/version_tracking/JE-1000F",
        help="Output directory for CSV/HTML reports",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tracked_root = resolve_path_from_root(args.tracked_root)
    config_path = resolve_path_from_root(args.config)
    output_dir = resolve_path_from_root(args.output_dir)
    try:
        raw_file_rows = collect_diff_rows(
            repo_root=ROOT,
            tracked_root=tracked_root,
            from_ref=args.from_ref,
            to_ref=args.to_ref,
        )
        is_initial_baseline = detect_initial_baseline(
            repo_root=ROOT,
            tracked_root=tracked_root,
            from_ref=args.from_ref,
            to_ref=args.to_ref,
            file_rows=raw_file_rows,
        )
        legacy_csv, legacy_html = generate_diff_report(
            repo_root=ROOT,
            tracked_root=tracked_root,
            from_ref=args.from_ref,
            to_ref=args.to_ref,
            output_dir=output_dir,
            config_path=config_path,
            data_root=args.data_root,
            ignore_initial_adds=args.ignore_initial_adds,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or str(exc), file=sys.stderr)
        return exc.returncode or 1

    base_name = build_report_base_name(tracked_root, args.from_ref, args.to_ref)
    if is_initial_baseline:
        print(
            "[diff_report] NOTE: Initial baseline detected under "
            f"{tracked_root}. All Added rows are expected because the subtree did not exist at {args.from_ref}."
        )
        if args.ignore_initial_adds:
            print("[diff_report] NOTE: Initial Added rows were excluded by default. Pass --include-initial-adds to keep them.")
    print(f"[diff_report] FILES CSV: {output_dir / f'{base_name}_files.csv'}")
    print(f"[diff_report] FILES HTML: {output_dir / f'{base_name}_files.html'}")
    print(f"[diff_report] PAGES CSV: {output_dir / f'{base_name}_pages.csv'}")
    print(f"[diff_report] PAGES HTML: {output_dir / f'{base_name}_pages.html'}")
    print(f"[diff_report] FIELDS CSV: {output_dir / f'{base_name}_fields.csv'}")
    print(f"[diff_report] FIELDS HTML: {output_dir / f'{base_name}_fields.html'}")
    print(f"[diff_report] INDEX HTML: {output_dir / f'{base_name}_index.html'}")
    print(f"[diff_report] CSV: {legacy_csv}")
    print(f"[diff_report] HTML: {legacy_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
