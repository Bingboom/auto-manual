"""Bind fresh PDF text regions to the existing Inbox/Overview/Operation slots.

The book supplies native PDF blocks, approved corrections and frozen renderer
contracts. All artwork is supplied separately by the governed-asset resolver;
this module never crops images or reads text from historical screenshot assets.
"""
from __future__ import annotations

from collections.abc import Mapping
from html import escape
import re
from typing import Any

from tools.component_specs.inbox import inbox_component_spec
from tools.component_specs.operation import operation_component_spec
from tools.component_specs.overview import overview_component_spec
from tools.frozen_ai_flow import node, paragraph, table, text
from tools.manual_ir.components import component_flow_node


MEDIA_ASSET_KEYS = (
    "inbox.main", "inbox.cable", "inbox.manual", "overview.front", "overview.right",
    "operation.main-power", "operation.ac-output", "operation.dc-usb-output",
    "operation.energy-saving", "operation.led-light",
)
# Coordinates are native PDF points. Selection/consumption uses the original
# block's top-left point, so a multiline block crossing a boundary stays intact.
_PANELS = (
    ("main-power", 0, (140, 75, 350, 190)),
    ("ac-output", 0, (25, 280, 350, 380)),
    ("dc-usb-output", 1, (25, 50, 350, 125)),
    ("energy-saving", 2, (220, 75, 345, 145)),
    ("led-light", 2, (25, 215, 345, 340)),
)
_CALLOUTS = {
    "front": {
        "power": (25, 100, 140, 120, True),
        "lcd": (240, 100, 350, 120, True),
        "dc12": (25, 120, 140, 151, False),
        "led_button": (240, 120, 350, 151, True),
        "usb_c_30": (25, 151, 140, 181, False),
        "led": (240, 151, 350, 169, True),
        "usb_c_100": (25, 181, 140, 219, False),
        "ac_power": (240, 169, 350, 195, True),
        "usb_a": (25, 219, 140, 260, False),
        "ac_output": (240, 195, 350, 245, False),
        "dc_usb": (25, 260, 140, 300, True),
        "total": (240, 250, 350, 300, False),
    },
    "right": {
        "handle": (25, 330, 145, 350, True),
        "dc_input": (25, 350, 145, 420, False),
        "ac_input": (240, 370, 350, 420, False),
    },
}


def _page(book: Any, section: str) -> int:
    return int(next(record for record in book.source["sections"]
                    if record["id"] == section)["physical_pages"][0])


def _clean(book: Any, value: str) -> str:
    value = " ".join(value.replace("\x1f", "⎓").split())
    return book.correct(value) if callable(getattr(book, "correct", None)) else value


def _blocks(book: Any, page: int, bbox: tuple) -> list[dict]:
    source = next(record for record in book.source["pages"] if record["physical_page"] == page)
    x0, y0, x1, y1 = bbox
    selected = [block for block in source["blocks_visual_order"]
                if x0 <= block["bbox"][0] < x1 and y0 <= block["bbox"][1] < y1
                and str(block["text"]).strip()]
    selected.sort(key=lambda block: (block["bbox"][1], block["bbox"][0]))
    if not selected:
        raise ValueError(f"{book.language}: PDF page {page} region {bbox} has no text")
    return selected


def _copy(book: Any, page: int, bbox: tuple) -> str:
    return _clean(book, " ".join(block["text"] for block in _blocks(book, page, bbox)))


def _asset(asset_refs: Mapping[str, Any], key: str) -> str:
    value = asset_refs[key]
    ref = str(value.get("asset_ref") or "") if isinstance(value, Mapping) else str(value)
    if not ref.strip():
        raise ValueError(f"governed media asset {key!r} has no asset_ref")
    return ref


def _image(ref: str, alt: str) -> dict:
    return node("image", source=ref, alt=alt)


def _cell(children: list[dict]) -> dict:
    return node("table_cell", children, header=False)


def _source_ref(book: Any, page: int, component: str) -> str:
    return f"{book.language}/pdf-page-{page}#{component}"


def _inbox(book: Any, assets: Mapping[str, Any]) -> dict:
    page = _page(book, "in_the_box")
    title = _copy(book, page, (25, 230, 350, 270))
    cards = []
    for key, left, right in (("main", 25, 135), ("cable", 135, 245), ("manual", 245, 350)):
        label = _copy(book, page, (left, 390, right, 425))
        cards.append({"image_ref": _asset(assets, f"inbox.{key}"), "label": label, "alt": label})
    tip_blocks = _blocks(book, page, (25, 450, 350, 490))
    if len(tip_blocks) == 1:
        tip_label, tip_body = tip_blocks[0]["text"].strip().split("\n", 1)
    else:
        tip_label = " ".join(b["text"] for b in tip_blocks if b["bbox"][0] < 80)
        tip_body = " ".join(b["text"] for b in tip_blocks if b["bbox"][0] >= 80)
    tip_label, tip_body = _clean(book, tip_label), _clean(book, tip_body)
    spec = inbox_component_spec(
        accessibility_label=title, cards=cards, tip_label=tip_label, tip_body=tip_body,
        language=book.language, source_ref=_source_ref(book, page, "inbox"),
        metadata={"physical_page": page, "source_region": [25, 280, 350, 490]},
    )
    card_table = table([[_cell([_image(c["image_ref"], c["alt"]), paragraph(c["label"])]) for c in cards]])
    tip_table = table([[_cell([paragraph(tip_label)]), _cell([paragraph(tip_body)])]])
    return component_flow_node(spec, carrier_flow=(card_table, tip_table), root=True)


