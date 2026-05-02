from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable


def run_main(
    argv: list[str] | None = None,
    *,
    parse_args: Callable[[list[str] | None], argparse.Namespace],
    repo_root: Path,
    load_config: Callable[[Path], dict[str, Any]],
    resolve_phase2_export_root: Callable[..., Path],
    process_build_queue: Callable[..., int],
) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    cfg = load_config(config_path)
    resolved_data_root = str(
        resolve_phase2_export_root(
            cfg,
            repo_root=repo_root,
            data_root=args.data_root,
        )
    )
    try:
        return process_build_queue(
            cfg=cfg,
            config_path=config_path,
            data_root=resolved_data_root,
            dry_run=bool(args.dry_run),
            force_phase2_refresh=bool(getattr(args, "force_phase2_refresh", False)),
            workflow_action=args.workflow_action,
            doc_phase=args.doc_phase,
            record_id=(args.record_id or "").strip() or None,
        )
    except RuntimeError as exc:
        print(f"[build-queue] ERROR: {exc}", file=sys.stderr)
        return 1
