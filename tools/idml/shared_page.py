"""Compose existing editable IDML components on one measured physical page.

The LaTeX fallback page plan can map multiple semantic source pages to the
same physical page.  This module does not define another visual style; it
only places the existing prose, Symbols, LCD, and Operations stories into
non-overlapping regions on that shared page.
"""
from __future__ import annotations

from pathlib import Path

from . import oppanel
from .components.prose_image import (
    IMAGE_ROLE_CHARGING_DIAGRAM,
    IMAGE_ROLE_FULL_MEASURE,
    IMAGE_ROLE_WIDE_DIAGRAM,
)
from .layout_est import template_symbol_split
from .page_objects import (
    frame_with_background,
    h1_bar_h_pt,
    heading_bar_opts,
    heading_text,
    with_rounded_outer,
)
from .params import IDPKG, component_param_pt, param_pt
from .page03 import (
    BODY_W,
    BODY_X,
    H1_BAR_H,
    _fcc_objects,
    _inbox_objects,
    _spread_page,
    component_spec,
)
from .page_overview import product_overview_frames, single_image_overview_frames
from .source_copy import source_text
from .symbols_page import SafetySymbolsPageStyle


def latex_start_page(page_plan: dict | None, page: Path, bundle_root: Path) -> int | None:
    """Return the measured one-based physical page for a prepared source."""

    try:
        source_ref = page.relative_to(bundle_root).as_posix()
    except ValueError:
        source_ref = page.name
    matches = [
        entry.get("latex_start_page")
        for entry in (page_plan or {}).get("pages", [])
        if entry.get("source_path") == source_ref
    ]
    if len(matches) != 1 or matches[0] is None:
        return None
    return int(matches[0])


def shares_latex_page(
    page_plan: dict | None,
    first: Path,
    second: Path,
    bundle_root: Path,
) -> bool:
    """Return whether two consecutive sources share one measured page."""

    first_start = latex_start_page(page_plan, first, bundle_root)
    return first_start is not None and first_start == latex_start_page(
        page_plan, second, bundle_root,
    )


