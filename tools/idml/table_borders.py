"""Table border helpers for IDML story XML."""
from __future__ import annotations

import re

from .style_names import table_style_ref


def suppress_outer_cell_edges(cells: list[str], n_rows: int, n_cols: int) -> list[str]:
    """Zero only the table perimeter; leave internal grid lines style-driven."""
    out: list[str] = []
    for idx, cell_xml in enumerate(cells):
        row = idx // n_cols
        col = idx % n_cols
        attrs: list[str] = []
        if row == 0:
            attrs.append('TopEdgeStrokeWeight="0"')
        if row == n_rows - 1:
            attrs.append('BottomEdgeStrokeWeight="0"')
        if col == 0:
            attrs.append('LeftEdgeStrokeWeight="0"')
        if col == n_cols - 1:
            attrs.append('RightEdgeStrokeWeight="0"')
        if not attrs:
            out.append(cell_xml)
            continue
        out.append(re.sub(r'(<Cell\b[^>]*)(>)',
                          r'\1 ' + " ".join(attrs) + r'\2',
                          cell_xml, count=1))
    return out


def component_table_xml(tid: str, cols: list[float], cells: list[str],
                        n_rows: int = 1, role: str | None = None, *,
                        outer_stroke: bool = True) -> str:
    table_style = table_style_ref(role)
    if not outer_stroke:
        cells = suppress_outer_cell_edges(cells, n_rows, len(cols))
    row_els = "\n".join(f'    <Row Self="{tid}r{ri}" Name="{ri}"/>'
                         for ri in range(n_rows))
    col_els = "\n".join(
        f'    <Column Self="{tid}col{ci}" Name="{ci}" SingleColumnWidth="{wd:g}"/>'
        for ci, wd in enumerate(cols))
    return (
        f'  <Table Self="{tid}" AppliedTableStyle="{table_style}" '
        f'BodyRowCount="{n_rows}" ColumnCount="{len(cols)}" HeaderRowCount="0" FooterRowCount="0">\n'
        f'{row_els}\n{col_els}\n' + "\n".join(cells) + "\n  </Table>\n")
