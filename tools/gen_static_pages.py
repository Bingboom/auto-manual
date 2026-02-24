#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from pathlib import Path
import sys

# ------------------------------------------------------------
# ① 注入路径（与 Auto-Doc 体系一致）
# ------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
TOOLS_DIR = THIS_FILE.parent
PROJECT_ROOT = TOOLS_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(TOOLS_DIR))

# ------------------------------------------------------------
# ② 使用统一路径系统（禁止硬编码）
# ------------------------------------------------------------
from tools.utils import path_utils as paths

ROOT = paths.ROOT

# 输出 rst 文件
OUT_OVERVIEW = ROOT / "docs" / "overview.rst"

# product_overview.pdf 建议放在 static 目录
PDF_PATH = paths.static_images_path() / "product_overview.pdf"


def main() -> None:

    if not PDF_PATH.exists():
        raise FileNotFoundError(f"未找到 PDF 文件: {PDF_PATH}")

    # ⚠️ LaTeX 必须使用 POSIX 路径（避免 Windows 反斜杠问题）
    pdf_latex_path = PDF_PATH.as_posix()

    content = "\n".join([
        "",
        ".. raw:: latex",
        "",
        f"   \\includepdf[pages=1-,fitpaper=true,pagecommand={{\\thispagestyle{{fancy}}}}]{{{pdf_latex_path}}}",
        "",
    ])

    OUT_OVERVIEW.write_text(content, encoding="utf-8")

    print(f"[gen_static_pages] Wrote: {OUT_OVERVIEW}")


if __name__ == "__main__":
    main()