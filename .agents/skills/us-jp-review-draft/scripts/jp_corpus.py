"""Search existing Japanese corpus: published JP Web manuals, JP RST templates and Translation_Memory dumps.

  # 1. sentence pool from every RTD JP manual (+ templates); short labels such as 「認証：」 are kept
  python3 -I jp_corpus.py pool --out pool.json [--rtd-root https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest] [--templates docs/templates/page_jp]
  # 2. regex search in the pool
  python3 -I jp_corpus.py grep pool.json '並列|拡張ポート' 'バイパス'
  # 3. TM: dump the tables first with feishu_api.py bitable-dump, then
  python3 -I jp_corpus.py tm-grep terms.json pairs.json 'parallel|並列'
  python3 -I jp_corpus.py tm-match terms.json pairs.json units.json [--min 0.45]

``units.json`` is a list of {"text": "..."} (e.g. extract_units.py output filtered to English units).
"""
from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import sys
import urllib.request
from urllib.parse import urljoin
from pathlib import Path

JP = re.compile(r"[぀-ヿ一-鿿]")


def fetch(url: str) -> str:
    # RTD (behind Cloudflare) answers urllib's default User-Agent with 403.
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (auto-manual us-jp-review-draft)"})
    with urllib.request.urlopen(request, timeout=90) as resp:
        return resp.read().decode("utf-8", "replace")


def html_text(src: str) -> str:
    src = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", src, flags=re.S)
    src = re.sub(r"<(p|li|h[1-6]|td|th|div|br|figcaption|span)[^>]*>", "\n", src)
    return html.unescape(re.sub(r"<[^>]+>", " ", src))


def build_pool(rtd_root: str, templates: str | None, extra: list[str]) -> dict[str, list[str]]:
    docs: dict[str, str] = {}
    root = fetch(rtd_root.rstrip("/") + "/")
    for href in sorted(set(re.findall(r'href="([^"]*/JP/ja/[^"]*\.html)"', root))):
        url = urljoin(rtd_root.rstrip("/") + "/", href)
        docs[href.split("/")[0] or url] = html_text(fetch(url))
    for path in extra:
        docs[Path(path).name] = html_text(Path(path).read_text(encoding="utf-8"))
    if templates:
        for rst in sorted(Path(templates).glob("*.rst")):
            docs["tpl:" + rst.name] = rst.read_text(encoding="utf-8")
    pool: dict[str, set[str]] = {}
    for name, text in docs.items():
        for s in re.split(r"(?<=[。！])|\n", text):
            s = re.sub(r"\s+", " ", s).strip()
            if 2 <= len(s) <= 240 and JP.search(s):
                pool.setdefault(s, set()).add(name)
    return {s: sorted(v) for s, v in pool.items()}


def txt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, list):
        return " ".join(txt(x) for x in v)
    if isinstance(v, dict):
        return v.get("text") or v.get("name") or ""
    return str(v)


def tm_rows(terms: str, pairs: str) -> list[tuple[str, str, str, str]]:
    rows = []
    for path, kind in ((terms, "term"), (pairs, "pair")):
        for item in json.load(open(path, encoding="utf-8")):
            f = item.get("fields", item)
            en, jp = txt(f.get("en")).strip(), txt(f.get("jp")).strip()
            if en and jp:
                rows.append((kind, en, jp, txt(f.get("Model"))))
    return rows


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", s.lower())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pool")
    p.add_argument("--out", required=True)
    p.add_argument("--rtd-root", default="https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest")
    p.add_argument("--templates", default="docs/templates/page_jp")
    p.add_argument("--extra", nargs="*", default=[], help="local JP manual .html/.md files")
    g = sub.add_parser("grep")
    g.add_argument("pool")
    g.add_argument("patterns", nargs="+")
    tg = sub.add_parser("tm-grep")
    tg.add_argument("terms")
    tg.add_argument("pairs")
    tg.add_argument("patterns", nargs="+")
    tm = sub.add_parser("tm-match")
    tm.add_argument("terms")
    tm.add_argument("pairs")
    tm.add_argument("units")
    tm.add_argument("--min", type=float, default=0.45)
    a = ap.parse_args()
    if a.cmd == "pool":
        pool = build_pool(a.rtd_root, a.templates, a.extra)
        json.dump(pool, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
        sources = sorted({s for v in pool.values() for s in v})
        print(len(pool), "sentences from", len(sources), "sources:", ", ".join(sources))
    elif a.cmd == "grep":
        pool = json.load(open(a.pool, encoding="utf-8"))
        for pat in a.patterns:
            rx = re.compile(pat)
            hits = [(s, v) for s, v in pool.items() if rx.search(s)]
            print(f"## {pat} ({len(hits)})")
            for s, v in hits[:12]:
                print("  -", s[:160], "|", ",".join(v)[:80])
    elif a.cmd == "tm-grep":
        rows = tm_rows(a.terms, a.pairs)
        for pat in a.patterns:
            rx = re.compile(pat, re.I)
            print(f"## {pat}")
            for kind, en, jp, model in rows:
                if rx.search(en) or rx.search(jp):
                    print(f"  {kind}: {en[:110]} => {jp[:110]} [{model[:20]}]")
    else:
        rows = tm_rows(a.terms, a.pairs)
        for i, unit in enumerate(json.load(open(a.units, encoding="utf-8"))):
            q = unit["text"]
            qt = {w for w in norm(q).split() if len(w) > 2}
            scored = []
            for kind, en, jp, model in rows:
                et = {w for w in norm(en).split() if len(w) > 2}
                score = max(difflib.SequenceMatcher(None, norm(q), norm(en)).ratio(), len(qt & et) / max(1, len(qt | et)))
                scored.append((score, kind, en, jp, model))
            scored.sort(reverse=True)
            print(f"\n#{i} {q[:110]}")
            for score, kind, en, jp, model in scored[:2]:
                if score >= a.min:
                    print(f"   {score:.2f} {kind} EN:{en[:100]} || JP:{jp[:100]} [{model[:16]}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
