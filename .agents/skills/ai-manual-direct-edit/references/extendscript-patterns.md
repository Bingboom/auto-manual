# ExtendScript Patterns & Pitfalls for Direct `.ai` Editing

Reference guide for `.agents/skills/ai-manual-direct-edit/`.

## 1. Coordinate System

Illustrator artboard/page rectangles are `[left, top, right, bottom]` where **Y increases upward** (`top > bottom`):

- Page-relative top-down point `(px, py)` maps to Illustrator `[rect[0] + px, rect[1] - py]`.
- Moving an item **up** on the page uses **positive** `dy`; moving an item **down** uses **negative** `dy`.
- `aiToPageTopY(rect, bounds)` converts `bounds[1]` (Illustrator top) to `rect[1] - bounds[1]`.

## 2. Multi-Artboard vs Single-Sheet Imposition Masters

| Master Type | How to Detect | Strategy |
| --- | --- | --- |
| Multi-artboard (`doc.artboards.length > 1`) | Each manual page already has its own artboard (`doc.artboards[i].artboardRect`). | Delete unwanted language artboards from highest index downward after removing their items via `visibleBounds` check; keep remaining artboards intact. |
| Single giant imposition sheet (`doc.artboards.length == 1`, e.g. 9000 × 6500 pt production sheet) | All language rows and an outer production spec border live on `artboards[0]`. | Define `page_boxes` (`[left, top, right, bottom]`) for kept pages in reading order, call `aiRemoveItemsOutsideBoxes(layer, pageBoxes, {maxBorderDim: 700})`, apply edits per box, then add one `doc.artboards.add(rect)` per kept page and remove original `artboards[0]`. |

## 3. Production Pitfalls & Safeguards

1. **Never edit AI PDFs with PyMuPDF redactions.** PyMuPDF rewrites PDF content streams without updating `/PieceInfo /Illustrator`, so reopening the file in Adobe Illustrator shows unedited original art. Always edit natively via Illustrator ExtendScript and save with `preserveEditability = true`.
2. **Chinese macOS ExtendScript encoding trap.** ExtendScript reads `.jsx` files in legacy locale encoding unless pure ASCII. Escape every non-ASCII character with `\uXXXX`:
   - `é` `\u00E9`, `è` `\u00E8`, `ê` `\u00EA`, `à` `\u00E0`, `ç` `\u00E7`, `ó` `\u00F3`, `í` `\u00ED`, `á` `\u00E1`, `ñ` `\u00F1`
   - `°` `\u00B0`, `±` `\u00B1`, `×` `\u00D7`, `≤` `\u2264`, `≥` `\u2265`, `·` `\u00B7`
   - `–` `\u2013`, `—` `\u2014`, `’` `\u2019`, `“` `\u201C`, `”` `\u201D`
   - `⎓` `\u2393`, `①` `\u2460`, `₄` `\u2084`
3. **Use `visibleBounds` (not `geometricBounds`) when deleting pages.** Clipped vector groups (`ClipGroup`) often have hidden mask paths extending past an artboard edge; deleting by `geometricBounds` removes artwork on adjacent kept pages. `aiRemoveItemsOutsideBoxes` skips any item whose `visibleBounds` intersects a kept page box.
4. **Filter duplicate text frames by vertical band (`yMin` / `yMax`).** When a page has the same label twice (e.g. `"LCD Screen"` in an overview diagram at `y=165` and as a section title at `y=285`), pass `{yMax: 220}` to `aiFindFrame` so the wrong frame is never matched and later deleted.
5. **Translate bands BEFORE expanding `AreaText` height, and watch oversized clipped `GroupItem` masks.** `aiTranslateItemsInBand` and `aiRemoveItemsInBand` filter items by vertical midpoint (`midY`). Expanding an `AreaText` frame's `textPath.height` shifts its `midY` downward and can pull it into the lower band — always translate lower sections first, then expand the upper `AreaText` box. Similarly, a clipped lower diagram whose hidden mask extends upward can have `midY` slightly above `yMin` and escape `aiRemoveItemsInBand`; sweep any non-page-border item whose bottom (`rect[1] - vb[3]`) falls deep inside the cleared band before drawing new cards.
6. **Watch for `AreaText` bottom clipping.** When replacement copy is longer than the original, `AreaText` clips extra lines silently at `textPath.height`. Remove awkward hard `\r` breaks, expand `textPath.height`, or adjust leading slightly — then confirm via both `must_exist` (checking the final words!) and PNG visual inspection.
7. **Special glyphs in Gilroy.** Gilroy lacks `⎓`, `①`, and subscript `₄`. `aiFixSpecialGlyphs(tf)` assigns `SegoeUISymbol` to `\u2393`, `NotoSansSymbols-Regular` to `\u2460`, and converts `\u2084` into `"4"` at `0.72×` size with `-0.22×` `baselineShift`.
8. **Matching original dark banner charcoal.** Rather than guessing an RGB→CMYK approximation for dark header bars, call `aiSampleBannerColor(layer, rect)` to clone the exact CMYK `fillColor` of an existing dark banner on the document.
9. **One-click red highlight reset for designers.** All highlighted edits share exact `CMYK 0/100/100/0`. In Illustrator, select any red text span and run `Select → Same → Fill Color` (`选择 → 相同 → 填色`) to reset all highlights back to body dark gray in one action.

