# JBP-1000B-SIL US native PDF Web intake

Status: active

## Discovery and execution plan

Authority: `Jackery Battery Pack-1.pdf`, SHA-256 `7afcb2a1e9e7b2011ddbfbe3ed81aa6c5ec5d196e4d9ad008208195fa06b6137`, 52 physical pages. English 4–19, French 20–35, Spanish 36–51; shared prefaces and contacts on 1–3/52. This is the FridgeGuard battery, not JBP-2000B. Preserve its native wording/specifications and installation steps.

Git-only: source-local frozen input + shared Manual IR/ComponentSpec replay. No phase2 enrollment, Base, queue or live registry writes; no publication authorization for this target. Isolated worktree preserves root tmp and all other checkouts.

Reference structure: JBP-2000B EU English chapters/components; retain this source's additional positioning/vertical/wood/concrete installation. Existing family configuration stays unchanged.

Phases: (1) inventory shared assets and source text/geometry; (2) EN semantic content and artwork via committed asset operators, strict Sphinx/cold replay, desktop/mobile visual acceptance; (3) only after EN acceptance, native FR/ES content over byte-identical neutral art; (4) source coverage, hash/geometry checks and PR validation. Source-local files under data/manual_sources/JBP-1000B-SIL/US; source recipe under data/asset_recipes. No shared renderer changes unless independently justified.

Safety net: source hash and page count, individual asset/input hashes, native text coverage census, original-vector provenance, no duplicate artwork labels, forbidden caption-frame checks, desktop/mobile image and text geometry. Rebuild outputs use unused scratch directories.

## Artwork selection before extraction

| Role | Candidates | Decision and reason | Background policy |
| --- | --- | --- | --- |
| Seven safety symbols | shared/symbols/native-v1; legacy common PNG | Inspect native glyph and transparency; reuse matching native variants; reject withdrawn legacy hashes | True transparency; no page/cell grey backdrop |
| Battery/product diagrams | jbp2000b_eu_en; je1000e_sil_us_en; supplied PDF | Different battery silhouette/thickness/connectors and installation geometry; native extraction required for product-specific art | Preserve structural panels/shading/leaders; independent text pills drawn in CSS |
| Manual/cable/brackets cards | JBP-2000B inbox candidates; native p5 | Compare actual cable/manual/stands, reuse exact candidate only | Complete object boundaries |
| FR/ES artwork | English neutral assets | Reuse byte-identical after English visual acceptance; native labels remain locale-specific | No per-language recrop |

## Source exceptions

Recover missing native PDF extraction segments against rendered text and record exact replacement. Preserve FR storage interval and ES residual English/product naming discrepancies with an explicit audit; do not silently translate or alter legal copy.

## Verification and acceptance

English layout acceptance was recorded at 2026-10-08T16:16:26Z before native French/Spanish production. Final acceptance at 1280×900 and 390×844 covers all three locales: 52 loaded images each, zero broken images, zero page horizontal overflow and no clipped live figure labels. Browser inspection covered safety glyphs, overview/LCD, power controls, positioning, vertical/wood/concrete installation, connections/charging/storage and warranty. Steps use two desktop columns and one mobile column; narrow installation-result artwork is capped at 120px. Complete product/panel/leader bounds are retained, SOLD SEPARATELY and car-note frames are CSS, and figure labels remain editable HTML. The LCD table scrolls internally on narrow screens.

All three packages share the same 52 source artwork bytes. Existing warning/WEEE assets were reused exactly. Five source-matched transparent native glyph variants were added to the shared symbol catalog once; older valid variants remain intact. Twenty-one source-bound symbol rows pass the fixed comparison gate with no threshold relaxation. Rejected legacy raster hashes are recorded and cannot return in fresh validation. The connection-note battery glyph is restored as an inline native SVG; an existing x8 glyph was rejected because its shape differs.

Native line census passes: EN 398, FR 446, ES 443. This complements visual and semantic inspection, rather than proving text placement by itself. Native defects remain documented in source/native_exceptions.json, including French 2-month storage versus English/Spanish 12 months, residual English/Spanish in the French installation copy, residual English in Spanish, and source warranty/product-naming defects. No unsolicited translation or correction was made.

Validation commands (all from this isolated worktree):

```sh
python3 -m unittest tests.test_symbol_asset_admission tests.test_caption_frame_admission tests.test_web_frozen_source_evidence
python3 -m ruff check build.py integrations tools tests scripts
python3 -m ruff check data/manual_sources/JBP-1000B-SIL/US/git-20261008-7afcb2a1/rebuild.py data/manual_sources/JBP-1000B-SIL/US/git-20261008-7afcb2a1/validate_source.py
python3 tools/check_maintainability_guardrails.py
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off AUTO_MANUAL_PRESENTATION_PROFILE=web python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US --lang en --data-root tests/fixtures/phase2 --staging-root tmp/jbp1000b-sil/fixture-regression-final --no-clean --skip-root-index
```

