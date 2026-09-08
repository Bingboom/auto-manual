# Web Publish OSS archive

## Discovery and scope

Baseline: current main `d1b12bf8`, plus the standalone consumer in PR #1079
(`92641b80`). This change depends on that PR; it does not merge it.

Web Publish builds a review snapshot in an isolated worktree, stages MyST and
HTML, writes queue success, and writes `auto-manual-web-publish/v1` metadata.
The worktree is removed afterwards. Archive packaging must happen before that
removal; upload must happen only after successful Web Publish metadata exists.
The metadata language field currently names the first configured language, so
it must not be used to slice a multilingual manual. Reuse the source-level
standalone language splitter against the frozen review snapshot instead.

User contract: Read the Docs is internal preview; OSS is archival storage;
IT owns external links and deployment. Archive success requires remote byte
verification, not an external domain. Never write OSS `latest/`. No live Base
schema changes, CI workflow edits, dependency manifest changes or print Publish
changes are included. Credentials stay outside the repository.

## Implementation plan and safety net

- [x] Stage standalone packages during Web Publish using its effective review
  worktree and data snapshot, before worktree cleanup.
- [x] Adapt package layout and validate source hashes and all local HTML links.
- [x] Add configured OSS adapter with immutable writes, exact-byte retries and
  read-back SHA-256 checks. Do not list buckets or change access permissions.
- [x] Trigger after successful Web Publish metadata; archive failures have a
  separate report and never turn an already successful publication into failure.
- [x] Test hook ordering, disabled mode, failed preparation, retries, version
  conflicts, broken links, traversal, symlinks and remote corruption.
- [x] Run Ruff, focused/full unittest, guardrails, docs links and build checks.

## Deployment and status

Implementation and local verification completed. The existing JE-1000F/US/2.3 archive
was uploaded manually via API; that is not proof of an automatic queue run.

## Configuration (per execution host)

The hook is opt-in. Read `AUTO_MANUAL_OSS_ARCHIVE_CONFIG`, or the local file
`~/.config/auto-manual/web-archive.json`. `AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off`
disables it explicitly. Missing default configuration leaves existing publishing
unchanged; an explicitly configured missing file produces a separate failure.

```json
{
  "enabled": true,
  "prefix": "便携/manuals",
  "credentials_file": "/private/operator/oss-credentials.json",
  "python": "/private/operator/oss-runtime/bin/python",
  "node": "node",
  "browser": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
}
```

The external Python runtime needs `oss2` plus the normal importable repository
source. The main project requirements are unchanged. `node_module_path` may
point to the Node modules directory containing Playwright when it is not on the
normal Node search path. The normal Web Publish interpreter builds packages.
Credentials JSON contains `access_key_id`, `access_key_secret`, `bucket`,
`region` and an HTTPS `endpoint`; keep it outside Git and owner-readable/writable
only (`0600` on Unix). Configuration is per host: this Mac's credentials do not
configure GitHub Actions or the Hello-Docs runner. No workflow or remote secret
was changed by this implementation.

## Lifecycle and archive contract

`queue_build_execution` prepares the package from the effective review worktree
and synchronized snapshot, before that worktree is removed. It reuses PR #1079's
source language projection and standalone consumer. Current toolbar languages
supported by that consumer are English, French and Spanish; other languages
produce a separate preparation failure until their UI contracts are added.
No language is inferred from the first-language metadata field or from HTML.

`queue_group_processing` calls `finish_web_archive` only after Web Publish
success writeback and metadata generation. Print Publish and draft paths do not
call it. This is the queue's successful build/publication handoff, not a promise
that a Read the Docs deployment or IT external link has completed.

The local version Web directory receives:

- `archive-package/`: portable site directory and manifest, kept for retries;
- `archive-preparation.json`: preparation status or sanitized error class;
- `oss-archive-result.json`: archived/failed status, path and checksum receipt.

A failed archive does not rewrite the successful queue result or live Base
fields. It is visible in the console and local report; operators must check the
archive report before claiming archive completion. No remote upload is attempted
when preparation failed. The SDK runs in a separate process so it is not a new
mandatory dependency for ordinary builds. SDK stderr and credential values are
never copied into reports.

The destination is `<prefix>/products/<model>/releases/<version>/<lang>/user-manual/`.
PDFs follow the supplied site's naming rule; source content and images are not
changed. First-phase private assets remain in each language package. A version
has one immutable manifest covering its full language set and region. A later
language addition or a different regional variant needs a new version or an
explicitly agreed distinct product identity; it may not overwrite that manifest.
No alias, public ACL, external URL, Base field or OSS `latest` is written.

`_archive-reservation.json` fixes the package identity before uploads, preventing
different concurrent packages from mixing. `_archive-complete.json` is written
last after reading every remote object and comparing its SHA-256. A partial
upload is not complete even if `index.html` is already visible. Identical retries
skip existing writes; any differing object or reservation blocks the upload.
Historical manually archived versions with a different manifest schema remain
untouched; the new adapter refuses to rewrite them.

## Retry without rendering or queue writes

Use the original metadata and staged MyST paths printed by Web Publish:

```bash
python -m tools.web_publish_archive \
  --metadata /absolute/path/to/version/web/archive-package/web-publish-metadata.json \
  --staged-md /absolute/path/to/version/web/md/manual.md
```

This invokes only the frozen package upload. It does not rebuild PDFs (whose
metadata may differ on a new render), trigger publication, write queue rows or
change `latest`. Missing preparation requires repairing/rebuilding locally;
missing upload credentials only requires configuring the host and retrying.

## Verification record

See the accompanying tests in `tests/test_web_oss_archive.py` and the existing
Web Publish queue suite. Live automatic queue execution is intentionally not
used as a test because it would mutate business-plane queue rows. The existing
JE-1000F archive can be read for parity without modifying its immutable version.

Local verification: targeted tests passed; real JE-1000F/US/en-fr-es package
preparation completed from the review snapshot. A read-only comparison of the
375 generated content/PDF/asset files with the existing OSS version matched
all hashes. US review-asis and JP auto build checks used the offline phase2
fixture and isolated staging roots. No live queue, Base or OSS version was
mutated during these implementation checks. The local host configuration is
enabled; other runners still require their own configuration and credentials.

Final local suite: 3,876 tests passed, 22 skipped; 20 focused archive/queue tests passed. Ruff, maintainability guardrails, 1,754 documentation links and both isolated build checks passed.
