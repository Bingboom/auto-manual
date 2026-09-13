# EU English Web batch integration — 2026-09-12

## Discovery

The independent-manual scope is 21 targets: 12 already merged and nine implemented in PRs #1091–#1099. PR #1100 contains subsequent JE-3000C illustration corrections. Combination projects are excluded. Latest inspected main is `d1eeb282`. GitHub permits squash merges only. Each source PR has passing checks before integration; this does not prove the combined tree or publication.

## Execution checklist

- [x] Inspect clean isolated checkout, source PR heads, merge policy, and publication boundaries.
- [x] Record MA-064 before merge actions.
- [ ] Merge #1091–#1099 and #1100 serially, preserving current source heads and user-approved crop fixes.
- [ ] Reconcile shared config, model lists, asset registry, manifest families, and count assertions after each merge.
- [ ] Run affected target checks, unit suite, Ruff, guardrails, and documentation integrity as applicable; require every final-head CI check green and no unresolved/changes-requested review.
- [ ] Use the existing Git-only publication path for RTD preview; verify actual deployed pages.

## Safety and non-goals

Work in an isolated integration worktree. Merge origin/main normally; do not force-push or rewrite contributor history. Resolve CSV conflicts as logical CSV records, never line-concatenate multiline cells. Retain all frozen-source hashes and semantic components. Build with `AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off`. No online Base write, OSS upload, combination manuals, IDML expansion, public API change, dependency change, or workflow edit.

## Validation commands

Use the repository Python environment: `python -m ruff check build.py integrations tools tests scripts`, `python -m unittest`, `python tools/check_maintainability_guardrails.py`, and `python tools/check_doc_link_integrity.py`. Target build/check commands and frozen data roots are recorded in each target acceptance document. Final publication acceptance requires real RTD URLs, not localhost screenshots.

## JBP-2000B source-lock repair during final integration

The JBP-2000B EU/en source manifest already had stale locks when PR #1081 first landed as `d36f5776`: `files[0]` (config.bp-eu-en.yaml), `files[18]` (eu_warranty.rst), and `files[46]` (target_overlays.json). This integration updates only their SHA-256 and size fields to the final validated tree so the Git-only preview can be reproduced; source authority, PDF identity, frozen CSVs, and manual copy remain unchanged.

Original PR history identifies the omitted lock refresh precisely: config changed after `f46f34dd` only to allow the existing Battery Pack 2000 / Explorer 2000 Plus / Explorer 1000 Plus identity literals; warranty changed after `aabd315f` only to separate bold year badges from bold captions without changing warranty terms. Both current files are byte-identical to the original merge. The shared overlay file subsequently added other target overlays; all existing overlay objects, including JBP-2000B EU, remain equal to the original merge. The original locked overlay bytes are available at `c9ce7bf6`.

The repair is required release traceability, not a PDF-version comparison or new content revision. Read back every declared source-manifest file after the three explicit replacements and verify the JBP-2000B frozen-source check and target regression tests.

## Final combined-tree validation

The local integration tree contains the full content of #1091–#1100; remote PR merging remains subject to each final-head gate. The full unit suite passed 3,970 tests (22 skipped). Ruff, maintainability guardrails, documentation links (1,758 checked; zero broken), frozen-source JE-3000C check, and the asset registry check passed. The actual registry contains 325 records, including 317 approved, with zero errors and existing declared missing/source-only warnings. Manifest-family verification passed for 37 manifests, six anchors and 31 folded derivatives. Six charger/accessory targets retain their intended Product Plan chapters. After the three explicit JBP-2000B lock corrections, all 47 declared files matched both SHA-256 and size, its frozen-source check passed, and eight related regression tests passed. No remote push, online-table write or OSS upload was performed from this integration worktree.

## JBP-3600A recipe-lock repair after preview preflight

All 20 frozen targets passed real check, Web Markdown and strict Sphinx builds at `978f7bcb`; source-lock validation correctly marked JBP-3600A unready because its `asset_recipe.sha256` still referenced the pre-#1078 recipe. Source intake #1075 (`d2b4629b`) froze that lock; approved #1078 (`f2f8abfc`) subsequently added the product's own LCD overview export and left the lock stale. The repair updates only this one recipe hash to the already-approved current recipe, preserving every image, prose, PDF authority and original source hash. Preflight results at the original SHA retain the failure; revalidation must identify the repaired Git SHA separately.

## Desktop flex-width correction from aggregate preview acceptance

The real aggregated release preview reproduced horizontal overflow on eight manuals at a 1,440 px viewport: shared desktop content (58 em plus four em of horizontal padding) and two 15 em drawers required 1,472 px. Furo's `.main` flex item retained its automatic minimum width. The existing `min-width: 82rem` media rule now sets `.main { min-width: 0; }` so normal flex shrink fits the available viewport; no overflow masking or cropping is added. The mobile rules are unchanged. No source manifest pins this CSS file, so no source-lock rewrite is needed. Preserve the prior failed browser evidence and validate freshly generated aggregate output for all 20 EU manuals at desktop and mobile widths before delivery.
