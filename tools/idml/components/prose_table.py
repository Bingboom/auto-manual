"""Prose-page data tables — the extractor's ``("table", json rows)`` block
(componentization P2). Two-column tables render in the spec-table shape;
wider ones (e.g. KEY COMBINATIONS) get a narrow first column and an even
split for the rest.
"""
from __future__ import annotations

import re

from ..params import param_pt
from ..primitives import cell, component_table, psr, spec_table, wrap_table_paragraph
from ..table_borders import suppress_outer_edges_xml
from .base import RenderContext
from .rounded_table import rounded_table_panel, table_text_indent


def body_data_table_kind(raw_rows: list[list]) -> str | None:
    """Classify the two source-driven body tables that share group layout."""
    if not raw_rows:
        return None
    n_cols = max(len(row) for row in raw_rows)
    first_cell = str(raw_rows[0][0]).replace("**", "").strip()
    if n_cols == 2 and first_cell == "Auto Resume Conditions":
        return "auto_resume"
    if (
        n_cols == 3
        and first_cell == "Buttons"
        and [str(cell).strip() for cell in raw_rows[0][1:3]]
        == ["Operation", "Function"]
    ):
        return "key_combinations"
    return None


def _overview_table(raw_rows: list[list], ctx: RenderContext, tid: str) -> str:
    n_cols = max(len(row) for row in raw_rows)
    body_w = ctx.text_measure
    cols = [body_w / n_cols] * n_cols
    rule = param_pt(ctx.params, "comp_table_inner_rule", 0.2)
    cells: list[str] = []
    first_cell = str(raw_rows[0][0]).replace("**", "").strip()
    for ri, row in enumerate(raw_rows):
        for ci in range(n_cols):
            text = str(row[ci]) if ci < len(row) else ""
            if text.startswith("**") and "** " in text[2:]:
                text = text.replace("** ", "**\n", 1)
            content = psr("HB Data Body", text, terminal=True)
            if first_cell == "Total Output":
                content = content.replace(
                    "<ParagraphStyleRange ",
                    '<ParagraphStyleRange LeftIndent="-0.96" ',
                    1,
                )
            bottom = 1.1
            if first_cell == "POWER Button" and ri == len(raw_rows) - 1:
                bottom = 6.0
            elif first_cell == "Total Output":
                bottom = 3.35
            top = 1.1
            valign = "CenterAlign"
            if first_cell == "Handle":
                top = 2.68 if ri == 0 else 1.54
                valign = "TopAlign"
            left_inset = 1.44 if first_cell == "Total Output" else 2.4
            cells.append(cell(
                f"{tid}c{ri}_{ci}", f"{ci}:{ri}",
                content,
                fill="Color/HB Bg K05" if ri % 2 == 0 else None,
                top=top, bottom=bottom, left=left_inset, right=2.4,
                edge_weight=rule, valign=valign,
            ))
    return component_table(
        tid, cols, cells, n_rows=len(raw_rows), role="data")


