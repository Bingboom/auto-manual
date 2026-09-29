"""Order fresh PDF copy and governed media events into neutral source pages.

The book owns extraction, approved errata and component construction. This
module consumes only declared PDF rectangles, never screenshot manifests or a
fixed figure count. A chapter's outer heading is owned here; full LCD/App and
warranty bodies are supplied by ``special``. Inbox/Overview media consume their
declared rectangles and leave surrounding source copy available to the flow.
"""
from __future__ import annotations

from pathlib import Path
import re

from tools.frozen_ai_flow import heading, prose, root, squash
from tools.frozen_pdf_frontmatter import preface_flow, strong_paragraph, template_heading_levels
from tools.frozen_ai_table_components import (
    specification_flow, symbol_pictogram_flow, troubleshooting_flow,
)
from tools.manual_ir.source import SourcePage
from tools.utils.path_utils import review_dir_of


_SECTIONS = (
    "safety", "symbols", "in_the_box", "product_overview", "lcd_display",
    "operations", "ups", "charging", "storage", "troubleshooting",
    "specifications", "warranty", "app_setup",
)

_EMERGENCY_CHARGING_LABELS = {
    "uk": "Режим аварійного заряджання",
    "pt": "Modo de carregamento de emergência",
    "nl": "Noodoplaadmodus",
    "pl": "Tryb ładowania awaryjnego",
}


def _body_prose(value, section, language):
    # The Ukrainian PDF joins this bold lead and its body in one text block;
    # the other three PDFs give it a separate block. Preserve both shapes.
    label = _EMERGENCY_CHARGING_LABELS.get(language)
    if section == "charging" and label and (value == label or value.startswith(label + " ")):
        return [strong_paragraph(label), *prose(value[len(label):].strip())]
    return prose(value)


def _key(value):
    return re.sub(r"\W+", "", squash(value), flags=re.UNICODE).casefold()


def _page(book, identity, nodes):
    source_path = getattr(book, "source_path", None)
    path = (source_path(identity) if callable(source_path) else
            review_dir_of(Path("frozen-pdf")) / book.target["model"] / book.target["region"] /
            book.language / f"{identity}.json")
    return SourcePage(
        page_id=identity, source_ref=f"{book.language}/{identity}",
        source_path=str(path), language=book.language,
        source_sha256=book.source["source_sha256"],
        blocks=tuple(("flow", root(template_heading_levels(item))) for item in nodes),
    )


def _introduction(book):
    preface = book.front_back["locales"][book.language]["preface"]["text"]
    product = book.source["tables"]["specifications"]["groups"]["general"][0]["value"]
    title = f"{product} — {book.locale['label']}"
    # Product identity remains document metadata, as on the template route.
    # The body opens with the source IMPORTANT label and separated paragraphs.
    return title, preface_flow(preface, book.correct)


def _owns(region, page, bbox, section):
    x0, y0, x1, y1 = region["consume_bbox"]
    return (region["physical_page"] == page and region.get("section", section) == section
            and x0 <= bbox[0] < x1 and y0 <= bbox[1] < y1)


def _table_events(book, starts):
    """Every structured table is an explicit event, even on an empty body page."""
    result = []
    symbols = book.records["symbols"]
    result.append((symbols["pictogram_page"], 0, "symbols", "pictograms", lambda: symbol_pictogram_flow(
        symbols, headings=book.headers("symbols"), accessibility_label=book.locale["titles"][1],
        icon_refs=book.icon_refs, language=book.language, source_ref=f"{book.language}/symbols/pictograms",
    )))
    operations = {key: value for key, value in book.records["operation_tables"].items()
                  if isinstance(value, dict) and "source_region" in value}
    if set(operations) != {"lcd_mode", "restore", "shortcuts"}:
        raise ValueError("incomplete PDF operation table recipe")
    for part, record in operations.items():
        result.append((record["physical_page"], record["source_region"][1], "operations",
                       f"table-{part}", lambda part=part: book.operation(part)))
    for section in ("troubleshooting", "specifications"):
        record = book.source["tables"][section]
        args = {"language": book.language, "source_ref": f"{book.language}/{section}"}
        if section == "troubleshooting":
            build = lambda record=record, args=args: troubleshooting_flow(record, headings=book.headers("troubleshooting"), **args)
            y = 250
        else:
            build = lambda record=record, args=args: [
                *specification_flow(record, group_headings=book.headers("specifications"), **args), *book.footnotes(),
            ]
            y = next(start[1] for start in starts if start[2] == section) + .01
        result.append((record["physical_page"], y, section, section, build))
    return result


def _structured_region(book, section, number, bbox):
    y = bbox[1]
    if section == "safety" and getattr(book, "source_kind", None) == "frozen-pdf-json":
        return True
    if section in {"lcd_display", "app_setup", "warranty", "specifications"}:
        return True
    if section == "troubleshooting":
        return number == book.source["tables"][section]["physical_page"] and y >= 250
    if section == "symbols":
        symbols = book.records["symbols"]
        return (number == symbols["physical_page"] and y >= 370
                or number == symbols["pictogram_page"] and y < 180)
    if section == "operations":
        return any(isinstance(record, dict) and "source_region" in record
                   and number == record["physical_page"]
                   and record["source_region"][0] <= bbox[0] < record["source_region"][2]
                   and record["source_region"][1] <= y < record["source_region"][3]
                   for record in book.records["operation_tables"].values())
    return False


