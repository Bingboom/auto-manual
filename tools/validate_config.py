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


SUPPORTED_PAGE_TYPES = {"cover_pdf", "csv_page", "pdf_insert"}


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

    # ---- pages ----
    pages = cfg.get("pages", None)
    if not isinstance(pages, list) or not pages:
        issues.append(Issue("ERROR", "pages must be non-empty list"))
        return issues

    for idx, p in enumerate(pages, start=1):
        if not isinstance(p, dict):
            issues.append(Issue("ERROR", f"pages[{idx}] must be mapping"))
            continue

        ptype = p.get("type")
        if ptype not in SUPPORTED_PAGE_TYPES:
            issues.append(Issue("ERROR", f"pages[{idx}].type invalid: {ptype}"))
            continue

        if ptype == "cover_pdf":
            if "file" not in p:
                issues.append(Issue("ERROR", f"pages[{idx}] cover_pdf requires file"))
            elif strict_files:
                f = p["file"]
                if has_tokenized_value(f):
                    issues.append(Issue("WARN", f"pages[{idx}] cover_pdf file is tokenized, skip strict check"))
                elif not as_path(f).exists():
                    issues.append(Issue("ERROR", f"cover file not found: {p['file']}"))

        elif ptype == "csv_page":
            page_name = p.get("page")
            if not page_name:
                issues.append(Issue("ERROR", f"pages[{idx}] csv_page requires page"))
                continue

            source = str(p.get("source", "phase1")).strip().lower()
            if source != "phase1":
                issues.append(Issue("ERROR", f"pages[{idx}] csv_page.source invalid: {source}"))

            plangs = p.get("langs", languages)
            if not is_list_of_str(plangs):
                issues.append(Issue("ERROR", f"pages[{idx}] csv_page.langs invalid"))

            if "include_dir" in p and not isinstance(p.get("include_dir"), str):
                issues.append(Issue("ERROR", f"pages[{idx}] csv_page.include_dir must be string"))

        elif ptype == "pdf_insert":
            file_map = p.get("file_map")
            if not isinstance(file_map, dict):
                issues.append(Issue("ERROR", f"pages[{idx}] pdf_insert requires file_map"))
            else:
                for lang, fname in file_map.items():
                    if strict_files:
                        if has_tokenized_value(fname):
                            issues.append(Issue("WARN", f"pages[{idx}] pdf_insert '{lang}' is tokenized, skip strict check"))
                        elif not as_path(fname).exists():
                            issues.append(Issue("ERROR", f"pdf_insert file not found: {fname}"))

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
