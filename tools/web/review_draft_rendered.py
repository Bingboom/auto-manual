"""Bind the rendered shared components of a newer review-draft shell.

Newer drafts start from a published Web manual, so their blocks are the
shared Web renderers' own output: each root carries ``data-component-id``.
Each adapter here reads that markup back into the component's slots and
builds the ComponentSpec with the shared builder, so the candidate renders the
block again from its spec (the review layer is already stripped). Shapes the
class-based adapters in ``review_draft_blocks`` already read (LCD, spec,
troubleshooting, warranty lead and sections, callouts) are left to them.

Reference figures keep their live labels: the positions the base-art
renderer wrote (``--hb-x`` … on each label, the panel's top band and tone)
become the figure's ``base_art_layout`` again, and the shell's dense layouts
become the shared ``mobile_labels`` and ``label_density`` options. Operation
panels keep their layout the same way (``review_draft_operations``).
"""
from __future__ import annotations

from collections.abc import Callable
import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from tools.component_specs.auto_resume import auto_resume_component_spec
from tools.component_specs.fcc import fcc_blocks_from_text, fcc_component_spec
from tools.component_specs.key_combinations import key_combinations_component_spec
from tools.component_specs.manual_tables import symbol_icon_component_spec, symbol_signal_component_spec
from tools.component_specs.warranty import warranty_years_component_spec
from tools.manual_ir.flow import flow_nodes_to_html, html_to_flow_nodes
from tools.web.review_draft_blocks import (
    DraftChapter,
    attribute,
    bind_inbox,
    classes_of,
    column_texts,
    css_variables,
    heading_before,
    inner_html,
    need,
    percent,
    text_of,
)
from tools.web.review_draft_figures import (
    bind_app_download,
    bind_inline_control,
    bind_reference,
    figure_slug,
    unique_reference_id,
)
from tools.web.review_draft_operations import operations
from tools.web.review_draft_overlay import COMPONENT_ATTRIBUTES, KEPT_ATTRIBUTES


def _components(chapter: DraftChapter, component_id: str) -> list[Tag]:
    return chapter.root.select(f'[data-component-id="{component_id}"]')


def _label(node: Tag) -> str:
    return attribute(node, "aria-label").strip() or heading_before(node)


def _plain(chapter: DraftChapter, node: Tag) -> Tag:
    """Copy moving into a hashed carrier, without renderer attributes and in canonical flow markup.

    A reference carrier is hashed as built and again after the IR flow round
    trip (which writes ``<b>`` as ``<strong>``), so its copy takes that form first.
    """
    for tag in (node, *node.find_all(True)):
        for name in [name for name in tag.attrs if name.casefold() not in KEPT_ATTRIBUTES]:
            chapter.dropped_attributes[name] += 1
            del tag[name]
    canonical = flow_nodes_to_html(html_to_flow_nodes(node.decode_contents()))
    node.clear()
    node.extend(list(BeautifulSoup(canonical, "html.parser").contents))
    return node


def _header_copy(table: Tag) -> list[dict[str, str]]:
    return [{"content_html": text_of(cell), "content_text": text_of(cell)} for cell in table.select("thead th")]


def print_layouts(chapter: DraftChapter) -> None:
    """A Word print layout flows in one column on the Web; its signal-word lead is a callout.

    ``manual-two-col-table`` is the Word bundle's two-column safety layout,
    not a data table: its cells flow in reading order. The one-row signal
    lead it opens with (``hb-safety-lead``) becomes the callout source shape
    the callout adapter binds.
    """
    for table in chapter.root.select("table.manual-two-col-table"):
        cells = [cell for row in table.select(":scope > tbody > tr, :scope > tr")
                 for cell in row.find_all("td", recursive=False)]
        table.replace_with(*[child.extract() for cell in cells for child in list(cell.contents)])
        chapter.notes["print layout tables flowed in one column"] += 1
    for banner in chapter.root.select("figure.hb-safety-instruction"):
        # an icon beside one instruction line: the line flows, the icon is decorative
        cells = banner.find_all("td")
        if not cells:
            raise ValueError(f"{chapter.page_id}: a safety instruction banner has no copy cell")
        banner.replace_with(*list(cells[-1].contents))
        chapter.notes["safety instruction icons not carried"] += 1
    for lead in chapter.root.select("figure.hb-safety-lead"):
        rows = lead.select("tbody > tr")
        if len(rows) != 1:
            raise ValueError(f"{chapter.page_id}: a safety lead is one signal row")
        label_cell = need(rows[0].select_one("td.hb-symbol-signal-label-cell"), "safety lead label")
        meaning = rows[0].find_all("td", recursive=False)[-1]
        # The signal word is the badge's label, or (icon-only badge) the meaning's first paragraph.
        label = text_of(label_cell.select_one(".hb-signal-label") or label_cell)
        first = meaning.find("p")
        if not label and first is not None:
            label = text_of(first)
            first.decompose()
        if not label:
            raise ValueError(f"{chapter.page_id}: the safety lead names no signal word")
        callout = need(BeautifulSoup(
            '<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label"><p></p></td>'
            '<td class="manual-callout-body"></td></tr></tbody></table>', "html.parser").table, "callout")
        need(callout.p, "callout label").string = label
        need(callout.select_one("td.manual-callout-body"), "callout body").extend(list(meaning.contents))
        parent = lead.parent
        owner = parent if parent is not None and parent.name == "p" and text_of(parent) == text_of(lead) else lead
        owner.replace_with(callout)


