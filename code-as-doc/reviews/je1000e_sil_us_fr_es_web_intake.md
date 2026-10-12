# JE-1000E-SIL / US — native French and Spanish Web intake

Status: active

Git-only candidate. The operator resumed and authorized engineering submission and three-language publication with “推上去 发布” on 2026-10-03. No online table, queue, or HTML_link writes are part of this release. Historical pause and validation entries below retain their original dates.

## Source and editing surface

- Authoritative attachment: `Jackery FridgeGuard User Manual V2.0-2026-07-29.pdf`.
- SHA-256: `537939d0d62b0cf0d3f91b432f8114e566aeb69b1267d2468410ee4d3f8b0fb1` (64 physical pages).
- French: physical pages 24–43 / printed 21–40; Spanish: physical pages 44–63 / printed 41–60. Both use their native preface on physical page 2.
- Native wording is transcribed, not translated from the English AI. Extraction joins visual line wrapping and normalizes typographic ligatures; it does not silently repair source copy.
- Edit `docs/templates/page_fridgeguard/fr/` and `docs/templates/page_fridgeguard/es/`; specification facts and footnotes live in each locale's frozen `data/manual_sources/JE-1000E-SIL/US/<lang>/git-20261002-537939d0/phase2/` snapshot.
- Existing family configs `config.us-fr.yaml` / `config.us-es.yaml` point to locale manifests. The preface is named `preface.rst` to avoid the legacy trilingual `00_preface.rst` projection rule.
- Reuses Manual IR and shared FCC, inbox, LCD, operation, reference-figure, fault-table, warranty and App components. No new renderer or product-specific CSS.
- Diagram instructions are native HTML text. Desktop labels retain their source positions; the shared mobile label flow keeps long copy readable without duplicating text. The original gray frames, dashed boxes and leaders remain. DC8020 stays in the solar/car base art as authorized.

## Asset reuse decision

| Content | Candidate / decision | Reason and provenance | Background policy |
| --- | --- | --- | --- |
| Power, UPS, stands, wood/concrete steps, solar/car | Reuse existing `je1000e_sil_us_en/*_art.png` unchanged | Same model/region illustration; external labels supplied from each native locale | Preserve original complete frames and leaders; use existing power CSS bubbles |
| LCD, battery connection, AC cable, box contents, QR | Reuse existing target assets and shared semantic icons | Language-neutral illustration / product engraving / QR | Preserve native artwork |
| Product overview | Crop native locale overview | Existing English overview contains burned English callouts; native FR/ES artwork required | Full device and all source leaders; no duplicate port/rating table |
| App phone screenshots | Crop screenshots from the native locale pages | PDF-specific panel extents and numbered captions; preserve the original UI (which is English in the supplied FR/ES pages) | Preserve entire phone image, status/footer UI and numbered captions |
| Maintenance and App button label | Native panel + text-only redaction | Existing counterparts contain burned English labels; labels must remain editable | Preserve native frame, background and leader lines |
| Wall installation | Reuse the English installation artwork and figure sequence | Remove the extra standalone wood-mount panel; its export is retained only as unused extraction evidence | Keep native editable labels and original artwork frames |

New native exports use `data/asset_recipes/manual_je1000e_sil_us_fr_es_web.json`, `crop` / `redact_text` with graphics and images preserved, per-asset source page/crop/hash sidecars. They remain quarantined for local preview; no asset registry promotion is claimed.

## Source discrepancies retained for review

