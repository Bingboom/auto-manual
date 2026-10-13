# Optimization checklist: Milestone K (enterprise ops hardening and platform consolidation)

Part of the [optimization checklist](../next_optimization_checklist.md); its index lists every milestone page,
and its §1 update rules apply here. Update item status on this page and add new
items for this milestone here, not to the hub.

## 6i. Milestone K: Enterprise Ops Hardening + Platform Consolidation

Milestone status: `pending`
Milestone target: `tier-driven, no calendar — Tier 1 = current real execution (4 items); Tier 2 = on business-pain trigger; Tier 3 = requires dedicated capacity`
Milestone note: registered 2026-07-17 as the PR-level breakdown of Workstreams
T (Phase 0), U (Phase 1), and the Workstream V design gate (Phase 2) from the
production-readiness review
([`reviews/production_readiness_review_2026-07-17.md`](../reviews/production_readiness_review_2026-07-17.md)).
Theme: the review found the code plane enterprise-grade but the operating plane
not. V implementation is deliberately **not** broken down here — only its
design doc (K15); implementation PRs get registered after the design is
approved, mirroring the Workstream N gating. Items touching
`.github/workflows/**`, `requirements.txt`, git history, or queue semantics are
operator-gated per `AGENTS.md` §8.7 and are marked below.
**Execution tiers (operator triage 2026-07-17):** so the list reads as "4 in
flight", not "15 pending", the items are grouped into three tiers below.
Tier assignment governs execution order only; the T/U/V phase mapping and each
item's technical scope are unchanged. Tier 1 items are `pending`; Tier 2/3
items are `deferred` with an explicit `Trigger:` line and flip to `pending`
when their trigger fires (per §1 update rules). The operator's triage named 12
items; **K3, K14 (→ Tier 2) and K6 (→ Tier 3) are provisional placements by
the same logic — re-tier in review if wrong.**

### Tier 1 — 当前真实执行 (current real execution)

Entry rule: no trigger needed. These are the next platform slices between
business deliveries, in this order: K4 → K5 → K7 → K1.

