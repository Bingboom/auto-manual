# 手册样式合同与维护指南

> **唯一的人类可读样式规范。** 新增组件、调整版式、查询四端绑定或追踪
> RST → Web 结构，都从本文开始。LaTeX 的旧注册表、IDML 的旧样式地图和旧标题
> 指南只保留兼容入口，不再各自维护规则。

一个手册语义会投影到四个输出面：**Web**（`web_manual.css`）、**PDF**
（LaTeX）、**IDML**（InDesign）和 **Word**（`reference.docx`）。本文统一回答五个
问题：语义是什么、源结构怎样表达、四端分别由谁实现、当前视觉合同是什么、修改后
怎样验证。

如果你只想做一件事，可直接跳转：

| 任务 | 入口 |
|---|---|
| 查某个 `HB-*` 在四端的绑定 | [§1 全量对照总表](#1-全量对照总表) |
| 调标题、表格、警示框或专题组件 | [§2–§8 视觉与实现合同](STYLE_DEFINITION/text-callouts-tables.md#2-文字与标题) |
| 看原始 RST 怎样变成 Web 版面 | [§10 逐层实例](STYLE_DEFINITION/layer-walkthrough.md#10-逐层实例原始-rst-怎么变成-web-版面) |
| 把已有样式或组件接到新型号/语言/页面 | [共享样式与完整组件应用指南](../../../code-as-doc/dev/style_component_usage_guide.md) |
| 新增组件或修改共享样式 | [附录 A 维护流程](STYLE_DEFINITION/appendix-a-maintenance.md#附录-a-组件与维护流程) |
| 查当前未对齐项或工具限制 | [附录 B 已知边界](STYLE_DEFINITION/appendix-b-boundaries.md#附录-b-已知边界) |

本文不保存某次构建的 commit、hash、页数或测试数量。这些会随发布变化，属于
[执行状态](../../../code-as-doc/dev/style_debt_execution_status.md)和批准
reference-layout 记录；复制进规范只会制造第二份过期事实。

## 本文怎样分页

本文保留 §1 全量对照总表和 §8 渲染器实现边界（测试直接读取这两节），其余章节
按原编号原样放在 `STYLE_DEFINITION/` 下的分页里。只打开任务需要的那一页；新增说明
写进所属分页，新增分页时在下表加一行，不要把说明追加到本文。

| 章节 | 位置 | 什么时候读 |
| --- | --- | --- |
| §0 | [`authority-and-approval.md`](STYLE_DEFINITION/authority-and-approval.md) | 判断哪个文件说了算、改动属于内容/语义/外观哪条路线、欠账与批准变体、流水线怎样加标识符、ComponentSpec 或可见文案来源 |
| §1 | 本文下方 | 查某个 `HB-*` 在 Web、PDF、IDML、Word 四端的绑定和状态 |
| §2–§4 | [`text-callouts-tables.md`](STYLE_DEFINITION/text-callouts-tables.md) | 调正文与列表、各级标题、警示框、安全面板，或通用表、规格表、故障排查表、LCD 表、符号表、对比表、按键组合表 |
| §5–§7 | [`figures-warranty-templates.md`](STYLE_DEFINITION/figures-warranty-templates.md) | 处理插图与专题版块、新录入网页的图文分工、质保组件或页面模板 |
| §8 | 本文下方 | 查 Web、LaTeX、IDML、Word 各渲染器的归属与不变量 |
| §9 | [`authority-and-approval.md`](STYLE_DEFINITION/authority-and-approval.md) | 判断合同何时生效、`aligned` / `partial` 的含义，或投影差异怎样登记 |
| §10 | [`layer-walkthrough.md`](STYLE_DEFINITION/layer-walkthrough.md) | 看原始 RST 逐层变成 Web 版面，或批量把存量文档转成当前 Web 样式 |
| §10.7 内「共用图标优先」 | [`web-artwork-reuse.md`](STYLE_DEFINITION/web-artwork-reuse.md) | 做任何说明书网页化的素材工作之前：先盘点、复用已有素材，再决定是否提取（AGENTS.md §3） |
| 附录 A | [`appendix-a-maintenance.md`](STYLE_DEFINITION/appendix-a-maintenance.md) | 新增组件、复用已有样式或完整组件，或修改共享样式 |
| 附录 B 及其后各节 | [`appendix-b-boundaries.md`](STYLE_DEFINITION/appendix-b-boundaries.md) | 查已知边界与兼容入口，或原稿组件说明：`HB-TABLE-REFERENCE`、原稿 LCD/面板、标题型号与警告框、PACKAGE LIST 分组、JA-AD600A EU 底图复核、原生前言 |

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
| 前言 / 引题 | `HB-TYPE-LEAD` | 流水线 | — | `HBTypeWarningTextStart`、`HBTypeRubricStart` | `HB Lead` | 经 HTML 转换 | aligned |
| 页脚 | `HB-TYPE-FOOTER` | 流水线 | 不渲染 | `HBTypeFooter` | `HB Footer` | 页脚域 | aligned |
| 页码 | `HB-TYPE-PAGE-NUMBER` | 流水线 | 不渲染 | `HBTypePageNumber` | `HB Page Number` | 页脚域 | aligned |

### 警示与安全

| 语义 | 语义 ID | 源写法 | Web | PDF | IDML | Word | 状态 |
|---|---|---|---|---|---|---|---|
| 警示框 | `HB-CALLOUT-STRIP` | `` ```{callout} `` | `.manual-callout-table` | warning/danger → `HBWarningBlock`；其余 → `HBCautionBlock` / `HBNoteBlock` / `HBTipBlock` @ `components_base` | `Caution` + `HB Rounded Panel` + `Notice表格` | 经 HTML 转换（标签文字归一） | aligned |
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
| 纯文字参考表 | `HB-TABLE-REFERENCE` | RST 显式语义声明 | `.hb-reference-composition` | 仅语义投影 | 仅语义投影 | 仅语义投影 | Web rendered；其余 projection-only |
| 通用表 | 无专属 ID | pipe 表 / `` ```{manual-table} `` | `.manual-table` | 走 `HB-TYPE-BODY` 排版 | `正文表格` | 表样式 `tableHeader`（单行且 ≥3 列时 `TableGrid`） | — |

IDML 的普通内容流采用三组可复用默认节奏：H2 上/下间距、普通图上/下间距、普通表上/下间距，分别由 `idml_title_l2_space_*`、`idml_figure_space_*`、`idml_data_table_space_*` 控制。当前 H2→图的组合净距为 5.67pt + 2.83pt，图→普通表为 4.25pt + 5.67pt。Operations、App、Charging、Product Overview、UPS、Troubleshooting 和 Specifications 等批准组件已有更具体 token 时覆盖这些默认值，不叠加逐页补丁。Charging 的图→带尾部胶囊标题属于完整组合内部过渡：只消费 `idml_charging_figure_space_after` 与 `idml_charging_headingpill_space_before`，不能再叠普通图后距与普通 H2 前距。该标题行的横向几何也归共享 `HeadingPill` 所有：标题列和胶囊列按 Gilroy Bold 字面宽度收紧，组件用 10.9pt 定义标题末字到胶囊首字的可见间距；页面编排器只能放置整行，不能把胶囊右对齐或重新分配两列宽度。

Storage 不定义产线专属标题条或正文卡。JE-1000F 与 JBP 共用
`h1_pill_paragraph` + prose story：同一 inline H1 的字面缩进和基线、同一正文
段落/列表规则、同一纸白内容流。compact `storage_specifications` 只能为 Storage
与 Specifications 分配外部故事矩形，不能添加 K05 正文底板、圆角、inset 或另建
标题故事。

生产 IDML 的普通 H2 圆点必须使用内联原生矢量圆和独立间隔对象，不能把
`●` 交给 Segoe UI Symbol、Yu Gothic 或其他平台字体。这样 Windows 与 macOS
打开同一自包含 IDML 时不会因缺字、替代字体或字面裁切而改变标题。圆点直径和
标题间距继续只消费 `comp_title_l2_bullet_radius` / `comp_title_l2_gap`；目标装配
不得通过标题文字、页码或型号分支替换这项共享语义。

规格值中的直流符号 `⎓` 同样由共享原生矢量输出，但其字面必须复刻 JE-1000F
批准稿的 Apple Symbols U+2393：2048 em、1514 advance、左右各 128 side bearing，
线条与断线位置按当前 `HB Spec Value` 字号等比缩放。standard/compact 与 EN/FR/ES
只能传规格文字和字号，不能另选字体、扩大符号或覆写基线；因此 JBP 与 JE 的直流
符号使用同一字宽、线重和垂直位置。

App 原生故事的编号与列表使用显式悬挂/tab 合同，不再依赖圆点后的普通空格估算。H2 圆点留在版心起点，并由 `idml_app_h2_marker_font_size` / `idml_app_h2_marker_baseline_shift` 单独约束在首个 tab 内；H2 编号文本与 H3 的 `4.x` 编号共同落在 `idml_app_notes_left_indent`。列表圆点由 `idml_app_list_left_indent` 与该编号边对齐，首行正文和全部续行则共同落在 `bullet_left - idml_app_list_first_line_indent` 的固定 tab 位。英文、法文及任何结构化为 App list 的语言都复用这组属性，不按标题文字或页码追加坐标补丁。

UPS 与 Charging 共用一条可编辑内容流：三语各自的 `lang_*_idml_ups_caution_space_after` 控制 UPS CAUTION→CHARGING 标题，`idml_charging_emphasis_space_before` 控制 Charging 引言→黑色强调胶囊。当前强调胶囊前距为 5pt；三语 CAUTION 后距相对上一版等量减少 4pt，因此重分配节奏但保持页面总深度、后续 NOTE 位置和分页不变。`idml_charging_emphasis_horizontal_padding` 同时登记文字左侧光学缩进与总宽的双端 allowance：左侧由段落 `LeftIndent` 明确落位，使字面与 CHARGING 标题内容对齐；右侧不写 `RightIndent`，而由总宽余量自然保留。不能再叠加非对称 frame inset 或右段落缩进，否则会重复缩窄可用行宽并把结尾挤成溢流。文本框继续使用 `VerticalJustification=CenterAlign`；完整文案保持单行后，垂直居中不再被隐藏的第二行拉偏。Charging 方法页的插图段落已经自带 AboveLine 原生行盒，所以图后的 `4.25pt` 普通后距与尾部胶囊标题前的 `5.67pt` 普通前距不得再次相加；共享 `charging` 变体把这两个显式边距都置零，EN/FR/ES 共用同一图→标题回归。该关系由组件 token 与估算高度共同维护，不允许在单页 XML 上追加坐标补丁。

IDML 可编辑表格的普通单元格统一由 `primitives.cell()` 输出 `VerticalJustification=CenterAlign`，模板合成阶段必须保留该语义属性，不允许因移除颜色、边线或 inset 覆盖而一并丢失。Troubleshooting 的 F6/F7 等多步骤行还要求左右格使用对称的上下内边距，正文格与错误码格都不得再叠加逐语言、逐行的 `BaselineShift`；否则虽然 XML 声明居中，视觉位置仍会被二次位移。LCD、Symbols 和通用图片表的图标段落另显式输出 `Justification=CenterAlign`，因此图标在格内同时横向、纵向居中。Symbols 信号词徽标分成两层基线合同：`idml_symbols_signal_badge_baseline_shift` 只校正整块深色徽标在表格行内的位置，`idml_symbols_signal_content_baseline_shift` 则统一校正徽标内部图标与文字的可见字面；两者不能用一次递归 `BaselineShift` 覆盖。圆角 WARNING/callout 不依赖表格默认值：标签框、正文框和黑框正文使用同一 `TextFramePreference.VerticalJustification=CenterAlign` 合同。

Troubleshooting 的短表和完整表共用 `HB-TABLE-TROUBLESHOOTING`，但行高预算
必须由真实行数和本地化换行计算：只有完整 12 行 profile 才消费其冻结 ordinal
minima；紧凑表使用 `idml_trouble_extra_row_min_height` 和
`idml_trouble_compact_outer_radius`。错误码列宽同时测量表头与全部代码，右侧表头
保持纸白，首列按合同使用灰底；源 RST 的 line-block 分隔符只能表达换行，不能以
字面量 `|` 进入单元格。故障段落和表格默认关闭断词，避免在错误码和措施文字中
产生源稿没有的词内断行。紧凑表把测得高度同时写入 `SingleRowHeight` 与
`MinimumHeight` 并关闭 AutoGrow，使可见行完整占满圆角外壳；表格内容框在圆角
外壳底边终止，随后串接一个独立、无填色无描边的透明文本框，专门承载终止标记。
`idml_trouble_native_carrier_allowance` 只决定该载体的初始高度，不属于外壳或首列
灰底。InDesign 最终化只能按 `tf_terminal_carrier_group_*` 的稳定标签校准该透明
载体，不能读取实际表高后改写可见外壳、内容框、遮罩或表格行。

### 专题版块

| 语义 | 语义 ID | 源写法 | Web | PDF | IDML | Word | 状态 |
|---|---|---|---|---|---|---|---|
| FCC 面板 | `HB-SPECIAL-FCC` | 流水线 | `.hb-fcc-composition` | `HBFccBlock` @ `components_special_pages` | `HB Rounded Panel` + `无表头表格` | `.hb-fcc-word-table` 双栏活文本 | **aligned** |
| 开箱清单卡 | `HB-SPECIAL-INBOX` | 流水线 | `.hb-inbox-composition`（三卡/可变卡） | `HBInBoxThree`（仅三卡） | `Item List Text` + `HB Inbox Card` + `无表头表格`（仅三卡） | `.hb-inbox-word-table` 活图文卡（仅三卡） | **aligned** |
| 产品概览 | `HB-SPECIAL-OVERVIEW` | 流水线 | `.hb-annotated-figure` | `HBOverviewPanel` | `HB Body`（可移动文本框） | 经 HTML 转换 | **aligned** |
| 操作面板 | `HB-SPECIAL-OPERATION` | 流水线 | `.hb-operation-figure` | `HBOperationPanel` | `oppanel` + `HB Operation Row Label`（可移动文本框） | 经 HTML 转换 | **aligned** |
| App 设置 | `HB-SPECIAL-APP` | 流水线 | `.hb-app-download-composition`、`.hb-app-add-device-composition` | `HBAppStep`、`HBAppAsset`、`HBAppNotice` | `HB Body` / `HB Callout Label` / `HB Callout Body` + `HB Rounded Panel` | 经 HTML 转换 | **aligned** |
| 参考整图 | `HB-SPECIAL-REFERENCE-FIGURE` | 流水线 | `.hb-reference-figure` | 通用图片投影 | `referencefigure`（可移动文本框） | 经 HTML 转换 | **aligned** |

### 质保与页面

| 语义 | 语义 ID | 源写法 | Web | PDF | IDML | Word | 状态 |
|---|---|---|---|---|---|---|---|
| 质保引语 | `HB-WARRANTY-LEAD` | 流水线 | `.hb-warranty-intro-composition` | `HBWarrantyLead` @ `components_warranty` | `HB Rounded Panel` | 经 HTML 转换 | aligned |
| 质保条款面板 | `HB-WARRANTY-SECTION` | 流水线 | `.hb-warranty-card` | `HBWarrantySection` | `HB Rounded Panel` | 经 HTML 转换 | aligned |
| 质保年限卡 | `HB-WARRANTY-YEARS` | 流水线 | `.hb-warranty-period-card` | `HBWarrantyYears` | `HB Big Numeral` + `HB Rounded Panel` | 经 HTML 转换 | aligned |
| 标准页 | `HB-PAGE-STANDARD` | 模板 | 无分页 | `HBPageTemplateStandard` @ `layout_templates` | `HB Standard Page` | 节属性 | aligned |
| 无页脚页 | `HB-PAGE-NO-FOOTER` | 模板 | 无分页 | `HBPageTemplateNoFooter` | `HB No Footer Page` | 节属性 | aligned |
| 封面 / 封底 | `HB-PAGE-COVER` | 模板 | 不渲染 | `HBPageTemplateCover`、`HBBackCoverPage` | `HB Cover Page` | 不渲染 | aligned |

> Web 不分页：`HB-PAGE-*`、`HB-TYPE-FOOTER`、`HB-TYPE-PAGE-NUMBER` 在网页投影里没有对应物，只在 PDF/IDML 生效。

---

## 8. 渲染器实现边界

本节收拢过去分别维护在 LaTeX registry、IDML style map 和标题指南里的实现规则。
这里登记**归属和不变量**；具体函数、宏和数值仍以代码与 token 为准。

### 8.1 Web：响应式、打印、字体

| 断点 | 改动 |
|---|---|
| `min-width: 82rem` | 加宽阅读区，组件取值不变 |
| `max-width: 760px` | H1 缩号缩圆角；H2 圆点顶对齐、字号锁 `1rem`；符号双栏转单列；LCD 模式转单列 |
| `max-width: 520px` | 警示框标签/正文上下堆叠 |
| `print` | H1/H2/H3 统一避免跨页断裂 |

所有通栏组件共享一条外宽契约：`box-sizing: border-box; width: 100%; max-width: var(--hb-component-band-max)`（= 阅读宽 58rem），成员包括 `h1`、docutils 表格容器、符号 / 故障排查 / 规格 / FCC / LCD / 对比六类 composition。新增通栏组件必须加进这条 `:is()` 列表，否则宽度会和邻居差一截。

整本 Web 文档不再生成文内语言跳转条和 `#hb-lang-*` 锚点；语言切换由手册中心的
[语言下拉框](../../../code-as-doc/dev/rtd_locale_navigation.md)承担。`declared_languages`
至少有两项时，整本 IR 重放器仍校验语言：未知、重复、越界或没有页面的语言均 fail-closed；
首个片段开头与声明语言一致的合并语言清单行（英文名或本地名，以 ` / ` 分隔）照旧删除。
目标 overlay 不得另造语言导航 HTML/CSS。

字体：`Gilroy` 是商业授权，不随站分发；回退 `Avenir Next → Avenir → Segoe UI → Helvetica → Arial`，字形与印刷稿不完全一致。

### 8.2 LaTeX：模块归属与加载顺序

`theme.tex` 按依赖顺序加载组件，`docs/conf_base.py` 以相同顺序复制进 Sphinx
LaTeX bundle。公共宏是模板与 doctree transform 的稳定 API，不能在重构时改名。

| 顺序 | 模块 | 只负责 |
|---:|---|---|
| 1 | `components_base.tex` | 图片、列表、通用表框架、callout 基础 |
| 2 | `components_headings.tex` | L1/L2/L3 标题对象 |
| 3 | `components_special_pages.tex` | 封底、App、开箱、概览、FCC、前言、目录 |
| 4 | `components_symbols.tex` | 信号词表与符号图标表 |
| 5 | `components_lcd.tex` | LCD 图标表与模式表 |
| 6 | `components_safety.tex` | 安全指令、WARNING、DANGER |
| 7 | `components_spec.tex` | 规格页与规格表 |
| 8 | `components_data_tables.tex` | Auto Resume、按键组合、故障排查 |
| 9 | `components_warranty.tex` | 质保引语、条款与年限卡 |

`type_system.tex` 和 `layout_templates.tex` 是跨组件基础层，不属于某个专题组件。
新增可见语义时，§1 的 PDF 列必须写公共入口和 owner；组件文件只能拥有自己的
公共宏，兼容别名必须在测试 allowlist 中显式登记。

### 8.3 IDML：可编辑对象与几何机制

IDML 的目标不是把 PDF 截图放进 InDesign，而是用可编辑的段落、表格、文本框、
矢量路径和已批准链接资产复现同一语义。以下规则是正式实现边界：

1. **参数单源。** 可见字号、间距、线宽、圆角和语言覆盖从
   `layout_params.csv` 经 `writer.params` 消费；renderer-local 常量只能是非可见
   容错量，并应有直接合同测试。
2. **内容与样式分离。** 文案、表行、信号词和资产身份来自 RST/IR；IDML renderer
   不翻译、不补默认标签，也不根据本地化文字决定组件类型。
3. **圆角外壳与可编辑内容分层。** 表格使用“圆角背景 + 方形可编辑内容框 +
   四角遮罩 + 顶层描边”；内部网格不负责外圆角。警示框、卡片和 H1 使用可编辑
   文本框叠加矢量路径。
4. **锚定对象有固定依赖顺序。** 子故事在 designmap 中位于宿主故事之后；内联锚定
   使用 `AnchoredObjectSetting`。圆角用贝塞尔路径本体，不依赖导入后不稳定的
   Corner 属性。
5. **自动尺寸必须按组件选择。** 普通文本框可用受控的 height-only 自适应；表格
   外壳不能套通用 auto-size。LCD 与 Symbols 在 InDesign 最终化后读取原生行高，
   同步收紧背景、内容框、遮罩和描边。
6. **语言差异只能选 token/profile。** FR/ES 等密度差异使用
   `lang_<lang>_*` token 或批准 reference profile；禁止复制一套逐语言绘制代码。
7. **批准目标 fail-closed。** 缺组件角色、token、链接资产或 composition binding
   时停止构建；不能静默降级成普通 prose 或把内容推入 overset 后继续交付。
8. **内容流先用默认节奏，再由语义组件覆盖。** 普通 H2、图片和表格消费
   `idml_title_l2_space_*`、`idml_figure_space_*`、`idml_data_table_space_*`；专题组件
   只通过已登记 token 覆盖，不按页名追加邻接位置补丁。

IDML 的段落/表格/对象样式名在 §1 的 IDML 列登记；实现入口集中在
`tools/idml/components/`、`tools/idml/styles.py`、`tools/idml/page_objects.py` 和
各页面 composer。一次性量测和修复证据留在历史执行记录，不回填到本节。

### 8.4 Word：结构归一而非固定页复刻

Word 复用结构语义，但不承诺 PDF/IDML 的固定页几何：

- Heading 1/2/3 归一到 `dingding-heading1/2/3`；
- 正文归一到 `BodyText` / `FirstParagraph` / `Compact`；
- 表格按形状选 `TableGrid` 或 `tableHeader`，必要时再做列宽和边框覆盖；
- 文档标题来自配置的 `build.word_title`，不是正文中的第一个 H1；
- `tools/word/bundle_docx_styles.py` 只做样式归一，不按英文标题匹配语义。

Word 若需要新增独立组件样式，应先进入 `manual_style.yaml` 的 `word` binding 与 §1
的语义对照，不能只在 DOCX remapper 中增加一次性规则。
