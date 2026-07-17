"""Absolute-positioned composed-page assemblers for the IDML exporter."""
from __future__ import annotations

from pathlib import Path

from .page_objects import frame_with_background, h1_bar_h_pt, heading_bar_opts, heading_text, with_rounded_outer
from .params import IDPKG, param_pt
from .symbols_page import (
    ROOT as ROOT,
    SUBBAR_H,
    _localized_signal_label_bar,
    _symbol_signal_bar,
    _symbols_icon_table,
    _symbols_signal_table,
    _table_story,
    add_safety_symbols_page,
)


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
    *,
    symbol_overflow: tuple[list[dict], list[dict]] | None = None,
    lang: str = "en",
) -> str:
    from .page03 import add_fcc_inbox_page as _add_fcc_inbox_page

    return _add_fcc_inbox_page(
        writer,
        sid,
        fcc_blocks,
        inbox_blocks,
        bundle_root,
        page_index,
        symbol_overflow=symbol_overflow,
        lang=lang,
    )
