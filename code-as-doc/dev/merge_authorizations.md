# Merge Authorizations (gate-on-green registry)

Status: active

The single source of truth for **who may merge what without waiting for the operator's per-PR review**. Default remains AGENTS.md §8.6: agents do not self-merge. A self-merge is allowed only when a **live entry in the table
below covers the PR** and the gate-on-green protocol passes. Chat authority alone is not enough: when the operator grants an authorization in chat, the
agent's FIRST action is to record it here (this file is the durable form —
session memory is not), then act on it.

Decided by the operator on 2026-07-30 (four picks: all-checks-green
definition; branch-pattern + PR-list scoping; parity line stays live; the P0
skill batch #738–#742 stays operator-reviewed).

## Gate-on-green protocol

An authorized PR may be merged only when ALL of the following hold:

1. **Every check is green** — `gh pr checks <N> --watch` until settled, then
   verify each listed check is `pass`. This includes **non-required** checks,
   and `pending`/`queued` is NOT green (a PR was once merged on a pending
   check; a non-required secret-scan once caught a real finding — both are
   why "required checks only" was rejected).
2. **No changes-requested review and no unresolved review threads.**
3. **The PR is covered by a live table entry** (branch pattern or explicit PR
   number). Doubt about coverage = not covered; fall back to waiting.

Then: `gh pr merge <N> --squash --delete-branch`. If the line's workflow
requires it (e.g. an in-review target consuming the change), trigger the
matching rebuild/republish after merge.

Red path: pull the failing job's log, diagnose, fix or report — never merge
partially green, never re-run checks blindly to "wash" a real failure.

## Grant / revoke flow

- **Grant**: operator states the scope in chat → agent adds a row at the top of
  the live table below (the next free `MA-nnn` from
  `python tools/next_registry_id.py ma`, which counts main, the
  [archive](merge_authorizations_archive.md), open PRs and the checkout; scope,
  grant quote + date, expiry condition) → the entry is live once pushed.
  Time-boxed grants name their milestone/date; standing grants say "until revoked".
  Where `gh` cannot run, the tool reads open PRs from the GitHub API. Two windows
  asking at once can still get the same number: the maintainability guardrails
  then fail the PR that merges second, which renumbers its row before merging.
- **Revoke / expire**: operator says so, or the expiry condition is met →
  flip 状态 to 已失效 in the next touch of this file and, in the same commit,
  move the row unchanged to the top of the first table in the
  [archive](merge_authorizations_archive.md). Expired entries stay there as
  history; never delete rows.

## Registry

Live rows only (状态 生效); add new rows at the top. Expired rows, the gate-decision
addenda and per-grant notes live in the [archive](merge_authorizations_archive.md):
grep it by `MA-nnn` when you need one; do not read it whole.

| ID | Scope | Grant | Expiry | Status |
| --- | --- | --- | --- | --- |
| MA-160 | 登记表清账 PR 的常设授权：操作者要求清账（如「清一次登记表」）时开出的 PR，只把失效条件已满足、或操作者已在对话中裁定失效的授权行的状态格改为「已失效（…）」，每行写明依据（所列 PR 的 squash SHA、线上核验结果或裁定原话）；不增删行、不改任何行的其他格、不改登记表以外的文件。每个此类 PR 须最终 head 包含最新 main、全部检查成功（含非必需项，pending 不算绿）、无 changes-requested 或未解决评审线程后，由 Claude 按本行 squash merge。本行同时覆盖 PR #1263（`docs/registry-expire-157-158`，**含本登记行**：把 MA-158 改为已失效并新增本行；MA-157 已由其窗口在 #1262 改为已失效）。**不含**：新增授权或改动授权范围（新的授权仍须操作者在对话中给出并单独登记）、为关闭单独一行而主动开 PR（仍按 MA-029 在下次触碰时顺带改）、`.github/workflows/**`、依赖、公开 CLI 或 Base schema 变更。 | 「加常设授权，等 CI 跑完你合入」2026-09-25（答复 Claude 为只改状态格、不增删行的清账 PR 设常设授权的提议；此前「清一次登记表」） | 操作者撤销 | 生效（推送后生效） |
| MA-002 | IDML 参考版式对齐（parity）线：`fix/idml-*`、`feat/idml-*` 分支，及提交题头 `fix(idml)`/`feat(idml)` 的对齐类 PR | 「授权你绿了自合」2026-07-10；2026-07-30 操作者确认仍生效 | 操作者撤销 | 生效 |
