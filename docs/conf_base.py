# docs/conf_base.py
# -*- coding: utf-8 -*-

from __future__ import annotations
from pathlib import Path

# --- project-independent defaults ---
project = ""
author = ""
extensions: list[str] = []
exclude_patterns = ["_build", "templates/*"]

# 默认入口（子类可覆盖）
master_doc = "index"

latex_engine = "xelatex"
latex_domain_indices = False
latex_show_urls = "no"

# --- HTML output (primary reading version) ---
html_theme = "furo"  # 推荐：furo（现代、干净）；也可用 sphinx_rtd_theme
html_static_path = ["_static"]
html_css_files = ["hb_manual.css",'hb_paged.css']
html_js_files = ["hb_manual.js",'hb_paged.js']  # 可先留空文件
html_title = "User Manual"

# 把 assets 暴露给 HTML（封面/overview/pdf_insert 用）
# 方案 A：直接把 renderers/latex/assets 作为 html_extra_path 暴露（最省事）
html_extra_path = ["renderers/latex/assets"]


# 渲染器主题文件（放在 docs/renderers/latex/ 下）
latex_additional_files = [
    "renderers/latex/assets/cover-en.pdf",
    "renderers/latex/assets/product_overview-en.pdf",
    "renderers/latex/assets/product_overview-fr.pdf",
    "renderers/latex/assets/product_overview-es.pdf",
    "renderers/latex/theme.tex",
    "renderers/latex/colors.tex",
    "renderers/latex/type_system.tex",
    "renderers/latex/tools.tex",
    "renderers/latex/params.tex",
    "renderers/latex/assets/warning_lockup.png",
    "renderers/latex/layout_templates.tex",
    "renderers/latex/layout_core.tex",
    "renderers/latex/components_base.tex",
    "renderers/latex/components_safety.tex",
    "renderers/latex/page_fit.tex",
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
    "classoptions": ",twoside,openany",

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
% so we input by filename (NOT renderers/latex/theme.tex).
% ============================
\input{theme.tex}
""",

}

# 可选：一个 helper，便于子类 append preamble
def append_preamble(extra_tex: str) -> None:
    """Append LaTeX code to latex_elements['preamble']."""
    latex_elements["preamble"] = (latex_elements.get("preamble", "") or "") + "\n" + extra_tex


# ✅ NEW: enable \includepdf
append_preamble(r"""
\usepackage{pdfpages}
""")

print("[conf_base] LOADED conf_base.py")
