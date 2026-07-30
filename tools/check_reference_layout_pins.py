#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Keep approved reference-layout contracts honest about repo-derived inputs.

An approved reference-layout contract pins the identity of the inputs it was
validated against. Two of those pins are derived from tracked repository files
— ``layout_params_sha256`` from ``data/layout_params.csv`` and
``style_contract_sha256`` from the manual style contract — so editing either
file without refreshing the pin silently decouples the contract from the
layout it claims to approve.

That is not hypothetical. PR #720 refreshed ``layout_params_sha256`` and then
took one more correction to ``data/layout_params.csv``
(``lang_en_idml_ups_caution_space_after`` 9.9pt -> 15.9pt) without recomputing
it. The production IDML build refused every target afterwards, and nothing
caught it: no CI job builds the production IDML, and #720's own post-merge run
was cancelled by the merges that followed it.

This check closes that gap cheaply. It never rebinds anything — re-pinning an
approved contract is an operator decision — it only reports the drift.

The other pins (``manual_content_sha256``, ``snapshot_sha256``) are derived
from a phase2 data snapshot that is not tracked, so they cannot be verified
from a checkout and are deliberately out of scope.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.render_contract import (  # noqa: E402
    contract_sha256,
    layout_tokens_sha256,
    load_layout_tokens,
    load_render_contract,
)
from tools.utils.path_utils import PathSegments, Paths  # noqa: E402

CONTRACTS_SUBDIR = ("docs", "renderers", "contracts", "reference_layout")


def _layout_pin(repo_root: Path) -> str:
    paths = Paths(root=repo_root)
    return layout_tokens_sha256(load_layout_tokens(paths.layout_params_csv))


def _style_pin(repo_root: Path) -> str:
    paths = Paths(root=repo_root)
    return contract_sha256(load_render_contract(paths.manual_style_contract))


def contract_paths(repo_root: Path) -> list[Path]:
    directory = repo_root.joinpath(*CONTRACTS_SUBDIR)
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.json") if p.is_file())


def collect_pin_drift(repo_root: Path) -> list[tuple[str, str, str, str]]:
    """(contract, pin name, pinned value, recomputed value) per mismatch."""
    expected = {
        "layout_params_sha256": _layout_pin(repo_root),
        "style_contract_sha256": _style_pin(repo_root),
    }
    drift: list[tuple[str, str, str, str]] = []
    for path in contract_paths(repo_root):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"{path}: unreadable reference-layout contract: {exc}")
        identity = payload.get("source_identity")
        if not isinstance(identity, dict):
            continue
        rel = path.relative_to(repo_root).as_posix()
        for name, actual in expected.items():
            pinned = identity.get(name)
            if pinned is None:
                continue
            if str(pinned) != actual:
                drift.append((rel, name, str(pinned), actual))
    return drift


def _fix_command(repo_root: Path, contract: str) -> str:
    contract_path = repo_root / contract
    try:
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return (
            "python tools/reference_layout_rebind.py "
            f"--plan {contract} --manual-ir <manual.ir.json> --write"
        )
    target = payload.get("target") if isinstance(payload, dict) else None
    model = str(target.get("model") or "").strip() if isinstance(target, dict) else ""
    region = str(target.get("region") or "").strip() if isinstance(target, dict) else ""
    languages = target.get("languages") if isinstance(target, dict) else None
    if model and region and isinstance(languages, list) and languages:
        ir_dir = Path(PathSegments.DOCS) / PathSegments.BUILD / model / region
        if len(languages) == 1:
            ir_dir /= str(languages[0]).strip().lower()
        ir_path = (ir_dir / "idml" / PathSegments.MANUAL_IR_JSON).as_posix()
    else:
        ir_path = "<manual.ir.json>"
    return (
        "python tools/reference_layout_rebind.py "
        f"--plan {contract} --manual-ir {ir_path} --write"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_reference_layout_pins",
        description=(
            "Fail when an approved reference-layout contract's repo-derived "
            "pins no longer match the tracked files they were computed from."
        ),
    )
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    args = parser.parse_args(argv)

    contracts = contract_paths(args.repo_root)
    if not contracts:
        print("[reference-pins] no reference-layout contracts to check")
        return 0
    drift = collect_pin_drift(args.repo_root)
    if not drift:
        print(f"[reference-pins] OK for {len(contracts)} contract(s)")
        return 0
    for contract, name, pinned, actual in drift:
        print(f"[reference-pins] DRIFT {contract} {name}")
        print(f"[reference-pins]   pinned:     {pinned}")
        print(f"[reference-pins]   recomputed: {actual}")
    print(
        "[reference-pins] the contract no longer describes the tracked inputs. "
        "Refreshing an approved pin is an operator decision. Copy the fix "
        "command below for each affected contract, then re-run the parity check."
    )
    for contract in sorted({contract for contract, _name, _pinned, _actual in drift}):
        print(f"[reference-pins] FIX {contract}")
        print(f"[reference-pins]   {_fix_command(args.repo_root, contract)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
