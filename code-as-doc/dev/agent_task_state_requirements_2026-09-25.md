# REV-45 设计输入：Agent 任务状态维护与多 Agent 交接机制（操作者需求原文）

- 来源：操作者 2026-09-25 在聊天中发给 Claude（桌面窗口）的需求原文，按原文收录，只把段落整理成 Markdown 标题和代码块，没有改写内容。
- 原文在第 30 节“当前阶段交付物”处中断，后续内容没有收到。
- 设计稿见 [agent_task_state_design_2026-09.md](agent_task_state_design_2026-09.md)。

---

设计需求与当前阶段实施约束

状态：设计输入 / 暂不直接进入完整实现

## 1. 先说明当前阶段

下面是我对 REV-45「Agent 任务状态维护与交接机制」的完整需求。

需要特别注意：

这份需求描述的是希望最终达到的 V1 行为，不代表现在立即进入完整实现。

当前 REV-44 已经完成 SSOT Source Registry 的第一阶段，但整个 Hello-Docs 的 SSOT 仍在继续收口。

目前已经具备：

- SSOT Source Registry 机制；
- 首批 Fact Domain；
- Source Registry validation；
- freshness / fallback；
- System Workspace 数据来源展示；
- Execution Ledger；
- Skills / Hooks；
- OpenClaw / MCP；
- Git / PR workflow；
- Merge Authorization；
- Evidence-driven 的部分生产流程。

但是：

SSOT 机制已经建立，不等于整个系统所有事实域已经完成建模。

目前仍需要继续厘清或逐步纳入的领域包括：

- Product Facts；
- Manual Content；
- Asset Identity；
- Review Authority；
- Publication Approval；
- Task State；
- Claim；
- Checkpoint；
- Handoff；
- Human Approval。

因此 REV-45 当前首先进入：

Discovery + Design

而不是：

Full Implementation。

## 2. 当前阶段原则

请严格遵守以下顺序：

```text
明确 Fact
    ↓
明确 Authority
    ↓
明确 Task State
    ↓
设计受控 Mutation
    ↓
设计 Handoff / Resume
    ↓
真实任务试点
    ↓
最后才考虑自动调度
```

不要反过来：

```text
先造 Multi-Agent Runtime
        ↓
再想状态放哪里
        ↓
再补 SSOT
```

## 3. REV-45 当前允许做什么

当前允许：

- 只读盘点；
- 架构设计；
- 数据契约设计；
- State Machine 设计；
- Task / Claim / Checkpoint / Evidence / Handoff schema 草稿；
- 现有能力复用分析；
- SSOT 缺口识别；
- 最小真实任务试点设计。

当前不要直接：

- 建新的 Task DB；
- 建新的 Agent Runtime；
- 建复杂 Orchestrator；
- 建 Agent 集群；
- 建实时 Agent Dashboard；
- 改造 Shared IR；
- 替 REV-39 决定 Manual Content Authority；
- 新建第二套 Execution State；
- 让 Agent 自由修改 Execution Ledger；
- 开始大规模多 Agent 并发。

如果设计过程中遇到尚未明确的 Authority：

记录 dependency / open question，不要自行假设。

## 4. 背景

Hello-Docs 当前已经逐渐形成以下几层：

```text
Facts
  ↓
SSOT / Source Registry
Capabilities
  ↓
Skills / Tools / MCP / Build Commands
Work
  ↓
Execution Ledger
Observation
  ↓
System Workspace
```

当前仍然缺少一层标准化机制：

任务在 Agent 之间如何被认领、执行、记录、交接和续接。

现在很多任务仍然依赖：

```text
Agent 执行
    ↓
聊天上下文
    ↓
人工询问做到哪里
    ↓
人工总结
    ↓
人工更新台账
```

希望逐渐转变为：

```text
Task
 ↓
Agent Claim
 ↓
Execution
 ↓
Checkpoint
 ↓
Evidence
 ↓
Handoff
 ↓
Verification
 ↓
Ledger
 ↓
System Workspace
```

核心变化是：

Agent 的工作过程本身产生可信的系统状态。

## 5. REV-45 核心目标

第一阶段不要把目标定义为：

“同时运行很多 Agent。”

真正的目标是：

一个任务能够被不同 Agent 安全接力，而系统始终知道：谁在做、做到哪里、依据是什么、下一步是什么。

