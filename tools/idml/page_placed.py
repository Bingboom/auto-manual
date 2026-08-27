"""Full-page placed-PDF cover and editable back-cover composition.

Production IDML may place the cover as finished art. Body pages and the back
cover stay native so their copy, tables, and components remain editable in
InDesign; in particular, the LaTeX-only ``product_overview-<lang>.pdf`` and
``back_cover-<lang>.pdf`` assets must never become production IDML links.
"""
from __future__ import annotations

import sys
from pathlib import Path
import re
import math
from xml.sax.saxutils import escape

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:  # export_idml.py runs as a direct script
    sys.path.insert(0, _REPO_ROOT)

from tools.utils.path_utils import latex_renderer_of

from .params import IDPKG

_ATTR = {'"': "&quot;"}


def _cover_model_slug(model: str | None) -> str:
    """Return the filename slug used by model-bound finished cover art."""
    return re.sub(r"[^a-z0-9]+", "", (model or "").lower())


def placed_asset_for(
    page_stem: str,
    lang: str,
    docs_dir: Path,
    *,
    model: str | None = None,
) -> Path | None:
    """Resolve the production-approved full-page asset, if any.

    Only the cover is allowed to use a full-page placed PDF. Product overview
    pages deliberately fall through to the editable prose/component composer,
    and the back cover is composed from its source-authored semantic payload.
    """
    assets_dir = latex_renderer_of(docs_dir) / "assets"
    lang = (lang or "en").lower()
    if page_stem.startswith("cover"):
        model_slug = _cover_model_slug(model)
        candidates: list[str] = []

        def add_candidate(name: str) -> None:
            if name not in candidates:
                candidates.append(name)

        if model_slug:
            add_candidate(f"cover_{model_slug}-{lang}.pdf")

        # The unscoped ``cover-<lang>.pdf`` files predate model-bound cover
        # names and belong to JE-1000F.  Keep that compatibility only for the
        # owning model (and old callers without model context); otherwise a
        # missing target cover must not silently place another product.
        if not model_slug or model_slug == "je1000f":
            add_candidate(f"cover-{lang}.pdf")

        if model_slug and lang != "en":
            add_candidate(f"cover_{model_slug}-en.pdf")
        if (not model_slug or model_slug == "je1000f") and lang != "en":
            add_candidate("cover-en.pdf")
    else:
        return None
    for name in candidates:
        path = assets_dir / name
        if path.is_file():
            return path
    return None


def add_placed_pdf_page(writer, sid: str, asset: Path, page_index: int) -> str:
    """One spread holding a single full-bleed rectangle linked to a PDF."""
    w, h = writer.page_w, writer.page_h
    x1, y1, x2, y2 = -w / 2, -h / 2, w / 2, h / 2
    pts = ((x1, y1), (x1, y2), (x2, y2), (x2, y1))
    anchors = "".join(
        f'<PathPointType Anchor="{x:g} {y:g}" LeftDirection="{x:g} {y:g}" '
        f'RightDirection="{x:g} {y:g}"/>' for x, y in pts
    )
    uri = escape(asset.resolve().as_uri(), _ATTR)
    spread_id = f"sp_{page_index}"
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
        f'  <Page Self="{spread_id}_pg" Name="{page_index + 1}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {h:g} {w:g}" '
        f'ItemTransform="1 0 0 1 {-w / 2:g} {-h / 2:g}"/>\n'
        f'  <Rectangle Self="rc_{sid}" ContentType="GraphicType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">\n'
        '    <Properties><PathGeometry><GeometryPathType PathOpen="false">'
        f'<PathPointArray>{anchors}</PathPointArray>'
        '</GeometryPathType></PathGeometry></Properties>\n'
        f'    <Image Self="rc_{sid}_img" ItemTransform="1 0 0 1 {x1:g} {y1:g}">\n'
        f'      <Link Self="rc_{sid}_lnk" LinkResourceURI="{uri}"/>\n'
        '    </Image>\n'
        '    <FrameFittingOption FittingOnEmptyFrame="Proportionally"/>\n'
        '  </Rectangle>\n'
        '</Spread>\n'
        '</idPkg:Spread>\n'
    )
    writer.spreads.append((spread_id, xml))
    return spread_id


