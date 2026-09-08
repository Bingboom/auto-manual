# Independent single-language Web packages

## Discovery and execution checklist

Request: [single-language package requirements](https://claude.ai/code/artifact/428b5125-8ed6-4f71-a06b-f764640789d9).
Baseline: auto-manual `d1b12bf8`; existing RTD publication remains unchanged.

- [x] Read the R1–R7 requirements and preserve Git-only intake (no online Base writes).
- [x] Reproduce the existing merged JE-1000F/US Web build through `build.py md`.
- [x] Investigate the existing `--lang` path: merged review fallback omits the
  cover mapping and fails before rendering. This path is not the package splitter.
- [x] Confirm explicit page language markers and manifest `lang_blocks` already
  exist. Reuse those source contracts; never infer language from rendered HTML.
- [x] Derive language bundles from one complete, frozen bundle and its index.
  Project mixed preface blocks into separate `00_preface_<lang>.rst` derivatives.
  Preserve the original review source and source language page identities.
- [x] Export each derivative through the existing whole-document IR/MyST path.
  Use unique manual filenames so the unchanged RTD assembler discovers all three.
- [x] Build standalone language sites: actual manual at index.html, local assets,
  language-specific search, no library branding, sibling language links to home.
- [x] Generate each PDF with headless Chrome and hide all package controls in print.
  Disable download only after confirmed HTTP 404/410, never on probe errors.
- [x] Produce deterministic archives, file inventories, release.json and catalog.json
  under `manual-release/<model>/<region>/<version>/<lang>/`.
- [x] Verify EN/FR/ES body and both TOCs, search isolation, nested-prefix relocation,
  moving one package alone, language navigation, PDF visibility and asset closure.
- [x] Run unit/lint/guardrails/doc links and the existing US/JP build checks.
- [x] Open [implementation PR #1079](https://github.com/Bingboom/auto-manual/pull/1079) with actual validation evidence.
- Upload is deferred by the operator; no OSS setup is needed for this milestone.
- [ ] Continue the remaining table-scoped Web intake using the validated common path.

## Ownership and safety net

`tools/web_language_bundle.py` owns source-index projection;
`tools/web_manual_package.py` owns the standalone Sphinx/PDF/archive consumer;
`tools/build_web_packages.py` is the thin orchestration command. Existing
`markdown_bundle.py`, shared IR and `readthedocs_source.py` remain the consumers.
Package UI lives in a dedicated renderer contract, not product-specific code.

All generation uses an isolated output directory. No edits to `docs/_review`,
no new per-model config, no HTML language slicing, no LaTeX PDF dependency,
no dependency or workflow changes, and no upload of credentials into artifacts.

Validation ladder: focused tests → Ruff → complete unittest → maintainability
and link checks → representative builds → browser/PDF/package relocation checks.
Compare source text and image identities with the merged baseline; do not update
baselines to hide content loss. Record any expected TOC count difference from the
prototype rather than hardcoding 46 for every product.

## Deferred decisions

OSS bucket, region and handoff prefix are not established by an OSS Browser
installer or an AccessKey. Build and local acceptance proceed independently;
upload waits for the destination contract. Language switching intentionally returns
to the destination homepage; cross-language section-anchor mapping is out of scope.


## Local build

Prerequisites: the normal repository Python/Pandoc/Sphinx environment, Node.js,
and an available Playwright installation with Chrome or Chromium. The PDF step
uses Node's `playwright` module (set `NODE_PATH` if it is supplied by a bundled
runtime). No Python dependency or CI changes are required.

Run from the repository root, using **new, separate directories**:

```sh
python -m tools.build_web_packages \
  --config configs/config.us.yaml --model JE-1000F --region US \
  --version 2.3 --languages en fr es \
  --source review-asis --data-root tests/fixtures/phase2 \
  --work-dir /tmp/manual-package-work \
  --output-dir /tmp/manual-release \
  --browser "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

The fixture supplies offline lookup data to the frozen `review-asis` derivative;
it is not a live source-table update. Use the approved snapshot for other targets.
The first supported package UI languages are EN/FR/ES; other languages require
localized package controls before admission. Model/region/version are explicit.
The legacy merged-review `build.py md --lang` overlay remains separate debt.

The generated MyST directories retain their normal RTD scaffolds and distinct
manual filenames. The separate delivery tree contains `catalog.json`, a version
directory with three language folders and ZIPs, and `release.json` with archive
and file hashes plus source projection provenance. ZIP entries include their
language folder, so extracting the three archives into one directory enables
`../fr/index.html` navigation. Unchanged input bytes produce identical ZIP bytes;
Chrome's PDF metadata can vary between independent print runs.

For Mac/Safari, extract the additional `_all.zip` preview bundle and double-click
`打开手册.command` (Python 3 must be available). It starts a loopback-only server
on an available port and opens the manual in the default browser. Keep that
terminal window open while reading; closing it stops the preview. This avoids
depending on Safari file-to-file navigation across sibling folders and enables
full search snippets. Nothing is uploaded and no browser security setting changes.

Open `<language>/index.html` for direct offline reading in browsers that allow
sibling file navigation; PDF links remain enabled for local files. Alternatively,
serve the extracted parent with `python -m http.server 8000` and open
`http://localhost:8000/en/index.html`.
Each search index includes only its own language. Moving one folder preserves
manual/images/search/PDF; language links need the sibling folders.

Source language scope is selected before parsing. The complete materialization
is retained in `_build/<model>/<region>/source`, and the language derivatives
keep that existing target path contract because governed figure selectors still
read the target directory. No HTML language guessing or duplicated parser is
introduced. Mixed preface source remains untouched.


## Acceptance — 2026-09-07

JE-1000F/US version 2.3: each language has 46 body headings, 46 left TOC
entries, 46 right TOC entries and 70 loaded image elements. Desktop (1440 px)
and mobile (375 px) have zero horizontal overflow and no browser script errors.
The language toolbar stays at the top while scrolling and navigates to the
sibling homepage. The PDF has 31 pages in English, 32 in French and 32 in Spanish;
package controls and skip links are absent from print. Representative PDF pages
were rendered and visually checked.

Archive extraction under another URL prefix passed file-hash and browser
checks; moving the French folder alone preserved its images and local PDF link.
PDF probes: 404/410 disable, 403/500/network failures leave enabled. Language
searches return only local `index.html` and its anchors. The unchanged RTD
assembler discovered all three generated MyST sources without alias collisions.

All 48 non-preface source pages retain identical IR payloads to the merged
baseline after normalizing only relocated provenance paths and their dependent
hashes. Prefaces use the existing explicit language-block trim. Full unit suite:
3,860 tests, 22 skips; focused package tests, Ruff, maintainability and documentation
links passed. US (`config.us-en.yaml`, review-asis) and JP (`config.ja.yaml`, auto)
checks passed with `--data-root tests/fixtures/phase2`, isolated staging,
`--no-clean --skip-root-index`. Bare checks in a clean clone initially failed
because the ignored live snapshot was absent; JP review-asis also had no review
bundle there. No source table was fetched or modified to bypass these conditions.

Deferred: uploading, RTD release integration for the standalone consumer, the
legacy merged-review `--lang` overlay, and existing low-resolution artwork. The
existing shared Web figure selectors still depend on target path segments; this
consumer preserves that contract without broadening the shared-renderer refactor.


### Operator acceptance correction

The initial local navigation check covered Chrome, not Safari. The operator
reported Safari sibling-language navigation failure after double-clicking an HTML
file. Delivery now includes a combined local-preview archive with the three
independent folders and a loopback launcher. This is a local-serving path, not a
change that makes Safari file-mode navigation unrestricted. Launch-script execute
permissions are retained in ZIP metadata. A regression test starts the actual
server and reads two sibling language pages without opening a browser.

Dark system appearance also exposed a black toolbar with dark links. Package
controls now use the same light gray surface as the warning panels, explicit dark
text for normal/visited/current links, and a stronger gray border for selection.
This presentation is checked under both light and dark browser appearance.