Targeted tests: 29 passed. The existing US/en fixture build check passed; it validates pipeline regression, not this battery's native body or phase2 enrollment. An optional JBP-2000B family check failed because the available unrelated phase2 snapshot has no matching symbols rows; no Base/snapshot changes were made. The documented fixture check replaces that unsuitable optional dataset check.

The extraction recipe reproduced all 154 artifacts (50 exports, 52 archived page PDFs, 52 previews) against pinned hashes. Intake manifest SHA-256: ec5da10a75cf717a2da3a4e99f7d36b0b7a28a674927325c1e90971bdb9da165. Recipe geometry and source artwork decisions are synchronized; frozen inputs and shared contracts are hash-bound. Three fresh cold replays, frozen byte parity, strict Sphinx, native text/artwork validation, caption-frame admission and all 21 symbol rows are checked again after the final freeze. A deliberately wrong input hash is rejected without modifying source files.

Final local previews: port 8892, /final/{en,fr,es}/manual_jbp1000bsil_us_{en,fr,es}.html. This intake is an engineering Git-only candidate. It has no merge, Hello-Docs mirror, RTD receipt or live acceptance claim.

Full canonical-temp unittest regression: 5217 tests, OK (skipped=35), 717.283 seconds. Only the test process temporary path was resolved; no host configuration changed.

## Native preface correction after operator screenshots

The initial extraction consumed only four p2 prose blocks per locale and omitted the fifth native title/region block; its text census had the same gap. Restore US IMPORTANT / FR IMPORTANT / ES IMPORTANTE as the leading editable heading, replacing the invented product-name heading. Shared opt-in preface classes in web_source_panels.css remove the chapter bar, render the native badge and compact the four native paragraphs. No artwork bytes or other chapter headings change. Validation now includes all five p2 blocks and explicitly requires each locale's heading and badge. Native line counts are EN 399 / FR 447 / ES 444. Desktop 1280×900 and mobile 390×844 browser inspection passed in all three locales with no page overflow. Three strict Sphinx builds and frozen package parity pass. The prior 5217-test run describes the initial intake; this CSS/content refinement receives targeted verification and fresh source/admission checks.

## FCC native composition correction

Replace the three plain FCC paragraph carriers with the existing HB-SPECIAL-FCC/two-column ComponentSpec. Preserve the native words, split the four corrective measures into a semantic list and bind NOTE/REMARQUE/NOTA plus MODIFICATION/MODIFICACIÓN as bold labels. Shared FCC rules provide the rounded grey panel, desktop two-column geometry, mobile single-column reading order and hidden chapter bar. Source-local geometry puts the small mark above the left opening copy. French opening punctuation uses a nonbreaking space before its colon to avoid an isolated colon, without changing words.

The only existing shared FCC raster (SHA-256 45f309ed8b3f4787b6dde440c738b8e0fbc5074bf758fecc2e1ac44307153d90) has an opaque grey corner and partially translucent pale matte. It is rejected for this transparent Web glyph and recorded in the existing asset decision log before extraction. Original p5 drawing 707 yields a complete transparent native FCC SVG; drawing 706 is the rounded page background and is excluded. The native glyph was inspected at 12x and added once to the existing shared catalog as fcc/nested-c-native-dark, with source/recipe/hash provenance; three languages reuse its exact bytes. No live registry promotion occurs.

All three desktop/mobile FCC views passed at 1280×900 and 390×844, with two/one columns, four measures, two bold labels, 53 loaded images, zero broken images and no page overflow. The intake now has 53 shared artwork files (the initial 52 plus the admitted FCC mark). Source validation explicitly rejects a missing FCC component/mark/measures/labels. Targeted FCC, symbol, caption-frame and frozen-source tests pass: 49 tests. Fresh native coverage remains EN 399 / FR 447 / ES 444; three strict Sphinx builds pass.

Final FCC recipe replay passed: 155 artifacts (51 exports and 104 archive/preview files), manifest SHA-256 4bebaf75a50ea2d35f1c3e1204f8bac88b4da6b94e3c38e510113e8b07f56ae8.

Final cold replay passes all three locale package comparisons, native text coverage, 21 symbol admissions and CSS caption-frame admission. Negative probes reject missing preface and FCC roles; the wrong-input-hash probe is also rejected. Final French punctuation rebuild was reloaded and visually checked.

## LCD icon size correction

