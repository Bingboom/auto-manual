"""V2.0 FCC + inbox composed page object rules."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from .components.notice import notice_box_layout, source_notice_label
from .fcc_fallback import component_spec, fcc_spec_from_blocks
from .page_objects import (
    BADGE_OBJECT_STYLE,
    CARD_OBJECT_STYLE,
    PANEL_OBJECT_STYLE,
    frame_with_background,
    heading_bar_opts,
    heading_text,
    left_rounded_xml,
    page_rectangle_xml,
    with_rounded_outer,
)
from .params import IDPKG, param_pt
from .style_names import paragraph_style_ref

ROOT = Path(__file__).resolve().parents[2]
H1_BAR_H = 20.0
BODY_X = 26.5
BODY_W = 311.0
BADGE_DIAMETER = 13.785
BADGE_Y_OFFSET = 22.431


def _story(writer, sid: str, title: str, parts: list[str]) -> str:
    return writer._add_story_parts(sid, title, parts)


def _image_paragraph(writer, tid: str, image: Path, max_w: float, *,
                     center: bool = True) -> str:
    width, height = writer._art_frame_size(image, max_w=max_w)
    figure_style = paragraph_style_ref("HB Figure")
    justification = ' Justification="CenterAlign"' if center else ""
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{figure_style}"'
        f'{justification}>\n'
        '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        + writer._image_cell_content(tid, image, width, height)
        + '<Content></Content><Br/></CharacterStyleRange>\n'
        '  </ParagraphStyleRange>\n'
    )


def _badge_text(number: int) -> str:
    style = paragraph_style_ref("HB InBox Label")
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style}" '
        'Justification="CenterAlign">\n'
        '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        'FillColor="Color/Paper" PointSize="10.912" FontStyle="Medium" '
        'BaselineShift="0.45">'
        f'<Content>{number}</Content></CharacterStyleRange>\n'
        '  </ParagraphStyleRange>\n'
    )


def _fcc_text_story(writer, sid: str, title: str, text: str) -> str:
    return _story(
        writer,
        sid,
        title,
        [writer._psr("HB FCC Text", text.strip(), terminal=True)],
    )


def _fcc_lead_and_body(text: str) -> tuple[str, str]:
    """Keep the preamble and both conditions beside the FCC mark.

    In the approved document the full opening, including conditions (1) and
    (2), occupies the narrow frame beside the mark.  The full-width left frame
    starts at the localized NOTE/REMARQUE/NOTA paragraph.  Splitting at (1)
    made the lower frame one paragraph too long and caused a real InDesign
    overset on page 6.
    """
    folded = text.casefold()
    markers = [
        index
        for token in (
            "**note:", "**remarque :", "**remarque:", "**nota:",
            "note:", "remarque :", "remarque:", "nota:",
        )
        if (index := folded.find(token)) >= 40
    ]
    if not markers:
        return "", text.strip()
    marker = min(markers)
    return text[:marker].strip(), text[marker:].strip()


def _fcc_text_frame_geometry(lang: str) -> tuple[float, float, float]:
    """Return lead width/height and the lower-copy top offset.

    The localized reference pages preserve the FCC mark size but give the
    longer FR/ES condition copy more room beside it.  The lower NOTE frame
    overlaps the lead frame by two points, matching the English shell while
    keeping both stories independent and editable.
    """
    language = lang.strip().casefold().replace("_", "-").split("-", 1)[0]
    lead_width = 103.0 if language in {"fr", "es"} else 97.0
    lead_height = {"fr": 62.0, "es": 56.0}.get(language, 50.0)
    return lead_width, lead_height, lead_height + 6.0


def _card_story(writer, sid: str, item: dict, bundle_root: Path,
                max_image_w: float) -> str:
    parts: list[str] = []
    image = writer._resolve_bundle_image(bundle_root, item.get("img", ""))
    if image is not None:
        parts.append(_image_paragraph(writer, f"{sid}_img", image, max_image_w))
    parts.append(writer._psr("HB InBox Label", item.get("label", ""), terminal=True))
    return _story(writer, sid, "Inbox card", parts)


def _tip_label(label: str, *, point_size: float, leading: float,
               baseline_shift: float) -> str:
    return writer_psr_template(
        "HB Callout Label",
        label.strip(),
        character_attrs=(
            f'PointSize="{point_size:g}" Leading="{leading:g}" '
            f'FontStyle="Bold" BaselineShift="{baseline_shift:g}"'
        ),
    )


def writer_psr_template(style: str, text: str, *,
                        character_attrs: str = "") -> str:
    style_ref = paragraph_style_ref(style)
    attrs = f" {character_attrs}" if character_attrs else ""
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}" '
        'Justification="CenterAlign">\n'
        '    <CharacterStyleRange '
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"'
        f'{attrs}>'
        f'<Content>{escape(text)}</Content></CharacterStyleRange>\n'
        '  </ParagraphStyleRange>\n'
    )


def _spread_page(writer, spread_id: str, page_no: int) -> str:
    return (
        f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} {-writer.page_h / 2:g}">\n'
        '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
        f'Top="{writer.m_t:g}" Bottom="{writer.m_b:g}" '
        f'Left="{writer.m_l:g}" Right="{writer.m_r:g}"/>\n'
        '  </Page>\n'
    )


def _fcc_objects(
    writer,
    sid: str,
    fcc_blocks: list[tuple[str, str]],
    bundle_root: Path,
    *,
    panel_y: float = 28.0,
    panel_h: float = 138.0,
    lang: str = "en",
) -> tuple[list[str], list[str]]:
    spec = fcc_spec_from_blocks(fcc_blocks)
    texts = ((spec.get("texts") or []) + ["", ""])[:2]
    # The cropped PDF carries out-of-page legacy text in its content stream.
    # InDesign clips it visually but re-exposes that hidden text on PDF export.
    # Use the clean transparent raster derivative for the decorative mark so
    # searchable text remains exclusively sourced from the RST/IR stories.
    mark = ROOT / "docs" / "renderers" / "latex" / "assets" / "fcc_mark.png"
    mark_sid = f"{sid}_fcc_mark"
    if mark.exists():
        _story(
            writer,
            mark_sid,
            "FCC mark",
            [_image_paragraph(writer, f"{mark_sid}_image", mark, 39.5)],
        )
    lead_text, left_text = _fcc_lead_and_body(texts[0])
    lead_sid = f"{sid}_fcc_lead"
    if lead_text:
        _fcc_text_story(writer, lead_sid, "FCC notice lead", lead_text)
    left_sid = f"{sid}_fcc_left"
    right_sid = f"{sid}_fcc_right"
    _fcc_text_story(writer, left_sid, "FCC notice left", left_text)
    _fcc_text_story(writer, right_sid, "FCC notice right", texts[1])
    bg = page_rectangle_xml(
        writer,
        f"bg_{sid}_fcc_panel",
        (BODY_X, panel_y, BODY_W, panel_h),
        fill="Color/HB Bg K05",
        stroke_color="Swatch/None",
        stroke_weight=0,
        object_style=PANEL_OBJECT_STYLE,
    )
    frames = [bg]
    story_ids = [left_sid, right_sid]
    if mark.exists():
        story_ids.append(mark_sid)
        frames.append(frame_with_background(
            writer,
            sid,
            "fcc_mark",
            mark_sid,
            (BODY_X + 6.0, panel_y + 7.0, 42.0, 34.0),
            {"inset": (0, 0, 0, 0), "valign": "CenterAlign"},
        ))
    if lead_text:
        story_ids.append(lead_sid)
        lead_w, lead_h, left_y_offset = _fcc_text_frame_geometry(lang)
        frames.append(frame_with_background(
            writer,
            sid,
            "fcc_lead",
            lead_sid,
            (BODY_X + 52.0, panel_y + 8.0, lead_w, lead_h),
            {"inset": (0, 0, 0, 0)},
        ))
    else:
        left_y_offset = 56.0
    frames.extend([
        frame_with_background(
            writer,
            sid,
            "fcc_left",
            left_sid,
            (
                BODY_X + 6.4,
                panel_y + left_y_offset,
                150.0,
                panel_h - left_y_offset,
            ),
            {"inset": (0, 0, 0, 0)},
        ),
        frame_with_background(
            writer,
            sid,
            "fcc_right",
            right_sid,
            (
                BODY_X + 166.8,
                panel_y + 8.0,
                BODY_W - 172.8,
                panel_h - 8.0,
            ),
            {"inset": (0, 0, 0, 0)},
        ),
    ])
    return story_ids, frames


def _symbol_continuation_objects(
    writer,
    sid: str,
    symbol_overflow: tuple[list[dict], list[dict]] | None,
    lang: str,
) -> tuple[list[str], list[str]]:
    if not symbol_overflow or not any(symbol_overflow):
        return [], []
    left_rows, right_rows = symbol_overflow
    table_gap = 7.0
    table_w = (BODY_W - table_gap) / 2.0
    table_y = 25.0 if lang == "es" else 20.0
    table_h = 68.0
    story_ids: list[str] = []
    frames: list[str] = []
    for side, rows, x in (
        ("left", left_rows, BODY_X),
        ("right", right_rows, BODY_X + table_w + table_gap),
    ):
        if not rows:
            continue
        story_id = f"{sid}_symbols_{side}"
        table = writer._symbols_icon_table(
            f"{sid}_symbols_{side}_tbl",
            rows,
            table_w,
            lang,
            include_header=False,
            row_heights=[table_h / len(rows)] * len(rows),
        )
        writer._table_story(story_id, f"Symbol icons continuation {side}", table)
        story_ids.append(story_id)
        frames.append(frame_with_background(
            writer,
            sid,
            f"symbols_{side}",
            story_id,
            (x, table_y, table_w, table_h),
            with_rounded_outer({"inset": (0, 0, 0, 0)}),
        ))
    return story_ids, frames


def _inbox_objects(writer, sid: str, inbox_spec: dict | None,
                   bundle_root: Path, *, lang: str = "en",
                   overflow_profile: bool = False) -> tuple[list[str], list[str]]:
    if not inbox_spec:
        return [], []
    items = inbox_spec.get("items", [])[:3]
    language = lang.strip().casefold().replace("_", "-").split("-", 1)[0]
    profile = "overflow_" if overflow_profile else ""
    def metric(name: str, fallback: float) -> float:
        base_key = f"idml_inbox_{profile}{name}"
        return param_pt(
            writer.params,
            f"lang_{language}_{base_key}",
            param_pt(writer.params, base_key, fallback),
        )

    card_w = 99.5
    card_h = metric("card_height", 172.5)
    card_y = metric("card_y", 273.0)
    card_xs = (BODY_X, 132.5, 238.0)
    image_ws = (
        metric("image_1_width", 72.0),
        metric("image_2_width", 60.0),
        metric("image_3_width", 58.0),
    )
    story_ids: list[str] = []
    frames: list[str] = []
    for idx, item in enumerate(items):
        x = card_xs[idx]
        frames.append(page_rectangle_xml(
            writer,
            f"bg_{sid}_card_{idx + 1}",
            (x, card_y, card_w, card_h),
            fill="Color/Paper",
            stroke_color="Color/HB Line K40",
            stroke_weight=0.75,
            object_style=CARD_OBJECT_STYLE,
        ))
        badge_rect = (
            x + card_w / 2.0 - BADGE_DIAMETER / 2.0,
            card_y + BADGE_Y_OFFSET,
            BADGE_DIAMETER,
            BADGE_DIAMETER,
        )
        frames.append(page_rectangle_xml(
            writer,
            f"bg_{sid}_badge_{idx + 1}",
            badge_rect,
            fill="Color/HB Brand Dark",
            stroke_color="Swatch/None",
            stroke_weight=0,
            corner_radius=BADGE_DIAMETER / 2.0,
            object_style=BADGE_OBJECT_STYLE,
        ))
        badge_sid = f"{sid}_badge_{idx + 1}"
        _story(writer, badge_sid, f"Inbox badge {idx + 1}", [_badge_text(idx + 1)])
        story_ids.append(badge_sid)
        frames.append(frame_with_background(
            writer,
            sid,
            f"badge_{idx + 1}",
            badge_sid,
            badge_rect,
            {"inset": (0, 0, 0, 0), "valign": "CenterAlign"},
        ))

        card_sid = f"{sid}_card_{idx + 1}"
        _card_story(writer, card_sid, item, bundle_root, image_ws[idx])
        story_ids.append(card_sid)
        frames.append(frame_with_background(
            writer,
            sid,
            f"card_{idx + 1}",
            card_sid,
            (x + 8.0, card_y + 36.0, card_w - 16.0, card_h - 44.5),
            {"inset": (0, 0, 0, 0), "valign": "CenterAlign"},
        ))
    return story_ids, frames


def _tip_objects(writer, sid: str,
                 tip_spec: dict | None, *, lang: str = "en",
                 overflow_profile: bool = False) -> tuple[list[str], list[str]]:
    if not tip_spec:
        return [], []
    label = source_notice_label(tip_spec)
    texts = [str(t).strip() for t in tip_spec.get("texts", []) if str(t).strip()]
    body = "\n".join(texts)
    layout = notice_box_layout(
        writer.params,
        BODY_W,
        label,
        texts,
        variant=str(tip_spec.get("variant", "")),
    )
    language = lang.strip().casefold().replace("_", "-").split("-", 1)[0]
    profile = "overflow_" if overflow_profile else ""
    base_key = f"idml_inbox_{profile}tip_y"
    tip_y = param_pt(
        writer.params,
        f"lang_{language}_{base_key}",
        param_pt(writer.params, base_key, 458.0),
    )
    tip_rect = (BODY_X, tip_y, BODY_W, layout.panel_height)
    plate_rect = (
        BODY_X + layout.plate_left,
        tip_rect[1] + layout.plate_left,
        layout.plate_width,
        tip_rect[3] - 2 * layout.plate_left,
    )
    body_x = BODY_X + layout.plate_left + layout.plate_width + layout.body_inset
    body_rect = (
        body_x,
        tip_rect[1] + layout.pad_tb,
        BODY_X + BODY_W - layout.right_inset - body_x,
        tip_rect[3] - 2 * layout.pad_tb,
    )
    label_sid = f"{sid}_tip_label"
    body_sid = f"{sid}_tip_body"
    _story(writer, label_sid, "Inbox tip label", [_tip_label(
        label,
        point_size=layout.label_size,
        leading=layout.label_leading,
        baseline_shift=layout.label_baseline_shift,
    )])
    body_xml = writer._psr("HB Callout Body", body, terminal=True).replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'PointSize="{layout.body_size:g}" Leading="{layout.body_leading:g}" '
        f'FontStyle="Medium" '
        f'HorizontalScale="{layout.body_horizontal_scale * 100:g}" '
        f'BaselineShift="{layout.body_baseline_shift:g}"',
        1,
    )
    _story(writer, body_sid, "Inbox tip body", [body_xml])
    frames = [
        page_rectangle_xml(
            writer,
            f"bg_{sid}_tip_strip",
            tip_rect,
            fill="Color/HB Bg K05",
            stroke_color="Swatch/None",
            stroke_weight=0,
            corner_radius=layout.arc,
            object_style=PANEL_OBJECT_STYLE,
        ),
        left_rounded_xml(
            writer,
            f"bg_{sid}_tip_label",
            plate_rect,
            fill="Color/Paper",
            corner_radius=max(0.0, layout.arc - layout.plate_left / 2.0),
            object_style=PANEL_OBJECT_STYLE,
        ),
        frame_with_background(
            writer,
            sid,
            "tip_label",
            label_sid,
            plate_rect,
            {"inset": (0, 0, 0, 1.0), "valign": "CenterAlign"},
        ),
        frame_with_background(
            writer,
            sid,
            "tip_body",
            body_sid,
            body_rect,
            {"inset": (0, 0, 0, 0), "valign": "CenterAlign"},
        ),
    ]
    return [label_sid, body_sid], frames


def add_fcc_inbox_page(
    writer,
    sid: str,
    fcc_blocks: list[tuple[str, str]],
    inbox_blocks: list[tuple[str, str]],
    bundle_root: Path,
    page_index: int,
    *,
    symbol_overflow: tuple[list[dict], list[dict]] | None = None,
    lang: str = "en",
) -> str:
    """V2.0 page 03: FCC panel, inbox card trio, and tip strip."""
    inbox_title = next((text.strip() for kind, text in inbox_blocks
                        if kind == "h1" and text.strip()), "")
    if not inbox_title:
        raise ValueError("inbox title is required from source RST")
    inbox_spec = component_spec(inbox_blocks, "inbox")
    tip_spec = component_spec(inbox_blocks, "notice")

    title_sid = f"{sid}_title"
    _story(writer, title_sid, "Inbox title",
           [heading_text(writer, inbox_title, level=1)])
    _, symbol_frames = _symbol_continuation_objects(
        writer,
        sid,
        symbol_overflow,
        lang,
    )
    has_symbol_overflow = bool(symbol_frames)
    if has_symbol_overflow:
        fcc_y = 98.0 if lang == "es" else 95.0
        fcc_h = 148.0 if lang == "es" else 145.0
    else:
        fcc_y = 28.0
        fcc_h = 130.0
    _, fcc_frames = _fcc_objects(
        writer,
        sid,
        fcc_blocks,
        bundle_root,
        panel_y=fcc_y,
        panel_h=fcc_h,
        lang=lang,
    )
    _, card_frames = _inbox_objects(
        writer,
        sid,
        inbox_spec,
        bundle_root,
        lang=lang,
        overflow_profile=has_symbol_overflow,
    )
    _, tip_frames = _tip_objects(
        writer,
        sid,
        tip_spec,
        lang=lang,
        overflow_profile=has_symbol_overflow,
    )
    title_y = 245.0
    if has_symbol_overflow:
        language = lang.strip().casefold().replace("_", "-").split("-", 1)[0]
        title_y = param_pt(
            writer.params,
            f"lang_{language}_idml_fcc_inbox_overflow_title_y",
            param_pt(writer.params, "idml_fcc_inbox_overflow_title_y", title_y),
        )

    frames = [
        *symbol_frames,
        *fcc_frames,
        frame_with_background(
            writer,
            sid,
            "title",
            title_sid,
            (BODY_X, title_y, BODY_W, H1_BAR_H),
            {**heading_bar_opts(1, (1.5, 5, 1, 6)),
             "text_rect": (
                 BODY_X + 6.4,
                 title_y - 1.96,
                 BODY_W - 12.8,
                 H1_BAR_H,
             )},
        ),
        *card_frames,
        *tip_frames,
    ]

    spread_id = f"sp_{page_index}"
    page_no = page_index + 1
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
        + _spread_page(writer, spread_id, page_no)
        + "".join(frames) +
        '</Spread>\n'
        '</idPkg:Spread>\n'
    )
    writer.spreads.append((spread_id, xml))
    return spread_id
