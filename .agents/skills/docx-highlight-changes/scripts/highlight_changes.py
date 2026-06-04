#!/usr/bin/env python3
"""Highlight specific text spans in a .docx by wrapping them in colored runs.

Why this exists: when you hand someone a corrected manual, "trust me, I fixed it"
is not reviewable. Marking the *exact* fragments you changed lets a reviewer see
every edit at a glance. Word's own highlighter can only paint a whole selection a
person made by hand; this script paints precise, programmatic spans — even a single
accent character mid-word — and only those spans, leaving everything else untouched.

It works at the run level. A `.docx` stores text in runs (`<w:r>`), and a single
logical word can be split across several runs (Word does this constantly). So to
colour exactly "is" inside "...this is fine..." we locate the target in the
*concatenated* paragraph text, then split the underlying runs at the target's
boundaries and add the colour property to just the covering run(s) — cloning each
original run's formatting (bold, size, font) so nothing else shifts.

Two colouring mechanisms, picked with --style:
  * shading   (default): <w:shd .../> run background. Matches the soft pastel
              marks teams often already use; accepts any hex colour.
  * highlight: <w:highlight/> the Word highlighter pen. Limited to Word's named
              palette, but renders identically across Word versions/readers.

Usage:
  # highlight whole phrases green (shading)
  python highlight_changes.py --in in.docx --out out.docx --color green \
      --target "non è incluso, ma è disponibile" --target "verrà disassociato"

  # rich spec from a JSON file (per-target colours, or colour just a sub-substring)
  python highlight_changes.py --in in.docx --out out.docx --spec changes.json

changes.json may be either
  {"color":"green","style":"shading","targets":[ ...items... ]}
or just a bare list of items. Each item is one of:
  "whole phrase to highlight"                          # colour the whole phrase
  {"text":"phrase", "color":"yellow"}                  # per-target colour
  {"text":"CA o CC è attiva", "mark":"è"}              # locate by context, colour
                                                        # only the "è" (accent style)

The script ALWAYS prints a per-target match report and a final summary. Treat any
"NOT FOUND (0)" line as a failure to investigate — a silent miss means the reviewer
sees an unmarked change. Requires lxml (faithful OOXML round-trip).
"""
import argparse
import copy
import json
import sys
import zipfile
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML = "http://www.w3.org/XML/1998/namespace"


def w(tag):
    return "{%s}%s" % (W, tag)


# Named colours for --style shading (hex fills). Add freely; these are just sugar
# on top of "any 6-digit hex works".
SHADING_HEX = {
    "green": "92D050", "lightgreen": "C6EFCE", "darkgreen": "548235",
    "yellow": "FFFF00", "lightyellow": "FFF5B8", "gold": "FFD966",
    "orange": "F9DDB2", "pink": "FFC0CB", "magenta": "FF00FF",
    "cyan": "00FFFF", "blue": "00B0F0", "lightblue": "DDEBF7",
    "red": "FF0000", "gray": "D9D9D9", "grey": "D9D9D9",
}
# Word highlighter pen palette (the only values <w:highlight w:val> accepts).
HIGHLIGHT_NAMES = {
    "yellow", "green", "cyan", "magenta", "blue", "red", "darkBlue", "darkCyan",
    "darkGreen", "darkMagenta", "darkRed", "darkYellow", "darkGray", "lightGray",
    "black", "white",
}


def resolve_color(color, style):
    """Map a user colour token to the concrete value the chosen style needs."""
    c = (color or "").strip()
    if style == "highlight":
        syn = {"grey": "lightGray", "gray": "lightGray",
               "lightgreen": "green", "lightyellow": "yellow", "orange": "darkYellow"}
        c2 = syn.get(c.lower(), c)
        for name in HIGHLIGHT_NAMES:
            if name.lower() == c2.lower():
                return name
        raise SystemExit("--style highlight needs a Word palette colour %s, got %r"
                         % (sorted(HIGHLIGHT_NAMES), color))
    # shading
    if c.lower() in SHADING_HEX:
        return SHADING_HEX[c.lower()]
    h = c.lstrip("#")
    if len(h) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in h):
        return h.upper()
    raise SystemExit("--style shading needs a name %s or a 6-digit hex, got %r"
                     % (sorted(SHADING_HEX), color))


def mark_rpr(base_rpr, color, style):
    """Clone a run's <w:rPr> and add the highlight property to the clone."""
    rpr = copy.deepcopy(base_rpr) if base_rpr is not None else etree.Element(w("rPr"))
    for tag in ("shd", "highlight"):          # avoid stacking onto an existing mark
        for e in rpr.findall(w(tag)):
            rpr.remove(e)
    if style == "highlight":
        el = etree.SubElement(rpr, w("highlight"))
        el.set(w("val"), color)
    else:
        el = etree.SubElement(rpr, w("shd"))
        el.set(w("val"), "clear")
        el.set(w("color"), "auto")
        el.set(w("fill"), color)
    return rpr


def single_t(r):
    """Return the run's lone <w:t> if it is a simple text run, else None.

    Runs carrying tabs, breaks, drawings or several <w:t> are 'complex'; we do not
    slice those (rare in body prose) — we highlight them whole as a fallback.
    """
    ts = r.findall(w("t"))
    others = [c for c in r if c.tag not in (w("rPr"), w("t"))]
    return ts[0] if (len(ts) == 1 and not others) else None


