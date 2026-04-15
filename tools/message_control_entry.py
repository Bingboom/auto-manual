from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Phase 0 dry-run resolver for Feishu message plus OpenClaw control actions."
    )
    ap.add_argument("--config", default="config.us.yaml", help="Config YAML path, used for repo context only")
    ap.add_argument("--message", required=True, help="Raw Feishu or OpenClaw user message to resolve")
    ap.add_argument("--record-id", default=None, help="Optional stable queue record_id hint")
    ap.add_argument("--document-id", default=None, help="Optional Document_ID hint")
    ap.add_argument("--document-key", default=None, help="Optional Document_Key hint")
    ap.add_argument("--model", default=None, help="Optional model hint")
    ap.add_argument("--region", default=None, help="Optional region hint")
    ap.add_argument("--lang", default=None, help="Optional language hint")
    ap.add_argument("--build-family", default=None, help="Optional Build_family hint")
    ap.add_argument("--git-ref", default=None, help="Optional Git_ref hint")
    ap.add_argument("--version", default=None, help="Optional version hint")
    ap.add_argument("--confirmed", action="store_true", help="Mark publish confirmation as already granted")
    return ap.parse_args(argv)


def run_main(
    argv: list[str] | None = None,
    *,
    root: Path,
    config_loader: Callable[[Path], dict[str, Any]],
    resolve_message_control: Callable[..., Any],
) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path

    try:
        config_loader(config_path)
        result = resolve_message_control(
            raw_message=args.message,
            repo_root=root,
            config_loader=config_loader,
            record_id=str(args.record_id or ""),
            document_id=str(args.document_id or ""),
            document_key=str(args.document_key or ""),
            model=str(args.model or ""),
            region=str(args.region or ""),
            lang=str(args.lang or ""),
            build_family=str(args.build_family or ""),
            git_ref=str(args.git_ref or ""),
            version=str(args.version or ""),
            confirmed=bool(args.confirmed),
        )
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"[message-control-dry-run] ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False, sort_keys=True))
    return 0
