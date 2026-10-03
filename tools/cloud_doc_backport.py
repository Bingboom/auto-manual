#!/usr/bin/env python3
"""Compatibility entry point for the cloud-doc backport CLI (moved to ``tools/backport/``, CQ-1.3).

``python tools/cloud_doc_backport.py <command>`` (AGENTS.md §3) keeps working and is
the same as ``python -m tools.backport.cloud_doc <command>``.  Importing
``tools.cloud_doc_backport`` is deprecated: it resolves to the very same module object
as :mod:`tools.backport.cloud_doc`, so ``mock.patch`` targets keep working until
CQ-1.5 removes this shim.
"""
import sys
import warnings
from importlib import import_module
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.backport.cloud_doc import main

    raise SystemExit(main())

warnings.warn(
    "tools.cloud_doc_backport moved to tools.backport.cloud_doc",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.backport.cloud_doc")
