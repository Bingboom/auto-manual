"""LCD, symbols, troubleshooting, and specification story builders."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

try:
    from tools.lcd_table_layout import split_lcd_table_rows
except ModuleNotFoundError:  # direct tools/export_idml.py execution
    from lcd_table_layout import split_lcd_table_rows  # type: ignore
from . import components as _components
from . import lcd_style as _lcd
from . import page_objects as _po
from . import table_borders as _tb
from .components.rounded_table import rounded_table_panel, table_text_indent
from .components.native_marker import (
    marked_text,
    marker_replacements,
    portable_symbol_text,
)
from .params import IDPKG, component_param_pt, param_pt
from .primitives import _ATTR_ENTITIES, spec_table
from .story_parts import add_story_parts
from .source_copy import source_text
from .spec_tables import spec_table_height
from .style_names import paragraph_style_ref

ROOT = Path(__file__).resolve().parents[2]


def add_lcd_story(
    writer,
    rows: list[dict],
    data_root: Path,
    lang: str = "en",
    *,
    title: str,
    hero_path: Path | None = None,
    compact: bool = False,
    table_variant: str = "number_icon_label_description",
    hero_horizontal_scale: float | None = None,
) -> str:
    """LCD icon table: circled-no / icon image / name / description."""
    if table_variant not in {
        "number_icon_label_description",
        "label_description",
    }:
        raise ValueError(f"unsupported LCD table variant: {table_variant}")
    title = source_text(title, owner="LCD page title")
    sid = "st_lcd" if lang == "en" else f"st_lcd_{lang}"
    body_w = (
        writer.page_w - writer.m_l - writer.m_r
        + param_pt(writer.params, "idml_lcd_table_width_adjust", 0.0)
    )
    is_english = lang.strip().casefold().replace("_", "-").startswith("en")
    first_limit = int(float(writer.params.get(
        "comp_lcd_first_segment_rows" if is_english
        else "comp_lcd_translated_first_segment_rows",
        ("7", "count"),
    )[0]))
    continuation_limit = int(float(writer.params.get(
        "comp_lcd_continuation_segment_rows" if is_english
        else "comp_lcd_translated_continuation_segment_rows",
        ("19", "count"),
    )[0]))
    raw_segments = split_lcd_table_rows(
        rows,
        lang=lang,
        first_segment_rows=first_limit,
        continuation_segment_rows=continuation_limit,
    )
    text_indent = table_text_indent(writer.params)
    governed_icon_line_reserve = component_param_pt(
        writer.params,
        "idml_lcd_governed_icon_line_reserve",
        0.0,
        strict=writer.strict_component_assets,
        owner="LCD governed row icon fit",
    )
    native_carrier_allowance = component_param_pt(
        writer.params,
        "idml_lcd_native_carrier_allowance",
        1.0,
        strict=writer.strict_component_assets,
        owner="LCD native terminal carrier",
    )
    def _vertical_pad(segment_index: int) -> float:
        if segment_index > 0:
            return param_pt(
                writer.params,
                f"lang_{lang}_idml_lcd_continuation_vertical_padding",
                param_pt(
                    writer.params,
                    "idml_lcd_continuation_vertical_padding",
                    param_pt(
                        writer.params,
                        "comp_lcd_continuation_vertical_padding",
                        1.2,
                    ),
                ),
            )
        if is_english:
            return param_pt(
                writer.params,
                "idml_lcd_first_vertical_padding",
                param_pt(writer.params, "comp_lcd_first_vertical_padding", 1.6),
            )
        return param_pt(
            writer.params,
            f"lang_{lang}_idml_lcd_translated_first_vertical_padding",
            param_pt(
                writer.params,
                "idml_lcd_translated_first_vertical_padding",
                param_pt(
                    writer.params,
                    "comp_lcd_translated_first_vertical_padding",
                    0.7,
                ),
            ),
        )

    prepared_segments: list[tuple[list[dict], list[float] | None]] = []
    for raw_index, raw_segment in enumerate(raw_segments):
        governed_heights = [
            str(row.get("row_height_pt") or "").strip() for row in raw_segment
        ]
        if not any(governed_heights):
            prepared_segments.append((raw_segment, None))
            continue
        if not all(governed_heights):
            raise ValueError(
                "LCD segment mixes governed and InDesign-native row heights"
            )
        base_heights = [float(height) for height in governed_heights]
        raw_cols, _, raw_pad = _lcd.layout_tokens(
            writer, body_w, segment_index=raw_index, lang=lang)
        if raw_index == 0:
            # The approved reference contract measures every physical row on
            # the first LCD page.  Preserve that exact distribution: a generic
            # character-width estimator is intentionally conservative and can
            # otherwise move the French terminal row onto a spurious third
            # page even though the reviewed template proves that it fits.
            # Continuation pages still use content-aware fitting/splitting
            # because their rows may change independently of the template.
            prepared_segments.append((raw_segment, base_heights))
        else:
            prepared_segments.extend(
                (
                    chunk_rows,
                    chunk_heights,
                )
                for chunk_rows, chunk_heights in _lcd.split_governed_rows(
                    writer,
                    raw_segment,
                    base_heights,
                    raw_cols,
                    padding=raw_pad,
                    vertical_pad=_vertical_pad(raw_index),
                    text_indent=text_indent,
                    lang=lang,
                    segment_index=raw_index,
                    governed_icon_line_reserve=governed_icon_line_reserve,
                )
            )
    writer.lcd_segment_counts[lang] = len(prepared_segments)
    table_panels: list[str] = []
    global_ri = 0
    for segment_index, (segment, row_heights) in enumerate(prepared_segments):
        full_cols, icon_pt, pad = _lcd.layout_tokens(
            writer, body_w, segment_index=segment_index, lang=lang)
        content_sized_rows = table_variant == "label_description" and row_heights is None
        if table_variant == "label_description":
            cols, label_description_pad, dynamic_row_heights = (
                _lcd.label_description_layout(
                    writer,
                    segment,
                    body_w,
                    lang=lang,
                    segment_index=segment_index,
                )
            )
        else:
            cols = full_cols
            label_description_pad = 0.0
            dynamic_row_heights = []
        if lang == "en":
            icon_pt = min(icon_pt, 23.0)
        vertical_pad = (
            label_description_pad
            if table_variant == "label_description"
            else _vertical_pad(segment_index)
        )
        tid = (
            "tbl_lcd" if segment_index == 0 and lang == "en"
            else f"tbl_lcd_{lang}" if segment_index == 0
            else f"tbl_lcd_cont_{lang}"
        )
        cells: list[str] = []
        terminal_fill = 0.0
        if segment_index == 0:
            if row_heights is not None:
                first_panel_height = param_pt(
                    writer.params,
                    f"lang_{lang}_idml_lcd_first_panel_height",
                    param_pt(
                        writer.params,
                        "idml_lcd_first_panel_height",
                        param_pt(
                            writer.params,
                            "comp_lcd_first_panel_height",
                            286.0,
                        ),
                    ),
                )
                terminal_fill = max(
                    0.0,
                    first_panel_height - sum(row_heights),
                )
            elif not compact:
                # Compact shared-page LCD tables own only their real rows.
                # The approved standalone LCD composition's terminal filler
                # would otherwise add 26+ pt of empty cell inset, hide the
                # final short row, and consume the Operations frame budget.
                terminal_fill = param_pt(
                    writer.params,
                    f"lang_{lang}_idml_lcd_first_terminal_fill",
                    param_pt(
                        writer.params,
                        "idml_lcd_first_terminal_fill",
                        0.0,
                    ),
                )
        elif row_heights is not None:
            # Every continuation frame is a complete page-owned table.  Its
            # last row absorbs the exact remaining page depth so the rounded
            # table closes on the linked-frame bottom instead of leaving a
            # white strip below it.  The inline anchor has a small native
            # baseline offset after IDML import; subtract it from the budget.
            visual_bottom = writer.page_h - param_pt(
                writer.params,
                f"lang_{lang}_idml_lcd_visual_bottom_gap",
                param_pt(
                    writer.params,
                    "idml_lcd_visual_bottom_gap",
                    writer.m_b,
                ),
            )
            continuation_top = param_pt(
                writer.params,
                f"lang_{lang}_idml_lcd_continuation_page_top",
                param_pt(
                    writer.params,
                    "idml_lcd_continuation_page_top",
                    writer.m_t,
                ),
            )
            target_height = (
                visual_bottom
                - continuation_top
                - param_pt(
                    writer.params,
                    "idml_lcd_inline_anchor_offset",
                    0.375,
                )
            )
            terminal_fill = max(0.0, target_height - sum(row_heights))
        if row_heights is not None and terminal_fill:
            row_heights = list(row_heights)
            row_heights[-1] += terminal_fill
        if content_sized_rows:
            row_heights = dynamic_row_heights
        for local_ri, row in enumerate(segment):
            label_size, label_leading, body_size, body_leading = (
                _lcd.typography_tokens(
                    writer, lang, row, segment_index=segment_index)
            )
            row_icon_pt = icon_pt
            governed_icon_size = str(row.get("icon_size_pt") or "").strip()
            if governed_icon_size:
                row_icon_pt = min(row_icon_pt, max(4.0, float(governed_icon_size)))
            governed_height = (
                f"{row_heights[local_ri]:g}"
                if row_heights is not None
                else str(row.get("row_height_pt") or "").strip()
            )
            if governed_height:
                # Fit the inline icon inside the compact row minimum,
                # including the 0.6 pt baseline shift applied below.  The
                # table row remains AutoGrow-enabled for real font metrics.
                row_icon_pt = min(
                    icon_pt,
                    max(
                        4.0,
                        float(governed_height)
                        - 2 * vertical_pad
                        - governed_icon_line_reserve,
                    ),
                )
            fig = (ROOT / row["figure"]) if row["figure"] else None
            image = (
                writer._image_cell_content(
                    f"{tid}img{global_ri}", fig, row_icon_pt, row_icon_pt)
                if fig and fig.exists() else ""
            )
            image_paragraph = _components.figure_paragraph(
                image,
                tail="<Content></Content>",
                justification="CenterAlign",
            )
            image_paragraph = image_paragraph.replace(
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                'BaselineShift="0.6"',
                1,
            )
            if table_variant == "label_description":
                cell_defs = (
                    (_lcd.typed_paragraph(
                        writer, "HB Spec Label", row["name"],
                        point_size=label_size, leading=label_leading,
                        bold=True), 0),
                    (_lcd.typed_paragraph(
                        writer, "HB Spec Value", row["desc"],
                        point_size=body_size, leading=body_leading), 1),
                )
            else:
                cell_defs = (
                    (_lcd.typed_paragraph(
                        writer, "HB Spec Label", row["no"],
                        "type_lcd_no_font_size", "type_lcd_no_font_leading"), 0),
                    (image_paragraph, 1),
                    (_lcd.typed_paragraph(
                        writer, "HB Spec Label", row["name"],
                        point_size=label_size, leading=label_leading,
                        bold=True), 2),
                    (_lcd.typed_paragraph(
                        writer, "HB Spec Value", row["desc"],
                        point_size=body_size, leading=body_leading), 3),
                )
            for content, ci in cell_defs:
                if (
                    table_variant == "number_icon_label_description"
                    and ci == 0
                    and row.get("suppress_number") == "true"
                ):
                    continue
                row_span = (
                    int(row.get("number_row_span", "1"))
                    if table_variant == "number_icon_label_description" and ci == 0
                    else 1
                )
                terminal_inset = (
                    terminal_fill / 2.0
                    if row_heights is None
                    and local_ri == len(segment) - 1
                    else 0.0
                )
                cell_xml = writer._cell(
                    f"{tid}c{global_ri}_{ci}", f"{ci}:{local_ri}", content,
                    top=vertical_pad + terminal_inset,
                    bottom=vertical_pad + terminal_inset,
                    left=(
                        text_indent
                        if (
                            table_variant == "label_description"
                            or ci >= 2
                        )
                        else pad
                    ),
                    right=pad,
                    valign="CenterAlign")
                if row_span > 1:
                    cell_xml = cell_xml.replace(
                        'RowSpan="1"', f'RowSpan="{row_span}"', 1)
                cells.append(cell_xml)
            global_ri += 1
        table = writer._component_table(
            tid,
            list(cols),
            cells,
            n_rows=len(segment),
            role="data",
            row_heights=row_heights,
            # Contract-measured first-page heights are exact physical rows,
            # not lower bounds.  Letting InDesign AutoGrow those rows makes
            # tiny native-metric differences accumulate until the indivisible
            # terminal row is pushed out of the fixed shell.  Continuation
            # rows remain content-aware minima and may still grow before the
            # finalizer fits their shell.
            auto_grow_rows=row_heights is not None and segment_index > 0,
        )
        shaded_columns = 1 if table_variant == "label_description" else 3
        for column in range(shaded_columns):
            table = _tb.fill_column_xml(table, column, "Color/HB Bg K05")
        if segment_index == 0:
            panel_height = param_pt(
                writer.params,
                f"lang_{lang}_idml_lcd_first_panel_height",
                param_pt(
                    writer.params,
                    "idml_lcd_first_panel_height",
                    param_pt(writer.params, "comp_lcd_first_panel_height", 286.0),
                ),
            )
        else:
            panel_height = param_pt(
                writer.params,
                "idml_lcd_continuation_panel_height",
                param_pt(
                    writer.params, "comp_lcd_continuation_panel_height", 465.0),
            )
        segment_limit = first_limit if segment_index == 0 else continuation_limit
        if row_heights is None and len(segment) < segment_limit:
            panel_height = min(
                panel_height,
                max(
                    param_pt(writer.params, "comp_lcd_partial_panel_min_height", 30.0),
                    len(segment)
                    * param_pt(writer.params, "comp_lcd_partial_row_height", 27.0)
                    + param_pt(writer.params, "comp_lcd_partial_panel_extra", 4.0),
                ),
            )
        # A complete governed table owns the full visible shell height: short
        # rows keep their compact fixed budget and the final row closes directly
        # against the rounded bottom border. The native end-of-story marker is
        # isolated in a separate transparent threaded carrier, never appended
        # to the visible shell or its table frame.
        if row_heights is not None:
            panel_height = sum(row_heights)
        panel = rounded_table_panel(
            writer._add_story_parts,
            writer.params,
            sid=f"st_anchor_lcd_table_{lang}_{segment_index}",
            title=f"{title} table segment {segment_index + 1}",
            table_xml=table,
            width=body_w,
            height=panel_height,
            n_cols=len(cols),
            terminal=segment_index == len(prepared_segments) - 1,
            fill="Color/Paper",
            stroke="Color/HB Brand Dark",
            start_next_page=segment_index > 0,
            terminal_carrier_height=native_carrier_allowance,
        )
        if segment_index == 0:
            left_indent = param_pt(
                writer.params,
                f"lang_{lang}_idml_lcd_first_left_indent",
                param_pt(writer.params, "idml_lcd_first_left_indent", 0.0),
            )
        else:
            left_indent = param_pt(
                writer.params,
                f"lang_{lang}_idml_lcd_continuation_left_indent",
                param_pt(
                    writer.params, "idml_lcd_continuation_left_indent", 0.0,
                ),
            )
        if left_indent:
            panel = panel.replace(
                "<ParagraphStyleRange ",
                f'<ParagraphStyleRange LeftIndent="{left_indent:g}" ',
                1,
            )
        table_panels.append(panel)
    parts = [
        _po.h1_pill_paragraph(
            writer, title, writer.page_w - writer.m_l - writer.m_r),
        _po.lcd_hero_paragraph(
            writer,
            lang,
            hero_path=hero_path,
            max_height=(
                param_pt(writer.params, "idml_compact_lcd_hero_max_height", 55.0)
                if compact else None
            ),
            horizontal_scale_override=hero_horizontal_scale,
        ),
        *table_panels,
    ]
    return writer._add_story_parts(sid, title, parts)


def add_symbols_story(
    writer,
    signals: list[object],
    icons: list[dict],
    data_root: Path,
    lang: str = "en",
    *,
    title: str,
    signal_headers: tuple[str, str],
    icon_headers: tuple[str, str],
) -> str:
    normalized_lang = lang.strip().casefold().replace("_", "-").split("-", 1)[0]
    id_suffix = "" if normalized_lang == "en" else f"_{normalized_lang}"
    sid = f"st_symbols{id_suffix}"
    title = source_text(title, owner="Symbols page title")
    signal_headers = (
        source_text(signal_headers[0], owner="Symbols signal column 1 header"),
        source_text(signal_headers[1], owner="Symbols signal column 2 header"),
    )
    icon_headers = (
        source_text(icon_headers[0], owner="Symbols icon column 1 header"),
        source_text(icon_headers[1], owner="Symbols icon column 2 header"),
    )
    parts = [_po.h1_pill_paragraph(
        writer, title, writer.page_w - writer.m_l - writer.m_r)]
    if signals:
        signal_cells = [
            [str(row.get("label") or ""), str(row.get("text") or "")]
            if isinstance(row, dict) else list(row)
            for row in signals
        ]
        table = writer._table(
            f"tbl_sym_sig{id_suffix}",
            [list(signal_headers), *signal_cells],
            label_style="HB Notice Label",
            role="data",
        )
        parts.append(writer._wrap_table_paragraph(
            table, False, span_columns=False))
    if icons:
        body_w = writer.page_w - writer.m_l - writer.m_r
        cols = (body_w * 0.18, body_w * 0.82)
        tid = f"tbl_sym_ico{id_suffix}"
        cells = [
            writer._cell(
                f"{tid}c0_0",
                "0:0",
                writer._psr("HB Symbol Header", icon_headers[0], terminal=True),
                fill="Color/HB Bg K05",
                top=2,
                bottom=2,
                left=3,
                right=3,
            ),
            writer._cell(
                f"{tid}c0_1",
                "1:0",
                writer._psr("HB Symbol Header", icon_headers[1], terminal=True),
                top=2,
                bottom=2,
                left=3,
                right=3,
            ),
        ]
        icon_pt = 20.0
        for ri, row in enumerate(icons, start=1):
            fig = (ROOT / row["figure"]) if row["figure"] else None
            image = (
                writer._image_cell_content(f"{tid}img{ri}", fig, icon_pt, icon_pt)
                if fig and fig.exists() else ""
            )
            image_cell = _components.figure_paragraph(
                image,
                tail="<Content></Content>",
                justification="CenterAlign",
            )
            for ci, content in (
                (0, image_cell),
                (1, writer._psr("HB Spec Value", row["text"], terminal=True)),
            ):
                cells.append(writer._cell(
                    f"{tid}c{ri}_{ci}", f"{ci}:{ri}", content,
                    top=2, bottom=2, left=3, right=3))
        table = writer._component_table(
            tid, list(cols), cells, n_rows=len(icons) + 1, role="data")
        parts.append(writer._wrap_table_paragraph(
            table, True, span_columns=False))
    return writer._add_story_parts(sid, title, parts)


def add_trouble_story(
    writer,
    rows: list[tuple[str, str]],
    *,
    title: str,
    lang: str = "en",
    intro: str = "",
    header: tuple[str, str] | None = None,
) -> str:
    """Build the Troubleshooting story.

    ``intro`` and ``header`` default to empty so the compositions that do not
    pass them render exactly what they rendered before.
    """
    sid = "st_trouble" if lang == "en" else f"st_trouble_{lang}"
    title = source_text(title, owner="Troubleshooting page title")
    parts = [_po.h1_pill_paragraph(
        writer, title, writer.page_w - writer.m_l - writer.m_r)]
    if intro:
        parts.append(writer._psr("HB Body", source_text(
            intro, owner="Troubleshooting intro")))
    table_id = "tbl_trouble" if lang == "en" else f"tbl_trouble_{lang}"
    if header is not None:
        # The width logic already treats row 0 as the header and sizes it with
        # `style.header_size`, so prepending it is what that code expects.
        rows = [tuple(header), *rows]
    table = writer._table(table_id, rows, role="data")
    body_style_ref = paragraph_style_ref("HB Body")
    parts.append(
        f'  <ParagraphStyleRange AppliedParagraphStyle="{body_style_ref}">\n'
        '    <CharacterStyleRange '
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
        + table
        + '    <Content></Content></CharacterStyleRange>\n'
        '  </ParagraphStyleRange>\n'
    )
    # Same sink as every other component story: it applies the duplicate-style
    # collapse and binds generic CJK runs to the document language's portable
    # face. Building the wrapper here instead left the two data-heaviest JP
    # pages on the Arial Unicode MS system font while sixteen sibling stories
    # carried the bundled JP face.
    return add_story_parts(writer, sid, title, parts)


def add_spec_story(
    writer,
    sections: list[dict],
    annotations: list[str] | None = None,
    lang: str = "en",
    *,
    title: str,
    layout_variant: str = "reference",
) -> str:
    sid = "st_spec" if lang == "en" else f"st_spec_{lang}"
    title = source_text(title, owner="Specifications page title")
    parts = [_po.h1_pill_paragraph(
        writer, title, writer.page_w - writer.m_l - writer.m_r)]
    # The approved US master repeats one specification shell for EN/FR/ES.
    # Localized copy changes line breaking inside the cells, not the native
    # rounded-table geometry.  Keeping this language-neutral also prevents a
    # translated page from silently falling back to the legacy square table.
    if layout_variant not in {"reference", "compact"}:
        raise ValueError(
            f"unsupported specification layout variant: {layout_variant}"
        )
    compact = layout_variant == "compact"
    if compact:
        reference_table_heights = tuple(
            spec_table_height(
                list(section["rows"]),
                writer.params,
                density="compact",
                language=lang,
            )
            for section in sections
        )
        default_section_before = (5.8, 8.2, 8.2)
        default_table_before = (2.5, 2.5, 2.5)
    else:
        reference_table_heights = (98.41, 49.06, 94.89, 27.11)
        default_section_before = (7.89, 9.56, 10.54, 14.41)
        default_table_before = (3.79, 2.47, 4.75, 3.30)
    native_symbol_index = 0

    def spec_paragraph(style: str, text: str, **kwargs) -> str:
        nonlocal native_symbol_index
        if not writer.native_structure_markers:
            return writer._psr(style, text, **kwargs)
        size_key = (
            "type_spec_label_font_size"
            if style == "HB Spec Label"
            else "type_spec_value_font_size"
        )
        point_size = param_pt(
            writer.params,
            f"lang_{lang}_{size_key}",
            param_pt(writer.params, size_key, 6.0),
        )
        portable_text, replacements = portable_symbol_text(
            text,
            marker_id=f"{sid}_spec_symbol_{native_symbol_index}",
            point_size=point_size,
        )
        native_symbol_index += 1
        return writer._psr(
            style,
            portable_text,
            inline_replacements=replacements,
            **kwargs,
        )

    for si, section in enumerate(sections):
        title_baseline_shift = param_pt(
            writer.params,
            f"lang_{lang}_idml_spec_section_text_baseline_shift",
            param_pt(
                writer.params,
                "idml_spec_section_text_baseline_shift",
                0.0,
            ),
        )
        bullet_baseline_shift = title_baseline_shift + param_pt(
            writer.params,
            "idml_spec_section_bullet_baseline_offset",
            -1.56,
        )
        if writer.native_structure_markers:
            section_title = writer._psr(
                "HB Spec Section",
                marked_text(section["title"]),
                inline_replacements=marker_replacements(
                    writer,
                    marker_id=f"{sid}_section_marker_{si}",
                ),
            )
        else:
            section_title = writer._psr(
                "HB Spec Section", "\u25cf " + section["title"])
            section_title = section_title.replace(
                'FontStyle="Regular"',
                'FontStyle="Regular" PointSize="13.2" '
                'HorizontalScale="100" '
                f'BaselineShift="{bullet_baseline_shift:g}"',
                1,
            )
        section_default = (
            default_section_before[si]
            if si < len(default_section_before) else 10.07
        )
        section_before = param_pt(
            writer.params,
            (
                f"lang_{lang}_idml_compact_spec_section_{si + 1}_space_before"
                if compact
                else f"lang_{lang}_idml_spec_section_{si + 1}_space_before"
            ),
            param_pt(
                writer.params,
                (
                    f"idml_compact_spec_section_{si + 1}_space_before"
                    if compact
                    else f"idml_spec_section_{si + 1}_space_before"
                ),
                section_default,
            ),
        )
        section_left_indent = param_pt(
            writer.params,
            f"lang_{lang}_idml_spec_section_left_indent",
            param_pt(
                writer.params,
                "idml_spec_section_left_indent",
                0.0,
            ),
        )
        section_title = section_title.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange SpaceBefore="{section_before:g}" '
            f'LeftIndent="{section_left_indent:g}" ',
            1,
        )
        if title_baseline_shift:
            section_title = section_title.replace(
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"'
                '><Content> ',
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                f'BaselineShift="{title_baseline_shift:g}"><Content> ',
                1,
            )
        parts.append(section_title)
        table = _tb.fill_column_xml(
            _tb.suppress_inner_vertical_edges_xml(
                spec_table(
                    f"tbl_spec_{lang}{si}", section["rows"], role="spec",
                    params=writer.params,
                    page_w=writer.page_w,
                    m_l=writer.m_l,
                    m_r=writer.m_r,
                    visual_parity=True,
                    density=layout_variant,
                    section_index=si,
                    language=lang,
                    paragraph_xml=spec_paragraph,
                ),
                2,
            ),
            0,
            "Color/HB Bg K05",
        )
        last = si == len(sections) - 1 and not annotations
        if si < len(reference_table_heights):
            table = _tb.suppress_outer_edges_xml(table, 2)
            inner = writer._wrap_table_paragraph(
                table, True, span_columns=False)
            panel = _po.anchored_panel_group_paragraph(
                writer._add_story_parts,
                f"st_anchor_spec_{lang}{si}",
                f"{section['title']} specification table",
                [inner],
                writer.page_w - writer.m_l - writer.m_r + 0.35,
                reference_table_heights[si],
                terminal=last,
                fill="Color/Paper",
                stroke="Color/HB Brand Dark",
                stroke_weight=0.75,
                radius=6.8,
            )
            table_default = (
                default_table_before[si]
                if si < len(default_table_before)
                else default_table_before[-1]
            )
            table_before = param_pt(
                writer.params,
                (
                    f"lang_{lang}_idml_compact_spec_table_{si + 1}_space_before"
                    if compact
                    else f"lang_{lang}_idml_spec_table_{si + 1}_space_before"
                ),
                param_pt(
                    writer.params,
                    (
                        f"idml_compact_spec_table_{si + 1}_space_before"
                        if compact
                        else f"idml_spec_table_{si + 1}_space_before"
                    ),
                    table_default,
                ),
            )
            panel = panel.replace(
                "<ParagraphStyleRange ",
                f'<ParagraphStyleRange SpaceBefore="{table_before:g}" ',
                1,
            )
            parts.append(panel)
            continue
        body_style_ref = paragraph_style_ref("HB Body")
        parts.append(
            f'  <ParagraphStyleRange AppliedParagraphStyle="{body_style_ref}">\n'
            '    <CharacterStyleRange '
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
            + table
            + ('    <Content></Content></CharacterStyleRange>\n' if last else
               '    <Br/></CharacterStyleRange>\n')
            + '  </ParagraphStyleRange>\n'
        )
    for ai, note in enumerate(annotations or []):
        note_xml = writer._psr(
            "HB Spec Note", note,
            terminal=(ai == len(annotations) - 1),
            # A leading circled numeral identifies the footnote line; it is
            # not an inline reference. Keep it at the same size and baseline
            # as the following note text. Inline references inside spec-table
            # cells remain superscripted by spec_tables.py.
            superscript_markers=False,
        )
        if lang == "en":
            note_xml = note_xml.replace(
                "<ParagraphStyleRange ",
                '<ParagraphStyleRange LeftIndent="-2.15" '
                'FirstLineIndent="-2.15" '
                f'SpaceBefore="{10.34 if ai == 0 else 4.57:g}" ',
                1,
            )
        elif lang in {"fr", "es"}:
            note_before = {
                "fr": (8.09, 5.07),
                "es": (5.65, 10.17),
            }[lang][min(ai, 1)]
            note_xml = note_xml.replace(
                "<ParagraphStyleRange ",
                f'<ParagraphStyleRange SpaceBefore="{note_before:g}" ',
                1,
            )
        parts.append(note_xml)
    return add_story_parts(writer, sid, title, parts)
