# 欧规说明书机读内容与知识抽取建设

Status: proposed · Owner: Auto-Manual maintainer · Created: 2026-10-04

本文件是需求与分阶段计划。第一阶段（Machine Corpus）的实施以本文件为准；
第二、三阶段只记录目标与边界，开工前各自再立项。现有查询链路的运行约定仍以
[`eu_manual_query.md`](eu_manual_query.md) 为准，本文件不改变它已上线的行为。

## 1. 背景

主流欧规便携储能说明书已基本完成 Web 化，形成覆盖多产品、多语言的真实
Manual Corpus。这批 Web Manual 持续按纸质说明书、产品变更、警示语更新和规格
修订维护，可以进一步用于：Safety 内容治理、Warning / Caution 治理、
Compliance / Certification 内容分析、跨产品比较、新旧 Manual 演化分析和
内容覆盖缺口发现。

## 2. 当前现实（2026-10-04 线上实测）

线上 `manual-knowledge.json`（schema `auto-manual-knowledge/v1`）由
`tools/manual_knowledge/` 在 RTD 构建末尾从**已发布网页 HTML** 提取，
部署回执 `manual-deployment.json` 记录它和每份网页的哈希；OpenClaw 钉钉插件
读取前校验回执与哈希。实测规模：EU 21 个型号、91 个版本、1,157 个章节，
6.2 MB；块类型为段落 4,754、标题 2,108、图片 1,673、表格 897、
警示框 874、列表 439。

因此当前机读面是：

```
Published HTML → Semantic Extraction → manual-knowledge.json
```

属于 **HTML-derived Compatibility Surface**，不是与网页同源直接生成的
Native Machine Surface。工作台「工作入口」图已标注
「当前：HTML-derived · Compatibility」。这一现实必须在 Workspace、Manifest
和文档中如实表达，不得描述成 IR-native。

已具备：去噪的语义提取（样式、脚本、导航、主题外壳排除；段落、列表、
表格含合并单元格、警示框、图片 alt 保留）；构建内生成与回执哈希；
完整清单覆盖校验（漏掉任何已发布 EU 版本即构建失败）。

已知不足（第一阶段要解决的）：

| 项目 | 现状 |
| --- | --- |
| 版本身份 | 文档 `id` 是网址哈希，换路由就变；没有 `manual_variant_id` |
| 修订号 | `version` 字段 91 个里 65 个是 `git-<日期>-<sha>` 技术快照号，另有 `candidate`、日期等，不是纸质修订号 |
| 语言 | 8 个旧版为多语言合订本，`lang: null`、`language_scope: legacy_unspecified` |
| 块级来源 | 只有章节锚点和 ID；块没有 `block_id` / `source_ref` |
| 来源绑定 | 只有整棵冻结源指纹和网页哈希；没有 `source_kind`、`generator_version`，未关联 Git-only 发布的 `source_manifest.json` |
| 生成模式 | 未记录 |
| 警示级别 | 警示框只有原文标签（CAUTION、VORSICHT、PRZESTROGA 等 14 种语言），没有统一级别 |
| 清单与状态 | 没有逐版本的机读面清单与状态 |
| 图片 | 只取 alt，不做 OCR；图中或图标里的警示不可见 |
| 区域 | 只导出 EU；插件拒收非 EU 数据 |

## 3. 原则

1. **机读内容不是新的 SSOT。** 不得形成「正式 Manual Source + 人工维护
   Machine JSON」双内容源。机读内容只能生成，禁止人工维护正文。修改回到该
   版本声明的内容权威源，重新构建发布后重新生成机读面。
2. **SSOT 是唯一权威，不是唯一格式。** 不同版本的权威源可以是结构化源、
   Git 原生 RST / MyST、冻结源或 Manual IR。不要求先统一格式才进入语料；
   要求的是：任意版本都能唯一确定该去哪里改，同一时刻不存在两个可独立编辑的
   正式内容源。
3. **Knowledge Layer 与 Surface 分离。** 内容权威源 → 人读面 / 机读面 →
   知识层。知识层是从多个版本观察抽取出的知识，不是正式内容源，不得直接写回
   权威源。
4. **如实标注成熟度。** `html_compatibility` 描述架构路径，不代表内容过期
   或低质量。

## 4. 分阶段路线

