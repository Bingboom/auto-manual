# 手册样式定义

一个语义在这套系统里有四处渲染：**Web**（`web_manual.css`）、**PDF**（LaTeX）、**IDML**（InDesign）、**Word**（`reference.docx`）。四者的绑定关系由 [`manual_style.yaml`](manual_style.yaml) 声明，共 31 条语义。本文把这 31 条逐条写定义，附录写组件的构造与新增方式。

当前合同状态以 `manual_style.yaml` 为准：21 条为无债 `aligned`，`HB-TABLE-LCD-ICON` 为带批准参考档说明的 `aligned`，另有 9 条长期 `partial`。2026-08-05 完成的 16 条 IDML 样式契约欠账已经同步进本文；执行证据见[样式契约欠账清算状态](../../../code-as-doc/dev/style_debt_execution_status.md)。

## 0. 怎么读

| 列 | 含义 |
|---|---|
| **语义 ID** | `manual_style.yaml` 里的契约名。改样式先找它，它绑着另外三处渲染 |
| **源写法** | 作者在 md / RST 里怎么写。`原生` = 普通 Markdown；`` ```{x} `` = MyST 围栏指令；`流水线` = 只能由源表 + 模板产出，作者写不出来 |
| **Web** | 顶层 class（`web_manual.css` 的挂点） |
| **PDF** | LaTeX 入口宏 @ 所属 `docs/renderers/latex/*.tex` |
| **IDML** | InDesign 段落样式 / 表样式 / 对象样式 |
| **Word** | `reference.docx` 的样式 ID，或"经 HTML 转换"（无独立样式）。Word 侧的表样式**按形状选，不按语义选**：单行且 ≥3 列走 `TableGrid`，其余走 `tableHeader` |
| **状态** | `aligned` = 四处的语义和共享合同一致；`partial` = 有已记录的偏差，见各条的债。`aligned` 仍可保留已批准边界说明，不代表待修缺陷 |

单位：Web 用 `rem`（1rem = 16px），`clamp(最小, 视口比例, 最大)` = 随视口缩放并夹住两端；PDF/IDML 用 pt/mm，值取自 [`data/layout_params.csv`](../../../data/layout_params.csv)；Word 的 `sz` 是半磅（34 = 17pt）。

颜色变量：`--hb-brand-dark` `#343031`、`--hb-text` `#343031`、`--hb-text-muted` `#666264`、`--hb-line` `#a7a5a6`、`--hb-line-soft` `#dedcdd`、`--hb-paper` `#ffffff`、`--hb-surface` `#f4f3f3`。

---

## 1. 全量对照总表

### 文字与标题

| 语义 | 语义 ID | 源写法 | Web | PDF | IDML | Word | 状态 |
|---|---|---|---|---|---|---|---|
| 正文段落 | `HB-TYPE-BODY` | 原生 | `p` | `HBTypeBody` @ `type_system` | 段落样式 | `BodyText` / `FirstParagraph` / `Compact` 归一 | aligned |
| 列表 | `HB-TYPE-LIST` | 原生 `-` / `1.` | `ul` `ol` | `HBTypeListStart` @ `components_base` | `Item List` | 经 HTML 转换 | aligned |
| 一级标题 | `HB-TITLE-L1` | `# ` | `h1` / `.hb-h1-pill` | `HBTitleLevelOne` @ `components_headings` | `Heading1` + `HB Capsule Heading` | `dingding-heading1` | aligned |
| 二级标题 | `HB-TITLE-L2` | `## ` | `h2` / `.hb-subbar` | `HBTitleLevelTwo` | `Heading2`、`HB Operation Row Label` | `dingding-heading2` | aligned |
| 三级标题 | `HB-TITLE-L3` | `### ` | `h3` | `HBTitleLevelThree` | `Heading3` | `dingding-heading3` | aligned |
| 前言 / 引题 | `HB-TYPE-LEAD` | 流水线 | — | `HBTypeWarningTextStart`、`HBTypeRubricStart` | `HB Lead` | 经 HTML 转换 | partial |
| 页脚 | `HB-TYPE-FOOTER` | 流水线 | 不渲染 | `HBTypeFooter` | `HB Footer` | 页脚域 | partial |
| 页码 | `HB-TYPE-PAGE-NUMBER` | 流水线 | 不渲染 | `HBTypePageNumber` | `HB Page Number` | 页脚域 | partial |

### 警示与安全

| 语义 | 语义 ID | 源写法 | Web | PDF | IDML | Word | 状态 |
|---|---|---|---|---|---|---|---|
| 警示框 | `HB-CALLOUT-STRIP` | `` ```{callout} `` | `.manual-callout-table` | `HBWarningBlock` / `HBCautionBlock` / `HBNoteBlock` / `HBTipBlock` @ `components_base` | `Caution` + `HB Rounded Panel` + `Notice表格` | 经 HTML 转换（标签文字归一） | aligned |
| 安全指令 | `HB-SAFETY-INSTRUCTION` | 流水线 | 经 RST 组件 | `HBSafetyInstruction` @ `components_safety` | `HB Safety Instruction` + `HB Rounded Panel` | 保留 `safety_` 源前缀 | **aligned** |
| 安全警告面板 | `HB-SAFETY-WARNING` | 流水线 | 经 RST 组件 | `safetywarningbox`、`safetywarning` | `HB Rounded Panel` + `Warning表格` | 同上 | aligned |
| 大号警告引语 | `HB-SAFETY-LEAD` | 流水线 | 经 RST 组件 | `HBWarningLeadBlock` | `HB Rounded Panel` | 同上 | **aligned** |
| 危险锁定块 | `HB-SAFETY-DANGER` | 流水线 | 经 RST 组件 | `HBDangerBlock` | `HB Rounded Panel` | 同上 | aligned |

### 表格

| 语义 | 语义 ID | 源写法 | Web | PDF | IDML | Word | 状态 |
|---|---|---|---|---|---|---|---|
| 竖式规格表 | `HB-TABLE-SPEC` | `` ```{spec-table} `` | `.hb-spec-table-composition` | `spectable` @ `components_spec` | `竖型表格` + `HB Rounded Table Outer` | 表样式 `tableHeader` + 33%/67% 列宽与黑色边框覆盖 | aligned |
| 信号词表 | `HB-TABLE-SYMBOL-SIGNAL` | 流水线 | `.hb-symbol-signal-composition` | `HBSymbolTable` @ `components_symbols` | `正文表格` + `HB Rounded Table Outer` | 经 HTML 转换 | aligned |
| 符号图标表 | `HB-TABLE-SYMBOL-ICON` | `` ```{symbols} `` | `.hb-symbol-pair-composition` | `HBSymbolTwoColumnTables` | 同上 | 经 HTML 转换 | aligned |
| LCD 图标表 | `HB-TABLE-LCD-ICON` | `` ```{lcd-icons} `` | `.hb-lcd-table-composition` | `HBLcdIconTable` @ `components_lcd` | 同上 | 经 HTML 转换 | **aligned** |
| LCD 模式表 | `HB-TABLE-LCD-MODE` | `` ```{lcd-mode} `` | `.hb-lcd-mode-composition` | `HBLcdModeTable` | 同上 | 经 HTML 转换 | aligned |
| 自动恢复对比表 | `HB-TABLE-AUTO-RESUME` | `` ```{comparison} `` | `.hb-auto-resume-composition` | `HBAutoResumeTable` @ `components_data_tables` | 同上 | 经 HTML 转换 | aligned |
| 按键组合表 | `HB-TABLE-KEY-COMBINATIONS` | 流水线 | `.manual-table` | `HBKeyCombinationTable` | `HB Data Header` / `HB Data Body`（可移动文本框） | 经 HTML 转换 | **aligned** |
| 故障排查表 | `HB-TABLE-TROUBLESHOOTING` | `` ```{troubleshooting} `` | `.hb-troubleshooting-composition` | `HBTroubleshootingTable` | `正文表格` + `HB Rounded Table Outer`（关闭自动缩放） | 经 HTML 转换 | aligned |
| 通用表 | 无专属 ID | pipe 表 / `` ```{manual-table} `` | `.manual-table` | 走 `HB-TYPE-BODY` 排版 | `正文表格` | 表样式 `tableHeader`（单行且 ≥3 列时 `TableGrid`） | — |

### 专题版块

| 语义 | 语义 ID | 源写法 | Web | PDF | IDML | Word | 状态 |
|---|---|---|---|---|---|---|---|
| FCC 面板 | `HB-SPECIAL-FCC` | 流水线 | `.hb-fcc-composition` | `HBFccBlock` @ `components_special_pages` | `HB Rounded Panel` + `无表头表格` | 经 HTML 转换 | partial |
| 开箱清单卡 | `HB-SPECIAL-INBOX` | 流水线 | `.hb-inbox-composition` | `HBInBoxThree` | `Item List Text` + `HB Inbox Card` + `无表头表格` | 经 HTML 转换 | partial |
| 产品概览 | `HB-SPECIAL-OVERVIEW` | 流水线 | `.hb-annotated-figure` | `HBOverviewPanel` | `HB Body`（可移动文本框） | 经 HTML 转换 | partial |
| App 设置 | `HB-SPECIAL-APP` | 流水线 | `.hb-app-download-composition`、`.hb-app-add-device-composition` | `HBAppStep`、`HBAppAsset`、`HBAppNotice` | `HB Body` / `HB Callout Label` / `HB Callout Body` + `HB Rounded Panel` | 经 HTML 转换 | **aligned** |

### 质保与页面

| 语义 | 语义 ID | 源写法 | Web | PDF | IDML | Word | 状态 |
|---|---|---|---|---|---|---|---|
| 质保引语 | `HB-WARRANTY-LEAD` | 流水线 | `.hb-warranty-intro-composition` | `HBWarrantyLead` @ `components_warranty` | `HB Rounded Panel` | 经 HTML 转换 | aligned |
| 质保条款面板 | `HB-WARRANTY-SECTION` | 流水线 | `.hb-warranty-card` | `HBWarrantySection` | `HB Rounded Panel` | 经 HTML 转换 | aligned |
| 质保年限卡 | `HB-WARRANTY-YEARS` | 流水线 | `.hb-warranty-period-card` | `HBWarrantyYears` | `HB Big Numeral` + `HB Rounded Panel` | 经 HTML 转换 | aligned |
| 标准页 | `HB-PAGE-STANDARD` | 模板 | 无分页 | `HBPageTemplateStandard` @ `layout_templates` | `HB Standard Page` | 节属性 | partial |
| 无页脚页 | `HB-PAGE-NO-FOOTER` | 模板 | 无分页 | `HBPageTemplateNoFooter` | `HB No Footer Page` | 节属性 | partial |
| 封面 / 封底 | `HB-PAGE-COVER` | 模板 | 不渲染 | `HBPageTemplateCover`、`HBBackCoverPage` | `HB Cover Page` | 不渲染 | partial |

> Web 不分页：`HB-PAGE-*`、`HB-TYPE-FOOTER`、`HB-TYPE-PAGE-NUMBER` 在网页投影里没有对应物，只在 PDF/IDML 生效。

---

## 2. 文字与标题

### 2.1 正文与列表

| 属性 | Web 值 |
|---|---|
| 段落下间距 | `0.82rem`（上间距 0） |
| 列表外边距 | `0 0 1.15rem`，`padding-left: 1.35rem` |
| 相邻列表项 | `margin-top: 0.34rem` |
| 正文容器 | `#furo-main-content`：`width: min(100%, 58rem)`，内边距 `clamp(1.25rem, 3vw, 2.6rem)`，白纸卡片 + `0.22rem` 圆角 + 阴影 |
| 字号 / 行高 | `1rem` / 1.58 |

IDML 的 FR/ES 列表与子列表通过类型化样式消费语言密度 token；普通列表和嵌套列表的边距、标签间距及段间距均由 `type_list_*`、`lang_*_type_list_*`、`comp_list_*`、`comp_sublist_*` 控制。

### 2.2 一级标题

**`# 标题`** → `<h1>`（等价 class `.hb-h1-pill`）。品牌深色通栏胶囊，上方切平、下方两角圆，白字全大写。

| 属性 | 值 | 窄屏 ≤760px |
|---|---|---|
| 背景 / 文字 | `--hb-brand-dark` / `--hb-paper`，700 | — |
| 字号 | `clamp(1.28rem, 2.5vw, 1.58rem)` | `clamp(1.12rem, 6vw, 1.34rem)` |
| 行高 | 1.14 | — |
| 大小写 | `uppercase`（源里不必写大写） | — |
| 内边距 | `0.72rem 1rem 0.68rem` | `0.68rem 0.78rem 0.64rem` |
| 圆角 | `0 0 0.62rem 0.62rem` | `0 0 0.48rem 0.48rem` |
| 下间距 | `1.25rem` | — |

PDF/IDML token：`type_h1_font_size` 12.0pt、`type_h1_font_leading` 14.4pt、`comp_h1_pill_arc` 2.0mm、`comp_h1_pill_height` 7.1mm。Word：`dingding-heading1`，`sz` 34（17pt），色 `343031`。

IDML 的 band 高度与 PDF 共用 `comp_h1_pill_height`；质保页的宽度和左缩进继续由明确登记的 `idml_warranty_h1_*` token 控制。

### 2.3 二级标题

**`## 标题`** → `<h2>`（等价 class `.hb-subbar`）。深色圆点 + 加粗大写正文色，不是色块。

| 属性 | 值 |
|---|---|
| 布局 | `flex`，`gap: 0.58rem`；窄屏圆点顶对齐（`margin-top: .22rem`） |
| 圆点 | `0.72rem` 正圆，`--hb-brand-dark`，`::before` 生成 |
| 字号 | `clamp(1rem, 1.7vw, 1.12rem)`；窄屏锁 `1rem` |
| 字重 / 行高 | 700 / 1.22，`uppercase` |
| 外边距 | `1.3rem 0 0.72rem`，最大宽 58rem |

例外：`h2.hb-spec-section`（规格分节标题）不套本规则；质保卡片内首个 `h2` 另有覆盖。

token：`type_title_l2_font_size` 8.6pt、`comp_title_l2_bullet_radius` 0.75mm。Word：`dingding-heading2`，`sz` 28（14pt）。

IDML 的 `KeepWithNext` 由 `comp_title_l2_needspace` 推导；Operation Guide 的首标题和节间节奏使用已登记的语言 token，不再靠渲染器本地常量。

### 2.4 三级标题

**`### 标题`** → `<h3>`。同二级但整体压缩，圆点小一号，**不转大写**。

| 属性 | 值 |
|---|---|
| 布局 | `flex`，`gap: 0.44rem` |
| 圆点 | `0.32rem` 正圆 |
| 字号 / 字重 / 行高 | `0.98rem`（不随视口缩放） / 700 / 1.28 |
| 外边距 | `1.1rem 0 0.62rem` |

token：`type_title_l3_font_size` 7.0pt、`comp_title_l3_bullet_radius` 0.28mm。Word：`dingding-heading3`，`sz` 22（11pt）。

IDML 的 `KeepWithNext` 由 `comp_title_l3_needspace` 推导。`myst_heading_anchors = 3`：只有前三级生成锚点，四级以下没有可引用的 id。

### 2.5 引语 / 页脚 / 页码

`HB-TYPE-LEAD` 是前言与警示引题的排版；`HB-TYPE-FOOTER`、`HB-TYPE-PAGE-NUMBER` 只在 PDF/IDML 的页脚域生效，Web 投影不渲染。三者都不能从 md 直接写。

---

## 3. 警示与安全

### 3.1 警示框

**`` ```{callout} WARNING ``** → `table.manual-callout-table`，左标签格 + 右正文格。

| 属性 | 值 |
|---|---|
| 外框 | `2px solid --hb-line-soft`，圆角 `0.82rem`，`overflow: hidden` |
| 底色 | `--hb-surface`（正文格） |
| 外边距 | `1rem 0 1.35rem` |
| 标签格 | 宽 `clamp(7.5rem, 16%, 9.5rem)`，白底，700，居中 + 垂直居中，内边距 `0.82rem 0.72rem` |
| 布局 | `table-layout: fixed` |
| ≤520px | 标签与正文改为上下堆叠，标签转左对齐 |

信号词：`WARNING` `CAUTION` `NOTE` `TIP` `DANGER` `IMPORTANT` `NOTICE` `ATTENTION`，自动转大写。正文按完整 Markdown 解析，可放列表。

IDML callout 的悬挂 bullet 几何、bullet 字号、面板内距和语言节奏全部登记在 `manual_style.yaml` 的 `HB-CALLOUT-STRIP.token_refs`；标签文字仍由源 RST/IR 提供，渲染器不翻译或补造。

### 3.2 安全面板四类

`HB-SAFETY-INSTRUCTION` / `-WARNING` / `-LEAD` / `-DANGER` 都是**流水线专属**：源自安全章节的结构化文本，作者无法用 md 写出。四者在 IDML 共用 `HB Rounded Panel` 对象样式，靠显式语义、段落样式与表样式区分；Word 侧保留 `safety_` 源前缀以便回溯。四类现在均为 `aligned`：`DANGER` 保留独立 variant，不再降级成普通 warning；`WARNING` 的图标列、图标上限和面板下限由 token 控制。现有 warning lockup 美术资产仍是共享资产边界，语义对齐不伪造新的 DANGER 美术。

---

## 4. 表格

六类组件表 + 一类通用表。共同底线：**行高不撑满、末行去下框线、末列去右框线**，靠细线分格而不是画满外框；每类都在超窄屏用外层容器横向滚动，绝不压字。

### 4.1 通用表

pipe 表 / `` ```{manual-table} `` → `table.manual-table`

| 属性 | 值 |
|---|---|
| 字号 / 行高 | `0.94rem` / 1.42 |
| 单元格内边距 | `0.72rem 0.82rem` |
| 分隔线 | 上/左 `1px solid --hb-line-soft`；首行去上线、首列去左线 |
| 表头格 | 底色 `--hb-surface`，600，左对齐 |
| 对齐 | `vertical-align: top` |
| 外层 | `1px solid --hb-line` + `0.62rem` 圆角面板 |

### 4.2 竖式规格表

`` ```{spec-table} 分节名 `` → `figure.hb-spec-table-composition` > `table.hb-spec-table`

| 属性 | 值 |
|---|---|
| 外框 | `2px solid --hb-brand-dark`，圆角 `0.92rem` |
| 列宽 | 标签 31% / 值 69%，`table-layout: fixed` |
| 字号 / 行高 | `0.9rem` / 1.25 |
| 内边距 | `0.52rem 0.72rem` |
| 分隔线 | 右/下 `1.25px solid --hb-brand-dark` |
| 标签格 | `<th scope="row">`，底色 `--hb-surface`，600 |
| 对齐 | `vertical-align: middle` |
| 溢出 | 表格 `min-width: 40rem`，外层横向滚动 |
| 脚注上标 | `.hb-spec-reference` = `0.62em`，`line-height: 0` |

合并：标签留空的行并入上一个标签（`rowspan`）。

**同一列宽有多组经合同登记的投影值**：Web 31% / PDF `comp_spec_table_left_ratio` 0.315 / Word 33%，IDML 默认 `idml_spec_table_left_ratio` 0.302，西语批准投影为 `lang_es_idml_spec_table_left_ratio` 0.362。它们分别服务响应式、固定版、Word 与批准语言版式，不应只改其中一处后假定其他渲染器自动同步。其余 token：`comp_table_outer_arc` 2.4mm、`comp_table_outer_rule` 0.75pt、`type_spec_label_font_size` 与 `type_spec_value_font_size` 均 6.0pt。

IDML 普通行由 `idml_spec_table_row_height` 控制；多行单元格使用 `comp_spec_table_multiline_min_height`，并输出 `MinimumHeight` / `AutoGrow`，不再由本地常量决定。

### 4.3 故障排查表

`` ```{troubleshooting} `` → `figure.hb-troubleshooting-composition`

| 属性 | 值 |
|---|---|
| 外框 | `2px solid --hb-brand-dark`，圆角 `0.92rem` |
| 列宽 | 代码 14% / 措施 86%，表格 `min-width: 42rem` |
| 字号 | 表 `0.9rem`；表头 `0.98rem`/700；**代码格 `1.12rem`/700 居中** |
| 代码格底色 | `--hb-surface`，左右内边距压到 `0.38rem` |
| 分隔线 | 右/下 `1.25px solid --hb-brand-dark` |
| 多步措施 | ` / ` 分隔 → `.line-block` > `.line`，行距 `0.25rem` |

表头固定 `Error Code` / `Corrective Measures`（见 [附录 B](#附录-b-已知缺陷)）。IDML 关闭自动缩放；批准语言的行 minima、表头/正文高度修正、内外线宽、面板下限、导入安全余量和 portable glyph-width 估算全部由 `idml_trouble_*` / `lang_*_idml_trouble_*` token 控制。

### 4.4 LCD 图标表

`` ```{lcd-icons} `` → `figure.hb-lcd-table-composition`

| 属性 | 值 |
|---|---|
| 列宽 | 序号 6% / 图 11% / 名称 27% / 说明 56% |
| 字号 / 行高 | `0.9rem` / 1.23，`min-width: 42rem` |
| 内边距 | `0.7rem 0.72rem`；序号列左右内边距归零 |
| 分隔线 | 右/下 `1px solid --hb-line`（浅色，与规格表的深色不同） |
| 说明列 | 支持 ` / ` 分步 |

四处语义对齐（`aligned`）。批准 reference profile 可保留型号特定行高，这是一条已批准边界说明；共享排版、位置和表结构仍由 token 控制，不是待修缺陷。

### 4.5 LCD 模式表

`` ```{lcd-mode} `` + 一张图 → `figure.hb-lcd-mode-composition`（图 + 表两栏网格）

| 属性 | 值 |
|---|---|
| 栅格 | `minmax(12rem, .9fr) minmax(25rem, 1.1fr)`，间距 `clamp(1rem, 2.4vw, 1.65rem)` |
| 表面板 | `2px solid --hb-brand-dark`，圆角 `0.78rem` |
| 表格 | 字号 `0.82rem` / 行高 1.17，`min-width: 25rem`（窄屏 34rem） |
| 内边距 | `0.42rem 0.52rem`，分隔线 `1px solid --hb-brand-dark` |
| ≤760px | 转单列（图在上、表在下），圆角 `0.9rem` |
| 列 | `状态 / 动作 / 说明`，每列独立向上合并 |

IDML 侧的 EN/FR/ES 批准 panel/row/column/margin/spacing、参考 measure、panel 宽度和插图目标均为语言 token；其他语言按内容动态计算列宽与行高。字号、leading、inset、内外线和圆角也全部 token 化，portable fallback 只消费登记的 fallback token。传入空参数时保留兼容默认，不改变旧调用者。

### 4.6 符号表两类

- `` ```{symbols} `` → `figure.hb-symbol-pair-composition`：`grid-template-columns: repeat(2, minmax(0,1fr))`，间距 `clamp(.72rem, 1.8vw, 1rem)`，窄屏转单列。面板表内边距 `clamp(.62rem,1.5vw,.9rem)` `clamp(.55rem,1.25vw,.78rem)`，格间线 `1.5px solid --hb-brand-dark`，表头下边框同宽。**两个面板行高互不影响**（PDF 用的就是两张独立表）。
- 信号词表 `HB-TABLE-SYMBOL-SIGNAL` → `.hb-symbol-signal-composition`，流水线专属，md 写不出。

IDML 的 subbar 高度、标题/维护区间距、H1 光学偏移、页面下限和非批准语言 fallback 估算均来自 `manual_style.yaml` 登记的 token；两类 Symbols 表均为 `aligned`。

### 4.7 对比表

`` ```{comparison} 左表头 | 右表头 `` → `figure.hb-auto-resume-composition`

| 属性 | 值 |
|---|---|
| 外框 | `2px solid --hb-brand-dark`，圆角 `1rem` |
| 字号 | 表 `0.91rem`；表头 `0.98rem`/700 |
| 内边距 | `0.46rem 0.72rem`，分隔线 `1px solid --hb-brand-dark` |
| 左列底色 | `--hb-surface`；右列 `--hb-paper` |
| 合并 | 每列独立向上合并 |

IDML 使用独立的 `table_auto_resume` 角色，不再退化成普通表；对比语义可由 IR 到最终 IDML 单独审计。

### 4.8 按键组合表

`HB-TABLE-KEY-COMBINATIONS`，流水线专属，Web 落到通用 `.manual-table`。IDML 用可移动文本框承载 `HB Data Header` / `HB Data Body`，四处对齐。

---

## 5. 图与专题版块

普通插图：`img { max-width: 100%; height: auto }`，Web 投影下每张独立图占满同一内容宽度并居中，不保留印刷侧的固定像素宽度提示。

四个专题版块都是**流水线专属**，作者不能用 md 写，只能改源表或模板：

| 版块 | Web 结构 | 说明 |
|---|---|---|
| FCC | `.hb-fcc-composition` > `.hb-fcc-grid` | 开场文案 + 分栏条款，IDML 用无表头表格承载 |
| 开箱清单 | `.hb-inbox-composition` > `.hb-inbox-grid` | 三张等宽圆角卡 + 1/2/3 角标 + 通栏 TIP 条 |
| 产品概览 | `.hb-annotated-figure` > `.hb-annotated-stage` + `.hb-leader-layer` | 带引线标注：标注位置靠逐图百分比坐标，是流水线独有的能力 |
| App 设置 | `.hb-app-download-composition`、`.hb-app-add-device-composition` | 商店徽章 / QR / 双机图，标签是活文本不是烧进图片 |

`web_manual.json` 里登记的目标（当前 `JE-1000F / US`）会把其中部分图替换为审批过的 PDF 派生图，标题与说明仍保持可搜索的活 HTML。

---

## 6. 质保

| 语义 | Web | 要点 |
|---|---|---|
| 引语 | `.hb-warranty-intro-composition` | |
| 条款面板 | `.hb-warranty-card` | 圆角面板，卡内首个 `h2` 有专门覆盖（不走 §2.3 的圆点条） |
| 年限卡 | `.hb-warranty-period-card` > `.hb-warranty-period-grid` | 大号数字 + 单位 + 副标题；IDML 用 `HB Big Numeral` |

token 以 `comp_warranty_*`、`type_warranty_*` 为前缀；语言相关的面板高度微调走 `lang_<xx>_idml_warranty_*`。共享 Warranty 模板通过 `container` 明确标记 `warranty_lead`、`warranty_section`、`warranty_years`，覆盖 en/fr/es/de/it/uk/ko/pt-BR。IDML 直接读取这些语义，不依赖标题措辞或年限文本形状；坏的 years 结构 fail-closed。冻结 review derivative 仍兼容旧启发式，避免历史批准稿失效。

---

## 7. 页面模板

| 语义 | PDF | IDML | 说明 |
|---|---|---|---|
| 标准页 | `HBPageTemplateStandard` | `HB Standard Page` | 带页脚；token 为 `page_paperwidth/height`、四边 `page_margin_*`、`page_footskip` |
| 无页脚页 | `HBPageTemplateNoFooter` | `HB No Footer Page` | 同上去掉 `page_footskip` |
| 封面 / 封底 | `HBPageTemplateCover`、`HBBackCoverPage` | `HB Cover Page` | 封面是置入的成品美术；封底几何为 InDesign 原生，文案来自共享 IR |

Web 投影没有页的概念，这三条不参与。

---

## 8. 响应式、打印、字体

| 断点 | 改动 |
|---|---|
| `min-width: 82rem` | 加宽阅读区，组件取值不变 |
| `max-width: 760px` | H1 缩号缩圆角；H2 圆点顶对齐、字号锁 `1rem`；符号双栏转单列；LCD 模式转单列 |
| `max-width: 520px` | 警示框标签/正文上下堆叠 |
| `print` | H1/H2/H3 统一避免跨页断裂 |

所有通栏组件共享一条外宽契约：`box-sizing: border-box; width: 100%; max-width: var(--hb-component-band-max)`（= 阅读宽 58rem），成员包括 `h1`、docutils 表格容器、符号 / 故障排查 / 规格 / FCC / LCD / 对比六类 composition。新增通栏组件必须加进这条 `:is()` 列表，否则宽度会和邻居差一截。

字体：`Gilroy` 是商业授权，不随站分发；回退 `Avenir Next → Avenir → Segoe UI → Helvetica → Arial`，字形与印刷稿不完全一致。

---

## 9. 合同生效与批准版式

`aligned` 表示四个输出面消费同一语义合同，并不要求响应式 Web、固定页 PDF/IDML 和 Word 逐像素相同。允许的投影差异必须写在 token、渲染绑定或批准说明里，不能留作未登记的渲染器常量。

`manual_style.yaml` 与 `data/layout_params.csv` 的语义哈希会写入批准 reference-layout plan 的 v2 `identity.style`。v2 把 identity 分为 `content`、`assembly`、`style`、`provenance`：前三者和逐页 source digest 是 production 硬门禁；全局 phase2 `snapshot_sha256` 只保留在 `provenance` 供追溯，不因无关表变化阻断当前 target。`assembly` 同时哈希 source 顺序、语言、页面角色和 composition map；批准装配出现 `UNCLASSIFIED_PROSE` 时默认失败，只有精确登记的 source-ref 例外可继续。对已有批准合同的 target，production `build.py idml --source auto` 解析为冻结 `review-asis` 装配；未批准 target 继续走 runtime。普通 reference rebind 只允许 style/provenance identity 更新，默认拒绝 content 或 assembly hash 变化。只有在最终 Manual IR 的 source 顺序、语言映射、物理页数、`skipped_raw` 与 composition map 均通过核验后，才可由操作者使用显式 content-approval 路由重绑；reference PDF 与 composition map 不因样式销账而改变。

当前 JE-1000F / US 批准装配的验收结果为 52 个 source、58 个物理页、`skipped_raw=0`。具体 hash、批准 metadata 与测试记录见[样式契约欠账清算状态](../../../code-as-doc/dev/style_debt_execution_status.md)。

---

## 附录 A 组件化定义

### A.1 一个组件由什么构成

| 层 | 内容 | 落在哪 |
|---|---|---|
| 语义 | 语义 ID、`semantic_source_kinds`、`token_refs`、四处渲染绑定、`status` / `debt` | [`manual_style.yaml`](manual_style.yaml) |
| 源写法 | MyST 围栏指令，或 RST 模板 / 源表字段 | PR #874 的 `tools/manual_md_directives.py`、`docs/templates/` |
| 标记 | `figure.hb-*-composition` 外壳 + 表格/网格骨架 + 每列一个 `col.hb-*-col-*` | 指令的 `run()` 或流水线渲染器 |
| 样式 | 顶层 class 上的规则；分列宽度写在 `col` class 上 | [`web_manual.css`](web_manual.css) 及两个分模块 |
| 印刷 | LaTeX 入口宏 + IDML 渲染器 | `docs/renderers/latex/`、`tools/idml/` |

外壳与骨架分离是硬约定：**外壳负责外框、圆角、横向滚动、外宽契约；内表只负责格线与排字**。规格表、故障排查表、对比表、LCD 模式表都遵循这一层划分，所以窄屏时是外壳滚动而不是表格压字。

### A.2 围栏指令的构造契约

八个指令共用基类 `_ManualDirective`（`has_content`、一个可选参数、`option_spec` 含 `class`）：

| 环节 | 约定 |
|---|---|
| 参数 | `self.label`。多数指令 → `aria-label`；`comparison` 拆成两个表头；`lcd-mode` 当作图片 |
| 行解析 | `rows()`：按 `|` 分列并 `strip`，**空行直接丢弃** |
| 行内子集 | `_inline_html()`：转义 `& < > "` 后只还原 `**粗体**`、`^上标^`、`~下标~`。`callout` 例外，走 `nested_parse` 完整 Markdown |
| 图片格 | `_image_html()`：只在 `lcd-icons` 第 2 列、`symbols` 第 1 列、`lcd-mode` 参数位 |
| 多步文本 | `_line_block()`：` / ` 分隔 → `.line-block` > `.line`；少于两段退化为 `<p>` |
| 合并语义 | `_merged_row()`：空格子并入上方（每列独立）。`spec-table` 用自己的实现，**只看第一列** |
| 输出 | `nodes.raw(format="html")`，即样式契约要的确切标记 |

### A.3 新增一个组件

1. 在 `manual_style.yaml` 加语义条目：`role`、`semantic_source_kinds`、`token_refs`、四处渲染绑定，并诚实填写 `status`；只有 `partial` 或批准边界说明才写 `debt`。
2. 如果组件面向 plain-Markdown 站点，在 PR #874 提供的 `manual_md_directives.py` 写指令类（继承 `_ManualDirective`，`run()` 返回 `nodes.raw`），并注册进 `DIRECTIVES`。
3. 在 `web_manual.css`（或两个分模块之一）加顶层 class 与 `col` 宽度；通栏组件记得加进 §8 那条 `:is()` 列表。
4. 印刷侧补 LaTeX 入口宏与 IDML 渲染器，token 加进 `data/layout_params.csv`。
5. plain-Markdown 组件在 PR #874 的 `tests/test_plain_markdown_site.py` 补断言；IDML/PDF/Word 同时补各自的直接合同测试，锁住语义与 token 消费关系。

三个样式模块的行数上限由 [`tools/check_maintainability_guardrails.py`](../../../tools/check_maintainability_guardrails.py) 看守（`web_manual.css` 1905 / `web_app_components.css` 128 / `web_symbols_fcc_components.css` 160），加样式超了要连同阈值一起调。

### A.4 改样式的顺序

先在 `manual_style.yaml` 找语义 ID → 看它绑了哪些 token 和另外三处渲染 → 再动 CSS / tex / IDML。**只改 CSS 可能让四处渲染悄悄分叉**；规格表的 Web / PDF / IDML / Word 列宽是经登记的投影差异，新增差异也必须用同样方式进入合同并补测试。改 `manual_style.yaml` 或 `layout_params.csv` 后要重新生成 `params.tex`、运行合同测试和 reference pin gate；不能手改批准 hash 绕过验证。

---

## 附录 B 已知缺陷

以下三条是 PR #874 plain-Markdown 指令实现中实测确认的缺陷，不是当前 IDML 样式债，也不是用法问题：

| 缺陷 | 表现 | 绕法 |
|---|---|---|
| 单元格里的竖线无法转义 | 转换阶段写成反斜杠加竖线，渲染阶段直接按竖线切分不认转义，结果多切一格且残留反斜杠 | 用全角 `｜` 或 `/`；必须用竖线就放 `callout` |
| `troubleshooting` 的 `:headers:` 不可用 | 代码读了 `options["headers"]` 但没注册该选项，写了报未知选项，不写则表头恒为 `Error Code` / `Corrective Measures` | 换 `manual-table` + `:headers:` |
| `:class:` 被接受但忽略 | 八个指令都声明了该选项，八个 `run()` 都不读 | 改 CSS 或改指令实现 |

当前剩余项以 `manual_style.yaml` 为唯一账本：`HB-TYPE-LEAD`、`HB-TYPE-FOOTER`、`HB-TYPE-PAGE-NUMBER`、`HB-SPECIAL-FCC`、`HB-SPECIAL-INBOX`、`HB-SPECIAL-OVERVIEW`、`HB-PAGE-STANDARD`、`HB-PAGE-NO-FOOTER`、`HB-PAGE-COVER` 为 9 条长期 `partial`；`HB-TABLE-LCD-ICON` 保留一条批准参考档说明。原始 16 条 IDML 合同债已全部销账，完整范围和验证结果见[样式契约欠账清算状态](../../../code-as-doc/dev/style_debt_execution_status.md)。
