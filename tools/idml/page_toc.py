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
from xml.sax.saxutils import escape

from .params import IDPKG
from . import page_objects as _po
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


def _entry_psr(title: str, folio: int | str, col_w: float) -> str:
    style = paragraph_style_ref("HB TOC Entry")
    available = col_w - 8.0
    point_size = min(6.5, available / max(1.0, len(title) * 0.56))
    point_size = max(5.4, point_size)
    leader = (
        '<Properties><TabList type="list"><ListItem type="record">'
        '<Alignment type="enumeration">RightAlign</Alignment>'
        '<AlignmentCharacter type="string">.</AlignmentCharacter>'
        '<Leader type="string">. </Leader>'
        f'<Position type="unit">{col_w - 2:.1f}</Position>'
        "</ListItem></TabList></Properties>"
    )
    safe = title.replace("&", "&amp;").replace("<", "&lt;")
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style}">{leader}'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'PointSize="{point_size:.3f}">'
        f"<Content>{safe}\t{str(folio).zfill(2)}</Content><Br/>"
        "</CharacterStyleRange></ParagraphStyleRange>\n"
    )


def _bar_psr(code: str, label: str) -> str:
    style = paragraph_style_ref("HB TOC Bar")
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style}">'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'PointSize="12" FontStyle="Bold"><Content>{escape(code)}</Content></CharacterStyleRange>'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'PointSize="7" FontStyle="SemiBold"><Content>\u00a0\u00a0\u00a0{escape(label)}</Content></CharacterStyleRange>'
        '</ParagraphStyleRange>\n'
    )


def _display_segments(
    collector: TocCollector, source: dict | None,
) -> tuple[str, list[tuple[str, str, list[tuple[str, int | str]]]]]:
    if source:
        segments = []
        for language in source.get("languages", []):
            header = f"{language.get('code', '')}  {language.get('label', '')}".strip()
            entries = [(str(entry.get("title", "")), str(entry.get("folio", "")))
                       for entry in language.get("entries", [])]
            segments.append((header, str(language.get("page_range", "")), entries))
        return str(source.get("title") or "TABLE OF CONTENTS"), segments
    segments = []
    for lang, entries in _segments(collector.entries):
        folios = [_folio(index) for _, index in entries]
        segments.append((_LANG_HEADERS.get(lang, lang.upper()),
                         f"{min(folios):02d}-{max(folios):02d}",
                         [(title, _folio(index)) for title, index in entries]))
    return "TABLE OF CONTENTS", segments


def finalize(
    writer, collector: TocCollector, add_story_parts, psr,
    source: dict | None = None,
) -> bool:
    """Build the TOC spread and splice it into the template slot."""
    title, segments = _display_segments(collector, source)
    if not segments or len(writer.spreads) <= _TOC_SLOT:
        return False

    body_x = writer.m_l
    body_w = writer.page_w - writer.m_l - writer.m_r
    col_w = body_w * 0.48
    col_gap = body_w - 2.0 * col_w
    y = 33.84
    frames: list[str] = []
    # master: plain large dark text, no bar (STYLE_MAP.md 标题族)
    title_sid = add_story_parts(
        "st_toc_title", "TOC title",
        [psr("HB TOC Title", title, terminal=True)])
    frames.append(writer._frame_xml(
        "tf_toc_title", title_sid,
        *writer._page_rect(body_x + 1.11, y, body_w - 1.11, 30.0),
        inset=(0, 0, 0, 0)))
    y = 65.51

    for si, (header, rng, segment) in enumerate(segments):
        code, _, label = header.partition("  ")
        bar_sid = add_story_parts(
            f"st_toc_bar_{si}", f"TOC bar {si}",
            [_bar_psr(code, label)])
        range_sid = add_story_parts(
            f"st_toc_range_{si}", f"TOC range {si}",
            [psr("HB TOC Range", rng, terminal=True)])
        # rounded via the capsule path Rectangle: CornerOption attrs are
        # unreliable on generated frames (STYLE_MAP.md 机制备忘)
        frames.append(_po.capsule_xml(
            writer, f"bg_toc_bar_{si}", (body_x, y, body_w, 14.85)))
        frames.append(writer._frame_xml(
            f"tf_toc_bar_{si}", bar_sid,
            *writer._page_rect(body_x + 5.93, y, body_w * 0.55, 14.85),
            valign="CenterAlign", inset=(0, 0, 0, 0)))
        frames.append(writer._frame_xml(
            f"tf_toc_range_{si}", range_sid,
            *writer._page_rect(body_x + body_w - 33.34, y + 0.63, 28.40, 14.85),
            valign="CenterAlign", inset=(0, 0, 0, 0)))
        entry_y = y + 25.98
        half = (len(segment) + 1) // 2
        for ci, chunk in enumerate((segment[:half], segment[half:])):
            if not chunk:
                continue
            xml = "".join(_entry_psr(t, folio, col_w) for t, folio in chunk)
            sid = add_story_parts(f"st_toc_seg{si}_c{ci}", f"TOC {si}/{ci}", [xml])
            frames.append(writer._frame_xml(
                f"tf_toc_seg{si}_c{ci}", sid,
                *writer._page_rect(body_x + ci * (col_w + col_gap), entry_y,
                                   col_w, 14.0 * half + 14.0),
                inset=(0, 0, 0, 0)))
        y += 142.75 if si == 0 else 149.22

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
