"""Which corpus blocks carry warning, safety and compliance knowledge (Phase 2a, P2-2).

Precedence is warning > compliance > safety, so one block is never two items;
only callout markup outranks cited legislation.

- **warning**: every callout; table rows whose first cell is a recognized signal
  word and paragraphs that open with ``<signal word>:`` (or with the signal word
  in capitals when the colon was lost in rendering), unless they cite
  legislation (a ``NOTE:``-prefixed FCC statement is compliance). Signal-word
  legend tables (two or more distinct signal words in the first column, e.g.
  each manual's WARNING / CAUTION / NOTE / TIP key) are definitions and carry
  nothing.
- **compliance**: text with an EU legislation number (``2014/53/EU``,
  ``(EU) 2015/863``) or a regulatory mark (CE, UKCA, WEEE, RoHS, FCC as written),
  anything in a regulations / declaration section, and symbol-table rows for a
  regulatory marking: a CE / UKCA / WEEE icon, or the WEEE household-waste
  statement where the icon's alt text only repeats the meaning. Statements are
  recorded as found; applicability is never judged.
- **safety**: paragraphs, list items and table rows in a safety section, and
  symbol-table rows that explain a product symbol. A symbol row is labelled with
  the icon's own name, never with alt text that repeats the meaning.

Granularity: one item per callout, paragraph, top-level list item (nested items
stay with their parent) and table row. Section titles are matched with stems in
all nine EU manual languages; the regulations sections carry English titles.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
import re

from tools.manual_knowledge.identity import callout_severity

SAFETY_TITLE = re.compile(r"safety|precaution|sicherheit|sécurité|seguridad|precauci|sicurezza|precauzion|veiligheid|"
                          r"bezpieczeństw|segurança|precauç|безпек", re.IGNORECASE)
COMPLIANCE_TITLE = re.compile(r"regulation|declaration|conformity|compliance|authori[sz]ed representative",
                              re.IGNORECASE)
SYMBOL_TITLE = re.compile(r"symbol|s[ií]mbol|символ", re.IGNORECASE)
LEGISLATION = re.compile(r"\b(?:19|20)\d\d/\d{1,4}/(?:EU|EC|EEC|EG|EWG|UE|CE|ЄС)\b"
                         r"|\((?:EU|UE|EG)\)\s*(?:N[or]\.?\s*)?(?:19|20)\d\d/\d{1,4}\b")
MARK = re.compile(r"\b(?:CE|UKCA|WEEE|RoHS|ROHS|FCC)\b")
MARKING_ICONS = frozenset({"ce", "ukca", "weee", "weee2", "battery_weee"})
# The WEEE statement in each manual language: "must not be disposed of with household waste".
HOUSEHOLD_WASTE = re.compile(r"household waste|hausmüll|haushaltsabfall|ordures ménagères|residuos domésticos|"
                             r"rifiut\w* domestic|huishoudelijk afval|odpad\w* domow|lixo doméstico|"
                             r"побутов\w* відход", re.IGNORECASE)
_SIGNAL_PREFIX = re.compile(r"^\W*([^\W\d_]+)\s*[:：]\s*")
# A label that lost its colon in rendering ("OPMERKING De …") still reads as one when written in capitals.
_BARE_SIGNAL = re.compile(r"^\W*([^\W\d_]+)\s+(?=\S)")


@dataclass(frozen=True)
class Carrier:
    category: str
    label: str | None
    text: str
    item_index: int | None
    rule: str
    severity: str | None = None


def section_kind(title: str) -> str | None:
    if COMPLIANCE_TITLE.search(title):
        return "compliance"
    if SAFETY_TITLE.search(title):
        return "safety"
    if SYMBOL_TITLE.search(title):
        return "symbols"
    return None


def legislation(text: str) -> list[str]:
    """Legislation numbers and regulatory marks exactly as the manual writes them."""
    found = [" ".join(match.split()) for match in LEGISLATION.findall(text) + MARK.findall(text)]
    return sorted(set(found))


def _signal(text: str) -> str | None:
    severity = callout_severity(re.sub(r"^\W+", "", text))  # "⚠ WARNING" in a legend's first column
    return None if severity == "unknown" else severity


def _text_label(cell: dict) -> str | None:
    """A first cell's own text; an icon-only cell (text taken from alt) is no signal word."""
    alts = " / ".join(alt for alt in cell.get("image_alts", []) if alt)
    text = cell["text"].strip()
    return text if text and not (alts and text == alts) else None


