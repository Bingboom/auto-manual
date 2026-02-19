# docs/conf_base.py
# -*- coding: utf-8 -*-

from __future__ import annotations
from pathlib import Path

# --- project-independent defaults ---
project = ""
author = ""
extensions: list[str] = []
exclude_patterns = ["_build"]

# 默认入口（子类可覆盖）
master_doc = "index"

latex_engine = "xelatex"
latex_domain_indices = False
latex_show_urls = "no"

# 主题文件（放在 docs/latex_theme/ 下）
latex_additional_files = [
    "latex_theme/theme.tex",
    "latex_theme/colors.tex",
    "latex_theme/type_system.tex",
    "latex_theme/tools.tex",
    "latex_theme/params.tex", 
    "latex_theme/assets/warning_lockup.png",  
    "latex_theme/layout.tex",
    "latex_theme/components.tex",
    "latex_theme/components_base.tex",
    "latex_theme/components_safety.tex",
]

# latex_documents 默认（子类可覆盖）
latex_documents = [
    (master_doc, "output.tex", "", "", "howto"),
]

# --- core latex elements (base) ---
latex_elements = {
    "papersize": "a4paper",
    "pointsize": "10pt",
    # 禁目录（同时避免 TOC 相关 error）
    "tableofcontents": "",

    # 让 xcolor 走 CMYK（必须抢先传参）
    "passoptionstopackages": r"\PassOptionsToPackage{cmyk}{xcolor}",

  "preamble": r"""
% ============================
% Kill title / toc AFTER sphinx defines them
% ============================
\usepackage{etoolbox}

\AtBeginDocument{%
  \makeatletter
  \ifdef{\sphinxmaketitle}{\renewcommand{\sphinxmaketitle}{}}{}%
  \ifdef{\sphinxtableofcontents}{\renewcommand{\sphinxtableofcontents}{}}{}%
  \renewcommand{\maketitle}{}%
  \renewcommand{\today}{}%
  \makeatother
}

% ============================
% Load separated theme
% NOTE: Sphinx copies additional files to _build/latex root,
% so we input by filename (NOT latex_theme/theme.tex).
% ============================
\input{theme.tex}
""",

}

# 可选：一个 helper，便于子类 append preamble
def append_preamble(extra_tex: str) -> None:
    """Append LaTeX code to latex_elements['preamble']."""
    latex_elements["preamble"] = (latex_elements.get("preamble", "") or "") + "\n" + extra_tex