| 阶段 | 内容 | 难度 | 时机 |
| --- | --- | --- | --- |
| Phase 1 Machine Corpus | HTML → Semantic JSON → Variant / Manifest → Freshness / Provenance | 中 | 现在做 |
| Phase 2 Knowledge Observation | Safety / Warning / Compliance 抽取 → 分类 / 聚类 / 差异 → 保留证据 | 中高 | Phase 1 验收后 |
| Phase 3 Knowledge Governance | Coverage、Evolution、Gap Candidate、Review、Approved Knowledge、Backflow | 高 | Phase 2 稳定后 |
| 并行长期线 Shared IR | 逐步把 HTML → Machine 替换为 IR → Human、IR → Machine | 独立立项 | 不与以上绑定 |

## 5. Phase 1 需求（Machine Corpus）

### 5.1 范围

需求原稿 §27 第一阶段列了 12 项，其中 7–10（知识抽取、聚类、覆盖矩阵、
缺口候选）属于 Phase 2。Phase 1 只做：

1. Manual Variant 身份契约
2. HTML 语义提取（补齐）
3. 机读面（在现有 v1 上增量）
4. 清单（Manifest）
5. 来源绑定（Source Binding）
6. 新鲜度校验
7. 来源核验（Provenance Verification）
8. 3–5 本代表性 EU 说明书的人工抽查

区域范围：Phase 1 只做 EU（待确认，见 §7 D4）。

### 5.2 Manual Variant 身份

`Manual Variant = Model × Region × Language × Revision` 是最小的内容、溯源和
分析单元。Region 与 Language 是独立维度，禁止由语言推导区域：
`JE-1000F / EU / en ≠ JE-1000F / US / en`。

身份分两层（待确认，见 §7 D2）：

```json
{
  "variant_key": "JE-1000F/EU/en",
  "manual_variant_id": "JE-1000F/EU/en@2.1",
  "model": "JE-1000F",
  "region": "EU",
  "language": "en",
  "revision": "2.1",
  "revision_kind": "printed"
}
```

- `variant_key` 不随修订、路由或生成模式变化，用于跨修订演化分析。
- `revision` 只放可信的说明书修订号。技术快照号（`git-…`）、`candidate`
  不冒充修订号：`revision: null`，`revision_kind: "technical_snapshot"`，原值
  保留在 `publication_version`。
- 多语言合订旧版：`language: "multi"`、`language_status: "needs_review"`，
  可检索，不参与多语言齐套分析（待确认，见 §7 D3）。
- 机读面以后从 `html_compatibility` 迁移到 `ir_native` 时，`variant_key` 和
  `manual_variant_id` 都不得因此改变。

### 5.3 语义提取（补齐）

目标是 `HTML → Semantic Manual Representation`，不是 `HTML → Plain Text`。
在现有提取上补：

- 每个块确定性的 `block_id`（章节 ID + 块序号），以及 `source_ref`
  （网页路由 + 章节锚点）。
- 警示框 `severity`：按多语言标签词表归一为 `warning` / `caution` / `note` /
  `tip`；识别不了的标 `unknown`，保留原文 `label`。
- 图片块保持 `alt_only_no_ocr` 覆盖声明；在清单中统计每个版本的无 alt 图片数，
  作为 Phase 2 的已知盲区。

现有排除规则与结构保留规则不变。

### 5.4 机读面元数据与来源绑定

每个版本记录：

```json
{
  "machine_surface": {
    "source_kind": "published_html",
    "generation_mode": "html_compatibility",
    "target_mode": "same_source_native",
    "generator_version": "manual-knowledge/<语义版本>"
  },
  "source": {
    "route": "JE-1000F/EU/en/md/manual_je1000f_eu_en.html",
    "html_sha256": "…",
    "frozen_source_sha256": "…",
    "authority": "git_native | structured | unknown",
    "source_manifest": "<Git-only 发布时 source_manifest.json 的位置或 null>",
    "published_at": "…"
  }
}
```

`generation_mode` 取值：`html_compatibility`、`source_native`、`ir_native`。
`authority` 只写能从发布元数据可靠得到的值；得不到写 `unknown`，不推断。

### 5.5 Manifest

新增 `machine_surface_manifest.json`，与 `manual-knowledge.json` 同一次构建
生成，并纳入部署回执。每个版本一行：

