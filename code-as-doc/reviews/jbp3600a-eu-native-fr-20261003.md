# JBP-3600A EU native intake: French first review batch

Status: active

English release565c52a2 is immutable and already published. The [native intake package](../../manual_sources/JBP-3600A/EU/native-0924/README.md) supplies French r4 for independent review; remaining seven locales are incomplete. No multilingual publication is authorized.

French copy is sourced from native pages2,15–22,79, including visually checked outlined safety, storage and warranty exclusions. Native source wording, technical values and legal identity remain intact; page79 remains English because the original is English. Eighteen neutral assets retain exact English bytes. Three French label-bearing panels and a transparent native ×5 inline badge remain candidate exceptions.

Independent reviews in `/tmp/jbp-independent-acceptance/fr-20261003/acceptance.md` and `/tmp/jbp-independent-acceptance/fr-r2-20261003/acceptance.md` requested changes. The second review closed FR-001/002 and added FR-003; r4 awaits independent recheck:

| Finding | Cause and correction | Baseline consequence |
| --- | --- | --- |
| FR-001: specifications missing from TOC | Shared frozen MyST replay skipped styled top-level headings. It now promotes `hb-h1-pill` headings while keeping component headings intact. | Published English Markdown already had the independent heading; no source-language workaround. |
| FR-002: locking contrast/mobile size | English target binding used pale fill and overlay CSS allowed8px. Existing reference component now supports measured foreground color; shared JBP binding uses `#434345`/white and opt-in source-foreground badges have14px minimum type. | English revision remains a candidate; the released baseline is not overwritten or reapproved. |
| FR-003: sticky mobile header obscures anchor headings | Shared responsive CSS clears both Furo header and back-to-top control. Direct LCD/overview/connections links and actual mobile TOC click place headings around96px below the48px header; desktop remains24px. | Shared stylesheet revision recorded separately from the structural trial; proposed, not baseline-approved. |

The French r4 trial has9 field differences representing5 review decisions:3 artwork hashes,1 inline-icon addition,4 badge fill/foreground fields,1 contract hash. The9-difference report must not be summarized as zero structural differences. The trial does not compare stylesheet bytes or all renderer behavior; shared FR-003 CSS is a separately recorded change. Applicability trial against the English profile has no component issues; fresh admission rejects pending source review, and FR applicability is not enrolled.

The [review ledger](../../manual_sources/JBP-3600A/EU/native-0924/review/fr-r4/review-ledger.json) binds IR/native-copy identities, source mappings, values/warnings/legal checks, screenshots and test status. The [HTML manifest](../../manual_sources/JBP-3600A/EU/native-0924/review/fr-r4/html-manifest.json) and [IR package manifest](../../manual_sources/JBP-3600A/EU/native-0924/review/fr-r4/package-manifest.json) bind the same fixed build. Local preview: [French r4](http://127.0.0.1:56059/fr-r4/manual_jbp3600a_eu_fr.html); [English shared-binding revision](http://127.0.0.1:56059/en-web-r4/manual_jbp3600a_eu.html).

After FR-001/002 shared logic changes the full suite passed5075 tests/35 skipped (762.048s). The final source-badge marker/sizing refinement then passed36 targeted tests. FR-003 changes only CSS and was verified in French/English browser at390px and1440px, without rerunning the full suite. Ruff, maintainability, doc links and strict French/English Sphinx passed. Final French cold replay is byte-identical; all29 package entries and60 HTML entries match the sealed manifests. US regression uses committed `tests/fixtures/phase2` explicitly because this isolated tree has no live phase2 snapshot. No Feishu writes or production changes were made.
