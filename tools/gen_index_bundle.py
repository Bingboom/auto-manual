#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.utils.path_utils import get_paths  # noqa: E402


def load_config() -> dict:
    paths = get_paths()
    cfg_path = paths.config_yaml
    if not cfg_path.exists():
        raise RuntimeError(f"config.yaml not found: {cfg_path}")

    import yaml  # requires PyYAML

    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def ensure_mapping(obj: Any, name: str) -> dict:
    if not isinstance(obj, dict):
        raise RuntimeError(f"{name} must be a mapping")
    return obj


def ensure_list(obj: Any, name: str) -> list:
    if not isinstance(obj, list):
        raise RuntimeError(f"{name} must be a list")
    return obj


def latex_cover_block(file_name: str) -> list[str]:
    return [
        ".. raw:: latex",
        "",
        f"   \\includepdf[pages=1-,fitpaper=true,pagecommand={{\\thispagestyle{{empty}}}}]{{{file_name}}}",
        "   \\clearpage",
        "   \\pagenumbering{arabic}",
        "   \\setcounter{page}{1}",
        "",
    ]


def latex_apply_lang(lang: str) -> list[str]:
    return [
        ".. raw:: latex",
        "",
        f"   \\HBApplyLang{{{lang}}}",
        "",
    ]


def include_safety(lang: str) -> list[str]:
    return [
        f".. include:: safety_{lang}.rst",
        "",
    ]


def latex_overview_block(file_name: str) -> list[str]:
    return [
        ".. raw:: latex",
        "",
        f"   \\includepdf[pages=1-,fitpaper=true,pagecommand={{\\thispagestyle{{normal}}}}]{{{file_name}}}",
        "",
    ]


def build_index_from_pages(cfg: dict) -> str:
    langs = cfg.get("build", {}).get("languages", ["en", "fr", "es"])
    langs = list(langs)

    pages = ensure_list(cfg.get("pages"), "config.pages")

    out: list[str] = []
    saw_cover = False

    for i, page in enumerate(pages, start=1):
        page = ensure_mapping(page, f"config.pages[{i}]")
        ptype = page.get("type")

        if ptype == "cover_pdf":
            file_name = page.get("file")
            if not isinstance(file_name, str) or not file_name:
                raise RuntimeError("cover_pdf page requires 'file'")
            out += latex_cover_block(file_name)
            saw_cover = True

        elif ptype == "safety_rst":
            # If langs specified here, use it; else use build.languages
            plangs = page.get("langs", langs)
            plangs = list(plangs)
            for lang in plangs:
                out += latex_apply_lang(lang)
                out += include_safety(lang)

        elif ptype == "overview_pdf":
            file_map = ensure_mapping(page.get("file_map"), "overview_pdf.file_map")
            # default langs from build.languages
            plangs = page.get("langs", langs)
            plangs = list(plangs)
            for lang in plangs:
                if lang not in file_map:
                    raise RuntimeError(f"overview_pdf.file_map missing lang '{lang}'")
                out += latex_overview_block(file_map[lang])

        else:
            raise RuntimeError(f"Unsupported page type: {ptype}")

    # Safety: if no cover was specified, still start numbering when document starts.
    if not saw_cover:
        # Not enforced; just a hint for future.
        pass

    return "\n".join(out) + "\n"


def main() -> None:
    cfg = load_config()

    doc_type = cfg.get("doc_type", "manual_bundle")
    if doc_type != "manual_bundle":
        raise RuntimeError(f"gen_index_bundle supports doc_type=manual_bundle only, got: {doc_type}")

    index_text = build_index_from_pages(cfg)

    paths = get_paths()
    out_path = paths.docs_dir / "index.rst"
    out_path.write_text(index_text, encoding="utf-8")
    print(f"[gen_index_bundle] Wrote: {out_path}")


if __name__ == "__main__":
    main()