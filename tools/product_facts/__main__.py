"""``python -m tools.product_facts``: build, write or check the own-product facts export.

Without ``--out`` or ``--check`` it only prints the summary and the problems. Run it from the repository whose
``docs/publish`` holds the publication (Hello-Docs); nothing is fetched and no table is written.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.product_facts.export import ASSETS, ProductFactsError, build_export, encode
from tools.utils.path_utils import repo_root


def _summary(document: dict) -> str:
    return ", ".join(f"{key} {value}" for key, value in document["summary"].items())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Own-product facts from the published Web manuals (read-only).")
    parser.add_argument("--root", type=Path, default=None, help="repository whose docs/publish to read (default: this one)")
    parser.add_argument("--assets", type=Path, default=ASSETS,
                        help="portal assets holding settings.json, product_matrix.json and the 产品分类 snapshot")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--out", type=Path, help="write the export to this file")
    target.add_argument("--check", type=Path, help="exit 1 when this file is not the current export")
    args = parser.parse_args(argv)
    try:
        document = build_export(args.root or repo_root(), args.assets)
    except (ProductFactsError, OSError, ValueError) as exc:
        print(f"ERROR   {exc}")
        return 2
    for problem in document["problems"]:
        print(f"PROBLEM {problem}")
    data = encode(document)
    if args.check:
        current = args.check.read_bytes() if args.check.is_file() else b""
        print(f"{'up to date' if current == data else 'STALE'}: {args.check} ({_summary(document)})")
        return 0 if current == data else 1
    if args.out:
        from tools.workspace_snapshot import atomic_json

        atomic_json(args.out, document)
        print(f"wrote {args.out}: {_summary(document)}")
        return 0
    print(f"dry run: {_summary(document)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
