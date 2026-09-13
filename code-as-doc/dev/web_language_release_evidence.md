# Web language release evidence (OPS-01b2)

## Discovery and implementation boundary

Baseline: main `51791920bf5d9326f13b54c26af03cf2c1caf7d5`. OPS-01b1
provides canonical explicit-language Web RST. This slice binds that projection
to immutable release artifacts and publication metadata: the queue previously
staged only md/html, and metadata could self-declare `single` without evidence.
Engineering code remains in auto-manual; business publication remains in
Hello-Docs. No workflow, live Base, public build.py flag, dependency, source
schema, approved asset or reviewed content changes are included.

## Evidence contract

Review parameter synchronization still precedes the Web build. If canonical
RST is already a Web language projection, sync reads the same build's complete
`web/source/rst` bundle instead: its index and source-page hashes must match
the projection manifest. Missing, stale or unsafe source files fail rather
than silently falling back. This keeps merged review-page names available to
the existing sync plan; it neither skips review sync nor writes a Web projection
back as the merged review source.

The queue captures the canonical `bundle_manifest.json` after each successful
`check`, `md`, and `html` action. Capture validates `web-language-bundle/v1`,
target identity, exact ordered index includes, page hashes and the transitive
include closure, including non-RST text includes. Escapes and symlinks fail.
The three actions must occur in order and have matching source fingerprints;
sealing rechecks the final source to reject changes after the HTML capture.

The new immutable version contains:

```text
<model>/<region>/<selected-lang>/versions/<version>/web/
  md/...
  html/...
  evidence/
    language_projection_receipt.json
    projection_bundle_manifest.json
```

The shared release-path resolver receives the actual selected language. A
shared EN/FR config with `lang=fr` must not stage under its default EN directory.
No per-language config clone is needed. Non-Web/default path behavior remains.

Receipt schema `auto-manual-web-language-release-evidence/v1` binds model,
region, canonical language, version and Git_ref. It contains the projection
manifest path/SHA-256, path-sorted canonical-source inventory, the three action
fingerprints, and complete staged Markdown/HTML inventories with sizes and
SHA-256 values. The Markdown inventory names its entry manual. Fingerprints
must match the manifest and source inventory, not merely each other. The
projection's pages must match their canonical inventory rows. There are no
timestamps or absolute source paths in the receipt.

The candidate receives md/html and both evidence files before immutable
promotion. Exact artifact retries remain no-ops; changed bytes cannot replace
an existing sealed version. Do not backfill evidence into historical versions:
produce a new version from approved inputs.

## Independent verification boundaries

1. Staging verifies capture identity against the requested target before
   promoting its candidate.
2. The metadata writer verifies same-version artifact/evidence paths and actual
   md/html inventories before adding `language_scope=single`,
   `language_projection_evidence_path` and
   `language_projection_evidence_sha256`. Explicit language and evidence must
   be supplied together; a missing half fails rather than downgrading to legacy.
3. Fresh publish assembly independently verifies metadata identity, receipt
   hash and md/html files before accepting the version.
4. Stored sources carry both evidence files under their `md/evidence/` plus the
   receipt path/hash in `publish_meta.json`. Stored reuse and the portal catalog
   call the same verifier against retained Markdown/assets and release identity.
   Only the two prescribed evidence files are allowed; they cannot hide extra
   untracked Markdown. The separately validated metadata is not part of the
   pre-metadata Markdown inventory.

Stored sources do **not** duplicate the verification HTML tree. Their HTML
inventory is historical sealed evidence; stored validation does not claim to
have revalidated absent HTML bytes. Fresh verification requires HTML. Missing
scope/no explicit-language evidence remains `legacy_unspecified`; setting
`single` without a valid receipt fails. `lang=en` alone proves neither content
scope nor translation completion.

## Safety net and acceptance limits

Validation proceeds through Ruff, focused positive/negative tests, parent
review, final-tree full unit suite, utility types, maintainability/doc checks,
fixture builds and frozen legacy corpus parity. Regression tests must retain
real valid receipts for positive single-language assembly/portal cases, and
exercise mismatched identities, missing captures, source/output drift and
stored tampering. Do not weaken quality gates or regenerate parity baselines.

Receipts are consistency evidence, not signed attestations. Git_ref binds the
queue's reference string; it is not a cryptographic proof of a toolchain commit.
They do not prove translation accuracy, correct visuals, warning-free layout,
content approval, an RTD deployed revision or correct official-link writeback.
The OPS-01 exit still requires real approved independent-language publication;
umbrella [#1103](https://github.com/Bingboom/auto-manual/pull/1103) stays Draft
until all operational exits are satisfied.

Rollback is a normal reviewed code PR, never deletion or rewriting of release
history. Failures preserve previous immutable bytes; do not label this slice as
complete Manual Operations or as authority for live-table writes.
