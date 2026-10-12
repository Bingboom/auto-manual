"""Stable source-fragment hashes for governed Web composite approval."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from bs4 import BeautifulSoup, Tag


def _fragment_sha256(*values: object) -> str:
    payload = "\n".join(str(value) for value in values)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalized_fragment(fragment: Tag, *, image_key: str) -> str:
    normalized = BeautifulSoup(str(fragment), "html.parser")
    for image in normalized.find_all("img"):
        image["src"] = f"asset:{image_key}"
    return str(normalized)


def semantic_source_fragment_sha256(semantic: Tag, *, image_key: str) -> str:
    """Hash a generic semantic figure while normalizing its asset location."""

    return _fragment_sha256(_normalized_fragment(semantic, image_key=image_key))


def reference_source_fragment_sha256(
    *,
    component: Mapping[str, Any],
    semantic: Tag,
    caption_labels: list[str],
    composite_locale: str | None,
) -> str:
    """Hash a reference figure using its exact or explicitly shared policy."""

    if str(composite_locale or "").casefold() == "shared":
        return _fragment_sha256(
            str(component["id"]),
            str(component["image_key"]),
            bool(component.get("captions_embedded")),
            int(component.get("capture_following_lines") or 0),
        )
    return _fragment_sha256(
        _normalized_fragment(
            semantic,
            image_key=str(component["image_key"]),
        ),
        "\n".join(caption_labels),
    )


__all__ = (
    "reference_source_fragment_sha256",
    "semantic_source_fragment_sha256",
)
