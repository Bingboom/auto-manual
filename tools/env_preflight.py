#!/usr/bin/env python3
"""Compare the running interpreter and packages with the pinned environment.

CI, ReadTheDocs, and the queue workers install from ``requirements.lock`` on the
Python version pinned in ``pyproject.toml``.  A local environment that drifts
from that (another Python minor version, a missing or newer package) does not
fail loudly: it shows up later as a scatter of unrelated-looking test or build
failures.  This module turns the drift into one explicit report up front.

It is read-only and never blocks: every finding is ``OK`` or ``WARN``.  It runs
inside ``build.py doctor`` and standalone before a local test run::

    python tools/env_preflight.py
"""

from __future__ import annotations

import re
import sys
import tomllib
from importlib import metadata
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCK_FILE = "requirements.lock"
PYPROJECT_FILE = "pyproject.toml"
MAX_LISTED = 20

Finding = tuple[str, str, str]

_PIN_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;#]+)")


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def pinned_python(repo_root: Path) -> tuple[int, int] | None:
    """Return the ``[tool.mypy] python_version`` pin, the repo's declared runtime."""

    path = repo_root / PYPROJECT_FILE
    if not path.exists():
        return None
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    raw = str(data.get("tool", {}).get("mypy", {}).get("python_version", "")).strip()
    match = re.fullmatch(r"(\d+)\.(\d+)", raw)
    return (int(match.group(1)), int(match.group(2))) if match else None


def load_lock_pins(repo_root: Path) -> dict[str, tuple[str, str]]:
    """Return ``{normalized name: (display name, version)}`` from the lock file."""

    path = repo_root / LOCK_FILE
    if not path.exists():
        return {}
    pins: dict[str, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _PIN_RE.match(line.strip())
        if match:
            pins[_normalize(match.group(1))] = (match.group(1), match.group(2))
    return pins


def _installed_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _listed(items: list[str]) -> str:
    shown = ", ".join(items[:MAX_LISTED])
    extra = len(items) - MAX_LISTED
    return f"{shown}, +{extra} more" if extra > 0 else shown


def collect_environment_findings(
    repo_root: Path = REPO_ROOT,
    *,
    python_version: tuple[int, int] | None = None,
    installed_version: Callable[[str], str | None] = _installed_version,
) -> list[Finding]:
    findings: list[Finding] = []
    current = python_version or (sys.version_info.major, sys.version_info.minor)
    expected = pinned_python(repo_root)
    current_text = f"{current[0]}.{current[1]}"
    if expected is None:
        findings.append(("WARN", "env.python", f"no python_version pin found in {PYPROJECT_FILE}"))
    elif current == expected:
        findings.append(("OK", "env.python", f"Python {current_text} matches the pinned runtime"))
    else:
        findings.append((
            "WARN",
            "env.python",
            f"Python {current_text} differs from the pinned {expected[0]}.{expected[1]}; "
            "tests and builds may fail for environment reasons",
        ))

    pins = load_lock_pins(repo_root)
    if not pins:
        findings.append(("WARN", "env.lock", f"{LOCK_FILE} not found or has no pins"))
        return findings

    missing: list[str] = []
    drifted: list[str] = []
    for name, version in pins.values():
        installed = installed_version(name)
        if installed is None:
            missing.append(name)
        elif installed != version:
            drifted.append(f"{name} {installed} (lock {version})")

    if not missing and not drifted:
        findings.append(("OK", "env.lock", f"all {len(pins)} pinned packages match {LOCK_FILE}"))
    if missing:
        findings.append(("WARN", "env.lock", f"{len(missing)} pinned package(s) not installed: {_listed(sorted(missing, key=str.casefold))}"))
    if drifted:
        findings.append(("WARN", "env.lock", f"{len(drifted)} package(s) differ from {LOCK_FILE}: {_listed(sorted(drifted, key=str.casefold))}"))
    if missing or drifted:
        findings.append((
            "WARN",
            "env.lock",
            f"to match CI: python -m pip install -r {LOCK_FILE} (on the pinned Python)",
        ))
    return findings


def main() -> int:
    for level, area, message in collect_environment_findings():
        print(f"[env-preflight] {level:<5} {area}: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
