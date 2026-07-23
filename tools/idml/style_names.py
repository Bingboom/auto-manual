"""IDML paragraph style names shared by resource and story writers.

The RST/LaTeX extraction layer keeps semantic ``HB ...`` names because they
describe component intent. The emitted IDML must use the names from the
designer template so exported stories can be placed into that template without
creating a second paragraph-style family.
"""
from __future__ import annotations


PARAGRAPH_STYLE_NAME_MAP = {
    "HB H1": "Heading1",
    "HB Title L2": "Heading2",
    "HB Title L3": "Heading3",
    "HB Notice Label": "Caution",
    "HB Notice Side Label": "\u9ed1\u5e95\u6bb5\u843d-\u6587\u672c",
    "HB Card Number": "Step",
    "HB InBox Label": "Item List Text",
    "HB Capsule Text": "\u5e26\u5e95Heading2",
    "HB Figure": "Figure",
    # designer template \u8bf4\u660e\u4e66\u6a21\u677f.idml has no \u6b63\u6587 style; its body family is
    # \u6bb5\u843d\u6837\u5f0f / \u6bb5\u843d\u6837\u5f0f2 / \u6bb5\u843d\u6837\u5f0f-\u52a0\u7c97 \u2014 point HB Body at the real one.
    "HB Body": "\u6bb5\u843d\u6837\u5f0f",
    "HB App H2 Download": "HB App H2 Download",
    "HB App H2": "HB App H2",
    "HB App Body Primary": "HB App Body Primary",
    "HB App Body Tail": "HB App Body Tail",
    "HB App Body Result": "HB App Body Result",
    "HB App Body Section": "HB App Body Section",
    "HB App H3": "HB App H3",
    "HB App List": "HB App List",
    "HB App Notes": "HB App Notes",
    "HB List": "Item List",
    "HB Spec Section": "TableHeading",
    "HB Spec Label": "\u6bb5\u843d\u6837\u5f0f-\u52a0\u7c97",
    "HB Spec Value": "\u6bb5\u843d\u6837\u5f0f2",
    "HB Spec Note": "\u6bb5\u843d\u6837\u5f0f-\u5de6\u7f29+\u60ac\u5782",
}


# Table styles: semantic role -> designer-template TableStyle name, so the
# production IDML (and a template-baked copy) adopt the template's table look.
# Unmapped roles fall back to the built-in [Basic Table].
TABLE_STYLE_NAME_MAP = {
    "spec": "\u7ad6\u578b\u8868\u683c",     # \u7ad6\u578b\u8868\u683c (vertical key/value)
    "data": "\u6b63\u6587\u8868\u683c",     # \u6b63\u6587\u8868\u683c (lcd/symbols/trouble/prose)
    "warning": "Warning\u8868\u683c",       # Warning\u8868\u683c
    "caution": "Caution\u8868\u683c",       # Caution\u8868\u683c
    "notice": "Notice\u8868\u683c",         # Notice\u8868\u683c
    "layout": "\u65e0\u8868\u5934\u8868\u683c",  # \u65e0\u8868\u5934\u8868\u683c (borderless: in-box, fcc)
}


def paragraph_style_name(name: str) -> str:
    return PARAGRAPH_STYLE_NAME_MAP.get(name, name)


def paragraph_style_ref(name: str) -> str:
    return "ParagraphStyle/" + paragraph_style_name(name)


def table_style_ref(role: str | None) -> str:
    name = TABLE_STYLE_NAME_MAP.get(role or "", "$ID/[Basic Table]")
    return "TableStyle/" + name
