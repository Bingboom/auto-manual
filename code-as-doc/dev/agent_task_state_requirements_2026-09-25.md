# REV-45 设计输入：Agent 任务状态维护与多 Agent 交接机制（操作者需求原文）

- 来源：操作者 2026-09-25 在聊天中分两次发给 Claude（桌面窗口）的需求原文。按原文收录，只把段落整理成 Markdown 标题、列表和代码块，没有改写内容。
- 第一次发到第 30 节开头就断了，最后一句是“现在先不要直接提交完整 REV-45”；第二次从第 30 节发到第 55 节，本文第 30 节起按第二次收录。
- 第二次原文里，第 48 节的图被第 51–55 节隔成两段，这里接回一处；第 51–55 节在原文中出现了两次，这里只收一次。
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

当前不要直接提交完整 REV-45 实现。

第一阶段请先输出一份：

REV-45 Multi-Agent Task Lifecycle Design Draft

至少包括以下内容。

### A. Current State Map

回答：

- 当前任务状态存在哪里；
- 谁修改；
- System Workspace 从哪里读；
- Agent 当前怎样知道下一步；
- 当前有没有 checkpoint；
- 当前有没有 handoff；
- 当前已有哪类任务队列；
- 哪些机制可以直接复用。

> REV-45 — Agent 任务状态维护与多 Agent 交接机制
>
> 第 30 节续 — 当前阶段交付物与验收要求

### B. Gap Analysis

至少判断以下能力当前处于什么状态：

```text
Task Authority
Claim
State Machine
Checkpoint
Evidence
Handoff
Resume
Acceptance
Audit Trail
Concurrency
```

每一项必须标记为：

```text
EXISTS
PARTIAL
MISSING
UNCLEAR
```

并说明：

- 当前实现在哪里；
- 是否可以复用；
- 当前缺口是什么；
- 是否依赖尚未明确的 SSOT Fact Domain；
- 是否需要新增实现；
- 是否应该暂缓。

不要因为某个文件里出现了类似字段，就直接判断能力已经存在。

例如：

存在 executor 字段

不等于：

已经存在 Agent Claim Protocol。

必须根据实际行为判断。

### C. SSOT Impact

列出 REV-45 会新增或改变哪些 Fact Domain。

重点判断：

- task_state
- task_claim
- checkpoint
- handoff
- acceptance
- human_decision

是否应该：

1. 独立成为 Fact Domain；
2. 作为 task_state 的子结构；
3. 只是 Evidence；
4. 不属于 SSOT。

对于每一项至少说明：

```yaml
Fact:
Authority:
Writers:
Readers:
Derived Copies:
Freshness:
Conflict Rule:
```

如果 Authority 当前无法确定：

```yaml
Authority: OPEN
```

并记录原因。

不要为了让设计完整而自行指定 Authority。

### D. Proposed Task Contract

给出第一版 Task Contract 草稿。

至少包含：

```yaml
task_id:
title:
scope:
status:
prerequisites:
authority_dependencies:
acceptance_criteria:
acceptance_policy:
executor:
claim:
evidence:
checkpoint:
handoff:
updated_at:
```

需要逐字段说明：

- 谁写；
- 谁能改；
- 谁能读；
- 是否 authoritative；
- 是否 derived；
- 是否必须；
- 什么时候产生。

### E. Proposed State Machine

输出明确状态图：

```text
planned
   ↓
ready
   ↓
claimed
   ↓
in_progress
   ├────────→ blocked
   │             │
   │             └────→ in_progress
   │
   └────────→ verifying
                  │
             ┌────┴────┐
             ↓         ↓
       in_progress     done
```

同时给出状态转换矩阵：

```text
From
To
Allowed Actor
Required Evidence
Required Condition
```

必须明确：

哪些转换 Agent 可以执行。

以及：

哪些转换必须由 Human / Verifier 执行。

### F. Proposed Handoff Contract

设计第一版 Handoff Schema。

至少回答：

- Agent A 在什么时候产生 handoff；
- handoff 写在哪里；
- 谁是 authority；
- Agent B 怎样发现它；
- Agent B 怎样确认它仍然有效；
- source revision 变化怎么办；
- branch 变化怎么办；
- task scope 变化怎么办；
- human decision 变化怎么办；
- handoff 是否可以覆盖；
- 历史 handoff 是否保留。

