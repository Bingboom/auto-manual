from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Consume Review-init rows and start review / seed draft branches and PRs.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override phase2 snapshot root for review seeding")
    ap.add_argument("--dry-run", action="store_true", help="List pending rows without creating branches or PRs")
    ap.add_argument("--record-id", default=None, help="Only consume one Review-init record_id")
    return ap.parse_args(argv)


def run_main(
    argv: list[str] | None = None,
    *,
    root: Path,
    load_config_fn: Callable[[Path], dict[str, Any]],
    resolve_phase2_export_root_fn: Callable[..., Path],
    process_review_start_queue_fn: Callable[..., int],
) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    cfg = load_config_fn(config_path)
    resolved_data_root = str(
        resolve_phase2_export_root_fn(
            cfg,
            repo_root=root,
            data_root=args.data_root,
        )
    )
    return process_review_start_queue_fn(
        cfg=cfg,
        config_path=config_path,
        data_root=resolved_data_root,
        dry_run=args.dry_run,
        record_id=args.record_id,
    )
