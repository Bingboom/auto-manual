#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.config_pages import CsvPage
from tools.build_docs_bundle import prepare_manual_bundle as _prepare_manual_bundle_impl
from tools.build_docs_cli import parse_args as _parse_args_impl
from tools.build_docs_entry import run_build as _run_build_impl
from tools.build_docs_export import build_target as _build_target_impl
from tools.build_docs_targets import (
    config_uses_model_token as _config_uses_model_token_impl,
    config_uses_region_token as _config_uses_region_token_impl,
    configured_build_targets as _configured_build_targets_impl,
    resolve_build_model as _resolve_build_model_impl,
    resolve_build_region as _resolve_build_region_impl,
    resolve_build_targets as _resolve_build_targets_impl,
)
from tools.config_loader import load_config_mapping
from tools.data_snapshot import resolve_data_snapshot_paths
from tools.gen_index_bundle import (
    MaterializedBundle,
    bundle_dir_for_target,
    cleanup_legacy_rst_artifacts,
    materialize_bundle,
)
from tools.page_manifest import resolve_config_pages_or_raise
from tools.review_support import (
    overlay_review_content_onto_bundle,
    overlay_review_onto_bundle,
    review_bundle_exists,
    review_content_exists,
)
from tools.utils.path_utils import get_paths  # noqa: E402
from tools.utils.process_utils import find_exe, open_file, run  # noqa: E402
from tools.utils.spec_master import (
    resolve_product_name_from_spec_master,
    resolve_template_substitutions_from_spec_master,
)
from tools.utils.targets import (
    config_uses_token_in_pages,
    resolve_build_languages as resolve_cfg_languages,
    resolve_build_model as resolve_target_model,
    resolve_build_region as resolve_target_region,
    resolve_output_lang,
)
from tools.utils.tex_utils import compile_xelatex  # noqa: E402
from tools.word_bundle import export_word_from_bundle  # noqa: E402
from tools.word_bundle_common import load_rst_substitutions  # noqa: E402

from tools.validate_config import validate as validate_cfg
from tools.validate_layout_params import validate as validate_layout

paths = get_paths()
VALID_FORMATS = {"html", "word", "pdf"}
VALID_PDF_MODES = {"latex", "word"}
VALID_SOURCE_MODES = {"auto", "runtime", "review"}
_TEMPLATE_TOKEN_RE = re.compile(r"\{([a-z_]+)\}")
MANUAL_META_FILE_NAME = "manual_meta.json"
SWITCHER_BLOCK_START = "<!-- HB_MANUAL_SWITCHER_START -->"
SWITCHER_BLOCK_END = "<!-- HB_MANUAL_SWITCHER_END -->"
BODY_SWITCHER_CLASS = "hb-manual-switcher-body"
_REMOVE_TREE_RETRY_DELAYS = (0.2, 0.5, 1.0)
_SWITCHER_BLOCK_RE = re.compile(
    rf"{re.escape(SWITCHER_BLOCK_START)}.*?{re.escape(SWITCHER_BLOCK_END)}",
    re.DOTALL,
)
_BODY_TAG_RE = re.compile(r"<body\b([^>]*)>", re.IGNORECASE)
_MANUAL_COVER_SECTION_RE = re.compile(
    r"<section class=\"manual-cover\">.*?</section>",
    re.IGNORECASE | re.DOTALL,
)
LANGUAGE_LABELS = {
    "en": "English",
    "es": "Espanol",
    "fr": "Francais",
    "ja": "日本語",
}


@dataclass(frozen=True)
class BuildTarget:
    model: str | None
    region: str | None
    lang: str | None = None


@dataclass(frozen=True)
class HtmlManualVariant:
    model: str
    region: str
    lang: str
    title: str
    html_dir: Path
    html_dir_token: str
    lang_in_output_path: bool


def load_config(cfg_path: Path) -> dict:
    return load_config_mapping(cfg_path)


