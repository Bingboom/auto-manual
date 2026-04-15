#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.release_manifest_service import build_release_manifest as _build_release_manifest  # noqa: E402


def _read_git_sha() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = (proc.stdout or "").strip()
    return value or None


def build_release_manifest(
    *,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None = None,
    built_at: datetime | None = None,
    docs_build_dir: Path | None = None,
    releases_root: Path | None = None,
) -> tuple[Path, Path]:
    return _build_release_manifest(
        repo_root=ROOT,
        config_path=config_path,
        model=model,
        region=region,
        git_sha=_read_git_sha(),
        data_root=data_root,
        built_at=built_at,
        docs_build_dir=docs_build_dir,
        releases_root=releases_root,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Write a release manifest for one explicit target.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    ap.add_argument("--docs-build-dir", default=None, help="Override docs/_build root used to locate outputs")
    ap.add_argument("--releases-root", default=None, help="Override reports/releases root used to write manifests")
    ap.add_argument("--model", required=True, help="Explicit release target model")
    ap.add_argument("--region", required=True, help="Explicit release target region")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path

    docs_build_dir = None
    if isinstance(args.docs_build_dir, str) and args.docs_build_dir.strip():
        docs_build_dir = Path(args.docs_build_dir.strip())
        if not docs_build_dir.is_absolute():
            docs_build_dir = ROOT / docs_build_dir

    releases_root = None
    if isinstance(args.releases_root, str) and args.releases_root.strip():
        releases_root = Path(args.releases_root.strip())
        if not releases_root.is_absolute():
            releases_root = ROOT / releases_root

    try:
        json_path, csv_path = build_release_manifest(
            config_path=config_path,
            model=args.model,
            region=args.region,
            data_root=args.data_root,
            docs_build_dir=docs_build_dir,
            releases_root=releases_root,
        )
    except RuntimeError as exc:
        print(f"[release-manifest] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"[release-manifest] JSON: {json_path}")
    print(f"[release-manifest] CSV: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
