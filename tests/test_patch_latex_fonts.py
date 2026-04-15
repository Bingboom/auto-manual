from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import patch_latex_fonts


class TestPatchLatexFonts(unittest.TestCase):
    def test_sanitize_fragile_unicode_glyphs_should_replace_known_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tex_path = Path(td) / "manual_demo.tex"
            tex_path.write_text("5V⎓3A\n※ USB Type-C\n", encoding="utf-8")

            changes = patch_latex_fonts.sanitize_fragile_unicode_glyphs(tex_path)

            self.assertEqual(2, changes)
            self.assertEqual("5V DC 3A\n* USB Type-C\n", tex_path.read_text(encoding="utf-8"))

    def test_inject_before_begin_document_should_be_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tex_path = Path(td) / "manual_demo.tex"
            tex_path.write_text("\\documentclass{article}\n\\begin{document}\nbody\n", encoding="utf-8")

            patch_latex_fonts.inject_before_begin_document(tex_path)
            patch_latex_fonts.inject_before_begin_document(tex_path)

            self.assertEqual(1, tex_path.read_text(encoding="utf-8").count("\\input{fonts.tex}"))


if __name__ == "__main__":
    unittest.main()
