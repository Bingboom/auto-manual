"""Full-page placed-PDF spreads (cover, product overview).

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