def add_safety_symbols_page(
    writer,
    *,
    safety_sid: str,
    safety_title: str,
    safety_blocks: list[tuple[str, str]],
    symbol_data,
    bundle_root: Path,
    data_root: Path,
    page_index: int,
    language: str,
) -> tuple[str, str]:
    """Compose the existing compact Safety and two-column Symbols components.

    The measured fallback plan owns only the fact that both semantic sources
    share one physical page.  Typography, table construction, icon fitting,
    signal badges, and rounded shells stay owned by the same component
    helpers used by the approved Safety/Symbols composition.
    """

    del data_root  # Figure paths are already resolved by Manual IR projection.
    lang = language.strip().casefold().replace("_", "-").split("-", 1)[0]
    style = SafetySymbolsPageStyle.from_writer(writer, lang)
    h1 = source_text(
        next((text for kind, text in safety_blocks if kind == "h1"), ""),
        owner="compact Safety page title",
    )
    body_blocks = [block for block in safety_blocks if block[0] != "h1"]
    safety_title_sid = f"{safety_sid}_title"
    writer._add_story_parts(
        safety_title_sid,
        h1,
        [heading_text(writer, h1, level=1)],
    )
    writer._safety_section_story(
        safety_sid,
        safety_title,
        body_blocks,
        bundle_root,
        compact=True,
    )

    symbol_sid = f"st_symbols_shared_{lang}"
    symbols_title = source_text(
        symbol_data.title,
        owner="compact Symbols page title",
    )
    signal_headers = tuple(
        source_text(value, owner=f"compact Symbols signal header {index + 1}")
        for index, value in enumerate(symbol_data.signal_headers)
    )
    icon_headers = tuple(
        source_text(value, owner=f"compact Symbols icon header {index + 1}")
        for index, value in enumerate(symbol_data.icon_headers)
    )
    symbols_title_sid = f"{symbol_sid}_title"
    writer._add_story_parts(
        symbols_title_sid,
        symbols_title,
        [heading_text(writer, symbols_title, level=1)],
    )

    body_x = writer.m_l
    body_w = writer.page_w - writer.m_l - writer.m_r
    signal_sid = f"{symbol_sid}_signals"
    writer._table_story(
        signal_sid,
        "Signal words",
        writer._symbols_signal_table(
            f"{symbol_sid}_sig_tbl",
            list(symbol_data.signals),
            body_w,
            bundle_root,
            lang,
            headers=signal_headers,
            row_heights=[style.signal_header_height]
            + [style.signal_row_height] * len(symbol_data.signals),
        ),
    )

    icon_gap = component_param_pt(
        writer.params,
        "idml_symbols_column_gap",
        component_param_pt(
            writer.params,
            "comp_symbol_column_gap",
            6.0,
            strict=False,
            owner="compact Symbols column fallback",
        ),
        strict=writer.strict_component_assets,
        owner="compact Symbols columns",
    )
    icon_table_trim = component_param_pt(
        writer.params,
        "idml_symbols_icon_table_width_trim",
        0.0,
        strict=writer.strict_component_assets,
        owner="compact Symbols tables",
    )
    icon_table_w = (body_w - icon_gap) / 2.0 - icon_table_trim
    icon_col = component_param_pt(
        writer.params,
        "idml_symbols_icon_col_width",
        component_param_pt(
            writer.params,
            "comp_symbol_icon_col_width",
            39.685,
            strict=False,
            owner="compact Symbols icon column fallback",
        ),
        strict=writer.strict_component_assets,
        owner="compact Symbols icon column",
    )
    left_icons, right_icons, overflow_left, overflow_right = (
        template_symbol_split(list(symbol_data.icons), dense=False)
    )
    if overflow_left or overflow_right:
        raise ValueError("compact Safety/Symbols page cannot drop symbol rows")

    def icon_row_heights(rows: list[dict], *, long_last: bool) -> list[float]:
        return (
            [style.icon_header_height]
            + [style.icon_row_height] * max(0, len(rows) - 1)
            + ([style.icon_long_last_row_height if long_last
                else style.icon_last_row_height] if rows else [])
        )

    left_heights = icon_row_heights(left_icons, long_last=False)
    right_heights = icon_row_heights(right_icons, long_last=True)
    shell_height = max(sum(left_heights), sum(right_heights))
    if left_heights:
        left_heights[-1] += shell_height - sum(left_heights)
    if right_heights:
        right_heights[-1] += shell_height - sum(right_heights)

    left_sid = f"{symbol_sid}_icons_left"
    writer._table_story(
        left_sid,
        "Symbol icons left",
        writer._symbols_icon_table(
            f"{symbol_sid}_icons_l_tbl",
            left_icons,
            icon_table_w,
            lang,
            headers=icon_headers,
            row_heights=left_heights,
            icon_col_width=icon_col,
            fit_body_to_row=True,
        ),
    )
    right_sid = f"{symbol_sid}_icons_right"
    writer._table_story(
        right_sid,
        "Symbol icons right",
        writer._symbols_icon_table(
            f"{symbol_sid}_icons_r_tbl",
            right_icons,
            icon_table_w,
            lang,
            headers=icon_headers,
            row_heights=right_heights,
            icon_col_width=icon_col,
            fit_body_to_row=True,
        ),
    )

    page_top = param_pt(writer.params, "idml_shared_page_top", 27.7)
    symbols_top = param_pt(
        writer.params,
        f"lang_{lang}_idml_compact_safety_symbols_title_top",
        param_pt(
            writer.params,
            "idml_compact_safety_symbols_title_top",
            163.2,
        ),
    )
    title_body_gap = param_pt(
        writer.params,
        "idml_compact_safety_title_body_gap",
        3.5,
    )
    safety_bottom_gap = param_pt(
        writer.params,
        "idml_compact_safety_symbols_gap",
        4.0,
    )
    symbols_title_gap = param_pt(
        writer.params,
        "idml_compact_symbols_title_gap",
        6.0,
    )
    title_h = h1_bar_h_pt(writer)
    signal_top = symbols_top + title_h + symbols_title_gap
    signal_h = style.signal_header_height + (
        style.signal_row_height * len(symbol_data.signals)
    )
    icons_top = signal_top + signal_h + style.signal_gap_after
    icons_h = shell_height + param_pt(
        writer.params,
        "idml_compact_symbols_table_frame_allowance",
        style.table_frame_allowance,
    )
    frames = [
        frame_with_background(
            writer,
            symbol_sid,
            "safety_title",
            safety_title_sid,
            (body_x, page_top, body_w, title_h),
            {
                **heading_bar_opts(1, (1.5, 5, 1, 6)),
                "text_rect": (body_x + 6, page_top, body_w - 12, title_h),
            },
        ),
        frame_with_background(
            writer,
            symbol_sid,
            "safety_body",
            safety_sid,
            (
                body_x,
                page_top + title_h + title_body_gap,
                body_w,
                symbols_top
                - safety_bottom_gap
                - (page_top + title_h + title_body_gap),
            ),
            {"inset": (0, 0, 0, 0)},
        ),
        frame_with_background(
            writer,
            symbol_sid,
            "symbols_title",
            symbols_title_sid,
            (body_x, symbols_top, body_w, title_h),
            {
                **heading_bar_opts(1, (1.5, 5, 1, 6)),
                "text_rect": (body_x + 6, symbols_top, body_w - 12, title_h),
            },
        ),
        frame_with_background(
            writer,
            symbol_sid,
            "signals",
            signal_sid,
            (body_x, signal_top, body_w, signal_h),
            with_rounded_outer({
                "inset": (0, 0, 0, 0),
                "rounded_outer_masks": True,
            }),
        ),
        frame_with_background(
            writer,
            symbol_sid,
            "icons_left",
            left_sid,
            (body_x, icons_top, icon_table_w, icons_h),
            with_rounded_outer({
                "inset": (0, 0, 0, 0),
                "rounded_outer_masks": True,
            }),
        ),
        frame_with_background(
            writer,
            symbol_sid,
            "icons_right",
            right_sid,
            (body_x + icon_table_w + icon_gap, icons_top, icon_table_w, icons_h),
            with_rounded_outer({
                "inset": (0, 0, 0, 0),
                "rounded_outer_masks": True,
            }),
        ),
    ]
    spread_id = f"sp_{page_index}"
    writer.spreads.append((
        spread_id,
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" '
        'ShowMasterItems="true">\n'
        f'  <Page Self="{spread_id}_pg" Name="{page_index + 1}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" '
        'GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} '
        f'{-writer.page_h / 2:g}">\n'
        '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
        f'Top="{writer.m_t:g}" Bottom="{writer.m_b:g}" '
        f'Left="{writer.m_l:g}" Right="{writer.m_r:g}"/>\n'
        '  </Page>\n'
        + "".join(frames)
        + '</Spread>\n</idPkg:Spread>\n'
    ))
    return safety_sid, symbol_sid


