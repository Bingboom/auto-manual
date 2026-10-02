# JE-100C EU Web layout and incremental language intake

Status: done

English PDF corrections and all eight additional languages are implemented locally (fr/es/de/it/uk/pt/nl/pl). Nine language pages are available through the local preview portal; no publication is claimed.

### Function-table review follow-up

All nine locales retain bold Function/Description column headers and vertically
center their function and description cells. The first-column normal-weight
rule applies only to body cells. The shared stylesheet was assembled into all
nine packages and strict Sphinx builds were rerun with fresh environments and
all pages rewritten. Browser computed-style checks confirm two 700-weight
headers and ten vertically centered body cells in every locale, with no broken
images. Evidence: `languages/function-table-style-builds.json` and
`languages/function-table-style-browser.json` under the local report directory.

## Authorized publication follow-up

The operator subsequently requested “合并然后发布”; MA-226 covers engineering
PR #1383 and the nine-language Git-only release. This supersedes the original
no-merge/no-publication task boundary below; no live-table write is included.
The final preparation integrates main `8d0f1272` and preserves both independent
document additions. The check-all failure was a missing JE-100C fixture:
its source-bound two specification rows and one variable-default row now run
all nine locales. The observation gate passes with 60 PASS, 16 SKIP and the
same two pre-existing FAIL rows; neither ratchet baseline was relaxed.
All nine Web/MyST and strict Sphinx rebuilds pass after the integration.

## Discovery and implementation plan

- Engineering base: `bee0226379a7c593f4735405146ba0e7295c3731` (live fetch and GitHub API agree).
- Business-plane main inspected: `0cdd5b5d0b4e5814f0408e5e4904ead468a40d49`.
- Published target inventory: English only, `git-20260930-24f51176-shared-components`, built 2026-09-30T13:30:08Z. Canonical route: https://ht-doc.readthedocs.io/JE-100C/EU/en/md/manual_je100c_eu_en.html (browser HTTP 200). This is a single-version site; `/en/latest/` is not its canonical root.
- Source AI: `HTE162-EU-9国语言-0928(1).ai`, SHA-256 `04d5a4075fc9fc5ad630416dca8e138576e9159fcfd4ce9a06328b8aa1a39cb5`, 113 physical pages. Product name Jackery Explorer 100D; model JE-100C.
- Verified native-page boundaries: cover 1; print-only multilingual contents 2–4; en 5–16; fr 17–28; es 29–40; de 41–52; it 53–64; uk 65–76; pt 77–88; nl 89–100; pl 101–112. Page 113 has outlined compliance/manufacturer copy and a QR code; it is not blank. Storage copy on pages 14/26/38/50/62 is also outlined; visual transcription is required only for these bounded regions.
- Existing English templates remain the starting point. The operator subsequently supplied the 65-page PDF `16-0102-000467 HTE162100A-EUUK-JAK 说明书 RoHS REACH A0(1).pdf` and explicitly requested correction against it. Its SHA-256 is `efc2b120e28c562068675836ea977aa9db4e4b2571b7247f8c39be586a1b1621`; English is physical pages 4–15. The older authority remains historical provenance; `source_manifest.json::web_comparison_authority` records the new comparison source and local candidate status.
- Worktree is isolated. The branch wrapper fetched main but cannot switch main because the root checkout owns it; branch was created from the verified `origin/main` inside this clean managed worktree. Root checkout and its `tmp/` remain untouched.

## Phases and safety nets

1. Capture real desktop (1440 px) and mobile (390 px) published screenshots, document exact defects; preserve baseline HTML and native page text under `reports/je100c_eu_web_20261001/`.
2. Repair existing English using its templates, governed assets and existing `build.py md` / manual-ir/v2 / ComponentSpec / shared Web renderer. Reuse same-model textless images. Derive bounded original artwork with explicit source geometry/hash and before/after review evidence. Preserve original panel gray backgrounds, rounded borders and in-figure labels; only remove unrelated crop contamination. No generated redraw or whole-book rasterization.
3. Build with real Pandoc/Sphinx and inspect desktop/mobile before extending fr/es/de/it/uk/pt/nl/pl. New languages reuse the verified layout and common assets; copy/tables come from their own source pages, with dense overview diagrams localized.
4. Run applicable source/hash, doc-link, component and real-build validation; record numeric/legal/source differences. Create an engineering PR only after applicable checks pass.

Non-goals: live Bitable edits, source-table replacement, changing other products, self-merge, publishing, or engineering changes to Hello-Docs. Asset registry promotion and source-version approval remain separate from local candidate review.

## Current English corrections and evidence

This section supersedes the earlier seven-notice baseline and incomplete crop,
CSS and provenance findings. No manual wording is invented. The operator's
supplied PDF is the comparison source for text, styles and figures.

