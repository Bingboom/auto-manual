"""Neutral source-flow construction for positioned, frozen manual text."""
from __future__ import annotations

from copy import deepcopy
import re

from tools.component_specs.adapters import web_callout_classes
from tools.component_specs.callout import callout_component_spec
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import FLOW_V2_SCHEMA_VERSION


def node(kind: str, children=(), **fields) -> dict:
    result = {"kind": kind, **fields}
    if kind not in {"text", "image", "component", "line_break"}:
        result["children"] = list(children)
    return result


def text(value: str) -> dict:
    return node("text", text=value)


def paragraph(value: str) -> dict:
    return node("paragraph", [text(value)])


def heading(value: str, *, level: int = 3, anchor: str | None = None) -> dict:
    return node("heading", [text(value)], level=level, **({"anchor": anchor} if anchor else {}))


def root(value: dict) -> dict:
    return {**deepcopy(value), "schema_version": FLOW_V2_SCHEMA_VERSION}


def squash(raw: str) -> str:
    raw = re.sub(r"jack-\s*\n\s*ery\.com", "jackery.com", raw, flags=re.I)
    return " ".join(raw.split())


def is_heading(raw: str) -> bool:
    value = squash(raw)
    letters = "".join(char for char in value if char.isalpha())
    return bool(letters) and letters == letters.upper() and len(value) <= 110


def prose(raw: str) -> list[dict]:
    value = squash(raw)
    if not value or re.fullmatch(r"\d{1,3}", value):
        return []
    if "•" in value:
        lead, *items = value.split("•")
        result = [paragraph(lead.strip())] if lead.strip() else []
        result.append(node("list", [node("list_item", [text(item.strip())])
                                     for item in items if item.strip()], ordered=False))
        return result
    return [heading(value) if is_heading(value) else paragraph(value)]


def flow_text(value: dict, *, separator: str = " ") -> str:
    if value.get("kind") == "text":
        return value["text"]
    return separator.join(filter(None, (flow_text(child, separator=separator)
                                       for child in value.get("children", []))))


def table(rows: list[list[dict]], *, css_class: str = "manual-table") -> dict:
    return node("table", [node("table_body", [node("table_row", row) for row in rows])],
                presentation={"html": {"attributes": {"class": css_class}}})


def cell(value: str, *, header=False, **fields) -> dict:
    return node("table_cell", [text(value)], header=header, **fields)


def scroll_table(rows: list[list[dict]]) -> dict:
    """Use the shared Web table container, including its mobile scroll rule."""
    return node("group", [table(rows)], role="container",
                presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}})


def callout(label: str, body: list[dict], *, variant: str, language: str, source_ref: str) -> dict:
    """Bind the source's exact label/body to the existing shared carrier contract."""
    def leaves(item):
        if item.get("kind") == "text":
            return [item["text"]]
        return [part for child in item.get("children", []) for part in leaves(child)]
    items = [flow_text(item) for block in body if block["kind"] == "list"
             for item in block["children"]]
    spec = callout_component_spec(label=label, body="\n".join(part for b in body for part in leaves(b)),
                                  items=items, variant=variant, language=language, source_ref=source_ref)
    classes = web_callout_classes(spec)
    def attributes(css):
        return {"html": {"attributes": {"class": css}}}
    carrier = table([[node("table_cell", [text(label)], header=False,
                           presentation=attributes("manual-callout-label")),
                      node("table_cell", body, header=False,
                           presentation=attributes("manual-callout-body"))]],
                    css_class=f"manual-callout-table {classes['table']}")
    return component_flow_node(spec, carrier_flow=[carrier])
