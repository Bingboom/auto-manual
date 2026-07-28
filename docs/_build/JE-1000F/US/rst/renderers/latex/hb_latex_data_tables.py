"""Map manual data tables to reusable rounded LaTeX components."""
from __future__ import annotations

import re

from docutils import nodes


_ENVIRONMENT_BY_KIND = {
    "auto_resume": "HBAutoResumeTable",
    "key_combinations": "HBKeyCombinationTable",
    "troubleshooting": "HBTroubleshootingTable",
}


class HBDataTable(nodes.General, nodes.Element):
    """A data table whose outer frame is separate from its inner grid."""


class HBDataRow(nodes.General, nodes.Element):
    """One physical row in a componentized data table."""


class HBDataCell(nodes.General, nodes.Element):
    """One cell with explicit column and row-span metadata."""


class HBDataHangingLine(nodes.General, nodes.Element):
    """A numbered corrective measure with a hanging continuation indent."""


class HBDataCellBreak(nodes.General, nodes.Element):
    """A deliberate line break between source cell blocks."""


class HBDataSectionGuard(nodes.General, nodes.Element):
    """Keep a data-table heading with its non-breaking framed table."""


def _direct_rows(table: nodes.table) -> list[nodes.row]:
    return list(table.findall(nodes.row))


def _entries(row: nodes.row) -> list[nodes.entry]:
    return [child for child in row.children if isinstance(child, nodes.entry)]


def _normalized(text: str) -> str:
    return " ".join(text.upper().split())


def _ancestor_section_title(table: nodes.table) -> str:
    section = _ancestor_section(table)
    if section is not None and section.children:
        first = section.children[0]
        if isinstance(first, nodes.title):
            return _normalized(first.astext())
    return ""


def _ancestor_section(table: nodes.table) -> nodes.section | None:
    parent = table.parent
    while parent is not None:
        if isinstance(parent, nodes.section):
            return parent
        parent = parent.parent
    return None


def _classify_table(table: nodes.table) -> str | None:
    rows = _direct_rows(table)
    if len(rows) < 2:
        return None

    first_entries = _entries(rows[0])
    first_text = [_normalized(entry.astext()) for entry in first_entries]
    column_count = len(list(table.findall(nodes.colspec)))

    first_body_code = ""
    if len(rows) > 1 and _entries(rows[1]):
        first_body_code = _normalized(_entries(rows[1])[0].astext())
    if (
        column_count == 2
        and first_body_code == "F0"
        and ("longtable" in table.get("classes", []) or "ERROR" in first_text[0])
    ):
        return "troubleshooting"

    section_title = _ancestor_section_title(table)
    has_row_span = any(
        int(entry.get("morerows", 0)) > 0 for entry in table.findall(nodes.entry)
    )
    if column_count == 2 and (
        has_row_span
        or "OUTPUT RESUME" in section_title
        or "REPRISE" in section_title
        or "REANUDACI" in section_title
    ):
        return "auto_resume"

    if column_count == 3 and (
        "KEY COMB" in section_title
        or "COMBINAISON" in section_title
        or "COMBINACI" in section_title
    ):
        return "key_combinations"

    return None


def _copy_inline(target: nodes.Element, source: nodes.Element) -> None:
    for child in source.children:
        target += child.deepcopy()


def _hanging_line(line: nodes.line) -> HBDataHangingLine | None:
    if not line.children or not isinstance(line.children[0], nodes.Text):
        return None
    match = re.match(r"^\s*(\d+)\.\s*(.*)$", str(line.children[0]))
    if match is None:
        return None

    number, remainder = match.groups()
    hanging = HBDataHangingLine(number=number)
    if remainder:
        hanging += nodes.Text(remainder)
    for child in line.children[1:]:
        hanging += child.deepcopy()
    return hanging


def _copy_cell_content(target: HBDataCell, entry: nodes.entry) -> None:
    block_index = 0
    for child in entry.children:
        if isinstance(child, nodes.paragraph):
            if block_index:
                target += HBDataCellBreak()
            _copy_inline(target, child)
            block_index += 1
            continue
        if isinstance(child, nodes.line_block):
            for line in child.children:
                if not isinstance(line, nodes.line):
                    continue
                hanging = _hanging_line(line)
                if hanging is not None:
                    target += hanging
                else:
                    if block_index:
                        target += HBDataCellBreak()
                    _copy_inline(target, line)
                block_index += 1
            continue
        target += child.deepcopy()
        block_index += 1