- Native Docutils `aside/div.admonition` boundaries were lost before Pandoc.
  The shared adapter now protects the callout type, rich body, language, ID and
  original title punctuation. Final PDF-aligned labels are `WARNING:`,
  `CAUTION`, `CAUTION`, `NOTE`, `CAUTION`, `CAUTION`.
- Removed the invented horizontal-scroll instruction and fabricated LCD
  headers. Four independent LCD icon tables have 10, 3, 3 and 2 rows. The
  three-row fault/temperature table has no invented numbers. Original icons,
  circled numbers where present, shaded columns and line-separated states
  are retained.
- Replaced the incorrect LCD SCREEN art with a bounded source crop preserving
  the product, hand, DISPLAY detail and leader. The adjacent function table
  shares its original outer frame: side by side on desktop, stacked on mobile.
- Restored the eight source symbols, including battery disposal; NOTE/TIP do
  not acquire extra warning triangles. Source safety, output/energy-saving,
  purchase strips, specifications and warranty panels now follow the supplied
  PDF. Maintenance is injected once, not duplicated by the target template.
- Explicit source containers survive the Pandoc pass. Styles belong to
  `docs/renderers/contracts/web_source_panels.css`; no size baseline was raised.
- The operator corrected the initial extraction's removal of charging-panel
  gray backgrounds. All three charging SVGs were rebuilt from PDF pages 11–12
  with the original gray regions, sloped two-tone USB-C composition, rounded
  edges and in-picture labels. No CSS flat-gray substitute is used. Separate
  duplicate SolarSaga/Vehicle paragraphs were removed.
- Derivative provenance is in
  `manual_sources/JE-100C/EU/en/2.0/web_svg_derivatives.json` and
  `web_source_corrections.json`, outside the governed recipe namespace.
  Illustration bindings and hashes were updated. Shopping-symbol reuse is
  explicitly opted in with `allow_reuse: true`; default duplicate rejection
  remains. Coverage is 11/11 finished bindings, zero missing, 17 finished image
  occurrences including four purchase-strip icons.

### Validation

All evidence below is local, under `reports/je100c_eu_web_20261001/`.

- Native-notice regression suite: 95 tests passed before the later PDF copy
  changes (`logs/note-targeted-tests-v3.log`).
- PDF/component/container suite: 77 tests passed
  (`logs/pdf-target-tests-v4.log`).
- JE-100C final target suite after gray restoration: 6 tests passed
  (`logs/gray-restored-target-tests.log`).
- Ruff passed (`logs/ruff-gray-final.log`). Discovery complexity decreased
  from 67 to 66; the ratchet requires recording improvements, so the matching
  baseline entry was lowered. Final guardrails passed for all 62 hotspot files
  (`logs/guardrails-gray-final.log`). Earlier v5 output stopped at the unrecorded
  improvement and was not a passing guardrail run.
- Actual JE-100C build through `build.py md`, followed by strict Sphinx
  `-b html -W --keep-going`, passed after the gray restoration
  (`logs/restore-gray-build.log`, `logs/restore-gray-sphinx.log`).
- The default JE-1000F US check cannot resolve Product Name because the local
  `data/phase2/Spec_Master.csv` snapshot is absent (`logs/us-build-check.log`).
  Repeating the same check with the committed `--data-root tests/fixtures/phase2`
  passed (`logs/us-fixture-build-check.log`). This is fixture regression
  validation, not a claim about live source data.
- Browser at 1440 and 390 px: zero broken images, no document overflow;
  original gray charging panels render. The 640 px LCD table scrolls inside
  its 354 px mobile container. LCD SCREEN art/table stacks inside a 356 px
  frame. All six source callout variants remain present.

Current browser evidence includes `charging-gray-restored-desktop.png`,
`charging-solar-gray-restored-desktop.png`,
`charging-car-gray-restored-desktop.png`, `charging-gray-restored-mobile.png`,
`lcd-table-scroll-mobile.png`, `lcd-actions-mobile.png`,
`lcd-table-desktop-final.png` and `charging-gray-restored-final.png`.
The older `source/latest-pdf/artwork-comparison.png` records the rejected
background removal; it is not evidence of the current result.

### Symbol crop follow-up

The operator identified a thin line beneath the dismantling prohibition icon.
The old crop reached 161pt and included the antialiased edge of the source
PDF table rule at y=161.0989pt. The new bottom edge is 160.2pt; the original
icon ends at 159.5117pt. Inspection of the same symbol group also found the
fire prohibition circle truncated at 175.4pt; its crop now reaches 176.3pt,
beyond the original circle ending at 175.6837pt and before the next rule.
Both icons were re-extracted from the same PDF, with no redraw, verified at
12x over white and checkerboard surfaces, and their provenance hashes were
updated. The source table's gray cells and borders are unchanged.

