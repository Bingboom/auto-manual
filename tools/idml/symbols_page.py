"""Meaning-of-symbols and combined safety-symbol page assemblers."""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from xml.sax.saxutils import escape

from .layout_est import est_table_height, template_symbol_split
from .loaders import symbol_copy
from .page_objects import (
    frame_with_background,
    h1_bar_h_pt,
    heading_bar_opts,
    heading_text,
    with_rounded_outer,
)
from .params import IDPKG, component_param_pt
from .style_names import paragraph_style_ref

ROOT = Path(__file__).resolve().parents[2]
SUBBAR_H = 13.9  # master/publish-PDF measured capsule height


@dataclass(frozen=True)
class SafetySymbolsPageStyle:
    """Token-driven vertical contract for the combined maintenance page."""

    page_top: float
    first_tail_height: float
    first_tail_gap: float
    second_tail_height: float
    second_tail_gap: float
    maintenance_body_height: float
    maintenance_body_gap: float
    signal_header_height: float
    signal_row_height: float
    signal_gap_after: float
    icon_header_height: float
    icon_row_height: float
    icon_last_row_height: float
    icon_long_last_row_height: float

    @classmethod
    def from_writer(cls, writer, language: str) -> "SafetySymbolsPageStyle":
        normalized = language.split("-", 1)[0]

        def token(key: str, default: float) -> float:
            return component_param_pt(
                writer.params,
                key,
                default,
                strict=writer.strict_component_assets,
                owner="safety symbols page",
            )

        def localized(key: str, default: float) -> float:
            base = token(key, default)
            if normalized not in {"en", "fr", "es"}:
                return base
            return token(f"lang_{normalized}_{key}", base)

        return cls(
            page_top=localized("idml_symbols_page_top", 27.7),
            first_tail_height=localized("idml_symbols_first_tail_height", 34.5),
            first_tail_gap=localized("idml_symbols_first_tail_gap", 4.4),
            second_tail_height=localized("idml_symbols_second_tail_height", 28.5),
            second_tail_gap=localized("idml_symbols_second_tail_gap", 6.8),
            maintenance_body_height=localized(
                "idml_symbols_maintenance_body_height", 21.5,
            ),
            maintenance_body_gap=localized(
                "idml_symbols_maintenance_body_gap", 0.0,
            ),
            signal_header_height=token(
                "idml_symbols_signal_header_height", 17.3,
            ),
            signal_row_height=token("idml_symbols_signal_row_height", 25.42),
            signal_gap_after=localized("idml_symbols_signal_gap_after", 4.1),
            icon_header_height=token("idml_symbols_icon_header_height", 15.0),
            icon_row_height=token("idml_symbols_icon_row_height", 30.7),
            icon_last_row_height=token(
                "idml_symbols_icon_last_row_height", 32.2,
            ),
            icon_long_last_row_height=token(
                "idml_symbols_icon_long_last_row_height", 64.9,
            ),
        )


