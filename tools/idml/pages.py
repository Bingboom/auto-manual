"""Composed-page assemblers for the IDML exporter (componentization P3).

Absolute-positioned multi-frame spreads (the V2.0-master safety page, the
safety+symbols merge, the fcc+inbox merge). Each function takes the writer
and appends stories + a spread. Moved verbatim from IdmlWriter — the golden
byte-comparison pins equivalence.
"""
from __future__ import annotations

from pathlib import Path

from . import components as _components
from .fcc_fallback import component_spec, fcc_spec_from_blocks
from .loaders import symbol_copy
from .params import IDPKG

ROOT = Path(__file__).resolve().parents[2]


def _frame_xml(writer, frame_id: str, story_id: str,
               x1: float, y1: float, x2: float, y2: float, *,
               columns: int = 1, fill: str | None = None,
               rounded: bool = False, balance_columns: bool = False,
               inset: tuple[float, float, float, float] | None = None) -> str:
    fill_attr = f'FillColor="{fill}" ' if fill else ""
    stroke_attr = (
        'StrokeColor="Swatch/None" StrokeWeight="0" '
        if fill else ""
    )
    corner_attr = 'CornerOption="RoundedCorner" CornerRadius="7" ' if rounded else ""
    balance_attr = ' VerticalBalanceColumns="true"' if balance_columns else ""
    inset_attr = ""
    if inset is not None:
        inset_attr = ' InsetSpacing="' + " ".join(f"{v:g}" for v in inset) + '"'
    return (
        f'  <TextFrame Self="{frame_id}" ParentStory="{story_id}" '
        'PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
        f'{fill_attr}{stroke_attr}{corner_attr}'
        'ItemTransform="1 0 0 1 0 0">\n'
        + writer._path_geometry(x1, y1, x2, y2) +
        f'    <TextFramePreference TextColumnCount="{columns}" '
        f'TextColumnGutter="11" AutoSizingType="Off"{balance_attr}{inset_attr}/>\n'
        '  </TextFrame>\n'
    )

def _page_rect(writer, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
    return (
        -writer.page_w / 2 + x,
        -writer.page_h / 2 + y,
        -writer.page_w / 2 + x + w,
        -writer.page_h / 2 + y + h,
    )

def _safety_section_story(writer, sid: str, title: str,
                          blocks: list[tuple[str, str]],
                          bundle_root: Path) -> str:
    parts: list[str] = []
    text_measure = writer.page_w - writer.m_l - writer.m_r
    column_measure = (text_measure - 11.0) / 2.0
    content_indices = [i for i, (kind, _) in enumerate(blocks) if kind != "layout"]
    last_idx = content_indices[-1] if content_indices else -1
    for bi, (kind, text) in enumerate(blocks):
        terminal = bi == last_idx
        if kind == "component":
            import json as _json
            xml_part, _ = writer._render_component(
                sid, bi, _json.loads(text), bundle_root, terminal,
                span_columns=False, measure_w=column_measure)
            parts.append(xml_part)
        elif kind == "body":
            parts.append(writer._psr("HB Title L2", text, terminal=terminal))
        elif kind == "list":
            parts.append(writer._psr("HB List", text, terminal=terminal))
        elif kind in {"h1", "h2", "h3"}:
            parts.append(writer._psr(writer._PROSE_STYLE[kind], text, terminal=terminal))
    return writer._add_story_parts(sid, title, parts)

def add_safety_page(writer, sid: str, title: str, blocks: list[tuple[str, str]],
                    bundle_root: Path, page_index: int) -> str:
    """V2.0 US safety page 01: fixed component regions, not one flow."""
    h1 = next((t for k, t in blocks if k == "h1"), title)
    top_warning = next((t for k, t in blocks
                        if k == "component" and '"kind": "safetywarning"' in t), None)
    subbar = next((t for k, t in blocks if k == "h2"), "OPERATING INSTRUCTIONS")

    sections: list[list[tuple[str, str]]] = []
    cur: list[tuple[str, str]] | None = None
    for kind, text in blocks:
        if kind == "layout" and text == "twocol_start":
            cur = []
        elif kind == "layout" and text == "twocol_end":
            if cur is not None:
                sections.append(cur)
            cur = None
        elif cur is not None:
            cur.append((kind, text))

    title_sid = f"{sid}_title"
    writer._add_story_parts(
        title_sid, f"{title} title",
        [writer._psr("HB Capsule Text", h1, terminal=True)])
    warning_sid = f"{sid}_top_warning"
    if top_warning:
        import json as _json
        xml_part, _ = writer._render_component(
            warning_sid, 0, _json.loads(top_warning), bundle_root,
            terminal=True, span_columns=False)
        writer._add_story_parts(warning_sid, f"{title} warning", [xml_part])
    bar_sid = f"{sid}_subbar"
    writer._add_story_parts(
        bar_sid, f"{title} subbar",
        [writer._psr("HB Capsule Text", subbar, terminal=True)])
    section_sids = []
    for idx, section in enumerate(sections[:2]):
        sec_sid = f"{sid}_section{idx + 1}"
        writer._safety_section_story(sec_sid, f"{title} section {idx + 1}",
                                   section, bundle_root)
        section_sids.append(sec_sid)

    spread_id = f"sp_{page_index}"
    page_no = page_index + 1
    body_x = 27.4
    body_w = writer.page_w - body_x * 2
    frames = []
    for frame_id, story_id, rect, opts in (
        ("title", title_sid, (body_x, 27.5, body_w, 18.8),
         {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (1, 5, 1, 6)}),
        ("warning", warning_sid, (body_x, 55.5, body_w, 31.5),
         {"inset": (0, 0, 0, 0)}),
        ("section1", section_sids[0] if section_sids else "", (body_x, 93.5, body_w, 162.0),
         {"columns": 2, "balance_columns": True, "inset": (0, 0, 0, 0)}),
        ("subbar", bar_sid, (body_x, 263.5, body_w, 17.2),
         {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (0.5, 5, 0.5, 6)}),
        ("section2", section_sids[1] if len(section_sids) > 1 else "",
         (body_x, 286.0, body_w, 205.0),
         {"columns": 2, "balance_columns": True, "inset": (0, 0, 0, 0)}),
    ):
        if not story_id:
            continue
        x1, y1, x2, y2 = writer._page_rect(*rect)
        frames.append(writer._frame_xml(
            f"tf_{sid}_{frame_id}", story_id, x1, y1, x2, y2, **opts))

    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
        f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} {-writer.page_h / 2:g}">\n'
        '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
        f'Top="{writer.m_t:g}" Bottom="{writer.m_b:g}" '
        f'Left="{writer.m_l:g}" Right="{writer.m_r:g}"/>\n'
        '  </Page>\n'
        + "".join(frames) +
        '</Spread>\n'
        '</idPkg:Spread>\n'
    )
    writer.spreads.append((spread_id, xml))
    return spread_id

