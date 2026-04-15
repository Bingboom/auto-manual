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

    patch_build_fonts_tex_windows(fonts_dst)

    main_tex = find_main_tex(build_dir, args.tex)
    inject_before_begin_document(main_tex)
    sanitize_fragile_unicode_glyphs(main_tex)


if __name__ == "__main__":
    main()
