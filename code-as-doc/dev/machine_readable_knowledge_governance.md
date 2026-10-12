# 欧规说明书知识治理立项（机读 Phase 3）

Status: active · Owner: Auto-Manual maintainer · Created: 2026-10-12

上位计划：[`machine_readable_manual_corpus.md`](machine_readable_manual_corpus.md)（§4 路线、§9 Phase 3 目标）。
Phase 2 立项：[`machine_readable_knowledge_observation.md`](machine_readable_knowledge_observation.md)；
Phase 2a 验收：[`machine_readable_knowledge_pilot_audit.md`](machine_readable_knowledge_pilot_audit.md)。

本文件是 Phase 3（Knowledge Governance）的立项文件，包括立项依据、范围、决策、契约、
PR 切分与验收标准。§5 的决策已于 2026-10-12 按建议确认，Phase 3a 的实施以本文件为准；各实施 PR
仍按 §10 另行登记授权。Phase 1、2 已上线的行为不因本文件改变。
仓库里另有两处"Phase 3"（平台演进路线、Backport 渲染基线），与本文件无关；本文件只指机读方案的
第三阶段。

## 1. 立项依据

### 1.1 Phase 2a 已经能稳定地找出问题

- Phase 2a 于 2026-10-11 验收：3,336 条知识条目、1,410 条关系；`high` 8/8、`medium` 全量 33 条中
  32 条确认（[验收记录](machine_readable_knowledge_pilot_audit.md) §2）。
- 验收记录 §3.2 的 23 条问题已于 2026-10-12 以文档形式交内容负责人，每条带版本、对照原文、位置、
  权威源类型和处理状态。
- 但人工结论没有落点：机器只写 `extracted` / `candidate`（Phase 2 D9），而那份文档不可机读，
  接不上观察产物，修完之后也没有办法确认问题真的消失。

### 1.2 修了一处、漏了一处

2026-09 的 MA-191 / MA-192（#1309，squash `138c9654`）把节能警告、UPS 警告和 0 ms 注意事项第 4 条
加进了 `docs/templates/`，网页与 Word 输出随 Hello-Docs #146 上线；韩、日、中、巴西葡语模板按当时
裁定"等审核译文"未动（[合入授权归档](merge_authorizations_archive.md)）。

同样三处内容，在 JE-1000H、JE-3000C（以及 JE-2000E 的 UPS 警告）的 nl/pl/pt 版本里至今缺失
（问题清单第 7、8、9 条）。这几个版本是 Git 冻结包，不读模板。修正沿一种权威源走完了，同一内容在
另一种权威源上没有人跟踪。Phase 3 要补的正是这本账：一条知识在哪些版本该有、有没有、谁批准、
改到哪里、改完是否生效。

### 1.3 不需要新的写入路径

修改权威源的入口、审批与回读规则都已存在（§4.2），批准措辞也有唯一的权威库（§4.3）。缺的只是
把"发现 → 结论 → 修改 → 发布 → 核验"串起来的台账和核验工具。

## 2. 目标与非目标

### 2.1 Phase 3a 目标（EU）

1. **发现台账**：把观察产物里的差异主张和人工发现登记为条目，带证据、人工结论和处理状态，放在业务面。
2. **回流跟踪**：每条确认的问题写明所在版本的权威源与编辑入口，经现有审批路径修改，台账记录 PR 与
   发布版本。
3. **闭环核验**：重新发布后再跑观察命令，机器给出"已消失 / 仍存在 / 无法比较"的证据，由人工关闭条目。
4. **覆盖矩阵**：知识 × 版本的 `present` / `absent` / `not_applicable` / `unknown` / `needs_review`，
   离线生成；`absent` 不等于错误。
5. **试点**：问题清单的高优先级条目至少走通一轮完整闭环。

### 2.2 非目标

- 机器不写任何权威源，不判定法规或认证的适用性。
- 不做跨区域比较（Phase 2b），不做跨修订的时间演化（3b）。
- 不新建数据库、向量库或措辞库；不做 OCR。
- 不改 `manual-knowledge.json`、观察产物的生成方式和发布流水线。

## 3. 范围

### 3.1 Phase 3a / 3b