def _single_component_story(writer, sid: str, title: str, spec: dict,
                            bundle_root: Path, measure_w: float) -> str:
    xml_part, _ = writer._render_component(
        sid, 0, spec, bundle_root,
        terminal=True, span_columns=False, measure_w=measure_w)
    return writer._add_story_parts(sid, title, [xml_part])


def add_fcc_inbox_page(
    writer,
    sid: str,
    fcc_blocks: list[tuple[str, str]],
    inbox_blocks: list[tuple[str, str]],
    bundle_root: Path,
    page_index: int,
) -> str:
    """V2.0 page 03: FCC notice and inbox cards share one page."""

    body_x = 27.4
    body_w = writer.page_w - body_x * 2
    fcc_spec = fcc_spec_from_blocks(fcc_blocks)
    inbox_title = next((text for kind, text in inbox_blocks if kind == "h1"),
                       "WHAT'S IN THE BOX")
    inbox_spec = component_spec(inbox_blocks, "inbox")
    tip_spec = component_spec(inbox_blocks, "notice")

    fcc_sid = f"{sid}_fcc"
    writer._single_component_story(
        fcc_sid, "FCC notice", fcc_spec, bundle_root, body_w)
    title_sid = f"{sid}_title"
    writer._add_story_parts(
        title_sid, "Inbox title",
        [writer._psr("HB Capsule Text", inbox_title, terminal=True)])
    frame_specs: list[tuple[str, str, tuple[float, float, float, float], dict]] = [
        ("fcc", fcc_sid, (body_x, 34.0, body_w, 184.0),
         {"fill": "Color/HB Bg K05", "rounded": True, "inset": (0, 0, 0, 0)}),
        ("title", title_sid, (body_x, 250.0, body_w, 21.5),
         {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (1, 5, 1, 6)}),
    ]
    if inbox_spec:
        inbox_sid = f"{sid}_inbox"
        writer._single_component_story(
            inbox_sid, "Inbox cards", inbox_spec, bundle_root, body_w)
        frame_specs.append(
            ("inbox", inbox_sid, (body_x, 278.0, body_w, 160.0),
             {"inset": (0, 0, 0, 0)})
        )
    if tip_spec:
        tip_sid = f"{sid}_tip"
        writer._single_component_story(
            tip_sid, "Inbox tip", tip_spec, bundle_root, body_w)
        frame_specs.append(
            ("tip", tip_sid, (body_x, 456.0, body_w, 42.0),
             {"inset": (0, 0, 0, 0)})
        )

    spread_id = f"sp_{page_index}"
    page_no = page_index + 1
    frames = []
    for frame_id, story_id, rect, opts in frame_specs:
        x1, y1, x2, y2 = writer._page_rect(*rect)
        frames.append(writer._frame_xml(
            f"tf_{sid}_{frame_id}", story_id, x1, y1, x2, y2, **opts))

    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
        f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} {-writer.page_h / 2:g}">\n'
        '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
        f'Top="{writer.m_t:g}" Bottom="{writer.m_b:g}" '
        f'Left="{writer.m_l:g}" Right="{writer.m_r:g}"/>\n'
        '  </Page>\n'
        + "".join(frames) +
        '</Spread>\n'
        '</idPkg:Spread>\n'
    )
    writer.spreads.append((spread_id, xml))
    return spread_id

