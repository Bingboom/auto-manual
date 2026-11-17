"""Cell text, table rows and table kinds of a published Web manual's markup.

Every table is read row by row and value column by value column: a header row names the value columns after it, a
row with one spanning cell (or a label with no value) is an in-table sub-heading, and a label cell spanning several
rows is carried to the rows it spans. Footnote markers are kept apart from the label they mark. Which tables are
specification tables is decided by ``classify_table`` from the table's class and the heading path above it.
"""
from __future__ import annotations

import html
import re
from collections.abc import Iterator
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

LINE_SEP = " | "  # a printed line or paragraph break inside one cell

# Headings that open a specification section, in every published language.
SPEC_HEADING = re.compile(
    r"SPECIFICATION|TECHNICAL PARAMETER|TECHNISCHE (SPEZIFIKATION|DATEN|PARAMETER|SPECIFICATIE)|ELEKTRISCHE DATEN"
    r"|ESPECIFICACION|ESPECIFICAÇ|SP[ÉE]CIFICATION|CARACT[ÉE]RISTIQUES TECHNIQUES|SPECIFICHE|PARAMETRI TECNICI"
    r"|SPECIFICATIES|SPECYFIKACJA|DANE TECHNICZNE|PARAMETRY TECHNICZNE|ТЕХНІЧНІ (ХАРАКТЕРИСТИКИ|ПАРАМЕТРИ)"
    r"|PAR[AÁÂ]METROS T[EÉ]CNICOS|SPEZIFIKATION|СПЕЦИФІКАЦІ"
    r"|仕様|规格|規格|技术参数|技術參數|사양|Specificaties", re.I)
# Specification-class tables outside the section that give usage or charge-time estimates, not ratings.
RUNTIME_HEADING = re.compile(r"目安|時間|时间|time|zeit|tiempo|temps|tempo|tijd|czas|час|runtime|working hours|trouble|"
                             r"error|故障|エラー", re.I)
# Headings outside the specification section whose tables are specification-like.
SPEC_LIKE_HEADING = re.compile(
    r"charg|recharg|laden|ladung|carga|recharge|ricaric|opla|ładow|заряд|充電|充电|目安|"
    r"\\bports?\\b|\\bpuertos?\\b|\\bportas?\\b|interface|\\bconnect|anschl|conex|collega|aansluit|złącz|підключ|接続|接口|"
    r"\bUPS\b|\bEPS\b|\bUSV\b|\bASI\b|\bSAI\b|ДБЖ|无间断|無停電|不断电|"
    r"expan|erweit|ampli|espans|uitbrei|rozszerz|розшир|拡張|扩展|battery pack|"
    r"compatib|kompatyb|kompatib|сумісн|互換|兼容|warrant|garant|gwaranc|гаранті|保証|保修|"
    r"solar|ソーラー|太阳能|working time|runtime|usage time|"
    r"同梱品|包装清单|包裝清單|package list|in the box|what's in|lieferumfang|contenu de la bo|contenido|contenuto|inhoud|"
    r"zawarto|комплект", re.I)
NOT_SPEC_LIKE_HEADING = re.compile(
    r"LCD|display|écran|pantalla|anzeige|schermo|wyświetl|дисплей|液晶|显示|symbol|safety|sicherheit|seguridad|sécurité|"
    r"sicurezza|veiligheid|bezpiecz|безпек|安全|trouble|störung|dépannage|solución|risoluzione|problemen|rozwiązyw|"
    r"несправн|トラブル|故障", re.I)
# Table classes that never hold data (callouts, symbol and LCD keys, troubleshooting, warranty …).
NON_DATA_CLASS = re.compile(r"callout|symbol|signal|lcd|troubleshoot|key-combination|safety|warning|lockup|item-list|"
                            r"warranty|jp-symbol|torque|led\b|native-led", re.I)
SPEC_CLASS = re.compile(r"spec", re.I)
_MARKER = re.compile(r"[*※†‡①-⑳⑴-⒇]+")
_EXPONENT_BEFORE = re.compile(r"(m|cm|mm|km|ft|in)\s*$")  # m², cm³ are exponents, not footnote markers


def clean_text(node: Any) -> str:
    """A node's visible words: line and paragraph breaks become LINE_SEP, whitespace collapses, images give alt."""
    if node is None:
        return ""
    parts: list[str] = []
    _walk(node, parts)
    text = html.unescape("".join(parts))
    lines = [re.sub(r"[ \t\r\f\v ]+", " ", line).strip() for line in text.split("\n")]
    return LINE_SEP.join(line for line in lines if line)


