"""IDML resource parts: paragraph styles, colors, fonts, preferences (P1).

Verbatim moves from IdmlWriter — the emitted XML strings carry
designer-reported InDesign contracts (Paragraph*-prefixed shading, Auto
leading for figure paragraphs, DOMVersion 15.0) and must not be
"normalized".
"""
from __future__ import annotations

from .params import IDPKG, brand_cmyk, param_pt
from .style_names import paragraph_style_name, paragraph_style_ref


def para_styles(params: dict[str, tuple[str, str]]) -> list[tuple[str, float, float, str, str]]:
    """(name, size, leading, font_style, extras)"""
    p = params
    def sz(key, d): return param_pt(p, key, d)
    return [
        ("HB H1", sz("type_h1_font_size", 9.0), sz("type_h1_font_leading", 10.8), "Bold", ""),
        ("HB Title L2", sz("type_title_l2_font_size", 8.6), sz("type_title_l2_font_leading", 9.4), "Heavy", ""),
        ("HB Title L3", sz("type_title_l3_font_size", 7.0), sz("type_title_l3_font_leading", 8.0), "Medium", ""),
        ("HB Notice Label", sz("type_notice_label_font_size", 6.8), sz("type_notice_label_font_leading", 7.4), "Bold", "label"),
        ("HB Notice Side Label", sz("type_notice_label_font_size", 6.8), sz("type_notice_label_font_leading", 7.4), "Bold", "center"),
        ("HB Callout Label", sz("type_tip_label_font_size", 8.0), sz("type_tip_label_font_leading", 9.0), "Bold", "center"),
        ("HB Callout Body", sz("type_tip_body_font_size", 6.5), sz("type_tip_body_font_leading", 7.83), "Medium", ""),
        ("HB Card Number", sz("type_inbox_label_font_size", 6.5), sz("type_inbox_label_font_leading", 7.0), "Bold", "card_number"),
        ("HB InBox Label", sz("type_inbox_label_font_size", 6.3), sz("type_inbox_label_font_leading", 7.0), "Bold", "center"),
        ("HB Capsule Text", sz("type_h1_font_size", 9.0), sz("type_h1_font_leading", 10.8), "Bold", "capsule_text"),
        ("HB Figure", sz("type_body_font_size", 6.2), 0.0, "Regular", "figure"),
        ("HB Body", sz("type_body_font_size", 6.2), sz("type_body_font_leading", 7.5), "Medium", ""),  # \HBTypeBody is HBFontMedium
        ("HB FCC Text", 5.6, 6.15, "Regular", ""),
        ("HB Safety Tail Label", 9.85, 10.2, "Bold", ""),
        ("HB Safety Tail Body", 5.6, 6.2, "Regular", ""),
        ("HB Maintenance Body", 6.0, 7.5, "Regular", ""),
        ("HB List", sz("type_list_font_size", 5.4), sz("type_list_font_leading", 6.4), "Regular", ""),
        ("HB Spec Section", sz("type_spec_section_font_size", 8.8), sz("type_spec_section_font_leading", 9.6), "Bold", ""),
        ("HB Spec Label", sz("type_spec_label_font_size", 6.0), sz("type_spec_label_font_leading", 6.6), "Medium", ""),
        ("HB Spec Value", sz("type_spec_value_font_size", 6.0), sz("type_spec_value_font_leading", 6.6), "Regular", ""),
        ("HB Spec Note", sz("type_spec_note_font_size", 5.4), sz("type_spec_note_font_leading", 6.0), "Regular", ""),
        ("HB Data Header", sz("type_data_table_header_font_size", 6.6), sz("type_data_table_header_font_leading", 7.0), "Heavy", ""),
        ("HB Data Header Center", sz("type_data_table_header_font_size", 6.6), sz("type_data_table_header_font_leading", 7.0), "Heavy", "center"),
        ("HB Data Body", sz("type_data_table_font_size", 5.9), sz("type_data_table_font_leading", 6.7), "Regular", ""),
        ("HB Data Code", sz("type_trouble_code_font_size", 8.0), sz("type_trouble_code_font_leading", 8.0), "Bold", "center"),
        ("HB TOC Title", 22.25, 26.0, "Bold", "toc_title"),
        ("HB TOC Bar", 10.0, 10.0, "Heavy", "toc_bar"),
        ("HB TOC Range", 9.0, 10.0, "Bold", "toc_range"),
        ("HB TOC Entry", 6.5, 14.0, "Regular", "toc_entry"),
        ("HB Big Numeral", 26.0, 26.0, "Bold", ""),
    ]


