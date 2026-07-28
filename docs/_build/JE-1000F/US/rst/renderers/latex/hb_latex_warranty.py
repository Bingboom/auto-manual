"""Render the English warranty page as dedicated LaTeX components."""
from __future__ import annotations

import re

from docutils import nodes


_WARRANTY_PAGE_TITLES = {"WARRANTY"}
_WARRANTY_PERIOD_TITLES = {"WARRANTY PERIOD"}


class HBWarrantyPage(nodes.General, nodes.Element):
    """A fixed-format warranty page with explicit page boundaries."""


class HBWarrantyLead(nodes.General, nodes.Element):
    """The shaded purchase-channel statement below the page title."""


class HBWarrantySection(nodes.General, nodes.Element):
    """A rounded warranty panel with an attached dark title label."""


class HBWarrantyYears(nodes.General, nodes.Element):
    """The two-column standard/extended warranty period component."""


class HBWarrantyYearColumn(nodes.General, nodes.Element):
    """One year badge, heading, and description within the period panel."""


def _direct_title(section: nodes.section) -> nodes.title | None:
    if section.children and isinstance(section.children[0], nodes.title):
        return section.children[0]
    return None


def _direct_rows(table: nodes.table) -> list[nodes.row]:
    return [node for node in table.findall(nodes.row) if node.parent is not None]


def _short_strong_paragraph(node: nodes.Node) -> bool:
    return (
        isinstance(node, nodes.paragraph)
        and len(node.astext()) <= 48
        and any(isinstance(child, nodes.strong) for child in node.children)
    )


def _year_column(entry: nodes.entry, index: int) -> HBWarrantyYearColumn | None:
    children = list(entry.children)
    if not children or not isinstance(children[0], nodes.paragraph):
        return None

    match = re.match(r"^\s*(\d+)\s+([^\s]+)(?:\s+(.*))?$", children[0].astext())
    if match is None:
        return None

    number, unit, inline_subtitle = match.groups()
    consumed = 1
    subtitle = (inline_subtitle or "").strip()
    if not subtitle and len(children) > 1 and _short_strong_paragraph(children[1]):
        subtitle = children[1].astext().strip()
        consumed = 2

    column = HBWarrantyYearColumn(
        index=index,
        number=number,
        unit=unit,
        subtitle=subtitle,
    )
    for child in children[consumed:]:
        column += child.deepcopy()
    return column


def _warranty_years(table: nodes.table) -> HBWarrantyYears | None:
    rows = _direct_rows(table)
    if len(rows) != 1:
        return None
    entries = [child for child in rows[0].children if isinstance(child, nodes.entry)]
    if len(entries) != 2:
        return None

    columns = [_year_column(entry, index) for index, entry in enumerate(entries, 1)]
    if any(column is None for column in columns):
        return None

    years = HBWarrantyYears()
    for column in columns:
        assert column is not None
        years += column
    return years


def _warranty_section(section: nodes.section, index: int) -> HBWarrantySection:
    title = _direct_title(section)
    assert title is not None
    panel = HBWarrantySection(title=title.astext(), index=index)
    is_period = title.astext().strip().upper() in _WARRANTY_PERIOD_TITLES

    for child in section.children[1:]:
        if is_period and isinstance(child, nodes.table):
            years = _warranty_years(child)
            if years is not None:
                panel += years
                continue
        panel += child.deepcopy()
    return panel


def _protect_apostrophes(root: nodes.Element) -> None:
    for text_node in list(root.findall(nodes.Text)):
        text = str(text_node)
        if "'" not in text and "\u2019" not in text:
            continue
        pieces = re.split(r"(['\u2019])", text)
        replacement: list[nodes.Node] = []
        for piece in pieces:
            if piece in {"'", "\u2019"}:
                replacement.append(nodes.raw("", r"\textquotesingle{}", format="latex"))
            elif piece:
                replacement.append(nodes.Text(piece))
        assert text_node.parent is not None
        text_node.parent.replace(text_node, replacement)


