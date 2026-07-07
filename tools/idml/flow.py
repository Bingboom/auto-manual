"""Single-story book flow for the IDML exporter.

The default (composed) exporter builds one story + one frame per page to
reproduce the PDF master's fixed layout. This module builds the OPPOSITE: the
whole manual as ONE story threaded through a single chain of linked frames, so
InDesign reflows continuously and editing feels like Word (user request).

Trade-off, accepted by the caller: fixed page composition is dropped —
data tables, safety two-column, and the fcc+inbox page all become inline,
single-column, reflowing content in reading order. Components still render as
inline tables/anchored frames (same primitives as the composed path); only the
per-page framing changes.

All section parts are built with ``terminal_last=False`` so every paragraph
keeps its trailing <Br/> and sections cannot fuse across the join.
"""
from __future__ import annotations

from xml.sax.saxutils import escape

from . import stories as _stories
from .params import IDPKG
from .primitives import _ATTR_ENTITIES

_DATA_PREFIXES = {
    "spec": "spec_",
    "lcd": "lcd_icons_",
    "trouble": "troubleshooting_",
    "symbols": "symbols_",
}


def build_flow_story(writer, ordered, tags, *, extract_page, bundle_root,
                     sections, spec_annotations, lcd_rows, trouble_rows,
                     symbol_rows_for, default_lang, sid="st_flow"):
    """Assemble every bundle construct into one story; returns (sid, est, skipped)."""
    parts: list[str] = []
    est = 0.0
    skipped = 0
    emitted: set[str] = set()

    def data_kind(name: str) -> str | None:
        return next((k for k, p in _DATA_PREFIXES.items() if name.startswith(p)), None)

    def add_data(kind: str) -> None:
        nonlocal est
        if kind in emitted:
            return
        emitted.add(kind)
        if kind == "spec":
            p = _stories.spec_parts(writer, sections, spec_annotations,
                                    tid_prefix="flow_tbl_spec", terminal_last=False)
            est += writer.estimate_spec_height(sections) + 10.0 * len(spec_annotations)
        elif kind == "lcd" and lcd_rows:
            p = _stories.lcd_parts(writer, lcd_rows, tid="flow_tbl_lcd", terminal_last=False)
            est += 16.0 + sum(max(28.0, 11.0 * (r["desc"].count("\n") + 1)) for r in lcd_rows)
        elif kind == "trouble" and trouble_rows:
            p = _stories.trouble_parts(writer, trouble_rows, tid="flow_tbl_trouble",
                                       terminal_last=False)
            est += 16.0 + sum(11.0 * (v.count("\n") + 1) for _, v in trouble_rows)
        elif kind == "symbols":
            sig, ico = symbol_rows_for(default_lang)
            if not (sig or ico):
                return
            p = _stories.symbols_parts(writer, sig, ico, default_lang,
                                       sig_tid="flow_tbl_sym_sig", ico_tid="flow_tbl_sym_ico",
                                       terminal_last=False)
            est += 16.0 + 14.0 * len(sig) + 26.0 * len(ico)
        else:
            return
        parts.extend(p)

    for page in ordered:
        kind = data_kind(page.name)
        if kind:
            add_data(kind)
            continue
        res = extract_page(page, tags)
        skipped += res.skipped_raw
        if not res.blocks:
            continue
        # unique tid seed per page so component/table ids never collide in the
        # single story
        seed = "flow_" + page.stem.replace("-", "_")
        sub, sub_est = _stories.prose_blocks_to_parts(
            writer, seed, res.blocks, bundle_root, terminal_last=False)
        parts.extend(sub)
        est += sub_est

    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" '
        f'StoryTitle="{escape("Manual", _ATTR_ENTITIES)}">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) + '</Story>\n</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid, est, skipped
