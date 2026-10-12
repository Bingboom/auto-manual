# Build guide: prepared Web component admission

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

## Prepared EU Web component admission

Fresh EU/UK Web staging and sealing require a valid IR sidecar and the reviewed chapter/variant policy. Existing immutable evidence remains replayable. See [admission and bounded migration debt](../dev/prepared_component_admission.md) before onboarding or rebuilding a legacy target.

Authored Web tables declare their semantic role in source RST; the shared adapter preserves rich cells and blank LCD callouts. CSV symbols use the assembly plan role instead of filename guessing. See [authored text references](../../docs/renderers/contracts/STYLE_DEFINITION.md#authored-text-references-hb-table-reference).

JE-3000C/EU 本地化操作章节与 JE-1000H/EU 英语章节通过现有目标展示 overlay 绑定共享操作表。自动恢复和组合键在 RST 导入时也生成 ComponentSpec，与 LCD 模式一起进入整本 IR；这不授予其它操作成品图的重排权限。存量发布迁移顺序与验收边界见 [EU shared-component rollout](../dev/eu_shared_component_rollout_2026-09.md)。

新增语言的原生便携手册须通过[共享组件准入](../dev/web_publish_pipeline.md#native-multilingual-shared-component-admission)：按稳定章节 ID 检查 LCD、自动恢复、组合键、规格、质保、App 等组件的实际绑定，不能只凭 `manual-ir/v2` 或组件数量声明认定复用完成。新 PDF 导入、冷重放、发布封存和发布证据核验会阻止漏绑定及组件外的普通表格/图片。构建生成的 `shared_component_coverage` 记录覆盖情况；已发布冻结版需逐语迁移并重新发布才能更新样式。

JE-1000H EU LCD 图标表（2026-09-30）：六语共用同一组冻结图标引用，并通过
`HB-TABLE-LCD-ICON` 保留编号、状态分行和加粗。发布门禁已取消六个纯文字表例外，
改为要求真实 LCD 组件；缺图不能再静默退回纯文字。素材记录见
[`lcd_icon_provenance.json`](../../manual_sources/JE-1000H/EU/en/2.0/lcd_icon_provenance.json)。
连接电池包的现有小图仍是清晰度待办，未重新裁图或变更线上源表。

新原生 PDF 的 LCD 表对相邻同编号条目（如高温／低温）保留两条独立图标、名称和说明，但编号只显示一次并跨行居中。该布局由冻结 ComponentSpec 的 `number_cell_layout: span-adjacent-equal` 声明；未声明的历史冻结版本维持原样，编号不跨非相邻行合并。

日规等审核稿中的纯文字装箱清单，Web 整本 IR 将完整的三项无图清单映射为 `HB-TABLE-REFERENCE/plain-inventory`，复用公共表格样式，保留原有注意事项和强调。带图片或紧邻提示表的清单仍按 `HB-SPECIAL-INBOX` 校验，缺图会阻止发布；不补入其他地区的图片。

JE-1000F/JP 的 Web 展示契约保留日规质保的 7 个正文章节与原有换行，不强制生成欧规年限卡片；旧 App 的“控制面板图 + 三段按钮名称”通过明确的源图绑定进入共享 App 组件，按钮标签保持日文并按 AC/DC 语义定位。

中规审核源也支持三项无图项目列表：复用 `plain-inventory` 并保留列表强调和外部备注。独立 LCD 模式图后紧邻的四列表（首列全部为空、三项表头和六行动作）保留原图与表头，映射至 `HB-TABLE-REFERENCE/lcd-actions`；非空占位列或结构变化拒绝导入。显式绑定的 App 双图之间若有一张纯文字备注表，共享面板将其保留在面板后方，备注仍独立进入共享提示组件，不被图片或标签吞掉。

原生 PDF 录入和审核 RST 的 Web Publish 共用[图文分工规则](../../docs/renderers/contracts/STYLE_DEFINITION.md#新录入网页的图文分工)：普通说明文字与文字框由共享 HTML/CSS 承载，保留实际插图边界，密集引线图按已批准例外处理。新目标必须登记组件和底图哈希并独立验收，不能把四语测试通过当作中规验收。显式 `base-art-live-copy` 绑定复用 ReferenceFigure 适配器，不需要启用该目标不适用的整套 legacy figure 布局。

App 下载段如果只有一张二维码，使用显式 `app_download.presentation=qr-only` 绑定，映射到 `HB-SPECIAL-APP/download-qr-only`；它保留相邻说明段和单个源二维码，复用共享限宽样式，不能按普通通栏插图输出。

Operation 源图已含外框时，中立 flow 包裹容器声明 `data-preserve-art-frame="true"`，避免共享 stage 再画第二层边线；前提说明使用 prerequisite 槽位及底图绑定坐标，文字和浅灰胶囊留在图内，由 HTML/CSS 绘制。

Web App 编号步骤标题保留源文大小写，隐藏圆点并与步骤正文左边线对齐；该共享样式只作用于 App 章节。冻结包需重新生成并核验桌面/手机预览后才能采用更新样式。

通用 LCD／状态图标及 POWER、AC、DC/USB、LIGHT 按钮图先按功能语义复用现有共用素材（Web 按钮图使用透明 SVG），不从各语言 PDF 重裁带底色的小图；仅在共用素材缺失或有明确机型差异时才提取。仅上述 LCD／状态图标、独立按钮符号等小图默认透明底，移除其外围单元格底色和边框；保留符号、按键面和丝印。大图面板保留灰底、圆角、外框和引线，不能套用小图规则。普通图采用无字底图加原生文字，表格保持原生 HTML，密集引线图不重复显示图内文字。规则见[共用图标优先](../../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)。

原稿 SVG 的填充／描边校验允许等价的绝对 H/V 闭合线段参与路径比较；导出仍保留原始路径、变换、透明度与裁切，并保留裁切范围内通过 `use` 引用的原稿嵌入图像；无法对应的路径继续拒绝。

中规共享配置 `configs/config.zh.yaml` 已声明 JE-2000E/CN 和 JE-2000F/CN；已有 JE-2000F 审核稿通过 `--source review-asis` 预览和 Web Publish，避免用运行时参数重建已确认版面。

### Native RST notices in Web output

Native RST `note`, `tip`, `warning`, `caution` and `danger` directives pass through the existing `HB-CALLOUT-STRIP` component before Pandoc. Their explicit body boundary, rich paragraphs and lists survive Markdown/Sphinx export; adjacent prose stays outside the box. Docutils titles such as `Caution!` retain their displayed punctuation and registered semantic variant. This also applies to the shared Word HTML adapter.

### Preserve source-authored Web layouts

`hb-lcd-icon-table` is a headerless four-column number/icon/name/description
source. Multiple declared LCD tables on a page retain separate boundaries.
Add `lcd-unnumbered` only for a source table with three actual
icon/name/description columns; do not synthesize a number or an empty numbered
cell. `hb-source-symbol-icons` admits the authored four-column symbol/meaning
matrix into the existing two-panel symbol component. Signal badges preserve
source label text without copying the Word adapter's decorative glyph.

For source compositions around existing components, RST containers
`hb-device-actions`, `hb-source-operation`, `hb-source-warranty`,
`hb-source-purchase`, and `hb-source-safety-heading` preserve the complete
outer boundary through Pandoc. Their responsive styles live in
`docs/renderers/contracts/web_source_panels.css`; the contained tables still
use registered ComponentSpecs and all text remains source-authored. Native
admonition titles retain their explicit punctuation independently of their
semantic type. Verify the final Sphinx DOM and browser rendering, since an
intact intermediate HTML container does not prove it survives Markdown.

Complete charging-panel assets retain the source gray backdrops, rounded
boundaries and in-figure labels when the operator requests PDF parity. Do not
replace shaped backgrounds with a generic CSS gray rectangle. A finished
illustration manifest can explicitly set `allow_reuse: true` for one
hash-verified shared icon used in several source notices; repeated source
identities without that opt-in still fail.
