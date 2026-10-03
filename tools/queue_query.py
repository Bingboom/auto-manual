#!/usr/bin/env python3
"""Compatibility entry point: ``python tools/queue_query.py`` runs :mod:`tools.build_queue.query` (CQ-1.4).

Prefer ``python -m tools.build_queue.query``.  Importing ``tools.queue_query`` is deprecated: it
resolves to the very same module object, so ``mock.patch`` targets keep working
until CQ-1.5 removes this shim.
"""
import sys
import warnings
from importlib import import_module

if __name__ == "__main__":
    import runpy

    runpy.run_module("tools.build_queue.query", run_name="__main__", alter_sys=True)
    raise SystemExit(0)

warnings.warn(
    "tools.queue_query moved to tools.build_queue.query",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.build_queue.query")