def add_lcd_operations_page(
    writer,
    *,
    lcd_data,
    operation_sid: str,
    operation_title: str,
    operation_blocks: list[tuple[str, str]],
    bundle_root: Path,
    data_root: Path,
    page_index: int,
    language: str,
    hero_path: Path | None,
) -> tuple[str, str]:
    """Place the existing compact LCD and Operations components on one page."""

    operation_blocks = oppanel.transform(operation_blocks)
    lcd_sid = writer.add_lcd_story(
        list(lcd_data.rows),
        data_root,
        lang=language,
        title=lcd_data.title,
        hero_path=hero_path,
        compact=True,
    )
    if writer.lcd_segment_counts.get(language, 1) != 1:
        raise ValueError("shared LCD/Operations page requires one LCD segment")
    writer.add_prose_story(
        operation_sid,
        operation_title,
        operation_blocks,
        bundle_root,
        language=language,
        image_roles=(IMAGE_ROLE_FULL_MEASURE,),
    )
    page_top = param_pt(writer.params, "idml_shared_page_top", 27.7)
    split = param_pt(
        writer.params,
        f"lang_{language}_idml_compact_lcd_operations_split",
        param_pt(writer.params, "idml_compact_lcd_operations_split", 181.0),
    )
    gap = param_pt(writer.params, "idml_compact_shared_page_gap", 4.0)
    bottom = writer.page_h - writer.m_b + param_pt(
        writer.params, "idml_compact_operations_frame_bottom_extra", 8.0,
    )
    writer.add_story_frames(lcd_sid, [(page_index, page_top, split)])
    writer.add_story_frames(operation_sid, [(page_index, split + gap, bottom)])
    return lcd_sid, operation_sid


