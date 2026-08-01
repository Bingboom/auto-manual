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


def transform_app_add_device(
    soup: BeautifulSoup,
    *,
    image: Tag,
    spec: dict[str, Any],
    source_path: Path,
    error_type: type[Exception],
) -> None:
    """Render shared App screenshots and device art with live localized labels."""
    reference_id = str(spec["id"])
    label_block, caption_labels = prepare_reference_caption_data(
        image=image,
        spec=spec,
        source_path=source_path,
        error_type=error_type,
    )
    if not isinstance(label_block, Tag):
        raise error_type(f"{source_path}: {reference_id} requires live control labels")

    roles = [str(value).strip() for value in spec.get("label_roles", [])]
    lines = label_block.find_all(class_="line", recursive=False)
    if len(roles) != len(lines) or not all(roles):
        raise error_type(
            f"{source_path}: {reference_id} label roles do not match its live labels"
        )
    control_artwork = str(spec.get("control_artwork", "")).strip()
    if not control_artwork:
        raise error_type(f"{source_path}: {reference_id} has no shared control artwork")

    figure = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-app-add-device-composition",
            "data-reference-id": reference_id,
        },
    )
    for attribute in ("style", "width", "height"):
        image.attrs.pop(attribute, None)
    image["class"] = [*image.get("class", []), "hb-app-add-device-phone-art"]
    image.replace_with(figure)

    phone_stage = soup.new_tag("div", attrs={"class": "hb-app-add-device-phone-stage"})
    phone_stage.append(image)
    figure.append(phone_stage)
    append_reference_captions(
        soup,
        figure,
        labels=caption_labels,
        layout=str(spec.get("caption_layout", "phone-pair")),
    )

    control_panel = soup.new_tag(
        "div",
        attrs={"class": "hb-app-add-device-control-panel"},
    )
    control_art = soup.new_tag(
        "img",
        attrs={
            "class": "hb-app-add-device-control-art",
            "src": control_artwork,
            "alt": "",
            "aria-hidden": "true",
            "loading": "lazy",
        },
    )
    control_panel.append(control_art)
    for role, line in zip(roles, lines, strict=True):
        line.extract()
        line.name = "span"
        line.attrs = {
            "class": [
                "hb-app-add-device-live-label",
                f"hb-app-add-device-live-label-{role}",
            ],
        }
        control_panel.append(line)
    label_block.decompose()
    figure.append(control_panel)


__all__ = [
    "append_reference_captions",
    "prepare_reference_caption_data",
    "transform_app_add_device",
]
