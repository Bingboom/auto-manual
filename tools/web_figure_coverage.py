"""Audit approved and fallback artwork through one Web figure-slot contract."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Tag

from tools.manual_ir import ManualIR


WEB_FIGURE_COVERAGE_SCHEMA = "web-figure-coverage/v1"
WEB_FIGURE_STATUSES = (
    "finished-panel",
    "approved-composite",
    "editable-fallback",
    "missing",
)
_FIGURE_SECTIONS = ("overview", "operation", "charging")
_FINAL_FIGURE_STATUSES = frozenset({"finished-panel", "approved-composite"})
_STAGED_DIGEST_SUFFIX_RE = re.compile(r"_[0-9a-f]{12}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _matches_source(page_id: str, patterns: Iterable[str]) -> bool:
    stem = Path(page_id).stem.casefold()
    return any(fnmatch.fnmatch(stem, str(pattern).casefold()) for pattern in patterns)


def _charging_source_patterns(contract: dict[str, Any]) -> tuple[str, ...]:
    patterns: list[str] = []
    reference = contract.get("reference_figures", {})
    for figure in reference.get("figures", []):
        if not isinstance(figure, dict):
            continue
        identifier = str(figure.get("id") or "").casefold()
        image_key = str(figure.get("image_key") or "").casefold()
        if identifier.startswith("charging-") or image_key.startswith("charging/"):
            patterns.extend(str(value) for value in figure.get("source_patterns", []))
    return tuple(dict.fromkeys(patterns))


def _figure_section(
    page_id: str,
    contract: dict[str, Any],
    page_slot: str = "",
) -> str | None:
    section_patterns = (
        (
            "overview",
            contract.get("product_overview", {}).get("source_patterns", []),
        ),
        ("operation", contract.get("operations", {}).get("source_patterns", [])),
        ("charging", _charging_source_patterns(contract)),
    )
    for section, patterns in section_patterns:
        if _matches_source(page_id, patterns):
            return section
    normalized_slot = page_slot.replace("\\", "/").casefold()
    slot_markers = (
        ("overview", "product_overview"),
        ("operation", "operation"),
        ("charging", "charging"),
    )
    for section, marker in slot_markers:
        if marker in normalized_slot:
            return section
    return None


def _classes(tag: Tag) -> set[str]:
    raw = tag.get("class", [])
    if isinstance(raw, str):
        return set(raw.split())
    return {str(value) for value in raw}


def _semantic_figure_class(figure: Tag) -> str | None:
    candidates = sorted(
        value
        for value in _classes(figure)
        if value.startswith("hb-")
        and (value.endswith("-composition") or value.endswith("-figure"))
    )
    return candidates[0] if candidates else None


def _source_image_name(src: str) -> str:
    name = Path(unquote(urlparse(src).path)).name or "unnamed-image"
    stem = _STAGED_DIGEST_SUFFIX_RE.sub("", Path(name).stem)
    return f"{stem}{Path(name).suffix.casefold()}"


def _unique_slot_id(base: str, observed: dict[str, int]) -> str:
    count = observed.get(base, 0) + 1
    observed[base] = count
    return base if count == 1 else f"{base}#{count}"


def _finished_asset(
    image: Tag,
    provenance: dict[str, Any] | None,
) -> tuple[dict[str, str], list[str]]:
    path = str(image.get("data-web-finished-panel-path") or "").strip()
    sha256 = str(image.get("data-web-finished-panel-sha256") or "").strip()
    entries = provenance.get("illustrations", []) if isinstance(provenance, dict) else []
    matches = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and str(entry.get("path") or "") == path
        and str(entry.get("sha256") or "") == sha256
    ]
    if len(matches) != 1:
        raise ValueError(
            "finished Web panel is missing unambiguous illustration provenance: "
            f"path={path!r} sha256={sha256!r}"
        )
    entry = matches[0]
    return (
        {"path": path, "sha256": sha256},
        [str(value) for value in entry.get("replaces", [])],
    )


def _composite_asset(
    figure: Tag,
    composites: list[dict[str, Any]],
) -> dict[str, str]:
    asset_key = str(figure.get("data-web-composite-asset-key") or "").strip()
    locale = str(figure.get("data-web-composite-locale") or "").strip()
    sha256 = str(figure.get("data-web-composite-sha256") or "").strip()
    matches = [
        entry
        for entry in composites
        if isinstance(entry, dict)
        and str(entry.get("asset_key") or "") == asset_key
        and str(entry.get("locale") or "") == locale
        and str(entry.get("content_sha256") or "") == sha256
    ]
    if len(matches) != 1:
        raise ValueError(
            "approved Web composite is missing unambiguous manifest provenance: "
            f"asset_key={asset_key!r} locale={locale!r} sha256={sha256!r}"
        )
    entry = matches[0]
    return {
        "asset_key": asset_key,
        "locale": locale,
        "path": str(entry.get("path") or ""),
        "sha256": sha256,
    }


def _summary(slots: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = {
        status: sum(slot["status"] == status for slot in slots)
        for status in WEB_FIGURE_STATUSES
    }
    by_section: dict[str, Any] = {}
    for section in _FIGURE_SECTIONS:
        section_slots = [slot for slot in slots if slot["section"] == section]
        if not section_slots:
            continue
        by_section[section] = {
            "total": len(section_slots),
            "by_status": {
                status: sum(slot["status"] == status for slot in section_slots)
                for status in WEB_FIGURE_STATUSES
            },
        }
    return {"total": len(slots), "by_status": by_status, "by_section": by_section}


def validate_web_figure_coverage(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != WEB_FIGURE_COVERAGE_SCHEMA:
        raise ValueError("unsupported Web figure coverage schema")
    if not isinstance(payload.get("model"), str) or not isinstance(
        payload.get("region"), str
    ):
        raise ValueError("Web figure coverage target must contain model and region")
    slots = payload.get("slots")
    if not isinstance(slots, list):
        raise ValueError("Web figure coverage slots must be a list")
    identities: set[tuple[str, str]] = set()
    for index, slot in enumerate(slots):
        if not isinstance(slot, dict):
            raise ValueError(f"Web figure coverage slot {index} must be an object")
        page_id = slot.get("page_id")
        slot_id = slot.get("slot_id")
        if not isinstance(page_id, str) or not page_id or not isinstance(slot_id, str) or not slot_id:
            raise ValueError(f"Web figure coverage slot {index} has an invalid identity")
        identity = (page_id, slot_id)
        if identity in identities:
            raise ValueError(f"duplicate Web figure coverage slot: {page_id}/{slot_id}")
        identities.add(identity)
        if slot.get("section") not in _FIGURE_SECTIONS:
            raise ValueError(f"Web figure coverage slot {index} has an invalid section")
        status = slot.get("status")
        if status not in WEB_FIGURE_STATUSES:
            raise ValueError(f"Web figure coverage slot {index} has an invalid status")
        if status in {"finished-panel", "approved-composite"}:
            asset = slot.get("asset")
            if (
                not isinstance(asset, dict)
                or not isinstance(asset.get("path"), str)
                or not asset["path"]
                or not isinstance(asset.get("sha256"), str)
                or not _SHA256_RE.fullmatch(asset["sha256"])
            ):
                raise ValueError(
                    f"Web figure coverage slot {index} has invalid approved asset evidence"
                )
    summary = payload.get("summary")
    expected = _summary(slots)
    if not isinstance(summary, dict) or summary.get("total") != expected["total"]:
        raise ValueError("Web figure coverage summary total does not match slots")
    if summary.get("by_status") != expected["by_status"]:
        raise ValueError("Web figure coverage status summary does not match slots")
    if summary.get("by_section") != expected["by_section"]:
        raise ValueError("Web figure coverage section summary does not match slots")


def _target_requirement_matches(
    requirement: dict[str, Any],
    *,
    model: str,
    region: str,
) -> bool:
    target = requirement.get("target")
    if not isinstance(target, dict):
        raise ValueError("Web figure coverage requirement target must be an object")
    required_model = str(target.get("model") or "").strip()
    required_region = str(target.get("region") or "").strip()
    if not required_model or not required_region:
        raise ValueError("Web figure coverage requirement target is incomplete")
    return (
        required_model.casefold() == model.casefold()
        and required_region.casefold() == region.casefold()
    )


def enforce_required_web_figure_coverage(
    ir: ManualIR,
    coverage: dict[str, Any],
) -> None:
    """Fail when a contract-governed target retains required figure debt."""

    if (
        str(coverage.get("model") or "").casefold() != ir.model.casefold()
        or str(coverage.get("region") or "").casefold() != ir.region.casefold()
    ):
        raise ValueError("Web figure coverage target does not match document target")
    contract = ir.metadata.get("web_contract")
    if not isinstance(contract, dict):
        raise ValueError("Web figure coverage requirements need a presentation contract")
    policy = contract.get("figure_coverage") or {}
    if not isinstance(policy, dict):
        raise ValueError("Web figure coverage policy must be an object")
    requirements = policy.get("requirements") or []
    if not isinstance(requirements, list):
        raise ValueError("Web figure coverage requirements must be a list")

    matching: list[dict[str, Any]] = []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            raise ValueError("Web figure coverage requirement must be an object")
        if _target_requirement_matches(
            requirement,
            model=ir.model,
            region=ir.region,
        ):
            matching.append(requirement)
    if len(matching) > 1:
        raise ValueError(
            f"multiple Web figure coverage requirements match {ir.model}/{ir.region}"
        )
    if not matching:
        return

    requirement = matching[0]
    locales = requirement.get("locales")
    required_slots = requirement.get("required_slots")
    allowed_statuses = requirement.get("allowed_statuses")
    if not isinstance(locales, list) or not locales:
        raise ValueError("Web figure coverage requirement locales must be non-empty")
    if not isinstance(required_slots, list) or not required_slots:
        raise ValueError("Web figure coverage required_slots must be non-empty")
    if not isinstance(allowed_statuses, list) or not allowed_statuses:
        raise ValueError("Web figure coverage allowed_statuses must be non-empty")

    normalized_locales = [str(value).strip().casefold() for value in locales]
    normalized_slots = [str(value).strip() for value in required_slots]
    normalized_statuses = {str(value).strip() for value in allowed_statuses}
    if (
        any(not value for value in normalized_locales)
        or len(set(normalized_locales)) != len(normalized_locales)
    ):
        raise ValueError("Web figure coverage requirement locales are invalid or duplicate")
    if (
        any(not value for value in normalized_slots)
        or len(set(normalized_slots)) != len(normalized_slots)
    ):
        raise ValueError("Web figure coverage required_slots are invalid or duplicate")
    if normalized_statuses != _FINAL_FIGURE_STATUSES:
        raise ValueError(
            "Web figure coverage allowed_statuses must contain only finished artwork"
        )

    raw_debt = requirement.get("known_debt", [])
    if not isinstance(raw_debt, list):
        raise ValueError("Web figure coverage known_debt must be a list")
    debt: dict[tuple[str, str], str] = {}
    for index, entry in enumerate(raw_debt):
        if not isinstance(entry, dict):
            raise ValueError(f"Web figure coverage known_debt {index} must be an object")
        locale = str(entry.get("locale") or "").strip().casefold()
        slot_id = str(entry.get("slot_id") or "").strip()
        status = str(entry.get("status") or "").strip()
        identity = (locale, slot_id)
        if (
            not locale
            or not slot_id
            or status not in {"editable-fallback", "missing"}
        ):
            raise ValueError(f"Web figure coverage known_debt {index} is invalid")
        if locale not in normalized_locales or slot_id not in normalized_slots:
            raise ValueError(
                f"Web figure coverage known_debt {locale}/{slot_id} is outside policy"
            )
        if identity in debt:
            raise ValueError(
                f"duplicate Web figure coverage debt entry: {locale}/{slot_id}"
            )
        debt[identity] = status

    declared_languages = ir.metadata.get("declared_languages")
    if isinstance(declared_languages, list) and declared_languages:
        active_languages = {
            str(value).strip().casefold()
            for value in declared_languages
            if str(value).strip()
        }
        normalized_locales = [
            locale for locale in normalized_locales if locale in active_languages
        ]
    elif getattr(ir, "language", ""):
        normalized_locales = [
            locale
            for locale in normalized_locales
            if locale == ir.language.strip().casefold()
        ]
    if not normalized_locales:
        return

    failures: list[str] = []
    stale_debt: list[str] = []
    slots = coverage.get("slots")
    if not isinstance(slots, list):
        raise ValueError("Web figure coverage slots must be a list")
    for locale in normalized_locales:
        for required_slot in normalized_slots:
            matches = [
                slot
                for slot in slots
                if isinstance(slot, dict)
                and str(slot.get("locale") or "").casefold() == locale
                and (
                    str(slot.get("slot_id") or "") == required_slot
                    or str(slot.get("slot_id") or "").startswith(
                        f"{required_slot}#"
                    )
                )
            ]
            if len(matches) != 1:
                failures.append(f"{locale}/{required_slot}=count:{len(matches)}")
                continue
            status = str(matches[0].get("status") or "")
            registered = debt.get((locale, required_slot))
            if status in normalized_statuses:
                if registered is not None:
                    stale_debt.append(
                        f"{locale}/{required_slot}=registered:{registered},current:{status}"
                    )
                continue
            if registered != status:
                suffix = (
                    f" (registered:{registered})"
                    if registered is not None
                    else " (unregistered debt)"
                )
                failures.append(
                    f"{locale}/{required_slot}={status or 'missing'}{suffix}"
                )
    if stale_debt:
        raise ValueError(
            f"stale debt baseline for {ir.model}/{ir.region}: "
            + ", ".join(stale_debt)
        )
    if failures:
        raise ValueError(
            f"required Web figure coverage failed for {ir.model}/{ir.region}: "
            + ", ".join(failures)
        )


def build_web_figure_coverage(
    ir: ManualIR,
    rendered_fragments: Sequence[str],
) -> dict[str, Any]:
    """Classify each rendered overview/operation/charging visual slot."""
    if len(ir.pages) != len(rendered_fragments):
        raise ValueError("Web figure coverage requires one rendered fragment per IR page")
    contract = ir.metadata.get("web_contract")
    composites = ir.metadata.get("composites")
    provenance = ir.metadata.get("illustration_provenance")
    page_slots = ir.metadata.get("page_slots", {})
    if not isinstance(contract, dict) or not isinstance(composites, list):
        raise ValueError("Web figure coverage requires document presentation bindings")
    if not isinstance(page_slots, dict):
        raise ValueError("Web figure coverage page slots must be a mapping")

    slots: list[dict[str, Any]] = []
    for page, fragment in zip(ir.pages, rendered_fragments, strict=True):
        locale = str(
            getattr(page, "language", None)
            or getattr(ir, "language", "")
            or "und"
        )
        section = _figure_section(
            page.page_id,
            contract,
            str(page_slots.get(page.page_id) or ""),
        )
        if section is None:
            continue
        soup = BeautifulSoup(fragment, "html.parser")
        consumed_images: set[int] = set()
        observed_ids: dict[str, int] = {}

        for figure in soup.select("figure[data-web-replace-key]"):
            if not isinstance(figure, Tag):
                continue
            consumed_images.update(id(image) for image in figure.find_all("img"))
            replace_key = str(figure.get("data-web-replace-key") or "").strip()
            slot: dict[str, Any] = {
                "page_id": page.page_id,
                "locale": locale,
                "section": section,
                "slot_id": _unique_slot_id(replace_key, observed_ids),
                "status": "editable-fallback",
            }
            if "hb-has-composite-art" in _classes(figure):
                slot["status"] = "approved-composite"
                slot["asset"] = _composite_asset(figure, composites)
            slots.append(slot)

        for figure in soup.find_all("figure"):
            if not isinstance(figure, Tag) or figure.has_attr("data-web-replace-key"):
                continue
            figure_class = _semantic_figure_class(figure)
            images = [image for image in figure.find_all("img") if isinstance(image, Tag)]
            if figure_class is None or not images:
                continue
            consumed_images.update(id(image) for image in images)
            source_names = [
                _source_image_name(str(image.get("src") or "")) for image in images
            ]
            slots.append(
                {
                    "page_id": page.page_id,
                    "locale": locale,
                    "section": section,
                    "slot_id": _unique_slot_id(
                        f"semantic.{figure_class.removeprefix('hb-')}", observed_ids
                    ),
                    "status": "editable-fallback",
                    "source_images": source_names,
                }
            )

        for image in soup.find_all("img"):
            if not isinstance(image, Tag) or id(image) in consumed_images:
                continue
            source_name = _source_image_name(str(image.get("src") or ""))
            if "manual-finished-illustration" in _classes(image):
                asset, replaces = _finished_asset(image, provenance)
                slot_id = f"finished-panel.{Path(asset['path']).stem}"
                slots.append(
                    {
                        "page_id": page.page_id,
                        "locale": locale,
                        "section": section,
                        "slot_id": _unique_slot_id(slot_id, observed_ids),
                        "status": "finished-panel",
                        "source_image": source_name,
                        "replaces": replaces,
                        "asset": asset,
                    }
                )
                continue
            slot_id = f"source-image.{Path(source_name).stem}"
            slots.append(
                {
                    "page_id": page.page_id,
                    "locale": locale,
                    "section": section,
                    "slot_id": _unique_slot_id(slot_id, observed_ids),
                    "status": "missing",
                    "source_image": source_name,
                }
            )

    payload = {
        "schema_version": WEB_FIGURE_COVERAGE_SCHEMA,
        "model": ir.model,
        "region": ir.region,
        "slots": slots,
        "summary": _summary(slots),
    }
    validate_web_figure_coverage(payload)
    return payload


def attach_web_figure_coverage(
    ir: ManualIR,
    rendered_fragments: Sequence[str],
) -> ManualIR:
    """Return the same content IR with a validated, read-only coverage report."""
    coverage = build_web_figure_coverage(ir, rendered_fragments)
    enforce_required_web_figure_coverage(ir, coverage)
    return replace(ir, metadata={**ir.metadata, "web_figure_coverage": coverage})


__all__ = (
    "WEB_FIGURE_COVERAGE_SCHEMA",
    "WEB_FIGURE_STATUSES",
    "attach_web_figure_coverage",
    "build_web_figure_coverage",
    "enforce_required_web_figure_coverage",
    "validate_web_figure_coverage",
)