def _walk(node: Any, parts: list[str]) -> None:
    if isinstance(node, NavigableString):
        if node.__class__.__name__ not in ("Comment", "Declaration", "ProcessingInstruction"):
            parts.append(str(node))
        return
    if not isinstance(node, Tag) or node.name in ("style", "script"):
        return
    if node.name == "br":
        parts.append("\n")
        return
    if node.name == "img":
        if node.get("alt"):
            parts.append(f"[img:{node.get('alt')}]")
        return
    block = node.name in ("p", "div", "li", "tr")
    if block:
        parts.append("\n")
    for child in node.children:
        _walk(child, parts)
    if block:
        parts.append("\n")


def _is_marker(sup: Tag) -> bool:
    text = sup.get_text("", strip=True)
    if not text:
        return False
    if _MARKER.fullmatch(text):
        return True
    if not re.fullmatch(r"\d{1,2}|[a-z]", text):
        return False
    classes = " ".join(sup.get("class") or [])
    if "reference" in classes or "footnote" in classes:
        return True
    previous = sup.previous_sibling
    before = str(previous) if isinstance(previous, NavigableString) else (
        previous.get_text() if isinstance(previous, Tag) else "")
    return not _EXPONENT_BEFORE.search(before or "")


def sup_markers(node: Any) -> list[str]:
    """The footnote markers a cell carries."""
    if node is None:
        return []
    found = [sup.get_text("", strip=True) for sup in node.find_all("sup") if _is_marker(sup)]
    for match in re.finditer(r"[①-⑳※]", node.get_text("", strip=False)):
        if match.group(0) not in found:
            found.append(match.group(0))
    return found


def text_without_markers(node: Any) -> str:
    """A label's words without its footnote markers."""
    if node is None:
        return ""
    clone = BeautifulSoup(str(node), "html.parser")
    for sup in clone.find_all("sup"):
        if _is_marker(sup):
            sup.decompose()
    return re.sub(r"[①-⑳]|※$", "", clean_text(clone)).strip()


def direct_rows(table: Tag) -> list[Tag]:
    return [tr for tr in table.find_all("tr") if tr.find_parent("table") is table]


def cells_of(row: Tag) -> list[Tag]:
    return list(row.find_all(["th", "td"], recursive=False))


def _row(label_cell: Tag | None, value_cell: Tag, index: int, column: int, headers: list[str], subheading: str,
         carried: bool = False) -> dict[str, Any]:
    markers = sup_markers(label_cell) + sup_markers(value_cell)
    return {"row_type": "continuation" if carried else ("pair" if label_cell is not None else "value_only"),
            "label": clean_text(label_cell) if label_cell is not None else "",
            "label_clean": text_without_markers(label_cell) if label_cell is not None else "",
            "value": clean_text(value_cell),
            "col_header": headers[column] if headers and column < len(headers) else "",
            "markers": list(dict.fromkeys(markers)), "subheading": subheading, "col_index": column,
            "row_index": index, "rowspan_cont": carried}


def _special(row_type: str, cell: Tag, label: str, index: int, value: str = "") -> dict[str, Any]:
    clean = label if row_type == "header" else text_without_markers(cell)
    return {"row_type": row_type, "label": label, "label_clean": clean, "value": value, "col_header": "",
            "markers": [] if row_type == "header" else sup_markers(cell), "subheading": "", "col_index": 0,
            "row_index": index, "rowspan_cont": False}


def _header_like(cells: list[Tag], texts: list[str], carrying: bool) -> bool:
    """A row of short, figure-free column names (STC / BNPI / NMOT count as names)."""
    if len(cells) < 3 or carrying:
        return False
    named = all((t and not re.search(r"\d", t.replace("STC", "").replace("BNPI", "")))
                or re.fullmatch(r"(STC|BNPI|NMOT)\*?", t or "") for t in texts[1:])
    return named and all(len(t) < 25 for t in texts[1:])


def _is_header(row: Tag, cells: list[Tag], texts: list[str], index: int, carrying: bool) -> bool:
    in_head = row.find_parent("thead") is not None
    all_th = all(c.name == "th" and c.get("scope") != "row" for c in cells)
    return ((in_head or all_th) and len(cells) > 1 and index == 0) or _header_like(cells, texts, carrying)


class _TableState:
    def __init__(self, width: int) -> None:
        self.width = width
        self.headers: list[str] = []
        self.carry: tuple[Tag, int] | None = None
        self.subheading = ""

    def carrying(self) -> bool:
        return self.carry is not None and self.carry[1] > 0