## 4. `scripts/ai_edit_lib.jsx` Function Summary

| Helper | Purpose |
| --- | --- |
| `aiMakeColor(doc, r, g, b)` / `aiMakePureRed(doc)` | Create CMYK (or RGB) color matching `doc.documentColorSpace`; pure red is `CMYK 0/100/100/0`. |
| `aiPagePoint(rect, px, py)` | Convert page-relative top-down `(px, py)` into Illustrator `[x, y]`. |
| `aiFramesInBox(doc, rect)` | Return all `TextFrame` objects whose center falls inside `rect`. |
| `aiFindFrame(doc, rect, substr, opts)` | Find a `TextFrame` containing `substr`, optionally constrained by `opts.yMin` / `opts.yMax` and `opts.log`. |
| `aiReplaceSub(tf, oldStr, newStr, opts)` | Character-level substring replacement preserving surrounding styling; colors replaced span with `opts.color` (default pure red when `opts.markRed !== false`). |
| `aiColorSubstrings(tf, substrList, color)` | Highlight exact substrings inside an existing `TextFrame`. |
| `aiFixSpecialGlyphs(tf, opts)` | Apply fallback fonts for `⎓` / `①` and subscript styling for `₄`. |
| `aiAddPointText` / `aiAddAreaText` | Create native `PointText` (with optional `alignRightX` / `centerWidth`) or `AreaText` (with optional `leading`, `boldSubstrings`, `redSubstrings`). |
| `aiAddRoundRect` / `aiAddLine` / `aiAddCalloutPill` / `aiDrawNativeTable` | Create native rounded cards, rules, callout pills, and styled 2-column tables. |
| `aiRemoveItemsOutsideBoxes(layer, pageBoxes, opts)` | Remove items whose `visibleBounds` touch no kept page box (plus oversized imposition borders). |
| `aiRemoveItemsInBand` / `aiTranslateItemsInBand` | Remove or translate page items inside a top-down `[yMin, yMax]` band while optionally preserving page numbers. |
| `aiSaveEditablePdf(doc, outPath)` / `aiSaveNativeAi(doc, outPath)` | Save natively with `preserveEditability = true` (PDF) or native `.ai`. |

## 5. QA Spec JSON Schema (`verify_ai_output.py`)

```json
{
  "expected_pages": 20,
  "require_illustrator": true,
  "stale_patterns": [
    {"pattern": "OLD-MODEL", "desc": "gen-1 model number"},
    {"pattern": "LCD Screen", "desc": "removed section", "ignore_pages": [3]}
  ],
  "must_exist": [
    {"page": 1, "phrase": "NEW-MODEL"},
    {"page": 5, "phrase": "authority to operate the device."}
  ]
}
```

- `page` and `ignore_pages` are **1-based** page numbers (`1..N`) so they match PDF viewer and Illustrator artboard numbering.
- `verify_ai_output.py` automatically normalizes ligatures (`\ufb01` → `fi`, `\ufb02` → `fl`), curly apostrophes (`\u2019` → `'`), and collapsed whitespace before checking `must_exist`.
