# docs/conf.py
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from conf_base import *  # noqa: F403

# ✅ 用整本入口
master_doc = "index"

latex_documents = [
    ("index", "manual_demo.tex", "", "", "howto"),
]

latex_domain_indices = False