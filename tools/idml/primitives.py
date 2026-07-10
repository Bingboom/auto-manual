"""IDML XML building blocks (componentization P1).

Pure functions extracted verbatim from IdmlWriter — every string literal
here is load-bearing for InDesign (designer-reported traps are kept in the
comments next to the code that dodges them). Page geometry arrives as
explicit arguments so components/stories can be built without the writer.
"""
from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

from .style_names import paragraph_style_ref, table_style_ref
from .table_borders import component_table_xml

# saxutils.escape only handles &<> by default; inside a double-quoted
# XML attribute a raw " truncates the value and malforms the part.
_ATTR_ENTITIES = {'"': "&quot;"}

# Text fallbacks are kept as a public compatibility hook for the writer,
# but semantic symbols should render as symbols, not be rewritten into
# approximate ASCII. Characters that Gilroy lacks are handled by
# SYMBOL_FONT_FALLBACK_CHARS below at character-run level.
GLYPH_FALLBACKS: tuple[tuple[str, str], ...] = ()

DIRECT_CURRENT_SYMBOL_FONT = "Apple Symbols"
GENERAL_SYMBOL_FONT = "Arial Unicode MS"
SYMBOL_FONT_FALLBACK_STYLE = "Regular"
SYMBOL_FONT_FALLBACKS = {
    "⎓": DIRECT_CURRENT_SYMBOL_FONT,
    "※": GENERAL_SYMBOL_FONT,
    **{ch: GENERAL_SYMBOL_FONT for ch in "₀₁₂₃₄₅₆₇₈₉①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖"},
}

PROSE_STYLE = {"h1": "HB H1", "h2": "HB Title L2", "h3": "HB Title L3",
               "label": "HB Notice Label", "body": "HB Body", "list": "HB List"}


def clean_text(text: str) -> str:
    for raw, replacement in GLYPH_FALLBACKS:
        text = text.replace(raw, replacement)
    return text


def bold_runs(line: str) -> list[tuple[str, bool]]:
    """Split rst inline strong markup (**x**) into (text, bold) runs.

    Designer-reported: literal ** asterisks in body text. Bare *
    emphasis is left alone (rare in the bundles and ambiguous with
    footnote markers).
    """
    runs: list[tuple[str, bool]] = []
    parts = re.split(r"\*\*(.+?)\*\*", line)
    for i, part in enumerate(parts):
        if part:
            runs.append((part, i % 2 == 1))
    return runs


def _character_runs(seg: str) -> list[tuple[str, str | None]]:
    """Split a run by the explicit font fallback it needs."""
    runs: list[tuple[str, str | None]] = []
    buf: list[str] = []
    current_font = SYMBOL_FONT_FALLBACKS.get(seg[0]) if seg else None
    for ch in seg:
        font = SYMBOL_FONT_FALLBACKS.get(ch)
        if font != current_font:
            runs.append(("".join(buf), current_font))
            buf = []
            current_font = font
        buf.append(ch)
    if buf:
        runs.append(("".join(buf), current_font))
    return runs


def _character_style_range(seg: str, *, bold: bool, fallback_font: str | None) -> str:
    attrs = 'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"'
    properties = ""
    if fallback_font:
        attrs += f' FontStyle="{SYMBOL_FONT_FALLBACK_STYLE}"'
        properties = (
            "<Properties>"
            f'<AppliedFont type="string">{escape(fallback_font)}</AppliedFont>'
            "</Properties>"
        )
    elif bold:
        attrs += ' FontStyle="Bold"'
    return f'<CharacterStyleRange {attrs}>{properties}<Content>{escape(seg)}</Content></CharacterStyleRange>'


