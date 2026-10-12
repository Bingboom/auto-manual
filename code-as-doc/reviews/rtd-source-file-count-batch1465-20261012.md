# Frozen-source file-count capacity for batch 1465

Status: active

The normal four-model Web publication candidate contains 10,043 frozen input
files and 1,122,025,832 bytes. The source inventory includes the preserved
self-contained releases and their assembled Web copies. Its count previously
shared the 10,000-file served-output/network limit and therefore rejected this
approved candidate, even though it fits the existing 1152 MiB source budget.
Publishing one model at a time did not resolve the aggregate count: JBP-2000B
alone reached 10,002 files against the earlier baseline, while JE-100C alone
reached 9,990 and was deployed through Hello-Docs PR #212.

The operator authorized “这个上限 至少得翻倍去调” on 2026-10-12. MA-287
records that grant. Frozen sources now have a separate `MAX_SOURCE_FILES =
20000`; the default inventory, selected routes, served receipt inventory and
online dependency traversal continue to use `MAX_FILES = 10000`. The source
1152 MiB, output/network 512 MiB, single-file 32 MiB, timeout, path, symlink,
hash and source/asset provenance guards are unchanged. No manual text or
artwork is removed, and no production callback is suppressed to fit capacity.

Deployment receipts were introduced by [PR #1127](https://github.com/Bingboom/auto-manual/pull/1127)
to bind frozen source and rendered output to the actual served bytes. The
original implementation bounded inventory and network work; that PR does not
document a capacity calculation for the specific 10,000-file threshold.

## Verification

- Before the change, `source_fingerprint` on the preserved normal candidate
  reproduced `Deployment inventory exceeds safety limits`; the existing
  receipt/throttle tests passed (40 tests).
- Ruff and the targeted receipt/throttle/portal tests pass (47 tests).
- Full local `python -m unittest` passes (5,381 tests, 42 skipped). It uses a
  canonical macOS TMPDIR and the test permissions required for localhost and
  self-cleaning home-directory fixtures; no assertion or unrelated production
  code was changed to resolve those environment failures.
- The new regression fits the source count exactly above the smaller output
  limit, rejects one additional source file, and proves that served receipt
  emission and online receipt-inventory verification still reject the smaller
  output/network limit.
- Maintainability guardrails, 2,777 documentation links (zero broken), and
  the fixture `build.py check` pass. Strict aggregate Sphinx with
  `myst_parser,tools.rtd.portal` passes on the retained 10,043-file candidate;
  its deployment receipt inventories 2,831 served files and 416,274,467 bytes,
  within the unchanged output limits.
- Every CI check must succeed before merging the engineering PR. The remaining
  publications use
  ordinary generated `docs/publish/**`-only PRs after normal mirror sync.

Each model is accepted only after the actual RTD commit, canonical/alias pages,
all referenced file hashes, and desktop/mobile rendering are read back. The
primary checkout, previous candidates, sealed releases and unrelated targets
are retained.