建立统一的 Agent Task Lifecycle：

```text
Task Created
      ↓
Ready
      ↓
Agent Claim
      ↓
In Progress
      ↓
Checkpoint(s)
      ↓
Evidence Collected
      ↓
Handoff / Verification
      ↓
Authorized Verification
      ↓
Done
```

## 6. Execution State 的 SSOT 原则

Task State 必须只有一个 Authority。

当前设计阶段需要明确：

Execution Ledger / 后续结构化 Task State 中，谁才是任务状态的权威来源。

禁止形成：

```text
Execution Ledger
+
Agent Todo
+
Agent Memory
+
Dashboard Status
+
Task DB
```

五套状态同时存在。

Agent 聊天记录、Todo、memory、临时 Markdown 都不能成为 Task State Authority。

System Workspace：

只做 Read Model。

Agent：

只能通过受控入口改变 Task State。

## 7. Agent 不拥有事实

REV-45 必须继承 REV-44 的原则：

Agent does not own facts.

Agent 可以：

- 读取 Authority；
- 执行转换；
- 发现冲突；
- 生成候选；
- 收集 Evidence；
- 提交变更；
- 在授权范围内执行 bounded write。

Agent 不可以因为：

“我认为另一个值更合理”

就改变 Authority。

遇到事实冲突：

```text
Pause
 ↓
Identify Authority
 ↓
Report Conflict
 ↓
Reconcile
 ↓
Resume
```

## 8. Agent 不拥有所有验收权

必须明确区分：

Execution Complete

和：

Accepted

Agent 可以说：

我的执行工作已经完成，可以提交验收。

但不能自动等价于：

任务已经通过验收。

因此需要：

```text
in_progress
     ↓
verifying
     ↓
done
```

其中：

in_progress → verifying

通常可以由执行 Agent 提交。

而：

verifying → done

必须根据 Acceptance Policy 决定。

## 9. Task State Model

建议设计以下状态：

```text
planned
ready
claimed
in_progress
blocked
verifying
done
deferred
cancelled
```

planned

任务已经登记，但尚未满足执行条件。

ready

前置依赖已经满足，可以被认领。

claimed

已有执行者认领。

in_progress

正在执行。

blocked

执行过程中遇到无法继续的问题。

必须记录：

- blocker；
- blocking authority；
- restart condition；
- next action。

verifying

执行工作已经完成，并提交退出证据，等待验收。

done

退出条件满足，并通过对应 Acceptance Policy。

deferred

任务有意暂缓。

必须记录：

- deferred reason；
- restart condition。

cancelled

任务不再执行。

必须有明确决定来源。

## 10. State Machine

第一版必须使用显式 State Machine。

允许：

```text
planned → ready
ready → claimed
claimed → in_progress
in_progress → blocked
blocked → in_progress
in_progress → verifying
verifying → in_progress
verifying → done
planned → deferred
ready → deferred
blocked → deferred
planned → cancelled
ready → cancelled
```

禁止：

```text
planned → done
claimed → done
blocked → done
```

不得为了：

“让 Dashboard 变绿”

跳过中间状态。

## 11. Task Contract

每一个可执行 Task 至少需要明确：

```yaml
task_id:
title:
scope:
status:
prerequisites:
acceptance_criteria:
authority_dependencies:
executor:
evidence:
updated_at:
```

后续可增加：

```yaml
claim:
checkpoint:
handoff:
acceptance_policy:
resource_locks:
source_revision:
```

Task Contract 描述：

做什么、什么时候算完成。

不要复制 Skill 的完整操作步骤。

## 12. Task 与 Skill 的关系

Task 描述：

要实现什么。

Skill 描述：

怎样执行某类操作。

例如：

```text
Task
REV-XX
更新某产品结构化规格
       ↓
Skill
spec-sheet-structured-intake
       ↓
Tool
Feishu / Git / Build
```

不要让每一个 Task 重新定义操作方法。

## 13. Agent Claim

同一个 Task 同一时间原则上只能有一个 active owner。

Claim 至少需要：

```yaml
task_id: REV-XX
claimed_by: claude
claimed_at: ...
claim_status: active
```

后续可考虑：

```yaml
claim_id:
agent_type:
session_id:
workspace:
branch:
```

V1 不要求一次实现全部字段。

