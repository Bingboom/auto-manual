#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.utils.spec_master import (
    read_spec_master_rows,
    resolve_spec_value_from_rows,
    resolve_template_substitutions_from_rows,
)
from tools.word_bundle_common import apply_rst_substitutions, resolve_config_path


SNIPPET_TOKEN_PREFIX = "{{snippet:"
SNIPPET_TOKEN_SUFFIX = "}}"


@dataclass(frozen=True)
class DraftFieldBinding:
    row_key: str
    pages: tuple[str, ...]
    line_order: str | None
    default: str | None = None


@dataclass(frozen=True)
class DraftRecipe:
    page_id: str
    template: str
    field_map: dict[str, DraftFieldBinding]
    required_row_keys: tuple[str, ...]
    snippet_slots: dict[str, str]
    contracts: tuple[str, ...]


@dataclass(frozen=True)
class SnippetEntry:
    snippet_id: str
    file: str
    lang: str
    regions: tuple[str, ...]
    required_placeholders: tuple[str, ...]
    tags: tuple[str, ...]


@dataclass(frozen=True)
class GeneratedPageRender:
    text: str
    template_path: Path
    recipe_path: Path
    recipe: DraftRecipe
    used_snippet_ids: tuple[str, ...]
    rendered_source_path: Path | None


