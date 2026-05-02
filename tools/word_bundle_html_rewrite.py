#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from copy import deepcopy
import re
from xml.etree import ElementTree as ET


_ALERT_LABELS = {
    "WARNING",
    "CAUTION",
    "DANGER",
    "NOTE",
    "TIP",
    "TIPS",
    "AVERTISSEMENT",
    "ATTENTION",
    "REMARQUE",
    "CONSEIL",
    "CONSEILS",
    "ADVERTENCIA",
    "PRECAUCIÓN",
    "PRECAUCION",
    "NOTA",
    "CONSEJO",
    "CONSEJOS",
    "WARNUNG",
    "VORSICHT",
    "HINWEIS",
    "TIPP",
    "AVVERTENZA",
    "ATTENZIONE",
    "SUGGERIMENTO",
    "ПОПЕРЕДЖЕННЯ",
    "УВАГА",
    "ПРИМІТКА",
    "ПОРАДИ",
    "警告",
    "注意",
    "ご注意",
    "提示",
    "说明",
    "備考",
    "備註",
    "备注",
}
_WARNING_BOX_LABEL_TEXTS = {
    *_ALERT_LABELS,
}
_SIGNAL_WORD_BANNERS = {
    "WARNING": "templates/word_template/common_assets/symbols/warning_bar.png",
    "CAUTION": "templates/word_template/common_assets/symbols/caution_bar.png",
    "NOTE": "templates/word_template/common_assets/symbols/note_bar.png",
    "TIP": "templates/word_template/common_assets/symbols/tip_bar.png",
}
_SAFETY_SUBLIST_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Do not charge the battery in extremely hot or cold environments",
        (
            "Charging temperature:",
            "Discharging temperature:",
        ),
    ),
    (
        "To ensure proper air circulation",
        (
            "Charging in damp or poorly ventilated spaces",
            "Water can cause short circuits",
        ),
    ),
)
_HTML_VOID_TAG_RE = re.compile(
    r"<(?P<tag>area|base|br|col|embed|hr|img|input|link|meta|param|source|track|wbr)(?P<attrs>(?:\s[^<>]*?)?)>",
    re.IGNORECASE,
)


def _html_tag_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1].lower()


def _html_class_names(element: ET.Element) -> set[str]:
    return {
        token.strip()
        for token in (element.attrib.get("class") or "").split()
        if token.strip()
    }


def _normalize_inline_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _normalize_alert_label_text(text: str) -> str:
    return _normalize_inline_text(text).rstrip(":：").upper()


def _has_non_label_punctuation_text(text: str) -> bool:
    normalized = _normalize_inline_text(text)
    return bool(normalized and _normalize_alert_label_text(normalized))


def _normalize_html_void_tags(fragment: str) -> str:
    def replace(match: re.Match[str]) -> str:
        raw = match.group(0)
        if raw.rstrip().endswith("/>"):
            return raw
        return f"<{match.group('tag')}{match.group('attrs') or ''} />"

    return _HTML_VOID_TAG_RE.sub(replace, fragment)


def _element_text_weight(element: ET.Element) -> int:
    return max(1, len(_normalize_inline_text("".join(element.itertext()))))


def _clone_list_with_items(template: ET.Element, items: list[ET.Element]) -> ET.Element:
    cloned = ET.Element(template.tag, dict(template.attrib))
    for item in items:
        cloned.append(deepcopy(item))
    return cloned


def _split_balanced_elements(
    elements: list[ET.Element],
    *,
    left_fixed_weight: int = 0,
    right_fixed_weight: int = 0,
) -> tuple[list[ET.Element], list[ET.Element]]:
    if len(elements) < 2:
        return elements, []

    weights = [_element_text_weight(element) for element in elements]
    prefix_sums = [0]
    for weight in weights:
        prefix_sums.append(prefix_sums[-1] + weight)

    best_split = 1
    best_score: tuple[int, int] | None = None
    total_weight = prefix_sums[-1]
    for split_at in range(1, len(elements)):
        left_weight = left_fixed_weight + prefix_sums[split_at]
        right_weight = right_fixed_weight + (total_weight - prefix_sums[split_at])
        score = (abs(left_weight - right_weight), left_weight)
        if best_score is None or score < best_score:
            best_score = score
            best_split = split_at
    return elements[:best_split], elements[best_split:]


