"""Two-column specification table XML, including master parity geometry."""
from __future__ import annotations

from collections.abc import Callable

from tools.component_specs.spec_table import (
    idml_spec_table_rows,
    spec_table_component_spec,
)

from .params import param_pt
from .style_names import table_style_ref


def spec_table_row_heights(
    rows: list[tuple[str, str]],
    params: dict[str, tuple[str, str]],
    *,
    density: str,
    language: str | None = None,
) -> list[float]:
    """Return component-owned row heights for one specification table."""

    if density not in {"reference", "compact"}:
        raise ValueError(f"unsupported specification-table density: {density}")
    compact = density == "compact"
    language_key = (
        (language or "").strip().casefold().replace("_", "-").split("-", 1)[0]
    )
    row_height_key = (
        "idml_compact_spec_table_row_height" if compact
        else "idml_spec_table_row_height"
    )
    multiline_height_key = (
        "idml_compact_spec_table_multiline_min_height" if compact
        else "comp_spec_table_multiline_min_height"
    )
    row_height = param_pt(
        params,
        row_height_key,
        10.3,
    )
    if language_key:
        row_height = param_pt(
            params,
            f"lang_{language_key}_{row_height_key}",
            row_height,
        )
    multiline_height = param_pt(
        params,
        multiline_height_key,
        13.0 if compact else 15.0,
    )
    if language_key:
        multiline_height = param_pt(
            params,
            f"lang_{language_key}_{multiline_height_key}",
            multiline_height,
        )
    cell_inset = (
        param_pt(params, "idml_compact_spec_table_cell_inset", 2.0)
        if compact else 0.0
    )
    value_leading = param_pt(params, "type_spec_value_font_leading", 6.6)
    if language_key:
        value_leading = param_pt(
            params,
            f"lang_{language_key}_type_spec_value_font_leading",
            value_leading,
        )
    heights: list[float] = []
    for label, value in rows:
        explicit_lines = max(
            len(str(label).splitlines()) or 1,
            len(str(value).splitlines()) or 1,
        )
        if explicit_lines <= 1:
            heights.append(row_height)
            continue
        if not compact:
            # Reference tables use AutoGrow=true in the emitted IDML.  Keep
            # their historical minimum-height contract and let InDesign grow
            # the row from the story contents instead of baking source line
            # count into the reference geometry.
            heights.append(max(row_height, multiline_height))
            continue
        # Compact cells use fixed-height rows, so the multiline token is only
        # a floor.  Explicit three-line source values must also reserve their
        # actual line boxes plus the component-owned top/bottom insets.
        heights.append(max(
            row_height,
            multiline_height,
            explicit_lines * value_leading + 2.0 * cell_inset,
        ))
    return heights


def spec_table_height(
    rows: list[tuple[str, str]],
    params: dict[str, tuple[str, str]],
    *,
    density: str,
    language: str | None = None,
) -> float:
    """Return the visible shell height owned by the table's rows."""

    return sum(spec_table_row_heights(
        rows,
        params,
        density=density,
        language=language,
    ))


