"""Fresh PDF App copy bound to shared App components and independent assets."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from html import escape
import re
from typing import Any

from bs4 import BeautifulSoup

from tools.component_specs.app import (
    app_add_device_component_spec,
    app_download_component_spec,
    app_inline_control_component_spec,
    resolve_app_control_label_roles,
)
from tools.component_specs.reference_figure import reference_figure_component_spec
from tools.frozen_ai_flow import callout, heading, node, paragraph, root, text
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import flow_nodes_to_html
from tools.web_composite_hashing import reference_source_fragment_sha256


APP_ASSET_KEYS = ("app.download", "app.store", "app.qr", "app.phone", "app.control", "app.result")


def artwork_node(asset_ref: str, reference_id: str, language: str, source_ref: str,
                 *, accessibility_label: str | None = None,
                 captions: Sequence[str] = ()) -> dict:
    """Bind governed standalone artwork with no invented composite/caption.

    The shared source-fragment hash normalizes image refs, so packaging may
    rebase the ref without invalidating semantic provenance. The package owns
    the actual artwork-byte hash and verification.
    """
    label = accessibility_label or reference_id
    carrier = root(_image(asset_ref, label))
    soup = BeautifulSoup("", "html.parser")
    semantic = soup.new_tag("div", attrs={"class": "hb-reference-semantic",
                                          "data-reference-id": f"{reference_id}.semantic"})
    image = BeautifulSoup(flow_nodes_to_html((carrier,)), "html.parser").img
    image["class"] = ["hb-reference-art"]
    semantic.append(image)
    caption_labels = [str(value).strip() for value in captions]
    if any(not value for value in caption_labels):
        raise ValueError(f"{source_ref}: artwork captions cannot be empty")
    digest = reference_source_fragment_sha256(
        component={"id": reference_id, "image_key": reference_id, "captions_embedded": False},
        semantic=semantic, caption_labels=caption_labels, composite_locale=None,
    )
    spec = reference_figure_component_spec(
        reference_id=reference_id, accessibility_label=label,
        caption_mode="live" if caption_labels else "none",
        captions=tuple({"html": escape(value), "text": value} for value in caption_labels),
        adjacent_copy=None, source_art_ref=asset_ref, source_art_locale_policy="shared",
        source_fragment_sha256=digest, source_ref=source_ref, language=language,
        image_key=reference_id,
        metadata={"captions_origin": "configured"} if caption_labels else None,
    )
    return component_flow_node(spec, carrier_flow=(carrier,), root=True)


def _clean(book: Any, value: str) -> str:
    value = re.sub(r'\\+"', '"', " ".join(value.split()))
    return book.correct(value) if callable(getattr(book, "correct", None)) else value


def _asset(assets: Mapping[str, Any], key: str) -> str:
    value = assets[key]
    ref = str(value.get("asset_ref") or "") if isinstance(value, Mapping) else str(value)
    if not ref.strip():
        raise ValueError(f"App governed asset {key!r} has no asset_ref")
    return ref


def _image(ref: str, label: str) -> dict:
    return node("image", source=ref, alt=label)


def _prose(book: Any, raw: str) -> list[dict]:
    lead, *items = _clean(book, raw).split("•")
    body = [paragraph(lead.strip())] if lead.strip() else []
    if items:
        body.append(node("list", [node("list_item", [text(item.strip())])
                                   for item in items if item.strip()], ordered=False))
    return body


def _control_labels(book: Any, page: int) -> list[dict]:
    """Recover only the three native labels, including merged PDF columns."""
    record = next(p for p in book.source["pages"] if p["physical_page"] == page)
    blocks = [b for b in record["blocks_visual_order"] if 400 <= b["bbox"][1] < 450]
    blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
    main = [b["text"] for b in blocks if b["bbox"][1] < 425 and b["bbox"][0] < 150]
    lower = [b for b in blocks if b["bbox"][1] >= 425]
    if not main or not lower:
        raise ValueError(f"{book.language}: PDF App control labels are incomplete")
    merged = [b for b in lower if b["bbox"][0] < 150 and b["bbox"][2] > 250]
    if merged:
        if len(merged) != 1 or len(lower) != 1:
            raise ValueError(f"{book.language}: merged App control columns are ambiguous")
        labels = [line for line in merged[0]["text"].splitlines() if line.strip()]
        if len(labels) != 2:
            raise ValueError(f"{book.language}: merged App control needs two complete labels")
        dc, ac = labels
    else:
        dc = " ".join(b["text"] for b in lower if b["bbox"][0] < 150)
        ac = " ".join(b["text"] for b in lower if b["bbox"][0] >= 250)
    values = [_clean(book, " ".join(main)), _clean(book, dc), _clean(book, ac)]
    if not all(values):
        raise ValueError(f"{book.language}: PDF App control label is empty")
    roles = resolve_app_control_label_roles(values, ("main-power", "dc-usb", "ac-power"),
                                           owner=f"{book.language}/pdf-page-{page}/App")
    return [{"role": role, "text": value, "html": escape(value)}
            for role, value in zip(roles, values, strict=True)]


def _native_step_captions(
    book: Any, blocks: Mapping, page: int, steps: Sequence[str]
) -> list[dict[str, str]]:
    """Verify a source-page number block against the existing App steps.

    PDF text order is not visual order on the three-phone result page: its
    single text block reads 2.5 / 2.3 / 2.4. The already identified step
    records establish the left-to-right sequence after the number set is
    confirmed against the native page block.
    """
    for number in steps:
        key = "step_" + number.replace(".", "_")
        step = blocks[key]
        if not re.match(rf"^{re.escape(number)}(?=\s|$)", step["raw_text"].strip()):
            raise ValueError(f"{book.language}: {key} does not start with {number}")
    record = next(p for p in book.source["pages"] if p["physical_page"] == page)
    matches = []
    for block in record["blocks_visual_order"]:
        lines = [line.strip() for line in block["text"].splitlines() if line.strip()]
        if len(lines) == len(steps) and set(lines) == set(steps):
            matches.append(block)
    if len(matches) != 1:
        raise ValueError(
            f"{book.language}/pdf-page-{page}: expected one native number block "
            f"with {list(steps)!r}; found {len(matches)}"
        )
    return [
        {"role": "step-" + number.replace(".", "-"), "text": number, "html": number}
        for number in steps
    ]


def _download(book: Any, blocks: Mapping, refs: Mapping[str, str], source_ref: str) -> dict:
    columns = [{"role": role, "text": _clean(book, blocks[f"download_{role}"]["raw_text"])}
               for role in ("store", "qr")]
    for column in columns:
        column["html"] = escape(column["text"])
    label = _clean(book, blocks["download_heading"]["raw_text"])
    spec = app_download_component_spec(
        accessibility_label=label, columns=columns, source_art_ref=refs["app.download"],
        store_art_ref=refs["app.store"], qr_art_ref=refs["app.qr"],
        source_ref=source_ref + "#download", language=book.language,
        metadata={"source_kind": "native-pdf-app-copy"},
    )
    carrier = [_image(refs["app.download"], label), *[paragraph(column["text"]) for column in columns]]
    return component_flow_node(spec, carrier_flow=carrier, root=True)


def _plus(book: Any, raw: str, source_ref: str) -> dict:
    parts = re.split(r"\s{5,}", raw)
    if len(parts) != 2 or not all(part.strip() for part in parts):
        raise ValueError(f"{source_ref}: PDF add-device vector-control gap is ambiguous")
    before, after = (_clean(book, part) for part in parts)
    carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    spec = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"<p>{escape(before)} <strong>+</strong> {escape(after)}</p>",
        paragraph_text=f"{before} + {after}", source_ref=source_ref + "#add-button", language=book.language,
        metadata={"visual_recovery": "native-pdf-vector-plus-control"},
    )
    return component_flow_node(spec, carrier_flow=(carrier,), root=True)


def _add_device(book: Any, blocks: Mapping, refs: Mapping[str, str], source_ref: str) -> dict:
    page = int(blocks["step_2_1"]["physical_page"])
    labels = _control_labels(book, page)
    captions = _native_step_captions(book, blocks, page, ("2.1", "2.2"))
    title = _clean(book, blocks["add_heading"]["raw_text"])
    spec = app_add_device_component_spec(
        accessibility_label=title, reference_id="app-add-device", labels=labels,
        source_art_ref=refs["app.phone"], phone_art_ref=refs["app.phone"], control_art_ref=refs["app.control"],
        source_ref=source_ref + "#add-device", language=book.language,
        step_captions=captions,
        metadata={"physical_page": page, "source_label_region": [25, 400, 345, 450]},
    )
    lines = [node("group", [text(label["text"])], role="container",
                  presentation={"html": {"attributes": {"class": "line"}}}) for label in labels]
    carrier = [_image(refs["app.phone"], title),
               node("group", lines, role="container",
                    presentation={"html": {"attributes": {"class": "line-block"}}})]
    return component_flow_node(spec, carrier_flow=carrier, root=True)


def app_section(book: Any, asset_refs: Mapping[str, Any]) -> list[dict]:
    """Return the whole App chapter body, with no duplicate outer H2/title.

    ``book.records['app_sections']`` must be freshly read from the native PDF.
    ``book.source.pages`` provides the original coordinate-bearing text blocks
    for the three control labels. ``book.correct`` applies approved errata.
    Six external asset refs supply the download source, stores, QR, phone UI,
    text-free control art and result UI; this adapter never manufactures art.
    """
    blocks = book.records["app_sections"]["blocks"]
    refs = {key: _asset(asset_refs, key) for key in APP_ASSET_KEYS}
    source_ref = f"{book.language}/pdf-page-{blocks['title']['physical_page']}/app"
    result = []

    def add_heading(key: str) -> None:
        result.append(root(heading(_clean(book, blocks[key]["raw_text"]))))

    def add_prose(key: str) -> None:
        result.extend(root(value) for value in _prose(book, blocks[key]["raw_text"]))

    def add_notice(prefix: str, variant: str) -> None:
        result.append(root(callout(
            _clean(book, blocks[f"{prefix}_label"]["raw_text"]),
            _prose(book, blocks[f"{prefix}_body"]["raw_text"]),
            variant=variant, language=book.language, source_ref=f"{source_ref}#{prefix}",
        )))

    add_heading("download_heading")
    result.append(_download(book, blocks, refs, source_ref))
    add_heading("add_heading")
    result.append(_plus(book, blocks["step_2_1"]["raw_text"], source_ref))
    add_prose("step_2_2")
    result.append(_add_device(book, blocks, refs, source_ref))
    add_prose("step_2_3")
    add_notice("bound_note", "note")
    add_prose("step_2_4")
    add_notice("wifi_note", "note")
    add_prose("step_2_5")
    result_page = int(blocks["step_2_5"]["physical_page"])
    result_captions = _native_step_captions(
        book, blocks, result_page, ("2.3", "2.4", "2.5")
    )
    result.append(artwork_node(
        refs["app.result"], "app-connect-result", book.language,
        source_ref + "#connect-result",
        accessibility_label=_clean(book, blocks["screenshots_note"]["raw_text"]),
        captions=[item["text"] for item in result_captions],
    ))
    add_prose("screenshots_note")
    add_notice("bluetooth_caution", "caution")
    for key, level in (("unbind", 3), ("enable", 4), ("disable", 4), ("reset", 4)):
        if key == "enable":
            add_heading("notes_heading")
        title, separator, body = blocks[key]["raw_text"].partition("\n")
        if not separator or not body.strip():
            raise ValueError(f"{source_ref}: {key} requires a heading and native body")
        result.append(root(heading(_clean(book, title), level=level)))
        result.extend(root(value) for value in _prose(book, body))
    return result


__all__ = ["APP_ASSET_KEYS", "app_section", "artwork_node"]