def _troubleshooting_table(raw_rows: list[list], ctx: RenderContext, tid: str) -> str:
    """Render the shared LaTeX troubleshooting-table contract in IDML.

    This table is deliberately not a generic two-column spec table: the
    narrow code column, bold code face, header treatment, row minima and
    inner hairlines all have their own shared layout tokens.
    """
    body_w = ctx.text_measure - (1.13 if ctx.add_story is not None else 0.0)
    left_ratio = float(ctx.params.get("comp_trouble_left_ratio", ("0.11", ""))[0])
    # TeX's m-column width is followed by the inter-column tab padding;
    # the visible divider therefore sits 2.64 pt to the right of the bare
    # ratio.  Carry that optical width into the IDML column itself.
    left_w = body_w * left_ratio + 11.36
    cols = [left_w, body_w - left_w]
    inner_rule = 0.25

    cells: list[str] = []
    for ri, row in enumerate(raw_rows):
        left = str(row[0]) if row else ""
        right = str(row[1]) if len(row) > 1 else ""
        is_steps = right.lstrip().startswith("|")
        if ri == 0:
            styles = ("HB Data Header", "HB Data Header")
            fills = ("Color/HB Bg K05", "Color/HB Bg K05")
        else:
            styles = ("HB Data Code", "HB Data Body")
            fills = ("Color/HB Bg K05", None)
        for ci, (text, style, fill) in enumerate(zip((left, right), styles, fills)):
            content = psr(style, text, terminal=True)
            if ri == 0:
                baseline = 1.31 if ci == 0 else 0.57
                content = content.replace(
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                    f'BaselineShift="{baseline:g}"',
                    1,
                )
            elif ci == 0:
                code_baseline = -0.45 if ri == 9 else 0.3 if ri == 6 else 1.3
                content = content.replace(
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                    f'BaselineShift="{code_baseline:g}"',
                    1,
                )
                content = content.replace(
                    "<ParagraphStyleRange ",
                    '<ParagraphStyleRange RightIndent="8.51" ',
                    1,
                )
            if ri == 0:
                top = 6.4 if ci == 0 else 3.0
                bottom = 4.0 if ci == 0 else 2.0
                valign = "CenterAlign"
            elif ci == 0 and is_steps:
                step_count = right.count("|")
                top = 12.7 if step_count >= 5 else 7.6
                bottom = 2.95
                valign = "TopAlign"
            else:
                top = 2.53 if ci == 1 and is_steps else 2.95
                bottom = 3.16 if ci == 1 and is_steps else 2.95
                if ri in range(1, 7):
                    top = bottom = 1.5
                if ri == 9:
                    top = bottom = 2.35
                valign = "TopAlign" if ri in {6, 9, 10, 11} else "CenterAlign"
            cells.append(cell(
                f"{tid}c{ri}_{ci}", f"{ci}:{ri}",
                content, fill=fill,
                top=top, bottom=bottom,
                left=(2.88 if ri == 0 and ci == 0 else 1.5 if ri > 0 and ci == 0 else 3.0),
                right=3.0,
                edge_weight=inner_rule, edge_color="Color/HB Brand Dark",
                valign=valign,
            ))

    # InDesign's exported cell box is about 1.2 pt shorter than the IDML
    # SingleRowHeight value at this page scale.  The additive optical
    # correction keeps the PDF minima equal to the shared LaTeX tokens.
    header_h = param_pt(ctx.params, "comp_data_table_header_height", 14.74) + 3.43
    row_h = param_pt(ctx.params, "comp_data_table_row_height", 11.91) + 2.79
    # The production master gives the long F6/F7 actions and the final
    # short-code rows explicit minima.  Content-driven auto height alone is
    # noticeably tighter in InDesign and leaves the English table ~28 pt
    # short, even though every row remains readable.  SingleRowHeight is
    # descriptive after import; MinimumHeight + AutoGrow is the operative
    # InDesign row contract.
    master_row_heights = {
        1: 11.80,  # F0
        2: 12.37,  # F1
        3: 11.79,  # F2
        4: 11.99,  # F3
        5: 11.87,  # F4
        6: 23.89,  # F5
        7: 57.61,  # F6
        8: 31.96,  # F7
        9: 17.41,  # F8
        10: 18.43,  # F9
        11: 11.97,  # FE
    }
    rows = "\n".join(
        f'    <Row Self="{tid}r{ri}" Name="{ri}" '
        f'SingleRowHeight="{header_h if ri == 0 else row_h:g}" '
        f'MinimumHeight="{14.77 if ri == 0 else master_row_heights.get(ri, 11.15):g}" '
        'AutoGrow="true"/>'
        for ri in range(len(raw_rows))
    )
    columns = "\n".join(
        f'    <Column Self="{tid}col{ci}" Name="{ci}" SingleColumnWidth="{width:g}"/>'
        for ci, width in enumerate(cols)
    )
    return (
        f'  <Table Self="{tid}" AppliedTableStyle="TableStyle/$ID/[Basic Table]" '
        f'BodyRowCount="{len(raw_rows)}" ColumnCount="2" HeaderRowCount="0" FooterRowCount="0">\n'
        f'{rows}\n{columns}\n' + "\n".join(cells) + "\n  </Table>\n"
    )


