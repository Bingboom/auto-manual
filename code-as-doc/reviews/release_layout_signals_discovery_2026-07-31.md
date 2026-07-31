# Release Layout Signals Discovery — 2026-07-31

## Scope

Workstream W / Stage 4a item 15 asks release manifests to expose page count
and overset count as machine-readable layout signals. This review checks the
current release path before adding another schema or collector.

## Current state

PR #723 already added `tools/release_indesign_package.py`. When a native
`finalize_report.json` is present beside the production IDML, the release JSON
contains:

- `indesign_package.preflight.page_count`;
- `indesign_package.preflight.overset_stories` as a count;
- the related preflight verdict, missing-font count, bad-link count, PDF/X
  verdict, and InDesign version.

The roadmap statement that these signals are absent from the manifest is
therefore stale in two narrower ways:

1. the release CSV, which is the flat dashboard carrier, exposes preflight
   success and parity acceptance but not page count or overset count; and
2. a legacy or partial finalize report with no `overset_stories` key is
   currently summarized as zero, which confuses “not reported” with a verified
   zero.

Adding a second top-level JSON `layout_signals` object would duplicate the
existing package contract and create two authorities. The bounded completion
is to keep the existing JSON location and finish its flattened CSV surface.

## Safety net

Before implementation:

1. pin a full release-manifest run to the existing nested JSON page/overset
   values;
2. require `indesign_preflight_page_count` and
   `indesign_preflight_overset_stories` in the release CSV;
3. pin explicit zero to the string `0`, not blank; and
4. pin an absent preflight field to blank/unknown, never a fabricated zero.

The new CSV assertions must fail against current `main`; the nested JSON
assertion documents the behavior already delivered by PR #723.

## Implementation plan

1. Preserve `indesign_package.preflight` as the single JSON authority.
2. Flatten its page and overset counts into two scalar release-CSV columns.
3. Treat a missing `overset_stories` field as unknown (`None` in JSON summary,
   blank in CSV), while preserving an explicit empty list as zero.
4. Update release workflow docs and mark Stage 4a item 15 complete with the
   pre-existing PR #723 contribution made explicit.

## Non-goals

- No new release gate and no change to publish success/failure.
- No PDF or IDML page-count approximation when native preflight is absent.
- No duplicated top-level layout schema.
- No change to InDesign finalize, parity, or approved-layout contracts.
- No E1 snapshot archive/binding work; that remains Stage 4a items 16–17 and
  requires the archive-location/retention gate.
