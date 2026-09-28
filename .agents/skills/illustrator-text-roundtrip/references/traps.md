# Illustrator text round-trip — traps

Each entry is a real failure with the wrong output it produces. Every one is pinned by
a check in `scripts/verify_importer.py`, so if you change the importer and a check
goes red, this file says what broke and why it matters.

## 1. Frame-level assignment flattens formatting

`textFrame.contents = x` and `paragraph.contents = x` make the whole assigned range
inherit the character attributes of its **first** character.

```
source   "Long Lifespan: " (Gilroy-Bold 20.5) + "6000 Cycles" (Gilroy-Medium 20.5)
wrong    "Longa vida útil: 6.000 ciclos"   ← all bold, value no longer differentiated
right    Bold run and Medium run replaced separately, both weights preserved
```

Same mechanism silently kills superscript footnote markers: a `¹` set at 4 pt inside a
6.8 pt line comes back at 6.8 pt. This is the reason the importer works at run level,
and the reason the CSV needs **one row per run** for mixed lines.

The importer's `allowFlatten` option exists only for the case where you genuinely have
just a whole-paragraph translation and accept the loss. It reports the action as
`REPLACE_FLATTENED` so it can never happen quietly.

## 2. The target's own whitespace gets eaten

Found by the harness, not by reading the code. With whitespace-insensitive matching on,
the importer trims the source to find a match and re-attaches the original lead/tail.
Applying that trim to an **exact** match destroys spacing the translator put there:

```
run      "Long Lifespan: "        target "Longa vida útil: "
wrong    "Longa vida útil:6.000 ciclos"     ← space after the colon gone
right    exact match  → target written verbatim
         trimmed match → lead + trim(target) + tail
```

Rule: only trim the target when the *match itself* needed trimming.

## 3. Deletions that do not round-trip

The dry-run report is meant to be re-imported. A deletion whose `TargetText` cell comes
back **empty** reads as "leave unchanged" on the next pass, so the deletion silently
stops happening. A `DELETE` verdict must write the literal `[[DELETE]]` token into the
report. Same reasoning for `UNCHANGED`, which writes the resolved text so the report
reads as a complete statement of intent rather than a set of blanks.

## 4. Two identical runs, different fates

```
"AC Output in Bypass Mode" | "1"(4pt) | " | Sortie CA en mode dérivation" | "1"(4pt)
```

The Canada bilingual gloss must go **and so must the superscript that belongs to it**,
while the first superscript stays. Text-keyed matching cannot express this: deleting
only the gloss leaves `Bypass11`, and mapping `1`→`1` cannot distinguish the two.

Glossary mode genuinely cannot do this — the check
`glossary mode cannot separate identical runs (known limit)` pins the wrong output on
purpose so nobody "fixes" it by guessing. Use positional mode.

## 5. Stale offsets

Positional mode addresses runs by character offset, which is only valid while the
document is unchanged. So it verifies the recorded `SourceText` against what is
actually at that position and **refuses per position** on a mismatch, naming the CSV
row, the expected text and the actual text. One refusal does not block the other
positions; the summary reports the count and the report marks them `REFUSED_STALE`.

Read the failure count in the summary dialog. A non-zero value means re-run the dry
run — never force it.

## 6. All-caps is a paragraph style, not the text

The stored string and the printed string differ:

| in the frame | on the box |
| --- | --- |
| `Input PORTS` | INPUT PORTS |
| `OUTput PORTS` | OUTPUT PORTS |
| `Input/OUTput PORTS` | INPUT/OUTPUT PORTS |

Key the CSV off what the extractor reports (the stored form). Do not "correct" the odd
casing in the source column — it will stop matching. And do not uppercase the target
by hand; the paragraph style still does that after the swap.

If you cross-check with a PDF text extraction, expect exactly this class of
difference, plus paragraph wrapping: a PDF layer reports one visual line per wrap while
the frame holds one paragraph.

## 7. Text that is not text

The extractor only sees live text frames. Copy can also be:

- **outlined** (converted to paths) — a logo or headline; no text to replace, the
  designer redraws it
- inside **placed/linked art** or a raster image — open the source file instead
- on a **hidden or locked layer** — the extractor's own options control these, and the
  importer has the matching pair; defaults are locked-included, hidden-excluded

A count mismatch against the PDF text layer is the cheap detector for all three.

## 8. Overflow is the normal failure after translation

Latin languages run 15–50% longer than English. Tight marketing headlines break first:

```
"Seamless Auto-Switching: UPS 10ms"                    33 chars, 20.5 pt
"Comutação automática sem interrupção: UPS de 10 ms"   50 chars  ← +52%
```

Area-text frames report `overflows`; the importer's report has an `OversetAfter`
column and the summary counts the frames. Point text does **not** report overflow — it
just runs past the artwork edge, so small spec type still needs a visual pass.

Carry a short alternative for headline rows in the CSV notes so the designer can pick
without another translation round.

## 9. Undo

Illustrator's undo across many scripted text edits is unreliable. Work on a copy of
the `.ai`. The dialog says so; believe it.
