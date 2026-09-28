---
name: illustrator-text-roundtrip
description: Export every editable string out of an Adobe Illustrator .ai (colour box, label, sticker, dieline artwork) to CSV, translate or revise it outside Illustrator, then write it back run-by-run so bold labels, superscript footnote markers and mixed-size runs survive. Use when a packaging/label .ai must be localized into a new market language, when reviewed copy must land back in artwork, or when specific artwork strings must be deleted for a region (California Prop 65, Canada bilingual glosses). Trigger on "翻译这个 ai 文件", "彩盒/标贴改文案", "导出文案再导回", "把译文灌回 Illustrator", "localize this packaging artwork". NOT for IDML/manual pipeline text (that is the build's own RST/IDML path), NOT for spec-sheet ingest (`spec-sheet-structured-intake`), and NOT for stripping text out of illustration assets (`asset-textless-extraction`).
---

# Illustrator text round-trip

Packaging artwork is the one surface the manual pipeline does not generate. Colour
boxes, labels and stickers live as `.ai` files that a designer owns, so localizing
them means getting the copy out, translating it with repo terminology, and getting it
back in without wrecking the typography. This skill is that loop, in two
ExtendScript halves plus a way to prove the import before it touches artwork.

## The two halves

| Direction | Script | What it does |
| --- | --- | --- |
| Export | `scripts/Illustrator_Text_Extractor.jsx` | Every text frame → CSV / TXT / JSON, with layer, artboard, fonts, sizes, bounds, hidden/locked/overset flags |
| Import | `scripts/Illustrator_Text_Importer.jsx` | A CSV of source→target back into the document, **one formatting run at a time** |

Both run the same way: open the document, `File > Scripts > Other Script...`, pick the
`.jsx`. Neither needs anything installed.

## The rule that matters

**Never assign `textFrame.contents` (or `paragraph.contents`) to place translated
copy.** In Illustrator the whole assigned range inherits the character attributes of
its first character, so a line like **`Long Lifespan:` 6000 Cycles** comes back
entirely bold, and a superscript `¹` footnote marker comes back full size. Real
artwork is full of these: on one colour box, 5 of 46 lines were mixed-format.

The importer therefore groups characters into runs (font + size + baseline + fill)
and replaces each run separately, back to front so earlier offsets stay valid. Give
it **one CSV row per run**, not per line:

```csv
Source,Target
"Long Lifespan: ","Longa vida útil: "
"6000 Cycles","6.000 ciclos"
```

Keep the surrounding spaces exactly as the run holds them — on an exact match the
target is written verbatim, precisely so deliberate spacing survives.

## Two matching modes

**Glossary** — match by source text. Any CSV with a source and a target column; you
pick the columns from its own header in the dialog. Fast, and enough for most work.
It cannot tell two identical strings apart.

**Positional** — match by `Frame` + `Paragraph` + `RangeStart`, verifying the recorded
source text still matches the document. This makes **the importer's own dry-run report
re-importable**, which is the canonical flow:

1. Run with **Dry run** on and your glossary CSV. Nothing changes; you get a report
   listing every run with its font, size, offsets, and pre-filled `TargetText`.
2. Fix up the rows the glossary could not reach.
3. Run again on that report. It auto-selects Positional mode.

Every run is then uniquely addressable — that is the only way to delete one `¹` while
keeping an identical one earlier in the same line. A report that no longer matches the
document is **refused per position** with the expected-vs-actual text, so a stale
report cannot silently corrupt artwork.

Target cell tokens: empty = leave unchanged, `[[SKIP]]` = deliberately unchanged,
`[[DELETE]]` = remove the text including its whitespace.

## Workflow

1. **Get the copy out.** Run the extractor (CSV, metadata on). Cross-check the count
   against the PDF text layer if the file matters — `.ai` is PDF-compatible, so
   `python3 -c "import fitz; ..."` on the same file is a free second opinion. A
   mismatch means text is outlined, on a hidden layer, or inside placed art.
2. **Translate with repo terminology, not from scratch.** Use
   `bitable-translation-memory` first: the `Terms` / `Translation_Memory` tables and
   `data/phase2/Spec_Master.csv` (`Row_label_<lang>`) / `Localized_Copy.csv`
   (`text_<lang>`) already hold approved wording for spec labels, port names and
   section headers. Mark each row TM-backed vs newly translated so the reviewer knows
   what needs审校.
3. **Split the mixed-format lines to run level** before importing. The dry-run report
   tells you which lines have more than one run.
4. **Dry run, read the report, then apply** — on a copy of the `.ai`, always.
5. **Check overflow.** The report's `OversetAfter` column flags frames that overflow
   after import. Latin languages expand 15–50% over English; small spec type and
   tight marketing headlines are where it breaks.

## Region deletions are part of the job

Localizing packaging is not only translation. Text that is legally required in one
market is wrong in another, and it must be **deleted, not translated**:
California Prop 65 warnings (plus their warning-triangle graphic, which is artwork —
delete it by hand), Canada bilingual French glosses, market-specific certification
marks. Route these through `[[DELETE]]` and say so explicitly in the handoff; also
flag what the new market *requires* and the artwork lacks (Brazil, for example, needs
importer name + CNPJ, and INMETRO marks).

## Proving a change before it touches artwork

`scripts/verify_importer.py` exercises the importer through `scripts/mock_illustrator.js`,
a stand-in for Illustrator's text DOM faithful on the one behaviour that matters
(range assignment inherits attributes at the range start). It pins 16 checks covering
every hazard above, including the glossary mode's known limit:

```bash
python3 .agents/skills/illustrator-text-roundtrip/scripts/verify_importer.py
```

Run it after **any** edit to the importer. `tests/test_illustrator_text_roundtrip.py`
wraps it for `python3 -m unittest` and skips when Node is unavailable.

## Read next

- `references/traps.md` — the failure modes with the actual wrong output each
  produces: formatting flattening, whitespace loss, non-round-tripping deletions,
  stale offsets, all-caps paragraph styles, outlined text, overset.

## Boundaries

- Manual/IDML text is the build pipeline's own surface — do not drive it through here.
- Terminology lookup and TM writes belong to `bitable-translation-memory` /
  `bilingual-tm-maintenance`.
- Removing burned-in text from illustration assets is `asset-textless-extraction`.
- `.docx` / Feishu cloud-doc pre-translation is `lark-tm-translation-preprocess`.
