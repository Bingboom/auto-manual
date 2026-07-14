#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Toolchain provenance: name the environment that produced an artifact.

Milestone I3. The LaTeX line has no golden snapshot, and the IDML line's
measured page plan is derived from the LaTeX PDF — so a silent TeX / pandoc /
package upgrade can reflow every manual (and trip the parity gate) with
nothing recording which versions were involved. This module is the single
source both consumers use:

- ``doctor`` prints the versions so drift is visible before a build;
- the release manifest embeds them so any published PDF can name the exact
  toolchain that produced it.

Collection is best-effort and never raises: a missing binary records ``None``,
a binary that exists but cannot report a version records ``"unknown"``.
"""
from __future__ import annotations

import hashlib
import platform as platform_module
import plistlib
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Callable

SCHEMA_VERSION = 1

LOCK_FILENAME = "requirements.lock"

# The packages whose exact versions shape rendered output or data handling.
PROVENANCE_PACKAGES = (
    "sphinx",
    "docutils",
    "myst-parser",
    "PyYAML",
    "PyMuPDF",
    "Pillow",
    "numpy",
    "furo",
)

_VERSION_TIMEOUT_SECONDS = 15


def _first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def command_version(
    binary: str,
    *,
    args: tuple[str, ...] = ("--version",),
    which: Callable[[str], str | None] = shutil.which,
    run: Callable[..., Any] = subprocess.run,
) -> str | None:
    """First line of ``<binary> --version``; None if absent, "unknown" if mute."""
    path = which(binary)
    if not path:
        return None
    try:
        proc = run(
            [path, *args],
            capture_output=True,
            text=True,
            timeout=_VERSION_TIMEOUT_SECONDS,
        )
    except Exception:
        return "unknown"
    line = _first_line((proc.stdout or "") + "\n" + (proc.stderr or ""))
    return line or "unknown"


def package_versions(
    packages: tuple[str, ...] = PROVENANCE_PACKAGES,
) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in packages:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def indesign_version(
    *,
    applications_root: Path = Path("/Applications"),
    platform: str = sys.platform,
) -> str | None:
    """Best-effort Adobe InDesign version on macOS (the finalize leg's host).

    Returns None off-macOS or when no app bundle is present; the newest
    install wins when several are.
    """
    if not platform.startswith("darwin"):
        return None
    try:
        plists = sorted(
            applications_root.glob(
                "Adobe InDesign*/Adobe InDesign*.app/Contents/Info.plist"
            )
        )
    except OSError:
        return None
    if not plists:
        return None
    newest = plists[-1]
    try:
        with newest.open("rb") as handle:
            info = plistlib.load(handle)
    except Exception:
        return "unknown"
    app_name = newest.parents[1].stem
    version = str(info.get("CFBundleShortVersionString") or "unknown")
    return f"{app_name} {version}"


def requirements_lock_state(repo_root: Path | None) -> dict[str, str | None]:
    """Whether the pinned-deps lock exists and which exact bytes it holds."""
    if repo_root is None:
        return {"path": None, "sha256": None}
    lock_path = repo_root / LOCK_FILENAME
    if not lock_path.is_file():
        return {"path": LOCK_FILENAME, "sha256": None}
    return {
        "path": LOCK_FILENAME,
        "sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
    }


def collect_toolchain(
    *,
    repo_root: Path | None = None,
    which: Callable[[str], str | None] = shutil.which,
    run: Callable[..., Any] = subprocess.run,
    platform: str = sys.platform,
) -> dict[str, Any]:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    return {
        "schema_version": SCHEMA_VERSION,
        "python": f"{platform_module.python_implementation()} {platform_module.python_version()}",
        "platform": platform_module.platform(),
        "packages": package_versions(),
        "xelatex": command_version("xelatex", which=which, run=run),
        "pandoc": command_version("pandoc", which=which, run=run),
        "indesign": indesign_version(platform=platform),
        "requirements_lock": requirements_lock_state(repo_root),
    }


def render_summary_lines(toolchain: dict[str, Any]) -> list[str]:
    """Human-readable one-liners (doctor output)."""
    lines = [
        f"python: {toolchain.get('python')} ({toolchain.get('platform')})",
        f"xelatex: {toolchain.get('xelatex') or 'not found'}",
        f"pandoc: {toolchain.get('pandoc') or 'not found'}",
    ]
    indesign = toolchain.get("indesign")
    if indesign is not None:
        lines.append(f"indesign: {indesign}")
    packages = toolchain.get("packages") or {}
    package_bits = ", ".join(
        f"{name} {version or 'missing'}" for name, version in packages.items()
    )
    if package_bits:
        lines.append(f"packages: {package_bits}")
    lock = toolchain.get("requirements_lock") or {}
    if lock.get("sha256"):
        lines.append(f"requirements.lock: sha256 {lock['sha256'][:12]}…")
    else:
        lines.append("requirements.lock: absent (deps unpinned on this checkout)")
    return lines


if __name__ == "__main__":
    import json

    print(json.dumps(collect_toolchain(repo_root=Path(__file__).resolve().parents[1]), ensure_ascii=False, indent=2))
