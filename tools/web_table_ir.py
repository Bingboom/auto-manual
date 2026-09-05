"""One public IR consumer for declared LCD and troubleshooting tables."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.manual_ir import (
    ManualIR,
    ManualIRValidationError,
    build_manual_ir_from_source,
    validate_manual_ir,
)
from tools.manual_ir.web_tables import (
    declared_tables,
    load_web_table_source,
    restore_table,
    table_boundary,
)


def _add_class(tag: Tag, value: str) -> None:
    tag["class"] = list(dict.fromkeys([*tag.get("class", []), value]))


def _render_lcd(soup: BeautifulSoup, table: Tag, rows: list[Tag]) -> None:
    roles = ("number", "icon", "name", "description")
    for colgroup in table.find_all("colgroup", recursive=False):
        colgroup.decompose()
    colgroup = soup.new_tag("colgroup")
    for role in roles:
        colgroup.append(soup.new_tag("col", attrs={"class": f"hb-lcd-col-{role}"}))
    table.insert(0, colgroup)
    _add_class(table, "hb-lcd-icon-table")
    for row in rows:
        for role, cell in zip(roles, row.find_all(["th", "td"], recursive=False)):
            _add_class(cell, f"hb-lcd-{role}")
        image = row.find_all(["th", "td"], recursive=False)[1].img
        if image is not None:
            _add_class(image, "hb-lcd-icon-art")
            for attribute in ("style", "width", "height"):
                image.attrs.pop(attribute, None)

    composition = table.parent
    if not (
        isinstance(composition, Tag)
        and composition.name == "figure"
        and "hb-lcd-table-composition" in composition.get("class", [])
    ):
        composition = soup.new_tag(
            "figure", attrs={"class": "hb-lcd-table-composition"}
        )
        table.replace_with(composition)
        composition.append(table)
    if not composition.get("aria-label"):
        composition["aria-label"] = "LCD icon meanings"
    composition["tabindex"] = "0"


def _render_troubleshooting(
    soup: BeautifulSoup, table: Tag, header_rows: list[Tag], data_rows: list[Tag]
) -> None:
    bodies = table.find_all("tbody", recursive=False)
    heads = table.find_all("thead", recursive=False)
    rows = [*header_rows, *data_rows]
    # Headerless source tables (including JP) explicitly put the authored
    # header first. Move that node; never synthesize translated header copy.
    if not heads:
        head = soup.new_tag("thead")
        bodies[0].insert_before(head)
        head.append(header_rows[0].extract())
    for colgroup in table.find_all("colgroup", recursive=False):
        colgroup.decompose()
    colgroup = soup.new_tag("colgroup")
    for role in ("code", "measures"):
        colgroup.append(
            soup.new_tag("col", attrs={"class": f"hb-troubleshooting-col-{role}"})
        )
    table.insert(0, colgroup)
    table.attrs.pop("style", None)
    _add_class(table, "hb-troubleshooting-table")
    for index, row in enumerate(rows):
        for role, cell in zip(
            ("code", "measures"), row.find_all(["th", "td"], recursive=False)
        ):
            cell.attrs.pop("style", None)
            _add_class(cell, f"hb-troubleshooting-{role}")
            if index == 0:
                cell.name = "th"
                cell["scope"] = "col"

    composition = table.parent
    if not (
        isinstance(composition, Tag)
        and composition.name == "figure"
        and "hb-troubleshooting-composition" in composition.get("class", [])
    ):
        composition = soup.new_tag(
            "figure", attrs={"class": "hb-troubleshooting-composition"}
        )
        table.replace_with(composition)
        composition.append(table)
    if not composition.get("aria-label"):
        composition["aria-label"] = " / ".join(
            cell.get_text(" ", strip=True)
            for cell in header_rows[0].find_all("th", recursive=False)
        )
    # The existing responsive style scrolls this figure at narrow widths.
    # Make that same scroll surface reachable by keyboard.
    composition["tabindex"] = "0"


def render_web_table_ir(ir: ManualIR) -> list[str]:
    """Replay complete scoped table blocks, rejecting partial or corrupt inputs."""
    issues = validate_manual_ir(ir, require_zero_skipped_raw=True)
    if issues:
        raise ManualIRValidationError(ir.source, issues)
    if ir.metadata.get("projection") != "web-declared-tables" or len(ir.pages) != 1:
        raise ValueError("expected a single-page web-declared-tables projection")
    output = []
    for block in ir.pages[0].blocks:
        if block.kind != "web_table":
            raise ValueError(f"{block.source_ref}: unsupported Web table block")
        soup, table, headers, rows = restore_table(block.payload, block.source_ref)
        if block.payload["table_kind"] == "lcd":
            _render_lcd(soup, table, rows)
        else:
            _render_troubleshooting(soup, table, headers, rows)
        output.append(str(soup))
    return output


def transform_declared_tables(
    soup: BeautifulSoup,
    *,
    table_kind: str,
    source_path: Path,
    declared_page: bool = False,
    error_type: type[Exception] = ValueError,
    language: str | None = None,
    model: str | None = None,
    region: str | None = None,
) -> bool:
    """Shared production entry: source -> public IR -> complete DOM replacement."""
    try:
        source = load_web_table_source(
            str(soup),
            table_kind=table_kind,
            source_path=source_path,
            declared_page=declared_page,
            language=language,
            model=model,
            region=region,
        )
        if source is None:
            return False
        rendered = render_web_table_ir(build_manual_ir_from_source(source))
        boundaries = [
            table_boundary(table, table_kind)
            for table in declared_tables(soup, table_kind, declared_page)
        ]
    except ValueError as exc:
        raise error_type(f"{source_path}: {exc}") from exc
    for boundary, fragment in zip(boundaries, rendered, strict=True):
        boundary.replace_with(BeautifulSoup(fragment, "html.parser"))
    return True
