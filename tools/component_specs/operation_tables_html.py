"""Bind normalized RST operation tables to the same components as PDF intake.

Only explicit shared presentation classes are eligible. Chapter applicability
and source geometry normalization remain owned by the presentation contract.
"""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.auto_resume import auto_resume_component_spec
from tools.component_specs.key_combinations import key_combinations_component_spec
from tools.component_specs.model import ComponentSpec


def _cells(row: Tag, name: str) -> list[Tag]:
    return row.find_all(name, recursive=False)


def _text(cell: Tag) -> str:
    return cell.get_text(" ", strip=True)


def parse_operation_tables_html(
    soup: BeautifulSoup, *, source_path: Path, language: str,
) -> list[tuple[ComponentSpec, Tag]]:
    """Preserve source cell copy and claim each complete shared table figure."""
    claims = []
    for kind, table_class in (
        ("auto-resume", "hb-auto-resume-table"),
        ("key-combinations", "hb-key-combination-table"),
    ):
        tables = soup.select("table." + table_class)
        if len(tables) > 1:
            raise ValueError(f"{source_path}: duplicate {kind} table")
        if not tables:
            continue
        table = tables[0]
        figure = table.parent
        expected = "hb-auto-resume-composition" if kind == "auto-resume" else "hb-key-combination-composition"
        if not isinstance(figure, Tag) or figure.name != "figure" or expected not in figure.get("class", []):
            raise ValueError(f"{source_path}: {kind} table must own its shared figure")
        if any(child is not table and str(child).strip() for child in figure.contents) or table.find(["table", "img", "caption", "tfoot"]):
            raise ValueError(f"{source_path}: unexpected nested content in {kind} figure")
        heads = table.select("thead > tr")
        rows = table.select("tbody > tr")
        if len(heads) != 1:
            raise ValueError(f"{source_path}: {kind} requires one header row")
        headers = [_text(cell) for cell in _cells(heads[0], "th")]
        cells = [_cells(row, "td") for row in rows]
        source_ref = f"{source_path.name}#{kind}"
        spec = (_auto_resume if kind == "auto-resume" else _key_combinations)(
            headers, cells, source_ref, language,
        )
        claims.append((spec, figure))
    return claims


def _auto_resume(headers: list[str], cells: list[list[Tag]], source_ref: str, language: str) -> ComponentSpec:
    if ([len(row) for row in cells] != [2, 2, 1, 2]
            or str(cells[1][0].get("rowspan", "")) != "2"):
        raise ValueError(f"{source_ref}: auto-resume lost its middle condition span")
    conditions = [[_text(cells[i][0]) for i in (0, 1, 3)],
                  [_text(row[-1]) for row in cells]]
    return auto_resume_component_spec(
        headers=headers, conditions=conditions, source_ref=source_ref, language=language,
    )


def _key_combinations(headers: list[str], cells: list[list[Tag]], source_ref: str, language: str) -> ComponentSpec:
    if any(str(cell.get(attr, "1")) != "1"
           for row in cells for cell in row for attr in ("rowspan", "colspan")):
        raise ValueError(f"{source_ref}: key-combinations must have unspanned cells")
    return key_combinations_component_spec(
        headers=headers, rows=[[_text(cell) for cell in row] for row in cells],
        source_ref=source_ref, language=language,
    )
