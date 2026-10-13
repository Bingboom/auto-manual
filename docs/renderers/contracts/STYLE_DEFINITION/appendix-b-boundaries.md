# 样式定义：附录 B 已知边界与原稿组件

属于[样式定义](../STYLE_DEFINITION.md)，其索引列出全部分页。章节编号与原文一致。
本主题的新说明写在本页，不要追加到总文件。

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
[历史执行状态](../../../../code-as-doc/dev/style_debt_execution_status.md)，不要把它们
复制回来重新维护。

### B.3 兼容入口

下面三个旧路径只保留迁移提示，不能再增加样式规则：

- `docs/renderers/latex/STYLE_REGISTRY.md`
- `tools/idml/STYLE_MAP.md`
- `code-as-doc/title_style_guide.md`

仓库内新链接、代码注释和测试应直接指向本文。`STYLE_DEBT.md` 是旧快照，不再作为
当前文档提交；未完成项直接维护在 `manual_style.yaml`，执行证据放历史状态文档。

### Authored text references (`HB-TABLE-REFERENCE`)

The shared Web component preserves source-authored text tables that do not have
per-row icon assets. RST declares `hb-source-lcd-legend` (number/name/description),
`hb-source-lcd-actions` (mode/action/result), `hb-source-lcd-actions-compact`
(function/description), `hb-source-lcd-descriptions` (headerless name/description),
or `hb-source-symbol-meanings` (two headerless columns).
CSV pages opt into the text-only LCD variant through the shared
`lcd_descriptions_template.rst`; actual icon rows are rejected, and other
LCD templates retain their existing contracts.
The source adapter preserves ordered rich-text cells and deliberately blank
callout numbers. It rejects conflicting declarations, unexpected columns,
headers, spans, nested tables and image cells. It never infers meaning from a
localized heading or adds replacement icon assets.

ComponentSpec owns the variant, accessible label, headers and rows. The Web
renderer owns `.hb-reference-composition` / `.hb-reference-table`; dark header,
paper, border and radius use the common manual CSS tokens. LCD artwork remains
an independently governed source image. LaTeX/IDML/Word adapters expose semantic
projections only; this addition does not claim new layout parity for those
renderers. The existing `HB-TABLE-LCD-ICON/icon-catalog` still requires one
approved icon per row.

`hb-source-specification` declares a headerless label/value table immediately
after its authored H2; it reuses `HB-TABLE-SPEC`. `hb-source-signals` reuses
`HB-TABLE-SYMBOL-SIGNAL`, and `hb-troubleshooting-table` reuses the existing
troubleshooting component. These declarations belong in source RST, not
hand-edited generated HTML. The CSV assembly plan also passes the semantic
`symbols` page role even when a slot renames the generated filename.

### Source-authored LCD and panel boundaries

A declared `hb-lcd-icon-table` may occur more than once in a page. The
`lcd-unnumbered` declaration maps a true three-column icon/name/description
source to `HB-TABLE-LCD-ICON/icon-catalog-unnumbered`; numbered sources retain
four columns and circles. Neither variant fabricates a header row.

The `web_source_panels.css` source containers preserve PDF grouping around
registered components: `hb-device-actions` pairs device art with an authored
function table, `hb-source-operation` groups illustration and source copy,
`hb-source-warranty` keeps a caption on the card border, and
`hb-source-purchase` / `hb-source-safety-heading` keep original icon/text strips.
Only these explicit boundaries bypass Pandoc flattening; ordinary paragraphs
continue through normal Markdown conversion. Narrow displays stack device art
above its function table without adding manual text. Both function-table column
headers retain bold type across languages; normal first-column weight applies
only to body cells. Function and description cells are vertically centered
within each row, including when localized text wraps across multiple lines.

Authored `hb-step-pair` containers pair a native `hb-step-copy` rubric number
with exactly one complete figure: two columns on desktop and copy followed by
art on narrow displays. Within each copy block, the circular number occupies
a fixed first column and prose starts on its right; continuation paragraphs
remain in the prose column. Copy and artwork align at their top edges. This uses the existing protected `hb-source-operation`
boundary; it does not require an operation-footer transform. `hb-source-note`
retains a gray notice, and `hb-source-power` retains the source's grouped power
instructions. A rubric within `hb-source-safety-heading` keeps the source signal
below the common icon without triggering a second warning-card transform.

Within `hb-source-status`, the native roles `hb-lamp-green`, `hb-lamp-red`,
`hb-lamp-blinking`, and `hb-lamp-off` add simple lamp shapes alongside editable
color text. Blinking has a static halo. The four-column status table scrolls
inside its own container on narrow screens. `hb-source-period-table` retains
a two-column period badge/prose composition on desktop and stacks on mobile.
The explicit `hb-source-warranty-note` marker on the protected introductory
notice scopes its containing chapter to compact source prose and title-case H2s
without decorative dots. The period badge uses a white numeral inside a dark
circle on white, followed by the unit and a bold subtitle. This declaration is
independent of product IDs, chapter IDs and localized heading wording.
Authored `hb-inbox-marker` labels replace numeric decoration; an optional
`hb-inbox-primary` source role puts the main item on its own row. Subsequent
items use four desktop columns and two mobile columns, retaining source order.
These opt-in compositions live in `web_source_panels.css`; ordinary inboxes
and warranty transformations retain their existing shared components.

