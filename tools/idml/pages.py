"""Absolute-positioned composed-page assemblers for the IDML exporter."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from . import components as _components
from .layout_est import est_table_height, template_symbol_split
from .loaders import symbol_copy
from .page_objects import frame_with_background, h1_bar_h_pt, heading_bar_opts, heading_text, with_rounded_outer
from .params import IDPKG, param_pt
from .style_names import paragraph_style_ref
ROOT = Path(__file__).resolve().parents[2]
SUBBAR_H = 13.9  # master/publish-PDF measured capsule height


def _page_rect(writer, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
    return (
        -writer.page_w / 2 + x,
        -writer.page_h / 2 + y,
        -writer.page_w / 2 + x + w,
        -writer.page_h / 2 + y + h,
    )


def _frame_xml(writer, frame_id: str, story_id: str,
               x1: float, y1: float, x2: float, y2: float, *,
               columns: int = 1, fill: str | None = None,
               gutter: float = 11.0,
               rounded: bool = False, balance_columns: bool = False,
               valign: str | None = None,
               inset: tuple[float, float, float, float] | None = None,
               object_style: str | None = None) -> str:
    fill_attr = f'FillColor="{fill}" ' if fill else ""
    stroke_attr = (
        'StrokeColor="Swatch/None" StrokeWeight="0" '
        if fill else ""
    )
    corner_attr = 'CornerOption="RoundedCorner" CornerRadius="7" ' if rounded else ""
    balance_attr = ' VerticalBalanceColumns="true"' if balance_columns else ""
    valign_attr = f' VerticalJustification="{valign}"' if valign else ""
    inset_attr = ""
    if inset is not None:
        inset_attr = ' InsetSpacing="' + " ".join(f"{v:g}" for v in inset) + '"'
    applied_style = object_style or "ObjectStyle/$ID/[Normal Text Frame]"
    return (
        f'  <TextFrame Self="{frame_id}" ParentStory="{story_id}" '
        'PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" '
        f'AppliedObjectStyle="{applied_style}" '
        f'{fill_attr}{stroke_attr}{corner_attr}'
        'ItemTransform="1 0 0 1 0 0">\n'
        + writer._path_geometry(x1, y1, x2, y2) +
        f'    <TextFramePreference TextColumnCount="{columns}" '
        f'TextColumnGutter="{gutter:g}" AutoSizingType="Off"'
        f'{balance_attr}{valign_attr}{inset_attr}/>\n'
        '  </TextFrame>\n'
    )


def _safety_section_story(writer, sid: str, title: str,
                          blocks: list[tuple[str, str]],
                          bundle_root: Path) -> str:
    parts: list[str] = []
    text_measure = writer.page_w - writer.m_l - writer.m_r
    column_gap = param_pt(writer.params, "comp_twocol_sep", 6.24)
    column_measure = (text_measure - column_gap) / 2.0
    content_indices = [i for i, (kind, _) in enumerate(blocks) if kind != "layout"]
    last_idx = content_indices[-1] if content_indices else -1
    previous_kind = ""
    dense_language = any(marker in sid.casefold() for marker in ("_fr_", "_es_"))
    scale_key = (
        "idml_safety_list_horizontal_scale_dense"
        if dense_language else "idml_safety_list_horizontal_scale"
    )
    horizontal_scale = 100.0 * float(
        writer.params.get(scale_key, ("0.90" if dense_language else "0.98", "ratio"))[0]
    )
    for bi, (kind, text) in enumerate(blocks):
        terminal = bi == last_idx
        if kind == "component":
            import json as _json
            xml_part, _ = writer._render_component(
                sid, bi, _json.loads(text), bundle_root, terminal,
                span_columns=False, measure_w=column_measure)
            parts.append(xml_part)
        elif kind == "body":
            # \HBTypeBody territory: lead-ins are body Medium, not L2 Bold
            parts.append(writer._psr("HB Body", text, terminal=terminal))
        elif kind == "safetylead":
            parts.append(writer._psr("HB Safety Lead", text, terminal=terminal))
        elif kind == "list":
            list_xml = writer._psr("HB Safety List", text, terminal=terminal)
            list_xml = list_xml.replace(
                "<ParagraphStyleRange ",
                (
                    '<ParagraphStyleRange '
                    f'LeftIndent="{param_pt(writer.params, "idml_list_left_indent", 3.7):g}" '
                    f'FirstLineIndent="{param_pt(writer.params, "idml_list_first_line_indent", -6.25):g}" '
                    'RightIndent="0" Hyphenation="false" '
                ),
                1,
            )
            list_xml = list_xml.replace(
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                f'HorizontalScale="{horizontal_scale:g}"',
            )
            parts.append(list_xml)
        elif kind == "sublist":
            sublist_xml = writer._psr(
                "HB Safety Sublist", text, terminal=terminal,
            )
            sublist_xml = sublist_xml.replace(
                "<ParagraphStyleRange ",
                (
                    '<ParagraphStyleRange '
                    f'LeftIndent="{param_pt(writer.params, "idml_sublist_left_indent", 9.58):g}" '
                    f'FirstLineIndent="{param_pt(writer.params, "idml_sublist_first_line_indent", -6.04):g}" '
                    'RightIndent="0" Hyphenation="false" '
                ),
                1,
            )
            if previous_kind != "sublist":
                first_gap = param_pt(
                    writer.params, "idml_sublist_first_space_before", 0.45,
                )
                sublist_xml = sublist_xml.replace(
                    "<ParagraphStyleRange ",
                    f'<ParagraphStyleRange SpaceBefore="{first_gap:g}" ',
                    1,
                )
            sublist_xml = sublist_xml.replace(
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                f'HorizontalScale="{horizontal_scale:g}"',
            )
            parts.append(sublist_xml)
        elif kind in {"h1", "h2", "h3"}:
            parts.append(writer._psr(writer._PROSE_STYLE[kind], text, terminal=terminal))
        if kind != "layout":
            previous_kind = kind
    return writer._add_story_parts(sid, title, parts)

def add_safety_page(writer, sid: str, title: str, blocks: list[tuple[str, str]],
                    bundle_root: Path, page_index: int) -> str:
    """V2.0 US safety page 01: fixed component regions, not one flow."""
    h1 = next((t for k, t in blocks if k == "h1"), title)
    top_warning = next((t for k, t in blocks
                        if k == "component" and any(
                            f'"kind": "{name}"' in t
                            for name in ("safetywarning", "safetyinstruction"))), None)
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
        [heading_text(writer, h1, level=1)])
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
        [heading_text(writer, subbar, level=2)])
    section_sids = []
    for idx, section in enumerate(sections[:2]):
        sec_sid = f"{sid}_section{idx + 1}"
        writer._safety_section_story(sec_sid, f"{title} section {idx + 1}",
                                   section, bundle_root)
        section_sids.append(sec_sid)

    spread_id = f"sp_{page_index}"
    page_no = page_index + 1
    body_x = writer.m_l
    body_w = writer.page_w - writer.m_l - writer.m_r
    column_gap = param_pt(writer.params, "comp_twocol_sep", 6.24)
    frames = []
    for frame_id, story_id, rect, opts in (
        ("title", title_sid, (body_x, 27.92, body_w, h1_bar_h_pt(writer)),
         {**heading_bar_opts(1, (1.5, 0, 1, 0)),
          "text_rect": (body_x + 6.0, 26.0, body_w - 12.0, h1_bar_h_pt(writer))}),
        ("warning", warning_sid, (body_x, 55.5, body_w, 31.5),
         with_rounded_outer({"inset": (0, 0, 0, 0)})),
        ("section1", section_sids[0] if section_sids else "", (body_x, 95.77, body_w, 162.0),
         {"columns": 2, "gutter": column_gap,
          "balance_columns": True, "inset": (0, 0, 0, 0)}),
        ("subbar", bar_sid, (body_x, 263.0, body_w, SUBBAR_H),
         {**heading_bar_opts(2, (0.5, 0, 0.5, 0)),
          "text_rect": (body_x + 6.0, 263.0, body_w - 12.0, SUBBAR_H)}),
        ("section2", section_sids[1] if len(section_sids) > 1 else "",
         (body_x, 281.88, body_w, 209.12),
         {"columns": 2, "gutter": column_gap,
          "balance_columns": True, "inset": (0, 0, 0, 0)}),
    ):
        if not story_id:
            continue
        frames.append(frame_with_background(writer, sid, frame_id, story_id, rect, opts))

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
    from .page03 import add_fcc_inbox_page as _add_fcc_inbox_page

    return _add_fcc_inbox_page(
        writer, sid, fcc_blocks, inbox_blocks, bundle_root, page_index)

def _localized_signal_label_bar(label: str) -> str:
    style_ref = paragraph_style_ref("HB Notice Side Label")
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}" '
        'ParagraphShadingOn="true" '
        'ParagraphShadingColor="Color/HB Brand Dark" '
        'ParagraphShadingTint="100" '
        'ParagraphShadingWidth="ColumnWidth" '
        'ParagraphShadingTopOrigin="AscentTopOrigin" '
        'ParagraphShadingBottomOrigin="DescentBottomOrigin" '
        'ParagraphShadingTopOffset="2" ParagraphShadingBottomOffset="2" '
        'ParagraphShadingLeftOffset="3" ParagraphShadingRightOffset="3">\n'
        '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'FillColor="Color/Paper"><Content>{escape(label)}</Content></CharacterStyleRange>\n'
        '  </ParagraphStyleRange>\n'
    )


def _symbol_signal_bar(writer, tid: str, label: str, bundle_root: Path) -> str:
    asset_name = f"{label.lower()}_bar.png"
    asset = (
        ROOT / "docs" / "templates" / "word_template" / "common_assets"
        / "symbols" / asset_name
    )
    if asset.exists():
        style_ref = paragraph_style_ref("HB Figure")
        return (f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">'
                '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                + writer._image_cell_content(tid, asset, 61.2, 16.2)
                + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
    return _localized_signal_label_bar(label)

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
    return writer._component_table(
        tid, cols, cells, n_rows=len(rows), role="data", outer_stroke=False)

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
                icon = writer._image_cell_content(f"{tid}img{ri}", fig, 18.0, 18.0)
            figure_style_ref = paragraph_style_ref("HB Figure")
            left_xml = (
                f'  <ParagraphStyleRange AppliedParagraphStyle="{figure_style_ref}">'
                '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                + icon + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
            right_xml = writer._psr("HB Spec Value", row["text"], terminal=True)
        cells.append(writer._cell(f"{tid}c{ri}_0", f"0:{ri}", left_xml,
                                top=2, bottom=2, left=4, right=4))
        cells.append(writer._cell(f"{tid}c{ri}_1", f"1:{ri}", right_xml,
                                top=2, bottom=2, left=5, right=4))
    return writer._component_table(
        tid, cols, cells, n_rows=len(rows), role="data", outer_stroke=False)

def _table_story(writer, sid: str, title: str, table: str) -> str:
    style_ref = paragraph_style_ref("HB Body")
    return writer._add_story_parts(
        sid, title,
        [f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">\n'
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

    tail_stories: list[tuple[str, float]] = []
    for bi, (kind, text) in enumerate(tail_blocks):
        if kind != "component":
            continue
        spec = _json.loads(text)
        if spec.get("kind") in {"safetywarning", "warnbox", "notice"}:
            spec = {
                "kind": "tailwarnbox",
                "label": spec.get("label") or copy["warning"],
                "texts": spec.get("texts", []),
            }
        tail_sid = f"{sid}_tail_{spec.get('label', bi).lower()}"
        xml_part, tail_h = writer._render_component(
            tail_sid, bi, spec, bundle_root,
            terminal=True, span_columns=False)
        writer._add_story_parts(tail_sid, f"Safety tail {bi}", [xml_part])
        tail_stories.append((tail_sid, tail_h))

    maint_title = next((t for k, t in maintenance_blocks if k in ("h1", "h2")),
                       "USER MAINTENANCE INSTRUCTIONS")
    maint_text = "\n".join(t for k, t in maintenance_blocks if k == "body")
    maint_title_sid = f"{sid}_maintenance_title"
    writer._add_story_parts(
        maint_title_sid, "Maintenance title",
        [heading_text(writer, maint_title, level=2)])
    maint_body_sid = f"{sid}_maintenance_body"
    writer._add_story_parts(
        maint_body_sid, "Maintenance body",
        [writer._psr("HB Maintenance Body", maint_text, terminal=True)])

    symbols_title_sid = f"{sid}_symbols_title"
    writer._add_story_parts(
        symbols_title_sid, "Symbols title",
        [heading_text(writer, copy["title"], level=1)])

    body_x = writer.m_l
    body_w = writer.page_w - writer.m_l - writer.m_r
    icon_gap = 6.0
    icon_table_w = (body_w - icon_gap) / 2.0
    left_icons, right_icons, _overflow_icons = template_symbol_split(icons)
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

    # Flow the frames from a cursor using coarse content-height estimates
    # instead of fixed rects (fixed heights hid taller content as overset);
    # the icon tables then take whatever remains down to the bottom margin.
    y = 27.5
    frame_specs: list[tuple[str, str, tuple[float, float, float, float], dict]] = []

    def _place(fid: str, story: str, h: float, opts: dict, gap: float = 6.0) -> None:
        nonlocal y
        frame_specs.append((fid, story, (body_x, y, body_w, h), opts))
        y += h + gap

    for ti, (t_sid, t_h) in enumerate(tail_stories):
        target_h = 34.5 if ti == 0 else 28.0
        tail_h = (target_h if lang == "en" else
                  min(max(target_h, t_h + 3.0), target_h + 6.0) + 3.0)
        _place(f"tail_{ti}", t_sid, tail_h,
               with_rounded_outer({
                   "inset": (0, 0, 0, 0),
                   "valign": "CenterAlign",
               }), gap=4.0)
    maint_h = (25.0 if lang == "en" else
               est_table_height([maint_text], body_w, 24.0) - 16.0)
    _place("maint_title", maint_title_sid, SUBBAR_H,
           heading_bar_opts(2, (0.5, 5, 0.5, 6)), gap=3.5)
    _place("maint_body", maint_body_sid, maint_h, {"inset": (0, 0, 0, 0)},
           gap=0.4 if lang == "en" else 8.0)
    _place("symbols_title", symbols_title_sid, h1_bar_h_pt(writer),
           heading_bar_opts(1, (1.5, 5, 1, 6)), gap=9.0)
    signal_row_h = 26.0 if lang == "en" else 18.0
    signals_h = est_table_height(
        [t for _, t in signals], body_w * 0.76, signal_row_h)
    _place("signals", signal_sid, signals_h, with_rounded_outer({"inset": (0, 0, 0, 0)}), gap=6.5)
    bottom = writer.page_h - 2.0
    icons_h = 3.0 + max(60.0, min(
        max(est_table_height([r.get("text", "") for r in left_icons], icon_table_w * 0.73, 24.0),
            est_table_height([r.get("text", "") for r in right_icons], icon_table_w * 0.73, 24.0)),
        bottom - y))
    frame_specs.append(("icons_left", left_sid, (body_x, y, icon_table_w, icons_h),
                        with_rounded_outer({"inset": (0, 0, 0, 0)})))
    frame_specs.append(("icons_right", right_sid,
                        (body_x + icon_table_w + icon_gap, y, icon_table_w, icons_h),
                        with_rounded_outer({"inset": (0, 0, 0, 0)})))

    spread_id = f"sp_{page_index}"
    page_no = page_index + 1
    frames = []
    for frame_id, story_id, rect, opts in frame_specs:
        if not story_id:
            continue
        if frame_id == "maint_title":
            opts = {**opts, "text_rect": (
                rect[0] + 6.0, rect[1], rect[2] - 12.0, rect[3])}
        elif frame_id == "symbols_title":
            # The production page keeps the text at this baseline but places
            # the 20.126 pt H1 bar 1.918 pt lower around it.  Separate the two
            # rectangles so the visible title is vertically centered without
            # shifting the already aligned signal table below.
            text_y = rect[1]
            rect = (rect[0], rect[1] + 1.918, rect[2], rect[3])
            opts = {**opts, "text_rect": (
                rect[0] + 6.0, text_y, rect[2] - 12.0, rect[3])}
        frames.append(frame_with_background(writer, sid, frame_id, story_id, rect, opts))
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