## 14. Agent 可以维护什么

Agent 可以：

- 查询 ready task；
- claim task；
- 设置 executor；
- claimed → in_progress；
- 写 checkpoint；
- 添加 evidence；
- 更新执行备注；
- 标记 blocked；
- 写 blocker；
- 写 restart condition；
- 写 handoff；
- 提交 verifying；
- 在明确授权的自动验收规则下触发 verifier。

## 15. Agent 不可以维护什么

Agent 不得自行：

- 修改 Task Scope；
- 修改 Acceptance Criteria；
- 删除已有 Evidence；
- 绕过 prerequisite；
- 抢占其他 Agent 的 active claim；
- 修改 Human Approval；
- 将需要人工验收的任务直接改为 done；
- 自行改变 Fact Authority；
- 因为输出“看起来正确”就覆盖 Source of Truth。

## 16. Checkpoint

长任务必须支持 Checkpoint。

目的：

Agent 中断以后，另一个 Agent 不需要重新阅读完整聊天历史即可续接。

建议：

```yaml
checkpoint:
  task_id: REV-XX
  executor: claude
  created_at: ...
  completed:
    - ...
  current_state:
    - ...
  changed_files:
    - ...
  evidence:
    - ...
  unresolved:
    - ...
  next_action:
    - ...
```

Checkpoint 不保存 Chain-of-Thought。

只保存：

可供下一执行者继续工作的事实性状态。

## 17. Evidence Model

Task 状态必须由 Evidence 支撑。

至少支持：

```text
PR
Commit
File
Test
Build
Artifact
URL
Snapshot
Human Approval
External Receipt
```

示例：

```yaml
evidence:
  - type: pr
    ref: auto-manual#1274
  - type: commit
    ref: eb114b8f
  - type: test
    command: python -m pytest tests/test_xxx.py
    result: passed
  - type: url
    ref: ...
  - type: human_approval
    actor: 夏冰
    date: 2026-09-25
    decision: accepted
```

禁止使用：

“Agent 认为已经完成”

作为退出证据。

## 18. Acceptance Policy

Task 应逐步支持：

```yaml
acceptance:
  mode: human | automated | hybrid
```

human

必须由指定 Human Authority 验收。

Agent 最多提交：

verifying

automated

仅当 Acceptance Criteria 完全机器可验证，例如：

- tests passed；
- schema valid；
- hash matches；
- expected artifact exists；
- zero unexpected diff；

才允许由受控 verifier 进入：

done

hybrid

机器检查通过以后仍需要 Human Decision。

例如：

```text
Tests Passed
+
Visual Review
+
Human Approval
       ↓
Done
```

## 19. Handoff

Agent A 转交 Agent B 时不能只依赖聊天。

必须产生结构化 Handoff。

建议：

```yaml
handoff:
  task_id: REV-XX
  from:
    agent: claude
  to:
    role: qa-agent
  completed:
    - ...
  evidence:
    - ...
  current_state:
    - ...
  unresolved:
    - ...
  next_action:
    - ...
  blocked_by:
    - ...
  files_touched:
    - ...
  branch:
    - ...
  source_revision:
    - ...
```

## 20. Resume Contract

Agent B 续接时优先读取：

```text
Task Contract
      ↓
SSOT Source Registry
      ↓
Latest Checkpoint
      ↓
Latest Handoff
      ↓
Evidence
```

而不是：

Agent A 的聊天历史。

续接前必须确认：

1. Task 仍然存在；
2. Status 允许继续执行；
3. Prerequisite 仍然满足；
4. Claim 状态合法；
5. Authority 是否变化；
6. Source Revision 是否变化；
7. Checkpoint 是否仍适用；
8. 是否产生新的 Human Decision；
9. 是否存在 unresolved blocker；
10. branch / workspace 是否安全。

发生 Drift：

```text
Pause
 ↓
Report Drift
 ↓
Reconcile
 ↓
Resume
```

## 21. 并发控制

V1 至少实现：

One Task → One Active Claim

防止：

```text
Agent A ─→ Task X
Agent B ─→ Task X
```

同时写同一任务。

后续才考虑 Resource Lock：

```yaml
lock:
  resource: manual
  scope: JE-1000F/EU
```

或者：

```yaml
lock:
  resource: translation_memory
  scope: terminology/ja
```

