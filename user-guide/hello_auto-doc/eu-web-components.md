# Workflow guide: EU Web shared components

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

四语原生网页的标题、前言分段、安全警告框与质保卡片沿用英文版公共组件。LCD 显示序号、图标、名称和说明四列；App 截图下保留 2.1–2.5 编号。标注线密集的产品前/右视图使用对应语言成品图，正文和表格仍可选择、搜索。

Native PDF LCD intake preserves semantic status lines and bold status prefixes in the existing `HB-TABLE-LCD-ICON` component. The verified uk/pt/nl/pl paragraph boundaries also separate App setup and retained-setting notes; printed line wrapping is not copied into Web layout. Numbered troubleshooting measures each start a new line; the emergency-charging lead retains its bold emphasis. Shared reference-figure captions follow the artwork, matching the App 2.1–2.2 captions. Source wording, governed icons and historical frozen versions remain unchanged.

产品前／右视图的小标题使用图片外的原生网页文字。四语成品图只保留插图、参数与标注线；冻结绑定 `overview_finished_panels` 的 `captions_embedded: false` 恢复可见标题，旧版 `true` 仍隐藏重复标题。导出时按源 PDF 坐标排除标题，保留来源哈希及已批准勘误，不改写历史冻结版本。

自动恢复条件使用共享 `HB-TABLE-AUTO-RESUME`：两列表头，左侧 3 条、右侧 4 条，中间左格跨两行。四语原生 PDF 录入通过 ComponentSpec 调用既有 Web 表格渲染器；标题和引言在表外，条件为可选文字，不以列表或截图替代。新版本保留全部图片及已审勘误。

交流充电图的源稿裁区必须包含完整外框和左右下圆角。说明文字继续作为网页正文；移除图内重复说明时只剥离文字，不删除背景、产品线条或边框。四语共用图修复须一起重建并核对其余图文不变。

太阳能接线图若自带外框和留白，外层底色须与留白对齐，避免生成双重灰边。太阳能板可复用，整张主机接线图仍须核对型号与插座／接口版本；不能仅按语言一致就跨地区替换。

按键组合表由共享 `HB-TABLE-KEY-COMBINATIONS` 承载三列表头和操作行，通过 `manual-ir/v2` 的 ComponentSpec 直接复用英文 Web 表格渲染：深色圆角边框、40/25/35 列宽、首列灰底及正文常规字重。原生 PDF 的操作文案取文字区域，排除时钟图旁重复的时长标记；不改动句内时长或功能内容。

Charging reference diagrams reuse the shared live-label component: captions occur once and note pills use HTML/CSS over artwork without baked text or white pills. Other portable power stations may reuse the component with their own verified device/interface artwork. See [the JE-2000 intake and regression record](../../code-as-doc/dev/je2000_eu_new_locales_ir_adapters_2026-09.md).

## 欧规网页共享组件防回退

