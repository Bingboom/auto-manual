#!/usr/bin/env python3
"""Language-asset fork sweep across Feishu tables and RST templates.

Cross-checks every (English key, target language) pair that appears in more
than one language-asset source and reports substantive divergences ("forks"):

- Translation_Memory sentence pairs and the Terms table (TM base,
  ``$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN``);
- print source tables in the phase2 doc-build base
  (``$FEISHU_PHASE2_BASE_TOKEN``): LCD icons, Symbols, TROUBLESHOOTING;
- template headings, aligned position-by-position between the English page
  file and its sibling language file (page_eu-*/page_us-*/page_shared/<lang>).

Also reports: TM rows sharing one English key with contradicting values,
"shadow" duplicate rows (one filled / one empty, which make TM pre-translation
miss silently), placeholder junk values (``test``/``TBD``) left in live
tables, and minor case/punctuation drift.

Read-only: nothing is written back to Feishu. Output goes to the Markdown
paths given on the command line.

Usage:
    python tools/lang_asset_sweep.py --out reports_dir/fork_report.md \
        [--adjudication reports_dir/adjudication.md] [--repo-root PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path

TM_SENTENCE_TABLE = "tblqtvNbgjDwR4ya"
TM_TERMS_TABLE = "tblzerRpOEuDIkKA"
DOC_TABLES = (
    ("tblW5fCuJ6YdAcND", "LCD_icons"),
    ("tblSZX8hBzpJLqAe", "Symbols"),
    ("tblOmJoAfU35brkb", "TROUBLESHOOTING"),
)

LANG_ALIASES = {
    "zh": "zh", "zh-TW": "zh-TW", "zh-tw": "zh-TW", "ko": "ko", "kr": "ko",
    "jp": "jp", "ja": "jp", "fr": "fr", "es": "es", "de": "de", "it": "it",
    "uk": "uk", "pt-BR": "pt-BR", "pt-br": "pt-BR",
}
JUNK_VALUE = re.compile(r"^(test|todo|tbd|xxx|n/?a|-|—)$", re.IGNORECASE)
_HEADING_UNDERLINE = re.compile(r"([=\-~^\"'#*+])\1{2,}")


def flat_cell(value: object) -> str:
    if isinstance(value, list):
        value = " ".join(
            str(x.get("text", x)) if isinstance(x, dict) else str(x) for x in value
        )
    if isinstance(value, str):
        return value.strip()
    return "" if value is None else str(value)


def norm_key(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"^[\*•●※\s]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.rstrip(".:：。").casefold()


def norm_val(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def minor_only(a: str, b: str) -> bool:
    def strip(x: str) -> str:
        return re.sub(r"[\s.。:：]+$", "", re.sub(r"\s+", "", x)).casefold()

    return strip(a) == strip(b)


def rst_headings(text: str) -> list[str]:
    out: list[str] = []
    lines = text.splitlines()
    for i in range(len(lines) - 1):
        title, underline = lines[i].rstrip(), lines[i + 1].rstrip()
        if (
            title
            and underline
            and not title.startswith("..")
            and not title.startswith("|")
            and _HEADING_UNDERLINE.fullmatch(underline)
            and len(underline) >= max(3, int(len(title) * 0.7))
        ):
            heading = re.sub(r"\*\*", "", title).strip()
            if heading:
                out.append(heading)
    return out


def template_evidence_eligible(variant: str) -> bool:
    v = variant.strip()
    non_ascii = any(ord(ch) > 127 for ch in v)
    return (non_ascii and len(v) >= 2) or (not non_ascii and len(v) >= 8)


def lark_dump(base_token: str, table_id: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    offset = 0
    while True:
        proc = subprocess.run(
            [
                "lark-cli", "base", "+record-list",
                "--base-token", base_token, "--table-id", table_id,
                "--limit", "200", "--offset", str(offset), "--format", "json",
            ],
            capture_output=True,
            text=True,
        )
        data = json.loads(proc.stdout)["data"]
        for rid, vals in zip(data["record_id_list"], data["data"]):
            rows.append({"record_id": rid, **dict(zip(data["fields"], vals))})
        if len(data["data"]) < 200:
            break
        offset += 200
    return rows


def lang_column_groups(columns: list[str]) -> dict[str, dict[str, str]]:
    """Group columns into {base: {canonical_lang_or_en: column_name}}."""
    groups: dict[str, dict[str, str]] = defaultdict(dict)
    for col in columns:
        if col == "en" or col in LANG_ALIASES:
            groups[""]["en" if col == "en" else LANG_ALIASES[col]] = col
        elif "_" in col:
            base, suffix = col.rsplit("_", 1)
            if base.startswith("aliases"):
                continue
            if suffix == "en" or suffix in LANG_ALIASES:
                groups[base]["en" if suffix == "en" else LANG_ALIASES[suffix]] = col
    return groups


def collect_table_entries(base_token, table_id, name, entries, tm_rows_by_key):
    rows = lark_dump(base_token, table_id)
    if not rows:
        return 0
    groups = lang_column_groups([k for k in rows[0] if k != "record_id"])
    for row in rows:
        for gbase, mapping in groups.items():
            if "en" not in mapping:
                continue
            en = flat_cell(row.get(mapping["en"]))
            if len(en) < 2:
                continue
            source = name if not gbase else f"{name}.{gbase}"
            if name == "TM句对" and not gbase and tm_rows_by_key is not None:
                tm_rows_by_key[norm_key(en)].append(row)
            for lang, col in mapping.items():
                if lang == "en":
                    continue
                val = flat_cell(row.get(col))
                if val:
                    entries.append((source, row["record_id"], en, lang, val))
    return len(rows)


def collect_template_entries(repo_root: Path, entries):
    tpl_root = repo_root / "docs" / "templates"
    fam_map: dict[tuple[str, str], dict[str, tuple[list[str], str]]] = defaultdict(dict)
    for d in sorted(tpl_root.glob("page_*")):
        if not d.is_dir():
            continue
        m = re.fullmatch(r"page_(eu|us|au)-(\w+(?:-\w+)?)", d.name)
        if not m:
            continue
        suffix = m.group(2)
        lang = "en" if suffix == "en" else LANG_ALIASES.get(suffix)
        if lang is None:
            continue
        for f in d.glob("*.rst"):
            heads = rst_headings(f.read_text(encoding="utf-8", errors="ignore"))
            fam_map[(m.group(1), f.name)][lang] = (heads, str(f.relative_to(repo_root)))
    shared = tpl_root / "page_shared"
    if shared.is_dir():
        for d in sorted(shared.iterdir()):
            if not d.is_dir():
                continue
            lang = "en" if d.name == "en" else LANG_ALIASES.get(d.name)
            if lang is None:
                continue
            for f in d.glob("*.rst"):
                heads = rst_headings(f.read_text(encoding="utf-8", errors="ignore"))
                fam_map[("shared", f.name)][lang] = (heads, str(f.relative_to(repo_root)))
    paired = skipped = 0
    for (fam, fname), by_lang in fam_map.items():
        if "en" not in by_lang:
            continue
        en_heads, _ = by_lang["en"]
        for lang, (heads, rel) in by_lang.items():
            if lang == "en":
                continue
            if not en_heads or len(heads) != len(en_heads):
                skipped += 1
                continue
            paired += 1
            for eh, xh in zip(en_heads, heads):
                if eh and xh:
                    entries.append((f"模板:{fam}/{fname}", rel, eh, lang, xh))
    return paired, skipped


def suggest(variants: dict, evidence: dict) -> str:
    with_tpl = [v for v in variants if evidence.get(v, (0,))[0] > 0]
    if len(with_tpl) == 1:
        return with_tpl[0]
    counts = {v: len({(s, r) for s, r, _, _ in occ}) for v, occ in variants.items()}
    best = max(counts.values())
    top = [v for v, c in counts.items() if c == best]
    return top[0] if len(top) == 1 else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, help="fork report Markdown path")
    ap.add_argument("--adjudication", help="optional adjudication checklist Markdown path")
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--tm-base-token", default=os.environ.get("FEISHU_TRANSLATION_MEMORY_BASE_TOKEN"))
    ap.add_argument("--doc-base-token", default=os.environ.get("FEISHU_PHASE2_BASE_TOKEN"))
    args = ap.parse_args()
    if not args.tm_base_token or not args.doc_base_token:
        ap.error("need --tm-base-token/--doc-base-token or the matching env vars")
    repo_root = Path(args.repo_root)

    entries: list[tuple[str, str, str, str, str]] = []
    tm_rows_by_key: dict[str, list[dict]] = defaultdict(list)
    stats: dict[str, int] = {}
    stats["TM句对"] = collect_table_entries(args.tm_base_token, TM_SENTENCE_TABLE, "TM句对", entries, tm_rows_by_key)
    stats["Terms"] = collect_table_entries(args.tm_base_token, TM_TERMS_TABLE, "Terms", entries, None)
    for table_id, name in DOC_TABLES:
        stats[name] = collect_table_entries(args.doc_base_token, table_id, name, entries, None)
    paired, skipped = collect_template_entries(repo_root, entries)

    tpl_corpus = {
        str(f.relative_to(repo_root)): unicodedata.normalize(
            "NFC", f.read_text(encoding="utf-8", errors="ignore")
        )
        for f in (repo_root / "docs" / "templates").rglob("*.rst")
    }

    def tpl_evidence(variant: str) -> tuple[int, list[str]]:
        if not template_evidence_eligible(variant):
            return 0, []
        hits = [p for p, txt in tpl_corpus.items() if variant.strip() in txt]
        return len(hits), hits[:3]

    bykey: dict[tuple[str, str], dict[str, list]] = defaultdict(lambda: defaultdict(list))
    en_display: dict[str, str] = {}
    for src, rid, en, lang, val in entries:
        key = norm_key(en)
        en_display.setdefault(key, en)
        bykey[(key, lang)][norm_val(val)].append((src, rid, en, val))

    forks, minors, junky = [], [], []
    for (key, lang), variants in sorted(bykey.items()):
        if len(variants) < 2:
            continue
        junk = {v: occ for v, occ in variants.items() if JUNK_VALUE.fullmatch(v.strip())}
        if junk:
            junky.append((key, lang, junk))
            variants = {v: o for v, o in variants.items() if not JUNK_VALUE.fullmatch(v.strip())}
            if len(variants) < 2:
                continue
        vals = list(variants)
        if all(minor_only(vals[0], v) for v in vals[1:]):
            minors.append((key, lang, variants))
        else:
            forks.append((key, lang, variants))

    dup_diverge, dup_shadow = [], defaultdict(list)
    for key, rows in tm_rows_by_key.items():
        if len(rows) < 2:
            continue
        for lang in sorted(set(LANG_ALIASES.values())):
            vals = [norm_val(flat_cell(r.get(lang))) for r in rows]
            non_empty = [v for v in vals if v]
            if len(set(non_empty)) > 1:
                dup_diverge.append(
                    (key, lang, [(r["record_id"], norm_val(flat_cell(r.get(lang)))) for r in rows])
                )
            elif non_empty and any(not v for v in vals):
                dup_shadow[lang].append((key, [r["record_id"] for r in rows]))
    dup_groups = sum(1 for rows in tm_rows_by_key.values() if len(rows) > 1)

    tm_keys = {norm_key(en) for s, _, en, _, _ in entries if s == "TM句对"}
    term_keys = {norm_key(en) for s, _, en, _, _ in entries if s == "Terms"}
    overlap = tm_keys & term_keys

    lines = [
        "# 语言资产分叉全库对账报告(P0 sweep)",
        "",
        "数据源:" + " / ".join(f"{k}({v}行)" for k, v in stats.items())
        + f" + 模板标题同位对齐({paired} 个文件对,跳过 {skipped} 个标题数不齐的)",
        "",
        "## 总览",
        "",
        f"- 实质分叉:**{len(forks)}** 处(按 英文键×语言 计)",
        f"- 轻微差异(大小写/标点):{len(minors)} 处",
        f"- TM 同英文重复行:{dup_groups} 组;译文矛盾 {len(dup_diverge)} 处;空影行按语言:"
        + ", ".join(f"{lg}:{len(v)}" for lg, v in sorted(dup_shadow.items())),
        f"- Terms 与 TM 英文键重叠:{len(overlap)} 个(重复维护面)",
        f"- 活表垃圾值(test/TBD 等):{len(junky)} 处",
        "",
        "## 实质分叉清单(按语言)",
        "",
    ]
    adj = [
        "# 语言资产分叉裁决清单",
        "",
        "逐条裁决:在「裁决」栏填最终值(或勾选建议)。建议规则 = 模板印刷证据优先,其次多来源多数。",
        "",
    ]
    by_lang: dict[str, list] = defaultdict(list)
    for key, lang, variants in forks:
        by_lang[lang].append((key, variants))
    for lang in sorted(by_lang):
        items = by_lang[lang]
        lines.append(f"### {lang} — {len(items)} 处")
        lines.append("")
        adj.append(f"## {lang} — {len(items)} 处")
        adj.append("")
        for key, variants in items:
            evidence = {v: tpl_evidence(occ[0][3]) for v, occ in variants.items()}
            lines.append(f"**EN: {en_display[key][:90]}**")
            for nv, occ in variants.items():
                srcs = "; ".join(sorted({f"{s}({r[:14]})" for s, r, _, _ in occ}))
                n_hits = evidence[nv][0]
                ev = f" ←模板出现 {n_hits} 处" if n_hits else ""
                lines.append(f"- `{occ[0][3][:80]}` ⟵ {srcs}{ev}")
            lines.append("")
            pick = suggest(variants, evidence)
            adj.append(f"### {en_display[key][:80]}")
            for nv, occ in variants.items():
                srcs = "; ".join(sorted({f"{s}" for s, _, _, _ in occ}))
                mark = " ✅建议" if nv == pick else ""
                n_hits = evidence[nv][0]
                ev = f"(模板×{n_hits})" if n_hits else ""
                adj.append(f"- [ ] `{occ[0][3][:80]}` — {srcs}{ev}{mark}")
            adj.append("- 裁决:______")
            adj.append("")
    lines += ["## TM 同英文重复行 — 译文矛盾", ""]
    for key, lang, rows in dup_diverge[:40]:
        lines.append(f"- [{lang}] EN: {en_display.get(key, key)[:70]}")
        for rid, v in rows:
            lines.append(f"    - {rid}: `{(v or '<空>')[:70]}`")
    if len(dup_diverge) > 40:
        lines.append(f"- …共 {len(dup_diverge)} 处,余略")
    lines += ["", "## TM 空影重复行(样例,每语言≤10)", ""]
    for lang, lst in sorted(dup_shadow.items()):
        sample = "; ".join(en_display.get(k, k)[:40] for k, _ in lst[:10])
        lines.append(f"- **{lang}**({len(lst)} 组): {sample}")
    lines += ["", "## 轻微差异(样例≤30)", ""]
    for key, lang, variants in minors[:30]:
        lines.append(f"- [{lang}] {en_display[key][:60]} → " + " | ".join(f"`{v[:40]}`" for v in variants))
    lines += ["", "## 垃圾值清单(活表里的 test/TBD 等占位残留)", ""]
    for key, lang, junk in junky:
        for v, occ in junk.items():
            srcs = "; ".join(sorted({f"{s}({r[:14]})" for s, r, _, _ in occ}))
            lines.append(f"- [{lang}] `{v}` @ {srcs} | EN: {en_display.get(key, key)[:60]}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"fork report -> {out}")
    if args.adjudication:
        adj_path = Path(args.adjudication)
        adj_path.parent.mkdir(parents=True, exist_ok=True)
        adj_path.write_text("\n".join(adj), encoding="utf-8")
        print(f"adjudication -> {adj_path}")
    print(
        f"forks={len(forks)} minors={len(minors)} dup_groups={dup_groups} "
        f"diverge={len(dup_diverge)} shadow={sum(len(v) for v in dup_shadow.values())} "
        f"overlap={len(overlap)} junk={len(junky)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
