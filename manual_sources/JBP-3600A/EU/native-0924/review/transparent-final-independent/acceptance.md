# JBP-3600A final transparent-symbol delta acceptance

Result: PASS for candidate content/layout delta, reviewed 2026-10-03.
Source commit: 44b6ce6101141681a6cf75c9fdfef05b8aef93b0.

This closes the final artwork revision for all eight added languages and English. Earlier full native-source audits remain applicable: the independent comparison proves Markdown differs only by the two intended asset hashes. This is not operator baseline approval, source-erratum approval, locale enrollment, merge or RTD publication.

## Independent checks

Package manifest hashes, actual served HTML and IR hashes, and every rendered image byte identity passed. Warning and battery WEEE are the only replaced images; equipment WEEE retains its bottom bar, battery WEEE has no bottom bar. JBP ×5 remains unchanged; HTE152 ×8 was not substituted. French CSS alone changes to the common reviewed version.

All nine pages were inspected in an actual browser at 390px and 1440px. Document widths equal viewport widths; images decode successfully. The 36 settled screenshots named LANGUAGE-WIDTH-symbol_*.png and four sheet-* contact sheets show no residual background patch or cropping. French warranty heading begins at 100.38px below the 48px header; title and body do not overlap. Initial LANGUAGE-mobile.png / LANGUAGE-desktop.png captures were taken before scroll settlement and are excluded from acceptance evidence.

| Revision | Package files verified | Images verified | HTML SHA256 |
| --- | ---: | ---: | --- |
| en-r6 | 27 | 21 | c6e447a16abc05b1a2f334e441dab1277b214992c008f173c5d27a272259abd0 |
| fr-r5 | 28 | 22 | dce81595d558e9975e474ed46e476222872256b99900daee931ea8e0c6ba5b49 |
| es-r3 | 28 | 22 | 7704b68d7877e56fb498bc803530fff7472ec664bf490cdff12868b85a9edd59 |
| de-r2 | 28 | 22 | 2a816bb562c1ee5fa96bd8706fdbb1f88f81ce81f46330fc4f4f4229429ce169 |
| it-r2 | 28 | 22 | 3d8079560ccff5242e035e3954250d13afda7c552b897e540bdb3297813e18e6 |
| uk-r2 | 28 | 22 | 916b2f5d5d8c08d6da4a7c87d64b6ffaa5848f468614e52e4b1b8966bbd6a9ab |
| pt-r2 | 28 | 22 | f09854b6c97968dcc1d92db920a736aaf22d516a4a9fbe85f54a39dc54134f36 |
| nl-r2 | 28 | 22 | e4dd3261ba1874fa7d74d907b7dfc0cfdf991f428ff3bca256568693098bd202 |
| pl-r2 | 28 | 22 | 9c842505cad6297029bdec56c584ccb010cc8e7c1229995c8bab32dc12a81677 |

## Publication boundary

Eight-language candidate content/layout acceptance is complete. Publishing still requires final English baseline operator confirmation, source-anomaly decisions (including German icon wording and Italian source differences), locale applicability/fresh admission, main synchronization, and applicable merge/publish authorization. No baseline has been auto-approved. Evidence: checks.json, mobile-metrics.json, desktop-metrics.json, check_delta.py, settled screenshots and fr-warranty.png in this directory.
