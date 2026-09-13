# JE-500A EU/en Web intake checklist - 2026-09

## Released-PDF correction in progress — 2026-09-13

The original AI-based acceptance below is historical and does not establish
parity with the released PDF now designated authoritative by the operator.
Released EU-UK V2.0-2026-06-09 PDF SHA-256:
`6f4b41ee74ca3282e655a2b2f6c6adf3b3448522b71b26f683b25785f6e5bee6`.
Delivery records `1gQyPR2Qyi` / `uNmShId5KH` resolve to node
`XPwkYGxZV3Rj0pEpF3d9vL5yWAgozOKL`; 89 physical pages.

- [x] Restore specification DC symbols from physical page 17 in native tables.
  A six-value regression failed on the original source and passes after repair.
- [x] Add the English preface from physical page 2 using a shared, product-bound
  legacy single-language fragment. The newer shared preface has additional legal
  sentences not present in this PDF and is deliberately not substituted.
- [x] Add physical page 89 EU declaration and manufacturer text. Preserve the
  source heading `RED Declaration of Conformity` despite its LVD/EMC/ROHS body;
  do not silently make an engineering/legal correction to the released source.
- [x] Visually confirm LCD high/low temperature share number 12, and fault codes
  F0/F1/F2/F3 share the restart action; existing native table mappings remain.
- [x] Replace the AI-derived Overview whose DC glyphs appeared as missing-glyph
  boxes with physical PDF page 7 crop `[25, 56, 342, 468]` at scale 4.
  Complete labels/leader lines remain; the heading/footer are outside the crop.
  New PNG SHA-256 is
  `749ca081dde5bfee3d3ac2dfc811f3e4078a11380c1cdc908bd832c7d9ae47bf`.
  Existing per-illustration recipe override carries the PDF source, while other
  illustrations retain truthful AI provenance. Preserve the semantic asset path
  `overview.png`; a different basename failed required-figure coverage, and that
  gate was not weakened. The original asset remains in Git history.
- [ ] Finish panel parity and update locked asset/source provenance together;
  no full PDF parity or production update is claimed yet.
- [x] Replace the LCD device map: the old AI crop clips number 5 at the right
  edge. Reviewed PDF page 8 candidate `[48, 63, 332, 223]`, scale 4, retains
  numbers 1–13 without including the table. Candidate hash:
  `122991a64cd306c82e70b0279024fa0bcad517e9fe0bfd8a30d6a81f0c46de99`.
  Both PDF panels replay through `manual_je500a_eu_pdf_panels.json` with package
  SHA-256 `aa6dfef814537ed4348415fa6f836c0c48040605f50969d5e6bec5244d50e6a9`.
- [ ] Complete real Web build, full validation, implementation PR and separate
  Git-only RTD publication gates before checking the overall acceptance.

English body: physical pages 5–18. Portuguese body: pages 75–88, explicitly
labelled `PT-BR` in the preface. Availability is not Web approval or publication.
Target tests: 7 pass after the Overview correction; real `build.py md` succeeds.
Strict Sphinx HTML succeeds. Full suite ran 4,100 tests with 22 skips and one
failure: the new shared preface was absent from the pinned structure registry.
Only its new English carrier is added to that registry, because the released
PDF uses distinct legacy prose; existing language grouping is unchanged.
Final full-suite rerun: 4,100 tests pass, with 22 skips (185.854 seconds).
Ruff, maintainability and 1,798 documentation links pass. Browser connection timed out, so no
new desktop/mobile visual acceptance is claimed.
After the LCD replacement, target check, real Markdown, RTD source assembly and
strict Sphinx succeed. Final HTML contains 16/16 locally present hash-verified
illustrations and eight native tables; required restored prose is present.
The original solar charging connection-diagram sentence is also restored.
Earlier target/preface/manifest tests: 19 pass before the Overview change. These
tests do not prove visual parity or a deployed release.

