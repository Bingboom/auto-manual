#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from pathlib import Path

from tools.word_bundle_common import derive_word_title, paths, resolve_bundle_targets, resolve_reference_doc
from tools.word_bundle_docx import export_word_from_bundle
from tools.word_bundle_html import render_safety_word_html, render_spec_word_html


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml", help="Path to config yaml")
    ap.add_argument("--sku", default=None, help="Optional SKU for word bundle")
    ap.add_argument("--model", default=None, help="Optional model for spec filtering / SKU resolving")
    ap.add_argument("--output", default="manual_bundle.docx", help="Output docx path")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path

    import yaml  # type: ignore

    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    target_sku, target_model = resolve_bundle_targets(cfg, args.sku, args.model)
    docx_path = export_word_from_bundle(cfg, target_sku, target_model, args.output)
    print(f"[word_bundle] Done. DOCX: {docx_path}")


if __name__ == "__main__":
    main()