def ordered_pages(book) -> tuple[str, tuple[SourcePage, ...]]:
    """Consume book methods and positioned events without revisiting the PDF.

    New book methods: ``media_section(section)``, ``operation_panels()`` and
    ``consumed_media_regions()``. Optional ``figures``/``figure(record)`` carry
    only governed reference figures and have no expected inventory size.
    """
    starts = list(book.starts())
    if (tuple(book.index["section_ids"]) != _SECTIONS or len(starts) != len(_SECTIONS)
            or [s[2] for s in starts] != list(_SECTIONS) or starts != sorted(starts)
            or len(book.locale["titles"]) != len(_SECTIONS)):
        raise ValueError("incomplete PDF chapter mapping")
    title, introduction = _introduction(book)
    pages = [_page(book, "introduction", introduction)]
    regions = list(book.consumed_media_regions())
    panels = list(book.operation_panels())
    regions += [{"physical_page": event["physical_page"], "section": "operations",
                 "consume_bbox": event["consume_bbox"]} for event in panels]
    events = []
    for index, (number, y, section) in enumerate(starts):
        events.append((number, y, 0, index, "chapter", section))
    for number, y, section, identity, build in _table_events(book, starts):
        events.append((number, y, 1, len(events), "content", (section, identity, build)))
    for index, event in enumerate(panels):
        events.append((event["physical_page"], event["y"], 1, len(events), "content",
                       ("operations", f"panel-{index}", lambda event=event: [event["node"]])))
    figures = list(getattr(book, "figures", ()))
    if len({figure["slug"] for figure in figures}) != len(figures):
        raise ValueError("duplicate PDF reference figure identity")
    for figure in figures:
        events.append((figure["physical_page"], figure["clip_points"][1], 1, len(events), "content",
                       (figure["section_id"], f"figure-{figure['slug']}", lambda figure=figure: [book.figure(figure)])))
    for page in book.source["pages"]:
        number = page["physical_page"]
        blocks = sorted(page["blocks_visual_order"], key=lambda b: (b["bbox"][1], b["bbox"][0]))
        notices, consumed = book.callouts(blocks, number)
        for index, block in enumerate(blocks):
            events.append((number, block["bbox"][1], 2, len(events), "block",
                           (block, notices.get(index), index in consumed)))
    body, chapter, seen, headings_seen = [], -1, set(), set()
    for number, y, _priority, _sequence, kind, payload in sorted(events):
        if kind == "chapter":
            if chapter >= 0:
                pages.append(_page(book, starts[chapter][2], body))
            chapter += 1
            section = starts[chapter][2]
            media = book.media_section(section)
            special = list(book.special(section))
            if section in {"symbols", "lcd_display", "app_setup", "warranty"} and not special:
                raise ValueError(f"PDF chapter {section} has no structured body")
            if section in {"in_the_box", "product_overview"} and not media:
                raise ValueError(f"PDF chapter {section} has no governed media body")
            body = [heading(book.locale["titles"][chapter], level=2, anchor=section),
                    *special, *(media or [])]
            continue
        if chapter < 0:
            if kind == "block" and not any(c.isalpha() for c in squash(payload[0]["text"])):
                continue  # Printer glyphs/page marks preceding the first heading.
            raise ValueError(f"unmapped PDF content before first chapter on {number}")
        section = starts[chapter][2]
        if kind == "content":
            owner, identity, build = payload
            if owner != section or identity in seen:
                raise ValueError(f"PDF event {identity} is duplicated or outside chapter {owner}")
            seen.add(identity)
            nodes = list(build())
            if not nodes:
                raise ValueError(f"PDF event {identity} produced no content")
            body.extend(nodes)
            continue
        block, notice, consumed = payload
        if (number == starts[chapter][0] and abs(y - starts[chapter][1]) < .01
                and _key(block["text"]) == _key(book.locale["titles"][chapter])):
            if section in headings_seen:
                raise ValueError(f"duplicate PDF chapter heading: {section}")
            headings_seen.add(section)
            continue
        if (_structured_region(book, section, number, block["bbox"])
                or any(_owns(region, number, block["bbox"], section) for region in regions)):
            continue
        if notice is not None:
            body.append(notice)
        elif not consumed:
            body.extend(_body_prose(book.correct(squash(block["text"])), section, book.language))
    if headings_seen != set(_SECTIONS):
        raise ValueError("incomplete PDF chapter heading coverage")
    pages.append(_page(book, starts[chapter][2], body))
    declaration = book.front_back["shared"]["eu_declaration"]["blocks_visual_order"]
    body = [heading("EU declaration and manufacturer", level=2)]
    for block in sorted(declaration, key=lambda b: (b["bbox"][1], b["bbox"][0])):
        body.extend(prose(book.correct(block["text"])))
    pages.append(_page(book, "eu-declaration", body))
    return title, tuple(pages)


__all__ = ["ordered_pages"]