def _warranty_page(title: nodes.title, children: list[nodes.Node]) -> HBWarrantyPage:
    page = HBWarrantyPage(title=title.astext())
    lead_wrapped = False
    section_index = 0
    for child in children:
        if isinstance(child, nodes.section):
            section_index += 1
            page += _warranty_section(child, section_index)
        elif isinstance(child, nodes.paragraph) and not lead_wrapped:
            lead = HBWarrantyLead()
            lead += child.deepcopy()
            page += lead
            lead_wrapped = True
        else:
            page += child.deepcopy()
    _protect_apostrophes(page)
    return page


def replace_warranty_page(app, doctree: nodes.document, _docname: str) -> None:
    """Replace only the English Warranty section for LaTeX output."""
    if getattr(app.builder, "format", None) != "latex":
        return

    if doctree.children and isinstance(doctree.children[0], nodes.title):
        document_title = doctree.children[0]
        if document_title.astext().strip().upper() in _WARRANTY_PAGE_TITLES:
            page = _warranty_page(document_title, list(doctree.children[1:]))
            doctree.children = [page]
            page.parent = doctree
            return

    for section in list(doctree.findall(nodes.section)):
        title = _direct_title(section)
        if title is None or title.astext().strip().upper() not in _WARRANTY_PAGE_TITLES:
            continue
        section.replace_self(_warranty_page(title, list(section.children[1:])))


def visit_warranty_page_latex(translator, node: HBWarrantyPage) -> None:
    translator.body.append(
        f"\n\\HBWarrantyPageStart{{{translator.encode(node['title'])}}}\n"
    )


def depart_warranty_page_latex(translator, _node: HBWarrantyPage) -> None:
    translator.body.append("\n\\HBWarrantyPageEnd\n")


def visit_warranty_lead_latex(translator, _node: HBWarrantyLead) -> None:
    translator.body.append("\n\\begin{HBWarrantyLead}\n")


def depart_warranty_lead_latex(translator, _node: HBWarrantyLead) -> None:
    translator.body.append("\n\\end{HBWarrantyLead}\n")


def visit_warranty_section_latex(translator, node: HBWarrantySection) -> None:
    translator.body.append(
        f"\n\\begin{{HBWarrantySection}}{{{translator.encode(node['title'])}}}"
        f"{{{node['index']}}}\n"
    )


def depart_warranty_section_latex(translator, _node: HBWarrantySection) -> None:
    translator.body.append("\n\\end{HBWarrantySection}\n")


def visit_warranty_years_latex(translator, _node: HBWarrantyYears) -> None:
    translator.body.append("\n\\begin{HBWarrantyYears}%\n")


def depart_warranty_years_latex(translator, _node: HBWarrantyYears) -> None:
    translator.body.append("\\end{HBWarrantyYears}\n")


def visit_warranty_year_column_latex(translator, node: HBWarrantyYearColumn) -> None:
    if node["index"] == 2:
        translator.body.append("\\hfill%\n")
    args = ("index", "number", "unit", "subtitle")
    encoded = [translator.encode(str(node[key])) for key in args]
    translator.body.append(
        "\\begin{HBWarrantyYearColumn}"
        + "".join(f"{{{value}}}" for value in encoded)
        + "%\n"
    )


def depart_warranty_year_column_latex(translator, _node: HBWarrantyYearColumn) -> None:
    translator.body.append("\\end{HBWarrantyYearColumn}%\n")


def setup(app):
    app.add_node(
        HBWarrantyPage,
        latex=(visit_warranty_page_latex, depart_warranty_page_latex),
    )
    app.add_node(
        HBWarrantyLead,
        latex=(visit_warranty_lead_latex, depart_warranty_lead_latex),
    )
    app.add_node(
        HBWarrantySection,
        latex=(visit_warranty_section_latex, depart_warranty_section_latex),
    )
    app.add_node(
        HBWarrantyYears,
        latex=(visit_warranty_years_latex, depart_warranty_years_latex),
    )
    app.add_node(
        HBWarrantyYearColumn,
        latex=(visit_warranty_year_column_latex, depart_warranty_year_column_latex),
    )
    app.connect("doctree-resolved", replace_warranty_page)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
