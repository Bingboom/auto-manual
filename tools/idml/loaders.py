"""phase2 snapshot CSV -> plain rows/dicts for the IDML exporter (P1).

Data shaping only — no XML. Also owns the small symbol-page copy
localization table (SYMBOL_COPY) and language normalization used to pick
localized snapshot columns.
"""
from __future__ import annotations

import csv
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


def load_spec_sections(data_root: Path, model: str, region: str) -> list[dict]:
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
    sections: list[dict] = []
    # rows sharing (Section, Row_order) merge into one multi-line value cell
    for r in rows:
        title = (r.get("Section") or "").strip()
        if not sections or sections[-1]["title"] != title:
            sections.append({"title": title, "rows": []})
        label = (r.get("Row_label_source") or "").strip()
        param = (r.get("Param_source") or "").strip()
        value = (r.get("Value_source") or "").strip()
        line = f"{param}: {value}" if param else value
        sec_rows = sections[-1]["rows"]
        if sec_rows and sec_rows[-1][0] == label and float(r.get("Line_order") or 1) > 1:
            sec_rows[-1] = (label, sec_rows[-1][1] + "\n" + line)
        else:
            sec_rows.append((label, line))
    return sections


def load_lcd_rows(data_root: Path, model: str) -> list[dict]:
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
            "name": (r.get("icon_en") or "").strip(),
            "desc": (r.get("icon_desc_en") or "").strip(),
        })
    out.sort(key=lambda x: float(x["no"] or 0))
    return out


def load_spec_annotations(data_root: Path, model: str, region: str) -> list[str]:
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
            text = (r.get("Text_en") or "").strip()
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
    rows = [r for r in csv.DictReader(path.open(encoding="utf-8"))
            if r.get("Is_Latest", r.get("Is_latest")) == "TRUE"]
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
            icons.append({"figure": (r.get("image_path") or "").strip(), "text": text})
    return signals, icons


def load_trouble_rows(data_root: Path, model: str, region: str) -> list[tuple[str, str]]:
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
                    (r.get("corrective_measures_en") or "").strip()))
    return out