def symbol_signals(chapter: DraftChapter) -> None:
    for figure in _components(chapter, "HB-TABLE-SYMBOL-SIGNAL"):
        table = need(figure.select_one("table.hb-symbol-signal-table"), "signal table")
        rows: list[dict[str, Any]] = []
        for row in table.select("tbody > tr"):
            label = need(row.select_one("td.hb-symbol-signal-label-cell"), "signal label")
            meaning = need(row.select_one("td.hb-symbol-signal-meaning-cell"), "signal meaning")
            rows.append({
                "label": text_of(label.select_one(".hb-signal-label") or label),
                "show_icon": label.select_one(".hb-signal-icon") is not None,
                "meaning_html": inner_html(meaning), "meaning_text": text_of(meaning),
            })
        spec = symbol_signal_component_spec(
            accessibility_label=_label(figure), headers=_header_copy(table), rows=rows,
            source_ref=chapter.source_ref("signals"), language=chapter.language,
        )
        chapter.claim(spec, (figure,))


def symbol_icons(chapter: DraftChapter) -> None:
    for figure in _components(chapter, "HB-TABLE-SYMBOL-ICON"):
        headers: list[dict[str, str]] = []
        panels: list[list[dict[str, Any]]] = []
        refs: list[str] = []
        assets: list[tuple[str, Tag]] = []
        for table in figure.select("table.hb-symbol-panel-table"):
            headers += _header_copy(table)
            rows: list[dict[str, Any]] = []
            for row in table.select("tbody > tr"):
                icon = need(row.select_one("td.hb-symbol-icon img"), "symbol icon")
                meaning = need(row.select_one("td.hb-symbol-meaning"), "symbol meaning")
                rows.append({"asset_index": len(refs), "icon_alt": attribute(icon, "alt") or text_of(meaning),
                             "meaning_html": inner_html(meaning), "meaning_text": text_of(meaning)})
                refs.append(attribute(icon, "src"))
                assets.append(("icons", icon))
            panels.append(rows)
        spec = symbol_icon_component_spec(
            accessibility_label=_label(figure), headers=headers, panels=panels, icon_refs=refs,
            source_ref=chapter.source_ref("symbols"), language=chapter.language,
        )
        chapter.claim(spec, (figure,), assets)


def inbox(chapter: DraftChapter) -> None:
    for figure in _components(chapter, "HB-SPECIAL-INBOX"):
        cards = [(attribute(need(card.select_one("img"), "inbox image"), "src"),
                  list(need(card.select_one(".hb-inbox-label"), "inbox label").contents))
                 for card in figure.select("li.hb-inbox-card")]
        tip = figure.select_one(".hb-inbox-tip")
        tip_cells = None
        if tip is not None:
            tip_cells = (need(tip.select_one(".hb-inbox-tip-label"), "tip label"),
                         need(tip.select_one(".hb-inbox-tip-body"), "tip body"))
        bind_inbox(chapter, figure, cards, accessibility_label=_label(figure), tip=tip_cells)


def warranty_periods(chapter: DraftChapter) -> None:
    for figure in _components(chapter, "HB-WARRANTY-YEARS"):
        periods = []
        for item in figure.select(".hb-warranty-period-item"):
            copy = need(item.select_one(".hb-warranty-period-copy"), "warranty period copy")
            periods.append({
                "number": text_of(item.select_one(".hb-warranty-year-badge")),
                "unit": text_of(item.select_one(".hb-warranty-years-unit")),
                "label": text_of(item.select_one(".hb-warranty-period-label")),
                "body_html": inner_html(copy), "body_text": text_of(copy),
            })
        spec = warranty_years_component_spec(
            title=_label(figure), periods=periods,
            source_ref=chapter.source_ref("warranty-years"), language=chapter.language,
        )
        chapter.claim(spec, (figure,))


