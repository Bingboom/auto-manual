"""Two-column specification table XML, including master parity geometry."""
from __future__ import annotations

from collections.abc import Callable

from .style_names import table_style_ref


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
    paragraph_xml: Callable[..., str],
) -> str:
    table_style = table_style_ref(role)
    left_ratio = float(params.get("comp_spec_table_left_ratio", ("0.315", ""))[0])
    body_w = page_w - m_l - m_r - (1.13 if visual_parity else 0.0)
    col1 = body_w * left_ratio + (2.3 if visual_parity else 0.0)
    col2 = body_w - col1
    first_label = rows[0][0] if rows else ""
    target_shrink = {
        "Product Name": 0.95,
        "1 × AC Input": 2.95,
        "Charging Temperature": 2.25,
    }.get(first_label, 0.0)
    inset_shrink = target_shrink / max(1, 2 * len(rows))
    table_baseline_nudge = {
        "Product Name": 2.85,
        "1 × AC Input": 1.35,
        "Charging Temperature": 2.43,
    }.get(first_label, 0.0)
    cells = []
    for ri, (label, value) in enumerate(rows):
        if not visual_parity:
            inset = 2.0
        elif "\n" in value:
            inset = 6.72 + (0.445 if ri == 0 else -0.445)
        elif len(value) > 80:
            inset = 5.0
        elif label.startswith("AC Output in Bypass"):
            inset = 5.39
        else:
            inset = 4.45 + (0.2 if ri in {0, len(rows) - 1} else 0.0)
        if visual_parity:
            inset = max(0.0, inset - inset_shrink)
        for ci, (text, style) in enumerate(
            ((label, label_style), (value, "HB Spec Value"))
        ):
            content = paragraph_xml(style, text, terminal=True)
            if visual_parity:
                if "\n" in value:
                    baseline = -1.43 if ci == 0 else 0.08
                elif label.startswith("AC Output in Bypass"):
                    baseline = -0.04
                elif label.startswith(("USB-C", "1 × USB", "1 × DC")):
                    baseline = -1.19
                else:
                    baseline = -1.52
                if first_label == "3 × AC":
                    if label == "3 × AC":
                        baseline += 1.20
                    elif label.startswith("AC Output in Bypass"):
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
                + ('VerticalJustification="CenterAlign" ' if visual_parity else '')
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
    row_xml = "\n".join(
        f'    <Row Self="{tid}r{ri}" Name="{ri}" SingleRowHeight="10.3"/>'
        for ri in range(len(rows))
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