def _build_two_col_table(left_children: list[ET.Element], right_children: list[ET.Element]) -> ET.Element:
    table = ET.Element(
        "table",
        {
            "class": "manual-two-col-table",
            "style": "width:100%; border-collapse:separate; border-spacing:12px 0; margin:0 0 16px 0;",
        },
    )
    tbody = ET.SubElement(table, "tbody")
    row = ET.SubElement(tbody, "tr")
    left_cell = ET.SubElement(
        row,
        "td",
        {
            "style": "width:50%; border:none; padding:0 8px 0 0; vertical-align:top;",
        },
    )
    right_cell = ET.SubElement(
        row,
        "td",
        {
            "style": "width:50%; border:none; padding:0 0 0 8px; vertical-align:top;",
        },
    )
    for child in left_children:
        left_cell.append(deepcopy(child))
    for child in right_children:
        right_cell.append(deepcopy(child))
    return table


def _rewrite_safety_two_col_layout(element: ET.Element) -> ET.Element:
    if _html_tag_name(element) != "div" or "hb-two-col" not in _html_class_names(element):
        return element

    lead_nodes: list[ET.Element] = []
    trailing_nodes: list[ET.Element] = []
    list_node: ET.Element | None = None

    for child in list(element):
        child_copy = deepcopy(child)
        if _html_tag_name(child_copy) == "ul" and "hb-list" in _html_class_names(child_copy) and list_node is None:
            list_node = child_copy
            continue
        if list_node is None:
            lead_nodes.append(child_copy)
        else:
            trailing_nodes.append(child_copy)

    if list_node is None:
        return element

    items = [deepcopy(item) for item in list(list_node) if _html_tag_name(item) == "li"]
    if len(items) < 2:
        return element

    left_items, right_items = _split_balanced_elements(
        items,
        left_fixed_weight=sum(_element_text_weight(node) for node in lead_nodes),
        right_fixed_weight=sum(_element_text_weight(node) for node in trailing_nodes),
    )
    if not right_items:
        return element

    left_children: list[ET.Element] = [deepcopy(node) for node in lead_nodes]
    left_children.append(_clone_list_with_items(list_node, left_items))

    right_children: list[ET.Element] = [_clone_list_with_items(list_node, right_items)]
    right_children.extend(deepcopy(node) for node in trailing_nodes)
    return _build_two_col_table(left_children, right_children)


def _match_safety_sublist_rule(text: str) -> tuple[str, ...] | None:
    normalized = _normalize_inline_text(text)
    for parent_prefix, child_prefixes in _SAFETY_SUBLIST_RULES:
        if normalized.startswith(parent_prefix):
            return child_prefixes
    return None


def _extract_alert_label(element: ET.Element) -> str | None:
    tag = _html_tag_name(element)
    text = _normalize_alert_label_text("".join(element.itertext()))
    if text not in _ALERT_LABELS:
        return None

    if tag in {"h1", "h2", "h3"}:
        return text

    if tag != "p":
        return None

    if _normalize_inline_text(element.text or ""):
        return None
    for child in element:
        if _html_tag_name(child) not in {"strong", "b"}:
            return None
        if _has_non_label_punctuation_text(child.tail or ""):
            return None
    return text


def _is_standalone_strong_paragraph(element: ET.Element) -> bool:
    if _html_tag_name(element) != "p":
        return False
    if _normalize_inline_text(element.text or ""):
        return False
    children = list(element)
    if not children:
        return False
    for child in children:
        if _html_tag_name(child) not in {"strong", "b"}:
            return False
        if _normalize_inline_text(child.tail or ""):
            return False
    return True


def _set_element_children(element: ET.Element, new_children: list[ET.Element]) -> ET.Element:
    for child in list(element):
        element.remove(child)
    for child in new_children:
        element.append(child)
    return element


