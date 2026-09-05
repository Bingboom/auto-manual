"""phase2 snapshot CSV -> plain rows/dicts for the IDML exporter (P1).

Data shaping only — no XML. Visible page copy remains source-authored; this
module only normalizes languages and selects localized snapshot columns.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from tools.localized_copy import first_text, localized_cell, snapshot_language_suffixes
from .text_clean import VariableSubstituter, clean_cell
from tools.utils.spec_footnotes import (
    append_footnote_markers as _append_footnote_markers,
    footnote_marker_for_order as _footnote_marker_for_order,
    parse_footnote_refs as _parse_footnote_refs,
)


def normalize_lang(lang: str | None) -> str:
    """Compatibility suffix API; canonical language identity stays in the registry."""
    suffixes = snapshot_language_suffixes(lang)
    return suffixes[0] if suffixes else "en"


_LEGACY_FOOTNOTE_PREFIX_RE = re.compile(r"^(?:[\u2460-\u2473]|\(\d+\)|\d+\.)\s*")


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
    titles = load_spec_title_map(data_root, lang)
    for r in rows:
        title = (r.get("Section") or "").strip()
        title = titles.get(title, title)
        if not sections or sections[-1]["title"] != title:
            sections.append({"title": title, "rows": []})
        label = _append_footnote_markers(
            localized_cell(r, "Row_label", normalize_lang(lang), fallback_columns=("Row_label_source",)),
            _parse_footnote_refs(r.get("Row_label_footnote_refs") or ""), marker_by_id)
        param = _append_footnote_markers(
            localized_cell(r, "Param", normalize_lang(lang), fallback_columns=("Param_source",)),
            _parse_footnote_refs(r.get("Param_footnote_refs") or ""), marker_by_id)
        value = _append_footnote_markers(
            localized_cell(r, "Value", normalize_lang(lang), fallback_columns=("Value_source",)),
            _parse_footnote_refs(r.get("Value_footnote_refs") or ""), marker_by_id)
        line = f"{param}: {value}" if param else value
        sec_rows = sections[-1]["rows"]
        if sec_rows and sec_rows[-1][0] == label and float(r.get("Line_order") or 1) > 1:
            sec_rows[-1] = (label, sec_rows[-1][1] + "\n" + line)
        else:
            sec_rows.append((label, line))
    return sections


def load_lcd_rows(data_root: Path, model: str, lang: str = "en", region: str | None = None) -> list[dict]:
    """LCD icon table rows for one model: no / icon path / name / description."""
    path = data_root / "lcd_icons_blocks.csv"
    subst = VariableSubstituter(data_root, model=model, lang=lang, region=region)
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
            "name": clean_cell(localized_cell(r, "icon", normalize_lang(lang), fallback_columns=("icon_en",)), subst),
            "desc": clean_cell(localized_cell(r, "icon_desc", normalize_lang(lang), fallback_columns=("icon_desc_en",)), subst),
        })
    out.sort(key=lambda x: float(x["no"] or 0))
    # The master numbers rows continuously; source "No." values may skip
    # (JE-1000F has no 21), so renumber for display.
    for index, row in enumerate(out, start=1):
        row["no"] = chr(0x245F + index) if index <= 20 else chr(0x323C + index)
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
            text = localized_cell(r, "Text", normalize_lang(lang), fallback_columns=("Text_en",))
            if text and fname == "Spec_Footnotes.csv":
                # The footnote line carries the same ① marker glyph as its
                # referencing cells. Renderers decide its presentation by
                # semantic position: inline references are superscript, while
                # the note-leading marker stays on the note text baseline.
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
        # Symbols retain their single historical suffix, unlike the other loaders.
        text = first_text(r, (text_col,), fallback_columns=("text_en",))
        if r.get("block_type") == "signal_row":
            if text:
                label = first_text(r, (label_col,), fallback_columns=("label_en",))
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
    candidates: list[tuple[str, dict]] = []
    target_model = model.casefold()
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("Is_latest") != "TRUE":
                continue
            models = [m.strip() for m in re.split(r"[,;|]", r.get("Model") or "") if m.strip()]
            model_tokens = {token.casefold() for token in models}
            if target_model in model_tokens:
                model_scope = "specific"
            elif not model_tokens or "all" in model_tokens:
                model_scope = "fallback"
            else:
                continue
            regions = [x.strip() for x in (r.get("Region") or "").split(",") if x.strip()]
            if regions and region not in regions and "ALL" not in regions:
                continue
            candidates.append((model_scope, r))

    specific = [r for scope, r in candidates if scope == "specific"]
    selected = specific or [r for scope, r in candidates if scope == "fallback"]
    out: list[tuple[str, str]] = []
    for r in selected:
        out.append(((r.get("error_code") or "").strip(),
                    clean_cell(localized_cell(r, "corrective_measures", normalize_lang(lang),
                                               fallback_columns=("corrective_measures_en",)))))
    return out


_TITLE_SUFFIX = {"jp": "jp", "ja": "jp", "uk": "uk", "ukr": "uk", "ko": "ko"}


def load_spec_title_map(data_root: Path, lang: str | None) -> dict[str, str]:
    """EN spec section title -> localized title (spec_titles.csv)."""
    suffix = _TITLE_SUFFIX.get((lang or "en").lower(), (lang or "en").lower())
    path = data_root / "spec_titles.csv"
    if suffix == "en" or not path.exists():
        return {}
    out: dict[str, str] = {}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        localized = (r.get(f"title_{suffix}") or "").strip()
        if localized:
            out[(r.get("title_en") or "").strip()] = localized
    return out