def spec_table_xml(
    tid: str,
    rows: list[tuple[str, str]],
    label_style: str,
    *,
    params: dict[str, tuple[str, str]],
    page_w: float,
    m_l: float,
    m_r: float,
    role: str | None,
    visual_parity: bool,
    density: str,
    section_index: int | None,
    language: str | None,
    paragraph_xml: Callable[..., str],
) -> str:
    if density not in {"reference", "compact"}:
        raise ValueError(f"unsupported specification-table density: {density}")
    compact = density == "compact"
    component = spec_table_component_spec(
        section_title=role or tid,
        rows=rows,
        source_ref=f"idml:{tid}",
        language=language or "und",
    )
    rows = idml_spec_table_rows(component)
    table_style = table_style_ref(role)
    language_key = (language or "").strip().casefold().replace("_", "-").split("-", 1)[0]
    default_left_ratio = params.get(
        "idml_spec_table_left_ratio",
        params.get("comp_spec_table_left_ratio", ("0.315", "")),
    )
    density_left_ratio = params.get(
        f"lang_{language_key}_idml_{density}_spec_table_left_ratio"
    )
    language_left_ratio = params.get(
        f"lang_{language_key}_idml_spec_table_left_ratio"
    )
    left_ratio = float(
        (density_left_ratio or language_left_ratio or default_left_ratio)[0]
    )
    body_w = page_w - m_l - m_r - (1.13 if visual_parity else 0.0)
    col1 = body_w * left_ratio + (2.3 if visual_parity else 0.0)
    col2 = body_w - col1
    first_label = rows[0][0] if rows else ""
    # The approved page has four semantic sections in a fixed order.  The
    # previous implementation keyed these optical corrections from English
    # cell copy, so the identical FR/ES tables silently skipped them after
    # translation and their final row became overset in real InDesign.
    # Prefer the renderer-owned section identity; retain the English lookup
    # for older internal callers that do not yet provide it.
    target_shrink = (
        {0: 0.95, 1: 2.95, 3: 2.25}.get(section_index, 0.0)
        if section_index is not None
        else {
            "Product Name": 0.95,
            "1 × AC Input": 2.95,
            "Charging Temperature": 2.25,
        }.get(first_label, 0.0)
    )
    inset_shrink = target_shrink / max(1, 2 * len(rows))
    table_baseline_nudge = (
        {0: 2.85, 1: 1.35, 3: 2.43}.get(section_index, 0.0)
        if section_index is not None
        else {
            "Product Name": 2.85,
            "1 × AC Input": 1.35,
            "Charging Temperature": 2.43,
        }.get(first_label, 0.0)
    )
    cells = []
    for ri, (label, value) in enumerate(rows):
        if compact:
            inset = param_pt(
                params,
                "idml_compact_spec_table_cell_inset",
                2.0,
            )
        elif not visual_parity:
            inset = 2.0
        elif "\n" in value:
            inset = 6.72 + (0.445 if ri == 0 else -0.445)
        elif len(value) > 80:
            inset = 5.0
        elif section_index == 2 and ri == 1 or label.startswith("AC Output in Bypass"):
            inset = 5.39
        else:
            inset = 4.45 + (0.2 if ri in {0, len(rows) - 1} else 0.0)
        if visual_parity:
            inset = max(0.0, inset - inset_shrink)
        for ci, (text, style) in enumerate(
            ((label, label_style), (value, "HB Spec Value"))
        ):
            content = paragraph_xml(
                style,
                text,
                terminal=True,
                superscript_markers=True,
            )
            if visual_parity and not compact:
                if "\n" in value:
                    baseline = -1.43 if ci == 0 else 0.08
                elif section_index == 2 and ri == 1 or label.startswith("AC Output in Bypass"):
                    baseline = -0.04
                elif (
                    section_index == 2 and ri >= 2
                    or label.startswith(("USB-C", "1 × USB", "1 × DC"))
                ):
                    baseline = -1.19
                else:
                    baseline = -1.52
                if section_index == 2 or first_label == "3 × AC":
                    if ri == 0:
                        baseline += 1.20
                    elif ri == 1:
                        baseline -= 1.21
                    else:
                        baseline += 0.10
                else:
                    baseline += table_baseline_nudge
                content = content.replace(
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                    f'BaselineShift="{baseline:g}"',
                    1,
                )
            left = (
                5.85 if visual_parity and ci == 0
                else 3.89 if visual_parity and ci == 1 and "\n" in value
                else 2.26 if visual_parity and ci == 1
                else 3.0
            )
            cells.append(
                f'    <Cell Self="{tid}c{ri}_{ci}" Name="{ci}:{ri}" '
                'RowSpan="1" ColumnSpan="1" '
                'AppliedCellStyle="CellStyle/$ID/[None]" '
                # Keep the table contract independent of the visual-parity
                # branch: every editable table cell is vertically centered.
                + 'VerticalJustification="CenterAlign" '
                + (
                    'LeftEdgeStrokeWeight="0.5" RightEdgeStrokeWeight="0.5" '
                    'TopEdgeStrokeWeight="0.5" BottomEdgeStrokeWeight="0.5" '
                    'LeftEdgeStrokeColor="Color/HB Brand Dark" '
                    'RightEdgeStrokeColor="Color/HB Brand Dark" '
                    'TopEdgeStrokeColor="Color/HB Brand Dark" '
                    'BottomEdgeStrokeColor="Color/HB Brand Dark" '
                    if visual_parity else ''
                )
                + f'TopInset="{inset:g}" BottomInset="{inset:g}" '
                f'LeftInset="{left:g}" RightInset="3">\n'
                + content
                + '    </Cell>'
            )
    row_heights = spec_table_row_heights(
        rows,
        params,
        density=density,
        language=language,
    )
    row_xml = "\n".join(
        f'    <Row Self="{tid}r{ri}" Name="{ri}" '
        f'SingleRowHeight="{height:g}" MinimumHeight="{height:g}" '
        f'AutoGrow="{str(not compact).lower()}"/>'
        for ri, height in enumerate(row_heights)
    )
    spacing = ' SpaceBefore="0" SpaceAfter="0"' if visual_parity else ""
    return (
        f'  <Table Self="{tid}" AppliedTableStyle="{table_style}" '
        f'BodyRowCount="{len(rows)}" ColumnCount="2" HeaderRowCount="0" '
        f'FooterRowCount="0"{spacing}>\n'
        f'{row_xml}\n'
        f'    <Column Self="{tid}col0" Name="0" SingleColumnWidth="{col1:g}"/>\n'
        f'    <Column Self="{tid}col1" Name="1" SingleColumnWidth="{col2:g}"/>\n'
        + "\n".join(cells)
        + "\n  </Table>\n"
    )
