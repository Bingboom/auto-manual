#!/usr/bin/env python3
"""Independent check of a fixed .ai against the original and the change spec (PyMuPDF, no Illustrator).
Usage: python3 verify.py ORIGINAL.ai FIXED.ai SPEC.json    -> exit 1 on any FAIL"""
import sys, re, json
from collections import Counter
try:
    import pymupdf as fitz
except ImportError:
    import fitz
o, d = fitz.open(sys.argv[1]), fitz.open(sys.argv[2])
spec = json.load(open(sys.argv[3], encoding="utf-8"))
norm = lambda s: re.sub(r"\s+", " ", s.replace("\xad", "-")).strip()
dele = sorted(c["page"] for c in spec["changes"] if c.get("op") == "delete_artboard")
newidx = lambda p: p - sum(1 for x in dele if x < p)          # 1-based original page -> 1-based fixed page
bad = 0
def fail(m):
    global bad; bad += 1; print("FAIL", m)
exp = o.page_count - len(dele)
if d.page_count != exp: fail(f"page count {d.page_count} != expected {exp}")
changed = {}
for c in spec["changes"]:
    if c.get("op") == "delete_artboard": continue
    changed.setdefault(c["page"], []).append(c)
for p, cs in changed.items():
    ot, nt = norm(o[p - 1].get_text()), norm(d[newidx(p) - 1].get_text())
    cnt = lambda t, x: len(re.findall(r"(?<![\w-])" + re.escape(x) + r"(?![\w-])", t))
    for x in {norm(c["old"]) for c in cs} | {norm(c["new"]) for c in cs}:
        if not x: continue
        want = cnt(ot, x) - sum(norm(c["old"]) == x for c in cs) + sum(norm(c["new"]) == x for c in cs)
        got = cnt(nt, x)
        if got != want: fail(f"p{p}: {x!r} occurs {got}x, expected {want}x (before {cnt(ot, x)}x)")
    # everything except the changed strings must be unchanged
    strip = lambda t: Counter(t.split())
    a, b = strip(ot), strip(nt)
    for c in cs:
        a.subtract(Counter(norm(c["old"]).split())); b.subtract(Counter(norm(c["new"]).split()))
    diff = {k: v for k, v in (b - a).items() if v} | {k: -v for k, v in (a - b).items() if v}
    if diff: print(f"WARN p{p}: other words differ (check render): {dict(list(diff.items())[:8])}")
for p in range(1, o.page_count + 1):
    if p in changed or p in dele: continue
    if norm(o[p - 1].get_text()) != norm(d[newidx(p) - 1].get_text()): fail(f"untouched page p{p} text changed")
# font health (skill: missing fonts silently degrade Type0 -> Type1 on save)
ft = lambda pg: sorted((x[3].split("+")[-1], x[1], x[5]) for x in pg.get_fonts(full=True))
fc = [p for p in range(1, o.page_count + 1) if p not in dele and ft(o[p - 1]) != ft(d[newidx(p) - 1])]
if fc: print(f"WARN embedded font type/encoding changed on pages {fc[:30]} -> render those pages and look for blank boxes (e.g. DC symbol)")
print("RESULT:", "PASS" if bad == 0 else f"{bad} FAIL")
sys.exit(1 if bad else 0)
