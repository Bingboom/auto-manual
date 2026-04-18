#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tools/patch_latex_fonts.py
from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)
DOCS = ROOT / "docs"
BUILD = DOCS / "_build" / "latex"

FONTS_SRC = DOCS / "renderers" / "latex" / "fonts.tex"
FONTS_DST = BUILD / "fonts.tex"

FRAGILE_UNICODE_REPLACEMENTS = (
    ("\u2393", " DC "),
    ("\u203b", "*"),
    ("\u2084", r"\textsubscript{4}"),
)

LOCAL_GILROY_DIR_ENV = "AUTO_MANUAL_LOCAL_GILROY_DIR"
LOCAL_GILROY_OVERRIDE_MARKER = "% AUTO_MANUAL_LOCAL_GILROY_OVERRIDE"
LOCAL_GILROY_REQUIRED_FILES = (
    "gilroy-regular-3.otf",
    "gilroy-bold-4.otf",
    "Gilroy-LightItalic-12.otf",
    "Gilroy-ExtraBoldItalic-10.otf",
)


def die(msg: str) -> None:
    raise SystemExit(f"[patch_latex_fonts] ERROR: {msg}")


def find_main_tex(build_dir: Path, preferred_name: str) -> Path:
    p = build_dir / preferred_name
    if p.exists():
        return p
    for tex in sorted(build_dir.glob("*.tex")):
        if tex.name.lower().startswith("sphinx"):
            continue
        txt = tex.read_text(encoding="utf-8", errors="ignore")
        if r"\begin{document}" in txt:
            return tex
    raise RuntimeError("No main .tex found in build dir.")


def inject_before_begin_document(tex_path: Path) -> None:
    s = tex_path.read_text(encoding="utf-8", errors="ignore")
    if r"\input{fonts.tex}" in s:
        return
    pat = r"(\\begin\{document\})"
    if not re.search(pat, s):
        raise RuntimeError(f"Cannot find \\begin{{document}} in {tex_path.name}")
    s2 = re.sub(pat, r"\\input{fonts.tex}\n\1", s, count=1)
    tex_path.write_text(s2, encoding="utf-8")
    print(f"[patch_latex_fonts] injected into: {tex_path.name}")


def sanitize_fragile_unicode_glyphs(tex_path: Path) -> int:
    s = tex_path.read_text(encoding="utf-8", errors="ignore")
    total = 0
    for raw, replacement in FRAGILE_UNICODE_REPLACEMENTS:
        count = s.count(raw)
        if not count:
            continue
        s = s.replace(raw, replacement)
        total += count
    if total:
        tex_path.write_text(s, encoding="utf-8")
        print(f"[patch_latex_fonts] sanitized fragile Unicode glyphs in: {tex_path.name} (changes={total})")
    return total


def strip_sphinx_default_mono_font(tex_path: Path) -> int:
    s = tex_path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(
        r"\\setmonofont\{FreeMono\}\[Scale=0\.9,\n"
        r"  Extension      = \.otf,\n"
        r"  UprightFont    = \*,\n"
        r"  ItalicFont     = \*Oblique,\n"
        r"  BoldFont       = \*Bold,\n"
        r"  BoldItalicFont = \*BoldOblique,\n"
        r"\]\n",
        flags=re.MULTILINE,
    )
    s2, count = pattern.subn("% Sphinx default FreeMono removed; fonts.tex provides mono font fallback.\n", s, count=1)
    if count:
        tex_path.write_text(s2, encoding="utf-8")
        print(f"[patch_latex_fonts] removed Sphinx default FreeMono block from: {tex_path.name}")
    return count


def resolve_local_gilroy_dir() -> Path | None:
    raw = os.environ.get(LOCAL_GILROY_DIR_ENV, "").strip()
    if not raw:
        return None

    font_dir = Path(raw).expanduser()
    if not font_dir.exists():
        print(f"[patch_latex_fonts] local Gilroy dir not found, skipping override: {font_dir}")
        return None
    if not font_dir.is_dir():
        print(f"[patch_latex_fonts] local Gilroy path is not a directory, skipping override: {font_dir}")
        return None

    missing = [name for name in LOCAL_GILROY_REQUIRED_FILES if not (font_dir / name).exists()]
    if missing:
        print(
            "[patch_latex_fonts] local Gilroy dir missing required font files, skipping override: "
            + ", ".join(missing)
        )
        return None

    return font_dir.resolve()


def build_local_gilroy_override(font_dir: Path) -> str:
    font_path = font_dir.as_posix().rstrip("/") + "/"
    regular_font = (font_dir / LOCAL_GILROY_REQUIRED_FILES[0]).as_posix()
    return "\n".join(
        (
            f"  \\IfFileExists{{{regular_font}}}{{%",
            "    \\setmainfont{gilroy-regular-3.otf}[",
            f"      Path={{{font_path}}},",
            "      Ligatures=TeX,",
            "      BoldFont=gilroy-bold-4.otf,",
            "      ItalicFont=Gilroy-LightItalic-12.otf,",
            "      BoldItalicFont=Gilroy-ExtraBoldItalic-10.otf",
            "    ]",
            "    \\setsansfont{gilroy-regular-3.otf}[",
            f"      Path={{{font_path}}},",
            "      Ligatures=TeX,",
            "      BoldFont=gilroy-bold-4.otf,",
            "      ItalicFont=Gilroy-LightItalic-12.otf,",
            "      BoldItalicFont=Gilroy-ExtraBoldItalic-10.otf",
            "    ]",
            "    \\global\\HBLocalGilroyFontsConfiguredtrue",
            "  }{}",
        )
    )


