from __future__ import annotations

import re
from pathlib import Path
from typing import Callable


def resolve_spec_master_csv_path(
    cfg: dict,
    *,
    data_root: str | None = None,
    repo_root: Path,
    resolve_data_snapshot_paths: Callable[..., object],
) -> Path:
    return resolve_data_snapshot_paths(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
    ).spec_master_csv


def resolve_product_name_for_build(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str,
    data_root: str | None = None,
    repo_root: Path,
    resolve_spec_master_csv_path: Callable[..., Path],
    resolve_product_name_from_spec_master: Callable[..., object | None],
) -> str | None:
    if not (model or "").strip():
        return None
    spec_master_csv = resolve_spec_master_csv_path(
        cfg,
        data_root=data_root,
        repo_root=repo_root,
    )
    match = resolve_product_name_from_spec_master(
        spec_master_csv,
        model=model,
        region=region,
        lang=lang,
    )
    if not match:
        return None
    return match.product_name


def resolve_rst_substitutions_for_build(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str,
    data_root: str | None = None,
    repo_root: Path,
    docs_dir: Path,
    load_rst_substitutions: Callable[[Path], dict[str, str]],
    load_config_rst_substitutions: Callable[[dict], dict[str, str]],
    resolve_spec_master_csv_path: Callable[..., Path],
    resolve_template_substitutions_from_spec_master: Callable[..., dict[str, str]],
) -> dict[str, str]:
    spec_master_csv = resolve_spec_master_csv_path(
        cfg,
        data_root=data_root,
        repo_root=repo_root,
    )
    page_copy_csv = spec_master_csv.parent / "page_copy.csv"
    base_substitutions = {
        **load_rst_substitutions(docs_dir / "conf_base.py"),
        **load_config_rst_substitutions(cfg, lang=lang, page_copy_csv=page_copy_csv),
    }
    if not (model or "").strip():
        return base_substitutions
    return {
        **base_substitutions,
        **resolve_template_substitutions_from_spec_master(
            spec_master_csv,
            model=model,
            region=region,
            lang=lang,
        ),
    }


def parse_csv_values(raw: str) -> list[str]:
    items = [item.strip().lower() for item in raw.split(",")]
    return [item for item in items if item]


def resolve_requested_formats(
    cfg: dict,
    cli_formats: str | None,
    *,
    valid_formats: set[str],
    parse_csv_values: Callable[[str], list[str]],
) -> list[str]:
    if cli_formats and cli_formats.strip():
        formats = parse_csv_values(cli_formats)
    else:
        build_cfg_raw = cfg.get("build", {})
        build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
        configured = build_cfg.get("formats")
        if isinstance(configured, str) and configured.strip():
            formats = parse_csv_values(configured)
        elif isinstance(configured, list):
            formats = [str(item).strip().lower() for item in configured if str(item).strip()]
        else:
            formats = []
            if bool(build_cfg.get("build_html", False)):
                formats.append("html")
            if bool(build_cfg.get("build_word", False)):
                formats.append("word")
            if not formats:
                formats.append("pdf")

    unknown = sorted(set(formats) - valid_formats)
    if unknown:
        raise RuntimeError(f"Unsupported formats: {', '.join(unknown)}")
    return list(dict.fromkeys(formats))


def resolve_pdf_mode(
    cfg: dict,
    cli_pdf_mode: str | None,
    *,
    valid_pdf_modes: set[str],
) -> str:
    if cli_pdf_mode and cli_pdf_mode.strip():
        mode = cli_pdf_mode.strip().lower()
    else:
        pdf_cfg_raw = cfg.get("pdf", {})
        pdf_cfg = pdf_cfg_raw if isinstance(pdf_cfg_raw, dict) else {}
        mode = str(pdf_cfg.get("mode", "latex")).strip().lower()
    if mode not in valid_pdf_modes:
        raise RuntimeError(f"Unsupported pdf mode: {mode}")
    return mode


def resolve_output_path(base_dir: Path, configured_name: str) -> Path:
    out_path = Path(configured_name)
    if out_path.is_absolute():
        return out_path
    return base_dir / out_path


def slug_token(value: str | None) -> str:
    text = (value or "").strip().lower()
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", "", text)


def language_slug_token(value: str | None) -> str:
    text = (value or "").strip().casefold().replace("_", "-")
    if text in {"br", "pt-br"}:
        return "br"
    return slug_token(value)


def render_build_template(
    template: str,
    *,
    model: str | None,
    region: str | None,
    lang: str | None,
    template_token_re: re.Pattern[str],
    slug_token: Callable[[str | None], str],
) -> str:
    values = {
        "model": (model or "").strip(),
        "region": (region or "").strip(),
        "lang": (lang or "").strip(),
        "model_slug": slug_token(model),
        "region_slug": slug_token(region),
        "lang_slug": language_slug_token(lang),
    }
    required_tokens = {match.group(1) for match in template_token_re.finditer(template)}
    unknown = sorted(token for token in required_tokens if token not in values)
    if unknown:
        raise RuntimeError(f"Unsupported build output token(s): {', '.join(unknown)}")
    missing = sorted(token for token in required_tokens if not values[token])
    if missing:
        raise RuntimeError(f"Build output template requires value(s) for: {', '.join(missing)}")
    return template.format(**values)


def ensure_target_identity(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str,
    data_root: str | None = None,
    repo_root: Path,
    resolve_product_name_for_build: Callable[..., str | None],
    resolve_spec_master_csv_path: Callable[..., Path],
) -> None:
    if not model:
        return
    product_name = resolve_product_name_for_build(
        cfg,
        model=model,
        region=region,
        lang=lang,
        data_root=data_root,
        repo_root=repo_root,
    )
    if product_name:
        return
    spec_master_csv = resolve_spec_master_csv_path(
        cfg,
        data_root=data_root,
        repo_root=repo_root,
    )
    raise RuntimeError(
        "Failed to resolve Product Name from Spec_Master.csv for "
        f"model='{model}', region='{region or ''}', lang='{lang}'. "
        f"Source: {spec_master_csv}"
    )
