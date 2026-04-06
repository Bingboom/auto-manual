from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


def parse_args(argv: list[str] | None = None, *, table_choices: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Sync structured content snapshot CSVs from Feishu/Lark base tables.")
    ap.add_argument("--config", default="config.us.yaml", help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override phase2 export root")
    ap.add_argument(
        "--table",
        action="append",
        default=[],
        choices=table_choices,
        help="Logical table id to sync; defaults to all content tables",
    )
    ap.add_argument("--dry-run", action="store_true", help="Validate and compare without writing CSV files")
    return ap.parse_args(argv)


def run_main(
    argv: list[str] | None = None,
    *,
    root: Path,
    table_choices: list[str],
    load_config_fn: Callable[[Path], dict[str, Any]],
    sync_phase2_snapshot_fn: Callable[..., Any],
    build_sync_run_output_lines_fn: Callable[[Any], list[str]],
) -> int:
    args = parse_args(argv, table_choices=table_choices)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path

    try:
        cfg = load_config_fn(config_path)
        result = sync_phase2_snapshot_fn(
            cfg=cfg,
            config_path=config_path,
            data_root=args.data_root,
            table_names=args.table,
            dry_run=args.dry_run,
        )
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"[sync-data] ERROR: {exc}", file=sys.stderr)
        return 1

    for line in build_sync_run_output_lines_fn(result):
        print(line)
    return 0
