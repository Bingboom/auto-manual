"""Adapt frozen extracted table records to registered components and neutral flow.

Inputs are already selected locale/table records; assets are package-relative
refs supplied by the caller. No historical renderer, source HTML, or filesystem
reads are involved. Only specification and warranty helpers emit headings:
specifications own their four group headings; warranty owns its subsection
headings while the caller owns the outer chapter title.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from html import escape
import re
from typing import Any

from tools.component_specs.auto_resume import auto_resume_component_spec
from tools.component_specs.lcd_mode import lcd_mode_component_spec
from tools.component_specs.manual_tables import (
    symbol_icon_component_spec,
    symbol_signal_component_spec,
    troubleshooting_component_spec,
)
from tools.component_specs.spec_table import spec_table_component_spec
from tools.component_specs.warranty import (
    warranty_lead_component_spec,
    warranty_section_component_spec,
    warranty_years_component_spec,
)
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import FLOW_V2_SCHEMA_VERSION


def _pair(key: str, text: str) -> dict[str, str]:
    return {f"{key}_text": text, f"{key}_html": escape(text)}


def _headers(headings: Sequence[str]) -> list[dict[str, str]]:
    return [_pair("content", heading) for heading in headings]


def _measures_pair(value: str) -> dict[str, str]:
    """Separate a complete numbered sequence, never decimal measurements."""
    starts = list(re.finditer(r"(?<!\S)(\d+)\.\s+", value))
    if (len(starts) < 2 or starts[0].start() != 0
            or [int(m[1]) for m in starts] != list(range(1, len(starts) + 1))):
        return _pair("measures", value)
    offsets = [m.start() for m in starts] + [len(value)]
    parts = [value[a:b].rstrip() for a, b in zip(offsets, offsets[1:])]
    return {"measures_text": value, "measures_html": "<br />".join(escape(p) for p in parts)}


def _text(text: str) -> dict[str, Any]:
    return {"kind": "text", "text": text}


def _heading(title: str, level: int = 3) -> dict[str, Any]:
    return {
        "schema_version": FLOW_V2_SCHEMA_VERSION,
        "kind": "heading", "level": level, "children": [_text(title)],
    }


def symbol_signal_flow(
    record: Mapping[str, Any], *, headings: Sequence[str],
    accessibility_label: str, source_ref: str, language: str,
) -> list[dict[str, Any]]:
    """Map the locale's signal rows; headings must contain two source labels."""
    spec = symbol_signal_component_spec(
        accessibility_label=accessibility_label, headers=_headers(headings),
        rows=[{"label": row["label"], **_pair("meaning", row["meaning"])}
              for row in record["rows"]],
        source_ref=source_ref, language=language,
    )
    return [component_flow_node(spec, root=True)]


def symbol_pictogram_flow(
    record: Mapping[str, Any], *, headings: Sequence[str],
    accessibility_label: str, icon_refs: Sequence[str],
    source_ref: str, language: str,
) -> list[dict[str, Any]]:
    """Preserve source panel/row order and bind one supplied icon per record."""
    rows = record["pictograms"]
    if len(headings) != 2 or len(icon_refs) != len(rows):
        raise ValueError("pictograms require two headers and one icon per row")
    columns = sorted({row["meaning_bbox"][0] for row in rows})
    if len(columns) != 2:
        raise ValueError("pictograms require two source panels")
    panels = [
        [{"asset_index": index, "icon_alt": row["meaning"],
          **_pair("meaning", row["meaning"])}
         for index, row in enumerate(rows) if row["meaning_bbox"][0] == column]
        for column in columns
    ]
    spec = symbol_icon_component_spec(
        accessibility_label=accessibility_label,
        headers=_headers([*headings, *headings]), panels=panels,
        icon_refs=icon_refs, source_ref=source_ref, language=language,
        icon_locale_policy="exact",
    )
    return [component_flow_node(spec, root=True)]


def troubleshooting_flow(
    record: Mapping[str, Any], *, headings: Sequence[str],
    source_ref: str, language: str,
) -> list[dict[str, Any]]:
    """Map the selected troubleshooting table without rewriting its measures."""
    spec = troubleshooting_component_spec(
        headers=_headers(headings),
        rows=[{**_pair("code", row["code"]), **_measures_pair(row["action"])}
              for row in record["rows"]],
        source_ref=source_ref, language=language,
    )
    return [component_flow_node(spec, root=True)]


def _spec_carrier(title: str, rows: Sequence[Sequence[str]]) -> list[dict[str, Any]]:
    # These are the existing renderer's carrier hooks, not a new presentation.
    heading = {
        "kind": "heading", "level": 2,
        "presentation": {"html": {"attributes": {"class": ["hb-spec-section"]}}},
        "children": [{
            "kind": "inline_group",
            "presentation": {"html": {"attributes": {"class": ["hb-spec-section-text"]}}},
            "children": [_text(title)],
        }],
    }
    body = {"kind": "table_body", "children": [
        {"kind": "table_row", "children": [
            {"kind": "table_cell", "header": index == 0,
             "children": [_text(cell)]} for index, cell in enumerate(row)
        ]} for row in rows
    ]}
    return [heading, {"kind": "table", "children": [body]}]


