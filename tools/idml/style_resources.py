"""IDML graphic, font, and document-preference resource parts."""
from __future__ import annotations

from .font_family import (
    IDML_FONT_FAMILY_TOKENS,
    PRIMARY_FONT_FAMILY_TOKEN,
    IdmlFontFamilyToken,
)
from .params import IDPKG, brand_cmyk


def graphic_xml(params: dict[str, tuple[str, str]]) -> str:
    colors = []
    for name, key, default in (
        ("HB Brand Dark", "brand_color_branddark", "0,0,0,0.90"),
        ("HB Text Gray", "brand_color_textgray", "0,0,0,0.90"),
        ("HB Line K40", "brand_color_linek40", "0,0,0,0.80"),
        ("HB Bg K05", "brand_color_bgk05", "0,0,0,0.05"),
        ("HB Border K10", "brand_color_borderk10", "0,0,0,0.10"),
        ("HB Header K08", "brand_color_headerk08", "0,0,0,0.08"),
    ):
        c, m, y, k = brand_cmyk(params, key, default)
        colors.append(
            f'  <Color Self="Color/{name}" Model="Process" Space="CMYK" '
            f'ColorValue="{c:g} {m:g} {y:g} {k:g}" Name="{name}"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Graphic xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        '  <Color Self="Color/Black" Model="Process" Space="CMYK" ColorValue="0 0 0 100" Name="Black"/>\n'
        '  <Color Self="Color/Paper" Model="Process" Space="CMYK" ColorValue="0 0 0 0" Name="Paper"/>\n'
        + "\n".join(colors) + "\n"
        '  <StrokeStyle Self="StrokeStyle/$ID/Dashed" Name="$ID/Dashed"/>\n'
        '  <Swatch Self="Swatch/None" Name="None"/>\n'
        '</idPkg:Graphic>\n'
    )


def _font_family_xml(token: IdmlFontFamilyToken) -> str:
    faces = "\n".join(
        f'    <Font Self="{face.resource_id}" FontFamily="{token.name}" '
        f'Name="{face.name}" PostScriptName="{face.postscript_name}" '
        f'Status="Installed" FontStyleName="{face.style_name}" '
        f'FontType="{face.font_type}"/>'
        for face in token.faces
    )
    return (
        f'  <FontFamily Self="{token.resource_id}" Name="{token.name}">\n'
        + faces + '\n'
        '  </FontFamily>'
    )


def fonts_xml() -> str:
    families = "\n".join(
        _font_family_xml(token) for token in IDML_FONT_FAMILY_TOKENS
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Fonts xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        + families + '\n'
        '</idPkg:Fonts>\n'
    )


def preferences_xml(*, page_w: float, page_h: float,
                    m_t: float, m_b: float, m_l: float, m_r: float) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Preferences xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'  <DocumentPreference PageWidth="{page_w:g}" PageHeight="{page_h:g}" '
        'PagesPerDocument="1" FacingPages="true" PageOrientation="Portrait" '
        'DocumentBleedTopOffset="8.5" DocumentBleedBottomOffset="8.5" '
        'DocumentBleedInsideOrLeftOffset="8.5" DocumentBleedOutsideOrRightOffset="8.5"/>\n'
        '  <MarginPreference ColumnCount="1" ColumnGutter="12" '
        f'Top="{m_t:g}" Bottom="{m_b:g}" Left="{m_l:g}" Right="{m_r:g}"/>\n'
        '</idPkg:Preferences>\n'
    )
