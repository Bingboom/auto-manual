# OPS-04a Local Web Version Seal

## Scope

OPS-04a hardens the local `Web Publish` queue path. It does not change CI
workflows, live-table behavior, portal behavior, authentication, withdrawal,
or backfill semantics.

## Seal contract

The first successful build of a target version creates this immutable payload:

```text
versions/<version>/
├── web/
│   ├── md/
│   │   ├── <manual>.md
│   │   ├── conf.py
│   │   ├── index.md
│   │   └── assets/**
│   └── html/**
└── web_publish_meta.json
```

Every file under `web/` is compared by relative path and SHA-256. An exact
same-version retry is a no-op. Missing, added, or changed Markdown, sidecar,
asset, or HTML files fail the retry without changing the sealed version.
First creation is assembled and verified in a sibling temporary directory,
then renamed into place so an interrupted copy cannot expose a partial seal.

Sphinx's `html/.doctrees/` directory is deliberately outside the payload. It
is an incremental-build cache containing local pickle state, not deployable
HTML or an asset. No other HTML path is excluded.

`versions/<version>/web_publish_meta.json` is immutable and sits outside the
asset tree so metadata creation cannot make an otherwise identical asset retry
look different. Its first-seal `built_at` is retained on retries. The mutable
`latest/web/publish_meta.json` pointer is replaced atomically only after the
version assets and version metadata are sealed.

Symlinks at payload entries, the version directory, and the latest Web metadata
directory fail closed before copying or metadata reads. `queue_record_ids` is
immutable release provenance: a legal same-version retry reuses the same queue
row set; a different row set must use a new version.

## Retry and failure ordering

The Web `check`, `md`, and `html` commands receive `SOURCE_DATE_EPOCH` from the
review input Git commit. If a retry produces different sealed
content, the existing version and existing latest pointer remain unchanged.
A new version may be fully sealed before a latest-pointer failure; leaving that
unreferenced seal is safe and lets the next retry finish idempotently.

The queue writes terminal `SUCCESS` only after metadata sealing and latest
pointer replacement succeed. A failure before that point follows the existing
terminal failure writeback path.

## Focused verification

The dedicated tests cover exact no-op retries, Markdown/asset/HTML drift,
copy-failure cleanup, first-seal metadata preservation, immutable metadata
drift, latest-pointer failure ordering, new-version advancement, `.doctrees`
exclusion, stable `SOURCE_DATE_EPOCH`, and queue success ordering.

Two real Sphinx HTML builds were also run from the same already-materialized
source at Git ref `b541689ac5b2a704c7b47041370101e979c3776f`, with
`SOURCE_DATE_EPOCH=1789283792` and the Web presentation profile. The 260-file
shipped inventories (excluding only `.doctrees`) were byte-identical. This is
renderer determinism evidence, not an end-to-end queue retry proof.

Two attempted end-to-end `build.py md` / `html` reproductions did not reach
Sphinx: the current review inputs referenced unresolved `lcd_icons` / `symbols`
attachments. They are recorded as an input-fixture blocker and are not counted
as passing evidence. Queue ordering, exact retry, drift, and failure behavior
remain covered by the dedicated unit tests above.
