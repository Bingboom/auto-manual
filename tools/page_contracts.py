#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar


@dataclass(frozen=True)
class PageValueSelector:
    row_key: str
    pages: tuple[str, ...] = ()
    line_order: str | None = None
    usage_type: str | None = None
    placement_key: str | None = None
    value_role: str | None = None
    variant_key: str | None = None


@dataclass(frozen=True)
class PageContract:
    page_id: str
    source_files: tuple[str, ...]
    required_placeholders: dict[str, tuple[str, ...]]
    required_copy_keys: dict[str, tuple[str, ...]]
    required_spec_keys: dict[str, tuple[str, ...]]
    required_page_values: dict[str, tuple[PageValueSelector, ...]]
    required_assets: dict[str, tuple[str, ...]]
    allowed_languages: tuple[str, ...]
    allowed_regions: tuple[str, ...]
    allowed_models: tuple[str, ...]


T = TypeVar("T")


def _normalize_rel_path(value: str) -> str:
    return Path(value.strip().replace("\\", "/")).as_posix()


def _normalize_requirement_map(raw: object, *, field_name: str) -> dict[str, tuple[str, ...]]:
    if isinstance(raw, list):
        values = tuple(str(item).strip() for item in raw if str(item).strip())
        return {"default": values}

    if not isinstance(raw, dict):
        raise RuntimeError(f"{field_name} must be a list or mapping")

    out: dict[str, tuple[str, ...]] = {}
    for lang, values_raw in raw.items():
        if not isinstance(values_raw, list):
            raise RuntimeError(f"{field_name}.{lang} must be a list")
        values = tuple(str(item).strip() for item in values_raw if str(item).strip())
        out[_normalize_requirement_key(str(lang), field_name=field_name)] = values
    return out


def _normalize_requirement_key(raw_key: str, *, field_name: str) -> str:
    """Normalize a requirement-map key.

    Language keys keep their historical lower-casing. Tier keys
    (``category:``/``region:``/``capability:``) keep their value's case,
    because they are matched against config/data values that are case
    significant (``MAIN``, ``US``, ``UPS功能``).
    """

    key = raw_key.strip()
    if not key:
        return "default"
    normalized_atoms: list[str] = []
    for raw_atom in key.split("+"):
        atom = raw_atom.strip()
        if not atom:
            raise RuntimeError(f"{field_name}.{raw_key} has an empty conjunction atom")
        for prefix in _TIER_PREFIXES:
            if atom.startswith(prefix):
                value = atom[len(prefix):].strip()
                if not value:
                    raise RuntimeError(f"{field_name}.{raw_key} tier key is missing a value")
                normalized_atoms.append(f"{prefix}{value}")
                break
        else:
            normalized_atoms.append(atom.lower())
    return "+".join(normalized_atoms)


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


