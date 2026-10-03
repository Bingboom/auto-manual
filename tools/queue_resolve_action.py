#!/usr/bin/env python3
"""Compatibility entry point: ``python tools/queue_resolve_action.py`` runs :mod:`tools.build_queue.resolve_action` (CQ-1.4).

Prefer ``python -m tools.build_queue.resolve_action``.  Importing ``tools.queue_resolve_action`` is deprecated: it
resolves to the very same module object, so ``mock.patch`` targets keep working
until CQ-1.5 removes this shim.
"""
import sys
import warnings
from importlib import import_module

if __name__ == "__main__":
    import runpy

    runpy.run_module("tools.build_queue.resolve_action", run_name="__main__", alter_sys=True)
    raise SystemExit(0)

warnings.warn(
    "tools.queue_resolve_action moved to tools.build_queue.resolve_action",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.build_queue.resolve_action")
