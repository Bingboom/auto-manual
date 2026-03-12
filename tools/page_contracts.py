#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PageContract:
    page_id: str
    source_files: tuple[str, ...]
    required_placeholders: dict[str, tuple[str, ...]]


def _normalize_rel_path(value: str) -> str:
    return Path(value.strip().replace("\\", "/")).as_posix()


def _normalize_placeholder_map(raw: object) -> dict[str, tuple[str, ...]]:
    if isinstance(raw, list):
        values = tuple(str(item).strip() for item in raw if str(item).strip())
        return {"default": values}

    if not isinstance(raw, dict):
        raise RuntimeError("required_placeholders must be a list or mapping")

    out: dict[str, tuple[str, ...]] = {}
    for lang, values_raw in raw.items():
        if not isinstance(values_raw, list):
            raise RuntimeError(f"required_placeholders.{lang} must be a list")
        values = tuple(str(item).strip() for item in values_raw if str(item).strip())
        out[str(lang).strip().lower() or "default"] = values
    return out


def load_page_contracts(contracts_dir: Path) -> list[PageContract]:
    if not contracts_dir.exists():
        return []

    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML not installed. Please run: pip install pyyaml") from exc

    contracts: list[PageContract] = []
    for path in sorted(contracts_dir.glob("*.y*ml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise RuntimeError(f"Invalid page contract root: {path}")

        page_id = str(data.get("page_id", "")).strip()
        if not page_id:
            raise RuntimeError(f"page_id is required in contract: {path}")

        source_files_raw = data.get("source_files")
        if not isinstance(source_files_raw, list) or not source_files_raw:
            raise RuntimeError(f"source_files must be a non-empty list in contract: {path}")
        source_files = tuple(_normalize_rel_path(str(item)) for item in source_files_raw if str(item).strip())
        if not source_files:
            raise RuntimeError(f"source_files must contain at least one non-empty entry in contract: {path}")

        placeholders = _normalize_placeholder_map(data.get("required_placeholders", []))
        contracts.append(
            PageContract(
                page_id=page_id,
                source_files=source_files,
                required_placeholders=placeholders,
            )
        )
    return contracts


def find_contract_for_source(source_rel_path: str, contracts: list[PageContract]) -> PageContract | None:
    normalized = _normalize_rel_path(source_rel_path)
    for contract in contracts:
        if normalized in contract.source_files:
            return contract
    return None


def required_placeholders_for_lang(contract: PageContract, lang: str | None) -> tuple[str, ...]:
    lang_key = (lang or "").strip().lower()
    default_values = list(contract.required_placeholders.get("default", ()))
    lang_values = list(contract.required_placeholders.get(lang_key, ())) if lang_key else []

    seen: set[str] = set()
    out: list[str] = []
    for item in [*default_values, *lang_values]:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return tuple(out)