def _normalize_pages(raw: object, *, field_name: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        return tuple(item.strip() for item in raw.split(",") if item.strip())
    if isinstance(raw, list):
        return tuple(str(item).strip() for item in raw if str(item).strip())
    raise RuntimeError(f"{field_name} must be a string or list")


def _normalize_page_value_selector(raw: object, *, field_name: str) -> PageValueSelector:
    if isinstance(raw, str):
        row_key = raw.strip()
        if not row_key:
            raise RuntimeError(f"{field_name} must be a non-empty string")
        return PageValueSelector(row_key=row_key)

    if not isinstance(raw, dict):
        raise RuntimeError(f"{field_name} must be a string or mapping")

    row_key = str(raw.get("row_key", "")).strip()
    if not row_key:
        raise RuntimeError(f"{field_name}.row_key is required")

    line_order_raw = raw.get("line_order")
    line_order = str(line_order_raw).strip() if line_order_raw is not None and str(line_order_raw).strip() else None
    usage_type_raw = raw.get("usage_type")
    usage_type = str(usage_type_raw).strip().lower() if usage_type_raw is not None and str(usage_type_raw).strip() else None
    placement_key_raw = raw.get("placement_key")
    placement_key = (
        str(placement_key_raw).strip().lower()
        if placement_key_raw is not None and str(placement_key_raw).strip()
        else None
    )
    value_role_raw = raw.get("value_role")
    value_role = str(value_role_raw).strip().lower() if value_role_raw is not None and str(value_role_raw).strip() else None
    variant_key_raw = raw.get("variant_key")
    variant_key = str(variant_key_raw).strip().lower() if variant_key_raw is not None and str(variant_key_raw).strip() else None

    return PageValueSelector(
        row_key=row_key,
        pages=_normalize_pages(raw.get("pages"), field_name=f"{field_name}.pages"),
        line_order=line_order,
        usage_type=usage_type,
        placement_key=placement_key,
        value_role=value_role,
        variant_key=variant_key,
    )


def _normalize_page_value_map(raw: object, *, field_name: str) -> dict[str, tuple[PageValueSelector, ...]]:
    if isinstance(raw, list):
        values = tuple(
            _normalize_page_value_selector(item, field_name=f"{field_name}.default[{idx}]")
            for idx, item in enumerate(raw)
        )
        return {"default": values}

    if not isinstance(raw, dict):
        raise RuntimeError(f"{field_name} must be a list or mapping")

    out: dict[str, tuple[PageValueSelector, ...]] = {}
    for lang, values_raw in raw.items():
        if not isinstance(values_raw, list):
            raise RuntimeError(f"{field_name}.{lang} must be a list")
        values = tuple(
            _normalize_page_value_selector(item, field_name=f"{field_name}.{lang}[{idx}]")
            for idx, item in enumerate(values_raw)
        )
        out[_normalize_requirement_key(str(lang), field_name=field_name)] = values
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

        placeholders = _normalize_requirement_map(data.get("required_placeholders", []), field_name="required_placeholders")
        required_copy_keys = _normalize_requirement_map(data.get("required_copy_keys", []), field_name="required_copy_keys")
        required_spec_keys = _normalize_requirement_map(data.get("required_spec_keys", []), field_name="required_spec_keys")
        required_page_values = _normalize_page_value_map(
            data.get("required_page_values", data.get("required_page_value_keys", data.get("required_tpl_keys", []))),
            field_name="required_page_values",
        )
        required_assets = _normalize_requirement_map(data.get("required_assets", []), field_name="required_assets")
        allowed_languages = _normalize_allowed_list(data.get("allowed_languages"), lower=True)
        allowed_regions = _normalize_allowed_list(data.get("allowed_regions"))
        allowed_models = _normalize_allowed_list(data.get("allowed_models"))
        contracts.append(
            PageContract(
                page_id=page_id,
                source_files=source_files,
                required_placeholders=placeholders,
                required_copy_keys=required_copy_keys,
                required_spec_keys=required_spec_keys,
                required_page_values=required_page_values,
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


@dataclass(frozen=True)
class ContractContext:
    """Applicability context a contract requirement map is resolved against.

    Tier keys let one shared contract serve several skeleton families without
    forking: the host-only placeholder groups live under ``category:MAIN``
    instead of ``default``, so a battery-pack target simply never selects them.
    Before this existed, the only escape from an inapplicable ``default`` group
    was forking the whole contract (docs/templates/contracts/
    03_product_overview_je300e.yaml is the precedent that cost 1 contract +
    5 template copies).
    """

    lang: str | None = None
    category: str | None = None
    region: str | None = None
    capabilities: frozenset[str] = frozenset()


_TIER_PREFIXES = ("category:", "region:", "capability:")

DEFAULT_CATEGORY = "MAIN"


def resolve_category(build_cfg: object) -> str:
    """The product line for one build, read from ``build.skeleton_family``.

    Single source for the whole axis: the contract tiers resolved here, the
    Sphinx ``-t category_*`` tag, and the manual IR's ``category_*`` atom all
    read this. Were any of them to re-derive the value or the default on its
    own, a carrier's ``category:`` requirement could resolve against one line
    while its ``.. only:: category_*`` body resolved against another.
    """

    if isinstance(build_cfg, dict):
        raw = str(build_cfg.get("skeleton_family") or "").strip()
        if raw:
            return raw
    return DEFAULT_CATEGORY


def contract_tier_keys(context: ContractContext) -> tuple[str, ...]:
    """Atoms this context selects, in fixed precedence order.

    ``default`` always applies. Then category, then region, then each TRUE
    capability, then the language atom — narrowest last so a language-scoped
    group still wins, exactly as before tiering existed.
    """

    keys: list[str] = ["default"]
    category = (context.category or "").strip()
    if category:
        keys.append(f"category:{category}")
    region = (context.region or "").strip()
    if region:
        keys.append(f"region:{region}")
    for capability in sorted(context.capabilities):
        capability_text = capability.strip()
        if capability_text:
            keys.append(f"capability:{capability_text}")
    lang_key = (context.lang or "").strip().lower()
    if lang_key:
        keys.append(lang_key)
    return tuple(keys)


def _requirements_for_context(
    requirements: dict[str, tuple[T, ...]],
    context: ContractContext,
) -> tuple[T, ...]:
    """Collect every requirement group whose key the context satisfies.

    A key is a ``+``-joined conjunction of atoms and applies only when the
    context selects *all* of them, so "host line AND this language" is
    expressible as ``category:MAIN+en``. Without conjunction, a placeholder
    that exists in the host templates of some languages but not others (the
    JP overview omits FRONT_TOTAL_OUTPUT_*) could only be expressed by a bare
    language key — which a battery-pack target sharing those languages would
    then wrongly select.

    Groups are emitted broadest-first (fewer atoms, then by atom precedence)
    so the resolved order is deterministic and independent of mapping order.
    """

    declared_categories = sorted(
        {
            part[len("category:"):]
            for key in requirements
            for part in key.split("+")
            if part.startswith("category:")
        }
    )
    context_category = (context.category or "").strip()
    if declared_categories and context_category not in declared_categories:
        rendered_category = context_category or "<missing>"
        raise RuntimeError(
            "contract requirement map declares category tiers "
            f"({', '.join(declared_categories)}), but context category "
            f"{rendered_category!r} is not declared; add an explicit "
            "category:<value> group (an empty list is allowed) or fix "
            "build.skeleton_family"
        )

    atoms = contract_tier_keys(context)
    atom_rank = {atom: index for index, atom in enumerate(atoms)}
    selected: list[tuple[int, int, str]] = []
    for key in requirements:
        parts = [part.strip() for part in key.split("+") if part.strip()]
        if not parts or any(part not in atom_rank for part in parts):
            continue
        selected.append((len(parts), min(atom_rank[part] for part in parts), key))
    selected.sort()

    seen: set[T] = set()
    out: list[T] = []
    for _count, _rank, key in selected:
        for item in requirements.get(key, ()):
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
    return tuple(out)


def _coerce_context(
    context: ContractContext | str | None,
    requirements: dict[str, tuple[T, ...]],
) -> ContractContext:
    """Accept a bare lang for tier-free requirement maps only.

    A bare lang carries no category/region/capability, so on a tiered map it
    would silently resolve to a near-empty requirement set — a weakened gate
    that still reports success. Refuse instead: the caller must say which
    context it means.
    """

    if isinstance(context, ContractContext):
        return context
    tiered = sorted(
        key for key in requirements
        if "+" in key or any(key.startswith(prefix) for prefix in _TIER_PREFIXES)
    )
    if tiered:
        raise RuntimeError(
            "contract requirement map has tier keys "
            f"({', '.join(tiered)}); pass a ContractContext instead of a bare lang"
        )
    return ContractContext(lang=context)


def _requirements_for_lang(
    requirements: dict[str, tuple[T, ...]],
    lang: ContractContext | str | None,
) -> tuple[T, ...]:
    return _requirements_for_context(requirements, _coerce_context(lang, requirements))


def required_placeholders_for_lang(
    contract: PageContract,
    lang: ContractContext | str | None,
) -> tuple[str, ...]:
    return _requirements_for_lang(contract.required_placeholders, lang)


def required_copy_keys_for_lang(
    contract: PageContract,
    lang: ContractContext | str | None,
) -> tuple[str, ...]:
    return _requirements_for_lang(contract.required_copy_keys, lang)


def required_spec_keys_for_lang(
    contract: PageContract,
    lang: ContractContext | str | None,
) -> tuple[str, ...]:
    return _requirements_for_lang(contract.required_spec_keys, lang)


def required_page_values_for_lang(
    contract: PageContract,
    lang: ContractContext | str | None,
) -> tuple[PageValueSelector, ...]:
    return _requirements_for_lang(contract.required_page_values, lang)


def required_assets_for_lang(
    contract: PageContract,
    lang: ContractContext | str | None,
) -> tuple[str, ...]:
    return _requirements_for_lang(contract.required_assets, lang)


def describe_page_value_selector(selector: PageValueSelector) -> str:
    qualifiers: list[str] = []
    if selector.pages:
        qualifiers.append(f"pages={','.join(selector.pages)}")
    if selector.usage_type:
        qualifiers.append(f"usage_type={selector.usage_type}")
    if selector.placement_key:
        qualifiers.append(f"placement_key={selector.placement_key}")
    if selector.value_role:
        qualifiers.append(f"value_role={selector.value_role}")
    if selector.variant_key:
        qualifiers.append(f"variant_key={selector.variant_key}")
    if selector.line_order:
        qualifiers.append(f"line_order={selector.line_order}")
    if not qualifiers:
        return selector.row_key
    return f"{selector.row_key}[{', '.join(qualifiers)}]"


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
