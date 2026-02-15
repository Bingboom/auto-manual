# docs/conf.py
# -*- coding: utf-8 -*-

# docs/conf.py
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

# ✅ 让 Sphinx 在执行 conf.py 时能 import 同目录模块
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from conf_base import *  # noqa: F403


# 2) 覆盖：项目入口 / 输出
master_doc = "safety"  # 只出安全页 demo

latex_documents = [
    ("safety", "safety_demo.tex", "", "", "howto"),
]

# 3) 覆盖：如果你不想生成任何索引
latex_domain_indices = False

# 4)（可选）额外的 LaTeX patch：只放与本 demo 强相关的东西
# 例如：有时你想临时加一段 debug 或小修
append_preamble(r"""
% (optional) extra patch for this project only
% e.g. \tracingall
""")  # noqa: F405