| | 3a（本立项实施） | 3b（另行立项） |
| --- | --- | --- |
| 内容 | 台账、回流跟踪、闭环核验、覆盖矩阵、试点 | 时间演化（跨修订）、Agent 查询接入台账、工作台页面 |
| 依赖 | Phase 2a 观察产物 | 历史语料重建工具、正式修订号（Phase 2 D11） |
| 区域 | EU | 视 Phase 2b 而定 |

### 3.2 角色

| 角色 | 做什么 |
| --- | --- |
| 机器（观察与台账命令） | 提出候选条目，给出证据与核验结果；只写 `candidate` 与核验字段 |
| 内容负责人 | 确认或否决问题，提出并执行修改 |
| 产品 / 认证负责人 | 判断适用性（`not_applicable`）和合规类条目 |
| 操作者 | 批准修改范围与措辞，合并 PR，裁决冲突 |

## 4. 现状（2026-10-12）

### 4.1 已有台账都承载不了知识发现

| 台账 | 位置 | 记什么 | 为什么不够 |
| --- | --- | --- | --- |
| 执行台账（REV） | [`manual_revitalization_execution.md`](manual_revitalization_execution.md) | 工程任务状态 | 工程面，粒度是任务 |
| 修订台账 | [`revision_ledger.md`](revision_ledger.md)，本地 JSONL | 机器建议 → 人工结论 | 不进 git，不共享 |
| QC 发现 | [`closed_loop_qc_implementation_plan.md`](closed_loop_qc_implementation_plan.md) | 构建 QC 发现与处理状态 | 飞书表未建，写入器只做 dry-run |
| 已知标签例外表 | [`machine_surface_known_callout_labels.csv`](../../data/machine_surface_known_callout_labels.csv) | 未识别警示标签的处置 | 只管标签 |
| 市场与政策记录 | Hello-Docs `docs/knowledge/market-policy/records.json` | 业务审核后的记录，RTD 发布 | 不是台账，但存放与审核方式可借鉴 |

市场与政策记录的做法是：业务数据放在 Hello-Docs `docs/knowledge/**`，经只含该目录的内容 PR 维护；
校验和页面代码在 auto-manual（[`market_policy.py`](../../tools/rtd/market_policy.py)）。这符合
[两平面分工](../../user-guide/two_plane_map.md)：业务台账在业务面，代码在工程面。

### 4.2 每个版本只有一个权威源

| 权威源（语料 `release_path` / `authority`） | EU 版本数（10-11） | 编辑入口 | 审批 |
| --- | ---: | --- | --- |
| `git_only_frozen` / `git_native` | 47 | 发布包不可改，修正后重建为新版本再发布（[发布流水线](web_publish_pipeline.md)） | 操作者指定内容；工程 PR + Hello-Docs 发布 PR |
| `unclassified` / `unknown` | 62 | 文档构建表 `Git_ref` 指向的源，多为 `docs/templates/` 与冻结的 phase2 输入（[门户](rtd_manual_portal.md)） | 同上；先确认绑定 |
| 评审分支（queue） | 0 | 回写 R 类改 `docs/_review/`、模板同步 T 类改 `docs/templates/`、F6 改飞书源表（[回写设计](../architecture/Feishu_Cloud_Doc_Backport_Design.md)、[模板同步](template_sync_runbook.md)） | 各自的门禁与回读 |

### 4.3 批准措辞已有唯一的库

- 句级译文的权威是 TM-B 的 `Translation_Memory`：每个（原文、语言）只有一条，`Status` 为
  Draft / Approved / Deprecated，写入经 `tm-apply` 或 bilingual-tm-maintenance，写后回读
  （[译文语料治理](translation_corpus_governance.md)）。
- 结构化构建由 Manual_Copy_Source × TM 生成 Localized_Copy；Git 冻结包不读 TM，修正时要把批准的
  措辞写进新版本。
- `terminology_rules.csv` 只管术语，不承载整句。

### 4.4 修订与历史

- 没有从 Hello-Docs Git 历史重建旧语料的工具，本地克隆为浅克隆。
- 正式修订号的来源存在但未使用：Git 源清单的 `printed_manual_version` 与
  `authority.published_revision`，发布文档管理 Base 的 版本 / 归档日期 / Is_latest。
  时间演化因此放到 3b。