def key_combinations(chapter: DraftChapter) -> None:
    """The table keeps its button art; the renderer copies cell markup from it."""

    for figure in _components(chapter, "HB-TABLE-KEY-COMBINATIONS"):
        table = need(figure.select_one("table.hb-key-combination-table"), "key-combination table")
        spec = key_combinations_component_spec(
            headers=[text_of(cell) for cell in table.select("thead th")],
            rows=[[text_of(cell) for cell in row.find_all("td", recursive=False)]
                  for row in table.select("tbody > tr")],
            source_ref=chapter.source_ref("buttons"), language=chapter.language,
        )
        figure.replace_with(table.extract())
        chapter.claim(spec, (table,))


def auto_resume(chapter: DraftChapter) -> None:
    for figure in _components(chapter, "HB-TABLE-AUTO-RESUME"):
        table = need(figure.select_one("table.hb-auto-resume-table"), "auto-resume table")
        headers = [text_of(cell) for cell in table.select("thead th")]
        spec = auto_resume_component_spec(
            headers=headers, conditions=column_texts(table, len(headers)),
            source_ref=chapter.source_ref("auto-resume"), language=chapter.language,
        )
        chapter.claim(spec, (figure,))


def _fcc_blocks(column: Tag) -> list[dict[str, Any]]:
    lines: list[str] = []
    for child in column.find_all(True, recursive=False):
        if "hb-fcc-opening" in classes_of(child):
            continue
        if child.name in {"ul", "ol"}:
            lines += [f"- {text_of(item)}" for item in child.find_all("li", recursive=False)]
        elif text_of(child):
            lines.append(text_of(child))
    return fcc_blocks_from_text("\n".join(lines))


def fcc(chapter: DraftChapter) -> None:
    for figure in _components(chapter, "HB-SPECIAL-FCC"):
        mark = need(figure.select_one("img.hb-fcc-mark"), "FCC mark")
        opening = need(figure.select_one(".hb-fcc-opening-copy"), "FCC opening")
        spec = fcc_component_spec(
            accessibility_label=_label(figure),
            opening_copy=[text_of(line) for line in opening.select(".line")] or [text_of(opening)],
            left_blocks=_fcc_blocks(need(figure.select_one(".hb-fcc-column-left"), "FCC left column")),
            right_blocks=_fcc_blocks(need(figure.select_one(".hb-fcc-column-right"), "FCC right column")),
            mark_asset_ref=attribute(mark, "src"),
            source_ref=chapter.source_ref("fcc"), language=chapter.language,
        )
        chapter.claim(spec, (figure,), (("compliance_mark", mark),))


def apps(chapter: DraftChapter) -> None:
    for node in _components(chapter, "HB-SPECIAL-APP"):
        if node.name == "span":  # the inline add-device control inside its paragraph
            paragraph = need(node.find_parent("p"), "App control paragraph")
            bind_inline_control(chapter, paragraph, node, attribute(node, "aria-label") or text_of(node))
            continue
        columns = {}
        for role in ("store", "qr"):
            copy = need(node.select_one(f".hb-app-download-copy-{role}"), f"App {role} copy")
            art = need(node.select_one(f"img.hb-app-download-art-{role}"), f"App {role} art")
            columns[role] = (copy.find_all("p") or [copy], attribute(art, "src"))
        semantic = need(node.select_one("img.hb-app-download-semantic-art"), "App download artwork")
        bind_app_download(chapter, node, columns, source_art=attribute(semantic, "src"),
                          accessibility_label=_label(node))


