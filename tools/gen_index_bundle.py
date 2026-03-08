#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.utils.path_utils import get_paths  # noqa: E402


def load_config(cfg_path: Path) -> dict:
    if not cfg_path.exists():
        raise RuntimeError(f"Config not found: {cfg_path}")

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


def latex_overview_block(file_name: str) -> list[str]:
    return [
        ".. raw:: latex",
        "",
        f"   \\includepdf[pages=1-,fitpaper=true,pagecommand={{\\thispagestyle{{normal}}}}]{{{file_name}}}",
        "",
    ]


def _format_tokenized(text: str, sku: str | None, model: str | None) -> str:
    if "{sku}" in text and not sku:
        raise RuntimeError("config uses '{sku}' but no --sku was provided")
    if "{model}" in text and not model:
        raise RuntimeError("config uses '{model}' but no --model was provided")
    return text.format(sku=sku or "", model=model or "")


def _config_uses_sku_token(cfg: dict) -> bool:
    for page in cfg.get("pages", []):
        if not isinstance(page, dict):
            continue
        ptype = (page.get("type") or "").strip()
        if ptype == "cover_pdf":
            file_name = page.get("file")
            if isinstance(file_name, str) and "{sku}" in file_name:
                return True
        elif ptype == "csv_page":
            include_dir = page.get("include_dir")
            if isinstance(include_dir, str) and "{sku}" in include_dir:
                return True
        elif ptype == "pdf_insert":
            file_map = page.get("file_map")
            if isinstance(file_map, dict):
                for v in file_map.values():
                    if isinstance(v, str) and "{sku}" in v:
                        return True
        elif ptype == "rst_include":
            file_name = page.get("file")
            if isinstance(file_name, str) and "{sku}" in file_name:
                return True
    return False


def _list_skus(product_vars_csv: Path) -> list[str]:
    if not product_vars_csv.exists():
        return []
    skus: set[str] = set()
    with product_vars_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sku = (row.get("sku_id") or "").strip()
            if sku:
                skus.add(sku)
    return sorted(skus)


def _list_skus_by_model(product_vars_csv: Path, model: str) -> list[str]:
    if not product_vars_csv.exists():
        return []
    model_keys = {"model", "product_model", "model_no", "model_number"}
    matched: set[str] = set()
    with product_vars_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sku = (row.get("sku_id") or "").strip()
            key = (row.get("var_key") or "").strip().lower()
            value = (row.get("var_value") or "").strip()
            if not sku or key not in model_keys:
                continue
            if value == model:
                matched.add(sku)
    return sorted(matched)


def resolve_build_model(cfg: dict, arg_model: str | None) -> str | None:
    if arg_model and arg_model.strip():
        return arg_model.strip()
    build_cfg = cfg.get("build", {})
    default_model = build_cfg.get("default_model")
    if isinstance(default_model, str) and default_model.strip():
        return default_model.strip()
    return None


def resolve_build_sku(
    cfg: dict,
    arg_sku: str | None,
    root: Path,
    arg_model: str | None = None,
) -> str | None:
    if arg_sku and arg_sku.strip():
        return arg_sku.strip()

    target_model = resolve_build_model(cfg, arg_model)
    product_vars_csv = root / "data" / "phase1" / "product_variables.csv"

    if target_model:
        matched_skus = _list_skus_by_model(product_vars_csv, target_model)
        if len(matched_skus) == 1:
            picked = matched_skus[0]
            print(
                "[gen_index_bundle] sku not provided, using "
                f"build/default model='{target_model}' -> sku='{picked}'"
            )
            return picked
        if len(matched_skus) > 1:
            raise RuntimeError(
                f"build/default model '{target_model}' maps to multiple SKUs {matched_skus}. "
                "Please pass --sku explicitly."
            )
        raise RuntimeError(
            f"build/default model '{target_model}' was not found in "
            "data/phase1/product_variables.csv "
            "(var_key in: model, product_model, model_no, model_number)."
        )

    if not _config_uses_sku_token(cfg):
        return None

    skus = _list_skus(product_vars_csv)
    if not skus:
        raise RuntimeError(
            "config uses '{sku}' but no SKU was found in data/phase1/product_variables.csv"
        )

    if len(skus) > 1:
        raise RuntimeError(
            "config uses '{sku}' and multiple SKUs are available "
            f"({skus}). Please pass --sku or set build.default_model."
        )

    picked = skus[0]
    print(f"[gen_index_bundle] sku not provided, inferred '{picked}' from product_variables.csv")
    return picked


