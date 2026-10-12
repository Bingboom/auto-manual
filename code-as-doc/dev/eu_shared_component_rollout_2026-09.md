# EU shared-component rollout

Status: active — original rollout accepted on 2026-09-30; LCD follow-up is PR #1343.

The published EU audit found 74 ordinary table blocks without their dedicated
shared component and 13 LCD text-only fallbacks across 24 language manuals.
The LCD fallbacks need a separate source-asset audit; a missing component marker
alone is not proof of a broken page. Existing governed `hb-*` compositions and
approved finished panels are not automatically migration defects.

## Execution order and acceptance

| Phase | Scope | Acceptance | Status |
| --- | --- | --- | --- |
| 1 | JE-3000C de/es/fr/it/uk: LCD mode, auto-resume, key combinations; JE-1000H en: the same three tables | All 18 actual blocks use ComponentSpec; full copy/assets and other chapters unchanged; strict Web build, desktop/mobile and RTD verification | Merged in #1340; six target routes published and verified |
| 2 | JBP-2000B multilingual symbols/warranty; JE-100C, JE-300D, JE-500A general tables | Source-preserving bindings and target-appropriate variants; independent audit of the 13 LCD asset fallbacks | Merged in #1341; eight target routes published and verified; 13-table source audit recorded |
| 3 | Existing RST/projection admission, followed by old App/finished-panel migration | Capability and present-chapter requirements; explicit approved-art exceptions; no blanket portable-manual checklist for accessories | Admission merged in #1342; App/finished-panel migration sequence documented, execution deferred |

## Phase 1 cause and repair

The shared operation-table selectors recognized the placeholder and JE-2000E
page names. JE-3000C's localized `05_operation_guide_<language>` names and
JE-1000H's English `05_operation_guide` did not match. These two targets now bind
their actual page names in the existing target overlay registry, with figure
and legacy artwork grants disabled. A global wildcard would also include the
JE-3600A operation page, which has a different capability set.

Normalized RST auto-resume and key-combination tables now become the same
`HB-TABLE-AUTO-RESUME` and `HB-TABLE-KEY-COMBINATIONS` specifications used by
native PDF imports. The existing LCD mode adapter supplies `HB-TABLE-LCD-MODE`.
The HTML adapter requires explicit normalized classes, validates table geometry,
and rejects duplicate tables and unexpected owned content instead of dropping
copy. It does not guess roles from translated headings or table size alone.

Regression tests use all six actual RST templates and verify the 18 bindings,
source text, image references, malformed spans, duplicate ownership and the
unaffected JE-3600A capability boundary. Full-book `build.py md` runs use isolated
staging roots and the designated source snapshots; comparisons normalize only
staging paths and derived hashes, then compare actual rendered text and assets.

The frozen carrier retains source-authored key-combination emphasis and line
breaks after its text is checked against the ComponentSpec. The LCD renderer
also retains the approved illustration's path, hash and provenance class after
checking that the carrier and component reference the same artwork. These
checks prevent a component migration from silently losing formatting or the
evidence that identifies an approved image.

## Local acceptance evidence

All six target `build.py check` and full-book Web builds passed. All six final
strict Sphinx builds passed. Relocated-package replay produced identical
fragments without reading source RST, CSV or current contracts; changing a
packaged image was rejected for every book. Original build bodies and image
bytes were compared with the published versions before evaluating the change.

Five books preserve rendered text exactly. In JE-3000C French, the source's
straight apostrophe in `d'énergie` remains straight in the shared HTML table;
previously Sphinx smartquotes rendered `d’énergie`. This typographic difference
is recorded explicitly, not normalized away or represented as six-book exact
text parity. Original source copy and all image bytes remain unchanged.

The first full-suite run executed 4,866 tests with two failures: the newly
converted LCD image lost its finished-illustration provenance marker. The
renderer was corrected, and both original regression tests now pass without
changing their expectations. The focused repair run passes 28 tests. Existing JE-2000E/F and JE-3000C
English tests now also require the retained LCD illustration path and hash;
their image counts include this previously unmarked approved image. The
JE-2000E/F regression run passes 31 tests and the JE-3000C English run passes
10 tests. The final full-suite run passes 4,868 tests (22 skipped), with zero
failures/errors. The runner redirects only host-local PDF/AI fixture paths to
hash-verified originals; no test assertions are bypassed. Desktop/mobile
verification passes 36 table/viewport checks across 12 full-book navigations.
These are local results, not merge or publication acceptance.

