#!/usr/bin/env python3
"""Compatibility entry point: ``python tools/process_build_queue.py`` runs :mod:`tools.build_queue.process_build_queue` (CQ-1.4).

Prefer ``python -m tools.build_queue.process_build_queue``.  Importing ``tools.process_build_queue`` is deprecated: it
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
    runpy.run_module("tools.build_queue.process_build_queue", run_name="__main__", alter_sys=True)
    raise SystemExit(0)

warnings.warn(
    "tools.process_build_queue moved to tools.build_queue.process_build_queue",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.build_queue.process_build_queue")
