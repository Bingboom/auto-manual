"""Bind a stripped review draft's figures and App blocks to shared components.

A typeset crop keeps its printed labels inside the artwork, so it becomes an
``HB-SPECIAL-REFERENCE-FIGURE`` with embedded captions. Copy the draft lays
over a crop (operation notes, charging captions, accessory names, the
frequency label) becomes that figure's live captions. App download panels and
inline App controls use ``HB-SPECIAL-APP``. Accessible labels come from the
draft's Japanese headings, never from its reviewer-facing alt text.

``finish`` runs last: decorative inline SVG leaves, empty paragraphs go, and
every class outside the shared Web theme is dropped, so plain flow passes the
prepared-document shared-style gate.
"""
from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList

from tools.component_specs.app import (
    app_download_component_spec,
    app_inline_control_component_spec,
)
from tools.component_specs.reference_figure_html import parse_reference_figure_html
from tools.manual_ir.whole_document_components import ComponentClaim
from tools.web.prepared_style_audit import GENERIC_CLASSES, shared_classes
from tools.web.review_draft_blocks import DraftChapter, attribute, classes_of, heading_before, need, text_of

LIVE_CAPTIONS = ".jp-ts-slot, .jp-acc-label, .jp-acc-sold, .jp-native-frequency"
_LOOSE_IMAGE_PARENTS = frozenset({"p", "figure", "td", "th", "a", "li", "span", "strong",
                                  "h1", "h2", "h3", "h4", "h5", "h6"})


def _clean_html(node: Tag) -> str:
    """Inner HTML without draft classes or ids, for copy placed inside a slot."""

    copy = BeautifulSoup(node.decode_contents(), "html.parser")
    for tag in copy.find_all(True):
        for name in ("class", "id"):
            tag.attrs.pop(name, None)
    paragraphs = copy.find_all("p")
    if paragraphs and len(paragraphs) == len(copy.find_all(True, recursive=False)):
        return "<br/>".join(p.decode_contents().strip() for p in paragraphs)
    return str(copy).strip()


def _claimed(chapter: DraftChapter, node: Tag) -> bool:
    owned = {id(owner) for claim in chapter.claims for owner in claim.owned_nodes}
    return any(id(candidate) in owned for candidate in (node, *node.parents))


def _slug(source: str) -> str:
    stem = Path(unquote(urlparse(source).path)).stem
    return re.sub(r"[^a-z0-9]+", "-", stem.casefold()).strip("-") or "figure"


def _reference_figure(chapter: DraftChapter, owner: Tag, art: Tag) -> None:
    """Replace ``owner`` with the governed source shape and bind it with the shared parser."""

    source = attribute(art, "src")
    slug = _slug(source)
    captions = [_clean_html(node) for node in owner.select(LIVE_CAPTIONS) if text_of(node)]
    shell = BeautifulSoup("", "html.parser")
    image = shell.new_tag("img", attrs={"alt": heading_before(owner) or slug, "src": source})
    nodes: list[Tag] = [image]
    if captions:
        block = shell.new_tag("div", attrs={"class": "line-block"})
        for html in captions:
            block.append(need(BeautifulSoup(f'<div class="line">{html}</div>', "html.parser").div, "caption"))
        nodes.append(block)
    owner.replace_with(*nodes)
    spec, owned, assets, _ = parse_reference_figure_html(
        chapter.root, image=image,
        config={"id": slug, "image_key": f"{chapter.image_key_prefix}/{slug}",
                "captions_embedded": not captions, "capture_following_lines": len(captions)},
        source_path=Path(f"{chapter.page_id}.html"), language=chapter.language,
        composite_locale=None, approved_entry=None, approved_path=None,
    )
    chapter.claims.append(ComponentClaim(spec=spec, owned_nodes=owned, asset_tags=assets))