def styles_xml(params: dict[str, tuple[str, str]]) -> str:
    styles = []
    for name, size, leading, weight, kind in para_styles(params):
        template_name = paragraph_style_name(name)
        self_id = paragraph_style_ref(name)
        # V2.0 master: H1 is a white-on-brand-dark bar; notice labels are
        # compact dark pills. Both map to paragraph shading in IDML.
        shaded = name == "HB H1" or kind in {"label", "card_number"}
        fill = (
            "Color/Paper"
            if shaded or kind in {"capsule_text", "toc_bar", "toc_range"}
            else "Color/HB Brand Dark"
        )
        # NOTE the Paragraph* prefix: bare ShadingOn/ShadingColor are
        # silently ignored by InDesign (designer-reported: no H1 bar,
        # invisible white labels/numerals)
        if kind == "card_number":
            shading = (
                'ParagraphShadingOn="true" '
                'ParagraphShadingColor="Color/HB Brand Dark" '
                'ParagraphShadingTint="100" '
                'ParagraphShadingWidth="TextWidth" '
                'ParagraphShadingTopOrigin="AscentTopOrigin" '
                'ParagraphShadingBottomOrigin="DescentBottomOrigin" '
                'ParagraphShadingTopOffset="2" ParagraphShadingBottomOffset="2" '
                'ParagraphShadingLeftOffset="3" ParagraphShadingRightOffset="3" '
                'SpaceBefore="7" SpaceAfter="6" '
            )
        elif shaded:
            shading = (
            'ParagraphShadingOn="true" '
            'ParagraphShadingColor="Color/HB Brand Dark" '
            'ParagraphShadingTint="100" '
            'ParagraphShadingWidth="ColumnWidth" '
            'ParagraphShadingTopOrigin="AscentTopOrigin" '
            'ParagraphShadingBottomOrigin="DescentBottomOrigin" '
            'ParagraphShadingTopOffset="2" ParagraphShadingBottomOffset="2" '
            'ParagraphShadingLeftOffset="3" ParagraphShadingRightOffset="3" '
            'LeftIndent="7" '
            'SpaceBefore="4" SpaceAfter="3" '
            )
        else:
            shading = ""
        justification = (
            "CenterAlign" if kind in {"center", "card_number"}
            else "RightAlign" if kind == "toc_range"
            else "LeftAlign"
        )
        styles.append(
            f'  <ParagraphStyle Self="{self_id}" Name="{template_name}" '
            f'PointSize="{size:g}" FillColor="{fill}" {shading}'
            f'Justification="{justification}">\n'
            f'    <Properties>\n'
            f'      <AppliedFont type="string">Gilroy</AppliedFont>\n'
            f'      <FontStyle type="string">{weight}</FontStyle>\n'
            # fixed leading does not grow for inline anchored objects —
            # figure paragraphs need Auto so art doesn't shoot out the top
            + (f'      <Leading type="unit">{leading:g}</Leading>\n'
               if kind != "figure" else
               '      <Leading type="enum">Auto</Leading>\n') +
            f'    </Properties>\n'
            f'  </ParagraphStyle>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Styles xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        '  <RootCharacterStyleGroup Self="rcsg">\n'
        '    <CharacterStyle Self="CharacterStyle/$ID/[No character style]" Name="$ID/[No character style]"/>\n'
        '  </RootCharacterStyleGroup>\n'
        '  <RootParagraphStyleGroup Self="rpsg">\n'
        '    <ParagraphStyle Self="ParagraphStyle/$ID/[No paragraph style]" Name="$ID/[No paragraph style]"/>\n'
        '    <ParagraphStyle Self="ParagraphStyle/$ID/NormalParagraphStyle" Name="$ID/NormalParagraphStyle"/>\n'
        + "\n".join(styles) + "\n"
        '  </RootParagraphStyleGroup>\n'
        '  <RootCellStyleGroup Self="rcellsg">\n'
        '    <CellStyle Self="CellStyle/$ID/[None]" Name="$ID/[None]"/>\n'
        '  </RootCellStyleGroup>\n'
        '  <RootTableStyleGroup Self="rtsg">\n'
        '    <TableStyle Self="TableStyle/$ID/[Basic Table]" Name="$ID/[Basic Table]"/>\n'
        '  </RootTableStyleGroup>\n'
        '  <RootObjectStyleGroup Self="rosg">\n'
        '    <ObjectStyle Self="ObjectStyle/$ID/[None]" Name="$ID/[None]"/>\n'
        '    <ObjectStyle Self="ObjectStyle/$ID/[Normal Text Frame]" Name="$ID/[Normal Text Frame]"/>\n'
        '    <ObjectStyle Self="ObjectStyle/HB Capsule Heading" Name="HB Capsule Heading"/>\n'
        '    <ObjectStyle Self="ObjectStyle/HB Rounded Table Outer" Name="HB Rounded Table Outer"/>\n'
        '    <ObjectStyle Self="ObjectStyle/HB Rounded Panel" Name="HB Rounded Panel"/>\n'
        '    <ObjectStyle Self="ObjectStyle/HB Inbox Card" Name="HB Inbox Card"/>\n'
        '    <ObjectStyle Self="ObjectStyle/HB Badge" Name="HB Badge"/>\n'
        '  </RootObjectStyleGroup>\n'
        '</idPkg:Styles>\n'
    )