def parse_table(table: Tag) -> Iterator[dict[str, Any]]:
    """One dict per row and value column; rowspan continuations and in-table sub-headings kept."""
    rows = direct_rows(table)
    if not rows:
        return
    state = _TableState(max(len(cells_of(r)) for r in rows))
    for index, row in enumerate(rows):
        cells = cells_of(row)
        if cells:
            yield from _table_row(row, cells, index, state)


def _table_row(row: Tag, cells: list[Tag], index: int, state: _TableState) -> Iterator[dict[str, Any]]:
    texts = [clean_text(c) for c in cells]
    if _is_header(row, cells, texts, index, state.carrying()):
        state.headers = texts
        yield _special("header", cells[0], texts[0], index, LINE_SEP.join(texts[1:]))
        return
    if state.carry is not None and state.carry[1] > 0:
        label_cell = state.carry[0]
        state.carry = (label_cell, state.carry[1] - 1)
        for column, cell in enumerate(cells):
            yield _row(label_cell, cell, index, column + 1, state.headers, state.subheading, carried=True)
        return
    if len(cells) == 1:
        yield from _single_cell(cells[0], texts[0], index, state)
        return
    label_cell, values = cells[0], cells[1:]
    span = int(label_cell.get("rowspan") or 1)
    if span > 1:
        state.carry = (label_cell, span - 1)
    if all(not clean_text(v) for v in values) and clean_text(label_cell):
        state.subheading = clean_text(label_cell)
        yield _special("subheading", label_cell, state.subheading, index)
        return
    for column, value in enumerate(values):
        yield _row(label_cell, value, index, column + 1, state.headers if len(values) > 1 else [], state.subheading)


def _single_cell(cell: Tag, text: str, index: int, state: _TableState) -> Iterator[dict[str, Any]]:
    if int(cell.get("colspan") or 1) >= 2 or (cell.name == "th" and state.width >= 2):
        state.subheading = text
        yield _special("subheading", cell, text, index)
    else:
        yield _row(None, cell, index, 1, state.headers, state.subheading)


def classify_table(table: Tag, in_spec: bool, heading_path: str) -> str:
    """spec_section, spec_class_elsewhere, spec_like_elsewhere, or a skip_* reason."""
    classes = " ".join(table.get("class") or [])
    if in_spec:
        return "spec_section" if SPEC_CLASS.search(classes) or not NON_DATA_CLASS.search(classes) \
            else "skip_non_data_in_spec"
    if SPEC_CLASS.search(classes):
        return "spec_like_elsewhere" if RUNTIME_HEADING.search(heading_path) else "spec_class_elsewhere"
    if NON_DATA_CLASS.search(classes):
        return "skip_non_data"
    if not direct_rows(table):
        return "skip_empty"
    last = heading_path.split(" > ")[-1]
    if SPEC_LIKE_HEADING.search(last) and not NOT_SPEC_LIKE_HEADING.search(last):
        return "spec_like_elsewhere"
    return "skip_other"


MODEL_IN_HEADING = re.compile(r"(?:Model|Modelo|Modèle|Modell|Modello|Модель|型番|型号)\s*[:：]?\s*"
                              r"([A-Z]{1,4}\d?-?[A-Z0-9][A-Z0-9-]{2,})")
SOLD_SEPARATELY = re.compile(r"SOLD SEPARATELY|SE VENDE POR SEPARADO|VENDU S[ÉE]PAR[ÉE]MENT|SEPARAT ERH|"
                             r"VENDUTO SEPARATAMENTE|APART VERKRIJGBAAR|SPRZEDAWAN|ПРОДАЄТЬСЯ ОКРЕМО|別売|另售|单独出售", re.I)
_BRACKET_NAME = re.compile(r"【([^】]+)】")
_PAREN_NAME = re.compile(r"\((Jackery [^)]+)\)")


def described_product(heading_path: str) -> str:
    """The product a heading names for the block under it (a bundle or an accessory sold separately), if any."""
    label = ""
    for part in heading_path.split(" > "):
        model = MODEL_IN_HEADING.search(part)
        named = _BRACKET_NAME.search(part) or _PAREN_NAME.search(part)
        if model:
            label = model.group(1)
        elif named:
            label = named.group(1).strip()
        elif SOLD_SEPARATELY.search(part):
            label = SOLD_SEPARATELY.sub("", part).strip(" -—()（）")
    return label


__all__ = ["LINE_SEP", "SPEC_CLASS", "SPEC_HEADING", "classify_table", "clean_text", "described_product",
           "direct_rows", "parse_table", "sup_markers", "text_without_markers"]