- [x] PR K4: Scheduled versioned export of the phase2 source tables + restore runbook (T4)
  - Status: `done`
  - Completed: `2026-07-20` (delivery merged 2026-07-17; reopened by the
    2026-07-19 false-green verification; closed by the first complete
    business-plane artifact)
  - Closing verification (2026-07-20, after #684's guard flip + mirror sync):
    dispatched `Phase2 Content Backup` in Hello-Docs — run
    [`29715297977`](https://github.com/Bingboom/Hello-Docs/actions/runs/29715297977)
    green, artifact opened and verified: business **21/21 tables / 1,314
    rows**, TM **2/2 tables / 888 rows**, `missing_tables` empty on both
    manifests, every CSV sha256 matches. Exit-code propagation is proven by
    mechanism (shell simulation in #684) rather than a live red run — the
    plane fix removed the failing condition before a red could be observed;
    the next real export failure exercises it end-to-end.
  - Note: delivered as `tools/bitable_content_backup.py` (export / restore /
    verify, reusing the `bitable_schema` primitives; restore is dry-run by
    default, requires an explicit target token, refuses non-empty tables, and
    never writes formula/lookup/link columns), the nightly
    `phase2-content-backup.yml` workflow (00:30 UTC + dispatch, 90-day
    artifact retention, sentinel Issue on failure), the
    `phase2-content-backup` env preset, and ops guide §4.7b (restore runbook
    + drill record). **Live drill 2026-07-17:** TM base full export 10s /
    business base 21 tables 58s; scratch-base restore 888/888 rows verified
    (~25s). The drill caught real drift on day one: select options added to
    the live base after the schema snapshot made batch-create reject the
    whole table (800030005) — restore now pre-syncs missing select options
    via field-update. Known limitation (recorded in the runbook): multi-select
    cells restore as one concatenated option; fidelity fix is a follow-up.
    **First-nightly verification 2026-07-19:** Actions run
    [`29672759849`](https://github.com/Bingboom/auto-manual/actions/runs/29672759849)
    was green, and every included CSV passed manifest row-count and SHA-256
    checks, but the artifact was incomplete: business exported 18 tables /
    850 rows and missed `01_数据入库`, `02_文档构建`, and
    `能力→章节映射规则`; TM exported 0 tables and missed
    `Translation_Memory` and `Terms`. The exporter returns non-zero for
    missing tables, but the workflow pipes it through `tee` without
    `pipefail`, so the shell reports `tee`'s zero exit code. K4 is reopened
    until the workflow failure is propagated and a subsequent artifact
    contains the complete 21 + 2 table set. The restore scratch Base
    `演练-K4内容恢复-20260717` was moved to the Feishu recycle bin on
    2026-07-20 after its exact token and owner were rechecked; an exact-name
    search then returned no result.
    **Exit-propagation fix landed 2026-07-20:** both export steps now declare
    `shell: bash` explicitly (GitHub's DEFAULT run shell is `bash -e {0}`
    without pipefail; the explicit form is `bash --noprofile --norc -eo
    pipefail {0}`) — verified by local simulation of both shells (0 vs 1).
    Review of the false-green run also found it had executed the
    "Close tracking issue on recovery" step, so a false green would silence
    an already-open sentinel too.
    **Root cause proven 2026-07-20 (plane mismatch, NOT bot permissions):**
    the same bot reads both canonical bases fully from the operator machine;
    the CI failure signature matches the OLD engineering-plane base exactly
    (18/21 manifest names present; `数据入库表`/`文档构建表` are the old
    names of the two missing `0x_` tables; `能力→章节映射规则` absent), and
    auto-manual's `FEISHU_PHASE2_BASE_TOKEN` secret predates the 06-11 base
    migration — it is the ENGINEERING-plane binding, correct for
    parity/promote, wrong for this backup; the TM secret is invalid for the
    base API (→ 0 tables, mechanism reproduced). Fix: the workflow guard is
    flipped to run ONLY in Hello-Docs (business plane), whose secrets bind
    the new bases the manifests describe; sentinel Issues open there (the
    backport-reminder precedent). Remaining to close K4: one complete 21 + 2
    artifact from a Hello-Docs run (dispatch once after merge, or wait for
    the nightly).
  - Original note: the I5 drill proved schema restore works (86s from repo
    artifacts) but covers structure only — table CONTENT had no point-in-time
    backup; a destructive Bitable edit was unrecoverable. Read-only export, no
    source-table writes.
  - Target files:
    - [`../tools/data_snapshot.py`](../../tools/data/snapshot.py)
    - [`../tools/bitable_schema.py`](../../tools/bitable_schema.py)
    - [`../user-guide/closed_loop_ops_guide.md`](../../user-guide/closed_loop_ops_guide.md)
  - Done when:
    - a scheduled workflow exports full phase2 table content to a dated, retained artifact (retention window recorded)
    - a written restore runbook extends ops guide §4.7 from schema-rebuild to content-restore
    - one content-restore drill has been run and timed against a scratch base
    - one scheduled artifact has been opened and verified to contain all 21 business + 2 TM tables, with a non-zero export exit code reaching the job result

- [x] PR K5: Queue-failure alerting via the sentinel Issue pattern (T5)
  - Status: `done`
  - Completed: `2026-07-17`
  - Note: delivered as the reusable composite action
    `.github/actions/queue-sentinel-issue/` (open-on-failure / close-on-
    success via github-script; cancelled runs open nothing) wired as the
    final `if: always()` step of all three queue workflows with per-workflow
    labels (`queue-failure-build` / `-draft` / `-start-review`).
    **Issue titles carry the record_id**, so the open/close lifecycle is
    per-record: the next successful run of the same record closes its own
    issue (batch runs use a `batch` title). The failure body names the
    writeback silent-divergence case (build succeeded, Bitable row stale) —
    exit-code propagation was verified: writeback failures join the queue
    runner's `failures` list, so the job fails and the sentinel fires.
    Wiring is pinned by `tests/test_queue_failure_sentinel.py` (permissions,
    last-step position, `always()`, distinct labels). Operator-facing doc:
    ops guide §3b. First live firing will be observed on the next real
    queue failure — nothing to pre-verify beyond a dispatch test.
  - Original note: touches `.github/workflows/**` → operator-gated. Today
    `cred-health-check` / `feishu-schema-parity` / `backport-reminder` open and
    close Issues, but a failed build-queue run only writes `FAILED …` to the
    Bitable row and fails the Actions run — nobody is notified unless watching.
  - Target files:
    - [`.github/workflows/feishu-build-queue.yml`](../../.github/workflows/feishu-build-queue.yml)
    - [`.github/workflows/feishu-draft-build-queue.yml`](../../.github/workflows/feishu-draft-build-queue.yml)
    - [`.github/workflows/feishu-start-review.yml`](../../.github/workflows/feishu-start-review.yml)
  - Done when:
    - a failed queue/draft/start-review run opens or updates a tracking Issue (same open/close lifecycle as the sentinels), carrying record_id, target, and the failure summary
    - the Issue closes when a subsequent run of the same record succeeds
    - writeback-failure (build succeeded, Bitable write failed) alerts too — it is the silent-divergence case

- [x] PR K7: InDesign finalize — version lock + second host (T7)
  - Status: `done`
  - Completed: `2026-07-21` (code/doc legs merged 2026-07-17; version
    preflight on the second host 2026-07-20; end-to-end verification
    2026-07-21)
  - Closing verification: `ArriettyMac-mini.local` finalized the
    JE-1000F_US 1.6 handoff zip end-to-end; report matched the main-Mac
    baseline item-for-item (pages=63, story_count=546, fonts=0, links=0,
    PDF/X-4 + Japan Color 2001 Coated + JC200103 pass, pin=match, and the
    11 overset story ids/order/frame positions identical; JSON diff zero
    after excluding local path fields) ⇒ hosts equivalent. Acceptance
    semantics corrected in the runbook (2026-07-21): known-good means
    known-BASELINE — overset ⊞ is a designed designer-workflow item
    (content present, drag to reveal; no overset=0 package has ever
    existed), so the criterion is baseline parity, not an empty overset
    list. The 11 oversets belong to the #692 composition-under-fallback
    issue, owned by the replica line's complete contract re-baseline
    (#693/#696 standing follow-up). **Tier 1 (K4/K5/K7/K1) is now fully
    closed.**
  - Note (2026-07-17 delivery): version pin committed at
    `tools/idml/indesign_version_pin.json` (seeded live from the operator Mac:
    `Adobe InDesign 2026 21.0.1.6`); `tools/indesign_finalize.py` now checks
    the pin at finalize time via the I3 collector — **mismatch refuses to run**
    (`--allow-version-mismatch` overrides, recorded in the report's
    `toolchain` block), plus `--check-host` (runbook step) and `--write-pin`
    (deliberate-upgrade re-seed). Exact-match policy: even patch-level drift
    makes finalize output non-comparable, so upgrades re-pin instead of
    loosening. Second-host procedure:
    [`dev/indesign_second_host_runbook.md`](../dev/indesign_second_host_runbook.md)
    (prereqs incl. fonts from the handoff manifest, five verification steps,
    upgrade discipline: all hosts together). ONBOARDING §3 register row
    updated from "无版本锁（已知风险）" to the documented recovery path.
    `--check-host` verified live on the operator Mac (match). **Second-host
    preflight 2026-07-20:** `ArriettyMac-mini.local` also reported an exact
    match for `Adobe InDesign 2026 21.0.1.6`. No known-good IDML was present
    in the downloaded-main checkout, so finalize steps 3-5 were not run and
    this is deliberately not recorded as the one-time end-to-end verification.
    11 unit tests.
  - Original note: the top delivery SPOF: the IDML→final-PDF leg runs only on
    the operator's Mac, no CI, no version lock (ONBOARDING §3 known risk). This
    PR is documentation + provenance binding, not automation.
  - Target files:
    - [`../tools/idml/indesign_finalize.jsx`](../../tools/idml/indesign_finalize.jsx)
    - [`../tools/toolchain_provenance.py`](../../tools/toolchain_provenance.py)
    - [`../ONBOARDING.md`](../../ONBOARDING.md)
  - Done when:
    - the expected InDesign version is pinned in provenance (a mismatch at finalize time warns loudly, reusing the I3 collector)
    - a second-host setup procedure is documented and verified once end-to-end on a machine that is not the operator's
    - the bus-factor register entry for this leg is updated from "known risk" to "documented recovery path"

- [x] PR K1: Make `requirements.lock` the CI/RTD install source (T1)
  - Status: `done`
  - Completed: `2026-07-17`
  - Note: all 10 `pip install -r requirements.txt` sites switched to the lock
    (manual-validation ×7 jobs, review-preview, feishu-common-setup — which
    also covers the queue/backup/sentinel workflows — and .readthedocs.yaml),
    plus the pip cache key (`cache-dependency-path`) moved to the lock so
    caches invalidate on pin changes. Lock coverage of every requirements.txt
    top-level dep pre-verified; the PR's own CI run is the on-Linux install
    proof. requirements.lock header now carries the refresh WHEN/HOW
    (clean 3.12 venv, freeze, commit lock+txt together); requirements.txt
    header states it is human-facing ranges only and fixes the stale
    "Python >= 3.9"; ONBOARDING §8 "构建环境未锁定" line corrected.
    Deliberate cut: the standalone ruff/mypy tool installs in CI stay
    unpinned (lint toolchain, not build deps).
    RTD first-build confirmation (2026-07-21, operator screenshot of RTD
    project `ht-doc` on the Hello-Docs mirror, build #33636549): the install
    step runs `python -m pip install -r requirements.lock` and passes (22s)
    — the K1-owned leg works on RTD. That build still failed downstream in
    `build.py md --source runtime` (bare clone has no phase2 snapshot), a
    pre-existing RTD-integration gap unrelated to K1, fixed separately by
    switching `.readthedocs.yaml` to `--source review-asis
    --data-root tests/fixtures/phase2` scoped to review bundles committed
    on main (currently JE-1000F/US).
  - Original note: touches `.github/workflows/**` → operator-gated. The lock
    exists (Milestone I3) but no workflow installs from it, so CI drifts from
    the pinned snapshot silently.
  - Target files:
    - [`.github/workflows/manual-validation.yml`](../../.github/workflows/manual-validation.yml)
    - [`../.github/actions/feishu-common-setup/action.yml`](../../.github/actions/feishu-common-setup/action.yml)
    - [`../.readthedocs.yaml`](../../.readthedocs.yaml)
    - [`../requirements.txt`](../../requirements.txt)
    - [`../ONBOARDING.md`](../../ONBOARDING.md)
  - Done when:
    - every CI python-setup path and ReadTheDocs install from `requirements.lock`; `requirements.txt` stays the human-facing range file
    - a documented lock-refresh procedure exists (when and how to regenerate)
    - the stale "Python >= 3.9" comment in `requirements.txt` and the stale "no lock file" note in `ONBOARDING.md` §3 are corrected

### Tier 2 — 业务痛点触发后执行 (execute when the business pain fires)

Entry rule: each item starts only when its named trigger is observed in real
production (the discovery-engine rule, roadmap §5) — then it legitimately
jumps the queue. Until then it stays `deferred` and exerts no pressure.

- [ ] PR K2: Pin and cache the TeXLive install in queue workflows (T2)
  - Status: `deferred`
  - Trigger: queue wall-time or Actions-quota pain observed again (dashboard
    queue metrics, or a quota warning/bill).
  - Note: touches `.github/workflows/**` → operator-gated. Today the full TeX
    stack is apt-installed unpinned on every dispatch (~minutes per run,
    multiplied by every queue build; the org Actions quota has been exhausted
    once already).
  - Target files:
    - [`.github/workflows/feishu-build-queue.yml`](../../.github/workflows/feishu-build-queue.yml)
    - [`.github/workflows/feishu-draft-build-queue.yml`](../../.github/workflows/feishu-draft-build-queue.yml)
  - Done when:
    - the TeX package set is version-pinned (or moved into a prebuilt container image) and cached, so a warm run skips the apt install
    - cold/warm run times are recorded once in the PR body as the baseline
    - build output is byte-identical before/after (release-manifest sha256 comparison on one target)

- [ ] PR K3: Route new binary artifacts to Git LFS (T3)
  - Status: `deferred`
  - Trigger: repo-size / clone-time / CI-checkout pain becomes visible (the
    repo-health metric on the ops dashboard), or the operator makes the
    storage-policy call proactively. **Provisional Tier 2 placement** (not in
    the operator's 2026-07-17 triage): the new-binaries-only half is cheap,
    but the policy decision and the LFS interaction with the Hello-Docs
    mirror / CI checkout make it more than a filler slice — re-tier if wrong.
    Caveat: history grows every week this waits; the trigger should be read
    generously.
  - Note: operator-gated twice over — it changes `.gitattributes` storage
    policy for `docs/_build` (adjacent to Deferred 5, but storage-only: no
    workflow-semantics change), and the history-rewrite question (pack already
    ~148 MiB with two 18.9 MB PDFs) is an explicit operator decision this PR
    only records, never executes. CI runners and contributor docs must gain
    `git lfs install`.
  - Target files:
    - [`../.gitattributes`](../../.gitattributes)
    - [`../ONBOARDING.md`](../../ONBOARDING.md)
  - Done when:
    - new PNG/PDF/DOCX blobs under `docs/_build/**` and `docs/templates/word_template/**` enter LFS instead of raw history
    - CI checkout and local onboarding steps handle LFS transparently
    - the history-rewrite decision (do it / defer it / never) is recorded with the size evidence, as its own operator call

- [ ] PR K8: Single Feishu transport client (U1)
  - Status: `deferred`
  - Trigger: a live sync/backport failure attributable to the transport gap —
    rate-limit (429) errors, a concurrent-sync race on `data/phase2/*.csv`,
    or another divergence bug between the duplicated runners.
  - Note: five-plus independent `run_lark_cli_json` implementations exist; the
    sync path has zero retry/backoff/rate-limit and no file locking. May land
    in slices (consolidate first, then retry/lock), but one module owns the
    boundary at the end.
  - Target files:
    - [`../tools/feishu_record_transport.py`](../../tools/feishu_record_transport.py)
    - [`../tools/queue_lark_ops.py`](../../tools/build_queue/lark_ops.py)
    - [`../tools/queue_bound_lark_ops.py`](../../tools/build_queue/bound_lark_ops.py)
    - [`../tools/listen_build_queue_lark.py`](../../tools/build_queue/listen_build_queue_lark.py)
    - [`../tools/spec_master_rebuild.py`](../../tools/spec_master_rebuild.py)
    - [`../tools/bitable_schema.py`](../../tools/bitable_schema.py)
  - Done when:
    - exactly one module builds and runs `lark-cli` invocations, with tested retry/backoff and rate-limit handling (Feishu ~20 QPS, 429 responses)
    - the listed call sites (plus sync/backport/intake `lark-cli` argv builders) route through it; no independent JSON-runner remains
    - `data/phase2/*.csv` snapshot writes take a file lock so concurrent syncs cannot interleave

- [ ] PR K11: Structured logging baseline in queue and build orchestration (U4)
  - Status: `deferred`
  - Trigger: after K5 alerting lands, the first time diagnosing a queue
    failure from print output costs real time — the alert tells you THAT it
    failed; this item fires when finding out WHY hurts.
  - Note: zero `logging` imports and 423 `print()` calls today. Scope is the
    baseline, not a repo-wide sweep: queue orchestration and build entry paths
    first; user-facing CLI output stays `print`.
  - Target files:
    - [`../tools/queue_orchestration.py`](../../tools/build_queue/orchestration.py)
    - [`../tools/build_runtime.py`](../../tools/build_runtime.py)
  - Done when:
    - queue and build orchestration emit leveled `logging` records (level via env), with run/record correlation ids on queue paths
    - Actions logs keep at least today's readability; `$GITHUB_STEP_SUMMARY` output is unchanged
    - a short convention note documents what logs vs what prints, so the sweep can continue incrementally

- [ ] PR K13: Data-driven language onboarding (U6)
  - Status: `deferred`
  - Trigger: the next new-language/region onboarding request lands (the
    natural moment: do K13 first, then onboard the language through the new
    data-driven path as its live proof).
  - Note: adding a language today edits four hardcoded Python enumerations
    plus paired golden-test expectations (`setup-map.md` §code registration) —
    a data problem solved with code edits, which fails at 50 lines.
  - Target files:
    - [`../tools/signal_words.py`](../../tools/signal_words.py)
    - [`../tools/sync_data_models.py`](../../tools/data/sync_data_models.py)
    - [`../tools/localized_copy.py`](../../tools/localized_copy.py)
    - [`../tools/manual_copy_source.py`](../../tools/manual_copy_source.py)
  - Done when:
    - language registration is data/config-driven (declared once, consumed by all four surfaces); an unknown language fails with a clear message, not a KeyError
    - adding a test language in fixtures requires zero Python edits, proven by a test
    - [`../.agents/skills/new-region-line/SKILL.md`](../../.agents/skills/new-region-line/SKILL.md) and its setup-map drop the code-registration step

- [ ] PR K14: Release labeling + rollback runbook (U7)
  - Status: `operator_drill_pending` — machine scope completed 2026-07-31:
    versioned manifests and publish metadata carry a deterministic release tag,
    `tools/release_tag.py` creates/verifies its annotated manifest binding, and
    the three-path rollback runbook is live. The first real timed drill remains
    operator-owned and this checkbox stays open until that result is recorded.
  - Trigger: the first real rollback need (a shipped manual must be reverted
    or re-delivered from a prior state), or the business asks for turnaround
    commitments. **Provisional Tier 2 placement** (not in the operator's
    2026-07-17 triage) — re-tier in review if wrong.
  - Note: manifests already carry git SHA, toolchain provenance, and per-output
    sha256 — traceability exists, labeling and the recovery procedure don't.
    Complements (does not replace) E1 snapshot freezing.
  - Target files:
    - [`../tools/release_manifest_service.py`](../../tools/release_manifest_service.py)
    - [`../user-guide/closed_loop_ops_guide.md`](../../user-guide/closed_loop_ops_guide.md)
  - Done when:
    - each publish gets a stable release identifier (git tag or release record) bound to its manifest
    - a written rollback runbook covers: re-deploy a prior Vercel build, re-deliver a prior Word/PDF from its manifest, and rebuild from a prior `Git_ref`
    - one rollback drill has been executed and timed

### Tier 3 — 必须有工程资源或专门窗口 (requires dedicated capacity or a protected window)

Entry rule: do NOT start these as between-delivery filler — each needs either
a second maintainer, formally allocated platform time, or a consciously shaped
low-delivery window (the Workstream U/V organizational triggers). Starting
them without that capacity risks a half-moved subsystem or an unfinished
semantic change sitting in the tree while business work resumes.

- [ ] PR K9: Package the flat `tools/` namespace, one subsystem per PR (U2)
  - Status: `deferred`
  - Trigger: dedicated capacity (second maintainer or allocated platform
    time). Each subsystem move is individually small, but the wave only pays
    off completed — partial packaging leaves two import styles coexisting.
  - Note: consistent with Deferred 3's rationale — this is the gradual
    boundary cleanup it calls for, explicitly NOT a big-bang rename: one
    subsystem per PR, behavior-preserving moves, import-compatible facades,
    guardrail entries updated per move. Queue first (largest family, ~37
    files), then word / backport / intake / sync / checks, following the
    proven `tools/idml/` pattern.
  - Target files:
    - [`../tools/`](../../tools)
    - [`../tools/check_maintainability_guardrails.py`](../../tools/check_maintainability_guardrails.py)
    - [`dev/orchestration_module_map.md`](../dev/orchestration_module_map.md)
  - Done when:
    - queue/word/backport/intake/sync/check subsystems live under packages with `__init__` facades keeping existing import paths working
    - guardrail thresholds move to the new paths in the same PR as each move
    - the ownership map reflects the package boundaries, and no prefix-family flat modules remain at `tools/` root for the moved subsystems

- [ ] PR K10: Extract target/config resolution out of the `build_docs` facade (U3)
  - Status: `deferred`
  - Trigger: dedicated capacity; natural window = alongside or just before
    the K9 queue-subsystem move (same import surfaces).
  - Note: 8 non-build modules (including queue code) import the 838-line
    facade just for `load_config` / `resolve_build_targets` /
    `build_root_for_target`, dragging Sphinx/export imports into queue and
    check paths.
  - Target files:
    - [`../tools/build_docs.py`](../../tools/build/docs.py)
    - [`../tools/utils/path_utils.py`](../../tools/utils/path_utils.py)
  - Done when:
    - target/config resolution lives in a lightweight `tools/utils/` module with no Sphinx-side imports
    - queue/check/sync-review/release importers stop importing `build_docs`; the facade re-exports for compatibility
    - importing a queue module no longer transitively imports the export stack (guarded by an import-time test, the Milestone A PR 1 pattern)

- [x] PR K12: Atomic queue claim + cross-workflow concurrency contract (U5)
  - Status: `done` (Workstream W / Stage 4b items 1–2, 2026-07-31)
  - Trigger: dedicated capacity, or the concurrency assumption breaks (cron
    re-enabled, a second dispatcher appears, or a double-claim near-miss is
    observed). Semantic change to the queue contract — needs a protected
    window and operator attention, not filler time.
  - Note: operator-gated — touches queue semantics, `.github/workflows/**`,
    and [`dev/external_table_contracts.md`](../dev/external_table_contracts.md) /
    [`dev/queue_state_model.md`](../dev/queue_state_model.md). Today the RUNNING
    write is a soft claim (no compare-and-swap) and the three queue workflows
    share no concurrency group — safe only because cron is disabled and
    dispatch is single-operator. The verified lease and explicit workflow
    concurrency domains now close this registered slice. The parallel build matrix is a recorded
    follow-up AFTER the claim lands, not part of this PR.
  - Target files:
    - [`../tools/queue_transitions.py`](../../tools/build_queue/transitions.py)
    - [`../tools/queue_orchestration.py`](../../tools/build_queue/orchestration.py)
    - [`dev/queue_state_model.md`](../dev/queue_state_model.md)
  - Done when:
    - claiming a row is atomic (claim token + TTL, or re-read-and-verify CAS) so two concurrent dispatches cannot both process the same record — covered by a fixture test
    - stale claims (worker died mid-run) expire and become re-claimable, with the expiry documented in the queue state model
    - the three queue workflows share an explicit concurrency contract, and the external-table contract doc gains the claim fields

- [x] PR K15: Review-branch propagation design doc (V — design gate only)
  - Status: `done` (operator approved 2026-07-31)
  - Trigger: dedicated capacity for sustained design + review attention
    (roadmap Phase 2 entry: Workstream T exit criteria passed). Business pain
    accelerates it: when the dashboard shows template-fix propagation
    measurably eating delivery capacity, this jumps the queue.
  - Note: the frozen-copy review-branch model is the review's #1 scale wall
    (a shared-template fix reaches zero open branches;
    [`../tools/check_review_branch_sync.py`](../../tools/check_review_branch_sync.py)
    is advisory by design). Implementation is deliberately not scheduled here:
    this PR delivers the design doc; implementation PRs get registered only
    after operator approval — the same gating as Workstream N. Touches
    `docs/_review` semantics conceptually, which is exactly why Deferred 5
    applies to the implementation and not to the design.
  - Target files:
    - [`architecture/Review_Branch_Propagation_Design.md`](../architecture/Review_Branch_Propagation_Design.md)
  - Done when:
    - the design covers: per-target-derivative-only review branches, a pinned-but-advanceable shared-template reference, automated per-branch bump PRs showing the rendered diff, authored-edit protection (classify-or-abstain, reusing the `sync-review` merge_params discipline), and migration of the existing open branches
    - blast radius, failure modes, and the propagation-lag metric are specified
    - the operator has approved or amended the design, recorded in the doc header

- [ ] PR K6: Governance floor — CODEOWNERS, secret scanning, dependabot (T6)
  - Status: `deferred` (severable slice delivered 2026-07-17; remainder waits
    on the trigger below)
  - Slice delivered (2026-07-17): the pre-authorized secret-scanning +
    dependabot half. `secret-scan` job in `manual-validation.yml` (gitleaks
    v8.30.1 pinned + checksum-verified, working-tree scan) with
    `.gitleaks.toml` encoding the repo policy — Feishu RESOURCE tokens and
    business-key vocabulary are allowlisted BY LINE SHAPE, credentials are
    not; tuned against a full local scan (31 findings triaged: all resource
    tokens/fixtures, zero credentials) and canary-verified both ways (clean
    tree = 0, planted ghp_/FEISHU_APP_SECRET shapes = caught).
    `.github/dependabot.yml`: github-actions weekly grouped bumps; pip and
    npm in security-only mode (routine Python pins go through the K1
    lock-refresh procedure, not per-package bumps). Remaining for the full
    K6: CODEOWNERS + server-side branch-protection verification.
  - Trigger (remainder): a second reviewer/maintainer exists (CODEOWNERS
    routing is mostly symbolic while one person reviews everything — its
    value activates with the Workstream U organizational trigger).
    **Provisional Tier 3 placement** (not in the operator's 2026-07-17
    triage) — re-tier if wrong.
  - Note: touches `.github/**` governance surfaces → operator-gated. CODEOWNERS
    is also the enabler for Workstream V's distributed-review model (K15).
  - Target files:
    - `.github/CODEOWNERS` (new)
    - `.github/dependabot.yml` (new)
    - [`.github/workflows/manual-validation.yml`](../../.github/workflows/manual-validation.yml)
  - Done when:
    - CODEOWNERS routes review by area (tools/queue vs docs/templates vs workflows), with the operator as owner of the compliance-sensitive surfaces
    - a push/PR secret-scanning gate runs in CI; dependabot files version-bump PRs (grouped, low noise)
    - server-side branch protection settings are verified against `AGENTS.md` §8 and the verification is recorded