def _symbol_signal_bar(writer, tid: str, label: str, bundle_root: Path) -> str:
    asset_name = f"{label.lower()}_bar.png"
    asset = (
        ROOT / "docs" / "templates" / "word_template" / "common_assets"
        / "symbols" / asset_name
    )
    if asset.exists():
        return ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                + writer._image_cell_content(tid, asset, 61.2, 16.2)
                + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
    return writer._psr("HB Capsule Text", label, terminal=True)

def _symbols_signal_table(writer, tid: str, signals: list[tuple[str, str]],
                          width: float, bundle_root: Path,
                          lang: str = "en") -> str:
    copy = symbol_copy(lang)
    rows = [(copy["symbol"], copy["meaning"], True)] + [
        (label, text, False) for label, text in signals
    ]
    cols = [width * 0.24, width * 0.76]
    cells = []
    for ri, (left, right, header) in enumerate(rows):
        if header:
            left_xml = writer._psr("HB Spec Label", left, terminal=True)
            right_xml = writer._psr("HB Spec Label", right, terminal=True)
        else:
            left_xml = writer._symbol_signal_bar(f"{tid}sig{ri}", left, bundle_root)
            right_xml = writer._psr("HB Spec Value", right, terminal=True)
        cells.append(writer._cell(f"{tid}c{ri}_0", f"0:{ri}", left_xml,
                                top=3, bottom=3, left=6, right=4))
        cells.append(writer._cell(f"{tid}c{ri}_1", f"1:{ri}", right_xml,
                                top=3, bottom=3, left=7, right=5))
    return writer._component_table(tid, cols, cells, n_rows=len(rows))

