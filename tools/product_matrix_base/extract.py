"""Every specification-table row of every published Web manual, verbatim, with where it came from.

The product information matrix (``code-as-doc/dev/product_matrix_base.md``) takes its values from the published Web
manuals. This module reads each edition the publish manifest lists (every model, market and language), finds its
specification tables and keeps every row: the printed label and text as the manual shows them, every number with its
unit, the section path and anchor the row sits under, and the attributes of the matrix dictionary the row maps to.
A row no attribute claims is kept and reported as unmapped; nothing is dropped.

A table is a specification table when its class says so (``spec-table``, ``native-spec``) or when it sits under a
heading that names the specifications in one of the manuals' languages. The figures the product-facts export reads
(``tools/product_facts``) are read with the export's own rules, edition by edition; the other dictionary attributes
are read here. Editions of one model and market are compared attribute by attribute, so a value one language edition
prints differently is listed for a person to check.

The output is internal product data: it is written only outside any git work tree.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any

from tools.product_facts.export import load_attributes as load_export_attributes
from tools.product_facts.export import read_facts
from tools.rtd.production_evidence import read_publications
from tools.utils.path_utils import Paths, PathSegments, docs_publish_of, docs_publish_web_of

SCHEMA = "hello-docs-matrix-extraction/v1"
DICTIONARY_SCHEMA = "hello-docs-matrix-attributes/v1"
DICTIONARY = Path(__file__).with_name("attributes.json")
VALUE_TYPES = {"number": "数值", "integer": "整数", "boolean": "布尔", "text": "文本", "range": "范围"}
PARSERS = ("export", "max_w", "dimensions", "chemistry", "temp_range", "manual")

# Headings that name the specifications, in the manuals' languages.
SPEC_HEADING = re.compile(
    r"SPECIFICATION|Spezifikation|TECHNISCHE (?:DATEN|PARAMETER)|TECHNICAL PARAMETERS|ESPECIFICA|SPÉCIFICATION|"
    r"CARACTÉRISTIQUES TECHNIQUES|SPECIFICHE|PARAMETRI TECNICI|SPECIFICATIES|DANE TECHNICZNE|PARAMETRY TECHNICZNE|"
    r"PARÁMETROS TÉCNICOS|PARÂMETROS TÉCNICOS|ТЕХНІЧНІ|Технічні|Специфікаці|仕様|规格|規格|技術參數|技術仕様|사양",
    re.I)
SPEC_TABLE_CLASS = re.compile(r"spec-table|native-spec|manual-spec")
_MD_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.M)
_HTML_HEADING = re.compile(r"<h([1-6])\b([^>]*)>(.*?)</h\1>", re.S | re.I)
_ANCHOR_SPAN = re.compile(r'<span\s+id="([^"]+)"\s*>\s*</span>')
_ID_ATTR = re.compile(r'\bid="([^"]+)"')
_TABLE = re.compile(r"<table\b([^>]*)>(.*?)</table>", re.S | re.I)
_SPEC_ROW = re.compile(r'data-source-layout="spec-row"[^>]*>\s*<p[^>]*>(.*?)</p>\s*<p[^>]*>(.*?)</p>', re.S)
_TAG = re.compile(r"<[^>]+>")
_BREAK = re.compile(r"<br\s*/?>", re.I)

# A number with its unit. A comma before exactly three digits groups thousands; any other comma is a decimal mark.
_QUANTITY = re.compile(
    r"(?<![\w.,])([-−]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|[-−]?\d+(?:[.,]\d+)?)\s?"
    r"(kWh|Wh|mAh|Ah|kW|W|V|A|kg|lbs?|g|mm|cm|in(?:ch(?:es)?)?|°C|℃|°F|Hz|%|cycles?|回|次)(?![A-Za-z])")
QUALIFIERS = (("峰值", r"surge|peak|峰值|瞬間|突波"), ("额定", r"rated|定格|额定|額定"), ("约", r"about|approx|約|约|大约|ca\."),
              ("最大", r"\bmax|最大|maximum"), ("最小", r"\bmin\b|最小|minimum"), ("典型", r"typical|典型"),
              ("≥", r"≥|>="), ("≤", r"≤|<="))


class ExtractionError(ValueError):
    """The inputs cannot give an extraction."""


def clean(fragment: str) -> str:
    """A cell's words as printed: line breaks become " / ", tags go, entities resolve, spaces collapse."""
    text = _TAG.sub("", _BREAK.sub(" / ", fragment))
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def slug(text: str) -> str:
    """The anchor a heading without an explicit id gets: lower case, words joined by hyphens."""
    words = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.U)
    return re.sub(r"[\s_]+", "-", words).strip("-")