def _body_data_table(raw_rows: list[list], ctx: RenderContext, tid: str,
                     kind: str) -> tuple[str, float]:
    """Mirror the shared LaTeX Auto Resume / Key Combination table tokens."""
    # The table shell owns the full body measure.  The requested one-character
    # inset belongs to the cells (``comp_table_text_indent``), never to the
    # heading/description/table group as a whole.
    body_w = ctx.text_measure - 1.5
    # LaTeX's m-columns add tabcolsep around the declared percentage.
    # These optical additions place the visible dividers at the same x
    # coordinates instead of treating the bare percentages as full cells.
    first_optical = 2.76
    if kind == "auto_resume":
        left = float(ctx.params.get("comp_auto_resume_left_ratio", ("0.5", ""))[0])
        first_w = body_w * left + first_optical
        cols = [first_w, body_w - first_w]
    else:
        left = float(ctx.params.get("comp_key_table_left_ratio", ("0.41", ""))[0])
        middle = float(ctx.params.get("comp_key_table_middle_ratio", ("0.29", ""))[0])
        first_w = body_w * left + first_optical
        middle_w = body_w * middle + 5.15
        cols = [first_w, middle_w, body_w - first_w - middle_w]
    header_h = param_pt(ctx.params, "comp_data_table_header_height", 14.74)
    row_h = param_pt(
        ctx.params,
        "comp_key_table_row_height" if kind == "key_combinations"
        else "comp_data_table_row_height",
        32.88 if kind == "key_combinations" else 11.91,
    )
    pad = param_pt(ctx.params, "comp_data_table_tabcolsep", 2.4)
    text_indent = table_text_indent(ctx.params)
    rule = param_pt(ctx.params, "comp_table_inner_rule", 0.2)
    cells: list[str] = []
    n_cols = len(cols)
    for ri, row in enumerate(raw_rows):
        for ci in range(n_cols):
            text = str(row[ci]) if ci < len(row) else ""
            if kind == "auto_resume" and ci == 0 and ri > 0 and not text.strip():
                continue
            rowspan = (
                2 if kind == "auto_resume" and ci == 0
                and ri + 1 < len(raw_rows)
                and not str(raw_rows[ri + 1][0]).strip()
                else 1
            )
            fill = (
                "Color/HB Header K08" if ri == 0
                else "Color/HB Bg K05" if ci == 0
                else None
            )
            cell_xml = cell(
                f"{tid}c{ri}_{ci}", f"{ci}:{ri}",
                psr("HB Data Header" if ri == 0 else "HB Data Body",
                    text, terminal=True),
                fill=fill, top=0, bottom=0,
                left=text_indent, right=pad,
                edge_weight=rule, edge_color="Color/HB Brand Dark",
                valign="CenterAlign",
            )
            if rowspan > 1:
                cell_xml = cell_xml.replace('RowSpan="1"', f'RowSpan="{rowspan}"', 1)
            cells.append(cell_xml)
    table = component_table(tid, cols, cells, n_rows=len(raw_rows), role="data")
    table = suppress_outer_edges_xml(table, n_cols)
    for ri in range(len(raw_rows)):
        minimum = header_h if ri == 0 else row_h
        table = re.sub(
            rf'(<Row Self="{re.escape(tid)}r{ri}" Name="{ri}")/?>',
            rf'\1 SingleRowHeight="{minimum:g}" MinimumHeight="{minimum:g}" '
            'AutoGrow="true"/>',
            table,
            count=1,
        )
    return table, header_h + row_h * (len(raw_rows) - 1) + 3.0


