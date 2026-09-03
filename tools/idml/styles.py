"""Load-bearing IDML paragraph styles, colors, fonts, and preferences."""
from __future__ import annotations

from .loaders import normalize_lang
from .params import IDPKG, param_pt, param_text
from .app_text_styles import paragraph_styles as app_paragraph_styles
from .paragraph_style_attrs import contract_paragraph_attrs
from .style_resources import PRIMARY_FONT_FAMILY_TOKEN, fonts_xml, graphic_xml, preferences_xml
from .style_names import paragraph_style_name, paragraph_style_ref


def para_styles(
    params: dict[str, tuple[str, str]],
    language: str = "",
) -> list[tuple[str, float, float, str, str]]:
    """(name, size, leading, font_style, extras)"""
    p = params
    def sz(key, d): return param_pt(p, key, d)

    # `normalize_lang` because the writer carries the source code -- "ja" --
    # while every layout row is keyed on the phase2 suffix "jp".
    code = normalize_lang(language) if language else ""

    def lsz(key, d):
        """A size a book may declare for itself, falling back to the shared row.

        `sz` reads one row for every book, which is right where the books
        agree. These roles disagree because their printed masters disagree.
        Only a language that declares a row moves: with no row the lookup
        returns `sz`'s own value, so widening this reached nobody until the
        first row existed. Do not point `lsz` at a key that already carries
        another language's row -- see the spec family, whose fr/es/de/it rows
        would activate four shipped books the moment it did.
        """
        return param_pt(p, f"lang_{code}_{key}", sz(key, d)) if code else sz(key, d)

    return [
        ("HB H1", sz("type_h1_font_size", 9.0), sz("type_h1_font_leading", 10.8), "Bold", ""),
        ("HB Title L2", sz("idml_title_l2_font_size", sz("type_title_l2_font_size", 8.6)), sz("type_title_l2_font_leading", 9.4), param_text(p, "idml_title_l2_font_style", "Heavy"), ""),
        (
            "HB Operation Row Label",
            sz("idml_operation_row_label_font_size", 10.0),
            sz("idml_operation_row_label_font_leading", 11.0),
            "Bold",
            "",
        ),
        ("HB Title L3", sz("type_title_l3_font_size", 7.0), sz("type_title_l3_font_leading", 8.0), "Medium", ""),
        ("HB Notice Label", sz("type_notice_label_font_size", 6.8), sz("type_notice_label_font_leading", 7.4), "Bold", "label"),
        ("HB Notice Side Label", sz("type_symbol_signal_font_size", 9.9), sz("type_symbol_signal_font_leading", 10.5), "Bold", "center"),
        ("HB Preface Tag", sz("idml_preface_tag_font_size", 6.0), sz("idml_preface_tag_font_size", 6.0), "Bold", "preface_tag"),
        ("HB Preface Title", sz("idml_preface_title_font_size", 8.0), sz("idml_preface_title_font_size", 8.0), "Bold", "preface_title"),
        ("HB Callout Label", sz("type_tip_label_font_size", 8.0), sz("type_tip_label_font_leading", 9.0), "Bold", "center"),
        ("HB Callout Body", sz("type_tip_body_font_size", 6.5), sz("type_tip_body_font_leading", 7.83), "Medium", ""),
        ("HB Emphasis Pill", sz("idml_charging_emphasis_font_size", 6.6), sz("idml_charging_emphasis_font_leading", 7.4), "Bold", "emphasis"),
        ("HB Card Number", sz("type_inbox_label_font_size", 6.5), sz("type_inbox_label_font_leading", 7.0), "Bold", "card_number"),
        ("HB InBox Label", sz("type_inbox_label_font_size", 6.3), sz("type_inbox_label_font_leading", 7.0), "Bold", "center"),
        ("HB Capsule Text", sz("type_h1_font_size", 9.0), sz("type_h1_font_leading", 10.8), "Bold", "capsule_text"),
        ("HB Figure", sz("type_body_font_size", 6.2), 0.0, "Regular", "figure"),
        (
            "HB Body",
            sz("type_body_font_size", 6.2),
            sz("type_body_font_leading", 7.5),
            param_text(p, "idml_body_font_style", "Medium"),
            "",
        ),
        ("HB Lead", sz("type_rubric_font_size", 8.6), sz("type_rubric_font_leading", 9.4), "Heavy", "lead"),
        ("HB Footer", sz("page_footer_font_size", 6.0), sz("page_footer_font_leading", 7.2), "Regular", "footer"),
        ("HB Page Number", sz("page_footer_font_size", 6.0), sz("page_footer_font_leading", 7.2), "Regular", "page_number"),
        *app_paragraph_styles(p),
        ("HB Preface Body", sz("idml_preface_body_font_size", 7.2), sz("idml_preface_body_font_leading", 8.6), "Regular", "preface_body"),
        ("HB Safety Lead", sz("type_safety_lead_font_size", 8.0), sz("type_safety_lead_font_leading", 9.6), "Bold", "safety_lead"),
        ("HB Safety Instruction", sz("idml_safety_instruction_font_size", 8.0), sz("idml_safety_instruction_font_leading", 9.6), param_text(p, "idml_safety_instruction_font_style", "Bold"), "warning_lead"),
        ("HB Warning Lead Label", sz("type_warning_lead_label_font_size", 10.0), sz("type_warning_lead_label_font_leading", 10.6), "Bold", "warning_lead"),
        ("HB Warning Lead Body", sz("type_warning_lead_body_font_size", 6.5), sz("type_warning_lead_body_font_leading", 7.2), "Bold", "warning_lead"),
        ("HB FCC Text", 5.6, 6.15, "Regular", ""),
        ("HB Safety Tail Label", sz("idml_safety_tail_label_font_size", 9.85),
         sz("idml_safety_tail_label_font_leading", 10.2), "Bold", ""),
        ("HB Safety Tail Body", 5.6, 6.2, "Regular", ""),
        ("HB Safety Tail Body EN", 5.6, 6.2, param_text(p, "idml_safety_tail_body_font_style", "Bold"), ""),
        ("HB Maintenance Body", 6.0, 7.5, "Regular", ""),
        ("HB List", sz("type_list_font_size", 5.4), sz("idml_list_font_leading", 7.2), "Regular", "list"),
        ("HB Sublist", sz("type_list_font_size", 5.4), sz("idml_list_font_leading", 7.2), "Regular", "sublist"),
        ("HB List FR", sz("type_list_font_size", 5.4), sz("lang_fr_type_list_font_leading", sz("idml_list_font_leading", 7.2)), "Regular", "list"),
        ("HB Sublist FR", sz("type_list_font_size", 5.4), sz("lang_fr_type_list_font_leading", sz("idml_list_font_leading", 7.2)), "Regular", "sublist"),
        ("HB List ES", sz("type_list_font_size", 5.4), sz("lang_es_type_list_font_leading", sz("idml_list_font_leading", 7.2)), "Regular", "list"),
        ("HB Sublist ES", sz("type_list_font_size", 5.4), sz("lang_es_type_list_font_leading", sz("idml_list_font_leading", 7.2)), "Regular", "sublist"),
        ("HB Safety List", sz("type_list_font_size", 5.4), sz("idml_list_font_leading", 7.2), "Regular", "list"),
        ("HB Safety Sublist", sz("type_list_font_size", 5.4), sz("idml_list_font_leading", 7.2), "Regular", "sublist"),
        ("HB Safety List FR", sz("type_list_font_size", 5.4), sz("lang_fr_idml_safety_list_leading", 7.0), "Regular", "list"),
        ("HB Safety Sublist FR", sz("type_list_font_size", 5.4), sz("lang_fr_idml_safety_list_leading", 7.0), "Regular", "sublist"),
        ("HB Safety List ES", sz("type_list_font_size", 5.4), sz("lang_es_idml_safety_list_leading", 6.5), "Regular", "list"),
        ("HB Safety Sublist ES", sz("type_list_font_size", 5.4), sz("lang_es_idml_safety_list_leading", 6.5), "Regular", "sublist"),
        ("HB Warranty Lead", lsz("type_warranty_lead_font_size", 7.0), lsz("type_warranty_lead_font_leading", 8.2), "Bold", ""),
        ("HB Warranty Note", lsz("type_warranty_body_font_size", 6.0), lsz("type_warranty_body_font_leading", 7.2), "Regular", "warranty_note"),
        ("HB Warranty Body", lsz("type_warranty_body_font_size", 6.0), lsz("idml_warranty_body_font_leading", 6.0), "Regular", ""),
        ("HB Warranty Title", lsz("idml_warranty_title_font_size", 8.0), lsz("type_warranty_title_font_leading", 8.8), "Bold", "warranty_title"),
        ("HB Warranty List", lsz("type_warranty_body_font_size", 6.0), lsz("type_warranty_body_font_leading", 7.2), "Regular", "warranty_list"),
        ("HB Warranty Year Heading", sz("type_warranty_year_unit_font_size", 12.0), sz("type_warranty_year_unit_font_size", 12.0), "Heavy", ""),
        ("HB Warranty Year Subtitle", sz("type_warranty_year_subtitle_font_size", 7.2), sz("type_warranty_year_subtitle_font_size", 7.2), "Bold", ""),
        ("HB Spec Section", sz("type_spec_section_font_size", 8.8), sz("type_spec_section_font_leading", 9.6), "Bold", ""),
        ("HB Spec Label", sz("type_spec_label_font_size", 6.0), sz("type_spec_label_font_leading", 6.6), "Medium", ""),
        ("HB Spec Value", sz("type_spec_value_font_size", 6.0), sz("type_spec_value_font_leading", 6.6), "Regular", ""),
        ("HB Spec Note", sz("type_spec_note_font_size", 5.4), sz("type_spec_note_font_leading", 6.0), "Regular", ""),
        ("HB Data Header", sz("type_data_table_header_font_size", 6.6), sz("type_data_table_header_font_leading", 7.0), "Heavy", ""),
        ("HB Data Header Center", sz("type_data_table_header_font_size", 6.6), sz("type_data_table_header_font_leading", 7.0), "Heavy", "center"),
        ("HB Data Body", sz("type_data_table_font_size", 5.9), sz("type_data_table_font_leading", 6.7), "Regular", ""),
        ("HB Data Code", sz("type_trouble_code_font_size", 8.0), sz("type_trouble_code_font_leading", 8.0), "Bold", "center"),
        ("HB Symbol Header", sz("idml_symbol_header_font_size", 8.0), sz("idml_symbol_header_font_leading", 8.8), "Bold", ""),
        ("HB Symbol Body", sz("type_symbol_body_font_size", 5.6), sz("type_symbol_body_font_leading", 6.5), "Regular", ""),
        ("HB TOC Title", 22.25, 26.0, "Bold", "toc_title"),
        ("HB TOC Bar", 10.0, 10.0, "Heavy", "toc_bar"),
        ("HB TOC Range", 9.0, 10.0, "Bold", "toc_range"),
        ("HB TOC Entry", lsz("type_toc_entry_font_size", 6.5),
         lsz("type_toc_entry_font_leading", 14.0), "Regular", "toc_entry"),
        ("HB Big Numeral", 26.0, 26.0, "Bold", ""),
    ]