## Phase 2 discovery

The eight baseline builds (JBP-2000B en/de/es/fr/it and JE-100C/JE-300D/JE-500A
en) pass. JBP-2000B's generated `symbol_meaning_<lang>` pages are not covered by
the default `symbols_*` selector. The build's CSV-page declaration map carries
LCD and troubleshooting roles but omits symbols, even though the source
adapter already accepts an explicit symbols declaration. Warranty pages also
use different source wrappers and projected names. Preserve those wrappers'
copy rather than substituting the portable-power-station warranty text.

A direct probe of all five staged JBP-2000B symbol pages succeeds with the
existing signal/icon adapters (ten component instances). The warranty adapter
also accepts en/de/es/it unchanged. French alone has three source-authored lead
paragraphs plus its local note, while the parser assumes one lead paragraph
plus one note. Extend the lead's ordered rich-text handling without merging,
rewriting or discarding the original paragraphs.

The three smaller products contain authored RST tables without semantic
classes. Their LCD explanations have three columns and sometimes intentionally
blank numbers; their screen-mode tables differ from the two-state, six-action
LCD component. They need declared, source-preserving shared variants, not
fabricated icon cells or a forced six-action layout. Specification tables can
use the existing specification component once explicitly declared; retain
multi-paragraph values and every table in each source section.

See the [LCD source audit](../reviews/eu_lcd_fallback_audit_2026-09.md) for the
separate 13-table asset findings and the JE-1000H numbering mismatch.

Historical immutable publications remain untouched. Source-code completion,
PR merge, immutable release creation and RTD acceptance are separate milestones.
The native-import-only admission work in PR #1339 does not cover all existing
RST/projection publications; phase 3 must close that separate boundary.


## Published acceptance — 2026-09-30

Engineering PRs [#1339](https://github.com/Bingboom/auto-manual/pull/1339),
[#1340](https://github.com/Bingboom/auto-manual/pull/1340),
[#1341](https://github.com/Bingboom/auto-manual/pull/1341) and
[#1342](https://github.com/Bingboom/auto-manual/pull/1342) were merged in order.
The final engineering main is `24f51176daa3e7a9369ce86e2c9ee4d8319b568e`.
[Hello-Docs #157](https://github.com/Bingboom/Hello-Docs/pull/157) published the
14 scoped manuals at main `335446d39242bf6cbc6b8cfeb57dd0f0c11fac07`.
[RTD latest build 34853738](https://app.readthedocs.org/projects/ht-doc/builds/34853738/)
succeeded at that exact commit; the persistent publish branch was retained.

Acceptance covered all 14 live bodies/component sequences and image references,
217 unique images (bytes or decoded pixels when CDN encoding differed), shared
CSS and legacy aliases. All 28 live desktop/mobile cases passed with no manual
image decode failures or horizontal overflow after bounded network retries.
All 4,672 publication inventory files were verified; the other 50 target source
and assembled-route subtrees stayed byte-identical. The 60 converted raw table
blocks comprise 18 operation tables, 14 JBP-2000B blocks, and 28 smaller-product
tables. Warranty component counts are separate from these raw-table counts.
Local receipts are retained under `/tmp/eu-shared-rollout/release-final/`,
including `acceptance.json`, `live-verification.json`, `live-qa/qa.json`,
`converted-table-counts.json` and `preservation.json`.

The admission corpus acceptance covered 51 prepared and 10 native packages,
958 rejected component/chapter-removal mutations, and a real App artwork change
that remained rejected after candidate hashes were recomputed. See the
[prepared admission contract](prepared_component_admission.md) for applicability,
explicit debt and the next representative App/finished-panel migrations.

This release did not repair the audited JE-1000H LCD icon table. Follow-up
[#1343](https://github.com/Bingboom/auto-manual/pull/1343) binds the existing
attachments for all six locales and removes their text-only exceptions; its
local previews and tests do not constitute merge or RTD publication acceptance.