## Scope and authority

- [x] Target identity is fixed as `JE-500A / EU / en`, product line
  `Jackery Explorer 500 V2`.
- [x] Source is the user-selected DingTalk record
  `YndMj49yWjP03jNjCDojvAQdJ3pmz5aA / 97v7518 / xF8IUxGEbx`.
- [x] PDF-compatible Illustrator source SHA-256 is
  `c85b8da316fd7b13e3e77e311df76c389234495f38f454019a88f61b6812d12f`.
- [x] The source contains one 7942.78 x 5567.33 pt artboard. The English body
  is the 14-panel row at y = 1435.81-1960.22 pt, x = 1181.37-6347.75 pt.
- [x] The task is Git-only. No live DingTalk/Feishu table writes, OSS upload,
  Hello-Docs publication, or PR self-merge is authorized.

## Structure and ownership

- [x] Freeze the target-scoped source snapshot, extraction recipe, and source
  manifest with reproducible hashes.
- [x] Reuse `configs/config.eu-en.yaml` and the shared portable-power semantic
  component pipeline; do not create a per-model config.
- [x] Add only the JE-500A page-manifest differences needed by the published
  English panel sequence.
- [x] Keep headings, safety text, tables, NOTES/CAUTION boxes, troubleshooting,
  specifications, and warranty as searchable semantic HTML.
- [x] Extract illustrations only from the JE-500A source. Complete
  image-owned instruction panels may retain their embedded copy and grey frame.
- [x] Keep LCD as device/screen artwork plus live HTML/CSS tables; do not use a
  rasterized LCD table or whole-page screenshot.
- [x] Prevent duplicated source-figure annotations and Web-native explanatory
  text.

## Verification

- [x] Recipe replay reproduces every approved asset hash.
- [x] Frozen source-manifest hashes reproduce in a clean checkout.
- [x] Target tests cover source bindings, identity/facts, semantic components,
  asset coverage, LCD ownership, and tamper rejection.
- [x] `build.py check` passes against the frozen JE-500A data root.
- [x] A real `build.py md` Web package and strict Sphinx HTML build pass.
- [x] Generated media references have zero missing files and no foreign-model
  residue, unresolved tokens, duplicated instructions, or missing glyphs.
- [x] Desktop and narrow-width browser review covers safety, NOTES/CAUTION,
  LCD, operations, charging, troubleshooting, specifications, and warranty.
- [x] Required repository unit, lint, link, secret, and diff checks pass.
- [x] Latest `origin/main` is merged normally before push; no rebase or force
  push is used.
- [x] A local preview and independent package are reported separately from
   formal publication, and the PR is left for operator review/merge.

## Acceptance evidence

| Gate | Result |
|---|---|
| Approved asset replay | 16 exports; package SHA-256 `03bf2187608397e75f92a75a62a1dbef3a8aaf56a7efc3df00d3bc565e029d6d` |
| Target and repository tests | Target coverage passed; full suite passed 3,909 tests with 22 skips |
| Manifest family | 29 manifests / 6 anchors / 23 folded; byte-identical round trip |
| Web build | Frozen-source `build.py check` and `build.py md` passed; strict Sphinx HTML passed with zero warnings |
| Web presentation | 13 semantic pages, 16 finished illustrations, 11/11 required figure slots complete |
| Browser | 1,440 px and 390 px: zero broken images and zero main-content overflow |
| Static checks | Ruff, maintainability guardrails, documentation links (178 files / 1,753 links / zero broken), gitleaks, and Git diff check passed |
| CI target observation | 22 pass / 9 baseline skips / 2 pre-existing observed failures; JE-500A is an expected frozen-source skip in shared fixtures |
| Independent package | `JE-500A-EU-en-web.zip`, SHA-256 `50546896420bde2feb1caafa46c7a893ee86b11daf5e04b14cdbeb4a7147f6c8` |
