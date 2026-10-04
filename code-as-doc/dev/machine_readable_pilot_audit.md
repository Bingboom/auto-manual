# 欧规机读面 Phase 1 试点验收记录（P1-4）

Status: done · Date: 2026-10-04 · 计划：[`machine_readable_manual_corpus.md`](machine_readable_manual_corpus.md) §6 P1-4、§8

## 1. 范围与方法

对象：线上 `https://ht-doc.readthedocs.io/manual-knowledge.json`（P1-1 合入后的
部署，91 个 EU 版本、10,745 个块）与同一部署的已发布网页、`manual-deployment.json`。

样本覆盖计划要求的五类产品，并加一个 Git-only 发布版本：

| 样本 | 类别 | 版本 / 修订 | 发布路径 |
| --- | --- | --- | --- |
| JE-1000F / EU / en | 较老、功能复杂 | 2.7（printed） | unclassified |
| JE-1000F / EU / nl | 同上，Git 原生源 | git-…（technical_snapshot） | git_only_frozen · git_native |
| JE-3600A / EU / en | 较新、功能复杂 | 2026-05-25.9（unclassified） | unclassified |
| JS-100F / EU / multi | 功能简单（太阳能板），多语言合订 | 1.0（printed） | unclassified |
| JA-AD01A / EU / multi | 配件，多语言合订 | git-…（technical_snapshot） | unclassified |
| JE-2000F / EU / en | 计划中"警示语有演化"候选 | 2.6（printed） | unclassified |

每个样本做的检查：

1. 线上网页去掉 RTD 注入的 head 标签后，字节哈希等于语料的 `html_sha256`，也等于部署回执记录；
2. 每个块都有 `block_id`（唯一）与 `source_ref`，且 `source_ref` 的锚点在线上网页中存在；
3. 块文本不含 CSS / JS / 主题 / 导航噪声（正则检查脚本、样式、`¶`、残留标签）；
4. 网页正文中的表格数、图片数与语料对得上；
5. 警示框标签与 `severity` 逐个人工核对。

警示框 `unknown` 和噪声两项另外对全量 91 个版本做了检查。

## 2. 结果

| 验收项（计划 §8） | 结果 |
| --- | --- |
| Identity | 通过。6 个样本的全部块都能恢复 Model / Region / Language / Revision（或 `null` + `revision_kind`）、`manual_variant_id`、`source_ref`；块 ID 无重复；全量 91 个 `manual_variant_id` 无重复。 |
| Content · 噪声 | 通过。全量 10,745 个块均未命中噪声规则。 |
| Content · 结构 | 通过。样本表格数网页 = 语料（12/12、12/12、12/12、3/3、4/4、13/13）。 |
| Content · 警示级别 | 通过。样本中全部警示框标签（WARNING / CAUTION / NOTE / TIP，WAARSCHUWING / OPGELET / OPMERKING / TIPS）人工核对 100% 正确；无法识别的标 `unknown`，见 §3。 |
| Provenance | 通过。样本中所有 `source_ref` 锚点在线上网页中存在；6 个样本线上字节与提取时完全一致。 |
| Freshness | 通过（P1-2）。用线上语料与回执生成清单再校验：91/91 fresh；篡改、过期、下线由单元测试覆盖。 |
| SSOT | 通过。机读面只在构建时从已发布网页生成，仓库中没有手工维护的机读正文。 |
| 兼容 | 通过。网页 HTML 字节未变；OpenClaw 插件 `validateCorpus` 接受新增字段的语料。 |
| 如实 | 通过。语料、清单、工作台均标 `html_compatibility`，没有显示为 IR-native。 |

## 3. 发现

### 3.1 已在本 PR 修复：图标型警示框标签为空

JE-1000F 与 JE-2000F 的 nl / pl / pt / uk Git 原生版本里，安全须知首个警示框
的标签只是一个警示三角图标（`<img alt="⚠">`），原提取只取文字，标签为空。
现在空标签时取标签内图片的 alt 作为标签（`⚠`），`severity` 仍为 `unknown`：
图标本身不足以区分 warning 与 caution，不做猜测。影响 6 个块，章节与块 ID 不变。

### 3.2 源内容缺陷（不在机读面修，应修说明书源）

提取忠实反映了已发布网页，以下问题出在网页本身，需要内容负责人在权威源修正：

| 版本 | 现象 |
| --- | --- |
| JE-1000H / EU / nl | 警示标签显示为 `WAARSCHU`，正文末尾多出 `UWING`：单词 WAARSCHUWING 被拆到两个单元格 |
| JE-1000H / EU / pl | 警示标签为 `OSTRZE`，同类拆词（OSTRZEŻENIE） |
| JE-2000E / EU / nl | 警示标签为 `OK-knop. OPMERKING`：上一步骤的"OK-knop."被并入标签；正文也在句中截断 |
| JBP-3600A / EU / fr | 警示标签为 `Important`（英文，未翻译） |

这 4 处在机读面中均为 `severity: unknown`，不会被误判成正确级别。

### 3.3 已知边界（Phase 1 不处理）

- **图片**：语料只为正文中的独立图片生成图片块；LCD 图标表、符号表里的图标
  计入覆盖统计，含义由表格文字承载，图片 alt 多为文件式键名（如
  `warning_triangle`）。图片内文字没有转写（`alt_only_no_ocr`）。全量无 alt
  图片 191 / 3,593。
- **修订号**：JE-3600A 的 `2026-05-25.9` 及其他日期式版本号不是可信修订号，
  标 `unclassified`；65 个版本是技术快照。正式修订号需要发布元数据补充，不由
  机读面推断。
- **警示演化（JE-2000F）**：线上只有每个版本的当前一版，无法在 Phase 1 验证
  跨修订的警示演化。JE-2000F 各语言之间的差异（en 为 WARNING，nl / pl 为图标
  标签）是不同发布路径的呈现差异，不是修订演化。跨修订比较归 Phase 2。

## 4. 结论

Phase 1 验收标准全部满足。机读面在 v1 上具备稳定身份、可回溯来源、部署封存
的清单与新鲜度校验，并在工作台如实展示为 HTML 兼容路径。§3.2 的 4 处源内容
缺陷交内容负责人在权威源修正；§3.3 的边界留给 Phase 2 立项时考虑。

## 5. 复现

```
python -m tools.manual_knowledge.manifest --base-url https://ht-doc.readthedocs.io
```

样本检查使用 `tools.rtd.deployment_receipt.FetchSession` 读取线上网页，
`_without_rtd_proxy_injection` 去掉 RTD 注入后比对 `html_sha256`，再用
BeautifulSoup 收集网页锚点、表格与图片，与语料逐项对照。
