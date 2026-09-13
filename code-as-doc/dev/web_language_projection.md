# Frozen Web language projection

OPS-01a provides `tools.web_language_bundle.split_web_bundle` as an internal
producer for a single-language `MaterializedBundle`. It reuses the source
projection from [PR #1079](https://github.com/Bingboom/auto-manual/pull/1079)
without importing its ZIP, PDF or browser runtime. That PR remains independent.

The helper uses explicit page language and declared `lang_blocks`, before HTML
rendering. Missing translations, unknown identity, escaping paths, symlinks,
foreign transitive includes and colliding projected paths fail closed. Shared
assets are copied byte-for-byte; input pages and the frozen bundle are not edited.
An implicit foreign preface block cannot be relabeled as a translated page.

The new destination must be outside the source and must not exist. Projected
index order and hashes are recorded in its bundle manifest. Only unreferenced
RST copies in the newly created derivative are pruned. This is not automatic
translation or semantic language detection of untagged text.

This slice does **not** wire the publish queue, change public `build.py` flags,
publish to RTD or demonstrate complete OPS-01 acceptance. The next integration
must consume this helper with locale-safe release identity and validate real
independent-language pages before checking off the overall milestone.

Validation: `python3 -m unittest tests.test_web_language_bundle`.
