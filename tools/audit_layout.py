#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "docs" / "_build" / "latex"

# match 12mm, 0.55pt, 1.2em, etc.
PAT = re.compile(r"(?<![A-Za-z])(\d+(?:\.\d+)?)(mm|pt|em)\b")

# ignore patterns that are already parameterized via csname HB...
IGNORE = [
    r"\\csname\s+HB",
    r"HB[0-9A-Za-z_]+",  # for debugging
]

def main():
    if not BUILD.exists():
        print(f"[audit] Build folder not found: {BUILD}")
        return

    hits = []
    for p in BUILD.glob("*.tex"):
        txt = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i, line in enumerate(txt, 1):
            if any(re.search(x, line) for x in IGNORE):
                continue
            for m in PAT.finditer(line):
                val = m.group(0)
                # skip very common harmless patterns if you want
                hits.append((p.name, i, val, line.strip()))

    hits.sort()
    print(f"[audit] Found {len(hits)} hard-coded lengths in build tex.")
    for fn, ln, val, line in hits[:200]:
        print(f"{fn}:{ln:<4} {val:<8} {line}")

    if len(hits) > 200:
        print(f"... ({len(hits)-200} more)")

if __name__ == "__main__":
    main()
