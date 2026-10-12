---
description: Diagnose and fix page-number / table-of-contents defects (wrong TOC references, stale duplicate labels, mis-numbered footers, per-language numbering schemes) in a multi-language Adobe Illustrator manual (.ai, PDF-compatible, one artboard per page), and re-export a clean portrait PDF. Use when the user hands you a .ai/.indd-style manual file — typically outside this repo, e.g. on the Desktop — and asks to check or renumber page numbers, fix the TOC, or export a "竖版/portrait" PDF from it.
when_to_use: Trigger phrases include "改页码", "目录页码不对", "封面第一页/封底最后一页", "导出竖版pdf", or any request to audit/fix page numbering, TOC entries, or footer numbers in a design-team .ai manual. Also use proactively if asked to "look at" or "check" such a file for correctness before a print/release handoff.
argument-hint: "[path to the .ai file, optionally the specific TOC/footer issue reported]"
---

# AI Manual Page-Number Fix

Method distilled from fixing `HTE153-EU-9国语言-0923.ai` (Jackery Explorer 1000, 9-language EU manual, 161 artboards = 161 pages) on 2026-09-23: TOC page-reference bugs, stale duplicate TOC labels, a whole-page language-contamination bug, and a full renumbering of four language sections to continue the page count instead of each restarting at 01.

This file targeted a **standalone design-team `.ai` file outside the repo's own build pipeline** (not `docs/`, not `phase2`, not `build.py`). Treat every such file as read-first, edit-with-a-safety-net — it is often a shipping/print artifact.

## 0. Before touching anything

- Confirm the file is PDF-compatible: `file "<path>.ai"` should report `PDF document, version 1.x, N pages`. If not, this whole approach (reading via PyMuPDF, artboard-index == PDF-page-index) does not apply — stop and ask.
- Copy the original aside before any edit: `cp original.ai original_备份.ai` (or a clearly-named backup). Never edit the operator's only copy in place without one.
- Check whether Adobe Illustrator is installed and get its exact app name (`ls /Applications | grep -i illustrator`) — you need the exact version string (e.g. `Adobe Illustrator 2026`) for every `Application("...")` call.
- **Check every font the file's live text uses is actually installed on this machine, before your first save — not after.** List fonts per page with PyMuPDF (`page.get_fonts(full=True)`), then check each family under `/System/Library/Fonts`, `/Library/Fonts`, `~/Library/Fonts`, `/Library/Application Support/Adobe`. A missing font — even one used only for a handful of special-symbol glyphs — gets silently degraded (full glyph table → lossy 256-slot subset, custom glyphs turn into blank boxes) the moment Illustrator saves the file on this machine, **regardless of what you actually edit, even a zero-edit open-then-save reproduces it**. This was discovered *after* several rounds of otherwise-correct edits had already baked the damage into the saved file — do the check first next time. See `references/jxa-illustrator-recipes.md` §0.

## 1. Diagnose with PyMuPDF first — never guess, never trust one page in isolation

Do the *entire* diagnosis read-only with PyMuPDF (`fitz`, Unicode-safe, fast) before opening Illustrator at all. Use the repo's own `.venv/bin/python3` (has `fitz` installed) unless another interpreter is confirmed to have it.

- **Map the document structure once.** For a multi-language manual, find where each language's content starts/ends and what its footer-numbering convention is. Footer digits: filter spans by `bbox[1] > page_height*0.94` (bottom margin) and a numeric-only regex — but also require a specific font/size match (inspect one page's `get_text("dict")` first to find the footer's actual font name/size, e.g. `Gilroy-Regular` size `6.0`) so you don't pick up decorative numbers elsewhere on the page (list markers, diagram callouts).
- **Cross-reference the TOC against reality**, not against assumption. Extract every TOC entry's (title, claimed page) and the *actual* footer number of the page where that section's heading (large bold font, top of page) appears. Any mismatch is a real bug; do not assume TOC is right and content is wrong, or vice versa — check both directions.
- **Look for stale/duplicate text**, not just wrong numbers. A range label showing two overlapping strings (e.g. both `"01-22"` and `"01-17"` at nearly the same position) is a classic sign of an old value left behind when the page count changed and only a new text frame was added, not the old one deleted.
- **Check for whole-page contamination**, not just numbers. When a page block was cloned from another language and only partially retranslated, hardcoded headings/labels can be left in the wrong language while data-driven body text is correctly localized. Scan the suspect page's full `get_text("dict")` for spans whose script/language looks inconsistent with the rest of the page's font/content pattern (e.g. Spanish text sitting in an otherwise-German page). Do not assume the *first* bug found is the *only* one on that page — dump the whole page and read every span once.
- **State every finding to the user with page numbers and old→new values before fixing anything**, and ask when the correct target scheme is ambiguous (e.g. "should each language restart at 01, or should the whole book be one continuous sequence?" is a business/design decision, not something to infer). See `references/diagnosis-recipes.md` for the exact PyMuPDF snippets used.

## 2. Get the artboard ↔ PDF-page mapping (before any edit)

Open the file in Illustrator (see §3 for the scripting bridge) and confirm:

```
doc.artboards.length            // should equal PyMuPDF's doc.page_count
```