def add_connections_page(
    writer,
    *,
    sid: str,
    title: str,
    blocks: list[tuple[str, str]],
    bundle_root: Path,
    page_index: int,
    language: str,
) -> str:
    """Place the connection hero at full measure on its planned page."""

    writer.add_prose_story(
        sid,
        title,
        blocks,
        bundle_root,
        language=language,
        image_roles=(IMAGE_ROLE_FULL_MEASURE,),
    )
    page_top = param_pt(writer.params, "idml_shared_page_top", 27.7)
    bottom = writer.page_h - writer.m_b + param_pt(
        writer.params,
        "idml_compact_connections_frame_bottom_extra",
        8.0,
    )
    writer.add_story_frames(sid, [(page_index, page_top, bottom)])
    return sid


def add_fcc_inbox_overview_page(
    writer,
    *,
    sid: str,
    fcc_blocks: list[tuple[str, str]],
    inbox_blocks: list[tuple[str, str]],
    overview_blocks: list[tuple[str, str]],
    bundle_root: Path,
    page_index: int,
    language: str,
) -> str:
    """Compose FCC, inbox cards, and one-art overview on one physical page."""

    lang = language.strip().casefold().replace("_", "-").split("-", 1)[0]
    fcc_top = param_pt(writer.params, "idml_shared_page_top", 27.7)
    fcc_height = param_pt(
        writer.params,
        "idml_compact_fcc_inbox_overview_fcc_height",
        116.0,
    )
    _, fcc_frames = _fcc_objects(
        writer,
        sid,
        fcc_blocks,
        bundle_root,
        panel_y=fcc_top,
        panel_h=fcc_height,
        lang=lang,
    )

    inbox_title = next(
        (text.strip() for kind, text in inbox_blocks if kind == "h1" and text.strip()),
        "",
    )
    if not inbox_title:
        raise ValueError("shared FCC/inbox/overview composition requires inbox title")
    inbox_spec = component_spec(inbox_blocks, "inbox")
    if inbox_spec is None:
        raise ValueError("shared FCC/inbox/overview composition requires inbox data")
    inbox_title_y = param_pt(
        writer.params,
        "idml_compact_inbox_title_y",
        fcc_top + fcc_height + 7.0,
    )
    inbox_title_sid = writer._add_story_parts(
        f"{sid}_inbox_title",
        inbox_title,
        [heading_text(writer, inbox_title, level=1)],
    )
    _, inbox_frames = _inbox_objects(
        writer,
        sid,
        inbox_spec,
        bundle_root,
        lang=lang,
        metric_namespace="compact_",
        require_tip=False,
        accessibility_label=inbox_title,
        tip_label="",
        tip_body="",
    )
    inbox_title_frame = frame_with_background(
        writer,
        sid,
        "inbox_title",
        inbox_title_sid,
        (BODY_X, inbox_title_y, BODY_W, H1_BAR_H),
        {
            **heading_bar_opts(1, (1.5, 5, 1, 6)),
            "text_rect": (
                BODY_X + 6.0,
                inbox_title_y,
                BODY_W - 12.0,
                H1_BAR_H,
            ),
        },
    )

    overview_top = param_pt(
        writer.params,
        "idml_compact_overview_top",
        292.0,
    )
    overview_height = param_pt(
        writer.params,
        "idml_compact_overview_height",
        142.0,
    )
    overview_h1 = any(kind == "h1" and text.strip() for kind, text in overview_blocks)
    overview_h2s = [text for kind, text in overview_blocks if kind == "h2"]
    overview_images = [text for kind, text in overview_blocks if kind == "image"]
    if overview_h1 and not overview_h2s and len(overview_images) == 1:
        overview_frames = single_image_overview_frames(
            writer,
            f"{sid}_overview",
            overview_blocks,
            bundle_root,
            page_top=overview_top,
            image_height=overview_height,
        )
    else:
        overview_frames = product_overview_frames(
            writer,
            f"{sid}_overview",
            overview_blocks,
            bundle_root,
        )
    frames = [*fcc_frames, inbox_title_frame, *inbox_frames, *overview_frames]
    spread_id = f"sp_{page_index}"
    writer.spreads.append((
        spread_id,
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" '
        'ShowMasterItems="true">\n'
        + _spread_page(writer, spread_id, page_index + 1)
        + "".join(frames)
        + '</Spread>\n</idPkg:Spread>\n',
    ))
    return spread_id


