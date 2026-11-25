---
name: ai-manual-direct-edit
description: "Edit an existing Adobe Illustrator .ai or AI-editable .pdf manual directly against a review draft (审核稿) or TM-B corpus on macOS, preserving dielines, bleed, color space, and native Illustrator editability. Use whenever asked to update an existing print .ai / AI-PDF master from a review draft or corpus (按审核稿改 .ai, 按语料改 .ai, 改2代说明书单英语, 改动标红, 拆画板删多余语种). NOT for pure page-number/TOC renumbering specs (ai-manual-pagenum-fix), extracting textless illustrations (asset-textless-extraction), read-only QC PDF annotations (pdf-annotate-qc), or authoring Web packages (web-manual-agent-authoring)."
metadata:
  owner: "印刷改稿维护人"
  status: "active"
  entry: "按审核稿或 TM-B 语料直接修改现有 .ai / AI 可编辑 .pdf 印刷设计稿并输出可编辑文件"
  tools: "Adobe Illustrator ExtendScript (scripts/ai_edit_lib.jsx)、scripts/inspect_ai_doc.py、scripts/run_illustrator_jsx.py、scripts/verify_ai_output.py、PyMuPDF"
  validation: "运行 tests/test_ai_manual_direct_edit_skill.py，并对实改产物核对 /PieceInfo /Illustrator、0 处旧值残留、必备文案完整度及逐页渲染目检"
  reviewed: "2026-11-25"
  retire_when: "印刷主线不再以直接修改现存 .ai / AI 可编辑 .pdf 设计稿为交付路径"
---

# AI Manual Direct Edit

Edit an existing Adobe Illustrator `.ai` or AI-editable `.pdf` (carrying `/PieceInfo /Illustrator`) directly in Adobe Illustrator on macOS against an approved review draft (审核稿) or TM-B corpus.

## Hard Working Rules

1. **Never overwrite the source master.** Copy the source file to a scratch path first and write the deliverable to a new dated/suffixed path (`<name>-<region>-<yyyymmdd>.pdf` or `.ai`).
2. **Preserve dielines, bleed, color space, and AI editability.** Never edit an Illustrator PDF with PyMuPDF redactions or overlays — PyMuPDF leaves stale `/PieceInfo /Illustrator` so Illustrator ignores the edits. Always execute natively in Adobe Illustrator and save with `PDFSaveOptions.preserveEditability = true` (or `IllustratorSaveOptions` for `.ai`). Keep existing dieline/bleed geometry and CMYK color space intact unless the task explicitly trims removed language pages.
3. **Pure ASCII ExtendScript only.** On Chinese macOS, ExtendScript reads non-ASCII `.jsx` files in legacy encoding and corrupts accents/symbols (`é`, `°`, `±`, `×`, `–`, `⎓`, `₄`). Escape every non-ASCII character as `\uXXXX` and validate via `scripts/run_illustrator_jsx.py` before invoking Illustrator.
4. **Mark edits in pure CMYK red by default.** Color every modified or newly added text span in `CMYK 0/100/100/0` (or an operator-chosen review color) while leaving unchanged copy in its original dark gray. Reviewers can inspect every diff at a glance and reset all red spans in Illustrator in one step (`Select → Same → Fill Color`).
5. **Two-stage verification gate before delivery.** Automated PyMuPDF QA (`scripts/verify_ai_output.py`) checks `/PieceInfo /Illustrator`, page count, zero stale values, and 100% required phrases, **followed by mandatory visual inspection of rendered PNGs** for every modified page (catches `AreaText` bottom clipping, line-wrap overlap, and shifted headers that text extraction cannot see).

## 5-Step Workflow

### Step 1 — Gather Authoritative Source Copy

- **From a review draft (审核稿):** pull the latest draft from `Hello-Docs-Review` via read-only `git -C <Hello-Docs-Review> fetch origin` + `git show origin/main:...` (never modify that checkout).
- **From corpus / terminology:** query `Translation_Memory` and `Terms` via [`bitable-translation-memory`](../bitable-translation-memory/SKILL.md) before authoring replacement strings.
- Copy the source `.ai` / `.pdf` to a scratch copy; confirm the original stays read-only.

### Step 2 — Inspect Canvas & Dump Native TextFrames

