# Frozen publication language navigation

OPS-03a groups the explicit RTD index publications into one card per model and
market. The default remains EU; EU and UK select the same EU publication set.
It reads sibling `sources/web/**/publish_meta.json` from the frozen publish tree,
not live tables, and does not copy or rewrite manual bodies as a data store.
Stored metadata validation reuses the OPS-02 shared contract reader rather than
introducing another route/schema parser in the portal.

Only a locale route with matching target v2 metadata and `language_scope=single`
enables a language option. Legacy/unknown scope retains **Current publication**;
the historical `lang=en` slot is not proof of English-only text. Missing metadata
for a locale route, conflicting defaults, duplicate languages and unsafe paths
fail closed. Planned languages without a verified publication remain disabled.

The language picker preserves model and market edition and opens the selected
manual from its beginning. No current chapter/query/fragment is carried across.
Single-language manual pages receive the same picker and explicit HTML language;
the configured Hebrew/Arabic options also select RTL content direction when a
real single-language publication is supplied. This is presentation support,
not a claim that those translations or renderer source-language bindings exist.

The twelve option labels are presentation configuration. Do not infer a specific
Portuguese regional translation from the generic planned label; confirm the
returned locale and content-source binding before a real Portuguese release.
The homepage's no-JavaScript list retains every explicit publication link.
Legacy manual pages receive no new injected navigation, preserving their output.

Validation includes real Sphinx builds, grouped legacy/single metadata tests,
unchanged source bytes and an in-app-browser QA fixture (not production data):
one EUUK card, English/French enabled, other ten disabled, homepage→French→English
and anchored English→French without the old hash. At 390 px, document width and
scroll width both measured 390 px. A browser verification on fixture content
does not close real RTD/manual-language acceptance in umbrella
[#1103](https://github.com/Bingboom/auto-manual/pull/1103).

The existing 21-publication frozen corpus was rebuilt separately: 66 HTML pages,
only index.html changed versus the prior deployed-portal baseline, and all 65
other HTML pages were byte-identical. No live corpus migration was performed.