Before/after evidence: `symbol-crop-fix/symbol_dismantle-comparison.png` and
`symbol-crop-fix/symbol_fire-comparison.png`. The real build and strict Sphinx
checks passed (`logs/symbol-crop-build.log`, `logs/symbol-crop-sphinx.log`).
Both open preview tabs were refreshed and loaded the new hashed assets.
The stale candidate-derivative pointer in the source manifest was also
corrected to the existing `manual_sources/.../web_svg_derivatives.json`.

### Remaining boundaries

The full suite executed 4916 tests in 902.770 seconds: 2 failures, 29 errors,
22 skips (`logs/full-suite-pdf-corrections.log`). Nine setup errors exposed a
regression when a combined illustration consumes a secondary source image
without its own primary binding. This is repaired; the explicit reuse and
secondary-consumption regression module passed 19 tests
(`logs/illustration-reuse-regression.log`). The affected product build suites,
including JE-2000E, JE-3000C and JE-3600A, plus final JE-100C coverage passed
all 100 tests in 283.482 seconds (`logs/sibling-illustration-regression.log`).

The other 20 errors and 2 failures all report the unrelated JE-1000F sibling-AI
provenance mismatch. Current hashing confirms that local
`/private/tmp/je1000f-nine-language-intake/HTE153-EU-9国语言-0923.ai`
has SHA-256 `9441d7fe9e48341774826d226e2ee4f68d6d18a5344afb77c064ec3867bd7231`,
while its committed recipe requires
`c38415f5c2d96832119105d963737a10901e470f70c5e7518ef6404f83625eb2`.
The external fixture and its validating implementation were not changed.
The complete suite is not claimed green.

The earlier full-suite boundary above is historical. The subsequent 4966-test
language run no longer reproduced the external JE-1000F fixture failures; it
identified 11 registry/family-index assertions, repaired as described below.
No asset registry promotion, PR, merge, publication or live Bitable write was
performed.

## Eight-language intake discovery

- The supplied newer PDF has native text for fr 16–27, es 28–39, de 40–51 and it 52–63; use these pages, not OCR drafts of the older outlined AI.
- uk 65–76, pt 77–88, nl 89–100 and pl 101–112 are only present in the nine-language AI. These native-text pages still carry older AC charging instructions, omit the newer cycle-life specification and omit the battery-disposal symbol/copy. The operator explicitly selected “以新版英文为准，校正这 4 语的差异译文”; all four now carry source-bound alignment records.
- Temporary positioned-text intake produces authored RST plus field/asset source evidence. All production outputs continue through build.py, manual-ir/v2, ComponentSpec, Pandoc and Sphinx. Original source labels, notices, gray charging panels and localized dense diagrams must survive.
- Reuse frozen product identity rows and shared pictograms. Register pt/nl/pl centrally and add EU language-family configs; do not alter live schemas or source tables.
- First validate French end to end, then complete the other languages, source-coverage checks, strict builds and browser review.


## Completed eight-language intake

- Each added locale has 11 authored RST sections, a target page manifest, a
  source/asset/hash manifest, and a localized illustration binding. Existing
  EU family configurations include the new target; pt/nl/pl are language-family
  configurations. All reuse the frozen English product-identity snapshot.
- The normal production lane is unchanged: `build.py md` → manual-ir/v2 →
  ComponentSpec → Pandoc → Sphinx. Positioned-text intake scripts are evidence
  tooling under `reports/je100c_eu_web_20261001/languages/`; they produce RST
  input, never replace the production build. Regeneration order is intake,
  approved-copy alignment, then binding/hash refresh.
- Added locales reuse the corrected common artwork and original localized
  overview/LCD/solar/car art. Gray regions, rounded edges and in-figure labels
  remain source vectors. Localized battery-health sample art is a documented
  exception to shared-icon reuse because the AI prints native-language text
  inside the icon. Its right crop ends at 57.65 pt, before the source table
  stroke starting near 57.912 pt. The four final 12× raster inspections show
  complete text and no stray rule.
- Signal labels carry explicit semantic RST roles; warning/caution retain their
  triangle and note/tip do not acquire one. Native On/Off/Blink states remain
  separate paragraphs in every locale. German line-wrap hyphens are rejoined
  with normalization evidence; genuine “und/oder” suspended compounds remain.
- The last four align to newer English: USB-C charging and separately sold
  charger; poor-connection overheating hazard; Li-ion LFP naming; 3000 cycles
  to 80%+ capacity; the full battery/accumulator separate-collection paragraph.
  Dutch safety restores its missing verb, and its inverted “Off” meaning is
  corrected. Covered, invisible temperature-label remnants in the pt/nl/pl
  source spec pages are excluded, based on rendered source-page evidence.
