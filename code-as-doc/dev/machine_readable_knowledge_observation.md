# 欧规说明书知识观察立项（机读 Phase 2）

Status: active · Owner: Auto-Manual maintainer · Created: 2026-10-11

上位计划：[`machine_readable_manual_corpus.md`](machine_readable_manual_corpus.md)（§4 路线、§9 Phase 2 目标）。
Phase 1 验收记录：[`machine_readable_pilot_audit.md`](machine_readable_pilot_audit.md)。

本文件是 Phase 2（Knowledge Observation）的立项文件，包括立项依据、范围、决策、契约草案、
PR 切分与验收标准。§5 的决策已于 2026-10-11 按建议确认，Phase 2a 的实施以本文件为准；
各实施 PR 仍按 §10 另行登记授权。Phase 1 已上线的行为（`manual-knowledge.json` v1、
机读面清单、查询插件）不因本文件改变。

## 1. 立项依据

### 1.1 Phase 1 已验收，当前仍然健康

- 合入与核验：#1434 身份与来源、#1435 清单与新鲜度、#1436 工作台覆盖面板、#1437 试点验收、
  #1439 线上核验；对应授权 MA-249～MA-252 均已失效（见
  [`merge_authorizations_archive.md`](merge_authorizations_archive.md)）。此后 main 没有再改动
  `tools/manual_knowledge/`。
- 2026-10-11 复核：在 Hello-Docs main `5c0a76ef`（冻结目录 `built_at` 2026-10-11T01:57Z）上，
  用与 RTD 相同的构建命令本地重建（RTD 线上地址在本次复核环境中无法访问，线上复核待补）：

| 指标 | 10-04 验收 | 10-11 本地重建 |
| --- | --- | --- |
| EU 型号 / 版本 | 21 / 91 | 21 / 109 |
| 章节 / 块 | 1,157 / 10,745 | 1,376 / 13,431 |
| 警示框 | 874 | 985 |
| 语料大小（上限 32 MiB） | 6.2 MB | 9.1 MB |
| 新鲜度 | 91/91 fresh | 109/109 fresh |
| 无 alt 图片 | 191 / 3,593 | 361 / 4,326 |

一周内新增的 18 个版本全部由清单覆盖校验自动纳入，机制按设计运转。

### 1.2 现有语料已能产出有价值的观察

用临时脚本在 10-11 语料上做了只读试探（脚本不入库，结论未经人工复核，明细见附录 B）：

- **跨语言警示齐套**：把无法识别级别的标签也计入后，仍有 8 个版本的 WARNING 少于同型号英文版
  （JE-1000H nl/pl/pt、JE-2000E pl/pt、JE-3000C nl/pl/pt）。其中 JE-3000C 的
  en/de/fr/es/it/uk 在 UPS 章节都有"不得用于数据服务器、医疗设备"一条 WARNING，
  nl/pl/pt 全文检索不到。
- **语言混入**：JE-3600A/EU/fr 充电章节有一句英文。
- **合规表述**：31 个非英语版本的 RED 符合性声明是英文；是否需要本地化由合规负责人判断。
- **警示用词不统一**：JE-3600A/EU/es 的 CAUTION 同时译作 `PRECAUCIÓN` 与 `Importante`。
- **复用**：英文版共有 51 种不同的警示正文，其中 15 种被 2–6 个型号原文共用；另有 37 对
  近似文本（例如 `0°C` 与 `0 °C`）。

这些正是上位计划 §9 要求的观察类型。

### 1.3 为什么现在做

- **现有检查覆盖不到。** [`docs_lang_parity`](../../tools/check/docs_lang_parity.py)
  （Milestone I1）在 `build.py check` 的目标构建包上检查文字体系、语言块与语言页是否齐全，
  明确不区分拉丁语系与英文；不经过这条路径的发布（如 Git 原生冻结发布）不在它的覆盖内。
  §1.2 的差异都在已发布网页的内容层。
