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

- Operator screenshot acceptance is **not passed**. Screenshots 1 and 3 show
  literal `.. image::` directives instead of safety/warning icons; the current
  generated `Story_st_01_meaning_of_symbols.xml` independently confirms 29 such
  directives. Screenshot 2 shows an EN/FR/ES contents page with ranges through
  page 54 inside the 28-page JP document; the current package confirms the same
  non-JP TOC. These are blocking content/component defects, not frame guides or
  cosmetic spacing. They need a separate table-image/target-TOC repair.
- Subsequent screenshots show the complete button table (printed page 14,
  header plus four rows) and all three temperature rows (printed page 21).
  These two visible regions close the layout-only screenshot checks. Celsius
  is still visibly missing in the supplied screenshots; the final font-fallback
  candidate needs version-identified screenshot verification.
- This is JE-1000F/JP; JBP-2000B/JP frozen-reference D1–D4 are separate.
- Existing JP grid-table parsing can put separator text/image directives in cells
  or mix column content (operation conditions and symbol explanations). This repair
  preserves that source/IR text and does not declare those pages content-approved.
- Power on/off copy debt, native/reference pagination differences (28 versus
  27 physical pages for the newly supplied reference), visual alignment and production eligibility remain separate review
  decisions. No reference-layout approval or production promotion is implied.
- No source schema, dependency, public CLI or workflow changes are included.


## Expanded screenshot review and supplied reference

The operator supplied 26 screenshots in three batches and then supplied
`Jackery ポータブル電源 1000 New取扱説明書V1.0-2026-06-05.pdf`.
The reference has 27 physical pages: cover, JP contents, printed pages 01–24,
and a back cover. All reference pages were rendered and visually inspected;
no additional InDesign export was performed. Its SHA-256 is
`d88b32fedb3f38bcbefc6df635079d10da52fd4b16e1046913c86c0c2fa65b0f`.
Metadata identifies Adobe Illustrator 30.5 (Windows); native Illustrator
editability and retained layers have not been tested. This supplied reference
supersedes the earlier 22-page comparison for this review. Screenshot numbers
below mean printed page numbers, not PDF indices. The supplied generated-book
screenshots do not cover the cover, printed page 10 or back cover, so this is
not a complete all-page acceptance.

| Generated printed page | Observed finding | Reference comparison / disposition |
| --- | --- | --- |
| Contents | EN/FR/ES and ranges through 54 | Reference contents is JP only, 01–24. Blocking target assembly defect; regenerate from the actual JP page plan, not hardcoded reference numbers. |
| Safety opening, 01–02 | Image directives and paths printed as table text | Reference 01–03 uses actual safety symbols. Blocking nested image rendering defect; current XML independently contains 29 literal image directives. |
| 03, 16, 20–21 | Missing Celsius glyphs | Reference units are visible. Layout-only screenshot candidate is not proof that the final fallback is composed correctly; verify the newer IDML separately. |
| 04 | Text-only inventory and large white area | Reference 06 combines three illustrated inventory cards with front overview. Existing text-only inventory fallback is intentional in the current build, but is not reference-equivalent; restoration is a component/asset follow-up, not proven source data loss. |
| 05, 06, 19, 25 | Blank body pages | Reference has no matching blank numbered body pages. Trace reserved spans and page allocation before removing anything; a blank screenshot alone does not establish missing content. |
| 07–08 | Front product image differs; overview labels flattened into tables | Reference 06–07 has a JE-1000F line drawing with positioned leaders. Screenshot front image label reads Explorer 2000. Asset selection and label placement need repair. |
| 09 | LCD panel crosses the body margin toward footer | Reference 07 has the diagram, 08–09 contain symbol rows. Generated page 10 was not supplied; do not claim remaining LCD rows are missing. |
| 11–13 | Uneven figure scale; literal substitution names, directive options, separators and mixed table columns | Page 12 shows `energy_saving_12h_title`, `energy_saving_12h_icon`, `es_dc`, `:alt:` and `:width:`; page 13 recovery conditions lose their two-column meaning. Reference 12–13 provides intact icons, thresholds and condition columns. Blocking parsing defects, not typography defects. Generated RST contains substitution definitions, so unresolved output is not evidence the data was absent. |
| 14 | Button table now fully visible; LED/LCD contents protrude beyond rounded containers | Button-table overflow fix passes for this visible region only. Reference 13 keeps LED/LCD diagrams and labels inside their components; original graphic button icons remain a separate fidelity gap. |
| 15–18 | UPS, charging and solar illustrations differ from target reference; car graphic contains English | Reference 14, 16–18 consistently uses the compact target unit; generated UPS/car and four-panel solar graphics include another wheeled unit. Reference car graphic says 車 and has a Japanese cable note; generated asset says Vehicle and The car charging cable is sold separately. Blocking target-asset/localization mismatch. |
| 20 | Troubleshooting rows F0–F9/FE visible | No visible missing row; reference 19 groups F0–F3, while output splits them. This structural difference alone is not content loss. F6 Celsius still needs glyph validation. |
| 21 | Three temperature rows visible, but storage durations crowded on one line | Original clipping fix passes for this region; reference 20 places the three storage durations on separate lines. Preserve this structure in a subsequent fidelity repair. |
| 22–24 | Warranty compressed and crosses bottom body margin; App section begins under warranty tail; labels detached across page break | Reference 21–22 reserves warranty pages, 23–24 App pages, with button labels attached to the figure. Follow-up should restore section/component pagination and keep labels with their figure. |

