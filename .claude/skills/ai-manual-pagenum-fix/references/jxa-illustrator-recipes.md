# JXA → Illustrator ExtendScript recipes

Every recipe below was hit against a real 161-artboard, 63MB production file (`HTE153-EU-9国语言-0923.ai`) on 2026-09-23. Read the whole file before writing a script — several of these are "the fix for the previous fix".

## 0. First, check for a font-embedding trap (do this before touching the real file)

**If this machine does not have every font the `.ai` file's live text uses installed, saving the file through Illustrator on this machine — via `doJavascript` or the GUI, with or without any edits — silently degrades any font whose glyphs use non-standard/private codepoints (custom symbol glyphs, dingbats) from a full embedded font (`Type0`/`Identity-H`, keeps any glyph) down to a lossy 256-slot subset (`Type1`/`WinAnsiEncoding`), and any glyph outside that slot table renders as a blank/box from then on.** This was proven with a zero-edit round trip: open the pristine file, immediately `saveAs` with no changes, and the symbol was already broken — it is **not** caused by the specific edits, it is inherent to opening+saving this document on a system missing the font.

Before any edit:

```bash
system_profiler SPFontsDataType 2>/dev/null | grep -i "<font family from `get_fonts()`, e.g. segoe>"
find /System/Library/Fonts /Library/Fonts ~/Library/Fonts "/Library/Application Support/Adobe" -iname "*<font>*" 2>/dev/null
```

```python
# in the diagnosis pass, for every page:
print(page.get_fonts(full=True))
```

If any font used for special glyphs isn't installed, **stop and tell the user before making any save** — quote which font, which pages/how many glyph instances are affected (count spans using that font across the whole doc), and give them the choice: get the font installed first, or accept the tradeoff and proceed (their call, not yours — it's their production file). Do not silently proceed and only discover this after the fact.

If they choose to proceed, the current numbering/TOC work is still valid and worth keeping — the font issue is an orthogonal, pre-existing-file-dependency problem, not something your edits caused, and is not made worse by doing more independent edits (it happens on the very first save either way).

## 1. Drive Illustrator over JXA, not plain AppleScript

```bash
osascript -l JavaScript -e '
var ai = Application("Adobe Illustrator 2026");   // exact app name, check /Applications
var app2 = Application.currentApplication();
app2.includeStandardAdditions = true;
var code = app2.read(Path("/absolute/ascii/path/to/script.jsx"));
var r = ai.doJavascript(code);
console.log("RESULT: " + r);
'
```

- The JXA method is **`doJavascript`** (lowercase j). Plain AppleScript (`tell application "..." to do javascript "..."`) throws a baffling fixed syntax error on this app/OS combo — don't debug it, just use JXA.
- `doJavascript` runs synchronously inside Illustrator's single UI thread. A slow script blocks *everything* — the app won't even answer a trivial `"1+1"` probe from a second `osascript` call until the first one finishes.

## 2. Non-ASCII text is corrupted somewhere in this bridge — always

Confirmed independently in two ways:
- A `.jsx` file path containing Chinese characters → `app.open()` reports "file not found" even though the file exists.
- A `.jsx` **source file** containing a literal accented character (`"PRODUKTÜBERSICHT"`) already reads back wrong when re-read from disk — the corruption happens before ExtendScript ever parses it.
- Even a `Ü` escape sequence (pure ASCII in the source) comes out as two garbled UTF-16 code units (`65533, 156`) instead of the single correct code unit (`220`) — some layer in the chain is prematurely decoding/re-encoding it.

**Rule: only ASCII touches this bridge, ever.**

- File paths: always operate on an ASCII-named scratch copy (`cp original.ai "$SCRATCH/work.ai"`), never the real (possibly non-ASCII) filename. When you're done, save to an ASCII temp path and `mv` it over the real destination from **Bash**, not from ExtendScript — `mv` is a shell operation and handles Unicode filenames fine.
- Writing a non-ASCII string into a text frame: build it **at ExtendScript runtime**, never as a literal or escape in the script source you send over the bridge:

