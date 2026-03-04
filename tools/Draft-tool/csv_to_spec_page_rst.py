#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]


# -------------------------
# Schema
# -------------------------

REQUIRED_KEYS_COMMON = [
    "项目代码",
    "Region",
    "Is_Latest",
    "Page",
    "Section",
    "Section_order",
    "Row_key",
    "Line_order",
]

# For EN rendering, Row_label_en is mandatory
REQUIRED_KEYS_EN = [
    "Row_label_en",
    "Value_en",  # if empty, we fallback to Spec_Value, but column should exist
]

# Optional but recommended existing in your master
OPTIONAL_FALLBACK_KEYS = [
    "Param_name",  # cn
    "Spec_Value",
]

# Optional localization keys
LOCALIZED_KEYS = {
    "en": {
        "row_label": "Row_label_en",
        "param": "Param_en",
        "value": "Value_en",
        "footnote_text": "Footnote_text_en",
    },
    "zh": {
        "row_label": "Row_label_zh",
        "param": "Param_zh",
        "value": "Value_zh",
        "footnote_text": "Footnote_text_zh",
    },
}


def _norm_bool(s: str) -> bool:
    return str(s).strip().lower() in ("1", "true", "yes", "y")


def _get(row: Dict[str, str], key: str, default: str = "") -> str:
    v = row.get(key, "")
    if v is None:
        return default
    v = str(v).strip()
    return v if v else default


def escape_latex(s: str) -> str:
    """
    Minimal LaTeX escaping.
    NOTE: For production, you may want a stricter/centralized escape shared across the repo.
    """
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(repl.get(ch, ch) for ch in s)


def ensure_headers(headers: Iterable[str], required: List[str], *, csv_path: Path) -> None:
    hset = set(headers)
    missing = [k for k in required if k not in hset]
    if missing:
        raise SystemExit(f"[schema error] {csv_path}: missing columns: {missing}")


# -------------------------
# Model
# -------------------------

@dataclass(frozen=True)
class SpecLine:
    section: str
    section_order: int
    row_key: str
    row_label: str
    line_order: int
    param: str
    value: str
    footnote_mark: str


@dataclass(frozen=True)
class Footnote:
    mark: str
    text: str


# -------------------------
# Parsing
# -------------------------

