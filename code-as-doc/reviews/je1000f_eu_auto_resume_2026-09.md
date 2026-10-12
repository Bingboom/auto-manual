# JE-1000F EU auto-resume table correction

Status: active

## Discovery and bounded plan

The native PDF extraction already preserves two headers and 3/4 conditions.
`FrozenBook.operation("restore")` incorrectly projects them as two lists.
The shared `HB-TABLE-AUTO-RESUME` style and Web transformer already implement
four rows with the second left cell spanning two rows, but this style has no
embedded ComponentSpec binding yet. Add that binding and reuse the existing
Web transformer and CSS. Freeze uk/pt/nl/pl again without changing copy or images.

Safety nets: four-language cold IR replay, exact condition/header preservation,
rowspan geometry, invalid shape rejection, unchanged non-table DOM and asset
hashes. Run focused tests, full unittest, Ruff, guardrails, doc links, US fixture
check, strict four-book Sphinx and exact RTD portal build. Inspect desktop and
390px layouts. Publish through engineering PR, mirror, publication-only PR and
RTD verification after every check is green. No live table writes, changes to
other targets, workflows, CLI, dependencies or historical frozen packages.

## Verification

Implemented a registered embedded ComponentSpec for the existing shared table
style. Web dispatch uses the existing auto-resume transformer and unchanged CSS;
other renderer bindings expose semantic projection only. No print-rendering
capability is newly claimed.

- Focused public replay and Web presentation suite: 62 tests passed.
- Four strict Sphinx builds: 15 sections each, one auto-resume component each.
- Four source extraction JSON files and all 57 assets per locale are byte-exact
  against the prior Overview-headings release; all other DOM is unchanged.
  Removing the two artificial subheadings also removes their navigation entries
  and shifts Sphinx automatic numeric anchors in Ukrainian; semantic chapter
  anchors remain unchanged. Only these generated anchors and whitespace were
  normalized in the DOM comparison.
- Source-free frozen IR replay reproduces each Markdown file exactly.
- Browser: bold headers (700), 16px rounded border, row cell counts 2/2/1/2,
  middle-left rowspan 2. At 390px all four pages remain 390px wide; the shared
  640px table scrolls inside its 354px container.
- Exact RTD portal build succeeded. Publication audit: 58 targets retained,
  54 unchanged target metadata records, 3,776 unchanged non-target files,
  4,060 manifest files verified and 2,252 pooled references resolved. Original
  five JE-1000F EU languages remain at version 2.7.
- Ruff, maintainability guardrails, doc links and US fixture check passed.
- Full unit suite: 4809 tests passed in 503.252s; OK (skipped=22).

The immutable source is
`manual_sources/JE-1000F/EU/nine-language/git-20260929-c38415f5-auto-resume/four-language`.
Engineering and publication CI plus final deployed revision/DOM checks remain
release gates under MA-200. Local preflight alone is not online acceptance.
