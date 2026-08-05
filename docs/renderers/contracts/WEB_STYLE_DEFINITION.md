# 样式定义（Web 投影）— 标题与表格

一个语义在这套系统里有三处渲染：Web（本文）、印刷 LaTeX、InDesign/IDML。三者的对应关系由 [`manual_style.yaml`](manual_style.yaml) 声明，本文写的是其中 **Web 一侧的实际取值**，取自 [`web_manual.css`](web_manual.css)。

图例：**源写法** = 作者在 md 里怎么写；**产出标记** = 编译后的 HTML；**语义 ID** = `manual_style.yaml` 里的契约名，改样式时以它为准找到另外两个渲染器。

单位：Web 用 `rem`（1rem = 16px）；印刷 token 用 pt/mm，取自 [`data/layout_params.csv`](../../../data/layout_params.csv)。`clamp(最小, 视口比例, 最大)` = 随视口缩放并在两端夹住。

本文覆盖**标题三级 + 表格三类**。其余语义（列表、图注、LCD/符号/故障排查组件、封面）见 [§6](#6-本次未覆盖)。

---

## 0. 总表

| 语义 | 源写法 | 产出标记 | 语义 ID | 类型 |
|---|---|---|---|---|
| 一级标题 | `# 标题` | `<h1>` | `HB-TITLE-L1` | 原生 |
| 二级标题 | `## 标题` | `<h2>` | `HB-TITLE-L2` | 原生 |
| 三级标题 | `### 标题` | `<h3>` | `HB-TITLE-L3` | 原生 |
| 通用表 | pipe 表 / `` ```{manual-table} `` | `table.manual-table` | `HB-TABLE-*` | 原生 / 围栏 |
| 竖式规格表 | `` ```{spec-table} 分节名 `` | `figure.hb-spec-table-composition` | `HB-TABLE-SPEC` | 围栏 |
| 警示框 | `` ```{callout} WARNING `` | `table.manual-callout-table` | `HB-CALLOUT-STRIP` | 围栏 |

围栏指令的完整写法见 [`md_site_guide.md`](../../../user-guide/md_site_guide.md)。

---

## 1. 一级标题

**源写法** `# IMPORTANT SAFETY INFORMATION` → **产出** `<h1>`（等价 class：`.hb-h1-pill`）

品牌深色通栏胶囊：**上方切平、下方两角圆**，白字全大写。

| 属性 | 值 | 备注 |
|---|---|---|
| 背景 | `--hb-brand-dark` `#343031` | |
| 文字 | `--hb-paper` `#ffffff`，700 | |
| 字号 | `clamp(1.28rem, 2.5vw, 1.58rem)` | 窄屏 `clamp(1.12rem, 6vw, 1.34rem)` |
| 行高 | 1.14 | |
| 大小写 | `text-transform: uppercase` | 源里不必写大写 |
| 内边距 | `0.72rem 1rem 0.68rem` | 窄屏 `0.68rem 0.78rem 0.64rem` |
| 圆角 | `0 0 0.62rem 0.62rem` | 窄屏 `0 0 0.48rem 0.48rem` |
| 下间距 | `1.25rem` | 上间距 0 |
| 锚点链接 | `rgba(255,255,255,.7)` | furo 的 `¶` |

印刷侧：LaTeX `HBTitleLevelOne`（`components_headings.tex`）／IDML 段落样式 `Heading1` + 对象样式 `HB Capsule Heading`。token：`type_h1_font_size` 12.0pt、`type_h1_font_leading` 14.4pt、`comp_h1_pill_arc` 2.0mm、`comp_h1_pill_height` 7.1mm。

> `manual_style.yaml` 记的债：IDML 的band 高度仍自行推导，没走 `comp_h1_pill_height`。

## 2. 二级标题

**源写法** `## Charging the Product` → **产出** `<h2>`（等价 class：`.hb-subbar`）

深色圆点 + 加粗大写正文色，不是色块。

| 属性 | 值 | 备注 |
|---|---|---|
| 布局 | `flex`，`gap: 0.58rem` | 窄屏 `align-items: flex-start`，圆点 `margin-top: .22rem` |
| 圆点 | `0.72rem` 正圆，`--hb-brand-dark` | `::before` 生成，不占源内容 |
| 文字 | `--hb-text` `#343031`，700，大写 | |
| 字号 | `clamp(1rem, 1.7vw, 1.12rem)` | 窄屏固定 `1rem` |
| 行高 | 1.22 | |
| 外边距 | `1.3rem 0 0.72rem` | |
| 最大宽 | `--hb-reading-width` 58rem | |

例外：`h2.hb-spec-section`（规格分节标题）不套这条规则；质保卡片内的首个 `h2` 另有一组覆盖。

印刷侧：LaTeX `HBTitleLevelTwo`／IDML `Heading2`、`HB Operation Row Label`。token：`type_title_l2_font_size` 8.6pt、`comp_title_l2_bullet_radius` 0.75mm。

## 3. 三级标题

**源写法** `### Charging with AC` → **产出** `<h3>`

同二级但整体压缩，圆点小一号。

| 属性 | 值 |
|---|---|
| 布局 | `flex`，`gap: 0.44rem` |
| 圆点 | `0.32rem` 正圆，`--hb-brand-dark` |
| 字号 | `0.98rem`（不随视口缩放） |
| 字重 / 行高 | 700 / 1.28 |
| 外边距 | `1.1rem 0 0.62rem` |
| 大小写 | 不转换，按源文照排 |

印刷侧：LaTeX `HBTitleLevelThree`／IDML `Heading3`。token：`type_title_l3_font_size` 7.0pt、`comp_title_l3_bullet_radius` 0.28mm。

`myst_heading_anchors = 3`：只有前三级生成锚点，四级以下没有可引用的 id。

---

## 4. 表格

三类共用一条底线规则：**行高不撑满、首行无上框线、首列无左框线**，靠 1px 细线分格而不是画满外框。

### 4.1 通用表

**源写法** 普通 pipe 表，或 `` ```{manual-table} 标题 ``（需要跨行合并时用后者）→ **产出** `table.manual-table`

| 属性 | 值 |
|---|---|
| 宽度 | `100%`，`border-collapse: separate` |
| 字号 / 行高 | `0.94rem` / 1.42 |
| 单元格内边距 | `0.72rem 0.82rem` |
| 分隔线 | 上/左 `1px solid --hb-line-soft` `#dedcdd`；首行去上线、首列去左线 |
| 表头格 | 底色 `--hb-surface` `#f4f3f3`，600，左对齐 |
| 对齐 | `vertical-align: top` |

外层包一个 `1px solid --hb-line` + `0.62rem` 圆角的面板。

### 4.2 竖式规格表

**源写法** `` ```{spec-table} INPUT PORTS `` → **产出** `figure.hb-spec-table-composition` > `table.hb-spec-table`

与通用表是**两套值**，不要混：这一类画粗深色外框，线也用深色。

| 属性 | 值 |
|---|---|
| 外框 | `2px solid --hb-brand-dark`，圆角 `0.92rem` |
| 列宽 | 标签 31% / 值 69%，`table-layout: fixed` |
| 字号 / 行高 | `0.9rem` / 1.25 |
| 单元格内边距 | `0.52rem 0.72rem` |
| 分隔线 | 右/下 `1.25px solid --hb-brand-dark`；末列去右线、末行去下线 |
| 标签格 | `<th scope="row">`，底色 `--hb-surface`，600 |
| 值格 | 底色 `--hb-paper`，400 |
| 对齐 | `vertical-align: middle` |
| 溢出 | 表格 `min-width: 40rem`，外层横向滚动（窄屏不压字） |
| 上标 | `.hb-spec-reference` = `0.62em`、`line-height: 0` |

合并：标签留空的行并入上一个标签（`rowspan`）。

印刷侧：LaTeX `spectable`（`components_spec.tex`）／IDML 表样式 `竖型表格` + `HB Rounded Table Outer`。token：`comp_spec_table_left_ratio` 0.315、`comp_table_outer_arc` 2.4mm、`comp_table_outer_rule` 0.75pt、`type_spec_label_font_size` / `type_spec_value_font_size` 均 6.0pt。

> 注意 Web 的 31% 与印刷的 0.315 是两个独立取值，改一处不会自动同步另一处。

### 4.3 警示框

**源写法** `` ```{callout} WARNING `` → **产出** `table.manual-callout-table`（左标签格 + 右正文格）

| 属性 | 值 |
|---|---|
| 外框 | `2px solid --hb-line-soft`，圆角 `0.82rem`，`overflow: hidden` |
| 底色 | `--hb-surface`（正文格） |
| 外边距 | `1rem 0 1.35rem` |
| 标签格 | 宽 `clamp(7.5rem, 16%, 9.5rem)`，白底，700，居中，垂直居中 |
| 标签内边距 | `0.82rem 0.72rem` |
| 布局 | `table-layout: fixed` |
| ≤520px | 标签与正文改为上下堆叠，标签转左对齐 |

信号词由源里的参数决定并自动转大写；正文按完整 Markdown 解析，可放列表。

印刷侧：LaTeX `HBWarningBlock` / `HBCautionBlock` / `HBNoteBlock` / `HBTipBlock`（`components_base.tex`）／IDML 段落样式 `Caution` + 对象样式 `HB Rounded Panel` + 表样式 `Notice表格`。

---

## 5. 响应式与打印

| 断点 | 影响本文范围的改动 |
|---|---|
| `min-width: 82rem` | 加宽阅读区，标题表格取值不变 |
| `max-width: 760px` | H1 缩号缩圆角；H2 圆点顶对齐、字号锁 `1rem`；符号栏转单列 |
| `max-width: 520px` | 警示框标签/正文堆叠 |
| `print` | H1/H2/H3 统一避免跨页断裂 |

字体：`Gilroy` 是商业授权，不随站分发；回退 `Avenir Next → Avenir → Segoe UI → Helvetica → Arial`，字形与印刷稿不完全一致。

## 6. 本次未覆盖

以下语义已有 CSS 与契约条目，但本文尚未逐条写定义：正文与列表（`HB-TYPE-BODY` / `HB-TYPE-LIST`）、图与图注、LCD 图标表与模式表（`HB-TABLE-LCD-ICON`）、符号表（`HB-TABLE-SYMBOL-SIGNAL` / `-ICON`）、故障排查表、对比表、质保卡片、封面/封底。

改样式的顺序始终是：先在 [`manual_style.yaml`](manual_style.yaml) 找语义 ID → 看它绑了哪些 token 与另外两个渲染器 → 再改 [`web_manual.css`](web_manual.css)。只改 CSS 会让三处渲染悄悄分叉。