### Source-content differences requiring their own disposition

The reference is a visual/layout and asset comparison source; it is not automatic
permission to overwrite structured product records. Examples visible on the
specification pages: reference 20 lists height 233.5 mm and both JE-1000F /
JE-1000F-SG, while generated 21 lists 236 mm and JE-1000F; the reference separates
30 W and 100 W USB-C rows, while output groups them. The four-panel solar image
also differs (reference SolarSaga 100 Air ×4, generated SolarSaga 200 ×4).
Distinguish target scope, approved data revisions and incorrect asset mapping
before applying source changes. Existing operator-approved power on/off debt
remains recorded and is not reopened by this screenshot review.

### Follow-up order

1. Repair nested table images, substitutions and grid-table semantics, using
   the observed safety/energy/recovery examples as regression cases.
2. Correct JP target TOC and asset selection; use approved reference artwork
   through the existing asset pipeline, preserving editable originals.
3. Reconcile page spans and component geometry: unexplained blank pages,
   overview/LED/LCD labels, warranty/App boundaries and storage line breaks.
4. Rebuild once and repeat version-identified screenshot checks, including
   Celsius. Keep PR #1043 draft and whole-package acceptance failed until the
   appropriate repair/review decisions are made. This review adds no new code,
   changes no product source data and does not silently extend the overflow PR
   into a parser/asset/page-plan refactor.


## Authorized continuation: parsing phase

The operator authorized parsing → JP assets/TOC → pagination/components.
The parsing phase fixes display-column slicing and partial grid rules, expands
local replacements after parsing, and renders table/inline image references
through shared production/flow asset resolution. Regression cases preserve the
energy thresholds, recovery condition columns and actual linked safety icons.
Native screenshots of the rebuilt artifact remain required. No source product
values or accepted power-button copy were changed.

## JP source TOC and approved artwork

The JP manifest now declares its own IDML-only `toc` payload: Japanese title
and language header, with entries collected from the actual assembled story
headings. Other-language legacy TOC behavior is unchanged. Physical TOC slot,
folio alignment and final page spans remain part of pagination acceptance.
Validation: 3,644 unit tests (22 skipped); Ruff and maintainability guardrails
passed. The manifest-family diff carrier is updated with the added source.

The operator approved all six supplied-reference crops after removing added
manual labels. Product engravings (including outlined English and parameters)
and the Jackery logo are part of the artwork and must remain. Policy is
`fixed-product-markings`, not literal zero-visible-characters. At 12x, every
changed pixel lies inside a removed real-text annotation bound; the front
product image is pixel-identical to its reference crop. Source SHA-256:
`d88b32fedb3f38bcbefc6df635079d10da52fd4b16e1046913c86c0c2fa65b0f`.
New assets use the three dedicated asset Base tables; the legacy illustration
table is read-only despite the older extraction skill's closing checklist.

Approved artwork package: 69 files reproduced byte-for-byte by two independent
intakes; package SHA `a18da95b614b8daa78dad188660bcf46bf3827308922ea31136a98106ac7924e`,
manifest SHA `9bdf9771e9384cd316511cf210818504e56eddb0860c9dd2c51e6de7db62529f`.
Six scoped local registry entries and 12 PDF/PNG exports pin the same recipe
hashes. They retain empty annotation panels for editable-layout copy.

**Archive debt:** live bot reads verified the three dedicated asset-table
schemas and no matching source/asset/export records. Source creation returned
`91403: you don't have permission`; no successful source record or attachment
write was observed. Source, package and manifest are staged locally. Complete
new-table archival and attachment download/hash verification when the bot has
write permission. Never fall back to the read-only legacy illustration table.


## Rebuilt screenshot candidate: approved artwork and front matter