def _base_art_lines(chapter: DraftChapter, semantic: Tag, labels: list[Tag]) -> tuple[Tag, dict[str, Any]]:
    """The live labels as captured source lines, and the layout that places them."""

    shell = BeautifulSoup('<div class="line-block"></div>', "html.parser")
    block = need(shell.div, "line block")
    placed: list[dict[str, Any]] = []
    owner = f"{chapter.page_id}: reference figure"
    ordered = sorted(labels, key=lambda label: int(attribute(label, "data-source-line") or 0))
    for index, label in enumerate(ordered):
        style = css_variables(label)
        line = shell.new_tag("div", attrs={"class": "line"})
        line.extend(list(label.contents))
        block.append(_plain(chapter, line))
        entry: dict[str, Any] = {"line": index, "rect": [
            percent(style, name, owner) for name in ("--hb-x", "--hb-y", "--hb-width", "--hb-height")]}
        if "--hb-fill" in style:
            entry["fill"] = style["--hb-fill"]
        if "--hb-label-color" in style:
            entry["color"] = style["--hb-label-color"]
        placed.append(entry)
    panel = css_variables(need(semantic.select_one(".hb-reference-art-panel"), "art panel"))
    layout: dict[str, Any] = {"panel_top": percent(panel, "--hb-panel-top", owner),
                              "panel_fill": panel.get("--hb-panel-fill", ""), "labels": placed}
    if attribute(semantic, "data-preserve-art-frame") == "true":
        layout["preserve_frame"] = True
    if attribute(semantic, "data-mobile-labels") == "overlay":
        layout["mobile_labels"] = "overlay"
    return block, layout


# The newer shell's own label layouts and the shared options that express them:
# a dense figure keeps its labels on the art and scrolls sideways on phones; an
# overview's long port copy uses the compact label type.
_SHELL_LABEL_OPTIONS = (("native-dense", "mobile_labels", "scroll"),
                        ("native-overview", "label_density", "compact"))


def _shell_label_options(figure: Tag) -> dict[str, str]:
    return {option: value for wrapper, option, value in _SHELL_LABEL_OPTIONS
            if figure.find_parent(class_=wrapper) is not None}


def _rendered_reference(chapter: DraftChapter, figure: Tag) -> None:
    semantic = figure.select_one(".hb-reference-semantic") or figure
    art = need(semantic.find("img"), "reference artwork")
    source = attribute(art, "src")
    declared = re.sub(r"[^a-z0-9]+", "-", attribute(figure, "data-reference-id").casefold()).strip("-")
    reference_id = unique_reference_id(chapter, declared or figure_slug(source))
    shell = BeautifulSoup("", "html.parser")
    image = shell.new_tag("img", attrs={"alt": heading_before(figure) or attribute(art, "alt") or reference_id,
                                        "src": source})
    nodes: list[Tag] = [image]
    config: dict[str, Any] = {"id": reference_id, "image_key": f"{chapter.image_key_prefix}/{reference_id}"}
    labels = [label for label in semantic.select(".hb-reference-live-label")
              if text_of(label) or label.find("img") is not None]
    paragraphs = [node for node in semantic.find_all("p", recursive=False) if text_of(node)]
    carried = labels + paragraphs[:1] if labels or len(paragraphs) == 1 else labels
    chapter.keep_copy(figure, [text_of(node) for node in carried], f"figure {reference_id}")
    art_count = len([node for node in semantic.find_all("img") if not node.find_parent(class_="hb-reference-live-label")])
    if art_count > 1:
        chapter.presentation_gaps.append({"page_id": chapter.page_id, "component": f"figure {reference_id}",
                                          "missing": f"{art_count - 1} more artwork(s) its draft shows"})
    if labels:
        block, layout = _base_art_lines(chapter, semantic, labels)
        nodes.append(block)
        layout.update(_shell_label_options(figure))
        config.update(captions_embedded=False, capture_following_lines=len(labels),
                      presentation_mode="base-art-live-copy", base_art_layout=layout)
    else:
        config["captions_embedded"] = True
        if len(paragraphs) == 1:
            nodes.append(_plain(chapter, paragraphs[0].extract()))
            config["capture_adjacent_paragraph"] = True
    bind_reference(chapter, figure, nodes, image, config)


def reference_figures(chapter: DraftChapter) -> None:
    for figure in chapter.root.select(".hb-reference-figure"):
        if not figure.decomposed and figure.find_parent(class_="hb-reference-figure") is None:
            _rendered_reference(chapter, figure)


def release_component_attributes(chapter: DraftChapter) -> None:
    """Every rendered component is read: its renderer attributes leave the flow, as review attributes did."""

    for node in chapter.root.find_all(True):
        for name in COMPONENT_ATTRIBUTES - KEPT_ATTRIBUTES:
            if name in node.attrs:
                chapter.dropped_attributes[name] += 1
                del node[name]


RENDERED_ADAPTERS: tuple[Callable[[DraftChapter], None], ...] = (
    print_layouts, symbol_signals, symbol_icons, inbox, warranty_periods, key_combinations, auto_resume, fcc, apps,
    operations, reference_figures, release_component_attributes,
)


__all__ = ["RENDERED_ADAPTERS"]
