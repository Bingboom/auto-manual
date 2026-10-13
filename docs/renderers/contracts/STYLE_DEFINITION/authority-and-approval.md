# 样式定义：权威边界、改动路由与合同生效（§0、§9）

属于[样式定义](../STYLE_DEFINITION.md)，其索引列出全部分页。章节编号与原文一致。
本主题的新说明写在本页，不要追加到总文件。

## 0. 权威边界与使用方法

### 0.1 哪个文件决定什么

“一份文档”不等于把机器合同改写成散文。可持续维护依赖下面七层各守边界：

| 层 | 权威来源 | 决定什么 | 不应该放什么 |
|---|---|---|---|
| 人类规范 | **本文** | 视觉意图、四端对照、实现归属、修改与验证方法 | 构建快照、临时排期、一次性 hash |
| 语义合同 | [`manual_style.yaml`](../manual_style.yaml) | 32 个稳定 `HB-*` ID、四端 capability/binding、theme-token role、`conformance`、`constraints`、`approved_variants` | CSS 像素值、逐页坐标 |
| 组件实例合同 | [`component_registry.yaml`](../component_registry.yaml) + [`tools/component_specs/`](../../../../tools/component_specs/) | 可跨 renderer 传递的 ComponentSpec 类型、variant、slot、asset role、token role 与 adapter key | CSS/TeX/XML/DOCX 几何实现、逐页坐标 |
| 主题投影合同 | [`manual_theme.yaml`](../manual_theme.yaml) | 稳定 `theme_id`、组件视觉角色及四端具体 binding | 单位值、目标/语言几何、页面实例坐标 |
| Web presentation stack | [`web_manual.json`](../web_manual.json) + [`web_presentation/`](../web_presentation/) | shared base、产品 skeleton、目标 overlay、Web 图能力授权与必需槽位 | 可见文案、跨 renderer 语义、另一个产品的整套复制配置 |
| 数值 token | [`data/layout_params.csv`](../../../../data/layout_params.csv) | PDF/IDML 共用的字号、间距、线宽、圆角及语言覆盖 | 组件路由和可见文案 |
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
variant、capability 和 token role 做机器校验，不能各自维护一套组件分类。若某个 variant
只适用于部分 renderer，`variant_adapters` 必须把四端逐项声明为 `rendered`、
`projection-only` 或 `not-applicable`；不能继承组件级 capability 后假称已支持。

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

单位：Web 用 `rem`（1rem = 16px），`clamp(最小, 视口比例, 最大)` = 随视口缩放并夹住两端；PDF/IDML 用 pt/mm，值取自 [`data/layout_params.csv`](../../../../data/layout_params.csv)；Word 的 `sz` 是半磅（34 = 17pt）。

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

本文的**流水线**特指以 [`build.py`](../../../../build.py) 为入口的生产手册链路：源表数据与 [`docs/templates/`](../../../templates/) 先组合成 prepared RST bundle。Web 生产路径由 [`tools/web/document_source.py`](../../../../tools/web/document_source.py) 一次读取有序源页，写出 `manual-ir/v2` / `whole-document-components/v1`；PDF、IDML 与 Word 保留各自的固定页/文档 adapter，历史 [`tools/idml_rst_extract.py`](../../../../tools/idml_rst_extract.py) `manual-ir/v1` 入口继续兼容。它不是“根据文字长得像什么来猜组件”，也不是 plain-Markdown 预览链路；[`tools/plain_markdown_site.py`](../../../../tools/plain_markdown_site.py) 只是把历史 Markdown 转成可审阅的中间指令并构建静态站点，不参与 production 发布装配。

```text
phase2 / 模板
    → prepared RST bundle（数据已替换、语言与页面顺序已确定）
    ├→ Web source adapter（识别结构标识与 ComponentSpec，一次读取）
    │   → manual-ir/v2 / whole-document-components/v1
    │   → 冻结 registry / theme / target contract / Overview instance / assets
    │   → Web replay（不重读 RST/CSV，不重跑旧 DOM projector）
    └→ PDF / IDML / Word adapters（消费同一 ComponentSpec 语义合同；各自拥有几何）

历史 manual-ir/v1 与 whole-document-flow/v1 只走显式兼容读取，不是新包的生产格式。
```

