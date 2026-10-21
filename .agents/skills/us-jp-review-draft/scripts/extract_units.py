"""Split the US RTD manual and the JP review draft into comparable content units.

  python3 -I extract_units.py <us_rtd.html> <jp_draft.html> <us_units.json> <jp_units.json> [--group-dir DIR]

A unit is the inline text a block element owns itself (text inside nested blocks
belongs to those blocks), so text in <div>/<strong> cards, LCD cells with an
extra <p>, and figure live labels ([data-source-line]) are all captured. Simple
table rows become one unit ("cell | cell"). JP units carry their Chinese gloss
(`zh`) separately and flag green new-translation units (`.en-new`; the key is still `green_english`).

With --group-dir, also writes one <group>.json per chapter group (see GROUPS)
for the per-group alignment agents.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

BLOCKS = {"p", "li", "ul", "ol", "table", "thead", "tbody", "tr", "td", "th", "div", "h1", "h2", "h3", "h4", "h5",
          "figure", "figcaption", "section", "article", "main", "aside", "header", "footer", "nav", "dl", "dt", "dd",
          "pre", "form", "select", "label", "button"}
SKIP_TAGS = {"style", "script", "pre", "button", "select", "option", "label", "noscript", "nav"}
CHROME = re.compile(r"^(Found an issue\?|Copy context|Email support)")

# US chapter names -> JP draft chapter names; edit when the draft gains chapters.
GROUPS = {
    "g1_safety": (["IMPORTANT SAFETY INFORMATION", "MEANING OF SYMBOLS", "FCC"], ["安全上のご注意", "絵表示の説明"]),
    "g2_box_overview": (["WHAT’S IN THE BOX", "PRODUCT OVERVIEW"], ["同梱品", "各部の名称"]),
    "g3_lcd": (["LCD DISPLAY"], ["液晶画面"]),
    "g4_operations": (["OPERATIONS"], ["使い方"]),
    "g5_ups_connections": (["UNINTERRUPTIBLE POWER SUPPLY (UPS)", "CONNECTIONS"], ["UPS 機能", "接続", "充電方法"]),
    "g6_charging_storage": (["CHARGING", "STORAGE"], ["充電方法"]),
    "g7_troubleshooting": (["TROUBLESHOOTING"], ["トラブルシューティング"]),
    "g8_specs": (["SPECIFICATIONS"], ["主な仕様"]),
    "g9_warranty_contact": (["WARRANTY", "CONTACT US"], ["保証について", "カスタマーサポート"]),
    "g10_app": (["APP SETUP"], ["Jackeryアプリ ユーザーマニュアル"]),
}


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()


def own_inline(el: Tag, zh_mode: str) -> str:
    """Inline text of ``el`` without nested blocks; zh_mode 'exclude' or 'only' for .zh-translation."""
    parts: list[str] = []

    def rec(node: Tag, in_zh: bool) -> None:
        for c in node.children:
            if isinstance(c, NavigableString):
                if c.parent.name not in SKIP_TAGS and (zh_mode == "only") == in_zh:
                    parts.append(str(c))
            elif isinstance(c, Tag):
                if c.name in SKIP_TAGS or c.name in BLOCKS or c.has_attr("data-source-line"):
                    continue
                if c.name == "br":
                    parts.append(" ")
                    continue
                rec(c, in_zh or "zh-translation" in (c.get("class") or []))

    rec(el, False)
    return norm("".join(parts))


def walk_units(root: Tag, is_jp: bool) -> list[dict]:
    found = []
    for el in root.find_all(True):
        if (el.name not in BLOCKS and not el.has_attr("data-source-line")) or el.name in SKIP_TAGS:
            continue
        if any(p.name in SKIP_TAGS for p in el.parents):
            continue
        if el.name in ("td", "th"):
            tr = el.find_parent("tr")
            if tr is not None and not tr.find(["p", "li", "ul", "ol", "div", "table"]):
                if el is not tr.find(["td", "th"]):
                    continue
                cells = tr.find_all(["td", "th"])
                t = " | ".join(own_inline(c, "exclude") for c in cells)
                zh = " | ".join(own_inline(c, "only") for c in cells) if is_jp else ""
                if norm(t.replace("|", "")) or norm(zh.replace("|", "")):
                    found.append((el, t, zh))
                continue
        t = own_inline(el, "exclude")
        zh = own_inline(el, "only") if is_jp else ""
        if t or zh:
            found.append((el, t, zh))
    out, chap, sub = [], None, None
    for el, t, zh in found:
        if el.name == "h1":
            chap, sub = t, None
        if el.name in ("h2", "h3"):
            sub = t
        rec = {"chapter": chap, "section": sub, "tag": el.name, "text": t}
        if is_jp:
            rec["zh"] = zh
            rec["green_english"] = bool(el.find_parent(class_="en-new") or "en-new" in (el.get("class") or [])
                                        or el.find(class_="en-new"))
        out.append(rec)
    return out


def us_units(path: str) -> list[dict]:
    root = BeautifulSoup(Path(path).read_text(encoding="utf-8"), "html.parser").find("article")
    for z in root.select(".headerlink"):
        z.decompose()
    units = [x for x in walk_units(root, False) if x["chapter"] and not CHROME.match(x["text"])]
    for i, x in enumerate(units, 1):
        x["id"] = f"US{i:03d}"
    return units


def jp_units(path: str) -> list[dict]:
    root = BeautifulSoup(Path(path).read_text(encoding="utf-8"), "html.parser").find(id="furo-main-content")
    for z in root.select(".jp-review, figcaption, #jp-review-appendix"):
        z.decompose()
    units = [x for x in walk_units(root, True) if x["chapter"]]
    for i, x in enumerate(units, 1):
        x["id"] = f"JP{i:03d}"
    return units


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("us_html")
    ap.add_argument("jp_html")
    ap.add_argument("us_out")
    ap.add_argument("jp_out")
    ap.add_argument("--group-dir")
    a = ap.parse_args()
    us, jp = us_units(a.us_html), jp_units(a.jp_html)
    json.dump(us, open(a.us_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(jp, open(a.jp_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("US", len(us), dict(Counter(x["chapter"] for x in us)))
    print("JP", len(jp), dict(Counter(x["chapter"] for x in jp)))
    if a.group_dir:
        d = Path(a.group_dir)
        d.mkdir(parents=True, exist_ok=True)
        for g, (uc, jc) in GROUPS.items():
            data = {"us": [x for x in us if x["chapter"] in uc], "jp": [x for x in jp if x["chapter"] in jc]}
            (d / f"{g}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            print(g, len(data["us"]), len(data["jp"]))
        grouped = {c for uc, _ in GROUPS.values() for c in uc}
        left = sorted({x["chapter"] for x in us} - grouped)
        if left:
            print("US chapters in no group (add to GROUPS or record as out of scope):", left)


if __name__ == "__main__":
    main()