- The first draft battery-disposal binding accidentally matched the lithium
  battery pictogram. The final binding selects `battery_separate_collection`
  explicitly and a regression asserts that its full paragraph appears once.
  Ukrainian copy matches four live TM records; pt/nl/pl reuse the same generic
  English paragraph's frozen translations from the JE-2000F source. No TM
  write occurred. Exact records, before/after text and authority hashes are in
  each `newer_english_alignment.json`.
- pt is distinct from pt-BR and reads the verified `eu-pt` TM field. Registering
  a Web locale does not provision core phase2 columns or an IDML language
  pack. The integrated upstream registry keeps live synchronization disabled
  and retains content-lint fallbacks for offline snapshot columns. Source-bound
  RST audits cover this target's actual localized copy; empty core-table
  observations do not count as copy validation. Display and IDML tests check
  their actual scopes.
- Eight manifests are also registered in the family index; after integrating
  the upstream solar manifest, all 50 manifests round-trip through six anchors
  and 44 folds. The language-literal baseline
  was refreshed because registration makes existing literals newly visible:
  all 13 newly reported entries were verified in 11 unchanged files. No new
  duplicated production language table was introduced.

### Final local evidence

All paths below are relative to `reports/je100c_eu_web_20261001/`.

- `languages/build-results.json`: all nine real `build.py md` builds and strict
  Sphinx builds passed; each has 11/11 finished bindings and zero missing.
- `languages/source-coverage-reviewed.json`: all eight native-source line
  audits have zero unexplained lines. Enumerated safety bullets, explicit
  approved copy replacements and the common 99.9/99,9 sample glyph are
  accounted for rather than misreported as missing body copy.
- Browser desktop 1440×1000 and mobile 390×844 checks cover all nine languages:
  no broken images or document overflow, six source callouts, four LCD tables
  with 10/3/3/2 rows, eight symbols, four purchase strips and five device-action
  rows. Final results are in `languages/browser-desktop-final.json` and
  `languages/browser-mobile-final.json`.
- `logs/language-portal.log`: strict Sphinx passed for the nine-language local
  navigation page. Browser inspection confirms nine native-language links.
- `logs/us-fixture-languages-final.log`: the US quality gate passed against
  committed fixtures; this does not assert live source-table completeness.
- Ruff, maintainability guardrails and documentation link checks passed.
  The final full suite ran 4967 tests in 922.926 seconds: passed, 19 skipped
  (`logs/full-suite-languages-final.log`). The separately strengthened registry,
  LaTeX-scope and family-manifest checks passed all 26 tests
  (`logs/registered-surfaces-final.log`). The earlier failing runs are
  superseded by these final results.

Local preview: http://127.0.0.1:18932/ . This is a local review candidate only.

The normal browser viewport was restored and both existing preview tabs were refreshed. The navigation screenshot is `languages/nine-language-portal-final.png`; final figure evidence includes `languages/pl-charging-mobile-final.png`, `languages/nl-overview-desktop-final.png` and the four `*-health-12x-final.png` files. The test-generated root index edit was reverted to its pre-task content; all source changes and review artifacts remain in the isolated worktree.


### Repository submission validation

The candidate was integrated onto engineering main
`a74513acc0edff148ed8863895f3b990472922f0` before submission. The upstream
offline-language sync boundary, LCD number-cell spans, registration styles
and other manual changes remain intact. The fresh full suite ran 5025 tests
in 749.121 seconds: OK, 19 skipped (`logs/prepush-full-suite-final.log`).
All nine real builds and strict Sphinx builds passed again, as did 40 focused
registry/table/family checks, Ruff, mypy, maintainability/complexity guardrails,
doc links, reference-layout pins and the asset check. Browser checks at
1280×720 confirm bold headers, centered function cells, six notices, LCD
10/3/3/2 row counts, no broken images and no document overflow in all nine
locales (`languages/prepush-browser.json`).

Source-copy follow-up: the newer Spanish original contains the French children
prohibition wording `Les enfants ne sont pas admis.` The authored Spanish
source preserves it, as recorded in its `native_source_intake.json`; its
translation requires a separate source-copy review.

This submission remains an engineering candidate; no live source-table write,
source-version approval or production publication is claimed.

The final submission also includes upstream guardrail update
`11edef3673ece87a7a33c2f89780f3587512e480`. It changes CI/guardrail tooling and
documentation, not the manual renderer. The three new helper signatures now
carry type annotations; their runtime behavior is unchanged. After this
update, 52 targeted tests passed in 48.522 seconds, covering the new
ratchets, authored tables, whole-document IR and all nine JE-100C locales
(`logs/prepush-final-compatibility-tests.log`). The CI-pinned mypy 2.3.1
ratchet reports zero new/grown errors; the ZIP strictness, maintenance and
documentation gates also pass. The 5025-test full-suite result above precedes
this final upstream guardrail update and annotation-only adjustment.