def discover_existing_bundle_targets(*, docs_dir: Path | None = None) -> list[BuildTarget]:
    actual_docs_dir = docs_dir or paths.docs_dir
    build_root = actual_docs_dir / "_build"
    if not build_root.exists():
        return []

    targets: list[BuildTarget] = []
    for model_dir in sorted(path for path in build_root.iterdir() if path.is_dir()):
        for region_dir in sorted(path for path in model_dir.iterdir() if path.is_dir()):
            if (region_dir / "rst" / "index.rst").exists():
                targets.append(BuildTarget(model=model_dir.name, region=region_dir.name))
            for lang_dir in sorted(path for path in region_dir.iterdir() if path.is_dir()):
                if (lang_dir / "rst" / "index.rst").exists():
                    targets.append(BuildTarget(model=model_dir.name, region=region_dir.name, lang=lang_dir.name))
    return targets


def build_root_for_target(
    model: str | None,
    region: str | None,
    lang: str | None = None,
    *,
    docs_build_dir: Path | None = None,
    preview_name: str | None = None,
) -> Path:
    actual_docs_build_dir = docs_build_dir or paths.docs_build_dir
    target_root = actual_docs_build_dir / _target_component(model, "_shared") / _target_component(region, "_default")
    if preview_name:
        return target_root / "preview" / _target_component(preview_name, "_preview")
    if (lang or "").strip():
        return target_root / _target_component(lang, "_default")
    return target_root


def clean_build_targets(
    targets: list[BuildTarget],
    *,
    docs_dir: Path | None = None,
    preview_name: str | None = None,
) -> None:
    actual_docs_dir = docs_dir or paths.docs_dir
    actual_docs_build_dir = actual_docs_dir / "_build"

    for target in targets:
        target_build_root = build_root_for_target(
            target.model,
            target.region,
            target.lang,
            docs_build_dir=actual_docs_build_dir,
            preview_name=preview_name,
        )
        if target_build_root.exists():
            print(f"[build] Cleaning target output: {target_build_root}")
            remove_tree_with_retries(target_build_root)

        if preview_name is None:
            cleanup_legacy_rst_artifacts(
                docs_dir=actual_docs_dir,
                model=target.model,
                region=target.region,
            )


def _is_retryable_cleanup_error(exc: OSError) -> bool:
    if getattr(exc, "winerror", None) == 32:
        return True
    if isinstance(exc, PermissionError):
        if os.name == "nt":
            return True
        message = str(exc).lower()
        return "file in use" in message or "resource busy" in message
    return False


def remove_tree_with_retries(path: Path) -> None:
    last_exc: OSError | None = None
    retry_count = len(_REMOVE_TREE_RETRY_DELAYS)

    for attempt in range(retry_count + 1):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except OSError as exc:
            if not _is_retryable_cleanup_error(exc):
                raise
            last_exc = exc
            if attempt >= retry_count:
                break
            delay = _REMOVE_TREE_RETRY_DELAYS[attempt]
            print(
                "[build] Cleanup blocked by an open handle; "
                f"retrying in {delay:.1f}s ({attempt + 1}/{retry_count})..."
            )
            time.sleep(delay)

    raise RuntimeError(
        "Could not clean build output: "
        f"{path}. Another program is still using this folder, or Windows has not released the handle yet. "
        "Close any File Explorer, browser, Word, or PDF windows pointing at docs/_build and rerun. "
        "If you only need to rebuild in place, rerun with --no-clean."
    ) from last_exc


def validate_loaded_config(cfg: dict) -> None:
    issues = validate_cfg(cfg, strict_files=False)
    errors = [i for i in issues if i.level == "ERROR"]
    for issue in issues:
        print(f"[build] config {issue.level.lower()}: {issue.msg}")
    if errors:
        raise RuntimeError("Config validation failed")


def validate_layout_csv(layout_csv_path: Path) -> None:
    issues = validate_layout(layout_csv_path)
    errors = [i for i in issues if i.level == "ERROR"]
    for issue in issues:
        print(f"[build] layout {issue.level.lower()}: {issue.msg}")
    if errors:
        raise RuntimeError("Layout params validation failed")


