"""Editable mixed image/text tables from the shared prepared-RST projection."""
from __future__ import annotations

from tools.rst_inline import IMAGE

from ..inline_images import prepare_inline_images
from ..line_metrics import estimated_line_count
from ..primitives import cell, component_table, psr, wrap_table_paragraph


def has_inline_images(rows: list[list]) -> bool:
    return any(IMAGE.search(str(value)) for row in rows for value in row)


def render_image_table(rows, ctx, *, tid, terminal, span_columns=True):
    count = max(map(len, rows))
    image_columns = {
        col for row in rows for col, value in enumerate(row)
        if IMAGE.fullmatch(str(value).strip())
    }
    # Reserve a small icon column and give the remaining measure to copy.
    icon_width = min(30.0, ctx.text_measure / count)
    text_count = count - len(image_columns)
    text_width = ((ctx.text_measure - icon_width * len(image_columns)) / text_count
                  if text_count else icon_width)
    widths = [icon_width if i in image_columns else text_width for i in range(count)]
    cells, heights = [], []
    for ri, row in enumerate(rows):
        height = 24.0
        for ci, width in enumerate(widths):
            text = str(row[ci]) if ci < len(row) else ""
            plain = IMAGE.sub("", text)
            text, replacements = prepare_inline_images(text, ctx, tid=f"{tid}_{ri}_{ci}", size=20.0)
            content = psr("HB Spec Value", text, terminal=True,
                          inline_replacements=replacements)
            if ci in image_columns:
                content = content.replace("<ParagraphStyleRange ",
                                          '<ParagraphStyleRange Justification="CenterAlign" ', 1)
            cells.append(cell(f"{tid}c{ri}_{ci}", f"{ci}:{ri}", content,
                              top=2.0, bottom=2.0, left=3.0, right=3.0,
                              valign="CenterAlign"))
            height = max(height, 4.0 + estimated_line_count(
                plain, max(1.0, width - 6.0), point_size=6.0,
            ) * 7.2)
        heights.append(height)
    table = component_table(tid, widths, cells, len(rows), role="data")
    return wrap_table_paragraph(table, terminal, span_columns), sum(heights)
