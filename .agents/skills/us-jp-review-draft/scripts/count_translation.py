"""Count the new-translation volume of a JP review draft (green units).

  python3 -I count_translation.py <draft.html> <out_dir> [--previous <prev_version_dir>]

Counts every element marked ``data-needs-translation`` = heading | term | name | sentence
(copy with no Japanese corpus). The English source is ``data-previous-english`` when
present -- from JHP-3600C v0.51 on, green units carry a first-pass Japanese draft and keep
the US English in that attribute -- otherwise the element's own (English) text. The
Japanese draft goes into its own column. Word counts leave out [PLACEHOLDER] text and
tokens that start with a digit (values such as 4000W, 20A, 10 ms are spec/R&D
parameters, purple in the draft, not translation work). Writes new-translation-needed.csv
(UTF-8 BOM for Excel), new-translation-needed.xlsx (list + summary sheets) and
new-translation-summary.json.

With ``--previous`` the previous version's new-translation-needed.csv is carried forward:
a unit whose English matches a previous row (in document order; a row counted with the
value spans left out of the English also matches) keeps that row's counts, so the totals
only move by the units added, removed or re-sourced in this version (how the JHP-3600C
draft was maintained); unmatched units are counted afresh.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

KIND = {"heading": "标题", "term": "术语／名称", "name": "配件名称", "sentence": "句子"}


def clean_text(el) -> str:
    e = BeautifulSoup(str(el), "html.parser")
    for z in e.select(".zh-translation, .jp-review, ol, figure"):
        z.decompose()
    return re.sub(r"\s+([.,;:)])", r"\1", re.sub(r"\s+", " ", e.get_text(" ", strip=True))).strip()


def zh_text(z) -> str:
    return re.sub(r"\s+", " ", z.get_text(" ", strip=True)).strip() if z is not None else ""


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def same_unit(prev_en: str, en: str) -> bool:
    """True when the previous row is this unit: same English, or the same English counted with value spans left out."""
    a, b = norm(prev_en), norm(en)
    if not a or a == b:
        return bool(a)
    rest = iter(b)
    return a[:20] == b[:20] and len(a) >= len(b) // 2 and all(ch in rest for ch in a)


def previous_rows(argv: list[str]) -> list[dict]:
    if "--previous" not in argv:
        return []
    path = Path(argv[argv.index("--previous") + 1]) / "new-translation-needed.csv"
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main() -> int:
    soup = BeautifulSoup(Path(sys.argv[1]).read_text(encoding="utf-8"), "html.parser")
    out = Path(sys.argv[2])
    prev, k, carried = previous_rows(sys.argv), 0, 0
    toc = {a["href"][1:]: a.get_text(strip=True) for a in soup.select("aside.toc a") if a.get("href", "").startswith("#")}
    rows = []
    for el in soup.select("[data-needs-translation]"):
        sec = el.find_parent("section")
        while sec is not None and sec.find_parent("section") is not None:
            sec = sec.find_parent("section")
        own = clean_text(el)
        text = re.sub(r"\s+", " ", el.get("data-previous-english", "")).strip() or own
        jp_draft = own if el.get("data-previous-english") else ""
        zh = el.find(class_="zh-translation", recursive=False)
        if zh is None and el.name == "span":
            zh = el.parent.find(class_="zh-translation", recursive=False)
        words = [w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9®'’/+\-.]*", re.sub(r"\[[^\]]*\]", " ", text))
                 if not w[0].isdigit()]
        sents = [s for s in re.split(r"(?<=[.!?])\s+", text) if re.search(r"[A-Za-z]", s)]
        kind = el["data-needs-translation"]
        chars = len(text)
        j = next((x for x in range(k, len(prev)) if norm(prev[x]["英文原文"]) == norm(text)), None)
        if j is None:
            j = next((x for x in range(k, min(k + 3, len(prev))) if same_unit(prev[x]["英文原文"], text)), None)
        if j is not None:   # carried forward: keep the previous version's counts for this unit
            k = j + 1
            words = ["w"] * int(prev[j].get("英文词数") or 0)
            sents = ["s"] * int(prev[j].get("句数") or 0)
            chars = int(prev[j].get("英文字符数") or chars)
            carried += 1
        rows.append({
            "章节": toc.get(sec.get("id"), sec.get("id")) if sec is not None else "",
            "类型": KIND.get(kind, kind),
            "英文原文": text,
            "日文初译（待审校）": jp_draft,
            "英文词数": len(words),
            "句数": len(sents) if kind == "sentence" else 0,
            "英文字符数": chars,
            "中文参考": zh_text(zh),
            "可参考的现成日文（近似，非直接复用）": el.get("data-reference-jp", ""),
            "备注": el.get("data-unmatched-reason", ""),
        })
    uniq = {}
    for r in rows:
        uniq.setdefault(r["英文原文"], r)
    summary = {"units": len(rows), "unique_units": len(uniq), "words": sum(r["英文词数"] for r in rows),
               "unique_words": sum(r["英文词数"] for r in uniq.values()), "chars": sum(r["英文字符数"] for r in rows),
               "pending_parameters": len(soup.select(".jp-parameter, [data-editorial-placeholder]")),
               "by_type": {}, "by_chapter": {}}
    for r in rows:
        for key, k in (("by_type", r["类型"]), ("by_chapter", r["章节"])):
            d = summary[key].setdefault(k, {"units": 0, "words": 0})
            d["units"] += 1
            d["words"] += r["英文词数"]

    fields = ["章节", "类型", "英文原文", "日文初译（待审校）", "英文词数", "句数", "英文字符数", "中文参考",
              "可参考的现成日文（近似，非直接复用）", "备注"]
    with open(out / "new-translation-needed.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["序号"] + fields)
        w.writeheader()
        for i, r in enumerate(rows, 1):
            w.writerow({"序号": i, **r})
    wb = Workbook()
    ws = wb.active
    ws.title = "新增翻译清单"
    ws.append(["序号"] + fields)
    for i, r in enumerate(rows, 1):
        ws.append([i] + [r[k] for k in fields])
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="E8F5E9")
    for col, width in zip("ABCDEFGHIJK", (6, 14, 10, 70, 60, 10, 8, 10, 50, 60, 50), strict=False):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    s2 = wb.create_sheet("汇总")
    s2.append(["指标", "数值"])
    for k, v in (("需新增翻译单元（总）", summary["units"]), ("去重后单元", summary["unique_units"]),
                 ("英文词数（总）", summary["words"]), ("英文词数（去重）", summary["unique_words"]),
                 ("英文字符数（总）", summary["chars"]), ("待填参数（非翻译）", summary["pending_parameters"])):
        s2.append([k, v])
    for title, key in (("按类型", "by_type"), ("按章节", "by_chapter")):
        s2.append([])
        s2.append([title, "单元", "词数"])
        for k, d in summary[key].items():
            s2.append([k, d["units"], d["words"]])
    s2.column_dimensions["A"].width = 26
    wb.save(out / "new-translation-needed.xlsx")
    (out / "new-translation-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("units", "unique_units", "words", "unique_words", "chars",
                                               "pending_parameters")}, ensure_ascii=False))
    print(json.dumps(summary["by_chapter"], ensure_ascii=False))
    if prev:
        print(f"carried forward {carried} of {len(rows)} units from {len(prev)} previous rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