| Source | Native content retained |
| --- | --- |
| FR p29 / ES p49 | Default standby is **2 hours**, unlike the English AI's **12 hours**. Native PDF has no additional English AI low-power-load sentence. |
| FR p25 | Indoor-use warning is `AVERTISSEMENT`; ES p45 is `PELIGRO`. Do not substitute English severity blindly. |
| FR p38 | Solar heading is Spanish `CARGA MEDIANTE PANELES SOLARES`. |
| ES p58 | Solar heading is French `CHARGE VIA PANNEAUX SOLAIRES`. |
| ES p51 | Stand step 1 remains English in the source PDF. |
| FR p39 | Fault table header is Spanish `Código de error`. Both locales specify `0,2 pouces/pulgadas (5 cm)`, an inconsistent conversion. |
| FR p36 | Battery-pack connection text refers to the FridgeGuard manual; Spanish refers to the Battery Pack manual. |
| FR p40 | Bypass specification reads `100V~120V~60Hz`; retain the native value. |
| ES p48 | DC input indicator description repeats the battery-pack description. |
| ES p61 | Interpretation-rights paragraph repeats the original-consumer limitation. |
| FR p43 | Network-reset note includes trailing English `re-bind the device.` |
| ES p62 | Add-device heading is French `2. Pour ajouter un appareil`. |

## Validation

Strict locale Web builds and Sphinx `-W` are required. Check rendered native copy against PDF lines, with only product-overview callouts intentionally image-led. Check 15 LCD rows, six LCD on/off actions, eight fault rows, four spec tables / 15 facts, one FCC component and all live figure captions. Desktop/mobile browser evidence and final results are recorded below.

The earlier English intake's full-suite / maintainability blockers are not cleared by this locale work; this record is not a release approval.

### Local validation result — 2026-10-02

- Both native locale `build.py md` runs and Sphinx `-W -b html` passed.
- Each locale: 18 top-level sections, 15 LCD rows, six LCD mode rows, eight fault rows, 20 shared reference figures and 40 native reference-label nodes; one shared FCC component with its logo.
- Every packaged image reference resolves. Original PDF source lines longer than 17 normalized characters are present in the rendered text except the two intentionally image-led input/output callouts in each overview. Full native overview images contain those callouts; no duplicate visible text is added.
- 21 relevant component/config tests passed. Doc-link check and `git diff --check` passed.
- Desktop 1280/1440 and mobile 390 browser checks performed. No page-level horizontal overflow; the LCD mode table retains the existing internally scrollable mobile panel. Native labels use the existing readable mobile flow.
- Complete overview and App phone edges inspected; new textless panel corners/edges inspected at 12x. Source-page selection was verified against the native PDF, not inferred from successful asset hashing.
- Screenshots: `/tmp/fridgeguard-intake/fr-desktop-final.png`, `fr-mobile-final.png`, `es-installation-desktop.png`, `es-mobile-final.png`, `es-app-final.png`; copy audit and counts in `locale-validation.json` in the same evidence directory.
- Remaining source anomalies are listed above. Engineering-wide historical blockers from the English intake remain out of this local acceptance scope. No publication has been resumed.

Frame repair (2026-10-02): audited original AI vector bounds for wall-installation panels. Restored clipped top borders in wood 4–5 / concrete 5–6, right border in wood 1, and stroke clearance in wood 6 / concrete 2. Re-extracted shared English textless artwork with 0.6 pt frame clearance; remapped native live-label coordinates in EN/FR/ES. No CSS-drawn substitute or registry promotion.

Car-charging note: removed raster note backdrop at the user-marked location; EN/FR/ES reuse the same textless artwork and existing CSS live-pill component with horizontal/vertical centered native copy. DC8020 and outer diagram frame retained.

Solar-charging note: removed raster note backdrop at the user-marked location; EN/FR/ES reuse the same textless artwork and existing CSS live-pill component with horizontal/vertical centered native copy. DC8020 and outer diagram frame retained.

Symbol layout correction: admit the language-directory filename `symbols.rst` through the shared meaning_symbols source pattern, alongside `symbols_*`. FR/ES now use the same signal badges and independent icon panels as EN; no locale-specific renderer or translated-copy rewrite.

Localized signal rows explicitly declare the existing hb-warning-lockup semantic boundary, avoiding the English-only legacy header rewrite. Strict FR/ES builds and 63 signal/presentation tests passed. Browser evidence: /tmp/fridgeguard-intake/es-symbols-shared.png.

### Safety presentation and edge alignment — 2026-10-03