def _localized_signal_label_bar(writer, tid: str, label: str) -> str:
    style_ref = paragraph_style_ref("HB Notice Side Label")
    badge_w = component_param_pt(
        writer.params,
        "comp_symbol_signal_width",
        60.94,
        strict=writer.strict_component_assets,
        owner="symbol signal badge",
    )
    badge_h = component_param_pt(
        writer.params,
        "comp_symbol_signal_height",
        15.3,
        strict=writer.strict_component_assets,
        owner="symbol signal badge",
    )
    asset = (
        ROOT / "docs" / "templates" / "word_template" / "common_assets"
        / "symbols" / "warning_triangle_white.svg"
    )
    icon = ""
    if asset.exists():
        icon_w = component_param_pt(
            writer.params,
            "idml_symbols_signal_icon_width",
            7.5,
            strict=writer.strict_component_assets,
            owner="symbol signal badge",
        )
        icon_h = component_param_pt(
            writer.params,
            "idml_symbols_signal_icon_height",
            7.0,
            strict=writer.strict_component_assets,
            owner="symbol signal badge",
        )
        icon = writer._image_cell_content(f"{tid}icon", asset, icon_w, icon_h)
    elif writer.strict_component_assets:
        raise FileNotFoundError(f"symbol signal badge asset missing: {asset}")
    content = (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">\n'
        '    <CharacterStyleRange '
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'FillColor="Color/Paper">{icon}<Content> {escape(label)}</Content>'
        '</CharacterStyleRange>\n  </ParagraphStyleRange>\n'
    )
    badge_cell = writer._cell(
        f"{tid}c0",
        "0:0",
        content,
        fill="Color/HB Brand Dark",
        stroke=False,
        top=0,
        bottom=0,
        left=3,
        right=2,
        valign="CenterAlign",
    )
    badge = writer._component_table(
        f"{tid}tbl",
        [badge_w],
        [badge_cell],
        outer_stroke=False,
        row_heights=[badge_h],
    )
    return writer._wrap_table_paragraph(badge, True, span_columns=False)


def _symbol_signal_bar(writer, tid: str, label: str, bundle_root: Path) -> str:
    del bundle_root
    return _localized_signal_label_bar(writer, tid, label)


def _symbols_signal_table(writer, tid: str, signals: list[tuple[str, str]],
                          width: float, bundle_root: Path,
                          lang: str = "en", *,
                          row_heights: list[float] | None = None) -> str:
    copy = symbol_copy(lang)
    rows = [(copy["symbol"], copy["meaning"], True)] + [
        (label, text, False) for label, text in signals
    ]
    left_col = component_param_pt(
        writer.params,
        "comp_symbol_signal_col_width",
        width * 0.24,
        strict=writer.strict_component_assets,
        owner="symbol signal table",
    )
    cols = [left_col, width - left_col]
    cells = []
    for ri, (left, right, header) in enumerate(rows):
        if header:
            left_xml = writer._psr("HB Symbol Header", left, terminal=True)
            right_xml = writer._psr("HB Symbol Header", right, terminal=True)
        else:
            left_xml = writer._symbol_signal_bar(f"{tid}sig{ri}", left, bundle_root)
            right_xml = writer._psr("HB Spec Value", right, terminal=True)
        cells.append(writer._cell(f"{tid}c{ri}_0", f"0:{ri}", left_xml,
                                  fill="Color/HB Bg K05",
                                  top=3, bottom=3,
                                  left=6 if header else 7.6,
                                  right=4,
                                  valign=None if header else "CenterAlign"))
        cells.append(writer._cell(f"{tid}c{ri}_1", f"1:{ri}", right_xml,
                                  top=3, bottom=3, left=7, right=5))
    table = writer._component_table(
        tid, cols, cells, n_rows=len(rows), role="data", outer_stroke=False)
    if row_heights is not None:
        if len(row_heights) != len(rows):
            raise ValueError("symbol signal row heights must match rendered rows")
        for row_index, height in enumerate(row_heights):
            before = f'<Row Self="{tid}r{row_index}" Name="{row_index}"/>'
            after = (
                f'<Row Self="{tid}r{row_index}" Name="{row_index}" '
                f'SingleRowHeight="{height:g}" MinimumHeight="{height:g}" '
                'AutoGrow="false"/>'
            )
            if before not in table:
                raise ValueError(f"symbol signal row anchor missing: {tid}r{row_index}")
            table = table.replace(before, after, 1)
    return table


