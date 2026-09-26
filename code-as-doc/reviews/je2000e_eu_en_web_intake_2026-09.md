# JE-2000E EU/en Web intake and implementation record

Date: 2026-09-08

Implementation baseline: `d1b12bf8686941b5e79d9b507d7cc991da3427b9`

Target: `JE-2000E / EU / en` (`HTE152`, Jackery Explorer 2000 Plus)

Status: local Web implementation and verification complete; PR pending review.

## Authority and source inventory

| Source | Role | Verified state |
| --- | --- | --- |
| DingTalk requirement row `LANG-S4mhIE7S` | Request scope and current-file linkage | Model `JE-2000E`, project `HTE152`, current material `160102000398`, status `已定稿` |
| Current published PDF, DingTalk node `YndMj49yWjP03jNjCRnbG07jJ3pmz5aA` | Visible copy and artwork authority | `Jackery HomePower 2000 Plus User Manual (JE-2000E) EUUK V2.0-2026-08-03`; 120 pages; SHA-256 `734f89ad824d2436d2c79c7ac1231d2dc111dd83ef43e8ee6326674124c396d0` |
| Business-plane phase2 Base | Existing structured semantic source | Live read-only sync completed; `JE-2000E_EU` capability row and 47 specification/placeholder rows are present |

The PDF metadata title identifies material `16-0102-000398` and model source
`HTE1522000A-EU-JAK`. Its English body is physical PDF pages 6-24 (printed
pages 01-19). PDF text extraction is used only for inventory; all 19 English
pages were rendered for visual review.

## Confirmed pre-edit findings

- The current EU/en family and shared semantic components already cover Safety,
  Symbols, Inbox, Overview, LCD, Operations, UPS, Charging, Troubleshooting,
  Specifications, Warranty and App Setup. A new per-model config is not needed.
- The live target data builds through the normal `build.py check` entrypoint but
  currently fails on three missing page values: `UPS_TRANSFER_TIME`,
  `PV_INPUT_RANGE`, and `DC_INPUT_CONNECTOR`. The capability gate also requires
  the shared extra-battery page because `加电包扩容=TRUE`.
- The published PDF supplies the missing values: UPS switching within `10 ms`,
  solar open-circuit range `16 V-60 V`, and two `DC8020` input ports. These will
  be recorded only in the Git-tracked target snapshot; no live Base write is in
  scope.
- The published Specifications table states `Jackery Explorer 2000 Plus`,
  `JE-2000E`, `2048 Wh`, `6000 cycles to 70%+ capacity`, 2400 W rated output,
  and 4800 W surge. JE-2000F values and artwork are not acceptable substitutes.
- The LCD remains a source-device diagram plus the shared editable HTML/CSS
  icon table. Overview, operation, UPS and charging illustrations may use
  target-local crops, but semantic tables and prose remain editable.
- PR #1082 contains the target-aware shared-family illustration selector and
  the final shared Inbox/operation/LCD/App component behavior required here.
  This task will consume that branch as an explicit stacked dependency, not
  create another implementation of the same shared capability. PR #1081 is
  unrelated and is not consumed.

## Implementation plan

1. Merge the reviewed PR #1082 branch into this task branch as an explicit
   dependency, preserving its commit ancestry and leaving both PRs unmerged.
2. Freeze only the existing JE-2000E EU/en structured rows and referenced shared
   attachments into `manual_sources/JE-2000E/EU/en/2.0/phase2/`; add the three
   published-source page values locally and lock every file hash.
3. Add JE-2000E to the shared EU/en target list and target-keyed illustration
   mapping; include the shared extra-battery page under the existing capability
   gate.
4. Extract only target-local panels from the verified PDF with recorded page,
   bounding box and hash. Keep complete gray illustration frames where the
   artwork owns labels; do not rasterize LCD/specification/troubleshooting/
   warranty tables.
5. Add target acceptance tests for source isolation, source-manifest locks,
   semantic components, figure coverage, cold replay and tamper rejection.
6. Validate in the cheap-to-expensive order: target tests, Ruff, full unit
   suite, maintainability guardrails, documentation links, target check, Web
   build, strict Sphinx, desktop/mobile localhost inspection, then current-main
   ancestry and PR checks.

## Non-goals

- No live Bitable write, queue mutation, OSS upload, Hello-Docs edit, RTD
  publication, JP/IDML work, PR merge or public-release claim.
- No copied JE-2000F/JBP-2000B artwork, product names or target parameters.
- No hand edits under `docs/_build/` and no cleanup of unrelated generated or
  review artifacts.

## Implemented source calibration