def _rewrite_known_safety_sublists(element: ET.Element) -> ET.Element:
    if _html_tag_name(element) != "ul" or "hb-list" not in _html_class_names(element):
        return element

    children = list(element)
    rewritten: list[ET.Element] = []
    index = 0
    while index < len(children):
        child = deepcopy(children[index])
        if _html_tag_name(child) != "li":
            rewritten.append(child)
            index += 1
            continue

        child_prefixes = _match_safety_sublist_rule("".join(child.itertext()))
        if not child_prefixes:
            rewritten.append(child)
            index += 1
            continue

        sub_items: list[ET.Element] = []
        next_index = index + 1
        while next_index < len(children):
            next_child = children[next_index]
            if _html_tag_name(next_child) != "li":
                break
            next_text = _normalize_inline_text("".join(next_child.itertext()))
            if not any(next_text.startswith(prefix) for prefix in child_prefixes):
                break
            sub_items.append(deepcopy(next_child))
            next_index += 1

        if sub_items:
            sublist = ET.Element("ul", {"class": "hb-sublist"})
            for sub_item in sub_items:
                sublist.append(sub_item)
            child.append(sublist)
            rewritten.append(child)
            index = next_index
            continue

        rewritten.append(child)
        index += 1

    return _set_element_children(element, rewritten)


def _rewrite_signal_word_banner_table(element: ET.Element) -> ET.Element:
    if _html_tag_name(element) != "table":
        return element

    head_row = element.find("./thead/tr")
    if head_row is None:
        return element

    head_cells = head_row.findall("./th")
    headers = [_normalize_inline_text("".join(cell.itertext())).lower() for cell in head_cells]
    if headers != ["symbol", "meaning"]:
        return element

    changed = False
    for row in element.findall("./tbody/tr"):
        cells = row.findall("./td")
        if len(cells) != 2:
            continue
        first_cell = cells[0]
        label = _normalize_inline_text("".join(first_cell.itertext())).upper()
        banner_src = _SIGNAL_WORD_BANNERS.get(label)
        if not banner_src:
            continue

        image = ET.Element(
            "img",
            {
                "alt": f"{label} banner placeholder.",
                "src": banner_src,
                "style": "width: 140px;",
            },
        )
        _set_element_children(first_cell, [image])
        first_cell.text = None
        changed = True

    return element if changed else element


def _table_has_header(element: ET.Element) -> bool:
    for node in element.iter():
        tag = _html_tag_name(node)
        if tag in {"thead", "th"}:
            return True
    return False


def _direct_table_rows(element: ET.Element) -> list[ET.Element]:
    rows: list[ET.Element] = []
    for child in list(element):
        child_tag = _html_tag_name(child)
        if child_tag == "tr":
            rows.append(child)
        elif child_tag == "tbody":
            rows.extend(row for row in list(child) if _html_tag_name(row) == "tr")
    return rows


def _row_cells(row: ET.Element) -> list[ET.Element]:
    return [cell for cell in list(row) if _html_tag_name(cell) in {"td", "th"}]


def _extract_alert_cell_label(cell: ET.Element) -> str | None:
    text = _normalize_alert_label_text("".join(cell.itertext()))
    if text not in _ALERT_LABELS:
        return None

    direct_text = _normalize_inline_text(cell.text or "")
    if direct_text and _normalize_alert_label_text(direct_text) != text:
        return None

    allowed_tags = {"p", "strong", "b", "span", "br"}
    for child in cell.iter():
        if child is cell:
            continue
        if _html_tag_name(child) not in allowed_tags:
            return None
        if _has_non_label_punctuation_text(child.tail or ""):
            return None
    return text


def _cell_body_nodes(cell: ET.Element) -> list[ET.Element]:
    body_nodes: list[ET.Element] = []
    lead_text = _normalize_inline_text(cell.text or "")
    if lead_text:
        para = ET.Element("p")
        para.text = lead_text
        body_nodes.append(para)
    body_nodes.extend(deepcopy(child) for child in list(cell))
    return body_nodes


def _rewrite_two_column_alert_table(element: ET.Element) -> ET.Element:
    if _html_tag_name(element) != "table":
        return element

    if "manual-callout-table" in _html_class_names(element):
        return element
    if _table_has_header(element):
        return element

    rows = _direct_table_rows(element)
    if len(rows) != 1:
        return element

    cells = _row_cells(rows[0])
    if len(cells) != 2:
        return element

    label = _extract_alert_cell_label(cells[0])
    if label is None:
        return element

    body_nodes = _cell_body_nodes(cells[1])
    if not body_nodes and not _normalize_inline_text("".join(cells[1].itertext())):
        return element

    return _build_alert_table(label, body_nodes)