All six approved JE-1000F/JP artwork keys now override their generic keys only
for that target. IDML XML contains all six replacement filenames. The candidate
has 21 physical spreads, 96 stories and 266 IR blocks with zero skipped raw
blocks. Content-node checks find zero literal image directives, alt/width
options, energy-saving substitutions or intermediate inline-image tokens.
The Japanese TOC is physical page 2; physical page 3 starts body folio 01.
The range is 01–19 in this estimate-based candidate, not the reference's
accepted pagination. Threaded-story headings may move under native reflow;
TOC folios and all component bounds still require screenshot verification.

No new InDesign automation or native PDF export was performed. Neither fewer
estimated pages nor green automated checks certify that blank pages, overset,
LED/LCD bounds, inbox artwork or warranty/App breaks are resolved. Source
reference artwork, product values and accepted power-button-copy debt remain
unchanged. PR #1043 remains draft and native acceptance remains pending.

Automated validation for this candidate: 3,648 unit tests, 22 skipped and the
rest passing; full Ruff, maintainability guardrails and documentation-link
checks pass. US fixture and JP frozen-snapshot `build.py check` runs pass.
Delivery packaging must collect and rewrite both production and flow links;
its hash/asset/residual report is included with the screenshot candidate.

## Pagination phase: page spans and section boundaries

The authorized third phase (pagination/components) starts from a rebuild of
`96618324` against the frozen JP snapshot. That rebuild reports 28 spreads,
108 stories and 266 IR blocks with zero skipped raw blocks. The IR block count
matches the previous candidate; the spread and story counts do **not** match
the "21 physical spreads, 96 stories" recorded for the earlier screenshot
candidate, and the working tree carries no uncommitted source change that
would explain the difference. Treat the earlier spread/story figures as
unreproduced at this commit and use the numbers below.

Two allocation defects were found, both in span selection rather than in
component geometry.

1. **Blank body pages.** Under the measured-LaTeX fallback plan a story's
   spread chain is the anchor distance to the next *matched* source. Three of
   the 14 JP sources do not match, and `planned_span` skipped over them to the
   next anchor. `02_whats_in_the_box` was therefore threaded across four
   frames for one page of content, while the unmatched sources were emitted
   again as their own spreads. An unanchored gap now falls back to the height
   estimate. Explicit assembly contracts are untouched, because they return
   their declared `planned_page_count` before this path is reached.
2. **Warranty and App Setup shared one chain.** The fallback merge that avoids
   overset had merged them into `11_warranty + 12_app_setup_placeholder`, which
   is why the App section opened under the warranty tail with its button labels
   detached across the page break. Both roles are now dedicated sections that
   never share a linked chain. Because a dedicated section can no longer borrow
   its neighbour's frames, it is also never allocated below its own estimate
   under a fallback plan; the LaTeX anchor distance gave Warranty one page for
   two pages of content, which is the reported bottom-margin compression.

`[export-idml] STORY SPANS` now reports every prose story's allocated pages and
its height estimate. Measured effect on JE-1000F/JP:

| | spreads | prose pages | warranty | app |
| --- | --- | --- | --- | --- |
| before | 28 | 23 | shared chain | shared chain |
| after | 26 | 21 | 2 | 3 |

Three unrelated spans remain plan-driven and above their estimate
(`01_meaning_of_symbols=4(est3)`, `08_charging_methods=3(est2)`,
`12_app_setup_placeholder=3(est2)`). The estimate is deliberately coarse and
biased low, so these are not evidence of blank pages; the next screenshots
decide them.

### Not a layout defect: storage durations

The reference places the three storage durations on separate lines and the
generated page crowds them onto one. This is a **source-data** difference, not
composition. `Spec_Master` row
`JE-1000F_JP__v1.1__specifications__s04__r03__storage_temperature__main__l01`
carries `1ヶ月 -20℃~45℃ 3ヶ月 0℃~45℃ 1年間 0℃~25℃`, while the sibling
`JE-1800B_JP` row carries the same content with `\n` separators. Correcting it
is a live source-table write through the approval-gated path with a read-back,
not a change to this branch; the local `data/phase2` mirror is not an editing
surface.

### Still open in this phase

Component geometry is untouched: the LCD panel crossing the body margin toward
the footer, LED/LCD content protruding beyond its rounded container, and the
overview labels flattened into tables all need measured native iteration rather
than span selection, and no automated signal in this repo distinguishes a
deliberate `bottom_extra` allowance from a real overflow. They remain phase-3
work. The rebuilt LaTeX PDF also still reports 20 missing `℃` glyphs in Gilroy;
the earlier Celsius repair covered the IDML font fallback, not the LaTeX lane.

Validation for this round: 3,650 unit tests (22 skipped); full Ruff;
maintainability guardrails (the span report lives with the story emitter rather
than raising the `tools/export_idml.py` line pin); documentation links; US
fixture and JP frozen-snapshot `build.py check`. Native acceptance remains
pending and PR #1043 remains draft.
