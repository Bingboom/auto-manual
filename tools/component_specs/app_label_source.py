"""Normalize an explicit control-image plus three label paragraphs source shape."""
from bs4 import BeautifulSoup, Tag


def normalize_control_labels(soup: BeautifulSoup, image: Tag, image_key: str) -> Tag | None:
    """Return the retained control image; change no source unless all labels validate."""
    if not image_key:
        return None
    control = image.find_next_sibling()
    if not isinstance(control, Tag) or control.name != "img":
        return None
    source = str(control.get("src") or "").replace("\\", "/")
    if image_key not in source and image_key.rsplit("/", 1)[-1] not in source:
        return None
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


def app_label_boundaries(soup: BeautifulSoup, image: Tag, config: dict):
    control = normalize_control_labels(soup, image, str(config.get("control_image_key") or ""))
    if control is None:
        block = image.find_next_sibling()
        return block, (image, block)
    block = control.find_next_sibling()
    return block, (image, control, block)
