# Web Publish locale queue contract

Web queue routing accepts an explicit `Lang` only with a matching single-language
`Build_family`: one configured language, `include_lang_in_output_path=true`,
and `queue_by_document_key=false`. For example, EU English and French use
separate `eu-en/en` and `eu-fr/fr` rows pointing at the same approved review ref.
The existing resolver still rejects region/language mismatches. Grouping stays
record-scoped, so equal model/market/version/ref cannot collapse these two rows.

Single-language families must supply `Lang`; a blank locale cannot silently
claim a verified single-language publication. Legacy blank-Lang whole-book Web
requests remain supported, with their existing evidence/metadata semantics.
Print `Publish` still requires blank Lang and whole-book output paths. Draft
routing is unchanged.

This repairs the queue boundary, not the deployment protocol. Existing language
projection and immutable release-evidence checks still decide whether metadata
may be marked `single`; queue acceptance alone is not proof. It does not enable
untranslated languages or override missing/drifted figure gates.

No workflow, source-table/schema, CLI or dependency changes are included. The
operator must still choose release versions and approve exact live queue writes.
The former build-time HTML_link writeback is retired (REV-07): the queue lane
records a pending registration only, and `web-publish-receipt.yml` writes
`HTML_link` after the publish PR merges and the deployment verifies — see
[web_publish_pipeline.md](web_publish_pipeline.md#41-receipt-timing-three-timestamps-kept-separate).

Validation: `tests.test_web_publish_locale_routing` exercises real EU configs,
action aliases, language/region conflicts, unsafe shared paths and grouping,
blank-locale behavior, and unchanged Print restrictions. Run it with existing
queue/release-evidence regressions, the full unit suite and fixture build checks.
Manual Operations umbrella [#1103](https://github.com/Bingboom/auto-manual/pull/1103)
remains Draft until its actual online acceptance exits are satisfied.