def render_csv_pages(
    cfg: dict,
    model: str | None,
    region: str | None,
    *,
    data_root: str | None = None,
) -> None:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    pages = resolve_config_pages_or_raise(
        cfg,
        default_languages=list(build_cfg.get("languages", [])),
        root=paths.root,
        model=model,
        region=region,
        error_prefix="config.pages",
    ).pages
    build_langs = cfg.get("build", {}).get("languages", [])
    snapshot_paths = resolve_data_snapshot_paths(
        cfg,
        repo_root=paths.root,
        data_root=data_root,
        model=model,
        region=region,
    )

    phase1_pages: set[str] = set()
    phase1_langs: set[str] = set()

    for page in pages:
        if not isinstance(page, CsvPage):
            continue

        page_name = page.page
        source = page.source
        if source != "phase1":
            raise RuntimeError(f"Unsupported csv_page source='{source}' for page='{page_name}' (phase1-only)")

        phase1_pages.add(page_name)
        langs = list(page.langs) or build_langs
        for lang in langs:
            phase1_langs.add(str(lang))

    if phase1_pages:
        cmd = [sys.executable, "tools/phase1_build.py"]
        cmd += ["--page", ",".join(sorted(phase1_pages))]
        if phase1_langs:
            cmd += ["--lang", ",".join(sorted(phase1_langs))]
        if model:
            cmd += ["--model", model]
        if region:
            cmd += ["--region", region]
        if isinstance(data_root, str) and data_root.strip():
            cmd += ["--data-root", data_root.strip()]
        cmd += ["--page-registry", str(snapshot_paths.page_registry_csv)]
        cmd += ["--page-blocks-dir", str(snapshot_paths.page_blocks_dir)]
        cmd += ["--spec-master-csv", str(snapshot_paths.spec_master_csv)]
        cmd += ["--spec-footnotes-csv", str(snapshot_paths.spec_footnotes_csv)]
        cmd += ["--spec-notes-csv", str(snapshot_paths.spec_notes_csv)]
        cmd += ["--spec-titles-csv", str(snapshot_paths.spec_titles_csv)]
        run(cmd, cwd=paths.root)


def _config_uses_model_token(cfg: dict) -> bool:
    return _config_uses_model_token_impl(
        cfg,
        config_uses_token_in_pages=config_uses_token_in_pages,
    )


def _config_uses_region_token(cfg: dict) -> bool:
    return _config_uses_region_token_impl(
        cfg,
        config_uses_token_in_pages=config_uses_token_in_pages,
    )


def resolve_build_model(cfg: dict, arg_model: str | None) -> str | None:
    return _resolve_build_model_impl(
        cfg,
        arg_model,
        resolve_target_model=resolve_target_model,
    )


def resolve_build_region(cfg: dict, arg_region: str | None) -> str | None:
    return _resolve_build_region_impl(
        cfg,
        arg_region,
        resolve_target_region=resolve_target_region,
    )


def _configured_build_targets(cfg: dict) -> list[BuildTarget]:
    return _configured_build_targets_impl(
        cfg,
        build_target_cls=BuildTarget,
        resolve_build_model=resolve_build_model,
        resolve_build_region=resolve_build_region,
        resolve_output_lang=resolve_output_lang,
    )


def resolve_build_targets(
    cfg: dict,
    *,
    arg_model: str | None,
    arg_region: str | None,
    all_targets: bool,
) -> list[BuildTarget]:
    return _resolve_build_targets_impl(
        cfg,
        arg_model=arg_model,
        arg_region=arg_region,
        all_targets=all_targets,
        build_target_cls=BuildTarget,
        configured_build_targets=_configured_build_targets,
        resolve_build_model=resolve_build_model,
        resolve_build_region=resolve_build_region,
        resolve_output_lang=resolve_output_lang,
    )


def _resolve_spec_master_csv_path(
    cfg: dict,
    *,
    data_root: str | None = None,
    repo_root: Path | None = None,
) -> Path:
    return resolve_data_snapshot_paths(
        cfg,
        repo_root=repo_root or paths.root,
        data_root=data_root,
    ).spec_master_csv


