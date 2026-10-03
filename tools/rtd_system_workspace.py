#!/usr/bin/env python3
"""Compatibility entry point: ``python tools/rtd_system_workspace.py`` runs :mod:`tools.rtd.system_workspace` (CQ-1.4).

Prefer ``python -m tools.rtd.system_workspace``.  Importing ``tools.rtd_system_workspace`` is deprecated: it
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
    runpy.run_module("tools.rtd.system_workspace", run_name="__main__", alter_sys=True)
    raise SystemExit(0)

warnings.warn(
    "tools.rtd_system_workspace moved to tools.rtd.system_workspace",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.rtd.system_workspace")
