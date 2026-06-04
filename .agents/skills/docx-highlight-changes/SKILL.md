---
name: docx-highlight-changes
description: Highlight specific text spans inside a Word .docx with a colour of your choice — to show a reviewer exactly what changed. Use after you correct/edit a manual and want every edit marked, or to flag terms, unresolved placeholders, or untranslated source. It colours ONLY the exact target text (splits runs, works across run boundaries, can colour a single character such as one accent), in any colour, via background shading or the Word highlighter pen. Trigger on "highlight the changes I made", "mark these fixes in green/yellow", "高亮我改的地方", "把修改的地方标出来", "让我选颜色高亮", "用绿色/黄色标出来", even when the user doesn't name the file type — as long as a .docx is in play.
---

# Highlight changes in a .docx

When you hand someone a corrected Word manual, "trust me, I fixed it" is not
reviewable. Marking the **exact** fragments you changed — in a colour the reviewer
recognises — lets them check every edit at a glance instead of re-reading the whole
document. That is what this skill is for: precise, programmatic highlighting of
chosen text spans, leaving everything else untouched.

This is different from Word's highlighter, which only paints a selection a human
made by hand. Here you name the spans (the strings you edited) and a colour, and the
bundled script colours just those — even a single accent character mid-word.

## The core tool

`scripts/highlight_changes.py` does the work. A `.docx` stores text in runs
(`<w:r>`), and one logical word is often split across several runs, so the script
locates each target in the *concatenated* paragraph text, then splits the underlying
runs at the target's boundaries and adds the colour to only the covering run(s),
cloning each original run's formatting (bold, size, font) so nothing else shifts.

Requires `lxml` (faithful OOXML round-trip): `python -m pip install lxml` if missing.

### Simple use — colour whole phrases

```bash
python scripts/highlight_changes.py --in in.docx --out out.docx --color green \
  --target "non è incluso, ma è disponibile" \
  --target "verrà disassociato"
```

`--target` is repeatable. `--in`/`--out` may be the same path to edit in place
(write to a temp path first if you want to keep the original).

### Rich use — per-target colours, or colour a sub-substring

Pass `--spec FILE.json` instead of (or with) `--target`. The JSON is either an
object `{"color": "...", "style": "...", "targets": [ ...items... ]}` or a bare
list of items. Each item is one of:

```jsonc
"whole phrase to highlight"                      // colour the whole phrase
{"text": "phrase", "color": "yellow"}            // give this target its own colour
{"text": "CA o CC è attiva", "mark": "è"}        // locate by context, colour ONLY the "è"
```

The `mark` form is how you highlight one character without painting the words around
it: `text` is a unique-enough context so the script finds the right spot, `mark` is
the substring within it that actually gets coloured. This is exactly how you mark a
restored accent (`e`→`è`) and nothing else.

## Choosing the colour

Two mechanisms, chosen with `--style` (or `"style"` in the spec):

| `--style` | XML | Colour values | When |
|-----------|-----|---------------|------|
| `shading` (default) | `<w:shd>` run background | **any 6-digit hex**, or a name below | matches soft pastel marks teams already use; lets you pick *exactly* the colour, and distinguish your pass from someone else's |
| `highlight` | `<w:highlight>` Word highlighter pen | Word palette name only | renders identically across Word versions/readers |

Shading colour names (sugar over "any hex works"): `green` (92D050), `lightgreen`,
`darkgreen`, `yellow`, `lightyellow`, `gold`, `orange`, `pink`, `magenta`, `cyan`,
`blue`, `lightblue`, `red`, `gray`. Pass any `#RRGGBB`/`RRGGBB` for anything else.

Highlighter-pen palette (the only values `highlight` accepts): `yellow`, `green`,
`cyan`, `magenta`, `blue`, `red`, `darkBlue`, `darkCyan`, `darkGreen`,
`darkMagenta`, `darkRed`, `darkYellow`, `darkGray`, `lightGray`, `black`, `white`.

**Always ask the user / confirm the colour and style** when they care — colour is the
whole point of the request. A common pattern: green for "my edits this round" when an
earlier pass already used yellow, so the two are distinguishable.

## Workflow

1. **Know the spans.** Highlight what you actually changed. If you just made the
   edits, you already have the exact strings — feed them as targets. If you only have
   a before and after file, derive the changed fragments first (diff the extracted
   text), then highlight those.
2. **Run the script** with your targets, colour, and style.
3. **Read the report — never skip this.** The script prints one line per target and
   exits non-zero if any target was `NOT FOUND (0)`. A miss means the reviewer would
   see an unmarked change, so treat it as a real failure: the string probably isn't
   contiguous in a single paragraph (it spans paragraphs, lives in a header/footer, or
   has different spacing/characters than you typed). Fix the target and re-run.
4. **Spot-check** for anything important: re-extract text (`pandoc out.docx -t plain`)
   to confirm wording is unchanged, or count coloured runs to confirm the expected
   number got marked.

## Composing with other skills

- To **read or edit** the .docx first, use the `docx` skill (unpack → edit → repack)
  or just `unzip -p file.docx word/document.xml`. This skill is the *marking* step you
  run after the text edits are in place.
- For a translation/review job that also needs source highlighting conventions
  (`==...==`), this complements `manual-rewrite-with-tm` / `bilingual-tm-maintenance`:
  use those for the rewrite, this to colour the resulting Word file for the reviewer.

## Limits (v1)

- Operates on the document body (`word/document.xml`). Text that lives only in
  **headers/footers** or **text boxes/drawings** may not be reached — the report will
  show it as `NOT FOUND`, which is your signal to handle it another way.
- A target must be contiguous **within one paragraph** to match (cross-*run* is fine,
  cross-*paragraph* is not).
- Complex runs (tabs, line breaks, embedded drawings) are highlighted whole rather
  than sliced — rare in body prose, but worth knowing.
