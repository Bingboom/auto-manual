"""Renderer-neutral FCC composition and four renderer projections."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import re
from typing import Any

from tools.component_specs.model import (
    ComponentAsset,
    ComponentSlot,
    ComponentSpec,
    ComponentSpecError,
)
from tools.component_specs.registry import load_component_registry, require_valid_component_spec
from tools.component_specs.theme import load_manual_theme, require_component_theme_roles


COMPONENT_ID = "HB-SPECIAL-FCC"
VARIANT = "two-column"
DEFAULT_MARK_ASSET_REF = "mark/fcc"

_LABEL_RE = re.compile(
    r"^(NOTE|REMARQUE|NOTA|MODIFICATION|MODIFICACIÓN|MODIFICACION)\s*:",
    re.IGNORECASE,
)
_OPENING_SPLIT_RE = re.compile(
    r"(?:\*\*)?(?:NOTE|REMARQUE|NOTA)\s*:(?:\*\*)?",
    re.IGNORECASE,
)


def _paragraph_block(text: str) -> dict[str, Any]:
    candidate = str(text).replace("**", "").strip()
    if not candidate:
        raise ComponentSpecError(f"{COMPONENT_ID}: paragraph text must be non-empty")
    match = _LABEL_RE.match(candidate)
    if match is None:
        return {"kind": "paragraph", "label": "", "text": candidate}
    return {
        "kind": "paragraph",
        "label": candidate[: match.end()].strip(),
        "text": candidate[match.end() :].strip(),
    }


def _list_block(items: Sequence[str]) -> dict[str, Any]:
    normalized = [str(item).strip() for item in items if str(item).strip()]
    if not normalized:
        raise ComponentSpecError(f"{COMPONENT_ID}: list block must contain an item")
    return {"kind": "list", "items": normalized}


def fcc_blocks_from_text(text: str) -> list[dict[str, Any]]:
    """Classify ordered FCC paragraphs and consecutive bullet items."""
    blocks: list[dict[str, Any]] = []
    pending_items: list[str] = []

    def flush_items() -> None:
        if pending_items:
            blocks.append(_list_block(pending_items))
            pending_items.clear()

    for raw_line in str(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("•", "·")):
            pending_items.append(line[1:].strip())
            continue
        if line.startswith("- "):
            pending_items.append(line[2:].strip())
            continue
        flush_items()
        blocks.append(_paragraph_block(line))
    flush_items()
    return blocks


def _validate_blocks(blocks: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, block in enumerate(blocks, start=1):
        if not isinstance(block, Mapping):
            raise ComponentSpecError(
                f"{COMPONENT_ID}: body block {index} must be a mapping"
            )
        kind = str(block.get("kind") or "")
        if kind == "paragraph":
            if set(block) != {"kind", "label", "text"}:
                raise ComponentSpecError(
                    f"{COMPONENT_ID}: paragraph block {index} has an invalid shape"
                )
            label = str(block.get("label") or "").strip()
            text = str(block.get("text") or "").strip()
            if not label and not text:
                raise ComponentSpecError(
                    f"{COMPONENT_ID}: paragraph block {index} is empty"
                )
            normalized.append({"kind": kind, "label": label, "text": text})
        elif kind == "list":
            if set(block) != {"kind", "items"}:
                raise ComponentSpecError(
                    f"{COMPONENT_ID}: list block {index} has an invalid shape"
                )
            normalized.append(_list_block(block.get("items") or []))
        else:
            raise ComponentSpecError(
                f"{COMPONENT_ID}: body block {index} has unknown kind {kind!r}"
            )
    return normalized


def fcc_component_spec(
    *,
    accessibility_label: str,
    opening_copy: Sequence[str],
    left_blocks: Sequence[Mapping[str, Any]],
    right_blocks: Sequence[Mapping[str, Any]],
    source_ref: str,
    language: str,
    mark_asset_ref: str = DEFAULT_MARK_ASSET_REF,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    active_registry = registry or load_component_registry()
    active_theme = theme or load_manual_theme(component_registry=active_registry)
    label = str(accessibility_label).strip()
    if not label:
        raise ComponentSpecError(f"{COMPONENT_ID}: accessibility label is required")
    opening = [str(line).strip() for line in opening_copy if str(line).strip()]
    left = _validate_blocks(left_blocks)
    right = _validate_blocks(right_blocks)
    ordered_blocks = [*left, *right]
    spec = ComponentSpec(
        component_id=COMPONENT_ID,
        variant=VARIANT,
        source_ref=str(source_ref),
        language=str(language or "und"),
        slots=(
            ComponentSlot("accessibility_label", "inline_text", label),
            ComponentSlot("opening_copy", "line_items", opening),
            ComponentSlot("body_blocks", "ordered_blocks", ordered_blocks),
            ComponentSlot("column_break", "block_index", len(left)),
        ),
        assets=(
            ComponentAsset(
                role="compliance_mark",
                asset_ref=str(mark_asset_ref),
                locale_policy="shared",
            ),
        ),
        token_roles=tuple(active_registry["components"][COMPONENT_ID]["token_roles"]),
        metadata=dict(metadata or {}),
    )
    require_valid_component_spec(spec, active_registry)
    return require_component_theme_roles(spec, active_theme)


def _split_opening(text: str) -> tuple[list[str], str]:
    candidate = str(text).strip()
    match = _OPENING_SPLIT_RE.search(candidate)
    if match is None:
        lines = [line.strip() for line in candidate.splitlines() if line.strip()]
        if not lines:
            return [], ""
        return lines, ""
    opening = [
        line.strip()
        for line in candidate[: match.start()].splitlines()
        if line.strip()
    ]
    return opening, candidate[match.start() :].strip()


def fcc_spec_from_payload(
    payload: Mapping[str, Any],
    *,
    source_ref: str,
    language: str,
    accessibility_label: str = "FCC",
    mark_asset_ref: str = DEFAULT_MARK_ASSET_REF,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    if str(payload.get("kind") or "") != "fcc":
        raise ComponentSpecError(f"{COMPONENT_ID}: payload kind must be 'fcc'")
    texts = [str(value) for value in payload.get("texts") or []]
    left_text, right_text = (texts + ["", ""])[:2]
    opening, left_body = _split_opening(left_text)
    return fcc_component_spec(
        accessibility_label=accessibility_label,
        opening_copy=opening,
        left_blocks=fcc_blocks_from_text(left_body),
        right_blocks=fcc_blocks_from_text(right_text),
        source_ref=source_ref,
        language=language,
        mark_asset_ref=mark_asset_ref,
        registry=registry,
        theme=theme,
    )


def fcc_semantic_projection(spec: ComponentSpec) -> dict[str, Any]:
    """Return validated FCC semantics without any renderer geometry."""
    opening = spec.slot("opening_copy").content
    blocks = spec.slot("body_blocks").content
    column_break = spec.slot("column_break").content
    if not isinstance(opening, list) or not all(isinstance(item, str) for item in opening):
        raise ComponentSpecError(f"{COMPONENT_ID}: opening_copy must contain strings")
    if not isinstance(blocks, list):
        raise ComponentSpecError(f"{COMPONENT_ID}: body_blocks must be a list")
    normalized_blocks = _validate_blocks(blocks)
    if isinstance(column_break, bool) or not isinstance(column_break, int):
        raise ComponentSpecError(f"{COMPONENT_ID}: column_break must be an integer")
    if column_break < 0 or column_break > len(normalized_blocks):
        raise ComponentSpecError(
            f"{COMPONENT_ID}: column_break {column_break} is outside body block range"
        )
    return {
        "accessibility_label": str(spec.slot("accessibility_label").content),
        "opening_copy": list(opening),
        "left_blocks": deepcopy(normalized_blocks[:column_break]),
        "right_blocks": deepcopy(normalized_blocks[column_break:]),
        "mark_asset_ref": spec.assets[0].asset_ref,
    }


__all__ = [
    "COMPONENT_ID",
    "DEFAULT_MARK_ASSET_REF",
    "VARIANT",
    "fcc_blocks_from_text",
    "fcc_component_spec",
    "fcc_semantic_projection",
    "fcc_spec_from_payload",
]