def resolve_product_name_for_build(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str,
    data_root: str | None = None,
    repo_root: Path | None = None,
) -> str | None:
    if not (model or "").strip():
        return None
    spec_master_csv = _resolve_spec_master_csv_path(
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
    repo_root: Path | None = None,
) -> dict[str, str]:
    base_substitutions = load_rst_substitutions(paths.docs_dir / "conf_base.py")
    if not (model or "").strip():
        return base_substitutions
    spec_master_csv = _resolve_spec_master_csv_path(
        cfg,
        data_root=data_root,
        repo_root=repo_root,
    )
    return {
        **base_substitutions,
        **resolve_template_substitutions_from_spec_master(
            spec_master_csv,
            model=model,
            region=region,
            lang=lang,
        ),
    }


def _build_rst_epilog(substitutions: dict[str, str]) -> str:
    lines: list[str] = []
    for key, value in substitutions.items():
        text = (value or "").strip()
        if not text:
            continue
        lines.append(f".. |{key}| replace:: {text}")
    return "\n".join(lines)


def _with_rst_epilog(cmd: list[str], substitutions: dict[str, str] | None) -> list[str]:
    if not substitutions:
        return cmd
    epilog = _build_rst_epilog(substitutions)
    if not epilog:
        return cmd
    return [*cmd, "-D", f"rst_epilog={epilog}"]


def _with_product_name_epilog(cmd: list[str], product_name: str | None) -> list[str]:
    if not (product_name or "").strip():
        return cmd
    name = product_name.strip()
    return _with_rst_epilog(
        cmd,
        {
            "PRODUCT_NAME": name,
            "PRODUCT_NAME_BOLD": f"**{name}**",
        },
    )


def _resolve_sphinx_build_cmd(builder: str) -> list[str]:
    sphinx_build = find_exe(["sphinx-build"])
    if sphinx_build:
        return [sphinx_build, "-b", builder]
    return [sys.executable, "-m", "sphinx", "-b", builder]


def _normalize_sphinx_tag_value(value: str | None) -> str | None:
    text = (value or "").strip().lower()
    if not text:
        return None
    normalized = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return normalized or None


def _sphinx_tag_args(*, model: str | None = None, region: str | None = None, lang: str | None = None) -> list[str]:
    args: list[str] = []
    for prefix, value in (("model", model), ("region", region), ("lang", lang)):
        normalized = _normalize_sphinx_tag_value(value)
        if normalized:
            args.extend(["-t", f"{prefix}_{normalized}"])
    return args


def _load_configured_html_theme(conf_base_path: Path) -> str | None:
    if not conf_base_path.exists():
        return None
    for line in conf_base_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("html_theme"):
            continue
        _, _, raw = stripped.partition("=")
        value = raw.split("#", 1)[0].strip().strip("\"'")
        return value or None
    return None


def _should_use_minimal_html_theme(conf_dir: Path, requested_minimal: bool) -> bool:
    if requested_minimal:
        return True
    theme_name = _load_configured_html_theme(conf_dir / "conf_base.py")
    if not theme_name or theme_name in {"alabaster", "classic", "basic"}:
        return False
    if importlib.util.find_spec(theme_name) is not None:
        return False
    print(f"[build] HTML theme '{theme_name}' not available, fallback to alabaster")
    return True


def _target_component(value: str | None, fallback: str) -> str:
    text = (value or "").strip() or fallback
    return text.replace("/", "_").replace("\\", "_").replace(":", "_")


def _body_tag_with_class(body_tag: str, class_name: str) -> str:
    class_match = re.search(r'\bclass=(["\'])(.*?)\1', body_tag, re.IGNORECASE | re.DOTALL)
    if class_match:
        quote = class_match.group(1)
        classes = class_match.group(2).split()
        if class_name in classes:
            return body_tag
        new_classes = " ".join([*classes, class_name]).strip()
        return body_tag[: class_match.start()] + f'class={quote}{new_classes}{quote}' + body_tag[class_match.end() :]
    return body_tag[:-1] + f' class="{class_name}">'


def _language_label(lang: str) -> str:
    key = (lang or "").strip().lower()
    return LANGUAGE_LABELS.get(key, key.upper() or "Unknown")


def _variant_key(variant: HtmlManualVariant) -> tuple[str, str]:
    return (variant.region.upper(), variant.lang.lower())


def _variant_priority(variant: HtmlManualVariant) -> tuple[int, str]:
    return (1 if variant.lang_in_output_path else 0, variant.html_dir_token)


