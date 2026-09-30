"""Test package for manual_demo tooling."""

from __future__ import annotations

import os
import sys
from typing import Callable, TextIO

ENV_PREFLIGHT_SWITCH = "AUTO_MANUAL_ENV_PREFLIGHT"


def _report_environment_drift(
    collect: Callable[[], list[tuple[str, str, str]]] | None = None,
    stream: TextIO | None = None,
) -> int:
    """Name environment drift once, before any test runs.

    A local interpreter or package set that differs from the pinned runtime
    and ``requirements.lock`` surfaces as a scatter of unrelated-looking
    failures. This prints the same advisory rows as ``build.py doctor`` (WARN
    rows only) so those failures can be attributed up front. It never changes
    a test outcome, stays silent when the environment matches CI, and is
    switched off with ``AUTO_MANUAL_ENV_PREFLIGHT=0``. Returns the number of
    rows printed.
    """
    if os.environ.get(ENV_PREFLIGHT_SWITCH, "").strip() == "0":
        return 0
    try:
        if collect is None:
            from tools.env_preflight import collect_environment_findings as collect
        rows = [
            f"[env-preflight] {level} {area}: {message}"
            for level, area, message in collect()
            if level != "OK"
        ]
    except Exception:  # advisory only: never break test discovery
        return 0
    if rows:
        print("\n".join(rows), file=stream or sys.stderr)
    return len(rows)


_report_environment_drift()