## 5. 决策（2026-10-12 按建议确认）

编号接续 Phase 2 的 D6–D14。

| # | 问题 | 决定 |
| --- | --- | --- |
| D15 | 范围与分期 | 3a 只做 EU：台账、回流跟踪、闭环核验、覆盖矩阵、试点；时间演化与 Agent 查询归 3b，另行立项 |
| D16 | 台账放在哪 | Hello-Docs `docs/knowledge/governance/findings.json`，经只含 `docs/knowledge/**` 的内容 PR 维护（同市场与政策记录）；校验与离线命令在 auto-manual；飞书同步以后再评估 |
| D17 | 状态与权限 | 机器只写 `candidate`、核验证据和 `needs_recheck` 标记；`confirmed` / `rejected` / `not_applicable` / `change_approved` / `applied` / `closed` / `superseded` 由人工给出，带人和日期 |
| D18 | 适用性 | `not_applicable` 只由人工给出并写理由；合规类条目由认证负责人确认；功能开关只作参考，不作推断 |
| D19 | 批准措辞放哪 | TM-B；台账只引用 TM 记录或权威源 PR，不抄措辞；Git 冻结包修正时按批准措辞重建 |
| D20 | 回流路径 | 只用 §4.2 的现有入口，按条目所在版本的权威源走；机器不写权威源；`unclassified` 版本先在条目里写明绑定 |
| D21 | 闭环核验 | 重新发布后用观察产物核验台账，给出 `closed` / `still_open` / `not_comparable`；台账状态仍由人工改 |
| D22 | 试点门槛 | 23 条全部登记并有人工结论；高优先级 7 条中至少 3 条走完闭环并核验为 `closed`；机器写权威源 0 次 |

## 6. 契约

§6.1 已随 P3-0 定稿，由 `python -m tools.manual_knowledge.findings check` 校验；§6.2、§6.3 仍是草案，
分别随 P3-1、P3-2 定稿。

### 6.1 台账条目

台账文件为 `{"schema": "auto-manual-knowledge-findings/v1", "region": "EU", "findings": [...]}`，
其中一条条目如下（`…` 为省略）：

```json
{
  "finding_id": "fd-ups-critical-load-warning-nl-pl-pt",
  "status": "confirmed",
  "priority": "high",
  "category": "warning",
  "summary": "JE-1000H、JE-3000C、JE-2000E 的 nl、pl、pt 版 UPS 章节缺少整条 WARNING：…",
  "registered": {"date": "2026-10-12", "source": "P2-4 验收记录 §3.2 第 7 条"},
  "claims": [{"kind": "absent",
              "variants": ["JE-1000H/EU/nl", "JE-1000H/EU/pl", "…", "JE-2000E/EU/pt"],
              "references": [{"knowledge_id": "kn:JE-1000H/EU/en:warning:823e5e18a1e9a174:0",
                              "source_ref": "JE-1000H/EU/en/md/manual_je1000h_eu_en.html#uninterruptible-power-supply-ups"},
                             "…"]}],
  "evidence": {"tier": "medium", "observation_ids": ["obs:language_parity:JE-1000H/EU:e4d4f3f299c51d8d", "…"],
               "generator": "manual-observations/0.5", "pilot_check": "real"},
  "authority": {"JE-1000H/EU/nl": "git_only_frozen", "…": "…"},
  "decisions": [{"status": "confirmed", "by": "<姓名>", "role": "content_owner", "date": "2026-10-13"}],
  "changes": [],
  "verification": null
}
```

- `finding_id`：`fd-` 加小写词，登记时由人命名，之后不变；条目不随观察产物重算。
- `category`：观察产物的 `warning` / `safety` / `compliance`；不对应知识条目的问题（例如混入的外语
  句子）记为 `other`。`priority`（`high` / `medium` / `low`）可选，由人给出。
