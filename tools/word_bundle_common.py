#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import glob
from pathlib import Path

from tools.config_pages import CsvPage, parse_config_pages_or_raise
from tools.phase1.builder import BuildPaths, BuildSelector, Phase1Builder
from tools.phase1.renderers import apply_vars
from tools.utils.path_utils import get_paths
from tools.utils.spec_master import resolve_product_name_from_spec_master
from tools.utils.targets import (
    format_tokenized,
    resolve_build_model,
    resolve_build_region,
)

paths = get_paths()


def format_tokenized_value(
    text: str,
    model: str | None,
    region: str | None,
) -> str:
    return format_tokenized(text, None, model, region)


def resolve_config_path(
    base_dir: Path,
    value: str,
    model: str | None,
    region: str | None,
) -> Path:
    rendered = format_tokenized_value(value, model, region)
    path = Path(rendered)
    if path.is_absolute():
        return path
    return base_dir / path


def resolve_optional_config_path(
    base_dir: Path,
    value: str | None,
    model: str | None,
    region: str | None,
) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return resolve_config_path(base_dir, value.strip(), model, region)


def resolve_csv_include_rst_path(
    page: CsvPage,
    lang: str,
    model: str | None,
    region: str | None,
) -> Path:
    page_name = page.page
    if page.include_dir is None:
        rel = f"{page_name}_{lang}.rst"
    else:
        rel = str(
            Path(format_tokenized_value(page.include_dir, model, region)) / f"{page_name}_{lang}.rst"
        )
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
    model: str | None,
    region: str | None,
) -> Phase1Builder:
    base_paths = BuildPaths.from_root(paths.root)
    cfg_paths_raw = cfg.get("paths", {})
    cfg_paths = cfg_paths_raw if isinstance(cfg_paths_raw, dict) else {}
    spec_master_cfg = cfg_paths.get("spec_master_csv")
    spec_footnotes_cfg = cfg_paths.get("spec_footnotes_csv")
    spec_master_csv = (
        resolve_config_path(paths.root, spec_master_cfg.strip(), model, region)
        if isinstance(spec_master_cfg, str) and spec_master_cfg.strip()
        else base_paths.spec_master_csv
    )
    spec_footnotes_csv = (
        resolve_optional_config_path(paths.root, spec_footnotes_cfg, model, region)
        if isinstance(spec_footnotes_cfg, str)
        else base_paths.spec_footnotes_csv
    )

    build_paths = BuildPaths(
        root=base_paths.root,
        page_registry=base_paths.page_registry,
        content_blocks=base_paths.content_blocks,
        template_dir=base_paths.template_dir,
        output_dir=base_paths.output_dir,
        spec_master_csv=spec_master_csv,
        spec_footnotes_csv=spec_footnotes_csv,
    )
    return Phase1Builder(build_paths)


def ensure_csv_page_rsts(
    cfg: dict,
    builder: Phase1Builder,
    model: str | None,
    region: str | None,
) -> None:
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
        models={model} if model else None,
        regions={region} if region else None,
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


def _pick_region_from_vars(vars_map: dict[str, str]) -> str:
    for key in ("region", "Region"):
        value = (vars_map.get(key) or "").strip()
        if value:
            return value
    return ""


def pick_vars_map(
    model: str | None,
    region: str | None,
) -> dict[str, str]:
    out: dict[str, str] = {}
    if model:
        out["model"] = model
    if region:
        out["region"] = region
    return out


def fill_product_name_from_spec_master(
    vars_map: dict[str, str],
    *,
    spec_master_csv: Path,
    model: str | None,
    region: str | None,
    lang: str,
) -> dict[str, str]:
    out = dict(vars_map)
    target_model = (model or _pick_model_from_vars(out)).strip()
    target_region = (region or _pick_region_from_vars(out)).strip() or None
    if not target_model:
        return out

    match = resolve_product_name_from_spec_master(
        spec_master_csv,
        model=target_model,
        region=target_region,
        lang=lang,
    )
    if not match:
        return out

    out["product_name"] = match.product_name
    if match.region and not target_region:
        out["region"] = match.region
    if target_model and not _pick_model_from_vars(out):
        out["model"] = target_model
    return out


def resolve_bundle_targets(
    cfg: dict,
    model: str | None,
    region: str | None,
) -> tuple[str | None, str | None]:
    picked_model = resolve_build_model(cfg, model)
    picked_region = resolve_build_region(cfg, region)
    return picked_model, picked_region