def number(text: str) -> float:
    text = text.replace("−", "-")
    if re.fullmatch(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?", text):
        return float(text.replace(",", ""))
    return float(text.replace(",", "."))


def quantities(text: str) -> list[dict[str, Any]]:
    """Every number with its unit, in printed order."""
    found = []
    for match in _QUANTITY.finditer(text):
        unit = match.group(2)
        unit = {"℃": "°C", "lb": "lbs", "cycle": "cycles", "inch": "in", "inches": "in"}.get(unit, unit)
        found.append({"value": _tidy(number(match.group(1))), "unit": unit, "text": match.group(0)})
    return found


def qualifiers(text: str) -> list[str]:
    return [name for name, pattern in QUALIFIERS if re.search(pattern, text, re.I)]


def _tidy(value: float) -> float | int:
    return int(value) if float(value).is_integer() else round(value, 3)


class _TableRows(HTMLParser):
    """The rows of one table, each a list of (tag, inner markup, colspan)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.rows: list[list[tuple[str, str, int]]] = []
        self._cell: list[str] | None = None
        self._tag = ""
        self._span = 1
        self._depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._depth += 1
        if self._depth > 1:
            self._raw(self.get_starttag_text() or "")
            return
        if tag == "tr":
            self.rows.append([])
        elif tag in ("th", "td") and self.rows:
            self._cell, self._tag = [], tag
            self._span = int(dict(attrs).get("colspan") or 1)
        else:
            self._raw(self.get_starttag_text() or "")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._raw(self.get_starttag_text() or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            self._depth -= 1
        if tag in ("th", "td") and self._depth <= 1 and self._cell is not None:
            self.rows[-1].append((self._tag, "".join(self._cell), self._span))
            self._cell = None
        else:
            self._raw(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self._raw(data)

    def handle_entityref(self, name: str) -> None:
        self._raw(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._raw(f"&#{name};")

    def _raw(self, text: str) -> None:
        if self._cell is not None:
            self._cell.append(text)


def table_rows(inner: str) -> list[dict[str, Any]]:
    """Label/value rows of a table. A row of header cells only names the value columns of the rows after it."""
    parser = _TableRows()
    parser.feed(f"<table>{inner}</table>")
    columns: list[str] = []
    rows = []
    for cells in parser.rows:
        if not cells:
            continue
        texts = [clean(markup) for _tag, markup, _span in cells]
        if all(tag == "th" for tag, _m, _s in cells) and len(cells) > 2:
            columns = texts[1:]
            continue
        if len(cells) < 2 or not texts[0]:
            continue
        values = texts[1:]
        if len(values) == 1 or not any(values[1:]):
            rows.append({"label": texts[0], "text": values[0], "column": ""})
            continue
        for index, value in enumerate(values):
            if value:
                column = columns[index] if index < len(columns) else f"#{index + 1}"
                rows.append({"label": texts[0], "text": value, "column": column})
    return rows


def _headings(markup: str) -> list[dict[str, Any]]:
    """Every heading with its level, text, anchor and position, Markdown and HTML alike."""
    found = []
    for match in _MD_HEADING.finditer(markup):
        found.append({"start": match.start(), "level": len(match.group(1)), "text": clean(match.group(2)),
                      "id": _ID_ATTR.search(match.group(2))})
    for match in _HTML_HEADING.finditer(markup):
        found.append({"start": match.start(), "level": int(match.group(1)), "text": clean(match.group(3)),
                      "id": _ID_ATTR.search(match.group(2))})
    found.sort(key=lambda item: item["start"])
    for heading in found:
        explicit = heading.pop("id")
        before = markup[max(0, heading["start"] - 200):heading["start"]]
        spans = _ANCHOR_SPAN.findall(before)
        heading["anchor"] = explicit.group(1) if explicit else (spans[-1] if spans else slug(heading["text"]))
    return found


def _context(headings: list[dict[str, Any]], position: int) -> tuple[list[dict[str, Any]], bool]:
    """The heading path above a position, and whether one of those headings names the specifications."""
    path: list[dict[str, Any]] = []
    for heading in headings:
        if heading["start"] >= position:
            break
        while path and path[-1]["level"] >= heading["level"]:
            path.pop()
        path.append(heading)
    return path, any(SPEC_HEADING.search(heading["text"]) for heading in path)


def spec_rows(markup: str) -> list[dict[str, Any]]:
    """Every specification-table row with its section path, anchor and table and row numbers."""
    headings = _headings(markup)
    blocks = [(match.start(), "table", match) for match in _TABLE.finditer(markup)]
    blocks += [(match.start(), "row", match) for match in _SPEC_ROW.finditer(markup)]
    rows: list[dict[str, Any]] = []
    table_number = 0
    for start, kind, match in sorted(blocks, key=lambda item: item[0]):
        path, under_spec = _context(headings, start)
        if kind == "table":
            if not (SPEC_TABLE_CLASS.search(match.group(1)) or under_spec):
                continue
            table_number += 1
            found = table_rows(match.group(2))
        else:
            if not under_spec and not rows:
                continue
            found = [{"label": clean(match.group(1)), "text": clean(match.group(2)), "column": ""}]
        section = " > ".join(heading["text"] for heading in path)
        anchor = path[-1]["anchor"] if path else ""
        for row in found:
            label = row["label"].rstrip(":：").strip()
            if not label or not row["text"] or len(label) >= 120:
                continue
            rows.append({"label": label, "text": row["text"], "column": row["column"], "section": section,
                         "anchor": anchor, "table": table_number if kind == "table" else 0,
                         "row": sum(1 for r in rows if r["table"] == table_number) + 1,
                         "quantities": quantities(row["text"]), "qualifiers": qualifiers(f"{label} {row['text']}")})
    return rows


# --- the dictionary -------------------------------------------------------------------------------------------


def load_dictionary(path: Path = DICTIONARY) -> list[dict[str, Any]]:
    """The matrix's attribute dictionary; export entries take names, unit, type and scope from the export's file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != DICTIONARY_SCHEMA or not isinstance(data.get("attributes"), list):
        raise ExtractionError(f"{path.name}: expected {DICTIONARY_SCHEMA} with an attributes list")
    export = {item["key"]: item for item in load_export_attributes()}
    seen: set[str] = set()
    out = []
    for order, item in enumerate(data["attributes"], start=1):
        key = item.get("key")
        if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", key) or key in seen:
            raise ExtractionError(f"{path.name}: attribute key {key!r} is missing, malformed or repeated")
        seen.add(key)
        if item.get("export"):
            if key not in export:
                raise ExtractionError(f"{path.name}: {key} is marked export but the export does not define it")
            base = export[key]
            entry = {"key": key, "label": base["label"], "label_en": base["label_en"], "unit": base.get("unit"),
                     "type": base["type"], "applies_to": base.get("applies_to"),
                     "definition": base.get("definition", ""), "parse": "export", "labels": [], "exclude": []}
        else:
            entry = {"key": key, "label": item.get("label"), "label_en": item.get("label_en"),
                     "unit": item.get("unit"), "type": item.get("type"), "applies_to": item.get("applies_to"),
                     "definition": item.get("definition", ""), "parse": item.get("parse"),
                     "labels": list(item.get("labels") or []), "exclude": list(item.get("exclude") or [])}
        entry.update({"group": item.get("group", "其他"), "competitor_field": item.get("competitor_field", ""),
                      "manual_usual": item.get("manual_usual", entry["parse"] != "manual"),
                      "status": item.get("status", "启用"), "order": order})
        if entry["type"] not in VALUE_TYPES or entry["parse"] not in PARSERS or not entry["label"]:
            raise ExtractionError(f"{path.name}: {key} needs a label, a type in {sorted(VALUE_TYPES)} and a parse "
                                  f"in {PARSERS}")
        for pattern in entry["labels"] + entry["exclude"]:
            re.compile(pattern)
        out.append(entry)
    return out


# Labels the export's rules read (tools/rtd/product_matrix.py), so a row they claim is not reported as unmapped.
def _export_labels() -> list[str]:
    from tools.rtd import product_matrix as matrix

    return [*matrix.CAPACITY, *matrix.WEIGHT, *matrix.CYCLES, *matrix.SOLAR, *matrix.IP_RATING, *matrix.OUTPUT,
            matrix.EXPANSION, matrix.AC_ROW, matrix.TOTAL_OUTPUT]


def row_attributes(label: str, attributes: list[dict[str, Any]]) -> list[str]:
    """The dictionary attributes whose printed labels this row's label matches."""
    keys = []
    for attribute in attributes:
        if attribute["parse"] in ("export", "manual"):
            continue
        if any(re.search(p, label, re.I) for p in attribute["labels"]) and not any(
                re.search(p, label, re.I) for p in attribute["exclude"]):
            keys.append(attribute["key"])
    return keys


def _chemistry(text: str) -> str:
    if re.search(r"LiFePO[4₄]|LFP|磷酸铁锂|リン酸鉄", text, re.I):
        return "LiFePO4"
    if re.search(r"\bNMC\b|\bNCM\b|三元", text, re.I):
        return "NMC"
    if re.search(r"Li-?ion|Lithium[- ]ion|リチウムイオン|锂离子|鋰離子", text, re.I):
        return "Li-ion"
    return ""


_RANGE = re.compile(r"([-−]?\s?\d+(?:\.\d+)?)\s*(?:°C|℃)?\s*(?:~|〜|～|–|—|to|至|-)\s*([-−]?\s?\d+(?:\.\d+)?)\s*(?:°C|℃)")
_DIMENSIONS = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:mm|cm|in)?\s*[x×*X]\s*(\d+(?:[.,]\d+)?)\s*(?:mm|cm|in)?\s*[x×*X]\s*"
                         r"(\d+(?:[.,]\d+)?)\s*(mm|cm|in(?:ch(?:es)?)?|\")")