def _csv_include_path(
    page: dict,
    page_name: str,
    lang: str,
    sku: str | None,
    model: str | None,
) -> str:
    include_dir = page.get("include_dir")
    if include_dir is None:
        return f"{page_name}_{lang}.rst"
    if not isinstance(include_dir, str) or not include_dir.strip():
        raise RuntimeError("csv_page.include_dir must be a non-empty string")

    rendered_dir = _format_tokenized(include_dir.strip(), sku, model)
    return str(Path(rendered_dir) / f"{page_name}_{lang}.rst").replace("\\", "/")


def build_index_from_pages(cfg: dict, sku: str | None = None, model: str | None = None) -> str:
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
            out += latex_cover_block(_format_tokenized(file_name, sku, model))
            saw_cover = True

        elif ptype == "pdf_insert":
            file_map = ensure_mapping(page.get("file_map"), "pdf_insert.file_map")

            plangs = page.get("langs", langs)
            plangs = list(plangs)

            for lang in plangs:
                if lang not in file_map:
                    raise RuntimeError(f"pdf_insert.file_map missing lang '{lang}'")
                if not isinstance(file_map[lang], str) or not file_map[lang]:
                    raise RuntimeError(f"pdf_insert.file_map['{lang}'] must be non-empty string")

                out += latex_overview_block(_format_tokenized(file_map[lang], sku, model))

        elif ptype == "csv_page":
            page_name = page.get("page")
            if not isinstance(page_name, str) or not page_name:
                raise RuntimeError("csv_page requires 'page'")

            plangs = page.get("langs", langs)
            plangs = list(plangs)

            for lang in plangs:
                out += latex_apply_lang(lang)
                include_path = _csv_include_path(page, page_name, lang, sku, model)
                out += [f".. include:: {include_path}", ""]

        elif ptype == "rst_include":
            file_name = page.get("file")
            if not isinstance(file_name, str) or not file_name.strip():
                raise RuntimeError("rst_include requires non-empty 'file'")
            lang = page.get("lang")
            if isinstance(lang, str) and lang.strip():
                out += latex_apply_lang(lang.strip())
            out += [f".. include:: {_format_tokenized(file_name.strip(), sku, model)}", ""]

        else:
            raise RuntimeError(f"Unsupported page type: {ptype}")

    # Safety: if no cover was specified, still start numbering when document starts.
    if not saw_cover:
        # Not enforced; just a hint for future.
        pass

    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml", help="Path to config yaml")
    ap.add_argument("--sku", default=None, help="Optional SKU for tokenized include/file paths")
    ap.add_argument("--model", default=None, help="Optional product model for SKU resolving")
    args = ap.parse_args()

    paths = get_paths()
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path

    cfg = load_config(cfg_path)

    doc_type = cfg.get("doc_type", "manual_bundle")
    if doc_type != "manual_bundle":
        raise RuntimeError(f"gen_index_bundle supports doc_type=manual_bundle only, got: {doc_type}")

    target_model = resolve_build_model(cfg, args.model)
    explicit_sku = (args.sku or "").strip() or None
    if explicit_sku:
        target_sku = explicit_sku
    elif _config_uses_sku_token(cfg) or not target_model:
        target_sku = resolve_build_sku(cfg, None, paths.root, args.model)
    else:
        target_sku = None
    index_text = build_index_from_pages(cfg, sku=target_sku, model=target_model)

    out_path = paths.docs_dir / "index.rst"
    out_path.write_text(index_text, encoding="utf-8")
    print(f"[gen_index_bundle] Wrote: {out_path}")


if __name__ == "__main__":
    main()