# Approved back-cover fallback for bundles that predate the semantic payload.
# This exception is page-role scoped and must not be reused by body renderers.
_BACK_COVER_COPY = {
    "US": {
        "company": "JACKERY INC.",
        "address": "5310 Bunche Dr., Fremont, CA 94538-8301",
        "phone": "1-888-502-2236 (US)",
        "lines": "hello@jackery.com\nwww.jackery.com",
    },
}

_JBP_US_BACK_COVER_PROFILE = {
    "qr_asset": "docs/renderers/latex/assets/back_cover_qr_jbp2000b.pdf",
    "display_address": "5310 Bunche Dr., Fremont, CA 94538-8301",
    "phone_suffix": "(US)",
    "contact_lines": "hello@jackery.com\nwww.jackery.com",
    "company_x": 28.096,
    "company_y": 430.5,
    "address_y": 446.2,
    "bar_x": 28.8,
    "bar_y": 461.2,
    "bar_width": 272.2,
    "bar_height": 36.8,
    "bar_stroke_weight": 0.35,
    "bar_corner_radius": 5.5,
    "phone_x": 60.298,
    "phone_y": 468.6,
    "phone_width": 137.0,
    "phone_height": 21.0,
    "divider_x": 199.5,
    "lines_x": 224.691,
    "lines_y": 467.7,
    "lines_width": 69.0,
    "lines_height": 23.0,
    "qr_x": 305.6,
    "qr_y": 460.4,
    "qr_size": 37.2,
    "qr_art_size": 30.0,
    "qr_stroke_weight": 0.35,
    "qr_corner_radius": 5.5,
}


def _add_qr_only_back_cover_page(
    writer,
    page_index: int,
    profile: dict,
    docs_dir: Path | None,
) -> bool:
    """Place the target-owned QR on an otherwise blank native back cover."""
    if docs_dir is None:
        raise ValueError("qr_only back cover requires a docs directory")
    qr_asset = str(profile.get("qr_asset") or "").strip()
    asset = docs_dir.parent / qr_asset
    if not qr_asset or not asset.is_file():
        raise ValueError(f"back-cover QR asset is missing: {asset}")
    qr_rect = profile.get("qr_rect")
    if not isinstance(qr_rect, list) or len(qr_rect) != 4:
        raise ValueError("qr_only back cover requires qr_rect")
    qr_x, qr_y, qr_w, qr_h = (float(value) for value in qr_rect)
    x1, y1, x2, y2 = writer._page_rect(qr_x, qr_y, qr_w, qr_h)
    frame = (
        '  <Rectangle Self="rc_st_back_cover_qr_only" ContentType="GraphicType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + writer._path_geometry(x1, y1, x2, y2)
        + f'    <Image Self="rc_st_back_cover_qr_only_img" '
        f'ItemTransform="1 0 0 1 {x1:g} {y1:g}">\n'
        f'      <Link Self="rc_st_back_cover_qr_only_lnk" '
        f'LinkResourceURI="{escape(asset.resolve().as_uri(), _ATTR)}"/>\n'
        '    </Image>\n'
        '    <FrameFittingOption FittingOnEmptyFrame="Proportionally" '
        'FittingAlignment="CenterAnchor" AutoFit="true"/>\n'
        '  </Rectangle>\n'
    )
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
        f'{-writer.page_h / 2:g}"/>\n'
        + frame
        + '</Spread>\n</idPkg:Spread>\n',
    ))
    return True


