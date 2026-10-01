"""Normalize an explicit control-image plus three label paragraphs source shape."""
from typing import Any, Mapping, Sequence

from bs4 import BeautifulSoup, Tag


def _bound_control(image: Tag, image_key: str) -> tuple[Tag | None, Tag | None]:
    if not image_key:
        return None, None
    control = image.find_next_sibling()
    # Keep an authored note between phone screenshots and controls in place.
    note = None
    if isinstance(control, Tag) and control.name == "table" and not control.find("img"):
        note = control
        control = control.find_next_sibling()
    if not isinstance(control, Tag) or control.name != "img":
        return None, None
    source = str(control.get("src") or "").replace("\\", "/")
    if image_key not in source and image_key.rsplit("/", 1)[-1] not in source:
        return None, None
    return control, note


def normalize_control_labels(soup: BeautifulSoup, image: Tag, image_key: str) -> Tag | None:
    """Normalize explicitly bound controls while retaining authored notes."""
    control, note = _bound_control(image, image_key)
    if control is None:
        return None
    existing = control.find_next_sibling()
    if isinstance(existing, Tag) and "line-block" in existing.get("class", []):
        return control
    labels = []
    node = control.find_next_sibling()
    for _ in range(3):
        if (not isinstance(node, Tag) or node.name != "p"
                or not node.get_text(strip=True) or node.find(["img", "table"])):
            raise ValueError("App control image requires three nonempty label paragraphs")
        labels.append(node)
        node = node.find_next_sibling()
    block = soup.new_tag("div", attrs={"class": "line-block"})
    for label in labels:
        line = soup.new_tag("div", attrs={"class": "line"})
        for child in list(label.contents):
            line.append(child.extract())
        block.append(line)
    labels[0].replace_with(block)
    for label in labels[1:]:
        label.decompose()
    return control


def app_label_boundaries(
    soup: BeautifulSoup, image: Tag, config: Mapping[str, Any],
) -> tuple[
    Tag | None,
    tuple[Tag, Tag | None]
    | tuple[Tag, Tag, Tag | None]
    | tuple[Tag, Tag | None, Tag, Tag | None],
]:
    control = normalize_control_labels(soup, image, str(config.get("control_image_key") or ""))
    if control is None:
        block = image.find_next_sibling()
        return block, (image, block)
    block = control.find_next_sibling()
    between = image.find_next_sibling()
    owned = (image, control, block) if between is control else (image, between, control, block)
    return block, owned


def app_interstitial_note(owned: Sequence[Tag]) -> dict[str, str] | None:
    """Snapshot the optional note without changing its source order."""
    if len(owned) != 4:
        return None
    note = owned[1]
    return {"html": str(note), "text": note.get_text(" ", strip=True)}


def app_display_metadata(config: Mapping[str, Any]) -> dict[str, Any]:
    """Carry only explicitly bound geometry; legacy packages keep their output."""
    return {"captions_embedded": bool(config.get("captions_embedded")),
            **{key: config[key] for key in ("phone_max_width_rem", "caption_centers_pct")
               if key in config}}