def specification_flow(
    record: Mapping[str, Any], *, group_headings: Sequence[str],
    source_ref: str, language: str,
) -> list[dict[str, Any]]:
    """Map every ordered group; carrier and ComponentSpec share semantic rows."""
    groups = record["groups"]
    if len(group_headings) != len(groups):
        raise ValueError("specifications require a heading for every group")
    nodes = []
    for title, (group_id, records) in zip(group_headings, groups.items(), strict=True):
        rows = [(row["label"], row["value"]) for row in records]
        spec = spec_table_component_spec(
            section_title=title, rows=rows, source_ref=f"{source_ref}#{group_id}",
            language=language,
        )
        nodes.append(component_flow_node(
            spec, carrier_flow=_spec_carrier(title, rows), root=True,
        ))
    return nodes


def auto_resume_flow(
    record: Mapping[str, Any], *, source_ref: str, language: str,
) -> list[dict[str, Any]]:
    """Retain the source's two columns and merged middle condition."""
    columns = record["columns"]
    spec = auto_resume_component_spec(
        headers=[column["heading"]["text"] for column in columns],
        conditions=[[item["text"] for item in column["items"]] for column in columns],
        source_ref=source_ref, language=language,
    )
    return [component_flow_node(spec, root=True)]


def lcd_mode_flow(
    record: Mapping[str, Any], *, artwork_ref: str, accessibility_label: str,
    source_ref: str, language: str,
) -> list[dict[str, Any]]:
    """Map the existing two-state/three-action recipe, retaining approved copy."""
    groups = []
    indices = [row["mode_index"] for row in record["rows"]]
    if indices != [0, 0, 0, 1, 1, 1]:
        raise ValueError("LCD mode rows must retain two ordered groups of three")
    for index, mode in enumerate(record["modes"]):
        state = mode["text"]
        if language == "pt":
            state = state.replace("continuame nte", "continuamente")
        groups.append({
            **_pair("state", state),
            "actions": [
                {**_pair("action", row["action"]["text"]),
                 **_pair("description", row["instruction"]["text"])}
                for row in record["rows"] if row["mode_index"] == index
            ],
        })
    spec = lcd_mode_component_spec(
        accessibility_label=accessibility_label, groups=groups,
        artwork_ref=artwork_ref, artwork_locale_policy="exact",
        source_ref=source_ref, language=language,
    )
    return [component_flow_node(spec, root=True)]


def _paragraph(text: str) -> dict[str, str]:
    return {"kind": "paragraph", "text": text, "html": f"<p>{escape(text)}</p>"}


def _warranty_blocks(text: str) -> list[dict[str, Any]]:
    lead, *items = text.split("•")
    blocks: list[dict[str, Any]] = [_paragraph(lead.strip())] if lead.strip() else []
    items = [item.strip() for item in items if item.strip()]
    if items:
        blocks.append({
            "kind": "list", "items": items,
            "html": "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>",
        })
    return blocks


def _warranty_period(record: Mapping[str, Any], prefix: str) -> dict[str, str]:
    blocks = record["blocks"]
    parts = [" ".join(part.split()) for part in blocks[f"{prefix}_heading"]["raw_text"].splitlines()
             if part.strip()]
    if len(parts) != 3 or parts[2] != str(record[f"{prefix}_years"]):
        raise ValueError(f"{prefix} warranty heading disagrees with extracted years")
    label, unit, number = parts
    body = blocks[f"{prefix}_body"]["text"]
    return {"label": label, "unit": unit, "number": number,
            "body_html": _paragraph(body)["html"], "body_text": body}


def warranty_flow(
    record: Mapping[str, Any], *, source_ref: str, language: str,
) -> list[dict[str, Any]]:
    """Emit lead, sections and registered year cards in original semantic order."""
    blocks = record["blocks"]
    lead = warranty_lead_component_spec(
        accessibility_label=blocks["title"]["text"],
        lead_html=f'<p><strong>{escape(blocks["scope"]["text"])}</strong></p>',
        local_note_html=_paragraph(blocks["local_law_note"]["text"])["html"],
        source_ref=f"{source_ref}#lead", language=language,
    )
    nodes = [component_flow_node(lead, root=True)]
    for index, name in enumerate(
        ("limited", "exchange", "buyer", "exclusions", "interpretation"), start=1,
    ):
        title = blocks[f"{name}_heading"]["text"]
        spec = warranty_section_component_spec(
            title=title, section_index=index,
            blocks=_warranty_blocks(blocks[f"{name}_body"]["text"]),
            source_ref=f"{source_ref}#{name}", language=language,
        )
        nodes.extend([_heading(title), component_flow_node(spec, root=True)])
        if name == "limited":
            title = blocks["period_heading"]["text"]
            years = warranty_years_component_spec(
                title=title,
                periods=[_warranty_period(record, prefix) for prefix in ("standard", "extension")],
                source_ref=f"{source_ref}#period", language=language,
            )
            nodes.extend([_heading(title), component_flow_node(years, root=True)])
    return nodes


__all__ = [
    "symbol_signal_flow", "symbol_pictogram_flow", "troubleshooting_flow",
    "specification_flow", "auto_resume_flow", "lcd_mode_flow", "warranty_flow",
]