### G. Resume Algorithm

用明确步骤描述 Agent B 怎样续接任务。

例如：

```text
1. Read Task Contract
2. Read Source Registry
3. Validate Task Status
4. Validate Prerequisites
5. Validate Claim
6. Read Latest Checkpoint
7. Read Latest Handoff
8. Validate Source Revision
9. Check New Human Decisions
10. Check Blockers
11. Acquire Claim
12. Resume
```

如果任意关键条件发生 Drift：

```text
STOP
↓
REPORT
↓
RECONCILE
```

不能自动猜测。

### H. Minimum Pilot

选择一个：

真实、低风险、范围清楚、容易验收

的任务作为第一条 Handoff Pilot。

不要为了测试 REV-45 人工制造一个没有业务价值的任务。

优先从真实待办中选择。

试点必须能够演示：

```text
Agent A
  ↓
Claim
  ↓
Execute
  ↓
Checkpoint
  ↓
Handoff
  ↓
Agent B
  ↓
Resume
  ↓
Evidence
  ↓
Verifying
  ↓
Acceptance
  ↓
Done
```

如果当前没有适合的真实任务：

记录 NO SUITABLE PILOT YET。

不要为了完成 REV-45 编造一个任务。

## 31. 第一阶段不要提交什么

Discovery / Design 阶段不要提交：

- 新 Task Database；
- 新 Web Backend；
- 新 Agent Runtime；
- 新 Orchestrator；
- Agent Scheduler；
- Agent Pool；
- WebSocket；
- Agent 实时监控；
- Token / Cost Dashboard；
- 自动模型选择；
- 自动负载均衡；
- 大规模并发；
- Distributed Lock；
- 新的长期 Memory System。

除非盘点发现：

仓库已经存在这些机制，只需要接入。

即使如此，也先报告，不直接扩大范围。

## 32. 不要为了 REV-45 重构现有生产系统

REV-45 应：

consume existing production capabilities

而不是：

rewrite existing production capabilities。

例如：

现有 Build Skill 已经能构建：

REV-45 不重新设计 Build。

现有 TM Skill 已经能查语料：

REV-45 不重新设计 Translation Memory。

现有 Publish Workflow 已经能发布：

REV-45 不重新设计 Publish。

REV-45 只负责回答：

哪个 Agent 在什么任务状态下，什么时候调用这些能力，以及调用之后怎样记录结果。

## 33. Agent 应是可替换执行者

设计不得绑定：

Claude 才能运行。

目标模型：

```text
              Task Contract
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       Claude     Codex    OpenClaw
          │         │         │
          └─────────┼─────────┘
                    ▼
             Same Skills/Tools
                    │
                    ▼
                Same SSOT
```

Agent 是：

replaceable worker

而不是：

system authority。

未来更换 Agent，不应该改变：

- Source of Truth；
- Task Contract；
- Acceptance Criteria；
- Production Rules。

## 34. Human Authority

设计必须明确：

系统不是完全无人治理。

Human Authority 至少负责：

- Task Scope；
- Acceptance Criteria；
- 高风险 Source Mutation；
- 无法机器判断的内容质量；
- Compliance / Legal 等业务决定；
- Architecture Scope Change；
- 需要人工验收的 verifying → done；
- Agent 无法解决的 Authority Conflict。

Human Approval 必须留下 Evidence。

不得只存在于：

一次聊天消息之后就消失。

## 35. Failure Model

必须设计以下异常。

### Agent Crash

Checkpoint 已存在：

新 Agent 从 Checkpoint 续接。

没有 Checkpoint：

回到最后一个可信 Evidence，不假装知道未记录的工作。

### Claim Abandoned

需要定义：

- claim expiry；
- manual release；
- takeover rule。

V1 可以暂时：

只允许 Human Release。

不需要自动 timeout。

### Source Drift

例如：

Agent A 开始时：

main = abc123

Agent B 接手时：

main = def456

必须检测。

不能默认 Checkpoint 仍然成立。

### Authority Conflict

例如：