- `claims`：一条或多条主张，每条只写一种差异：缺失（`absent`）、等级不一致（`severity`）、数字不一致
  （`numbers`）或人工发现（`manual`）。`variants` 是有差异的版本，`references` 是参照条目
  （`knowledge_id` 加 `source_ref`）。前三种主张由机器比较，必须给参照的 `knowledge_id`，其类别与
  条目一致；参照版本不能同时被主张，每个被主张的版本都要有同型号的参照。`manual` 主张可以只给页面锚点。
- 核验以参照的 `knowledge_id` 为锚：参照条目（通常是英文版）的文字不变，核验就能找到同一簇；参照
  条目变了，核验给 `not_comparable` 并标 `needs_recheck`，不自动作废。
- `evidence`：档位 `tier`（`high` / `medium` / `low`，人工发现为 `manual`）。机器报出的条目列出
  支持它的 `observation_ids` 与生成器版本；`pilot_check` 是登记前的人工核对结论（`real` /
  `partly` / `explainable` / `false_positive`），未核对为 `null`。
- `authority`：每个被主张版本的发布路径（`git_only_frozen` / `unclassified` / `queue` / `legacy`，
  见 §4.2）；编辑入口由 P3-3 补上。
- `decisions`：按顺序重放状态迁移：`candidate` → `confirmed` / `rejected` / `not_applicable`；
  `confirmed` → `change_approved` → `applied` → `closed`；任一状态 → `superseded`。每条带人
  （`by`）、角色（`content_owner` / `certification_owner` / `operator`，即 §3.2 的内容负责人、
  产品 / 认证负责人、操作者）与日期，日期不早于登记日和上一条；`rejected` / `not_applicable` /
  `superseded` 必须在 `note` 里写理由。`not_applicable` 和合规类条目的 `confirmed` / `rejected`
  只能由 `certification_owner` 给出（D18），`change_approved` 由 `operator` 给出。
- `changes`：从 `change_approved` 起记录。每条写所改版本、批准措辞（只写 `tm:<记录 ID>`，不写原文，
  D19）、权威源 PR 与发布后的 `manual_variant_id`；`applied` / `closed` 要求每个被主张的版本都有
  PR 与新版本。
- `verification`：机器写入的核验字段（`result`、`observed_at`、`generator`、`needs_recheck`，见 §6.2）。
  含机器比较主张的条目，只有核验结果为 `closed` 才能关闭（D21）；只有 `manual` 主张的条目由人核验。

与立项时的草案相比：一条发现可能跨多个型号、多处内容（问题清单第 1 条涉及两个型号的四类条目），
所以 `claim` / `reference` 改为 `claims` / `references` 列表，`change` 改为 `changes` 列表，并逐版本
记录发布版本；另补了 `registered`、`priority`、决定的 `role` 和类别 `other`。

### 6.2 核验结果

- `closed`：每条主张的每个版本都已成为同型号参照条目所在簇的成员，或等级、数字已与参照一致。
- `still_open`：差异仍在。
- `not_comparable`：参照条目已不在产物中，或该版本不再参与比较。
- 同一观察产物上运行两次，结果字节一致；结果只写入核验报告，台账的状态改动走 Hello-Docs 内容 PR。

### 6.3 覆盖矩阵

- 行是一个簇（跨语言齐套关系或产品专属警示），列是该型号的各版本。
- 单元格：成员为 `present`；`absent_in` 且有已确认条目为 `absent`；有 `not_applicable` 结论为
  `not_applicable`；未参与比较（多语合订版）为 `unknown`；`absent_in` 但尚无人工结论为 `needs_review`。
- 离线生成，确定性，不进 RTD 构建。

## 7. 计划（PR 切分）

