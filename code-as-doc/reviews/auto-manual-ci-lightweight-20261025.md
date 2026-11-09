# auto-manual change-aware CI reduction

Status: active

Date: 2026-10-25. Scope: auto-manual engineering CI after the merged mirror P0
[PR #1605](https://github.com/Bingboom/auto-manual/pull/1605).
Base: `8a465628659ed42d43856f315de07766ad9790f2`.
Implementation and local evidence below are separate from merge/rollout evidence.

## Trigger and executed-job comparison

| Workflow / change | Before | After |
| --- | --- | --- |
| Manual Validation: maintainer Markdown only | Every PR/main push; 17 executed jobs | Same triggers and check names; 4 executed jobs (classification + 3 checks), 14 engineering jobs skipped |
| Manual Validation: code/data/templates/config/unknown | 17 executed jobs | Original 17 + classification; no test removed |
| Manual Validation: Hello-Docs / Review | Secret scan + business-content | Unchanged; new classifier and engineering jobs are auto-manual-only |
| Review Preview: README / code-as-doc / user-guide only | Automatic PR packaging | No automatic packaging; manual dispatch retained |
| Review Preview: actual inputs | Existing tools/config/template/review paths | Retained, plus renderer/static/art assets, all data, dependency manifests |
| Nightly: schedule | Daily toolchain install + render | Daily lightweight gate; render only without an exact successful input/runner/week marker or when retry is required |
| Nightly: manual dispatch / rerun | Render | Always render |
| Other 15 workflows (including Manifest Diff and mirror sync) | Existing triggers/jobs | Unchanged |

Editorial classification is deliberately narrow: ordinary mode-100644 `.md`
under `code-as-doc/`, `user-guide/`, plus root README. `AGENTS.md`, `CLAUDE.md`,
`SKILL.md`, renderer contracts, templates and machine-readable files do not qualify.
Empty/unknown diffs run full CI. Deletions and both sides of renames are inspected.
Sensitive-information, maintainability (including frozen-source governance) and
link/lifecycle checks stay active on editorial PRs.

## Baseline and estimate method

Read-only GitHub job timestamps were collected on 2026-10-25:

- [Manual Validation 40167119183](https://github.com/Bingboom/auto-manual/actions/runs/40167119183),
  main `8a465628`: 17 successful jobs, sum of job elapsed times **2,610 s / 43.5 min**.
  The 14 selectively skipped jobs account for **2,490 s / 41.5 min**; the retained
  three account for 120 s. Unit alone took 1,501 s. Jobs overlap, so these are
  aggregate runner-time proxies, not workflow wall time or GitHub invoice minutes.
- [Review Preview 40165828789](https://github.com/Bingboom/auto-manual/actions/runs/40165828789):
  successful packaging took 113 s. Removing a docs-only trigger saves that package
  run, subject to variation in setup and cache state.
- [Nightly success 37127734366](https://github.com/Bingboom/auto-manual/actions/runs/37127734366)
  took 195 s, but is dated **2026-10-03**; use it only as an older reference, not a
  current stable-success duration.

For a measured period, compute:

`manual savings = eligible docs-only events × (sum of 14 avoided job durations − classification duration)`

`preview savings = avoided docs-only preview runs × measured package duration`

`nightly savings = safely skipped renders × measured full-render duration − all nightly gate durations`

Count PR and post-merge main events separately. Subtract classification overhead
on engineering events too. Use observed cache hits, not scheduled wakeups, as saved
renders. Sample medians over comparable runs after rollout; there is no claimed
monthly monetary saving. Standard GitHub-hosted execution in this public repository
generally does not consume the private-repository 2,000-minute allowance.

## Existing Nightly failure (not hidden by this change)

The latest three schedules at inspection failed. In
[run 40095876032](https://github.com/Bingboom/auto-manual/actions/runs/40095876032)
(2026-10-24), the render driver raises:

`Pilot config must resolve exactly one registered target: configs/config.us-en.yaml (matches=2)`

This predates the change. Target resolution is a separate follow-up; this PR does
not change model/region/data semantics to manufacture a green render. No success
marker is written for failures. Until a real render succeeds, the daily schedule
continues to retry and **Nightly savings are zero**. The successful input marker
is never a business publication/deployment receipt.

## Safety, dependencies and rollback

- Manual Validation has no workflow-level path filter; required check names remain
  present, including skipped checks. A failed gate causes full engineering jobs
  to run. The original repository guards still exclude both mirrors.
- PR classification executes the base-commit script. The first PR before the script
  exists on main runs full CI. Git tree diffs avoid API file-list truncation.
- Nightly fingerprints all tracked non-editorial inputs, including path/mode/hash.
  Exact keys only; markers are saved after success, scoped by Actions cache branch
  rules and OS/architecture, and rotate each ISO UTC week. Eviction means rebuilding.
- Read-only Actions history checks all available pages up to 2,000 runs, selecting
  the latest attempt by start time. Failure/cancellation, incomplete history, API
  error, missing cache or gate failure forces render. Manual dispatch and explicit
  reruns force render even when an earlier successful marker still exists.
- The gate has only contents/actions read permissions and uses no business secrets.
  No queue, Workspace, Phase2/TM-B backup, Web Publish, RTD receipt/verification,
  repository visibility or production Feishu writes are changed.
- Rollback: revert this PR's three workflow changes and helper/tests/docs via an
  auto-manual PR. The original 17-job behavior and daily render resume; existing
  markers become unused. Mirror sync carries the workflow rollback normally.
  For one immediate Nightly verification, use manual dispatch; no cache deletion
  or secret change is needed.

## Validation evidence

- Targeted regression suite: 34 tests passed; covers actual Git renames,
  deletions, mode/symlink changes, unknown paths, missing history, trusted-base
  routing, unchanged fingerprints, failure/retry history and workflow wiring.
- Ruff, Actionlint 1.7.12 and maintainability guardrails passed. All 16 live
  required-check names are preserved; 87 live Nightly history records correctly
  select retry.
- Fixture-backed EN/US build check passed.
- `TMPDIR=/private/tmp python3 -m unittest`: **5,704 tests, 67 skipped, zero
  failures**, 691.006 seconds. The first attempt used the macOS aliased temp
  directory and hit the existing pinned-root guard; a 39-test reproduction and
  the full rerun passed with the canonical temporary path, without code changes.
- Doc links/lifecycle: 349 files, 3,059 links, no broken links or lifecycle debt.
  Twelve evaluated workflow-condition scenarios confirm full/error/mirror/skip
  and forced-render routing.
- Hosted CI is tracked separately in the PR. Local preflight reports one missing
  and 20 mismatched locked packages; local results do not substitute for that run.
- Merge and post-merge mirror/skip behavior have not been executed by this change.
