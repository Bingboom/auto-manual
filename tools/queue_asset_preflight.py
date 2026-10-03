"""Deprecated alias of :mod:`tools.build_queue.asset_preflight` (CQ-1.4); import the new path.

The old name resolves to the very same module object, so attribute reads and
``mock.patch`` targets keep working until CQ-1.5 removes this shim.
"""
import sys
import warnings
from importlib import import_module

warnings.warn(
    "tools.queue_asset_preflight moved to tools.build_queue.asset_preflight",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.build_queue.asset_preflight")