def render_table_block(raw_rows: list[list], ctx: RenderContext, *, tid: str,
                       terminal: bool, span_columns: bool = True) -> tuple[str, float]:
    n_cols = max(len(r) for r in raw_rows)
    first_cell = str(raw_rows[0][0]).replace("**", "").strip() if raw_rows else ""
    is_overview = first_cell in {"POWER Button", "Total Output", "Handle"}
    is_troubleshooting = (
        n_cols == 2 and bool(raw_rows)
        and str(raw_rows[0][0]).strip().casefold() == "error code"
    )
    body_kind = body_data_table_kind(raw_rows)
    is_auto_resume = body_kind == "auto_resume"
    is_key_combinations = body_kind == "key_combinations"
    if is_overview:
        table = _overview_table(raw_rows, ctx, tid)
    elif is_troubleshooting:
        table = _troubleshooting_table(raw_rows, ctx, tid)
    elif is_auto_resume or is_key_combinations:
        table, framed_h = _body_data_table(
            raw_rows, ctx, tid,
            "auto_resume" if is_auto_resume else "key_combinations",
        )
    elif n_cols <= 2:
        rows2 = [(r[0], r[1] if len(r) > 1 else "") for r in raw_rows]
        table = spec_table(tid, [(str(a), str(b)) for a, b in rows2],
                           params=ctx.params, page_w=ctx.page_w,
                           m_l=ctx.m_l, m_r=ctx.m_r,
                           role="data")
    else:
        # N-column prose tables (e.g. KEY COMBINATIONS): first
        # column narrow-ish, rest evenly split
        body_w2 = ctx.page_w - ctx.m_l - ctx.m_r
        cols = [body_w2 * 0.3] + [body_w2 * 0.7 / (n_cols - 1)] * (n_cols - 1)
        cells = []
        for ri, r in enumerate(raw_rows):
            for ci in range(n_cols):
                txt = str(r[ci]) if ci < len(r) else ""
                style = "HB Spec Label" if ri == 0 else "HB Spec Value"
                cells.append(cell(
                    f"{tid}c{ri}_{ci}", f"{ci}:{ri}",
                    psr(style, txt, terminal=True)))
        table = component_table(tid, cols, cells, n_rows=len(raw_rows),
                                role="data")
    if (is_auto_resume or is_key_combinations) and ctx.add_story is not None:
        xml = rounded_table_panel(
            ctx.add_story,
            ctx.params,
            sid=f"st_anchor_data_{tid}",
            title="body data table",
            table_xml=table,
            width=ctx.text_measure,
            height=framed_h,
            n_cols=n_cols,
            terminal=terminal,
            fill="Color/Paper",
            stroke="Color/HB Brand Dark",
            corner_fills={
                "top_left": "Color/HB Header K08",
                "top_right": "Color/HB Header K08",
                "bottom_left": (
                    "Color/HB Bg K05" if is_auto_resume else "Color/Paper"
                ),
                "bottom_right": "Color/Paper",
            },
            space_before=param_pt(ctx.params, "comp_data_table_before", 3.4),
            space_after=param_pt(ctx.params, "comp_data_table_after", 3.4),
        )
    elif is_troubleshooting and ctx.add_story is not None:
        xml = rounded_table_panel(
            ctx.add_story,
            ctx.params,
            sid=f"st_anchor_trouble_{tid}",
            title="troubleshooting table",
            table_xml=table,
            width=ctx.text_measure - 0.75,
            height=240.00,
            n_cols=2,
            terminal=terminal,
            fill="Color/Paper",
            stroke="Color/HB Brand Dark",
            stroke_weight=0.57,
        )
    else:
        xml = wrap_table_paragraph(table, terminal, span_columns=span_columns)
    if is_overview:
        if first_cell == "Total Output":
            xml = xml.replace(
                "<ParagraphStyleRange ",
                '<ParagraphStyleRange SpaceAfter="2.6" ',
                1,
            )
        else:
            xml = xml.replace(
                "<ParagraphStyleRange ",
                f'<ParagraphStyleRange SpaceBefore="1.14" '
                f'SpaceAfter="{12.97 if first_cell == "POWER Button" else 0:g}" ',
                1,
            )
    if is_troubleshooting:
        # LaTeX's HBDataTableFrame has a dedicated before gap.  Keep it on
        # the host paragraph so page-flow and table geometry remain separate.
        xml = xml.replace(
            "<ParagraphStyleRange ",
            '<ParagraphStyleRange SpaceBefore="9.74" ',
            1,
        )
    if is_auto_resume or is_key_combinations:
        return xml, framed_h + 2 * param_pt(ctx.params, "comp_data_table_before", 3.4)
    return xml, 11.0 * (len(raw_rows) + 1)
