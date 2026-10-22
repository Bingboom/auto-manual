# Research & Intelligence 项目章程

Status: active · Owner: 夏冰 · Created: 2026-10-22
孵化分支：Bingboom/auto-manual 的 `feat/product-intelligence-demo`
治理更新：2026-10-21（America/Los_Angeles）。原建档日期保留；真实联调日期未定。

## 定位

Research & Intelligence 是从 Hello-Docs 仓库中孵化的独立研究平台项目。当前分支仅作为
原型开发与迁移过渡环境，最终交付目标是独立仓库。不得将完整研究平台合入
`auto-manual/main`；后续与 Hello-Docs 的集成通过明确的数据契约与适配器实现。

长期定位：**以研究问题为中心，以多来源证据为基础，通过知识组织、关联分析与人工判断，
持续积累可追溯的研究成果，为业务决策提供支持。** 研究范围不受限于自身产品、说明书、
竞品或单一事件类型；一个研究问题可以跨来源、跨事件，也可以不对应任何事件。

这里的 Hello-Docs 指说明书系统：工程面 Bingboom/auto-manual 和业务面
Bingboom/hello-docs，见[两面图](../../user-guide/two_plane_map.md)。本项目不是
Hello-Docs 的新功能。Hello-Docs 对它来说只是可选的数据来源和集成对象。

## 长期概念边界与当前实现

下表是未来架构的概念边界，不是 #1585 新增的数据表、schema 或已落地能力。

| 概念 | 边界与关系 | 当前状态 |
| --- | --- | --- |
| Research Topic（研究问题） | 定义研究目的、范围和待回答的问题，组织来源、发现与决策；不等于单条事件的决策问题 | 尚无独立模型或工作台 |
| Research Source（研究来源） | 文档、网页、报告、访谈等原始材料及其出处、版本和获取边界；来源本身不是已核实事实 | 仅有事件来源链接与可选冻结政策/产品输入 |
| Evidence / Fact（证据／事实） | 证据提供可定位、可核查的依据；事实是带来源、时效、适用边界及核实状态的陈述 | 事件修订和可选产品证据已有局部实现，尚无通用研究证据模型 |
| Finding / Hypothesis（发现／假设） | 从多条证据组织出的判断或待验证解释，保留推理、反证与不确定性，不能冒充事实 | 现有 hypotheses/unknowns 只是事件内字段，多来源综合尚未实现 |
| Event（事件） | 有时间与情境的信息变化，是一种研究输入，不是所有研究成果的共同根模型 | 当前 event-first 核心已实现，类型仍限 policy/market/competitor |
| Decision（决策） | 对研究结果作出的人工选择、责任与后续行动，应关联当时证据和判断版本 | 已有事件级问题、负责人、期限和人工判断记录，尚无跨 Topic 决策模型 |

当前真实已实现的是 `tools/intel/` 的 event-first 飞书同步／决策摘要／待发恢复和
Markdown Wiki 生成；“已实现”指代码与静态、模拟及独立运行验证，**不代表真实飞书联调
通过**。Wiki 是事件文件的派生视图，不是已经建成的多源研究知识库。

多源非结构化材料接入、知识组织、跨来源关联分析及 WeKnora 集成都属于新仓库里的后续
设计。WeKnora 只是候选能力，不是当前运行依赖，也未在 #1585 接入；#1585 不开发 Topic
数据表、RAG、研究工作台或部署。现有 event schema 的限制不限制平台长期研究范围。

## Agent 按需上下文

根级 `AGENTS.md`／`CLAUDE.md` 继续治理 Hello-Docs 宿主；平台局部入口在
[`tools/intel/AGENTS.md`](../../tools/intel/AGENTS.md) 和其薄
[`CLAUDE.md`](../../tools/intel/CLAUDE.md)。架构任务使用
[research-intelligence-architecture Skill](../../.claude/skills/research-intelligence-architecture/SKILL.md)，
按需导航到本章程（方向唯一权威）、[契约](product-intelligence-contract.md)、
[计划](product-intelligence-demo-plan.md)或联调手册，不复制一套规范。
加载路径、验证与迁移位置见 Skill 的
[文档导航](../../.claude/skills/research-intelligence-architecture/references/document-map.md)。

## 为什么独立

这个 Demo 最初从 Hello-Docs 的产品知识和 RTD 展示能力延伸出来，所以放在 auto-manual
里。几轮讨论后，它的定位已经变了：

- 不局限于自身产品或竞品分析；
- 以研究问题为中心，不以说明书数据为中心；
- 需要接入 WeKnora 等非结构化知识处理能力；
- 将来有独立的数据模型、研究工作台和业务闭环。

