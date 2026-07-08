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

from pathlib import Path
from xml.sax.saxutils import escape

from . import section_parts as _sp
from .params import IDPKG
from .primitives import _ATTR_ENTITIES

_DATA_PREFIXES = {
    "spec": "spec_",
    "lcd": "lcd_icons_",
    "trouble": "troubleshooting_",
    "symbols": "symbols_",
}


def flow_parts(writer, ordered, tags, *, extract_page, bundle_root,
               sections, spec_annotations, lcd_rows, trouble_rows,
               symbol_rows_for, default_lang):
    """Reading-order parts for the whole book; returns (parts, est, skipped).

    Shared by the .idml single-story path (build_flow_story) and the .icml
    placeable-story path (build_icml_story).
    """
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
            p = _sp.spec_parts(writer, sections, spec_annotations,
                                    tid_prefix="flow_tbl_spec", terminal_last=False)
            est += writer.estimate_spec_height(sections) + 10.0 * len(spec_annotations)
        elif kind == "lcd" and lcd_rows:
            p = _sp.lcd_parts(writer, lcd_rows, tid="flow_tbl_lcd", terminal_last=False)
            est += 16.0 + sum(max(28.0, 11.0 * (r["desc"].count("\n") + 1)) for r in lcd_rows)
        elif kind == "trouble" and trouble_rows:
            p = _sp.trouble_parts(writer, trouble_rows, tid="flow_tbl_trouble",
                                       terminal_last=False)
            est += 16.0 + sum(11.0 * (v.count("\n") + 1) for _, v in trouble_rows)
        elif kind == "symbols":
            sig, ico = symbol_rows_for(default_lang)
            if not (sig or ico):
                return
            p = _sp.symbols_parts(writer, sig, ico, default_lang,
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
        sub, sub_est = _sp.prose_blocks_to_parts(
            writer, seed, res.blocks, bundle_root, terminal_last=False)
        parts.extend(sub)
        est += sub_est
    return parts, est, skipped


def build_flow_story(writer, ordered, tags, *, extract_page, bundle_root,
                     sections, spec_annotations, lcd_rows, trouble_rows,
                     symbol_rows_for, default_lang, sid="st_flow"):
    """Assemble every bundle construct into one .idml story; (sid, est, skipped)."""
    parts, est, skipped = flow_parts(
        writer, ordered, tags, extract_page=extract_page, bundle_root=bundle_root,
        sections=sections, spec_annotations=spec_annotations, lcd_rows=lcd_rows,
        trouble_rows=trouble_rows, symbol_rows_for=symbol_rows_for,
        default_lang=default_lang)
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


def build_icml_story(writer, ordered, tags, *, extract_page, bundle_root,
                     sections, spec_annotations, lcd_rows, trouble_rows,
                     symbol_rows_for, default_lang, sid="ust_flow"):
    """Placeable InCopy (.icml) story XML — content + style-name refs only.

    No spreads / styles / colors / geometry: File→Place into the designer
    template and every paragraph/table style name resolves against the
    template's own definitions (precise match, zero duplication).
    """
    parts, est, skipped = flow_parts(
        writer, ordered, tags, extract_page=extract_page, bundle_root=bundle_root,
        sections=sections, spec_annotations=spec_annotations, lcd_rows=lcd_rows,
        trouble_rows=trouble_rows, symbol_rows_for=symbol_rows_for,
        default_lang=default_lang)
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<?aid style="50" type="document" readerVersion="6.0" featureSet="257" '
        'product="15.0(100)"?>\n'
        '<?aid SnippetType="InCopyInterchange"?>\n'
        f'<Story xmlns:idPkg="{IDPKG}" Self="{sid}" AppliedTOCStyle="n" '
        f'TrackChanges="false" StoryTitle="{escape("Manual", _ATTR_ENTITIES)}">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) + '</Story>\n'
    )
    return xml, est, skipped


def run_alt(writer, args, *, check_idml, **kw) -> int:
    """Dispatch to the .icml or --flow export path (whichever args selects)."""
    if args.icml:
        return run_icml(writer, args, **kw)
    return run_flow(writer, args, check_idml=check_idml, **kw)


def run_flow(writer, args, *, bundle_root, tags, bundle_page_order, extract_page,
             sections, spec_annotations, lcd_rows, trouble_rows, symbol_rows_for,
             default_output_path, check_idml) -> int:
    """Full --flow path: single threaded story + one frame chain; writes + checks."""
    ordered = bundle_page_order(bundle_root) if bundle_root.is_dir() else []
    if not ordered:
        print(f"[export-idml] ERROR: --flow needs a prepared bundle at {bundle_root} "
              "(run `build.py rst` first)")
        return 1
    sid, est, skipped = build_flow_story(
        writer, ordered, tags, extract_page=extract_page, bundle_root=bundle_root,
        sections=sections, spec_annotations=spec_annotations,
        lcd_rows=lcd_rows, trouble_rows=trouble_rows,
        symbol_rows_for=symbol_rows_for, default_lang=args.lang)
    pages = writer.pages_for_height(est)
    writer.add_spread_chain(sid, pages, 0)
    out = Path(args.out) if args.out else default_output_path(
        args.model, args.region, args.lang, bundle_root)
    writer.write(out)
    issues = check_idml(out)
    for i in issues:
        print(f"[export-idml] SELF-CHECK FAIL: {i}")
    print(f"[export-idml] {'OK' if not issues else 'WROTE WITH ISSUES'}: {out}")
    print(f"[export-idml] FLOW single story | spreads={pages} "
          f"skipped raw blocks={skipped}")
    return 1 if issues else 0


def run_icml(writer, args, *, bundle_root, tags, bundle_page_order, extract_page,
             sections, spec_annotations, lcd_rows, trouble_rows, symbol_rows_for,
             default_output_path) -> int:
    """--icml path: write a placeable InCopy story (.icml) for the template."""
    from xml.etree import ElementTree as ET

    ordered = bundle_page_order(bundle_root) if bundle_root.is_dir() else []
    if not ordered:
        print(f"[export-idml] ERROR: --icml needs a prepared bundle at {bundle_root} "
              "(run `build.py rst` first)")
        return 1
    xml, _est, skipped = build_icml_story(
        writer, ordered, tags, extract_page=extract_page, bundle_root=bundle_root,
        sections=sections, spec_annotations=spec_annotations,
        lcd_rows=lcd_rows, trouble_rows=trouble_rows,
        symbol_rows_for=symbol_rows_for, default_lang=args.lang)
    if args.out:
        out = Path(args.out)
    else:
        idml_out = default_output_path(args.model, args.region, args.lang, bundle_root)
        out = idml_out.with_suffix(".icml")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(xml, encoding="utf-8")
    # self-check: the story body (minus the aid PIs) must be well-formed XML
    try:
        ET.fromstring(xml.split("?>\n", 1)[-1].split("?>\n", 1)[-1])
        ok = True
    except ET.ParseError as exc:
        print(f"[export-idml] SELF-CHECK FAIL: icml not well-formed: {exc}")
        ok = False
    print(f"[export-idml] {'OK' if ok else 'WROTE WITH ISSUES'}: {out}")
    print(f"[export-idml] ICML placeable story | skipped raw blocks={skipped}")
    return 0 if ok else 1
