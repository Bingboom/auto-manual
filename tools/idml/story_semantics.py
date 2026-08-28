"""Small semantic helpers for the prose-story renderer."""
from __future__ import annotations

from . import prose_flow


def story_language(
    blocks: list[tuple[str, str]],
    language: str | None,
) -> str:
    """Resolve the source-authored story language without page-name branches."""
    first_h1 = next((text for kind, text in blocks if kind == "h1"), "")
    return language or {
        "WARRANTY": "en",
        "GARANTIE": "fr",
        "GARANTÍA": "es",
    }.get(first_h1) or prose_flow.operation_language(blocks)


def image_role(
    image_roles: tuple[str, ...],
    index: int,
    *,
    title: str,
) -> str | None:
    """Return the ordered semantic role for one image, failing on underrun."""
    if not image_roles:
        return None
    if index >= len(image_roles):
        raise ValueError(f"{title}: semantic image roles do not cover every image")
    return image_roles[index]


def consume_image_role(
    override: str | None,
    image_roles: tuple[str, ...],
    index: int,
    *,
    title: str,
) -> tuple[str | None, int]:
    """Consume one target override or the next ordered semantic image role."""
    if override is not None:
        return override, index
    return image_role(image_roles, index, title=title), index + 1


def require_all_image_roles(
    image_roles: tuple[str, ...],
    consumed: int,
    *,
    title: str,
) -> None:
    """Fail when an assembly declares roles for images that were not present."""
    if image_roles and consumed != len(image_roles):
        raise ValueError(
            f"{title}: semantic image roles require {len(image_roles)} images, "
            f"found {consumed}"
        )


__all__ = ["consume_image_role", "image_role", "require_all_image_roles", "story_language"]