- Native FR physical page 24 / printed page 21 was rendered and compared with the operator's English print reference. The risk banner had degraded to an ordinary table with an empty header; the white warning SVG had a zero-sized box in the localized source.
- EN/FR/ES now declare the existing signal composition's `hb-safety-instruction` / `hb-safety-lead` variants. Reuse the existing dark and white SVG triangles with explicit 30px / 48px widths. Preserve the dark full icon cell, bold instruction, compact safety copy and dark operating subbar. No new artwork or renderer.
- The outer two-column table has zero border spacing; inner cell padding supplies the gutter. Browser measurements put the title, risk banner and warning lead at the same left edge in all three locales. At 390px, the FR outer table and all four stacked cells are 358px wide with the same 16px left edge, visible icons and no page overflow. The operating subbar follows the first group with a 10.4px gap on desktop.
- Source-visible copy and rendered-visible copy match the pre-fix source in EN/FR/ES. Hidden callout label-sizing spans are excluded from visible-copy comparison. English's non-HTML branch is byte-identical. Each page has one risk banner, one warning lead, two column groups and no risk-banner table header; packaged icons resolve.
- Three `build.py md` runs and strict Sphinx `-W` passed. `python3 -m unittest tests.test_web_presentation tests.test_web_signal_ir tests.test_word_bundle` passed 110 tests; doc-link integrity and `git diff --check` passed. Frozen repo-input hashes include the shared CSS and reused SVGs.
- Evidence: `/tmp/fridgeguard-intake/safety-validation.json`, `fr-safety-aligned.png`, `fr-safety-mobile.png`, `fr-safety-operation.png`, `en-safety-aligned.png`, and `es-safety-aligned.png`. Local preview only; publication remains paused and prior engineering-wide blockers are unchanged.

### App download and complete phone sizing — 2026-10-03

- Operator's Web screenshot and printed p19 reference show the missing store badges, wrong QR-only layout, and oversized 2.1–2.2 phones. Bind the existing `HB-SPECIAL-APP/download` through an authored `hb-source-app-download` declaration and explicit `store` / `qr` artwork roles; no new renderer or model allowlist. Native copy remains two live columns. Missing artwork or missing column copy rejects intake.
- Reuse `docs/renderers/contracts/assets/app/app_store_badges.png` and the exact approved English `app_qr.png` in EN/FR/ES. Preserve each existing complete phone crop; no artwork was re-extracted. Apply the shared phone image rules plus `hb-app-phone-pair` / `hb-app-phone-trio` (22rem / 36.75rem maxima). Ordinary finished-art replacement normalizes print-width hints, so the shared classes carry this deliberate App display size. Keep the 2.1–2.5 captions, phone borders, status/footer UI and neighboring control panels.
- Numbered App headings keep source case, have no generic dot markers, and use compact shared spacing. Tighten the existing full-download artwork frame and gutter; keep native store/QR wording below its matching art. Mobile copy is 14px.
- Three `build.py md` runs and strict Sphinx `-W -b html` passed. `python3 -m unittest tests.test_web_app_download_declared tests.test_web_app_download_ir tests.test_web_app_qr_declared tests.test_web_presentation` passed 68 tests. Ruff, documentation links and `git diff --check` passed. Before/after authored App copy matches in all locales; each rendered download paragraph occurs once. Frozen manifests include the reused badge, shared App/base CSS and source/claim adapters; all repo-input hashes read back without mismatch.
- Browser evidence at 1280px and 390px confirms two download columns, identical badge/QR hashes, complete loaded images, no page overflow, 352px / 588px desktop phone panels and 352px / 358px phone panels on the 390px viewport. Full phone edges and captions were visually checked. Evidence: `/tmp/fridgeguard-intake/app-layout-{en,fr,es}-{desktop,mobile}.png`, `app-phones-pair-mobile.png`, `app-phones-trio-mobile.png`, `app-layout-validation.json`, and `app-source-copy-validation.json`.
- Current whole-worktree validation is not green: full unittest ran 5055 tests with 10 failures / 3 errors / 35 skips (CI-target and family/structure baselines, charger FCC admission, frozen replay and compatibility hashes). Maintainability fails for the shared symbols/FCC stylesheet at 249 lines versus its 160-line limit; the App stylesheet remains within 128 lines. Default JE-1000F check cannot resolve the missing local Spec_Master snapshot. The frozen-data FridgeGuard check remains blocked by two `DUPLICATE_RENDER_TEXT_MISMATCH` findings in the source/staged English safety page, already noted above. Logs: `app-full-tests.log`, `app-guardrails.log`, `app-build-check.log`, `app-target-check.log` in the evidence directory. These results do not authorize a PR or publication. Git-only local preview; publication remains paused.


