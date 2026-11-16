"""Walk every published web manual and capture every specification-table row (step 1).

Adapted from auto-manual tools/rtd/product_matrix.py (spec heading detection, th/td pairing,
data-source-layout="spec-row" lists, _clean/<br> handling), generalised to every table, every
language and every manual instead of ~10 figures from one manual per model.

Read-only on the repositories. Usage:
    python parse_manuals.py <Hello-Docs root> <out dir>
"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

LINE_SEP = " | "  # printed line / paragraph break inside one cell

# Section headings that open a specification section (all published languages).
SPEC_HEADING = re.compile(
    r"SPECIFICATION|TECHNICAL PARAMETER|TECHNISCHE (SPEZIFIKATION|DATEN|PARAMETER|SPECIFICATIE)|ELEKTRISCHE DATEN"
    r"|ESPECIFICACION|ESPECIFICAÇ|SP[ÉE]CIFICATION|CARACT[ÉE]RISTIQUES TECHNIQUES|SPECIFICHE|PARAMETRI TECNICI"
    r"|SPECIFICATIES|SPECYFIKACJA|DANE TECHNICZNE|PARAMETRY TECHNICZNE|ТЕХНІЧНІ (ХАРАКТЕРИСТИКИ|ПАРАМЕТРИ)"
    r"|PAR[AÁÂ]METROS T[EÉ]CNICOS|SPEZIFIKATION|СПЕЦИФІКАЦІ"
    r"|仕様|规格|規格|技术参数|技術參數|사양|Specificaties", re.I)
# Spec-class tables outside the spec section that give usage or charge-time estimates, not ratings.
RUNTIME_HEADING = re.compile(r"目安|時間|时间|time|zeit|tiempo|temps|tempo|tijd|czas|час|runtime|working hours|trouble|error|故障|エラー", re.I)
# Headings outside the spec section whose tables are specification-like.
SPEC_LIKE_HEADING = re.compile(
    r"charg|recharg|laden|ladung|carga|recharge|ricaric|opla|ładow|заряд|充電|充电|目安|"
    r"\\bports?\\b|\\bpuertos?\\b|\\bportas?\\b|interface|\\bconnect|anschl|conex|collega|aansluit|złącz|підключ|接続|接口|"
    r"\bUPS\b|\bEPS\b|\bUSV\b|\bASI\b|\bSAI\b|ДБЖ|无间断|無停電|不断电|"
    r"expan|erweit|ampli|espans|uitbrei|rozszerz|розшир|拡張|扩展|battery pack|"
    r"compatib|kompatyb|kompatib|сумісн|互換|兼容|warrant|garant|gwaranc|гаранті|保証|保修|"
    r"solar|ソーラー|太阳能|working time|runtime|usage time|"
    r"同梱品|包装清单|包裝清單|package list|in the box|what's in|lieferumfang|contenu de la bo|contenido|contenuto|inhoud|zawarto|комплект", re.I)
NOT_SPEC_LIKE_HEADING = re.compile(r"LCD|display|écran|pantalla|anzeige|schermo|wyświetl|дисплей|液晶|显示|symbol|safety|sicherheit|"
                                   r"seguridad|sécurité|sicurezza|veiligheid|bezpiecz|безпек|安全|trouble|störung|dépannage|"
                                   r"solución|risoluzione|problemen|rozwiązyw|несправн|トラブル|故障", re.I)
# Table classes that are never data tables (callouts, symbol keys, LCD keys, troubleshooting, warranty …).
NON_DATA_CLASS = re.compile(
    r"callout|symbol|signal|lcd|troubleshoot|key-combination|safety|warning|lockup|item-list|warranty|jp-symbol|torque|led\b|native-led",
    re.I)
SPEC_CLASS = re.compile(r"spec", re.I)
STYLE_OPEN, STYLE_CLOSE = re.compile(r"<style", re.I), re.compile(r"</style>", re.I)
MD_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
MD_ANCHOR = re.compile(r"\s*\{#([^}]+)\}\s*$")
SPAN_ID = re.compile(r'^\s*<span id="([^"]+)"></span>\s*$')
MYST_LABEL = re.compile(r"^\(([^)]+)\)=\s*$")
FOOTNOTE_TEXT = re.compile(r"^[\s*※†‡①-⑳⑴-⒇\d,a-z]{1,6}$")


def clean_text(node) -> str:
    """Visible text of a node, line/paragraph breaks as LINE_SEP, whitespace collapsed; <sup>/<sub> kept inline."""
    if node is None:
        return ""
    parts: list[str] = []

    def walk(n):
        if isinstance(n, NavigableString):
            if n.__class__.__name__ in ("Comment", "Declaration", "ProcessingInstruction"):
                return
            parts.append(str(n))
            return
        if not isinstance(n, Tag):
            return
        if n.name in ("style", "script"):
            return
        if n.name == "br":
            parts.append("\n")
            return
        if n.name == "img":
            alt = n.get("alt")
            if alt:
                parts.append(f"[img:{alt}]")
            return
        block = n.name in ("p", "div", "li", "tr")
        if block:
            parts.append("\n")
        for c in n.children:
            walk(c)
        if block:
            parts.append("\n")

    walk(node)
    text = html.unescape("".join(parts))
    lines = [re.sub(r"[ \t\r\f\v\u00a0]+", " ", ln).strip() for ln in text.split("\n")]
    return LINE_SEP.join(ln for ln in lines if ln)


def _is_marker(sup: Tag) -> bool:
    t = sup.get_text("", strip=True)
    if not t:
        return False
    if re.fullmatch(r"[*※†‡①-⑳⑴-⒇]+", t):
        return True
    cls = " ".join(sup.get("class") or [])
    if re.fullmatch(r"\d{1,2}|[a-z]", t):
        if "reference" in cls or "footnote" in cls:
            return True
        prev = sup.previous_sibling
        prev_text = str(prev) if isinstance(prev, NavigableString) else (prev.get_text() if isinstance(prev, Tag) else "")
        return not re.search(r"(m|cm|mm|km|ft|in)\s*$", prev_text or "")  # m², cm³ are exponents
    return False


def sup_markers(node) -> list[str]:
    if node is None:
        return []
    out = [s.get_text("", strip=True) for s in node.find_all("sup") if _is_marker(s)]
    raw = node.get_text("", strip=False)
    for m in re.finditer(r"[①-⑳※]", raw):
        if m.group(0) not in out:
            out.append(m.group(0))
    return out


def text_without_sup(node) -> str:
    if node is None:
        return ""
    clone = BeautifulSoup(str(node), "html.parser")
    for s in clone.find_all("sup"):
        if _is_marker(s):
            s.decompose()
    t = clean_text(clone)
    return re.sub(r"[①-⑳]|※$", "", t).strip()


def strip_heading_markup(raw: str) -> tuple[str, str]:
    anchor = ""
    m = MD_ANCHOR.search(raw)
    if m:
        anchor, raw = m.group(1), raw[: m.start()]
    soup = BeautifulSoup(raw, "html.parser")
    span = soup.find(id=True)
    if span is not None and not anchor:
        anchor = span.get("id", "")
    text = clean_text(soup).replace(LINE_SEP, " ")
    return re.sub(r"\\(['\"])", r"\1", text).strip(), anchor


def chunk_events(text: str):
    """Yield ('md_heading', level, text, anchor, line) and ('html', fragment, start_line)."""
    lines = text.split("\n")
    in_style = False
    buf: list[str] = []
    buf_start = 1
    pending_anchor = ""
    for i, line in enumerate(lines, 1):
        if in_style:
            if STYLE_CLOSE.search(line):
                in_style = False
            continue
        if STYLE_OPEN.search(line) and not STYLE_CLOSE.search(line):
            in_style = True
            continue
        m = MD_HEADING.match(line)
        if m:
            if buf:
                yield ("html", "\n".join(buf), buf_start)
                buf = []
            heading, anchor = strip_heading_markup(m.group(2))
            yield ("md_heading", len(m.group(1)), heading, anchor or pending_anchor, i)
            pending_anchor = ""
            buf_start = i + 1
            continue
        sm = SPAN_ID.match(line) or MYST_LABEL.match(line)
        if sm:
            pending_anchor = sm.group(1)
        elif line.strip():
            pending_anchor = ""
        if not buf:
            buf_start = i
        buf.append(line)
    if buf:
        yield ("html", "\n".join(buf), buf_start)


def top_level_items(soup):
    """HTML headings, spec-title divs, spec-row divs and outermost tables in document order."""
    for node in soup.descendants:
        if not isinstance(node, Tag):
            continue
        if node.find_parent("table") is not None:
            continue
        if node.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            yield ("html_heading", node)
        elif node.name == "table":
            yield ("table", node)
        elif node.get("data-source-layout") == "spec-title":
            yield ("spec_title", node)
        elif node.get("data-source-layout") == "spec-row":
            yield ("spec_row", node)


def direct_rows(table: Tag):
    rows = []
    for tr in table.find_all("tr"):
        if tr.find_parent("table") is table:
            rows.append(tr)
    return rows


def cells_of(tr: Tag):
    return [c for c in tr.find_all(["th", "td"], recursive=False)]


def is_label_cell(c: Tag, index: int) -> bool:
    cls = " ".join(c.get("class") or [])
    return c.name == "th" or "label" in cls or "native-key" in cls or index == 0


def parse_table(table: Tag):
    """Yield dicts per (row, value column). Keeps rowspan continuations and in-table sub-headings."""
    rows = direct_rows(table)
    if not rows:
        return
    caption = table.find("caption")
    col_headers: list[str] = []
    carry_label = None  # (label_cell, remaining)
    subheading = ""
    max_cols = max(len(cells_of(r)) for r in rows)
    for r_index, tr in enumerate(rows):
        cells = cells_of(tr)
        if not cells:
            continue
        texts = [clean_text(c) for c in cells]
        # Header row: every cell a th without scope=row, or the first row of a multi-column table inside <thead>.
        in_thead = tr.find_parent("thead") is not None
        header_like = len(cells) >= 3 and all(t and not re.search(r"\d", t.replace("STC", "").replace("BNPI", "")) or re.fullmatch(r"(STC|BNPI|NMOT)\*?", t or "") for t in texts[1:]) \
            and all(len(t) < 25 for t in texts[1:]) and not (carry_label is not None and carry_label[1] > 0)
        if ((in_thead or all(c.name == "th" and c.get("scope") != "row" for c in cells)) and len(cells) > 1 and r_index == 0) or header_like:
            col_headers = texts
            yield {"row_type": "header", "label": texts[0], "label_clean": texts[0], "value": LINE_SEP.join(texts[1:]),
                   "col_header": "", "markers": [], "subheading": "", "col_index": 0, "row_index": r_index,
                   "rowspan_cont": False}
            continue
        span = int(cells[0].get("colspan") or 1)
        if carry_label is not None and carry_label[1] > 0:
            label_cell = carry_label[0]
            carry_label = (label_cell, carry_label[1] - 1)
            for j, c in enumerate(cells):
                yield row_dict(label_cell, c, r_index, j + 1, col_headers, subheading, cont=True)
            continue
        if len(cells) == 1:
            if span >= 2 or (cells[0].name == "th" and max_cols >= 2):
                subheading = texts[0]
                yield {"row_type": "subheading", "label": texts[0], "label_clean": text_without_sup(cells[0]),
                       "value": "", "col_header": "", "markers": sup_markers(cells[0]), "subheading": "",
                       "col_index": 0, "row_index": r_index, "rowspan_cont": False}
            else:
                yield row_dict(None, cells[0], r_index, 1, col_headers, subheading)
            continue
        label_cell, values = cells[0], cells[1:]
        rs = int(label_cell.get("rowspan") or 1)
        if rs > 1:
            carry_label = (label_cell, rs - 1)
        # th + empty td (group label row) -> in-table sub-heading
        if all(not clean_text(v) for v in values) and clean_text(label_cell):
            subheading = clean_text(label_cell)
            yield {"row_type": "subheading", "label": subheading, "label_clean": text_without_sup(label_cell),
                   "value": "", "col_header": "", "markers": sup_markers(label_cell), "subheading": "",
                   "col_index": 0, "row_index": r_index, "rowspan_cont": False}
            continue
        for j, v in enumerate(values):
            yield row_dict(label_cell, v, r_index, j + 1, col_headers if len(values) > 1 else [], subheading)
    _ = caption


def row_dict(label_cell, value_cell, r_index, col_index, col_headers, subheading, cont=False):
    label = clean_text(label_cell) if label_cell is not None else ""
    markers = sup_markers(label_cell) + sup_markers(value_cell)
    header = col_headers[col_index] if col_headers and col_index < len(col_headers) else ""
    return {"row_type": "continuation" if cont else ("pair" if label_cell is not None else "value_only"),
            "label": label, "label_clean": text_without_sup(label_cell) if label_cell is not None else "",
            "value": clean_text(value_cell), "col_header": header, "markers": list(dict.fromkeys(markers)),
            "subheading": subheading, "col_index": col_index, "row_index": r_index, "rowspan_cont": cont}


def classify_table(table: Tag, in_spec: bool, heading_text: str) -> str:
    cls = " ".join(table.get("class") or [])
    if SPEC_CLASS.search(cls) and in_spec:
        return "spec_section"
    if in_spec and not NON_DATA_CLASS.search(cls):
        return "spec_section"
    if in_spec:
        return "skip_non_data_in_spec"
    if SPEC_CLASS.search(cls):
        return "spec_like_elsewhere" if RUNTIME_HEADING.search(heading_text) else "spec_class_elsewhere"
    if NON_DATA_CLASS.search(cls):
        return "skip_non_data"
    rows = direct_rows(table)
    widths = [len(cells_of(r)) for r in rows]
    if not rows:
        return "skip_empty"
    last = heading_text.split(" > ")[-1]
    if SPEC_LIKE_HEADING.search(last) and not NOT_SPEC_LIKE_HEADING.search(last):
        return "spec_like_elsewhere"
    _ = widths
    return "skip_other"


MODEL_IN_HEADING = re.compile(r"(?:Model|Modelo|Modèle|Modell|Modello|Модель|型番|型号)\s*[:：]?\s*([A-Z]{1,4}\d?-?[A-Z0-9][A-Z0-9-]{2,})")
SEPARATE = re.compile(r"SOLD SEPARATELY|SE VENDE POR SEPARADO|VENDU S[ÉE]PAR[ÉE]MENT|SEPARAT ERH|VENDUTO SEPARATAMENTE|"
                      r"APART VERKRIJGBAAR|SPRZEDAWAN|ПРОДАЄТЬСЯ ОКРЕМО|別売|另售|单独出售", re.I)
BRACKET_NAME = re.compile(r"【([^】]+)】")
PAREN_SPEC = re.compile(r"\((Jackery [^)]+)\)")


def described_product(section_path: str) -> str:
    """The product a spec block describes when a heading names one (bundles, accessories sold separately)."""
    label = ""
    for part in section_path.split(" > "):
        m = MODEL_IN_HEADING.search(part)
        if m:
            label = m.group(1)
            continue
        b = BRACKET_NAME.search(part) or PAREN_SPEC.search(part)
        if b:
            label = b.group(1).strip()
            continue
        if SEPARATE.search(part):
            label = SEPARATE.sub("", part).strip(" -—()（）")
    return label


def edition_label(meta: dict) -> str:
    """The web edition a row was read from: publish date of the web build (publish_meta built_at).
    publish_meta 'version' is a pipeline build label (date, commit and channel), not a printed edition, so it is
    summarised in the report rather than copied into every row."""
    return f"web build {meta.get('built_at', '')[:10]}" if meta.get("built_at") else ""


def main(root: Path, out: Path) -> None:
    web = root / "docs" / "publish" / "sources" / "web"
    manifest = json.loads((root / "docs" / "publish" / "publish_manifest.json").read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    rows_out, tables_out, manuals_out = [], [], []
    for t in manifest["targets"]:
        route = web / t["route"]
        md = route / t["manual"]
        meta_path = route / "publish_meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
        text = md.read_text(encoding="utf-8", errors="replace")
        md_stack: list[tuple[int, str, str]] = []
        spec_tables = 0
        table_idx = 0
        specrow_idx = 0
        n_rows = 0
        file_rel = f"docs/publish/sources/web/{t['route']}/{t['manual']}"

        # Spec region: opened by a spec heading at level L; a later heading at level <= L keeps it open only
        # when the next table is a spec-class table (spec groups printed as sibling headings).

        state = {"region": None, "md_base": 0, "html_sub": ("", ""), "spec_seen": False}

        def ctx():
            region = state["region"]
            path = " > ".join(h[1] for h in md_stack)
            anchor = next((h[2] for h in reversed(md_stack) if h[2]), "")
            in_spec = region is not None and not region["candidate"]
            spec_h = region["heading"] if region else ""
            return path, anchor, in_spec, spec_h

        def on_heading(level: int, htext: str, anchor: str) -> None:
            while md_stack and md_stack[-1][0] >= level:
                md_stack.pop()
            md_stack.append((level, htext, anchor))
            state["html_sub"] = ("", "")
            region = state["region"]
            if SPEC_HEADING.search(htext):
                state["spec_seen"] = True
                state["region"] = {"level": level, "heading": htext, "candidate": False}
            elif region is not None:
                if region["candidate"]:
                    state["region"] = None
                elif level <= region["level"]:
                    region["candidate"] = True

        for ev in chunk_events(text):
            if ev[0] == "md_heading":
                _, level, htext, anchor, _line = ev
                state["md_base"] = level
                on_heading(level, htext, anchor)
                continue
            soup = BeautifulSoup(ev[1], "html.parser")
            for kind, node in top_level_items(soup):
                if kind == "html_heading":
                    htext = clean_text(node).replace(LINE_SEP, " ")
                    inner = node.find(id=True)
                    anchor_h = node.get("id", "") or (inner.get("id", "") if inner is not None else "")
                    on_heading(state["md_base"] + int(node.name[1]), htext, anchor_h)
                    continue
                if kind == "spec_title":
                    state["html_sub"] = (clean_text(node).replace(LINE_SEP, " "), node.get("id", ""))
                    continue
                region = state["region"]
                path, anchor, in_spec, spec_h = ctx()
                if region is not None and region["candidate"]:
                    is_spec_cls = kind == "spec_row" or bool(SPEC_CLASS.search(" ".join(node.get("class") or [])))
                    if is_spec_cls:
                        region["candidate"] = False
                    else:
                        state["region"] = None
                    path, anchor, in_spec, spec_h = ctx()
                html_sub = state["html_sub"]
                in_spec_eff = in_spec
                section_path = path + (f" > {html_sub[0]}" if html_sub[0] else "")
                base = {"model": t["model"], "region": t["region"], "language": t["lang"],
                        "edition_version": edition_label(meta),
                        "source_file": file_rel, "section_path": section_path,
                        "spec_section_heading": spec_h, "anchor_id": html_sub[1] or anchor,
                        "html_subheading": html_sub[0], "described_product": described_product(section_path)}
                if kind == "spec_row":
                    ps = node.find_all("p", recursive=False) or node.find_all("p")
                    if len(ps) < 2:
                        continue
                    specrow_idx += 1
                    n_rows += 1
                    rows_out.append({**base, "table_kind": "spec_section" if in_spec_eff else "spec_class_elsewhere",
                                     "table_index": "specrow-list", "table_class": "data-source-layout=spec-row",
                                     "row_index": specrow_idx, "row_type": "pair", "col_index": 1, "col_header": "",
                                     "table_subheading": "", "under_table_subheading": "no",
                                     "row_label": clean_text(ps[0]), "row_label_clean": text_without_sup(ps[0]).rstrip(":：").strip(),
                                     "value_text": LINE_SEP.join(clean_text(p) for p in ps[1:]),
                                     "footnote_markers": " ".join(sup_markers(node)), "rowspan_continuation": "no"})
                    continue
                table_idx += 1
                kind_t = classify_table(node, in_spec_eff, section_path)
                cls = " ".join(node.get("class") or [])
                n_direct = len(direct_rows(node))
                tables_out.append({**base, "table_index": table_idx, "table_class": cls, "table_kind": kind_t,
                                   "n_tr": n_direct})
                if kind_t.startswith("skip"):
                    continue
                if kind_t == "spec_section":
                    spec_tables += 1
                for r in parse_table(node):
                    n_rows += 1
                    rows_out.append({**base, "table_kind": kind_t, "table_index": table_idx, "table_class": cls,
                                     "row_index": r["row_index"], "row_type": r["row_type"], "col_index": r["col_index"],
                                     "col_header": r["col_header"], "table_subheading": r["subheading"],
                                     "under_table_subheading": "yes" if r["subheading"] else "no",
                                     "row_label": r["label"], "row_label_clean": r["label_clean"].rstrip(":：").strip(),
                                     "value_text": r["value"], "footnote_markers": " ".join(r["markers"]),
                                     "rowspan_continuation": "yes" if r["rowspan_cont"] else "no"})
        manuals_out.append({"model": t["model"], "region": t["region"], "language": t["lang"],
                            "edition_version": edition_label(meta), "built_at": meta.get("built_at", ""),
                            "source_file": file_rel, "spec_heading_found": "yes" if state["spec_seen"] else "no",
                            "spec_tables": spec_tables, "rows_captured": n_rows,
                            "spec_section_rows": sum(1 for r in rows_out if r["source_file"] == file_rel
                                                     and r["table_kind"] == "spec_section")})
    write_csv(out / "work_spec_rows_raw.csv", rows_out)
    write_csv(out / "work_tables_inventory.csv", tables_out)
    write_csv(out / "work_manuals.csv", manuals_out)
    print(f"manuals={len(manuals_out)} rows={len(rows_out)} tables={len(tables_out)}")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fields = list(rows[0].keys())
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
