# JE-3600A EU nine-language Git-only Web release

Status: active

Operator scope (2026-10-04): complete en/fr/es/de/it/uk/pt/nl/pl from the local
161-page HTE139 source, fix the accessory kit frame, merge and publish. MA-256
records the engineering and publication authorization. No live Base writes.

## Discovery and plan

The published historical accessory PNG clips the top dashed edge. PR #1403
already contains a complete textless native accessory panel and selectable
English labels, plus the confirmed English component layout. Reuse that asset
byte-identically instead of the discarded CSS patch or a new language crop.
The current main routes and PR #1403 candidate are distinct versions; do not
mix historical technical values with the 0924 native source.

1. Import the preserved English candidate into this task branch without
   modifying the other worktree. Sync current main and resolve composition.
2. Inventory the nine source blocks and freeze native text/provenance. Reuse
   English semantic components and neutral artwork; source-owned wording,
   values, warnings and legal text remain per language.
3. Replay all nine packages through the shared renderer and strict Sphinx;
   validate component coverage, asset identity, source fidelity and layout.
4. Pass applicable local and remote gates, squash merge engineering, verify
   mirror sync, assemble only docs/publish changes, merge and inspect RTD.

Safety nets: preserve root tmp, the original English source package, prior
JBP packages, other worktree reports and the persistent publish branch.
No workflows, dependencies, public CLI flags or schemas change.

## Accessory artwork reuse

| Candidate | Identity/content | Decision |
| --- | --- | --- |
| Historical connections_accessories-en.png | JBP-3600A art, English labels; cropped top frame | Reject incomplete panel |
| JE-2000E battery_pack_kit.png | Complete frame, different battery model | Layout reference only |
| PR #1403 assets/battery-accessories.png | JE-3600A companion JBP-3600A; complete native frame, cart badge, external wording removed | Byte-identical multilingual reuse; selectable localized captions |

The complete labelled scratch crop and CSS border experiment are discarded.
The artwork is a complete white/gray panel, not a transparent standalone icon.

## Reviewed source and immutable versions

Original: `HTE139-EU-9国说明书-0924.ai`, 161 physical PDF pages,
SHA-256 `47a346dcfec4966ac98fbe1426e4f2b89cf54a964e4d1baf2ad9c7b02dc78043`.
Each language is frozen under
`manual_sources/JE-3600A/EU/<lang>/git-20261004-47a346dc/`.
This is a technical Git snapshot version; the paper-manual version is unknown.
The existing English `git-20261002-47a346dc` and May source remain immutable.

| Language | Native body pages | Preface page |
| --- | --- | --- |
| en | 8–24 | 2 |
| fr | 25–41 | 2 |
| es | 42–58 | 2 |
| de | 59–75 | 3 |
| it | 76–92 | 3 |
| uk | 93–109 | 3 |
| pt | 110–126 | 4 |
| nl | 127–143 | 4 |
| pl | 144–160 | 4 |

All packages include the common English EU declaration from physical page 161.
The original artwork is referenced by hash, not duplicated as a 161-page binary.
Native span ledgers, component-cell captures and explicit visual transcriptions
retain physical page and region provenance. Headings are captured separately
from adjacent body copy, avoiding an earlier German box-heading misbinding and
troubleshooting introductions leaking into the navigation.

All nine reuse the same ordered 16 chapters and ComponentSpec variants. The
reviewed source requirements live under the original SHA in
`prepared_component_admission.json:source_profiles`; the 75 historical target
entries are unchanged. The map independently requires symbol, LCD, operation,
UPS, expansion, fault, specification, warranty and App components. Deleting LCD
components still fails admission even with an unchanged candidate inventory.
Native source lacks an automatic-output-restore table; no other model's facts
are substituted.

## Native-source exceptions retained

| Source | Verified issue | Disposition |
| --- | --- | --- |
| EN p2 | Preface mentions US in this EU artwork | Retain original copy; target remains EU |
| EN p14 | Energy-saving copy says AC/DC where operation uses USB | Retain original copy |
| EN p20 | FA corrective action mentions both units | Retain original copy; no invented connection procedure |
| FR p36 | Car figure captions are English; solar paragraph names HomePower 3600 Plus | Retain source wording |
| ES p45/p51 | LCD/connections headings are French | Retain AFFICHAGE LCD / CONNEXIONS |
| ES p55 | Charging/discharging temperature labels are French | Retain source labels and values |
| IT p88 | F0–F6 corrective actions are German | Retain source actions; no independent translation |
| NL p127 | Safety heading is English | Retain IMPORTANT SAFETY INFORMATION |
| PT p123 | Model cell prints JE-3600 A | Retain typography; technical identity is JE-3600A |

Normalization is limited to ligatures, native line-break hyphen joining,
superscript placement, source headings and external copy separation. No
technical ratings, safety requirements, manufacturer identity or legal copy
are silently corrected.

## Artwork and browser evidence

Each locale has 55 packaged assets: 53 shared bytes and two source-labelled
product overview panels. The accessory panel SHA is
`4d320b9cd3273dc56cbc3a4a09512e2e4d412839d84c739c17d2cec8b51f5950`
in every package. Its four native dashed edges, shopping cart badge and product
markings are preserved; there is no synthetic CSS border. External labels are
selectable native HTML; long labels wrap within their allotted regions.
Source App screenshot frames are preserved and shared. Clock glyphs use CSS.