def _add_legacy_back_cover_page(
    writer, region: str, page_index: int, copy: dict[str, str] | None = None,
) -> bool:
    """Keep the established generic back cover unchanged without a profile."""
    copy = copy or _BACK_COVER_COPY.get(region)
    if copy is None:
        return False
    from . import page_objects as _po

    body_x = 27.4
    body_w = writer.page_w - body_x * 2
    sid = "st_back_cover"
    company_sid = writer._add_story_parts(
        f"{sid}_company", "Back cover company",
        [writer._psr("HB Title L2", copy["company"]),
         writer._psr("HB Body", copy["address"], terminal=True)])
    phone_sid = writer._add_story_parts(
        f"{sid}_phone", "Back cover phone",
        [writer._psr("HB Spec Section", copy["phone"], terminal=True)])
    lines = copy.get("lines", "") or "\n".join(filter(None, (
        copy.get("email", ""),
        copy.get("web", ""),
    )))
    lines_sid = (writer._add_story_parts(
        f"{sid}_lines", "Back cover contact lines",
        [writer._psr("HB Body", lines, terminal=True)]) if lines else None)

    bar_y = writer.page_h - writer.m_b - 30.0
    bar_h = 27.0
    frames = [
        _po.rounded_outer_xml(writer, f"bg_{sid}_bar",
                              (body_x, bar_y, body_w * 0.62, bar_h)),
        writer._frame_xml(f"tf_{sid}_company", company_sid,
                          *writer._page_rect(body_x, bar_y - 34.0, body_w, 26.0),
                          inset=(0, 0, 0, 0)),
        writer._frame_xml(f"tf_{sid}_phone", phone_sid,
                          *writer._page_rect(body_x + 8.0, bar_y + 7.0,
                                             body_w * 0.34, 14.0),
                          inset=(0, 0, 0, 0)),
    ]
    if lines_sid:
        frames.append(writer._frame_xml(
            f"tf_{sid}_lines", lines_sid,
            *writer._page_rect(body_x + 8.0 + body_w * 0.36,
                               bar_y + 3.0, body_w * 0.24, 20.0),
            inset=(0, 0, 0, 0)))
    spread_id = f"sp_{page_index}"
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
        f'  <Page Self="{spread_id}_pg" Name="{page_index + 1}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} {-writer.page_h / 2:g}"/>\n'
        + "".join(frames) +
        '</Spread>\n'
        '</idPkg:Spread>\n'
    )
    writer.spreads.append((spread_id, xml))
    return True


