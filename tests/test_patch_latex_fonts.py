from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import patch_latex_fonts


class TestPatchLatexFonts(unittest.TestCase):
    def test_sanitize_fragile_unicode_glyphs_should_replace_known_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tex_path = Path(td) / "manual_demo.tex"
            tex_path.write_text("5V\u23933A\n\u203b USB Type-C\n", encoding="utf-8")

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

    def test_apply_local_gilroy_override_should_inject_only_when_env_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fonts_path = root / "fonts.tex"
            gilroy_dir = root / "gilroy"
            gilroy_dir.mkdir()
            for name in patch_latex_fonts.LOCAL_GILROY_REQUIRED_FILES:
                (gilroy_dir / name).write_text("", encoding="utf-8")

            fonts_path.write_text(
                "\\newif\\ifHBLocalGilroyFontsConfigured\n"
                "\\HBLocalGilroyFontsConfiguredfalse\n"
                "\\newcommand{\\HBLocalGilroyOverride}{%\n"
                f"  {patch_latex_fonts.LOCAL_GILROY_OVERRIDE_MARKER}\n"
                "}\n",
                encoding="utf-8",
            )

            with mock.patch.dict(
                os.environ,
                {patch_latex_fonts.LOCAL_GILROY_DIR_ENV: str(gilroy_dir)},
                clear=False,
            ):
                applied = patch_latex_fonts.apply_local_gilroy_override(fonts_path)

            content = fonts_path.read_text(encoding="utf-8")
            self.assertTrue(applied)
            self.assertNotIn(patch_latex_fonts.LOCAL_GILROY_OVERRIDE_MARKER, content)
            self.assertIn("\\global\\HBLocalGilroyFontsConfiguredtrue", content)
            self.assertIn(gilroy_dir.as_posix().rstrip("/") + "/", content)

    def test_apply_local_gilroy_override_should_skip_when_required_files_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fonts_path = root / "fonts.tex"
            gilroy_dir = root / "gilroy"
            gilroy_dir.mkdir()
            (gilroy_dir / patch_latex_fonts.LOCAL_GILROY_REQUIRED_FILES[0]).write_text("", encoding="utf-8")

            original = (
                "\\newcommand{\\HBLocalGilroyOverride}{%\n"
                f"  {patch_latex_fonts.LOCAL_GILROY_OVERRIDE_MARKER}\n"
                "}\n"
            )
            fonts_path.write_text(original, encoding="utf-8")

            with mock.patch.dict(
                os.environ,
                {patch_latex_fonts.LOCAL_GILROY_DIR_ENV: str(gilroy_dir)},
                clear=False,
            ):
                applied = patch_latex_fonts.apply_local_gilroy_override(fonts_path)

            self.assertFalse(applied)
            self.assertEqual(original, fonts_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
