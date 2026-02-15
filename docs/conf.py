# -*- coding: utf-8 -*-

# =========================
# Sphinx basics
# =========================
project = ""
author = ""
extensions = []
exclude_patterns = ["_build"]

# 直接以 safety.rst 为入口（只输出安全页 Demo）
master_doc = "safety"

# =========================
# LaTeX output
# =========================
latex_engine = "xelatex"

# howto 比 manual 更干净（不会强制 CHAPTER/Contents 那套）
latex_documents = [
    ("safety", "safety_demo.tex", "", "", "howto"),
]

latex_domain_indices = False
latex_show_urls = "no"

# 关键：提前把 xcolor 切到 CMYK 模式
# Sphinx 自己会加载 xcolor，所以要用 PassOptionsToPackage 抢先传参
latex_elements = {
    # 小开本：130 x 185 mm（你规范里写的）
    # 注意：papersize 这里不用 a4paper，而是自定义 geometry
    "papersize": "a4paper",
    "pointsize": "10pt",

    # 禁目录
    "tableofcontents": "",

    # 让 xcolor 走 CMYK
    "passoptionstopackages": r"\PassOptionsToPackage{cmyk}{xcolor}",

    "preamble": r"""
% ==================================================
% Packages
% ==================================================
\usepackage{geometry}
\usepackage{fontspec}
\usepackage{xcolor}
\usepackage[most]{tcolorbox}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{multicol}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{fancyhdr}
\usepackage{tikz}

% ==================================================
% Page size & margins (SPEC)
% - Size: 130 x 185 mm
% - Margin: 10 mm
% ==================================================
\geometry{
  paperwidth=130mm,
  paperheight=185mm,
  left=10mm,
  right=10mm,
  top=10mm,
  bottom=10mm
}

% ==================================================
% Typography (SPEC)
% - Body >= 5pt, leading >= 120%
% - Page number 6pt
% - Use Sans, clean, print-friendly
% ==================================================
\setmainfont{Helvetica}
\setsansfont{Helvetica}

% 将“正文基准字号”压到更接近小开本手册密度（你样张就是偏小字号）
% 这里把 normalsize 设为 6.5pt，行距 120%
\makeatletter
\renewcommand\normalsize{%
  \@setfontsize\normalsize{6.5pt}{7.8pt}% 120%
  \abovedisplayskip 4pt \@plus1pt \@minus1pt
  \belowdisplayskip 4pt \@plus1pt \@minus1pt
  \abovedisplayshortskip 3pt \@plus1pt
  \belowdisplayshortskip 3pt \@plus1pt \@minus1pt
  \let\@listi\@listI
}
\normalsize
\makeatother

\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}

% ==================================================
% CMYK Colors (SPEC)
% - 90% single black printing target
% - Grays use K-only; avoid CMY to keep single-plate feel
% - K 5% background for note/table shading
% ==================================================
\definecolor{BrandDark}{cmyk}{0,0,0,0.80}   % 深灰条（K-only）
\definecolor{TextK90}{cmyk}{0,0,0,0.90}     % 正文更“单黑印刷”观感
\definecolor{LineK40}{cmyk}{0,0,0,0.40}     % 外框线
\definecolor{LineK20}{cmyk}{0,0,0,0.20}     % 内框线
\definecolor{BgK05}{cmyk}{0,0,0,0.05}       % 灰底 K5%
\definecolor{AccentBlue}{cmyk}{0.90,0.55,0,0.60} % 规范里“蓝色标题”的近似（如需精确按品牌给值）

\color{TextK90}

% ==================================================
% Footer page number (SPEC: 6pt Regular)
% ==================================================
\fancyhf{}
\pagestyle{fancy}
\fancyfoot[C]{\fontsize{6pt}{7.2pt}\selectfont\thepage}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% ==================================================
% Hard-disable Sphinx TOC (avoid \sphinxtableofcontents)
% ==================================================
\makeatletter
\@ifundefined{sphinxtableofcontents}{}{%
  \renewcommand{\sphinxtableofcontents}{}
}
\makeatother

% ==================================================
% Heading styles (SPEC)
% 1) Level-1: dark rounded bar, Bold, >= 9pt
% 2) Level-2: bullet + bold, >= 7pt
% 3) Level-3: bullet + bold, >= 7pt
% ==================================================

% --- Level-1: Sphinx usually uses \section for top-level in howto
\titleformat{\section}
  {\bfseries\color{white}\fontsize{9pt}{10.8pt}\selectfont}
  {}
  {0pt}
  {%
    \begin{tcolorbox}[
      colback=BrandDark,
      colframe=BrandDark,
      arc=3mm,
      left=5mm,right=5mm,top=2.2mm,bottom=2.2mm,
      boxrule=0pt,
      width=\textwidth
    ]\strut
  }
  [\end{tcolorbox}\vspace{3mm}]
\titlespacing*{\section}{0pt}{0pt}{0pt}

% --- Level-2: \subsection => bullet + bold 7pt
\titleformat{\subsection}
  {\bfseries\fontsize{7pt}{8.4pt}\selectfont}
  {\textbullet}
  {0.7em}
  {}
\titlespacing*{\subsection}{0pt}{2mm}{1mm}

% --- Level-3: \subsubsection => bullet + bold 7pt (slightly smaller spacing)
\titleformat{\subsubsection}
  {\bfseries\fontsize{7pt}{8.4pt}\selectfont}
  {\textbullet}
  {0.7em}
  {}
\titlespacing*{\subsubsection}{0pt}{1.5mm}{0.8mm}

% ==================================================
% Custom components for your safety page
% - WARNING box
% - Operating pill bar
% - Two-column list
% ==================================================

% Warning triangle icon (filled K-only)
\newcommand{\warnicon}{%
\begin{tikzpicture}[scale=1.15,baseline=-0.25em]
\draw[fill=BrandDark,draw=BrandDark] (0,0)--(1,0)--(0.5,0.866)--cycle;
\node[color=white,font=\bfseries\fontsize{7pt}{7pt}\selectfont] at (0.5,0.33) {!};
\end{tikzpicture}%
}

% WARNING box (outer frame stronger)
\newtcolorbox{safetywarningbox}{%
  enhanced,
  colback=white,
  colframe=LineK40,
  arc=2.5mm,
  boxrule=0.8pt,
  left=4mm,right=4mm,top=3mm,bottom=3mm,
  before skip=0mm, after skip=3mm,
}

\newcommand{\safetywarning}[2]{%
\begin{safetywarningbox}
\begin{tabularx}{\textwidth}{@{}l l X@{}}
{\warnicon} &
{\bfseries\fontsize{9pt}{10.8pt}\selectfont #1} &
{\bfseries\fontsize{6.5pt}{7.8pt}\selectfont\MakeUppercase{#2}}
\end{tabularx}
\end{safetywarningbox}
}

% OPERATING INSTRUCTIONS bar
\newcommand{\safetysubbar}[1]{%
  \begin{tcolorbox}[
    colback=BrandDark,
    colframe=BrandDark,
    arc=3mm,
    left=5mm,right=5mm,top=2.2mm,bottom=2.2mm,
    boxrule=0pt,
    width=\textwidth
  ]
  {\color{white}\bfseries\fontsize{9pt}{10.8pt}\selectfont\MakeUppercase{#1}}
  \end{tcolorbox}
  \vspace{2mm}
}

% Two-column list (SPEC-like density)
\setlength{\columnsep}{10mm}
\setlist[itemize]{leftmargin=*, itemsep=1.5mm, topsep=0mm, parsep=0mm}

\newenvironment{safetytwocol}{%
  \begin{multicols}{2}
  \fontsize{6.5pt}{7.8pt}\selectfont
}{%
  \end{multicols}
}

% ==================================================
% NOTE / Callout style (SPEC)
% - Background K5%
% - "Note" tag + body
% ==================================================
\newtcolorbox{notebox}{%
  enhanced,
  colback=BgK05,
  colframe=BgK05,
  arc=2.5mm,
  boxrule=0pt,
  left=3mm,right=3mm,top=2.5mm,bottom=2.5mm,
}

% ==================================================
% Table style (SPEC)
% - Outer border >= 0.4pt
% - Inner border >= 0.2pt
% ==================================================
\arrayrulewidth=0.2pt % 内线（>=0.2pt）
\setlength{\tabcolsep}{3.5pt}

% 外框线宽用单独宏包一层（简化：用 tcolorbox 包裹表格实现 0.4pt 外框）
\newtcolorbox{tableframe}{%
  enhanced,
  colback=white,
  colframe=LineK40,
  arc=2mm,
  boxrule=0.4pt, % 外框（>=0.4pt）
  left=0mm,right=0mm,top=0mm,bottom=0mm,
}

% ==================================================
% Rubric styling (SAVE THESE INSTRUCTIONS in blue, Bold)
% ==================================================
\makeatletter
\@ifundefined{sphinxstylerubric}{}{%
  \renewcommand{\sphinxstylerubric}[1]{%
    \par\medskip\noindent
    {\color{AccentBlue}\bfseries\fontsize{7pt}{8.4pt}\selectfont\MakeUppercase{##1}}
    \par\smallskip
  }%
}
\makeatother
""",
}
