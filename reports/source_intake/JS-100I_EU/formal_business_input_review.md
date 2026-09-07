# JS-100I_EU deferred online-normalization audit

Status: read-only historical gap audit retained for possible future data
normalization. It is **not** a release gate, approval request, or executable
write plan for the current V2.0 Web release.

The current release is Git-only: frozen structured input, MyST source, CSS and
13 hash-bound images are assembled into Hello-Docs `docs/publish/**`, then
Read the Docs builds that committed snapshot. No online Bitable write, build
row, queue dispatch, or published-link writeback is required or authorized in
this batch.

## Read-only findings

The earlier audit observed that the business Base already had the JS-100I
product identity and EU region identity but no target-specific Document_key,
specification, note, asset, or queue records. Those empty association fields do
not block the Git-only publishing route.

The companion
[`formal_business_input_plan.json`](formal_business_input_plan.json) preserves
the exact additive candidates that were derived during that audit so later work
does not need to reconstruct them. Its phases are disabled and deferred. A
future operator must treat that JSON as review evidence only and start a new
live preflight before authorizing any write.

## Source evidence retained

- Published revision: `V2.0-2026-04-01`; English body physical pages 4–12.
- Published PDF SHA-256:
  `cec27af653d9f5da11d641e2431ddc0b71ced186bbadfd9594fa8cd9c96e1596`.
- PDF-compatible Illustrator master: `371JNuMVqZ.ai`, 10 pages; SHA-256
  `5d7ded6ba7810505cfb4c91b128a71cbef16a0e11aae720cdbd887559224b96a`.
- Asset recipe SHA-256:
  `45755c66d4d98ec356d120b5dd14a535b9633c17191e90de0285fd1bb8910c14`.
- Deterministic asset package replay: 33 artifacts; 13/13 semantic exports
  byte-identical to the committed Web assets.

The semantic crops intentionally preserve English in-figure annotations; they
are localized full images, not textless derivatives.

## Explicit boundary

For the current publication batch:

- do not create a Document_key;
- do not write specification, note, asset, or build-queue tables;
- do not change online field options;
- do not dispatch the queue;
- do not write a production link back to a Base field.

Any future online normalization is a separate, newly authorized task with fresh
live reads and same-record readback. It must not be inferred from this report or
from the successful Git/Read the Docs release.