- **正在进行的安全修订可以直接受益。** batch 1465 的 EU 修订（#1473、#1475、#1476、#1478、
  #1479 等）正在推进，Phase 2 的试点可以服务这一轮核对。
- **漂移在累积。** 无法识别的警示标签在新内容中持续出现（§4.1），越晚治理，存量越大。

## 2. 目标与非目标

### 2.1 Phase 2a 目标

1. 从已封存的 EU 机读语料抽取 Safety / Warning / Compliance 知识条目（Knowledge Item），
   每条保留完整版本身份与块级来源。
2. 按受控词表做主题分类；无法判定的写 `unknown` 并标 `needs_review`。
3. 两类比较：同区域跨产品（复用与产品特有）、同产品同区域跨语言（齐套），输出带证据的候选。
4. 条目级新鲜度：内容变化后，只有文本变化的条目及相关比较记录被识别为 stale。
5. 3–5 个型号的人工试点验收，记录精度与误报原因。

### 2.2 非目标

- 跨区域比较（同产品不同区域），留给 Phase 2b（§3.1）。
- Coverage Matrix、Gap Candidate、演化分析、Approved Knowledge 与回流，属于 Phase 3。
- 不改 `manual-knowledge.json` v1 及其 schema 字符串，不改清单既有字段的语义，不改网页 HTML。
- 不在 RTD 构建中运行知识抽取（D7）。
- 不做 OCR；不引入向量库、新数据库或新模型订阅；不用 LLM 产出事实。
- 不修改说明书正文、`docs/publish/**`、飞书源表；不改 OpenClaw 插件。
- 不把任何观察写回内容权威源。

## 3. 范围

### 3.1 Phase 2a / 2b

| | Phase 2a（本次立项） | Phase 2b（另行立项） |
| --- | --- | --- |
| 区域 | EU | EU 与其他区域 |
| 比较 | 同区域跨产品；同产品同区域跨语言 | 同产品不同区域 |
| 消费方 | 离线报告、试点验收记录 | 按需要接入工作台或查询插件 |
| 前提 | Phase 1 | 上位计划 D4 的区域扩展与插件改动；重合型号足够 |

拆分理由：当前冻结目录中与 EU 有重合的型号只有 JE-1000F（EU / US / JP）和 JE-2000F
（EU / CN），不足以支撑跨区域比较；查询插件的
[`validateCorpus`](../../integrations/openclaw/auto-manual-control-layer/lib/manual-query/client.mjs)
对 `region` 和网址都只接受 EU。

### 3.2 数据面（2026-10-11）

- 可做齐套比较：11 个九语型号，共 99 个版本。
- 只参与跨产品比较：JE-300D、JE-500A（仅 en）。
- 8 个多语言合订旧版（`language: multi`、`needs_review`）：照常抽取、可检索，不参与齐套
  （沿用上位计划 D3）。
- 产品功能（`feature`）：[`model_capabilities.csv`](../../data/model_capabilities.csv) 覆盖
  21 个 EU 型号中的 8 个（UPS、TOU、自发自用等）；其余写 `unknown`，不从说明书正文推断。

### 3.3 与现有检查的分工

- I1 `docs_lang_parity` 在构建 / 评审包上守结构齐全，阻断式运行，已知问题登记在
  [`lang_parity_known_exceptions.csv`](../../data/lang_parity_known_exceptions.csv)。
- Phase 2 观察已发布内容，覆盖全部发布路径，只产出候选，不阻断构建或发布。
- 两者发现的问题都回到同一个修改入口（模板、冻结源或 Git 原生源），Phase 2 不新增修改通道。

## 4. 立项必须正视的现状

### 4.1 警示级别识别在漂移

985 个警示框中有 13 个为 `unknown`（识别率 98.7%）：

