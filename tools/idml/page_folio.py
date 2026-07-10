"""Folio (page-number) footers for the composed IDML manual.

The master prints a small folio at the bottom outer corner of every
numbered content page; the cover, preface, TOC and back cover carry
none, and the placed finished-art pages (product overview) already
include theirs inside the artwork. Applied as a post-pass after the TOC
splice so the numbering matches what the TOC printed.
"""
from __future__ import annotations

_FIRST_CONTENT_SLOT = 3  # cover, preface, TOC precede the folio'd pages


def _skip(xml: str) -> bool:
    return "rc_st_placed_" in xml or "st_back_cover" in xml


def apply(writer, add_story_parts, psr) -> int:
    """Append a folio frame to each numbered content spread."""
    applied = 0
    for slot, (sid, xml) in enumerate(writer.spreads):
        if slot < _FIRST_CONTENT_SLOT or _skip(xml):
            continue
        folio = slot - _FIRST_CONTENT_SLOT + 1
        story_sid = add_story_parts(
            f"st_folio_{slot}", f"Folio {folio}",
            [psr("HB Spec Note", f"{folio:02d}", terminal=True)])
        x2 = writer.page_w / 2 - writer.m_r
        y2 = writer.page_h / 2 - 14.0
        frame = writer._frame_xml(
            f"tf_folio_{slot}", story_sid,
            x2 - 24.0, y2 - 10.0, x2, y2, inset=(0, 0, 0, 0))
        assert xml.rstrip().endswith("</idPkg:Spread>")
        xml = xml.replace("</Spread>\n</idPkg:Spread>",
                          frame + "</Spread>\n</idPkg:Spread>")
        writer.spreads[slot] = (sid, xml)
        applied += 1
    return applied
