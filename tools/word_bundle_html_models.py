"""Deprecated alias of :mod:`tools.word.bundle_html_models` (CQ-1.4); import the new path.

The old name resolves to the very same module object, so attribute reads and
``mock.patch`` targets keep working until CQ-1.5 removes this shim.
"""
import sys
import warnings
from importlib import import_module

warnings.warn(
    "tools.word_bundle_html_models moved to tools.word.bundle_html_models",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = import_module("tools.word.bundle_html_models")