def psr(style: str, text: str, *, terminal: bool = False,
        span_columns: bool = False) -> str:
    """One ParagraphStyleRange.

    IDML paragraphs are delimited by explicit <Br/> characters in the
    content stream, NOT by ParagraphStyleRange boundaries — without a
    trailing <Br/> adjacent ranges fuse into one paragraph
    ("SPECIFICATIONSGENERAL INFO", designer-reported). Every range
    therefore ends with <Br/> unless it is the story's last one.
    """
    lines = clean_text(text).split("\n")
    line_xmls = []
    for line in lines:
        runs = bold_runs(line)
        line_xmls.append("".join(
            _character_style_range(piece, bold=bold, fallback_font=fallback_font)
            for seg, bold in runs
            for piece, fallback_font in _character_runs(seg)
        ) or '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
             '<Content></Content></CharacterStyleRange>')
    br = ('<CharacterStyleRange AppliedCharacterStyle='
          '"CharacterStyle/$ID/[No character style]"><Br/></CharacterStyleRange>')
    content = br.join(line_xmls)
    if not terminal:
        content += br
    sid = paragraph_style_ref(style)
    span_attr = ' SpanColumnType="SpanColumns"' if span_columns else ""
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{sid}"{span_attr}>\n'
        f'    {content}\n'
        '  </ParagraphStyleRange>\n'
    )


def spec_table(tid: str, rows: list[tuple[str, str]],
               label_style: str = "HB Spec Label", *,
               params: dict[str, tuple[str, str]],
               page_w: float, m_l: float, m_r: float,
               role: str | None = None) -> str:
    table_style = table_style_ref(role)
    left_ratio = float(params.get("comp_spec_table_left_ratio", ("0.315", ""))[0])
    body_w = page_w - m_l - m_r
    col1 = body_w * left_ratio
    col2 = body_w - col1
    cells = []
    for ri, (label, value) in enumerate(rows):
        for ci, (txt, style) in enumerate(((label, label_style), (value, "HB Spec Value"))):
            cells.append(
                f'    <Cell Self="{tid}c{ri}_{ci}" Name="{ci}:{ri}" RowSpan="1" ColumnSpan="1" '
                'AppliedCellStyle="CellStyle/$ID/[None]" '
                'TopInset="2" BottomInset="2" LeftInset="3" RightInset="3">\n'
                + psr(style, txt, terminal=True) +
                '    </Cell>'
            )
    row_els = "\n".join(
        f'    <Row Self="{tid}r{ri}" Name="{ri}" SingleRowHeight="10.3"/>' for ri in range(len(rows))
    )
    return (
        f'  <Table Self="{tid}" AppliedTableStyle="{table_style}" '
        f'BodyRowCount="{len(rows)}" ColumnCount="2" HeaderRowCount="0" FooterRowCount="0">\n'
        f'{row_els}\n'
        f'    <Column Self="{tid}col0" Name="0" SingleColumnWidth="{col1:g}"/>\n'
        f'    <Column Self="{tid}col1" Name="1" SingleColumnWidth="{col2:g}"/>\n'
        + "\n".join(cells) + "\n"
        '  </Table>\n'
    )


def image_cell_content(rect_id: str, image_path: Path, w_pt: float, h_pt: float) -> str:
    """Anchored image frame for a table cell, linked to a file on disk.

    The Link keeps the file external (URI), so the designer relinks or
    edits assets through InDesign's Links panel — the same contract as
    a hand-built document.
    """
    uri = image_path.resolve().as_uri()
    # Inline anchored objects hang from the text baseline: the path must
    # span y in [-h, 0]. A [0, h] path drops below the line and overlaps
    # the following text (designer-reported).
    x1, y1, x2, y2 = 0.0, -h_pt, w_pt, 0.0
    pts = ((x1, y1), (x1, y2), (x2, y2), (x2, y1))
    anchors = "".join(
        f'<PathPointType Anchor="{x:g} {y:g}" LeftDirection="{x:g} {y:g}" '
        f'RightDirection="{x:g} {y:g}"/>' for x, y in pts
    )
    return (
        f'<Rectangle Self="{rect_id}" ContentType="GraphicType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0" '
        'StrokeColor="Swatch/None" StrokeWeight="0" AnchoredPosition="InlinePosition">'
        '<Properties><PathGeometry><GeometryPathType PathOpen="false">'
        f'<PathPointArray>{anchors}</PathPointArray>'
        '</GeometryPathType></PathGeometry></Properties>'
        f'<Image Self="{rect_id}_img" ItemTransform="1 0 0 1 0 0">'
        f'<Link Self="{rect_id}_lnk" LinkResourceURI="{escape(uri, _ATTR_ENTITIES)}"/>'
        '</Image>'
        '<FrameFittingOption FittingOnEmptyFrame="Proportionally"/>'
        '</Rectangle>'
    )