def _effective_variants_for_current(
    variants: list[HtmlManualVariant],
    *,
    current_variant: HtmlManualVariant,
) -> list[HtmlManualVariant]:
    selected: dict[tuple[str, str], HtmlManualVariant] = {}
    for variant in sorted(variants, key=lambda item: (item.region.upper(), item.lang.lower(), item.html_dir_token)):
        key = _variant_key(variant)
        existing = selected.get(key)
        if existing is None or _variant_priority(variant) > _variant_priority(existing):
            selected[key] = variant
    selected[_variant_key(current_variant)] = current_variant
    return sorted(selected.values(), key=lambda item: (item.region.upper(), item.lang.lower(), item.html_dir_token))


def write_html_manual_meta(
    html_out_dir: Path,
    *,
    docs_build_dir: Path,
    model: str | None,
    region: str | None,
    lang: str,
    title: str,
    lang_in_output_path: bool,
) -> Path:
    if not (model or "").strip():
        raise RuntimeError("HTML manual metadata requires a model")
    if not (region or "").strip():
        raise RuntimeError("HTML manual metadata requires a region")

    html_dir_token = html_out_dir.relative_to(docs_build_dir).as_posix()
    payload = {
        "model": model.strip(),
        "region": region.strip(),
        "lang": lang.strip(),
        "title": title.strip(),
        "html_dir": html_dir_token,
        "lang_in_output_path": bool(lang_in_output_path),
    }
    meta_path = html_out_dir / MANUAL_META_FILE_NAME
    meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta_path


def _load_html_manual_variant(meta_path: Path, *, docs_build_dir: Path) -> HtmlManualVariant | None:
    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None

    model = str(raw.get("model", "")).strip()
    region = str(raw.get("region", "")).strip()
    lang = str(raw.get("lang", "")).strip().lower()
    title = str(raw.get("title", "")).strip()
    html_dir_token = str(raw.get("html_dir", "")).strip()
    if not (model and region and lang and html_dir_token):
        return None

    html_dir = docs_build_dir / Path(html_dir_token)
    lang_in_output_path = bool(raw.get("lang_in_output_path", False))
    return HtmlManualVariant(
        model=model,
        region=region,
        lang=lang,
        title=title,
        html_dir=html_dir,
        html_dir_token=html_dir_token,
        lang_in_output_path=lang_in_output_path,
    )


def collect_model_html_variants(
    *,
    model: str | None,
    docs_build_dir: Path | None = None,
) -> list[HtmlManualVariant]:
    if not (model or "").strip():
        return []

    actual_docs_build_dir = docs_build_dir or paths.docs_build_dir
    model_dir = actual_docs_build_dir / _target_component(model, "_shared")
    if not model_dir.exists():
        return []

    variants: list[HtmlManualVariant] = []
    for meta_path in sorted(model_dir.rglob(MANUAL_META_FILE_NAME)):
        variant = _load_html_manual_variant(meta_path, docs_build_dir=actual_docs_build_dir)
        if variant is None or variant.model != model:
            continue
        if not (variant.html_dir / "index.html").exists():
            continue
        variants.append(variant)
    return variants


def _resolve_variant_target_page(current_html_path: Path, target_variant: HtmlManualVariant) -> Path:
    target_page = target_variant.html_dir / current_html_path.name
    if target_page.exists():
        return target_page
    return target_variant.html_dir / "index.html"


def build_manual_switcher_markup(
    *,
    current_variant: HtmlManualVariant,
    variants: list[HtmlManualVariant],
    current_html_path: Path,
) -> str | None:
    return None


def inject_manual_switcher_into_html(html_path: Path, markup: str | None) -> bool:
    original = html_path.read_text(encoding="utf-8")
    stripped = _SWITCHER_BLOCK_RE.sub("", original).strip()
    body_match = _BODY_TAG_RE.search(stripped)
    if body_match is None:
        return False

    body_tag = body_match.group(0)
    new_body_tag = _body_tag_with_class(body_tag, BODY_SWITCHER_CLASS)
    updated = stripped[: body_match.start()] + new_body_tag + stripped[body_match.end() :]
    insert_at = body_match.start() + len(new_body_tag)
    if markup:
        updated = updated[:insert_at] + "\n" + markup + "\n" + updated[insert_at:]
    updated = updated + "\n"
    if updated == original:
        return False
    html_path.write_text(updated, encoding="utf-8")
    return True