```text
Source Registry → Authority A
Task notes → Value B
```

必须：

BLOCK

而不是：

Agent 自行选 B。

### Failed Verification

```text
verifying
   ↓
verification failed
   ↓
in_progress
```

保留失败 Evidence。

不得删除失败记录后重新提交，制造“第一次就通过”的假象。

## 36. Observability

REV-45 V1 不要求实时监控。

但必须能够回答：

现在有哪些任务正在执行？

谁在执行？

哪些 blocked？

哪些等待验收？

最后一次 checkpoint 是什么时候？

最近的 evidence 是什么？

这些信息未来由 System Workspace 展示。

因此 Task Model 需要能够提供：

```text
status
executor
updated_at
last_checkpoint
last_evidence
blocked_reason
verification_state
```

但 System Workspace 仍然只是：

Read Model。

## 37. Security / Governance

Agent 不得因为拥有仓库写权限就默认拥有所有业务权限。

必须继续遵守现有：

- Merge Authorization；
- Branch Rules；
- Feishu write approval；
- Asset Gate；
- Review / Backport approval；
- Publish approval；
- Human Decision。

REV-45 不能成为绕过这些治理机制的新入口。

原则：

Orchestration does not imply authorization.

Agent 能调度某项能力：

不等于：

Agent 有权批准该项能力产生的结果。

## 38. 与 Merge Authorization 的关系

需要盘点：

Merge Authorization 是否属于 Task Evidence / Human Approval / Governance Decision。

不要重复建设第二套“Agent Approval”。

如果现有 Merge Authorization 已经能够表达：

谁允许合什么、范围是什么、何时失效，

则 REV-45 应引用它，而不是复制。

## 39. 与 Queue 的关系

需要盘点现有 Build Queue / Publish Queue。

明确：

Queue Item 和 Task 是不是同一个概念。

预计：

```text
Task
= business / engineering work unit
Queue Item
= execution request
```

一个 Task 可能产生多个 Queue Item。

例如：

```text
Task
“发布 JE-1000F EU 2.2”
        ↓
Build Queue
        ↓
Publish Queue
        ↓
Verification
```

不要因为已有 Queue，就直接把 Queue 当 Task State SSOT。

需要先判断语义。

## 40. 与 Git Branch / Worktree 的关系

Agent Claim 需要考虑：

```text
Task
↓
Branch
↓
Workspace / Worktree
```

第一版至少需要记录：

- branch；
- base revision；
- current revision。

避免 Agent B 接手时不知道：

工作到底在哪个分支。

如果已有 branch guard / hook 能解决部分问题，优先复用。

## 41. 与 Agent Context 的关系

不要依赖：

“把整个仓库上下文喂给 Agent。”

续接时应该使用最小必要上下文：

```text
Task Contract
+
Relevant AGENTS.md
+
Relevant Skill
+
SSOT refs
+
Latest Checkpoint
+
Latest Handoff
+
Evidence
```

这样未来多个 Agent 才不会因为上下文越来越大而失控。

## 42. 与局部 AGENTS.md 的关系

如果仓库已经通过目录级 AGENTS.md 管理局部规则：

REV-45 必须继续遵守。

Task Contract 不重复复制目录规则。

Agent 执行某个路径时：

```text
Task
↓
Target Scope
↓
Applicable AGENTS.md
↓
Relevant Skill
↓
Execute
```

这也是未来减少上下文的重要机制。

## 43. REV-45 V1 最小实现边界

只有 Discovery / Design 经确认以后，才进入 V1 Implementation。

V1 Implementation 最多建设：

1. Task Contract
2. State Machine
3. Single Active Claim
4. Checkpoint
5. Evidence
6. Handoff
7. Resume Validation
8. Acceptance Transition
9. Audit Trail
10. System Workspace Readout

不要超出这十项。

## 44. REV-45 V1 真实验收场景

最终必须用真实任务完成：

```text
Task Created
      ↓
Ready
      ↓
Agent A Claim
      ↓
In Progress
      ↓
Agent A Execute
      ↓
Checkpoint
      ↓
Agent A Handoff
      ↓
Agent B Validate
      ↓
Agent B Claim / Resume
      ↓
Agent B Execute
      ↓
Evidence Complete
      ↓
Verifying
      ↓
Human / Authorized Verification
      ↓
Done
      ↓
System Workspace reflects Done
```

