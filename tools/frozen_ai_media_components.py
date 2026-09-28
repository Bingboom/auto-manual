"""Map frozen source artwork and App copy into existing shared IR components.

Artwork refs and hashes are supplied by the package assembler. This adapter
neither reads the historical HTML nor modifies or subdivides approved images.
The caller owns the outer App chapter heading.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from html import escape
import re
from typing import Any

from bs4 import BeautifulSoup

from tools.component_specs.app import app_inline_control_component_spec
from tools.component_specs.reference_figure import reference_figure_component_spec
from tools.frozen_ai_flow import callout, root
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import FLOW_V2_SCHEMA_VERSION, flow_nodes_to_html
from tools.web_composite_hashing import reference_source_fragment_sha256


def _text(value: str) -> dict[str, Any]:
    return {"kind": "text", "text": value}


def _block(kind: str, value: str, **fields: Any) -> dict[str, Any]:
    return {
        "schema_version": FLOW_V2_SCHEMA_VERSION,
        "kind": kind,
        **fields,
        "children": [_text(value)],
    }


def _normalized(value: str) -> str:
    # The Dutch extraction escaped its quotation marks twice. These slashes
    # are serialization residue, not part of the approved authored copy.
    return re.sub(r'\\+"', '"', " ".join(value.split()))


def _prose(value: str) -> list[dict[str, Any]]:
    lead, *items = _normalized(value).split("•")
    nodes = [_block("paragraph", lead.strip())] if lead.strip() else []
    if items:
        nodes.append({
            "schema_version": FLOW_V2_SCHEMA_VERSION,
            "kind": "list",
            "ordered": False,
            "children": [
                {"kind": "list_item", "children": [_text(item.strip())]}
                for item in items if item.strip()
            ],
        })
    return nodes


def figure_node(
    *,
    asset_ref: str,
    content_sha256: str,
    reference_id: str,
    alt: str,
    language: str,
    source_ref: str,
) -> dict[str, Any]:
    """Bind an unchanged approved crop as both semantic and display artwork.

    The semantic source hash uses the shared public hash helper and exactly
    the wrapper/image attributes produced by the public ReferenceFigure
    transform. Its normalized image identity survives asset-path rebasing.
    """
    image = {
        "schema_version": FLOW_V2_SCHEMA_VERSION,
        "kind": "image", "source": asset_ref, "alt": alt,
    }
    semantic = BeautifulSoup("", "html.parser")
    wrapper = semantic.new_tag("div", attrs={
        "class": "hb-reference-semantic",
        "data-reference-id": f"{reference_id}.semantic",
    })
    semantic_image = BeautifulSoup(flow_nodes_to_html((image,)), "html.parser").img
    semantic_image["class"] = ["hb-reference-art"]
    wrapper.append(semantic_image)
    source_hash = reference_source_fragment_sha256(
        component={"id": reference_id, "image_key": reference_id,
                   "captions_embedded": True},
        semantic=wrapper, caption_labels=[], composite_locale=language,
    )
    spec = reference_figure_component_spec(
        reference_id=reference_id, accessibility_label=alt,
        caption_mode="embedded", captions=(), adjacent_copy=None,
        source_art_ref=asset_ref, source_art_locale_policy="exact",
        source_fragment_sha256=source_hash, source_ref=source_ref,
        language=language, image_key=reference_id,
        web_replace_key=f"reference.{reference_id}",
        approved_composite={
            "asset_key": f"frozen-source/{reference_id}",
            "asset_ref": asset_ref, "locale": language,
            "content_sha256": content_sha256,
            "source_fragment_sha256": source_hash,
        },
        metadata={"artwork_origin": "unchanged-approved-source-crop"},
    )
    return component_flow_node(spec, carrier_flow=(image,), root=True)


def _inline_add_device(raw: str, *, language: str, source_ref: str) -> dict[str, Any]:
    # The circled plus is vector artwork absent from the extracted text. The
    # frozen record explicitly identifies its whitespace gap for recovery.
    parts = re.split(r"\s{5,}", raw)
    if len(parts) != 2:
        raise ValueError(f"{source_ref}: App add-device control gap is ambiguous")
    before, after = (_normalized(part) for part in parts)
    if not before or not after:
        raise ValueError(f"{source_ref}: App add-device control copy is incomplete")
    paragraph = {
        "schema_version": FLOW_V2_SCHEMA_VERSION, "kind": "paragraph",
        "children": [_text(before + " "),
                     {"kind": "strong", "children": [_text("+")]},
                     _text(" " + after)],
    }
    spec = app_inline_control_component_spec(
        accessibility_label="+",
        paragraph_html=f"<p>{escape(before)} <strong>+</strong> {escape(after)}</p>",
        paragraph_text=f"{before} + {after}",
        source_ref=source_ref, language=language,
        metadata={"visual_recovery": "source-vector-plus-control"},
    )
    return component_flow_node(spec, carrier_flow=(paragraph,), root=True)


def app_nodes(
    locale_record: Mapping[str, Any],
    packaged_figures_map: Mapping[str, Mapping[str, Any]],
    *,
    language: str,
    source_ref: str,
) -> tuple[dict[str, Any], ...]:
    """Preserve the complete frozen App chapter as ordered v2 flow roots.

    Figure entries must provide ``asset_ref`` and ``sha256``. The combined
    download badges/QR crop stays a ReferenceFigure: the registered App
    download layout requires separate governed art, absent from this source.
    """
    blocks = locale_record["blocks"]
    result: list[dict[str, Any]] = []

    def add_block(name: str, *, heading: bool = False) -> None:
        raw = str(blocks[name]["raw_text"])
        if name == "step_2_1":
            result.append(_inline_add_device(
                raw, language=language, source_ref=f"{source_ref}#step_2_1",
            ))
        elif heading:
            result.append(_block("heading", _normalized(raw), level=3))
        else:
            result.extend(_prose(raw))

    def add_figure(slug: str) -> None:
        record = packaged_figures_map[slug]
        node = figure_node(
            asset_ref=str(record["asset_ref"]), content_sha256=str(record["sha256"]),
            reference_id=slug, alt=f"{blocks['title']['text']}: {slug.replace('_', ' ')}",
            language=language, source_ref=f"{source_ref}#{slug}",
        )
        if slug == "app_qr_and_badges":
            node["component_spec"]["metadata"]["source_artwork_layout"] = "combined-store-badges-and-qr"
        result.append(node)

    def add_notice(prefix: str, variant: str) -> None:
        body = _prose(str(blocks[f"{prefix}_body"]["raw_text"]))
        # Root markers belong to document blocks, not carrier children.
        for item in body:
            item.pop("schema_version", None)
        result.append(root(callout(
            _normalized(str(blocks[f"{prefix}_label"]["raw_text"])), body,
            variant=variant, language=language, source_ref=f"{source_ref}#{prefix}",
        )))

    add_block("download_heading", heading=True)
    add_block("download_store")
    add_block("download_qr")
    add_figure("app_qr_and_badges")
    add_block("add_heading", heading=True)
    add_block("step_2_1")
    add_block("step_2_2")
    add_figure("app_add_device")
    add_figure("app_control")
    add_block("step_2_3")
    add_notice("bound_note", "note")
    add_block("step_2_4")
    add_notice("wifi_note", "note")
    add_block("step_2_5")
    add_figure("app_pairing")
    add_block("screenshots_note")
    add_notice("bluetooth_caution", "caution")
    unbind_heading, unbind_body = str(blocks["unbind"]["raw_text"]).split("\n", 1)
    result.append(_block("heading", _normalized(unbind_heading), level=3))
    result.extend(_prose(unbind_body))
    add_block("notes_heading", heading=True)
    for name in ("enable", "disable", "reset"):
        add_block(name)
    return tuple(deepcopy(result))


__all__ = ["app_nodes", "figure_node"]