业务边界已经独立，就不再作为 Hello-Docs 的内部功能开发。这次调整不否定之前的工作：
[Bingboom/auto-manual#1585](https://github.com/Bingboom/auto-manual/pull/1585) 已经完成
模块解耦，接下来完成仓库和项目治理层面的解耦。

## 孵化期规则

- `feat/product-intelligence-demo` 不以合入 `auto-manual/main` 为目标。不创建把它
  整体合入 `main` 的 PR。
- 孵化期的 PR 以这个分支为目标，例如 #1585。合入这些 PR 不等于合入 `main`。
- auto-manual 的 `main` 不依赖孵化分支里的任何内容。
- #1585 和孵化分支只做静态、模拟 transport、fixtures、契约与独立运行验证；禁止真实
  Feishu 读表、写表、建测试 Base/群或发群消息，包括会真实读表的 `sync` dry run。
  [联调手册](../tests/external_intel_live_integration_2026-10.md)在此仅为待迁移参考，不授予执行权限。
- 描述这项工作时，称它为 Research & Intelligence 孵化原型，不称“Hello-Docs 新功能”。
- 新仓库不从这个分支整体推送生成：分支带着 Hello-Docs 的大量代码和历史，整体迁过去
  就失去独立建仓的意义。只迁出下面清单里的独立部分。

## 现有成果的归属

| 部分 | 现在的位置 | 归属 |
| --- | --- | --- |
| 事件库、决策摘要、飞书同步与推送、待发恢复、Markdown 视图 | `tools/intel/`（只依赖标准库和包内模块） | 平台核心，迁出 |
| 核心测试与样例 | `tests/test_intel_*.py`、`tests/fixtures/external_intel/`、`tests/test_external_intel_boundary.py` 中的导入扫描和独立运行 | 迁出 |
| 数据契约 | `external-intel-events/v1`、`external-intel/v1`、决策摘要 `items`、Markdown 视图布局，见[契约](product-intelligence-contract.md) | 迁出，作为对外契约 |
| 运行说明与待执行联调手册 | [操作说明](../../user-guide/hello_auto-doc/product-intelligence-demo.md)的飞书闭环和 Markdown 视图部分、[联调手册](../tests/external_intel_live_integration_2026-10.md) | 迁出；无真实联调完成记录 |
| Agent 上下文 | `tools/intel/AGENTS.md`、`CLAUDE.md` 与 `.claude/skills/research-intelligence-architecture/` | 迁出；独立仓库根级入口仅在新仓库建立 |
| 研究页、产品视角、RTD 接入 | `tools/rtd/` 的研究页文件、`tools/product_knowledge/`、`tools/rtd_portal_assets/` 的研究页资源及其测试 | Hello-Docs 一侧的集成，不属于平台核心；去留见待决策 |
| 与宿主读取器的一致性检查 | `tests/test_external_intel_boundary.py` 中对照 `workspace_snapshot`、`market_policy` 的部分 | 留在 Hello-Docs 一侧，迁出后改为契约测试 |

## 迁移路线

1. [x] 冻结方向：写入本章程。
2. [ ] 完成 #1585：仅交付静态／模拟测试、契约、独立运行验证、文档与 Agent 引导。
   经操作者审查后可合入孵化分支；真实联调不是此 PR 的合入条件。本任务不执行合入。
3. [ ] 提取独立模块：新建独立仓库（暂名 `research-intelligence`），迁入上表中“迁出”的
   部分和本章程。只迁文件，不迁本仓库历史；包名和默认状态目录
   `~/.cache/auto-manual/external-intel` 随新仓库改名。
4. [ ] **仅在独立仓库执行真实联调**：先迁完核心、测试、fixtures、契约、操作与联调
   手册、Agent 引导，修正包名和路径并在无 Hello-Docs 依赖的干净环境通过测试。记录
   迁入清单与来源 commit；由操作者在新仓库确认测试数据归属、存储、权限与测试目标，
   才创建测试 Base/群，按迁移后的手册执行读表、人工判断回合、群消息与 Wiki 验证。
5. [ ] 重新建立接口：需要时，Hello-Docs 通过独立适配器接入平台，只读平台导出的契约
   数据；平台不导入 Hello-Docs 的代码。
6. [ ] 结束孵化：新仓库验收、所需适配器契约测试与回退核对通过后，旧分支保留一段
   时间用于核对，由操作者决定归档，不整体合入 `main`。

### 迁移验收与回退

- 验收证据分开记录：文件清单／来源 commit、干净环境独立测试、契约与输出一致性、
  新仓库 commit 对应的真实飞书测试回执及人工可读性检查。模拟测试不能代替真实回执。
- 联调须验证完整分页、人工判断与事实变更后的重开、发送与回执、失败待发恢复、
  幂等窗口限制、Wiki 稳定生成与泄漏检查，结果留在新仓库的迁移后手册中。
- 失败则停止真实读写和发送，保留脱敏证据、候选文件与待发状态；不盲目重发、不在
  auto-manual 降级试跑。新仓库回退到记录的迁入基线并修复后重测，人工核对远端已发消息
  与判断，代码回退不会撤销这些动作。测试资源由操作者按新仓库授权处理。
- Hello-Docs 如已接适配器，失败时禁用该可选集成或回到上一份已验证冻结导出，继续使用
  原生产链。未通过验收不归档孵化分支、不启动生产试运行或定时任务。

## 待决策

- **数据存放。** 之前定的“事件和判断全部进 Hello-Docs”与新定位冲突。建议事件库和人工
  判断归平台自己的仓库或存储，Hello-Docs 的市场政策记录、产品知识只作可选输入。确认
  之前不默认写入 Hello-Docs；本仓库不开展真实试运行。新仓库联调前还须明确数据所有者、
  访问权限、保留策略和测试存储位置，正式业务数据主权另行决策。
- **新仓库。** 名称、可见性、许可证和所有者。
- **研究页和产品视角。** 是作为 Hello-Docs 一侧的适配器保留，还是由平台自己的研究
  工作台取代。
- **WeKnora 等非结构化知识处理。** 接入方式和数据边界，在新仓库里单独设计。
