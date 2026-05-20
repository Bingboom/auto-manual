from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable


def run_bundle_entry(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    load_config: Callable[[Path], dict],
    materialize_bundle: Callable[..., Any],
    printer: Callable[[str], None] = print,
) -> None:
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = repo_root / cfg_path

    cfg = load_config(cfg_path)

    doc_type = cfg.get("doc_type", "manual_bundle")
    if doc_type != "manual_bundle":
        raise RuntimeError(f"gen_index_bundle supports doc_type=manual_bundle only, got: {doc_type}")

    bundle = materialize_bundle(
        cfg,
        model=args.model,
        region=args.region,
        lang=getattr(args, "lang", None),
        data_root=args.data_root,
    )
    printer(f"[gen_index_bundle] Wrote bundle index: {bundle.index_path}")
    printer(f"[gen_index_bundle] Wrote wrapper index: {bundle.wrapper_index_path}")