Local browser evidence is retained in
`reports/je3600a-nine-language/browser/`: nine 1280px desktop and nine 390px
mobile accessory screenshots plus `local-qc.json`. Both widths have zero page
horizontal overflow and no accessory label overflow. All App images loaded
after visiting the App section; unloaded offscreen lazy images were not
misclassified as broken. On mobile the artwork stays complete and native copy
flows below it. `frozen-audit.json` records per-language cold replay, asset
identity, trusted fresh admission and actual tampered-asset rejection. Cold
replay reproduces the reviewed Markdown byte-for-byte for all nine languages.

## Validation and delivery state

- Nine frozen packages: strict Sphinx HTML (`-W`) successful.
- Targeted policy/admission tests: 19 successful, including missing native LCD
  component rejection and historical projection compatibility.
- Ruff and maintainability guardrails: successful.
- Documentation link/lifecycle validation: successful.
- Historical JE-3600A/EU check: successful with the committed May phase2
  snapshot passed as `--data-root`. The normal local snapshot is intentionally
  absent; this historical gate does not validate the new native language bodies.
- Full suite initial run: 5173 tests, 35 skipped, one macOS `/var` versus
  `/private/var` temporary-path error in an existing publication-provenance
  test. The full rerun with `TMPDIR=/private/tmp` passes: 5174 tests, 35 skipped.
- Standard US regression: `build.py check` with `configs/config.us-en.yaml`,
  JE-1000F/US and `tests/fixtures/phase2`: successful.
- Full frozen catalog preflight: 105 language targets; other 96 target metadata
  unchanged and existing source diffs restricted to JE-3600A/EU. Strict Sphinx
  with `myst_parser,tools.rtd.portal` successful; 2028-file deployment receipt
  generated. Source receipts will be resealed at the corrected exact source commit before release.

Engineering merge, mirror sync, publication merge and RTD/live acceptance are
pending. No candidate or local page is claimed as published.

## Aggregated-page source corrections before merge

The aggregate browser review caught German and Italian App timeout paragraphs
starting below the first native line. They now bind the full native text block,
including the two-hour condition. A companion full-block audit checked all nine
App timeout tips and both circled specification footnotes. Spanish, Ukrainian
and Polish footnotes wrapped beyond the English rectangles; both numbered
notes now retain their full native text. Ukrainian note ② continues below
physical y=500, so capture follows its actual span geometry, not the nominal
English body boundary. A standalone printed footer number is excluded.

Only native copy bindings, derived IR/Markdown and corresponding input hashes
change; artwork and shared component structure remain byte-identical. The
corrected five languages pass strict Sphinx, and all nine repeat cold replay,
fresh admission and tamper rejection. The full 5174-test result remains
applicable to the unchanged production code; final-head CI is required again.

## Native symbol header capture

Final aggregate review found that fixed English column coordinates clipped
Ukrainian, Portuguese, Dutch and Polish headers, and included first-row text
in Spanish, German and Italian headers. The author now captures both complete
native header spans by their actual header-band geometry. The frozen source
records retain each span and rectangle in `source/symbol-header-capture.json`.
All nine header pairs were checked in the browser; Italian native `Símbolo`
is preserved exactly. Nine strict builds and frozen replay/admission/tamper
checks pass again. Browser evidence is in `symbol-headers-qc.json` and the
nine `*-symbol-headers.png` files beside the earlier layout evidence.

## Publication hold and native heading correction

Engineering #1442 merged as `c1c984c5f5e656df6ec0a90905c8e9fd99d8e92b`;
Hello-Docs mirror is `5b6d0b4a724e8c25532933c60e5c195c047709f7`.
Publication #176 remains unmerged. Final inspection found Ukrainian, Portuguese,
Dutch and Polish solar headings included the tail of the preceding AC caution.
German and these four locales also repeated solar heading text in the body.

The corrective source package is `git-20261005-47a346dc` for all nine languages.
The earlier committed packages remain byte-identical and are not published.
Four charging/connection subheadings now follow the native heading font size,
with the selectable sold-separately badge supplied independently. Solar
paragraphs use complete native body spans and exclude the larger heading and
badge spans. No native technical content, artwork or component structure is
changed. The source SHA remains the same HTE139 master. This is a blocking
source-only correction within MA-256, not a shared renderer or workflow change.

The new revision passes nine strict Sphinx builds, source-input hash checks,
identical English component signatures, byte-identical cold replay, fresh
trusted admission and actual tampered-art rejection. Nine desktop/mobile
solar heading/body checks show no horizontal overflow; evidence is retained
in `reports/je3600a-nine-language/browser/solar-heading-qc.json` and the
18 `*-solar-heading-*.png` files. The English Markdown remains byte-identical.
Production Python, renderer/CSS and technical data are unchanged; the earlier
5174-test full local pass still applies, and final-head CI is required anew.
The branch wrapper could not switch the shared main checkout because another
worktree owns it; the isolated correction branch was created directly from
the freshly fetched, verified `origin/main` after that refusal.
