# Locale-safe Web publication identity

OPS-02 separates the routing identity `(model, region, lang)` from language
content verification. Engineering implementation belongs to auto-manual;
business publication changes remain scoped to Hello-Docs `docs/publish/**`.

## Stored source contract

The existing `auto-manual-web-publish/v1` input remains readable. Identity must
match its `latest/web/publish_meta.json` coordinates and its versioned md/html
paths. Version directory normalization reuses the release contract. Invalid
types, duplicate identities, missing files, symlinks and path escapes fail closed.

Stored target v2 uses `model/region/lang/md`. Old target v1 sources are migrated
inside the candidate only. Their `model/region/md` links and root short aliases
remain redirect pages, not duplicated manual bodies. A migrated legacy default
is retained; multiple new locales require one explicitly designated default.
An explicit non-default is never silently promoted.

`language_scope=single` requires a verified
[language projection receipt](web_language_release_evidence.md), not just a
producer declaration. Both fresh assembly and stored-source reuse verify the
receipt against target/release identity and retained artifacts. Missing scope
and all legacy migrations are `legacy_unspecified`: `lang=en` alone does **not**
prove English-only content. The grouped portal must not enable independent
language options or count translated coverage from legacy scope. Existing
sealed releases are not backfilled; build a new version to add evidence.

## Safety and remaining integration

Assembly validates an isolated candidate before replacing the output. Failure
before promotion preserves the old tree; failed promotion attempts restoration.
If restoration also fails, the error identifies a retained sibling backup;
operators must recover that copy before retrying. Temporary candidate cleanup
never deletes that last recoverable copy.
Repository roots and overlapping release/output trees are rejected. Existing
targets absent from a batch remain present; absence is not a withdrawal command.

The locale contract and evidence binding do not modify the queue workflow,
publish a real multi-language corpus, or verify formal link writeback.
OPS-03 portal grouping and OPS-01 source/evidence support are engineering
capabilities; live multi-language migration still needs approved content and
actual RTD publication acceptance.
The umbrella [#1103](https://github.com/Bingboom/auto-manual/pull/1103) remains Draft.

Validation: targeted publish assembly / RTD tests include a real Sphinx `-W`
build, old aliases, multi-locale coexistence and negative identity/path cases.
Real RTD migration and the complete OPS-02 exit remain separate acceptance.
