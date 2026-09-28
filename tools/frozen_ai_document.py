"""Order a frozen AI extraction into chapters of shared, renderer-neutral flow."""
from __future__ import annotations

import re

from tools.frozen_ai_flow import heading, node, paragraph, prose, root, squash, text
from tools.frozen_ai_source import FrozenBook, _key
from tools.frozen_ai_table_components import (
    specification_flow, symbol_pictogram_flow, troubleshooting_flow,
)
from tools.manual_ir.hashing import value_sha256
from tools.manual_ir.source import SourcePage


def _page(book, identity, nodes):
    return SourcePage(
        page_id=identity, source_ref=f"{book.language}/{identity}",
        source_path=f"frozen-source/{book.language}/{identity}.json",
        language=book.language,
        source_sha256=value_sha256({"manifest": book.manifest, "chapter": identity}),
        blocks=tuple(("flow", root(item)) for item in nodes),
    )


def _introduction(book):
    preface = book.front_back["locales"][book.language]["preface"]["text"]
    preface = re.sub(r"^(?:UA|PT|NL|PL)\s*\n", "", preface)
    preface = re.sub(r"\nВАЖЛИВО\s*$", "", preface)
    # Original paragraph starts, retained from the approved source intake.
    markers = {
        "uk": ("Відповідно до законів", "Зверніть увагу", "* Зображення"),
        "pt": ("Em conformidade", "Observe que", "* As imagens"),
        "nl": ("Volgens de wet", "Houd er rekening", "* De afbeeldingen"),
        "pl": ("Zgodnie z przepisami", "Należy pamiętać", "* Obrazy"),
    }
    for marker in markers.get(book.language, ()):
        preface = preface.replace("\n" + marker, "\n\n" + marker)
    general = book.source["tables"]["specifications"]["groups"]["general"]
    product = general[0]["value"]
    title = f"{product} — {book.locale['label']}"
    links = [node("list_item", [node("link", [text(label)], target=f"#{identity}")])
             for identity, label in zip(book.index["section_ids"], book.locale["titles"], strict=True)]
    return title, [heading(title, level=1), paragraph(f"Model: {book.target['model']} · hello.eu@jackery.com"),
                   heading("Introduction", level=2),
                   *[paragraph(squash(chunk)) for chunk in preface.split("\n\n") if squash(chunk)],
                   heading("Contents", level=2), node("list", links, ordered=False)]


def ordered_pages(book: FrozenBook) -> tuple[str, tuple[SourcePage, ...]]:
    """Interpret extraction coordinates only at intake, never during replay."""
    title, intro = _introduction(book)
    pages = [_page(book, "introduction", intro)]
    starts, sections = book.starts(), []
    chapter, body = -1, []
    figures_seen, operations_seen = set(), set()
    pictograms_seen = False

    def emit_figure(figure):
        if figure["slug"] in figures_seen:
            raise ValueError(f"duplicate source figure: {figure['slug']}")
        body.append(book.figure(figure))
        figures_seen.add(figure["slug"])

    for page in book.source["pages"]:
        number = page["physical_page"]
        blocks = sorted(page["blocks_visual_order"], key=lambda b: (b["bbox"][1], b["bbox"][0]))
        figures = sorted((f for f in book.figures if f["physical_page"] == number
                          and f["section_id"] not in {"lcd_display", "app_setup"}
                          and f["slug"] != "lcd_mode_art"), key=lambda f: f["clip_points"][1])
        notices, consumed = book.callouts(blocks, number)
        position = 0
        for index, block in enumerate(blocks):
            y = block["bbox"][1]
            while (position < len(figures) and figures[position]["clip_points"][1] <= y
                   and chapter >= 0 and figures[position]["section_id"] == starts[chapter][2]):
                emit_figure(figures[position])
                position += 1
            if (chapter + 1 < len(starts) and number == starts[chapter + 1][0]
                    and abs(y - starts[chapter + 1][1]) < 0.01
                    and _key(block["text"]) == _key(book.locale["titles"][chapter + 1])):
                if chapter >= 0:
                    pages.append(_page(book, starts[chapter][2], body))
                chapter += 1
                section = starts[chapter][2]
                sections.append(section)
                body = [heading(book.locale["titles"][chapter], level=2, anchor=section), *book.special(section)]
                if section in {"lcd_display", "app_setup"}:
                    figures_seen.update(f["slug"] for f in book.figures if f["section_id"] == section)
                continue
            if chapter < 0:
                raise ValueError(f"unexpected text before first chapter on {number}")
            section = starts[chapter][2]
            skip = False
            if section == "operations":
                for part, record in book.records["operation_tables"].items():
                    if not isinstance(record, dict) or "source_region" not in record:
                        continue
                    if number == record["physical_page"] and y >= record["source_region"][1] and part not in operations_seen:
                        body.extend(book.operation(part))
                        operations_seen.add(part)
                        if part == "lcd_mode":
                            figures_seen.add("lcd_mode_art")
                    skip |= number == record["physical_page"] and record["source_region"][1] <= y < record["source_region"][3]
            symbols = book.records["symbols"]
            if section == "symbols" and number == symbols["pictogram_page"] and not pictograms_seen:
                body.extend(symbol_pictogram_flow(symbols, headings=book.headers("symbols"),
                            accessibility_label=book.locale["titles"][chapter], icon_refs=book.icon_refs,
                            language=book.language, source_ref=f"{book.language}/symbols/pictograms"))
                pictograms_seen = True
            if (skip or section in {"lcd_display", "app_setup"}
                    or section == "warranty" and number == book.records["warranty_columns"]["physical_page"]
                    or section == "troubleshooting" and number == book.source["tables"][section]["physical_page"] and y >= 250
                    or section == "specifications" and number == book.source["tables"][section]["physical_page"]
                    or section == "symbols" and (number == symbols["physical_page"] and y >= 370
                                                or number == symbols["pictogram_page"] and y < 180)):
                continue
            if index in notices:
                body.append(notices[index])
            elif index not in consumed:
                body.extend(prose(book.correct(squash(block["text"]))))
        for figure in figures[position:]:
            if figure["section_id"] != starts[chapter][2]:
                raise ValueError(f"figure in wrong chapter: {figure['slug']}")
            emit_figure(figure)
        section = starts[chapter][2]
        if section in {"troubleshooting", "specifications"} and number == book.source["tables"][section]["physical_page"]:
            args = {"language": book.language, "source_ref": f"{book.language}/{section}"}
            record = book.source["tables"][section]
            body.extend(troubleshooting_flow(record, headings=book.headers(section), **args) if section == "troubleshooting"
                        else [*specification_flow(record, group_headings=book.headers(section), **args), *book.footnotes()])
    if (sections != book.index["section_ids"] or figures_seen != {f["slug"] for f in book.figures}
            or operations_seen != {"lcd_mode", "restore", "shortcuts"} or not pictograms_seen):
        raise ValueError("incomplete frozen document mapping")
    pages.append(_page(book, starts[chapter][2], body))
    declaration = book.front_back["shared"]["eu_declaration"]["blocks_visual_order"]
    body = [heading("EU declaration and manufacturer", level=2)]
    for block in [declaration[0], *sorted(declaration[1:], key=lambda b: (b["bbox"][1], b["bbox"][0]))]:
        body.extend(prose(block["text"]))
    pages.append(_page(book, "eu-declaration", body))
    return title, tuple(pages)
