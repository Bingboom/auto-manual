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
| 调标题、表格、警示框或专题组件 | [§2–§8 视觉与实现合同](#2-文字与标题) |
| 看原始 RST 怎样变成 Web 版面 | [§10 逐层实例](#10-逐层实例原始-rst-怎么变成-web-版面) |
| 新增组件或修改共享样式 | [附录 A 维护流程](#附录-a-组件与维护流程) |
| 查当前未对齐项或工具限制 | [附录 B 已知边界](#附录-b-已知边界) |

本文不保存某次构建的 commit、hash、页数或测试数量。这些会随发布变化，属于
[执行状态](../../../code-as-doc/dev/style_debt_execution_status.md)和批准
reference-layout 记录；复制进规范只会制造第二份过期事实。

## 0. 权威边界与使用方法

### 0.1 哪个文件决定什么

“一份文档”不等于把机器合同改写成散文。可持续维护依赖下面六层各守边界：

| 层 | 权威来源 | 决定什么 | 不应该放什么 |
|---|---|---|---|
| 人类规范 | **本文** | 视觉意图、四端对照、实现归属、修改与验证方法 | 构建快照、临时排期、一次性 hash |
| 语义合同 | [`manual_style.yaml`](manual_style.yaml) | 31 个稳定 `HB-*` ID、四端 capability/binding、theme-token role、`conformance`、`constraints`、`approved_variants` | CSS 像素值、逐页坐标 |
| 组件实例合同 | [`component_registry.yaml`](component_registry.yaml) + [`tools/component_specs/`](../../../tools/component_specs/) | 可跨 renderer 传递的 ComponentSpec 类型、variant、slot、asset role、token role 与 adapter key | CSS/TeX/XML/DOCX 几何实现、逐页坐标 |
| 主题投影合同 | [`manual_theme.yaml`](manual_theme.yaml) | 稳定 `theme_id`、组件视觉角色及四端具体 binding | 单位值、目标/语言几何、页面实例坐标 |
| 数值 token | [`data/layout_params.csv`](../../../data/layout_params.csv) | PDF/IDML 共用的字号、间距、线宽、圆角及语言覆盖 | 组件路由和可见文案 |
| 渲染实现 | Web CSS、LaTeX 模块、IDML renderer、Word remapper | 把合同投影成目标格式 | 自创未登记语义或渲染器本地可见常量 |

冲突处理顺序：先确认语义合同和 token 是否正确，再修渲染实现，最后在**同一改动**
更新本文。不能用“文档写了某个值”覆盖机器合同，也不能因为当前 CSS/IDML 恰好能
渲染，就把未登记行为当成正式样式。

`manual_style.yaml` 当前使用 schema v2，机器校验 LaTeX、IDML、Web、Word、token、
component adapter、capability 和边界记录。本文仍是四端维护入口和视觉意图来源；机器
绑定以 YAML 为准，直接测试负责确认登记的 CSS selector、Word style 与 adapter 真实
存在。公共 loader 在一个兼容窗口内仍可读取 schema v1，但新提交不得继续写 v1。

`component_registry.yaml` 当前使用 `component-registry/v1`。它不取代
`manual_style.yaml`：前者约束“一个具体组件实例带什么语义内容并调用哪个 adapter”，
后者约束“这个语义样式在四端由谁实现、当前是否对齐”。两者以同一个 `HB-*` style ID、
variant、capability 和 token role 做机器校验，不能各自维护一套组件分类。

`manual_theme.yaml` 当前使用 `manual-theme/v1`。它把
`component.callout`、`component.table.spec` 这类组件 token role 展开为
`surface.brand`、`border.strong`、`type.table.label` 等语义角色，再绑定到
CSS custom property、LaTeX/layout token、IDML style/token 和 Word property adapter。
校验器要求每个角色有消费者、每个组件 token role 有投影、每个投影四端
绑定完整。它不存储 `px` / `pt` / `mm` 数值或页面坐标；固定页单位仍以
`layout_params.csv` 为权威，Web 数值仍由 CSS 自定义属性所有。

### 0.2 改动路由：先判断你改的是内容、语义还是外观

| 你要改什么 | 正确入口 | 常见错误 |
|---|---|---|
| 标题、表头、标签等可见文字 | `Manual_Copy_Source.csv`、模板 RST、源表或配置 | 在 CSS/renderer 里按英文文案匹配 |
| 标题层级、组件类型、表格角色 | 模板/生成器的稳定结构标识 + extractor/IR + `manual_style.yaml` | 根据翻译后的标题猜语义 |
| 字号、间距、线宽、圆角、列宽 | `layout_params.csv` 或 Web CSS；再检查四端投影 | 只改一个 renderer 的本地常量 |
| 某个已评审目标的文字 | `docs/_review/<model>/<region>/page/*.rst` | 为单个目标改共享模板 |
| 存量 Markdown 的自动识别 | `plain_markdown_site.py` → 人工确认中间指令 | 把启发式识别接进 production |
| 批准 IDML 的最后一公里几何 | reference-layout 合同允许的 frame/page/asset 调整 | 在 InDesign 最终化阶段改正文内容 |

标题文字与样式要特别分开：结构层级来自 RST 标题或稳定组件角色；共享短文案来自
`Manual_Copy_Source.csv` 及生成的 `Localized_Copy.csv` / `spec_titles.csv`；Word
文档标题来自配置的 `build.word_title`。改变文字不等于改变样式，改变样式也不应
改写文字。

#### 0.2.1 §1 对照表怎样读

| 列 | 含义 |
|---|---|
| **语义 ID** | `manual_style.yaml` 里的契约名。改样式先找它，再核对四端投影 |
| **源写法** | 作者在 md / RST 里怎么写。`原生` = 普通 Markdown；`` ```{x} `` = MyST 围栏指令；`流水线` = 由生产流水线写入结构标识，不能靠普通正文直接表达（见下文） |
| **Web** | 顶层 class（`web_manual.css` 的挂点） |
| **PDF** | LaTeX 入口宏 @ 所属 `docs/renderers/latex/*.tex` |
| **IDML** | InDesign 段落样式 / 表样式 / 对象样式 |
| **Word** | `reference.docx` 的样式 ID，或"经 HTML 转换"（无独立样式）。Word 侧的表样式**按形状选，不按语义选**：单行且 ≥3 列走 `TableGrid`，其余走 `tableHeader` |
| **状态** | `aligned` = 四处的语义和共享合同一致；`partial` = 仍有可修复的 conformance debt。constraint 和 approved variant 本身不构成 `partial`，见 §0.3 |

单位：Web 用 `rem`（1rem = 16px），`clamp(最小, 视口比例, 最大)` = 随视口缩放并夹住两端；PDF/IDML 用 pt/mm，值取自 [`data/layout_params.csv`](../../../data/layout_params.csv)；Word 的 `sz` 是半磅（34 = 17pt）。

颜色变量：`--hb-brand-dark` `#343031`、`--hb-text` `#343031`、`--hb-text-muted` `#666264`、`--hb-line` `#a7a5a6`、`--hb-line-soft` `#dedcdd`、`--hb-paper` `#ffffff`、`--hb-surface` `#f4f3f3`。

### 0.3 欠账、约束与批准变体

样式状态只描述共享语义是否按合同投影，不能把所有端间差异都叫“欠账”。统一使用
下面三个互斥的分类：

| 分类 | 定义 | 必备记录 | 对 `conformance.state` 的影响 |
|---|---|---|---|
| `debt` | 已承诺的共享语义在一个或多个适用输出面缺失、错误、未登记或缺少守护，且可以通过实现修复的 conformance gap | 原因、受影响输出面、owner、修复条件和测试证据 | 未销账时必须是 `partial` |
| `constraint` | 共享语义合同有意接受的 renderer / platform 能力边界，例如响应式 Web 不分页、封面使用批准成品美术 | 原因、适用 renderer、scope、owner 和验证证据 | 本身不构成 `partial` |
| `approved_variant` | 经评审并由测试或 reference 合同钉住的 target / model / region / language / renderer 几何或行为差异 | scope、批准理由、owner、参数或绑定来源、回归证据 | 本身不构成 `partial` |

`aligned` 不等于四端逐像素相同；只要同一语义的所有适用投影都按合同工作，就可以
同时带有 constraint 或 approved variant。只有仍存在可执行的 `debt` 才使用
`partial`。不能为了把状态改绿，把可修复缺陷改名为平台约束；也不能把未评审的
renderer-local 常量称为批准变体。

生命周期固定为：

1. 发现差异时先分类，不直接改 `conformance.state`；不确定时按 debt 候选处理。
2. 在机器合同的 `conformance.debt`、`constraints` 或 `approved_variants` 记录
   `reason`、`owner`、`scope` 和 `evidence`。schema v2 的 strict 模式只报告
   actionable debt，不把平台约束或批准变体误报为欠账。
3. debt 只有在实现、直接测试和适用的四端验证通过后才销账；constraint 和
   approved variant 必须有边界测试或 reference pin，不能只留散文说明。
4. 平台能力、目标范围或批准结论变化时重新评审：可修复的 constraint 可以重分类为
   debt；不再需要的 variant 应删除其专属参数和守护。
5. 修改分类时同步 `manual_style.yaml`、本文 §1/对应视觉章节和执行 ledger；一次性
   hash、构建数量和 PR 证据只写执行 ledger。

### 0.4 “流水线”的定义

本文的**流水线**特指以 [`build.py`](../../../build.py) 为入口的生产手册链路：源表数据与 [`docs/templates/`](../../templates/) 组合成 prepared RST bundle，再由 [`tools/idml_rst_extract.py`](../../../tools/idml_rst_extract.py) 提取为 `manual-ir/v1`，最后投影到 Web、PDF、IDML 或 Word。它不是“根据文字长得像什么来猜组件”，也不是本 PR 新增的 plain-Markdown 预览链路；[`tools/plain_markdown_site.py`](../../../tools/plain_markdown_site.py) 只是把历史 Markdown 转成可审阅的中间指令并构建静态站点，不参与 production 发布装配。

```text
phase2 / 模板
    → prepared RST bundle（数据已替换、语言与页面顺序已确定）
    → RST extractor（识别结构标识）
    → manual-ir/v1（有类型、有来源、有哈希）
    → renderer projection（Web / PDF / IDML / Word）
```

“流水线”一栏表示：该语义由源表字段、模板宏、显式 RST 容器、页面清单或页面角色共同产生，普通作者不能只写一段同名文案就触发它。例如正文出现 `Warranty Period` 不会自动变成质保年限卡；模板必须显式写出 `warranty-section warranty-years`。

### 0.5 流水线怎样加标识符

标识分五层，彼此不能混用：

| 层 | 标识示例 | 谁写入 / 负责什么 |
|---|---|---|
| 样式合同 ID | `HB-WARRANTY-SECTION`、`HB-TABLE-SYMBOL-SIGNAL` | [`manual_style.yaml`](manual_style.yaml) 声明稳定语义、theme-token role、token 与四端 capability/binding；本文解释可读对照；`HB-*` 通常不会原样写进正文 |
| 源结构标识 | RST 标题、``.. container:: warranty-section``、`\\HBSymbolTable` | 模板或生成器写入 prepared RST；标识必须与本地化文案无关 |
| IR 类型标识 | block `kind`，以及 `component` / `data` / `semantic` payload 里的 `kind`、`roles` | extractor 解析源结构后写入，供渲染器按类型路由 |
| 装配角色 | `PageRole.WARRANTY`、`PageRole.SYMBOLS` | [`page_roles.py`](../../../tools/idml/page_roles.py) 根据 manifest 中的 `source_ref` / 稳定文件名决定页面由哪个 composer 接管 |
| 输出标识 | Web `.hb-*` class、LaTeX `HB*` 宏、IDML paragraph/table/object style、Word style ID | 各 renderer 消费同一语义合同后生成；这是结果，不是源语义的判定依据 |

具体写入规则如下：

1. **原生结构直接类型化。** RST 一级标题、二级标题、列表和正文分别提取为 `h1`、`h2`、`list`、`body` block，再映射到 `heading_1`、`heading_2`、`list_item`、`paragraph` 等合同语义。
2. **需要跨段或组合结构时，模板加显式容器。** 例如：

   ```rst
   .. container:: warranty-section warranty-years

      Warranty Period
      ---------------

      .. list-table::
   ```

   [`semantic_containers.py`](../../../tools/idml/semantic_containers.py) 会把连字符规范成下划线，输出 `kind=warranty_section`、`roles=[warranty_section, warranty_years]`，并保留容器内的 typed blocks。后续 projector 生成 `warrantysection` / `warrantyyears` component，分别绑定 `HB-WARRANTY-SECTION` / `HB-WARRANTY-YEARS`。当前显式 semantic container 只支持质保语义；增加其他容器必须同时扩展 extractor、projector 和测试，不能只在模板里发明一个 class。
3. **生成型组件用稳定 HB 宏或 `manual-ir` payload。** 规格、Symbols、LCD、FCC、开箱和安全内容由模板生成 `\\HB...` 宏，或在 ``.. raw:: manual-ir`` 中携带带 `kind` 的 JSON。extractor 不保留排版命令本身，而是转成 renderer-neutral 的 `data` / `component` block，例如 `symbol_signals`、`lcd_icons`、`spec_section`、`safetywarning`。
4. **页面身份单独登记。** prepared bundle 的 manifest 决定 source 顺序和语言；稳定文件名 / `source_ref` 再映射为 `PageRole`。页面角色决定 physical composer，不能从页面标题翻译文本推断。批准装配中的 `UNCLASSIFIED_PROSE` 默认失败，只有精确登记的 source-ref 例外可放行。
5. **IR 再分配可追踪 ID。** [`manual_ir/builder.py`](../../../tools/manual_ir/builder.py) 按最终页面顺序生成 `page-0001-<stem>`，按块顺序生成 `:block-0001`，同时保存 `source_ref`、`kind`、`payload`、内容哈希和资产引用。这些 `page_id` / `block_id` 是实例身份；`HB-*` 是样式语义身份，两者不能相互替代。

因此，新增一个“流水线”语义不能只改 `manual_style.yaml`：必须同时有稳定源标识、extractor/IR 类型、renderer 路由、四端绑定和直接合同测试。未知 raw 块会计入 `skipped_raw`；production 要求其为 0。显式容器结构不合法时必须报错，不能静默退化成靠文案识别的普通段落。

### 0.6 ComponentSpec：共享语义，不共享 renderer 几何

当一个组合组件需要由 Web、PDF/LaTeX、IDML 和 Word 同时消费时，源 adapter 把已类型化
的 RST / Markdown / Manual IR 结构投影为 `component-spec/v1`：

```text
schema_version
component_id + variant
source_ref + language
slots[]  = role / content_kind / content
assets[] = role / asset_ref / locale_policy
token_roles[]
metadata
```

[`component_registry.yaml`](component_registry.yaml) 是实例结构与 adapter key 的机器注册表；
[`model.py`](../../../tools/component_specs/model.py) 和
[`registry.py`](../../../tools/component_specs/registry.py) 对未知 component、variant、slot、
asset role、renderer 或 adapter key fail-closed。可见标签仍由源提供，ComponentSpec 与
renderer 都不翻译、不补造文案。

四端只共享上述语义和资产角色：Web adapter 生成响应式 class，LaTeX adapter 选择宏，
IDML adapter 生成/恢复 notice payload，Word adapter 生成 Word-friendly 表结构。CSS
尺寸、TeX 宏体、IDML XML/ObjectStyle 和 DOCX 属性仍分别归各 renderer；不能把 InDesign
坐标或对象样式复制成 CSS。历史 callout notice 仍可在兼容窗口内通过已登记的 source
adapter 进入合同；FCC、Inbox、Overview 的 renderer-local facade 已关闭，IDML/LaTeX
必须从 ComponentSpec 的语义 slot 与 asset role 重建自己的 payload，不能再把旧 payload
藏进 `metadata` 原样往返。

首个 pilot 是 `HB-CALLOUT-STRIP`；第二个是 `HB-TABLE-SPEC`，用结构化
`section_title` / `rows` slot 验证了空标签 rowspan、多行值和圈号上标。后续组件
只有在自己的编号 PR 完成四端基线和 registry 测试后才进入该注册表；不能因为
代码里出现同名 class 就宣称已组件化。

### 0.7 可见文案来源：renderer 只投影，不补全

正文页所有面向读者的文字都必须能回溯到 prepared RST、源表、显式配置或 typed
Manual IR / ComponentSpec slot。这里的“可见”包括普通正文，也包括标题、表头、信号词、
按钮名、状态词、持续时间、图注、图片替代文字和占位说明。Web、LaTeX、IDML、Word
adapter 只能拆分、排序、选择样式和生成目标格式对象，不能根据 component kind、
page role、reference PDF、文件名或当前语言自行补出这些文字。

JE-1000F/US 批准版式中的物理第 1–3 页（封面、前言、目录）和封底是封闭的装配例外，
先保持既有 fallback：前言无语言码的首个 `IMPORTANT` 可按 EN 徽标装配，目录可从
collector 与 language pack 装配标题/语言条，封底可读取 region fallback 和批准合同中的
联系信息。例外只由这些 page role 的 composer 消费，不得被正文组件、普通 flow 或
其他页面复用；Key Combinations、Operation、Symbols、FCC、App 等正文组件仍严格执行
source-driven 门禁。

允许和禁止的边界如下：

| 情况 | 规则 |
|---|---|
| `Press and hold ... for 3 seconds` 显示成 `3s` | 允许；它是对源动作句的确定性紧凑投影。匹配不到时为空或失败，不能默认 `3s` |
| `On/Off`、`SOS`、Symbols 两列表头 | 必须来自 RST / `manual-ir` payload；renderer 不得按组件类型补值 |
| warning fence 没有 label | production fail-closed；不得用 fence 的 `warning` 自动生成 `WARNING` |
| 第 2 页 preface 的 `**IMPORTANT**` 没有语言码 | 批准特殊页例外：保持既有 EN 徽标装配；不得扩散到正文 |
| 图片只有资产路径、没有 alt | 保持空 alt 或要求上游补源字段；不得把文件名或 `figure` 当读者文案 |
| 未知 component 没有 `label` / `texts` | 不输出可见 fallback；不得显示内部 `kind`、JSON 或 `component` |
| 字体 fallback、样式名、StoryTitle、asset role、几何 token | renderer-owned 元数据/外观，不属于业务文案补全；字体 fallback 只能换字体 run，必须保留源 codepoint（如 `Nº` 的 `º`），不得改写文案 |
| 用真实标题字符串查批准测量值 | 只允许作为不改变文字的排版校准；不能把该查找表反向当作标题来源 |

IDML 在 [`source_copy.py`](../../../tools/idml/source_copy.py) 统一执行必填源文案检查；
批准 production 正文路径缺源时 fail-closed，兼容手递路径最多省略对应可见层。Symbols
续页通过带 `headers` 的 `SymbolOverflow` 继续传递源表头；数据页、Safety、FCC、
Operation 与 App 都从 Manual IR 的真实 payload 消费文案，不保留正文语言文案
registry。第 1–3 页和封底的 page-role scoped fallback 由上面的批准例外测试单独守护。
[`test_idml_visible_copy_sources.py`](../../../tests/test_idml_visible_copy_sources.py) 同时守护
行为和静态 literal sink；增加 IDML composer 或 adapter 时必须把新的可见字段纳入该
门禁。

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
| 通用表 | 无专属 ID | pipe 表 / `` ```{manual-table} `` | `.manual-table` | 走 `HB-TYPE-BODY` 排版 | `正文表格` | 表样式 `tableHeader`（单行且 ≥3 列时 `TableGrid`） | — |

IDML 的普通内容流采用三组可复用默认节奏：H2 上/下间距、普通图上/下间距、普通表上/下间距，分别由 `idml_title_l2_space_*`、`idml_figure_space_*`、`idml_data_table_space_*` 控制。当前 H2→图的组合净距为 5.67pt + 2.83pt，图→普通表为 4.25pt + 5.67pt。Operations、App、Charging、Product Overview、UPS、Troubleshooting 和 Specifications 等批准组件已有更具体 token 时覆盖这些默认值，不叠加逐页补丁。

生产 IDML 的普通 H2 圆点必须使用内联原生矢量圆和独立间隔对象，不能把
`●` 交给 Segoe UI Symbol、Yu Gothic 或其他平台字体。这样 Windows 与 macOS
打开同一自包含 IDML 时不会因缺字、替代字体或字面裁切而改变标题。圆点直径和
标题间距继续只消费 `comp_title_l2_bullet_radius` / `comp_title_l2_gap`；目标装配
不得通过标题文字、页码或型号分支替换这项共享语义。

App 原生故事的编号与列表使用显式悬挂/tab 合同，不再依赖圆点后的普通空格估算。H2 圆点留在版心起点，并由 `idml_app_h2_marker_font_size` / `idml_app_h2_marker_baseline_shift` 单独约束在首个 tab 内；H2 编号文本与 H3 的 `4.x` 编号共同落在 `idml_app_notes_left_indent`。列表圆点由 `idml_app_list_left_indent` 与该编号边对齐，首行正文和全部续行则共同落在 `bullet_left - idml_app_list_first_line_indent` 的固定 tab 位。英文、法文及任何结构化为 App list 的语言都复用这组属性，不按标题文字或页码追加坐标补丁。

UPS 与 Charging 共用一条可编辑内容流：三语各自的 `lang_*_idml_ups_caution_space_after` 控制 UPS CAUTION→CHARGING 标题，`idml_charging_emphasis_space_before` 控制 Charging 引言→黑色强调胶囊。当前强调胶囊前距为 5pt；三语 CAUTION 后距相对上一版等量减少 4pt，因此重分配节奏但保持页面总深度、后续 NOTE 位置和分页不变。`idml_charging_emphasis_horizontal_padding` 同时登记文字左侧光学缩进与总宽的双端 allowance：左侧由段落 `LeftIndent` 明确落位，使字面与 CHARGING 标题内容对齐；右侧不写 `RightIndent`，而由总宽余量自然保留。不能再叠加非对称 frame inset 或右段落缩进，否则会重复缩窄可用行宽并把结尾挤成溢流。文本框继续使用 `VerticalJustification=CenterAlign`；完整文案保持单行后，垂直居中不再被隐藏的第二行拉偏。该关系由组件 token 与估算高度共同维护，不允许在单页 XML 上追加坐标补丁。

IDML 可编辑表格的普通单元格统一由 `primitives.cell()` 输出 `VerticalJustification=CenterAlign`，模板合成阶段必须保留该语义属性，不允许因移除颜色、边线或 inset 覆盖而一并丢失。Troubleshooting 的 F6/F7 等多步骤行还要求左右格使用对称的上下内边距，正文格与错误码格都不得再叠加逐语言、逐行的 `BaselineShift`；否则虽然 XML 声明居中，视觉位置仍会被二次位移。LCD、Symbols 和通用图片表的图标段落另显式输出 `Justification=CenterAlign`，因此图标在格内同时横向、纵向居中。Symbols 信号词徽标分成两层基线合同：`idml_symbols_signal_badge_baseline_shift` 只校正整块深色徽标在表格行内的位置，`idml_symbols_signal_content_baseline_shift` 则统一校正徽标内部图标与文字的可见字面；两者不能用一次递归 `BaselineShift` 覆盖。圆角 WARNING/callout 不依赖表格默认值：标签框、正文框和黑框正文使用同一 `TextFramePreference.VerticalJustification=CenterAlign` 合同。

Troubleshooting 的短表和完整表共用 `HB-TABLE-TROUBLESHOOTING`，但行高预算
必须由真实行数和本地化换行计算：只有完整 12 行 profile 才消费其冻结 ordinal
minima；紧凑表使用 `idml_trouble_extra_row_min_height` 和
`idml_trouble_compact_outer_radius`。错误码列宽同时测量表头与全部代码，右侧表头
保持纸白，首列按合同使用灰底；源 RST 的 line-block 分隔符只能表达换行，不能以
字面量 `|` 进入单元格。故障段落和表格默认关闭断词，避免在错误码和措施文字中
产生源稿没有的词内断行。

### 专题版块

| 语义 | 语义 ID | 源写法 | Web | PDF | IDML | Word | 状态 |
|---|---|---|---|---|---|---|---|
| FCC 面板 | `HB-SPECIAL-FCC` | 流水线 | `.hb-fcc-composition` | `HBFccBlock` @ `components_special_pages` | `HB Rounded Panel` + `无表头表格` | `.hb-fcc-word-table` 双栏活文本 | **aligned** |
| 开箱清单卡 | `HB-SPECIAL-INBOX` | 流水线 | `.hb-inbox-composition` | `HBInBoxThree` | `Item List Text` + `HB Inbox Card` + `无表头表格` | `.hb-inbox-word-table` 活图文卡 | **aligned** |
| 产品概览 | `HB-SPECIAL-OVERVIEW` | 流水线 | `.hb-annotated-figure` | `HBOverviewPanel` | `HB Body`（可移动文本框） | 经 HTML 转换 | **aligned** |
| App 设置 | `HB-SPECIAL-APP` | 流水线 | `.hb-app-download-composition`、`.hb-app-add-device-composition` | `HBAppStep`、`HBAppAsset`、`HBAppNotice` | `HB Body` / `HB Callout Label` / `HB Callout Body` + `HB Rounded Panel` | 经 HTML 转换 | **aligned** |

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

IDML 普通行由 `idml_spec_table_row_height` 控制；多行单元格使用 `comp_spec_table_multiline_min_height`，并输出 `MinimumHeight` / `AutoGrow`，不再由本地常量决定。分节标题的圆点与文字共享同一组件基线合同：`idml_spec_section_text_baseline_shift`（及语言覆盖）确定标题基线，`idml_spec_section_bullet_baseline_offset` 只表达圆点相对文字的光学校正；`idml_spec_section_left_indent` 统一让圆点左边缘与随后表格的外框共线。所有分节和语言复用这些值，不逐标题写死位置。表格单元格里的圈号是引用标记，保持小号上标；页底脚注行首的同一圈号是注释编号，必须继承 `HB Spec Note` 的正常字号与基线。注册商标 `®` 保留字体自身的上标字形，不套用圈号引用规则。

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
`:headers: A | B` 提供两个本地化表头（见 [附录 B](#附录-b-已知边界)）。IDML 关闭自动缩放；批准语言的行 minima、表头/正文高度修正、内外线宽、面板下限、导入安全余量和 portable glyph-width 估算全部由 `idml_trouble_*` / `lang_*_idml_trouble_*` token 控制。

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

IDML 的 subbar 高度、标题/维护区间距、H1 光学偏移、页面下限和非批准语言 fallback 估算均来自 `manual_style.yaml` 登记的 token；两类 Symbols 表均为 `aligned`。批准语言的图标表保留原有固定行高，外层框在行高总和之外统一增加 `idml_symbols_table_frame_allowance`（当前 `0.25pt`）作为 InDesign 表格承载余量；它只吸收导入后的表格标记，不缩字、不改分栏，也不允许最终化脚本隐藏 overset。

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

IDML App 下载构图以左右两个活文本栏的中心分别对齐商店徽章和 QR，不以整页中心或固定左边缘对齐；控制面板的三条原生延长线统一消费 `idml_app_control_leader_extension_weight`，与链接底图中的引线保持同一视觉线宽。

FCC 的单一语义实例是 `HB-SPECIAL-FCC` ComponentSpec：它保存无障碍标签、开场文案、按源顺序排列的段落/列表、逻辑分栏点和 `compliance_mark` 资产角色；资产实例只引用注册表语义键 `mark/fcc`，各 renderer adapter 再解析自己的 PDF/PNG 路径。Web、LaTeX、IDML、Word 分别消费自己的适配器；两栏宽度、固定页坐标、DOCX 表格属性和 CSS 断点不进入 ComponentSpec。Web 只渲染审批过的浅灰 FCC 外框，导航里的 `FCC` H1 保留给目录和无障碍技术但视觉隐藏，不合成黑色标题条；外框继续服从 §8.1 的通栏等宽契约。源 payload 先类型化为 ComponentSpec；IDML/LaTeX 再从语义 block 重建自己的结构，不保留或回放旧双文本 payload。

开箱清单的单一语义实例是 `HB-SPECIAL-INBOX` ComponentSpec：它固定保存三张有序卡，每张卡包含序号、独立 `card_N_art` 资产角色、可访问 alt 和可编辑本地化 label，并把相邻 TIP 的 label/body 纳入同一实例。Web adapter 输出等宽三卡和响应式 tip；LaTeX adapter 继续投影 `HBInBoxThree` 六个实参；IDML adapter 保留批准的绝对坐标卡片 composer；Word adapter 输出三列活图片/活文本表格和 16/84 tip 表。卡片宽度、图高、断点、IDML 坐标和 DOCX 单元格属性属于各自 adapter，不进入 ComponentSpec。source projector 必须显式提供源 H1、严格三卡以及相邻 TIP label/body；缺任一项即失败，不再保留 partial-list 或页面形状 fallback。

产品概览的单一语义实例是 `HB-SPECIAL-OVERVIEW` ComponentSpec：它保存 H1 无障碍标签、`front` / `right` 两个有序视图、`front_art` / `right_art` 资产角色，以及 15 个稳定 callout 的 ID、可编辑 label/body 和源引用。JE-1000F/US 的百分比 Web 坐标、固定页 IDML 坐标、16 条引线顺序、composite locale/source mapping 与 `web_replace_key` 统一登记在版本化 [`overview_component_instances.json`](overview_component_instances.json)，不进入语义实例。Web adapter 支持 `annotated-live` 和 `approved-composite`：批准图匹配时显示完整图文资产，无匹配时保留完整可搜索 HTML/SVG fallback；LaTeX、IDML、Word 分别消费自己的 projection。生产投影必须解析一个版本化 `instance_id`；旧 target-local 默认实例已删除，缺失或未知实例会失败。

`web_manual.json` 里登记的目标（当前 `JE-1000F / US`）会把其中部分图替换为审批过的 PDF 派生图，标题与说明仍保持可搜索的活 HTML。

---

## 6. 质保

| 语义 | Web | 要点 |
|---|---|---|
| 引语 | `.hb-warranty-intro-composition` | |
| 条款面板 | `.hb-warranty-card` | 圆角面板，卡内首个 `h2` 有专门覆盖（不走 §2.3 的圆点条） |
| 年限卡 | `.hb-warranty-period-card` > `.hb-warranty-period-grid` | 大号数字 + 单位 + 副标题；IDML 用 `HB Big Numeral` |

token 以 `comp_warranty_*`、`type_warranty_*` 为前缀；语言相关的面板高度微调走 `lang_<xx>_idml_warranty_*`。IDML 年限副标题通过 `idml_warranty_year_subtitle_left_indent` 与单位文字做光学左对齐，年限列内部统一顶对齐。共享 Warranty 模板通过 `container` 明确标记 `warranty_lead`、`warranty_section`、`warranty_years`，覆盖 en/fr/es/de/it/uk/ko/pt-BR。IDML 直接读取这些语义，不依赖标题措辞或年限文本形状；坏的 years 结构 fail-closed。冻结 review derivative 仍兼容旧启发式，避免历史批准稿失效。

---

## 7. 页面模板

`tools/page_plan/` 是四端共享的页面语义层。它只记录 source ref、语言、
source ordinal、physical start/span、page role、footer/folio policy 与各 renderer
capability；不携带 TeX 尺寸、IDML XML/ObjectsStyle 几何、DOCX XML 或 CSS 坐标。
LaTeX、IDML 和 Word 各自通过 adapter 投影这些角色；Web 明确记录
`pagination=not-applicable`，不伪造 PDF 式分页。

JE-1000F/US 批准合同仍为 52 个 source page / 58 个 physical page，顺序、
语言和 composition map 均由 reference-layout pin 约束。封面保留“置入已批准成品美术”
constraint；封底仍是 source-driven 可编辑文案。IDML folio 不再通过本地化
标题、story ID 或 spread XML 推断，而是仅读 PagePlan 的角色与 policy。

| 语义 | PDF | IDML | 说明 |
|---|---|---|---|
| 标准页 | `HBPageTemplateStandard` | `HB Standard Page` | 带页脚；token 为 `page_paperwidth/height`、四边 `page_margin_*`、`page_footskip` |
| 无页脚页 | `HBPageTemplateNoFooter` | `HB No Footer Page` | 同上去掉 `page_footskip` |
| 封面 / 封底 | `HBPageTemplateCover`、`HBBackCoverPage` | `HB Cover Page` | 封面是置入的成品美术；封底几何为 InDesign 原生，文案来自共享 IR |

Web 投影没有页的概念，这三条不参与。

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
- `tools/word_bundle_docx_styles.py` 只做样式归一，不按英文标题匹配语义。

Word 若需要新增独立组件样式，应先进入 `manual_style.yaml` 的 `word` binding 与 §1
的语义对照，不能只在 DOCX remapper 中增加一次性规则。

---

## 9. 合同生效与批准版式

`aligned` 表示各输出面按已登记的同一语义工作，并不要求响应式 Web、固定页
PDF/IDML 和 Word 逐像素相同。`partial` 只表示仍有 §0.3 定义的可修复 debt；
constraint 或 approved variant 不会单独把语义降为 `partial`。**当前状态只读
`manual_style.yaml` 的 `conformance.state` / `conformance.debt`；不要在本文再维护
一份计数或清单。** §1 的状态列用于阅读，修改合同状态时必须在同一提交同步它。

允许的投影差异必须满足至少一项：写进 token、写进 renderer binding、或写进批准
reference-layout 的边界说明，并按 §0.3 登记为 constraint 或 approved variant。
未登记的 renderer-local 可见常量不是“平台差异”，而是 debt。

`manual_style.yaml` 与 `data/layout_params.csv` 的语义哈希会写入批准 reference-layout plan 的 v2 `identity.style`。v2 把 identity 分为 `content`、`assembly`、`style`、`provenance`：前三者和逐页 source digest 是 production 硬门禁；全局 phase2 `snapshot_sha256` 只保留在 `provenance` 供追溯，不因无关表变化阻断当前 target。`assembly` 同时哈希 source 顺序、语言、页面角色和 composition map；批准装配出现 `UNCLASSIFIED_PROSE` 时默认失败，只有精确登记的 source-ref 例外可继续。对已有批准合同的 target，production `build.py idml --source auto` 与 Print Publish 的所有输出都解析为冻结 `review-asis` 装配；强制刷新 phase2 只更新发布归档和资产解析，不得在 Publish 阶段改写被 content/page digest 批准的正文。未批准 target 继续走 runtime 或历史 `review` 同步。普通 reference rebind 只允许 style/provenance identity 更新，默认拒绝 content 或 assembly hash 变化。只有在最终 Manual IR 的 source 顺序、语言映射、物理页数、`skipped_raw` 与 composition map 均通过核验后，才可由操作者使用显式 content-approval 路由重绑；reference PDF 与 composition map 不因样式销账而改变。

某个 target 的 source 数、物理页数、hash、批准 metadata 和测试结果应记录在其
reference-layout plan 或[执行状态](../../../code-as-doc/dev/style_debt_execution_status.md)，
不写进本文。这样规范不会因为一次发布或重新批准而过期。

---

## 10. 逐层实例：原始 RST 怎么变成 Web 版面

本节服务一个具体动作：**批量把存量文档转成当前构建物的 Web 样式**。示例全部取自真实源文件（共享模板与 JE-1000F / US 的冻结 review 派生物 [`docs/_review/JE-1000F/US/page/`](../../_review/JE-1000F/US/page/)），每个语义按「原始 RST → 中间态 → 最终 Web 标记」给出，末尾给出批量转换时的 md 等价写法。版面数值不在这里重复，见 §2–§7 各条。

### 10.1 两条到达同一版面的链路

生产 Web 构建物走四层：

```text
(1) 装配   phase2 源表 + docs/templates/*.rst
           占位符（|PRODUCT_NAME|）与 {{ … }} 槽位替换、语言/区域 only 分支定型
           → prepared RST bundle：docs/_build/<model>/<region>/rst/page/*.rst
             （冻结样例：docs/_review/JE-1000F/US/page/）

(2) 出片   docutils 逐页渲染 HTML fragment（tools/word_bundle_html.py），
           同时做结构归一（tools/word_bundle_html_rewrite.py）：
           无表头、单行两列、首格是登记信号词的 list-table
           → table.manual-callout-table 等

(3) 升级   Web 档案（AUTO_MANUAL_PRESENTATION_PROFILE=web → tools/web_presentation.py）
           按 web_manual.json 的 source_patterns 认页（按页名 pattern，如
           spec_* / troubleshooting_* / *11_warranty，不猜内容），
           把 docutils 结构升级为 figure.hb-*-composition 骨架；
           结构不满足契约 → WebPresentationError，fail-closed

(4) 成站   pandoc 导出 MyST md（figure / callout 先换 token 保护、再原样恢复）
           → furo Sphinx 站点 + web_manual.css = 最终版面
```

两点边界：figure 升级只对 [`web_manual.json`](web_manual.json) `figure_targets` 里登记的 `(model, region)`（当前 JE-1000F / US）生效，未登记目标保持 docutils 原样结构、只有基础排版；Web publish 的入口就是 `AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md …`（见 [`user-guide/hello_auto-doc.md`](../../../user-guide/hello_auto-doc.md)）。

存量转换链（本分支）只有两层：

```text
存量 Markdown → tools/plain_markdown_site.py 转成中间 md（```{callout} 等围栏指令）
             → tools/manual_md_directives.py 的指令 run() 直接产出合同标记
             → 同一份 web_manual.css = 同一版面
```

**两条链的汇合点是「合同标记 + `web_manual.css`」。** 生产链靠"识别 RST 结构再升级"，存量链靠"指令直接产出"，落到页面上是同一套顶层 class。所以批量复刻**不需要**复刻 RST 那几层——RST 层的价值是看懂哪个源结构对应哪块版面、以及哪些版面只有流水线数据才长得出来；真正转换时写 md 指令即可。

### 10.2 逐语义速查

| 版面 | 原始 RST 源结构（生产链） | Web 挂点 | 批量转换写法 |
|---|---|---|---|
| H1 胶囊 | 页标题 `=====` 下划线；生成页直接 raw `<h1 class="hb-h1-pill">` | `h1` | `# 标题` |
| H2 圆点条 | 小节 `-----` 下划线 | `h2` | `## 标题` |
| 警示框 | 单行两列 `list-table :widths: 12 88`，首格 `**CAUTION**` | `table.manual-callout-table` | `` ```{callout} CAUTION `` |
| 竖式规格表 | 生成器写 raw `<table class="hb-spec-table">` | `figure.hb-spec-table-composition` | `` ```{spec-table} 分节名 `` |
| 故障排查表 | `list-table :widths: 14 86` + 表头行，行来自源表 | `figure.hb-troubleshooting-composition` | `` ```{troubleshooting} `` |
| LCD 图标表 | 四列 `list-table :widths: 8 12 28 52`，第 2 列是图 | `figure.hb-lcd-table-composition` | `` ```{lcd-icons} `` |
| 符号图标表 | 四列 `list-table :widths: 12 38 12 38`，左右两对 | `figure.hb-symbol-pair-composition` | `` ```{symbols} `` |
| 信号词表 | `list-table :widths: 22 78` + raw 徽标 span | `figure.hb-symbol-signal-composition` | 流水线专属，无 md 写法 |
| 对比表 | 操作页内两列带表头 `list-table`（条件列向上合并） | `figure.hb-auto-resume-composition` | `` ```{comparison} 左表头 \| 右表头 `` |
| 质保三件套 | `.. container:: warranty-*` + 50/50 `list-table` | `.hb-warranty-*` | 流水线专属，无 md 写法 |
| 开箱清单 | 三列 `list-table :widths: 33 33 34`（图 + 名） | `figure.hb-inbox-composition` | 流水线专属，无 md 写法 |
| 通用表 | 普通 `list-table` / grid 表 | `table.manual-table` | pipe 表 / `` ```{manual-table} `` |

下面逐条展开。每条的三层分别是：**L1 原始 RST**（占位符已合并的 prepared 形态）、**L2 中间态**（docutils 出什么、谁在哪一步识别）、**L3 最终 Web 标记**（`web_manual.css` 消费的骨架）。

### 10.3 标题与正文（`HB-TITLE-*`、`HB-TYPE-BODY/LIST`）

**L1 原始 RST**（[`troubleshooting_en.rst`](../../_review/JE-1000F/US/page/troubleshooting_en.rst)、[`08_charging_methods.rst`](../../templates/page_shared/en/08_charging_methods.rst)）：

```rst
TROUBLESHOOTING
===============

If any of the following fault codes appear, follow the listed corrective actions...

CHARGING VIA SOLAR PANELS (SOLD SEPARATELY)
-------------------------------------------

- 列表项一
- 列表项二
```

**L2** docutils 原生类型化：页标题 → `<h1>`、`-----` 小节 → `<h2>`、`~~~~~` → `<h3>`、段落 → `<p>`、列表 → `<ul>/<ol>`，不需要任何识别步骤。生成页（规格页）跳过 RST 标题、直接 raw 写 `<h1 class="hb-h1-pill">`，两种来源到 L3 等价。

**L3** CSS 直接挂在裸标签上（`#furo-main-content h1/h2/h3/p/ul`），版面规则见 §2.2–§2.4。**md 等价**：`# ` / `## ` / `### ` 与原生段落列表；H1 的大写由 CSS `uppercase` 完成，源里不必写大写。

### 10.4 警示框（`HB-CALLOUT-STRIP`）

**L1 原始 RST**（[`08_charging_methods.rst`](../../templates/page_shared/en/08_charging_methods.rst)，一框一表，正文格可带子列表）：

```rst
.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **CAUTION**
     - Ensure that the input voltage for both DC input ports is the same...

       - Use the same model of Jackery solar panels...
       - Do not charge the product using both a car charger and a solar panel...
```

**L2** 归一发生在链路第 (2) 层（[`word_bundle_html_rewrite.py`](../../../tools/word_bundle_html_rewrite.py)）：判定条件是**无表头 + 恰好一行 + 恰好两格 + 首格文本是 [`signal_words.py`](../../../tools/signal_words.py) 登记的信号词**，四项都满足才归一；差一项就按通用表处理。类型化入口随后生成同一个 `HB-CALLOUT-STRIP` ComponentSpec；五种 variant 是 `warning`、`danger`、`caution`、`note`、`tip`，标签、正文、列表、语言和 source ref 保持为实例数据。Web、LaTeX、IDML、Word 各自通过注册的 adapter 消费它，不再各自维护一份 variant 映射。

**L3 最终 Web 标记**：

```html
<table class="manual-callout-table"><tbody><tr>
  <td class="manual-callout-label"><p><strong>CAUTION</strong></p></td>
  <td class="manual-callout-body">…完整正文，可含列表…</td>
</tr></tbody></table>
```

版面规则见 §3.1。**md 等价**：`` ```{callout} CAUTION ``，正文按完整 Markdown 解析（[`manual_md_directives.py`](../../../tools/manual_md_directives.py) 先校验 ComponentSpec，再由 Web adapter 产出上面这段标记）。Pandoc 前后由 [`web_presentation.py`](../../../tools/web_presentation.py) 保护并原样恢复整张表；恢复前后会重新校验同一 component ID、variant 和 slot 内容，不能靠 Pandoc 重建一个近似表格。

### 10.5 竖式规格表（`HB-TABLE-SPEC`）

规格页整页由生成器产出，prepared RST 里已是 `.. only::` 双分支的 raw（LaTeX 分支走 `\specsectiontitle` + `spectable` 环境）。

**L1 原始 RST**（[`spec_en.rst`](../../_review/JE-1000F/US/page/spec_en.rst) 的 HTML 分支）：

```rst
.. only:: html

   .. raw:: html

      <h1 class="hb-h1-pill">SPECIFICATIONS</h1>

   .. raw:: html

      <h2 class="hb-spec-section">…GENERAL INFO…</h2>
      <table class="hb-spec-table">
        <tbody>
          <tr>
            <th scope="row" class="hb-spec-label">Product Name</th>
            <td class="hb-spec-value">Jackery Explorer 1000</td>
          </tr>
          …
```

**L2** 源 adapter 先把每个分节投影为 `HB-TABLE-SPEC` ComponentSpec：
`section_title` 保留本地化标题，`rows` 按 label group 记录 `label_rowspan`、值列表和
圈号 reference。CSV/RST、MyST、IDML 和 Word 的旧入口是薄 facade，先经同一结构校验，
再交给各自 adapter；多行值在 Web 中仍可是一个 `<br>` 单元格，Word 可投影为带
rowspan 的多个物理行，因为物理标记不是共享合同。

网页链路第 (3) 层按页名 `spec_*` 认页，把每张 `hb-spec-table` 包进
`figure.hb-spec-table-composition` 外壳，并校验分节数与 ① 圈号脚注数
（`web_manual.json` 的 `specifications.section_count` / `circled_reference_count`）——
数不对整页报错。包装后还会从最终 DOM 反向校验一次 ComponentSpec，确保 Pandoc
保护/恢复的是同一张结构表，不是近似的通用表。

**L3**：`figure.hb-spec-table-composition > table.hb-spec-table`（外壳负责深色外框、圆角、横向滚动；内表只管格线），版面规则见 §4.2。**md 等价**：

````markdown
```{spec-table} GENERAL INFO
Product Name | Jackery Explorer 1000
Model No.    | JE-1000F /JE-1000F-SG
             | 标签留空 = 并入上一标签（rowspan）
```
````

### 10.6 故障排查表（`HB-TABLE-TROUBLESHOOTING`）

**L1 原始 RST**（[`troubleshooting_en.rst`](../../_review/JE-1000F/US/page/troubleshooting_en.rst)；模板只有表头，行由源表经 `{{ troubleshooting_rows_rst }}` 灌入）：

```rst
.. list-table::
   :class: longtable
   :header-rows: 1
   :widths: 14 86

   * - Error Code
     - Corrective Measures
   * - F0
     - Restart the product.
   * - F4
     - Connect the product to loads to discharge its battery until the fault disappears.
```

**L2** 第 (3) 层按页名 `troubleshooting_*` 认页，要求**恰好一张**「1 表头行 + 错误码序列 F0…FE」的两列表；找到后注入 `colgroup`（`hb-troubleshooting-col-code/measures`）、给格子打 `hb-troubleshooting-code/measures` class，再包 `figure` 外壳。

**L3**：`figure.hb-troubleshooting-composition > table.hb-troubleshooting-table`，版面规则见 §4.3。**md 等价**：`` ```{troubleshooting} ``，行写 `F4 | 措施一 / 措施二`（` / ` 自动拆成分步行）；需要本地化表头时写 `:headers: Code | Corrective measures`，必须恰好两个非空格子。

### 10.7 LCD 图标表（`HB-TABLE-LCD-ICON`）

**L1 原始 RST**（[`lcd_icons_en.rst`](../../_review/JE-1000F/US/page/lcd_icons_en.rst)；行含序号、源表附件图、名称、多步说明）：

```rst
.. only:: not latex

   .. list-table::
      :class: longtable
      :header-rows: 0
      :widths: 8 12 28 52

      * - 1
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/1_Wi-Fi_….png
             :alt: Wi-Fi
             :width: 42px
        - Wi-Fi
        - | **On:** Wi-Fi connected.
          | **Blink:** Ready to connect to Wi-Fi.
          | **Off:** Wi-Fi disconnected.
```

**L2** 第 (3) 层按页名 `lcd_icons_*` 认页，要求**全页恰好一张四列表**、每行第 2 格必须有 `img`；命中后注入 `colgroup`（`hb-lcd-col-number/icon/name/description`）、逐格打 class、图片清掉宽高改由 CSS 管，再包 `figure`。

**L3**：`figure.hb-lcd-table-composition > table.hb-lcd-icon-table`，版面规则见 §4.4。**md 等价**：`` ```{lcd-icons} ``，行写 `1 | 图.png | Wi-Fi | On: … / Blink: …`（图片格只认第 2 列）。

### 10.8 符号页两表（`HB-TABLE-SYMBOL-SIGNAL` / `-ICON`）

**L1 原始 RST**（[`symbols_en.rst`](../../_review/JE-1000F/US/page/symbols_en.rst)；同一页两张表）——信号词表是 22/78 两列，徽标是流水线生成的 raw span：

```rst
.. list-table::
   :class: longtable
   :header-rows: 1
   :widths: 22 78

   * - Symbol
     - Meaning
   * - .. raw:: html

          <span class="hb-warning-lockup" …>⚠ WARNING</span>
     - Hazardous practices that may result in severe injury, death...
```

图标表是 12/38/12/38 四列（左右各一对「图 + 释义」）：

```rst
.. list-table::
   :header-rows: 0
   :widths: 12 38 12 38

   * - .. image:: …/symbols/1_warning_triangle_….png
     - Warning and Caution Symbols. Alerts individuals to...
     - .. image:: …/symbols/7_do_not_dismantle_….png
     - Do not dismantle the product.
```

**L2** 第 (3) 层按页名 `symbols_*` 认页：信号词表按登记行数校验后升级为 `.hb-symbol-signal-composition`；四列表拆成左右两块独立面板。

**L3**：`figure.hb-symbol-signal-composition` 与 `figure.hb-symbol-pair-composition`（双面板 grid，行高互不影响），版面规则见 §4.6。**md 等价**：图标表用 `` ```{symbols} ``（每行四格）；信号词表流水线专属，存量转换时用 `` ```{callout} `` 或通用表近似，无同款徽标。

### 10.9 质保三件套（`HB-WARRANTY-LEAD` / `-SECTION` / `-YEARS`）

**L1 原始 RST**（[`11_warranty.rst`](../../templates/page_shared/en/11_warranty.rst)；语义靠**显式 container**，与标题措辞无关——§0.2 的第 2 条写入规则就是这里）：

```rst
.. container:: warranty-lead

   **This warranty applies only to customers who purchase from...**

.. container:: warranty-section warranty-years

   Warranty Period
   ---------------

   .. list-table::
      :header-rows: 0
      :widths: 50 50

      * - **3 YEARS**

          **Standard Warranty**

          The standard warranty period for |PRODUCT_NAME| is 36 months...

        - **2 YEARS**

          **Extended Warranty**
          ...
```

**L2** docutils 把 container 渲染成 `<div class="warranty-section …">`；第 (3) 层按页名 `*11_warranty` 认页，按登记的 `section_count` / `period_years` 校验后重组。

**L3**：引语 → `.hb-warranty-intro-composition`，条款 → `.hb-warranty-card`，年限 → `.hb-warranty-period-card > .hb-warranty-period-grid`（大数字徽章 + 单位 + 副本），版面规则见 §6。**md 无等价写法**：年限卡的「3 YEARS / 2 YEARS」拆解依赖登记结构，存量转换遇到质保页保持普通标题 + 段落即可。

### 10.10 开箱清单卡（`HB-SPECIAL-INBOX`）

**L1 原始 RST**（[`02_whats_in_the_box.rst`](../../_review/JE-1000F/US/page/02_whats_in_the_box.rst)；区域分支 + 三列图文表 + TIP 框）：

```rst
.. only:: not latex and region_us

   .. raw:: html

      <h1>WHAT'S IN THE BOX</h1>

   .. list-table::
      :header-rows: 0
      :widths: 33 33 34

      * - .. image:: asset:in_the_box/main_unit1
             :width: 120px

          **Jackery Explorer 1000**
        - .. image:: asset:in_the_box/ac_charging_cable
             :width: 120px

          **AC Charging Cable**
        - …
```

**L2/L3** source projector 把 H1、三列图文表和紧随其后的 TIP 表组合为一个 `HB-SPECIAL-INBOX` ComponentSpec；Web adapter 再输出 `.hb-inbox-composition > .hb-inbox-grid`：三张等宽圆角卡 + 1/2/3 角标 + 通栏 TIP 条（版面见 §5）。projector 以显式 H1、三卡和 TIP 合同 fail-closed，不再从不完整列表或页面邻接形状补造实例。**md 无等价写法**（角标与卡片组版是流水线重组的产物）。

### 10.11 例外：模板自带双分支的页（安全页、FCC）

安全页不走「识别升级」：模板里 LaTeX 与 HTML 两个分支**并排手写**，Web 标记在源里就是成品（[`safety_en.rst`](../../templates/page_us-en/safety_en.rst)）：

```rst
.. only:: latex

   .. raw:: latex

      \HBSafetyInstruction{INSTRUCTIONS PERTAINING TO RISK OF FIRE, ...}
      \HBWarningLeadBlock{WARNING}{Always follow these basic precautions...}

.. only:: html

   .. raw:: html

      <div class="hb-safety">
        <h1 class="hb-h1-pill">IMPORTANT SAFETY INFORMATION</h1>
        <div class="hb-warning-box">…</div>
        <div class="hb-two-col">
          <p class="hb-lead">Always follow these basic precautions...</p>
          <ul class="hb-list">…</ul>
        </div>
      </div>
```

改这类页 = 同时改两个分支；只改一个分支就是 Web/印刷分叉。批量转换存量文档遇到安全类内容时，用 `` ```{callout} WARNING `` 承载文案即可，不要手抄 `hb-safety` 结构（那是 §3.2 的流水线专属语义）。

---

## 附录 A 组件与维护流程

### A.1 一个组件由什么构成

| 层 | 内容 | 落在哪 |
|---|---|---|
| 语义 | 语义 ID、`semantic_source_kinds`、`theme_token_roles`、token refs、四端 capability/binding、`conformance` / `constraints` / `approved_variants` | [`manual_style.yaml`](manual_style.yaml) |
| 主题角色 | 组件 token role 消费的 surface / border / radius / type / width 角色及四端 binding | [`manual_theme.yaml`](manual_theme.yaml) |
| 源写法 | MyST 围栏指令，或 RST 模板 / 源表字段 | [`tools/manual_md_directives.py`](../../../tools/manual_md_directives.py)、`docs/templates/` |
| 标记 | `figure.hb-*-composition` 外壳 + 表格/网格骨架 + 每列一个 `col.hb-*-col-*` | 指令的 `run()` 或流水线渲染器 |
| 样式 | 顶层 class 上的规则；分列宽度写在 `col` class 上 | [`web_manual.css`](web_manual.css) 及两个分模块 |
| 印刷 | LaTeX 入口宏 + IDML 渲染器 | `docs/renderers/latex/`、`tools/idml/` |

外壳与骨架分离是硬约定：**外壳负责外框、圆角、横向滚动、外宽契约；内表只负责格线与排字**。规格表、故障排查表、对比表、LCD 模式表都遵循这一层划分，所以窄屏时是外壳滚动而不是表格压字。

### A.2 围栏指令的构造契约

八个指令共用基类 `_ManualDirective`（`has_content`、一个可选参数、默认不接受任意 option）：

| 环节 | 约定 |
|---|---|
| 参数 | `self.label`。多数指令 → `aria-label`；`comparison` 拆成两个表头；`lcd-mode` 当作图片 |
| 行解析 | `rows()`：按未转义的 `|` 分列并 `strip`，奇数个连续反斜杠转义紧随其后的竖线（`\|` → 字面 `|`），偶数个反斜杠保留一半并仍把竖线作为分隔符；**空行直接丢弃** |
| 类型化 option | `callout` 只接受 `:variant:`，值限 `warning` / `danger` / `caution` / `note` / `tip`；`troubleshooting` 接受恰好两个非空格子的 `:headers:`；`manual-table` 接受 `:headers:`。其它 option、任意 `:class:` 和未知 variant 均 fail-closed |
| 行内子集 | `_inline_html()`：转义 `& < > "` 后只还原 `**粗体**`、`^上标^`、`~下标~`。`callout` 例外，走 `nested_parse` 完整 Markdown |
| 图片格 | `_image_html()`：只在 `lcd-icons` 第 2 列、`symbols` 第 1 列、`lcd-mode` 参数位 |
| 多步文本 | `_line_block()`：` / ` 分隔 → `.line-block` > `.line`；少于两段退化为 `<p>` |
| 合并语义 | `_merged_row()`：空格子并入上方（每列独立）。`spec-table` 用自己的实现，**只看第一列** |
| 输出 | `nodes.raw(format="html")`，即样式契约要的确切标记 |

### A.3 新增一个组件

1. **定义稳定语义。** 在 `manual_style.yaml` 加 `role`、
   `semantic_source_kinds`、`theme_token_roles`、token refs、四端 capability/binding，
   并诚实填写 `conformance`、`constraints` 和 `approved_variants`。先有语义，再有
   渲染器。
2. **提供稳定源结构。** 在模板、生成器或源表 schema 中加与本地化文案无关的
   标识；同步扩展 extractor、Manual IR 类型与 projector。不能从英文标题反推。
3. **实现四端投影。** Web 加顶层 composition/class，LaTeX 加稳定公共宏，IDML
   加可编辑组件/样式，Word 加结构归一规则。通栏 Web 组件加入 §8.1 的共享外宽
   selector。
4. **只在需要时提供 Markdown 指令。** 面向存量 Markdown 时，在
   [`manual_md_directives.py`](../../../tools/manual_md_directives.py) 实现指令并注册；
   启发式 detector 只生成可审阅中间态，不直接决定 production 语义。
5. **补机器合同和本文。** 每端至少一个直接测试；§1 增加唯一对照行，相关视觉章节
   写清不变量、响应式/固定页差异和 source → output 示例。
6. **验证批准目标。** token 或合同变化要检查 reference pin；若 content/assembly
   发生变化，必须走显式批准，不能把 style rebind 当内容批准。

样式模块的规模边界由
[`tools/check_maintainability_guardrails.py`](../../../tools/check_maintainability_guardrails.py)
看守。不要在本文复制阈值数字；阈值属于代码门禁，调整时要解释模块为什么不能继续
拆分，而不是只把上限调大。

### A.4 改样式的顺序

1. 在 `manual_style.yaml` 找语义 ID，确认 `semantic_source_kinds`、四端 binding、
   token 和当前 `conformance.debt` / 边界记录。
2. 在 §1 和所属视觉章节确认四端投影；判断本次是共享值变化，还是有理由的
   renderer-specific 投影。
3. 先改权威源：数值进 `layout_params.csv`，Web 响应式值进 CSS，结构语义进
   模板/extractor/IR。不要先改生成的 `params.tex` 或输出 HTML/IDML。
4. 更新所有受影响 renderer 和直接测试；新增差异必须登记，不能靠注释解释本地常量。
5. 更新本文，保证 §1、视觉定义、示例和维护规则不互相矛盾。
6. 按影响面验证；生成副作用只提交应提交的源文件。

最低验证矩阵：

| 影响面 | 至少运行 |
|---|---|
| 本文、导航或链接 | `python tools/check_doc_link_integrity.py` |
| `manual_style.yaml` / renderer 合同 | render-contract 定向测试 + `python -m unittest` |
| Python renderer / tests | Ruff + `python -m unittest` + maintainability guardrails |
| `layout_params.csv` | `python tools/csv_to_tex_params.py`，再审计 `params.tex` 差异 |
| Web 样式 | plain-Markdown 组件测试 + 一个真实 Web build |
| PDF/IDML 共享样式 | US check/build + reference pin；视觉变化另做真实 PDF/IDML 比对 |

规格表的 Web / PDF / IDML / Word 列宽就是已登记投影差异的例子。**只改 CSS 可能
让四端悄悄分叉**；只改 IDML 则可能让 token 名存实亡。不能手改批准 hash 绕过
reference gate。

---

## 附录 B 已知边界

### B.1 plain-Markdown 指令边界

plain-Markdown 的三处实现缺口已经关闭：单元格支持确定性的 `\|` 字面竖线，
`troubleshooting` 支持类型化双表头，任意 `:class:` 不再被静默接受。当前合同如下：

| 边界 | 行为 |
|---|---|
| 字面竖线 | 在单元格内写 `\|`；连续反斜杠按奇偶规则解析，避免先转换、后渲染得到不同列数 |
| 故障排查表头 | 可省略并使用 `Error Code` / `Corrective Measures`，或写 `:headers: A | B`；不是两个非空格子即失败 |
| callout variant | `:variant:` 只允许 `warning` / `danger` / `caution` / `note` / `tip`；可识别的源信号词也会映射到这五种语义 |
| 任意 class / 未知 option | 不属于作者合同；strict build 直接失败。需要新视觉变体时先登记 ComponentSpec variant 和四端 adapter，不得临时注入 CSS class |

### B.2 样式债与批准边界

分类定义和生命周期以 §0.3 为准。当前项以 `manual_style.yaml` schema v2 的
`conformance.debt`、`constraints`、`approved_variants` 为机器账本；本文 §1 仅提供
可读投影。
已经完成的清算范围、批准方法和验证结果属于
[历史执行状态](../../../code-as-doc/dev/style_debt_execution_status.md)，不要把它们
复制回来重新维护。

### B.3 兼容入口

下面三个旧路径只保留迁移提示，不能再增加样式规则：

- `docs/renderers/latex/STYLE_REGISTRY.md`
- `tools/idml/STYLE_MAP.md`
- `code-as-doc/title_style_guide.md`

仓库内新链接、代码注释和测试应直接指向本文。`STYLE_DEBT.md` 是旧快照，不再作为
当前文档提交；未完成项直接维护在 `manual_style.yaml`，执行证据放历史状态文档。
