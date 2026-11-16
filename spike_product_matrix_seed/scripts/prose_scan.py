"""Where gap attributes sit outside the spec tables, and what time/version strings a manual prints.

Usage: python prose_scan.py <Hello-Docs root> <out dir>
Writes work_gap_hits.csv (one line per manual x gap attribute with up to 2 snippets) and work_time_strings.csv.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

from parse_manuals import LINE_SEP, chunk_events, clean_text

URL = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\w+")
GAPS = {
    "ac_charge_time": re.compile(r"(?:fully|full|0\s?[-–~]\s?100|0\s?[-–~]\s?80|満充電|フル充電|充满|満タン|vollständig|complètement|completamente|80\s?%).{0,60}?\d+(?:[.,]\d+)?\s?(?:hours?|hrs?|h\b|時間|小时|分|minutes?|min\b|Std|heures?|horas?|ore\b|uur|godz|год)|\d+(?:[.,]\d+)?\s?(?:hours?|hrs?|時間|小时|minutes?|分)\s?.{0,30}?(?:fully charg|full charge|満充電|充满|0-80|80\s?%)", re.I),
    "max_expandable_capacity_wh": re.compile(r"(?:expand|expandable|up to|bis zu|jusqu|hasta|fino a|tot|do|до|最大|最多|拡張).{0,40}?\d[\d,.]*\s?k?Wh", re.I),
    "noise_db": re.compile(r"\d+(?:\.\d+)?\s?dB\b", re.I),
    "app_connectivity": re.compile(r"Wi-?Fi|Bluetooth", re.I),
    "warranty_period": re.compile(r"\d+[- ]?(?:year|yr|jahr|ans?\b|años?|anni|jaar|lat|рок|年|ヶ月|か月|months?)s?\s?(?:limited |standard |extended )?(?:warranty|garantie|garantía|garanzia|gwarancj|гаранті|保証|保修)|(?:warranty|garantie|garantía|garanzia|保証期間|保修期).{0,40}?\d+\s?(?:years?|jahre|ans|años|anni|jaar|lat|років|年|ヶ月|か月|months?)", re.I),
    "certifications": re.compile(r"\b(?:UL ?\d{3,4}|FCC|UKCA|PSE|TÜV|RoHS|CSA|ETL|IEC ?\d{4,5}|CE marking|CE-Kennzeichnung)\b"),
    "ups_switch_ms": re.compile(r"\d+\s?ms\b", re.I),
    "pv_efficiency": re.compile(r"(?:efficien\w*|変換効率|转换效率|Wirkungsgrad|rendement|eficiencia|efficienza|rendement).{0,40}?\d+(?:[.,]\d+)?\s?%", re.I),
    "list_price": re.compile(r"(?:\$|€|£|￥|¥)\s?\d[\d,.]+|\d[\d,]+\s?円"),
    "launch_date": re.compile(r"(?:launch|release date|発売日|上市|発売)", re.I),
    "solar_input_max_w": re.compile(r"(?:solar|PV|ソーラー|太阳能|panneau|Solarmodul|solare|zonne|słoneczn|сонячн).{0,60}?\d[\d,]*\s?W\b(?!h)", re.I),
}
TIME = {
    "version_label": re.compile(r"\b(?:Ver(?:sion)?\.?|Rev(?:ision)?\.?|版本|バージョン|第\s?\d+\s?版)\s?:?\s?[A-Z]?\d+(?:\.\d+)*\b|\bV\d+\.\d+(?:\.\d+)?\b", re.I),
    "date": re.compile(r"(?<!Directive )(?<!Richtlinie )\b20[12]\d\s?[./-年]\s?(?:1[0-2]|0?[1-9])(?!\d)(?!\s?/\s?(?:EU|EC|UE|CE|ЄС))(?:\s?[./-月]\s?\d{1,2}\s?日?)?\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20[12]\d\b"),
    "copyright_year": re.compile(r"(?:©|Copyright)\s?(?:\w+\s){0,3}?20[12]\d", re.I),
    "printed_or_made_in": re.compile(r"Printed in|印刷|Made in China|中国製|中国制造", re.I),
}


def manual_paragraphs(text: str):
    path: list[tuple[int, str]] = []
    for ev in chunk_events(text):
        if ev[0] == "md_heading":
            level, htext = ev[1], ev[2]
            while path and path[-1][0] >= level:
                path.pop()
            path.append((level, htext))
            continue
        soup = BeautifulSoup(ev[1], "html.parser")
        for t in soup.find_all("table"):
            if re.search(r"spec", " ".join(t.get("class") or [])):
                t.decompose()
        for para in clean_text(soup).split(LINE_SEP):
            if para.strip():
                yield " > ".join(h for _, h in path), para


def main(root: Path, out: Path) -> None:
    web = root / "docs/publish/sources/web"
    manifest = json.loads((root / "docs/publish/publish_manifest.json").read_text(encoding="utf-8"))
    gap_rows, time_rows = [], []
    for t in manifest["targets"]:
        route = web / t["route"]
        text = (route / t["manual"]).read_text(encoding="utf-8", errors="replace")
        hits: dict[str, list[tuple[str, str]]] = {}
        times: dict[str, list[str]] = {}
        for section, para in manual_paragraphs(text):
            para = URL.sub("[link removed]", para)
            for key, pat in GAPS.items():
                m = pat.search(para)
                if m and len(hits.setdefault(key, [])) < 2:
                    s = max(0, m.start() - 60)
                    hits[key].append((section[-80:], para[s: m.end() + 60]))
            for key, pat in TIME.items():
                for m in pat.finditer(para):
                    times.setdefault(key, [])
                    if m.group(0) not in times[key] and len(times[key]) < 4:
                        times[key].append(m.group(0))
        for key, hs in hits.items():
            gap_rows.append({"model": t["model"], "region": t["region"], "language": t["lang"], "gap_attribute": key,
                             "example_1_section": hs[0][0], "example_1": hs[0][1],
                             "example_2_section": hs[1][0] if len(hs) > 1 else "", "example_2": hs[1][1] if len(hs) > 1 else ""})
        meta = json.loads((route / "publish_meta.json").read_text(encoding="utf-8"))
        time_rows.append({"model": t["model"], "region": t["region"], "language": t["lang"],
                          "publish_meta_version_shape": re.sub(r"(?<=[-^])\d{3,4}(?=-)|^\d{3,4}(?=-)", "<n>", re.sub(r"m\d{4,}", "m<id>", re.sub(r"batch\d+", "batch<n>", re.sub(r"-(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}(?=-|$)", "-<commit>", meta.get("version", ""))))), "publish_meta_built_at": meta.get("built_at", ""),
                          **{k: " ‖ ".join(v) for k, v in times.items()}})
    for name, rows in (("work_gap_hits.csv", gap_rows), ("work_time_strings.csv", time_rows)):
        fields = list(dict.fromkeys(k for r in rows for k in r))
        with (out / name).open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    print(f"gap hits={len(gap_rows)} manuals={len(time_rows)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
