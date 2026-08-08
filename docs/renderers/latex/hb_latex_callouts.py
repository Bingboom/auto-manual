"""Render notice-shaped RST tables as reusable LaTeX callout components."""
from __future__ import annotations

from pathlib import Path
import sys

from docutils import nodes

# Sphinx loads this extension from the prepared RST bundle, where the console
# entrypoint does not put the repository root on sys.path. Resolve the owning
# checkout explicitly so the renderer can consume the shared ComponentSpec
# adapter in both source and generated-bundle locations.
_REPO_ROOT = next(
    (
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "tools" / "component_specs").is_dir()
    ),
    None,
)
if _REPO_ROOT is None:  # pragma: no cover - invalid handoff/package boundary
    raise RuntimeError("hb_latex_callouts requires the owning repository tools package")
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.component_specs.adapters import latex_callout_macro
from tools.component_specs.callout import callout_component_spec, variant_for_label
from tools.component_specs.model import ComponentSpec


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
        variant = variant_for_label(label)
        if variant is None:
            continue

        language = str(
            getattr(getattr(app, "config", None), "language", None) or "und"
        )
        spec = callout_component_spec(
            label=label,
            body=entries[1].astext(),
            source_ref=f"{_docname}:{table.line or 0}",
            language=language,
            variant=variant,
        )
        callout = HBCallout(
            label=label,
            variant=variant,
            component_spec=spec.to_dict(),
        )
        for child in entries[1].children:
            if isinstance(child, nodes.paragraph):
                _append_inline_children(callout, child)
            elif isinstance(child, nodes.bullet_list):
                _append_bullet_items(callout, child)
            else:
                callout += child.deepcopy()
        table.replace_self(callout)


def visit_callout_latex(translator, node: HBCallout) -> None:
    spec = ComponentSpec.from_dict(node["component_spec"])
    macro = latex_callout_macro(spec)
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
