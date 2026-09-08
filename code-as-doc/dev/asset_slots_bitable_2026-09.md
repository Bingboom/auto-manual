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

分两轮执行：第一轮补齐注册表里已有的 155 个，第二轮把 JS-100I 那批
**原本连注册表行都没有**的 13 张图先入注册表再建槽位。

| 表 | 起点 | 第一轮 | 第二轮（JS-100I） | 现在 |
| --- | --- | --- | --- | --- |
| `data/asset_registry.csv` | 182 | — | **+13** | **195** |
| `04_资产定义` | 27 | **+155** | **+13** | **195** |
| `04_资产导出物` | 183 | **+192** | **+13** | **388** |
| `04_资产源文件` | 3 | 0 | 0 | 3 |

`04_资产定义` 的 195 行与 `data/asset_registry.csv` 的 195 行一一对应，
无多、无少、无重复。全部为新增，未修改也未删除任何既有行。

## 2. 一个槽位由什么组成

多维表里「一张图」跨两张表，因为定义表没有附件字段：

| 表 | 承担 | 关键字段 |
| --- | --- | --- |
| `04_资产定义` | 资产**身份**：这是什么图、给哪个型号/区域/语言用 | `asset_key`、`category`、`model_scope`、`region_scope`、`language_dimension`、`language_variants`、`status`、`override_for` |
| `04_资产导出物` | 具体**文件位**：图放在这里 | `export_file`（附件，本轮 205 张已传入，见 §4.4）、`format`、`repo_path`、`content_sha256`（预置期望哈希）、`export_key` |

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

## 3.5 JS-100I：先补注册表，再建槽位

JS-100I 的 13 张 Web 整图此前**绕过注册表**，只存在于
`docs/renderers/web/js100i_eu_en_illustrations.json`，构建通过文件名替换消费，
仓库侧没有资产身份，多维表里自然也无从建槽位。

本轮按 JA-AD01A 的 Web-first 先例补进 `data/asset_registry.csv`：

- key 形如 `web/js-100i/eu/en/<slug>`（slug 由文件名下划线转连字符），
  `语言维度=按语言`、`语言变体=en`、`适用机型=JS-100I`、`适用区域=EU`、
  `导出物路径=docs/renderers/web/assets/js100i_eu_en`，`override_for` 留空。
- `内容哈希` 直接取 illustrations 清单里已锁定的 SHA-256，两处因此同源。
- 备注记录母版页码与裁切框，并写明 `371JNuMVqZ` 是**钉钉记录 ID 而非文件名**
  （真名 `16-0102-000209 说明书 HTS006100C-EU-JAK RoHS REACH.ai`），
  避免后来者拿这个串去磁盘上搜。

注册表侧验证：195 行加载通过；13 个 key 逐个 `resolve_asset` 命中自身
（未被任何覆盖劫持）且导出文件哈希与声明一致（13 ok / 0 bad）；
`python build.py asset-check --config configs/config.us.yaml --model JE-1000F --region US`
退出码 0，工作区除 `data/asset_registry.csv` 外无任何副作用。

`tests/test_asset_registry.py` 的三处行数棘轮 182→195、核准数棘轮 174→187 同步更新；
全量 `python -m unittest` 3856 通过。

## 4. 验证

### 4.1 行数回读

- `04_资产定义` 全表 195 行（27 + 155 + 13）。
- `04_资产导出物` 全表 388 行（183 + 192 + 13），分页读取累计确认。

### 4.2 逐条回读抽样

| 记录 | 内容 |
| --- | --- |
| `recvuCHHTViLxq` | `04_资产定义` / `asset_key = lcd/jbp3600a/screen` / **`override_for = lcd/lcd_map`** |
| `recvuCHOuj2Cb8` | `04_资产导出物` / `registry::docs/renderers/latex/assets/jbp3600a_lcd_map.pdf` / `format = pdf` / `content_sha256 = 195029e3386f…` |
| `recvuCHOujP98A` | `04_资产导出物` / 同资产的 `.png` / `format = png` / `content_sha256 = 5e793d99a847…` |

建成时三件事都成立：覆盖关系写进去了、附件位空着可传、期望哈希预置好了。
这两条的 `export_file` 随后在 §4.4 一并填入。

### 4.3 反向同步验证（最强的一条）

槽位值是否正确，不看写入返回，看它同步回仓库会不会改动任何东西：
拉取全部 195 条线上定义记录，喂给仓库自己的
[`merge_registry_csv`](../../tools/sync_asset_registry.py)，与当前
`data/asset_registry.csv` 比对。

```text
merge stats: MergeStats(updated=(), appended=(), managed=195)
rows 195 -> 195
asset_key order identical: True
cell-level differences: 0
```

- `managed=195`：195 行全部由 Base 管理了（写入前只有 27 行被管理）。
- `updated=()`：**没有任何一行的任何一列被 Base 改动**。
- `appended=()`：没有产生仓库里不存在的孤儿行。
- 逐单元格比对 **0 差异**，行顺序一致。

