# 样式定义：文字与标题、警示与安全、表格（§2–§4）

属于[样式定义](../STYLE_DEFINITION.md)，其索引列出全部分页。章节编号与原文一致。
本主题的新说明写在本页，不要追加到总文件。

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

IDML 的 flowed H1 与 fixed/composed H1 必须消费同一个 `heading_text` +
`h1_frame_opts` 合同：文本框与深色标题条共用相同的纵向起点和高度，
`VerticalJustification=CenterAlign`，Gilroy 可见大写字面统一使用
`BaselineShift=0.5pt`。页面组件只能提交标题条外矩形；不得再提供独立
`title_text_rect`、负向 Y 偏移或 `BaselineShift=-1.5pt` 来抵消另一套基线。
Safety、Symbols、Inbox、Overview、Storage 以及 EN/FR/ES 都受同一回归约束。

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

token：`type_title_l2_font_size` 8.6pt、`comp_title_l2_bullet_radius` 0.75mm。IDML 的普通 H2 默认上下间距由 `idml_title_l2_space_before` / `idml_title_l2_space_after` 控制（当前均为 5.67pt）。Word：`dingding-heading2`，`sz` 28（14pt）。

IDML 的 `KeepWithNext` 由 `comp_title_l2_needspace` 推导。Operation Guide 中，凡 H2 后紧接可编辑 operation panel，标题到 panel 的间距统一使用 `idml_title_l2_space_after`（当前 5.67pt）；首个标题仍保留 `idml_operation_first_h2_space_before` 及语言覆盖。`idml_operation_inter_section_space_after` 是第一页的总节奏预算；渲染器会把统一标题后间距和 panel→正文间距从该预算等量扣回，使第二个 panel 的绝对位置保持不变。

Operation Guide 只计算一个三语各自的整页动态 content gap：以 `operation panel → CAUTION → body → CAUTION` 密集页的固定内容高度和可用文字框高度求值，并限制在 `idml_operation_stack_gap_min` / `idml_operation_stack_gap_max`（当前 8.5–14.17pt）之间；`idml_operation_stack_gap_preferred`（11.34pt）是模板参考值，`idml_operation_stack_page_fill_ratio`（0.84）控制内容在整页中的参考落点。该值随后统一复用于主电源 panel→正文、panel→CAUTION、CAUTION→正文、正文→CAUTION、Energy 正文→panel、Energy panel→NOTE。Energy 页新增的间距会从 NOTE→LED H2 的原有可调预算等量扣回，同时 LED H2→panel 仍为 5.67pt，因此 LED panel 不下移。所有匹配只依赖 block/component 结构和 `layout` 角色，不依赖 `NOTE`、`ENERGY SAVING MODE` 等可见语言文字。

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

### 2.5 页面局部标题变体（不新增语义 ID）

下面两类标题沿用既有标题语义，但为了批准页面的构图而采用专门投影。它们不是新的
`HB-*`，也不能反过来改变普通 H1/H2：

| 变体 | 视觉不变量 | 实现归属 |
|---|---|---|
| Safety subbar | PDF/IDML 为品牌深色全圆胶囊（stadium）+ 白色大写文字；Web 的普通 H2 仍保持 §2.3 的圆点标题 | `components_safety.tex` 与 Symbols/Safety IDML composer，共用 `type_subbar_*`、`comp_subbar_*` 及语言覆盖 token |
| TOC 大标题 | 深色大字、无底条；不得套用 §2.2 的 H1 胶囊 | LaTeX 目录组件与 IDML `HB TOC Title` |
| TOC 语言条 | 深色圆角条，语言标签和页码范围保持可编辑文字 | IDML `HB TOC Bar` / `HB TOC Range` 与 `page_toc.py`；批准页面几何由 composer 和 reference/视觉测试守护 |

页面局部变体不能成为绕过合同的后门。新增变体时，要么明确写成现有 `HB-*` 的
renderer-specific 投影并在本节登记，要么新增正式语义并走附录 A；不能只留在代码
注释或某个 renderer 的局部常量里。

### 2.6 引语 / 页脚 / 页码

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

Safety 首段文本框与后续深色 subbar 必须保留 `idml_safety_first_section_to_subbar_gap` 的净空；语言密度调整只能通过 `lang_<lang>_idml_safety_list_horizontal_scale_dense`，不得让文本框伸进标题条。

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