| 字段 | 说明 |
| --- | --- |
| variant_key / manual_variant_id | 身份 |
| model / region / language / revision | 维度 |
| generation_mode | 架构路径 |
| html_sha256 / surface_sha256 | 来源与产物哈希 |
| status | `fresh` / `stale` / `failed` / `unavailable` |
| counts | 章节、块、警示框（按 severity）、无 alt 图片 |

状态与生成模式分开记录。

### 5.6 新鲜度

```
Published HTML hash ↔ Machine Surface source hash → match: fresh / mismatch: stale
```

机读面与网页同一次构建生成，构建时天然一致；`stale` 主要用于缓存副本和下游
产物（Phase 2 的知识记录引用的网页哈希与当前不一致）。提供校验脚本，用当前
部署回执判断任一机读产物是否 stale。Agent 默认不得把 stale 内容当作当前正式
内容回答（现有插件已在回执不一致时拒绝回答）。

### 5.7 Workspace

机读面面板保留兼容路径说明，并增加：总版本数、fresh / stale / failed /
unavailable 数、各生成模式数量。长期希望看到 HTML Compatibility 下降、
IR Native 上升，但这不是 Phase 1 的目标。

### 5.8 兼容性约束

- OpenClaw 插件严格校验 `schema == "auto-manual-knowledge/v1"`、
  `region == "EU"`、文档 `id` 唯一等。Phase 1 只在 v1 上**增加字段**，不改
  `schema` 字符串、不改现有字段语义、保留现有 `id`（新增 `manual_variant_id`
  并行）；插件无需同步发布（待确认，见 §7 D5）。
- 文件大小上限 32 MiB（`deployment_receipt.MAX_FILE_BYTES`），当前 6.2 MB。
- 所有已发布网页 HTML 字节不变。

## 6. Phase 1 计划（4 个 PR）

| PR | 内容 | 主要文件 | 验证 |
| --- | --- | --- | --- |
| P1-1 身份与来源 | `variant_key` / `manual_variant_id` / 修订号拆分 / 多语言合订标注；`machine_surface` 与 `source` 元数据；`block_id` / `source_ref`；警示级别归一 | `tools/manual_knowledge/`、`tests/test_manual_knowledge.py` | 单元测试；冻结语料基线与候选构建对比：网页 HTML 字节不变，现有字段不变，插件测试通过 |
| P1-2 清单与新鲜度 | `machine_surface_manifest.json` 生成并纳入回执；stale 校验脚本 | `tools/manual_knowledge/`、`tools/rtd/deployment_receipt.py`（仅纳入清单） | 篡改 / 过期 / 缺失用例；回执校验 |
| P1-3 工作台 | 机读面面板覆盖统计 | `tools/rtd_portal_assets/manual_workbench.html`、`tools/rtd/` | Sphinx 构建 + 桌面 / 手机截图 |
| P1-4 试点验收 | 3–5 本代表性 EU 说明书人工抽查与报告 | `code-as-doc/dev/` 验收记录 | 见 §8 |

代表性样本需覆盖：较老产品、较新产品、功能简单产品、功能复杂产品、已知发生过
Safety / Warning 演化的产品。候选：JE-1000F（老、复杂）、JE-3600A（新、
复杂）、JS-100F（简单、太阳能板）、JA-AD01A（配件）、JE-2000F（警示语有演化，
待核实）。

每个 PR 按 AGENTS.md §8 与 `merge_authorizations.md` 流程：先登记授权，
全部检查通过后合入，再核验 Hello-Docs 同步、RTD 构建与线上产物。

## 7. 待确认决策

| # | 问题 | 建议 |
| --- | --- | --- |
| D1 | Phase 1 是否包含知识抽取、聚类、覆盖矩阵、缺口候选 | 不包含，归 Phase 2 |
| D2 | 修订号与身份 | `variant_key` 不含修订；技术快照不当修订号（§5.2） |
| D3 | 8 个多语言合订旧版 | 标 `multi / needs_review`，不参与齐套分析；暂不拆分 |
| D4 | 区域范围 | Phase 1 只做 EU；US 等区域在 Phase 2 跨区域比较前，与插件改动一起扩展 |
| D5 | 格式演进 | 在 v1 上只增字段，外加独立 Manifest；不升 schema |

## 8. Phase 1 验收标准

- **Identity**：每个版本、章节、块都能恢复 Model、Region、Language、
  Revision（或明确的 `null` + 原因）、`manual_variant_id`、`source_ref`；
  聚合过程不丢身份。
