#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Source document intake helpers.

MVP scope: read a structured Markdown/Feishu document, extract source-table
candidates, and optionally emit approval-gated source-table change requests for
existing rows. Live writes remain owned by ``tools/cloud_doc_backport.py
apply-source-table`` / ``tools.source_table_sync``.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.source_intake_extract import read_input_text  # noqa: E402
from tools.source_intake_runtime import (  # noqa: E402
    enrich_candidates_with_snapshot,
    extract_candidates_from_text,
    write_intake_outputs,
)
from tools.utils.path_utils import get_paths  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert source specs/manual tables into reviewable source-table candidates.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser(
        "run",
        description=(
            "Extract candidates and, when --data-root is provided, emit source-table "
            "change requests for existing-row updates."
        ),
    )
    run.add_argument("--input", required=True, help="Markdown file, stdin '-', or Feishu/Lark doc URL")
    run.add_argument("--document-key", required=True, help="Target document key, e.g. JE-2000F_EU")
    run.add_argument("--source-lang", default="en", help="Source language code; default: en")
    run.add_argument("--version", default="", help="Optional source version carried onto candidates")
    run.add_argument("--data-root", help="Optional phase2 snapshot root used to classify create/update/noop")
    run.add_argument("--out", help="Output directory; defaults to reports/source_intake/<run-id>")
    run.add_argument("--run-id", default="source-intake-local", help="Stable run id for report paths")
    run.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary when --input is a cloud doc")
    return parser


def _default_out_dir(run_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in run_id).strip(".-")
    return get_paths().source_intake_reports_dir / (safe or "source-intake-local")


def _run(args: argparse.Namespace) -> int:
    data_root = Path(args.data_root).resolve() if args.data_root else None
    out_dir = Path(args.out).resolve() if args.out else _default_out_dir(str(args.run_id or "source-intake-local"))
    try:
        text = read_input_text(args.input, lark_cli=args.lark_cli)
        candidates = extract_candidates_from_text(
            text,
            document_key=str(args.document_key or "").strip(),
            source_lang=str(args.source_lang or "en").strip() or "en",
            version=str(args.version or "").strip(),
        )
        if data_root is not None:
            candidates = enrich_candidates_with_snapshot(candidates, data_root=data_root)
        paths = write_intake_outputs(
            out_dir=out_dir,
            candidates=candidates,
            run_id=str(args.run_id or "source-intake-local"),
            source=str(args.input),
            document_key=str(args.document_key),
            data_root=data_root,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"source-intake: {exc}", file=sys.stderr)
        return 2

    for label, path in sorted(paths.items()):
        print(f"WROTE {label} {path}")
    print(f"CANDIDATES {len(candidates)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