Operator comparison exposed undersized LCD indicator art under the shared fixed 3rem square fit. Source-local geometry increases icon width to 4.5rem (72px, +50%), preserves intrinsic SVG height, expands the icon column from 11% to 14% and reduces horizontal icon-cell padding. All 53 artwork bytes remain unchanged. Desktop 1280×900 and mobile 390×844 checks across EN/FR/ES confirm seven loaded icons, no image/cell overlap and no page overflow. Mobile retains the shared internal 640px table scroll rather than shrinking the icons.

LCD final cold replay passes strict Sphinx, frozen byte parity, unchanged native coverage, all 21 symbol rows, CSS caption-frame admission and wrong-input rejection in all three languages.

## Power composition correction

Operator comparison exposed the missing native rounded outer frame, separated full-width Note and loose state/instruction spacing. Group the existing reference-figure and Note ComponentSpecs without changing their words or art bytes. CSS uses shared panel/color tokens to restore the frame, desktop right-bottom inset Note and native light label/white body. Native state labels are enlarged; instruction rectangles are moved closer. EN/FR/ES pass desktop 1280×900 and mobile 390×844 visual checks, with five live labels and Note inside the frame, no page overflow. Mobile reuses the shared readable stacked labels to avoid the French long-press text overlapping the baked clock mark; the Note follows inside the same frame.

Power final cold replay passes strict Sphinx, frozen byte parity, unchanged native copy/artwork census, 21 symbol admissions, CSS caption-frame admission and wrong-input rejection. The 29 reference/flow/callout/frozen-evidence tests pass.

## LCD mode table correction

The generic six-row table repeated states and missed the existing LCD mode presentation. Bind native words and the unchanged lcd-button.png to HB-TABLE-LCD-MODE/two-state-three-action. Its shared renderer restores two rowspan=3 state cells, grey state/action backgrounds, dark rules and rounded outer border. Source-local geometry sizes the portrait to the table height without distorting its aspect ratio; state text stays regular and actions medium-bold. The obsolete native-lcd-actions layout is removed.

EN/FR/ES browser checks pass at 1280×900 and 390×844. Desktop image/table heights match: EN 389.164px, FR/ES 425.984px. Artwork remains complete, with no image/table overlap or page overflow. Mobile uses a 144px-wide native-aspect illustration above a 544px internally scrollable table in the 358px panel. The 28 existing LCD mode/section/flow/frozen-evidence tests pass; three strict Sphinx builds and native line/artwork census remain valid. This source refinement does not rerun the initial full-suite claim.

LCD mode final cold replay passes all three locales: frozen parity, strict Sphinx, unchanged native text/artwork coverage, 21 symbol admissions, caption-frame admission and wrong-input rejection. Documentation link integrity passes with 0 broken links.

## Bracket caution list spacing

The English bracket caution carrier split its two bullets into separate unordered lists, creating an extra inter-list margin. Merge them into one two-item list, matching the existing French/Spanish carrier structure; preserve the ComponentSpec words and shared callout CSS. All three desktop/mobile checks confirm one list, two bullets, 5.4375px between items and no page overflow. Three strict Sphinx rebuilds preserve native coverage and all 53 artwork bytes.

## Vertical stand opening correction

Operator comparison exposed the chapter bar, preparation text outside its image and oversized equal-width cards. Preserve the chapter heading/TOC while rendering its native plain style. Move the native preparation caption into the existing HB-SPECIAL-REFERENCE-FIGURE base-art-live-copy component, with a hash-bound existing vertical-prep.png and locale-native live text. Remove the two opening card wrappers; put introduction and preparation art left, unframed result art right. The original 53 artwork files remain byte-identical; no recrop or extraction is performed.

All three locales pass 1280×900 and 390×844 browser inspection: caption inside its panel with no clipping, transparent heading, preserved chapter navigation, no image overlap/page overflow, and native result aspect ratio (198/354). Desktop prep width is 449.227px; result 173.805×310.742px with 34.164px clearance. Mobile stacks a 358px preparation panel and 120px native-aspect result art. The 22 existing base-art/flow/frozen-evidence tests pass, along with strict Sphinx, frozen parity and unchanged native text/artwork census.

### Vertical-stand full-width installation rows

The three installation steps now follow the native one-step-per-row composition through source-local CSS scoped to the three locale section IDs. All words and 53 artwork files remain unchanged. EN/FR/ES at 1280×900 and 390×844 have equal-width vertically ordered cards, loaded images at native aspect ratio and no page overflow. Strict Sphinx and native text/artwork coverage pass for all three locales.

### Wall-mount heading and introductory spacing

The wall-mount title reuses the source-local plain heading treatment already accepted for the vertical stand. Wooden/concrete-wall subheadings omit the native-absent round marker; the introduction is compact, with a 5.59px title gap and 10.40px subsection gap. EN/FR/ES at 1280×900 and 390×844 retain chapter navigation, contained headings and no page overflow. Native words and artwork remain unchanged; strict Sphinx/native coverage and cold replay pass.
