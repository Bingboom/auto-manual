"""CLI parsing and path/diagnostic adapters for the IDML exporter façade."""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def build_parser(description: str | None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--model", help="product model registered in the build target")
    parser.add_argument("--region", default="US")
    parser.add_argument("--lang", default="en")
    parser.add_argument(
        "--category",
        default=None,
        help=(
            "product line, from build.skeleton_family; carriers branch on it as "
            "'.. only:: category_<value>'. Left unset a carrier's category branch "
            "is simply absent, so build.py always passes the configured value."
        ),
    )
    parser.add_argument("--data-root", default="data/phase2")
    parser.add_argument("--out", default=None)
    parser.add_argument(
        "--bundle-root",
        default=None,
        help=(
            "Prepared rst bundle dir (default: "
            "docs/_build/<model>/<region>/<lang>/rst); prose pages are skipped if absent"
        ),
    )
    parser.add_argument(
        "--mode", "--idml-mode", dest="mode",
        choices=("production", "flow", "both"), default="production",
        help="IDML export mode; production preserves historical behavior.",
    )
    parser.add_argument("--check", default=None, help="validate an existing .idml and exit")
    parser.add_argument(
        "--template",
        default=None,
        help="bake production idml into this template .idml (pre-styled)",
    )
    parser.add_argument(
        "--assembly-plan",
        default=None,
        help=(
            "configured candidate target assembly JSON; approved reference "
            "contracts still take precedence"
        ),
    )
    parser.add_argument(
        "--layout-params-csv",
        default="data/layout_params.csv",
        help="baseline layout-token CSV selected by the build config",
    )
    parser.add_argument(
        "--layout-params-overlay",
        action="append",
        default=[],
        help="additive IDML composition-token CSV; may be repeated",
    )
    return parser


def resolve_input_paths(
    root: Path,
    args: argparse.Namespace,
) -> tuple[Path, Path, tuple[Path, ...]]:
    data_root = root / args.data_root if not Path(args.data_root).is_absolute() else Path(args.data_root)
    layout_params_csv = (
        root / args.layout_params_csv
        if not Path(args.layout_params_csv).is_absolute()
        else Path(args.layout_params_csv)
    )
    overlays = tuple(
        root / value if not Path(value).is_absolute() else Path(value)
        for value in args.layout_params_overlay
    )
    return data_root, layout_params_csv, overlays


def dump_prepared_bundle_debug(
    root: Path,
    bundle_root: Path,
    *,
    model: str,
    region: str,
) -> None:
    """Preserve CI prepared-page bytes after a same-source pin failure."""
    try:
        debug_root = Path(os.environ.get("GITHUB_WORKSPACE") or root)
        debug_dir = debug_root / "docs" / "_build" / model / region / "same_source_debug"
        if debug_dir.exists():
            shutil.rmtree(debug_dir)
        shutil.copytree(bundle_root / "page", debug_dir / "page")
        print(f"[export-idml] DEBUG: prepared bundle pages copied to {debug_dir}")
    except Exception as exc:  # noqa: BLE001 - diagnostics must never mask the error
        print(f"[export-idml] DEBUG: bundle dump failed: {exc}")