def add_back_cover_page(
    writer, region: str, page_index: int, copy: dict[str, str] | None = None,
    *, profile: dict | None = None, docs_dir: Path | None = None,
) -> bool:
    """Compose the template's back page: company block + contact bar."""
    if profile is not None and profile.get("variant") == "qr_only":
        return _add_qr_only_back_cover_page(
            writer,
            page_index,
            profile,
            docs_dir,
        )
    if profile is None:
        return _add_legacy_back_cover_page(writer, region, page_index, copy)
    copy = copy or _BACK_COVER_COPY.get(region)
    if copy is None:
        return False
    from . import page_objects as _po

    body_x = float(profile.get("company_x", 27.4))
    body_w = writer.page_w - body_x * 2
    sid = "st_back_cover"
    def sized_psr(style: str, text: str, size: float, leading: float,
                  *, bold: bool = False, terminal: bool = True) -> str:
        xml = writer._psr(style, text, terminal=terminal)
        attrs = f'PointSize="{size:g}" Leading="{leading:g}"'
        if bold:
            attrs += ' FontStyle="Bold"'
        return xml.replace(
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            + attrs,
            1,
        )

    company_sid = writer._add_story_parts(
        f"{sid}_company", "Back cover company",
        [sized_psr("HB Title L2", copy["company"], 12.0, 14.5,
                   bold=True)])
    address_sid = writer._add_story_parts(
        f"{sid}_address", "Back cover address",
        [sized_psr(
            "HB Body",
            str(profile.get("display_address") or copy["address"]),
            8.0,
            10.0,
        )])
    phone_match = re.fullmatch(r"\s*(.*?)\s*(\(US\))\s*", copy["phone"])
    phone_number = phone_match.group(1) if phone_match else copy["phone"]
    phone_suffix = str(
        profile.get("phone_suffix")
        or (phone_match.group(2) if phone_match else "")
    )
    phone_sid = writer._add_story_parts(
        f"{sid}_phone", "Back cover phone",
        [sized_psr("HB Spec Section", phone_number, 15.415, 18.5, bold=True)])
    phone_suffix_sid = (writer._add_story_parts(
        f"{sid}_phone_suffix", "Back cover phone suffix",
        [sized_psr("HB Body", phone_suffix, 8.0, 10.0)]) if phone_suffix else None)
    lines = str(profile.get("contact_lines") or "") or copy.get("lines", "") or "\n".join(filter(None, (
        copy.get("email", ""),
        copy.get("web", ""),
    )))
    lines_sid = (writer._add_story_parts(
        f"{sid}_lines", "Back cover contact lines",
        [sized_psr("HB Body", lines, 8.005, 10.8)]) if lines else None)

    company_y = float(profile.get("company_y", writer.page_h - writer.m_b - 64.0))
    bar_x = float(profile.get("bar_x", body_x))
    bar_y = float(profile.get("bar_y", writer.page_h - writer.m_b - 30.0))
    bar_w = float(profile.get("bar_width", body_w * 0.62))
    bar_h = float(profile.get("bar_height", 27.0))
    frames = [
        _po.page_rectangle_xml(
            writer, f"bg_{sid}_bar", (bar_x, bar_y, bar_w, bar_h),
            fill="Color/Paper", stroke_color="Color/HB Line K40",
            stroke_weight=float(profile.get("bar_stroke_weight", 0.35)),
            corner_radius=float(profile.get("bar_corner_radius", 5.5)),
        ),
        writer._frame_xml(f"tf_{sid}_company", company_sid,
                          *writer._page_rect(body_x, company_y, body_w, 16.0),
                          inset=(0, 0, 0, 0)),
        writer._frame_xml(f"tf_{sid}_address", address_sid,
                          *writer._page_rect(
                              body_x,
                              float(profile.get("address_y", company_y + 15.7)),
                              body_w,
                              12.0,
                          ),
                          inset=(0, 0, 0, 0)),
        writer._frame_xml(f"tf_{sid}_phone", phone_sid,
                          *writer._page_rect(
                              float(profile.get("phone_x", bar_x + 8.0)),
                              float(profile.get("phone_y", bar_y + 7.0)),
                              float(profile.get("phone_width", body_w * 0.34)),
                              float(profile.get("phone_height", 20.0))),
                          inset=(0, 0, 0, 0)),
    ]
    if phone_suffix_sid:
        frames.append(writer._frame_xml(
            f"tf_{sid}_phone_suffix", phone_suffix_sid,
            *writer._page_rect(
                float(profile.get("phone_suffix_x", 179.374)),
                float(profile.get("phone_suffix_y", 476.3)), 24.0, 12.0),
            inset=(0, 0, 0, 0)))
    if lines_sid:
        frames.append(writer._frame_xml(
            f"tf_{sid}_lines", lines_sid,
            *writer._page_rect(
                float(profile.get("lines_x", bar_x + 195.9)),
                float(profile.get("lines_y", bar_y + 5.4)),
                float(profile.get("lines_width", 69.0)),
                float(profile.get("lines_height", 25.0))),
            inset=(0, 0, 0, 0)))
    divider_x = float(profile.get("divider_x", bar_x + 171.0))
    frames.append(
        f'  <GraphicLine Self="gl_{sid}_divider" ContentType="Unassigned" '
        'StrokeColor="Color/HB Line K40" StrokeWeight="0.35" '
        'ItemTransform="1 0 0 1 0 0">'
        '<Properties><PathGeometry><GeometryPathType PathOpen="true">'
        '<PathPointArray>'
        f'<PathPointType Anchor="{divider_x - writer.page_w / 2:g} '
        f'{bar_y + 8.5 - writer.page_h / 2:g}" LeftDirection="{divider_x - writer.page_w / 2:g} '
        f'{bar_y + 8.5 - writer.page_h / 2:g}" RightDirection="{divider_x - writer.page_w / 2:g} '
        f'{bar_y + 8.5 - writer.page_h / 2:g}"/>'
        f'<PathPointType Anchor="{divider_x - writer.page_w / 2:g} '
        f'{bar_y + bar_h - 8.5 - writer.page_h / 2:g}" LeftDirection="{divider_x - writer.page_w / 2:g} '
        f'{bar_y + bar_h - 8.5 - writer.page_h / 2:g}" RightDirection="{divider_x - writer.page_w / 2:g} '
        f'{bar_y + bar_h - 8.5 - writer.page_h / 2:g}"/>'
        '</PathPointArray></GeometryPathType></PathGeometry></Properties>'
        '</GraphicLine>\n'
    )
    def line_xml(name: str, points: list[tuple[float, float]], *,
                 closed: bool = False, weight: float = 0.75) -> str:
        anchors = "".join(
            f'<PathPointType Anchor="{x - writer.page_w / 2:g} '
            f'{y - writer.page_h / 2:g}" LeftDirection="{x - writer.page_w / 2:g} '
            f'{y - writer.page_h / 2:g}" RightDirection="{x - writer.page_w / 2:g} '
            f'{y - writer.page_h / 2:g}"/>'
            for x, y in points
        )
        path_open = "false" if closed else "true"
        return (
            f'  <GraphicLine Self="gl_{sid}_{name}" ContentType="Unassigned" '
            f'StrokeColor="Color/HB Brand Dark" StrokeWeight="{weight:g}" '
            'FillColor="Swatch/None" ItemTransform="1 0 0 1 0 0">'
            '<Properties><PathGeometry><GeometryPathType '
            f'PathOpen="{path_open}"><PathPointArray>{anchors}'
            '</PathPointArray></GeometryPathType></PathGeometry></Properties>'
            '</GraphicLine>\n'
        )

    phone_cx, phone_cy, phone_r = bar_x + 17.0, bar_y + 18.4, 9.0
    frames.append(line_xml(
        "phone_ring",
        [
            (
                phone_cx + phone_r * math.cos(2 * math.pi * i / 20),
                phone_cy + phone_r * math.sin(2 * math.pi * i / 20),
            )
            for i in range(20)
        ],
        closed=True,
        weight=0.8,
    ))
    frames.append(line_xml(
        "phone_handset",
        [
            (phone_cx - 3.8, phone_cy - 4.7),
            (phone_cx - 5.2, phone_cy - 2.8),
            (phone_cx - 3.2, phone_cy + 1.9),
            (phone_cx + 1.2, phone_cy + 5.1),
            (phone_cx + 4.0, phone_cy + 3.8),
        ],
        weight=2.3,
    ))
    mail_x, mail_y = bar_x + 181.0, bar_y + 9.0
    frames.extend((
        line_xml("mail_box", [
            (mail_x, mail_y), (mail_x + 9.0, mail_y),
            (mail_x + 9.0, mail_y + 6.0), (mail_x, mail_y + 6.0),
        ], closed=True, weight=0.65),
        line_xml("mail_fold", [
            (mail_x, mail_y), (mail_x + 4.5, mail_y + 3.2),
            (mail_x + 9.0, mail_y),
        ], weight=0.65),
    ))
    web_cx, web_cy, web_r = bar_x + 185.5, bar_y + 24.0, 4.5
    frames.extend((
        line_xml("web_ring", [
            (
                web_cx + web_r * math.cos(2 * math.pi * i / 16),
                web_cy + web_r * math.sin(2 * math.pi * i / 16),
            )
            for i in range(16)
        ], closed=True, weight=0.65),
        line_xml("web_equator", [
            (web_cx - web_r, web_cy), (web_cx + web_r, web_cy),
        ], weight=0.55),
        line_xml("web_meridian", [
            (web_cx, web_cy - web_r), (web_cx, web_cy + web_r),
        ], weight=0.55),
    ))
    qr_asset = str(profile.get("qr_asset") or "").strip()
    if qr_asset and docs_dir is not None:
        asset = docs_dir.parent / qr_asset
        if not asset.is_file():
            raise ValueError(f"back-cover QR asset is missing: {asset}")
        qr_x = float(profile.get("qr_x", bar_x + bar_w + 5.0))
        qr_y = float(profile.get("qr_y", bar_y))
        qr_size = float(profile.get("qr_size", bar_h))
        qr_art_size = float(profile.get("qr_art_size", qr_size))
        if qr_art_size <= 0 or qr_art_size > qr_size:
            raise ValueError("back-cover QR art size must be within its outer frame")
        frames.append(_po.page_rectangle_xml(
            writer,
            f"bg_{sid}_qr",
            (qr_x, qr_y, qr_size, qr_size),
            fill="Color/Paper",
            stroke_color="Color/HB Line K40",
            stroke_weight=float(profile.get("qr_stroke_weight", 0.35)),
            corner_radius=float(profile.get("qr_corner_radius", 5.5)),
        ))
        qr_art_x = qr_x + (qr_size - qr_art_size) / 2.0
        qr_art_y = qr_y + (qr_size - qr_art_size) / 2.0
        x1, y1, x2, y2 = writer._page_rect(
            qr_art_x, qr_art_y, qr_art_size, qr_art_size,
        )
        frames.append(
            f'  <Rectangle Self="rc_{sid}_qr" ContentType="GraphicType" '
            'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
            'StrokeColor="Swatch/None" StrokeWeight="0" '
            'ItemTransform="1 0 0 1 0 0">\n'
            + writer._path_geometry(x1, y1, x2, y2)
            + f'    <Image Self="rc_{sid}_qr_img" ItemTransform="1 0 0 1 {x1:g} {y1:g}">\n'
            f'      <Link Self="rc_{sid}_qr_lnk" LinkResourceURI="{escape(asset.resolve().as_uri(), _ATTR)}"/>\n'
            '    </Image>\n'
            '    <FrameFittingOption FittingOnEmptyFrame="Proportionally" '
            'FittingAlignment="CenterAnchor" AutoFit="true"/>\n'
            '  </Rectangle>\n'
        )
    spread_id = f"sp_{page_index}"
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
        f'  <Page Self="{spread_id}_pg" Name="{page_index + 1}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} {-writer.page_h / 2:g}"/>\n'
        + "".join(frames) +
        '</Spread>\n'
        '</idPkg:Spread>\n'
    )
    writer.spreads.append((spread_id, xml))
    return True


def add_preferred_back_cover_page(
    writer,
    region: str,
    lang: str,
    docs_dir: Path,
    page_index: int,
    copy: dict[str, str] | None = None,
    *,
    reference_plan: dict | None = None,
) -> bool:
    """Compose an editable back cover, even when LaTeX finished art exists."""
    profile = (
        ((reference_plan or {}).get("idml_contract") or {})
        .get("editable_components", {})
        .get("back_cover")
    )
    if (
        profile is None
        and _cover_model_slug(getattr(writer, "model", None)) == "jbp2000b"
        and region.upper() == "US"
    ):
        profile = _JBP_US_BACK_COVER_PROFILE
    return add_back_cover_page(
        writer, region, page_index, copy, profile=profile, docs_dir=docs_dir,
    )
