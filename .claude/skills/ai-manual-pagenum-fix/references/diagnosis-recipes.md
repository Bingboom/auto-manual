# PyMuPDF diagnosis recipes

All of this is read-only against the `.ai` file's PDF-compatible layer. Use the repo's `.venv/bin/python3` (has `fitz`). Never open Illustrator until diagnosis is complete and you know exactly what needs to change.

## Confirm the file is workable this way

```bash
file "/path/to/manual.ai"
# expect: PDF document, version 1.x, N pages
```

```python
import fitz
doc = fitz.open("/path/to/manual.ai")
print(doc.page_count)
```

## Find the footer's actual font/size (do this once per file — do not assume `Gilroy-Regular`/`6.0`)

```python
p = doc[7]  # a known content page, 0-indexed
d = p.get_text("dict")
spans = sorted(
    ((s["bbox"][1], s["bbox"][0], s["font"], s["size"], s["text"])
     for b in d["blocks"] for l in b.get("lines", []) for s in l["spans"]),
)
for y, x, font, size, text in spans[-15:]:  # bottom of page
    print(f"{y:7.1f} {x:7.1f} {font:20s} {size:5.1f} {text!r}")
```

Look for the short numeric string closest to the page bottom (`bbox[1]` near `page.rect.height`) and note its exact `font`/`size` — use that as the filter below.

## Extract every content page's actual footer number

```python
import re

def footer(pno0, font_name="Gilroy-Regular", size=6.0):
    p = doc[pno0]
    h = p.rect.height
    d = p.get_text("dict")
    best = None
    for b in d["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                t = s["text"].strip()
                bb = s["bbox"]
                if (bb[1] > h * 0.94 and s["font"] == font_name
                        and abs(s["size"] - size) < 0.3 and t.isdigit()):
                    if best is None or bb[1] > best[0]:
                        best = (bb[1], bb[0], t)
    return best  # (y, x, value) or None
```

Run this across every content page in a language block and check the sequence is exactly consecutive (`range(1, N+1)` or whatever the intended scheme is) — a gap or duplicate is a real bug.

## Extract TOC entries with position (title + claimed page number)

Dump the whole TOC page sorted by `(y, x)` and read it as a human would — column layout (title left, dotted leader, page number right) is usually obvious from the coordinates:

```python
p = doc[toc_page_idx]
d = p.get_text("dict")
spans = sorted(
    (round(s["bbox"][1], 2), round(s["bbox"][0], 2), s["text"])
    for b in d["blocks"] for l in b.get("lines", []) for s in l["spans"]
)
for y, x, t in spans:
    print(f"{y:8.2f} {x:8.2f} {t}")
```

Cross-reference each `(title, claimed_page)` against the *actual* footer number of the page where that section's heading appears (see next recipe). A stray duplicate range label (e.g. both `"01-22"` and `"01-17"` printed at nearly the same `(x, y)`) shows up as two spans a few points apart — that is a leftover, not two legitimate labels.

## Find section headings and their real page

```python
def headings_with_footer(pno0_start, pno0_end_inclusive, heading_font="Gilroy-Bold", heading_size=12.0):
    for pno0 in range(pno0_start, pno0_end_inclusive + 1):
        page = doc[pno0]
        fo = footer(pno0)
        d = page.get_text("dict")
        heads = [s["text"].strip() for bl in d["blocks"] for l in bl.get("lines", [])
                 for s in l["spans"]
                 if s["font"] == heading_font and s["size"] >= heading_size - 0.5 and s["bbox"][1] < 100]
        print(f"pdfpage {pno0+1} footer={fo[2] if fo else None} heads={heads}")
```

Same caveat as the footer font: inspect one known heading first (`get_text("dict")` on that page, look at font/size of the big bold title) before assuming `Gilroy-Bold`/`12.0`.

## Scan a whole page for language contamination

Don't stop at the first wrong string found — dump the entire page and read every span once, because cloned/mistranslated pages often have more than one leftover string (a title *and* a diagram label *and* a spec line, in the HTE153 case).

```python
p = doc[pno0]
for b in p.get_text("dict")["blocks"]:
    for l in b["lines"]:
        for s in l["spans"]:
            print(round(s["bbox"][1], 1), round(s["bbox"][0], 1), s["font"], round(s["size"], 1), repr(s["text"]))
```

Read the output and manually pick out spans whose script/vocabulary doesn't match the rest of the page.

## Don't assume the bug shape from the last file

Every file in this family (HTE153, HTE156, ...) has had a *different* mix of defects. Re-derive from scratch each time, on this specific file:

- **TOC entries can be wrong in two different physical layouts.** Some language blocks store each entry as `"TITLE ........... NN"` in one flat string (find the number with a regex on the string itself); others store the title and the page number as two separate text frames in two visual columns (locate by `(y, x)` row-grouping, then pair left-column-number with left-column-title, right-column-number with right-column-title — **do not assume column order**, re-derive it by print­ing each row's items sorted by `x` and reading which title sits next to which number, the same way you would read the printed page). Mixing the two up (pairing a title with the wrong column's number) produced a wrong bug list once — always print the row grouping and eyeball-verify a few rows before trusting it.
- **A whole run of TOC entries can be off by the same delta, not just one.** HTE153 had exactly one wrong entry (LCD DISPLAY) per affected language, with everything after it correct. HTE156 had *six* consecutive wrong entries per affected language (from LCD DISPLAY through to the end of that language's TOC), all off by exactly +1 — a different upstream edit (probably a page removed later in the sequence) that the first file didn't have. Check *every* entry against its actual heading page, not just the ones a prior file taught you to expect.
- **A "duplicate" range label doesn't mean the non-duplicate one is correct.** In HTE153 the surviving value (`"01-17"` next to a stale `"01-22"`) matched the section's real page count. In HTE156, *neither* of the two overlapping values was right (`"01-22"` and `"01-17"` were both wrong; the section was actually 16 pages, `"01-16"`) — compute the correct range yourself from the section's actual first/last footer, don't assume either printed value is a valid fallback.
- **A footer can be missing outright**, not just wrong — a page with zero digit spans matching the footer font/size filter, sitting between two pages whose footers are consecutive (e.g. page N=91, page N+1=<nothing>, page N+2=93 — the missing page should read 92). This needs a different fix from a text edit: duplicate an existing footer frame from a nearby page (to inherit its font/size/color/paragraph style for free), reposition it onto the target artboard by preserving the *offset from the artboard's own top-left corner* (`newLeft = dstRect[0] + (srcFrame.geometricBounds[0] - srcRect[0])`, same for top), then set `.contents`. See `references/jxa-illustrator-recipes.md` for the exact duplicate+reposition snippet.

## Check embedded font health (do this before *and after* any Illustrator save — see the JXA recipes file's font-corruption warning)

```python
p = doc[pno0]
print(p.get_fonts(full=True))
```

A font shown as `Type0`/`Identity-H` (TrueType, full glyph table) that turns into `Type1`/`WinAnsiEncoding` (CFF, 256-slot fixed encoding) after a round-trip is a sign that a custom/private-codepoint glyph (anything outside standard Latin — DC-voltage symbols, custom icons, dingbats) may have been silently dropped or replaced with a blank. Render the region before/after at high zoom (`page.get_pixmap(matrix=fitz.Matrix(6,6), clip=fitz.Rect(...))`, save as PNG, `Read` it) and compare — don't trust the font-name string alone, an empty/'notdef' glyph in the new subset still reports a normal-looking font name.