def parse_value(attribute: dict[str, Any], text: str) -> dict[str, Any] | None:
    """The value a row states for one dictionary attribute, or None when it states none the rules can read."""
    kind = attribute["parse"]
    if kind == "max_w":
        watts = [q["value"] for q in quantities(text) if q["unit"] == "W"]
        kilowatts = [q["value"] * 1000 for q in quantities(text) if q["unit"] == "kW"]
        found = watts + kilowatts
        return {"number": _tidy(max(found)), "text": "", "unit": "kW" if not watts else "W"} if found else None
    if kind == "dimensions":
        matches = list(_DIMENSIONS.finditer(text))
        if not matches:
            return None
        preferred = next((m for m in matches if m.group(4) == "mm"), matches[0])
        unit = preferred.group(4).replace('"', "in")
        unit = "in" if unit.startswith("in") else unit
        factor = {"mm": 1, "cm": 10, "in": 25.4}[unit]
        sides = [_tidy(round(number(preferred.group(i)) * factor, 1)) for i in (1, 2, 3)]
        return {"number": None, "text": " × ".join(str(side) for side in sides), "unit": unit}
    if kind == "chemistry":
        found = _chemistry(text)
        return {"number": None, "text": found or text, "unit": ""}
    if kind == "temp_range":
        match = _RANGE.search(text)
        if not match:
            return None
        low, high = (_tidy(number(group.replace(" ", ""))) for group in match.groups())
        return {"number": None, "text": f"{low}~{high}", "unit": "°C"}
    return None