- 6 个是图标标签 `⚠`，按设计不猜；
- 4 个是 P1-4 记录的源内容缺陷，10-11 仍在：JE-1000H nl `WAARSCHU`、pl `OSTRZE`，
  JE-2000E nl `OK-knop. OPMERKING`，JBP-3600A fr `Important`；
- 3 个来自 10-04 之后发布的内容：JE-3600A uk `ПОРАДА`（TIP 的单数，词表只收了复数
  `ПОРАДИ`）、JE-3600A es `Importante`、JBP-2000B fr `IMPORTANT`。

`Important`、`IMPORTANT`、`Importante` 在对应位置都是英文版的 CAUTION。P1-4 把
JBP-3600A fr 的 `Important` 记为"英文，未翻译"并不准确：这是法语 / 西语使用了词表之外的
警示等级词，应按 Style Guide 的等级词条款决定是纳入映射还是修源（D13）。目前没有任何检查会在
出现新的 `unknown` 标签时提示。

### 4.2 修订号基本不可用

109 个版本中只有 20 个是可信的印刷修订号，84 个是技术快照，4 个无法分类，1 个为
`candidate`。同一型号内部也不一致：JE-1000F 的 en/de/es/fr/it 为 2.7，nl/pl/pt/uk 为技术快照；
JE-3000C 的 en 为 2.10，nl/pl/pt 为技术快照。因此齐套比较无法断言两版属于同一修订（D11）。

### 4.3 只有当前一版

每个 `variant_key` 在语料中只有一版，跨修订比较需要历史语料。Hello-Docs main 的 Git 历史保存了
每次冻结发布，可以按需重建任意一次部署的语料（D12）。

### 4.4 同一型号的各语言可能来自不同谱系

例如 JE-3000C：de 的 Shared IR 有 `page_slots`（指向
`templates/page_shared/de/06_ups_mode.rst` 等），插图来源 PDF 为
`…EUUK-V2.0-2026-07-31.pdf`；nl/pl/pt 是 Git 原生冻结发布（`git_only_frozen`），IR 页面为
`introduction`、`ups`、`eu-declaration` 等，没有 `page_slots`。章节数也不同（en 15、nl 16）。
因此跨语言对齐不能依赖章节序号或块序号。109 个版本中有 83 个带 `manual.ir.json`。

### 4.5 同一条提示的块类型可能不同

JBP-2000B/EU/de 的两条 `HINWEISE` 渲染为表格，JS-100I/EU/en 的两条提示是普通段落，
其他语言则是警示框。11 个九语型号中有 6 个的警示框数量在各语言之间不一致，其中一部分就是这种
呈现差异，不是内容缺失。抽取不能只看 `callout` 块，齐套比较必须容忍块类型差异。

### 4.6 `block_id` 只在原地修改时稳定

`block_id` 由"章节哈希 + 块序号"组成，章节哈希取决于网址和锚点。用 Hello-Docs #200
（JE-1000H EU de LCD 修订）前后两版渲染对比：139 个块 ID 全部保留，只有 1 个块的文本变化。
但插入或删除块会让后续序号整体后移，换路由则全部改变。另外，现有新鲜度以整份网页
（`html_sha256`）为粒度，任何一处改动都会让该版本的全部下游条目变为 stale。

### 4.7 图片盲区在扩大

无 alt 图片从 191 / 3,593 增至 361 / 4,326，JE-3600A 每个语言 13 / 56。图中或图标里的
警示在 Phase 2 中仍不可见（不做 OCR），报告按版本列出盲区规模。

## 5. 决策（2026-10-11 按建议确认）

编号接续上位计划 §7 的 D1–D5。