IDML 普通行由 `idml_spec_table_row_height` 控制；多行单元格使用 `comp_spec_table_multiline_min_height`，并输出 `MinimumHeight` / `AutoGrow`，不再由本地常量决定。compact Specifications 的所有单行固定为 `idml_compact_spec_table_row_height`，关闭 AutoGrow；圆角外壳高度严格等于该表全部行高之和。不得再设置逐表固定外壳高度，也不得把外壳余量塞进末行，否则同为单行的最后一行会被单独拉高。分节标题的圆点与文字共享同一组件基线合同：`idml_spec_section_text_baseline_shift`（及语言覆盖）确定标题基线，`idml_spec_section_bullet_baseline_offset` 只表达圆点相对文字的光学校正；`idml_spec_section_left_indent` 统一让圆点左边缘与随后表格的外框共线。所有分节和语言复用这些值，不逐标题写死位置。表格单元格里的圈号是引用标记，保持小号上标；页底脚注行首的同一圈号是注释编号，必须继承 `HB Spec Note` 的正常字号与基线。注册商标 `®` 保留字体自身的上标字形，不套用圈号引用规则。

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

表头默认 `Error Code` / `Corrective Measures`；plain-Markdown 可用类型化
`:headers: A | B` 提供两个本地化表头（见 [附录 B](appendix-b-boundaries.md#附录-b-已知边界)）。IDML 关闭自动缩放；批准语言的行 minima、表头/正文高度修正、内外线宽、面板下限、导入安全余量和 portable glyph-width 估算全部由 `idml_trouble_*` / `lang_*_idml_trouble_*` token 控制。
紧凑表的可见外壳高度严格等于可见行高总和；原生终止标记余量使用独立透明载体，最终化不得把余量加到圆角外框底部。

IDML production 由普通 block 流进入 `components/prose_table.py` 的公共
`render_table_block(...)` 边界。页面编排器只能提供外部 flow/frame，不能调用
`_troubleshooting_*` 私有 helper，也不能读取行高、列宽、填色、圆角或载体 token。
组件拥有 EN/FR/ES 行高增长、原生垂直居中、可见外壳和透明终止载体；最终化只可
按 `tf_terminal_carrier_group_*` 标签处理不可见载体，禁止改主表框、底板、遮罩、
外框或末行。具体接入与验收见
[`共享样式与完整组件应用指南`](../../../../code-as-doc/dev/style_component_usage_guide.md)。

### 4.4 LCD 图标表

`` ```{lcd-icons} `` → `figure.hb-lcd-table-composition`

| 属性 | 值 |
|---|---|
| 列宽 | 序号 6% / 图 11% / 名称 27% / 说明 56% |
| 字号 / 行高 | `0.9rem` / 1.23，`min-width: 42rem` |
| 内边距 | `0.7rem 0.72rem`；序号列左右内边距归零 |
| 分隔线 | 右/下 `1px solid --hb-line`（浅色，与规格表的深色不同） |
| 说明列 | 支持 ` / ` 分步；`On:` / `Blink:` / `Off:` 及本地化状态前缀保留源 strong 语义，IDML 输出为可编辑粗体字符 run |

四处语义对齐（`aligned`）。批准 reference profile 可保留型号特定行高，这是一条已批准边界说明；共享排版、位置和表结构仍由 token 控制，不是待修缺陷。

IDML 的可见圆角外壳高度严格等于全部行高之和；原生终止标记进入与主表框串接的
独立透明载体，而不是在末行或可见外壳下方留白。页面入口只传行数据、语言、批准
profile 和外部 story frame；它不能改列、行、图标、底板或 shell。最终化只能按
`tf_terminal_carrier_group_*` 标签扩展透明载体，不能读取表高后拉伸主表框、圆角
plate、mask 或 outline。EN/FR/ES 共用这一结构回归，应用方法见
[`共享样式与完整组件应用指南`](../../../../code-as-doc/dev/style_component_usage_guide.md)。

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

IDML 侧的 EN/FR/ES 批准 panel/row/column/margin/spacing、参考 measure、panel 宽度和插图目标均为语言 token；其他语言按内容动态计算列宽与行高。字号、leading、inset、内外线和圆角也全部 token 化，portable fallback 只消费登记的 fallback token。传入空参数时保留兼容默认，不改变旧调用者。Web 的 `HB-TABLE-LCD-MODE` 是共享语义组件，不依赖某个目标的插图能力授权。

### 4.6 符号表两类

- `` ```{symbols} `` → `figure.hb-symbol-pair-composition`：`grid-template-columns: repeat(2, minmax(0,1fr))`，间距 `clamp(.72rem, 1.8vw, 1rem)`，窄屏转单列。面板表内边距 `clamp(.62rem,1.5vw,.9rem)` `clamp(.55rem,1.25vw,.78rem)`，格间线 `1.5px solid --hb-brand-dark`，表头下边框同宽。**两个面板行高互不影响**（PDF 用的就是两张独立表）。
- 信号词表 `HB-TABLE-SYMBOL-SIGNAL` → `.hb-symbol-signal-composition`，流水线专属，md 写不出。

IDML 的 subbar 高度、标题/维护区间距、页面下限和非批准语言 fallback 估算均来自 `manual_style.yaml` 登记的 token；两类 Symbols 表均为 `aligned`。Symbols H1 不再拥有独立光学偏移 token，统一服从 §2.2 的共享标题框与字面基线。标准 JE 密度保留已批准的固定行高及 `0.25pt` 外壳承载容差；compact 密度的较大 `idml_compact_symbols_*_frame_allowance` 必须由组件吸收到可见正文行内，不能悬空成为表格尾部白带。InDesign 终止标记需要的原生承载空间由独立的透明文本框余量 `idml_symbols_native_carrier_allowance` 提供；它不属于可见外壳、底板、遮罩或行高。组件不缩字、不改分栏，也不允许最终化脚本隐藏 overset。

IDML 的完整可编辑单元是 `SymbolsPanel`，而不是页面 composer 中的三张散表。组件内部拥有标题条、圆角外壳、列宽、各行高度、表格载体余量、信号词表与图标表之间的最小间距，以及内容超出可用高度时的续页拆分。JE/JBP 页面 composer 只能传入本地化数据、语言、`standard` / `compact` 密度和组件可用矩形；它可以决定组件放在哪里，但不能再调用 Symbols 表格 primitive 或覆盖内部几何。两种密度遵守同一填色规则：只有 `Symbol` / 图标列使用 K05，`Meaning` 列和圆角外壳保持 Paper；compact 可见行完整占满外框，标准密度仅保留原有 `0.25pt` 容差，因此底板不再替大块尾部空带补色或补画分隔线。最终化脚本只能校准透明的原生载体文本框，禁止改写圆角外壳、K05 底板、遮罩、分隔线或表格行。EN/FR/ES 的两种密度共同使用 [`tests/fixtures/idml_symbols_panel_golden.json`](../../../../tests/fixtures/idml_symbols_panel_golden.json) 作为几何与可编辑 Story 回归基准，边界测试同时禁止页面 composer 重新消费内部行高 token。

新产线或新页面不得从低层 Symbols primitive 重新组装同一内容；公共调用形状、允许
输入和边界验收见
[`共享样式与完整组件应用指南`](../../../../code-as-doc/dev/style_component_usage_guide.md)。

### 4.7 对比表

`` ```{comparison} 左表头 | 右表头 `` → `figure.hb-auto-resume-composition`

| 属性 | 值 |
|---|---|
| 外框 | `2px solid --hb-brand-dark`，圆角 `1rem` |
| 字号 | 表 `0.91rem`；表头 `0.98rem`/700 |
| 内边距 | `0.46rem 0.72rem`，分隔线 `1px solid --hb-brand-dark` |
| 左列底色 | `--hb-surface`；右列 `--hb-paper` |
| 合并 | 每列独立向上合并 |

IDML 使用独立的 `table_auto_resume` 角色，不再退化成普通表；对比语义可由 IR 到最终 IDML 单独审计。Web 的 `HB-TABLE-AUTO-RESUME` 同样属于共享语义组件，不依赖某个目标的插图能力授权。

### 4.8 按键组合表

`HB-TABLE-KEY-COMBINATIONS`，流水线专属，Web 落到通用 `.manual-table`。IDML 用可移动文本框承载 `HB Data Header` / `HB Data Body`，四处对齐。
