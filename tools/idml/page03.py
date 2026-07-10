"""V2.0 FCC + inbox composed page object rules."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

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
)
from .params import IDPKG
from .style_names import paragraph_style_ref

ROOT = Path(__file__).resolve().parents[2]
H1_BAR_H = 20.0
BODY_X = 26.5
BODY_W = 311.0


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
        'FillColor="Color/Paper" PointSize="7.4">'
        f'<Content>{number}</Content></CharacterStyleRange>\n'
        '  </ParagraphStyleRange>\n'
    )


def _fcc_text_story(writer, sid: str, title: str, text: str, *,
                    image: Path | None = None) -> str:
    parts: list[str] = []
    if image is not None and image.exists():
        parts.append(_image_paragraph(writer, f"{sid}_mark", image, 32.0, center=False))
    parts.append(writer._psr("HB Body", text.strip(), terminal=True))
    return _story(writer, sid, title, parts)


def _card_story(writer, sid: str, item: dict, bundle_root: Path,
                max_image_w: float) -> str:
    parts: list[str] = []
    image = writer._resolve_bundle_image(bundle_root, item.get("img", ""))
    if image is not None:
        parts.append(_image_paragraph(writer, f"{sid}_img", image, max_image_w))
    parts.append(writer._psr("HB InBox Label", item.get("label", ""), terminal=True))
    return _story(writer, sid, "Inbox card", parts)


def _tip_label(label: str) -> str:
    text = "TIPS" if label.strip().upper() == "TIP" else label.strip().upper()
    return (
        writer_psr_template("HB Notice Side Label", text)
    )


def writer_psr_template(style: str, text: str) -> str:
    style_ref = paragraph_style_ref(style)
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}" '
        'Justification="CenterAlign">\n'
        '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
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


def _fcc_objects(writer, sid: str, fcc_blocks: list[tuple[str, str]],
                 bundle_root: Path) -> tuple[list[str], list[str]]:
    spec = fcc_spec_from_blocks(fcc_blocks)
    texts = ((spec.get("texts") or []) + ["", ""])[:2]
    mark = ROOT / "docs" / "renderers" / "latex" / "assets" / "fcc_mark.pdf"
    left_sid = f"{sid}_fcc_left"
    right_sid = f"{sid}_fcc_right"
    _fcc_text_story(writer, left_sid, "FCC notice left", texts[0], image=mark)
    _fcc_text_story(writer, right_sid, "FCC notice right", texts[1])
    bg = page_rectangle_xml(
        writer,
        f"bg_{sid}_fcc_panel",
        (BODY_X, 28.0, BODY_W, 129.5),
        fill="Color/HB Bg K05",
        stroke_color="Swatch/None",
        stroke_weight=0,
        object_style=PANEL_OBJECT_STYLE,
    )
    frames = [
        bg,
        frame_with_background(
            writer,
            sid,
            "fcc_left",
            left_sid,
            (BODY_X + 4.0, 34.0, 145.0, 116.0),
            {"inset": (0, 0, 0, 0)},
        ),
        frame_with_background(
            writer,
            sid,
            "fcc_right",
            right_sid,
            (BODY_X + 156.0, 34.0, BODY_W - 162.0, 116.0),
            {"inset": (0, 0, 0, 0)},
        ),
    ]
    return [left_sid, right_sid], frames


def _inbox_objects(writer, sid: str, inbox_spec: dict | None,
                   bundle_root: Path) -> tuple[list[str], list[str]]:
    if not inbox_spec:
        return [], []
    items = inbox_spec.get("items", [])[:3]
    card_w = 99.5
    card_h = 172.5
    card_y = 273.0
    card_xs = (BODY_X, 132.5, 238.0)
    image_ws = (72.0, 60.0, 58.0)
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
        badge_rect = (x + card_w / 2.0 - 6.75, card_y + 21.0, 13.5, 13.5)
        frames.append(page_rectangle_xml(
            writer,
            f"bg_{sid}_badge_{idx + 1}",
            badge_rect,
            fill="Color/HB Brand Dark",
            stroke_color="Swatch/None",
            stroke_weight=0,
            corner_radius=6.75,
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
            (badge_rect[0], badge_rect[1] - 0.2, badge_rect[2], badge_rect[3]),
            {"inset": (1.4, 0, 0, 0)},
        ))

        card_sid = f"{sid}_card_{idx + 1}"
        _card_story(writer, card_sid, item, bundle_root, image_ws[idx])
        story_ids.append(card_sid)
        frames.append(frame_with_background(
            writer,
            sid,
            f"card_{idx + 1}",
            card_sid,
            (x + 8.0, card_y + 37.0, card_w - 16.0, 125.5),
            {"inset": (0, 0, 0, 0)},
        ))
    return story_ids, frames


def _tip_objects(writer, sid: str,
                 tip_spec: dict | None) -> tuple[list[str], list[str]]:
    if not tip_spec:
        return [], []
    label = str(tip_spec.get("label", "TIP"))
    body = "\n".join(str(t).strip() for t in tip_spec.get("texts", []) if str(t).strip())
    tip_rect = (BODY_X, 453.5, BODY_W, 42.0)
    label_w = 52.0
    label_sid = f"{sid}_tip_label"
    body_sid = f"{sid}_tip_body"
    _story(writer, label_sid, "Inbox tip label", [_tip_label(label)])
    _story(writer, body_sid, "Inbox tip body", [writer._psr("HB Body", body, terminal=True)])
    frames = [
        page_rectangle_xml(
            writer,
            f"bg_{sid}_tip_strip",
            tip_rect,
            fill="Color/HB Bg K05",
            stroke_color="Swatch/None",
            stroke_weight=0,
            object_style=PANEL_OBJECT_STYLE,
        ),
        left_rounded_xml(
            writer,
            f"bg_{sid}_tip_label",
            (BODY_X, tip_rect[1], label_w, tip_rect[3]),
            fill="Color/Paper",
        ),
        frame_with_background(
            writer,
            sid,
            "tip_label",
            label_sid,
            (BODY_X, tip_rect[1], label_w, tip_rect[3]),
            {"inset": (15.0, 2.0, 0, 2.0)},
        ),
        frame_with_background(
            writer,
            sid,
            "tip_body",
            body_sid,
            (BODY_X + label_w, tip_rect[1], BODY_W - label_w, tip_rect[3]),
            {"inset": (12.0, 7.0, 0, 7.0)},
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
) -> str:
    """V2.0 page 03: FCC panel, inbox card trio, and tip strip."""
    inbox_title = next((text for kind, text in inbox_blocks if kind == "h1"),
                       "WHAT'S IN THE BOX")
    inbox_spec = component_spec(inbox_blocks, "inbox")
    tip_spec = component_spec(inbox_blocks, "notice")

    title_sid = f"{sid}_title"
    _story(writer, title_sid, "Inbox title",
           [heading_text(writer, inbox_title, level=1)])
    _, fcc_frames = _fcc_objects(writer, sid, fcc_blocks, bundle_root)
    _, card_frames = _inbox_objects(writer, sid, inbox_spec, bundle_root)
    _, tip_frames = _tip_objects(writer, sid, tip_spec)

    frames = [
        *fcc_frames,
        frame_with_background(
            writer,
            sid,
            "title",
            title_sid,
            (BODY_X, 245.0, BODY_W, H1_BAR_H),
            heading_bar_opts(1, (1.5, 5, 1, 6)),
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
