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
    required_spec_keys: dict[str, tuple[str, ...]]
    required_tpl_keys: dict[str, tuple[str, ...]]
    required_assets: dict[str, tuple[str, ...]]
    allowed_languages: tuple[str, ...]
    allowed_regions: tuple[str, ...]
    allowed_models: tuple[str, ...]


def _normalize_rel_path(value: str) -> str:
    return Path(value.strip().replace("\\", "/")).as_posix()


def _normalize_requirement_map(raw: object) -> dict[str, tuple[str, ...]]:
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


def _normalize_allowed_list(raw: object, *, lower: bool = False) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise RuntimeError("allowed_* must be a list when provided")

    values: list[str] = []
    for item in raw:
        value = str(item).strip()
        if not value:
            continue
        values.append(value.lower() if lower else value)
    return tuple(values)


def _validate_tpl_keys(values: dict[str, tuple[str, ...]], *, path: Path) -> None:
    for lang, items in values.items():
        for item in items:
            if item.startswith("tpl_"):
                continue
            raise RuntimeError(f"required_tpl_keys.{lang} must keep the 'tpl_' prefix in contract: {path}")


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

        placeholders = _normalize_requirement_map(data.get("required_placeholders", []))
        required_spec_keys = _normalize_requirement_map(data.get("required_spec_keys", []))
        required_tpl_keys = _normalize_requirement_map(data.get("required_tpl_keys", []))
        _validate_tpl_keys(required_tpl_keys, path=path)
        required_assets = _normalize_requirement_map(data.get("required_assets", []))
        allowed_languages = _normalize_allowed_list(data.get("allowed_languages"), lower=True)
        allowed_regions = _normalize_allowed_list(data.get("allowed_regions"))
        allowed_models = _normalize_allowed_list(data.get("allowed_models"))
        contracts.append(
            PageContract(
                page_id=page_id,
                source_files=source_files,
                required_placeholders=placeholders,
                required_spec_keys=required_spec_keys,
                required_tpl_keys=required_tpl_keys,
                required_assets=required_assets,
                allowed_languages=allowed_languages,
                allowed_regions=allowed_regions,
                allowed_models=allowed_models,
            )
        )
    return contracts


def find_contract_for_source(source_rel_path: str, contracts: list[PageContract]) -> PageContract | None:
    normalized = _normalize_rel_path(source_rel_path)
    for contract in contracts:
        if normalized in contract.source_files:
            return contract
    return None


def _requirements_for_lang(requirements: dict[str, tuple[str, ...]], lang: str | None) -> tuple[str, ...]:
    lang_key = (lang or "").strip().lower()
    default_values = list(requirements.get("default", ()))
    lang_values = list(requirements.get(lang_key, ())) if lang_key else []

    seen: set[str] = set()
    out: list[str] = []
    for item in [*default_values, *lang_values]:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return tuple(out)


def required_placeholders_for_lang(contract: PageContract, lang: str | None) -> tuple[str, ...]:
    return _requirements_for_lang(contract.required_placeholders, lang)


def required_spec_keys_for_lang(contract: PageContract, lang: str | None) -> tuple[str, ...]:
    return _requirements_for_lang(contract.required_spec_keys, lang)


def required_tpl_keys_for_lang(contract: PageContract, lang: str | None) -> tuple[str, ...]:
    return _requirements_for_lang(contract.required_tpl_keys, lang)


def required_assets_for_lang(contract: PageContract, lang: str | None) -> tuple[str, ...]:
    return _requirements_for_lang(contract.required_assets, lang)


def contract_applies_to(
    contract: PageContract,
    *,
    lang: str | None,
    model: str | None,
    region: str | None,
) -> bool:
    lang_key = (lang or "").strip().lower()
    if contract.allowed_languages and lang_key not in contract.allowed_languages:
        return False
    if contract.allowed_models and (model or "").strip() not in contract.allowed_models:
        return False
    if contract.allowed_regions and (region or "").strip() not in contract.allowed_regions:
        return False
    return True
