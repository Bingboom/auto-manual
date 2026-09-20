# Frozen Web language projection

OPS-01a provides `tools.web_language_bundle.split_web_bundle` as an internal
producer for a single-language `MaterializedBundle`. OPS-01b1 connects that
producer to the existing Web presentation profile when the caller supplies an
explicit `--lang`: the complete configured-language source freezes under
`<target>/web/source/rst`, then the selected language atomically replaces the
canonical `<target>/rst` bundle consumed by `check`, Markdown and HTML. The
no-`--lang` full-book path and every non-Web profile retain their existing
materialization path.

The complete source keeps the requested language as its target identity and
substitution locale while materializing all configured page languages. When a
language-scoped Web build falls back to a shared review root, the source overlay
therefore copies the complete review bundle, including `cover-en.rst`, before
projection. The canonical derivative still contains only the selected Web
pages; it does not expose the complete source as the artifact input.

This integration reuses the source projection from
[PR #1079](https://github.com/Bingboom/auto-manual/pull/1079) without importing
its ZIP, PDF or browser runtime. That PR remains independent.

The helper uses explicit page language and declared `lang_blocks`, before HTML
rendering. Missing translations, unknown identity, escaping paths, symlinks,
foreign transitive includes and colliding projected paths fail closed. Shared
assets are copied byte-for-byte; input pages and the frozen bundle are not edited.
An implicit foreign preface block cannot be relabeled as a translated page.

Some document formats deliberately retain a mixed-language page. JE-1000F US
is the live case: the en/fr/es document manifests keep the trilingual preface
for IDML/Word/PDF, while each config declares
`build.web_language_block_pages: {00_preface.rst: en}`. The Web source
materializer adds that declaration only to its frozen bundle metadata, so the
single-language route can project the page without changing document output.

The low-level split destination must be new and outside the source. The
canonical integration validates in a fresh sibling directory, rejects symbolic
link destinations, and swaps only after validation succeeds. Wrapper-index
writes use an atomic replace; a failed swap restores the previous canonical
bundle, and a failed rollback preserves the previous bundle as a reported
backup instead of deleting its only copy.

Projected index order and source hashes are recorded in
`bundle_manifest.json` with schema `web-language-bundle/v1`. Unreferenced RST
copies are pruned, and the frozen asset-usage manifest is fail-closed validated
then reduced to the retained RST closure so HTML asset copying cannot re-enter a
foreign or removed source page. This is not automatic translation or semantic
language detection of untagged text.

OPS-01b2 adds [release evidence binding](web_language_release_evidence.md): an
explicit-language Web queue build captures this canonical manifest and its
include closure after each successful `check`, `md`, and `html` action. All
three captures must agree before the new immutable version is staged. This
does not change public `build.py` flags or demonstrate complete OPS-01 acceptance;
real independent-language publication and content approval remain separate.

Review pre-sync consumes the complete frozen runtime source when canonical RST
is a projection, validating its index and page hashes against the projection
manifest. It does not look for merged review page names in the single-language
derivative, skip parameter sync, or copy the projected manual back into review.

Targeted validation:

```bash
python3 -m unittest \
  tests.test_build_docs_export \
  tests.test_build_docs_review_compat \
  tests.test_web_language_bundle \
  tests.test_target_resolution
```
