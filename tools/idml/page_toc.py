"""Table-of-contents page for the composed IDML manual.

Entries are collected while the spreads are assembled (title + the spread
cursor it starts on); the TOC spread is then built last and spliced in at
the template's slot (after the preface), renumbering the later spreads.
Folio numbers inherit the exporter's coarse page estimates — like every
frame height here they are close, and the designer nudges the rest.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .params import IDPKG
from .style_names import paragraph_style_ref

# The template's language block headers; entries carry the language they
# were assembled under (the page loop is strictly language-ordered).
_LANG_HEADERS = {"en": "EN  English", "fr": "FR  Français", "es": "ES  Español"}

# Titles for pages that emit no prose h1 of their own.
DATA_TITLES = {
    "spec": "SPECIFICATIONS",
    "lcd": "LCD DISPLAY",
    "trouble": "TROUBLESHOOTING",
    "symbols": "MEANING OF SYMBOLS",
}
OVERVIEW_TITLES = {
    "en": "PRODUCT OVERVIEW",
    "fr": "APERÇU DU PRODUIT",
    "es": "DESCRIPCIÓN GENERAL DEL PRODUCTO",
}
SYMBOL_TITLES = {
    "en": "MEANING OF SYMBOLS",
    "fr": "SIGNIFICATION DES SYMBOLES",
    "es": "SIGNIFICADO DE LOS SÍMBOLOS",
}
_TOC_SLOT = 2  # cover, preface, TOC, then the numbered content pages


@dataclass
class TocCollector:
    entries: list[tuple[str, str, int]] = field(default_factory=list)
    lang: str = "en"
    stem_langs: dict[str, str] = field(default_factory=dict)

    def latch(self, stem_or_title: str) -> None:
        """Adopt the language recorded when the page entered the flow buffer
        (its flush may lag into the next language's assembly)."""
        stem = stem_or_title.split(" + ")[0]
        self.lang = self.stem_langs.get(stem, self.lang)

    def note(self, title: str, spread_index: int,
             lang: str | None = None) -> None:
        """lang overrides the running language — composed pages note right
        after a buffer flush whose latch() may have rewound self.lang."""
        title = (title or "").strip()
        if title:
            self.entries.append((lang or self.lang, title, spread_index))

    def note_h1s(self, blocks: list[tuple[str, str]], spread_index: int,
                 pages: int = 1) -> None:
        """Multiple h1s inside one flowed story land on later chained pages;
        spread them proportionally by block position (coarse, like every
        height estimate here)."""
        total = max(1, len(blocks))
        for bi, (kind, text) in enumerate(blocks):
            if kind == "h1":
                offset = min(max(0, pages - 1), int(pages * bi / total))
                self.note(text, spread_index + offset)


def _segments(entries: list[tuple[str, str, int]]) -> list[tuple[str, list[tuple[str, int]]]]:
    segments: list[tuple[str, list[tuple[str, int]]]] = []
    for lang, title, idx in entries:
        if not segments or segments[-1][0] != lang:
            segments.append((lang, []))
        segments[-1][1].append((title, idx))
    return segments


def _folio(spread_index: int) -> int:
    # Recorded before the TOC splice: cover=0, preface=1, content from 2;
    # after splicing the TOC at slot 2 the first content page becomes
    # spread 3 = folio 01.
    return max(1, spread_index - 1)


def _entry_psr(title: str, folio: int, col_w: float) -> str:
    style = paragraph_style_ref("HB Spec Label")
    leader = (
        '<Properties><TabList type="list"><ListItem type="record">'
        '<Alignment type="enumeration">RightAlign</Alignment>'
        '<AlignmentCharacter type="string">.</AlignmentCharacter>'
        '<Leader type="string">.</Leader>'
        f'<Position type="unit">{col_w - 2:.1f}</Position>'
        "</ListItem></TabList></Properties>"
    )
    safe = title.replace("&", "&amp;").replace("<", "&lt;")
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style}">{leader}'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        f"<Content>{safe}\t{folio:02d}</Content><Br/>"
        "</CharacterStyleRange></ParagraphStyleRange>\n"
    )


def finalize(writer, collector: TocCollector, add_story_parts, psr) -> bool:
    """Build the TOC spread and splice it into the template slot."""
    segments = _segments(collector.entries)
    if not segments or len(writer.spreads) <= _TOC_SLOT:
        return False

    body_x = 27.4
    body_w = writer.page_w - body_x * 2
    col_w = (body_w - 12.0) / 2.0
    y = 24.0
    frames: list[str] = []
    title_sid = add_story_parts(
        "st_toc_title", "TOC title", [psr("HB Capsule Text", "TABLE OF CONTENTS", terminal=True)])
    frames.append(writer._frame_xml(
        "tf_toc_title", title_sid, *writer._page_rect(body_x, y, body_w, 20.0),
        fill="Color/HB Brand Dark", rounded=True, valign="CenterAlign",
        inset=(1, 7, 1, 7)))
    y += 30.0

    for si, (seg_lang, segment) in enumerate(segments):
        header = _LANG_HEADERS.get(seg_lang, seg_lang.upper())
        folios = [_folio(i) for _, i in segment]
        rng = f"{min(folios):02d}-{max(folios):02d}"
        bar_sid = add_story_parts(
            f"st_toc_bar_{si}", f"TOC bar {si}",
            [psr("HB Capsule Text", f"{header}\t{rng}", terminal=True)])
        frames.append(writer._frame_xml(
            f"tf_toc_bar_{si}", bar_sid,
            *writer._page_rect(body_x, y, body_w, 14.0),
            fill="Color/HB Brand Dark", rounded=True, inset=(1, 5, 1, 6)))
        y += 20.0
        half = (len(segment) + 1) // 2
        for ci, chunk in enumerate((segment[:half], segment[half:])):
            if not chunk:
                continue
            xml = "".join(_entry_psr(t, _folio(i), col_w) for t, i in chunk)
            sid = add_story_parts(f"st_toc_seg{si}_c{ci}", f"TOC {si}/{ci}", [xml])
            frames.append(writer._frame_xml(
                f"tf_toc_seg{si}_c{ci}", sid,
                *writer._page_rect(body_x + ci * (col_w + 12.0), y,
                                   col_w, 9.0 * half + 4.0),
                inset=(0, 0, 0, 0)))
        y += 9.0 * half + 14.0

    spread_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="sp_toc" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
        f'  <Page Self="sp_toc_pg" Name="{_TOC_SLOT + 1}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} {-writer.page_h / 2:g}"/>\n'
        + "".join(frames) +
        "</Spread>\n"
        "</idPkg:Spread>\n"
    )

    renumbered: list[tuple[str, str]] = []
    for sid, xml in writer.spreads[_TOC_SLOT:]:
        match = re.fullmatch(r"sp_(\d+)", sid)
        if match:
            n = int(match.group(1))
            xml = xml.replace(f'Self="sp_{n}"', f'Self="sp_{n + 1}"')
            xml = xml.replace(f'Self="sp_{n}_pg"', f'Self="sp_{n + 1}_pg"')
            xml = xml.replace(f'Name="{n + 1}"', f'Name="{n + 2}"', 1)
            sid = f"sp_{n + 1}"
        renumbered.append((sid, xml))
    writer.spreads[_TOC_SLOT:] = [("sp_toc", spread_xml)] + renumbered
    return True