def graphic_xml(params: dict[str, tuple[str, str]]) -> str:
    p = params
    colors = []
    for name, key, default in (
        ("HB Brand Dark", "brand_color_branddark", "0,0,0,0.90"),
        ("HB Text Gray", "brand_color_textgray", "0,0,0,0.90"),
        ("HB Line K40", "brand_color_linek40", "0,0,0,0.80"),
        ("HB Bg K05", "brand_color_bgk05", "0,0,0,0.05"),
        ("HB Border K10", "brand_color_borderk10", "0,0,0,0.10"),
        ("HB Header K08", "brand_color_headerk08", "0,0,0,0.08"),
    ):
        c, m, y, k = brand_cmyk(p, key, default)
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
        '  <Swatch Self="Swatch/None" Name="None"/>\n'
        '</idPkg:Graphic>\n'
    )


def fonts_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Fonts xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        '  <FontFamily Self="ff_gilroy" Name="Gilroy">\n'
        '    <Font Self="ff_gilroy_r" FontFamily="Gilroy" Name="Gilroy Regular" PostScriptName="Gilroy-Regular" Status="Installed" FontStyleName="Regular" FontType="OpenTypeCFF"/>\n'
        '    <Font Self="ff_gilroy_m" FontFamily="Gilroy" Name="Gilroy Medium" PostScriptName="Gilroy-Medium" Status="Installed" FontStyleName="Medium" FontType="OpenTypeCFF"/>\n'
        '    <Font Self="ff_gilroy_sb" FontFamily="Gilroy" Name="Gilroy Semibold" PostScriptName="Gilroy-SemiBold" Status="Installed" FontStyleName="Semibold" FontType="OpenTypeCFF"/>\n'
        '    <Font Self="ff_gilroy_b" FontFamily="Gilroy" Name="Gilroy Bold" PostScriptName="Gilroy-Bold" Status="Installed" FontStyleName="Bold" FontType="OpenTypeCFF"/>\n'
        '    <Font Self="ff_gilroy_h" FontFamily="Gilroy" Name="Gilroy Heavy" PostScriptName="Gilroy-Heavy" Status="Installed" FontStyleName="Heavy" FontType="OpenTypeCFF"/>\n'
        '  </FontFamily>\n'
        '  <FontFamily Self="ff_arial_unicode_ms" Name="Arial Unicode MS">\n'
        '    <Font Self="ff_arial_unicode_ms_r" FontFamily="Arial Unicode MS" Name="Arial Unicode MS Regular" PostScriptName="ArialUnicodeMS" Status="Installed" FontStyleName="Regular" FontType="OpenTypeTT"/>\n'
        '  </FontFamily>\n'
        '  <FontFamily Self="ff_apple_symbols" Name="Apple Symbols">\n'
        '    <Font Self="ff_apple_symbols_r" FontFamily="Apple Symbols" Name="Apple Symbols Regular" PostScriptName="AppleSymbols" Status="Installed" FontStyleName="Regular" FontType="TrueType"/>\n'
        '  </FontFamily>\n'
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