def _qualifier(attribute_key: str, row_qualifiers: list[str]) -> str:
    preferred = {"ac_surge_w": "峰值", "ac_rated_w": "额定"}.get(attribute_key)
    if preferred:
        return preferred
    for name in ("约", "≥", "≤", "最大", "最小", "典型"):
        if name in row_qualifiers:
            return name
    return "无"


# --- editions -------------------------------------------------------------------------------------------------


def _page(target: dict[str, Any]) -> str:
    return f"{target['route']}/{PurePosixPath(target['manual']).stem}.html"


def source_key(target: dict[str, Any]) -> str:
    return f"web/{target['model']}/{target['region']}/{target['lang']}/{target.get('version') or 'unversioned'}"


def _row_markup(rows: list[dict[str, Any]]) -> str:
    """The found rows as one specification table, so the export's rules read every layout the extractor finds."""
    cells = "".join(f"<tr><th>{html.escape(row['label'])}</th><td>{html.escape(_row_text(row))}</td></tr>"
                    for row in rows)
    return f"# SPECIFICATIONS\n<table>{cells}</table>\n"


def _row_text(row: dict[str, Any]) -> str:
    """A row's value as the export reads it; a value under a named column (STC, BNPI) carries the column's name."""
    return f"{row['column']}: {row['text']}" if row["column"] and not row["column"].startswith("#") else row["text"]


