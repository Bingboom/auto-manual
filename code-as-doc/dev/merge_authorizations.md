# Merge Authorizations (gate-on-green registry)

The single source of truth for **who may merge what without waiting for the
operator's per-PR review**. Default remains AGENTS.md §8.6: agents do not
self-merge. A self-merge is allowed only when a **live entry in the table
below covers the PR** and the gate-on-green protocol passes. Chat authority
alone is not enough: when the operator grants an authorization in chat, the
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

- **Grant**: operator states the scope in chat → agent adds a row (next
  `MA-nnn`, scope, grant quote + date, expiry condition) → the entry is live
  once pushed. Time-boxed grants name their milestone/date; standing grants
  say "until revoked".
- **Revoke / expire**: operator says so, or the expiry condition is met →
  flip 状态 to 已失效 in the next touch of this file. Expired entries stay as
  history; never delete rows.

## Registry

| ID | 范围 (branch pattern / PR list) | 授予出处 | 失效条件 | 状态 |
| --- | --- | --- | --- | --- |
| MA-001 | 闭环报告工程 ①–⑦ 的 PR（2026-07-02 当日各线） | 「授予你全绿就合入PR的权利 直到闭环报告工程①–⑦完成为止」2026-07-02 | 工程①–⑦完成（当日达成） | 已失效 |
| MA-002 | IDML 参考版式对齐（parity）线：`fix/idml-*`、`feat/idml-*` 分支，及提交题头 `fix(idml)`/`feat(idml)` 的对齐类 PR | 「授权你绿了自合」2026-07-10；2026-07-30 操作者确认仍生效 | 操作者撤销 | 生效 |
| MA-003 | PR #738、#739、#740、#741、#742、#743（2026-07 月度回顾 P0 批次 + 本协议 PR） | 「全绿即合的授权给你 六个PR都合了」2026-07-30 | 六个 PR 全部合入即失效 | 已失效（2026-07-30 六 PR 全部合入） |
| MA-004 | PR #744、#745、#746、#747（2026-07 回顾 P1 第一波，含本登记行所在的 #744） | 「合入吧」2026-07-30（指 P1 第一波四个全绿 PR） | 四个 PR 全部合入即失效 | 已失效（2026-07-30 四 PR 全部合入） |
| MA-005 | PR #748（Workstream W 规模化执行计划登记，含本登记行） | 「合入吧 授权给你」2026-07-30 | #748 合入即失效 | 已失效（2026-07-30 #748 已合入） |
| MA-007 | same-source 门 CI 稳定性修复 PR（fix/same-source-gate-ci-stability，含本登记行；1.7 publish 解阻） | 「合入 重新派发」2026-07-31 | 该 PR 合入即失效 | 已失效（2026-07-31 #813 已合入） |
| MA-009 | same-source 门失配诊断 PR（fix/repin-je1000f-us-after-812，含本登记行） | 「合」2026-07-31 | 该 PR 合入即失效 | 已失效（2026-07-31 #815 已合入） |
| MA-010 | 1.7 publish 解阻链的诊断/修复类 PR（含本登记行所在 PR），按批全绿即合；不越过 F6/契约审批语义 | 「授」2026-07-31 | JE-1000F_US 1.7 publish 成功交付即失效 | 已失效（2026-08-01 run 30683387378 交付 1.7，wiki XhhVw4nDNij5DckM00ocxnlCnlf） |
| MA-011 | 队列/护栏加固批次 PR #856、#857、#858、#859（含本登记行所在 PR）——终态写回所有权、钉钉会话凭据探测、web 表面护栏登记、review 分支同步哨兵；验收发现由本窗口修复后按批全绿即合 | 「你直接优化 这4个pr 然后合入」2026-08-03 | 四个 PR 全部合入即失效 | 已失效（2026-08-03 #856/#857/#858/#859 全部合入） |
| MA-012 | 钉钉交付对接切片 stacked PR #864、#866、#867（含本登记行所在 PR）——交付坐标映射表、outbox 写入器与 `/output/` ignore、队列接线与文档；按依赖序 #864 → #866 → #867 合入。不含语言门（EU 整本按型号裁语言）改动，那是下一批 | 「合入吧 语言门下一批做」2026-08-03 | 三个 PR 全部合入即失效 | 已失效（2026-08-03 #864/#866/#867 全部合入） |
| MA-006 | Workstream W 切片 PR（交付 scaling_execution_plan.md §4 条目、PR body 标注 Workstream W/Milestone L 的 PR），**按批全绿即合**；但计划 §5 的 gated 条目（workflow 变更、公开 CLI 行为、队列并发语义、strict 翻转、F6 seed 等）必须先有对应拍板记录才可合，本授权不越过任何 gate；stacked PR 按依赖序合 | 「W切片的PR授权也一并给你 按批全绿即合」2026-07-30 | Workstream W 收官或操作者撤销 | 已失效（最终逐项状态与证据收官变更合入时） |

Note: MA-003 superseded the earlier per-PR-review decision for #738–#742 —
the operator re-decided after reviewing the batch's CI state.

## Gate decision addenda

This table records releases of implementation gates. It does not create a new
self-merge authorization; PR merge authority still comes from the registry
above.

| ID | 范围 | 操作者原话与日期 | 保留边界 | 状态 |
| --- | --- | --- | --- | --- |
| GD-001 | Workstream W 剩余 Stage 4 与全部 Stage 5 gate，包括 F6 production seed | 「814批准：Stage4全部放心；Stage5全量放行」2026-07-31 | K14 首次计时回滚演练、下一条真实产线 ≤2 操作者日只在真实现场事件后记录；不伪造结果 | 已执行；证据见 [`../reviews/workstream_w_closeout_2026-07-31.md`](../reviews/workstream_w_closeout_2026-07-31.md) |
