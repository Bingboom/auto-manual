from __future__ import annotations

import re
import shutil
from pathlib import Path

from tools.config_loader import load_config_mapping
from tools.config_pages import ConfigPage, CoverPdfPage, CsvPage, GeneratedPage, PdfInsertPage, RstIncludePage
from tools.data_snapshot import resolve_data_snapshot_paths
from tools.utils.path_utils import docs_build_dir_of
from tools.utils.targets import (
    format_tokenized,
    resolve_build_languages,
    resolve_build_model as resolve_target_model,
    resolve_build_region as resolve_target_region,
)
from tools.word_bundle_common import resolve_config_path

_INCLUDE_RE = re.compile(r"^\s*\.\.\s+include::\s+(\S+)\s*$")


def load_config(cfg_path: Path) -> dict:
    return load_config_mapping(cfg_path)


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


def format_bundle_tokenized(
    text: str,
    model: str | None,
    region: str | None,
) -> str:
    return format_tokenized(text, None, model, region)


def resolve_build_model(cfg: dict, arg_model: str | None) -> str | None:
    return resolve_target_model(cfg, arg_model)


def resolve_build_region(cfg: dict, arg_region: str | None) -> str | None:
    return resolve_target_region(cfg, arg_region)


def build_langs(cfg: dict) -> list[str]:
    langs = resolve_build_languages(cfg)
    return langs or ["en"]


def bundle_component(value: str | None, fallback: str) -> str:
    text = (value or "").strip() or fallback
    return text.replace("/", "_").replace("\\", "_").replace(":", "_")


def bundle_dir_for_target(
    *,
    docs_dir: Path,
    docs_build_dir: Path | None = None,
    model: str | None,
    region: str | None,
    lang: str | None = None,
) -> Path:
    actual_docs_build_dir = docs_build_dir or docs_build_dir_of(docs_dir)
    target_root = actual_docs_build_dir / bundle_component(model, "_shared") / bundle_component(region, "_default")
    if (lang or "").strip():
        target_root = target_root / bundle_component(lang, "_default")
    return target_root / "rst"


def legacy_bundle_dir_for_target(
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
) -> Path:
    return docs_dir / bundle_component(model, "_shared") / bundle_component(region, "_default")


def legacy_generated_dir_for_target(
    *,
    docs_dir: Path,
    model: str | None,
) -> Path:
    return docs_dir / "generated" / bundle_component(model, "_shared")


def cleanup_legacy_rst_artifacts(
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
) -> None:
    legacy_bundle_dir = legacy_bundle_dir_for_target(
        docs_dir=docs_dir,
        model=model,
        region=region,
    )
    legacy_generated_dir = legacy_generated_dir_for_target(
        docs_dir=docs_dir,
        model=model,
    )

    if legacy_bundle_dir.exists():
        shutil.rmtree(legacy_bundle_dir)
        parent = legacy_bundle_dir.parent
        if parent != docs_dir and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()

    if legacy_generated_dir.exists():
        shutil.rmtree(legacy_generated_dir)
        parent = legacy_generated_dir.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()


def resolve_spec_master_csv_path(
    cfg: dict,
    *,
    repo_root: Path,
    data_root: str | None,
    model: str | None,
    region: str | None,
) -> Path:
    return resolve_data_snapshot_paths(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    ).spec_master_csv


def resolve_localized_copy_csv_path(
    cfg: dict,
    *,
    repo_root: Path,
    data_root: str | None,
    model: str | None,
    region: str | None,
) -> Path:
    return resolve_data_snapshot_paths(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    ).localized_copy_csv


def resolve_csv_rst_path(
    *,
    source_root: Path,
    page: CsvPage,
    lang: str,
    model: str | None,
    region: str | None,
) -> Path:
    if page.include_dir is None:
        rel = f"{page.page}_{lang}.rst"
    else:
        rel = str(Path(format_bundle_tokenized(page.include_dir, model, region)) / f"{page.page}_{lang}.rst")
    return source_root / rel


def resolve_generated_source_path(
    *,
    bundle_dir: Path,
    page: GeneratedPage,
    lang: str,
    model: str | None,
    region: str | None,
) -> Path | None:
    if page.include_dir is None:
        return None
    rel = Path(format_bundle_tokenized(page.include_dir, model, region)) / f"{page.page}_{lang}.rst"
    return bundle_dir / rel


def resolve_generated_template_path(
    *,
    docs_dir: Path,
    page: GeneratedPage,
    model: str | None,
    region: str | None,
) -> Path:
    return resolve_config_path(docs_dir, page.template, model, region)


def resolve_generated_recipe_path(
    *,
    docs_dir: Path,
    page: GeneratedPage,
    model: str | None,
    region: str | None,
) -> Path:
    return resolve_config_path(docs_dir, page.recipe, model, region)


def source_path_for_contract(
    page: ConfigPage,
    *,
    docs_dir: Path,
    bundle_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> Path | None:
    if isinstance(page, RstIncludePage):
        return resolve_config_path(docs_dir, page.file, model, region)
    if isinstance(page, GeneratedPage):
        return resolve_generated_template_path(docs_dir=docs_dir, page=page, model=model, region=region)
    if isinstance(page, CsvPage):
        if lang is None:
            return None
        return resolve_csv_rst_path(
            source_root=bundle_dir,
            page=page,
            lang=lang,
            model=model,
            region=region,
        )
    return None


def read_included_page_paths(index_path: Path) -> list[Path]:
    out: list[Path] = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        match = _INCLUDE_RE.match(line)
        if not match:
            continue
        out.append((index_path.parent / match.group(1)).resolve())
    return out


__all__ = [
    "build_langs",
    "bundle_component",
    "bundle_dir_for_target",
    "cleanup_legacy_rst_artifacts",
    "format_bundle_tokenized",
    "latex_apply_lang",
    "latex_cover_block",
    "latex_overview_block",
    "load_config",
    "read_included_page_paths",
    "resolve_build_model",
    "resolve_build_region",
    "resolve_csv_rst_path",
    "resolve_generated_recipe_path",
    "resolve_generated_source_path",
    "resolve_generated_template_path",
    "resolve_spec_master_csv_path",
    "source_path_for_contract",
]
