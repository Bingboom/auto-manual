"""Render notice-shaped RST tables as reusable LaTeX callout components."""
from __future__ import annotations

from docutils import nodes


_VARIANTS_BY_LABEL = {
    "WARNING": "warning",
    "CAUTION": "caution",
    "NOTE": "note",
    "TIP": "tip",
    "TIPS": "tip",
    "AVERTISSEMENT": "warning",
    "ATTENTION": "caution",
    "REMARQUE": "note",
    "CONSEIL": "tip",
    "CONSEILS": "tip",
    "ADVERTENCIA": "warning",
    "PRECAUCIÓN": "caution",
    "PRECAUCION": "caution",
    "NOTA": "note",
    "CONSEJO": "tip",
    "CONSEJOS": "tip",
}

_MACRO_BY_VARIANT = {
    "warning": "HBWarningBlock",
    "caution": "HBCautionBlock",
    "note": "HBNoteBlock",
    "tip": "HBTipBlock",
}


class HBCallout(nodes.General, nodes.Element):
    """A callout replacing a one-row label/body table in LaTeX output."""


class HBCalloutItem(nodes.General, nodes.Element):
    """One flattened list item within a callout body."""


def _display_label(text: str) -> str:
    return text.strip().rstrip(":：-").strip()


def _direct_rows(table: nodes.table) -> list[nodes.row]:
    return [node for node in table.findall(nodes.row) if node.parent is not None]


def _append_inline_children(target: nodes.Element, paragraph: nodes.paragraph) -> None:
    if target.children:
        target += nodes.Text(" ")
    for child in paragraph.children:
        target += child.deepcopy()


def _append_bullet_items(target: HBCallout, bullet_list: nodes.bullet_list) -> None:
    for list_item in bullet_list.children:
        if not isinstance(list_item, nodes.list_item):
            continue
        callout_item = HBCalloutItem()
        nested_lists: list[nodes.bullet_list] = []
        for child in list_item.children:
            if isinstance(child, nodes.paragraph):
                _append_inline_children(callout_item, child)
            elif isinstance(child, nodes.bullet_list):
                nested_lists.append(child)
            else:
                callout_item += child.deepcopy()
        if callout_item.children:
            target += callout_item
        for nested in nested_lists:
            _append_bullet_items(target, nested)


def replace_notice_tables(app, doctree: nodes.document, _docname: str) -> None:
    """Replace only the one-row, two-cell tables carrying notice labels."""
    if getattr(app.builder, "format", None) != "latex":
        return

    for table in list(doctree.findall(nodes.table)):
        rows = _direct_rows(table)
        if len(rows) != 1:
            continue
        entries = [child for child in rows[0].children if isinstance(child, nodes.entry)]
        if len(entries) != 2:
            continue

        label = _display_label(entries[0].astext())
        variant = _VARIANTS_BY_LABEL.get(label.upper())
        if variant is None:
            continue

        callout = HBCallout(label=label, variant=variant)
        for child in entries[1].children:
            if isinstance(child, nodes.paragraph):
                _append_inline_children(callout, child)
            elif isinstance(child, nodes.bullet_list):
                _append_bullet_items(callout, child)
            else:
                callout += child.deepcopy()
        table.replace_self(callout)


def visit_callout_latex(translator, node: HBCallout) -> None:
    macro = _MACRO_BY_VARIANT[node["variant"]]
    translator.body.append(f"\n\\{macro}{{{translator.encode(node['label'])}}}{{%\n")


def depart_callout_latex(translator, _node: HBCallout) -> None:
    translator.body.append("}%\n")


def visit_callout_item_latex(translator, _node: HBCalloutItem) -> None:
    translator.body.append("\\HBCalloutBullet{%\n")


def depart_callout_item_latex(translator, _node: HBCalloutItem) -> None:
    translator.body.append("}%\n")


def setup(app):
    app.add_node(HBCallout, latex=(visit_callout_latex, depart_callout_latex))
    app.add_node(HBCalloutItem, latex=(visit_callout_item_latex, depart_callout_item_latex))
    app.connect("doctree-resolved", replace_notice_tables)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