def strip_html_cover_section(html_path: Path) -> bool:
    original = html_path.read_text(encoding="utf-8")
    updated, count = _MANUAL_COVER_SECTION_RE.subn("", original, count=1)
    if count == 0 or updated == original:
        return False
    html_path.write_text(updated, encoding="utf-8")
    return True


def refresh_model_html_switchers(
    *,
    model: str | None,
    docs_build_dir: Path | None = None,
) -> None:
    variants = collect_model_html_variants(model=model, docs_build_dir=docs_build_dir)
    if not variants:
        return

    for current_variant in variants:
        for html_path in sorted(current_variant.html_dir.glob("*.html")):
            markup = build_manual_switcher_markup(
                current_variant=current_variant,
                variants=variants,
                current_html_path=html_path,
            )
            inject_manual_switcher_into_html(html_path, markup)


def _parse_csv_values(raw: str) -> list[str]:
    items = [item.strip().lower() for item in raw.split(",")]
    return [item for item in items if item]


def resolve_requested_formats(cfg: dict, cli_formats: str | None) -> list[str]:
    if cli_formats and cli_formats.strip():
        formats = _parse_csv_values(cli_formats)
    else:
        build_cfg_raw = cfg.get("build", {})
        build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
        configured = build_cfg.get("formats")
        if isinstance(configured, str) and configured.strip():
            formats = _parse_csv_values(configured)
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

    unknown = sorted(set(formats) - VALID_FORMATS)
    if unknown:
        raise RuntimeError(f"Unsupported formats: {', '.join(unknown)}")
    return list(dict.fromkeys(formats))


def resolve_pdf_mode(cfg: dict, cli_pdf_mode: str | None) -> str:
    if cli_pdf_mode and cli_pdf_mode.strip():
        mode = cli_pdf_mode.strip().lower()
    else:
        pdf_cfg_raw = cfg.get("pdf", {})
        pdf_cfg = pdf_cfg_raw if isinstance(pdf_cfg_raw, dict) else {}
        mode = str(pdf_cfg.get("mode", "latex")).strip().lower()
    if mode not in VALID_PDF_MODES:
        raise RuntimeError(f"Unsupported pdf mode: {mode}")
    return mode


def resolve_output_path(base_dir: Path, configured_name: str) -> Path:
    out_path = Path(configured_name)
    if out_path.is_absolute():
        return out_path
    return base_dir / out_path


def _slug_token(value: str | None) -> str:
    text = (value or "").strip().lower()
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", "", text)


