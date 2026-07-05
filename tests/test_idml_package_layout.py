#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layering contract for the tools/idml package (componentization P1).

tools/export_idml.py is the façade: existing callers/tests import everything
from there, so the re-export surface must stay complete; and the package
modules must never import the façade back (no cycles, imports point down).
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The public surface pinned by P0/P1 — everything a caller or test imports
# from tools.export_idml today. Grows only deliberately.
FACADE_NAMES = (
    "MIMETYPE", "IDPKG", "MM_TO_PT",
    "load_layout_params", "param_pt", "brand_cmyk",
    "SYMBOL_COPY", "normalize_lang", "symbol_copy",
    "load_spec_sections", "load_lcd_rows", "load_spec_annotations",
    "load_symbols_rows", "load_trouble_rows",
    "IdmlWriter", "check_idml",
    "split_safety_first_page", "default_bundle_root", "default_output_path",
    "main",
)


class IdmlPackageLayoutTests(unittest.TestCase):
    def test_facade_reexports_public_surface(self) -> None:
        import tools.export_idml as facade

        missing = [name for name in FACADE_NAMES if not hasattr(facade, name)]
        self.assertEqual(missing, [], f"façade lost re-exports: {missing}")

    def test_package_modules_do_not_import_the_facade(self) -> None:
        import re

        import_re = re.compile(r"^\s*(?:from|import)\s+[\w.]*export_idml", re.MULTILINE)
        offenders: list[str] = []
        for module in sorted((ROOT / "tools" / "idml").rglob("*.py")):
            if import_re.search(module.read_text(encoding="utf-8")):
                offenders.append(module.relative_to(ROOT).as_posix())
        self.assertEqual(offenders, [], f"reverse imports of the façade: {offenders}")

    def test_writer_delegates_share_primitive_implementations(self) -> None:
        from tools.export_idml import IdmlWriter
        from tools.idml import primitives

        # the delegate and the module function must be the same logic — a fork
        # here is exactly the drift the componentization removes
        self.assertEqual(
            IdmlWriter._psr("HB Body", "x", terminal=True),
            primitives.psr("HB Body", "x", terminal=True),
        )
        self.assertIs(IdmlWriter.GLYPH_FALLBACKS, primitives.GLYPH_FALLBACKS)
        self.assertIs(IdmlWriter._PROSE_STYLE, primitives.PROSE_STYLE)


if __name__ == "__main__":
    unittest.main()