“流水线”一栏表示：该语义由源表字段、模板宏、显式 RST 容器、页面清单或页面角色共同产生，普通作者不能只写一段同名文案就触发它。例如正文出现 `Warranty Period` 不会自动变成质保年限卡；模板必须显式写出 `warranty-section warranty-years`。

### 0.5 流水线怎样加标识符

标识分五层，彼此不能混用：

| 层 | 标识示例 | 谁写入 / 负责什么 |
|---|---|---|
| 样式合同 ID | `HB-WARRANTY-SECTION`、`HB-TABLE-SYMBOL-SIGNAL` | [`manual_style.yaml`](../manual_style.yaml) 声明稳定语义、theme-token role、token 与四端 capability/binding；本文解释可读对照；`HB-*` 通常不会原样写进正文 |
| 源结构标识 | RST 标题、``.. container:: warranty-section``、`\\HBSymbolTable` | 模板或生成器写入 prepared RST；标识必须与本地化文案无关 |
| IR 类型标识 | block `kind`，以及 `component` / `data` / `semantic` payload 里的 `kind`、`roles` | extractor 解析源结构后写入，供渲染器按类型路由 |
| 装配角色 | `PageRole.WARRANTY`、`PageRole.SYMBOLS` | [`page_roles.py`](../../../../tools/idml/page_roles.py) 根据 manifest 中的 `source_ref` / 稳定文件名决定页面由哪个 composer 接管 |
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

   [`semantic_containers.py`](../../../../tools/idml/semantic_containers.py) 会把连字符规范成下划线，输出 `kind=warranty_section`、`roles=[warranty_section, warranty_years]`，并保留容器内的 typed blocks。后续 projector 生成 `warrantysection` / `warrantyyears` component，分别绑定 `HB-WARRANTY-SECTION` / `HB-WARRANTY-YEARS`。当前显式 semantic container 只支持质保语义；增加其他容器必须同时扩展 extractor、projector 和测试，不能只在模板里发明一个 class。
3. **生成型组件用稳定 HB 宏或 `manual-ir` payload。** 规格、Symbols、LCD、FCC、开箱和安全内容由模板生成 `\\HB...` 宏，或在 ``.. raw:: manual-ir`` 中携带带 `kind` 的 JSON。extractor 不保留排版命令本身，而是转成 renderer-neutral 的 `data` / `component` block，例如 `symbol_signals`、`lcd_icons`、`spec_section`、`safetywarning`。
4. **页面身份单独登记。** prepared bundle 的 manifest 决定 source 顺序和语言；稳定文件名 / `source_ref` 再映射为 `PageRole`。页面角色决定 physical composer，不能从页面标题翻译文本推断。批准装配中的 `UNCLASSIFIED_PROSE` 默认失败，只有精确登记的 source-ref 例外可放行。
5. **IR 再分配可追踪 ID。** [`manual_ir/builder.py`](../../../../tools/manual_ir/builder.py) 按最终页面顺序生成 `page-0001-<stem>`，按块顺序生成 `:block-0001`，同时保存 `source_ref`、`kind`、`payload`、内容哈希和资产引用。这些 `page_id` / `block_id` 是实例身份；`HB-*` 是样式语义身份，两者不能相互替代。

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

[`component_registry.yaml`](../component_registry.yaml) 是实例结构与 adapter key 的机器注册表；
[`model.py`](../../../../tools/component_specs/model.py) 和
[`registry.py`](../../../../tools/component_specs/registry.py) 对未知 component、variant、slot、
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

IDML 在 [`source_copy.py`](../../../../tools/idml/source_copy.py) 统一执行必填源文案检查；
批准 production 正文路径缺源时 fail-closed，兼容手递路径最多省略对应可见层。Symbols
续页通过带 `headers` 的 `SymbolOverflow` 继续传递源表头；数据页、Safety、FCC、
Operation 与 App 都从 Manual IR 的真实 payload 消费文案，不保留正文语言文案
registry。第 1–3 页和封底的 page-role scoped fallback 由上面的批准例外测试单独守护。
[`test_idml_visible_copy_sources.py`](../../../../tests/test_idml_visible_copy_sources.py) 同时守护
行为和静态 literal sink；增加 IDML composer 或 adapter 时必须把新的可见字段纳入该
门禁。

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
reference-layout plan 或[执行状态](../../../../code-as-doc/dev/style_debt_execution_status.md)，
不写进本文。这样规范不会因为一次发布或重新批准而过期。
