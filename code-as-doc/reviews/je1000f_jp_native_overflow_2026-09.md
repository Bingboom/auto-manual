# JE-1000F JP native overflow repair — 2026-09-05

## Baseline and scope

The three round-three PRs merged in order with 17/17 final-head checks passing:
IR #1039 (`951e2210`), Web #1040 (`4d91d96b`), data #1041 (`f49b394a`).
This independent repair starts at `f49b394a`, using the same frozen local
JP snapshot as the previous preview. No live tables or source copy changed.

InDesign 21.0.1.6 reproduced two overset stories and 17 overset cells on
physical pages 14–17 and 24. Both inspection passes report the same findings;
the aggregate 38 is not a count of distinct defects.

## Findings and implementation

1. The measured operation plan injected a next-page paragraph before the final
   button table. Preceding native content already occupied page four of the
   chain. The table could not compose, regardless of row height or frame
   enlargement. Removing only the injected break composed all 15 cells; the
   native table height was 76.2001 pt. Approved-reference boundaries and
   explicitly authored breaks remain intact.
2. The temperature table had three rows in a 27.11 pt reference shell. Native
   composition needed 41.0901 pt. Measured fallback shells now use the emitted
   column widths, cell insets and Unicode line estimates, with the historical
   shell as a floor. Approved reference, compact and no-plan export paths keep
   their existing geometry. The existing fallback data-page caller owns opt-in;
   no per-model or per-language layout branch was added.
3. After clearing overset, PDF export exposed 20 `.notdef` glyphs for U+2103
   (`℃`) in Gilroy. The existing bundled Noto Sans face contains this glyph
   (verified glyph ID 2476), so the shared symbol fallback now routes the
   character there. Source units and adjacent text are unchanged.

The discovery plan and native experiments preceded production changes.
Experiments ran on disposable documents without saving changes to the
previously delivered IDML/INDD. No golden baseline was regenerated and no
maintainability limit was raised.

## Verification

- `python -m unittest`: 3,640 tests; 22 skipped; remaining tests pass.
- Ruff, maintainability guardrails, US fixture and JP frozen-data `build.py check`
  pass. Four composed golden variants and low-level package goldens are unchanged.
- The real `build.py idml --config configs/config.ja.yaml --model JE-1000F
  --region JP --source runtime --data-root <frozen-snapshot> --idml-mode both
  --no-clean --skip-root-index` build passes.
- Before/after complete `manual.ir.json` is identical (270 blocks, zero skipped
  raw blocks). All 117 production stories preserve exactly 20,764 text characters.
- The layout-only candidate saves and reopens with zero overset stories/cells,
  zero missing fonts and zero bad links. It retains 28 physical pages.
- Final visual acceptance including the Celsius fallback is pending operator
  screenshots. After an interactive diagnostic export timed out, the operator
  confirmed no other InDesign editing was in progress and authorized restart,
  then changed the acceptance method: “我截图给你验收啊 不用导出了”. Further PDF
  exports stopped. The earlier diagnostic PDF is not deliverable: it contains
  the 20 missing Celsius glyphs. Do not equate zero overset with visual acceptance.

## Remaining boundaries

- This is JE-1000F/JP; JBP-2000B/JP frozen-reference D1–D4 are separate.
- Existing JP grid-table parsing can put separator text/image directives in cells
  or mix column content (operation conditions and symbol explanations). This repair
  preserves that source/IR text and does not declare those pages content-approved.
- Power on/off copy debt, native/reference pagination differences (28 versus
  22 pages), visual alignment and production eligibility remain separate review
  decisions. No reference-layout approval or production promotion is implied.
- No source schema, dependency, public CLI or workflow changes are included.
