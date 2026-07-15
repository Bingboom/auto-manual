"""Single build-entry façade for asset registry checks and AI intake."""

from __future__ import annotations

import argparse
from pathlib import Path

from tools.asset_intake import run_asset_intake
from tools.asset_registry import run_asset_check

_INTAKE_REQUIRED_ARGS = (
    ("asset_source_key", "--asset-source-key"),
    ("asset_source_file", "--asset-source-file"),
    ("asset_recipe", "--asset-recipe"),
    ("asset_output_root", "--asset-output-root"),
)


def _missing_intake_flags(args: argparse.Namespace) -> tuple[str, ...]:
    missing: list[str] = []
    for attribute, flag in _INTAKE_REQUIRED_ARGS:
        value = getattr(args, attribute, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(flag)
    return tuple(missing)


def run_asset_command(args: argparse.Namespace, *, repo_root: Path) -> None:
    """Dispatch one fail-closed asset command from the public build entrypoint."""

    if args.action == "asset-check":
        run_asset_check(args, repo_root=repo_root)
        return
    if args.action == "asset-intake":
        missing = _missing_intake_flags(args)
        if missing:
            raise RuntimeError(f"asset-intake requires: {', '.join(missing)}")
        run_asset_intake(args, repo_root=repo_root)
        return
    raise RuntimeError(f"unsupported asset action: {args.action!r}")


__all__ = ("run_asset_command",)