## 45. V1 验收标准

必须证明：

1. Agent A 中断后，Agent B 不依赖聊天记录也能续接；
2. 两个 Agent 不能同时持有同一个 Task 的 Active Claim；
3. planned → done 被拒绝；
4. prerequisite 未满足时不能执行；
5. Agent 无法伪造 Human Approval；
6. done 必须存在符合 Acceptance Criteria 的 Evidence；
7. Handoff 能明确告诉下一执行者“下一步是什么”；
8. Source Drift 能被发现；
9. Authority Conflict 会停止执行，而不是自动猜；
10. Failed Verification 会留下记录；
11. System Workspace 能读到最终状态；
12. 不产生第二套 Task State SSOT；
13. 不破坏现有 Build / Publish / Review / TM / Asset Governance；
14. Agent 可以替换，不绑定单一模型；
15. 整个试点至少发生一次真实 Agent Handoff。

## 46. V1 不以什么作为成功标准

以下都不能单独证明 REV-45 成功：

“同时启动了三个 Agent。”

“Agent 能自动改 Markdown。”

“Dashboard 显示 Agent 名字。”

“Claude 能把任务交给另一个 Claude。”

“做了一个很漂亮的任务页面。”

“Agent 能自己把任务标成 done。”

真正的成功标准是：

任务状态在 Agent 切换过程中仍然可信、可追溯、可续接。

## 47. 长期演进方向

V1 稳定以后，才考虑：

```text
Task Registry
      ↓
Scheduler
      ↓
Role-based Agent Selection
      ↓
Parallel Execution
      ↓
Resource Lock
      ↓
Automated Verification
      ↓
Control Center
```

这些属于后续阶段。

不得在 REV-45 V1 提前实现。

## 48. 最终架构目标

Hello-Docs 最终希望形成：

```text
                  Human Authority
                        │
                        ▼
                       SSOT
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
      Data            Content          Assets
        │               │               │
        └───────────────┼───────────────┘
                        ▼
                Production System
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
         Web           Word         IDML/PDF
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                  Deliverables
```

```text
Skills / Tools ─────── Capabilities
Task / Ledger ──────── Work
Checkpoint / Handoff ─ Continuity
Agents ──────────────── Execution
System Workspace ───── Observation
```

其中：

SSOT 决定系统相信什么。

Skills / Tools 决定系统能做什么。

Task 决定现在应该做什么。

Checkpoint 决定已经做到哪里。

Handoff 决定谁继续做。

Evidence 决定凭什么认为完成。

Human Authority 决定哪些关键结果被接受。

Agent 是可替换执行者。

System Workspace 让人看见整个系统。

## 49. 当前阶段请先做什么

收到本需求以后，先不要直接实现 REV-45。

第一步请完成：

REV-45 Multi-Agent Task Lifecycle Design Draft

交付内容必须包括：

1. Current State Map；
2. Existing Mechanism Inventory；
3. Gap Analysis；
4. SSOT Impact；
5. Proposed Task Contract；
6. Proposed State Machine；
7. Proposed Claim Model；
8. Proposed Checkpoint Model；
9. Proposed Evidence Model；
10. Proposed Handoff Contract；
11. Resume Algorithm；
12. Acceptance Model；
13. Concurrency Boundary；
14. Audit Trail；
15. Minimum Real Pilot；
16. Open Questions；
17. Dependencies；
18. Explicit Non-goals。

其中所有发现必须尽量引用当前仓库真实文件、Skill、Workflow、Ledger 或现有实现。

不要根据本需求假设某项能力已经存在。

## 50. 完成 Design Draft 后停止

Design Draft 完成后：

先停下来给我审核。

不要自动进入 Implementation。

我确认：

- Task Authority；
- SSOT 新增 Fact Domain；
- State Machine；
- Handoff Contract；
- Pilot Scope；

之后，再决定 REV-45 是否进入 V1 Implementation。

## 51. 总原则

整个 REV-45 必须遵守一句话：

先让任务可以被安全接力，再让 Agent 自动调度任务。

