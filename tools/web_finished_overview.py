"""Exact Web-only bindings for approved, complete Overview illustrations."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Tag
from tools.manual_ir.validate import finished_overview_views
from tools.web_base_art_locale import resolve_base_art_figure


def find_source_images(
    soup: BeautifulSoup, views: Mapping[str, Mapping[str, str]], *, source_path: Any,
) -> dict[str, Tag]:
    """Match the original source images before a manifest rewrites their src."""

    found: dict[str, Tag] = {}
    for view_id, binding in views.items():
        key = binding["image_key"].replace("\\", "/").casefold()
        matches = [
            image for image in soup.find_all("img")
            if key in str(image.get("src") or "").replace("\\", "/").casefold()
        ]
        if len(matches) != 1:
            raise ValueError(f"{source_path}: finished Overview {view_id} needs one source image")
        source_name = PurePosixPath(unquote(urlparse(str(matches[0].get("src") or "")).path)).name
        if source_name != binding["source_image"]:
            raise ValueError(f"{source_path}: finished Overview {view_id} source image disagrees")
        found[view_id] = matches[0]
    if len({id(image) for image in found.values()}) != 2:
        raise ValueError(f"{source_path}: finished Overview source images overlap")
    return found


def bind_finished_images(
    soup: BeautifulSoup, images: Mapping[str, Tag],
    views: Mapping[str, Mapping[str, str]], entries: Mapping[tuple[str, str], Mapping[str, Any]],
    *, language: str, source_path: Any,
) -> None:
    """Bind only manifest-verified artwork to the two frozen coverage slots."""

    for view_id, binding in views.items():
        image = images[view_id]
        source_image = binding["source_image"]
        entry = entries.get((language, source_image))
        if (
            not isinstance(entry, Mapping)
            or entry.get("replaces") != [source_image]
            or not entry.get("covered_annotations")
            or str(image.get("data-web-finished-panel-path") or "") != entry.get("path")
            or str(image.get("data-web-finished-panel-sha256") or "") != entry.get("sha256")
            or not image.get("alt")
        ):
            raise ValueError(f"{source_path}: finished Overview {view_id} lacks approved artwork")
        section = image.find_parent("section")
        if not isinstance(section, Tag) or section.select("table"):
            raise ValueError(f"{source_path}: finished Overview {view_id} has uncovered copy")
        figure = soup.new_tag("figure", attrs={
            "class": "hb-finished-overview-figure",
            "data-web-replace-key": binding["web_replace_key"],
        })
        image.replace_with(figure)
        figure.append(image)


def find_finished_operation_images(
    soup: BeautifulSoup, figures: list[dict[str, Any]],
    entries: Mapping[tuple[str, str], Mapping[str, Any]], *,
    language: str, source_path: Any,
) -> dict[str, tuple[Tag, str]]:
    """Select only manifest-backed copy-consuming panels, never active flow art."""

    found: dict[str, tuple[Tag, str]] = {}
    for figure in figures:
        slot = str(figure.get("web_replace_key") or "").strip()
        key = str(figure.get("image_key") or "").replace("\\", "/").casefold()
        if not slot or not key or slot in found:
            raise ValueError(f"{source_path}: finished Operation has invalid slot/image key")
        short_key = key.rsplit("/", 1)[-1]
        matches = [
            image for image in soup.find_all("img")
            if key in str(image.get("src") or "").replace("\\", "/").casefold()
            or short_key in PurePosixPath(unquote(urlparse(
                str(image.get("src") or "")
            ).path)).stem.casefold()
        ]
        if len(matches) != 1:
            raise ValueError(f"{source_path}: finished Operation {slot} needs one source image")
        image = matches[0]
        source_name = PurePosixPath(unquote(urlparse(str(image.get("src") or "")).path)).name
        if not source_name:
            raise ValueError(f"{source_path}: finished Operation {slot} has no source name")
        entry = entries.get((language, source_name))
        covered = isinstance(entry, Mapping) and bool(entry.get("covered_annotations"))
        if resolve_base_art_figure(figure, language).get("presentation_mode") == "base-art-live-copy":
            if covered:
                raise ValueError(
                    f"{source_path}: flow Operation {slot} still has a copy-consuming finished manifest"
                )
            continue
        if not covered:
            continue
        if entry.get("replaces") != [source_name]:
            raise ValueError(f"{source_path}: finished Operation {slot} source replacement disagrees")
        found[slot] = image, source_name
    if len({id(image) for image, _name in found.values()}) != len(found):
        raise ValueError(f"{source_path}: finished Operation images overlap")
    return found


def bind_finished_operation_images(
    soup: BeautifulSoup, images: Mapping[str, tuple[Tag, str]],
    entries: Mapping[tuple[str, str], Mapping[str, Any]], *,
    language: str, source_path: Any,
) -> None:
    """Use the original slot only after manifest replacement consumed exact copy."""

    for slot, (image, source_name) in images.items():
        entry = entries.get((language, source_name))
        if (
            not isinstance(entry, Mapping)
            or entry.get("replaces") != [source_name]
            or not entry.get("covered_annotations")
            or str(image.get("data-web-finished-panel-path") or "") != entry.get("path")
            or str(image.get("data-web-finished-panel-sha256") or "") != entry.get("sha256")
            or not image.get("alt")
        ):
            raise ValueError(f"{source_path}: finished Operation {slot} lacks approved artwork")
        carrier = soup.new_tag("figure", attrs={
            "class": "hb-finished-operation-figure",
            "data-web-replace-key": slot,
        })
        image.replace_with(carrier)
        carrier.append(image)


def find_finished_reference_images(
    soup: BeautifulSoup, figures: list[dict[str, Any]],
    entries: Mapping[tuple[str, str], Mapping[str, Any]], *,
    language: str, source_path: Any,
) -> dict[str, tuple[Tag, str]]:
    """Select exact finished Charging art without claiming unrelated references."""

    found: dict[str, tuple[Tag, str]] = {}
    for figure in figures:
        if not str(figure.get("id") or "").startswith("charging-"):
            continue
        if figure.get("presentation") == "shared-art-live-labels":
            continue
        slot = str(figure.get("web_replace_key") or "").strip()
        key = str(figure.get("image_key") or "").replace("\\", "/").casefold()
        if not slot or not key or slot in found:
            raise ValueError(f"{source_path}: finished Charging has invalid slot/image key")
        matches = [
            image for image in soup.find_all("img")
            if key in str(image.get("src") or "").replace("\\", "/").casefold()
        ]
        if len(matches) != 1:
            raise ValueError(f"{source_path}: finished Charging {slot} needs one source image")
        image = matches[0]
        source_name = PurePosixPath(unquote(urlparse(str(image.get("src") or "")).path)).name
        entry = entries.get((language, source_name))
        if entry is None:
            continue
        if entry.get("replaces") != [source_name]:
            raise ValueError(f"{source_path}: finished Charging {slot} source replacement disagrees")
        found[slot] = image, source_name
    if len({id(image) for image, _name in found.values()}) != len(found):
        raise ValueError(f"{source_path}: finished Charging images overlap")
    return found


def bind_finished_reference_images(
    soup: BeautifulSoup, images: Mapping[str, tuple[Tag, str]],
    entries: Mapping[tuple[str, str], Mapping[str, Any]], *,
    language: str, source_path: Any,
) -> None:
    """Attach a Charging slot only after its frozen image was replaced exactly."""

    for slot, (image, source_name) in images.items():
        entry = entries.get((language, source_name))
        if (
            not isinstance(entry, Mapping)
            or entry.get("replaces") != [source_name]
            or str(image.get("data-web-finished-panel-path") or "") != entry.get("path")
            or str(image.get("data-web-finished-panel-sha256") or "") != entry.get("sha256")
            or not image.get("alt")
        ):
            raise ValueError(f"{source_path}: finished Charging {slot} lacks approved artwork")
        carrier = soup.new_tag("figure", attrs={
            "class": "hb-finished-charging-figure",
            "data-web-replace-key": slot,
        })
        image.replace_with(carrier)
        carrier.append(image)


__all__ = [
    "bind_finished_images", "bind_finished_operation_images", "bind_finished_reference_images",
    "find_source_images", "find_finished_operation_images", "find_finished_reference_images",
    "finished_overview_views",
]
