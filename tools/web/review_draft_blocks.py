"""Bind the printed blocks of a stripped review draft to shared components.

The draft markup follows the ``manual-review-draft`` skill
(``references/jp-style-mapping.md``): shared Web manual shapes (spec tables,
LCD tables, callouts, warranty cards, troubleshooting) and JP-only shapes taken
from a reference page (signal table, symbol and warning panels, inbox cards,
button and output-resume grids). Each adapter reads one shape and builds its
ComponentSpec with the shared builder; ``embed_component_claims`` later
replaces the shape with the component node. Figures and App blocks are bound
by ``review_draft_figures``.

No adapter writes copy. When a builder needs copy the draft does not hold
(symbol table headers), the adapter takes ``review_draft_fallback_copy.json``
and records the use; the release gate refuses a package that still has one.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
import hashlib
import json
import re
from typing import Any

from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList, PageElement

from tools.component_specs.auto_resume import auto_resume_component_spec
from tools.component_specs.inbox import CARD_ASSET_ROLES, VARIABLE_CARD_ASSET_ROLE, inbox_component_spec
from tools.component_specs.key_combinations import key_combinations_component_spec
from tools.component_specs.lcd_mode import lcd_mode_component_spec
from tools.component_specs.manual_tables import (
    lcd_icon_component_spec,
    symbol_icon_component_spec,
    symbol_signal_component_spec,
    troubleshooting_component_spec,
)
from tools.component_specs.model import ComponentSpec
from tools.component_specs.registry import require_valid_component_spec
from tools.component_specs.spec_table import spec_table_component_spec
from tools.component_specs.warranty import (
    warranty_lead_component_spec,
    warranty_section_component_spec,
)
from tools.manual_ir.web_callouts import decode_callout_payload
from tools.manual_ir.whole_document_components import ComponentClaim
from tools.utils.path_utils import get_paths

FALLBACK_COPY_JSON = "review_draft_fallback_copy.json"
_SPACE = re.compile(r"\s+")
_CSS_VARIABLE = re.compile(r"(--[\w-]+)\s*:\s*([^;]+)")


@dataclass
class DraftChapter:
    """One chapter being bound, and what its adapters recorded."""

    root: BeautifulSoup
    page_id: str
    language: str
    image_key_prefix: str
    claims: list[ComponentClaim] = field(default_factory=list)
    fallbacks: list[dict[str, str]] = field(default_factory=list)
    exceptions: list[dict[str, str]] = field(default_factory=list)
    presentation_gaps: list[dict[str, str]] = field(default_factory=list)
    dropped_attributes: Counter = field(default_factory=Counter)
    notes: Counter = field(default_factory=Counter)
    _families: Counter = field(default_factory=Counter)

    def source_ref(self, family: str) -> str:
        self._families[family] += 1
        return f"review-draft/{self.page_id}#{family}-{self._families[family]}"

    def claim(
        self, spec: ComponentSpec, owned: Iterable[Tag], assets: Iterable[tuple[str, Tag]] = (),
    ) -> None:
        self.claims.append(ComponentClaim(spec=spec, owned_nodes=tuple(owned), asset_tags=tuple(assets)))

    def keep_copy(self, owner: Tag, carried: Iterable[str], component: str) -> None:
        """List copy ``owner`` shows that its component does not carry, so a release cannot lose it."""

        left = "".join(owner.get_text("").split())
        for text in carried:
            left = left.replace("".join(text.split()), "", 1)
        if left:
            self.presentation_gaps.append({"page_id": self.page_id, "component": component,
                                           "missing": f"part of its copy («{left[:60]}»)"})


def text_of(node: Tag | None) -> str:
    return _SPACE.sub(" ", node.get_text(" ", strip=True)) if node is not None else ""


def inner_html(node: Tag | None) -> str:
    return node.decode_contents().strip() if node is not None else ""


def need(node: Tag | None, what: str) -> Tag:
    """A required element of the draft markup contract."""

    if node is None:
        raise ValueError(f"review draft markup: {what} is missing")
    return node


def attribute(node: Tag, name: str) -> str:
    value = node.get(name)
    return " ".join(value) if isinstance(value, list) else str(value or "")


def classes_of(node: Tag) -> list[str]:
    return [str(name) for name in node.get_attribute_list("class") if name]


def css_variables(node: Tag) -> dict[str, str]:
    """The custom properties a shared renderer wrote on ``node``: its positions and tones."""

    return {name: value.strip() for name, value in _CSS_VARIABLE.findall(attribute(node, "style"))}


def percent(style: dict[str, str], name: str, owner: str) -> float:
    value = style.get(name, "")
    if not value.endswith("%"):
        raise ValueError(f"{owner}: rendered position {name} is not a percentage")
    return float(value[:-1])


def heading_before(node: Tag, levels: Sequence[str] = ("h1", "h2", "h3")) -> str:
    return text_of(node.find_previous(list(levels)))


def lines_of(cell: Tag) -> list[str]:
    """Visible lines of a cell: a ``<br>`` or a paragraph ends a line."""

    copy = BeautifulSoup(str(cell), "html.parser")
    for br in copy.find_all("br"):
        br.replace_with("\n")
    for block in copy.find_all(["p", "li", "div"]):
        block.insert_before("\n")
        block.append("\n")
    lines = [_SPACE.sub(" ", line).strip() for line in copy.get_text("").split("\n")]
    return [line for line in lines if line]


@lru_cache(maxsize=1)
def _fallback_copy() -> dict[str, Any]:
    path = get_paths().renderer_contracts_dir / FALLBACK_COPY_JSON
    return json.loads(path.read_text(encoding="utf-8"))


def fallback(chapter: DraftChapter, key: str) -> list[str]:
    values = _fallback_copy()["languages"].get(chapter.language, {}).get(key)
    if not values:
        raise ValueError(f"{chapter.page_id}: the draft holds no {key} and no fallback exists")
    chapter.fallbacks.append({"page_id": chapter.page_id, "copy": key, "values": " / ".join(values)})
    return list(values)


def _headers(chapter: DraftChapter, table: Tag, key: str, count: int) -> list[dict[str, str]]:
    cells = table.select("thead th")
    texts = [text_of(cell) for cell in cells] if len(cells) == count else fallback(chapter, key)
    return [{"content_html": value, "content_text": value} for value in texts]


def _callout_table(label: str, body: Tag) -> Tag:
    shell = BeautifulSoup(
        '<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">'
        f"<p>{label}</p></td><td class=\"manual-callout-body\"></td></tr></tbody></table>",
        "html.parser",
    )
    target = need(shell.select_one("td.manual-callout-body"), "callout body")
    for section in body.select("div.jp-safety-cell-section"):
        section.unwrap()
    for child in list(body.contents):
        target.append(child.extract())
    return need(shell.table, "callout table")


def safety_rows_as_callouts(chapter: DraftChapter) -> None:
    """Warning and caution pictogram rows become callout strips, as printed JP manuals do.

    The strip carries the signal word; the per-row pictogram has no slot in
    ``HB-CALLOUT-STRIP`` and is counted in the notes.
    """
    for heading in chapter.root.select("h2.jp-warning-heading"):
        label = text_of(heading)
        for icon in heading.find_all("svg"):
            icon.decompose()
        container = need(heading.parent, "warning section")
        for panel in container.select("table.jp-symbol-panel"):
            anchor = panel.find_parent("div", class_="jp-warning-grid") or panel
            for row in panel.find_all("tr"):
                cells = row.find_all("td", recursive=False)
                if row.find("img") is not None:
                    chapter.notes["safety pictograms without a component slot"] += 1
                anchor.insert_before(_callout_table(label, cells[-1]))
            panel.decompose()
            if anchor is not panel and not anchor.select("table.jp-symbol-panel"):
                anchor.decompose()


def callouts(chapter: DraftChapter) -> None:
    for table in chapter.root.select("table.manual-callout-table"):
        for sizer in table.select(".manual-callout-label-sizer"):
            sizer.decompose()
        reference = chapter.source_ref("callout")
        payload = decode_callout_payload(str(table), source_ref=reference)
        spec = require_valid_component_spec(ComponentSpec.from_dict(payload["component_spec"]))
        chapter.claim(spec, (table,))


def signal_tables(chapter: DraftChapter) -> None:
    for table in chapter.root.select("table.jp-signal-table"):
        owner = table.find_parent("div", class_="jp-signal-wrap") or table
        rows: list[dict[str, Any]] = []
        for row in table.select("tbody > tr"):
            label, meaning = need(row.find("th"), "signal label"), need(row.find("td"), "signal meaning")
            rows.append({
                "label": text_of(label), "show_icon": label.find("svg") is not None,
                "meaning_html": inner_html(meaning), "meaning_text": text_of(meaning),
            })
        spec = symbol_signal_component_spec(
            accessibility_label=heading_before(owner),
            headers=_headers(chapter, table, "symbol_signal_headers", 2),
            rows=rows, source_ref=chapter.source_ref("signals"), language=chapter.language,
        )
        chapter.claim(spec, (owner,))


def symbol_panels(chapter: DraftChapter) -> None:
    for grid in chapter.root.select("div.jp-symbol-grid"):
        panels = grid.select("table.jp-symbol-panel")
        refs: list[str] = []
        assets: list[tuple[str, Tag]] = []
        normalized: list[list[dict[str, Any]]] = []
        for panel in panels:
            rows: list[dict[str, Any]] = []
            for row in panel.find_all("tr"):
                icon, meaning = need(row.find("img"), "symbol icon"), row.find_all("td", recursive=False)[-1]
                rows.append({"asset_index": len(refs), "icon_alt": (lines_of(meaning) or [""])[0],
                             "meaning_html": inner_html(meaning), "meaning_text": text_of(meaning)})
                refs.append(attribute(icon, "src"))
                assets.append(("icons", icon))
            normalized.append(rows)
        spec = symbol_icon_component_spec(
            accessibility_label=heading_before(grid),
            headers=_headers(chapter, grid, "symbol_icon_headers", 4),
            panels=normalized, icon_refs=refs,
            source_ref=chapter.source_ref("symbols"), language=chapter.language,
        )
        chapter.claim(spec, (grid,), assets)


def bind_inbox(
    chapter: DraftChapter, owner: Tag, cards: Sequence[tuple[str, Sequence[PageElement | str]]], *,
    accessibility_label: str, tip: tuple[Tag, Tag] | None = None,
) -> None:
    """Replace ``owner`` with the card (and TIP) tables the Inbox renderer checks, and claim them."""

    roles = CARD_ASSET_ROLES if len(cards) == len(CARD_ASSET_ROLES) else (
        (VARIABLE_CARD_ASSET_ROLE,) * len(cards))
    carrier = BeautifulSoup("<table><tbody><tr></tr></tbody></table>", "html.parser")
    row = need(carrier.tr, "inbox row")
    items: list[dict[str, Any]] = []
    assets: list[tuple[str, Tag]] = []
    for role, (source, label) in zip(roles, cards, strict=True):
        cell = carrier.new_tag("td")
        cell.extend(list(label))
        image = carrier.new_tag("img", attrs={"alt": text_of(cell), "src": source})
        cell.insert(0, image)
        if cell.find(["p", "div"]) is None:
            image.insert_after(carrier.new_tag("br"))
        row.append(cell)
        items.append({"image_ref": source, "label": text_of(cell), "alt": text_of(cell)})
        assets.append((role, image))
    tables = [need(carrier.table, "inbox table")]
    if tip is not None:
        tip_table = need(BeautifulSoup("<table><tbody><tr><td></td><td></td></tr></tbody></table>",
                                       "html.parser").table, "inbox tip")
        for cell, source_cell in zip(tip_table.find_all("td"), tip, strict=True):
            cell.extend(list(source_cell.contents))
        tables.append(tip_table)
    spec = inbox_component_spec(
        accessibility_label=accessibility_label, cards=items,
        tip_label=text_of(tables[1].td) if tip else "", tip_body=text_of(tables[1].find_all("td")[1]) if tip else "",
        source_ref=chapter.source_ref("inbox"), language=chapter.language, require_tip=False,
    )
    owner.replace_with(*tables)
    chapter.claim(spec, tables, assets)


def inbox_cards(chapter: DraftChapter) -> None:
    for grid in chapter.root.select("div.jp-inbox-grid"):
        cards = [(attribute(need(card.find("img"), "inbox image"), "src"), [text_of(card.find("figcaption"))])
                 for card in grid.select("figure.jp-inbox-card")]
        bind_inbox(chapter, grid, cards, accessibility_label=heading_before(grid, ("h1",)))


def lcd_icon_tables(chapter: DraftChapter) -> None:
    for figure in chapter.root.select("figure.hb-lcd-table-composition"):
        rows: list[dict[str, Any]] = []
        refs: list[str] = []
        assets: list[tuple[str, Tag]] = []
        number: Tag | None = None
        description: Tag | None = None
        for row in figure.select("table.hb-lcd-icon-table tbody > tr"):
            number = row.select_one("td.hb-lcd-number") or number  # a spanned cell serves each row it spans
            description = row.select_one("td.hb-lcd-description") or description
            icon = need(row.select_one("img"), "LCD icon")
            name = row.select_one("td.hb-lcd-name")
            rows.append({
                "number_html": text_of(number), "number_text": text_of(number),
                "name_html": inner_html(name), "name_text": text_of(name),
                "description_html": inner_html(description), "description_text": text_of(description),
                "icon_alt": text_of(name), "asset_index": len(refs),
            })
            refs.append(attribute(icon, "src"))
            assets.append(("icons", icon))
        spans = {f"{role}_cell_layout": "span-adjacent-equal" for role in ("number", "description")
                 if figure.select_one(f"td.hb-lcd-{role}[rowspan]") is not None}
        spec = lcd_icon_component_spec(
            accessibility_label=heading_before(figure), rows=rows, icon_refs=refs,
            source_ref=chapter.source_ref("lcd-icons"), language=chapter.language, metadata=spans,
        )
        chapter.claim(spec, (figure,), assets)


def lcd_mode_tables(chapter: DraftChapter) -> None:
    for figure in chapter.root.select("figure.hb-lcd-mode-composition"):
        art = need(figure.select_one("img.hb-lcd-mode-art") or figure.find("img"), "LCD mode artwork")
        groups: list[dict[str, Any]] = []
        for row in figure.select("table.hb-lcd-mode-table tbody > tr"):
            state = row.select_one("td.hb-lcd-mode-state")
            if state is not None:
                groups.append({"state_html": inner_html(state), "state_text": text_of(state), "actions": []})
            action, copy = row.select_one("td.hb-lcd-mode-action"), row.select_one("td.hb-lcd-mode-copy")
            groups[-1]["actions"].append({
                "action_html": inner_html(action), "action_text": text_of(action),
                "description_html": inner_html(copy), "description_text": text_of(copy),
            })
        spec = lcd_mode_component_spec(
            accessibility_label=heading_before(figure), groups=groups,
            artwork_ref=attribute(art, "src"), artwork_locale_policy="exact",
            source_ref=chapter.source_ref("lcd-mode"), language=chapter.language,
        )
        chapter.claim(spec, (figure,), (("artwork", art),))


def column_texts(table: Tag, count: int) -> list[list[str]]:
    """Column-major copy of a table body whose cells may span rows."""

    columns: list[list[str]] = [[] for _ in range(count)]
    spans = [0] * count
    for row in table.select("tbody > tr"):
        cells = iter(row.find_all(["td", "th"], recursive=False))
        for column in range(count):
            if spans[column]:
                spans[column] -= 1
                continue
            cell = next(cells, None)
            if cell is None:
                break
            columns[column].append(text_of(cell))
            spans[column] = int(attribute(cell, "rowspan") or 1) - 1
    return columns


def grid_tables(chapter: DraftChapter) -> None:
    """Button combinations and output-resume conditions, declared by their template section."""

    for table in chapter.root.select("table.jp-grid-table"):
        owner = table.find_parent("div", class_="jp-grid-composition") or table
        section_classes = set(classes_of(table.find_parent("section") or table))
        headers = [text_of(cell) for cell in table.select("thead th")]
        if "jp-button-template" in section_classes:
            rows = [[text_of(cell) for cell in row.find_all("td")] for row in table.select("tbody > tr")]
            spec = key_combinations_component_spec(
                headers=headers, rows=rows, source_ref=chapter.source_ref("buttons"), language=chapter.language)
            table["class"] = AttributeValueList(["hb-key-combination-table"])
            if owner is not table:
                owner.replace_with(table.extract())
                owner = table
        elif "jp-output-resume-template" in section_classes:
            spec = auto_resume_component_spec(
                headers=headers, conditions=column_texts(table, len(headers)),
                source_ref=chapter.source_ref("auto-resume"), language=chapter.language)
        else:
            raise ValueError(f"{chapter.page_id}: grid table has no declared template section")
        chapter.claim(spec, (owner,))


def _spec_carrier(title: str, rows: Sequence[Sequence[str]]) -> tuple[Tag, Tag]:
    """The declared specification source shape the shared renderer checks."""

    soup = BeautifulSoup(
        '<h2 class="hb-spec-section"><span class="hb-spec-section-text"></span></h2>'
        "<table><tbody></tbody></table>", "html.parser")
    need(soup.span, "specification title").string = title
    body = need(soup.tbody, "specification body")
    spans = [sum(1 for _ in _continuations(rows, index)) for index in range(len(rows))]
    for index, (label, value) in enumerate(rows):
        row = soup.new_tag("tr")
        if label:
            cell = soup.new_tag("th", attrs={"rowspan": str(spans[index])} if spans[index] > 1 else {})
            cell.string = label
            row.append(cell)
        cell = soup.new_tag("td")
        cell.string = value
        row.append(cell)
        body.append(row)
    return need(soup.h2, "specification heading"), need(soup.table, "specification table")


def _continuations(rows: Sequence[Sequence[str]], index: int) -> Iterator[int]:
    if not rows[index][0]:
        return
    yield index
    following = index + 1
    while following < len(rows) and not rows[following][0]:
        yield following
        following += 1


def declare_plain_table(chapter: DraftChapter, table: Tag, reason: str) -> None:
    chapter.exceptions.append({
        "page_id": chapter.page_id, "language": chapter.language, "kind": "table",
        "text_sha256": table_text_sha256(table), "reason": reason,
    })


def _label_value_rows(table: Tag) -> bool:
    return table.thead is None and all(
        len(row.find_all("td", recursive=False)) == 1 and len(row.find_all("th", recursive=False)) <= 1
        for row in table.find_all("tr"))


def spec_tables(chapter: DraftChapter) -> None:
    """Label/value rows under their own H2 are ``HB-TABLE-SPEC``; any other table is declared."""

    for figure in chapter.root.select("figure.hb-spec-table-composition"):
        table = figure.select_one("table.manual-spec-table, table.hb-spec-table")
        heading = figure.find_previous_sibling()
        if table is None:
            continue
        if not _label_value_rows(table):
            declare_plain_table(chapter, table, "Specification-style table with a header row or more "
                                "than two columns: no registered table component fits.")
            continue
        if heading is None or heading.name != "h2":
            declare_plain_table(chapter, table, "Label/value table without its own section heading: "
                                "HB-TABLE-SPEC needs a source-authored section title.")
            continue
        rows: list[list[str]] = []
        for row in table.find_all("tr"):
            values = lines_of(need(row.find("td"), "specification value")) or [""]
            rows.append([text_of(row.find("th")), values[0]])
            rows.extend(["", value] for value in values[1:])
        spec = spec_table_component_spec(
            section_title=text_of(heading), rows=rows,
            source_ref=chapter.source_ref("specification"), language=chapter.language,
        )
        title, carrier = _spec_carrier(text_of(heading), rows)
        heading.replace_with(title)
        figure.replace_with(carrier)
        chapter.claim(spec, (title, carrier))


def troubleshooting_tables(chapter: DraftChapter) -> None:
    for figure in chapter.root.select("figure.hb-troubleshooting-composition"):
        table = need(figure.select_one("table.hb-troubleshooting-table"), "troubleshooting table")
        header_cells = table.select("thead th") or need(table.find("tr"), "troubleshooting header").find_all("th")
        rows: list[dict[str, Any]] = []
        for row in table.find_all("tr"):
            cells = row.find_all("td", recursive=False)
            if len(cells) == 2:
                rows.append({"code_html": inner_html(cells[0]), "code_text": text_of(cells[0]),
                             "measures_html": inner_html(cells[1]), "measures_text": text_of(cells[1])})
        spec = troubleshooting_component_spec(
            headers=[{"content_html": text_of(cell), "content_text": text_of(cell)} for cell in header_cells],
            rows=rows, source_ref=chapter.source_ref("troubleshooting"), language=chapter.language,
        )
        chapter.claim(spec, (figure,))


_WARRANTY_BLOCK_TAGS = frozenset({"p", "ul", "ol", "h3", "h4", "div", "table"})


def _warranty_block(child: Tag) -> dict[str, Any] | None:
    if child.name in {"ul", "ol"}:
        return {"kind": "list", "html": str(child),
                "items": [text_of(item) for item in child.find_all("li", recursive=False)]}
    if child.name in {"h3", "h4"}:
        return {"kind": "paragraph", "html": f"<p><strong>{inner_html(child)}</strong></p>", "text": text_of(child)}
    return {"kind": "paragraph", "html": str(child), "text": text_of(child)} if text_of(child) else None


def _warranty_blocks(card: Tag) -> list[dict[str, Any]]:
    """Paragraphs and lists in order; copy between blocks (or a text-only card) is a paragraph."""

    blocks: list[dict[str, Any]] = []
    loose: list[str] = []

    def flush() -> None:
        paragraph = BeautifulSoup(f"<p>{''.join(loose).strip()}</p>", "html.parser").p
        if paragraph is not None and text_of(paragraph):
            blocks.append({"kind": "paragraph", "html": str(paragraph), "text": text_of(paragraph)})
        loose.clear()

    for child in card.contents:
        if isinstance(child, Tag) and child.name in _WARRANTY_BLOCK_TAGS:
            flush()
            block = _warranty_block(child)
            if block is not None:
                blocks.append(block)
        else:
            loose.append(str(child))
    flush()
    return blocks


def warranty(chapter: DraftChapter) -> None:
    for intro in chapter.root.select("figure.hb-warranty-intro-composition"):
        spec = warranty_lead_component_spec(
            accessibility_label=heading_before(intro, ("h1",)),
            lead_html=inner_html(intro.select_one(".hb-warranty-intro-panel")),
            local_note_html=inner_html(intro.select_one(".hb-warranty-local-note")),
            source_ref=chapter.source_ref("warranty-lead"), language=chapter.language,
        )
        chapter.claim(spec, (intro,))
    for index, card in enumerate(chapter.root.select("figure.hb-warranty-card"), start=1):
        heading = card.find_previous_sibling()
        if heading is None or heading.name != "h2":
            raise ValueError(f"{chapter.page_id}: warranty card {index} has no adjacent H2")
        spec = warranty_section_component_spec(
            title=text_of(heading), section_index=index, blocks=_warranty_blocks(card),
            source_ref=chapter.source_ref("warranty"), language=chapter.language,
        )
        chapter.claim(spec, (card,))  # the card renders no title; its H2 stays in the flow


def table_text_sha256(table: Tag) -> str:
    """Same identity as ``prepared_style_audit.table_text_sha256`` on the flow table."""

    return hashlib.sha256("".join(table.get_text("").split()).encode("utf-8")).hexdigest()


def declared_plain_tables(chapter: DraftChapter) -> None:
    """The energy-saving threshold table has no registered table component."""

    for table in chapter.root.select("div.jp-energy-table table"):
        declare_plain_table(chapter, table, "Energy-saving threshold table: no registered table component "
                            "fits; declared like the published JP energy-saving tables.")


TABLE_ADAPTERS = (
    safety_rows_as_callouts, signal_tables, symbol_panels, callouts, inbox_cards,
    lcd_icon_tables, lcd_mode_tables, grid_tables, spec_tables, troubleshooting_tables,
    warranty, declared_plain_tables,
)


__all__ = [
    "DraftChapter",
    "TABLE_ADAPTERS",
    "bind_inbox",
    "declare_plain_table",
    "column_texts",
    "css_variables",
    "heading_before",
    "inner_html",
    "lines_of",
    "percent",
    "table_text_sha256",
    "text_of",
]