def run_concat_text(r):
    return "".join((t.text or "") for t in r.findall(w("t")))


def highlight_paragraph(p, targets, style):
    """Find every target inside this paragraph and colour exactly its span.

    Matching is done on the concatenated run text so a target may span runs; each
    run is then sliced independently, which makes a cross-run hit Just Work.
    """
    runs = [r for r in p.iter(w("r")) if r.find(w("t")) is not None]
    if not runs:
        return 0

    segs = []  # [run, t_or_None, text, start, end]
    pos = 0
    for r in runs:
        t = single_t(r)
        txt = (t.text or "") if t is not None else run_concat_text(r)
        segs.append([r, t, txt, pos, pos + len(txt)])
        pos += len(txt)
    full = "".join(s[2] for s in segs)

    intervals = []  # (start, end, resolved_color)
    for tg in targets:
        text = tg["text"]
        if not text:
            continue
        mark = tg.get("mark")
        color = tg["_color"]
        i = full.find(text)
        while i != -1:
            if mark:
                m = full.find(mark, i, i + len(text))
                if m != -1:
                    intervals.append((m, m + len(mark), color))
                    tg["_hits"] += 1
            else:
                intervals.append((i, i + len(text), color))
                tg["_hits"] += 1
            i = full.find(text, i + len(text))
    if not intervals:
        return 0

    for r, t, txt, s, e in segs:
        if not txt:
            continue
        local = []
        for a, b, color in intervals:
            lo, hi = max(a, s), min(b, e)
            if lo < hi:
                local.append((lo - s, hi - s, color))
        if not local:
            continue

        if t is None:  # complex run -> coarse whole-run highlight
            base = r.find(w("rPr"))
            new = mark_rpr(base, local[0][2], style)
            if base is not None:
                r.replace(base, new)
            else:
                r.insert(0, new)
            continue

        local.sort()
        base = r.find(w("rPr"))
        pieces, cur = [], 0
        for a, b, color in local:
            if a < cur:        # overlapping target ranges: keep the first, skip rest
                continue
            if a > cur:
                pieces.append((txt[cur:a], None))
            pieces.append((txt[a:b], color))
            cur = b
        if cur < len(txt):
            pieces.append((txt[cur:], None))

        new_runs = []
        for ptxt, color in pieces:
            if ptxt == "":
                continue
            nr = etree.Element(w("r"))
            if color is not None:
                nr.append(mark_rpr(base, color, style))
            elif base is not None:
                nr.append(copy.deepcopy(base))
            nt = etree.SubElement(nr, w("t"))
            nt.text = ptxt
            nt.set("{%s}space" % XML, "preserve")
            new_runs.append(nr)

        parent = r.getparent()
        idx = list(parent).index(r)
        parent.remove(r)
        for off, nr in enumerate(new_runs):
            parent.insert(idx + off, nr)

    return len(intervals)


def load_targets(args):
    targets = [{"text": t} for t in args.target]
    style, default_color = args.style, args.color
    if args.spec:
        with open(args.spec, encoding="utf-8") as fh:
            spec = json.load(fh)
        if isinstance(spec, dict):
            style = spec.get("style", style)
            default_color = spec.get("color", default_color)
            items = spec.get("targets", [])
        else:
            items = spec
        for item in items:
            targets.append({"text": item} if isinstance(item, str) else dict(item))
    if not targets:
        raise SystemExit("no targets given (use --target or --spec)")
    for tg in targets:
        tg["_hits"] = 0
        tg["_color"] = resolve_color(tg.get("color", default_color), style)
    return targets, style


def main():
    ap = argparse.ArgumentParser(description="Highlight exact text spans in a .docx.")
    ap.add_argument("--in", dest="inp", required=True, help="input .docx")
    ap.add_argument("--out", required=True, help="output .docx")
    ap.add_argument("--color", default="green",
                    help="default colour: a name or 6-digit hex (shading) / Word palette name (highlight)")
    ap.add_argument("--style", choices=["shading", "highlight"], default="shading",
                    help="shading = <w:shd> background (any hex); highlight = Word highlighter pen")
    ap.add_argument("--target", action="append", default=[],
                    help="exact text to highlight (repeatable)")
    ap.add_argument("--spec", help="JSON file of targets (see module docstring)")
    args = ap.parse_args()

    targets, style = load_targets(args)

    with zipfile.ZipFile(args.inp) as z:
        names = z.namelist()
        blobs = {n: z.read(n) for n in names}
    if "word/document.xml" not in blobs:
        raise SystemExit("not a Word .docx (no word/document.xml)")

    root = etree.fromstring(blobs["word/document.xml"])
    total = 0
    for p in root.iter(w("p")):
        total += highlight_paragraph(p, targets, style)
    blobs["word/document.xml"] = etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", standalone=True)

    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, blobs[n])

    print("=== highlight report (style=%s) ===" % style)
    missing = 0
    for tg in targets:
        label = tg["text"] if not tg.get("mark") else "%s  [mark %r]" % (tg["text"], tg["mark"])
        if tg["_hits"] == 0:
            missing += 1
            print("  NOT FOUND (0): %s" % label)
        else:
            print("  ok (%d): %s" % (tg["_hits"], label))
    print("highlighted %d span(s) across %d target(s); %d NOT FOUND -> %s"
          % (total, len(targets), missing, args.out))
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
