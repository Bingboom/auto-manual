# JA-AD500A-SIL / US / en Web intake

Status: active

English candidate preparation; no publication authorization.

## Discovery and implementation plan

The operator supplied `16-0102-000239 说明书 HTO889A-US-JAK RoHS REACH.ai`
and requested Git-only intake, English first. Cover and specifications both name
`JA-AD500A-SIL`, Jackery DC Input Module. HTO889A is the source project identifier.
SHA-256: `a6d1659e25a48272f50af44ca5b2f0a5741d7b1ea04fde7c426094faa0ede3da`.
The PDF-compatible AI contains one 3269 × 2265.719970703125 pt artboard,
six English body panels (printed 01–06), cover, back, blank and contents panels.
Most text is vector outlines; the LED table retains selectable PDF text.
Printed version is unknown. Logical panel coordinates and visual transcription
will be frozen beside the unmodified original.

The retained, clean worktree is `manual-intake-assist/auto-manual2`, starting
from fetched `origin/main` at `ed4d4ec5071d000d590d5b53322aea6c12186f7c`.
The branch wrapper failed because main is checked out in the primary worktree;
`git switch -c feat/hto889a-us-en-web-intake origin/main` is the worktree-safe
fallback. The primary checkout's unrelated `tmp/` remains untouched.

1. Freeze source, panel map and English copy in
   `manual_sources/JA-AD500A-SIL/US/en/git-20261005-a6d1659e/`.
2. Package the necessary illustrations through the existing asset pipeline,
   keeping quarantine status and no registry promotion. Author prepared RST
   with shared inbox, ReferenceFigure, callout, specification and warranty
   components. Use the existing whole-document `manual-ir/v2` projection,
   shared Web renderer and MyST export; no new renderer or per-model config.
   Add one data row to the existing target overlay registry for the six native
   warranty sections / single one-year period, using the existing charger profile.
3. Verify source completeness, component identities, native values, strict
   Sphinx, cold IR replay and rejection of modified assets. Inspect the actual
   browser at desktop and 390px, including diagram labels and all images.
4. Commit the source/preview evidence and open an engineering intake PR.
   Merge, Hello-Docs publication, RTD and other languages are outside this grant.

Safety nets: original hash/readback; immutable new snapshot directory; input
and output SHA-256 inventories; source-panel reference per chapter; source
copy compared with rendered text; existing component tests and documentation
links. No phase2 target/schema change, live table/queue/asset/build/link write,
workflow/dependency edit, or cleanup of prior evidence.

## Artwork inventory before extraction

Searched target/same-region manifests and assets in `manual_sources`,
`docs/renderers/web/assets`, `docs/renderers/latex/assets`,
`docs/templates/word_template/common_assets`, `data/asset*` and
`docs/manifests`. No JA-AD500A-SIL/HTO889A binding was found in this Git tree.
Opened the six closest FridgeGuard candidates in a contact sheet before extraction.
This is a local inventory, not a claim about live Base records.

| Slot | Candidates checked | Identity/content decision | Decision and concrete reason | Source/boundary |
| --- | --- | --- | --- | --- |
| Module inbox | `je1000e_sil_us_en/inbox_unit.png`, charger inbox manifests | Existing main-unit art depicts a station, not this DC module | Extract module-only drawing | p01; no number, label or card frame |
| Manual inbox | Existing power-station/charger manual cards | Cover/product identity differs | Extract original manual drawing | p01; preserve miniature product/cover content |
| Module overview | `je1000e_sil_us_en/overview.png`, JA-AD01A/JA-AD600A manifests | Existing diagrams show a station or a DC-DC charger | Extract complete English labelled overview | p02; retain full leaders, device and labels; no chapter title/table |
| Solar connection | `je1000e_sil_us_en/solar.png`, `solar_art.png`, shared solar bindings | Closest panel shows SolarSaga 500 X; source is SolarSaga 100 Air × 4 with two adapters/inputs | Extract exact native connection | p03; preserve complete frame, four panels, leads, enlargement and SolarSaga identity; DC8020 stays in the original bottom image per operator correction |
| Car connection | `je1000e_sil_us_en/car.png`, `car_art.png`, shared car bindings | Same station/module family, but different diagram geometry/leader map and note | Extract native layout, remove isolated annotation text/note backdrop | p04; complete frame/enlargement retained; Vehicle, DC8020 and note use ReferenceFigure live labels |
| Contact QR | Existing contact QR variants | Exact source payload has not been established as identical | Extract original QR | back; keep full quiet zone, no invented destination |

No standalone LCD or safety symbol is present. The LED status is a native
three-column table, not a private collection of icon images. Asset hashes and
crop/transform coordinates live in the source package recipe and manifest.

## Source concerns retained

- Battery-cell exclusion appears in the DC module warranty; retain it verbatim
  for operator review rather than infer an editorial correction.
