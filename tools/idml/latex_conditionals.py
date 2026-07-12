"""Select the content branch hidden from LaTeX by simple conditionals."""
from __future__ import annotations

import re


def active_lines(lines: list[str], tags: set[str]) -> list[str]:
    """Drop RST fallback copy bracketed by standalone ``\\iffalse``/``\\fi``."""
    if "latex" not in tags:
        return lines
    selected: list[str] = []
    hidden = False
    for line in lines:
        if not hidden and re.search(r"\\iffalse\b", line):
            hidden = True
        elif hidden and re.search(r"\\fi\b", line):
            hidden = False
        elif not hidden:
            selected.append(line.replace(r"\HBPageBreak", r"\HBPageBreak{}"))
    return selected
