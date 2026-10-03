#!/usr/bin/env python3
"""Compatibility entry point: ``python tools/rtd_deliverables.py`` runs :mod:`tools.rtd.deliverables` (CQ-1.4).

Prefer ``python -m tools.rtd.deliverables``.  Importing ``tools.rtd_deliverables`` is deprecated: it
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
    runpy.run_module("tools.rtd.deliverables", run_name="__main__", alter_sys=True)
    raise SystemExit(0)

warnings.warn(
    "tools.rtd_deliverables moved to tools.rtd.deliverables",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.rtd.deliverables")