- Keep the distinct module input range and downstream FridgeGuard/battery-pack
  open-circuit voltage guidance exactly as printed.
- Normalize source wrapping and replace the drawn DC sign with Unicode `⎓`;
  preserve every number/unit, four-panel count, 12V/24V restriction and 12-month
  warranty. Do not infer paper version from filename or snapshot date.

## Candidate verification

The operator requested that solar **DC8020 stay in the bottom image**. The
final crop therefore retains the complete original label/leader; the existing
ReferenceFigure binding declares embedded captions and has no duplicate live
label. Car labels remain native overlays and fit the actual 390px view.

Frozen candidate and evidence are in
[`manual_sources/JA-AD500A-SIL/US/en/git-20261005-a6d1659e/README.md`](../../manual_sources/JA-AD500A-SIL/US/en/git-20261005-a6d1659e/README.md).
The original source hash was unchanged. Strict Sphinx, source-free cold IR
replay/body-text parity, six-image hash/load checks and changed-asset rejection
passed. The component inventory matches all seven required component kinds;
the DC Input label retains rowspan=2. All chapters/cautions/native warranty
copy survive the Web projection. OCR supported the visual transcription and
was not used as authority for model/technical values.

38 focused component tests and 20 overlay contract tests passed. Ruff,
maintainability guardrails and documentation links/lifecycle passed. The
JE-1000F/US/en regression passed with `--data-root tests/fixtures/phase2`;
its default invocation lacked the local Spec_Master snapshot and is retained
as an environment-limitation log, not reported as a passing target check.
No new-model phase2 target check is claimed.

Actual desktop (1440×1000) and phone (390×844) inspection found six loaded
images, no document horizontal overflow and valid chapter anchors. The shared
LED table has an internal horizontal scroll surface on phone. Solar, car,
specification and one-year warranty screenshots are retained. The preview is
`http://127.0.0.1:18979/manual_jaad500asil_us_en.html`.

This completes preparation of the English intake candidate. Operator English
baseline confirmation, merge/publication and locale expansion remain outside
this result; all package publication flags remain false. No live business-plane
writes were made, and root/other-window artifacts were preserved.

## Operator correction: back-cover copy without an added chapter

The operator clarified: “封底的内容可以放上去 但是 封底 没有 CONTACT US这个章节”.
The previous standalone contact heading/navigation entry was an intake
structure error. It has been removed. Exact back-cover company/address/phone/
email/website copy and the unchanged QR are retained in an untitled page-end
block; QR width is 96px at desktop and mobile. `evidence/source-contact-proof.png`
shows the original AI back-cover area (physical page 1, pt [308,480,563,579]).

Candidate 6 uses the existing frozen-IR replay for final MyST export, retaining
the native footer container rather than flattening its width constraint. Strict
Sphinx and source-free exact-MyST replay pass. Comparison with candidate 3 shows
identical body copy except for the deleted added heading, and identical six
artwork assets. Actual desktop/mobile inspection confirms zero contact headings,
the original five-chapter navigation, all contact copy, 96px QR and no document
overflow. Corrected screenshots and `evidence/footer-correction.json` supersede
the earlier footer display; historical evidence remains retained.

## Operator correction: LED status table presentation

The operator compared the native rounded, bordered LED table with the unstyled
Web table. The table had no explicit shared-grid class in the frozen IR replay.
The source now binds the existing `manual-table` and `table-wrapper docutils`
presentation, with source-native compact spacing/dark borders and an explicit
header/body divider. `LED Light` remains a bold table label rather than an
added bullet subsection. The three native columns retain 25/20/55 proportions,
left alignment, grey header, all four rows and every original word.

Candidate 9's strict Sphinx and source-free exact-MyST replay passed; body-word
comparison against candidate 6 is equal. Actual desktop and 390px inspection
confirms the complete grid/header alignment. On phone the table fits within
its 358px wrapper (355px table), wraps the long status copy and does not clip
behind the generic 576px table minimum. No shared renderer or CSS changed;
the source declares the existing table presentation and its dimensions.

## Operator correction: remove the added introduction

The operator marked both `Model: JA-AD500A-SIL` and
`US · English · User Manual` for deletion. The Web body now starts directly
at **WHAT’S IN THE BOX**. The title-only cover source remains committed for
provenance and is omitted from the Web page order, avoiding an empty normalized
preface. Target metadata and original specification identity remain intact.

Candidate 10b passes strict Sphinx and exact source-free IR replay. Its MyST
from the first chapter onward is byte-identical to candidate 9, as are all six
artwork assets. Actual 1440px desktop and 390px phone views confirm the first
chapter at the top, no added intro and no document horizontal overflow.
Corrected screenshots, strict log and `evidence/intro-correction.json` are
retained; earlier candidates and evidence remain preserved.

