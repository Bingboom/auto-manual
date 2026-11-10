"""The reading frame around a verified single-language manual page (2026-11).

tools/rtd/portal.py decorates each verified manual page; this module builds what
the frame shows around the manual (manual_reader.html): a top bar with the
product, market, language and version, a chapter list read from the page's
rendered sections and headings, the feedback card and a footer. The manual body
itself is never changed: it stays the only main region
(``article#furo-main-content``), so the knowledge and search extractors read
exactly the manual text.
"""
from __future__ import annotations

from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Any

import yaml

TEXT_NAME = "manual_reader_text.yaml"
FALLBACK_LANGUAGE = "en"
_PLACEHOLDERS = {"chapters": "{n}", "email": "{address}"}
_GIT_DATE = re.compile(r"git-(\d{4})(\d{2})(\d{2})-")
_HEADINGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
# Heading parts that are not its name: Sphinx's permalink and the source's model label.
_UNNAMED = frozenset({"headerlink", "hb-heading-model"})


def version_date(version: str) -> str | None:
    """``git-20261027-36f9aa96-battery-symbol`` reads as ``2026-10-27``; other versions have no date."""
    match = _GIT_DATE.match(version or "")
    return "-".join(match.groups()) if match else None


class _Section:
    """A listed place in the manual: a section, or a heading with its own id."""

    __slots__ = ("id", "title", "named", "entries", "flat")

    def __init__(self, anchor: str | None, title: str = "") -> None:
        self.id, self.title, self.named = anchor, title, bool(title)
        self.entries: list[_Section] = []
        self.flat: list[tuple[int, _Section]] = []  # this section's open id'd headings, by rank


class _Outline(HTMLParser):
    """The rendered manual body's sections and id'd headings, in reading order.

    A section links by its id (else its title heading's) and is named by its first heading. Raw-HTML
    manuals also mark chapters with headings that carry their own id: such a heading is an entry of the
    section it sits in, under the nearest earlier one of a higher rank. A section without an id or a name
    hands its entries to its parent; headings outside every section (page furniture such as the product
    suggestion form) are not listed. A name leaves out the heading's permalink and its model label, which
    the top bar already shows.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.page = _Section(None)
        self.page.named = True
        self.open = [self.page]
        self.heading: tuple[str, str | None, list[str]] | None = None
        self.unnamed: list = []  # [tag, depth] while inside a heading part that is not its name

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "section":
            outer = self.open[-1]
            outer.named, outer.flat = True, []  # a nested section ends the outer one's headings
            self.open.append(_Section(values.get("id")))
        elif self.heading is None:
            if tag in _HEADINGS:
                self.heading = (tag, values.get("id"), [])
        elif self.unnamed:
            if tag == self.unnamed[0]:
                self.unnamed[1] += 1
        elif _UNNAMED.intersection((values.get("class") or "").split()) or values.get("data-source-layout") == "model":
            self.unnamed = [tag, 1]
        elif tag == "br":
            self.heading[2].append(" ")

    def handle_endtag(self, tag):
        if tag == "section":
            self._close_section()
        elif self.heading is not None and tag == self.heading[0]:
            self._close_heading()
        elif self.unnamed and tag == self.unnamed[0]:
            self.unnamed[1] -= 1
            if not self.unnamed[1]:
                self.unnamed = []

    def handle_data(self, data):
        if self.heading is not None and not self.unnamed:
            self.heading[2].append(data)

    def close(self):
        super().close()
        while len(self.open) > 1:
            self._close_section()

    def _close_section(self) -> None:
        if len(self.open) == 1:
            return  # an unmatched </section> in raw HTML
        section = self.open.pop()
        outer = self.open[-1]
        if section.id and section.title:
            outer.entries.append(section)
        else:
            outer.entries.extend(section.entries)

    def _close_heading(self) -> None:
        tag, anchor, parts = self.heading
        self.heading, self.unnamed = None, []
        title = " ".join("".join(parts).split())
        section = self.open[-1]
        if not section.named:
            section.named, section.title, section.id = True, title, section.id or anchor
        elif anchor and title and section is not self.page:
            entry, rank = _Section(anchor, title), int(tag[1])
            while section.flat and section.flat[-1][0] >= rank:
                section.flat.pop()
            (section.flat[-1][1] if section.flat else section).entries.append(entry)
            section.flat.append((rank, entry))


def chapters(body: str) -> list[dict[str, Any]]:
    """The manual's chapters with their sections, as the rendered ids and titles the list links to.

    A manual that puts every chapter under one title section lists that title's entries instead. A page
    with fewer than two chapters lists none, and the frame then shows no chapter list.
    """
    outline = _Outline()
    outline.feed(body or "")
    outline.close()
    top = outline.page.entries
    if len(top) == 1 and top[0].entries:
        top = top[0].entries
    listed = [{"id": item.id, "title": item.title,
               "subs": [{"id": sub.id, "title": sub.title} for sub in item.entries]} for item in top]
    return listed if len(listed) > 1 else []


@lru_cache(maxsize=None)
def load_text(assets: Path) -> dict[str, dict[str, str]]:
    """The frame's own words by language (manual_reader_text.yaml); every set gives every English key."""
    table = yaml.safe_load((assets / TEXT_NAME).read_text(encoding="utf-8"))
    keys = set(table[FALLBACK_LANGUAGE])
    for lang, words in table.items():
        if set(words) != keys:
            raise ValueError(f"{TEXT_NAME}: {lang} must give exactly the {FALLBACK_LANGUAGE} keys")
        for key, placeholder in _PLACEHOLDERS.items():
            if placeholder not in words[key]:
                raise ValueError(f"{TEXT_NAME}: {lang}.{key} must contain {placeholder}")
    return table


def frame_text(table: dict[str, dict[str, str]], lang: str) -> tuple[str, dict[str, str]]:
    """The frame's words in the manual's language, else in English, with the language they are in."""
    shown = lang if lang in table else FALLBACK_LANGUAGE
    return shown, table[shown]


def locale_options(product: dict, active: dict, pathto) -> list[dict[str, Any]]:
    """The language select: one option per verified publication of the product, the current one selected."""
    options = []
    for item in product["language_options"]:
        url = pathto(item["url"][:-5])
        if url == "#":
            url = Path(item["url"]).name
        options.append({"url": url, "display": item["display"], "selected": item["url"] == active["url"]})
    return options


def reader_context(*, product: dict, active: dict, lang_label: str, direction: str, options: list[dict[str, Any]],
                   body: str, text: tuple[str, dict[str, str]], feedback: str, library: str,
                   search: str) -> dict[str, Any]:
    """What manual_reader.html shows around the manual body.

    The frame speaks the manual's language (``text`` from frame_text, with the language it is in); the chapter
    list keeps the manual's own titles.
    """
    version = active.get("version") or ""
    listed = chapters(body)
    shown, words = text
    return {
        "name": product.get("name") or "", "model": active["model"], "region": active["region"],
        "lang": active["lang"], "dir": direction, "ui_lang": shown, "text": words,
        "lang_label": lang_label, "version": version, "version_date": version_date(version),
        "options": options, "chapters": listed, "count": words["chapters"].replace("{n}", str(len(listed))),
        "feedback": feedback, "library": library, "search": search,
    }


__all__ = ["chapters", "frame_text", "load_text", "locale_options", "reader_context", "version_date"]
