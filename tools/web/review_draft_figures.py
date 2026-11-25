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

from collections.abc import Mapping, Sequence
import hashlib
from pathlib import Path
import re
from typing import Any
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


def figure_slug(source: str) -> str:
    if source.startswith("data:"):  # an embedded image is named by its content
        return "figure-" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
    stem = Path(unquote(urlparse(source).path)).stem
    return re.sub(r"[^a-z0-9]+", "-", stem.casefold()).strip("-") or "figure"


def unique_reference_id(chapter: DraftChapter, base: str) -> str:
    """A page shows the same artwork twice under two reference ids."""

    taken = {str(claim.spec.slot("reference_id").content) for claim in chapter.claims
             if claim.spec.component_id == "HB-SPECIAL-REFERENCE-FIGURE"}
    candidate, index = base, 1
    while candidate in taken:
        index += 1
        candidate = f"{base}-{index}"
    return candidate


def bind_reference(
    chapter: DraftChapter, owner: Tag, nodes: Sequence[Tag], image: Tag, config: dict[str, Any],
) -> None:
    """Replace ``owner`` with a reference figure in governed source shape, and claim it.

    The carrier is parsed apart from the page, so the art's neighbours are
    only its own copy (an adjacent paragraph cannot be the page's next one).
    """
    wrapper = BeautifulSoup("", "html.parser")
    marker = wrapper.new_tag("span")
    owner.replace_with(marker)
    wrapper.extend(list(nodes))
    spec, owned, assets, _ = parse_reference_figure_html(
        wrapper, image=image, config=config, source_path=Path(f"{chapter.page_id}.html"),
        language=chapter.language, composite_locale=None, approved_entry=None, approved_path=None,
    )
    marker.replace_with(*nodes)
    chapter.claims.append(ComponentClaim(spec=spec, owned_nodes=owned, asset_tags=assets))


def _reference_figure(chapter: DraftChapter, owner: Tag, art: Tag) -> None:
    """Replace ``owner`` with the governed source shape and bind it with the shared parser."""

    source = attribute(art, "src")
    slug = unique_reference_id(chapter, figure_slug(source))
    captions = [_clean_html(node) for node in owner.select(LIVE_CAPTIONS) if text_of(node)]
    chapter.keep_copy(owner, [text_of(node) for node in owner.select(LIVE_CAPTIONS)], f"figure {slug}")
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


def bind_app_download(
    chapter: DraftChapter, owner: Tag, columns: Mapping[str, tuple[Sequence[Tag], str]], *,
    source_art: str, accessibility_label: str,
) -> None:
    """Replace ``owner`` with the store and QR copy and art the App renderer checks, and claim them.

    ``columns`` maps ``store`` and ``qr`` to the column's paragraphs and art;
    an artwork used for two roles is one tag.
    """
    shell = BeautifulSoup("", "html.parser")
    nodes: list[Tag] = []
    images: dict[str, Tag] = {}

    def image_for(source: str, alt: str) -> Tag:
        if source not in images:
            images[source] = shell.new_tag("img", attrs={"alt": alt, "src": source})
            nodes.append(images[source])
        return images[source]

    copy = []
    for role in ("store", "qr"):
        paragraphs, art = columns[role]
        paragraph = shell.new_tag("p")
        for child in [node for p in paragraphs for node in list(p.contents)]:
            paragraph.append(child.extract())
        copy.append({"role": role, "html": paragraph.decode_contents().strip(), "text": text_of(paragraph)})
        nodes.append(paragraph)
        image_for(art, text_of(paragraph))
    image_for(source_art, accessibility_label)
    spec = app_download_component_spec(
        accessibility_label=accessibility_label, columns=copy, source_art_ref=source_art,
        store_art_ref=columns["store"][1], qr_art_ref=columns["qr"][1],
        source_ref=chapter.source_ref("app-download"), language=chapter.language,
    )
    owner.replace_with(*nodes)
    chapter.claim(spec, nodes, (("source_art", images[source_art]), ("store_art", images[columns["store"][1]]),
                                ("qr_art", images[columns["qr"][1]])))


def app_downloads(chapter: DraftChapter) -> None:
    for figure in chapter.root.select("figure.jp-app-download"):
        columns = figure.select("div.jp-app-col")
        store, qr = figure.select_one("img.jp-app-badges"), figure.select_one("img.jp-app-qr")
        if len(columns) != 2 or store is None or qr is None:
            raise ValueError(f"{chapter.page_id}: App download needs two columns, badges and QR")
        bind_app_download(
            chapter, figure,
            {"store": (columns[0].find_all("p"), attribute(store, "src")),
             "qr": (columns[1].find_all("p"), attribute(qr, "src"))},
            source_art=attribute(store, "src"), accessibility_label=heading_before(figure),
        )


def bind_inline_control(chapter: DraftChapter, paragraph: Tag, icon: Tag, label: str) -> None:
    """The control's label replaces its icon as the paragraph's only emphasis."""

    for emphasis in paragraph.find_all("strong"):
        emphasis.unwrap()
    strong = BeautifulSoup("", "html.parser").new_tag("strong")
    strong.string = label
    icon.replace_with(strong)
    paragraph.attrs.pop("class", None)
    spec = app_inline_control_component_spec(
        accessibility_label=label, paragraph_html=str(paragraph), paragraph_text=text_of(paragraph),
        source_ref=chapter.source_ref("app-control"), language=chapter.language,
    )
    chapter.claim(spec, (paragraph,))


def app_inline_controls(chapter: DraftChapter) -> None:
    for icon in chapter.root.select("p img.jp-inline-plus"):
        paragraph = need(icon.find_parent("p"), "App control paragraph")
        bind_inline_control(chapter, paragraph, icon, attribute(icon, "alt").strip() or "+")


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
    "bind_app_download",
    "bind_inline_control",
    "bind_reference",
    "figure_slug",
    "unique_reference_id",
    "finish",
    "native_panels",
    "reference_figures",
]
