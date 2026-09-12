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
