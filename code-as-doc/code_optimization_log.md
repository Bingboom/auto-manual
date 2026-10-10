# Code Optimization Log

Updated: 2026-10-10

This file records major maintainability milestones.
It is a history log, not the day-to-day usage guide.

Recent records stay here, newest first; add new records at the top. Older
records (the numbered 2026-03 to 2026-08 entries, the 2026-09 IR and
operations entries) and the archived roadmap sections are in
[`code_optimization_log_archive.md`](code_optimization_log_archive.md).
Grep the archive when you need history; do not read it whole.

For the active optimization checklist, use:

- [`next_optimization_checklist.md`](next_optimization_checklist.md)

For current rules, see:

- [`code-as-doc/README.md`](README.md)
- [`code-as-doc/build_doc_guide.md`](build_doc_guide.md)
- [`code-as-doc/code_style_guide.md`](code_style_guide.md)
- [`user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)

## 2026-10-10: Agent-facing docs split for on-demand reading

Parallel agent rounds (the Workstream Y lanes, #1350–#1423) paid for the same
documents once per agent: AGENTS.md sent every agent to `build_doc_guide.md`
(~76K tokens) and `hello_auto-doc.md` (~70K), merge grants lived in a 360 KB
registry (~109K), and this log had reached ~52K. Following CQ-7.5/7.6 (#1321):

- `build_doc_guide.md` and `hello_auto-doc.md` are indexes (54 and 40 lines) over
  20 and 17 topic pages of at most ~7.7K tokens. Content moved verbatim and was
  regrouped by topic; links were rebased and the four deep links repointed.
- `dev/merge_authorizations.md` keeps the protocol and the 42 live grants; the
  239 expired rows and the addenda moved to `merge_authorizations_archive.md`,
  and `next_registry_id` counts both files.
- This log keeps its recent records; older ones moved to
  [`code_optimization_log_archive.md`](code_optimization_log_archive.md).
- AGENTS.md §10 sets on-demand reading and sub-agent briefing; §5 and
  `code-as-doc.md` Rule 7 send new notes to the owning page; the maintainability
  guardrails cap the five hub and live files.

## 2026-10-03: CQ-3.4 complexity cleanup and CQ-2.3 test decoupling done

- CQ-3.4 done: every function at complexity ≥50 was split, 24 → 0, in batches
  A–E (#1399, #1400, #1401, #1402, #1405, #1406, #1407). Each split was checked
  for behavior: old-vs-new differential runs on real and randomized inputs; for
  the IDML renderers, byte-identical exports of four real targets (1,431 zip
  parts); for the two IDML table builders that no local target reaches, a replay
  of every call made by the full test run.
- CQ-2.3 done: facade patches in tests 363 → 11 (#1384, #1387, #1392, #1411,
  #1412). The remaining 11 patch where the name is looked up, or check the
  facade's own forwarding, and stay. `QueueDeps` gained
  `resolve_config_path_for_task`; tests share `tests/queue_build_fixture.py`.
- CQ-2 acceptance changed by operator decision: the `build_docs.py` `*_impl`
  forwards are the dependency wiring point and stay ("facade only wires"),
  instead of going to 0.
- CQ-1.2: `tools/` top-level modules (398) and files carrying script bootstrap
  code (103) are ratcheted; a new top-level module needs a recorded reason.
- CQ-1.3 done: the 13 `cloud_doc_backport*` modules moved into `tools/backport/`
  (entry `python -m tools.backport.cloud_doc`); each old path is a warning shim that
  aliases the same module object, so the AGENTS.md §3 command and old patch targets
  keep working. Bootstrap files 103 → 93. The move also fixed the
  `run-review-branch` per-page worker, which had run a module with no `__main__`
  since the G0 split and so exited 0 on every page without diffing.
- CQ-1.4 queue family: the 39 `queue_*` / `process_*queue*` modules moved into
  `tools/build_queue/` (named so it cannot shadow the stdlib `queue` when `tools/`
  is on `sys.path`), with the same alias shims; the moved modules compute the repo
  root directly instead of running script bootstrap code.
- CQ-1.4 check family: the 14 `check_docs*` modules moved into `tools/check/`;
  bootstrap files 93 → 90.
- CQ-1.4 build family: the 18 `build_docs*` modules moved into `tools/build/`;
  `tools.build.docs` is the facade, and the facade-patch ratchet watches both names.
- CQ-1.4 web family: the 44 `web_*` modules moved into `tools/web/`; the isolated
  Sphinx runtime that `plain_markdown_site` stages now carries a `tools/web` package.
- CQ-1.4 done with the rtd and word families (15 + 15 modules) moved into `tools/rtd/`
  and `tools/word/`: 158 modules now live in six packages, each old name a shim
  until CQ-1.5. `workspace-data-verify.yml` also triggers on `tools/rtd/**`.
- CQ-1.5 done: `build.py` child processes, docs, `scripts/` and workflow commands run
  `python -m tools.…`; the 158 shims are gone, and modules that are only imported no
  longer carry script bootstrap code. `tools/` top level 398 → 240 (−40%; the ≥50%
  target needs the families the plan did not list, such as `listen_*`, `message_*`,
  `source_*`, `sync_data*`); bootstrap files 103 → 75, all of them script entry points.
- CQ-1 follow-up toward the ≥50% target, moving without shims: `listen_*` and
  `message_*` (8 modules) into `tools/build_queue/`; `backport_*` (4) into
  `tools/backport/`; `source_*`, `sync_data*` and `data_*` (23) into `tools/data/`;
  `frozen_*` and `document_*` (22) into `tools/web/`. CQ-1 acceptance met: `tools/`
  top level 398 → 183 (−54%), bootstrap files 103 → 67, all script entry points.

## 2026-10-02: Workstream Y parallel lanes round

The [parallel-lanes plan](dev/workstream_y_parallel_lanes.md) ran the remaining
[Workstream Y](dev/code_quality_iterability_plan.md) items as independent agent
lanes for one day, with no build-output changes:

- CQ-3.2 done: the five head validators (#1350, #1357, #1355, #1363/#1377,
  #1361) became per-section functions behind characterization nets; functions
  with complexity ≥50 fell 32 → 25.
- CQ-3.3: `lang_asset_sweep` and `bitable_schema` `main()` split into command
  handlers (#1356, #1360); `export_idml` remains.
- CQ-2.3: queue `QueueDeps` seam landed (#1362); no test migrated yet, so
  facade patches stay at 363.
- CQ-7.3: lifecycle status backfilled for `reviews/` and `dev/` docs
  (#1354, #1359), 174 → 5 unclassified.
- CQ-5.3: `csv_pages` exception audit (#1358), broad handlers 89 → 86.
- New ratchets: `zip()` without `strict=` (64, guardrails) and per-file
  untyped-def mypy errors in the three CQ-4.5 packages (68, CI `type-check`
  job with mypy pinned). Both counts had regressed during the round
  (B905 62 → 64; mypy fixed back by #1375, #1379).
- #1365, #1366 and #1368 were closed unmerged after falling 16 commits behind.

## 2026-09-30: Shared-component admission and 14-manual rollout

PRs #1339–#1342 added native and prepared RST/projection admission, repaired
18 operation tables plus JBP-2000B symbols/warranty and smaller-product general
tables, and recorded the separate 13-table LCD asset audit. All 14 scoped manuals
were published through Hello-Docs #157; RTD latest build 34853738, 14 live page
comparisons, 217 image checks and 28 desktop/mobile cases passed. Other 50
publication targets remained unchanged. The original rollout is accepted;
JE-1000H's additional LCD icon repair in #1343 remains a separate unpublished
follow-up. The 27 legacy App chapters and their finished-panel migration order
are documented, not represented as already migrated. Detailed evidence and
release identities: [rollout acceptance](dev/eu_shared_component_rollout_2026-09.md#published-acceptance--2026-09-30).

## 2026-09-30: Workstream Y phase 1 — lint, complexity and doc-lifecycle gates

Phase 1 of the [code quality and iterability plan](dev/code_quality_iterability_plan.md)
turned the 2026-09-28 assessment into CI-enforced ratchets without changing
any build output:

- #1322: closed seven leaking CSV handles (test `ResourceWarning`s 54 → 0),
  audited all 24 `B023` sites, removed dead imports while keeping facade
  re-exports explicit, and widened ruff from three rules to `F` + `B023`. Two
  shadowed duplicate tests in `tests/test_export_idml.py` run again.
- #1318: per-function complexity ratchet; `data/complexity_baseline.tsv`
  held 262 functions above 20 at merge.
- #1319 and #1329: `env.python` / `env.lock` drift is reported by
  `build.py doctor`, standalone, and once at the start of each test run.
- #1320: plan and review docs declare a lifecycle `Status:`; 174 pre-rule
  docs are baselined.
- #1321: `AGENTS.md` §7 skill prose moved to `.agents/skills/README.md`
  (26 KB → 20 KB loaded into every agent session).
- #1331: module boundaries refreshed, with a proposed subpackage per
  domain for the CQ-1 migration.

Phase 2 (test seams, logging and subprocess contracts, validator rewrites)
continues in the plan.

## 2026-09-13: Strict receipt transport through the production CDN

Kept frozen byte hashes authoritative while adding internal unique cache probes,
complete bounded response reads and limited transient retries. The change fixes
an observed Cloudflare Polish image transformation and interrupted HTTP bodies;
it does not accept approximate images or broaden the RTD HTML exception.
No workflow, dependency, CLI, publishing input or online table changed.

## 2026-09-13: Git-only RTD deployment receipt slice

Reused the paused verified-publication receipt module as a separate read-only
engineering slice: the existing frozen Sphinx portal build emits source/output
hash evidence, and callers verify served HTML and its local resource closure.
No workflow, queue, formal link writer or online source table changed. The
[receipt contract](dev/rtd_deployment_receipt.md) records the API and evidence
boundaries; live deployment and complete OPS-04 operations remain separate.