def _symbols_icon_table(
    writer,
    tid: str,
    icons: list[dict],
    width: float,
    lang: str = "en",
    *,
    include_header: bool = True,
    row_heights: list[float] | None = None,
) -> str:
    copy = symbol_copy(lang)
    header = [{"figure": "", "text": copy["meaning"], "header": True}]
    rows = (header if include_header else []) + [
        {**row, "header": False} for row in icons
    ]
    left_col = component_param_pt(
        writer.params,
        "idml_symbols_icon_col_width",
        component_param_pt(
            writer.params,
            "comp_symbol_icon_col_width",
            width * 0.27,
            strict=False,
            owner="symbol icon table fallback",
        ),
        strict=writer.strict_component_assets,
        owner="symbol icon table",
    )
    cols = [left_col, width - left_col]
    icon_w = component_param_pt(
        writer.params,
        "idml_symbols_icon_width",
        component_param_pt(
            writer.params,
            "comp_symbol_icon_width",
            18.0,
            strict=False,
            owner="symbol icon table fallback",
        ),
        strict=writer.strict_component_assets,
        owner="symbol icon table",
    )
    icon_h = component_param_pt(
        writer.params,
        "idml_symbols_icon_height",
        component_param_pt(
            writer.params,
            "comp_symbol_icon_height",
            18.0,
            strict=False,
            owner="symbol icon table fallback",
        ),
        strict=writer.strict_component_assets,
        owner="symbol icon table",
    )
    cells = []
    for ri, row in enumerate(rows):
        if row.get("header"):
            left_xml = writer._psr("HB Symbol Header", copy["symbol"], terminal=True)
            right_xml = writer._psr("HB Symbol Header", row["text"], terminal=True)
        else:
            fig = (ROOT / row["figure"]) if row.get("figure") else None
            icon = ""
            if fig and fig.exists():
                icon = writer._image_cell_content(
                    f"{tid}img{ri}", fig, icon_w, icon_h,
                )
            figure_style_ref = paragraph_style_ref("HB Figure")
            left_xml = (
                f'  <ParagraphStyleRange AppliedParagraphStyle="{figure_style_ref}">'
                '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                + icon + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
            right_xml = writer._psr("HB Symbol Body", row["text"], terminal=True)
            if lang in {"fr", "es"}:
                right_xml = right_xml.replace(
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                    'PointSize="5.6" Leading="6.15" HorizontalScale="96"',
                    1,
                )
        cells.append(writer._cell(f"{tid}c{ri}_0", f"0:{ri}", left_xml,
                                  fill="Color/HB Bg K05",
                                  top=2, bottom=2, left=4,
                                  right=2 if row.get("header") else 4))
        cells.append(writer._cell(f"{tid}c{ri}_1", f"1:{ri}", right_xml,
                                  top=2, bottom=2, left=5, right=4))
    table = writer._component_table(
        tid, cols, cells, n_rows=len(rows), role="data", outer_stroke=False)
    if row_heights is not None:
        if len(row_heights) != len(rows):
            raise ValueError("symbol table row heights must match rendered rows")
        for ri, height in enumerate(row_heights):
            before = f'<Row Self="{tid}r{ri}" Name="{ri}"/>'
            after = (
                f'<Row Self="{tid}r{ri}" Name="{ri}" '
                f'SingleRowHeight="{height:g}" MinimumHeight="{height:g}" '
                'AutoGrow="false"/>'
            )
            if before not in table:
                raise ValueError(f"symbol table row anchor missing: {tid}r{ri}")
            table = table.replace(before, after, 1)
    return table


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
    *,
    dense: bool = False,
) -> tuple[str, tuple[list[dict], list[dict]]]:
    """V2.0 page 02: safety tail + maintenance + symbols on one page."""
    import json as _json
    copy = symbol_copy(lang)
    style = SafetySymbolsPageStyle.from_writer(writer, lang)
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
    icon_gap = component_param_pt(
        writer.params,
        "idml_symbols_column_gap",
        component_param_pt(
            writer.params,
            "comp_symbol_column_gap",
            6.0,
            strict=False,
            owner="symbol icon tables fallback",
        ),
        strict=writer.strict_component_assets,
        owner="symbol icon tables",
    )
    icon_table_w = (body_w - icon_gap) / 2.0
    left_icons, right_icons, overflow_left, overflow_right = template_symbol_split(
        icons,
        dense=dense and lang in {"fr", "es"},
    )
    signal_sid = f"{sid}_signals"
    writer._table_story(
        signal_sid, "Signal words",
        writer._symbols_signal_table(
            f"{sid}_sig_tbl",
            signals,
            body_w,
            bundle_root,
            lang,
            row_heights=[style.signal_header_height]
            + [style.signal_row_height] * len(signals),
        ))
    left_row_heights = (
        [style.icon_header_height]
        + [style.icon_row_height] * max(0, len(left_icons) - 1)
        + ([style.icon_last_row_height] if left_icons else [])
    )
    right_row_heights = (
        [style.icon_header_height]
        + [style.icon_row_height] * max(0, len(right_icons) - 1)
        + ([
            style.icon_long_last_row_height
            if lang == "en" else style.icon_last_row_height
        ] if right_icons else [])
    )
    left_sid = f"{sid}_icons_left"
    writer._table_story(
        left_sid, "Symbol icons left",
        writer._symbols_icon_table(
            f"{sid}_icons_l_tbl",
            left_icons,
            icon_table_w,
            lang,
            row_heights=left_row_heights,
        ))
    right_sid = f"{sid}_icons_right"
    writer._table_story(
        right_sid, "Symbol icons right",
        writer._symbols_icon_table(
            f"{sid}_icons_r_tbl",
            right_icons,
            icon_table_w,
            lang,
            row_heights=right_row_heights,
        ))

    # Flow the frames from a cursor using coarse content-height estimates
    # instead of fixed rects (fixed heights hid taller content as overset);
    # the icon tables then take whatever remains down to the bottom margin.
    y = style.page_top
    frame_specs: list[tuple[str, str, tuple[float, float, float, float], dict]] = []

    def _place(fid: str, story: str, h: float, opts: dict, gap: float = 6.0) -> None:
        nonlocal y
        frame_specs.append((fid, story, (body_x, y, body_w, h), opts))
        y += h + gap

    tail_geometry = (
        (style.first_tail_height, style.first_tail_gap),
        (style.second_tail_height, style.second_tail_gap),
    )
    for ti, ((t_sid, _estimated_height), (tail_h, tail_gap)) in enumerate(
        zip(tail_stories, tail_geometry, strict=False)
    ):
        _place(
            f"tail_{ti}",
            t_sid,
            tail_h,
            with_rounded_outer({
                "inset": (0, 0, 0, 0),
                "valign": "CenterAlign",
            }),
            gap=tail_gap,
        )
    _place("maint_title", maint_title_sid, SUBBAR_H,
           heading_bar_opts(2, (0.5, 5, 0.5, 6)), gap=3.5)
    _place(
        "maint_body",
        maint_body_sid,
        style.maintenance_body_height,
        {"inset": (0, 0, 0, 0)},
        gap=style.maintenance_body_gap,
    )
    _place("symbols_title", symbols_title_sid, h1_bar_h_pt(writer),
           heading_bar_opts(1, (1.5, 5, 1, 6)), gap=9.0)
    signals_h = style.signal_header_height + style.signal_row_height * len(signals)
    _place("signals", signal_sid, signals_h,
           with_rounded_outer({"inset": (0, 0, 0, 0)}),
           gap=style.signal_gap_after)
    bottom = writer.page_h - 2.0
    if lang in {"en", "fr", "es"}:
        icons_h = 3.0 + max(sum(left_row_heights), sum(right_row_heights))
    else:
        icons_h = 3.0 + max(60.0, min(
            max(est_table_height([r.get("text", "") for r in left_icons],
                                 icon_table_w * 0.73, 24.0),
                est_table_height([r.get("text", "") for r in right_icons],
                                 icon_table_w * 0.73, 24.0)),
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
    return spread_id, (overflow_left, overflow_right)