def read_spec_lines(
    csv_path: Path,
    *,
    product_code: str,
    region: str,
    page: str,
    lang: str,
    strict: bool,
) -> Tuple[List[SpecLine], List[Footnote]]:
    if lang not in LOCALIZED_KEYS:
        raise SystemExit(f"[error] unsupported lang: {lang}. supported: {list(LOCALIZED_KEYS.keys())}")

    loc = LOCALIZED_KEYS[lang]
    row_label_key = loc["row_label"]
    param_key = loc["param"]
    value_key = loc["value"]
    footnote_text_key = loc["footnote_text"]

    lines: List[SpecLine] = []
    footnote_map: Dict[str, str] = {}

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SystemExit(f"[schema error] {csv_path}: empty header")

        ensure_headers(reader.fieldnames, REQUIRED_KEYS_COMMON, csv_path=csv_path)

        # Language-specific required keys
        if lang == "en":
            ensure_headers(reader.fieldnames, REQUIRED_KEYS_EN, csv_path=csv_path)

        # We don't force these, but we may fallback to them
        # (no hard check)

        for idx, row in enumerate(reader, start=2):  # line number ~ header=1
            if not _norm_bool(_get(row, "Is_Latest")):
                continue
            if _get(row, "项目代码") != product_code:
                continue
            if _get(row, "Region") != region:
                continue
            if _get(row, "Page") != page:
                continue

            section = _get(row, "Section")
            if not section:
                if strict:
                    raise SystemExit(f"[schema error] {csv_path}:{idx}: empty Section")
                else:
                    continue

            row_key = _get(row, "Row_key")
            if not row_key:
                if strict:
                    raise SystemExit(f"[schema error] {csv_path}:{idx}: empty Row_key")
                else:
                    continue

            # Row label: if localized label missing, fallback to EN, then fail/warn
            row_label = _get(row, row_label_key)
            if not row_label:
                row_label = _get(row, "Row_label_en")
            if not row_label:
                if strict:
                    raise SystemExit(f"[schema error] {csv_path}:{idx}: missing row label ({row_label_key}/Row_label_en)")
                else:
                    row_label = "(missing label)"

            # Content fields
            param = _get(row, param_key)
            if not param:
                # fallback to English param, then Chinese Param_name
                param = _get(row, "Param_en", _get(row, "Param_name", ""))

            value = _get(row, value_key)
            if not value:
                # fallback to English value then Spec_Value
                value = _get(row, "Value_en", _get(row, "Spec_Value", ""))
            if not value and strict:
                raise SystemExit(f"[schema error] {csv_path}:{idx}: missing value ({value_key}/Value_en/Spec_Value)")

            footnote_mark = _get(row, "Footnote_mark")
            footnote_text = _get(row, footnote_text_key)
            if footnote_mark and footnote_text:
                # Keep first occurrence (stable)
                footnote_map.setdefault(footnote_mark, footnote_text)

            try:
                section_order = int(_get(row, "Section_order", "99"))
            except ValueError:
                section_order = 99
                if strict:
                    raise SystemExit(f"[schema error] {csv_path}:{idx}: invalid Section_order")

            try:
                line_order = int(_get(row, "Line_order", "1"))
            except ValueError:
                line_order = 1
                if strict:
                    raise SystemExit(f"[schema error] {csv_path}:{idx}: invalid Line_order")

            lines.append(
                SpecLine(
                    section=section,
                    section_order=section_order,
                    row_key=row_key,
                    row_label=row_label,
                    line_order=line_order,
                    param=param,
                    value=value,
                    footnote_mark=footnote_mark,
                )
            )

    # Deterministic ordering for diff stability
    lines.sort(key=lambda x: (x.section_order, x.section, x.row_key, x.line_order))

    # Footnotes: deterministic by mark
    footnotes = [Footnote(mark=k, text=v) for k, v in sorted(footnote_map.items(), key=lambda kv: kv[0])]
    return lines, footnotes


# -------------------------
# Rendering
# -------------------------

def render_section_table_latex(section: str, items: List[SpecLine], *, left_col_ratio: float = 0.32) -> str:
    """
    Render one section as a 2-col table with "merged left cell" effect:
    - Left col: row_label (one cell)
    - Right col: multiple lines of param/value
    """
    # group by (row_key, row_label)
    grouped: Dict[Tuple[str, str], List[SpecLine]] = {}
    for it in items:
        grouped.setdefault((it.row_key, it.row_label), []).append(it)

    # stable ordering by row_key
    rows: List[Tuple[str, List[SpecLine]]] = []
    for (_, row_label), sub in grouped.items():
        sub_sorted = sorted(sub, key=lambda x: x.line_order)
        rows.append((row_label, sub_sorted))

    # Keep deterministic order by row_label text as secondary (row_key order already in initial sort)
    # But grouped loses row_key ordering; rebuild by first appearance order:
    # We'll preserve by scanning items:
    order_keys: List[Tuple[str, str]] = []
    seen = set()
    for it in items:
        key = (it.row_key, it.row_label)
        if key not in seen:
            seen.add(key)
            order_keys.append(key)
    rows = [(row_label, grouped[(row_key, row_label)]) for (row_key, row_label) in order_keys]

    # Build LaTeX
    buf: List[str] = []
    buf.append("")
    buf.append(".. raw:: latex")
    buf.append("")
    buf.append(r"   \vspace{8pt}")
    buf.append(rf"   \noindent\textbf{{{escape_latex(section)}}}\par")
    buf.append(r"   \vspace{4pt}")
    buf.append(r"   \noindent")
    buf.append(rf"   \begin{{tabularx}}{{\textwidth}}{{|p{{{left_col_ratio:.2f}\textwidth}}|X|}}")
    buf.append(r"   \hline")

    for row_label, sub in rows:
        sub_sorted = sorted(sub, key=lambda x: x.line_order)
        first = sub_sorted[0]

        def fmt_line(x: SpecLine) -> str:
            # If param empty, only show value; else "param: value"
            p = (x.param or "").strip()
            v = (x.value or "").strip()
            if p:
                return f"{escape_latex(p)}: {escape_latex(v)}"
            return escape_latex(v)

        # First row prints left label + first right line
        buf.append(rf"   {escape_latex(row_label)} & {fmt_line(first)} \\")
        # Subsequent rows keep left col empty to mimic merged cell
        for extra in sub_sorted[1:]:
            buf.append(rf"    & {fmt_line(extra)} \\")
        buf.append(r"   \hline")

    buf.append(r"   \end{tabularx}")
    buf.append("")
    return "\n".join(buf)


