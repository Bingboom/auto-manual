"""Deprecated alias of :mod:`tools.web.app_controls` (CQ-1.4); import the new path.

The old name resolves to the very same module object, so attribute reads and
``mock.patch`` targets keep working until CQ-1.5 removes this shim.
"""
import sys
import warnings
from importlib import import_module

warnings.warn(
    "tools.web_app_controls moved to tools.web.app_controls",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.web.app_controls")
