# Overview headings as native Web text

## Discovery and scope

The clean reusable checkout has tree 8a0c192add689551c58b25fa7ae6dea17f4c78c9,
identical to live engineering main 79e337ec. The branch wrapper timed out during
Git transport; authenticated Git Data API remains the verified publication path.

Finished Overview crops include the front/right source headings, while the
native carrier headings are hidden unconditionally. The operator requests those
titles outside the image, consistent with the shared Web typography.

## Plan and safety net

1. Honor each finished panel's explicit captions_embedded boolean; hide the
   carrier heading only for legacy panels which include it. Keep shared
   Overview ComponentSpec and public renderer unchanged.
2. Render eight narrower clips from the original AI/PDF, using the existing
   corrected Dutch front-view PDF. Retain product callouts, specifications,
   leader lines, source hashes and approved errata. No image synthesis.
3. Build a new immutable four-language source package, replay cold IR and
   compare full-book words and all non-Overview markup/assets to the release.
4. Run focused/full tests, Ruff, guardrails, docs links, US fixture check,
   strict four-language Sphinx builds and local browser checks.
5. Publish through all-green engineering and docs/publish-only PR gates,
   then verify the deployed RTD revision and four language pages.

Non-goals: other models/languages, live tables, original source edits, CSS forks,
workflow changes, dependencies and modifications to historical frozen releases.

## Verified artifact boundary

Eight clips exclude view titles (front starts at 95 pt, right at 333 pt).
Retained pixels exactly match the same source rendering before clipping.
Dutch front view uses the existing hash-pinned corrected PDF. Four strict
Sphinx builds and exact cold replay pass. All fresh source JSON and complete
body words are identical; DOM changes only in Overview heading visibility
and the two image refs/hashes. All 55 other assets per language are unchanged.
Polish desktop and 390 px browser show bold live headings above the images,
with no horizontal overflow. Historical packages and the shared CSS are unchanged.

Full regression passed (4,807 tests, 22 skipped); focused tests 12 passed.
Ruff, maintainability guardrails, doc links and US fixture build check passed.
The exact RTD Sphinx command passed against the assembled 58-target candidate.
Scope audit preserves 54 other target metadata records and 3,768 non-target
files; old five languages stay at 2.7. All four 390 px browser checks show two
visible bold headings above their respective images and document width 390 px.