def _build_alert_table(label: str, body_nodes: list[ET.Element]) -> ET.Element:
    table = ET.Element(
        "table",
        {
            "class": "manual-callout-table",
            "style": "width:100%; border-collapse:collapse; margin:0 0 16px 0;",
        },
    )
    tbody = ET.SubElement(table, "tbody")
    row = ET.SubElement(tbody, "tr")

    if label:
        label_cell = ET.SubElement(
            row,
            "td",
            {
                "class": "manual-callout-label",
                "style": "width:16%; border:1px solid #888; padding:6px 8px; vertical-align:top; background:#f3c27b;",
            },
        )
        label_p = ET.SubElement(label_cell, "p")
        label_strong = ET.SubElement(label_p, "strong")
        label_strong.text = label

    body_cell = ET.SubElement(
        row,
        "td",
        {
            "class": "manual-callout-body",
            **({"colspan": "2"} if not label else {}),
            "style": "border:1px solid #888; padding:6px 8px; vertical-align:top;",
        },
    )
    if not body_nodes:
        ET.SubElement(body_cell, "p")
        return table

    for node in body_nodes:
        body_cell.append(deepcopy(node))
    return table


def _warning_box_table_parts(element: ET.Element) -> tuple[str, list[ET.Element]]:
    lockup_text = ""
    warning_text = ""
    for node in element.iter():
        node_classes = _html_class_names(node)
        if "hb-warning-lockup" in node_classes and not lockup_text:
            lockup_text = _normalize_inline_text("".join(node.itertext()))
        if "hb-warning-text" in node_classes and not warning_text:
            warning_text = _normalize_inline_text("".join(node.itertext()))

    label = lockup_text
    body_text = warning_text
    if not label and warning_text.upper() in _WARNING_BOX_LABEL_TEXTS:
        label = warning_text
        body_text = ""

    body_nodes: list[ET.Element] = []
    if body_text:
        para = ET.Element("p")
        para.text = body_text
        body_nodes.append(para)
    return label, body_nodes


def _rewrite_word_friendly_children(
    children: list[ET.Element],
    *,
    lang: str | None = None,
) -> list[ET.Element]:
    normalized_children: list[ET.Element] = []
    for child in children:
        rewritten_child = deepcopy(child)
        if list(rewritten_child):
            _set_element_children(
                rewritten_child,
                _rewrite_word_friendly_children(list(rewritten_child), lang=lang),
            )
        rewritten_child = _rewrite_known_safety_sublists(rewritten_child)
        rewritten_child = _rewrite_signal_word_banner_table(rewritten_child)
        rewritten_child = _rewrite_two_column_alert_table(rewritten_child)
        rewritten_child = _rewrite_safety_two_col_layout(rewritten_child)
        normalized_children.append(rewritten_child)

    rewritten: list[ET.Element] = []
    index = 0
    while index < len(normalized_children):
        child = normalized_children[index]
        child_tag = _html_tag_name(child)
        child_classes = _html_class_names(child)

        if child_tag == "section" and "manual-cover" in child_classes:
            title = _normalize_inline_text("".join(child.itertext()))
            if title:
                heading = ET.Element("h1")
                heading.text = title
                rewritten.append(heading)
            index += 1
            continue

        if child_tag == "div" and "hb-warning-box" in child_classes:
            label, body_nodes = _warning_box_table_parts(child)
            rewritten.append(_build_alert_table(label, body_nodes))
            index += 1
            continue

        alert_label = _extract_alert_label(child)
        if alert_label is not None:
            body_nodes: list[ET.Element] = []
            next_index = index + 1
            saw_terminal_block = False
            while next_index < len(normalized_children):
                next_child = normalized_children[next_index]
                next_tag = _html_tag_name(next_child)
                if next_tag == "div" and "manual-page-break" in _html_class_names(next_child):
                    break
                if _extract_alert_label(next_child) is not None:
                    break
                if next_tag in {"h1", "h2", "h3", "section"}:
                    break
                if _is_standalone_strong_paragraph(next_child):
                    break
                if saw_terminal_block:
                    break
                if next_tag in {"ul", "ol", "img", "table"}:
                    body_nodes.append(next_child)
                    saw_terminal_block = True
                    next_index += 1
                    continue
                if next_tag in {"p", "div"}:
                    body_nodes.append(next_child)
                    next_index += 1
                    continue
                break

            if body_nodes:
                rewritten.append(_build_alert_table(alert_label, body_nodes))
                index = next_index
                continue

        rewritten.append(child)
        index += 1

    return rewritten