When the operator requests preservation of original panel backgrounds, retain
the complete source panel (including gray shapes and rounded edges). The
standalone-device crop and the complete illustration panel are different
presentation assets. Avoid duplicate live captions when the original panel
already contains them.


Within `hb-source-signals`, the source may explicitly mark a label using the
RST roles `hb-signal-warning`, `hb-signal-danger`, `hb-signal-caution`,
`hb-signal-note`, or `hb-signal-tip`. This binds icon presence to authored
semantics while retaining the exact localized label. At most one such role
may occur in a label cell; conflicting roles are rejected. Unmarked legacy
labels keep the existing language-data lookup behavior.

### 原稿标题型号与完整警告框

原稿标题条右侧带型号时，在同一个可导航 H1 中声明 `hb-heading-title` 与
`hb-heading-model`，保留 `Model:` 原文；共享 `web_source_panels.css` 负责字号、
右对齐和窄屏换行。不要把型号移到标题下方段落，也不要把用于区分章节的内部名称
附加到原稿标题文字。

原稿为整行白底、深色描边的图标警告框时，在现有 `HB-CALLOUT-STRIP/warning`
载体上声明 `hb-source-warning-lockup`；label 中使用 `hb-warning-lockup` 绑定现有
共用 SVG 和原语种信号词，body 的原稿加粗使用语义 strong。共享样式处理描边、
列宽及手机堆叠，不增设型号专属告警适配器。普通接线图内标签继续使用现有
ReferenceFigure `base-art-live-copy` 源坐标，全部说明（含图内脚注）放在图内对应位置。

### 可编辑 PACKAGE LIST 分组

原稿将多个配件放在一个外框内时，可用共享 `hb-package-panel` / `hb-package-grid` 保持分组和原稿顺序；四列或 `hb-package-grid--five` 五列在窄屏统一降为两列。每件配件使用已核对的共用无外部标签图片，名称保留为原生段落；实线/虚线完整外框及 `hb-package-sold` availability capsule 均由共享 CSS 绘制，禁止底图保留空白标签框或 capsule。说明书缩略封面可换成现有通用文档图标，以可编辑名称区分文档；省略的微型封面印刷细节必须在原稿覆盖记录中注明，不能用已停用整图的 bbox 冒充保留。固定产品铭文及实物模板印刷仍属实物图形。

原稿中独立的深色圆角正文提示使用原生 `p.hb-prose-pill > strong`；共享样式使用品牌深色底、白色粗体、内容宽度及可换行胶囊。它仍是正文，不升级为标题或更改警告级别。引导短语使用原生 `strong`，其后的正文维持普通字重。

原稿图内的说明文字应绑定 `HB-SPECIAL-REFERENCE-FIGURE/base-art-live-copy` 的原稿坐标，不另放图外重复段落。完整底图使用 `preserve_frame`；需要手机可读字号时，`hb-reference-contained-copy` 容器让共用组件的默认手机排版仍处于同一原稿色调的圆角图框内，图片保持原字节和完整边缘。桌面坐标布局不受影响。


### JA-AD600A EU 共用底图复核

操作者要求图内需要翻译的说明与底图分离；尺寸、单位、固定铭刻和对应编号可保留。
英文当前通过既有 ReferenceFigure 接入五张共用底图，共 26 个原生说明标签；
九语均复用同一图形，各语文字仍应来自各语原稿。本地预览不提供点击编辑功能。

| 图示 | 已检查候选与决定 | 原稿及底图策略 |
|---|---|---|
| 产品概览 | 既有 `product_overview.png` 留有英文；同型号其他语言及 shared/template 无匹配无字图，新增共用 PDF/PNG | 当前 AI 实际第 5 页；去除六处说明，保留铭刻、产品轮廓及全部虚线引线 |
| 安装总图 | 既有 `installation_diagram.png` 留有英文；无匹配共用裸图，新增共用 PDF/PNG | 当前 AI 实际第 9 页；去除八处说明及独立脚注底框，保留灰色放大面板、车辆、线缆和 A–F 编号；脚注框由 CSS 绘制 |
| 保险丝、ACC 接线、端口连接 | 复用本轮已核实的 `ja_ad600a_eu_shared` 底图，不重新提取 | 现有底图哈希不变，十二处原生标签独立于图形 |

新增两图的原稿 SHA-256、四个输出哈希及删除区域锁定在
[`manual_ja_ad600a_eu_overview_bases.json`](../../../../data/asset_recipes/manual_ja_ad600a_eu_overview_bases.json)，
对应标签坐标和必需槽位锁定在 `ja-ad600a-eu-v1` target overlay。
旧图及原始 recipe 保留追溯，本轮未写入资产注册表或线上业务表。


短版 FCC 的标题/正文/标志排版由共享 `web_fcc_statement.css` 承载，接入既有样式组装列表；完整 FCC 样式保持原模块，不提高维护性行数上限。

### Native preface heading and prose

Source-authored PDF prefaces use `h1.hb-preface-heading` with `.hb-preface-region` and `.hb-preface-prose` (shared rules in `web_source_panels.css`). The heading has a transparent background with the native region/language badge; prose uses compact 1.45 line height and 0.45rem paragraph margins. Keep the native title/region text and keep ordinary chapter H1 bars unchanged. This treatment is explicitly opt-in through authored classes, not a target/model selector.
