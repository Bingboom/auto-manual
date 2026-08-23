"""Absolute-positioned composed-page assemblers for the IDML exporter."""
from __future__ import annotations

from pathlib import Path

from .page_objects import frame_with_background, h1_bar_h_pt, heading_bar_opts, heading_text, with_rounded_outer
from .params import IDPKG, component_param_pt, param_pt
from .safety_story import _safety_language, _safety_list_xml, _safety_section_story
from .source_copy import source_block_text
from .symbols_page import (
    ROOT as ROOT, SymbolOverflow,
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


def _split_safety_section_at_list(
    blocks: list[tuple[str, str]], left_list_items: int,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    seen = 0
    for index, (kind, _text) in enumerate(blocks):
        if kind != "list":
            continue
        if seen == left_list_items:
            return blocks[:index], blocks[index:]
        seen += 1
    raise ValueError(
        "approved safety-page split exceeds the available first-section list items"
    )


def _approved_safety_param(writer, key: str, default: float) -> float:
    return component_param_pt(
        writer.params,
        key,
        default,
        strict=writer.strict_component_assets,
        owner="safety-page",
    )

def add_safety_page(writer, sid: str, title: str, blocks: list[tuple[str, str]], bundle_root: Path, page_index: int) -> str:
    """V2.0 US safety page 01: fixed component regions, not one flow."""
    h1 = source_block_text(blocks, "h1", owner="Safety page title")
    top_warning = next((t for k, t in blocks
                        if k == "component" and any(
                            f'"kind": "{name}"' in t
                            for name in ("safetywarning", "safetyinstruction"))), None)
    subbar = source_block_text(blocks, "h2", owner="Safety operating-instructions title")

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
    language = _safety_language(sid)
    dense_reference = writer.strict_component_assets and language in {"fr", "es"}
    section_sids: list[tuple[str, str | None]] = []
    for idx, section in enumerate(sections[:2]):
        sec_sid = f"{sid}_section{idx + 1}"
        if idx == 0 and dense_reference:
            split_key = f"lang_{language}_idml_safety_first_section_left_list_items"
            base_left_count = _approved_safety_param(
                writer, "idml_safety_first_section_left_list_items", 5.0,
            )
            left_count = round(
                _approved_safety_param(writer, split_key, base_left_count)
            )
            left_blocks, right_blocks = _split_safety_section_at_list(
                section, left_count,
            )
            left_sid = f"{sec_sid}_left"
            right_sid = f"{sec_sid}_right"
            writer._safety_section_story(
                left_sid, f"{title} section {idx + 1} left",
                left_blocks, bundle_root,
            )
            writer._safety_section_story(
                right_sid, f"{title} section {idx + 1} right",
                right_blocks, bundle_root,
            )
            section_sids.append((left_sid, right_sid))
        else:
            writer._safety_section_story(
                sec_sid, f"{title} section {idx + 1}", section, bundle_root,
            )
            section_sids.append((sec_sid, None))

    spread_id = f"sp_{page_index}"
    page_no = page_index + 1
    body_x = writer.m_l
    body_w = writer.page_w - writer.m_l - writer.m_r
    column_gap = param_pt(writer.params, "comp_twocol_sep", 6.24)
    warning_top = _approved_safety_param(writer, "idml_safety_warning_top", 55.5)
    warning_height = _approved_safety_param(
        writer, "idml_safety_warning_height", 31.5,
    )
    second_section_top = _approved_safety_param(
        writer, "idml_safety_second_section_top", 281.88,
    )
    second_section_height = _approved_safety_param(
        writer, "idml_safety_second_section_height", 209.12,
    )
    subbar_height = param_pt(writer.params, "comp_subbar_height", 13.9)
    subbar_top = 263.0
    if dense_reference:
        warning_top = _approved_safety_param(
            writer, f"lang_{language}_idml_safety_warning_top", warning_top,
        )
        warning_height = _approved_safety_param(
            writer, f"lang_{language}_idml_safety_warning_height", warning_height,
        )
        second_section_height = _approved_safety_param(
            writer,
            f"lang_{language}_idml_safety_second_section_height",
            second_section_height,
        )
    frames = []
    for frame_id, story_id, rect, opts in (
        ("title", title_sid, (body_x, 27.92, body_w, h1_bar_h_pt(writer)),
         {**heading_bar_opts(1, (1.5, 0, 1, 0)),
          "text_rect": (body_x + 6.0, 26.0, body_w - 12.0, h1_bar_h_pt(writer))}),
        ("warning", warning_sid, (body_x, warning_top, body_w, warning_height),
         with_rounded_outer({
             "inset": (0, 0, 0, 0),
             "valign": "CenterAlign",
         })),
        ("section1", section_sids[0][0] if section_sids else "", (body_x, 95.77, body_w, 162.0),
         {"columns": 2, "gutter": column_gap,
          "balance_columns": True, "inset": (0, 0, 0, 0)}),
        ("subbar", bar_sid, (body_x, subbar_top, body_w, subbar_height),
         {**heading_bar_opts(2, (0.5, 0, 0.5, 0)),
          "text_rect": (body_x + 6.0, subbar_top, body_w - 12.0, subbar_height)}),
        ("section2", section_sids[1][0] if len(section_sids) > 1 else "",
         (body_x, second_section_top, body_w, second_section_height),
         {"columns": 2, "gutter": column_gap,
          "balance_columns": True, "inset": (0, 0, 0, 0)}),
    ):
        if not story_id:
            continue
        if frame_id == "section1" and dense_reference:
            base_gap = _approved_safety_param(
                writer, "idml_safety_first_section_column_gap", 13.4,
            )
            dense_gap = _approved_safety_param(
                writer, f"lang_{language}_idml_safety_first_section_column_gap",
                base_gap,
            )
            base_left_top = _approved_safety_param(
                writer, "idml_safety_first_section_left_top", 95.77,
            )
            left_top = _approved_safety_param(
                writer, f"lang_{language}_idml_safety_first_section_left_top",
                base_left_top,
            )
            base_right_top = _approved_safety_param(
                writer, "idml_safety_first_section_right_top", base_left_top,
            )
            right_top = _approved_safety_param(
                writer, f"lang_{language}_idml_safety_first_section_right_top",
                base_right_top,
            )
            bottom = _approved_safety_param(
                writer, "idml_safety_first_section_bottom", 257.77,
            )
            bottom = _approved_safety_param(
                writer,
                f"lang_{language}_idml_safety_first_section_bottom",
                bottom,
            )
            section_to_subbar_gap = _approved_safety_param(
                writer, "idml_safety_first_section_to_subbar_gap", 4.0,
            )
            bottom = min(bottom, subbar_top - section_to_subbar_gap)
            column_w = (body_w - dense_gap) / 2.0
            frames.append(frame_with_background(
                writer, sid, "section1_left", story_id,
                (body_x, left_top, column_w, bottom - left_top),
                {"inset": (0, 0, 0, 0)},
            ))
            frames.append(frame_with_background(
                writer, sid, "section1_right", section_sids[0][1] or "",
                (body_x + column_w + dense_gap, right_top,
                 column_w, bottom - right_top),
                {"inset": (0, 0, 0, 0)},
            ))
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
    symbol_overflow: SymbolOverflow | None = None,
    lang: str = "en",
    reference_profile: dict | None = None,
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
        reference_profile=reference_profile,
    )