def _fact(attribute: dict[str, Any], row: dict[str, Any] | None, label: str, text: str, number_value: Any,
          text_value: str, original_unit: str) -> dict[str, Any]:
    qualifier = "无" if attribute["type"] == "boolean" else _qualifier(attribute["key"], row["qualifiers"] if row
                                                                       else [])
    return {"attribute": attribute["key"], "number": number_value, "text": text_value,
            "unit": attribute.get("unit") or "", "original_unit": original_unit, "qualifier": qualifier,
            "condition": row["column"] if row else "", "label": label, "quote_text": text, "row": row}


def _export_facts(rows: list[dict[str, Any]], attributes: list[dict[str, Any]], category: str | None
                  ) -> list[dict[str, Any]]:
    """The export attributes, read by the export's own rules from every row the extractor found."""
    by_key = {a["key"]: a for a in attributes if a["parse"] == "export"}
    exported, _unknown = read_facts(_row_markup(rows), [a for a in load_export_attributes() if a["key"] in by_key],
                                    category)
    facts = []
    for key, fact in exported.items():
        label, _sep, text = fact["quote"].partition(": ")
        row = next((r for r in rows if r["label"] == label and _row_text(r) == text), None)
        value = fact["value"]
        is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
        facts.append(_fact(by_key[key], row, label, row["text"] if row else text, value if is_number else None,
                           "" if is_number else ("是" if value is True else str(value)),
                           _export_unit(by_key[key], row)))
    return facts


def _export_unit(attribute: dict[str, Any], row: dict[str, Any] | None) -> str:
    """The unit the row prints the export value in: the canonical one unless a weight is printed only in g or lbs."""
    units = [q["unit"] for q in (row["quantities"] if row else [])]
    if attribute["key"] == "weight_kg" and units and "kg" not in units:
        return next((u for u in units if u in ("g", "lbs")), attribute.get("unit") or "")
    return attribute.get("unit") or ""


