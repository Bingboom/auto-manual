"""Web projection of explicitly declared troubleshooting tables.

The existing style contract owns the CSS. There is no registered troubleshooting
ComponentSpec yet: this adapter consumes source DOM, without inventing a public
schema or using target names, translated headers or error-code vocabularies.
"""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag


def _add_class(tag: Tag, value: str) -> None:
    tag["class"] = list(dict.fromkeys([*tag.get("class", []), value]))


def _project_table(
    soup: BeautifulSoup, table: Tag, *, source_ref: str,
    error_type: type[Exception],
) -> None:
    bodies = table.find_all("tbody", recursive=False)
    heads = table.find_all("thead", recursive=False)
    if (
        table.find("table") or table.find("tfoot") or len(bodies) != 1
        or len(heads) > 1 or table.find("tr", recursive=False)
    ):
        raise error_type(f"{source_ref}: troubleshooting requires one table body")
    body_rows = bodies[0].find_all("tr", recursive=False)
    header_rows = heads[0].find_all("tr", recursive=False) if heads else body_rows[:1]
    data_rows = body_rows if heads else body_rows[1:]
    if len(header_rows) != 1 or not data_rows:
        raise error_type(f"{source_ref}: troubleshooting requires one header and data rows")
    rows = [*header_rows, *data_rows]
    for index, row in enumerate(rows):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) != 2 or any(
            str(cell.get(attribute, "1")) != "1"
            for cell in cells for attribute in ("rowspan", "colspan")
        ):
            raise error_type(
                f"{source_ref}: troubleshooting row {index + 1} requires two unspanned cells"
            )
        if not all(cell.get_text(" ", strip=True) for cell in cells):
            raise error_type(
                f"{source_ref}: troubleshooting row {index + 1} has an empty header or value"
            )

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
        colgroup.append(soup.new_tag("col", attrs={"class": f"hb-troubleshooting-col-{role}"}))
    table.insert(0, colgroup)
    table.attrs.pop("style", None)
    _add_class(table, "hb-troubleshooting-table")
    for index, row in enumerate(rows):
        for role, cell in zip(("code", "measures"), row.find_all(["th", "td"], recursive=False)):
            cell.attrs.pop("style", None)
            _add_class(cell, f"hb-troubleshooting-{role}")
            if index == 0:
                cell.name = "th"
                cell["scope"] = "col"

    composition = table.parent
    if not (
        isinstance(composition, Tag) and composition.name == "figure"
        and "hb-troubleshooting-composition" in composition.get("class", [])
    ):
        composition = soup.new_tag("figure", attrs={"class": "hb-troubleshooting-composition"})
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


def transform_troubleshooting_tables(
    soup: BeautifulSoup, *, source_path: Path, declared_page: bool = False,
    error_type: type[Exception] = ValueError,
) -> bool:
    """Project explicit table classes or a caller's declared CsvPage boundary.

    Without a declaration, ordinary tables are unchanged. A page declaration
    must contain exactly one table; ambiguous/missing structures fail closed.
    An explicit table class can scope a component on a mixed-content page.
    """
    tables = soup.select(".hb-troubleshooting-table")
    if declared_page:
        tables = soup.find_all("table")
        if len(tables) != 1:
            raise error_type(
                f"{source_path}: declared troubleshooting page requires exactly one table; "
                f"found {len(tables)}"
            )
    for index, table in enumerate(tables, start=1):
        source_ref = f"{source_path}#troubleshooting-{index}"
        if table.name != "table":
            raise error_type(f"{source_ref}: troubleshooting declaration must be on a table")
        _project_table(soup, table, source_ref=source_ref, error_type=error_type)
    return bool(tables)
