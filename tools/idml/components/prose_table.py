"""Prose-page data tables — the extractor's ``("table", json rows)`` block
(componentization P2). Two-column tables render in the spec-table shape;
wider ones (e.g. KEY COMBINATIONS) get a narrow first column and an even
split for the rest.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re

from ..character_metrics import with_character_metrics
from ..params import component_param_pt, param_pt
from ..primitives import (
    cell,
    component_table,
    psr,
    spec_table,
    wrap_table_paragraph,
)
from ..table_borders import suppress_outer_edges_xml
from ..text_clean import strip_rst_inline
from .base import RenderContext
from .key_combinations import (
    is_key_combinations_rows,
    render_key_combinations,
)
from .rounded_table import rounded_table_panel, table_text_indent


@dataclass(frozen=True)
class _AutoResumeGeometry:
    """Measured geometry for one localized production-master table."""

    row_heights: tuple[float, ...]
    column_widths: tuple[float, float]
    cell_insets: tuple[tuple[float, float], tuple[float, float]]
    first_line_indent: float
    space_before: float


@dataclass(frozen=True)
class _TroubleshootingLocaleCalibration:
    """Native row-height baseline for the approved localized source copy."""

    native_row_heights: tuple[float, ...]
    left_line_baseline: tuple[int, ...]
    right_line_baseline: tuple[int, ...]


@dataclass(frozen=True)
class TroubleshootingTableStyle:
    """Source-side geometry contract for the editable troubleshooting table.

    InDesign auto-grows table rows after importing the IDML, while the
    enclosing rounded group deliberately keeps ``AutoSizingType=Off`` so its
    background, masks and outline remain one movable object.  The group must
    therefore budget the same localized row growth before it is emitted.
    """

    left_ratio: float
    body_size: float
    body_leading: float
    header_size: float
    header_leading: float
    code_size: float
    code_leading: float
    header_single_height: float
    body_single_height: float
    row_minima: tuple[float, ...]
    steps_pad_tb: float
    outer_radius: float
    panel_min_height: float = 240.0
    import_safety: float = 4.0
    glyph_width_ratio: float = 0.50
    left_optical_width: float = 4.0
    inner_rule: float = 0.25
    outer_rule: float = 0.57
    space_before: float = 9.74
    table_space_before_by_language: tuple[float, float, float] = (
        8.74, 6.70, 7.75,
    )

    @classmethod
    def from_context(cls, ctx: RenderContext) -> TroubleshootingTableStyle:
        """Resolve shared type/row tokens once for rendering and estimation."""
        def token(key: str, default: float) -> float:
            value = component_param_pt(
                ctx.params,
                key,
                default,
                strict=ctx.strict_component_assets,
                owner="TroubleshootingTableStyle",
            )
            if not math.isfinite(value) or value <= 0:
                raise ValueError(
                    "TroubleshootingTableStyle layout token must be finite and "
                    f"positive: {key}"
                )
            return value

        header_h = token("comp_data_table_header_height", 14.74)
        row_h = token("comp_data_table_row_height", 11.91)
        left_ratio = token("comp_trouble_left_ratio", 0.11)
        if left_ratio >= 1:
            raise ValueError(
                "TroubleshootingTableStyle comp_trouble_left_ratio must be "
                "less than 1"
            )
        style = cls(
            left_ratio=left_ratio,
            body_size=token("type_trouble_body_font_size", 5.5),
            body_leading=token("type_trouble_body_font_leading", 6.0),
            header_size=token("type_data_table_header_font_size", 6.6),
            header_leading=token("type_data_table_header_font_leading", 7.0),
            code_size=token("type_trouble_code_font_size", 8.0),
            code_leading=token("type_trouble_code_font_leading", 8.0),
            # InDesign's exported cell box is about 1.2 pt shorter than the
            # IDML SingleRowHeight at this scale. These corrections preserve
            # the established production-master row contract.
            header_single_height=header_h + 3.43,
            body_single_height=row_h + 2.79,
            row_minima=_TROUBLESHOOTING_BASE_ROW_MINIMA,
            steps_pad_tb=token("comp_trouble_steps_pad_tb", 2.83465),
            outer_radius=token("comp_table_outer_arc", 6.8),
            left_optical_width=token("idml_trouble_left_optical_width", 4.0),
            table_space_before_by_language=(
                token("lang_en_idml_trouble_table_space_before", 8.74),
                token("lang_fr_idml_trouble_table_space_before", 6.70),
                token("lang_es_idml_trouble_table_space_before", 7.75),
            ),
        )
        return style

    def table_space_before(self, language: str) -> float:
        index = {"en": 0, "fr": 1, "es": 2}.get(language, 0)
        return self.table_space_before_by_language[index]

    def minimum_for_row(self, row_index: int) -> float:
        if row_index < len(self.row_minima):
            return self.row_minima[row_index]
        return 11.15


_TROUBLESHOOTING_HEADER_LANGUAGES = {
    "error code": "en",
    "code d'erreur": "fr",
    "code d’erreur": "fr",
    "código de fallo": "es",
    "codigo de fallo": "es",
    "código de error": "es",
    "codigo de error": "es",
}
_TROUBLESHOOTING_BASE_ROW_MINIMA = (
    14.77, 11.80, 12.37, 11.79, 11.99, 11.87,
    23.89, 57.61, 31.96, 17.41, 18.43, 11.97,
)
_TROUBLESHOOTING_LOCALE_CALIBRATIONS = {
    "en": _TroubleshootingLocaleCalibration(
        native_row_heights=(
            14.77, 11.97, 11.97, 11.97, 11.43, 12.51,
            11.97, 62.03, 38.67, 15.15, 19.74, 15.61,
        ),
        left_line_baseline=(2,) + (1,) * 11,
        right_line_baseline=(1, 1, 1, 1, 1, 1, 1, 8, 4, 1, 2, 1),
    ),
    "fr": _TroubleshootingLocaleCalibration(
        native_row_heights=(
            14.53, 11.97, 11.96, 11.97, 11.97, 11.97,
            11.97, 72.30, 39.34, 17.22, 16.67, 24.22,
        ),
        left_line_baseline=(2,) + (1,) * 11,
        right_line_baseline=(1, 1, 1, 1, 1, 2, 2, 9, 4, 1, 2, 1),
    ),
    "es": _TroubleshootingLocaleCalibration(
        native_row_heights=(
            14.68, 11.97, 11.97, 11.97, 11.97, 11.97,
            11.96, 71.83, 42.36, 16.89, 22.11, 16.52,
        ),
        left_line_baseline=(2,) + (1,) * 11,
        right_line_baseline=(1, 1, 1, 1, 1, 1, 2, 9, 5, 1, 2, 1),
    ),
}

_AUTO_RESUME_WIDTH = 311.02
_AUTO_RESUME_LEADING = 5.0
_AUTO_RESUME_COMPACT_THRESHOLD = 55
_AUTO_RESUME_FRAME_SLACK = 0.5
_AUTO_RESUME_HEADERS = {
    "auto resume conditions": "en",
    "conditions de reprise automatique": "fr",
    "condiciones de reanudación automática": "es",
}
_AUTO_RESUME_GEOMETRY = {
    "en": _AutoResumeGeometry(
        row_heights=(12.50, 11.49, 11.48, 10.01, 10.75),
        column_widths=(157.52, 152.00),
        cell_insets=((5.2, 2.4), (5.2, 2.4)),
        first_line_indent=-6.82,
        space_before=6.62,
    ),
    "fr": _AutoResumeGeometry(
        row_heights=(12.50, 14.45, 11.49, 10.01, 10.75),
        column_widths=(147.78, 161.74),
        cell_insets=((2.8, 2.4), (2.4, 2.4)),
        first_line_indent=-2.57,
        space_before=8.04,
    ),
    "es": _AutoResumeGeometry(
        row_heights=(12.50, 10.85, 11.48, 10.01, 10.75),
        column_widths=(147.78, 161.74),
        cell_insets=((2.8, 2.4), (2.4, 2.4)),
        first_line_indent=-5.49,
        space_before=9.26,
    ),
}


def _plain_cell(value: object) -> str:
    """Normalize table copy for governed-header matching."""
    return " ".join(str(value).replace("**", "").split())


def _troubleshooting_cell_geometry(
    row_index: int,
    column_index: int,
    *,
    step_count: int,
    steps_pad_tb: float,
) -> tuple[float, float, float, float, str]:
    """Return the shared top/bottom/left/right/vertical cell contract."""
    is_steps = step_count > 0
    if row_index == 0:
        top = 0.8 if column_index == 0 else 1.5
        bottom = 0.5 if column_index == 0 else 1.5
        valign = "CenterAlign"
    elif column_index == 0 and is_steps:
        top = 12.7 if step_count >= 5 else 7.6
        bottom = 2.95
        valign = "TopAlign"
    else:
        top = (
            max(0.0, steps_pad_tb - 0.30465)
            if column_index == 1 and is_steps else 2.95
        )
        bottom = (
            steps_pad_tb + 0.32535
            if column_index == 1 and is_steps else 2.95
        )
        if row_index in range(1, 7):
            top = bottom = 1.5
        if row_index == 9:
            top = bottom = 2.35
        valign = (
            "TopAlign" if row_index in {6, 9, 10, 11} else "CenterAlign"
        )
    left = (
        2.88 if row_index == 0 and column_index == 0
        else 1.5 if row_index > 0 and column_index == 0
        else 3.0
    )
    return top, bottom, left, 3.0, valign


def _troubleshooting_line_count(
    text: object,
    width: float,
    *,
    size: float,
    glyph_width_ratio: float,
) -> int:
    """Conservatively predict InDesign word wrapping for one table cell."""
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", strip_rst_inline(str(text)))
    chars_per_line = max(1, int(width / max(0.1, size * glyph_width_ratio)))
    count = 0
    for source_line in cleaned.splitlines() or [""]:
        words = source_line.split()
        if not words:
            count += 1
            continue
        used = 0
        lines = 1
        for word in words:
            required = len(word) + (1 if used else 0)
            if used and used + required > chars_per_line:
                lines += 1
                used = len(word)
            else:
                used += required
        count += lines
    return max(1, count)


def _troubleshooting_frame_height(
    raw_rows: list[list],
    *,
    body_width: float,
    style: TroubleshootingTableStyle,
) -> float:
    """Budget localized AutoGrow rows before emitting the fixed panel group.

    The approved EN/FR/ES copy has a native-InDesign row-height baseline.  It
    captures font shaping that a deterministic build cannot query from a host
    application (notably the two-line FR/ES code header).  The same width,
    type, leading and inset calculation then adds growth when edited copy wraps
    beyond that reviewed baseline.
    """
    left_width = body_width * style.left_ratio + style.left_optical_width
    column_widths = (left_width, body_width - left_width)
    header = _plain_cell(raw_rows[0][0]).casefold() if raw_rows else ""
    language = _TROUBLESHOOTING_HEADER_LANGUAGES.get(header, "en")
    calibration = _TROUBLESHOOTING_LOCALE_CALIBRATIONS[language]
    budget = 0.0
    for row_index, row in enumerate(raw_rows):
        right = str(row[1]) if len(row) > 1 else ""
        step_count = right.count("|") if right.lstrip().startswith("|") else 0
        measured_lines: list[int] = []
        for column_index in range(2):
            text = row[column_index] if column_index < len(row) else ""
            _top, _bottom, left, right_inset, _ = _troubleshooting_cell_geometry(
                row_index,
                column_index,
                step_count=step_count,
                steps_pad_tb=style.steps_pad_tb,
            )
            if row_index == 0:
                size = style.header_size
            elif column_index == 0:
                size = style.code_size
            else:
                size = style.body_size
            lines = _troubleshooting_line_count(
                text,
                max(1.0, column_widths[column_index] - left - right_inset),
                size=size,
                glyph_width_ratio=style.glyph_width_ratio,
            )
            measured_lines.append(lines)
        if row_index < len(calibration.native_row_heights):
            native_height = calibration.native_row_heights[row_index]
            left_baseline = calibration.left_line_baseline[row_index]
            right_baseline = calibration.right_line_baseline[row_index]
        else:
            native_height = style.minimum_for_row(row_index)
            left_baseline = right_baseline = 1
        left_growth = max(0, measured_lines[0] - left_baseline) * (
            style.header_leading if row_index == 0 else style.code_leading
        )
        right_growth = max(0, measured_lines[1] - right_baseline) * (
            style.header_leading if row_index == 0 else style.body_leading
        )
        budget += native_height + max(left_growth, right_growth)
    if budget <= style.panel_min_height:
        return style.panel_min_height
    return budget + style.import_safety


def auto_resume_language(raw_rows: list[list]) -> str | None:
    """Return the locale encoded by an approved Auto Resume header."""
    if (
        not raw_rows
        or not raw_rows[0]
        or max((len(row) for row in raw_rows), default=0) != 2
    ):
        return None
    return _AUTO_RESUME_HEADERS.get(_plain_cell(raw_rows[0][0]).casefold())


def body_data_table_kind(raw_rows: list[list]) -> str | None:
    """Classify the two source-driven body tables that share group layout."""
    if not raw_rows:
        return None
    if auto_resume_language(raw_rows) is not None:
        return "auto_resume"
    if is_key_combinations_rows(raw_rows):
        return "key_combinations"
    # Preserve the generic-table fallback used by shortened/unit-test inputs
    # with a governed localized header. A production-shaped five-row table is
    # never allowed through this header-only path: it must pass the semantic
    # button-pair check above before fixed Key assets can be selected.
    header = tuple(
        _plain_cell(cell).casefold()
        for cell in raw_rows[0][:3]
    )
    localized_key_headers = {
        ("buttons", "operation", "function"),
        ("boutons", "utilisation", "fonction"),
        ("botones", "operación", "función"),
    }
    if len(raw_rows) != 5 and header in localized_key_headers:
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


def _troubleshooting_table(
    raw_rows: list[list],
    ctx: RenderContext,
    tid: str,
    style: TroubleshootingTableStyle,
) -> tuple[str, float]:
    """Render the shared LaTeX troubleshooting-table contract in IDML.

    This table is deliberately not a generic two-column spec table: the
    narrow code column, bold code face, header treatment, row minima and
    inner hairlines all have their own shared layout tokens.
    """
    body_w = ctx.text_measure - (1.13 if ctx.add_story is not None else 0.0)
    # The reference divider is four points to the right of the bare ratio.
    # Keep that optical allowance distinct from cell padding so the visible
    # code column stays aligned in every language.
    left_w = body_w * style.left_ratio + style.left_optical_width
    cols = [left_w, body_w - left_w]
    header = _plain_cell(raw_rows[0][0]).casefold() if raw_rows else ""
    language = _TROUBLESHOOTING_HEADER_LANGUAGES.get(header, "en")
    calibration = _TROUBLESHOOTING_LOCALE_CALIBRATIONS[language]

    cells: list[str] = []
    for ri, row in enumerate(raw_rows):
        left = str(row[0]) if row else ""
        right = str(row[1]) if len(row) > 1 else ""
        step_count = right.count("|") if right.lstrip().startswith("|") else 0
        if ri == 0:
            styles = ("HB Data Header", "HB Data Header")
            fills: tuple[str | None, str | None] = (
                "Color/HB Bg K05",
                "Color/HB Bg K05",
            )
        else:
            styles = ("HB Data Code", "HB Data Body")
            fills = ("Color/HB Bg K05", None)
        for ci, (text, paragraph_style, fill) in enumerate(
            zip((left, right), styles, fills)
        ):
            content = psr(paragraph_style, text, terminal=True)
            if ri == 0:
                content = content.replace(
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                    'FontStyle="Bold"',
                    1,
                )
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
            else:
                content = with_character_metrics(
                    content,
                    point_size=style.body_size,
                    leading=style.body_leading,
                )
            top, bottom, left_inset, right_inset, valign = (
                _troubleshooting_cell_geometry(
                    ri,
                    ci,
                    step_count=step_count,
                    steps_pad_tb=style.steps_pad_tb,
                )
            )
            cells.append(cell(
                f"{tid}c{ri}_{ci}", f"{ci}:{ri}",
                content, fill=fill,
                top=top, bottom=bottom,
                left=left_inset,
                right=right_inset,
                edge_weight=style.inner_rule, edge_color="Color/HB Brand Dark",
                valign=valign,
            ))

    # InDesign's exported cell box is about 1.2 pt shorter than the IDML
    # SingleRowHeight value at this page scale.  The additive optical
    # correction keeps the PDF minima equal to the shared LaTeX tokens.
    rows = "\n".join(
        f'    <Row Self="{tid}r{ri}" Name="{ri}" '
        f'SingleRowHeight="{style.header_single_height if ri == 0 else style.body_single_height:g}" '
        f'MinimumHeight="{calibration.native_row_heights[ri] if ri < len(calibration.native_row_heights) else style.minimum_for_row(ri):g}" '
        'AutoGrow="true"/>'
        for ri in range(len(raw_rows))
    )
    columns = "\n".join(
        f'    <Column Self="{tid}col{ci}" Name="{ci}" SingleColumnWidth="{width:g}"/>'
        for ci, width in enumerate(cols)
    )
    table_xml = (
        f'  <Table Self="{tid}" AppliedTableStyle="TableStyle/$ID/[Basic Table]" '
        f'BodyRowCount="{len(raw_rows)}" ColumnCount="2" HeaderRowCount="0" FooterRowCount="0">\n'
        f'{rows}\n{columns}\n' + "\n".join(cells) + "\n  </Table>\n"
    )
    return table_xml, _troubleshooting_frame_height(
        raw_rows,
        body_width=body_w,
        style=style,
    )


def _body_data_table(
    raw_rows: list[list],
    ctx: RenderContext,
    tid: str,
    kind: str,
    *,
    panel_width: float | None = None,
    row_heights: tuple[float, ...] | None = None,
    column_widths: tuple[float, ...] | None = None,
    cell_insets: tuple[tuple[float, float], ...] | None = None,
) -> tuple[str, float]:
    """Mirror the shared LaTeX Auto Resume / Key Combination table tokens."""
    # The table shell owns the full body measure.  The requested one-character
    # inset belongs to the cells (``comp_table_text_indent``), never to the
    # heading/description/table group as a whole.
    body_w = (panel_width or ctx.text_measure) - 1.5
    # LaTeX's m-columns add tabcolsep around the declared percentage.
    # These optical additions place the visible dividers at the same x
    # coordinates instead of treating the bare percentages as full cells.
    first_optical = 2.76
    if kind == "auto_resume":
        if column_widths is not None:
            if len(column_widths) != 2:
                raise ValueError("Auto Resume column geometry must have two widths")
            if abs(sum(column_widths) - body_w) > 0.01:
                raise ValueError("Auto Resume column geometry does not match panel width")
            cols = list(column_widths)
        else:
            left = float(
                ctx.params.get("comp_auto_resume_left_ratio", ("0.5", ""))[0]
            )
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
    if cell_insets is not None and len(cell_insets) != n_cols:
        raise ValueError("Auto Resume cell inset geometry does not match columns")
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
            paragraph = psr(
                "HB Data Header" if ri == 0 else "HB Data Body",
                text,
                terminal=True,
            )
            if kind == "auto_resume" and ri > 0:
                # The production master uses tight 5pt leading in this one
                # fixed-height table. Long right-column copy uses 5.5pt at
                # every body-row position so FR protection and ES timer copy
                # remain on one line instead of growing into the next row.
                point_size = (
                    5.5
                    if ci == 1
                    and len(_plain_cell(text)) >= _AUTO_RESUME_COMPACT_THRESHOLD
                    else 6.0
                )
                paragraph = with_character_metrics(
                    paragraph,
                    point_size=point_size,
                    leading=_AUTO_RESUME_LEADING,
                )
            left_inset, right_inset = (
                cell_insets[ci]
                if cell_insets is not None else (text_indent, pad)
            )
            cell_xml = cell(
                f"{tid}c{ri}_{ci}", f"{ci}:{ri}",
                paragraph,
                fill=fill, top=0, bottom=0,
                left=left_inset, right=right_inset,
                edge_weight=rule, edge_color="Color/HB Brand Dark",
                valign="CenterAlign",
            )
            if rowspan > 1:
                cell_xml = cell_xml.replace('RowSpan="1"', f'RowSpan="{rowspan}"', 1)
            cells.append(cell_xml)
    table = component_table(tid, cols, cells, n_rows=len(raw_rows), role="data")
    table = suppress_outer_edges_xml(table, n_cols)
    if row_heights is not None and len(row_heights) != len(raw_rows):
        raise ValueError("Auto Resume row geometry does not match source rows")
    applied_heights = row_heights or tuple(
        header_h if ri == 0 else row_h
        for ri in range(len(raw_rows))
    )
    for ri, minimum in enumerate(applied_heights):
        auto_grow = not (kind == "auto_resume" and row_heights is not None)
        table = re.sub(
            rf'(<Row Self="{re.escape(tid)}r{ri}" Name="{ri}")/?>',
            rf'\1 SingleRowHeight="{minimum:g}" MinimumHeight="{minimum:g}" '
            f'AutoGrow="{str(auto_grow).lower()}"/>',
            table,
            count=1,
        )
    return table, sum(applied_heights) + (0.0 if row_heights else 3.0)


def render_table_block(raw_rows: list[list], ctx: RenderContext, *, tid: str,
                       terminal: bool, span_columns: bool = True) -> tuple[str, float]:
    n_cols = max(len(r) for r in raw_rows)
    first_cell = str(raw_rows[0][0]).replace("**", "").strip() if raw_rows else ""
    is_overview = first_cell in {"POWER Button", "Total Output", "Handle"}
    # Troubleshooting is a shared visual component across EN/FR/ES. Detect
    # the semantic header in every governed language so localized pages do
    # not silently fall back to the legacy square table.
    trouble_headers = {
        "error code", "code d'erreur", "code d’erreur",
        "código de fallo", "codigo de fallo",
        "código de error", "codigo de error",
    }
    trouble_header = str(raw_rows[0][0]).strip().casefold() if raw_rows else ""
    is_troubleshooting = n_cols == 2 and trouble_header in trouble_headers
    body_kind = body_data_table_kind(raw_rows)
    is_auto_resume = body_kind == "auto_resume"
    is_key_combinations = body_kind == "key_combinations"
    auto_language = auto_resume_language(raw_rows) if is_auto_resume else None
    auto_geometry = _AUTO_RESUME_GEOMETRY.get(auto_language or "")
    if auto_geometry is not None and len(raw_rows) != len(auto_geometry.row_heights):
        auto_geometry = None
    data_table_before = param_pt(ctx.params, "comp_data_table_before", 3.4)
    data_table_after = param_pt(ctx.params, "comp_data_table_after", 3.4)
    auto_space_before = (
        auto_geometry.space_before
        if auto_geometry is not None else data_table_before
    )
    troubleshooting_style: TroubleshootingTableStyle | None = None
    troubleshooting_estimate: float | None = None
    if (
        is_key_combinations
        and ctx.add_story is not None
        and is_key_combinations_rows(raw_rows)
    ):
        xml, framed_h = render_key_combinations(
            raw_rows,
            ctx,
            tid=tid,
            terminal=terminal,
        )
        if xml:
            after = param_pt(ctx.params, "comp_data_table_after", 3.4)
            xml = xml.replace(
                "<ParagraphStyleRange ",
                f'<ParagraphStyleRange SpaceAfter="{after:g}" ',
                1,
            )
            return xml, framed_h + after
    if is_overview:
        table = _overview_table(raw_rows, ctx, tid)
    elif is_troubleshooting:
        troubleshooting_style = TroubleshootingTableStyle.from_context(ctx)
        table, framed_h = _troubleshooting_table(
            raw_rows,
            ctx,
            tid,
            troubleshooting_style,
        )
    elif is_auto_resume or is_key_combinations:
        table, framed_h = _body_data_table(
            raw_rows, ctx, tid,
            "auto_resume" if is_auto_resume else "key_combinations",
            panel_width=(
                min(_AUTO_RESUME_WIDTH, ctx.text_measure)
                if auto_geometry is not None else None
            ),
            row_heights=(
                auto_geometry.row_heights
                if auto_geometry is not None else None
            ),
            column_widths=(
                auto_geometry.column_widths
                if auto_geometry is not None else None
            ),
            cell_insets=(
                auto_geometry.cell_insets
                if auto_geometry is not None else None
            ),
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
        table_width = (
            min(_AUTO_RESUME_WIDTH, ctx.text_measure)
            if auto_geometry is not None else ctx.text_measure
        )
        table_before = auto_space_before if is_auto_resume else data_table_before
        xml = rounded_table_panel(
            ctx.add_story,
            ctx.params,
            sid=f"st_anchor_data_{tid}",
            title="body data table",
            table_xml=table,
            width=table_width,
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
            # InDesign ignores the nested inline Group transform. The host
            # paragraph below owns the measured first-line offset instead.
            left_indent=0.0,
            space_before=table_before,
            space_after=(
                max(0.0, data_table_after - _AUTO_RESUME_FRAME_SLACK)
                if is_auto_resume else data_table_after
            ),
            content_bottom_bleed=(
                _AUTO_RESUME_FRAME_SLACK if is_auto_resume else 0.0
            ),
        )
        if auto_geometry is not None:
            paragraph_indent = (
                auto_geometry.first_line_indent - ctx.inline_origin_shift
            )
            xml = xml.replace(
                "<ParagraphStyleRange ",
                '<ParagraphStyleRange LeftIndent="0" '
                f'FirstLineIndent="{paragraph_indent:g}" ',
                1,
            )
    elif is_troubleshooting and ctx.add_story is not None:
        if troubleshooting_style is None:
            raise RuntimeError("troubleshooting style was not resolved")
        xml = rounded_table_panel(
            ctx.add_story,
            ctx.params,
            sid=f"st_anchor_trouble_{tid}",
            title="troubleshooting table",
            table_xml=table,
            width=ctx.text_measure - 0.75,
            height=framed_h,
            n_cols=2,
            terminal=terminal,
            fill="Color/Paper",
            stroke="Color/HB Brand Dark",
            stroke_weight=troubleshooting_style.outer_rule,
            radius=troubleshooting_style.outer_radius,
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
        if troubleshooting_style is None:
            raise RuntimeError("troubleshooting style was not resolved")
        # LaTeX's HBDataTableFrame has a dedicated before gap.  Keep it on
        # the host paragraph so page-flow and table geometry remain separate.
        header = _plain_cell(raw_rows[0][0]).casefold() if raw_rows else ""
        language = _TROUBLESHOOTING_HEADER_LANGUAGES.get(header, "en")
        table_space_before = troubleshooting_style.table_space_before(language)
        xml = xml.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange SpaceBefore="{table_space_before:g}" ',
            1,
        )
        troubleshooting_estimate = framed_h + table_space_before
    if is_auto_resume:
        return xml, framed_h + auto_space_before + data_table_after
    if is_key_combinations:
        return xml, framed_h + 2 * param_pt(ctx.params, "comp_data_table_before", 3.4)
    if is_troubleshooting:
        if troubleshooting_estimate is None:
            raise RuntimeError("troubleshooting estimate was not resolved")
        return xml, troubleshooting_estimate
    return xml, 11.0 * (len(raw_rows) + 1)
