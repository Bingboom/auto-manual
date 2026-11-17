# -*- coding: utf-8 -*-
"""CLI entrypoint for ``python -m tools.bitable_backup``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools import bitable_schema as bs
from tools.bitable_backup.sidecars import plan_and_restore_links


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Sidecar operations for Feishu Bitable content backups.")
    sub = p.add_subparsers(dest="command", required=True)
    rl = sub.add_parser(
        "restore-links",
        description="Pass-2 relational link restore by business key. Dry-run unless --write --yes.",
    )
    rl.add_argument("--backup", required=True, help="backup label dir containing links_manifest.json")
    rl.add_argument("--base-token", required=True, help="TARGET base token")
    rl.add_argument("--tables", help="comma-separated source table names (default: all)")
    rl.add_argument("--write", action="store_true", help="actually write link cells (else dry-run)")
    rl.add_argument("--yes", action="store_true", help="confirm TARGET base is correct; REQUIRED with --write")
    rl.add_argument("--lark-cli", default="lark-cli")
    rl.add_argument("--profile", help="lark-cli config profile to route through")
    rl.add_argument("--identity", default="bot", choices=["bot", "user"], help="lark-cli token identity (default: bot)")
    return p


def main(argv: list[str] | None = None) -> int:
    """Run ``tools.bitable_backup`` CLI subcommands."""
    args = _parser().parse_args(argv)
    bs._PROFILE = getattr(args, "profile", None)
    bs._IDENTITY = getattr(args, "identity", None) or "bot"
    if args.command != "restore-links":
        return 2
    write = bool(args.write and args.yes)
    if args.write and not args.yes:
        print("⚠ --write ignored: re-run with --write --yes once you've confirmed the TARGET base token.")
    tables = [t.strip() for t in args.tables.split(",") if t.strip()] if args.tables else None
    report = plan_and_restore_links(
        Path(args.backup),
        args.base_token,
        tables=tables,
        write=write,
        lark_cli=args.lark_cli,
    )
    mode = "WRITE" if write else "dry-run"
    print(
        f"RESTORE-LINKS ({mode}): planned {len(report['planned'])}, "
        f"written {len(report['written'])}, already_linked {len(report['already_linked'])}, "
        f"abstained {len(report['abstained'])}, verify_failed {len(report['verify_failed'])}, "
        f"errors {len(report['errors'])}"
    )
    for item in report["abstained"]:
        print(f"  ? ABSTAIN {item['table']}.{item['column']} ({item['primary_key_value']}): {item['reason']}")
    for item in report["verify_failed"]:
        print(f"  ✗ VERIFY_FAILED {item['table']}.{item['column']} ({item['primary_key_value']})")
    for item in report["errors"]:
        print(f"  ✗ ERROR {item['table']}.{item['column']}: {item['error']}")
    return 1 if (report["verify_failed"] or report["errors"]) else 0


if __name__ == "__main__":
    sys.exit(main())
