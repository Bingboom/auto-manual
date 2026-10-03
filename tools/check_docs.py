#!/usr/bin/env python3
"""Compatibility entry point: ``python tools/check_docs.py`` runs :mod:`tools.check.docs` (CQ-1.4).

Prefer ``python -m tools.check.docs``.  Importing ``tools.check_docs`` is deprecated: it
resolves to the very same module object, so ``mock.patch`` targets keep working
until CQ-1.5 removes this shim.
"""
import sys
import warnings
from importlib import import_module
from pathlib import Path

if __name__ == "__main__":
    import runpy

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    runpy.run_module("tools.check.docs", run_name="__main__", alter_sys=True)
    raise SystemExit(0)

warnings.warn(
    "tools.check_docs moved to tools.check.docs",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.check.docs")
