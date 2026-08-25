"""Compose existing editable IDML components on one measured physical page.

The LaTeX fallback page plan can map multiple semantic source pages to the
same physical page.  This module does not define another visual style; it
only places the existing prose, Symbols, LCD, and Operations stories into
non-overlapping regions on that shared page.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import oppanel
from .components.prose_image import (
    IMAGE_ROLE_CHARGING_DIAGRAM,
    IMAGE_ROLE_FULL_MEASURE,
    IMAGE_ROLE_REFERENCE_MEASURE,
    IMAGE_ROLE_WIDE_DIAGRAM,
)
from .components.lcd_callout import add_lcd_callouts
from .components.symbols_panel import SymbolsPanel, SymbolsPanelData
from .heading_suffix import promote_h2_suffix_pills
from .page_objects import (
    frame_with_background,
    h1_bar_h_pt,
    heading_bar_opts,
    heading_text,
)
from .params import IDPKG, param_pt
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
    body_x = writer.m_l
    body_w = writer.page_w - writer.m_l - writer.m_r
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
    title_h = h1_bar_h_pt(writer)
    panel = SymbolsPanel(
        writer,
        sid=symbol_sid,
        data=SymbolsPanelData.from_source(symbol_data),
        bundle_root=bundle_root,
        language=lang,
        density="compact",
    ).render(
        x=body_x,
        y=symbols_top,
        width=body_w,
        available_height=writer.page_h - symbols_top,
    )
    if panel.overflow.has_rows():
        raise ValueError("compact SymbolsPanel cannot drop symbol rows")
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
        *panel.frames,
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
    composition_data: dict | None = None,
) -> tuple[str, str]:
    """Place the existing compact LCD and Operations components on one page."""

    lcd_options = dict((composition_data or {}).get("lcd") or {})
    operation_blocks = oppanel.transform(operation_blocks)
    operation_panel_variant = str(
        lcd_options.get("operation_panel_variant") or ""
    )
    if operation_panel_variant:
        if operation_panel_variant != "paired_cards":
            raise ValueError(
                "unsupported LCD/Operations panel variant: "
                f"{operation_panel_variant}"
            )
        operation_blocks = oppanel.promote_paired_operation_cards(
            operation_blocks,
        )
    table_variant = str(
        lcd_options.get("table_variant")
        or "number_icon_label_description"
    )
    lcd_sid = writer.add_lcd_story(
        list(lcd_data.rows),
        data_root,
        lang=language,
        title=lcd_data.title,
        hero_path=hero_path,
        compact=True,
        table_variant=table_variant,
        hero_horizontal_scale=lcd_options.get("hero_horizontal_scale"),
    )
    if writer.lcd_segment_counts.get(language, 1) != 1:
        raise ValueError("shared LCD/Operations page requires one LCD segment")
    writer.add_prose_story(
        operation_sid,
        operation_title,
        operation_blocks,
        bundle_root,
        language=language,
        image_roles=(IMAGE_ROLE_FULL_MEASURE,) * sum(
            kind == "image" for kind, _payload in operation_blocks
        ),
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
    add_lcd_callouts(
        writer,
        page_index=page_index,
        language=language,
        rows=list(lcd_data.rows),
        callouts=list(lcd_options.get("hero_callouts") or []),
    )
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
    composition_data: dict | None = None,
) -> str:
    """Place Connections through target-declared shared semantic variants."""

    options = dict((composition_data or {}).get("connections") or {})
    layout_variant = str(options.get("layout_variant") or "")
    prepared_blocks = list(blocks)
    if layout_variant:
        if layout_variant != "notice_before_primary_figure":
            raise ValueError(
                f"unsupported Connections layout variant: {layout_variant}"
            )
        image_index = next((
            index for index, (kind, _payload) in enumerate(prepared_blocks)
            if kind == "image"
        ), None)
        notice_index = None
        if image_index is not None:
            for index in range(image_index + 1, len(prepared_blocks)):
                kind, payload = prepared_blocks[index]
                if kind != "component":
                    continue
                try:
                    spec = json.loads(payload)
                except (TypeError, json.JSONDecodeError):
                    continue
                if isinstance(spec, dict) and spec.get("kind") == "notice":
                    notice_index = index
                    break
        if image_index is None or notice_index is None:
            raise ValueError(
                "notice_before_primary_figure requires an image followed by "
                "a notice component"
            )
        notice = prepared_blocks.pop(notice_index)
        prepared_blocks.insert(image_index, notice)
        notice_roles = ("bp_connection_caution", "bp_connection_notes")
        notice_ordinal = 0
        for index, (kind, payload) in enumerate(prepared_blocks):
            if kind != "component" or notice_ordinal >= len(notice_roles):
                continue
            try:
                spec = json.loads(payload)
            except (TypeError, json.JSONDecodeError):
                continue
            if not isinstance(spec, dict) or spec.get("kind") != "notice":
                continue
            spec["layout_role"] = notice_roles[notice_ordinal]
            prepared_blocks[index] = (
                kind,
                json.dumps(spec, ensure_ascii=False),
            )
            notice_ordinal += 1

    image_role_name = str(options.get("image_role") or "full_measure")
    image_roles = {
        "full_measure": IMAGE_ROLE_FULL_MEASURE,
        "reference_measure": IMAGE_ROLE_REFERENCE_MEASURE,
    }
    try:
        image_role = image_roles[image_role_name]
    except KeyError as exc:
        raise ValueError(
            f"unsupported Connections semantic image role: {image_role_name}"
        ) from exc
    image_count = sum(kind == "image" for kind, _payload in prepared_blocks)

    writer.add_prose_story(
        sid,
        title,
        prepared_blocks,
        bundle_root,
        language=language,
        image_roles=(image_role,) * image_count,
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
    trouble_sid: str,
    trouble_title: str,
    trouble_blocks: list[tuple[str, str]],
    bundle_root: Path,
    page_index: int,
    language: str,
    composition_data: dict | None = None,
) -> tuple[str, str]:
    """Compose a plan-routed connection tail above the shared trouble table."""

    if not connection_blocks:
        raise ValueError("connection-tail composition requires routed blocks")
    options = dict((composition_data or {}).get("troubleshooting") or {})
    image_role_name = str(
        options.get("connection_image_role") or "wide_diagram"
    )
    image_roles = {
        "wide_diagram": (IMAGE_ROLE_WIDE_DIAGRAM,),
        "full_measure": (IMAGE_ROLE_FULL_MEASURE,),
        "reference_measure": (IMAGE_ROLE_REFERENCE_MEASURE,),
    }
    if image_role_name not in image_roles:
        raise ValueError(
            "connection-tail troubleshooting image role must be wide_diagram "
            "or full_measure/reference_measure"
        )
    writer.add_prose_story(
        connection_sid,
        connection_title,
        connection_blocks,
        bundle_root,
        language=language,
        image_roles=image_roles[image_role_name],
    )
    writer.add_prose_story(
        trouble_sid,
        trouble_title,
        trouble_blocks,
        bundle_root,
        language=language,
        disable_hyphenation=True,
        first_h1_space_after=(
            float(options["heading_space_after"])
            if "heading_space_after" in options
            else None
        ),
    )
    page_top = param_pt(writer.params, "idml_shared_page_top", 27.7)
    split = float(options.get("split")) if "split" in options else param_pt(
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


def add_charging_page(
    writer,
    *,
    sid: str,
    title: str,
    charging_blocks: list[tuple[str, str]],
    bundle_root: Path,
    page_index: int,
    language: str,
    composition_data: dict | None = None,
) -> str:
    """Place Charging through target-declared shared semantic variants."""

    options = dict((composition_data or {}).get("charging") or {})
    image_role_name = str(options.get("image_role") or "charging_diagram")
    image_roles = {
        "charging_diagram": IMAGE_ROLE_CHARGING_DIAGRAM,
        "full_measure": IMAGE_ROLE_FULL_MEASURE,
        "reference_measure": IMAGE_ROLE_REFERENCE_MEASURE,
    }
    try:
        image_role = image_roles[image_role_name]
    except KeyError as exc:
        raise ValueError(
            f"unsupported Charging semantic image role: {image_role_name}"
        ) from exc
    prepared_blocks = promote_h2_suffix_pills(
        charging_blocks,
        list(options.get("h2_suffix_pill_indices") or []),
    )
    image_count = sum(kind == "image" for kind, _text in prepared_blocks)

    writer.add_prose_story(
        sid,
        title,
        prepared_blocks,
        bundle_root,
        language=language,
        image_roles=(image_role,) * image_count,
    )
    page_top = param_pt(writer.params, "idml_shared_page_top", 27.7)
    bottom = writer.page_h - writer.m_b + param_pt(
        writer.params,
        "idml_compact_charging_frame_bottom_extra",
        36.0,
    )
    writer.add_story_frames(sid, [(page_index, page_top, bottom)])
    return sid


def grouped_spec_sections(
    sections: list[dict],
    composition_data: dict | None,
) -> list[dict]:
    """Apply target-declared section grouping without inspecting localized copy."""

    options = dict((composition_data or {}).get("specifications") or {})
    groups = list(options.get("section_groups") or [])
    if not groups:
        return [dict(section) for section in sections]
    grouped: list[dict] = []
    used: list[int] = []
    for group in groups:
        indices = list(group.get("source_indices") or [])
        if not indices:
            raise ValueError("specification section group cannot be empty")
        if any(
            not isinstance(index, int) or isinstance(index, bool)
            or index < 0 or index >= len(sections)
            for index in indices
        ):
            raise ValueError("specification section group index is out of range")
        selected = [sections[index] for index in indices]
        rows = [
            row
            for section in selected
            for row in list(section.get("rows") or [])
        ]
        grouped.append({
            "title": str(group.get("title") or selected[0].get("title") or ""),
            "rows": rows,
        })
        used.extend(indices)
    if sorted(used) != list(range(len(sections))):
        raise ValueError(
            "specification section groups must cover each source section once"
        )
    return grouped


def add_storage_specifications_page(
    writer,
    *,
    sid: str,
    storage_blocks: list[tuple[str, str]],
    spec_data,
    bundle_root: Path,
    page_index: int,
    language: str,
    composition_data: dict | None = None,
) -> tuple[str, str, list[dict]]:
    """Compose Storage and the existing specification tables on one page."""

    storage_title = source_text(
        next((text for kind, text in storage_blocks if kind == "h1"), ""),
        owner="Storage page title",
    )
    if not storage_title:
        raise ValueError("storage_specifications requires a Storage H1")
    storage_body = [
        block for block in storage_blocks if block[0] != "h1"
    ]
    storage_title_sid = f"{sid}_storage_title"
    storage_body_sid = f"{sid}_storage_body"
    writer._add_story_parts(
        storage_title_sid,
        f"{storage_title} title",
        [heading_text(writer, storage_title, level=1)],
    )
    writer.add_prose_story(
        storage_body_sid,
        f"{storage_title} body",
        storage_body,
        bundle_root,
        language=language,
        disable_hyphenation=True,
    )

    options = dict((composition_data or {}).get("specifications") or {})
    sections = grouped_spec_sections(list(spec_data.sections), composition_data)
    spec_sid = writer.add_spec_story(
        sections,
        list(spec_data.annotations),
        lang=language,
        title=spec_data.title,
        layout_variant=str(options.get("layout_variant") or "reference"),
    )

    body_x = writer.m_l
    body_w = writer.page_w - writer.m_l - writer.m_r
    page_top = param_pt(writer.params, "idml_shared_page_top", 27.7)
    title_h = h1_bar_h_pt(writer)
    body_top = param_pt(
        writer.params,
        "idml_compact_storage_spec_body_top",
        59.0,
    )
    body_bottom = param_pt(
        writer.params,
        "idml_compact_storage_spec_body_bottom",
        131.5,
    )
    spec_top = param_pt(
        writer.params,
        "idml_compact_storage_spec_spec_top",
        148.8,
    )
    if not page_top + title_h < body_top < body_bottom < spec_top:
        raise ValueError("storage_specifications frame tokens are not ordered")
    body_inset = param_pt(
        writer.params,
        "idml_compact_storage_spec_body_inset",
        6.0,
    )
    frames = [
        frame_with_background(
            writer,
            sid,
            "storage_title",
            storage_title_sid,
            (body_x, page_top, body_w, title_h),
            {
                **heading_bar_opts(1, (1.5, 5, 1, 6)),
                "text_rect": (
                    body_x + 6,
                    page_top,
                    body_w - 12,
                    title_h,
                ),
            },
        ),
        frame_with_background(
            writer,
            sid,
            "storage_body",
            storage_body_sid,
            (body_x, body_top, body_w, body_bottom - body_top),
            {
                "fill": "Color/HB Bg K05",
                "rounded": True,
                "inset": (body_inset, body_inset, body_inset, body_inset),
            },
        ),
    ]
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
    bottom = writer.page_h - writer.m_b + param_pt(
        writer.params,
        "idml_compact_spec_frame_bottom_extra",
        8.0,
    )
    writer.add_story_frames(spec_sid, [(page_index, spec_top, bottom)])
    return storage_body_sid, spec_sid, sections


__all__ = (
    "add_charging_page",
    "add_charging_storage_page",
    "add_connection_tail_troubleshooting_page",
    "add_connections_page",
    "add_fcc_inbox_overview_page",
    "add_lcd_operations_page",
    "add_safety_symbols_page",
    "add_storage_specifications_page",
    "grouped_spec_sections",
    "latex_start_page",
    "shares_latex_page",
)
