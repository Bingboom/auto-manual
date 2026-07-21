"""Target-scoped governed assets consumed only by native IDML components.

Most bundle assets are declared directly in RST and are therefore discovered
by the ordinary asset rewriter.  A native IDML component can need additional
art that has no visible RST node.  Keep those exceptional dependencies here so
bundle finalization and component rendering share one semantic asset key
instead of duplicating a build-tree path.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


APP_PAIRING_PANEL_ASSET_URI = (
    "asset:controls/je1000f_us/network_pairing_panel"
)


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


def is_je1000f_us_app_reference_page(
    page_path: Path,
    *,
    model: str | None,
    region: str | None,
    language: str | None,
) -> bool:
    """Return whether a page owns the approved JE-1000F/US App reproduction.

    The approved physical composition is language-neutral: English, French,
    and Spanish use the same editable artwork and frame geometry.  Localized
    copy remains in independent top-layer text frames, so extending the
    contract to the sibling languages does not bake translated text into the
    illustration.
    """

    language_key = (
        (language or "").strip().casefold().replace("_", "-").split("-", 1)[0]
    )
    return (
        (model or "").strip().casefold() == "je-1000f"
        and (region or "").strip().casefold() == "us"
        and language_key in {"en", "fr", "es"}
        and re.fullmatch(
            r"(?:p\d+_)?12_app_setup_placeholder",
            page_path.stem.casefold(),
        ) is not None
    )


def is_je1000f_us_app_reference_plan_page(
    page_plan: dict | None,
    stem: str,
) -> bool:
    """Resolve the exact App page from validated approved-plan metadata."""

    if (page_plan or {}).get("plan_source") != "approved-reference":
        return False
    pages = (page_plan or {}).get("pages")
    if not isinstance(pages, list):
        return False
    page_entry = next((
        entry
        for entry in pages
        if isinstance(entry, dict)
        and Path(str(entry.get("source_path") or "")).stem.casefold()
        == stem.casefold()
    ), None)
    approved_contract = (page_plan or {}).get("approved_contract")
    if page_entry is None or not isinstance(approved_contract, dict):
        return False
    target = approved_contract.get("target")
    if not isinstance(target, dict):
        return False
    return is_je1000f_us_app_reference_page(
        Path(stem),
        model=target.get("model") if isinstance(target.get("model"), str) else None,
        region=target.get("region") if isinstance(target.get("region"), str) else None,
        language=(
            page_entry.get("language")
            if isinstance(page_entry.get("language"), str)
            else None
        ),
    )


def requirements_for_page(
    page_path: Path,
    *,
    model: str,
    region: str,
    language: str | None,
) -> tuple[IdmlAssetRequirement, ...]:
    """Return native-IDML dependencies for one finalized bundle page.

    The pairing panel is part of the approved JE-1000F US physical page for
    English, French, and Spanish.  Other targets and languages stay on their
    ordinary renderer path and must not pull this product-specific asset into
    unrelated bundles.
    """

    if is_je1000f_us_app_reference_page(
        page_path,
        model=model,
        region=region,
        language=language,
    ):
        return (_APP_PAIRING_PANEL,)
    return ()


__all__ = (
    "APP_PAIRING_PANEL_ASSET_URI",
    "IdmlAssetRequirement",
    "is_je1000f_us_app_reference_page",
    "is_je1000f_us_app_reference_plan_page",
    "is_je1000f_us_en_app_reference_page",
    "is_je1000f_us_en_app_reference_plan_page",
    "requirements_for_page",
)

# Compatibility names for callers in downstream review tooling.  Keep these
# aliases while the public helper names migrate; they intentionally resolve to
# the language-neutral contract above rather than reintroducing EN-only scope.
is_je1000f_us_en_app_reference_page = is_je1000f_us_app_reference_page
is_je1000f_us_en_app_reference_plan_page = is_je1000f_us_app_reference_plan_page