```javascript
var UE = String.fromCharCode(220); // Ü
tf.contents = "PRODUKT" + UE + "BERSICHT";
```

- Pure digits, dashes, plain English content through this bridge is fine — only non-ASCII is at risk.

## 3. Never scan every `textFrame` once per edit target

Naive version (**do not do this** on a large doc — it silently blows the ~120s AppleEvent timeout, error `-1712`, and leaves Illustrator's UI thread stuck for an unknown time processing the abandoned script):

```javascript
for (var ti = 0; ti < targets.length; ti++) {
    for (var t = 0; t < doc.textFrames.length; t++) { /* compare */ }  // O(targets × frames)
}
```

Build a position-bucketed index in **one pass**, then look up each target in its bucket:

```javascript
var rectOf = {};               // artboard index -> artboardRect, only for artboards you need
for (var k = 0; k < abSet.length; k++) rectOf[abSet[k]] = doc.artboards[abSet[k]].artboardRect;

var buckets = {};
for (var k = 0; k < abSet.length; k++) buckets[abSet[k]] = [];

for (var t = 0; t < doc.textFrames.length; t++) {           // ONE pass over all frames
    var tf = doc.textFrames[t];
    var gb; try { gb = tf.geometricBounds; } catch (e) { continue; }
    var cx = (gb[0] + gb[2]) / 2, cy = (gb[1] + gb[3]) / 2;
    for (var k = 0; k < abSet.length; k++) {
        var r = rectOf[abSet[k]];
        if (cx >= r[0] - 2 && cx <= r[2] + 2 && cy <= r[1] + 2 && cy >= r[3] - 2) {
            buckets[abSet[k]].push({ cx: cx, cy: cy, tf: tf });
            break;
        }
    }
}

for (var ti = 0; ti < targets.length; ti++) {
    var tg = targets[ti], bucket = buckets[tg.ab];
    var best = null, bestDist = 999999;
    for (var b = 0; b < bucket.length; b++) {
        var dx = bucket[b].cx - tg.ai_x, dy = bucket[b].cy - tg.ai_y;
        var dist = dx * dx + dy * dy;              // squared — compare to a squared threshold!
        if (dist < bestDist) { bestDist = dist; best = bucket[b].tf; }
    }
    if (best && bestDist < 400.0 /* ~20pt, squared */ && best.contents === tg.old) {
        best.contents = tg.new;
    } else {
        // log a FAIL, do not guess — this caught a real mis-match once
    }
}
```

This took a 124-target run from "never finishes" to a few seconds.

## 4. If Illustrator does stop responding

Don't retry the same `doJavascript` call hoping it unsticks, and don't send more commands hoping one gets through — it's one single thread and they'll all queue up or time out too. Also check for a blocked modal alert dialog (a missing-font warning is a likely cause — see §0) before assuming it's just slow:

```javascript
app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;  // set this before opening/saving
```

If it's genuinely stuck:

```bash
pkill -9 -f "Adobe Illustrator"
open "/Applications/Adobe Illustrator 2026/Adobe Illustrator.app"
# poll until it answers a trivial probe, in an until-loop (not chained sleeps):
i=0
until osascript -l JavaScript -e 'Application("Adobe Illustrator 2026").name();' 2>/dev/null; do
  i=$((i+1)); [ $i -gt 30 ] && { echo "gave up"; break; }; sleep 2
done
```

This is safe as long as nothing was saved yet in that stuck run — re-copy the working file fresh and start over. If a save may have partially landed, don't assume; re-verify the actual saved file with PyMuPDF before trusting it.

## 5. Locate text frames by position, not content

Convert the PDF coordinates you already extracted with PyMuPDF (top-left origin, y grows down) to Illustrator's coordinates (y grows up) using the target artboard's rect:

```javascript
ai_x = pdf_x + artboard.left;
ai_y = artboard.top - pdf_y;
```

Match by nearest position (see §3) and **always verify `frame.contents === expectedOldValue` before overwriting, never assume the nearest frame is the right one.** A length-based match once found the wrong frame (two different labels happened to have the same character count) and silently overwrote a spec value that had to be restored from a length-only heuristic gone wrong — position + content double-check is what makes this safe.

For a text frame holding several stacked values (`\r`-joined lines, common for a two-column TOC's number list), replace at the **line** level, not the whole frame:

```javascript
var lines = tf.contents.split("\r");
var idx = lines.indexOf(oldVal);   // or find the unique matching line some other way
lines[idx] = newVal;
tf.contents = lines.join("\r");
```

## 6. Verify visually, not just by the edit script's own log

```javascript
doc.artboards.setActiveArtboardIndex(i);
var opts = new ExportOptionsPNG24();
opts.antiAliasing = true; opts.artBoardClipping = true;
opts.horizontalScale = 150; opts.verticalScale = 150;
doc.exportFile(new File("/scratch/verify.png"), ExportType.PNG24, opts);
```

Then actually `Read` the PNG and look at it. This is what caught the wrong-frame overwrite in §5 — the edit script reported success, the render showed the mistake immediately.

Also re-open the saved file with PyMuPDF and assert the expected values programmatically (see `diagnosis-recipes.md`) as a second, independent check in a different tool.

## 6b. Creating a footer that's missing entirely (not just wrong)

Some pages have zero footer text at all — not a wrong value, no frame. Duplicate a neighboring page's footer frame (inherits font/size/color for free) and reposition it by preserving its offset from the artboard's own corner, rather than trying to build a new text frame from scratch:

```javascript
var srcRect = doc.artboards[srcAbIndex].artboardRect;   // a page with a normal footer, e.g. the one before the gap
var dstRect = doc.artboards[dstAbIndex].artboardRect;   // the page missing its footer
// srcFrame = the footer text frame found on srcRect by position/content, e.g. contents === "91"
var gb = srcFrame.geometricBounds;                      // [left, top, right, bottom]
var offLeft = gb[0] - srcRect[0];
var offTop  = srcRect[1] - gb[1];
var dup = srcFrame.duplicate();
dup.contents = "92";                                     // the correct value for the gap page
dup.top  = dstRect[1] - offTop;
dup.left = dstRect[0] + offLeft;
```

Verify with a render export of the target artboard afterward — position, font, and color should look identical to the surrounding pages' footers.

## 7. Save back

```javascript
var opts = new IllustratorSaveOptions();
opts.compatibility = Compatibility.ILLUSTRATOR24;
opts.pdfCompatible = true;      // keep both the editable layer and the PDF-compatible layer
opts.embedICCProfile = true;
doc.saveAs(new File("/Users/you/Desktop/ascii_temp_name.ai"), opts);
```

then from Bash: `mv "/Users/you/Desktop/ascii_temp_name.ai" "/Users/you/Desktop/<real, possibly non-ASCII, name>.ai"`.

For a portrait, one-page-per-artboard PDF export (cover first, back cover last, if that's the artboard order — verify, don't assume):

```javascript
var opts = new PDFSaveOptions();
opts.artboardRange = "1-" + doc.artboards.length;
```

Prefer leaving the rest of `PDFSaveOptions` at their defaults unless you have a specific reason to change one — deviating from defaults (`preserveEditability`, `optimization`, compression settings) was tried while chasing the font-corruption bug in §0 and made no difference to that specific bug, but changing several defaults at once for no reason is its own source of surprises. Change one thing at a time if you're debugging an export difference.

Close the document when done: `app.activeDocument.close(SaveOptions.DONOTSAVECHANGES);` (only after you've already `saveAs`'d what you wanted — this just discards the in-memory doc, it does not undo a completed save).