Verify (do not assume) that `doc.artboards[i]` (0-indexed) corresponds to PDF page `i+1` — export a couple of artboards you already identified content for by PyMuPDF and check the text matches, or list text frames per artboard and match against known page content. It has held for every file seen so far (PDF export follows artboard array order), but confirm per file.

Artboards may **not** be laid out in reading-order on the canvas (gaps, out-of-order rows) — do not derive page order from `artboardRect` position, only from array index.

## 3. Script Illustrator via the JXA bridge — read `references/jxa-illustrator-recipes.md` fully before writing any .jsx

The short version, all of which is explained with working code in that reference file:

1. Drive Illustrator with `osascript -l JavaScript -e '...'` (JXA), calling `Application("Adobe Illustrator 2026").doJavascript(jsxCodeString)` — **not** plain AppleScript `do javascript` (it errors on this app/OS combo for unclear reasons) and **not** `doJavaScript` (wrong casing).
2. **Never put non-ASCII characters in a `.jsx` file path, nor as literal characters or `\u` escapes in the JS source you send through this bridge** — they get silently corrupted somewhere in the tool-call → JXA → ExtendScript chain, even before ExtendScript's own parser sees them. Work on an ASCII-named scratch copy of the file; when you must *write* a non-ASCII string into a text frame, build it at ExtendScript runtime with `String.fromCharCode(...)`, never as a literal in your script source.
3. **Never scan all `textFrames` once per edit target** on a large multi-page doc — build a single position-indexed bucket (one pass over all frames) and look up each target in its bucket. The naive O(targets × frames) approach silently blows past the AppleEvent timeout (~120s, error `-1712`) *and* leaves Illustrator's single UI thread stuck processing the old script, unresponsive to any new command, for an unknown amount of time. If you ever see that timeout, don't keep sending more commands hoping one gets through — `pkill -9 -f "Adobe Illustrator"` (safe if nothing has been saved yet), relaunch with `open "/Applications/.../Adobe Illustrator.app"`, wait for it to answer a trivial `doJavascript` probe in an until-loop, and reopen the working copy.
4. **Locate the text frame to edit by position (converted from the PyMuPDF coordinates you already have), not by content** — TOC numbers repeat (`"05"` appears many times per page) and content matching a string with accents hits the corruption problem in point 2. Convert PDF coords (top-left origin, y-down) to Illustrator coords (y-up) with `ai_x = pdf_x + artboard.left; ai_y = artboard.top - pdf_y`, find the nearest text frame by **squared** distance (don't compare squared distance to a linear threshold — that bug wasted a whole run), and **always verify `frame.contents === expectedOldValue` before overwriting** — abort that one edit and log it rather than guessing, if it doesn't match. This caught a real mistake (a stray length-match overwrote the wrong frame and had to be restored) before it went unnoticed into the saved file.
5. Multi-line TOC blocks (one text frame with several page numbers stacked via `\r`) need a **line-level** replace: split on `\r`, replace the one line matching, rejoin, reassign `.contents`. Standalone single-value frames are simpler: `frame.contents = newValue`.

## 4. Verify visually before saving

After every batch of edits, export the affected artboards as PNG (`doc.artboards.setActiveArtboardIndex(i)`, `ExportOptionsPNG24`, `artBoardClipping = true`) and actually look at them (Read tool on the PNG) — do not trust the edit script's own success log alone. This is what caught the wrong-frame overwrite in step 3.4 above. Also re-open the saved file with PyMuPDF afterward and assert the expected values programmatically (page count unchanged, target substrings present/absent, numbering sequence exactly matches `range(1, N+1)` if it's meant to be continuous) — a second, independent check in a different tool.

## 5. Save back without corrupting the filename

Illustrator's own save/open through this bridge cannot reliably handle a non-ASCII file path (see §3.2). Save to an ASCII temp path on the Desktop with `doc.saveAs(file, new IllustratorSaveOptions())` (`pdfCompatible = true` to keep both the editable and PDF-compatible layers), then `mv` it over the real (possibly Chinese-named) destination path from Bash — `mv` is a shell operation and handles Unicode filenames fine, it's only the Illustrator-JXA-ExtendScript chain that can't.

For a portrait PDF export (cover page 1, back cover last page, one page per artboard, no spreads): `PDFSaveOptions` with `artboardRange = "1-" + doc.artboards.length` — artboard order already gives you cover-first/back-cover-last for free if that's how the source file's artboards are ordered (verify with PyMuPDF on the exported PDF, don't assume).

## 6. Close the loop

- Keep every intermediate `.jsx`/probe script and the PyMuPDF diagnosis output in the session scratchpad, not in the repo.
- Tell the user exactly what changed (table of old→new values), what you deliberately left alone and why, and any adjacent defect you noticed but that was out of the requested scope — let them decide whether to fix it in the same pass.
- If the target file's directory is a git repo (this one usually isn't the target — it's a Desktop file — but check), this skill's own edits to `.claude/skills/**` still fall under this repo's `config-review` skill and branch/PR discipline in `AGENTS.md` §8; the manual-file edits themselves are not a repo change and need no branch/PR.

See also: `references/diagnosis-recipes.md` (PyMuPDF snippets) and `references/jxa-illustrator-recipes.md` (the full JXA/ExtendScript recipes, ready to adapt).
