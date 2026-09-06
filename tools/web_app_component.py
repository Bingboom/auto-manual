"""Web renderer for App ComponentSpecs embedded in whole-document flow."""
from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from tools.component_specs.app_adapters import web_app_projection
from tools.component_specs.model import ComponentSpec


def _normalized(value: str) -> str:
    return " ".join(value.split())


def _asset(payload: dict, role: str) -> str:
    value = str(payload.get(role) or "").strip()
    if not value:
        raise ValueError(f"embedded App component is missing {role}")
    return value


def _render_download(spec: ComponentSpec, carrier_html: str) -> str:
    payload = web_app_projection(spec)
    soup = BeautifulSoup(carrier_html, "html.parser")
    images = [
        image
        for image in soup.find_all("img")
        if str(image.get("src") or "") == _asset(payload, "source_art")
    ]
    paragraphs = soup.find_all("p", recursive=False)
    if len(images) != 1 or len(paragraphs) not in {1, 2}:
        raise ValueError(f"{spec.source_ref}: App download carrier is incomplete")
    expected_text = _normalized(
        " ".join(str(column["text"]) for column in payload["columns"])
    )
    actual_text = _normalized(
        " ".join(paragraph.get_text(" ", strip=True) for paragraph in paragraphs)
    )
    if actual_text != expected_text:
        raise ValueError(f"{spec.source_ref}: App download carrier disagrees with slots")
    image = images[0]
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-app-download-composition",
            "aria-label": payload["accessibility_label"],
            "data-component-id": spec.component_id,
        },
    )
    image["class"] = [*image.get("class", []), "hb-app-download-semantic-art"]
    grid = soup.new_tag("div", attrs={"class": "hb-app-download-grid"})
    for column in payload["columns"]:
        role = str(column["role"])
        wrapper = soup.new_tag(
            "div",
            attrs={"class": ["hb-app-download-column", f"hb-app-download-column-{role}"]},
        )
        art_frame = soup.new_tag("div", attrs={"class": "hb-app-download-art-frame"})
        art_frame.append(
            soup.new_tag(
                "img",
                attrs={
                    "class": ["hb-app-download-art", f"hb-app-download-art-{role}"],
                    "src": _asset(payload, f"{role}_art"),
                    "alt": "",
                    "aria-hidden": "true",
                    "loading": "lazy",
                },
            )
        )
        wrapper.append(art_frame)
        copy = soup.new_tag(
            "div",
            attrs={"class": ["hb-app-download-copy", f"hb-app-download-copy-{role}"]},
        )
        paragraph = soup.new_tag("p")
        markup = BeautifulSoup(str(column["html"]), "html.parser")
        for child in list(markup.contents):
            paragraph.append(child.extract())
        copy.append(paragraph)
        wrapper.append(copy)
        grid.append(wrapper)
    figure.append(grid)
    semantic = soup.new_tag("div", attrs={"class": "hb-app-download-semantic"})
    semantic.append(image.extract())
    figure.append(semantic)
    return str(figure)


def _render_inline_control(spec: ComponentSpec, carrier_html: str) -> str:
    payload = web_app_projection(spec)
    soup = BeautifulSoup(carrier_html, "html.parser")
    paragraph = soup.find("p")
    if not isinstance(paragraph, Tag) or len(soup.find_all("p")) != 1:
        raise ValueError(f"{spec.source_ref}: App inline carrier requires one paragraph")
    slot = payload["paragraph"]
    labels = paragraph.find_all("strong")
    if (
        len(labels) != 1
        or labels[0].get_text(" ", strip=True) != payload["accessibility_label"]
        or _normalized(paragraph.get_text(" ", strip=True))
        != _normalized(str(slot["text"]))
    ):
        raise ValueError(f"{spec.source_ref}: App inline carrier disagrees with slots")
    icon = soup.new_tag(
        "span",
        attrs={
            "class": "hb-inline-add-device-icon",
            "role": "img",
            "aria-label": payload["accessibility_label"],
            "data-component-id": spec.component_id,
        },
    )
    icon.string = "+"
    labels[0].replace_with(icon)
    return str(paragraph)


def _render_add_device(spec: ComponentSpec, carrier_html: str) -> str:
    payload = web_app_projection(spec)
    soup = BeautifulSoup(carrier_html, "html.parser")
    images = [
        image
        for image in soup.find_all("img")
        if str(image.get("src") or "") == _asset(payload, "source_art")
    ]
    blocks = soup.select(".line-block")
    if len(images) != 1 or len(blocks) != 1:
        raise ValueError(f"{spec.source_ref}: App add-device carrier is incomplete")
    lines = blocks[0].find_all(class_="line", recursive=False)
    labels = payload["labels"]
    if [line.get_text(" ", strip=True) for line in lines] != [
        str(label["text"]) for label in labels
    ]:
        raise ValueError(f"{spec.source_ref}: App add-device carrier disagrees with slots")
    image = images[0]
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-app-add-device-composition",
            "data-reference-id": payload["reference_id"],
            "data-step-captions": "embedded",
            "data-component-id": spec.component_id,
        },
    )
    for attribute in ("style", "width", "height"):
        image.attrs.pop(attribute, None)
    image["src"] = _asset(payload, "phone_art")
    image["class"] = [*image.get("class", []), "hb-app-add-device-phone-art"]
    phone_stage = soup.new_tag("div", attrs={"class": "hb-app-add-device-phone-stage"})
    phone_stage.append(image.extract())
    figure.append(phone_stage)
    control_panel = soup.new_tag("div", attrs={"class": "hb-app-add-device-control-panel"})
    control_panel.append(
        soup.new_tag(
            "img",
            attrs={
                "class": "hb-app-add-device-control-art",
                "src": _asset(payload, "control_art"),
                "alt": "",
                "aria-hidden": "true",
                "loading": "lazy",
            },
        )
    )
    for line, label in zip(lines, labels, strict=True):
        line.extract()
        line.name = "span"
        line.attrs = {
            "class": [
                "hb-app-add-device-live-label",
                f"hb-app-add-device-live-label-{label['role']}",
            ]
        }
        control_panel.append(line)
    figure.append(control_panel)
    return str(figure)


def render_app_component(spec: ComponentSpec, carrier_html: str) -> str:
    """Render one validated App variant without a page-DOM source scan."""

    if spec.variant == "download":
        return _render_download(spec, carrier_html)
    if spec.variant == "inline-control":
        return _render_inline_control(spec, carrier_html)
    if spec.variant == "add-device":
        return _render_add_device(spec, carrier_html)
    raise ValueError(f"{spec.source_ref}: unsupported App variant {spec.variant!r}")


__all__ = ["render_app_component"]