def add_connection_tail_troubleshooting_page(
    writer,
    *,
    connection_sid: str,
    connection_title: str,
    connection_blocks: list[tuple[str, str]],
    trouble_data,
    bundle_root: Path,
    page_index: int,
    language: str,
) -> tuple[str, str]:
    """Compose a plan-routed connection tail above the shared trouble table."""

    if not connection_blocks:
        raise ValueError("connection-tail composition requires routed blocks")
    writer.add_prose_story(
        connection_sid,
        connection_title,
        connection_blocks,
        bundle_root,
        language=language,
        image_roles=(IMAGE_ROLE_WIDE_DIAGRAM,),
    )
    trouble_sid = writer.add_trouble_story(
        list(trouble_data.rows),
        title=trouble_data.title,
        lang=language,
    )
    page_top = param_pt(writer.params, "idml_shared_page_top", 27.7)
    split = param_pt(
        writer.params,
        "idml_compact_connection_trouble_split",
        218.0,
    )
    gap = param_pt(writer.params, "idml_compact_shared_page_gap", 4.0)
    bottom = writer.page_h - writer.m_b + param_pt(
        writer.params,
        "idml_compact_trouble_frame_bottom_extra",
        18.0,
    )
    writer.add_story_frames(connection_sid, [(page_index, page_top, split)])
    writer.add_story_frames(trouble_sid, [(page_index, split + gap, bottom)])
    return connection_sid, trouble_sid


def add_charging_storage_page(
    writer,
    *,
    sid: str,
    title: str,
    charging_blocks: list[tuple[str, str]],
    storage_blocks: list[tuple[str, str]],
    bundle_root: Path,
    page_index: int,
    language: str,
) -> str:
    """Compose Charging and Storage with reusable semantic image roles."""

    blocks = [*charging_blocks, *storage_blocks]
    writer.add_prose_story(
        sid,
        title,
        blocks,
        bundle_root,
        language=language,
        image_roles=(IMAGE_ROLE_CHARGING_DIAGRAM, IMAGE_ROLE_CHARGING_DIAGRAM),
    )
    page_top = param_pt(writer.params, "idml_shared_page_top", 27.7)
    bottom = writer.page_h - writer.m_b + param_pt(
        writer.params,
        "idml_compact_charging_storage_frame_bottom_extra",
        18.0,
    )
    writer.add_story_frames(sid, [(page_index, page_top, bottom)])
    return sid


__all__ = (
    "add_charging_storage_page",
    "add_connection_tail_troubleshooting_page",
    "add_connections_page",
    "add_fcc_inbox_overview_page",
    "add_lcd_operations_page",
    "add_safety_symbols_page",
    "latex_start_page",
    "shares_latex_page",
)