## Operator correction: reduce the complete product overview

The operator requested a smaller whole overview diagram. Its previous RST
75% width was overridden by the shared standalone-image 100% rule, resulting
in an 842.8125px-wide image at 1440px. The source now declares a centered,
proportional `min(100%,40rem)` width that takes precedence: actual desktop
width is 640px and phone width is 358px. The original full diagram, labels,
leaders and bytes remain intact; no shared CSS/renderer changed.

Candidate 11 passes strict Sphinx and exact source-free replay. Body text and
all six images are unchanged from candidate 10b. Actual 1440px and 390px
screenshots show the complete diagram with no clipping or horizontal overflow.
The report and screenshots are retained in the snapshot evidence directory.

## Operator correction: compact car-cable capsule

The operator requested a single-line car-cable note on desktop and less
vertical blank space. The existing source-bound live-copy rectangle is now
`[57,83.5,40,4]` percent, widening the capsule while reducing its minimum
height. No forced nowrap, new renderer or shared CSS was added. Native copy,
other labels and all artwork bytes remain unchanged.

Candidate 12 passes strict Sphinx, exact source-free replay and body-text
comparison against candidate 11. At 1440px the note uses one line and the
capsule height drops from 83.58px to 28.14px; at 390px it wraps naturally onto
two lines in a 19.34px capsule. Both views have no horizontal overflow or text
clipping. Corrected screenshots and measurements are retained in evidence.

## Operator request: language-neutral overview and editable labels

| Figure | Inventoried candidates | Identity/content | Decision | Reason | Source | Background/bounds |
| --- | --- | --- | --- | --- | --- | --- |
| Product overview | Current snapshot `assets/overview.png`; JA-AD500A-SIL/HTO889 entries in `data/asset_registry.csv`, `data/asset_recipes`, `manual_sources`, shared Web/LaTeX/common assets | Current crop matches supplied US source; no suitable textless model-matching asset found in those inventories | New corrective textless derivative; reuse exact crop and product artwork | Operator explicitly requests native labels and reusable base art; current English annotations are vector outlines, not text spans | Original AI SHA a6d1659e25a48272f50af44ca5b2f0a5741d7b1ea04fde7c426094faa0ede3da, page 1, pt [582,688,791,923] | Complete drawing on original white canvas; retain all leaders, edges, shading and product markings |

The original recipe and labeled overview stay byte-identical. A separate
source-local corrective recipe records removal of outlined annotation paths
on isolated white canvas; ordinary text redaction cannot remove these outlines.
No registry promotion or live business-plane write is authorized by this Git-only
request. The shared reference component will place six editable English lines;
future locales reuse this exact base art and supply native text/anchor decisions.

The final neutral PNG SHA is
`910a6ce8542f5be9df214a28699b57df6c5abb97c788f1efd72c3b6507f967c2`.
PNG and vector PDF outputs are pinned in the separate recipe and frozen input
manifest. Original source/recipe/labeled asset are unchanged. Production PNG
pixels outside the three white-canvas annotation regions and all four edges
are identical to the original crop. 12x label-edge inspection finds no residual
strokes or severed leaders; 12x cropped-PDF rendering has minor antialias phase
differences (max channel 14), recorded without an exact raster-parity claim.

Candidate 13b uses the existing ReferenceFigure with six live lines, retains
640px desktop and full phone width, and has three required reference figures.
Strict Sphinx, source-free exact-MyST replay, changed-new-base-art rejection and
21 reference/IR tests pass. The rest of body copy and the other five active
artwork assets are unchanged. Actual 1440px desktop and 390px phone show all
six native lines once, aligned above intact leaders, without clipping or
horizontal overflow. Final screenshots, before/after pair, extraction manifest,
artifact list and verification reports are in the frozen evidence directory.

## 2026-10-06 authorized English publication

The operator instructed “上线发布” for the current reviewed English candidate
(commit `45609dc9935e6d3b9e00686fcc962352239e315e`, candidate 13b). MA-259
covers engineering and the corresponding Git-only data release. This is the
actual release instruction, not a fabricated separate pixel-approval quote.

Discovery: current main is `ed4d4ec5071d000d590d5b53322aea6c12186f7c`,
PR #1446 initially has all 18 checks successful. HD#177 occupies persistent
publish and will remain untouched. The US prepared source uses its normal
component-slot, asset-hash and source-local inventory gates; the additional
EU/UK enrollment gate does not apply to US. No phase2 target is registered.

Plan: preserve the review snapshot, create a distinct approved package with a
source-bound approval record, freshly rerender prepared RST through the shared
pipeline and validate actual component slots/assets. Compare MyST/CSS/art bytes
with candidate 13b, strict-build and cold replay. At the committed source ref,
seal frozen language evidence, assemble only this route over current Hello-Docs
publish data, preflight strict Sphinx with myst_parser and tools.rtd.portal,
then gate both PRs on final-head all-green checks before merging and verify
the actual production build/resources. No business-plane table writes.