def _dictionary_fact(attribute: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """A dictionary attribute's value in one edition: the largest number, else the first row that states it."""
    best = None
    for row in rows:
        value = parse_value(attribute, row["text"]) if attribute["key"] in row["attributes"] else None
        if value is not None and (best is None or (value["number"] or 0) > (best[0]["number"] or 0)):
            best = (value, row)
    if best is None:
        return None
    value, row = best
    return _fact(attribute, row, row["label"], row["text"], value["number"], value["text"], value["unit"])


def edition_facts(rows: list[dict[str, Any]], attributes: list[dict[str, Any]],
                  category: str | None) -> list[dict[str, Any]]:
    """The values one edition states: export attributes by the export's rules, the rest by the dictionary's."""
    facts = _export_facts(rows, attributes, category)
    for attribute in attributes:
        if attribute["parse"] not in ("export", "manual"):
            fact = _dictionary_fact(attribute, rows)
            if fact:
                facts.append(fact)
    order = {a["key"]: a["order"] for a in attributes}
    return sorted(facts, key=lambda fact: order[fact["attribute"]])


def _edition(srcdir: Path, target: dict[str, Any], attributes: list[dict[str, Any]], catalog_models: dict[str, Any],
             export_labels: list[str], problems: list[str]) -> dict[str, Any]:
    path = (srcdir / target["route"] / target["manual"]).resolve()
    identity = f"{target['model']}/{target['region']}/{target['lang']}"
    data = path.read_bytes() if path.is_relative_to(srcdir.resolve()) and path.is_file() else None
    if data is None:
        problems.append(f"{identity}: published manual {target['route']}/{target['manual']} is not readable")
    markup = data.decode("utf-8", errors="replace").replace("\r\n", "\n") if data else ""
    rows = spec_rows(markup)
    for row in rows:
        row["attributes"] = row_attributes(row["label"], attributes)
        row["export_label"] = any(re.search(p, row["label"], re.I) for p in export_labels)
    if data is not None and not rows:
        problems.append(f"{identity}: no specification table found")
    category = (catalog_models.get(target["model"]) or {}).get("category")
    facts = edition_facts(rows, attributes, category) if rows else []
    title = next((h["text"] for h in _headings(markup) if h["level"] == 1), "")
    return {"model": target["model"], "market": target["region"], "language": target["lang"],
            "version": target.get("version") or None, "built_at": target.get("built_at") or None,
            "source_key": source_key(target), "page": _page(target),
            "source": f"{target['route']}/{target['manual']}",
            "sha256": hashlib.sha256(data).hexdigest() if data else None, "title": title,
            "rows": rows, "facts": facts}


def compare(editions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per model and market, each attribute whose language editions print different values (or only some print)."""
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for edition in editions:
        groups[(edition["model"], edition["market"])].append(edition)
    found = []
    for (model, market), group in sorted(groups.items()):
        if len(group) < 2:
            continue
        keys = sorted({fact["attribute"] for edition in group for fact in edition["facts"]})
        for key in keys:
            values: dict[str, list[str]] = defaultdict(list)
            for edition in group:
                fact = next((f for f in edition["facts"] if f["attribute"] == key), None)
                shown = "—" if fact is None else (f"{fact['number']}" if fact["number"] is not None else fact["text"])
                values[shown].append(edition["language"])
            if len(values) > 1:
                found.append({"model": model, "market": market, "attribute": key,
                              "values": [{"value": value, "languages": langs} for value, langs in values.items()]})
        counts = {edition["language"]: len(edition["rows"]) for edition in group}
        if len(set(counts.values())) > 1:
            found.append({"model": model, "market": market, "attribute": "_rows", "values": [
                {"value": str(count), "languages": [lang]} for lang, count in sorted(counts.items())]})
    return found


def extract(root: Path, dictionary: Path = DICTIONARY, catalog_models: dict[str, Any] | None = None
            ) -> dict[str, Any]:
    """The extraction for the Web publication under ``root``'s docs directory."""
    docs = Paths(root).docs_dir
    manifest = docs_publish_of(docs) / PathSegments.PUBLISH_MANIFEST_JSON
    targets, built_at = read_publications(manifest)
    if targets is None:
        raise ExtractionError(f"{manifest} is missing or malformed")
    attributes = load_dictionary(dictionary)
    export_labels = _export_labels()
    problems: list[str] = []
    srcdir = docs_publish_web_of(docs)
    ordered = sorted(targets, key=lambda t: (t["model"], t["region"], t["lang"], t["route"]))
    editions = [_edition(srcdir, target, attributes, catalog_models or {}, export_labels, problems)
                for target in ordered]
    unmapped: dict[str, dict[str, Any]] = {}
    for edition in editions:
        for row in edition["rows"]:
            if row["attributes"] or row["export_label"]:
                continue
            entry = unmapped.setdefault(row["label"], {"label": row["label"], "count": 0, "languages": Counter(),
                                                       "example": f"{edition['source_key']}: {row['text'][:80]}"})
            entry["count"] += 1
            entry["languages"][edition["language"]] += 1
    unmapped_list = sorted(({**v, "languages": dict(v["languages"])} for v in unmapped.values()),
                           key=lambda v: (-v["count"], v["label"]))
    names = catalog_names(docs, problems)
    for edition in editions:
        edition["catalog_name"] = names.get((edition["model"], edition["market"]), "")
    differences = compare(editions)
    rows = sum(len(e["rows"]) for e in editions)
    summary = {"editions": len(editions), "markets": len({(e["model"], e["market"]) for e in editions}),
               "models": len({e["model"] for e in editions}), "rows": rows,
               "mapped_rows": sum(1 for e in editions for r in e["rows"] if r["attributes"] or r["export_label"]),
               "facts": sum(len(e["facts"]) for e in editions), "unmapped_labels": len(unmapped_list),
               "differences": len(differences), "problems": len(problems)}
    return {"schema": SCHEMA, "inputs": {
        "publish_manifest": {"path": f"{PathSegments.DOCS}/{PathSegments.PUBLISH}/{PathSegments.PUBLISH_MANIFEST_JSON}",
                             "sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(), "built_at": built_at or None},
        "dictionary": {"schema": DICTIONARY_SCHEMA, "sha256": hashlib.sha256(dictionary.read_bytes()).hexdigest()}},
        "attributes": attributes, "summary": summary, "editions": editions, "differences": differences,
        "unmapped": unmapped_list, "problems": problems}


def catalog_names(docs: Path, problems: list[str]) -> dict[tuple[str, str], str]:
    """Each model and market's name in the portal's manual catalog (the names the 产品矩阵 shows), if readable."""
    settings_path = Path(__file__).resolve().parents[1] / "rtd_portal_assets" / "settings.json"
    try:
        from tools.rtd.portal import catalog

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        products = catalog(docs_publish_web_of(docs), settings)
    except (ImportError, OSError, ValueError, KeyError) as exc:
        problems.append(f"portal manual catalog unreadable, product names left empty: {exc}")
        return {}
    names: dict[tuple[str, str], str] = {}
    for product in products:
        names.setdefault((product["model"], product["region"]), product.get("name") or "")
    return names


def inside_git_work_tree(path: Path) -> bool:
    """Whether a path would land inside any git work tree (extraction output never may)."""
    probe = path.resolve()
    for parent in [probe, *probe.parents]:
        if (parent / ".git").exists():
            return True
    return False


__all__ = ["DICTIONARY", "ExtractionError", "SCHEMA", "clean", "compare", "edition_facts", "extract",
           "inside_git_work_tree", "load_dictionary", "parse_value", "quantities", "row_attributes", "source_key",
           "spec_rows", "table_rows"]
