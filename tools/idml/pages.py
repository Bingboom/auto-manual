"""Absolute-positioned composed-page assemblers for the IDML exporter."""
from __future__ import annotations

from pathlib import Path

from .params import IDPKG
from .safety_story import _safety_section_story
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


def add_safety_page(
    writer,
    sid: str,
    title: str,
    blocks: list[tuple[str, str]],
    bundle_root: Path,
    page_index: int,
) -> str:
    """Place the complete standard Safety component on one page."""

    from .components.safety_panel import SafetyPanel, SafetyPanelData

    panel = SafetyPanel(
        writer,
        sid=sid,
        data=SafetyPanelData.from_blocks(blocks, story_title=title),
        bundle_root=bundle_root,
    ).render(
        x=writer.m_l,
        y=0.0,
        width=writer.page_w - writer.m_l - writer.m_r,
        available_height=writer.page_h,
    )
    spread_id = f"sp_{page_index}"
    page_no = page_index + 1
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" '
        'ShowMasterItems="true">\n'
        f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" '
        'GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} '
        f'{-writer.page_h / 2:g}">\n'
        '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
        f'Top="{writer.m_t:g}" Bottom="{writer.m_b:g}" '
        f'Left="{writer.m_l:g}" Right="{writer.m_r:g}"/>\n'
        '  </Page>\n'
        + "".join(panel.frames)
        + '</Spread>\n'
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
