# Frozen publication language navigation

Status: active

OPS-03a groups the explicit RTD index publications into one card per model and
market. The default remains EU; EU and UK select the same EU publication set.
It reads sibling `sources/web/**/publish_meta.json` from the frozen publish tree,
not live tables, and does not copy or rewrite manual bodies as a data store.
Stored metadata validation reuses the OPS-02 shared contract reader rather than
introducing another route/schema parser in the portal.

Only a locale route with matching target v2 metadata and `language_scope=single`
adds a language option. Legacy/unknown scope retains **Current publication**;
the historical `lang=en` slot is not proof of English-only text. Missing metadata
for a locale route, conflicting defaults, duplicate languages, a published
language without a display code and unsafe paths fail closed. The picker lists
only verified publications: planned or unverified languages are not shown, and
there are no disabled options or reasons. A single-language product therefore
shows one selected option; a legacy publication keeps **Current publication**
beside any verified single-language pages.

Option text is the language code from `settings.json` `language_display_codes`
(`en-US`, `fr-FR`, `es-ES`, `de-DE`, `it-IT`, `pt-BR`, `nl-NL`, `pl-PL`, `uk-UA`,
`zh-CN`, `zh-TW`, `ja-JP`, plus defaults `el-GR`, `he-IL`, `ar-SA`, `ko-KR`), used by
both the manual-page picker and the homepage “查看说明书” dialog. Codes are per language,
not per market: English is `en-US` in every market, EU/UK included. Page titles,
descriptions, `hreflang`, search languages and homepage card tags keep the native
names from `language_labels`.

The language picker preserves model and market edition and opens the selected
manual from its beginning. No current chapter/query/fragment is carried across.
Single-language manual pages receive the same picker and explicit HTML language;
the configured Hebrew/Arabic options also select RTL content direction when a
real single-language publication is supplied. This is presentation support,
not a claim that those translations or renderer source-language bindings exist.

Display codes are presentation configuration. Do not infer a specific
Portuguese regional translation from the `pt-BR` display code; confirm the
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

## Leading language label

On verified single-language pages, the locale switcher already identifies the active
language. The portal omits a plain leading paragraph only when its full text equals
the active language label (for example, `English` or `Français`). Other introductory
paragraphs, later occurrences and legacy mixed-language pages are preserved. This
is a render-time presentation change; frozen publication sources remain unchanged.

The portal sets the shared Sphinx site title to `说明书资料库`, including the
mobile header and desktop sidebar. Individual manual browser titles retain
their product, market and language metadata.
