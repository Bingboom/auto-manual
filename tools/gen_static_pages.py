#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_OVERVIEW = ROOT / "docs" / "overview.rst"

def main() -> None:
    OUT_OVERVIEW.write_text(
        "\n".join([
            "",
            ".. raw:: latex",
            "",
            "   \\includepdf[pages=1-,fitpaper=true,pagecommand={\\thispagestyle{fancy}}]{product_overview.pdf}",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"[gen_static_pages] Wrote: {OUT_OVERVIEW}")

if __name__ == "__main__":
    main()