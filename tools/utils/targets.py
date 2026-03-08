#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

MODEL_VAR_KEYS = {"model", "product_model", "model_no", "model_number"}


def format_tokenized(text: str, sku: str | None, model: str | None) -> str:
    if "{sku}" in text and not sku:
        raise RuntimeError("config uses '{sku}' but no --sku was provided")
    if "{model}" in text and not model:
        raise RuntimeError("config uses '{model}' but no --model was provided")
    return text.format(sku=sku or "", model=model or "")


def config_uses_token_in_pages(
    cfg: dict[str, Any],
    token: str,
    *,
    include_rst_include: bool = False,
) -> bool:
    placeholder = f"{{{token}}}"
    for page in cfg.get("pages", []):
        if not isinstance(page, dict):
            continue
        ptype = (page.get("type") or "").strip()
        if ptype == "cover_pdf":
            file_name = page.get("file")
            if isinstance(file_name, str) and placeholder in file_name:
                return True
        elif ptype == "csv_page":
            include_dir = page.get("include_dir")
            if isinstance(include_dir, str) and placeholder in include_dir:
                return True
        elif ptype == "pdf_insert":
            file_map = page.get("file_map")
            if isinstance(file_map, dict):
                for value in file_map.values():
                    if isinstance(value, str) and placeholder in value:
                        return True
        elif include_rst_include and ptype == "rst_include":
            file_name = page.get("file")
            if isinstance(file_name, str) and placeholder in file_name:
                return True
    return False


def config_uses_token(
    cfg: dict[str, Any],
    token: str,
    *,
    include_rst_include: bool = False,
    paths_keys: Iterable[str] = (),
    build_keys: Iterable[str] = (),
) -> bool:
    placeholder = f"{{{token}}}"
    if config_uses_token_in_pages(cfg, token, include_rst_include=include_rst_include):
        return True

    paths_cfg = cfg.get("paths", {})
    if isinstance(paths_cfg, dict):
        for key in paths_keys:
            value = paths_cfg.get(key)
            if isinstance(value, str) and placeholder in value:
                return True

    build_cfg = cfg.get("build", {})
    if isinstance(build_cfg, dict):
        for key in build_keys:
            value = build_cfg.get(key)
            if isinstance(value, str) and placeholder in value:
                return True

    return False


def list_skus(product_vars_csv: Path) -> list[str]:
    if not product_vars_csv.exists():
        return []
    skus: set[str] = set()
    with product_vars_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sku = (row.get("sku_id") or "").strip()
            if sku:
                skus.add(sku)
    return sorted(skus)


def list_skus_by_model(
    product_vars_csv: Path,
    model: str,
    *,
    model_var_keys: set[str] | None = None,
) -> list[str]:
    if not product_vars_csv.exists():
        return []
    keys = model_var_keys or MODEL_VAR_KEYS
    matched: set[str] = set()
    with product_vars_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sku = (row.get("sku_id") or "").strip()
            key = (row.get("var_key") or "").strip().lower()
            value = (row.get("var_value") or "").strip()
            if not sku or key not in keys:
                continue
            if value == model:
                matched.add(sku)
    return sorted(matched)


def resolve_build_model(cfg: dict[str, Any], arg_model: str | None) -> str | None:
    if arg_model and arg_model.strip():
        return arg_model.strip()
    build_cfg = cfg.get("build", {})
    if not isinstance(build_cfg, dict):
        return None
    default_model = build_cfg.get("default_model")
    if isinstance(default_model, str) and default_model.strip():
        return default_model.strip()
    return None


def resolve_sku_from_inputs(
    cfg: dict[str, Any],
    arg_sku: str | None,
    arg_model: str | None,
    root: Path,
    *,
    requires_sku_token: bool,
    log_prefix: str | None = None,
) -> str | None:
    if arg_sku and arg_sku.strip():
        return arg_sku.strip()

    product_vars_csv = root / "data" / "phase1" / "product_variables.csv"
    target_model = resolve_build_model(cfg, arg_model)

    if target_model:
        matched_skus = list_skus_by_model(product_vars_csv, target_model)
        if len(matched_skus) == 1:
            picked = matched_skus[0]
            if log_prefix:
                print(
                    f"[{log_prefix}] sku not provided, using "
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

    if not requires_sku_token:
        return None

    skus = list_skus(product_vars_csv)
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
    if log_prefix:
        print(f"[{log_prefix}] sku not provided, inferred '{picked}' from product_variables.csv")
    return picked
