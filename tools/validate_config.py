#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/validate_config.py

P0 validator for configs/config.us.yaml.

Checks:
- YAML readable
- Detect duplicate YAML keys (fail-fast)
- Required sections exist
- pages DSL structure valid
- csv_page source check (phase2-only)
- Optional file existence checks
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.utils.path_utils import Paths  # noqa: E402
from tools.config_pages import (
    CoverPdfPage,
    CsvPage,
    GeneratedPage,
    PdfInsertPage,
    RstIncludePage,
)
from tools.page_manifest import resolve_config_pages, resolve_page_manifest_path
from tools.spec_master_sources import has_source_table_ids

SYNC_PHASE2_PROVIDERS = {"lark_cli", "lark-cli", "cli"}
SYNC_PHASE2_TABLES = {
    "spec_master",
    "spec_footnotes",
    "spec_notes",
    "symbols_blocks",
    "lcd_icons",
    "troubleshooting",
    "variable_defaults",
    "variable_lang_overrides",
    "manual_copy_source",
    "translation_memory",
}


@dataclass
class Issue:
    level: str  # "ERROR" | "WARN"
    msg: str


def is_list_of_str(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def as_path(p: str) -> Path:
    pp = Path(p)
    return pp if pp.is_absolute() else (ROOT / pp)


def has_tokenized_value(v: Any) -> bool:
    return isinstance(v, str) and ("{" in v and "}" in v)


def _non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError:
        raise RuntimeError("PyYAML not installed. Run: pip install pyyaml")

    # -------------------------------
    # YAML loader that rejects duplicate keys
    # -------------------------------
    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def _construct_mapping(loader: UniqueKeyLoader, node: yaml.Node, deep: bool = False):
        mapping = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise RuntimeError(f"[validate_config] Duplicate key detected in YAML: '{key}'")
            value = loader.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping

    UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        _construct_mapping,
    )

    with path.open("r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=UniqueKeyLoader) or {}

    if not isinstance(data, dict):
        raise RuntimeError("config root must be a mapping (YAML dict).")
    return data


def validate(cfg: dict, strict_files: bool) -> list[Issue]:
    issues: list[Issue] = []
    docs_dir_value = Paths(root=ROOT).docs_dir

    def _validate_optional_path(
        value: Any,
        *,
        key: str,
        require_non_empty: bool = False,
        expect_dir: bool = False,
    ) -> None:
        if value is None:
            return
        if not isinstance(value, str):
            issues.append(Issue("ERROR", f"{key} must be a string when provided"))
            return
        text = value.strip()
        if require_non_empty and not text:
            issues.append(Issue("ERROR", f"{key} must be a non-empty string when provided"))
            return
        if not text or not strict_files or has_tokenized_value(text):
            return
        candidate = as_path(text)
        if not candidate.exists():
            issues.append(Issue("ERROR", f"{key} path not found: {text}"))
            return
        if expect_dir and not candidate.is_dir():
            issues.append(Issue("ERROR", f"{key} must point to a directory: {text}"))

    # ---- build ----
    build = cfg.get("build", {})
    if not isinstance(build, dict):
        issues.append(Issue("ERROR", "build must be a mapping"))
        build = {}

    languages = build.get("languages", [])
    if not is_list_of_str(languages) or not languages:
        issues.append(Issue("ERROR", "build.languages must be non-empty list of strings"))

    include_lang_in_output_path = build.get("include_lang_in_output_path")
    if include_lang_in_output_path is not None and not isinstance(include_lang_in_output_path, bool):
        issues.append(Issue("ERROR", "build.include_lang_in_output_path must be a boolean when provided"))
    elif (
        include_lang_in_output_path is True
        and is_list_of_str(languages)
        and len(languages) != 1
    ):
        issues.append(Issue("ERROR", "build.include_lang_in_output_path requires exactly one build language"))

    default_model = build.get("default_model")
    if default_model is not None and (not isinstance(default_model, str) or not default_model.strip()):
        issues.append(Issue("ERROR", "build.default_model must be a non-empty string when provided"))

    default_region = build.get("default_region")
    if default_region is not None and (not isinstance(default_region, str) or not default_region.strip()):
        issues.append(Issue("ERROR", "build.default_region must be a non-empty string when provided"))

    raw_targets = build.get("targets")
    if raw_targets is not None:
        if not isinstance(raw_targets, list) or not raw_targets:
            issues.append(Issue("ERROR", "build.targets must be a non-empty list when provided"))
        else:
            for idx, item in enumerate(raw_targets, start=1):
                if not isinstance(item, dict):
                    issues.append(Issue("ERROR", f"build.targets[{idx}] must be a mapping"))
                    continue

                model = item.get("model")
                if not isinstance(model, str) or not model.strip():
                    issues.append(Issue("ERROR", f"build.targets[{idx}].model must be a non-empty string"))

                region = item.get("region")
                if region is not None and (not isinstance(region, str) or not region.strip()):
                    issues.append(Issue("ERROR", f"build.targets[{idx}].region must be a non-empty string when provided"))

    # ---- paths ----
    paths = cfg.get("paths", {})
    if paths is not None and not isinstance(paths, dict):
        issues.append(Issue("ERROR", "paths must be a mapping"))
        paths = {}
    else:
        docs_dir_raw = paths.get("docs_dir") if isinstance(paths, dict) else None
        if isinstance(docs_dir_raw, str) and docs_dir_raw.strip():
            docs_dir_value = as_path(docs_dir_raw.strip())

    _validate_optional_path(paths.get("structured_data_dir"), key="paths.structured_data_dir", require_non_empty=True, expect_dir=True)
    _validate_optional_path(paths.get("page_registry_csv"), key="paths.page_registry_csv", require_non_empty=True)
    _validate_optional_path(paths.get("page_blocks_dir"), key="paths.page_blocks_dir", require_non_empty=True, expect_dir=True)

    spec_master_csv = paths.get("spec_master_csv")
    if spec_master_csv is not None:
        if not isinstance(spec_master_csv, str) or not spec_master_csv.strip():
            issues.append(Issue("ERROR", "paths.spec_master_csv must be a non-empty string when provided"))
        elif strict_files and not has_tokenized_value(spec_master_csv):
            if not as_path(spec_master_csv).exists():
                issues.append(Issue("ERROR", f"spec_master_csv file not found: {spec_master_csv}"))

    spec_footnotes_csv = paths.get("spec_footnotes_csv")
    if spec_footnotes_csv is not None:
        if not isinstance(spec_footnotes_csv, str):
            issues.append(Issue("ERROR", "paths.spec_footnotes_csv must be a string when provided"))
        elif spec_footnotes_csv.strip() and strict_files and not has_tokenized_value(spec_footnotes_csv):
            if not as_path(spec_footnotes_csv).exists():
                issues.append(Issue("ERROR", f"spec_footnotes_csv file not found: {spec_footnotes_csv}"))

    spec_notes_csv = paths.get("spec_notes_csv")
    if spec_notes_csv is not None:
        if not isinstance(spec_notes_csv, str):
            issues.append(Issue("ERROR", "paths.spec_notes_csv must be a string when provided"))
        elif spec_notes_csv.strip() and strict_files and not has_tokenized_value(spec_notes_csv):
            if not as_path(spec_notes_csv).exists():
                issues.append(Issue("ERROR", f"spec_notes_csv file not found: {spec_notes_csv}"))

    spec_titles_csv = paths.get("spec_titles_csv")
    if spec_titles_csv is not None:
        if not isinstance(spec_titles_csv, str):
            issues.append(Issue("ERROR", "paths.spec_titles_csv must be a string when provided"))
        elif spec_titles_csv.strip() and strict_files and not has_tokenized_value(spec_titles_csv):
            if not as_path(spec_titles_csv).exists():
                issues.append(Issue("ERROR", f"spec_titles_csv file not found: {spec_titles_csv}"))

    page_manifest = paths.get("page_manifest")
    if page_manifest is not None:
        if not isinstance(page_manifest, str) or not page_manifest.strip():
            issues.append(Issue("ERROR", "paths.page_manifest must be a non-empty string when provided"))
        elif strict_files and not has_tokenized_value(page_manifest):
            manifest_path = resolve_page_manifest_path(cfg, root=ROOT)
            if manifest_path is not None and not manifest_path.exists():
                issues.append(Issue("ERROR", f"page_manifest file not found: {page_manifest}"))

    # ---- checks ----
    checks = cfg.get("checks", {})
    if checks is not None and not isinstance(checks, dict):
        issues.append(Issue("ERROR", "checks must be a mapping"))
        checks = {}

    allowed_foreign_identity_literals = checks.get("allowed_foreign_identity_literals")
    if allowed_foreign_identity_literals is not None:
        if not is_list_of_str(allowed_foreign_identity_literals):
            issues.append(Issue("ERROR", "checks.allowed_foreign_identity_literals must be a list of strings"))
        elif any(not item.strip() for item in allowed_foreign_identity_literals):
            issues.append(Issue("ERROR", "checks.allowed_foreign_identity_literals must not contain empty strings"))

    # ---- sync ----
    sync = cfg.get("sync", {})
    if sync is not None and not isinstance(sync, dict):
        issues.append(Issue("ERROR", "sync must be a mapping"))
        sync = {}

    phase2_raw = sync.get("phase2", {}) if isinstance(sync, dict) else {}
    if phase2_raw is not None and not isinstance(phase2_raw, dict):
        issues.append(Issue("ERROR", "sync.phase2 must be a mapping when provided"))
        phase2_raw = {}
    phase2 = phase2_raw if isinstance(phase2_raw, dict) else {}

    provider = phase2.get("provider")
    if provider is not None:
        if not isinstance(provider, str) or not provider.strip():
            issues.append(Issue("ERROR", "sync.phase2.provider must be a non-empty string when provided"))
        elif provider.strip().lower() not in SYNC_PHASE2_PROVIDERS:
            issues.append(
                Issue(
                    "ERROR",
                    "sync.phase2.provider must be one of: cli, lark-cli, lark_cli",
                )
            )

    for key in ("cli_bin", "base_token_env"):
        value = phase2.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            issues.append(Issue("ERROR", f"sync.phase2.{key} must be a non-empty string when provided"))

    for key in ("export_root", "manifest_path"):
        value = phase2.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            issues.append(Issue("ERROR", f"sync.phase2.{key} must be a non-empty string when provided"))

    spec_master_sources = phase2.get("spec_master_sources")
    if spec_master_sources is not None:
        if not isinstance(spec_master_sources, dict):
            issues.append(Issue("ERROR", "sync.phase2.spec_master_sources must be a mapping when provided"))
            spec_master_sources = {}
        for key in ("spec_rows_source_table_id", "page_placeholders_source_table_id"):
            value = spec_master_sources.get(key) if isinstance(spec_master_sources, dict) else None
            if value is not None and (not isinstance(value, str) or not value.strip()):
                issues.append(Issue("ERROR", f"sync.phase2.spec_master_sources.{key} must be a non-empty string when provided"))

    tables_raw = phase2.get("tables", {})
    if tables_raw is not None and not isinstance(tables_raw, dict):
        issues.append(Issue("ERROR", "sync.phase2.tables must be a mapping when provided"))
        tables_raw = {}
    tables = tables_raw if isinstance(tables_raw, dict) else {}
    for table_name, table_cfg in tables.items():
        if table_name not in SYNC_PHASE2_TABLES:
            issues.append(
                Issue(
                    "ERROR",
                    "sync.phase2.tables contains unsupported table key: "
                    f"{table_name}",
                )
            )
            continue
        if not isinstance(table_cfg, dict):
            issues.append(
                Issue(
                    "ERROR",
                    f"sync.phase2.tables.{table_name} must be a mapping",
                )
            )
            continue
        for key in ("base_token_env", "table_id_env", "view_id_env", "table_id", "view_id"):
            value = table_cfg.get(key)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                issues.append(
                    Issue(
                        "ERROR",
                        f"sync.phase2.tables.{table_name}.{key} must be a non-empty string when provided",
                    )
                )
        if not _non_empty_str(table_cfg.get("base_token_env")) and not _non_empty_str(phase2.get("base_token_env")):
            issues.append(
                Issue(
                    "ERROR",
                    f"sync.phase2.tables.{table_name}.base_token_env is required, "
                    "or provide sync.phase2.base_token_env",
                )
            )
        if (
            not _non_empty_str(table_cfg.get("table_id"))
            and not _non_empty_str(table_cfg.get("table_id_env"))
            and not (table_name == "spec_master" and has_source_table_ids(cfg))
        ):
            issues.append(
                Issue(
                    "ERROR",
                    f"sync.phase2.tables.{table_name}.table_id or "
                    f"sync.phase2.tables.{table_name}.table_id_env is required",
                )
            )

    # ---- pages ----
    try:
        resolved_pages = resolve_config_pages(
            cfg,
            default_languages=languages if is_list_of_str(languages) else None,
            root=ROOT,
        )
    except RuntimeError as exc:
        issues.append(Issue("ERROR", str(exc)))
        return issues
    parsed_pages = resolved_pages.pages
    issues.extend(Issue(level=i.level, msg=i.msg) for i in resolved_pages.issues)
    if any(i.level == "ERROR" for i in resolved_pages.issues):
        return issues

    allowed_languages = set(languages) if is_list_of_str(languages) else set()

    def _validate_page_languages(idx: int, key: str, raw_languages: tuple[str, ...]) -> None:
        if not raw_languages:
            issues.append(Issue("ERROR", f"pages[{idx}] {key} must not be empty"))
            return
        if not allowed_languages:
            return
        unknown = sorted({lang for lang in raw_languages if lang not in allowed_languages})
        if unknown:
            issues.append(
                Issue(
                    "ERROR",
                    f"pages[{idx}] {key} contains languages not declared in build.languages: "
                    + ", ".join(unknown),
                )
            )

    for idx, page in enumerate(parsed_pages, start=1):
        if isinstance(page, CoverPdfPage):
            if strict_files:
                if has_tokenized_value(page.file):
                    issues.append(
                        Issue(
                            "WARN",
                            f"pages[{idx}] cover_pdf file is tokenized, skip strict check",
                        )
                    )
                elif not as_path(page.file).exists():
                    issues.append(Issue("ERROR", f"cover file not found: {page.file}"))
            continue

        if isinstance(page, CsvPage):
            _validate_page_languages(idx, "csv_page.langs", page.langs)
            continue

        if isinstance(page, GeneratedPage):
            _validate_page_languages(idx, "generated_page.langs", page.langs)
            if strict_files:
                for raw_path, label in ((page.recipe, "recipe"), (page.template, "template")):
                    if has_tokenized_value(raw_path):
                        issues.append(
                            Issue(
                                "WARN",
                                f"pages[{idx}] generated_page {label} is tokenized, skip strict check",
                            )
                        )
                        continue
                    candidate = as_path(raw_path)
                    if not candidate.exists():
                        candidate = docs_dir_value / raw_path
                    if not candidate.exists():
                        issues.append(Issue("ERROR", f"generated_page {label} not found: {raw_path}"))
            continue

        if isinstance(page, PdfInsertPage):
            _validate_page_languages(idx, "pdf_insert.langs", page.langs)
            file_map_languages = tuple(page.file_map)
            _validate_page_languages(idx, "pdf_insert.file_map", file_map_languages)
            missing_file_map_languages = sorted(set(page.langs) - set(page.file_map))
            if missing_file_map_languages:
                issues.append(
                    Issue(
                        "ERROR",
                        "pages[{}] pdf_insert.file_map is missing entries for langs: {}".format(
                            idx,
                            ", ".join(missing_file_map_languages),
                        ),
                    )
                )
            if strict_files:
                for lang, fname in page.file_map.items():
                    if has_tokenized_value(fname):
                        issues.append(
                            Issue(
                                "WARN",
                                f"pages[{idx}] pdf_insert '{lang}' is tokenized, skip strict check",
                            )
                        )
                    elif not as_path(fname).exists():
                        issues.append(Issue("ERROR", f"pdf_insert file not found: {fname}"))
            continue

        if isinstance(page, RstIncludePage):
            if page.lang is not None:
                _validate_page_languages(idx, "rst_include.lang", (page.lang,))
            continue

    return issues


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/config.us.yaml")
    ap.add_argument("--strict-files", action="store_true")
    args = ap.parse_args()

    cfg_path = as_path(args.config)
    if not cfg_path.exists():
        raise SystemExit(f"[validate_config] ERROR: config not found: {cfg_path}")

    cfg = load_yaml(cfg_path)
    issues = validate(cfg, args.strict_files)

    errors = [i for i in issues if i.level == "ERROR"]
    warns = [i for i in issues if i.level == "WARN"]

    for w in warns:
        print(f"[validate_config] WARN: {w.msg}", file=sys.stderr)
    for e in errors:
        print(f"[validate_config] ERROR: {e.msg}", file=sys.stderr)

    if errors:
        raise SystemExit(1)

    print("[validate_config] OK")


if __name__ == "__main__":
    main()