Run `scripts/inspect_ai_doc.py` on the scratch copy to determine whether the master is **multi-artboard** (one artboard per page) or a **single giant imposition sheet** (all pages placed on `artboards[0]`):

```sh
python .agents/skills/ai-manual-direct-edit/scripts/inspect_ai_doc.py \
  --source /path/to/scratch_copy.pdf \
  --out-report /path/to/inspect.txt \
  --dump-frames /path/to/frames.txt
```

For a single-sheet imposition master, first run without `--dump-frames` (or inspect page frame coordinates), supply `--page-boxes /path/to/page_boxes.json` (list of `{"name": "P01_Cover", "rect": [left, top, right, bottom]}`), and re-run with `--dump-frames` so every frame is grouped with page-relative `x, y, w, h` coordinates.

### Step 3 — Author a Task ExtendScript Using `scripts/ai_edit_lib.jsx`

Write a pure-ASCII task `.jsx` script that uses the reusable helpers in `scripts/ai_edit_lib.jsx` (see [`references/extendscript-patterns.md`](references/extendscript-patterns.md) for function signatures and traps):

- `aiFindFrame(doc, rect, substr, {yMin, yMax})` — narrow by vertical band when identical text appears twice on a page.
- `aiReplaceSub(tf, oldStr, newStr, {all, color})` — character-level replacement preserving surrounding styles and coloring only the replaced span red.
- `aiFixSpecialGlyphs(tf)` — maps `⎓` (`\u2393`) → `SegoeUISymbol`, `①` (`\u2460`) → `NotoSansSymbols-Regular`, and `₄` (`\u2084`) → scaled baseline-shifted subscript `4`.
- `aiDrawNativeTable` / `aiAddCalloutPill` / `aiAddAreaText` / `aiAddPointText` — rebuild tables and callout boxes as native CMYK Illustrator objects.
- `aiRemoveItemsOutsideBoxes` / `aiRemoveItemsInBand` / `aiTranslateItemsInBand` — always filter by `visibleBounds` (never `geometricBounds`) so cross-artboard `ClipGroup` artwork is not deleted, and translate adjacent sections **before** expanding an `AreaText` frame's height.
- `aiSaveEditablePdf(doc, outPath)` or `aiSaveNativeAi(doc, outPath)` — saves natively without touching the source file.

### Step 4 — Validate Pure ASCII & Execute in Adobe Illustrator

```sh
python .agents/skills/ai-manual-direct-edit/scripts/run_illustrator_jsx.py \
  --script /path/to/task_edit.jsx \
  --with-lib \
  --source /path/to/source_master.pdf \
  --out /path/to/deliverable.pdf \
  --log /path/to/run_log.txt
```

`run_illustrator_jsx.py` enforces:
- `--source` and `--out` resolve to different paths (hard refusal to overwrite source).
- Zero non-ASCII characters in the bundled `.jsx` (prints exact line/column and `\uXXXX` escape on failure).
- Clean execution log with zero `WARNING:` / `ERROR:` lines (override only with `--allow-warnings` when inspecting a partial pass).

Use `--check-only` to validate ASCII and source/output guards offline without launching Illustrator.

### Step 5 — Automated QA & Mandatory Visual Review

Author a JSON QA spec (`expected_pages`, `require_illustrator`, `stale_patterns`, `must_exist`) per [`references/extendscript-patterns.md`](references/extendscript-patterns.md) and run:

```sh
python .agents/skills/ai-manual-direct-edit/scripts/verify_ai_output.py \
  --pdf /path/to/deliverable.pdf \
  --spec /path/to/qa_spec.json \
  --render-dir /path/to/rendered_pages \
  --dpi 150
```

Then **visually inspect every rendered PNG of modified pages** to confirm:
- No clipped lines at the bottom of `AreaText` boxes.
- No overlap between wrapped paragraphs and callout pills / tables below them.
- Correct special glyphs (`⎓`, `°`, `±`, `×`, `LiFePO₄`) and balanced margins.
- List any legacy vector illustrations (hardware line art, bracket steps) that still require designer artwork swaps in the handoff note.

## Validation

- Offline unit suite: `python -m unittest tests.test_ai_manual_direct_edit_skill`
- Live Illustrator delivery: `verify_ai_output.py` passes with `0` stale values, `100%` required phrases, `/PieceInfo /Illustrator` present, and every modified page visually verified from rendered PNGs.