| # | 问题 | 决定 |
| --- | --- | --- |
| D6 | 范围拆分 | Phase 2a 只做 EU；跨区域比较进 Phase 2b，与上位计划 D4 的区域扩展和插件改动一起另行立项（理由见 §3.1） |
| D7 | 产物与生成位置 | 2a 用离线命令读取已封存的语料与回执后生成，不进 RTD 构建，抽取出错不影响发布；2b 再按消费方需要评估是否进构建 |
| D7a | 产物是否入库 | 不提交，只在本地或制品中生成；试点结论写成验收记录入库（与 P1-4 相同） |
| D8 | 条目身份 | 内容寻址的 `knowledge_id`（含规范化文本哈希），新鲜度按 `knowledge_id` 判断（§6.2）；不改 v1 语料 |
| D9 | 状态边界 | 机器只写 `extracted` / `candidate`；人工结论归 Phase 3 评审台账，试点的人工核对写成验收记录 |
| D10 | 分类与对齐方法 | 确定性规则：多语受控词表加实体锚点（数字、单位、型号、接口名），同一语料输出字节一致。由现有网关模型出候选作为 2a 之后的可选增量，另行确认；不用向量检索 |
| D11 | 修订号 | 不推断；比较结果带 `revision_alignment`（`same` / `different` / `unknown`）。正式修订号由发布元数据补充，另行立项 |
| D12 | 跨修订比较的归属 | 归 Phase 3（与上位计划 §9 一致），P2-0 更正 P1-4 §3.3"跨修订比较归 Phase 2"的说法；2a 产物记录 `source_sha256`，将来可从 Hello-Docs Git 历史重建语料做比较，不新建归档存储 |
| D13 | 警示级别词表 | 补 `ПОРАДА`；`Important` / `IMPORTANT` / `Importante` 按 Style Guide 等级词条款处理：允许则映射为 caution，不允许则作为源缺陷交内容负责人；加 §7 P2-0 的 `unknown` 标签护栏 |
| D14 | 试点验收门槛 | 高置信度齐套候选的人工确认率 ≥ 80%（确认为真实差异，或差异有可解释的原因）；全部误报记录原因 |

## 6. 契约

§6.1、§6.2 已由 P2-1 实现；§6.3、§6.4 随 P2-2、P2-3 落地。

### 6.1 产物

- 命令：`python -m tools.manual_knowledge.observe --site <构建输出目录>` 或
  `--base-url <站点>`，可选 `--output <文件>`、`--previous <旧产物>`。先按
  `manual-deployment.json` 校验语料与清单（与 `manifest` 命令共用同一读取器），不一致则拒绝
  生成并以退出码 1 结束；给出 `--previous` 时报告旧产物中已 stale 的条目与比较记录。
- 产物：`manual-observations.json`，schema `auto-manual-knowledge-observations/v1`。
  头部记录 `corpus_sha256`、`source_sha256`、`generator_version`、`feature_source`；同一语料
  两次运行字节一致。
- 默认写到 `reports/knowledge_observations/<source_sha256 前 12 位>/`，路径由
  [`path_utils.py`](../../tools/utils/path_utils.py) 的 `knowledge_observation_reports_of` 给出；
  该目录已列入 `.gitignore`（D7a）。
- 代码在 `tools/manual_knowledge/observe.py`，不新增 `tools/` 顶层模块。
- 产物不进入 `docs/publish/**`，也不进入 RTD 部署。

### 6.2 Knowledge Item

```json
{
  "knowledge_id": "kn:JE-3000C/EU/en:warning:5c1f…:0",
  "category": "warning",
  "topic": ["ups"],
  "severity": "warning",
  "label": "WARNING",
  "text": "Do not use this product for applications such as data servers or medical devices, …",
  "variant_key": "JE-3000C/EU/en",
  "manual_variant_id": "JE-3000C/EU/en@2.10",
  "observed_context": {
    "model": "JE-3000C", "region": "EU", "language": "en", "language_status": "verified",
    "revision": "2.10", "revision_kind": "printed",
    "release_path": "unclassified", "authority": "unknown",
    "feature": {"UPS功能": true, "TOU/计划充电": true, "LED照明灯": false}
  },
  "source": {
    "section_id": "b5fe50b9efaf9d57ced0396a",
    "section_title": "UNINTERRUPTIBLE POWER SUPPLY (UPS)",
    "block_id": "b5fe50b9efaf9d57ced0396a:6", "block_type": "callout", "item_index": null,
    "source_ref": "JE-3000C/EU/en/md/manual_je3000c_eu_en.html#uninterruptible-power-supply-ups",
    "html_sha256": "…"
  },
  "content_sha256": "5c1f…",
  "status": "extracted",
  "review_flags": [],
  "method": {"generator": "manual-observations/0.1", "rules": ["extract.callout", "topic.ups"]}
}
```

