"""Approved-contract ownership for native IDML component assets.

Most bundle assets are visible in RST and are discovered by the ordinary
asset rewriter. Native IDML components can require additional art with no RST
node. The approved reference contract therefore owns both the source pages
that may instantiate a component and the hidden assets that renderer needs.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.utils.path_utils import PathSegments, Paths


APP_ADD_DEVICE_COMPONENT = "app_add_device"
APP_PAIRING_PANEL_ASSET_URI = "asset:controls/je1000f_us/network_pairing_panel"
APP_ADD_DEVICE_ICON_ASSET_URI = "asset:app/add_device_plus"

_APPROVED_PLAN_SCHEMA = "approved-reference-layout-plan/v1"
_REGISTRY_SCHEMA = "approved-reference-layout-registry/v1"


class IdmlAssetContractError(ValueError):
    """A registered IDML component-ownership contract is unusable."""


@dataclass(frozen=True)
class IdmlAssetRequirement:
    """One registry asset required by a native IDML page composition."""

    asset_uri: str
    format_name: str
    consumer: str = "idml-renderer"
    reference_kind: str = "idml-component-contract"


_APP_PAIRING_PANEL = IdmlAssetRequirement(
    asset_uri=APP_PAIRING_PANEL_ASSET_URI,
    format_name="pdf",
)
_APP_ADD_DEVICE_ICON = IdmlAssetRequirement(
    asset_uri=APP_ADD_DEVICE_ICON_ASSET_URI,
    format_name="png",
)


def _language_code(value: object) -> str:
    normalized = str(value or "").strip().casefold().replace("_", "-")
    return normalized.split("-", 1)[0]


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise IdmlAssetContractError(f"{label} does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise IdmlAssetContractError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise IdmlAssetContractError(f"{label} must contain a JSON object: {path}")
    return payload


def load_registered_approved_contract(
    *,
    root: Path,
    model: str,
    region: str,
    languages: tuple[str, ...],
) -> dict[str, Any] | None:
    """Load one exact registered target contract before Manual IR exists.

    Bundle finalization runs before Manual IR/reference-plan normalization. It
    may inspect only the exact registry binding and approval state here; the
    full source/hash/composition validation still runs later through
    ``reference_layout_plan`` before production IDML is emitted.
    """

    root = root.resolve()
    registry_path = (
        Paths(root=root).renderer_contracts_dir
        / PathSegments.REFERENCE_LAYOUT_REGISTRY_JSON
    )
    if not registry_path.is_file():
        return None
    registry = _read_json(registry_path, "approved reference layout registry")
    if registry.get("schema_version") != _REGISTRY_SCHEMA:
        raise IdmlAssetContractError(
            f"registry schema_version must be {_REGISTRY_SCHEMA}"
        )
    entries = registry.get("plans")
    if not isinstance(entries, list):
        raise IdmlAssetContractError("registry plans must be a list")
    target = {
        "model": model,
        "region": region,
        "languages": list(languages),
    }
    matches = [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("target") == target
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise IdmlAssetContractError(
            "approved reference layout registry has duplicate exact target bindings"
        )
    raw_path = matches[0].get("path")
    relative = Path(str(raw_path or ""))
    if not raw_path or relative.is_absolute() or ".." in relative.parts:
        raise IdmlAssetContractError(
            "approved reference layout registry path must be repository-relative"
        )
    contract_path = (root / relative).resolve()
    try:
        contract_path.relative_to(root)
    except ValueError as exc:
        raise IdmlAssetContractError(
            "approved reference layout registry path escapes the repository"
        ) from exc
    contract = _read_json(contract_path, "approved reference layout plan")
    if contract.get("schema_version") != _APPROVED_PLAN_SCHEMA:
        raise IdmlAssetContractError(
            f"approved plan schema_version must be {_APPROVED_PLAN_SCHEMA}"
        )
    approval = contract.get("approval")
    if not isinstance(approval, dict) or approval.get("status") != "approved":
        raise IdmlAssetContractError("registered reference layout plan is not approved")
    if contract.get("target") != target:
        raise IdmlAssetContractError(
            "registered reference layout plan target does not match its registry binding"
        )
    return contract


def _component_contract(
    approved_contract: dict[str, Any] | None,
    component: str,
) -> dict[str, Any] | None:
    if not isinstance(approved_contract, dict):
        return None
    if approved_contract.get("schema_version") != _APPROVED_PLAN_SCHEMA:
        return None
    approval = approved_contract.get("approval")
    if not isinstance(approval, dict) or approval.get("status") != "approved":
        return None
    idml_contract = approved_contract.get("idml_contract")
    editable = (
        idml_contract.get("editable_components")
        if isinstance(idml_contract, dict)
        else None
    )
    value = editable.get(component) if isinstance(editable, dict) else None
    return value if isinstance(value, dict) else None


def component_owns_page(
    page_path: Path,
    *,
    language: str | None,
    component: str,
    approved_contract: dict[str, Any] | None,
) -> bool:
    """Return whether an approved component explicitly owns one source page."""

    component_contract = _component_contract(approved_contract, component)
    owners = (
        component_contract.get("page_owners")
        if isinstance(component_contract, dict)
        else None
    )
    if (
        not isinstance(owners, list)
        or not owners
        or any(not isinstance(owner, str) or not owner.strip() for owner in owners)
    ):
        return False
    if page_path.is_absolute() or ".." in page_path.parts:
        return False
    source_ref = page_path.as_posix().removeprefix("./")
    if source_ref not in owners:
        return False
    pages = approved_contract.get("pages") if isinstance(approved_contract, dict) else None
    if not isinstance(pages, list):
        return False
    matches = [
        page
        for page in pages
        if isinstance(page, dict) and page.get("source_ref") == source_ref
    ]
    if len(matches) != 1:
        return False
    page_language = matches[0].get("language")
    language_code = _language_code(language)
    if not language_code or _language_code(page_language) != language_code:
        return False
    target = approved_contract.get("target")
    target_languages = target.get("languages") if isinstance(target, dict) else None
    return (
        isinstance(target_languages, list)
        and language_code in {_language_code(value) for value in target_languages}
    )


def plan_page_owns_component(
    page_plan: dict[str, Any] | None,
    stem: str,
    *,
    component: str,
) -> bool:
    """Resolve component ownership from normalized approved-plan metadata."""

    if (page_plan or {}).get("plan_source") != "approved-reference":
        return False
    approved_contract = (page_plan or {}).get("approved_contract")
    pages = (page_plan or {}).get("pages")
    if not isinstance(approved_contract, dict) or not isinstance(pages, list):
        return False
    matches = [
        page
        for page in pages
        if isinstance(page, dict)
        and Path(str(page.get("source_path") or page.get("source_ref") or ""))
        .stem.casefold()
        == stem.casefold()
    ]
    if len(matches) != 1:
        return False
    page = matches[0]
    source_ref = page.get("source_ref") or page.get("source_path")
    if not isinstance(source_ref, str) or not source_ref.strip():
        return False
    return component_owns_page(
        Path(source_ref),
        language=page.get("language") if isinstance(page.get("language"), str) else None,
        component=component,
        approved_contract=approved_contract,
    )


def requirements_for_page(
    page_path: Path,
    *,
    language: str | None,
    approved_contract: dict[str, Any] | None,
) -> tuple[IdmlAssetRequirement, ...]:
    """Return hidden native-IDML dependencies for one contracted source page."""

    if component_owns_page(
        page_path,
        language=language,
        component=APP_ADD_DEVICE_COMPONENT,
        approved_contract=approved_contract,
    ):
        return (_APP_PAIRING_PANEL, _APP_ADD_DEVICE_ICON)
    return ()


__all__ = (
    "APP_ADD_DEVICE_COMPONENT",
    "APP_PAIRING_PANEL_ASSET_URI",
    "APP_ADD_DEVICE_ICON_ASSET_URI",
    "IdmlAssetContractError",
    "IdmlAssetRequirement",
    "component_owns_page",
    "load_registered_approved_contract",
    "plan_page_owns_component",
    "requirements_for_page",
)
