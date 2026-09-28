"""Exact locale activation for container-free Operation artwork.

The one map binds both the opt-in and its artwork. It never falls back to a
different language, and does not replace the legacy composite locale resolver.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import re
from typing import Any


LOCALE_LAYOUTS = "base_art_layout_by_locale"
_LOCALE = re.compile(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})*")
_SHA256 = re.compile(r"[0-9a-f]{64}")


def base_art_locale_layouts(
    figure: Mapping[str, Any], *, error_type: type[Exception] = ValueError,
) -> dict[str, dict[str, str]]:
    """Validate an optional locale map without selecting or broadening it."""

    if LOCALE_LAYOUTS not in figure:
        return {}
    raw = figure[LOCALE_LAYOUTS]
    if figure.get("layout") != "status-right" or any(
        key in figure for key in ("presentation_mode", "base_art_layout")
    ):
        raise error_type(
            f"{LOCALE_LAYOUTS} requires status-right without a global mode/layout"
        )
    if not isinstance(raw, Mapping) or not raw:
        raise error_type(f"{LOCALE_LAYOUTS} must be a non-empty locale object")
    result = {}
    for locale, layout in raw.items():
        if not isinstance(locale, str) or locale == "und" or not _LOCALE.fullmatch(locale):
            raise error_type(f"{LOCALE_LAYOUTS} keys must be canonical lowercase locales")
        if (
            not isinstance(layout, Mapping)
            or set(layout) != {"art_sha256", "copy_layout"}
            or layout["copy_layout"] != "flow"
            or not isinstance(layout["art_sha256"], str)
            or not _SHA256.fullmatch(layout["art_sha256"])
        ):
            raise error_type(
                f"{LOCALE_LAYOUTS}.{locale} requires exactly flow and a valid art_sha256"
            )
        result[locale] = dict(layout)
    return result


def resolve_base_art_figure(
    figure: Mapping[str, Any], language: str | None,
) -> dict[str, Any]:
    """Select one exact locale, or leave an unselected locale on its old path."""

    layouts = base_art_locale_layouts(figure)
    resolved = deepcopy(dict(figure)) if layouts else dict(figure)
    if not layouts:
        return resolved
    locale = str(language or "").strip().casefold()
    if not locale or locale == "und" or not _LOCALE.fullmatch(locale):
        raise ValueError(f"{LOCALE_LAYOUTS} requires an explicit page language")
    del resolved[LOCALE_LAYOUTS]
    if locale in layouts:
        resolved["presentation_mode"] = "base-art-live-copy"
        resolved["base_art_layout"] = deepcopy(layouts[locale])
    return resolved


def base_art_slot_locales(
    contract: Mapping[str, Any], *, error_type: type[Exception] = ValueError,
) -> dict[str, list[str]]:
    """Derive the exact coverage scope from the same activation map."""

    operations = contract.get("operations", {})
    figures = operations.get("figures", []) if isinstance(operations, Mapping) else []
    scoped = {}
    for figure in figures:
        if not isinstance(figure, Mapping):
            continue
        layouts = base_art_locale_layouts(figure, error_type=error_type)
        if not layouts:
            continue
        slot = str(figure.get("web_replace_key") or "").strip()
        if not slot or slot in scoped:
            raise error_type(f"{LOCALE_LAYOUTS} needs a unique web_replace_key")
        scoped[slot] = sorted(layouts)
    return scoped


__all__ = [
    "LOCALE_LAYOUTS", "base_art_locale_layouts", "base_art_slot_locales",
    "resolve_base_art_figure",
]
