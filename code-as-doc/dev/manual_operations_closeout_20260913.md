# Manual operations accepted closeout — 2026-09-13

**The operator accepted closure with the remaining online resource re-verification deferred:** “后置剩余复验，收口合入 #1103”. All code/PR checks, latest-main ancestry, reviews/threads and MA-066 gates still apply to the final merge. The remaining verification is explicitly **not performed / user-deferred**, never reported passed.

## Actual state

| Item | Verified result |
| --- | --- |
| Six corrected EU English manuals | JE-1000H, JE-2000F, JE-3000C, JE-2000E, JBP-2000B, JE-500A; six existing family-config builds, 24 successful check/Markdown/RTD-source/strict-Sphinx actions |
| Business release | [Hello-Docs #73](https://github.com/Bingboom/Hello-Docs/pull/73), all 16 checks green; merged `d7ef906f139b6aa1479280ee04228f5cf5feb230` at 2026-09-13T23:58:38Z; RTD build **34539682 succeeded** |
| Final engineering code | [#1127](https://github.com/Bingboom/auto-manual/pull/1127) deployment receipt, [#1128](https://github.com/Bingboom/auto-manual/pull/1128) withdrawal/restoration, [#1129](https://github.com/Bingboom/auto-manual/pull/1129) complete original-byte CDN transport; each 17/17 checks green before authorized merge |
| Latest runtime | Engineering main `7a6a7ebbf9c2da523e1e5391b133a13a5a3f2197`; Hello-Docs mirror `0aee1bce717ef4b674dcd7c14e36443492dc2fd4`; RTD **34539775 succeeded**. Critical runtime blobs and unchanged publish tree `070bf2fd5fc7a2fe64c5f8f35ec26f9217c25a9f` independently verified via Git API |
| Final live verification | **23/23 actual canonical HTML responses and 608/709 recursive resources passed strict hash checks**. Intended traversal spans 91 routes and did not complete. Remaining 101 resource re-verification is user-deferred by explicit approval. A supplemental final HEAD run was not performed; actual 23-page HTTPS200 observations are recorded separately |
| Approved-list coverage | 20/20 model entries published; 23 publications including two preserved out-of-list scopes. Eight evidence-backed single-language publications; 15 legacy entries retain unspecified language scope |
| Preserved publications/routes | Other 17 target sources, metadata and evidence byte-identical; all 23 canonical routes and 67 aliases retained; the preservation statement is frozen-tree/local aggregate evidence, not a claim of101 additional live reads |

## Operator-approved remaining verification deferral

After more than 600 successful original-byte reads, the site returned HTTP429. The batch stopped; an initial 60-second cooldown and a later five-minute cooldown did not clear it. At 2026-09-14T00:19:32Z a **single ordinary GET without any query** to `manual-deployment.json` also returned HTTP429 with `Cf-Mitigated: challenge`, title “Just a moment...”, 5,520-byte body and no Retry-After. Therefore this is not just cache-nonce traffic being rejected. It proves an edge challenge for this client/endpoint; it does not prove all visitors or the entire site are unavailable.

Origin requests stopped. No IP/proxy switching, challenge bypass, browser workaround or fake response was used. The operator subsequently reported that their browser opens the site without a challenge, then explicitly approved deferring the remaining resource re-verification and closing #1103. All 23 canonical article HTML responses were already fetched with HTTP200 and match the frozen output after only the exact known RTD injection is removed. Of the 101 remaining files,98 are byte-identical to the prior build; the changed items are index.html and JE-500A's lcd_map.png/overview.png. Both new images passed local strict build and sealed-file hash checks. These facts justify the operator's stated acceptance decision; they do **not** turn 101 missing live reads or the unrun supplemental HEAD into successes. Later human visual/content acceptance and response SLA remain user-deferred. Any future automatic retry requires legitimate access recovery and receipt-matching cache; no repeated PDF audit or challenge bypass is authorized.

## Completed pilot receipt, metadata and feedback

JE-1000F EU EN/FR V2.0 was originally published by [Hello-Docs #72](https://github.com/Bingboom/Hello-Docs/pull/72), commit `a87ff6ec97c2a4f1a071936dce5dd38b976550e2`, RTD34536139. Its actual desktop/mobile language-navigation and article-image evidence remains in the historical checklist.

Before the approved metadata writes, RTD **34539600** / business `5f98b0eaf6bbaaf610e265f61335d09481809c6a` passed a complete pilot receipt verification: **147 files / 10,991,251 bytes**, both EN/FR articles and recursive resources. Both actual pages expose GitHub Issues plus Model, Region, Language, Version and Page context. The first 23-publication HEAD check recorded one JBP-2000B network failure; a fresh complete check returned zero failures. These reports predate the six-target release and are not relabelled as its final health. The six-target release has a separate actual 23-canonical-page HTTP200/hash observation report, plus the later automated-client429 incident; neither is mislabelled a fresh HEAD check.

The user approved exactly two additive publication-metadata records in business Base `LD3lb4G1ua4GOVs1vxAc9W2enje`, build table `tblbnRHjpJeCVTtj`, using prod/bot. Each record was GET-read back after creation:

| record_id | Document_ID | Version / Lang | HTML_link | Git_ref |
| --- | --- | --- | --- | --- |
| `recvv9cTEvtUF4` | JE-1000F_EU_en_2.0 | 2.0 / en | [English](https://ht-doc.readthedocs.io/JE-1000F/EU/en/md/manual_je1000f_eu_en.html) | `a87ff6ec97c2a4f1a071936dce5dd38b976550e2` |
| `recvv9cTEvtX8l` | JE-1000F_EU_fr_2.0 | 2.0 / fr | [Français](https://ht-doc.readthedocs.io/JE-1000F/EU/fr/md/manual_je1000f_eu_fr.html) | `a87ff6ec97c2a4f1a071936dce5dd38b976550e2` |

Workflow_action and build-trigger select are null; immediate-build, Review and writeback booleans are false. Owner remarks identify 夏冰 and user-deferred manual acceptance. Scoped row count changed from one to three, preserving old V1.0 `recvkYv81hLOex`; no body extraction, schema change or queue dispatch occurred. These links bind unchanged EN/FR content from #72, not a later runtime-only mirror commit.

Genuine historical feedback [Issue #1126](https://github.com/Bingboom/auto-manual/issues/1126) records the original Codex feedback and approved fixes (6.5 A, 4000 cycles, 0–45°C), source location, review/publication and actual pilot verification. The user explicitly authorized its [reply](https://github.com/Bingboom/auto-manual/issues/1126#issuecomment-5657169522) and closure; closed state was read back at **2026-09-13T23:54:29Z**. It is a retrospective real-feedback record, not invented visitor traffic.

## Lifecycle, health and accepted deferrals

- Real JE-2000E approved content was built/sealed as `2.0-20260913` → fresh same-content technical `2.0-20260913-drill` → original. All three strict Sphinx builds passed; the final complete publish tree equals the correct baseline. Body/assets matched; two technical sidecars differed in isolated paths/derived hashes. Local commits: `db812b2738b125d83f6e12b9a8e84cb673827ccb` → `37a01b5575685c5654489ebc8ef276707f083742` → `09fa5c9b8fca3f5f958272001f55ab0d62c1a3f6`.
- Real cold 23-publication snapshot: withdraw JE-1000F EU FR → 22, restore → 23. Withdrawal/compatibility notices, default-language guards, accidental resurrection rejection and exact-source restoration were validated; strict Sphinx and integrated receipt fixtures passed (24 routes/573 files withdrawn, 23 routes/639 restored). Local commits `862579c241dd7fe67a1fdb6784c66e9e2a4bc7d2` → `38dc878a8d7c0409a34e18d31aa35139c8d3936f`.
- Normal four-release health → remove one real referenced image in an isolated derivative → one target/missing-asset failure → restore → zero. An explicitly simulated HTTP404 against the actual 23-entry index produced one failure. These are **local real-artifact drills**, not production rollback/withdrawal or a visitor outage.
- Owner and acceptance: **夏冰**. Feedback: **GitHub Issues**. Cadence: **check after each publication**. Response SLA and later manual content/visual acceptance are **user-deferred**, not passed or promised. Failed checks stop acceptance; locate source, repair through the reviewed release path, then verify receipt/health before resuming.
- Additional returned/in-progress translation statuses stay in the [coverage ledger](manual_operations_evidence/20260913/coverage.json). Returned translation is not accepted or published; mixed legacy content is not relabelled English. Follow-up structured governance continues per manual after human acceptance. No new language facts or repeated PDF audit were introduced.

## Costs and durable evidence

Six builds completed 24 actions; two seal inventories contain 2,846 files. Integrity audit recorded 3.046 seconds. #1127 final CI ran 4,130 tests /24 skipped /302.112s; #1128 ran 4,139 /24 skipped /344.373s. Transport repair local suite ran 4,149 /22 skipped /174.209s, plus 26 targeted tests and two exact original-PNG live probes. Total build wall time, human labor, visitor metrics and total monetary cost were not fully measured: **no_data**.

[SHA256-indexed evidence](manual_operations_evidence/20260913/sha256.json) includes source lineage, coverage, successful pilot receipts, metadata values, Issue closure, lifecycle/fault drills, engineering/business merge gates, mirror/build identity, partial real-response hashes and the challenge diagnosis. The old #1110 PR still reports open/unmerged, although its feedback code is already in main at `9a015afdbee91786feecaf44567a6ad4d7a0c86e` with an identical tree; it was not merged twice, and #1125 activated it. Code integration and PR metadata remain distinct.

Operator procedures: [guide](../../user-guide/hello_auto-doc.md), [deployment receipt](rtd_deployment_receipt.md), [withdrawal/restoration](web_publication_withdrawal.md), [online health](manual_operations_online_health.md). Workflow modifications remain unapproved. MA-066 remains effective until the actual final #1103 merge and then expires automatically. Scope acceptance is complete under the explicit user deferral; this document does not predeclare the time or success of its own future merge.


## Exact accepted deferral and final gates

[Recorded operator decision](manual_operations_evidence/20260913/final-acceptance-deferral.json):
“后置剩余复验，收口合入 #1103”. The question explicitly disclosed 23 canonical
pages/608 resources verified,101 remaining reads with only the homepage and
two JE-500A images changed. [Remaining-file comparison](manual_operations_evidence/20260913/remaining-resource-delta.json)
and [actual canonical responses](manual_operations_evidence/20260913/canonical-pages-live-verification.json)
preserve the boundary. All technical/operational checklist items are accepted
with this deferral; final current-head CI/reviews/ancestry still must pass
before merge. No additional Cloudflare requests or live-table writes are needed.