- `knowledge_id`：`kn:` + `variant_key` + `category` + `content_sha256` 前 16 位 + 同一键下的
  出现序号。`content_sha256` 是规范化内容的 SHA-256：NFKC 统一全半角、去掉行首列表符号、
  合并空白，负号、星号和编号照原样保留。警示框的内容包括原文标签和正文，改标签
  （如 WARNING → CAUTION）或改正文都会得到新 ID；插入或删除其他块、换路由不改变 ID，
  `block_id` 与 `source_ref` 每次运行重新解析。
- `label` 保留原文标签，`severity` 取自语料；级别未知的条目带 `severity_unknown`。
- `observed_context.feature` 是 `model_capabilities.csv` 中该型号与区域的全部功能开关；
  没有对应行时写 `"unknown"`，来源写在产物头部 `feature_source`，不从说明书正文推断。
- 条目新鲜度：旧产物中的条目，若其 `knowledge_id` 在当前语料的抽取结果中已不存在，判为
  `stale`；其余条目不受整份网页变化的影响。
- 比较记录新鲜度：任一成员为 `stale`，或任一 `absent_in` 版本的 `html_sha256` 已变化
  （缺失的内容可能已经补上），判为 `stale`。
- 颗粒度：警示框正文一条；列表按项拆分（记录 `item_index`）；表格按行；段落一条。
- `status` 只取 `extracted`（直接抽取）或 `candidate`（比较产生的关系或差异）。`reviewed`、
  `approved`、`superseded` 留给 Phase 3，机器不写。
- 无法判定的字段写 `unknown`，并在 `review_flags` 中写明原因（如 `topic_unknown`、
  `language_multi`、`severity_unknown`）。

### 6.3 抽取范围与分类

- **Warning**：全部 `callout` 块；外加首格为警示等级词的表格行（如 JBP-2000B/EU/de 的
  `HINWEISE`）和以等级词开头的段落。每本手册里解释等级词含义的说明表要排除。
- **Safety**：章节标题命中多语安全章节词表（SAFETY、SICHERHEIT、SÉCURITÉ 等）的块，按 §6.2
  的颗粒度拆分。子类沿用上位计划 §9：通用、电气、电池、充电、存储运输、废弃处理。
- **Compliance**：只记录说明书里实际存在的表述（符合性声明、WEEE、标志说明等），
  `applicability` 一律为 `unknown`，不预设任何法规适用于某个产品。
- **主题受控词表（初版）**：`ups`、`energy_saving`、`ac_output`、`dc_usb_car`、`pv_input`、
  `grounding`、`temperature`、`battery`、`app_wireless`、`connection`。九种语言各自维护词条，
  优先使用数字、单位、接口名这类跨语言不变量；未命中写 `[]` 并标 `topic_unknown`。
  试探结果：10 条简单的英文规则即可覆盖 51 种英文警示正文中的 48 种。

### 6.4 关系与比较记录

```json
{
  "observation_id": "obs:language_parity:JE-3000C/EU:…",
  "kind": "language_parity",
  "scope": {"model": "JE-3000C", "region": "EU"},
  "members": [
    {"knowledge_id": "…", "manual_variant_id": "JE-3000C/EU/en@2.10",
     "source_ref": "…", "severity": "warning"}
  ],
  "absent_in": [
    {"variant_key": "JE-3000C/EU/nl", "manual_variant_id": "JE-3000C/EU/nl@git-20261002-45219a6e-pv-web",
     "searched": "whole_document", "revision_alignment": "unknown", "html_sha256": "…"}
  ],
  "anchors": ["UPS"],
  "confidence": "medium",
  "status": "candidate"
}
```