def resolve_bundle_image(bundle_root: Path, ref: str) -> Path | None:
    """Resolve an image reference from a bundle page.

    Refs are either bundle-relative paths (_assets/..., _repo_assets/...)
    or bare basenames from component macro args (main_unit1.png).
    """
    cand = bundle_root / ref
    if cand.exists():
        return cand
    name = Path(ref).name
    for base in (bundle_root / "_assets", bundle_root / "_repo_assets"):
        if base.is_dir():
            hits = sorted(base.rglob(name))
            if hits:
                return hits[0]
    return None


def art_frame_size(img: Path, max_w: float = 120.0, *,
                   page_w: float, m_l: float, m_r: float) -> tuple[float, float]:
    """Frame size honoring the image's real aspect ratio (Pillow when
    available; 0.62 heuristic keeps working without it)."""
    w_pt = min(max_w, page_w - m_l - m_r)
    try:
        from PIL import Image as _PILImage
        with _PILImage.open(img) as im:
            iw, ih = im.size
        if iw > 0:
            return w_pt, w_pt * ih / iw
    except Exception:
        pass
    return w_pt, w_pt * 0.62


def cell(cid: str, name: str, content: str, *, fill: str | None = None,
         stroke: bool = True, top: float = 3, bottom: float = 3,
         left: float = 4, right: float = 4) -> str:
    # cell fill is FillColor in IDML; CellFillColor is silently ignored
    # (designer-reported: no gray FCC/notice panels)
    fill_attr = f'FillColor="{fill}" ' if fill else ""
    stroke_attr = "" if stroke else (
        'LeftEdgeStrokeWeight="0" RightEdgeStrokeWeight="0" '
        'TopEdgeStrokeWeight="0" BottomEdgeStrokeWeight="0" ')
    return (
        f'    <Cell Self="{cid}" Name="{name}" RowSpan="1" ColumnSpan="1" '
        f'AppliedCellStyle="CellStyle/$ID/[None]" {fill_attr}{stroke_attr}'
        f'TopInset="{top:g}" BottomInset="{bottom:g}" '
        f'LeftInset="{left:g}" RightInset="{right:g}">\n'
        + content + '    </Cell>')


def component_table(tid: str, cols: list[float], cells: list[str],
                    n_rows: int = 1, role: str | None = None, *,
                    outer_stroke: bool = True) -> str:
    return component_table_xml(tid, cols, cells, n_rows, role=role, outer_stroke=outer_stroke)


def wrap_table_paragraph(table: str, terminal: bool,
                         span_columns: bool = True) -> str:
    # SpanColumns: component tables run full measure across multi-column
    # frames (V2.0 master: warning boxes span the two-column safety text;
    # designer-reported overlap otherwise). No effect in single-column
    # frames.
    span_attr = ' SpanColumnType="SpanColumns"' if span_columns else ""
    style_ref = paragraph_style_ref("HB Body")
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}"'
        f'{span_attr}>\n'
        '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
        + table +
        ('    <Content></Content></CharacterStyleRange>\n' if terminal else
         '    <Br/></CharacterStyleRange>\n')
        + '  </ParagraphStyleRange>\n')


def path_geometry(x1: float, y1: float, x2: float, y2: float) -> str:
    """Rectangle as IDML PathGeometry.

    Spline items (TextFrame etc.) do NOT take a GeometricBounds
    attribute — that is a scripting-DOM property. InDesign silently
    ignores it and instantiates a degenerate (invisible) frame, which
    is exactly the "opens fine but every page is blank" failure mode.
    The geometry must be a four-anchor closed path in Properties.
    """
    pts = ((x1, y1), (x1, y2), (x2, y2), (x2, y1))
    anchors = "\n".join(
        f'            <PathPointType Anchor="{x:g} {y:g}" '
        f'LeftDirection="{x:g} {y:g}" RightDirection="{x:g} {y:g}"/>'
        for x, y in pts
    )
    return (
        '    <Properties>\n'
        '      <PathGeometry>\n'
        '        <GeometryPathType PathOpen="false">\n'
        '          <PathPointArray>\n'
        f'{anchors}\n'
        '          </PathPointArray>\n'
        '        </GeometryPathType>\n'
        '      </PathGeometry>\n'
        '    </Properties>\n'
    )
