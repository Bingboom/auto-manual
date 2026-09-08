# Workstream Z / A0：试点范围与缺口清单

- 执行日期：2026-09-08
- 上级计划：[可编辑插图资产与设计交付计划](editable_asset_delivery_debt_plan_2026-09.md) §5 A0
- 阶段状态：A0 完成（盘点与缺口登记）；A1 及之后仍为 `deferred`
- 本文性质：只读盘点记录。本轮没有上传任何附件、没有写任何线上表、没有通知设计同事、没有改动模板或发布物。

## 1. 本轮欧规单语上线批次

engineering 仓 `Bingboom/auto-manual`，核对基线 `origin/main = d1b12bf8`（2026-09-08 读取）。
本轮以 Web-first 方式交付的欧规单语目标共三个：

| 目标 | 产品 | 配置 | 说明书版本 | 交付记录 |
| --- | --- | --- | --- | --- |
| `JS-100I / EU / en` | SolarSaga 100 Air | `configs/config.solar-eu-en.yaml` | V2.0-2026-04-01 | [验收](js100i_eu_en_web_acceptance.md)、[发布就绪](js100i_eu_en_web_release_readiness.md) |
| `JBP-3600A / EU / en` | Battery Pack 3600（Explorer 3600 Plus 加电包） | `configs/config.bp-eu-en-web.yaml` | V2.0-2026-08-04 | PR #1066 / #1075 / #1078 |
| `JA-AD01A / EU / en` | 102W 充电器 | `configs/config.charger-eu-en.yaml` | — | `code-as-doc/tests/ja_ad01a_eu_en_web_acceptance.md` 及两份 evidence JSON |

三者都已产出冻结包并通过本地验收；正式完成仍以 Hello-Docs `docs/publish/**` 合入与
真实 Read the Docs URL 回读为准。本文不代替那一步，也不宣称线上已完成。

## 2. 试点选定：`JBP-3600A / EU / en`

选它而不是另外两个，理由是它在**不额外扩展范围**的前提下同时具备计划要求的三件事：

1. **自带共享/覆盖关系。** 计划 §5 A0 要求"优先从这批样本选一组共享/覆盖关系"。
   JBP-3600A 是三者中唯一命中真实 `override_for` 的目标，且一次命中两组
   （`lcd/lcd_map` 与 `page/cover`），无需为验证机制补样本或重画素材。
2. **两条资产链路同时存在。** 它既有 15 行 `asset_registry.csv` 记录（印刷/IDML 链路），
   又有 8 张 Web 整图（`docs/renderers/web/assets/jbp3600a_eu_en/`），可以在同一本书里
   暴露 §4.1 消费闭合的真实边界。JS-100I 只有 Web 一条链路，JA-AD01A 体量过小。
3. **母版身份完整。** AI 母版、SHA-256、页数、recipe、`asset_sources.csv` 行齐备。

JS-100I 与 JA-AD01A 不进入 A0 试点，但其缺口在 §6 一并登记，不因未选中而消账。

### 2.1 三类代表样本

按计划 §5 A0"简单矢量图 / 含可修改文案的图 / 复杂或混合素材"各取一张：

| 类别 | `asset_key` | 文件 | 依据 |
| --- | --- | --- | --- |
| 简单 | `lcd/jbp3600a/charging_indicator` | `jbp3600a_charging_indicator.png` | 语言维度=中立，登记为"仅保留电池充电图标且排除相邻引线与百分号" |
| 含可修改文案 | `lcd/jbp3600a/display` | `jbp3600a_lcd_screen.png` | 语言维度=按语言（en），登记为"完整 LCD 标签与说明面板" |
| 复杂/混合 | `connections/jbp3600a/stacking_locking` | `jbp3600a_stacking_locking.png` | 源 p07 整页 bbox `[27,10,342,495]`，堆叠+Lock+Unlock 多子图，Web 副本 302 KB |

三张都取自同一 AI 母版，便于 A1 在一份源文件里对比三种可编辑性等级。

## 3. 原文件位置与哈希

### 3.1 设计母版

