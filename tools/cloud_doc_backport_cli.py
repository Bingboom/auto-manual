"""Deprecated alias of :mod:`tools.backport.cli` (CQ-1.3); import the new path.

The old name resolves to the very same module object, so attribute reads and
``mock.patch`` targets keep working until CQ-1.5 removes this shim.
"""
import sys
import warnings
from importlib import import_module

warnings.warn(
    "tools.cloud_doc_backport_cli moved to tools.backport.cli",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.backport.cli")