- `kind` 取值：`exact_reuse`、`near_reuse`、`language_parity`、`product_specific`、`unknown`。
  上位计划 §9 中的 `semantic_variant` 在 2a 不自动判定；`region_specific` 属于 2b。
- 成员保留完整身份与来源，禁止把多条合并成一句而丢失来源。
- `absent_in` 只表示"在所述范围内没有找到对应条目"，不等于错误，必须写明搜索范围与
  `revision_alignment`。`revision_alignment` 为 `unknown` 时，置信度不高于 `medium`。
- 跨语言对齐：先按同型号、同主题、同等级分组，再用锚点（数字加单位、型号、接口名、`UPS`
  等拉丁术语）匹配。块类型不同（警示框 / 表格 / 段落）不影响对齐；没有锚点的条目只给 `low`。
- 三类比较分开输出，不共用一种相似度（上位计划 §9）。

### 6.5 运行摘要

每次运行输出：各版本条目数、主题未判定率、`unknown` 等级标签清单、无 alt 图片数（盲区）、
各类候选的数量与置信度分布。

## 7. 计划（PR 切分）

| PR | 内容 | 主要文件 | 验证 |
| --- | --- | --- | --- |
| 立项 | 本文件；上位计划头部指向本文件；系统演进史环 14 的状态表述 | `code-as-doc/dev/`、`code-as-doc/architecture/system_evolution_history.md` | 文档链接与生命周期检查；系统演变页测试 |
| P2-0 词表与护栏 | D13 的词表调整；`machine_surface_manifest.json` 增加 `unknown` 标签清单（只加字段）；`manifest` 命令对照仓库内的已知例外表报告新增的 `unknown` 标签，不在构建中失败；按 D12、D13 的决定更正 P1-4 §3.2、§3.3 的说法 | `tools/manual_knowledge/identity.py`、`manifest.py`、`data/` 下新的例外表、测试、P1-4 验收记录 | 单元测试；本地重建前后对比：网页 HTML 与语料其他字段不变 |
| P2-1 契约与身份 | 观察命令与产物骨架；`knowledge_id`、条目与比较记录的新鲜度 | `tools/manual_knowledge/`、`tools/utils/path_utils.py`、测试 | 确定性（两次运行字节一致）；原地改字、插入块、换路由三种用例 |
| P2-2 抽取与分类 | §6.3 的抽取范围、多语词表、等级词说明表排除 | 同上 | 规则用例；本地重建上的覆盖率与未判定率报告 |
| P2-3 比较与关系 | 复用聚类、跨语言齐套候选、置信度 | 同上 | 用例覆盖呈现差异（表格 / 段落）、谱系差异、`absent_in` |
| P2-4 试点验收 | 3–5 个型号人工核对，记录精度与误报原因；交内容负责人的问题清单 | `code-as-doc/dev/` 下的验收记录 | 见 §8 |

试点样本建议：JE-3000C（谱系差异、UPS）、JE-1000H（拆词标签、batch 1465）、JE-3600A
（较新、语言混入、等级词不统一）、JBP-2000B（呈现差异、配件）、JS-100I（功能简单、太阳能板）。

实现（P2-0）：词表补 `ПОРАДА`（tip），生成器升为 `manual-knowledge/1.2`。Style Guide 尚未裁定
`Important` / `IMPORTANT` / `Importante`，按 D13 暂不映射；它们与 `⚠` 图标标签、P1-4 记录的源缺陷一起
登记在 [`machine_surface_known_callout_labels.csv`](../../data/machine_surface_known_callout_labels.csv)。
清单逐版本记录 `unknown` 标签，`manifest` 命令报告新增与已不再出现的标签（上位计划 §5.5–§5.6）。

