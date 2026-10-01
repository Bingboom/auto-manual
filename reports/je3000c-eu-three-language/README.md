# JE-3000C EU three-language intake

Status: three complete local candidates, 2026-10-01. Portuguese and Polish are
eligible for release; Dutch remains a non-publishable source-review candidate.
No engineering or publication PR has been merged for this intake yet.

## Confirmed scope

Add Portuguese, Dutch and Polish to the existing EU Web manual using the
operator-provided `HTE156-EU-9国语言-0923.ai`. Preserve the six existing
en/fr/es/de/it/uk editions and all other products. Use native text, shared
manual-ir/v2 components and the public Web renderer. No independent HTML/CSS
implementation, OCR, source-table/schema changes or speculative translation.

## Source evidence

- Model on cover: JE-3000C, Jackery Explorer 3000.
- SHA-256: `45219a6e488358c4a76b847cd0288f5a865fd8ab899d8ceb9e154a5696816574`.
- 152 PDF-compatible pages. Body: pt 104–119, nl 120–135, pl 136–151.
- Shared preface page 4; print contents page 7 omitted from Web;
  manufacturer/declaration page 152 retained.
- Existing authority remains the six-language EUUK V2.0-2026-07-31 PDF.
  New language intake does not replace its content or source revision.

## Delivered candidates and shared components

The adjacent intake package records source geometry, artwork reuse decisions,
asset hashes, native captions and the reproducible extraction recipe. The
`git-20261001-45219a6e-native-web` package contains complete pt/nl/pl frozen IR,
MyST, assets and the common Web scaffold. Each edition has 15 chapters. Native
text and tables use the existing public components; dense localized overview
drawings retain their source callouts, with headings outside the artwork.

Shared same-model art supplies the unit, cable, manual, LCD map, UPS and AC-wall
figures. LCD/status symbols, WEEE2 and App-store/QR artwork reuse existing assets.
All three languages use identical ordinary-operation, solar and car artwork
with native localized labels. App screens retain complete phone edges.

The adapter adds an explicit `native_captions` binding for native PDF labels
that share one extracted block. It checks page and geometry provenance and
rejects mixed or duplicate labels. Safety labels may occur at either end of a
merged native block. These remain existing ComponentSpec/renderer paths; no
new public schema or target-only renderer is introduced.

## Repeated caption-box defect and regression coverage

The first car-art candidate removed lettering but retained the empty white
caption capsule. The extraction incorrectly treated that text container as
part of the native panel. Component admission only checked the semantic
structure; it could not detect the remaining raster box.

The reviewed recipe now replaces just that capsule with an empty, uniform
same-page gray source region. This preserves the original clipping masks,
device, wire and outer panel. The caption capsule is produced by the shared
ReferenceFigure CSS, including on narrow screens. Final shared-art SHA-256:
`594fa3eb67203bc5c45a260c9423f37992c93361f52c9d07671e7452dbc62f7f`.

`test_je3000c_caption_box_is_css_without_empty_box_in_shared_raster` cold-replays
all three packages, requires one CSS pill and two live labels, checks the old
capsule region for the uniform native gray, and requires identical art bytes
across languages. This protects this reviewed asset against recurrence; it is
not a general detector for arbitrary text boxes in every future image.

## Source decisions still pending

Dutch source pages 127–128 refer to DC where the diagram identifies the AC
button; page 122's front overview has the same mismatch. The car input's
combined current is 16 A on pages 122 and 132, versus 8 A in the English,
Portuguese and Polish editions. The operator has been asked to decide whether
to correct these. No factual correction has been applied; `errata.json` is
empty and the frozen Dutch metadata declares `publication_eligible: false`.
Do not include Dutch in a release until that decision and corresponding
image/text verification are complete.

## Verification

- Full `python3 -m unittest`: 4,995 tests, 22 skipped, passed before the final
  asset-specific regression was added. The final targeted suite passed all
  20 tests, including that regression.
- `python3 -m ruff check build.py integrations tools tests scripts` passed.
- `python3 tools/check_maintainability_guardrails.py` passed.
- `python3 tools/check_doc_link_integrity.py` passed.
- `python3 build.py check --config configs/config.us-en.yaml --model JE-1000F
  --region US --data-root tests/fixtures/phase2` passed as a repository
  regression gate; it does not validate the three new language bodies.
- `python3 build.py check --config configs/config.eu-en.yaml --model JE-3000C
  --region EU --data-root tests/fixtures/phase2` also passed for the existing
  target. The same new-language validation boundary applies.
- Each source-local candidate built with `python3 -m sphinx -q -W --keep-going
  -b html <candidate> <verification-html>`.
- Native body-line presence audit: pt 582, nl 580, pl 597; zero missing.
  This is content-coverage evidence, not independent linguistic approval.
- Cold replay with PDF/source reads disabled reproduced identical MyST for
  all three languages. Both source inventories match their pinned hashes.
- All 57 files of the previous six-language authority remain byte-identical.
- Formal asset intake and 12x inspection covered 16 extracted assets; source
  edges, phone corners, control circles and panel boundaries were checked.
- Browser checks cover desktop and 390 px layouts, broken images, overflow,
  car caption, operation labels, App numbering, LCD and warranty components.
  The evidence directory records measurements and the screenshots directory
  contains only retained visual checks.

Worktree starts clean at engineering main `34609ca8`; the branch wrapper would
switch shared `main`, already used by another window. The dedicated worktree
was branched directly from fetched `origin/main`, preserving all other trees.

The branch was then fast-forwarded to `b78ec590` after checking the intervening
App type-annotation change; focused App tests (23 passed) supplement the previous full
suite. Publication will use the existing Git-only frozen-evidence and
`docs/publish/**` assembly path. Engineering merge, release merge, RTD build and
production verification are separate milestones and remain to be recorded.