原始文本比对会显示 25 行差异，那是 CSV 引号归一化（已知的引号抖动），
不是值变化——所以这里以解析后的单元格为准，并把两种结果都记下来。

## 4.4 图片已上传

建完槽位后把 **205 张图全部传进 `export_file`**（39.4 MB，最大单张 4.0 MB）。
用 `lark-cli base +record-upload-attachment`，一条记录一次，逐条校验返回的
`file_token` 非空且报告大小等于本地文件；失败自动重试三次。

```text
DONE  uploaded=204  already=1  failed=0
```

回读结果：

| 检查 | 结果 |
| --- | --- |
| 205 个 `registry::` 槽位有附件 | **205 / 205**，仍空 0 |
| 空 `file_token` | 0 |
| 附件大小与本地文件不符 | 0 |
| 附件名与 `repo_path` 文件名不符 | 0 |
| **随机 8 个下载回本地重算 SHA-256** | **8 / 8 三方一致**（云端字节＝表内 `content_sha256`＝仓库文件） |

最后一行是关键：不是"上传返回成功"，是把字节取回来重新算过。

上传后 `04_资产导出物` 388 行中 **246 行有独立附件**，其余 142 行是 ZIP 成员索引（见 §5）。

## 5. 边界：本轮没做的

- **未改任何既有行。** 27 条既有定义、183 条既有导出物原样未动；
  上传只写自己新建的 205 个槽位。
- **既有 142 行的"空附件"不是缺文件。** 它们全部带 `zip_member_path`
  与 `package_sha256`（`775b291101026f0e…`），字节在源文件记录挂的
  `asset-package.zip` 里，export 行是逐文件索引。因此表里现在并存两种存法：
  ZIP 成员（142 行，传不进去）与独立附件（246 行，可直接上传）。
  外观相同、行为不同，尚无字段标记区分——登记为遗留。
- **未建 `04_资产源文件` 记录。** 可编辑母版（`.ai`）的归档是另一件事，
  见 [A1 母版实测](asset_pilot_a1_master_editability_2026-09.md) 第 6 节。
- **未给新槽位设 `gate_status` / `build_eligible`。** 留空，因此新槽位不会被
  [`sync_web_composites.py`](../../tools/sync_web_composites.py) 之类按
  `approved` 筛选的下游误当成已核准内容。图传进来之后再走审核。
- **`web-composite/je1000f_eu/*` 的 11 个定义槽位没有配导出物行。**
  那批由 `sync_web_composites.py` 自己管理导出物，重复建会出现两个写入方
  争同一批行。另有 6 个 `qr` / `mark` / `illustration` / `feishu` 前缀的
  资产同样暂无导出物槽位，合计 17 个，登记待补。
- **`illustrations.json` 与注册表仍是两条并行链路。** JS-100I 补进注册表后，
  同一张图的哈希在两处同源，但 Web 构建消费的仍然是清单里的文件名替换，
  不经 `asset_key` 解析。补注册表解决了「有没有身份和槽位」，
  没有解决「Web 消费是否走同一条解析」——后者仍是 AS-D04。

## 6. 遗留

| 项 | 说明 |
| --- | --- |
| 17 个定义槽位缺导出物行 | 其中 11 个属 `sync_web_composites.py` 管辖，需先划清所有权 |
| 上传后的校验闭环 | 本轮 205 张是脚本上传并逐条比对过的；但**别人从表里手工传一张新图时没有任何闸门**去比对 `content_sha256` |
| 两种存法无字段区分 | ZIP 成员 142 行与独立附件 246 行在表里看不出差别 |
| 表结构与人的用法错配 | 第一层已做（`preview` 字段 + 画廊视图，见 §6.5）；仍存的是一个资产按格式散成多行（388 行只对应 178 个 `asset_key`）与权威归属，见 §7 第 2、3 层 |
| 可编辑母版归档 | `04_资产源文件` 仍只有 3 条；JE-1000F EU、JBP-3600A、JS-100I、JA-AD01A 的母版都未归档 |
| 可编辑性/色彩/字体依赖字段 | 三表仍无对应字段，见 [A1 §4](asset_pilot_a1_master_editability_2026-09.md) |

## 6.5 第一层已执行：`preview` 字段 + 画廊视图

2026-09-08，按 §7 建议的第一层执行（第二、三层未动）。

### 新增字段

| 字段 | id | 类型 | 说明 |
| --- | --- | --- | --- |
| `preview` | `fldGtEpu8Y` | attachment | 该资产的预览图（≤600px PNG）。**仅供浏览识别，不是构建输入**——构建仍读 `04_资产导出物` 的 `export_file` |

### 新增视图

`04_资产定义` 增加画廊视图 **「图墙」**（`vewLcSWlqd`）。创建时封面自动绑定到
`preview` 字段；卡片可见字段设为 `asset_key`、`preview`、`model_scope`、
`region_scope`、`language_dimension`、`language_variants`、`override_for`、
`status`、`category` 共 9 项。此前三张表各只有一个默认 Grid View。

