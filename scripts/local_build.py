#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)
DEFAULT_STAGING_ROOT = ".tmp/staging"
SUPPORTED_ACTIONS = {
    "all",
    "check",
    "diff-report",
    "doctor",
    "fast",
    "html",
    "pdf",
    "preview",
    "publish",
    "release-manifest",
    "rst",
    "sync-review",
    "word",
}


def resolve_build_command(
    argv: Sequence[str],
    *,
    python_exe: str = sys.executable,
    repo_root: Path = ROOT,
) -> list[str]:
    forwarded = list(argv)
    if not forwarded:
        raise RuntimeError(
            "Usage: python scripts/local_build.py <action> [build.py args...]\n"
            "Recommended local actions: check, diff-report, release-manifest, publish."
        )

    action = forwarded[0]
    if action not in SUPPORTED_ACTIONS:
        supported = ", ".join(sorted(SUPPORTED_ACTIONS))
        raise RuntimeError(
            f"scripts/local_build.py only supports staging-safe local actions. "
            f"Unsupported action: {action}. Supported actions: {supported}."
        )

    command = [python_exe, str(repo_root / "build.py"), action]
    remainder = forwarded[1:]
    has_explicit_staging = "--staging-root" in remainder
    has_env_staging = bool(str(os.environ.get("AUTO_MANUAL_STAGING_ROOT", "")).strip())
    if not has_explicit_staging and not has_env_staging:
        command.extend(["--staging-root", DEFAULT_STAGING_ROOT])
    command.extend(remainder)
    return command


def main(argv: Sequence[str] | None = None) -> int:
    try:
        command = resolve_build_command(argv or sys.argv[1:])
    except RuntimeError as exc:
        print(f"[local-build] {exc}", file=sys.stderr)
        return 1

    print(f"[local-build] {' '.join(command)}")
    completed = subprocess.run(command, cwd=str(ROOT))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
