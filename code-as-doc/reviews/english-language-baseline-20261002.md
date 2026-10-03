# English baseline inheritance implementation

Status: active

No production English baseline is approved by this change.

## Discovery and boundary

The existing shared-component admission checks presence, variants, bounded legacy
debt and actual asset bytes. It does not compare a candidate with an independently
approved English structure and asset-selection decision. The existing artwork
selection table is a procedural prerequisite, not an automatic comparison.

JE-3600A English is still receiving artwork corrections. JBP-3600A has a local
English preview and PR #1404. The operator subsequently authorized English
merge/publication in its own window; the final LCD-corrected IR and visual
evidence still need binding before a baseline is promoted. Neither candidate
may be silently promoted. JE-2000E is a structural reference for JE-3600A, not
the authority for JE-3600A values or copy.

## Bounded plan

1. Add a content-neutral IR structure/asset summary; retain semantic components,
   ordered slots, table/column shapes and presentation decisions. Hash packaged
   bytes, not just candidate declarations. Never modify source text.
2. Extend the existing reviewed admission contract with optional language-baseline
   enrollment. Candidate metadata cannot opt out. Require explicit approval,
   source/IR/evidence hashes and exact locale/page mappings for approved entries.
3. Compare at the existing fresh admission seam for both native and prepared
   inputs. Historical replay remains immutable. Unenrolled targets are reported
   as uncovered, not baseline-verified. Candidate entries block fresh release,
   while local rendering remains available for review.
4. Verify source-free mutations and a real bilingual trial. Candidate trial
   results are not production approval or a publication receipt.

No new renderer, service, language stylesheet, live-table write, workflow change,
public build.py flag, dependency change or historical manual migration.

## Safety net and validation

Test removed/reordered components, changed variants/table shape, recropped art
with recomputed candidate hashes, absent metadata, invalid approval/identity and
unreviewed differences. Also test native-language text/long-copy changes and
precisely reviewed differences. Run targeted tests, Ruff, the full unittest
suite, maintainability/doc-link checks and the existing US build check. Inspect
a real non-English trial without overwriting either English intake worktree.

## Results

- Implementation: trusted enrollment is integrated into the existing fresh
  component admission used by prepared/native seal, stage and verify. Reports
  distinguish `not_enrolled`; fresh receipts persist the baseline status.
- Current target coverage: JE-3600A/EU and JBP-3600A/EU are explicitly enrolled
  as **candidate**, blocking new release until English confirmation. No history
  was modified and no production baseline is approved.
- Candidate trial: JBP-3600A operation chapter, English source page 9 versus
  French source page 17 of HTP011-EU-9国语言-0924.ai, source SHA-256
  `8c6c25ddbc885b8e186b3b643fb53677a383ddf22295b3a2ba689c4d5d8cf8d1`.
  Eleven native French strings are verified against the PDF text; both English
  artwork files retain identical bytes. The same shared IR renderer and MyST /
  Sphinx Web path rendered the sample. Zero structural differences, always
  `candidate_trial` / `publication_eligible: false`.
- Visual evidence: the actual French source page was inspected. Local browser
  screenshots at desktop (1280 px) and mobile (390 px) showed selectable French
  status/copy, responsive labels and the complete LCD-control section. This is
  chapter-level local visual inspection, not full English confirmation, full
  French source acceptance or RTD publication.
- Local artifacts are preserved under `.tmp/english-baseline-pilot/`: the
  reproducible `run_trial.py`, `source-copy-map.json`, full English candidate,
  chapter candidate/mapping, native source-page renders, shared-renderer IR
  packages and `cli-trial-report.json`. The pilot intentionally excludes all
  other chapters rather than presenting untranslated English as French.
- Verification: 64 targeted admission/seal/replay and guardrail tests passed.
  The complete suite passed: 5,075 tests, 32 skipped (2,314.481 seconds).
  A follow-up mutation additionally checks the actual embedded Web contract
  digest, preventing a changed renderer contract from retaining an old declared
  style hash. The final full suite also passed: 5,075 tests, 32 skipped
  (3,053.886 seconds). The updated real EN/FR chapter trial still reports zero
  structural differences. Ruff, maintenance guardrails, doc integrity and the strict English /
  French sample Sphinx builds passed. The default US check initially failed
  because this fresh worktree has no local phase2 snapshot; the supported
  `--data-root /Users/pika/Documents/auto-manual2/data/phase2` run passed without
  changing that snapshot.

## Remaining acceptance boundaries

The automated comparator cannot certify semantic translation accuracy or detect
an empty text frame already present in an approved image. Neither a candidate
record nor green tests are operator confirmation. Complete and confirm the exact
English IR/evidence/asset decision record, then promote it through reviewed
contract changes. The remaining native languages must preserve original content
and record any approved source-backed exceptions. No publication or live-table
write is performed by this implementation.

On 2026-10-02 the operator requested that, after testing succeeds, the existing
JBP-3600A window continue the remaining languages. Handoff is recorded separately
from implementation validation; it does not approve the English baseline.
