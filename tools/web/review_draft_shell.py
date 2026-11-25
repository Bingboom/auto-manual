"""Where a review draft (审核稿) keeps its manual copy: content root and chapters.

The JHP-3600C shell holds its chapters in ``article#furo-main-content > div``;
newer shells hold them directly in ``main#furo-main-content``, beside review
asides and an appendix the review layer removes. Copy outside any chapter
(a model note, a preface) is kept: see ``_chapter_sections``.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import TypeGuard

from bs4 import BeautifulSoup, Tag
from bs4.element import PageElement

from tools.web.review_draft_overlay import ReviewLayerReport, strip_review_layer

CONTENT_ROOTS = ("article#furo-main-content", "main#furo-main-content")


def _is_chapter(node: PageElement) -> TypeGuard[Tag]:
    return isinstance(node, Tag) and node.name == "section" and bool(node.get("id"))


def _has_content(nodes: Sequence[PageElement]) -> bool:
    return any(isinstance(node, Tag) and bool(node.get_text(strip=True) or node.find("img"))
               for node in nodes)


def _chapter_sections(body: Tag) -> list[Tag]:
    """Top-level chapters; copy outside any chapter joins the chapter after it.

    A run of such copy that opens with an identified heading (a preface) is a
    chapter of its own.
    """

    chapters: list[Tag] = []
    loose: list[PageElement] = []
    for node in list(body.children):
        if not _is_chapter(node):
            loose.append(node)
            continue
        if _has_content(loose):
            heading = next((item for item in loose if isinstance(item, Tag)
                            and item.name in {"h1", "h2"} and item.get("id")), None)
            if heading is not None:
                front = BeautifulSoup("", "html.parser").new_tag("section", attrs={"id": str(heading["id"])})
                for item in loose:
                    front.append(item.extract())
                node.insert_before(front)
                chapters.append(front)
            else:
                for item in reversed(loose):
                    node.insert(0, item.extract())
        loose = []
        chapters.append(node)
    if chapters and _has_content(loose):
        for item in loose:
            chapters[-1].append(item.extract())
    return chapters


def manual_chapters(soup: BeautifulSoup, *, source: str) -> tuple[list[Tag], ReviewLayerReport]:
    """The draft's chapters with the review layer stripped, and what stripping found."""

    root = next((node for node in map(soup.select_one, CONTENT_ROOTS) if node is not None), None)
    if root is None:
        raise ValueError(f"{source}: no manual article ({' or '.join(CONTENT_ROOTS)})")
    layer = strip_review_layer(root)
    body = root
    if not any(_is_chapter(node) for node in root.children):
        body = root.find("div", recursive=False) or root
    sections = _chapter_sections(body)
    if not sections:
        raise ValueError(f"{source}: the manual article has no chapter sections")
    return sections, layer


__all__ = ["CONTENT_ROOTS", "manual_chapters"]
