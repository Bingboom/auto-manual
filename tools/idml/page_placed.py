"""Full-page placed-PDF spreads (cover and product overview).

The LaTeX pipeline ships these pages as finished art via ``\\includepdf``
(``docs/renderers/latex/assets/cover-en.pdf``,
``product_overview-<lang>.pdf``); composing them from parts would only
drift from the master. Place the same asset as a full-bleed linked
graphic so InDesign shows the identical page and the delivery packager
collects the PDF into ``Links/`` like any other asset.
"""
from __future__ import annotations

import sys
from pathlib import Path
from xml.sax.saxutils import escape

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:  # export_idml.py runs as a direct script
    sys.path.insert(0, _REPO_ROOT)

from tools.utils.path_utils import latex_renderer_of

from .params import IDPKG

_ATTR = {'"': "&quot;"}


def placed_asset_for(page_stem: str, lang: str, docs_dir: Path) -> Path | None:
    """Resolve the finished-art PDF for a bundle page, if any."""
    assets_dir = latex_renderer_of(docs_dir) / "assets"
    lang = (lang or "en").lower()
    if page_stem.startswith("cover"):
        candidates = [f"cover-{lang}.pdf", "cover-en.pdf"]
    elif "03_product_overview" in page_stem:
        candidates = [f"product_overview-{lang}.pdf", "product_overview-en.pdf"]
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


# Temporary composed back cover, pending a finished-art asset
# (back_cover-<lang>.pdf) exported from the master InDesign file — copy
# below mirrors the V2.0 template's back page verbatim. TODO: delete this
# table once the asset lands; placed_asset_for will then take over.
_BACK_COVER_COPY = {
    "US": {
        "company": "JACKERY INC.",
        "address": "5310 Bunche Dr., Fremont, CA 94538-8301",
        "phone": "1-888-502-2236 (US)",
        "lines": "hello@jackery.com\nwww.jackery.com",
    },
}


def add_back_cover_page(
    writer, region: str, page_index: int, copy: dict[str, str] | None = None,
) -> bool:
    """Compose the template's back page: company block + contact bar."""
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
    lines = copy.get("lines", "")
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
