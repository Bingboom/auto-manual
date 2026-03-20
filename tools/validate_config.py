#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/validate_config.py

P0 validator for config.yaml.

Checks:
- YAML readable
- Detect duplicate YAML keys (fail-fast)
- Required sections exist
- pages DSL structure valid
- csv_page source check (phase1-only)
- Optional file existence checks
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.config_pages import (
    CoverPdfPage,
    CsvPage,
    PdfInsertPage,
    RstIncludePage,
    parse_config_pages,
)


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

    spec_titles_csv = paths.get("spec_titles_csv")
    if spec_titles_csv is not None:
        if not isinstance(spec_titles_csv, str):
            issues.append(Issue("ERROR", "paths.spec_titles_csv must be a string when provided"))
        elif spec_titles_csv.strip() and strict_files and not has_tokenized_value(spec_titles_csv):
            if not as_path(spec_titles_csv).exists():
                issues.append(Issue("ERROR", f"spec_titles_csv file not found: {spec_titles_csv}"))

    # ---- pages ----
    parsed_pages, page_issues = parse_config_pages(
        cfg.get("pages", None),
        default_languages=languages if is_list_of_str(languages) else None,
    )
    issues.extend(Issue(level=i.level, msg=i.msg) for i in page_issues)
    if any(i.level == "ERROR" for i in page_issues):
        return issues

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
            continue

        if isinstance(page, PdfInsertPage):
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
            continue

    return issues


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
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
