# 系统演进史（骨架与来路）

Updated: 2026-10-04

## 0. 本文角色

回溯性架构叙事：回答"系统为什么长成这样"。与三份既有文档互补、不重叠：

- [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md) 向前看——方向与稳定边界；
- [`../optimization_project.md`](../optimization_project.md) 看现在——执行路线图；
- [`../code_optimization_log.md`](../code_optimization_log.md) 逐笔流水——每次改了什么。

本文只记录**环级**转折（改变生产原则的那一层），细节一律指向流水账与 PR。
受众是接手的维护者：读完 [`ONBOARDING.md`](../../ONBOARDING.md) 的第一小时之后、
翻完整优化日志之前，先用十分钟建立这份心智模型。

维护规则：新增"环"、已记录环的关键验收或收官证据变化时更新本文；普通功能与修复不记。
本文中的数量是注明日期和口径的历史快照，不是实时仪表盘。
已形成的能力、仍在验收的建设、未来方向分别标注；合入不等于部署或线上验收。

RTD `/workspace/system/` 的「系统演变」读取本文 §7 的同源摘要，
以“说明书工厂”的类比讲给人看。摘要随历史正文一起维护，不另设网页历史源。
长期方向仍归 Strategy，当前任务状态仍归路线图和执行台账。

## 1. 一行内核（2026-02-15，`fa988f52`）

第一天的全部系统：

```
CSV(安全条目) + RST 模板(占位符) ──csv_to_rst──> RST ──Sphinx(conf.py)──> LaTeX ──> PDF
```

一页安全说明、一个产品、没有机型/区域维度，构建产物直接提交进仓库。
多机型生成页 02-28 已出现（`15b14df2`）；Word 输出 03-05 才有
（pandoc，`d81da227`——同一提交里 spec 页成为整本构建的结构化入口）；
`build.py` 入口 03-10（`248bed28`，`--region` 参数自出生即有）。

**内核至今未变：结构化数据 × 可复用模板 → 确定性构建。**
之后的每一环都是绕着这一行长出来的——不是替换它，而是把它周围每一处
"人手改产物"替换成"改源 + 过门"。

## 2. 生产骨架与新增消费面

```mermaid
flowchart LR
  subgraph 数据面
    F[飞书源表<br/>规格/占位/文案/能力/资产] --sync-data--> S[data/phase2 快照]
  end
  subgraph 仓库面
    T[RST 模板 + asset:引用]
    A[资产注册表 + .ai 配方]
  end
  S --> ASM[组装<br/>manifest 选页 · 能力裁剪]
  T --> ASM
  A --> ASM
  ASM --> G{质量门<br/>lint/能力/语言/棘轮/URL/资产}
  G --> R[评审层 docs/_review]
  R -.批准后按对应编辑面回源.-> F
  G --> OUT1[Sphinx → PDF/Word/HTML]
  G --> OUT2[IDML → InDesign → 印刷PDF]
  OUT1 & OUT2 --> REL[发布<br/>manifest·血缘·tag]
  Q[飞书构建队列] -.驱动.-> ASM
  REL --> WEB[冻结 Web 发布 → RTD HTML]
  WEB --> MACHINE[HTML 语义提取<br/>Machine JSON + Manifest]
  MACHINE --> READ[核验回执与哈希 → 查询 / Agent]
```

（图内不含环 5 的双平面拓扑——评审实际发生在 Hello-Docs 镜像侧——
与环 10 的 config 派生元规则，见对应环。机读支路是当前的
HTML compatibility 路径；未来的 IR-native 人读/机读同源生成见 §6。）

## 3. 演进十四环（按各环成形的顺序）

每环三件事：**动机 → 落点 → 留下的不变量**。

### 环 1 · 目标矩阵（2026-03 ～ 05）

一个产品变一族产品。`tools/utils/targets.py` 与首个语言配置 03-08，
manifest 选页 03-20（`4b4fba7d`），家族配置 `config.us.yaml` 04-04（#41），
`configs/` 归位 05-30（#285）。
**不变量**：一份模板服务所有机型，差异由数据与配置表达——AGENTS 里
"不许每机型一个 config"的规则来自自己的化石（见 §4）。