def _rewrite_word_friendly_fragment(fragment: str, *, lang: str | None = None) -> str:
    normalized_fragment = _normalize_html_void_tags(fragment)
    wrapped = f"<root>{normalized_fragment}</root>"
    try:
        root = ET.fromstring(wrapped)
    except ET.ParseError:
        return fragment

    rewritten = _rewrite_word_friendly_children(list(root), lang=lang)
    return "".join(ET.tostring(node, encoding="unicode", method="html") for node in rewritten)


def _html_fragment_root(fragment: str) -> ET.Element | None:
    normalized_fragment = _normalize_html_void_tags(fragment)
    wrapped = f"<root>{normalized_fragment}</root>"
    try:
        return ET.fromstring(wrapped)
    except ET.ParseError:
        return None


def _extract_html_cell_text(cell: ET.Element) -> str:
    fragments: list[str] = []

    def walk(element: ET.Element) -> None:
        if element.text:
            fragments.append(element.text)
        for child in list(element):
            tag = _html_tag_name(child)
            if tag == "br":
                fragments.append("\n")
            else:
                walk(child)
                if tag in {"p", "div", "li", "ul", "ol"}:
                    fragments.append("\n")
            if child.tail:
                fragments.append(child.tail)

    walk(cell)
    normalized_lines = [_normalize_inline_text(line) for line in "".join(fragments).splitlines()]
    return "\n".join(line for line in normalized_lines if line)


def _normalize_spec_section_title(text: str) -> str:
    title = _normalize_inline_text(text)
    while title and title[0] in {"●", "•", "◉", "○", "◌"}:
        title = title[1:].strip()
    return title


def _extract_spec_word_data(fragment: str) -> dict[str, object] | None:
    root = _html_fragment_root(fragment)
    if root is None:
        return None

    title_main = ""
    sections: list[dict[str, object]] = []
    notes: list[str] = []
    footnotes: list[str] = []
    trailers: list[tuple[str, str]] = []
    current_section: dict[str, object] | None = None

    for child in list(root):
        tag = _html_tag_name(child)
        text = _normalize_inline_text("".join(child.itertext()))
        if not text:
            continue

        if tag == "h1":
            title_main = text
            current_section = None
            continue

        if tag == "h2":
            current_section = {
                "title": _normalize_spec_section_title(text),
                "rows": [],
            }
            sections.append(current_section)
            continue

        if tag == "table" and current_section is not None:
            rows: list[tuple[str, str]] = []
            for row in child.findall(".//tr"):
                cells = [cell for cell in list(row) if _html_tag_name(cell) in {"td", "th"}]
                if len(cells) < 2:
                    continue
                left = _extract_html_cell_text(cells[0])
                right = _extract_html_cell_text(cells[1])
                if left or right:
                    rows.append((left, right))
            if rows:
                current_rows = current_section.setdefault("rows", [])
                if isinstance(current_rows, list):
                    current_rows.extend(rows)
            continue

        if tag == "p":
            trailer_kind = _normalize_inline_text(str(child.get("data-spec-trailer-kind") or "")).lower()
            class_names = {
                token.strip()
                for token in str(child.get("class") or "").split()
                if token.strip()
            }
            if trailer_kind == "footnote":
                footnotes.append(text)
                trailers.append(("footnote", text))
            elif trailer_kind == "note":
                notes.append(text)
                trailers.append(("note", text))
            elif "hb-spec-footnote" in class_names or "manual-spec-footnote" in class_names:
                footnotes.append(text)
                trailers.append(("footnote", text))
            elif "hb-spec-note" in class_names or "manual-spec-note" in class_names:
                notes.append(text)
                trailers.append(("note", text))
            else:
                notes.append(text)
                trailers.append(("note", text))

    if not title_main or not sections:
        return None
    return {
        "title_main": title_main,
        "sections": sections,
        "notes": notes,
        "footnotes": footnotes,
        "trailers": trailers,
    }
