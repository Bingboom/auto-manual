"""Shared DOM projection for declared LCD icon tables in RST and MyST."""
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
    if (
        len(bodies) != 1 or table.find(["thead", "tfoot", "table"])
        or table.find("tr", recursive=False)
    ):
        raise error_type(f"{source_ref}: LCD icon table requires one headerless body")
    rows = bodies[0].find_all("tr", recursive=False)
    if not rows:
        raise error_type(f"{source_ref}: LCD icon table requires data rows")
    for index, row in enumerate(rows, start=1):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) != 4 or any(
            str(cell.get(attr, "1")) != "1"
            for cell in cells for attr in ("rowspan", "colspan")
        ):
            raise error_type(f"{source_ref}: LCD row {index} requires four unspanned cells")
        icons = cells[1].find_all("img")
        if (
            len(icons) != 1 or not str(icons[0].get("src", "")).strip()
            or not all(cells[i].get_text(" ", strip=True) for i in (0, 2, 3))
        ):
            raise error_type(f"{source_ref}: LCD row {index} requires number, icon, name and description")

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
        _add_class(image, "hb-lcd-icon-art")
        for attribute in ("style", "width", "height"):
            image.attrs.pop(attribute, None)

    composition = table.parent
    if not (
        isinstance(composition, Tag) and composition.name == "figure"
        and "hb-lcd-table-composition" in composition.get("class", [])
    ):
        composition = soup.new_tag("figure", attrs={"class": "hb-lcd-table-composition"})
        table.replace_with(composition)
        composition.append(table)
    if not composition.get("aria-label"):
        composition["aria-label"] = "LCD icon meanings"
    composition["tabindex"] = "0"


def transform_lcd_icon_tables(
    soup: BeautifulSoup, *, source_path: Path, declared_page: bool = False,
    error_type: type[Exception] = ValueError,
) -> bool:
    """Use a table declaration or the assembly planner's CSV page identity."""
    tables = soup.select(".hb-lcd-icon-table")
    if declared_page:
        tables = soup.find_all("table")
        if len(tables) != 1:
            raise error_type(f"{source_path}: declared LCD page requires exactly one table; found {len(tables)}")
    for index, table in enumerate(tables, start=1):
        source_ref = f"{source_path}#lcd-{index}"
        if table.name != "table":
            raise error_type(f"{source_ref}: LCD declaration must be on a table")
        _project_table(soup, table, source_ref=source_ref, error_type=error_type)
    return bool(tables)