def render_build_template(
    template: str,
    *,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> str:
    values = {
        "model": (model or "").strip(),
        "region": (region or "").strip(),
        "lang": (lang or "").strip(),
        "model_slug": _slug_token(model),
        "region_slug": _slug_token(region),
        "lang_slug": _slug_token(lang),
    }
    required_tokens = {match.group(1) for match in _TEMPLATE_TOKEN_RE.finditer(template)}
    unknown = sorted(token for token in required_tokens if token not in values)
    if unknown:
        raise RuntimeError(f"Unsupported build output token(s): {', '.join(unknown)}")
    missing = sorted(token for token in required_tokens if not values[token])
    if missing:
        raise RuntimeError(f"Build output template requires value(s) for: {', '.join(missing)}")
    return template.format(**values)


def sphinx_build(
    builder: str,
    *,
    src_dir: Path,
    out_dir: Path,
    conf_dir: Path,
    model: str | None = None,
    region: str | None = None,
    lang: str | None = None,
    minimal_theme: bool = False,
    substitutions: dict[str, str] | None = None,
) -> None:
    print(f"[build] Sphinx -> {builder.upper()}")
    out_dir.mkdir(parents=True, exist_ok=True)
    actual_minimal_theme = _should_use_minimal_html_theme(conf_dir, minimal_theme) if builder == "html" else False
    cmd = _resolve_sphinx_build_cmd(builder) + _sphinx_tag_args(model=model, region=region, lang=lang)
    cmd += [str(src_dir), str(out_dir), "-c", str(conf_dir)]
    if builder == "html" and actual_minimal_theme:
        cmd += [
            "-D",
            "html_theme=alabaster",
        ]
    cmd = _with_rst_epilog(cmd, substitutions)
    run(cmd, cwd=paths.root)


def patch_fonts(patch_fonts_script: str, main_tex: str, *, build_dir: Path) -> None:
    print("[build] Patch fonts (inject fonts.tex)")
    run(
        [
            sys.executable,
            patch_fonts_script,
            "--tex",
            main_tex,
            "--build-dir",
            str(build_dir),
        ],
        cwd=paths.root,
    )


def export_word_from_latex(
    tex_path: Path,
    *,
    resource_dir: Path,
    out_path: Path,
) -> Path:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("pandoc is required for Word export. Please install pandoc first.")
    if not tex_path.exists():
        raise RuntimeError(f"LaTeX source not found for Word export: {tex_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    print("[build] Convert LaTeX -> DOCX")
    run(
        [
            pandoc,
            str(tex_path),
            "--from=latex",
            "--to=docx",
            "--resource-path",
            str(resource_dir),
            "-o",
            str(out_path),
        ],
        cwd=paths.root,
    )
    return out_path


def export_word_from_html(
    html_index: Path,
    *,
    out_path: Path,
) -> Path:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("pandoc is required for Word export. Please install pandoc first.")
    if not html_index.exists():
        raise RuntimeError(f"HTML source not found for Word export: {html_index}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    print("[build] Convert HTML -> DOCX")
    run(
        [
            pandoc,
            str(html_index),
            "--from=html",
            "--to=docx",
            "--resource-path",
            str(html_index.parent),
            "-o",
            str(out_path),
        ],
        cwd=paths.root,
    )
    return out_path


def export_pdf_from_docx_via_word(docx_path: Path, pdf_path: Path) -> Path:
    if not sys.platform.startswith("win"):
        raise RuntimeError("pdf mode 'word' is supported on Windows only")
    if not docx_path.exists():
        raise RuntimeError(f"DOCX source not found for PDF export: {docx_path}")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    docx_literal = str(docx_path).replace("'", "''")
    pdf_literal = str(pdf_path).replace("'", "''")
    script = f"""
$ErrorActionPreference = 'Stop'
$docxPath = '{docx_literal}'
$pdfPath = '{pdf_literal}'
$word = $null
$doc = $null
$wdFormatPDF = 17
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $doc = $word.Documents.Open($docxPath, $false, $true)
    $doc.SaveAs([ref]$pdfPath, [ref]$wdFormatPDF)
}} finally {{
    if ($doc) {{
        $doc.Close([ref]$false)
    }}
    if ($word) {{
        $word.Quit()
    }}
}}
"""
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        check=True,
        cwd=str(paths.root),
    )
    return pdf_path


def ensure_target_identity(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str,
    data_root: str | None = None,
    repo_root: Path | None = None,
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
    spec_master_csv = _resolve_spec_master_csv_path(
        cfg,
        data_root=data_root,
        repo_root=repo_root,
    )
    raise RuntimeError(
        "Failed to resolve Product Name from Spec_Master.csv for "
        f"model='{model}', region='{region or ''}', lang='{lang}'. "
        f"Source: {spec_master_csv}"
    )


def prepare_manual_bundle(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str | None = None,
    data_root: str | None = None,
    source_mode: str = "auto",
    page_selector: str | None = None,
    output_root: Path | None = None,
    write_wrapper_index: bool = True,
) -> MaterializedBundle:
    return _prepare_manual_bundle_impl(
        cfg,
        model=model,
        region=region,
        lang=lang,
        data_root=data_root,
        source_mode=source_mode,
        page_selector=page_selector,
        output_root=output_root,
        write_wrapper_index=write_wrapper_index,
        valid_source_modes=VALID_SOURCE_MODES,
        materialize_bundle=materialize_bundle,
        review_bundle_exists=review_bundle_exists,
        overlay_review_onto_bundle=overlay_review_onto_bundle,
        review_content_exists=review_content_exists,
        overlay_review_content_onto_bundle=overlay_review_content_onto_bundle,
        docs_dir=paths.docs_dir,
    )


def write_docs_root_index_for_targets(targets: list[BuildTarget]) -> None:
    merged_targets: list[BuildTarget] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    for target in [*discover_existing_bundle_targets(), *targets]:
        key = (target.model, target.region, target.lang)
        if key in seen:
            continue
        seen.add(key)
        merged_targets.append(target)

    if not merged_targets:
        return

    if len(merged_targets) == 1:
        target = merged_targets[0]
        bundle_rel = bundle_dir_for_target(
            docs_dir=paths.docs_dir,
            model=target.model,
            region=target.region,
            lang=target.lang,
        ).relative_to(paths.docs_dir)
        lines = [
            ".. Auto-generated by tools/build_docs.py. Do not edit directly.",
            "",
            f".. include:: {bundle_rel.as_posix()}/index",
            "",
        ]
        (paths.docs_dir / "index.rst").write_text("\n".join(lines), encoding="utf-8")
        return

    lines = [
        "Available Manual Bundles",
        "========================",
        "",
        ".. toctree::",
        "   :maxdepth: 1",
        "",
    ]
    for target in merged_targets:
        bundle_rel = bundle_dir_for_target(
            docs_dir=paths.docs_dir,
            model=target.model,
            region=target.region,
            lang=target.lang,
        ).relative_to(paths.docs_dir)
        lines.append(f"   {bundle_rel.as_posix()}/index")
    lines.append("")
    (paths.docs_dir / "index.rst").write_text("\n".join(lines), encoding="utf-8")


def build_target(
    cfg: dict,
    *,
    target_model: str | None,
    target_region: str | None,
    target_lang: str | None,
    requested_formats: list[str],
    pdf_mode: str,
    build_cfg: dict,
    tools_cfg: dict,
    no_open: bool,
    source_mode: str,
    data_root: str | None,
    page_selector: str | None = None,
    output_root: Path | None = None,
    output_base_root: Path | None = None,
    write_wrapper_index: bool = True,
) -> None:
    return _build_target_impl(
        cfg,
        target_model=target_model,
        target_region=target_region,
        target_lang=target_lang,
        requested_formats=requested_formats,
        pdf_mode=pdf_mode,
        build_cfg=build_cfg,
        tools_cfg=tools_cfg,
        no_open=no_open,
        source_mode=source_mode,
        data_root=data_root,
        page_selector=page_selector,
        output_root=output_root,
        output_base_root=output_base_root,
        write_wrapper_index=write_wrapper_index,
        default_docs_build_dir=paths.docs_build_dir,
        resolve_cfg_languages=resolve_cfg_languages,
        build_root_for_target=build_root_for_target,
        ensure_target_identity=ensure_target_identity,
        prepare_manual_bundle=prepare_manual_bundle,
        render_build_template=render_build_template,
        resolve_output_path=resolve_output_path,
        sphinx_build=sphinx_build,
        patch_fonts=patch_fonts,
        compile_xelatex=compile_xelatex,
        export_word_from_bundle=export_word_from_bundle,
        export_word_from_html=export_word_from_html,
        export_word_from_latex=export_word_from_latex,
        export_pdf_from_docx_via_word=export_pdf_from_docx_via_word,
        copy_file=shutil.copy2,
        open_file=open_file,
        strip_html_cover_section=strip_html_cover_section,
        write_html_manual_meta=write_html_manual_meta,
        refresh_model_html_switchers=refresh_model_html_switchers,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return _parse_args_impl(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    _run_build_impl(
        args,
        paths=paths,
        load_config=load_config,
        validate_loaded_config=validate_loaded_config,
        validate_layout_csv=validate_layout_csv,
        resolve_build_targets=resolve_build_targets,
        config_uses_model_token=_config_uses_model_token,
        config_uses_region_token=_config_uses_region_token,
        clean_build_targets=clean_build_targets,
        resolve_requested_formats=resolve_requested_formats,
        resolve_pdf_mode=resolve_pdf_mode,
        build_target=build_target,
        write_docs_root_index_for_targets=write_docs_root_index_for_targets,
    )


if __name__ == "__main__":
    main()
