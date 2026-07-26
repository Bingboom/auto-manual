# JE-1000F US reference-copy parity discovery (2026-07-26)

## Objective

Align the frozen `JE-1000F/US` review copy with the approved 58-page V2.0
reference PDF before the remaining asset and layout-parity work begins.

Reference:

- file: `Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf`
- SHA-256: `e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2`
- pages: 58
- geometry: 368.787 x 524.692 pt

Frozen baseline:

- branch base: `origin/main` at `863c45ddb73043df98de737461a2c2f69d612919`
- approved contract:
  `docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json`
- baseline Manual IR content SHA-256:
  `e38dad9c6e8d47ea2e1a3c5fe724786d22489861832beebd42cb5a4d953318b3`

## Discovery method

1. Extract the reference PDF with `pdftotext -layout` so physical page and
   two-column reading order remain inspectable.
2. Compare it with the 52-source-page Manual IR captured in the latest clean
   58-page InDesign package.
3. Trace every candidate delta back to
   `docs/_review/JE-1000F/US/{page,generated}`.
4. Check historical generated bundles when the PDF extraction is ambiguous;
   never transcribe a broken line ending or discretionary hyphen as source.
5. Rebuild Manual IR after editing and re-run the text ledger against the
   reference.

## Difference classification

| Class | Examples | PR1 action |
| --- | --- | --- |
| Real frozen-copy drift | translated maintenance copy, localized signal labels, operation/App wording, back-cover address/contact fields | update the frozen review source and record the exact reference wording |
| Reference typography only | spaces around units, PDF line wrapping, discretionary hyphens, curly/straight quote presentation | preserve semantic source unless the printed characters materially differ |
| Renderer omission or relocation | `3s` missing beside an operation button; safety-tail panels composed on the following physical page | no source workaround; route to the owning layout PR |
| Artwork text | product-overview port labels, LCD artwork labels, QR artwork | no source workaround; route to the asset PR |

## Confirmed source-copy work

- English safety copy: restore the printed `overheats` wording, parenthesized
  operating-temperature notation, printed button/cross-reference wording,
  and punctuation where the reference differs.
- French and Spanish: align safety, user-maintenance, signal/symbol, FCC,
  operation, charging, troubleshooting, specification, warranty, and App copy
  only where the printed reference contains a materially different phrase.
- Back cover: restore the complete printed address, `(US)` phone suffix,
  `hello@jackery.com`, and `www.jackery.com` through the existing five-field
  editable component.
- Keep review-page and materialized generated copies synchronized when both
  carry the same structured block.

The final file list is deliberately source-driven: only files with a confirmed
reference delta will be staged.

## Reference-faithful printed anomalies

PR1 intentionally preserves characters printed in the locked reference even
when they look like editorial defects. Correcting them here would no longer be
a one-to-one source-copy replica. Confirmed examples include:

- `Doucuments` / `Doucumentos` in the in-box labels;
- French `alimentation vec commutation`;
- Spanish `da` and `pied` residues;
- English `ackery's` in the warranty copy;
- the repeated Spanish UPS phrase `al mismo tiempo`;
- other printed forms already confirmed during the page audit, including
  `supresión` and `ssimultanément`.

These strings may conflict with ordinary language-quality rules. Treat that as
an explicit reference-fidelity exception, not permission to silently normalize
the locked PDF wording.

## Non-goals

- No edits to `data/layout_params.csv`, IDML geometry, styles, finalizer JSX,
  visual thresholds, pagination, or the 58-page composition map.
- No raster/icon, QR, transparency, or effective-boundary changes; those are
  PR2.
- No writes to Feishu/Base source tables in this PR. Structured-field
  differences are recorded in the frozen review derivative; any live source
  table back-port remains approval-gated and requires exact record IDs.
- No generated `docs/_build/**`, `reports/**`, `tmp/**`, INDD, IDML, PDF, or
  package artifacts are committed.

## Contract gate

The current approved contract is hash-bound to the baseline Manual IR. The
maintainer rebind command correctly rejects a changed
`manual_content_sha256`: copy changes require a new page-by-page layout review
and approval. The physical map and reference-PDF identity must remain byte-for-
byte unchanged.

PR1 therefore treats the refreshed source identity as a review candidate until
the rebuilt 58-page package has been inspected. It must not claim that a
mechanical rebind constitutes human approval.