Approved package freshly assembles all seven component kinds through the
prepared-source/public-slot validation path. Strict Sphinx succeeds. MyST,
CSS and final manual HTML are byte-identical to reviewed candidate 13b;
source-free cold replay is exact and a changed neutral base-art is rejected.
The old candidate remains unchanged. `approval-parity.json` retains evidence.

## 2026-10-07 native French and Spanish candidate intake

The operator requested “就补 法语和西语” and supplied
`Jackery DC Input Module User Manual V2.0-2026-05-25.pdf` (SHA-256
`28c58312ffafae322161d17701869ede8f6b87e58799379a84fad2850c638530`).
Cover and specifications identify JA-AD500A-SIL, US. The PDF has 22 physical
pages; FR body = 10–15 (printed 07–12), ES = 16–21 (printed 13–18), shared
back cover = 22. V2.0/date are filename labels, not a verified printed version.
Native outlined copy was visually transcribed from every relevant page; native
LED tables were also checked against the retained selectable PDF text. These
are source-native imports, not translations of English. The preceding instruction
“你先不用删” remains in force for the battery-cell warranty exclusion.

Candidates live in
[`git-20261007-28c58312-native`](../../manual_sources/JA-AD500A-SIL/US/fr-es/git-20261007-28c58312-native/README.md).
The previously published English snapshot and its original AI are unchanged.
This request prepares the two candidates; it does not extend MA-259 to their
merge/publication. Publication eligibility remains false.

### Artwork inventory and reuse decisions

| Slot | Candidate checked | Decision and evidence |
| --- | --- | --- |
| Inbox module/manual | Six active approved English assets plus PDF pp10/16 | Reuse the same module and miniature English manual-cover artwork; native captions are live text. |
| Product overview | Approved textless English PNG plus PDF pp11/17 | Reuse intact drawing and leaders; replace the six external labels with native copy, same reference ID and geometry. |
| Solar connection | Approved solar PNG plus PDF pp12/18 | Reuse the complete four-panel SolarSaga 100 Air drawing, adapters and frame; DC8020 remains embedded as instructed. No localized visible text needs removal. |
| Car connection | Approved textless car PNG plus PDF pp13/19 | Reuse drawing/frame and reference anchors; Vehicle and sold-separately note use native live labels and wrap naturally. |
| Footer QR | Approved contact QR plus shared PDF p22 | Reuse exact contact block/QR without an added CONTACT US chapter. |

All six PNGs are byte-identical to the approved English assets. No extraction,
registry promotion, new per-model config, component, renderer or locale stylesheet
was introduced. The existing target overlay admits only warranty_fr/es and
charging_fr/es alongside the unchanged English patterns. The source-local adapter
uses the existing prepared RST → shared ComponentSpec/IR → MyST/replay path.

### Source concerns preserved for review

- FR PDF p14 labels the 11–16V/16–60V rows `Sortie CC` and the 42–58V
  row `Entrée CC`; the input/output labels are reversed against EN/ES.
- FR PDF p11 prints `Oiture` and retains English `Double to`; ES p20 also
  retains `Double to`. Native source wording is retained.
- ES PDF p21 `DERECHOS DE INTERPRETACIÓN` repeats the original-buyer and
  non-transferability sentence instead of an interpretation-rights clause.
- FR/ES PDF pp13/19 keep downstream 36.8–56V and 40–57.6V PV Voc advice.
  The disputed electrical ranges have not been editorially corrected.
- FR/ES PDF pp15/21 include the battery-cell charging exclusion; it is retained
  under the operator's latest instruction.

### Validation

Both candidates pass strict Sphinx. Every field of the native transcription is
present in the rendered body; all component types/order/reference IDs match the
English baseline. Each has 1 Inbox, 3 ReferenceFigure, 3 callouts, 2 specification
components, 1 warranty lead, 5 warranty sections and 1 year card. LED column widths
and input rowspan=2 are unchanged; native year units are AN/AÑO. Localized LED
header horizontal padding is reduced from 0.6rem to 0.4rem so French `Couleur`
remains whole at 390px; no shared stylesheet or body text changed.

Source-free cold replay reproduces exact MyST; changed-artwork replay is rejected.
84 existing presentation/contract/reference tests pass; Ruff passes. Actual browser
checks at 1440×1000 and 390×844 retain complete native labels, loaded artwork,
working chapter anchors and no page horizontal overflow. Source issues above
remain review issues, not hidden intake corrections. Preview/browser/hash/cold-replay
reports are retained with the candidates and under `/tmp/jaad500-fr-es-20261007/`.
