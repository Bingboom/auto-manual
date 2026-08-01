"""Reusable reference-figure helpers for the responsive web manual."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag


def prepare_reference_caption_data(
    *,
    image: Tag,
    spec: dict[str, Any],
    source_path: Path,
    error_type: type[Exception],
) -> tuple[Tag | None, list[str]]:
    """Validate the governed semantic labels and return optional figure captions."""
    reference_id = str(spec["id"])
    label_block: Tag | None = None
    if "capture_following_lines" in spec:
        sibling = image.next_sibling
        while sibling is not None and not isinstance(sibling, Tag):
            sibling = sibling.next_sibling
        label_block = sibling
        if not isinstance(label_block, Tag) or "line-block" not in label_block.get(
            "class", []
        ):
            raise error_type(
                f"{source_path}: reference figure {reference_id} must be followed by a line-block"
            )
        expected = int(spec["capture_following_lines"])
        lines = label_block.find_all(class_="line", recursive=False)
        if len(lines) != expected:
            raise error_type(
                f"{source_path}: reference figure {reference_id} has {len(lines)} "
                f"governed label lines; expected exactly {expected}"
            )
    labels = [
        str(value).strip()
        for value in spec.get("caption_labels", [])
        if str(value).strip()
    ]
    if label_block is None and not labels:
        raise error_type(
            f"{source_path}: reference figure {reference_id} must declare captured labels "
            "or caption labels"
        )
    return label_block, labels


def append_reference_captions(
    soup: BeautifulSoup,
    figure: Tag,
    *,
    labels: list[str],
    layout: str = "equal",
) -> None:
    if not labels:
        return
    caption = soup.new_tag(
        "figcaption",
        attrs={
            "class": "hb-reference-caption-grid",
            "data-caption-layout": layout,
            "data-caption-count": str(len(labels)),
        },
    )
    for label in labels:
        item = soup.new_tag("span", attrs={"class": "hb-reference-caption"})
        item.string = label
        caption.append(item)
    figure["class"] = [*figure.get("class", []), "hb-has-reference-captions"]
    figure.append(caption)