def _component_table(table: nodes.table, kind: str) -> HBDataTable:
    rows = _direct_rows(table)
    ncols = len(list(table.findall(nodes.colspec)))
    component = HBDataTable(kind=kind, ncols=ncols)
    active_spans = [0] * ncols

    for row_index, source_row in enumerate(rows):
        continuations = [index for index, remaining in enumerate(active_spans) if remaining]
        component_row = HBDataRow(
            kind=kind,
            ncols=ncols,
            header=row_index == 0,
            last=row_index == len(rows) - 1,
            continuations=continuations,
        )

        source_entries = _entries(source_row)
        if (
            kind == "auto_resume"
            and active_spans[0]
            and source_entries
            and not source_entries[0].astext().strip()
        ):
            source_entries = source_entries[1:]

        column = 0
        for entry_index, entry in enumerate(source_entries):
            while column < ncols and active_spans[column]:
                column += 1
            if column >= ncols:
                break
            rowspan = int(entry.get("morerows", 0)) + 1
            if (
                kind == "auto_resume"
                and column == 0
                and entry_index == 0
                and entry.astext().strip()
            ):
                for future_row in rows[row_index + 1 :]:
                    future_entries = _entries(future_row)
                    if not future_entries or future_entries[0].astext().strip():
                        break
                    rowspan += 1
            cell = HBDataCell(
                kind=kind,
                col=column,
                rowspan=rowspan,
                header=row_index == 0,
                first=not component_row.children,
                hanging=False,
            )
            _copy_cell_content(cell, entry)
            cell["hanging"] = any(
                isinstance(child, HBDataHangingLine) for child in cell.children
            )
            component_row += cell
            if rowspan > 1:
                active_spans[column] = rowspan
            column += 1

        span_after = [index for index, remaining in enumerate(active_spans) if remaining > 1]
        component_row["span_after"] = span_after
        for index, remaining in enumerate(active_spans):
            if remaining:
                active_spans[index] -= 1
        component += component_row
    return component


def replace_data_tables(app, doctree: nodes.document, _docname: str) -> None:
    """Replace recognized manual data tables only for LaTeX output."""
    if getattr(app.builder, "format", None) != "latex":
        return

    for table in list(doctree.findall(nodes.table)):
        kind = _classify_table(table)
        if kind is not None:
            if kind in {"key_combinations", "troubleshooting"}:
                section = _ancestor_section(table)
                if section is not None and section.parent is not None:
                    index = section.parent.index(section)
                    section.parent.insert(index, HBDataSectionGuard(kind=kind))
            table.replace_self(_component_table(table, kind))


def visit_data_table_latex(translator, node: HBDataTable) -> None:
    environment = _ENVIRONMENT_BY_KIND[node["kind"]]
    translator.body.append(f"\n\\begin{{{environment}}}\n")


def depart_data_table_latex(translator, node: HBDataTable) -> None:
    environment = _ENVIRONMENT_BY_KIND[node["kind"]]
    translator.body.append(f"\\end{{{environment}}}\n")


def visit_data_row_latex(translator, node: HBDataRow) -> None:
    translator._hb_data_last_col = -1
    if node["header"]:
        translator.body.append("\\rowcolor{HBTableHeadBg}%\n")


def depart_data_row_latex(translator, node: HBDataRow) -> None:
    translator.body.append("\\tabularnewline\n")
    if node["last"]:
        return
    span_after = node["span_after"]
    if span_after:
        first_open_column = max(span_after) + 2
        translator.body.append(f"\\cline{{{first_open_column}-{node['ncols']}}}\n")
    else:
        translator.body.append("\\hline\n")


def _cell_macro(node: HBDataCell) -> str:
    if node["header"]:
        return "HBDataHeaderCell"
    if node["hanging"]:
        return "HBDataStepsCell"
    if node["kind"] == "troubleshooting" and node["col"] == 0:
        return "HBDataCodeCell"
    return {
        "auto_resume": "HBDataAutoResumeCell",
        "key_combinations": "HBDataKeyCombinationsCell",
        "troubleshooting": "HBDataTroubleshootingCell",
    }[node["kind"]]


def visit_data_cell_latex(translator, node: HBDataCell) -> None:
    previous = translator._hb_data_last_col
    ampersands = node["col"] if previous < 0 else node["col"] - previous
    if ampersands:
        translator.body.append(" & " * ampersands)
    translator._hb_data_last_col = node["col"]

    if node["rowspan"] > 1:
        translator.body.append(f"\\multirow{{{node['rowspan']}}}{{=}}{{%\n")
    translator.body.append(f"\\{_cell_macro(node)}{{%\n")


def depart_data_cell_latex(translator, node: HBDataCell) -> None:
    translator.body.append("}%\n")
    if node["rowspan"] > 1:
        translator.body.append("}%\n")


def visit_hanging_line_latex(translator, node: HBDataHangingLine) -> None:
    translator.body.append(f"\\HBDataHangingLine{{{node['number']}}}{{%\n")


def depart_hanging_line_latex(translator, _node: HBDataHangingLine) -> None:
    translator.body.append("}%\n")


def visit_cell_break_latex(translator, _node: HBDataCellBreak) -> None:
    translator.body.append("\\HBDataCellBreak{}")
    raise nodes.SkipNode


def visit_section_guard_latex(translator, node: HBDataSectionGuard) -> None:
    macro = (
        "HBDataKeySectionGuard"
        if node["kind"] == "key_combinations"
        else "HBDataTroubleSectionGuard"
    )
    translator.body.append(f"\n\\{macro}\n")
    raise nodes.SkipNode


def setup(app):
    app.add_node(HBDataTable, latex=(visit_data_table_latex, depart_data_table_latex))
    app.add_node(HBDataRow, latex=(visit_data_row_latex, depart_data_row_latex))
    app.add_node(HBDataCell, latex=(visit_data_cell_latex, depart_data_cell_latex))
    app.add_node(
        HBDataHangingLine,
        latex=(visit_hanging_line_latex, depart_hanging_line_latex),
    )
    app.add_node(HBDataCellBreak, latex=(visit_cell_break_latex, None))
    app.add_node(HBDataSectionGuard, latex=(visit_section_guard_latex, None))
    app.connect("doctree-resolved", replace_data_tables)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
