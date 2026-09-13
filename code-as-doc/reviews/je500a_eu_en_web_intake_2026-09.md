# JE-500A EU/en Web intake checklist - 2026-09

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
