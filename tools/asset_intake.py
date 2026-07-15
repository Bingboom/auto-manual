#!/usr/bin/env python3
"""Package a PDF-compatible design master through a strict asset recipe."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.asset_pipeline import AssetIntakeError, load_recipe, run_intake
from tools.asset_pipeline.package import result_summary


def _resolve_path(value: str | Path, *, repo_root: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def run_asset_intake(args: argparse.Namespace, *, repo_root: Path) -> None:
    """Stable dispatcher entrypoint used by the repository's asset action."""

    if getattr(args, "asset_promote", False):
        raise AssetIntakeError(
            "asset promotion is not implemented; intake is package-only and never edits the worktree"
        )
    recipe_path = _resolve_path(args.asset_recipe, repo_root=repo_root)
    source_path = _resolve_path(args.asset_source_file, repo_root=repo_root)
    output_root = _resolve_path(args.asset_output_root, repo_root=repo_root)
    recipe = load_recipe(recipe_path)
    requested_source_key = str(args.asset_source_key).strip()
    if requested_source_key != recipe.source.source_key:
        raise AssetIntakeError(
            "asset source key mismatch: "
            f"recipe declares {recipe.source.source_key!r}, got {requested_source_key!r}"
        )
    result = run_intake(
        source_path=source_path,
        recipe=recipe,
        output_root=output_root,
    )
    print(json.dumps(result_summary(result), ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-source-key", required=True)
    parser.add_argument("--asset-source-file", required=True, type=Path)
    parser.add_argument("--asset-recipe", required=True, type=Path)
    parser.add_argument("--asset-output-root", required=True, type=Path)
    parser.add_argument(
        "--asset-promote",
        action="store_true",
        help="Reserved fail-closed flag; promotion is not part of this package-only stage.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run_asset_intake(args, repo_root=Path(__file__).resolve().parents[1])
    except AssetIntakeError as exc:
        print(f"[asset_intake] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
