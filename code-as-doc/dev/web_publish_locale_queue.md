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

## Output naming on a locale route

The Markdown stem is what puts a manual at its URL, so a locale route inherits a
hard constraint from whatever is already published there. Republishing an
existing book under a new stem moves the canonical page and leaves the old URL
404: `publish_branch_assembly` writes alias redirects only for the legacy
`<MODEL>/<REGION>/md` route and the site root, never inside a locale route.
Sibling locales carry the opposite constraint — two manuals sharing one stem are
rejected as a duplicate RTD short alias.

`JE-1000F / US` therefore pins `manual_je1000f_us` on its English route through
`md_output` in [`configs/config.us-en.yaml`](../../configs/config.us-en.yaml),
while French and Spanish keep the `_fr` / `_es` suffixes inherited from
[`configs/config-bases/us-single-language-base.yaml`](../../configs/config-bases/us-single-language-base.yaml).
`md_output` overrides the Markdown name only, so the Word and PDF artefacts
still carry `_en` and stay distinct from their siblings on disk. `JBP-2000B / EU`
is the live precedent for the shape. A line with no published URL to protect
needs none of this and should take the base `_{lang_slug}` names throughout.

One explicit portal default per product/market needs no per-target flag either.
Release metadata never emits `legacy_default`; `stage_web_target` inherits it
from the stored payload for the same `(model, region, lang)`, so republishing
the existing English route in place keeps the single default, and
`assign_legacy_defaults` writes the new locale siblings as explicit
non-defaults.

Validation: `tests.test_web_publish_locale_routing` exercises real EU and US
configs, action aliases, language/region conflicts, unsafe shared paths and
grouping, blank-locale behavior, single-language output naming, and unchanged
Print restrictions. `tests.test_publish_branch_assembly` replays the US locale
round end to end — inherited default, preserved English URL, and the cost of
renaming a default stem. Run them with existing
queue/release-evidence regressions, the full unit suite and fixture build checks.
Manual Operations umbrella [#1103](https://github.com/Bingboom/auto-manual/pull/1103)
remains Draft until its actual online acceptance exits are satisfied.
