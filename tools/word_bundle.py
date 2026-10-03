#!/usr/bin/env python3
"""Compatibility entry point: ``python tools/word_bundle.py`` runs :mod:`tools.word.bundle` (CQ-1.4).

Prefer ``python -m tools.word.bundle``.  Importing ``tools.word_bundle`` is deprecated: it
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
    runpy.run_module("tools.word.bundle", run_name="__main__", alter_sys=True)
    raise SystemExit(0)

warnings.warn(
    "tools.word_bundle moved to tools.word.bundle",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.word.bundle")
