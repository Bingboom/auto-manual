"""Declared LCD/troubleshooting HTML source adapter for scoped public IR.

Table roles and authored headers are semantic data. Rich markup remains an
explicit presentation payload until renderer-neutral rich text is available.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from bs4 import BeautifulSoup, Tag

from tools.manual_ir.hashing import file_sha256
from tools.manual_ir.source import ManualSource
from tools.manual_ir.web_source import make_web_source
from tools.utils.path_utils import Paths, repo_root


class TableProfile(NamedTuple):
    label: str
    table_class: str
    composition_class: str
    roles: tuple[str, ...]


_TABLES = {
    "lcd": TableProfile(
        "LCD",
        "hb-lcd-icon-table",
        "hb-lcd-table-composition",
        ("number", "icon", "name", "description"),
    ),
    "troubleshooting": TableProfile(
        "troubleshooting",
        "hb-troubleshooting-table",
        "hb-troubleshooting-composition",
        ("code", "measures"),
    ),
}


def table_profile(table_kind: str) -> TableProfile:
    try:
        return _TABLES[table_kind]
    except KeyError as exc:
        raise ValueError(f"unsupported declared table kind: {table_kind}") from exc


def declared_tables(
    soup: BeautifulSoup, table_kind: str, declared_page: bool
) -> list[Tag]:
    profile = table_profile(table_kind)
    tables = (
        soup.find_all("table")
        if declared_page
        else soup.select("." + profile.table_class)
    )
    if declared_page and len(tables) != 1:
        raise ValueError(
            f"declared {profile.label} page requires exactly one table; found {len(tables)}"
        )
    if any(table.name != "table" for table in tables):
        raise ValueError(f"{profile.label} declaration must be on a table")
    return tables


def table_boundary(table: Tag, table_kind: str) -> Tag:
    parent = table.parent
    if (
        isinstance(parent, Tag)
        and parent.name == "figure"
        and table_profile(table_kind).composition_class in parent.get("class", [])
    ):
        if len(parent.find_all("table")) != 1:
            raise ValueError("declared table figure must contain exactly one table")
        return parent
    return table


def _lcd_rows(table: Tag, source_ref: str) -> tuple[list[Tag], list[Tag]]:
    error_type = ValueError
    bodies = table.find_all("tbody", recursive=False)
    if (
        len(bodies) != 1
        or table.find(["thead", "tfoot", "table"])
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
            for cell in cells
            for attr in ("rowspan", "colspan")
        ):
            raise error_type(
                f"{source_ref}: LCD row {index} requires four unspanned cells"
            )
        icons = cells[1].find_all("img")
        if (
            len(icons) != 1
            or not str(icons[0].get("src", "")).strip()
            or not all(cells[i].get_text(" ", strip=True) for i in (0, 2, 3))
        ):
            raise error_type(
                f"{source_ref}: LCD row {index} requires number, icon, name and description"
            )

    return [], rows


def _troubleshooting_rows(table: Tag, source_ref: str) -> tuple[list[Tag], list[Tag]]:
    error_type = ValueError
    bodies = table.find_all("tbody", recursive=False)
    heads = table.find_all("thead", recursive=False)
    if (
        table.find("table")
        or table.find("tfoot")
        or len(bodies) != 1
        or len(heads) > 1
        or table.find("tr", recursive=False)
    ):
        raise error_type(f"{source_ref}: troubleshooting requires one table body")
    body_rows = bodies[0].find_all("tr", recursive=False)
    header_rows = heads[0].find_all("tr", recursive=False) if heads else body_rows[:1]
    data_rows = body_rows if heads else body_rows[1:]
    if len(header_rows) != 1 or not data_rows:
        raise error_type(
            f"{source_ref}: troubleshooting requires one header and data rows"
        )
    rows = [*header_rows, *data_rows]
    for index, row in enumerate(rows):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) != 2 or any(
            str(cell.get(attribute, "1")) != "1"
            for cell in cells
            for attribute in ("rowspan", "colspan")
        ):
            raise error_type(
                f"{source_ref}: troubleshooting row {index + 1} requires two unspanned cells"
            )
        if not all(cell.get_text(" ", strip=True) for cell in cells):
            raise error_type(
                f"{source_ref}: troubleshooting row {index + 1} has an empty header or value"
            )

    return header_rows, data_rows


def decode_table(
    table: Tag, table_kind: str, source_ref: str
) -> tuple[dict, list[Tag], list[Tag]]:
    profile = table_profile(table_kind)
    headers, rows = (_lcd_rows if table_kind == "lcd" else _troubleshooting_rows)(
        table, source_ref
    )
    values = []
    for row in rows:
        cells = row.find_all(["th", "td"], recursive=False)
        record = {
            role: cell.get_text("\n", strip=True)
            for role, cell in zip(profile.roles, cells, strict=True)
        }
        if table_kind == "lcd":
            image = cells[1].img
            record["icon"] = {
                "src": str(image["src"]),
                "alt": str(image.get("alt", "")),
            }
        values.append(record)
    boundary = table_boundary(table, table_kind)
    payload = {
        "table_kind": table_kind,
        "headers": [
            [
                cell.get_text("\n", strip=True)
                for cell in row.find_all(["th", "td"], recursive=False)
            ]
            for row in headers
        ],
        "rows": values,
        "fragment_html": str(boundary),
        "assets": [
            {"src": str(image["src"])}
            for image in boundary.select("img[src]")
            if image["src"]
        ],
    }
    return payload, headers, rows


def restore_table(
    payload: object, source_ref: str
) -> tuple[BeautifulSoup, Tag, list[Tag], list[Tag]]:
    """Validate owned payload geometry and semantic/markup agreement on replay."""
    if not isinstance(payload, dict) or not isinstance(
        payload.get("fragment_html"), str
    ):
        raise ValueError(f"{source_ref}: incomplete declared table payload")
    kind = payload.get("table_kind")
    if not isinstance(kind, str):
        raise ValueError(f"{source_ref}: missing declared table kind")
    table_profile(kind)
    soup = BeautifulSoup(payload["fragment_html"], "html.parser")
    tables = soup.find_all("table")
    if len(tables) != 1:
        raise ValueError(f"{source_ref}: retained markup requires exactly one table")
    decoded, headers, rows = decode_table(tables[0], kind, source_ref)
    if payload != decoded:
        raise ValueError(f"{source_ref}: table semantics do not match retained markup")
    return soup, tables[0], headers, rows


def load_web_table_source(
    html_fragment: str,
    *,
    table_kind: str,
    source_path: Path,
    declared_page: bool = False,
    language: str | None = None,
    model: str | None = None,
    region: str | None = None,
) -> ManualSource | None:
    soup = BeautifulSoup(html_fragment, "html.parser")
    blocks = []
    for index, table in enumerate(
        declared_tables(soup, table_kind, declared_page), start=1
    ):
        payload, _, _ = decode_table(
            table, table_kind, f"{source_path}#{table_kind}-{index}"
        )
        blocks.append(("web_table", payload))
    if not blocks:
        return None
    stylesheet = Paths(root=repo_root()).renderer_contracts_dir / "web_manual.css"
    return make_web_source(
        html_fragment,
        source_path=source_path,
        blocks=tuple(blocks),
        projection="web-declared-tables",
        style_contract_sha256=file_sha256(stylesheet),
        language=language,
        model=model,
        region=region,
    )