| PR | 内容 | 主要文件 | 验证 |
| --- | --- | --- | --- |
| 立项 | 本文件；上位计划头部指向本文件；系统演进史环 14 的状态表述 | `code-as-doc/dev/`、`code-as-doc/architecture/system_evolution_history.md` | 文档链接与生命周期检查；系统演进页测试 |
| P3-0 台账契约 | §6.1 的 schema 与校验（状态迁移、必填证据、人工字段）；Hello-Docs 内容 PR 登记 23 条为 `candidate`，带 P2-4 核对结论 | `tools/manual_knowledge/`、测试；Hello-Docs `docs/knowledge/governance/` | 单元测试；校验命令通过真实台账 |
| P3-1 登记与核验 | 从观察产物提出候选条目（去重）；按 §6.2 核验台账 | 同上 | 用例覆盖已修复、仍存在、参照变化三种情形；确定性 |
| P3-2 覆盖矩阵 | §6.3 的离线报告 | 同上 | 确定性；每个版本都有列 |
| P3-3 权威源绑定 | 每个台账条目列出所在版本的编辑入口；标出没有绑定的 `unclassified` 版本 | 同上 | 只读；与 §4.2 一致 |
| P3-4 试点验收 | 高优先级条目走完闭环；验收记录 | `code-as-doc/dev/` 下的验收记录 | 见 §8 |

每个 PR 的本地验证按 [`AGENTS.md`](../../AGENTS.md) §8.5。Hello-Docs 的内容 PR 只含
`docs/knowledge/**`，与工程 PR 分开。

实现（P3-0）：`tools/manual_knowledge/findings.py` 实现 §6.1 的校验，`check` 子命令只读，报告问题
与按状态、档位、类别的汇总。台账经 Hello-Docs 内容 PR 登记：[验收记录](machine_readable_knowledge_pilot_audit.md)
§3.2 的 23 条全部为 `candidate`，`pilot_check` 为 `real`，优先级沿用交给内容负责人的问题清单（高 7 条、
中 11 条、低 5 条），共主张 53 个版本；引用的 `knowledge_id` 与 `observation_id` 都取自 10-11 本地重建的
`manual-observations/0.5` 产物。在同一产物上按 §6.2 的规则试算，19 条可比较条目的 21 条主张全部为
`still_open`（142 个版本与参照的组合，没有 `closed` 或 `not_comparable`）；只有人工主张的 4 条
（第 8、21、22、23 条）不参与比较。
`tests/test_knowledge_findings.py` 在含台账的检出里还会校验真实台账，所以 Hello-Docs 的台账内容 PR
由 Manual Validation 的单元测试把关；auto-manual 没有该文件，此用例跳过。

## 8. 验收标准

- **证据**：每个条目至少有一个能回到线上锚点的 `source_ref`；来自观察产物的条目带 `observation_id`
  与生成器版本。
- **人工边界**：除 `candidate` 与核验字段外，所有状态都有人和日期；机器写权威源 0 次。
- **可追溯**：每个 `applied` 条目都能追到权威源的 PR 与发布版本。
- **闭环**：试点至少 3 条核验为 `closed`；同一产物上核验两次，结果字节一致。
- **覆盖矩阵**：确定性；未确认的缺失显示为 `needs_review`，不显示为错误。
- **兼容**：Phase 1、2 的产物与发布不变；Hello-Docs 内容 PR 只含 `docs/knowledge/**`。
- **SSOT**：台账不承载措辞，措辞只在 TM-B 或权威源里。

## 9. 风险与应对

| 风险 | 应对 |
| --- | --- |
| 内容负责人处理得慢 | 台账先承载全部条目；试点只要求 3 条闭环 |
| 冻结包修正成本高（重建版本、等审核译文） | 同一版本的多条问题合并到一次重建 |
| 观察规则变化导致条目对不上 | `needs_recheck`，不自动作废，人工复核 |
| 台账在 Git、业务在飞书，两边割裂 | 3a 先用 Git 与 PR 审核；飞书同步在试点后评估 |
| 与仓库里其他"Phase 3"混淆 | 文件与 PR 一律写"机读 Phase 3" |

## 10. 授权与流程

- auto-manual 的 PR 按 [`AGENTS.md`](../../AGENTS.md) §8 与
  [`merge_authorizations.md`](merge_authorizations.md) 执行；Agent 合并需要新的 MA 登记。
- Hello-Docs 的台账改动走只含 `docs/knowledge/**` 的内容 PR，由操作者审核合并。
- 飞书写入（如 TM-B 的措辞批准）只在操作者确认后进行，写后回读同一记录。
- §5 于 2026-10-12 确认后本文件转为 `active`；
  [`system_evolution_history.md`](../architecture/system_evolution_history.md) 环 14 的表述在立项 PR 中同步更新。
