# 插图资产槽位：多维表已建成记录

- 执行日期：2026-09-08
- 上级计划：[可编辑插图资产与设计交付计划](editable_asset_delivery_debt_plan_2026-09.md)
- 相关：[A0 试点范围与缺口清单](asset_pilot_a0_scope_2026-09.md)、
  [JE-1000F EU 母版实测](asset_pilot_a1_master_editability_2026-09.md)
- 状态：**已执行完毕并回读验证**。这是一次线上写库，不是计划。

## 1. 做了什么

把构建实际读的每一个插图资产，在飞书 `文档构建` Base 里建成槽位：
资产有身份行，文件有位置可传。任何人画好图，往对应槽位的附件位一传就行，
不需要先懂 `asset_registry.csv`，也不需要找特定的人。

写入前 `04_资产定义` 只有 27 行，覆盖构建实际使用的 182 个资产中的 15%。
其余 155 个在多维表里根本不存在，「在表里管资产」实际上管不到。

| 表 | 写入前 | 新建 | 写入后 |
| --- | --- | --- | --- |
| `04_资产定义` | 27 | **+155** | **182** |
| `04_资产导出物` | 183 | **+192** | **375** |
| `04_资产源文件` | 3 | 0 | 3 |

写入后 `04_资产定义` 的 182 行与 `data/asset_registry.csv` 的 182 行一一对应，
无多、无少、无重复。全部为新增，未修改也未删除任何既有行。

## 2. 一个槽位由什么组成

多维表里「一张图」跨两张表，因为定义表没有附件字段：

| 表 | 承担 | 关键字段 |
| --- | --- | --- |
| `04_资产定义` | 资产**身份**：这是什么图、给哪个型号/区域/语言用 | `asset_key`、`category`、`model_scope`、`region_scope`、`language_dimension`、`language_variants`、`status`、`override_for` |
| `04_资产导出物` | 具体**文件位**：图往这里传 | `export_file`（附件，**留空待传**）、`format`、`repo_path`、`content_sha256`（预置期望哈希）、`export_key` |

导出物槽位的 `content_sha256` 预先写入了当前在用文件的哈希。这样上传的新图
是否真的换了内容、换成了什么，可以直接比对，不用靠文件名或上传时间猜。

新增导出物槽位的 `export_key` 统一用 `registry::<repo_path>` 前缀，
与既有的 `<source_key>::artifacts/<path>` 一批区分开，两批不会互相覆盖。

## 3. 新增字段 `override_for`

原 `04_资产定义` 没有表达覆盖关系的字段，而 155 个待建槽位里有 **27 个是覆盖图**
（例如 `lcd/jbp3600a/screen` 覆盖共享的 `lcd/lcd_map`）。没有这个字段，
覆盖关系进不了表，槽位建了也丢信息。

本轮新增：

| 字段 | id | 类型 | 说明 |
| --- | --- | --- | --- |
| `override_for` | `fldJp29f3p` | text | 被本资产覆盖的基础 `asset_key`；空＝非覆盖资产。对应 `data/asset_registry.csv` 的 `override_for` 列，单层覆盖，不嵌套。 |

纯新增字段，不改动任何既有字段，不影响
[`sync_asset_registry.py`](../../tools/sync_asset_registry.py) 现有的七列同步范围。

## 4. 验证

### 4.1 行数回读

- `04_资产定义` 全表 182 行（27 + 155）。
- `04_资产导出物` 全表 375 行（183 + 192），分页读取累计确认。

### 4.2 逐条回读抽样

| 记录 | 内容 |
| --- | --- |
| `recvuCHHTViLxq` | `04_资产定义` / `asset_key = lcd/jbp3600a/screen` / **`override_for = lcd/lcd_map`** |
| `recvuCHOuj2Cb8` | `04_资产导出物` / `registry::docs/renderers/latex/assets/jbp3600a_lcd_map.pdf` / `format = pdf` / `export_file` **空** / `content_sha256 = 195029e3386f…` |
| `recvuCHOujP98A` | `04_资产导出物` / 同资产的 `.png` / `format = png` / `export_file` **空** / `content_sha256 = 5e793d99a847…` |

覆盖关系写进去了、附件位空着可传、期望哈希预置好了——三件事都成立。

### 4.3 反向同步验证（最强的一条）

槽位值是否正确，不看写入返回，看它同步回仓库会不会改动任何东西：
拉取全部 182 条线上定义记录，喂给仓库自己的
[`merge_registry_csv`](../../tools/sync_asset_registry.py)，与当前
`data/asset_registry.csv` 比对。

```text
merge stats: MergeStats(updated=(), appended=(), managed=182)
rows before=182 after=182
asset_key order identical: True
cell-level differences: 0
```

- `managed=182`：182 行全部由 Base 管理了（写入前只有 27 行被管理）。
- `updated=()`：**没有任何一行的任何一列被 Base 改动**。
- `appended=()`：没有产生仓库里不存在的孤儿行。
- 逐单元格比对 **0 差异**，行顺序一致。

原始文本比对会显示 25 行差异，那是 CSV 引号归一化（已知的引号抖动），
不是值变化——所以这里以解析后的单元格为准，并把两种结果都记下来。

## 5. 边界：本轮没做的

- **未上传任何图片。** 全部 192 个导出物槽位的 `export_file` 都是空的，等人往里传。
- **未改任何既有行。** 27 条既有定义、183 条既有导出物原样未动。
- **未建 `04_资产源文件` 记录。** 可编辑母版（`.ai`）的归档是另一件事，
  见 [A1 母版实测](asset_pilot_a1_master_editability_2026-09.md) 第 6 节。
- **未给新槽位设 `gate_status` / `build_eligible`。** 留空，因此新槽位不会被
  [`sync_web_composites.py`](../../tools/sync_web_composites.py) 之类按
  `approved` 筛选的下游误当成已核准内容。图传进来之后再走审核。
- **`web-composite/je1000f_eu/*` 的 11 个定义槽位没有配导出物行。**
  那批由 `sync_web_composites.py` 自己管理导出物，重复建会出现两个写入方
  争同一批行。另有 6 个 `qr` / `mark` / `illustration` / `feishu` 前缀的
  资产同样暂无导出物槽位，合计 17 个，登记待补。
- **JS-100I 的 13 张 Web 整图仍然没有槽位。** 它们绕过注册表，只存在于
  `docs/renderers/web/js100i_eu_en_illustrations.json`，仓库侧先得有
  `asset_registry.csv` 行，才谈得上在多维表里建槽位。这是本轮最大的遗留。

## 6. 遗留

| 项 | 说明 |
| --- | --- |
| JS-100I 13 张图入注册表 | 入注册表后再补槽位，做法与本轮相同 |
| 17 个定义槽位缺导出物行 | 其中 11 个属 `sync_web_composites.py` 管辖，需先划清所有权 |
| 上传后的校验闭环 | 目前 `content_sha256` 是预置期望值，尚无「上传件与之比对」的自动闸门 |
| 可编辑母版归档 | `04_资产源文件` 仍只有 3 条；JE-1000F EU、JBP-3600A、JS-100I、JA-AD01A 的母版都未归档 |
| 可编辑性/色彩/字体依赖字段 | 三表仍无对应字段，见 [A1 §4](asset_pilot_a1_master_editability_2026-09.md) |