新型号、地区或语言录入也遵循同一套[图文分工规则](../../docs/renderers/contracts/STYLE_DEFINITION.md#新录入网页的图文分工)：文字和承载它的灰/白框用 HTML/CSS；底图保留完整主机、线缆、放大圆和实际外框。密集引线概览图、App 界面、二维码及产品铭刻按各自例外保留。四语已有测试不替代中规等新入口的组件绑定、哈希和桌面/窄屏验收。

新发布的欧规／英规候选包必须携带 IR，并符合已登记的章节、共享组件及变体要求。删除组件、旁车文件或扩大遗留例外会阻止发布。新增型号／语言要先登记适用章节；历史 App 整图和 LCD 降级不会算作已复用。历史发布仍可回放，详见[共享组件准入与迁移](../../code-as-doc/dev/prepared_component_admission.md)。

维护旧版网页表格时，在源 RST 中声明共享表格类型，重新构建整本；不要直接修改生成 HTML。纯文字 LCD 说明保留原编号（包括空编号），不自动补图标。多语质保开场可有多段，顺序和段落边界必须保留。定义见 [共享样式](../../docs/renderers/contracts/STYLE_DEFINITION.md#authored-text-references-hb-table-reference)。

旧 RST 手册的共享样式也须核验实际章节绑定。JE-3000C 欧规五语与 JE-1000H 欧规英语的操作表沿用同一组自动恢复、LCD 模式和组合键组件，原文和图片保持源稿所有权。代码修复不自动改变已发布冻结版本：需重新构建、核验并发布。进度与剩余范围见 [EU shared-component rollout](../../code-as-doc/dev/eu_shared_component_rollout_2026-09.md)。

### 新增语言的共享样式检查

新增原生 PDF 语言沿用同一组共享组件；译文、型号参数和对应地区的图片由源稿决定，表格、质保卡片、操作区和 App 的版式由共享组件负责。现在导入/冷重放与发布封存会检查章节所需组件是否真的存在。报错 `shared component coverage failed` 时，根据提示的章节和组件 ID 补绑定，不能用普通表格或截图绕过。密集标注整图保留已批准的引用图方式。

验收新增语言时，逐语检查图内提示框是否遮住按钮圆图或引线，以及手机换行后是否越界。节能图只应有一个时钟，源稿 App 步骤编号若仅在截图下出现，应保留这一结构。修复提取范围和图文绑定后生成新的候选预览；既有语言的冻结版本保持不变。

指定沿用源稿完整配件排版时，应保留虚线框、配件标题与“单独销售”徽标的相对位置，
不能把徽标文字当成第四个普通标题。对应语言成品参考图保留图内文字，另提供检索和
读屏文本，不重复显示图外标题；该排图内文字需回源稿修改，不是独立 HTML 文字框。
充电、UPS、扩容等完整大图也应保留原稿灰底、白色说明区和圆角边框；透明底规则
仅用于 LCD／状态图标、独立按钮符号等小图，不用于完整面板。

共享代码更新后，旧的冻结手册不会自动迁移。每次修复需列出受影响语言、生成新冻结版本、检查桌面/手机并重新发布；验收应打开正式 RTD 路由。检查通过表示组件覆盖完整，仍需核验译文、参数、地区图片和实际版面。技术边界见[共享组件准入](../../code-as-doc/dev/web_publish_pipeline.md#native-multilingual-shared-component-admission)。

JE-1000H EU LCD 图标表（2026-09-30）：六语共用同一组冻结图标引用，并通过
`HB-TABLE-LCD-ICON` 保留编号、状态分行和加粗。发布门禁已取消六个纯文字表例外，
改为要求真实 LCD 组件；缺图不能再静默退回纯文字。素材记录见
[`lcd_icon_provenance.json`](../../manual_sources/JE-1000H/EU/en/2.0/lcd_icon_provenance.json)。
连接电池包的现有小图仍是清晰度待办，未重新裁图或变更线上源表。

新原生 PDF 的 LCD 表对相邻同编号条目（如高温／低温）保留两条独立图标、名称和说明，但编号只显示一次并跨行居中。该布局由冻结 ComponentSpec 的 `number_cell_layout: span-adjacent-equal` 声明；未声明的历史冻结版本维持原样，编号不跨非相邻行合并。

日规等审核稿中的纯文字装箱清单，Web 整本 IR 将完整的三项无图清单映射为 `HB-TABLE-REFERENCE/plain-inventory`，复用公共表格样式，保留原有注意事项和强调。带图片或紧邻提示表的清单仍按 `HB-SPECIAL-INBOX` 校验，缺图会阻止发布；不补入其他地区的图片。

JE-1000F/JP 的 Web 展示契约保留日规质保的 7 个正文章节与原有换行，不强制生成欧规年限卡片；旧 App 的“控制面板图 + 三段按钮名称”通过明确的源图绑定进入共享 App 组件，按钮标签保持日文并按 AC/DC 语义定位。

Web 操作图只保留一层实际外框。源图已有浅灰圆角框时，不再叠加网页边框；原稿图内的前提说明仍在图内左上方，用可选择文字和 CSS 胶囊承载。

Web App 的编号步骤标题按原稿保留大小写，与步骤正文左边线对齐，不额外显示圆点。重新生成的候选包采用共享样式，旧冻结包需单独更新并检查预览。

中规审核源也支持三项无图项目列表：复用 `plain-inventory` 并保留列表强调和外部备注。独立 LCD 模式图后紧邻的四列表（首列全部为空、三项表头和六行动作）保留原图与表头，映射至 `HB-TABLE-REFERENCE/lcd-actions`；非空占位列或结构变化拒绝导入。显式绑定的 App 双图之间若有一张纯文字备注表，共享面板将其保留在面板后方，备注仍独立进入共享提示组件，不被图片或标签吞掉。

通用 LCD／状态图标及 POWER、AC、DC/USB、LIGHT 按钮图先按功能语义复用现有共用素材（Web 按钮图使用透明 SVG），不从各语言 PDF 重裁带底色的小图；仅在共用素材缺失或有明确机型差异时才提取。仅上述 LCD／状态图标、独立按钮符号等小图默认透明底，移除其外围单元格底色和边框；保留符号、按键面和丝印。大图面板保留灰底、圆角、外框和引线，不能套用小图规则。普通图采用无字底图加原生文字，表格保持原生 HTML，密集引线图不重复显示图内文字。规则见[共用图标优先](../../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)。

原稿 SVG 的填充／描边校验允许等价的绝对 H/V 闭合线段参与路径比较；导出仍保留原始路径、变换、透明度与裁切，并保留裁切范围内通过 `use` 引用的原稿嵌入图像；无法对应的路径继续拒绝。

JE-2000F/CN 沿用 `configs/config.zh.yaml` 中规共享配置与现有审核源；预览、发布按审核稿原样构建。

新增 JE-3000C/EU 葡语、荷语、波语沿用现有六语网页的公共 IR 和组件。
图中标签从各语原稿的坐标范围读取，保持可选文字；同一个 PDF 文本块里的多个标签
也分别绑定，避免漏用共享图文组件。安全提示的标签在原生读取顺序首尾均能识别，
正文只显示一次。技术事实矛盾记录为待确认，预览可以打开，但发布封存会阻止该语种。
范围、来源和验收见[三语录入记录](../../reports/je3000c-eu-three-language/README.md)。

### 原生 RST 提示框的 Web 保留

Native RST `note`, `tip`, `warning`, `caution` and `danger` directives pass through the existing `HB-CALLOUT-STRIP` component before Pandoc. Their explicit body boundary, rich paragraphs and lists survive Markdown/Sphinx export; adjacent prose stays outside the box. Docutils titles such as `Caution!` retain their displayed punctuation and registered semantic variant. This also applies to the shared Word HTML adapter.

PDF 对照修正时，表头、圈号、图标、提示标签和说明文字都以操作员提供的原稿为准。
不要补写滚动提示或把购买提示改成 NOTE。LCD 图标表可分别声明有编号四列或
无编号三列；设备图与操作表、保修卡片等原稿组合使用受保护的 RST 容器，
需在实际 Sphinx 页面检查桌面和手机显示。独立设备图应排除误截的表格边框；充电等完整成图应保留原稿的灰底、分区、
圆角及图内标签。保留设备、手指、引线及产品标记，并单独记录来源、页码、裁切范围和哈希。


JE-100C/EU 的 Web 本地源现支持英文及新增法、西、德、意、乌、葡、荷、波，共九语。
按语种选择 `configs/config.eu-<lang>.yaml`，复用英文冻结包中的产品身份数据，
正文和插图由各自语言的原稿及修订记录绑定；[示例命令与来源边界](../../code-as-doc/build_doc_guide/web-target-notes.md#je-100ceu-nine-language-web-source)。
乌、葡、荷、波的旧版 AC 充电等差异已按操作者指示对齐新版英文，原始来源和修订依据均保留。
葡语代码为 `pt`，区别于巴西葡语 `pt-BR`。本地构建通过不等于线上发布；
正式发布仍走既有审核、冻结快照、Hello-Docs 和 RTD 流程。

### 原生 PDF 的已确认勘误

原生语言导入的 `source/errata.json` 可为已确认条目登记 `native_bindings`：源哈希、确认记录、来源页码、精确字段路径以及修改前后全文。适配器在共享组件构造前应用，原始提取证据保留；原文或来源不匹配即失败。文字勘误涉及带标注的概览图时，须同时修正图内文字并重锁资产哈希；清空待确认状态不能代替实际修正。

冻结 PDF 参数表的语义换行由 `source/target_layout.json` 各语言的 `specifications.value_breaks` 声明（`group`、从零开始的 `row`、唯一匹配的 `before`）。例如车充／PV 共用单元格在 `PV:` 前换行；源文字和已批准勘误先保持完整匹配，再投影为共享 IR 的 `line_break`，不恢复印刷版所有折行、不拆出额外表格行。更新时创建新的冻结版本，旧版本保持不变。

HTP011 英文无图标 LCD 说明通过共享 `lcd_descriptions_template.rst` 显式绑定
`HB-TABLE-REFERENCE/lcd-descriptions`，保留名称／说明两列及原稿文字；
发布封存直接校验组件，不再依赖该目标旧 LCD 表的内容哈希例外。

Intake preparation: [source-copy work packets and shared-art review](../../code-as-doc/dev/manual_intake_assistance.md) enumerate pending work without approving a baseline or publishing.

共用图确认清单可通过 `tools.manual_intake_assist art-review --selections` 导入；
太阳能保留型号/数量标识，车充文字用 HTML/CSS，操作与按键图片不纳入共用库。
图标按原稿中匹配的符号复用，独立图标须真实透明底。

仅含一段声明的 FCC 可用 `hb-fcc-composition hb-fcc-statement` 复用完整 FCC 的浅灰圆角面板和紧凑正文，保持单栏和原稿内容；完整 FCC 的 NOTE / MODIFICATION 不应补入短声明。原生 H2 标题保留在 section 中，正文和左侧共用 FCC 标志由既有受保护 figure 通过原生 flow 输出；共享 CSS 将它们排在同一面板中。


短版 FCC 的标题/正文/标志排版由共享 `web_fcc_statement.css` 承载，接入既有样式组装列表；完整 FCC 样式保持原模块，不提高维护性行数上限。