实现（P2-1）：`tools/manual_knowledge/observe.py` 实现 §6.1 的命令与产物和 §6.2 的条目契约，
与 `manifest` 命令共用部署读取器。P2-1 只把全部警示框记为 `warning` 条目（`topic` 为空并标
`topic_unknown`）；其余载体和主题分类随 P2-2，比较记录随 P2-3。10-11 本地重建上共 985 条，
`knowledge_id` 全部唯一（JE-2000F nl、pt 各有一条警示在同一手册里出现两次，出现序号为 1），
两次运行字节一致，产物约 1.8 MB。

每个 PR 的本地验证按 [`AGENTS.md`](../../AGENTS.md) §8.5：`ruff`、`unittest`、改动
`tools/` 边界时的 `check_maintainability_guardrails`、文档链接检查；改 `path_utils` 时加
`mypy tools/utils`。

## 8. 验收标准

- **身份**：每条知识条目都能恢复 `manual_variant_id`、`source_ref`、`content_sha256`；关系记录中
  每个成员保留完整身份。
- **证据**：每条候选至少有一个能回到线上锚点的 `source_ref`；`absent_in` 写明搜索范围与修订
  对齐状态。
- **如实**：机器不写 `reviewed` / `approved`；规则推断不记为事实；无法判定写 `unknown` 并标
  `needs_review`。
- **确定性**：同一语料运行两次，产物字节一致。
- **新鲜度**：内容变化后，只有文本变化的条目、引用它们的比较记录，以及 `absent_in` 版本已变化
  的比较记录变为 stale。
- **兼容**：`manual-knowledge.json`、清单既有字段、网页 HTML 字节不变；查询插件测试通过；
  RTD 构建不运行观察命令。
- **试点精度**：高置信度齐套候选中，人工确认为真实差异或可解释差异的比例 ≥ 80%（D14）；
  全部误报记录原因。
- **SSOT**：观察产物不进入 `docs/publish/**`，不写入任何权威源；问题只以清单形式交内容负责人。

## 9. 风险与应对

| 风险 | 应对 |
| --- | --- |
| 误报给内容团队增加负担 | 只交高置信度候选，附 `source_ref` 与对照原文；absent ≠ error |
| 谱系或呈现差异导致对齐错误 | 锚点对齐，容忍块类型差异；记录 `release_path` 与 `authority` |
| 修订不明导致误判"缺失" | 一律带 `revision_alignment`；为 `unknown` 时置信度不高于 `medium` |
| 多语词表的维护成本 | 词条按语言集中管理；未命中写 `unknown`，不扩大猜测 |
| 语料持续增长 | 观察产物独立于 v1 语料，离线生成 |
| 与发布节奏冲突 | 只读已封存语料，不改发布路径 |

## 10. 授权与流程

- 每个 PR 按 [`AGENTS.md`](../../AGENTS.md) §8 与 [`merge_authorizations.md`](merge_authorizations.md)
  执行。已归档的 MA-251 明确不含 Phase 2，实施 PR 需要新的登记，取号用
  `python -m tools.next_registry_id ma`。
- §5 于 2026-10-11 确认后本文件转为 `active`；
  [`system_evolution_history.md`](../architecture/system_evolution_history.md) 环 14 中
  "Phase 2／3 尚未立项"的表述在立项 PR 中同步更新。
- 观察发现的源内容问题只交内容负责人，在该版本声明的权威源修改后重新发布；不在机读面或
  观察产物中修正。

## 附录 A：2026-10-11 复核数据

来源：Hello-Docs main `5c0a76ef` 本地重建（生成器 `manual-knowledge/1.1`）。

