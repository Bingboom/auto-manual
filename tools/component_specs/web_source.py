"""Web-source validation for registered ComponentSpec adapters."""
from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag

from tools.component_specs.adapters import web_callout_classes
from tools.component_specs.callout import callout_component_spec
from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.spec_table import (
    spec_table_component_spec,
    web_spec_table_projection,
)


_CIRCLED_REFERENCE_RE = re.compile(r"[\u2460-\u2473]")


def validate_web_callout_html(
    callout_html: str,
    *,
    source_ref: str,
    error_type: type[Exception] = ComponentSpecError,
    language: str | None = None,
    variant: str | None = None,
) -> ComponentSpec:
    """Validate protected Web callout HTML against the registered adapter."""
    soup = BeautifulSoup(callout_html, "html.parser")
    label_node = soup.select_one(".manual-callout-label")
    body_node = soup.select_one(".manual-callout-body")
    if label_node is None or body_node is None:
        raise error_type(f"{source_ref}: manual callout requires label and body cells")
    spec = callout_component_spec(
        label=label_node.get_text(" ", strip=True),
        body=body_node.get_text("\n", strip=True),
        items=[item.get_text(" ", strip=True) for item in body_node.select("li")],
        source_ref=source_ref,
        language=str((soup.table.get("lang") if soup.table else None) or language or "und"),
        variant=variant,
    )
    table_class = web_callout_classes(spec)["table"]
    if soup.select_one(f"table.{table_class}") is None:
        raise error_type(
            f"{source_ref}: callout does not satisfy the registered Web adapter"
        )
    return spec


def superscript_circled_references(soup: BeautifulSoup, cell: Tag) -> int:
    replacements = 0
    for text_node in list(cell.find_all(string=_CIRCLED_REFERENCE_RE)):
        if text_node.find_parent("sup"):
            continue
        text = str(text_node)
        fragments: list[NavigableString | Tag] = []
        cursor = 0
        for match in _CIRCLED_REFERENCE_RE.finditer(text):
            if match.start() > cursor:
                fragments.append(NavigableString(text[cursor : match.start()]))
            reference = soup.new_tag("sup", attrs={"class": "hb-spec-reference"})
            reference.string = match.group(0)
            fragments.append(reference)
            replacements += 1
            cursor = match.end()
        if cursor < len(text):
            fragments.append(NavigableString(text[cursor:]))
        text_node.replace_with(*fragments)
    return replacements


def validate_web_spec_table_html(
    composition_html: str,
    *,
    source_ref: str,
    error_type: type[Exception] = ComponentSpecError,
) -> ComponentSpec:
    """Validate the final protected Web table through HB-TABLE-SPEC."""
    soup = BeautifulSoup(composition_html, "html.parser")
    composition = soup.select_one("figure.hb-spec-table-composition")
    table = soup.select_one("table.hb-spec-table")
    if composition is None or table is None:
        raise error_type(f"{source_ref}: governed specification composition is missing")
    title = str(composition.get("aria-label") or "").strip()
    rows: list[tuple[str, str]] = []
    for index, row in enumerate(table.select("tbody > tr"), start=1):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) == 2:
            label, value = cells
            label_text = label.get_text("\n", strip=True)
        elif len(cells) == 1:
            value = cells[0]
            label_text = ""
        else:
            raise error_type(
                f"{source_ref}: specification row {index} lost two-column geometry"
            )
        rows.append((label_text, value.get_text("\n", strip=True)))
    try:
        spec = spec_table_component_spec(
            section_title=title,
            rows=rows,
            source_ref=source_ref,
            language=str(table.get("lang") or composition.get("lang") or "und"),
        )
        projection = web_spec_table_projection(spec)
    except ComponentSpecError as exc:
        raise error_type(f"{source_ref}: {exc}") from exc
    if projection["composition_class"] not in composition.get("class", []):
        raise error_type(f"{source_ref}: specification composition adapter mismatch")
    return spec


__all__ = [
    "superscript_circled_references",
    "validate_web_callout_html",
    "validate_web_spec_table_html",
]
