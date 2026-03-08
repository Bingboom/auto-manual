#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import glob
from pathlib import Path

from tools.config_pages import CsvPage, parse_config_pages_or_raise
from tools.phase1.builder import BuildPaths, BuildSelector, Phase1Builder
from tools.phase1.renderers import apply_vars
from tools.utils.path_utils import get_paths
from tools.utils.targets import (
    config_uses_token,
    format_tokenized,
    resolve_build_model,
    resolve_sku_from_inputs,
)

paths = get_paths()


def format_tokenized_value(text: str, sku: str | None, model: str | None) -> str:
    return format_tokenized(text, sku, model)


def resolve_config_path(base_dir: Path, value: str, sku: str | None, model: str | None) -> Path:
    rendered = format_tokenized_value(value, sku, model)
    path = Path(rendered)
    if path.is_absolute():
        return path
    return base_dir / path


def resolve_optional_config_path(
    base_dir: Path,
    value: str | None,
    sku: str | None,
    model: str | None,
) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return resolve_config_path(base_dir, value.strip(), sku, model)


def resolve_csv_include_rst_path(page: CsvPage, lang: str, sku: str | None, model: str | None) -> Path:
    page_name = page.page
    if page.include_dir is None:
        rel = f"{page_name}_{lang}.rst"
    else:
        rel = str(Path(format_tokenized_value(page.include_dir, sku, model)) / f"{page_name}_{lang}.rst")
    return paths.docs_dir / rel


def load_rst_substitutions(conf_base_path: Path) -> dict[str, str]:
    substitutions: dict[str, str] = {}
    if not conf_base_path.exists():
        return substitutions

    for line in conf_base_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith(".. |") or "| replace::" not in line:
            continue
        head, value = line.split("| replace::", 1)
        key = head.removeprefix(".. |").strip()
        substitutions[key] = value.strip()
    return substitutions


def apply_rst_substitutions(
    text: str,
    substitutions: dict[str, str],
    vars_map: dict[str, str],
) -> str:
    out = apply_vars(text, vars_map)
    for key, value in substitutions.items():
        out = out.replace(f"|{key}|", value)
    return out


def resolve_reference_doc(reference_value: str | None, *, root: Path | None = None) -> Path | None:
    if not reference_value:
        return None

    candidate = reference_value.strip()
    if not candidate:
        return None

    root_dir = root or paths.root
    has_glob = any(ch in candidate for ch in "*?[")
    if has_glob:
        pattern = candidate
        if not Path(pattern).is_absolute():
            pattern = str(root_dir / pattern)
        matches = sorted(glob.glob(pattern))
        if not matches:
            raise RuntimeError(f"Word reference doc did not match any files: {candidate}")
        return Path(matches[0])

    path = Path(candidate)
    if not path.is_absolute():
        path = root_dir / path
    if not path.exists():
        raise RuntimeError(f"Word reference doc not found: {path}")
    return path


def derive_word_title(
    build_cfg: dict,
    reference_doc: Path | None,
    substitutions: dict[str, str],
    vars_map: dict[str, str],
) -> str:
    configured = (build_cfg.get("word_title") or "").strip()
    if configured:
        return apply_rst_substitutions(configured, substitutions, vars_map).replace("\xa0", " ")

    if reference_doc is not None:
        return reference_doc.stem.replace("\xa0", " ")

    product_name = substitutions.get("PRODUCT_NAME") or vars_map.get("product_name")
    if product_name:
        return f"{product_name} User Manual"
    return "User Manual"


def load_word_context(
    cfg: dict,
    sku: str | None,
    model: str | None,
) -> tuple[Phase1Builder, dict[str, dict[str, str]]]:
    base_paths = BuildPaths.from_root(paths.root)
    cfg_paths_raw = cfg.get("paths", {})
    cfg_paths = cfg_paths_raw if isinstance(cfg_paths_raw, dict) else {}
    spec_master_cfg = cfg_paths.get("spec_master_csv")
    spec_footnotes_cfg = cfg_paths.get("spec_footnotes_csv")
    spec_master_csv = (
        resolve_config_path(paths.root, spec_master_cfg.strip(), sku, model)
        if isinstance(spec_master_cfg, str) and spec_master_cfg.strip()
        else base_paths.spec_master_csv
    )
    spec_footnotes_csv = (
        resolve_optional_config_path(paths.root, spec_footnotes_cfg, sku, model)
        if isinstance(spec_footnotes_cfg, str)
        else base_paths.spec_footnotes_csv
    )

    build_paths = BuildPaths(
        root=base_paths.root,
        page_registry=base_paths.page_registry,
        content_blocks=base_paths.content_blocks,
        product_variables=base_paths.product_variables,
        template_dir=base_paths.template_dir,
        output_dir=base_paths.output_dir,
        spec_master_csv=spec_master_csv,
        spec_footnotes_csv=spec_footnotes_csv,
    )
    builder = Phase1Builder(build_paths)
    vars_by_sku = builder._load_vars_by_sku()
    return builder, vars_by_sku


def ensure_csv_page_rsts(cfg: dict, builder: Phase1Builder, sku: str | None, model: str | None) -> None:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    build_langs = list(build_cfg.get("languages", ["en"]))
    pages_cfg = parse_config_pages_or_raise(
        cfg.get("pages"),
        default_languages=build_langs,
        error_prefix="config.pages",
    )

    page_ids: set[str] = set()
    langs: set[str] = set()
    for page in pages_cfg:
        if not isinstance(page, CsvPage):
            continue
        page_ids.add(page.page)
        for lang in page.langs:
            langs.add(str(lang))

    if not page_ids:
        return

    selector = BuildSelector(
        skus={sku} if sku else None,
        models={model} if model else None,
        pages=page_ids,
        langs=langs or None,
    )
    builder.build(selector, strict_renderer=True)


def _pick_model_from_vars(vars_map: dict[str, str]) -> str:
    for key in ("model", "product_model", "model_no", "model_number", "Model"):
        value = (vars_map.get(key) or "").strip()
        if value:
            return value
    return ""


def pick_vars_map(
    vars_by_sku: dict[str, dict[str, str]],
    sku: str | None,
    model: str | None,
) -> dict[str, str]:
    if sku:
        return vars_by_sku.get(sku, {})
    if model:
        matched = [
            vars_map
            for vars_map in vars_by_sku.values()
            if _pick_model_from_vars(vars_map) == model
        ]
        if len(matched) == 1:
            return matched[0]
    return {}


def _config_uses_sku_token(cfg: dict) -> bool:
    return config_uses_token(
        cfg,
        "sku",
        include_rst_include=True,
        paths_keys=("spec_master_csv", "spec_footnotes_csv"),
        build_keys=("word_reference_doc",),
    )


def resolve_bundle_targets(cfg: dict, sku: str | None, model: str | None) -> tuple[str | None, str | None]:
    picked_model = resolve_build_model(cfg, model)
    if sku and sku.strip():
        return sku.strip(), picked_model

    if not _config_uses_sku_token(cfg):
        return None, picked_model

    picked_sku = resolve_sku_from_inputs(
        cfg,
        arg_sku=None,
        arg_model=picked_model,
        root=paths.root,
        requires_sku_token=True,
        log_prefix=None,
    )
    return picked_sku, picked_model

