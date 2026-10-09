#!/usr/bin/env python3
"""Find text on a page of a PDF-compatible .ai and print change-spec-ready entries.
Usage:
  python3 locate.py FILE.ai PAGE "substring"        # PAGE is 1-based PDF page = artboard
  python3 locate.py FILE.ai PAGE --dump              # dump all spans of the page (y, x, font, size, text)
  python3 locate.py FILE.ai PAGE --footer            # footer digit spans
Output bbox is in PDF coords (top-left origin), as the change spec expects.
Text that is outlined (converted to paths) does NOT appear here and cannot be edited by the script."""
import sys, re, json
try:
    import pymupdf as fitz
except ImportError:
    import fitz
f, page = sys.argv[1], int(sys.argv[2])
arg = sys.argv[3] if len(sys.argv) > 3 else "--dump"
p = fitz.open(f)[page - 1]
spans = [s for b in p.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"] if s["text"].strip()]
r = lambda b: [round(v, 2) for v in b]
if arg == "--dump":
    for s in sorted(spans, key=lambda s: (round(s["bbox"][1]), s["bbox"][0])):
        print(round(s["bbox"][1], 1), round(s["bbox"][0], 1), s["font"], round(s["size"], 1), repr(s["text"]))
elif arg == "--footer":
    h = p.rect.height
    for s in spans:
        if re.fullmatch(r"\d{1,3}", s["text"].strip()) and s["bbox"][1] > h * 0.93:
            print(json.dumps({"page": page, "old": s["text"].strip(), "pdf_bbox": r(s["bbox"]), "font": s["font"], "size": round(s["size"], 1)}, ensure_ascii=False))
else:
    hits = [s for s in spans if arg in s["text"]]
    if not hits:
        print("NOT FOUND as a single span. It may span several lines/spans or be outlined. Try a shorter substring or --dump.")
    for s in hits:
        print(json.dumps({"page": page, "op": "set" if s["text"].strip() == arg else "replace", "old": arg,
                          "new": "<FILL>", "pdf_bbox": r(s["bbox"]), "span_text": s["text"], "font": s["font"], "size": round(s["size"], 1)}, ensure_ascii=False))
