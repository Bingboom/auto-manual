#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.word_bundle_common import derive_word_title, paths, resolve_bundle_targets, resolve_reference_doc
from tools.word_bundle_docx import export_word_from_bundle
from tools.word_bundle_html import render_safety_word_html, render_spec_word_html


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.us.yaml", help="Path to config yaml")
    ap.add_argument("--model", default=None, help="Optional model for spec filtering")
    ap.add_argument("--region", default=None, help="Optional region for spec filtering")
    ap.add_argument("--output", default="manual_bundle.docx", help="Output docx path")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path

    import yaml  # type: ignore

    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    target_model, target_region = resolve_bundle_targets(
        cfg,
        args.model,
        args.region,
    )
    docx_path = export_word_from_bundle(cfg, target_model, target_region, args.output)
    print(f"[word_bundle] Done. DOCX: {docx_path}")


if __name__ == "__main__":
    main()