V1 不建设复杂分布式锁。

## 22. Task State 与 SSOT Source Registry

REV-45 设计过程中必须明确：

Task / Handoff 是否需要成为新的 Fact Domain。

预计可能新增：

```yaml
id: task_state
label: 任务执行状态
authority: ...
read: build
used_by:
  - Agent
  - System Workspace
```

但当前不要提前假定 Authority。

先盘点现有：

- Execution Ledger；
- checkpoint；
- task files；
- Git / PR；
- OpenClaw；
- Agent Skills。

再决定。

如果当前 Execution Ledger 继续作为 Authority，则需要说明：

怎样安全修改它。

如果未来引入结构化 Task State，则必须说明：

为什么它不会和 Execution Ledger 形成第二套状态。

## 23. Ledger 更新入口

长期不建议 Agent 自由编辑：

manual_revitalization_execution.md

应设计一个受控入口，例如概念上：

```text
task status
task claim
task checkpoint
task evidence
task block
task handoff
task submit
task accept
```

具体 CLI / Skill / API 名称由实现阶段决定。

受控入口负责：

- State Machine；
- prerequisite；
- claim ownership；
- evidence schema；
- timestamp；
- executor；
- acceptance policy；
- audit trail。

如果 V1 暂时仍直接以 Markdown Ledger 为 Authority，也必须：

通过统一 Skill / Tool 修改。

不得让不同 Agent 任意编辑表格。

## 24. 长期 Ledger 模型

后续如果证明有必要，可以演进为：

```text
Structured Task State
        ↓
Ledger Renderer
        ↓
Human-readable Ledger
        ↓
System Workspace
```

但不要为了“架构漂亮”提前建设。

必须有真实需求以后再迁移。

## 25. Audit Trail

每一次状态变化必须回答：

谁，在什么时候，把什么状态改成什么状态，为什么？

例如：

```yaml
event:
  task_id: REV-XX
  actor: claude
  actor_type: agent
  from: in_progress
  to: verifying
  timestamp: ...
  reason: implementation complete
  evidence:
    - PR #...
```

Human Decision 也必须进入 Audit Trail。

## 26. 与 System Workspace 的关系

System Workspace 继续作为 Read Model。

未来可以展示：

```text
Ready
In Progress
Blocked
Verifying
Done
```

以及：

```text
Current Executor
Last Checkpoint
Last Evidence
Updated At
```

但 V1 不要求 System Workspace 成为 Control Center。

不能为了：

“网页上可以点按钮”

绕过 Task Contract。

## 27. 与 REV-39 Shared IR 的边界

REV-39 负责：

Manual Content / Shared Semantic Boundary。

REV-45 不负责：

- 定义 renderer-neutral content；
- 修改 IR；
- 决定 Web / IDML 的公共语义；
- 决定 Manual Content Authority。

如果 REV-45 发现需要这些信息：

登记 dependency，等待 REV-39。

不要自行解决。

## 28. 与当前 SSOT 未完成部分的关系

SSOT 与 REV-45 可以并行进行有限重叠。

正确关系：

```text
SSOT mechanism
REV-44
DONE
   ↓
REV-45 Discovery
   ↓
发现新的 Fact Domain
   ↓
补充 SSOT Registry
   ↓
Authority 明确
   ↓
REV-45 Implementation
```

因此：

REV-45 的设计可以帮助发现 SSOT 缺口。

但：

SSOT 未明确的部分不能由 REV-45 自己猜。

## 29. 当前阶段必须先盘点的已有能力

设计前先检查：

Execution

- manual_revitalization_execution.md
- 当前 REV 状态结构
- Gate
- Executor
- Evidence

SSOT

- ssot_source_registry_design.md
- source_registry.yaml
- rtd_source_registry.py

Agent

- .agents/skills
- .claude/skills
- AGENTS.md
- OpenClaw
- MCP / Wukong Bridge

Git / Governance

- PR workflow
- Merge Authorization
- branch rules
- hooks
- validation

Workspace

- System Workspace
- Deliverables
- current focus
- capability map

Existing continuation mechanisms

搜索现有：

- checkpoint
- resume
- handoff
- task
- queue
- executor
- claim

避免重新发明已经存在的能力。

## 30. 当前阶段交付物

现在先不要直接提交完整 REV-45

（原文到此中断。）