def _symbols_icon_table(writer, tid: str, icons: list[dict], width: float,
                        lang: str = "en") -> str:
    copy = symbol_copy(lang)
    rows = [{"figure": "", "text": copy["meaning"], "header": True}] + [
        {**row, "header": False} for row in icons
    ]
    cols = [width * 0.27, width * 0.73]
    cells = []
    for ri, row in enumerate(rows):
        if row.get("header"):
            left_xml = writer._psr("HB Spec Label", copy["symbol"], terminal=True)
            right_xml = writer._psr("HB Spec Label", row["text"], terminal=True)
        else:
            fig = (ROOT / row["figure"]) if row.get("figure") else None
            icon = ""
            if fig and fig.exists():
                icon = writer._image_cell_content(f"{tid}img{ri}", fig, 28.0, 28.0)
            left_xml = (
                '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                + icon + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
            right_xml = writer._psr("HB Spec Value", row["text"], terminal=True)
        cells.append(writer._cell(f"{tid}c{ri}_0", f"0:{ri}", left_xml,
                                top=3, bottom=3, left=4, right=4))
        cells.append(writer._cell(f"{tid}c{ri}_1", f"1:{ri}", right_xml,
                                top=3, bottom=3, left=5, right=4))
    return writer._component_table(tid, cols, cells, n_rows=len(rows))

def _table_story(writer, sid: str, title: str, table: str) -> str:
    return writer._add_story_parts(
        sid, title,
        ['  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
         '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
         + table +
         '    <Content></Content></CharacterStyleRange>\n'
         '  </ParagraphStyleRange>\n'])

def add_safety_symbols_page(
    writer,
    sid: str,
    tail_blocks: list[tuple[str, str]],
    maintenance_blocks: list[tuple[str, str]],
    signals: list[tuple[str, str]],
    icons: list[dict],
    bundle_root: Path,
    page_index: int,
    lang: str = "en",
) -> str:
    """V2.0 page 02: safety tail + maintenance + symbols on one page."""
    import json as _json
    copy = symbol_copy(lang)

    tail_sids: list[str] = []
    for bi, (kind, text) in enumerate(tail_blocks):
        if kind != "component":
            continue
        spec = _json.loads(text)
        if spec.get("kind") == "safetywarning":
            spec = {
                "kind": "tailwarnbox",
                "label": copy["warning"],
                "texts": spec.get("texts", []),
            }
        elif spec.get("kind") == "warnbox":
            spec = {
                **spec,
                "kind": "tailwarnbox",
            }
        tail_sid = f"{sid}_tail_{spec.get('label', bi).lower()}"
        xml_part, _ = writer._render_component(
            tail_sid, bi, spec, bundle_root,
            terminal=True, span_columns=False)
        writer._add_story_parts(tail_sid, f"Safety tail {bi}", [xml_part])
        tail_sids.append(tail_sid)

    maint_title = next((t for k, t in maintenance_blocks if k == "h1"),
                       "USER MAINTENANCE INSTRUCTIONS")
    maint_text = "\n".join(t for k, t in maintenance_blocks if k == "body")
    maint_title_sid = f"{sid}_maintenance_title"
    writer._add_story_parts(
        maint_title_sid, "Maintenance title",
        [writer._psr("HB Capsule Text", maint_title, terminal=True)])
    maint_body_sid = f"{sid}_maintenance_body"
    writer._add_story_parts(
        maint_body_sid, "Maintenance body",
        [writer._psr("HB Body", maint_text, terminal=True)])

    symbols_title_sid = f"{sid}_symbols_title"
    writer._add_story_parts(
        symbols_title_sid, "Symbols title",
        [writer._psr("HB Capsule Text", copy["title"], terminal=True)])

    body_x = 27.4
    body_w = writer.page_w - body_x * 2
    icon_gap = 6.0
    icon_table_w = (body_w - icon_gap) / 2.0
    left_icons = icons[:6]
    right_icons = icons[6:]
    signal_sid = f"{sid}_signals"
    writer._table_story(
        signal_sid, "Signal words",
        writer._symbols_signal_table(
            f"{sid}_sig_tbl", signals, body_w, bundle_root, lang))
    left_sid = f"{sid}_icons_left"
    writer._table_story(
        left_sid, "Symbol icons left",
        writer._symbols_icon_table(f"{sid}_icons_l_tbl", left_icons, icon_table_w, lang))
    right_sid = f"{sid}_icons_right"
    writer._table_story(
        right_sid, "Symbol icons right",
        writer._symbols_icon_table(
            f"{sid}_icons_r_tbl", right_icons, icon_table_w, lang))

    frame_specs = (
        ("tail_warning", tail_sids[0] if tail_sids else "", (body_x, 18.0, body_w, 46.0),
         {"inset": (0, 0, 0, 0)}),
        ("tail_danger", tail_sids[1] if len(tail_sids) > 1 else "", (body_x, 68.0, body_w, 38.0),
         {"inset": (0, 0, 0, 0)}),
        ("maint_title", maint_title_sid, (body_x, 113.0, body_w, 16.5),
         {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (0.5, 5, 0.5, 6)}),
        ("maint_body", maint_body_sid, (body_x, 132.5, body_w, 34.0),
         {"inset": (0, 0, 0, 0)}),
        ("symbols_title", symbols_title_sid, (body_x, 173.5, body_w, 27.0),
         {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (2, 5, 1, 6)}),
        ("signals", signal_sid, (body_x, 211.5, body_w, 111.0),
         {"inset": (0, 0, 0, 0)}),
        ("icons_left", left_sid, (body_x, 329.0, icon_table_w, 179.0),
         {"inset": (0, 0, 0, 0)}),
        ("icons_right", right_sid, (body_x + icon_table_w + icon_gap, 329.0, icon_table_w, 179.0),
         {"inset": (0, 0, 0, 0)}),
    )

    spread_id = f"sp_{page_index}"
    page_no = page_index + 1
    frames = []
    for frame_id, story_id, rect, opts in frame_specs:
        if not story_id:
            continue
        x1, y1, x2, y2 = writer._page_rect(*rect)
        frames.append(writer._frame_xml(
            f"tf_{sid}_{frame_id}", story_id, x1, y1, x2, y2, **opts))
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
        f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} {-writer.page_h / 2:g}">\n'
        '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
        f'Top="{writer.m_t:g}" Bottom="{writer.m_b:g}" '
        f'Left="{writer.m_l:g}" Right="{writer.m_r:g}"/>\n'
        '  </Page>\n'
        + "".join(frames) +
        '</Spread>\n'
        '</idPkg:Spread>\n'
    )
    writer.spreads.append((spread_id, xml))
    return spread_id