Two identities are useful during review:

- frozen review-source audit IR: 52 pages, 570 blocks, `skipped_raw=0`,
  `manual_content_sha256=0f73d5bdc9a3fde2985194336aef0638ad956155fc9341c03864380529d1e4c8`;
- prepared merged production IR (after asset aliases are materialized): 52
  pages, 570 blocks, `skipped_raw=0`,
  `manual_content_sha256=cc2ac59f3878788028f7acf61aa1fce535a3e2b80aaa87e8978e50b1db51fae7`.

Both bind to snapshot
`7e5ebfa8713983d055210c00e22305e34f636a83d5c3bcab210bb39a5706f0c5`.
The prepared identity is the one a future approved production contract must
bind after human page review.

## Candidate native-preflight result

An isolated temporary contract copy was rebound only for local preview. It
preserved the approved reference PDF digest, 58-page physical map,
composition IDs, and visual thresholds, and was explicitly labelled as not a
human approval. The production exporter then completed with 58 spreads and a
52/52 source-page match.

Native InDesign 2026 `21.0.1.6` preflight found:

- pages: 58;
- missing fonts: 0;
- bad links: 0;
- overset stories: 2;
- Spanish operation flow: physical pages 46-49;
- Spanish warranty flow: physical page 55.

The two oversets are a layout follow-up caused by the longer locked-reference
copy. They are not resolved by changing the copy in PR1 and the formal
approved contract remains untouched.

## Validation trap found during PR1

`build.py check --source review-asis` currently forwards that value to
`validate_spec_master.py`, which rejects it because the child parser accepts
only `auto`, `runtime`, or `review`. Using `--source review` is not a safe
read-only substitute on a dirty frozen review bundle: the wrapper runs
`sync-review --sync-scope params` first and rewrites review files.

For this PR, the safe read-only equivalent is to prepare an isolated
`review-asis` staging bundle and invoke `tools/check_docs.py` directly against
that staging root. That check passed. Fixing the CLI boundary is out of scope.

## Target-scoped sync preservation plan

The PR check exposed a second, narrower problem: the automatic
`sync-review --sync-scope params` pass re-merges placeholder-bearing lines in
the shared US safety templates. A placeholder and its surrounding raw HTML can
share one physical RST line, so refreshing the placeholder also restores the
generic template wording around it and loses the reference-faithful frozen
copy.

The approved fix is target-scoped and data-driven:

1. Teach review sync to honor an exact `sync_preserve_paths` list stored in a
   review bundle's own `manifest.json`.
2. Declare the three frozen safety pages in the committed
   `JE-1000F / US` review manifest. No other target receives the declaration.
3. Skip a protected destination before copy or parameter merge, and record the
   skipped paths in sync metadata so the behavior is observable.
4. Add regression coverage proving the protected safety raw HTML remains
   byte-for-byte unchanged while an undeclared sibling target still syncs.
5. Document that removing the manifest declaration (or deliberately reseeding
   the review bundle) is required before those pages can be refreshed.

Safety nets:

- protected paths must be relative `.rst` files under `page/` or `generated/`;
  invalid or escaping declarations fail closed;
- shared US templates and phase-2 source tables remain unchanged;
- ordinary parameter synchronization remains unchanged for all undeclared
  targets and paths.

Non-goals:

- no model-name branch in Python;
- no new prose override directory;
- no change to `review --refresh-review`, which remains the deliberate full
  reseed path;
- no attempt to solve the two native InDesign oversets in this sync fix.

## Validation ladder

1. RST/source parity ledger: no unexplained textual deltas.
2. Manual IR: 52 source pages, zero skipped raw blocks, stable source order.
3. Reference contract: unchanged reference PDF digest, page geometry,
   composition IDs, physical page ranges, and visual thresholds.
4. Targeted Manual IR, reference-layout, data-component, and special-page
   tests.
5. `python -m ruff check build.py integrations tools tests scripts`.
6. `python -m unittest`.
7. `python tools/check_doc_link_integrity.py`.
8. `python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US`.
9. Production IDML + native InDesign finalization: 58 pages, zero overset,
   zero missing fonts, zero bad links.
10. Page-by-page text re-audit against the locked reference before contract
    approval and PR publication.
