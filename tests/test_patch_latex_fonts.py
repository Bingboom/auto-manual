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

    def test_apply_language_cjk_override_should_carry_and_select_japanese_font(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build_dir = root / "latex"
            build_dir.mkdir()
            fonts_path = build_dir / "fonts.tex"
            fonts_path.write_text("\\HBSetupFonts\n", encoding="utf-8")
            source = root / patch_latex_fonts.JAPANESE_PORTABLE_FONT_FILE
            source.write_bytes(b"portable-japanese-font")

            applied = patch_latex_fonts.apply_language_cjk_override(
                fonts_path,
                build_dir=build_dir,
                language="ja-JP",
                portable_font_source=source,
            )

            self.assertTrue(applied)
            self.assertEqual(
                source.read_bytes(),
                (build_dir / source.name).read_bytes(),
            )
            content = fonts_path.read_text(encoding="utf-8")
            self.assertIn(patch_latex_fonts.LANGUAGE_CJK_OVERRIDE_MARKER, content)
            self.assertEqual(
                4,
                content.count(patch_latex_fonts.JAPANESE_PORTABLE_FONT_FILE),
            )

    def test_apply_language_cjk_override_should_leave_non_japanese_build_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            build_dir = Path(td)
            fonts_path = build_dir / "fonts.tex"
            fonts_path.write_text("unchanged\n", encoding="utf-8")

            applied = patch_latex_fonts.apply_language_cjk_override(
                fonts_path,
                build_dir=build_dir,
                language="en",
            )

            self.assertFalse(applied)
            self.assertEqual("unchanged\n", fonts_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