`data/asset_sources.csv` 行 `source/manual_jbp3600a_eu_master`：

| 字段 | 值 |
| --- | --- |
| 母版 SHA-256 | `e0ccc33427f89c77c30d32e073a3027123f4c8a9c9f5029d2378172a7f0a3761` |
| 页数 / 页面尺寸 | 10 页 / 130 × 185 mm |
| 当前发布 PDF SHA-256 | `084dd4517feddcd9b77da10415a2787ec4427f882a7b819160725fdff679ccfe` |
| recipe | `data/asset_recipes/manual_jbp3600a_eu_web.json` |
| 线上归档 | **未完成**，见 §6 |

**本轮新核实的重要事实：**`docs/renderers/web/jbp3600a_eu_en_illustrations.json` 记的
`source_pdf_name: hgXiHot5Ow.ai` 不是设计交付文件名，而是钉钉「交付工作管理」Base
`电子说明书新增语言` 表的**记录 ID**。该记录的真实附件名是
`16-0102-000334 说明书 HTP0113600A-EU-JAK RoHS REACH.ai`（8,923,381 字节）。
JS-100I 的 `371JNuMVqZ` 与 JA-AD01A 的 `xG4bYnERxR` 同理。

这意味着仓库当前记录的"母版名"是下载产物名，不能作为设计侧的资产身份。
计划 §4.1"不用原始文件名承担唯一性"在此已有实证：真正稳定的身份是那张表的记录，
而仓库侧尚未保存指向它的指针（`asset_sources.csv` 的 `source_pointer` 指向的是另一个
钉钉节点，不是这条记录）。登记为 AS-D02 子项。

### 3.2 该表可作为 A1/A2 的设计侧入口

`电子说明书新增语言` 表共 38 行，其中 21 行带 `Ai文件` 附件，并已由业务侧维护一个
`翻译源文件描述` 字段，把母版的画板结构分成三类：

| 描述值 | 数量 | 与计划 §3.2 的关系 |
| --- | --- | --- |
| 分页画板-符合翻译输入要求 | 10 | 结构可直接用于按页取图/按页交付 |
| 大画板-符合翻译输入要求 | 7 | 单画板，取图需按 bbox 裁切 |
| 含大画板+分页画板-需剔除重复画板 | 4 | 结构有重复，交付前需清理 |

这是设计侧**已经存在**的结构分级，与计划要求的可编辑性分级不是同一维度
（它描述画板组织，不描述矢量/活文字/位图），但可以直接复用为 A1 交付表单的
一个必填项，不必新造字段。三个试点目标均为"分页画板-符合翻译输入要求"。

### 3.3 实际用图与哈希核验

两条链路的本地文件全部逐字节核验通过（2026-09-08，本 worktree）：

| 链路 | 清单 | 结果 |
| --- | --- | --- |
| Web | `docs/renderers/web/jbp3600a_eu_en_illustrations.json` | 8/8 文件存在且 SHA-256 与声明一致 |
| 印刷/IDML | `data/asset_registry.csv` 15 行 JBP-3600A | 17/17 导出物存在且哈希一致，0 缺失、0 不符 |

Web 8 张：`overview` / `lcd` / `power` / `lcd_control` / `clearance` /
`stacking_locking` / `ac_charging` / `solar_charging`，分别来自母版 p04–p08。

## 4. 现有资产记录核实

### 4.1 线上三张表（只读查询，2026-09-08）

以用户身份 `唐夏冰` 只读查询 `文档构建` Base（坐标见
[`data/asset_base_bindings.json`](../../data/asset_base_bindings.json)）：

| 表 | 全表行数 | 覆盖到的来源 |
| --- | --- | --- |
| `04_资产源文件` | 3 | `manual_je1000f_us_master`、`manual_jbp2000b_eu_master_normalized`、`manual_jbp2000b_jp_master`，均 `已归档` |
| `04_资产定义` | 27 | `ALL` 8、`JBP-2000B` 8、`JE-1000F` 11 |
| `04_资产导出物` | 183 | `manual_je1000f_us_master` 167、`manual_jbp2000b_jp_master` 16 |

