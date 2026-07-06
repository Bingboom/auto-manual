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
    "HB Body": "\u6b63\u6587",
    "HB List": "Item List",
    "HB Spec Section": "TableHeading",
    "HB Spec Label": "\u6bb5\u843d\u6837\u5f0f-\u52a0\u7c97",
    "HB Spec Value": "\u6bb5\u843d\u6837\u5f0f2",
    "HB Spec Note": "\u6bb5\u843d\u6837\u5f0f-\u5de6\u7f29+\u60ac\u5782",
}


def paragraph_style_name(name: str) -> str:
    return PARAGRAPH_STYLE_NAME_MAP.get(name, name)


def paragraph_style_ref(name: str) -> str:
    return "ParagraphStyle/" + paragraph_style_name(name)