def apply_local_gilroy_override(fonts_path: Path) -> bool:
    if not fonts_path.exists():
        return False

    font_dir = resolve_local_gilroy_dir()
    if font_dir is None:
        return False

    s = fonts_path.read_text(encoding="utf-8", errors="ignore")
    if LOCAL_GILROY_OVERRIDE_MARKER not in s:
        raise RuntimeError(f"Cannot find local Gilroy override marker in {fonts_path}")

    override_block = build_local_gilroy_override(font_dir)
    s = s.replace(LOCAL_GILROY_OVERRIDE_MARKER, override_block, 1)
    fonts_path.write_text(s, encoding="utf-8")
    print(f"[patch_latex_fonts] enabled local Gilroy override from: {font_dir}")
    return True


def patch_build_fonts_tex_windows(fonts_path: Path) -> int:
    """
    Windows-only: patch _build/latex/fonts.tex to avoid missing Helvetica-family.
    IMPORTANT: Only touches fonts.tex. Never touches theme.tex.

    Strategy:
      - Replace any literal setmainfont/setsansfont to Helvetica/Helvetica Rounded with Arial/Calibri fallback.
      - Also replace any IfFontExistsTF{Helvetica...}{...} with IfFontExistsTF{Arial}{...} to avoid probing missing fonts.

    Returns: number of replacements (approx).
    """
    if os.name != "nt":
        return 0
    if not fonts_path.exists():
        return 0

    s = fonts_path.read_text(encoding="utf-8", errors="ignore")
    total = 0

    # Replace \setmainfont{Helvetica...} / \setsansfont{Helvetica...}
    rx_main = re.compile(r"\\setmainfont\s*(\[[^\]]*\])?\s*\{\s*Helvetica(?:\s+Rounded)?\s*\}", flags=re.MULTILINE)
    rx_sans = re.compile(r"\\setsansfont\s*(\[[^\]]*\])?\s*\{\s*Helvetica(?:\s+Rounded)?\s*\}", flags=re.MULTILINE)

    def repl_main(m: re.Match) -> str:
        opts = m.group(1) or ""
        return (
            r"\IfFontExistsTF{Arial}{"
            "\n  " + rf"\setmainfont{opts}{{Arial}}" +
            "\n}{"
            "\n  " + r"\IfFontExistsTF{Calibri}{" +
            "\n    " + rf"\setmainfont{opts}{{Calibri}}" +
            "\n  }{"
            "\n    " + rf"\setmainfont{opts}{{Latin Modern Roman}}" +
            "\n  }"
            "\n}"
        )

    def repl_sans(m: re.Match) -> str:
        opts = m.group(1) or ""
        return (
            r"\IfFontExistsTF{Arial}{"
            "\n  " + rf"\setsansfont{opts}{{Arial}}" +
            "\n}{"
            "\n  " + r"\IfFontExistsTF{Calibri}{" +
            "\n    " + rf"\setsansfont{opts}{{Calibri}}" +
            "\n  }{"
            "\n    " + rf"\setsansfont{opts}{{Latin Modern Sans}}" +
            "\n  }"
            "\n}"
        )

    s, n = rx_main.subn(repl_main, s)
    total += n
    s, n = rx_sans.subn(repl_sans, s)
    total += n

    # Replace \IfFontExistsTF{Helvetica...}{ with \IfFontExistsTF{Arial}{
    rx_if = re.compile(r"\\IfFontExistsTF\s*\{\s*Helvetica(?:\s+Rounded)?\s*\}\s*\{", flags=re.MULTILINE)
    s, n = rx_if.subn(r"\\IfFontExistsTF{Arial}{", s)
    total += n

    if total:
        fonts_path.write_text(s, encoding="utf-8")
        print(f"[patch_latex_fonts] patched build fonts.tex for Windows (changes={total})")
    else:
        print("[patch_latex_fonts] no changes needed for build fonts.tex")

    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", default="manual_demo.tex", help="main tex filename in _build/latex")
    ap.add_argument("--build-dir", default=None, help="LaTeX build directory (defaults to docs/_build/latex)")
    args = ap.parse_args()

    build_dir = Path(args.build_dir).resolve() if args.build_dir else BUILD
    fonts_dst = build_dir / "fonts.tex"

    if not build_dir.exists():
        die(f"build dir not found: {build_dir}")
    if not FONTS_SRC.exists():
        die(f"fonts.tex not found: {FONTS_SRC}")

    shutil.copyfile(FONTS_SRC, fonts_dst)
    print(f"[patch_latex_fonts] copied fonts.tex -> {fonts_dst}")

    apply_local_gilroy_override(fonts_dst)
    patch_build_fonts_tex_windows(fonts_dst)

    main_tex = find_main_tex(build_dir, args.tex)
    strip_sphinx_default_mono_font(main_tex)
    inject_before_begin_document(main_tex)
    sanitize_fragile_unicode_glyphs(main_tex)


if __name__ == "__main__":
    main()