### 环 2 · 评审层与第一道门（2026-03-11/12）

产物要给人看，人不能直接改产物。`docs/_review/` 03-11，
`review_bundle.py` + `check_docs.py` **同一提交**出生（`9a7a958e`，03-12）。
**不变量**：评审改派生层，构建可重建它；检查与评审天生一对。

### 环 3 · 数据上云 + 队列（2026-04-01，同一提交）

CSV 不再手编。`tools/sync_data.py`、`data/phase2/`、
`.github/workflows/feishu-build-queue.yml`、`tools/process_build_queue.py`
全部来自 **一个提交**（`d90de79c`，#21）。
**不变量**：飞书源表是数据的单一真相，仓库只留可重放的快照；
自动化不是后加的，是数据上云的孪生。

### 环 4 · 回写闭环（2026-06-08 起）

评审改动要回到源头。`cloud_doc_backport.py` 以 diff 报告形态出生
（#343，06-08），次日长出受护栏的写回（#349/#350/#352，06-09），
06-19 补渲染基线库与 seed（#411），06-24 闭环测试（#470）。
**不变量**：修改最终回到声明的权威源，再按目标重建。
**当前操作边界**：云文档回写先写评审派生层；模板同步和正式源表写入分别走各自
流程与批准门，不能把评审回写理解成自动改源表。具体命令与允许写入的路径
以 [AGENTS.md §3](../../AGENTS.md#3-workflow-rules) 为准。

### 环 5 · 双平面（2026-06-10 / 07-02）

工程与业务分离。Hello-Docs 镜像同步 #360，两平面地图
[`../../user-guide/two_plane_map.md`](../../user-guide/two_plane_map.md) #526。
**不变量**：auto-manual = 工程面，镜像 = 业务面；代码永不直接 PR 镜像主干。

### 环 6 · 质量门体系（2026-06-07 ～ 07-27）

不过门不出货。content-lint 06-07（#335），能力→章节门 07-12（#649），
语言树一致性 + 警告棘轮 + 印刷 URL 巡检 07-14（I1/I2/I4，#657-659），
资产状态门入 publish 07-27（#722）。
**不变量**：每类"印出去无法撤回"的错误都要有一道构建期的门。

### 环 7 · 印刷线（2026-07-04 ～ 08-06）

Word 之外长出 InDesign 印刷线。IDML 导出 MVP 07-04（#548），
组件化拆包 07-05（#577-585），真 InDesign finalize 07-13（#648），
参考版式契约 07-17（#675），逐页视觉对齐战役 07-26/27（#711-729，
#729 宣告收官），pin 护栏进 CI 07-27（#724），契约 v2 分域
（内容/装配/样式 fail-closed + 快照溯源不阻塞）08-06（#886）。
**不变量**：操作者批准的参考版式是唯一真相，契约哈希钉死每一页；
"绿"必须可以从干净检出复现。

### 环 8 · 资产环（2026-07-15 ～ 28）

图片走同一原则。注册表普查 07-15（#662），`asset_registry.py` #668、
确定性 .ai 入库 `asset_pipeline/` #670；注册表镜像入 sync-data 07-27
（#721），发布血缘 + 资产门 #722，InDesign 包入发布记录 #723，
对象级引线修复取代白补丁 07-28（#734）。
**不变量**：.ai 是源、导出物是投影；每张图有身份（asset: 键）、
有状态（门控）、有哈希（血缘）。

### 环 9 · 发布自证（2026-03-15 ～ 07-31）

发布要能自证用料、可复现归档。这一环生长最慢：`release_manifest.py`
03-15 就有雏形（`6ff0f08d`），
但从"记录"到"自证"用了四个月——工具链指纹 07-13（I3，#656），
资产血缘 + InDesign 包 07-27（#722/#723），版本快照冻结与
字节级重建证明（E1，#818/#820）、不可变发布标签 07-31（#837）。
**不变量**：一次发布能回答"用了哪版数据、哪版工具、哪些字节的图、
给印厂发什么"，且归档可字节复现。

### 环 10 · 规模化（2026-07-30/31，Workstream W）

前九环长完，规模化收敛为切片工程：计划 #748 当日批准，
76 个切片两日内全部落地（约 50 片当天、其余次日；#838/#839 收官对账）。新语言=改注册表零代码、
新区域=一条命令、CI 目标从 configs 自动推导、队列并发有租约语义。
**不变量**：一切随 config 派生——加产线不加代码。

### 环 11 · 共享语义与组件准入（2026-08 ～ 09）

多格式、多产品不能依赖每条产线各自解释一遍内容。
Manual IR、ComponentSpec 和产品骨架逐步承接语义、组件角色和资产引用；
9 月共享组件准入与原生导入把这些约束用于真实 Web 交付，
14 本手册的集中 rollout 在 09-30 完成（#1339–1342，Hello-Docs #157）。
[rollout 验收](../dev/eu_shared_component_rollout_2026-09.md)
记录了 14 个线上页面对比、217 次图片检查和 28 个桌面/手机案例。
这不是所有格式已完全统一的证明：布局、分页、字体和印刷交付仍各自验收。
**不变量**：语义与组件角色由共享契约约束，各 Renderer 对原生格式负责；
声明了组件就要通过准入，不能在另一种语言中静默退化。
稳定边界见 [Strategy §4.6](System%20Evolution%20Strategy.md#46-cross-layer-operations-feedback-and-shared-intake)。

### 环 12 · Web Corpus 与 Workspace（2026-09 ～ 10）

交付对象从一次性的文件变为持续维护的已发布内容集合。
RTD 工作台把手册、语言版本、语料、生产入口和证据放到同一导航中；
冻结目录决定可见的手册，来源登记决定数字从哪来。
#1351 将交付物页变为说明书工作台，#1430 统一外壳，
#1431 在工作入口标出各版本的内容权威源。
机器语料方案保存的 **2026-10-04 线上实测快照** 为 EU 21 个型号、
91 个版本、1,157 个章节；这是该方案的观察口径，不是全站实时计数，
也不同于 TM 的句对数量。
**不变量**：目录、生产状态、内容权威源与验收证据要能分别定位；
工作台展示派生事实，不能成为第二个发布源。
运行契约见 [RTD 工作台](../dev/rtd_manual_portal.md)，
快照口径见 [机读语料方案 §2](../dev/machine_readable_manual_corpus.md#2-当前现实2026-10-04-线上实测)。

### 环 13 · 高速扩张后的工程治理（2026-09-28 ～ 10-03，Workstream Y）

产线增长也带来了复杂函数、门面临时接线、散落模块和环境漂移。
[Workstream Y](../dev/code_quality_iterability_plan.md) 将治理拆成边界清晰的任务，
把复杂度、类型、异常、包结构、测试接线与文档生命周期纳入持续护栏。
历史数字必须带口径：09-28 方案基线为 CC≥50 的函数 31 个；
10-03 清理收官记录为 0（最后批次从 24 降到 0）。
测试中的 facade patch 从 363 降到 11；`tools/` 顶层 `.py` 从 398 降到 183，
保留的 11 处接线有明确理由，模块减少包括迁入包，并不代表删除了相同比例功能。
#1399–1407 的拆分使用真实/随机输入的新旧差分；IDML 四个真实目标的
1,431 个 ZIP 部件保持字节一致。入口迁移与包整理延续到 #1423–1428。
**不变量**：扩建必须受持续约束，重构用行为证据验收；
增加规则文件不等于规则已落实，子项完成也不自动代表整条 Workstream 结案。
详细日期、分项和保留理由见 [优化日志](../code_optimization_log.md)。

### 环 14 · Machine Surface（2026-10-01 起，正在建设）

已发布网页不仅给人读，也开始提供供程序精确检索的语义数据。
[EU 查询契约](../dev/eu_manual_query.md) 建立 HTML 语义提取、
`manual-knowledge.json`、回执核验和有来源引用的查询；
10-04 的 [Machine Corpus 方案](../dev/machine_readable_manual_corpus.md) 将
版本身份、块级来源、生成模式、清单和 freshness 分阶段建设。
#1434 合入身份与来源；#1435 合入逐版本清单与新鲜度校验；
#1436 合入工作台覆盖面板。它们是工程落点，代表手册人工抽查与整体线上验收
仍按方案分别完成，
不能用两个 PR 合入替代整体线上验收。
**不变量**：机读面只能由正式内容派生；当前明确标为 `html_compatibility`，
图片仅消费 alt、不冒充 OCR；机器结论保留版本、章节、块和来源，
并在使用前核验当前部署。它是新的消费面，尚不是知识回流闭环。

## 4. 三条反直觉的史实

1. **评审层早于数据上云三周**（03-11 vs 04-01）：系统先解决
   "人怎么改"，再解决"数据从哪来"。评审与门是骨架的第一层加固，
   不是后补的流程。
2. **队列与云数据同一提交出生**（`d90de79c`）：自动化从来不是
   锦上添花，"数据在云上"与"构建不用人跑"是同一个决定的两半。
3. **反模式的化石还在历史里**：`config.je1000f.jp.yaml`（03-10）
   早于家族配置（04-04）。AGENTS 的"不许每机型一个 config"不是
   凭空规定，是自己踩过的坑。

## 5. 不变量清单

| 环 | 不变量 | 今天的载体 |
|---|---|---|
| 内核 | 数据×模板→确定性构建 | `build.py` + Sphinx + 快照 |
| 1 | 差异进数据/配置，不进模板副本 | 家族 config + manifest + 能力矩阵 |
| 2 | 改派生层，不改产物 | `docs/_review` + sync-review |
| 3 | 飞书是数据单一真相 | sync-data 快照 + 队列 |
| 4 | 评审回写不越过正式源的批准边界 | backport 评审派生层 + 模板同步/源表审批 |
| 5 | 工程/业务两平面 | Hello-Docs 镜像 + two_plane_map |
| 6 | 不过门不出货 | check 门族 + publish 资产门 |
| 7 | 参考版式唯一真相，契约钉死 | reference_layout 契约 + pin 护栏 CI |
| 8 | 图有身份/状态/哈希 | asset: 引用 + 注册表 + 血缘 |
| 9 | 发布可自证、可复现 | release manifest/tag + E1 重建证明 |
| 10 | 加产线不加代码 | 语言注册表 + 一条命令新区域 |
| 11 | 共享语义与组件准入，各格式分别验收 | Manual IR / ComponentSpec / 骨架 / conformance |
| 12 | 内容集合可观察，展示不成为发布源 | 冻结目录 / Workspace / source registry |
| 13 | 工程扩建有持续护栏，重构有行为证据 | Workstream Y / ratchets / 差分验证 |
| 14 | 机读派生，不形成第二内容源 | HTML compatibility / 回执 / 身份与清单 |

## 6. 下一阶段（方向，不计为已完成的历史环）

**Shared IR：建设中央标准半成品层。** 现有 IR 与组件共享已经形成部分能力；
长期线是扩大共同语义的覆盖，让 Web、Word、IDML 和 Machine Surface 直接消费
同一份公共语义，各自负责表达。逐步替换 HTML → Machine 的兼容路径，
用现有机读语料作语义迁移基线，而不是一次重写所有 Renderer。
代表试点、边界与各格式验收仍按 REV-39/REV-40 和独立方案推进。

**Knowledge Feedback：让生产经验回到下一次生产。** 先观察 Safety / Warning /
Compliance 的原文、差异与来源，再形成缺口候选，经人工评审决定适用范围和
批准措辞，最后通过该版本声明的模板/评审/正式源编辑面回流。
机器推断不直接变成安规事实；知识观察、审核与回源属于 Phase 2/3，尚未完成。

```mermaid
flowchart LR
  A[生产说明书] --> B[积累版本语料]
  B --> C[机读内容]
  C -.未来.-> D[观察知识与缺口候选]
  D -.-> E[人工评审与批准]
  E -.-> F[回到声明的正式源]
  F -.-> A
```

## 7. RTD 同源展示摘要

以下是本文面向公众的摘要，不是独立台账。事实变化先更新上面的历史与证据，
再同步这段摘要；构建只读此块，所有文案按纯文本转义。
`recorded` 表示历史能力已形成，不表示所有产品、格式或后续治理均验收完成；
`in_progress` 和 `planned` 明确区分当前建设与未来方向。数量如需展示，
须写在附日期的历史说明中，不作为实时计数。

<!-- system-evolution:start -->
```yaml
schema: system-evolution/v1
updated_on: 2026-10-04
title: 从一条自动化脚本，到持续运行的说明书工厂
intro: 每次扩建都来自真实生产中的问题。从让第一份说明书自动生成，到让过去的生产结果帮助下一次生产。
stages:
  - id: kernel
    period: 2026-02 ～ 03
    status: recorded
    title: 最小生产线
    metaphor: 第一台机器跑起来
    summary: 把安全条目交给数据和模板，让同样的输入稳定生成同样的说明书。
    flow: [CSV + RST 模板, RST, PDF]
    detail: 02-15 的内核先生成 PDF，03-05 才加入 Word。多机型、区域入口随后出现，生产原则开始从手工复制转为确定性构建。
    invariant: 结构化数据 × 可复用模板 → 确定性构建。
    evidence: ["file:auto-manual:code-as-doc/architecture/system_evolution_history.md"]
  - id: targets
    period: 2026-03 ～ 05
    status: recorded
    title: 多产品、多区域、多格式
    metaphor: 小作坊开始增加产线
    summary: 同一套生产方法要服务不同产品和市场，差异逐步交给配置、数据与选页规则。
    flow: [数据 + 家族模板, 目标装配, PDF / Word / HTML]
    detail: 从单一目标扩展到型号、区域和语言的组合；家族配置与 manifest 选页减少了逐机型复制模板和配置的需要。
    invariant: 加目标表达差异，优先复用已有结构。
    evidence: ["pr:auto-manual#41", "pr:auto-manual#285"]
  - id: workflow
    period: 2026-03 ～ 07
    status: recorded
    title: 评审、队列与回写
    metaphor: 建立生产和返修流程
    summary: 生成文件之外，还要让人能审核、让任务能排队、让修改回到可追溯的编辑面。
    flow: [正式源, 构建与检查, 评审, 受控回写]
    detail: 评审层先于云数据出现；数据上云与队列同一提交形成。后来工程面和业务面分开，评审回写、模板同步和正式源写入各有边界。
    invariant: 修改沿声明的编辑面回流，再构建和过门。
    evidence: ["pr:auto-manual#21", "pr:auto-manual#343", "pr:auto-manual#360", "file:auto-manual:user-guide/two_plane_map.md"]
  - id: production
    period: 2026-07 ～ 08
    status: recorded
    title: 印刷线、资产与发布追溯
    metaphor: 建立印刷车间和出货记录
    summary: 排版、插图和交付包都进入生产管理；一次发布要能说明用了什么、如何复现。
    flow: [受控内容与资产, IDML / 文档渲染, 验收, 冻结发布]
    detail: InDesign 印刷线采用批准的参考版式；资产有身份、状态和哈希；发布记录绑定数据、工具和交付字节。自动化不能代替原生格式验收。
    invariant: 不过门不出货，发布可追溯、可复现。
    evidence: ["pr:auto-manual#548", "pr:auto-manual#722", "pr:auto-manual#837"]
  - id: corpus
    period: 2026-08 ～ 10
    status: recorded
    title: 真实手册规模化
    metaphor: 工厂扩大，也积累了产品和经验
    summary: 共享语义与组件支持更多语言版本，Web 手册成为持续维护的内容集合，工作台让入口和证据可观察。
    flow: [共享语义与组件, 多语言手册, Web Corpus, Workspace]
    detail: 09-30 的 14 本手册 rollout 留下线上页面与桌面、手机验收证据。10 月工作台继续标出每个版本的内容权威源；发布规模、语料规模和能力成熟度分别呈现。
    invariant: 共享语义约束组件；每个版本仍有自己的权威源与验收证据。
    evidence: ["file:auto-manual:code-as-doc/dev/eu_shared_component_rollout_2026-09.md", "pr:auto-manual#1351", "pr:auto-manual#1431"]
  - id: engineering
    period: 2026-09-28 ～ 10-03
    status: recorded
    title: Workstream Y · 工程治理
    metaphor: 重新铺电、划分车间、安装护栏
    summary: 产线高速增长后，需要降低接线和维修成本，让工厂能继续安全扩建。
    flow: [发现复杂度与接线债务, 分包与拆分, 行为对比, 持续护栏]
    detail: 09-28 基线至 10-03 收官：CC≥50 的函数 31 → 0，测试 facade patch 363 → 11，tools 顶层 .py 398 → 183。模块迁入包，11 处接线有保留理由；这组历史快照不代表所有后续治理都已结案。
    invariant: 用新旧输出和真实目标证明重构没有改变生产行为。
    evidence: ["file:auto-manual:code-as-doc/dev/code_quality_iterability_plan.md", "file:auto-manual:code-as-doc/code_optimization_log.md"]
  - id: machine
    period: 2026-10-01 起
    status: in_progress
    title: 机器读取内容
    metaphor: 增加程序和 Agent 的数据出口
    summary: 把已发布网页整理为可定位、可引用、可核验的语义内容，为检索和后续知识观察准备原料。
    flow: [已发布 HTML, 语义 JSON, 身份与来源清单, 程序 / Agent]
    detail: 当前路径是 HTML-derived / html_compatibility。身份与来源（#1434）、清单与新鲜度（#1435）、工作台覆盖面板（#1436）已合入；代表手册人工抽查与整体线上验收仍待完成。图片仅取 alt，不做 OCR。
    invariant: 机读内容只能生成，不能成为第二个可编辑的正式源。
    evidence: ["pr:auto-manual#1434", "pr:auto-manual#1435", "pr:auto-manual#1436", "file:auto-manual:code-as-doc/dev/machine_readable_manual_corpus.md"]
  - id: shared_ir
    period: 下一阶段 · 按独立试点推进
    status: planned
    title: Shared IR 与知识反馈
    metaphor: 建设中央标准半成品层，让经验回到生产
    summary: 扩大已有 IR 共享能力，让各格式消费共同语义；另建知识反馈流程，让经过评审的经验帮助下一次生产。
    flow: [Shared IR, Web / Word / IDML / Machine]
    detail: 现有 IR 与组件共享已形成部分能力。更完整的 IR-native 多格式消费属于长期线；知识观察和缺口治理属于 Phase 2/3。二者分别立项，不把机器推断直接当作正式安规内容。
    invariant: 同一份公共语义只理解一次；知识回流先保留证据，再经过人工批准。
    evidence: ["file:auto-manual:code-as-doc/architecture/System Evolution Strategy.md", "file:auto-manual:code-as-doc/dev/machine_readable_manual_corpus.md", "file:auto-manual:code-as-doc/dev/manual_revitalization_execution.md"]
feedback:
  title: 下一步，为什么是闭环
  steps: [生产说明书, 积累版本语料, 机器读取, 发现知识与缺口, 人工审核, 回到正式来源, 下一次生产]
  note: 生产、发布与机读已有落点；知识观察、缺口审核和知识回流是未来阶段。让过去的生产结果帮助下一次生产，需要把这后半圈逐步跑通。
```
<!-- system-evolution:end -->
