"""IDML access to the shared language registry.

The exporter supports both ``tools.idml`` package imports and direct
``python tools/export_idml.py`` execution, where the package is imported as
top-level ``idml``.  Keep that bootstrap detail at one boundary while the
language data itself remains owned by ``tools.lang_registry``.
"""
from __future__ import annotations

try:  # normal repository-package import
    from tools.lang_registry import (
        IDML_LANGUAGE_PACKS,
        IDML_SYMBOL_COPY_KEYS,
        LANGUAGE_REGISTRY,
        canonical_language,
        governed_languages,
    )
except ImportError:  # direct exporter-script import
    from lang_registry import (  # type: ignore[no-redef]
        IDML_LANGUAGE_PACKS,
        IDML_SYMBOL_COPY_KEYS,
        LANGUAGE_REGISTRY,
        canonical_language,
        governed_languages,
    )


__all__ = (
    "IDML_LANGUAGE_PACKS",
    "IDML_SYMBOL_COPY_KEYS",
    "LANGUAGE_REGISTRY",
    "canonical_language",
    "governed_languages",
)
