#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

BUILD_TEX = ROOT / "docs" / "_build" / "latex" / "manual_demo.tex"

# 这些文件最可能定义页脚/页码（按你仓库结构）
THEME_FILES = [
    ROOT / "docs" / "latex_theme" / "theme.tex",
    ROOT / "docs" / "latex_theme" / "layout_templates.tex",
    ROOT / "docs" / "latex_theme" / "layout_core.tex",
    ROOT / "docs" / "latex_theme" / "components_base.tex",
    ROOT / "docs" / "latex_theme" / "components_safety.tex",
    ROOT / "docs" / "latex_theme" / "type_system.tex",
    ROOT / "docs" / "latex_theme" / "tools.tex",
]

# 关键字：只要出现这些，就高度相关
PATTERNS = [
    r"\\usepackage\{fancyhdr\}",
    r"\\pagestyle\{.*?\}",
    r"\\thispagestyle\{.*?\}",
    r"\\fancypagestyle\{.*?\}",
    r"\\fancyhf",
    r"\\fancyfoot",
    r"\\fancyhead",
    r"\\headrulewidth",
    r"\\footrulewidth",
    r"\\thepage",
    r"HBPageTemplate",
    r"HBTypePageNumber",
    r"HBTypeFooter",
]

CTX = 3  # 上下文行数


def die(msg: str) -> None:
    print(f"[diag_pagenum] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def grep_file(path: Path) -> list[tuple[int, str]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    hits: list[tuple[int, str]] = []
    rx = re.compile("|".join(f"(?:{p})" for p in PATTERNS))
    for i, line in enumerate(lines, start=1):
        if rx.search(line):
            hits.append((i, line))
    return hits


def print_hits(path: Path) -> None:
    if not path.exists():
        print(f"\n--- {path} (MISSING)")
        return

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    hits = grep_file(path)

    print(f"\n=== {path.relative_to(ROOT)} ===")
    if not hits:
        print("(no matches)")
        return

    for (lineno, _) in hits:
        start = max(1, lineno - CTX)
        end = min(len(lines), lineno + CTX)
        print(f"\n-- hit @ line {lineno} --")
        for j in range(start, end + 1):
            prefix = ">>" if j == lineno else "  "
            print(f"{prefix} {j:4d}: {lines[j-1]}")


def main() -> None:
    print("[diag_pagenum] Scanning build output + theme files for page-number rules...")

    # 1) 主 tex 必须存在（先 build 一次）
    if not BUILD_TEX.exists():
        die(f"Build tex not found: {BUILD_TEX}\nRun: make build (or sphinx-build) first.")

    print_hits(BUILD_TEX)

    # 2) 扫主题文件
    for f in THEME_FILES:
        print_hits(f)

    print("\n[diag_pagenum] Done.")
    print("Tip: Look for the LAST occurrence of \\fancyfoot[...] or \\pagestyle{...} "
          "in manual_demo.tex — that is usually the final override.")


if __name__ == "__main__":
    main()