def styles_xml(
    params: dict[str, tuple[str, str]],
    language: str = "",
) -> str:
    styles = []
    for name, size, leading, weight, kind in para_styles(params, language):
        template_name = paragraph_style_name(name)
        self_id = paragraph_style_ref(name)
        # V2.0 master: H1 is a white-on-brand-dark bar; notice labels are
        # compact dark pills. Both map to paragraph shading in IDML.
        shaded = name == "HB H1" or kind in {"label", "card_number"}
        fill = (
            f'Color/{param_text(params, "page_footer_color", "TextGray")}'
            if kind in {"footer", "page_number"}
            else "Color/Paper"
            if shaded or kind in {"capsule_text", "toc_bar", "toc_range", "emphasis", "warranty_title", "preface_tag"}
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
            "CenterAlign" if kind in {"center", "card_number", "preface_tag"}
            else "RightAlign" if kind == "toc_range"
            else "LeftAlign"
        )
        paragraph_attrs = contract_paragraph_attrs(name, kind, leading, params)
        styles.append(
            f'  <ParagraphStyle Self="{self_id}" Name="{template_name}" '
            f'PointSize="{size:g}" FillColor="{fill}" {shading}'
            f'{paragraph_attrs}Justification="{justification}">\n'
            f'    <Properties>\n'
            f'      <AppliedFont type="string">{PRIMARY_FONT_FAMILY_TOKEN.name}</AppliedFont>\n'
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
        '    <ObjectStyle Self="ObjectStyle/HB Standard Page" Name="HB Standard Page"/>\n'
        '    <ObjectStyle Self="ObjectStyle/HB No Footer Page" Name="HB No Footer Page"/>\n'
        '    <ObjectStyle Self="ObjectStyle/HB Cover Page" Name="HB Cover Page"/>\n'
        '  </RootObjectStyleGroup>\n'
        '</idPkg:Styles>\n'
    )