| 项目 | 数值 |
| --- | --- |
| 块类型 | 段落 6,194、标题 2,497、图片 2,118、表格 1,026、警示框 985、列表 611 |
| 警示级别 | caution 500、note 298、warning 116、tip 58、unknown 13 |
| 修订类型 | technical_snapshot 84、printed 20、unclassified 4、candidate 1 |
| 语言状态 | verified 101、needs_review 8 |
| 发布路径 / 权威源 | `git_only_frozen` / `git_native` 47；`unclassified` / `unknown` 62 |
| 带 Shared IR | 83 / 109 |
| 产品功能覆盖 | 8 / 21 个 EU 型号 |

## 附录 B：试探性候选（未经人工复核）

| # | 类型 | 版本 | 现象 | 证据 |
| --- | --- | --- | --- | --- |
| 1 | 齐套 | JE-3000C/EU nl、pl、pt | en/de/fr/es/it/uk 的 UPS 章节有"不得用于数据服务器、医疗设备"的 WARNING，三语全文检索不到；三语为 Git 原生谱系，en 为 2.10、三语为技术快照 | en：`JE-3000C/EU/en/md/manual_je3000c_eu_en.html#uninterruptible-power-supply-ups`；nl 同章节：`JE-3000C/EU/nl/md/manual_je3000c_eu_nl.html#ononderbroken-stroomvoorziening-ups` |
| 2 | 齐套 | JE-1000H/EU nl、pl、pt；JE-2000E/EU pl、pt | 计入 `unknown` 标签后，WARNING 仍比 en 少 1 | 仅计数，待逐条对齐 |
| 3 | 语言混入 | JE-3600A/EU/fr | 英文句 `*The car charging cable is sold separately.` | `JE-3600A/EU/fr/md/manual_je3600a_eu_fr.html#charge`（块 `3179bc6e054bb1ad96985cf0:18`） |
| 4 | 合规表述 | 31 个非英语版本 | RED 符合性声明为英文；是否需要本地化由合规负责人判断 | 词表启发式检出 |
| 5 | 等级词 | JE-3600A/EU/es | CAUTION 同时用 `PRECAUCIÓN` 与 `Importante` | `JE-3600A/EU/es/md/manual_je3600a_eu_es.html#cargando` |
| 6 | 等级词 | JBP-2000B/EU/fr、JBP-3600A/EU/fr | CAUTION 写作 `IMPORTANT` / `Important` | `JBP-2000B/EU/fr/md/manual_jbp2000b_eu_fr.html#connexions`、`JBP-3600A/EU/fr/md/manual_jbp3600a_eu_fr.html#connexions` |
| 7 | 词表缺口 | JE-3600A/EU/uk | `ПОРАДА`（TIP 单数）未收录 | `JE-3600A/EU/uk/md/manual_je3600a_eu_uk.html#id5` |
| 8 | P1-4 遗留 | JE-1000H/EU nl、pl；JE-2000E/EU nl | 被拆开或并入其他文字的标签仍在（JBP-3600A/EU/fr 见第 6 条） | 见 P1-4 §3.2 |
| 9 | 呈现差异 | JBP-2000B/EU/de、JS-100I/EU/en | 提示渲染为表格或段落，影响警示框计数，不一定是内容缺失 | 对齐需容忍（§4.5） |

## 附录 C：复现

auto-manual 与 Hello-Docs 为同级检出时，在 auto-manual 根目录运行：

```bash
PYTHONPATH="$PWD" python -m sphinx -q -b html \
  -D extensions=myst_parser,tools.rtd.portal \
  -D rtd_knowledge_dir=../Hello-Docs/docs/knowledge \
  ../Hello-Docs/docs/publish/web .tmp/machine-phase2/site
python -m tools.manual_knowledge.manifest --site .tmp/machine-phase2/site
```

§1、§4 与附录 A、B 的数字来自对上述构建输出（`manual-knowledge.json`、
`machine_surface_manifest.json`）的临时分析脚本，不是生产产物；P2-1 之后以观察命令的输出为准。