def is_legend(table: dict) -> bool:
    labels = {_signal(label) for row in table["rows"] if row and (label := _text_label(row[0]))}
    return len(labels - {None}) >= 2


def _plain(text: str, kind: str | None, index: int | None) -> Iterator[Carrier]:
    if legislation(text):
        yield Carrier("compliance", None, text, index, "extract.compliance_legislation")
    elif kind == "compliance":
        yield Carrier("compliance", None, text, index, "extract.compliance_section")
    elif kind == "safety":
        yield Carrier("safety", None, text, index, "extract.safety_section")


def _signal_prefix(text: str) -> re.Match[str] | None:
    match = _SIGNAL_PREFIX.match(text)
    if match is None and (bare := _BARE_SIGNAL.match(text)) and bare.group(1).isupper():
        return bare
    return match


def _paragraph(block: dict, kind: str | None) -> Iterator[Carrier]:
    match = _signal_prefix(block["text"])
    if legislation(block["text"]):
        yield from _plain(block["text"], kind, None)
    elif match and (severity := _signal(match.group(1))) and block["text"][match.end():].strip():
        yield Carrier("warning", match.group(1), block["text"][match.end():].strip(), None,
                      "extract.signal_paragraph", severity)
    else:
        yield from _plain(block["text"], kind, None)


def _list(block: dict, kind: str | None) -> Iterator[Carrier]:
    for index, item in enumerate(block["items"]):
        text = "\n".join([item["text"]] + [child["text"] for child in item["children"]])
        yield from _plain(text, kind, index)


def _symbol_row(row: list[dict], text: str, index: int) -> Iterator[Carrier]:
    if not row[0].get("image_alts"):
        # No icon in the first cell: the cells are meanings side by side and stay one row.
        yield Carrier("safety", None, "\n".join(cell["text"] for cell in row if cell["text"].strip()), index,
                      "extract.symbol_row")
        return
    name = row[0]["text"].strip()
    icon = name if name and name != text.strip() else None
    if (icon and re.sub(r"[\s-]+", "_", icon.casefold()) in MARKING_ICONS) or HOUSEHOLD_WASTE.search(text):
        yield Carrier("compliance", icon, text, index, "extract.marking_symbol")
    elif legislation(text):
        yield Carrier("compliance", icon, text, index, "extract.compliance_legislation")
    else:
        yield Carrier("safety", icon, text, index, "extract.symbol_row")


def _table(block: dict, kind: str | None) -> Iterator[Carrier]:
    if is_legend(block):
        return
    for index, row in enumerate(block["rows"]):
        if not row or all(cell["header"] for cell in row):
            continue
        label = _text_label(row[0])
        rest = "\n".join(cell["text"] for cell in row[1:] if cell["text"].strip())
        if label and rest and not legislation(rest) and (severity := _signal(label)):
            yield Carrier("warning", label, rest, index, "extract.signal_row", severity)
        elif kind == "symbols" and rest:
            yield from _symbol_row(row, rest, index)
        else:
            yield from _plain("\n".join(cell["text"] for cell in row if cell["text"].strip()), kind, index)


def carriers(section: dict) -> Iterator[tuple[dict, Carrier]]:
    """Each knowledge-bearing piece of a section with the block it came from, in reading order."""
    kind = section_kind(section["title"])
    for block in section["blocks"]:
        if block["type"] == "callout":
            yield block, Carrier("warning", block["label"], block["body"], None, "extract.callout",
                                 block.get("severity", "unknown"))
        elif block["type"] == "paragraph":
            yield from ((block, carrier) for carrier in _paragraph(block, kind))
        elif block["type"] == "list":
            yield from ((block, carrier) for carrier in _list(block, kind))
        elif block["type"] == "table":
            yield from ((block, carrier) for carrier in _table(block, kind))