### 预览图怎么来的

对 195 个资产按 `png > jpg > pdf > svg` 取最佳来源，统一渲染成长边 ≤600px 的 PNG：

- 位图直接缩放（Lanczos）；
- PDF / SVG 用 PyMuPDF 渲染首页；
- **透明底一律压白**——否则透明插图在深色主题的画廊卡片上看不见。

产出 168 张、合计 8.0 MB、最大单张 158 KB。渲染质量抽查了四张不同来源
（SVG 警告三角、PDF 封面、PDF 的 JBP-3600A LCD 深底图、PNG 太阳能板），逐张目视确认。

### 27 个没有预览图，且不应该有

| 原因 | 数量 | 说明 |
| --- | --- | --- |
| 未声明任何导出物 | 13 | `web-composite/*`、`qr/*`、`mark/*`、`feishu/*` |
| `⛔隔离` 状态 | 2 | `page/back_cover`、`qr/back_cover_reference_candidate`，解析器本就拒绝导入 |
| Feishu 物化、无本地文件 | 12 | `web-composite/je1000f_eu/*` |

**没有给画廊加筛选把这 27 个藏起来。** 空白卡片本身就是「这个资产在本地没有可用文件」
的信号，藏掉反而看不见缺口。

### 验证

| 检查 | 结果 |
| --- | --- |
| 上传 | `uploaded=168 already=0 failed=0` |
| 有 `preview` 的定义行 | 168 / 195（其余 27 见上表） |
| 空 `file_token` / 大小不符 / 多传 / 漏传 | 0 / 0 / 0 / 0 |
| 单行附件数 >1（误重传） | 0 |
| 随机 6 张下载回本地重算 SHA-256 | **6 / 6 与生成件一致** |
| 加两个新字段后的反向同步 | 仍 `MergeStats(updated=(), appended=(), managed=195)`，逐单元格 0 差异 |

最后一行是要点：`preview` 与 `override_for` 都是纯新增字段，
不干扰 `sync_asset_registry.py` 既有的七列同步范围。

## 7. 表结构评估：拆分是对的，工作面是缺的

槽位建成、图也传完之后，暴露出的问题不在三张表的划分，而在这套表**是按
「构建控制面的镜像」设计的，不是按「人干活的地方」设计的**。现在要它承担后者。

三表的 `母版 → 逻辑资产 → 具体文件` normalization 本身正确，不建议推倒——
推倒会同时砸掉 [`sync_asset_registry.py`](../../tools/sync_asset_registry.py)、
[`sync_web_composites.py`](../../tools/sync_web_composites.py)、
[`asset_base_bindings.json`](../../data/asset_base_bindings.json)、入库工具和 388 行既有数据，
而且解决不了实际的不好用。

实测到的错配：

| 现象 | 实测值 |
| --- | --- |
| 图不在"资产"那张表 | `04_资产定义` 195 行是人看的那张（有 `asset_key`、适用机型、`override_for`），**没有附件字段** |
| 一张图散成多行 | 388 行只对应 **178 个 `asset_key`**：99 个一行、66 个两行、13 个三行（pdf/png/svg 各一行） |
| 没有能看图的视图 | 三张表**各只有一个默认 Grid View**，无画廊、无分组、无筛选 |
| 两种存法混在一张表 | ZIP 成员 142 行 vs 独立附件 246 行，外观一样行为不一样 |
| 命名两套 | `source/…::artifacts/…` 与本轮新增的 `registry::…` |
| 关键语义靠后补 | `override_for` 本轮才加；可编辑性等级 / 色彩模式 / 字体依赖仍无字段 |
| **双权威** | `sync_asset_registry.py` 只同步七列，导出路径与哈希归仓库——Base 实为镜像而非权威，与"在多维表管理资产"的说法矛盾 |

建议分三层。**第一层已执行，见 §6.5；第二、三层未动。**

1. ~~**低成本高感知**：给 `04_资产定义` 加 `preview` 附件字段并建画廊视图。~~
   已完成（`fldGtEpu8Y` + 「图墙」`vewLcSWlqd`，168 张预览图已入）。
2. **补齐语义**：加可编辑性等级、色彩模式、字体依赖三个字段，
   再加一个标记区分 ZIP 成员与独立附件。
3. **需要操作者拍板**：权威归属。Base 为权威、仓库 CSV 由其生成，或反过来；
   当前中间态最难维护。加字段解决不了这一层。

唯一可能需要真重构的一处：若目标是"任何人都能传"，
`04_资产导出物` 按 (资产 × 格式 × 语言) 一行的粒度偏细——
合理形态是一图一行、多格式共用一个附件字段（附件字段本就支持多文件）。
但这会改动 `sync_web_composites.py` 的读法与 `export_key` 契约，属独立排期。