## Publication preparation — 2026-10-03

The operator’s “推上去 发布” supersedes the earlier publication pause. The
candidate was preserved in a scoped backup/stash and synchronized to engineering
main `120876a0be964c823bc50fd5e488c78cb221934a`; module paths follow main’s
`tools/web`, `tools/check` and current IR layout. No old dispatcher was restored.

Publication blockers were resolved without changing native manual wording:

- Registered three FridgeGuard family manifests/diffs and their UPS capability;
  family counts become 53 (47 folded, six anchors), UPS count 43, and the new
  `page_fridgeguard` tree is the only added template-structure fixture.
- The shared `symbols.rst` alias intentionally changes the presentation contract
  hash to `dc8519d531c28de4f366c32dbee411147123648ce2c3f919ed51414654b7be3c`.
  New NOTE/TIP source badges omit hazard icons; frozen historical `show_icon`
  values retain their replay behavior. Historical JE-1000F replay still passes.
- Exact FCC headings/declarations require the shared component. Part 15 opening
  fallback is limited to headingless orphan fragments; compact mixed-page FCC
  statements remain native and do not get forced into the full two-column card.
- Duplicate-copy checking distinguishes RST list-table cells from real bullets;
  the English grounding warning remains unbulleted in both source branches.
- Safety variant CSS was moved verbatim into `web_safety_components.css`, directly
  before symbols/FCC styles. No CSS limit was raised and the cascade is preserved.
- Complexity evidence changes only the two reduced Web functions: embedded
  dispatch 22 to 14 (below threshold) and presentation transform 33 to 31.
- The new FridgeGuard test-fixture PRODUCT_NAME row is model-specific rather than
  a second global default. Six old-model IDML errors from the first full run
  were reproduced and the affected test modules now pass.

All three actual `build.py check`, `md`, and `html` actions passed against their
frozen locale snapshots with matching canonical projection fingerprints. Strict
MyST Sphinx passed for all three. Visible-copy comparisons against the confirmed
preview have zero word differences. The fresh 1280px/390px browser checks retain
one FCC component per language, 352px phone pairs and 588px desktop / 358px phone
trios, with no page overflow. Lazy App images are checked after visiting App.
Evidence is under `/tmp/fridgeguard-intake/publication-20261003/`.

This entry records pre-publication evidence. Engineering PR/merge, release PR,
RTD commit and live acceptance will be reported only after they are observed.

Final source inventory uses canonical Git blobs. Derived CSV snapshots retain
their committed LF policy; only CRLF/LF normalization changed, with source AI/PDF
bytes and all native values preserved. Candidate RST whitespace was normalized;
a seven-equals Storage underline was lengthened to avoid Git’s conflict-marker
false positive. Durable release authorization is MA-248 (MA-247 was reserved
by another open PR before push).

Final engineering gates passed: 5148 unittest tests (35 skipped, no failures),
Ruff, maintainability (zero new/grown/stale entries), documentation links and
staged whitespace checks. Three target checks/builds and strict Sphinx passed.
The generated root index is preserved locally and excluded from the commit.

CI type-gate follow-up: all seven new declaration helpers now carry explicit
input/output types (FCC claims use a read-only structural protocol). The pinned
mypy 2.3.1 gate reports zero new/grown/improved/stale errors; tools/utils passes.
Focused declaration tests pass. No type baseline, dependency file or layout
behavior changed. Source inventories and release receipts are refreshed at the
new source commit before publication.