- Froze only `JE-2000E_EU` plus required shared rows and referenced attachments
  under `manual_sources/JE-2000E/EU/en/2.0/phase2/`; the build has no live Base
  dependency.
- Corrected the target-local weight to the visible paper value `About 19.1 kg`
  and added the paper-only `10 ms`, `16 V-60 V`, `DC8020`, 75 A expansion-input,
  and 55 A expansion-output values. No online source row was modified.
- Registered the existing JE-2000E battery-pack section with the explicit
  capability page-plan slot and replaced its generic device placeholder with
  the target-local connection panel, without duplicating visible copy.
- Bound 16 Web replacements to 12× target-local source crops. The 12 public-IR
  figure slots report `finished-panel=11`, `editable-fallback=1`, `missing=0`;
  the one editable fallback is the intentional LCD device-art + semantic-table
  composition. Inbox remains the shared
  semantic three-card component because its canonical line art already matches
  the JE-2000E paper manual.
- Kept LCD as the target device-only crop plus the semantic HTML/CSS table and
  retained editable specification, troubleshooting, warranty, and regulatory
  sections.

## Naming and publication boundary

The DingTalk file title uses `HomePower 2000 Plus`, while the visible V2.0 EU
PDF cover, diagrams, and Specifications table use `Jackery Explorer 2000 Plus`.
The Web copy follows the visible formal PDF and records the title mismatch as a
source fact; it does not introduce the JE-2000F `Explorer 2000` product. This
work proves only a local Git-replayable Web build. It does not prove a live Base
write, asset archive upload, OSS upload, Hello-Docs publish, or public release.


## Released-PDF specification correction (2026-09-13)

Rechecked physical PDF page 21 / printed page 16 against the current frozen
English table. The PDF SHA-256 remains
`734f89ad824d2436d2c79c7ac1231d2dc111dd83ef43e8ee6326674124c396d0`.

- Output bypass is `230 V~ 50 Hz, 10 A max.`; input charge and bypass retain
  their distinct `220 V-240 V~ 50 Hz, 10 A max.` values.
- DC8020 input displays the PDF's PV line before Car, with both labels explicit.
- Output ports follow the paper sequence: AC, bypass, USB-A, USB-C 30W,
  USB-C 140W, DC12V and expansion. The USB-C ports have separate one-port
  labels, using the existing shared specification renderer.
- AC, USB-A and DC12V labels follow the visible PDF. All port ratings other
  than the corrected output-bypass voltage are preserved.

Changes are confined to this English frozen snapshot, its file lock and target
regressions. Translated text columns and stable row identities are preserved;
only this singleton English snapshot's row order changes. No online Base,
shared renderer, schema or workflow is changed. This correction requires a
separate Git-only business publication before it can be called live on RTD.


Handoff verification: 13 target/shared specification tests passed; the full
suite passed 4112 tests (22 skipped). Ruff, maintainability, documentation links
(197 documents / 1798 links), target `build.py check`, real Web Markdown and
strict Sphinx passed. All 55 local image references resolve. A cell comparison
against `af3d6d12` limits the change to 13 English-content/order cells; translated
text, other pages and row identities are unchanged. The initial RTD assembly
command used an output outside its build root and was rejected; rerunning with
`rtd-source` inside that root passed without code changes.

The operator explicitly deferred repeated PDF/content and desktop/mobile visual
acceptance to later manual review on 2026-09-13. It is pending, not claimed as
passed and not a blocker for the authorized batch Web publication. Required
automated build, artifact-integrity and URL checks remain release gates.

## 2026-09-24 App panels for fr/es/de/it/uk

The fr/es/de/it/uk routes, wired later from this frozen source, had no
illustration manifest, so App setup showed the shared JP-market
`add_device.png` and `connect_result.png`. The print's other five language
blocks place the same App bitmaps as the English block, so two shared panels
cut at 12x now replace them through five two-entry manifests: the add-device
screens with their 2.1/2.2 captions from p23 (bbox 41 208 322.75 349, stopping
above the grey control-panel box whose button labels are translated per
block and stay live text) and the connection-result screens with their
2.3/2.4/2.5 captions from p24 (bbox 41 79 322.75 249.5, excluding the
localized "screenshots are for reference only" sentence). As App UI, their
recipe `manual_je2000e_eu_web_app.json` stays quarantined, and the source
manifest binds it as `app_asset_recipe`. English is unchanged. The operator
confirmed both crops on 2026-09-24.

## 2026-09-24 App add-device figure with the control-panel box