def _overview(book: Any, assets: Mapping[str, Any]) -> dict:
    page = _page(book, "product_overview")
    title = _copy(book, page, (25, 25, 350, 55))
    views, carriers = [], []
    for geometry in book.overview_instance["views"]:
        view_id = geometry["id"]
        caption_box = (25, 60, 350, 90) if view_id == "front" else (25, 310, 350, 330)
        caption = _copy(book, page, caption_box)
        callouts = []
        for binding in geometry["callouts"]:
            callout_id = binding["id"]
            *box, label_only = _CALLOUTS[view_id][callout_id]
            blocks = _blocks(book, page, tuple(box))
            values = [_clean(book, block["text"]) for block in blocks]
            label, body = (" ".join(values), []) if label_only else (values[0], values[1:])
            if not label_only and not body:
                raise ValueError(f"{book.language}: overview {callout_id} lost its PDF specification")
            callouts.append({"id": callout_id, "label": label, "body": body})
        ref = _asset(assets, f"overview.{view_id}")
        views.append({"id": view_id, "title": caption, "image_ref": ref,
                      "alt": caption, "callouts": callouts})
        rows = [[_cell([paragraph(item["label"]), *[paragraph(v) for v in item["body"]]])]
                for item in callouts]
        caption_node = node("heading", [text(caption)], level=2)
        panel = getattr(book, "overview_finished_panels", {}).get(view_id, {})
        if panel.get("captions_embedded") is True:
            caption_node["presentation"] = {"html": {"attributes": {"hidden": "", "style": "display:none"}}}
        carriers.append(node("section", [caption_node, _image(ref, caption), table(rows)]))
    spec = overview_component_spec(
        accessibility_label=title, views=views, geometry_ref=book.overview_instance["instance_id"],
        source_ref=_source_ref(book, page, "overview"), language=book.language,
        metadata={"physical_page": page, "source_region": [25, 60, 350, 420]},
    )
    return component_flow_node(spec, carrier_flow=carriers, root=True)


def media_section(book: Any, section: str, asset_refs: Mapping[str, Any]) -> list[dict] | None:
    """Return complete Inbox/Overview chapter bodies, excluding the outer H2.

    ``book`` provides ``source.pages/sections``, ``language``, ``correct`` and
    ``overview_instance``. Other sections return None for the caller to handle.
    Use ``operation_panels`` to interleave operations with the remaining prose.
    """
    if section == "in_the_box":
        return [_inbox(book, asset_refs)]
    if section == "product_overview":
        return [_overview(book, asset_refs)]
    return None


def consumed_media_regions(book: Any) -> list[dict]:
    """Return the exact PDF regions owned by this adapter (headings excluded)."""
    start = _page(book, "operations")
    return [
        {"section": "in_the_box", "physical_page": _page(book, "in_the_box"),
         "consume_bbox": [25, 280, 350, 490]},
        {"section": "product_overview", "physical_page": _page(book, "product_overview"),
         "consume_bbox": [25, 60, 350, 420]},
        *[{"section": "operations", "operation_id": identity, "physical_page": start + offset,
           "consume_bbox": list(box)} for identity, offset, box in _PANELS],
    ]


def _line(value: str, *, bold: bool = False) -> dict:
    children = [node("strong", [text(value)])] if bold else [text(value)]
    return node("group", children, role="container",
                presentation={"html": {"attributes": {"class": "line"}}})


def _step(identity: str, values: list[str]) -> dict:
    roles = ("label", "instruction") if len(values) == 2 else ("summary",)
    return {"id": identity, "parts": [{"role": role, "text": value,
            "html": f"<strong>{escape(value)}</strong>" if role == "label" else escape(value)}
            for role, value in zip(roles, values, strict=True)]}