- **Content**：抽查样本中不含 CSS / JS / 主题 / 导航噪声；章节、标题、段落、
  警示、步骤、表格、图片说明结构保留；警示级别归一正确率人工抽查 100%
  （无法识别的标 `unknown`）。
- **SSOT**：机读面不形成第二个可人工维护的内容源；仓库中不存在手工编辑的
  机读正文。
- **Freshness**：网页更新后，旧机读产物可被识别为 stale；当前构建产物为
  fresh。
- **Provenance**：抽查样本中每个块都能通过 `source_ref` 回到线上原网页锚点。
- **兼容**：已发布网页 HTML 字节不变；现有插件与查询测试全部通过。
- **如实**：工作台与 Manifest 显示 `html_compatibility`，不显示为 IR-native。

## 9. Phase 2 / Phase 3 目标（开工前另行立项）

### Phase 2 Knowledge Observation

- 范围：Safety（通用、电气、电池、充电、存储运输、废弃处理）；Warning /
  Caution（UPS、节能模式、AC / DC 输出、PV 输入、接地、温度、电池、App /
  无线）；Compliance / Certification 只抽取说明书实际存在的表述，禁止预设
  某法规适用于某产品。
- Knowledge Item 至少包含：`knowledge_id`、`category`、`topic`、`text`、
  `manual_variant_id`、`observed_context`（model、region、language、revision、
  可可靠获得时的 feature）、`source`（section、block、source_ref）、`status`
  （extracted / candidate / reviewed / approved / superseded）。AI 推断的适用性
  不得记录为事实，无法确认时写 `unknown` / `needs_review`。
- 聚类不破坏版本身份：簇内保留每个成员的完整身份与来源，禁止把多条警示总结
  成一句而丢失来源。关系至少区分 exact reuse、near reuse、semantic variant、
  product-specific、region-specific、language parity variant、unknown；
  语义相似不等于可以自动合并，canonical wording 必须经过评审。
- 三类比较分开：同区域不同产品（产品族覆盖）、同产品不同区域（法规、认证、
  警示、规格差异）、同产品同区域不同语言（齐套 / parity），不得混为一种
  语义相似度。
- 已知盲区：图片 / 图标中的警示（无 OCR）不可见。

### Phase 3 Knowledge Governance

- Coverage Matrix：知识 × 版本，状态 present / absent / not_applicable /
  unknown / needs_review；absent ≠ error。
- 时间演化：修订或日期数据可靠时，可以说「D 更常出现在较新的说明书中」，
  不能直接说「旧说明书都应增加 D」。
- Gap Candidate：AI 负责找差异、找相似产品、给证据、提候选和置信度；不负责
  法规 / 认证适用性的最终裁决，必须人工评审。
- 回流：Knowledge Finding → Gap / Change Candidate → 人工 / 产品 / 认证评审 →
  Approved Change → 内容权威源 → 构建发布 → 人读面 → 机读面刷新 → 知识抽取，
  形成闭环；知识发现不得直接写入权威源。
- Agent 查询：优先读机读语料，回答必须保留来源（例如：哪些 EU 说明书包含 UPS
  警示、某产品 EU 各语言警示是否齐套、EU 与 US 英文的 Safety 差异、某警示最早
  出现在哪个修订、哪些说明书可能存在覆盖缺口）。

## 10. 长期线：Machine Surface Native Generation

目标：把 `manual-knowledge.json` 的生成源从 Published HTML Extraction 迁移到
Assembly / Shared IR，使人读面与机读面成为同一次生产的两个确定性派生物，
机读面成为 Shared Manual IR 的只读 projection，而不是独立内容模型。

```
迁移前：HTML → manual-knowledge.json
迁移后：IR → HTML；IR → manual-knowledge.json
```

验收：新旧 JSON 语义等价；Variant 身份与 provenance 不丢；Agent 查询不退化；
人读面 HTML 不发生非预期变化。完成后工作台标签由
「HTML-derived · Compatibility」改为「IR-native · Same-source」。
前提是 Shared IR 覆盖面足够；作为独立 Workstream，不与 Phase 1–3 绑定。

## 11. 非目标

- 不重构说明书构建流水线，不改变 `manual-knowledge.json` 的生成方式
  （仍从已发布 HTML 提取）。
- 不修改说明书正文、`docs/publish/**`、飞书源表。
- 不引入向量库、新数据库或新模型订阅。
- 不做 OCR。
- 不扩大机器人或网关权限。