def app_downloads(chapter: DraftChapter) -> None:
    for figure in chapter.root.select("figure.jp-app-download"):
        columns = figure.select("div.jp-app-col")
        store, qr = figure.select_one("img.jp-app-badges"), figure.select_one("img.jp-app-qr")
        if len(columns) != 2 or store is None or qr is None:
            raise ValueError(f"{chapter.page_id}: App download needs two columns, badges and QR")
        shell = BeautifulSoup("", "html.parser")
        nodes: list[Tag] = []
        copy = []
        for role, column, art in zip(("store", "qr"), columns, (store, qr), strict=True):
            paragraph = shell.new_tag("p")
            for child in [node for p in column.find_all("p") for node in list(p.contents)]:
                paragraph.append(child.extract())
            copy.append({"role": role, "html": paragraph.decode_contents().strip(), "text": text_of(paragraph)})
            nodes += [paragraph, shell.new_tag("img", attrs={"alt": text_of(paragraph), "src": attribute(art, "src")})]
        spec = app_download_component_spec(
            accessibility_label=heading_before(figure), columns=copy,
            source_art_ref=attribute(nodes[1], "src"), store_art_ref=attribute(nodes[1], "src"),
            qr_art_ref=attribute(nodes[3], "src"),
            source_ref=chapter.source_ref("app-download"), language=chapter.language,
        )
        figure.replace_with(*nodes)
        chapter.claim(spec, nodes, (("source_art", nodes[1]), ("store_art", nodes[1]), ("qr_art", nodes[3])))


def app_inline_controls(chapter: DraftChapter) -> None:
    for icon in chapter.root.select("p img.jp-inline-plus"):
        paragraph = need(icon.find_parent("p"), "App control paragraph")
        label = attribute(icon, "alt").strip() or "+"
        for emphasis in paragraph.find_all("strong"):
            emphasis.unwrap()  # the shared control owns the paragraph's only emphasis
        strong = need(BeautifulSoup(f"<strong>{label}</strong>", "html.parser").strong, "App control label")
        icon.replace_with(strong)
        paragraph.attrs.pop("class", None)
        spec = app_inline_control_component_spec(
            accessibility_label=label, paragraph_html=str(paragraph), paragraph_text=text_of(paragraph),
            source_ref=chapter.source_ref("app-control"), language=chapter.language,
        )
        chapter.claim(spec, (paragraph,))


def native_panels(chapter: DraftChapter) -> None:
    """A restored JP panel: its note precedes the figure, its label is a live caption."""

    for panel in chapter.root.select("div.jp-native-panel"):
        for note in panel.select("div.jp-native-note"):
            panel.insert_before(note.extract())
        art = panel.find("img")
        if art is None:
            raise ValueError(f"{chapter.page_id}: native panel has no artwork")
        _reference_figure(chapter, panel, art)


def reference_figures(chapter: DraftChapter) -> None:
    for wrapper in chapter.root.select("div.us-op"):
        wrapper.unwrap()
    for figure in chapter.root.find_all("figure"):
        images = figure.find_all("img")
        if not _claimed(chapter, figure) and len(images) == 1:
            _reference_figure(chapter, figure, images[0])
    for image in chapter.root.find_all("img"):
        parent = image.parent
        if (parent is not None and parent.name not in _LOOSE_IMAGE_PARENTS
                and not _claimed(chapter, image)):
            _reference_figure(chapter, image, image)


def finish(chapter: DraftChapter) -> None:
    """Make plain flow shared-theme clean; component carriers stay as their parsers bound them."""

    for icon in chapter.root.find_all("svg"):
        chapter.notes["decorative inline svg"] += 1
        icon.decompose()
    known = shared_classes() | GENERIC_CLASSES
    for node in list(chapter.root.find_all(True)):
        if node.decomposed or _claimed(chapter, node):
            continue
        if node.name == "p" and not text_of(node) and node.find("img") is None:
            node.decompose()
            continue
        classes = [name for name in classes_of(node) if name in known]
        if classes:
            node["class"] = AttributeValueList(classes)
        else:
            node.attrs.pop("class", None)


FIGURE_ADAPTERS = (app_downloads, app_inline_controls, native_panels, reference_figures, finish)


__all__ = [
    "FIGURE_ADAPTERS",
    "LIVE_CAPTIONS",
    "app_downloads",
    "app_inline_controls",
    "finish",
    "native_panels",
    "reference_figures",
]
