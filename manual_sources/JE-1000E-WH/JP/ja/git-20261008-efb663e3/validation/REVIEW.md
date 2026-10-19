# Engineering candidate review — JE-1000E-WH / JP / ja

Authoritative source: operator-supplied 27-page Japanese PDF, SHA256
`efb663e3b22fec90bb8d4f602cb830471360034d9ead9293168f708ce937c3be`.
Filename V2.0 / 2026-07-29 is provenance; no printed version was recovered.
This package remains `publication_eligible=false`, candidate admission only.

## Source and replay evidence

- Fresh PDF native blocks/coordinates match the frozen source. `native-verification.json`
  covers 620 native lines, 17 chapter targets and 61 local image elements; none missing.
- Two fresh replays are byte-identical and match `web/ja`; source tampering,
  missing chapter and unbound image are rejected. Outputs are pinned separately
  by `output-inventory.json`, avoiding a self-referential manifest hash.
- 60 artwork files: reused mechanical panels plus 19 source-local illustration/QR
  crops and 12 source-native vector safety symbols. The real `build.py asset-intake`
  pipeline passes all 31 extraction entries with expected hashes (`asset-intake.log`).
- `artwork-structure.json`: 12x raster comparisons outside native text-redaction
  rectangles preserve all unaffected illustration pixels; crop-only panels are exact.
  Native drawing-list equality is sometimes false after MuPDF path cleanup. This is
  raster evidence, not a claim that every PDF vector command is byte-identical.
- `source/symbol-bindings.json` records inspected shared candidates and explicit
  native path selection. None of those shared candidates passed the fixed native
  glyph/tint/transparency check. Twelve original SVG symbols independently compare
  with zero normalized channel error. `native-symbol-pairs-12x.png` shows original
  source cell backgrounds beside the transparent candidate symbols. Rejected
  earlier PNG copies remain evidence-only under `rejected-symbols/`.

## Browser evidence

Real in-app browser, desktop 1280x900 and mobile 390x844. Browser theme preference
was preserved. `browser-desktop.json` and `browser-mobile.json` record all 17
anchors, loaded images and no overlapping live label pairs. Document widths remain
1280 and 390 respectively. Cover artwork is 260px wide; duplicate cover names are
represented once in the title. Direct `#product-overview` navigation and reload
keep the overview heading visible (desktop anchor 31.9px, mobile 95.8px).
Images reserve intrinsic aspect ratios before decoding to avoid fragment drift;
measurements and screenshots are taken after smooth scrolling settles.

Safety signal order is warning, caution, explanation, hint. Original symbol
panels retain left/right order, with one recycling heading/body row and the
native Li-ion32 glyph. The signal badges use the native triangle via document CSS;
mobile label width is 27%, with 15.2px description text. `desktop-safety.png`,
`desktop-safety-symbols*.png` and `mobile-safety*.png` show the actual result.

Final full-page desktop/mobile captures and cover/overview screenshots accompany
App and installation screenshots. The unchanged LCD component was actually
scrolled 286px horizontally on mobile (`mobile-lcd-scrolled.png`); LCD modes and
troubleshooting tables retain their shared horizontal scrolling containers.
The final full-page mobile capture uses the initial table scroll position.

## Local checks

- Credential-shape scan: official checksum-verified gitleaks v8.30.1, same
  configuration as CI; zero findings after documented test-ledger digest
  omission (`secret-scan.log`, `log-sanitization.json`).
- Strict Sphinx: `python3 -m sphinx -W --keep-going -b html <cold-source> <html>`.
- `PYTHONPATH=. python3 <package>/verify.py --html <html>/manual.html --pdf <PDF>`.
- `python3 -m ruff check build.py integrations tools tests scripts <package>/*.py`.
- `python3 tools/check_maintainability_guardrails.py` (`guardrails.log`).
- `python3 tools/check_doc_link_integrity.py`: 266 docs, 2578 links, zero broken.
- JP regression: `python3 build.py check --config configs/config.ja.yaml
  --model JE-1000F --region JP --data-root tests/fixtures/phase2` passes. This
  verifies the existing JP fixture, not production enrollment of JE-1000E-WH.
  Default checkout check lacks `data/phase2/Spec_Master.csv`; its failure log is
  preserved, and no live snapshot or Base was changed to satisfy it.
- Full discovered-suite coverage: 5217 unique cases, 5182 passed, 35 skipped,
  zero unresolved failures (`unittest-receipt.json`). Canonical `/private/tmp`
  subprocess shards covered 5193 cases; 24 bridge tests could not import their
  discovery-injected module by synthetic dotted ID. The native `load_tests`
  entrypoint recovered all 24, plus a passing provenance recheck (25 tests).
  Original failed runs and their logs are retained (log trailing whitespace
  normalized; raw originals remain in local `/tmp`). Four opaque fixture-ledger
  SHA1 `run_key` values were omitted from public logs because the credential
  scanner matches their assignment shape; see `log-sanitization.json`. No
  scanner rule, workflow, test verdict or candidate content was changed. This is equivalent complete
  case coverage, not a clean single `python3 -m unittest` invocation.
  Queue/publish/write messages in these logs are mocked test operations, not
  external business-plane writes.

## Material boundaries and review obligations

Four finished localized panels (UPS and AC/solar/car charging) retain original
non-empty captions and numbers, plus exact semantic text companions. Visible
caption changes require a refreshed source-local asset; they are not all live
HTML labels. Complete App phone frames and QR pixels are retained. QR destinations
were not decoded or invented. Original technical wording, main-power off/on pairing,
JP temperatures, UPS 8A and `出カポート` remain; F2/F6 native font-glyph recovery is
explicit in `source/differences.json`.

Warnings use shared callout carriers with readable paragraphs/lists rather than
reproducing every pictogram and row frame from PDF pages 4–5. Page 3 symbol
meanings and glyphs are source-bound. This is source-faithful Web reflow, not a
pixel-identical paginated PDF reproduction.

Operator text/pixel review and production prepared-component enrollment remain
pending. No merge, publication, Hello-Docs/RTD receipt, Base/source-table/queue,
HTML_link or asset registry write. Root tmp/ and other windows are untouched.
