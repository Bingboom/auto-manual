"""Structure-first HTML source adapters for App ComponentSpecs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, cast

from bs4 import BeautifulSoup, Tag

from tools.component_specs.app import (
    app_add_device_component_spec,
    app_download_component_spec,
    app_inline_control_component_spec,
    resolve_app_control_label_roles,
)
from tools.component_specs.app_label_source import (
    app_display_metadata, app_interstitial_note, app_label_boundaries,
)
from tools.component_specs.app_qr_source import parse_app_qr_download_html
from tools.component_specs.model import ComponentSpec
from tools.manual_ir.web_app_download import load_web_download_source
from tools.utils.path_utils import repo_root


def _path(value: object, *, owner: str) -> Path:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{owner} requires a governed artwork path")
    path = Path(raw)
    return path if path.is_absolute() else repo_root() / path


def _matches_image(image: Tag, image_key: str) -> bool:
    source = str(image.get("src") or "").replace("\\", "/").casefold()
    key = image_key.replace("\\", "/").casefold()
    return key in source or key.rsplit("/", 1)[-1] in source


def _next_tag(tag: Tag) -> Tag | None:
    candidate = tag.next_sibling
    while candidate is not None and not isinstance(candidate, Tag):
        candidate = candidate.next_sibling
    return candidate if isinstance(candidate, Tag) else None


def parse_app_download_html(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    config: Mapping[str, Any],
    language: str,
    model: str,
    region: str,
) -> tuple[ComponentSpec, tuple[Tag, ...], tuple[tuple[str, Tag], ...], tuple[tuple[str, Path], ...]]:
    """Parse the established two-column source contract without mutating it."""

    if config.get("presentation") == "qr-only":
        return parse_app_qr_download_html(
            soup, config=config, source_path=source_path, language=language,
        )

    source = load_web_download_source(
        str(soup),
        source_path=source_path,
        config=dict(config),
        language=language,
        model=model,
        region=region,
    )
    payload = source.pages[0].blocks[0][1]
    image_html = str(payload["semantic_image_html"])
    images = [image for image in soup.find_all("img") if str(image) == image_html]
    if len(images) != 1:
        raise ValueError(f"{source_path}: App download carrier is ambiguous")
    image = images[0]
    section = image.find_parent("section")
    if not isinstance(section, Tag):
        raise ValueError(f"{source_path}: App download carrier has no section")
    paragraphs = tuple(section.find_all("p", recursive=False))
    if len(paragraphs) not in {1, 2}:
        raise ValueError(f"{source_path}: App download carrier copy is ambiguous")
    artwork = config.get("artwork")
    if not isinstance(artwork, Mapping):
        raise ValueError(f"{source_path}: App download artwork contract is invalid")
    spec = app_download_component_spec(
        accessibility_label=str(payload["label"]),
        columns=tuple(payload["columns"]),
        source_art_ref=str(image.get("src") or ""),
        store_art_ref=str(artwork.get("store") or ""),
        qr_art_ref=str(artwork.get("qr") or ""),
        source_ref=f"{source_path}#app-download",
        language=language,
        metadata={"image_key": str(config.get("image_key") or "")},
    )
    return (
        spec,
        (image, *paragraphs),
        (("source_art", image),),
        (
            ("store_art", _path(artwork.get("store"), owner="App store artwork")),
            ("qr_art", _path(artwork.get("qr"), owner="App QR artwork")),
        ),
    )


def parse_declared_app_downloads(soup, *, source_path, language):
    """Bind authored artwork choices to the existing full download component."""
    for image in soup.select("img.hb-source-app-download"):
        config = json.loads(str(image.get("data-app-download") or "{}"))
        if not isinstance(config, dict) or set(config) != {"artwork"}:
            raise ValueError(f"{source_path}: declared App download requires artwork bindings")
        config["image_key"] = str(image.get("src") or "")
        yield parse_app_download_html(
            soup, source_path=source_path, config=config,
            language=language, model="", region="",
        )


def parse_app_inline_control_html(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    config: Mapping[str, Any],
    language: str,
) -> tuple[ComponentSpec, tuple[Tag, ...]]:
    """Parse one numbered rich paragraph and its localized visible label."""

    prefix = str(config.get("add_device_paragraph_prefix") or "").strip()
    if not prefix:
        raise ValueError(f"{source_path}: App inline control requires a prefix")
    candidates = [
        paragraph
        for paragraph in soup.find_all("p")
        if paragraph.get_text(" ", strip=True).startswith(prefix)
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"{source_path}: expected one {prefix} App control paragraph; "
            f"found {len(candidates)}"
        )
    paragraph = candidates[0]
    labels = paragraph.find_all("strong")
    if len(labels) != 1 or labels[0].find(["img", "svg"]):
        raise ValueError(
            f"{source_path}: App control paragraph requires one text-only label"
        )
    label = labels[0].get_text(" ", strip=True)
    if not label:
        raise ValueError(f"{source_path}: App control label is empty")
    spec = app_inline_control_component_spec(
        accessibility_label=label,
        paragraph_html=str(paragraph),
        paragraph_text=paragraph.get_text(" ", strip=True),
        source_ref=f"{source_path}#app-inline-control",
        language=language,
        metadata={"paragraph_prefix": prefix},
    )
    return spec, (paragraph,)


def parse_app_add_device_html(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    config: Mapping[str, Any],
    language: str,
) -> tuple[ComponentSpec, tuple[Tag, ...], tuple[tuple[str, Tag], ...], tuple[tuple[str, Path], ...]]:
    """Parse shared text-free App art plus ordered live localized labels."""

    image_key = str(config.get("image_key") or "").strip()
    images = [
        image for image in soup.find_all("img") if _matches_image(image, image_key)
    ]
    if not image_key or len(images) != 1:
        raise ValueError(
            f"{source_path}: App add-device requires one governed image; "
            f"found {len(images)}"
        )
    image = images[0]
    owned_nodes: tuple[Tag | None, ...]
    label_block, owned_nodes = app_label_boundaries(soup, image, config)
    if not isinstance(label_block, Tag) or "line-block" not in label_block.get(
        "class", []
    ):
        raise ValueError(f"{source_path}: App add-device image requires live labels")
    owned_nodes = cast(tuple[Tag, ...], owned_nodes)
    lines = [
        line
        for line in label_block.find_all(class_="line", recursive=False)
        if line.get_text(" ", strip=True)
    ]
    roles = [str(value).strip() for value in config.get("label_roles", [])]
    if len(lines) != len(roles) or len(lines) != 3 or not all(roles):
        raise ValueError(f"{source_path}: App add-device label roles are incomplete")
    resolved_roles = resolve_app_control_label_roles(
        [line.get_text(" ", strip=True) for line in lines],
        roles,
        owner=f"{source_path}: App add-device",
    )
    labels = tuple(
        {
            "role": role,
            "html": line.decode_contents().strip(),
            "text": line.get_text(" ", strip=True),
        }
        for role, line in zip(resolved_roles, lines, strict=True)
    )
    spec = app_add_device_component_spec(
        accessibility_label=str(image.get("alt") or config.get("id") or "App add device"),
        reference_id=str(config.get("id") or ""),
        labels=labels,
        source_art_ref=str(image.get("src") or ""),
        phone_art_ref=str(config.get("phone_artwork") or ""),
        control_art_ref=str(config.get("control_artwork") or ""),
        source_ref=f"{source_path}#app-add-device",
        language=language,
        step_captions=config.get("step_captions"),
        interstitial_note=app_interstitial_note(owned_nodes),
        metadata=app_display_metadata(config),
    )
    return (
        spec,
        owned_nodes,
        (("source_art", image),),
        (
            (
                "phone_art",
                _path(config.get("phone_artwork"), owner="App phone artwork"),
            ),
            (
                "control_art",
                _path(config.get("control_artwork"), owner="App control artwork"),
            ),
        ),
    )


__all__ = [
    "parse_app_add_device_html",
    "parse_app_download_html",
    "parse_app_inline_control_html",
]