不要把 Multi-Agent 理解为：

多开几个 Agent。

它真正需要解决的是：

当执行者发生变化以后，任务事实、执行状态、已有成果、未解决问题、证据和下一步仍然能够被另一个执行者准确理解并继续。

因此整个系统最终应该满足：

```text
Agent A 离开
     │
     ▼
系统仍然知道
├── 任务是什么
├── 为什么要做
├── Authority 在哪里
├── 做到了哪里
├── 修改了什么
├── 有什么 Evidence
├── 有什么 Blocker
├── 哪些决定已经被批准
├── 哪些事情仍待验证
└── 下一步应该做什么
     │
     ▼
Agent B 接手
     │
     ▼
Validate
     │
     ▼
Resume
```

而不是：

```text
Agent A 离开
     ↓
上下文丢失
     ↓
重新读整个仓库
     ↓
重新理解问题
     ↓
重复已经做过的工作
     ↓
甚至得出另一套事实
```

## 52. REV-45 与 SSOT 的最终关系

REV-45 不应该建立自己的事实世界。

正确关系是：

```text
              Source Registry
                    │
                    ▼
                  SSOT
                    │
           Agent 读取事实
                    │
                    ▼
               Task Contract
                    │
                    ▼
                  Execute
                    │
                    ▼
        Candidate / Artifact / Evidence
                    │
                    ▼
             Verification / Approval
                    │
                    ▼
           Authoritative Mutation
```

因此：

Agent 的任务状态可以由 Agent 维护，但业务事实不能因为 Agent 执行了一项任务就自动变成权威事实。

Task State 和 Business Fact 必须区分。

例如：

REV-XX = done

只代表：

这个任务按照定义完成并通过验收。

不自动代表：

所有下游业务事实都正确。

下游事实是否 authoritative，仍由对应 Fact Domain 的规则决定。

## 53. REV-45 与 Human Authority 的最终关系

Human 不需要继续：

手工推动每一个执行步骤。

但 Human 应继续掌握：

```text
Scope
Architecture Decision
Authority Decision
Risk Acceptance
Business Approval
Quality Judgment
Exception Handling
```

最终希望从：

```text
Human
↓
安排每一步
↓
提醒 Agent
↓
检查 Agent
↓
问进度
↓
整理状态
↓
再安排下一步
```

变成：

```text
Human
↓
定义目标 / 边界 / 验收
↓
System
↓
Task
↓
Agents Execute
↓
Evidence / Handoff / Verification
↓
Human only handles
Decision / Approval / Exception
```

这才是 REV-45 真正要减少的人工负担。

## 54. 最终判断标准

未来判断 REV-45 是否真正成功，只问一个问题：

如果当前执行 Agent 此刻消失，另一个 Agent 能不能在不询问我的情况下，根据系统留下的 Task、SSOT、Checkpoint、Handoff 和 Evidence，准确判断做到哪里，并安全继续？

如果答案是：

可以。

那么 Task Continuity 已经建立。

如果仍然需要我解释：

“它之前其实做到这里了，你接下来应该这样……”

那么 REV-45 还没有真正完成。

## 55. 当前动作

现在请：

Step 1

只读盘点当前仓库。

Step 2

完成：

REV-45 Multi-Agent Task Lifecycle Design Draft

Step 3

明确指出：

- 已有能力；
- 可复用能力；
- 缺失能力；
- SSOT 缺口；
- Open Questions；
- 最小 Pilot。

Step 4

提交 Design Draft 给我审核。

Step 5

停止。

不要自动进入实现。

等我确认：

- Task Authority；
- State Machine；
- SSOT Fact Domain；
- Handoff Contract；
- Minimum Pilot；

以后，再开始 V1 Implementation。

## 最终原则

SSOT 让所有 Agent 共享同一个事实世界。

Task Contract 让所有 Agent 共享同一个工作目标。

Checkpoint 和 Handoff 让工作跨 Agent 连续存在。

Evidence 让“完成”成为可验证的事实，而不是 Agent 的判断。

Human Authority 保留关键决定权。

System Workspace 让整个过程对人可见。

在这些基础稳定以前，不追求更多 Agent、更高并发或更复杂的自动调度。