**结论（已按 AGENTS.md 实时数据纪律核实，不是从本地文件推断）：本轮三个欧规单语
目标在三张线上表中的记录数均为 0。** 试点目标 JBP-3600A 的母版、定义与导出物
当前只存在于 Git 控制面。

这不是新缺陷——`asset_sources.csv` 的备注早已写明"线上 04_资产源/定义/导出记录
待审批入库"——但 A0 需要把它从"备注里的一句话"变成有查询证据的债务基线。

### 4.2 共享/专用分类与覆盖解析

用仓库自己的 resolver（`tools.asset_registry.resolve_asset`）实跑，而不是读 CSV 推断：

| 请求 key | 目标 | 实际选中 | 结果 |
| --- | --- | --- | --- |
| `lcd/lcd_map` | JBP-3600A / EU / en | `lcd/jbp3600a/screen` | 覆盖命中 ✅ |
| `lcd/lcd_map` | JBP-2000B / JP / ja | `lcd/jbp2000b/screen` | 机型隔离正确 ✅ |
| `lcd/lcd_map` | JE-1000F / US / en | `lcd/lcd_map` | 回落基础图 ✅ |
| `page/cover` | JBP-3600A / EU / en | `page/jbp3600a_eu/cover` | 覆盖命中 ✅ |
| `page/cover` | JS-100I / EU / en | —— | 未注册，明确失败 ✅ |
| `lcd/lcd_map` | JS-100I / EU / en | `lcd/lcd_map` | **见下** ⚠️ |

最后一行是 A0 发现的实质问题：`lcd/lcd_map` 的适用范围是 `ALL/ALL`，因此
**太阳能板 JS-100I 也会静默解析到 Explorer 电站的 LCD 总览图**。当前不炸，只是因为
`manual_solar-eu-en.yaml` 没有 `lcd_icons` 页，从未发起这个请求——即偶然没触发，
不是范围正确。这正是计划 §4.2 规则 1 所说"不将历史宽范围视为设计适用性已确认"，
和规则 3"不用 `ALL` 默认值掩盖专用记录缺失"。登记为 AS-D07 子项。

对照之下 `page/cover` 对 JS-100I 明确失败，是期望行为——同一份注册表里两种范围
风格并存，说明 `ALL` 不是经过裁决的结论，而是历史默认值。

### 4.3 两条资产链路只靠文件名相接

`tools/web_document_source.py` 用 `web-illustrations/v1` 清单在 HTML 层做整图替换，
匹配键是 `replaces` 里的**文件名**（如 `jbp3600a_lcd_screen.png`），不是 `asset_key`。
它会校验替换文件的 SHA-256、拒绝重复来源与未使用绑定，这部分是收紧的；但：

- Web 实际消费的字节，其身份是"文件名 + 内容哈希"，没有 `asset_key`、没有母版修订；
- 同一张图在两条链路上各有一份哈希，两者之间没有登记关系；
- `overview.png` 一张 Web 图同时 `replaces` 了 `jbp3600a_front_controls.png` 和
  `jbp3600a_left_side_ports.png` 两个印刷资产——多对一，现有清单无法表达。

因此"这本说明书的这个版本用了哪张图的哪个修订"目前只能答一半。这是 AS-D04 的
具体形态，也是 A3 必须收口的点。计划 §4.2 规则 5"复用现有用图 manifest……字段缺口
先在既有清单补齐"在这里有了明确的缺口对象。

## 5. 设计联系人与编辑器

计划 §5 A0 要求"确认设计联系人及实际使用的编辑器"。这两项**需要操作者指定**，
本轮未确认，不猜测。已知的只有：母版为 `.ai`，`asset_sources.csv` 标注
`pdf-illustrator-compatible`，即当前按 Illustrator 可读的 PDF 兼容形态使用。
在联系人和编辑器版本确认前，A1 不能声称交付约定"可以交给设计同事"。

## 6. 缺口清单

对照计划 §7 债务账本，A0 把每项债务落到本试点的具体对象。全部保持 `deferred`。

