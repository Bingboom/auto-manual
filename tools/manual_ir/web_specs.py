"""Prepared HTML adapter for a scoped Web specification ManualIR projection.

This is not the neutral core or a whole-manual extractor. ComponentSpec carries
semantics; the owned HTML payload preserves authored inline markup for replay.
Other page content remains in its original document, outside this projection.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.model import ComponentSpecError
from tools.component_specs.registry import load_component_registry
from tools.component_specs.spec_table import spec_table_component_spec
from tools.component_specs.theme import load_manual_theme
from tools.manual_ir.hashing import value_sha256
from tools.manual_ir.source import ManualSource, SourcePage


def _source_rows(
    table: Tag, *, source_ref: str, error_type: type[Exception]
) -> list[list[Tag]]:
    """Decode existing HTML spans, without discarding or manufacturing cells."""
    if table.find("thead") or table.find("table") or len(table.find_all("tbody")) != 1:
        raise error_type(
            f"{source_ref}: specification requires one headerless table body"
        )
    rows = [
        row.find_all(["th", "td"], recursive=False)
        for row in table.select("tbody > tr")
    ]
    remaining = 0
    for cells in rows:
        if any(str(cell.get("colspan", "1")) != "1" for cell in cells):
            raise error_type(f"{source_ref}: specification cells cannot span columns")
        if len(cells) == 2 and remaining == 0:
            try:
                span = int(str(cells[0].get("rowspan", "1")))
            except ValueError as exc:
                raise error_type(
                    f"{source_ref}: invalid specification label rowspan"
                ) from exc
            if span < 1:
                raise error_type(
                    f"{source_ref}: specification label rowspan must be positive"
                )
            remaining = span - 1
        elif len(cells) == 1 and remaining > 0:
            remaining -= 1
        else:
            raise error_type(
                f"{source_ref}: specification lost its two-column row geometry"
            )
        if str(cells[-1].get("rowspan", "1")) != "1":
            raise error_type(f"{source_ref}: specification values cannot span rows")
    if not rows or remaining:
        raise error_type(
            f"{source_ref}: specification has missing rows for its label span"
        )
    return rows


def load_web_spec_source(
    html_fragment: str,
    *,
    source_path: Path,
    language: str | None = None,
    model: str | None = None,
    region: str | None = None,
) -> ManualSource | None:
    """Decode declared sections once; no filename or target implies semantics."""
    soup = BeautifulSoup(html_fragment, "html.parser")
    headings = soup.select("h2.hb-spec-section")
    if not headings:
        return None
    error_type = ValueError
    blocks = []
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    for index, heading in enumerate(headings):
        source_ref = f"{source_path}#specification-{index + 1}"
        title = heading.select_one(".hb-spec-section-text")
        if title is None:
            raise error_type(
                f"{source_ref}: specification heading lost its localized title span"
            )
        table = heading.find_next_sibling()
        if (
            not isinstance(table, Tag)
            or table.name != "table"
            or not {"hb-spec-table", "manual-spec-table"}.intersection(
                table.get("class", [])
            )
        ):
            raise error_type(
                f"{source_ref}: declared specification must be followed by its governed table"
            )
        source_rows = _source_rows(table, source_ref=source_ref, error_type=error_type)
        try:
            spec = spec_table_component_spec(
                section_title=title.get_text(" ", strip=True),
                rows=[
                    (
                        cells[0].get_text("\n", strip=True) if len(cells) == 2 else "",
                        cells[-1].get_text("\n", strip=True),
                    )
                    for cells in source_rows
                ],
                source_ref=source_ref,
                language=str(table.get("lang") or language or "und"),
                registry=registry,
                theme=theme,
            )
        except ComponentSpecError as exc:
            raise ValueError(f"{source_ref}: {exc}") from exc
        blocks.append(
            (
                "web_specification",
                {
                    "component_spec": spec.to_dict(),
                    "heading_html": str(heading),
                    "table_html": str(table),
                    "markup_assets": [
                        {"src": str(image["src"])}
                        for node in (heading, table)
                        for image in node.select("img[src]")
                        if image["src"]
                    ],
                },
            )
        )
    digest = hashlib.sha256(html_fragment.encode("utf-8")).hexdigest()
    return ManualSource(
        model=model or "unspecified",
        region=region or "unspecified",
        language=language or "und",
        source="prepared-html",
        bundle_root=str(source_path.parent),
        bundle_sha256=digest,
        snapshot_sha256=None,
        layout_params_sha256=value_sha256({"layout_params": "not-used"}),
        style_contract_sha256=value_sha256({"registry": registry, "theme": theme}),
        pages=(
            SourcePage(
                page_id=str(source_path),
                source_ref=str(source_path),
                source_path=str(source_path),
                language=language or "und",
                source_sha256=digest,
                blocks=tuple(blocks),
            ),
        ),
        metadata={
            "projection": "web-specifications",
            "source_format": "prepared-html",
            "layout_params": "not-used",
        },
    )