def _panel_copy(book: Any, identity: str, page: int) -> dict:
    result: dict[str, Any] = {"prerequisite": "", "supporting_copy": [],
                              "mode_label": "", "sos_label": ""}
    if identity in {"main-power", "ac-output", "dc-usb-output"}:
        ranges = {"main-power": (75, 103, 127), "ac-output": (320, 348, 375),
                  "dc-usb-output": (75, 96, 120)}
        top, middle, bottom = ranges[identity]
        steps = []
        for step_id, y0, y1 in (("on", top, middle), ("off", middle, bottom)):
            values = [_clean(book, b["text"]) for b in _blocks(book, page, (250, y0, 350, y1))]
            if len(values) != 2:
                raise ValueError(f"{book.language}: {identity}/{step_id} requires label and action")
            steps.append(_step(step_id, values))
        result["steps"] = steps
        if identity == "main-power":
            support = _blocks(book, page, (140, 140, 350, 195))
            lines = [line for b in support for line in b["text"].splitlines() if line.strip()]
            # PDF wrapping differs across locales. Keep the standby sentence
            # and the App note intact instead of treating the final wrapped
            # line (sometimes only "Jackery-app.") as a whole semantic note.
            sentences = re.split(r"(?<=\.)\s+", " ".join(lines[1:]).strip(), maxsplit=1)
            if len(sentences) != 2:
                raise ValueError(f"{book.language}: standby copy requires its sentence and App note")
            result["supporting_copy"] = [_clean(book, value) for value in (lines[0], *sentences)]
        else:
            bounds = (25, 280, 350, 310) if identity == "ac-output" else (25, 45, 350, 70)
            result["prerequisite"] = _copy(book, page, bounds)
    elif identity == "energy-saving":
        blocks = _blocks(book, page, (220, 110, 345, 145))
        lines = [line.strip() for b in blocks for line in b["text"].splitlines() if line.strip()]
        # The diagram's standalone 3s glyph is repeated by the live instruction.
        instruction = re.sub(r"^3\s*[sс]\s*", "", " ".join(lines[:-1]))
        button_label = _copy(book, page, (280, 75, 345, 100))
        result["steps"] = [_step("toggle", [button_label, _clean(book, instruction)])]
        result["mode_label"] = _clean(book, lines[-1])
    else:
        result["prerequisite"] = _copy(book, page, (25, 215, 345, 245))
        result["steps"] = [_step(step_id, [_copy(book, page, (250, y0, 345, y1))])
                           for step_id, y0, y1 in (("light", 255, 288), ("sos", 288, 312), ("off", 312, 340))]
        # The button caption is localized in the native master. Keep it as
        # live copy even when the shared artwork has the fixed LIGHT marking.
        light_label = _copy(book, page, (140, 280, 210, 310))
        light_instruction = result["steps"][0]["parts"][0]["text"]
        result["steps"][0] = _step("light", [f"{light_label}: {light_instruction}"])
        glyphs = _copy(book, page, (210, 288, 250, 312))
        result["sos_label"] = re.sub(r"^2\s*", "", glyphs)
    return result


def operation_panels(book: Any, asset_refs: Mapping[str, Any]) -> list[dict]:
    """Return positioned component events; caller retains all unconsumed copy.

    Each event has ``physical_page``, ``y``, ``consume_bbox`` and a root ``node``.
    Consume only blocks whose top-left lies inside that half-open rectangle.
    Surrounding headings, cautions, paragraphs and tables are not consumed.
    The public renderer needs this same ``book.contract`` and a target-scoped
    source path; a path outside its figure_targets deliberately returns carrier.
    """
    start = _page(book, "operations")
    presentations = {p["id"]: p for p in book.contract["operations"]["figures"]}
    events = []
    for identity, offset, box in _PANELS:
        page, presentation = start + offset, presentations[identity]
        copy = _panel_copy(book, identity, page)
        ref = _asset(asset_refs, f"operation.{identity}")
        prerequisite = copy["prerequisite"]
        supporting = copy["supporting_copy"]
        if bool(prerequisite) != bool(presentation.get("capture_prerequisite")):
            raise ValueError(f"{identity}: PDF prerequisite disagrees with frozen presentation")
        if len(supporting) != int(presentation.get("capture_following_lines", 0)):
            raise ValueError(f"{identity}: PDF supporting copy disagrees with frozen presentation")
        label = " ".join(part["text"] for step in copy["steps"] for part in step["parts"])
        metadata = {"physical_page": page, "source_region": list(box)}
        if presentation.get("presentation_mode"):
            metadata["presentation_mode"] = presentation["presentation_mode"]
        spec = operation_component_spec(
            operation_id=identity, accessibility_label=label, layout=presentation["layout"],
            steps=copy["steps"], prerequisite_html=f"<p>{escape(prerequisite)}</p>" if prerequisite else "",
            supporting_copy=[escape(value) for value in supporting], artwork_ref=ref,
            source_ref=_source_ref(book, page, identity), language=book.language,
            mode_label=copy["mode_label"], sos_label=copy["sos_label"], metadata=metadata,
        )
        lines = [_line(part["text"], bold=part["role"] == "label")
                 for step in copy["steps"] for part in step["parts"]]
        carrier = ([paragraph(prerequisite)] if prerequisite else []) + [
            _image(ref, label), node("group", lines, role="container",
                                     presentation={"html": {"attributes": {"class": "line-block"}}}),
        ]
        events.append({"physical_page": page, "y": box[1], "consume_bbox": list(box),
                       "node": component_flow_node(spec, carrier_flow=carrier, root=True)})
    return events


__all__ = ["MEDIA_ASSET_KEYS", "consumed_media_regions", "media_section", "operation_panels"]