| 债务 | 本试点的具体缺口 | A0 已取得的证据 |
| --- | --- | --- |
| AS-D01 | 尚无任何一份"设计交付包"实物；§3.1 表格的七类内容目前一项都没有样例 | 已选定三类代表样本作为 A1 的验证对象 |
| AS-D02 | 母版身份记的是钉钉记录 ID 而非设计文件名；`source_pointer` 未指向真实母版记录；线上三表 0 记录 | 已核实真实附件名与字节数；线上查询结果见 §4.1 |
| AS-D03 | 无修订留存与旧发布固定引用的证据；当前只有单一 SHA-256 快照 | 母版/发布 PDF/导出物哈希已全部锁定，可作为"旧修订"基线 |
| AS-D04 | Web 与印刷两条链路仅靠文件名相接；一对多替换无法表达；无 `asset_key` → 消费字节的完整链 | §4.3 |
| AS-D05 | 未取得母版即无法给出矢量/转曲/混合/位图分级；`.ai` 扩展名不构成证据 | 业务侧已有画板结构分级可复用（§3.2），但不覆盖可编辑性维度 |
| AS-D06 | 未发生任何真实设计修订闭环 | —— |
| AS-D07 | `lcd/lcd_map` 的 `ALL/ALL` 范围未经裁决，对无 LCD 的 JS-100I 也会解析成功；同一注册表内 `ALL` 与 fail-closed 两种风格并存 | §4.2 实跑结果 |

### 6.1 未进入试点但已登记的缺口

- `JS-100I / EU / en`：13 张 Web 整图，`asset_registry.csv` **0 行**，完全绕过注册表；
  母版 `371JNuMVqZ`（真实名 `16-0102-000209 说明书 HTS006100C-EU-JAK RoHS REACH.ai`，
  7,408,588 字节）线上未归档。
- `JA-AD01A / EU / en`：5 张图已登记为 `web/ja-ad01a/eu/en/*`（第三种风格：Web-first
  按语言 key），但 **`data/asset_sources.csv` 完全没有它的行**，母版
  `xG4bYnERxR`（真实名 `(翻译用）38-0001-000880 HTO847-EU-JAK 102W充电器 说明书
  RoSH REACH.ai`，918,848 字节）既无本地行也无线上记录。

三个目标三种资产登记风格（无注册表 / 印刷 key + Web 清单 / Web-first key），
本身就是 AS-D02 要收敛的对象。A0 只登记，不在本轮统一。

## 7. A0 退出对照

| 计划 §5 A0 要求 | 状态 |
| --- | --- |
| 选一本说明书及其实际用图清单 | ✅ `JBP-3600A / EU / en`，Web 8 + 印刷 17 |
| 三类代表样本各一张 | ✅ §2.1 |
| 交付试点范围、原文件位置/哈希 | ✅ §3 |
| 交付现有资产记录和缺口清单 | ✅ §4、§6 |
| 核对共享/专用分类、基础 key、覆盖 key 和适用范围 | ✅ §4.2，含一处实质问题 |
| 优先从样本选一组共享/覆盖关系 | ✅ 两组，均已实跑验证 |
| 确认设计联系人及实际使用的编辑器 | ⛔ 待操作者指定，见 §5 |
| 只盘点试点，不重跑全仓资产审计 | ✅ 未跑全量审计；线上查询为只读全表计数 |

A0 在设计联系人/编辑器一项未闭合，因此**不宣称 A0 全部退出条件达成**；
其余项已有证据。A1 需要该两项与母版实物才能启动。

## 8. 本轮未做的事

- 未下载任何 `.ai` 母版（需操作者确认后执行，见 §5）。
- 未写任何线上表、未上传附件、未改 `asset_registry.csv` / `asset_sources.csv`。
- 未修改模板、manifest、review 派生物或任何发布产物。
- 未联系设计同事、未发送任何文件。
- 未对 `lcd/lcd_map` 的 `ALL` 范围做任何收窄——那是 AS-D07 的裁决，需设计/资料确认。
