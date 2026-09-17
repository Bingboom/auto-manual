# Manual operations follow-up debt

Status: open follow-up after [#1103](https://github.com/Bingboom/auto-manual/pull/1103).
Owner: 夏冰. Updated: 2026-09-14 UTC.

The #1103 operating checklist is merged at
`c1ee9992b6107a78b9f3e79e84d9a88cc5494812`. This file records only work that
the operator explicitly deferred; it does not reopen #1103 or turn deferred
verification into a passed check.

## 1. Remaining deployed-resource verification

The accepted closeout has actual HTTP 200 and strict hash evidence for all 23
canonical manual pages and 608 of 709 recursively referenced resources. The
remaining 101 resources were explicitly deferred to the later visual/content
acceptance. Of those 101, 98 are byte-identical to the preceding deployment;
the changed paths are the portal home page and two JE-500A images:

- `index.html`
- `_static/manual-assets/JE-500A/EU/en/md/assets/ir/122991a64cd306c82e70b0279024fa0bcad517e9fe0bfd8a30d6a81f0c46de99/lcd_map.png`
- `_static/manual-assets/JE-500A/EU/en/md/assets/ir/749ca081dde5bfee3d3ac2dfc811f3e4078a11380c1cdc908bd832c7d9ae47bf/overview.png`

The full queue, frozen-output SHA-256 values and prior-byte comparison are in
[`manual_operations_followup_pending_resources.json`](manual_operations_followup_pending_resources.json).
The frozen source and publication identities remain:

- engineering #1103 merge: `c1ee9992b6107a78b9f3e79e84d9a88cc5494812`
- Hello-Docs #73 release: `d7ef906f139b6aa1479280ee04228f5cf5feb230`
- release RTD build: `34539682`
- final mirrored runtime: `0aee1bce717ef4b674dcd7c14e36443492dc2fd4`
- final runtime RTD build: `34539775`
- frozen `docs/publish` tree: `070bf2fd5fc7a2fe64c5f8f35ec26f9217c25a9f`

Resume only after the client can access RTD normally. Do not switch proxies or
IPs to evade the Cloudflare challenge. Fetch the current deployment receipt,
require the same frozen-source fingerprint, then verify only the 101 queued
paths. A later build may legitimately produce a new receipt; in that case
first prove that its `docs/publish` tree still equals the frozen tree above.
Record failures and retries rather than deleting them. A successful build,
local Sphinx output or image similarity does not replace exact served-byte
verification.

Exit: every queued path has an HTTP 200 response matching a newly fetched
deployment receipt, and that receipt agrees with the recorded frozen-output
hash, or the operator records a new explicit acceptance decision for the exact
remainder.
Keep the already verified 608-resource evidence; do not repeat the prior PDF or
content audit.

## 2. Manual visual/content acceptance

The operator chose to perform the lower-cost visual/content acceptance later.
Review the published manuals against the existing designated list and approved
source evidence. Record each accepted model/language/version and concrete
finding. Route a correction through a reviewed source PR and a scoped
Hello-Docs `docs/publish/**` release; never edit the frozen business snapshot
or publication metadata as a substitute for fixing the source.

This acceptance must not be inferred from green CI, Sphinx success, page count,
the 23 canonical HTTP responses or the 608 resource hashes. Those prove build
and deployment properties, not human content or visual approval.

Exit: 夏冰 records the reviewed scope and outcome. Unknown or unreviewed
languages remain `user-deferred` or `needs_review` rather than passed.

## 3. Feedback response SLA

The active operating agreement is GitHub Issues, owner 夏冰, checked after
each publication. A response SLA was deliberately left undecided. Choose and
document it only when the operator is ready; do not reintroduce the earlier
unapproved one-working-day proposal.

Exit: an explicit operator decision is recorded in the owning operations guide
and referenced from the release/feedback procedure.

## 4. Per-manual structured governance

Online extraction of manual body/structured content was excluded from the
publication prerequisite. It remains follow-up work after human acceptance:
process one reviewed manual at a time through the existing skeleton, product
binding, source-table approval and readback rules. Returned translation does
not equal approved or published language coverage.

Exit: each later ingest has its own staged candidates, explicit source-table
authorization, same-record readback and release evidence. Do not batch-create
body rows merely to close this debt record.

## 5. Stale #1110 PR metadata

[#1110](https://github.com/Bingboom/auto-manual/pull/1110) remains Open in
GitHub, but it must not be merged again. Its head
`557f9b3a227d0449d23536136681b2d8b8f72fc1` and the mainline commit
`9a015afdbee91786feecaf44567a6ad4d7a0c86e` have the identical Git tree
`6197054f47f49380aacca4e5747758e24cfd47a5`. #1125 subsequently activated
the feedback configuration, and #1103 recorded the operating closure.

The remaining action is administrative: after rechecking those three SHAs,
close #1110 as superseded/already integrated and link the mainline commit.
Do not use mergeability or the old 17 green checks as a reason to create a
duplicate commit.

## Other-computer handoff

1. Check out this Draft PR and confirm its base contains #1103 merge
   `c1ee9992b6107a78b9f3e79e84d9a88cc5494812`.
2. Read the [accepted closeout](manual_operations_closeout_20260913.md), the
   [exact deferral](manual_operations_evidence/20260913/final-acceptance-deferral.json)
   and the pending-resource JSON before making any request or write.
3. Work only on the debt item being closed. Preserve the other items and their
   status; do not duplicate the two publication-metadata rows or Issue #1126
   reply/closure.
4. Update this file with durable evidence and close only the completed item.
   Keep the PR Draft while it is serving as a cross-machine handoff.

The two existing publication records are `recvv9cTEvtUF4` (EN) and
`recvv9cTEvtX8l` (FR). Both were already read back with null workflow/build
triggers. Issue #1126 is already replied to and closed. These actions are not
part of the debt and must not be repeated.
