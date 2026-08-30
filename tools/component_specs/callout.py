"""Callout source adapters for ComponentSpec v1."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import re
from typing import Any, Mapping, Sequence

from tools.component_specs.model import ComponentSlot, ComponentSpec, ComponentSpecError
from tools.component_specs.registry import load_component_registry, require_valid_component_spec


COMPONENT_ID = "HB-CALLOUT-STRIP"
CALLOUT_VARIANTS = frozenset({"warning", "danger", "caution", "note", "tip"})
_VARIANT_ALIASES = {"notice": "note", "tips": "tip"}
_VARIANTS_BY_LABEL = {
    "WARNING": "warning",
    "DANGER": "danger",
    "CAUTION": "caution",
    "NOTE": "note",
    # The plural is what the shipped books actually print for a multi-item
    # notes block, and an unrecognised label is not a warning — it silently
    # degrades. replace_notice_tables leaves the table alone, so LaTeX emits
    # \sphinxstylestrong{NOTES} instead of \HBCautionBlock and Word emits loose
    # paragraphs: the box is lost in BOTH renderers with nothing in the log.
    # `tip` already carried TIPS / CONSEILS / CONSEJOS; `note` was the
    # inconsistent one.
    "NOTES": "note",
    "TIP": "tip",
    "TIPS": "tip",
    "IMPORTANT": "note",
    "NOTICE": "note",
    "AVERTISSEMENT": "warning",
    "ATTENTION": "caution",
    "REMARQUE": "note",
    "REMARQUES": "note",
    "CONSEIL": "tip",
    "CONSEILS": "tip",
    "ADVERTENCIA": "warning",
    "PELIGRO": "danger",
    "PRECAUCIÓN": "caution",
    "PRECAUCION": "caution",
    "NOTA": "note",
    "NOTAS": "note",
    "OBSERVACIÓN": "note",
    "OBSERVACION": "note",
    "OBSERVACIONES": "note",
    # Recognition-only synonyms the data plane does not carry: the zh corpus
    # authors 备注/说明 beside the registered 提示/注意, templates carry the
    # traditional-script 備註, and uk uses the plural ПОРАДИ of the registered
    # ПОРАДА. Everything else non-en/fr/es resolves through the data index.
    "备注": "note",
    "說明": "note",
    "说明": "note",
    "備註": "note",
    "ПОРАДИ": "tip",
    "CONSEJO": "tip",
    "CONSEJOS": "tip",
    # Keep the shipped Korean labels as recognition literals too.  The live
    # data mirror can temporarily carry English compatibility values in its
    # ``text_ko`` column; that must not let an authored Korean notice silently
    # degrade to a generic table while the fixture/source catches up.
    "경고": "warning",
    "위험": "danger",
    "주의": "caution",
    "참고": "note",
    "팁": "tip",
    "중요": "note",
}


def display_label(value: str) -> str:
    return re.sub(r"[\s:：-]+$", "", str(value).strip()).strip()


@lru_cache(maxsize=1)
def _data_variant_index() -> dict[str, str]:
    """label → variant, derived from the ten-language signal-word data plane.

    ``Localized_Copy.csv`` / ``symbols_blocks.csv`` (read through
    ``tools.signal_words``, with the committed fixture as fallback when the
    live mirror is absent) already carry every language's printed signal
    words. This reverse index is what lets LaTeX and IDML recognise them the
    way Word always has — before it, a de/ko/uk/zh callout silently lost its
    box in both print renderers while Word boxed it.

    Where the same label maps to two signal keys (zh 提示 is both note's label
    and tips' label), the first key in sorted order wins — note over tips —
    matching the Word pipeline's long-standing ``setdefault`` behaviour.
    Cached for the build's lifetime; a long-lived process does not observe
    mirror edits.
    """

    from tools.signal_words import signal_label_entries

    index: dict[str, str] = {}
    for entry in signal_label_entries():
        variant = _VARIANT_ALIASES.get(entry.key, entry.key)
        if variant not in CALLOUT_VARIANTS:
            continue
        index.setdefault(display_label(entry.label).upper(), variant)
    return index


def known_signal_word_labels() -> frozenset[str]:
    """Every label ``variant_for_label`` recognises, static and data-derived.

    The audit tooling consumes this so its vocabulary can never disagree with
    what the renderers actually recognise.
    """

    return frozenset(_VARIANTS_BY_LABEL) | frozenset(_data_variant_index())


def variant_for_label(label: str) -> str | None:
    """Resolve a printed signal word to its callout variant, any language.

    The static map keeps recognition-only synonyms the data plane does not
    hold (plural forms, accent-stripped near-misses — ``aliases_*`` columns
    exist in the source table but are not read by ``signal_words``); the data
    index supplies every registered language's printed labels. Static entries
    win, so the historical en/fr/es behaviour is unchanged by construction.
    """

    key = display_label(label).upper()
    static = _VARIANTS_BY_LABEL.get(key)
    if static is not None:
        return static
    return _data_variant_index().get(key)


def _normalized_variant(label: str, variant: str | None, *, legacy: bool) -> str:
    declared = _VARIANT_ALIASES.get(str(variant or "").strip().casefold(), str(variant or "").strip().casefold())
    if declared in CALLOUT_VARIANTS:
        return declared
    inferred = variant_for_label(label)
    if inferred is not None:
        return inferred
    if legacy and not declared:
        return "note"
    raise ComponentSpecError(
        f"{COMPONENT_ID}: cannot resolve callout variant from label={label!r} "
        f"variant={variant!r}"
    )


def callout_component_spec(
    *,
    label: str,
    body: str,
    source_ref: str,
    language: str,
    variant: str | None = None,
    items: Sequence[str] = (),
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    normalized_label = display_label(label)
    if not normalized_label:
        raise ComponentSpecError(f"{COMPONENT_ID}: label must be source-authored")
    active_registry = registry if registry is not None else load_component_registry()
    slots = [
        ComponentSlot(role="label", content_kind="inline_text", content=normalized_label),
        ComponentSlot(role="body", content_kind="rich_text", content=str(body)),
    ]
    normalized_items = [str(item) for item in items]
    if normalized_items:
        slots.append(
            ComponentSlot(role="items", content_kind="list_items", content=normalized_items)
        )
    spec = ComponentSpec(
        component_id=COMPONENT_ID,
        variant=_normalized_variant(normalized_label, variant, legacy=False),
        source_ref=str(source_ref),
        language=str(language or "und"),
        slots=tuple(slots),
        assets=(),
        token_roles=tuple(
            active_registry["components"][COMPONENT_ID]["token_roles"]
        ),
        metadata=dict(metadata or {}),
    )
    return require_valid_component_spec(spec, active_registry)


def callout_spec_from_legacy_notice(
    payload: Mapping[str, Any],
    *,
    source_ref: str,
    language: str,
    registry: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    label = display_label(str(payload.get("label") or ""))
    if not label:
        raise ComponentSpecError(f"{COMPONENT_ID}: legacy notice label is missing")
    texts = [str(item) for item in payload.get("texts") or []]
    declared_variant = str(payload.get("variant") or "").strip()
    semantic_variant = _normalized_variant(label, declared_variant, legacy=True)
    active_registry = registry if registry is not None else load_component_registry()
    slots = [
        ComponentSlot(role="label", content_kind="inline_text", content=label),
        ComponentSlot(role="body", content_kind="rich_text", content="\n".join(texts)),
    ]
    if payload.get("list"):
        slots.append(ComponentSlot(role="items", content_kind="list_items", content=texts))
    spec = ComponentSpec(
        component_id=COMPONENT_ID,
        variant=semantic_variant,
        source_ref=source_ref,
        language=language or "und",
        slots=tuple(slots),
        assets=(),
        token_roles=tuple(
            active_registry["components"][COMPONENT_ID]["token_roles"]
        ),
        metadata={"legacy_payload": deepcopy(dict(payload))},
    )
    return require_valid_component_spec(spec, active_registry)


__all__ = [
    "CALLOUT_VARIANTS",
    "COMPONENT_ID",
    "callout_component_spec",
    "callout_spec_from_legacy_notice",
    "display_label",
    "variant_for_label",
]