The English add-device figure bound the approved `control_panel` crop (p23,
bbox 28 351 342 431), which holds the grey control-panel box but not the
2.1/2.2 App screens above it, while fr–uk showed the shared screens with the
four button labels as plain text. Each language block prints the screens and
its own control-panel box as one region, so EN/FR/ES/DE/IT now bind a 12x crop
of that region from their own block (quarantined App recipe entries
`web/je2000e/eu/<lang>/app_add_device_panel`):

| Route | PDF page | bbox (pt) | Printed labels vs page labels |
| --- | --- | --- | --- |
| en | 23 | 27.5 208 341.5 434.5 | "Main Power Button" vs "Main POWER Button" |
| fr | 42 | 26.7 204.3 340.6 423.2 | same wording |
| es | 61 | 25.1 217.5 339 438 | same wording |
| de | 80 | 25.1 217.5 339 438 | "POWER-Taste" vs "Haupt-POWER-Taste" |
| it | 99 | 25.1 217.5 339 438 | "Pulsante CC/USB" vs "Pulsante DC / USB" |

Each crop ends in the white gap above the next paragraph (step 2.3) and has
pure-white edges. The page's four label lines become covered annotations, so
the figure's alt text keeps the page wording. The uk block (p118) prints
"Кнопка AC1" for both AC buttons; that crop is not reused, and uk keeps the
shared screens with live labels. The operator chose this scope on 2026-09-24.

## 2026-09-26 fr–uk figures from each print block

Problem:

- The fr/es/de/it/uk illustration manifests bound only the two App panels. The
  other figure slots fell back to the shared art from the JE-1000F/US master,
  which shows another product and US outlets. The battery-pack section showed
  the in-box unit image as a placeholder.
- English bound its block crops but not its in-box crops. "Implemented source
  calibration" above says the shared in-box line art matches the paper manual.
  It does not: the print draws the Explorer 2000 Plus, with UK sockets in the
  English block and EU sockets in the fr–uk blocks.

Change:

- `data/asset_recipes/manual_je2000e_eu_web.json` gains 85 approved crops, 17
  per language (the English figures plus the three in-box items), from the fr
  (PDF pages 25–43), es (44–62), de (63–81), it (82–100) and uk (101–119)
  blocks:
  - The positions come from raster matching with the text removed, then each
    block's own panel frame. The blocks drift from English by up to 9.5 pt.
  - Crop edges exclude the neighbouring headings and text.
  - The 19 English outputs are unchanged.
- The English manifest binds its approved in-box crops (`inbox_main`,
  `inbox_cable`, `inbox_manual`, p7) to the three in-box cards.
- The five fr–uk manifests bind the 17 crops to the English slots. Their
  `recipe` is now the web recipe; the App entries keep their own.
- The fr–uk `charging.rst` templates' battery-pack section (JE-2000E only) now
  points at its block's `extra_battery` crop, as English has since #1085. It
  used the in-box unit image, whose shared name made the in-box binding
  ambiguous (`repeated Web illustration source`).
- Copy printed in a crop moves from the page into the figure's alt text, with
  English's selectors: the overview callout tables, the operation panel lines,
  the energy-saving notes, the LED lines, the UPS paragraphs, the AC wall
  sentence and the car line.
  - The French power section keeps its on/off and standby lines in one block,
    so it has one binding where English has two.
  - Like English, the fr–uk entries need no `consume_before_presentation`.
- `source_manifest.json` re-locks the web recipe and the English manifest.

Verification:

- **Recipe:** `tools/asset_intake.py` reproduces all 104 outputs against their
  expected hashes; the 19 English crops are byte-identical.
- **Visual review:** every crop was checked next to the English crop and its
  page. The fr–uk crops show EU sockets and their own language's labels; no
  English line remains apart from product markings (`LIGHT`).
- **Covered copy:** each covered text was compared with the print text inside
  its crop. The remaining misses are wording variants of the same instruction
  (uk "Увімкнення" vs the page's "Увімкнути") and Italian accents that the PDF
  text layer drops.
- **Trial Web builds** (frozen data root, web profile) against the live pages
  (2.2; uk 2.1):
  - each fr–uk route replaces its 17 figures, drops the second solar figure as
    English does, and removes only the covered copy (57–59 text lines);
  - English replaces only its three in-box images;
  - no shared JE-1000F figure remains on any route.
- **Regression tests:** `Je2000eEuBlockIllustrationTests` and the German build
  test fail on the previous recipe, manifests and templates (five failures, one
  error).

Still open (not changed here):

- On fr–uk the LCD-mode image stays in the page's plain table; the English
  LCD-mode component is not built there. Only the image changed.
- `page_shared/pt-BR/charging.rst` keeps the in-box placeholder in its JE-2000E
  block; there is no JE-2000E pt-BR route.