def render_spec_page_rst(
    lines: List[SpecLine],
    footnotes: List[Footnote],
    *,
    lang: str,
    title: Optional[str] = None,
) -> str:
    if not title:
        title = "SPECIFICATIONS" if lang == "en" else "规格参数"

    # group by section
    sections: Dict[str, List[SpecLine]] = {}
    for ln in lines:
        sections.setdefault(ln.section, []).append(ln)

    # stable section order by section_order
    section_names = sorted(
        sections.keys(),
        key=lambda s: min(x.section_order for x in sections[s]) if sections[s] else 99,
    )

    out: List[str] = []
    out.append(title)
    out.append("=" * len(title))
    out.append("")

    for sec in section_names:
        out.append(render_section_table_latex(sec, sections[sec]))
        out.append("")

    # Footnotes block
    if footnotes:
        out.append("")
        out.append(".. raw:: latex")
        out.append("")
        out.append(r"   \vspace{6pt}")
        out.append(r"   \footnotesize")
        for fn in footnotes:
            out.append(rf"   {escape_latex(fn.mark)} {escape_latex(fn.text)}\par")
        out.append(r"   \normalsize")
        out.append("")

    return "\n".join(out).strip() + "\n"


# -------------------------
# CLI
# -------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        description="HB-Docs Spec Page Engine: Spec_Master.csv -> specifications_<lang>.rst"
    )
    p.add_argument("--csv", default=str(ROOT / "Draft-tool" / "data" / "Spec_Master.csv"), help="Spec master CSV path")
    p.add_argument("--product", required=True, help="项目代码 (e.g. HTE152-US)")
    p.add_argument("--region", default="US", help="Region filter (e.g. US/JP/EU)")
    p.add_argument("--page", default="specifications", help="Page id filter (default: specifications)")
    p.add_argument("--lang", default="en", choices=list(LOCALIZED_KEYS.keys()), help="Output language")
    p.add_argument("--strict", action="store_true", help="Strict schema validation (fail fast)")
    p.add_argument("--out", default="", help="Output rst path (default: docs/specifications_<lang>.rst)")
    p.add_argument("--title", default="", help="Page title override")
    args = p.parse_args()

    csv_path = Path(args.csv)
    out_path = Path(args.out) if args.out else (ROOT /"Draft-tool" / "docs" / f"specifications_{args.lang}.rst")

    print("[phase1] validate & load rows...")
    lines, footnotes = read_spec_lines(
        csv_path,
        product_code=args.product,
        region=args.region,
        page=args.page,
        lang=args.lang,
        strict=args.strict,
    )
    if not lines:
        raise SystemExit(
            f"[error] no rows found. filters: product={args.product}, region={args.region}, page={args.page}, lang={args.lang}"
        )

    print("[phase2] render rst...")
    rst = render_spec_page_rst(
        lines,
        footnotes,
        lang=args.lang,
        title=(args.title.strip() or None),
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rst, encoding="utf-8")
    print(f"[write] {out_path}")


if __name__ == "__main__":
    main()