"""phase2 snapshot CSV -> plain rows/dicts for the IDML exporter (P1).

Data shaping only — no XML. Also owns the small symbol-page copy
localization table (SYMBOL_COPY) and language normalization used to pick
localized snapshot columns.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

SYMBOL_COPY = {
    "en": {
        "title": "MEANING OF SYMBOLS",
        "symbol": "Symbol",
        "meaning": "Meaning",
        "warning": "WARNING",
    },
    "fr": {
        "title": "SIGNIFICATION DES SYMBOLES",
        "symbol": "Symbole",
        "meaning": "Signification",
        "warning": "AVERTISSEMENT",
    },
    "es": {
        "title": "SIGNIFICADO DE LOS SÍMBOLOS",
        "symbol": "Símbolo",
        "meaning": "Significado",
        "warning": "ADVERTENCIA",
    },
}


def normalize_lang(lang: str | None) -> str:
    lang = (lang or "en").strip()
    aliases = {"ja": "jp", "pt-br": "pt-BR", "pt_BR": "pt-BR"}
    return aliases.get(lang, aliases.get(lang.lower(), lang.lower() or "en"))


def symbol_copy(lang: str | None) -> dict[str, str]:
    return SYMBOL_COPY.get(normalize_lang(lang), SYMBOL_COPY["en"])


# The snapshot's localized column suffixes are not uniform across tables
# (lcd/trouble use jp + ukr + both pt-BR/br; Spec_Footnotes/Notes use ja + uk),
# so a language maps to a candidate-suffix tuple, tried in order.
_SUFFIX_CANDIDATES = {
    "jp": ("jp", "ja"),
    "uk": ("uk", "ukr"),
    "pt-BR": ("pt-BR", "br"),
    "zh": ("zh", "cn"),
}


def _lang_suffixes(lang: str | None) -> tuple[str, ...]:
    lang = normalize_lang(lang)
    return _SUFFIX_CANDIDATES.get(lang, (lang,))


def _localized_cell(row: dict, base: str, lang: str | None,
                    fallbacks: tuple[str, ...] = ()) -> str:
    """``{base}_{lang-suffix}`` with per-table suffix aliases, falling back to
    the given source/en columns — the same fallback philosophy as
    load_symbols_rows: untranslated cells ship the source text rather than
    a hole."""
    for suffix in _lang_suffixes(lang):
        value = (row.get(f"{base}_{suffix}") or "").strip()
        if value:
            return value
    for col in fallbacks:
        value = (row.get(col) or "").strip()
        if value:
            return value
    return ""


# Footnote ① markers — MIRRORS tools/csv_pages/renderers_spec_parser.py
# (_footnote_marker_for_order / _parse_footnote_refs / _append_footnote_markers),
# parity is test-enforced so the IDML spec page can never drift from the PDF.
_CIRCLED_NUMBER_MARKERS = {
    1: "\u2460", 2: "\u2461", 3: "\u2462", 4: "\u2463", 5: "\u2464",
    6: "\u2465", 7: "\u2466", 8: "\u2467", 9: "\u2468", 10: "\u2469",
}
_LEGACY_FOOTNOTE_PREFIX_RE = re.compile(r"^(?:[\u2460-\u2473]|\(\d+\)|\d+\.)\s*")


def _footnote_marker_for_order(order: float) -> str:
    normalized = int(order)
    if normalized <= 0:
        return ""
    return _CIRCLED_NUMBER_MARKERS.get(normalized, f"({normalized})")


def _parse_footnote_refs(value: str) -> list[str]:
    refs: list[str] = []
    for token in (value or "").split(","):
        item = token.strip()
        if item and item not in refs:
            refs.append(item)
    return refs


def _append_footnote_markers(text: str, refs: list[str], marker_by_id: dict[str, str]) -> str:
    if not text:
        return text
    markers = "".join(marker_by_id.get(ref, "") for ref in refs if marker_by_id.get(ref, ""))
    if not markers:
        return text
    return f"{text}{markers}"


def _target_matches(row: dict, model: str, region: str) -> bool:
    if row.get("Is_Latest") != "TRUE" or row.get("Enabled", "TRUE") == "FALSE":
        return False
    models = [m.strip() for m in (row.get("Model") or "").split(",") if m.strip()]
    if models and model not in models and "ALL" not in models:
        return False
    regions = [x.strip() for x in (row.get("Region") or "").split(",") if x.strip()]
    if regions and region not in regions and "ALL" not in regions:
        return False
    return True


def load_footnote_markers(data_root: Path, model: str, region: str) -> dict[str, str]:
    """Footnote_id -> ① marker for the target, from Spec_Footnotes.csv."""
    path = data_root / "Spec_Footnotes.csv"
    if not path.exists():
        return {}
    markers: dict[str, str] = {}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        if not _target_matches(r, model, region):
            continue
        footnote_id = (r.get("Footnote_id") or "").strip()
        marker = _footnote_marker_for_order(float(r.get("Footnote_order") or 0))
        if footnote_id and marker:
            markers[footnote_id] = marker
    return markers


def load_spec_sections(data_root: Path, model: str, region: str,
                       lang: str = "en") -> list[dict]:
    doc_key = f"{model}_{region}"
    path = data_root / "Spec_Master.csv"
    rows = [
        r for r in csv.DictReader(path.open(encoding="utf-8"))
        if r.get("document_key") == doc_key
        and r.get("Is_Latest") == "TRUE"
        and r.get("Page") == "specifications"
    ]
    rows.sort(key=lambda r: (float(r.get("Section_order") or 0),
                             float(r.get("Row_order") or 0),
                             float(r.get("Line_order") or 0)))
    marker_by_id = load_footnote_markers(data_root, model, region)
    sections: list[dict] = []
    # rows sharing (Section, Row_order) merge into one multi-line value cell
    for r in rows:
        title = (r.get("Section") or "").strip()
        if not sections or sections[-1]["title"] != title:
            sections.append({"title": title, "rows": []})
        label = _append_footnote_markers(
            _localized_cell(r, "Row_label", lang, ("Row_label_source",)),
            _parse_footnote_refs(r.get("Row_label_footnote_refs") or ""), marker_by_id)
        param = _append_footnote_markers(
            _localized_cell(r, "Param", lang, ("Param_source",)),
            _parse_footnote_refs(r.get("Param_footnote_refs") or ""), marker_by_id)
        value = _append_footnote_markers(
            _localized_cell(r, "Value", lang, ("Value_source",)),
            _parse_footnote_refs(r.get("Value_footnote_refs") or ""), marker_by_id)
        line = f"{param}: {value}" if param else value
        sec_rows = sections[-1]["rows"]
        if sec_rows and sec_rows[-1][0] == label and float(r.get("Line_order") or 1) > 1:
            sec_rows[-1] = (label, sec_rows[-1][1] + "\n" + line)
        else:
            sec_rows.append((label, line))
    return sections


def load_lcd_rows(data_root: Path, model: str, lang: str = "en") -> list[dict]:
    """LCD icon table rows for one model: no / icon path / name / description."""
    path = data_root / "lcd_icons_blocks.csv"
    out: list[dict] = []
    for r in csv.DictReader(path.open(encoding="utf-8")):
        if r.get("Is_latest") != "TRUE":
            continue
        models = [m.strip() for m in (r.get("Model") or "").split(",")]
        if model not in models:
            continue
        out.append({
            "no": (r.get("No.") or "").strip(),
            "figure": (r.get("figure") or "").strip(),
            "name": _localized_cell(r, "icon", lang, ("icon_en",)),
            "desc": _localized_cell(r, "icon_desc", lang, ("icon_desc_en",)),
        })
    out.sort(key=lambda x: float(x["no"] or 0))
    return out


def load_spec_annotations(data_root: Path, model: str, region: str,
                          lang: str = "en") -> list[str]:
    """Spec-page footnotes + notes for the target — the master prints them
    under the spec tables (user-reported as missing)."""
    out: list[str] = []
    for fname, order_col in (("Spec_Footnotes.csv", "Footnote_order"),
                             ("Spec_Notes.csv", "Note_order")):
        path = data_root / fname
        if not path.exists():
            continue
        rows: list[tuple[float, str]] = []
        for r in csv.DictReader(path.open(encoding="utf-8")):
            if r.get("Is_Latest") != "TRUE" or r.get("Enabled", "TRUE") == "FALSE":
                continue
            models = [m.strip() for m in (r.get("Model") or "").split(",") if m.strip()]
            if models and model not in models and "ALL" not in models:
                continue
            regions = [x.strip() for x in (r.get("Region") or "").split(",") if x.strip()]
            if regions and region not in regions and "ALL" not in regions:
                continue
            text = _localized_cell(r, "Text", lang, ("Text_en",))
            if text and fname == "Spec_Footnotes.csv":
                # PDF parity: the footnote line under the tables carries the
                # same ① marker its referencing cells display.
                order = float(r.get(order_col) or 0)
                text = f"{_footnote_marker_for_order(order)} " \
                       f"{_LEGACY_FOOTNOTE_PREFIX_RE.sub('', text, count=1).strip()}".strip()
            if text:
                rows.append((float(r.get(order_col) or 0), text))
        out.extend(t for _, t in sorted(rows))
    return out


def load_symbols_rows(data_root: Path, lang: str = "en") -> tuple[list[tuple[str, str]], list[dict]]:
    """symbols_blocks.csv -> localized (signal rows [label, meaning], icon rows)."""
    path = data_root / "symbols_blocks.csv"
    signals: list[tuple[str, str]] = []
    icons: list[dict] = []
    lang = normalize_lang(lang)
    label_col = f"label_{lang}"
    text_col = f"text_{lang}"
    with path.open(encoding="utf-8") as fh:
        rows = [
            r for r in csv.DictReader(fh)
            if r.get("Is_Latest", r.get("Is_latest")) == "TRUE"
        ]
    rows.sort(key=lambda r: float(r.get("order") or 0))
    for r in rows:
        text = ((r.get(text_col) or "").strip()
                or (r.get("text_en") or "").strip())
        if r.get("block_type") == "signal_row":
            if text:
                label = ((r.get(label_col) or "").strip()
                         or (r.get("label_en") or "").strip())
                signals.append((label, text))
        elif r.get("block_type") == "table_row":
            icons.append({
                "symbol_key": (r.get("symbol_key") or "").strip(),
                "order": (r.get("order") or "").strip(),
                "figure": (r.get("image_path") or "").strip(),
                "text": text,
            })
    return signals, icons


def load_trouble_rows(data_root: Path, model: str, region: str,
                      lang: str = "en") -> list[tuple[str, str]]:
    path = data_root / "troubleshooting_blocks.csv"
    out: list[tuple[str, str]] = []
    for r in csv.DictReader(path.open(encoding="utf-8")):
        if r.get("Is_latest") != "TRUE":
            continue
        models = [m.strip() for m in (r.get("Model") or "").split(",") if m.strip()]
        if models and model not in models and "ALL" not in models:
            continue
        regions = [x.strip() for x in (r.get("Region") or "").split(",") if x.strip()]
        if regions and region not in regions and "ALL" not in regions:
            continue
        out.append(((r.get("error_code") or "").strip(),
                    _localized_cell(r, "corrective_measures", lang,
                                    ("corrective_measures_en",))))
    return out