def _load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML not installed. Please run: pip install pyyaml") from exc
    if not path.exists():
        raise RuntimeError(f"YAML file not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def resolve_snippet_registry_path(docs_dir: Path) -> Path:
    return docs_dir / "templates" / "snippets" / "registry.yaml"


def _normalize_csv_or_list(raw: object, *, field_name: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        values = [item.strip() for item in raw.split(",") if item.strip()]
        return tuple(values)
    if isinstance(raw, list):
        values = [str(item).strip() for item in raw if str(item).strip()]
        return tuple(values)
    raise RuntimeError(f"{field_name} must be a string or list")


def _normalize_field_binding(raw: object, *, placeholder: str) -> DraftFieldBinding:
    if isinstance(raw, str):
        row_key = raw.strip()
        if not row_key:
            raise RuntimeError(f"field_map.{placeholder} must be a non-empty string")
        return DraftFieldBinding(
            row_key=row_key,
            pages=("spec", "specifications"),
            line_order=None,
        )

    if not isinstance(raw, dict):
        raise RuntimeError(f"field_map.{placeholder} must be a string or mapping")

    row_key = str(raw.get("row_key", "")).strip()
    if not row_key:
        raise RuntimeError(f"field_map.{placeholder}.row_key is required")

    pages = _normalize_csv_or_list(raw.get("pages"), field_name=f"field_map.{placeholder}.pages")
    line_order_raw = raw.get("line_order")
    line_order = str(line_order_raw).strip() if line_order_raw is not None and str(line_order_raw).strip() else None
    default_raw = raw.get("default")
    default = str(default_raw) if default_raw is not None else None

    return DraftFieldBinding(
        row_key=row_key,
        pages=pages or ("spec", "specifications"),
        line_order=line_order,
        default=default,
    )


def load_draft_recipe(path: Path) -> DraftRecipe:
    data = _load_yaml(path)
    if not isinstance(data, dict):
        raise RuntimeError(f"Draft recipe root must be a mapping: {path}")

    page_id = str(data.get("page_id", "")).strip()
    if not page_id:
        raise RuntimeError(f"page_id is required in draft recipe: {path}")

    template = str(data.get("template", "")).strip()
    if not template:
        raise RuntimeError(f"template is required in draft recipe: {path}")

    field_map_raw = data.get("field_map", {})
    if not isinstance(field_map_raw, dict):
        raise RuntimeError(f"field_map must be a mapping in draft recipe: {path}")
    field_map = {
        str(placeholder).strip(): _normalize_field_binding(binding_raw, placeholder=str(placeholder).strip())
        for placeholder, binding_raw in field_map_raw.items()
        if str(placeholder).strip()
    }

    required_row_keys = _normalize_csv_or_list(data.get("required_row_keys"), field_name="required_row_keys")
    snippet_slots_raw = data.get("snippet_slots", {})
    if not isinstance(snippet_slots_raw, dict):
        raise RuntimeError(f"snippet_slots must be a mapping in draft recipe: {path}")
    snippet_slots = {
        str(slot).strip(): str(snippet_id).strip()
        for slot, snippet_id in snippet_slots_raw.items()
        if str(slot).strip() and str(snippet_id).strip()
    }
    contracts = _normalize_csv_or_list(data.get("contracts"), field_name="contracts")

    return DraftRecipe(
        page_id=page_id,
        template=template,
        field_map=field_map,
        required_row_keys=required_row_keys,
        snippet_slots=snippet_slots,
        contracts=contracts,
    )


def load_snippet_registry(registry_path: Path) -> list[SnippetEntry]:
    data = _load_yaml(registry_path)
    entries_raw: object
    if isinstance(data, list):
        entries_raw = data
    elif isinstance(data, dict):
        entries_raw = data.get("snippets", [])
    else:
        raise RuntimeError(f"Snippet registry root must be a mapping or list: {registry_path}")

    if not isinstance(entries_raw, list):
        raise RuntimeError(f"snippets must be a list in snippet registry: {registry_path}")

    entries: list[SnippetEntry] = []
    for idx, raw in enumerate(entries_raw, start=1):
        if not isinstance(raw, dict):
            raise RuntimeError(f"snippets[{idx}] must be a mapping in snippet registry: {registry_path}")
        snippet_id = str(raw.get("snippet_id", "")).strip()
        file = str(raw.get("file", "")).strip()
        lang = str(raw.get("lang", "")).strip().lower()
        if not snippet_id or not file or not lang:
            raise RuntimeError(
                f"snippets[{idx}] must include snippet_id, file, and lang in snippet registry: {registry_path}"
            )
        entries.append(
            SnippetEntry(
                snippet_id=snippet_id,
                file=file,
                lang=lang,
                regions=_normalize_csv_or_list(raw.get("regions"), field_name=f"snippets[{idx}].regions"),
                required_placeholders=_normalize_csv_or_list(
                    raw.get("required_placeholders"),
                    field_name=f"snippets[{idx}].required_placeholders",
                ),
                tags=_normalize_csv_or_list(raw.get("tags"), field_name=f"snippets[{idx}].tags"),
            )
        )
    return entries


def collect_registry_snippet_ids(entries: list[SnippetEntry]) -> set[str]:
    return {entry.snippet_id for entry in entries}


def _match_snippet_entry(
    entries: list[SnippetEntry],
    *,
    snippet_id: str,
    lang: str,
    region: str | None,
) -> SnippetEntry | None:
    exact_region: list[SnippetEntry] = []
    default_region: list[SnippetEntry] = []
    for entry in entries:
        if entry.snippet_id != snippet_id or entry.lang != lang.lower():
            continue
        if entry.regions and (region or "").strip() in entry.regions:
            exact_region.append(entry)
            continue
        if not entry.regions:
            default_region.append(entry)

    if exact_region:
        return sorted(exact_region, key=lambda item: item.file)[0]
    if default_region:
        return sorted(default_region, key=lambda item: item.file)[0]
    return None


def select_snippet_entry(
    entries: list[SnippetEntry],
    *,
    snippet_id: str,
    lang: str,
    region: str | None,
) -> SnippetEntry:
    entry = _match_snippet_entry(entries, snippet_id=snippet_id, lang=lang, region=region)
    if entry is None:
        raise RuntimeError(
            f"Snippet '{snippet_id}' is not defined for lang '{lang}'"
            + (f" and region '{region}'" if (region or "").strip() else "")
        )
    return entry


def resolve_snippet_file_path(
    entry: SnippetEntry,
    *,
    docs_dir: Path,
    registry_path: Path,
    model: str | None,
    region: str | None,
) -> Path:
    candidate = Path(entry.file)
    if candidate.is_absolute():
        return candidate

    docs_candidate = resolve_config_path(docs_dir, entry.file, model, region)
    if docs_candidate.exists():
        return docs_candidate

    registry_candidate = registry_path.parent / candidate
    if registry_candidate.exists():
        return registry_candidate
    return docs_candidate


def _derive_label_lower(value: str) -> str:
    tokens = value.split()
    lowered: list[str] = []
    for token in tokens:
        if token.upper() == "BUTTON":
            lowered.append("button")
            continue
        if token.isupper():
            lowered.append(token)
            continue
        lowered.append(token.lower())
    return " ".join(lowered)


def _with_derived_bindings(substitutions: dict[str, str]) -> dict[str, str]:
    out = dict(substitutions)
    for key, value in list(out.items()):
        if not value or key.endswith("_BOLD") or key.endswith("_LOWER"):
            continue
        out.setdefault(f"{key}_BOLD", f"**{value}**")
        if key.endswith("_LABEL"):
            out.setdefault(f"{key}_LOWER", _derive_label_lower(value))
    return out


def resolve_recipe_substitutions(
    recipe: DraftRecipe,
    *,
    spec_rows: list[dict[str, str]],
    model: str | None,
    region: str | None,
    lang: str,
) -> dict[str, str]:
    substitutions = resolve_template_substitutions_from_rows(
        spec_rows,
        model=model,
        region=region,
        lang=lang,
    )
    for placeholder, binding in recipe.field_map.items():
        match = resolve_spec_value_from_rows(
            spec_rows,
            model=model,
            region=region,
            lang=lang,
            row_key=binding.row_key,
            pages=binding.pages,
            line_order=binding.line_order,
        )
        if match is not None:
            substitutions[placeholder] = match.value
            continue
        if binding.default is not None:
            substitutions[placeholder] = binding.default
    return _with_derived_bindings(substitutions)


def missing_required_row_keys(
    recipe: DraftRecipe,
    *,
    spec_rows: list[dict[str, str]],
    model: str | None,
    region: str | None,
    lang: str,
) -> list[str]:
    missing: list[str] = []
    for row_key in recipe.required_row_keys:
        match = resolve_spec_value_from_rows(
            spec_rows,
            model=model,
            region=region,
            lang=lang,
            row_key=row_key,
        )
        if match is None:
            missing.append(row_key)
    return missing


def _render_snippet_text(
    *,
    template_text: str,
    substitutions: dict[str, str],
    vars_map: dict[str, str],
) -> str:
    text = apply_rst_substitutions(template_text, substitutions, vars_map)
    return text if text.endswith("\n") else f"{text}\n"


def render_generated_page(
    *,
    docs_dir: Path,
    recipe_path: Path,
    template_path: Path,
    spec_master_csv: Path,
    registry_path: Path,
    vars_map: dict[str, str],
    base_substitutions: dict[str, str],
    model: str | None,
    region: str | None,
    lang: str,
    rendered_source_path: Path | None = None,
) -> GeneratedPageRender:
    recipe = load_draft_recipe(recipe_path)
    spec_rows = read_spec_master_rows(spec_master_csv)
    substitutions = {
        **base_substitutions,
        **resolve_recipe_substitutions(
            recipe,
            spec_rows=spec_rows,
            model=model,
            region=region,
            lang=lang,
        ),
    }

    missing_row_keys = missing_required_row_keys(
        recipe,
        spec_rows=spec_rows,
        model=model,
        region=region,
        lang=lang,
    )
    if missing_row_keys:
        raise RuntimeError(
            f"Draft recipe '{recipe.page_id}' is missing required Spec_Master row(s) for lang '{lang}': "
            f"{', '.join(missing_row_keys)}"
        )

    registry_entries = load_snippet_registry(registry_path)
    template_text = template_path.read_text(encoding="utf-8")
    used_snippet_ids: list[str] = []
    for slot_name, snippet_id in recipe.snippet_slots.items():
        token = f"{SNIPPET_TOKEN_PREFIX}{slot_name}{SNIPPET_TOKEN_SUFFIX}"
        if token not in template_text:
            continue
        entry = select_snippet_entry(
            registry_entries,
            snippet_id=snippet_id,
            lang=lang,
            region=region,
        )
        missing_placeholders = [
            placeholder for placeholder in entry.required_placeholders if not (substitutions.get(placeholder) or "").strip()
        ]
        if missing_placeholders:
            raise RuntimeError(
                f"Snippet '{snippet_id}' is missing required placeholders for lang '{lang}': "
                f"{', '.join(missing_placeholders)}"
            )
        snippet_path = resolve_snippet_file_path(
            entry,
            docs_dir=docs_dir,
            registry_path=registry_path,
            model=model,
            region=region,
        )
        if not snippet_path.exists():
            raise RuntimeError(f"Snippet file not found for '{snippet_id}': {snippet_path}")
        snippet_text = _render_snippet_text(
            template_text=snippet_path.read_text(encoding="utf-8"),
            substitutions=substitutions,
            vars_map=vars_map,
        )
        template_text = template_text.replace(token, snippet_text.rstrip("\n"))
        used_snippet_ids.append(snippet_id)

    rendered = apply_rst_substitutions(template_text, substitutions, vars_map)
    if rendered_source_path is not None:
        rendered_source_path.parent.mkdir(parents=True, exist_ok=True)
        rendered_source_path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")

    return GeneratedPageRender(
        text=rendered,
        template_path=template_path,
        recipe_path=recipe_path,
        recipe=recipe,
        used_snippet_ids=tuple(dict.fromkeys(used_snippet_ids)),
        rendered_source_path=rendered_source_path,
    )
