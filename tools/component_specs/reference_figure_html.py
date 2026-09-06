"""Structure-first HTML adapter for governed reference-figure ComponentSpecs."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from bs4 import BeautifulSoup, Tag

from tools.component_specs.reference_figure import reference_figure_component_spec
from tools.manual_ir.hashing import file_sha256
from tools.web_composite_hashing import reference_source_fragment_sha256
from tools.web_composite_manifest import WebCompositeEntry


def _sibling(tag: Tag, *, previous: bool) -> Tag | None:
    candidate = tag.previous_sibling if previous else tag.next_sibling
    while candidate is not None and not isinstance(candidate, Tag):
        candidate = candidate.previous_sibling if previous else candidate.next_sibling
    return candidate if isinstance(candidate, Tag) else None


def _clone(tag: Tag) -> Tag:
    cloned = BeautifulSoup(str(tag), "html.parser").find()
    if not isinstance(cloned, Tag):
        raise ValueError("reference figure carrier clone failed")
    return cloned


def _semantic_fragment(
    *,
    image: Tag,
    reference_id: str,
    adjacent: Tag | None,
    adjacent_position: str,
    label_block: Tag | None,
) -> Tag:
    soup = BeautifulSoup("", "html.parser")
    semantic = soup.new_tag(
        "div",
        attrs={
            "class": "hb-reference-semantic",
            "data-reference-id": f"{reference_id}.semantic",
        },
    )
    image_copy = _clone(image)
    image_copy["class"] = [*image_copy.get("class", []), "hb-reference-art"]
    if adjacent is not None and adjacent_position == "before":
        semantic.append(_clone(adjacent))
    semantic.append(image_copy)
    if adjacent is not None and adjacent_position == "after":
        semantic.append(_clone(adjacent))
    if label_block is not None:
        labels = _clone(label_block)
        labels["class"] = [*labels.get("class", []), "hb-reference-labels"]
        semantic.append(labels)
    return semantic


def parse_reference_figure_html(
    soup: BeautifulSoup,
    *,
    image: Tag,
    config: Mapping[str, Any],
    source_path: Path,
    language: str,
    composite_locale: str | None,
    approved_entry: WebCompositeEntry | None,
    approved_path: Path | None,
) -> tuple[
    object,
    tuple[Tag, ...],
    tuple[tuple[str, Tag], ...],
    tuple[tuple[str, Path], ...],
]:
    """Parse one exact governed image and its contiguous semantic carrier."""

    reference_id = str(config.get("id") or "").strip()
    if not reference_id:
        raise ValueError(f"{source_path}: reference figure has no stable id")
    label_block: Tag | None = None
    labels: list[dict[str, str]] = []
    capture_lines = int(config.get("capture_following_lines") or 0)
    if capture_lines:
        candidate = _sibling(image, previous=False)
        if not isinstance(candidate, Tag) or "line-block" not in candidate.get(
            "class", []
        ):
            raise ValueError(
                f"{source_path}: reference figure {reference_id} requires a line block"
            )
        lines = candidate.find_all(class_="line", recursive=False)
        if len(lines) != capture_lines:
            raise ValueError(
                f"{source_path}: reference figure {reference_id} has {len(lines)} "
                f"labels; expected {capture_lines}"
            )
        label_block = candidate
        labels = [
            {
                "html": line.decode_contents().strip(),
                "text": line.get_text(" ", strip=True),
            }
            for line in lines
        ]
        if any(not item["text"] for item in labels):
            raise ValueError(
                f"{source_path}: reference figure {reference_id} has an empty label"
            )

    configured_captions = [
        str(value).strip()
        for value in config.get("caption_labels", [])
        if str(value).strip()
    ]
    if configured_captions:
        labels = [{"html": value, "text": value} for value in configured_captions]
    if not labels and not config.get("captions_embedded"):
        raise ValueError(
            f"{source_path}: reference figure {reference_id} requires live or embedded labels"
        )

    adjacent: Tag | None = None
    adjacent_position = ""
    adjacent_copy: dict[str, str] | None = None
    if config.get("capture_adjacent_paragraph"):
        preceding = _sibling(image, previous=True)
        following = _sibling(image, previous=False)
        candidates = [
            candidate
            for candidate in (preceding, following)
            if isinstance(candidate, Tag) and candidate.name == "p"
        ]
        if len(candidates) != 1:
            raise ValueError(
                f"{source_path}: reference figure {reference_id} must have exactly "
                f"one adjacent paragraph; found {len(candidates)}"
            )
        adjacent = candidates[0]
        adjacent_position = "before" if adjacent is preceding else "after"
        adjacent_copy = {
            "position": adjacent_position,
            "html": str(adjacent),
            "text": adjacent.get_text(" ", strip=True),
        }

    semantic = _semantic_fragment(
        image=image,
        reference_id=reference_id,
        adjacent=adjacent,
        adjacent_position=adjacent_position,
        label_block=label_block,
    )
    source_hash = reference_source_fragment_sha256(
        component=dict(config),
        semantic=semantic,
        caption_labels=configured_captions,
        composite_locale=composite_locale,
    )
    approved: dict[str, str] | None = None
    frozen_assets: tuple[tuple[str, Path], ...] = ()
    if approved_entry is not None:
        if approved_path is None or not approved_path.is_file():
            raise ValueError(
                f"{source_path}: approved composite {approved_entry.asset_key} is missing"
            )
        actual_hash = file_sha256(approved_path)
        if actual_hash != approved_entry.content_sha256:
            raise ValueError(
                f"{source_path}: approved composite content SHA-256 changed; "
                f"expected {approved_entry.content_sha256}, got {actual_hash}"
            )
        if source_hash != approved_entry.source_fragment_sha256:
            raise ValueError(
                f"{source_path}: approved composite source changed for "
                f"{approved_entry.web_replace_key!r}; expected "
                f"{approved_entry.source_fragment_sha256}, got {source_hash}"
            )
        approved = {
            "asset_key": approved_entry.asset_key,
            "asset_ref": approved_entry.path,
            "locale": approved_entry.locale,
            "content_sha256": approved_entry.content_sha256,
            "source_fragment_sha256": approved_entry.source_fragment_sha256,
        }
        frozen_assets = (("approved_composite", approved_path),)

    source_policy = (
        "shared"
        if str(config.get("asset_scope") or "").strip().casefold() == "shared"
        else "exact"
    )
    spec = reference_figure_component_spec(
        reference_id=reference_id,
        accessibility_label=str(image.get("alt") or reference_id),
        caption_mode="embedded" if config.get("captions_embedded") else "live",
        captions=tuple(labels),
        adjacent_copy=adjacent_copy,
        source_art_ref=str(image.get("src") or ""),
        source_art_locale_policy=source_policy,
        source_fragment_sha256=source_hash,
        source_ref=f"{source_path}#reference-{reference_id}",
        language=language,
        image_key=str(config.get("image_key") or ""),
        web_replace_key=str(config.get("web_replace_key") or ""),
        caption_layout=str(config.get("caption_layout") or "equal"),
        approved_composite=approved,
        metadata={
            "capture_following_lines": capture_lines,
            "captions_embedded": bool(config.get("captions_embedded")),
            "captions_origin": "configured" if configured_captions else "carrier",
            "composite_locale": str(composite_locale or ""),
        },
    )
    owned = [image]
    if adjacent is not None and adjacent_position == "before":
        owned.insert(0, adjacent)
    if adjacent is not None and adjacent_position == "after":
        owned.append(adjacent)
    if label_block is not None:
        owned.append(label_block)
    return spec, tuple(owned), (("source_art", image),), frozen_assets


__all__ = ["parse_reference_figure_html"]
