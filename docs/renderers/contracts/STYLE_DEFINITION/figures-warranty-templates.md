# 样式定义：图与专题版块、质保、页面模板（§5–§7）

属于[样式定义](../STYLE_DEFINITION.md)，其索引列出全部分页。章节编号与原文一致。
本主题的新说明写在本页，不要追加到总文件。

## 5. 图与专题版块

普通插图：`img { max-width: 100%; height: auto }`，Web 投影下每张独立图占满同一内容宽度并居中，不保留印刷侧的固定像素宽度提示。

### 新录入网页的图文分工

以下规则同时适用于原生 PDF 四语录入和审核 RST 的 Web Publish，不能因型号、
地区、语言或输入入口不同而重新选择样式。已批准的历史 finished-panel 契约仍按
其目标范围执行，不能用这段规则自动改写历史冻结版本。

| 源稿内容 | 网页承载 | 验收要求 |
|---|---|---|
| 普通操作、UPS、充电图中的说明文字 | 无字底图 + 既有 Operation / ReferenceFigure 的活文字 | 每段源文字只消费一次；章节标题、正文和表格不截入底图 |
| 承载说明文字的灰框、白框、胶囊和气泡 | 共享 HTML/CSS 绘制，随文字换行 | 底图连同空文字框一起去除；不能只删字后留下空框。沿用共享色阶与圆角 |
| 插图自身的背景、外轮廓、外框、线缆、引线及放大圆 | 保留完整源图几何 | 去文字框不能扩大裁切、截断右边线或放大圆；不得用白块覆盖非白背景 |
| 正视图、侧视图等密集引线标注图 | 经目标确认的本地化完整图 | 保留完整标注，不混入章节标题；型号、插座、接口必须匹配 |
| App 界面、二维码、产品实物铭刻 | 保留图内内容 | App 步骤号统一用图下 HTML；不把界面文字当说明文字删除 |

2026-10-03 共用图整理约束：太阳能接线图保留原图中的 `SolarSaga 型号 × 数量`
文字作为选材主标识（例如 `SolarSaga 100 Air × 4`），不得把该标识当普通说明文字去除；
同标识下仍核对主机、接口及接线变体，不能据此跨型号误用。原标识未写数量时不自行补数。
车充及车充线图的说明文字采用原生 HTML，文字框采用共享 CSS；无字底图中不能残留
文字或空白文字框。操作与按键**图片**不纳入共用素材库，既有 Operation 等共享组件
继续复用。独立 LCD/安规符号需真实透明底，灰底、白底及低分辨率版本不能选作主资产；
图内数值（例如连接电池 `×8`）属于身份，不能用 `×5` 等近似图替代。

外观相同的素材由执行者对照归一到既有主资产，旧路径/哈希作为追溯别名保留；
不同分辨率、透明区隐藏 RGB 或留白不作为新图身份。感知相似度只能筛候选，最终核对
符号形状、数值、主机及接线。操作者按明确标识和差异确认，不承担逐张重复认图。

Operation 底图已含完整外框时，在承载组件的中立 flow 容器声明
`data-preserve-art-frame="true"`：共享 CSS 取消组件额外的外框和圆角裁边。
图内前提说明继续使用 Operation 的 prerequisite 槽位及源坐标，浅灰胶囊由
HTML/CSS 按 `prerequisite_fill` 绘制；只有前缀加粗，不把说明移到图外。

跨语言可复用已核对的同一底图和组件；跨型号复用前必须核对主机、接口和地区差异。
共享样式不代表可以借用另一型号的底图。底图、源文字、SHA-256 和百分比标签位置
必须一起登记；独立线缆名称也使用 ReferenceFigure 的活文字标签，产品实物
铭刻继续保留。无文字框的标签不额外生成胶囊。`base-art-live-copy` 复用现有
`manual-ir/v2 → ComponentSpec → 公共 Web 渲染器`，不能用目标专属 HTML 或截图绕开它。

新增目标要登记必需的组件槽位。校验分别检查源文字只出现一次、组件实际使用、
布局所绑定的底图哈希，以及去字区域无残字/空文字框；最后对照 PDF 检查桌面和
窄屏。构建通过、旧语言测试通过，都不等于新目标的视觉验收通过。

图内文字由 HTML 承载不等于把文字移到图外。ReferenceFigure 的
`base_art_layout.mobile_labels=overlay` 明确要求窄屏仍按底图坐标放置；
`preserve_frame=true` 保留源图边界，禁止默认裁边。JE-2000F/CN 的两张太阳能图
和车充图使用这两个选项，车充白色提示框由 `.hb-reference-live-pill` 绘制。

原稿同时有应用商店徽章和二维码时，使用已有 `HB-SPECIAL-APP/download` 双栏组件。
源图声明 `hb-source-app-download`，`data-app-download` 绑定 `artwork.store` 与
`artwork.qr`，后接两段原语种说明；共享 IR 固定两栏和素材角色，不依赖型号白名单。
复用已批准的徽章与源二维码，缺素材或少一栏说明即拒绝录入，不降级为仅二维码。
编号 App 标题不加圆点，采用原稿大小写与紧凑间距。完整双机/三机截图使用现有
`hb-app-add-device-phone-art` 加 `hb-app-phone-pair` / `hb-app-phone-trio` 共享限宽
变体，最大 22rem / 36.75rem，窄屏缩至可用宽度；该尺寸在成品图替换后仍有效。
截图保留手机全框、状态栏、底部界面和原有步骤号，各语言继承同一组件及尺寸决策。

只有下载二维码与说明的源稿使用 `HB-SPECIAL-APP/download-qr-only` Web 变体：
原文左排、二维码右排，二维码最大 `9rem`，手机为 `6rem`，保留完整边框。
它不补画源稿没有的应用商店徽章，不套用普通插图的通栏宽度。该变体通过共享 IR
冻结一个源图与一段活文字；印刷适配器尚未声明支持，调用时明确拒绝。

App 添加设备源稿中夹在手机图和按键图之间的备注，由共享组件的
`interstitial_note` 活文字槽位保存原顺序；不能为合并图片而移到按键图之后。
手机图与图下步骤号共同服从目标声明的最大宽度，窄屏按比例缩小。
若源截图之间留有间隔，App/ReferenceFigure 使用 `caption_centers_pct` 登记各图的
原生横向中心；不能把整幅图机械等分后让编号偏离手机中心。
审核 RST 的 App 行内按钮和结果截图可用 `semantic_source_patterns` 显式登记，
分别使用现有 `inline-control` 与 ReferenceFigure 活编号组件，无需开启历史整页插图适配。

四语的已验证实现与历史纠错见
[`four_language_shared_ir_alignment.md`](../../../../code-as-doc/dev/four_language_shared_ir_alignment.md)
及[充电标签纠错记录](../../../../code-as-doc/dev/je2000_eu_new_locales_ir_adapters_2026-09.md#charging-label-regression-and-english-artwork-reuse-2026-09-29)。

四个专题版块都是**流水线专属**，作者不能用 md 写，只能改源表或模板：

| 版块 | Web 结构 | 说明 |
|---|---|---|
| FCC | `.hb-fcc-composition` > `.hb-fcc-grid` | 开场文案 + 分栏条款，IDML 用无表头表格承载 |
| 开箱清单 | `.hb-inbox-composition` > `.hb-inbox-grid` | 三张等宽圆角卡 + 1/2/3 角标 + 通栏 TIP 条 |
| 产品概览 | `.hb-annotated-figure` > `.hb-annotated-stage` + `.hb-leader-layer` | 带引线标注：标注位置靠逐图百分比坐标，是流水线独有的能力 |
| App 设置 | `.hb-app-download-composition`、`.hb-app-add-device-composition` | 商店徽章 / QR / 双机图；默认的共享按键底图不依赖目标插图授权，标签保持为覆盖活文本。仅当 target 的已核准 finished-panel 明确包含该组标签时，允许在 presentation 前以整图消费该 reference，并同时移除重复活文本；JE-2000F/EU/en 的三键控制面板属于此批准变体。LCD 模式表不属于此例外，仍由设备图与语义化 CSS/HTML 表格组成 |

Web App 的编号步骤标题保留源文大小写，不加圆点，与步骤正文左边线对齐；该例外仅限包含共享 Add Device 组件的章节，不覆盖其他章节的 H2/H3。

IDML App 下载构图以左右两个活文本栏的中心分别对齐商店徽章和 QR，不以整页中心或固定左边缘对齐；控制面板的三条原生延长线统一消费 `idml_app_control_leader_extension_weight`，与链接底图中的引线保持同一视觉线宽。

FCC 的单一语义实例是 `HB-SPECIAL-FCC` ComponentSpec：它保存无障碍标签、开场文案、按源顺序排列的段落/列表、逻辑分栏点和 `compliance_mark` 资产角色；资产实例只引用注册表语义键 `mark/fcc`，各 renderer adapter 再解析自己的 PDF/PNG 路径。Web、LaTeX、IDML、Word 分别消费自己的适配器；两栏宽度、固定页坐标、DOCX 表格属性和 CSS 断点不进入 ComponentSpec。Web 只渲染审批过的浅灰 FCC 外框，导航里的 `FCC` H1 保留给目录和无障碍技术但视觉隐藏，不合成黑色标题条；外框继续服从 §8.1 的通栏等宽契约。源 payload 先类型化为 ComponentSpec；IDML/LaTeX 再从语义 block 重建自己的结构，不保留或回放旧双文本 payload。
FCC Web 正文左右高度明显失衡时，可在现有 FCC 组件外声明共享 `hb-fcc-balanced-flow` 容器。桌面使用自动平衡的两栏文字流，FCC 标志左浮动并允许文字在其下方续排；手机回到单栏。DOM 保持开场、NOTE 正文、措施列表和 MODIFICATION 的原文顺序；不改 ComponentSpec 的印刷分栏点，也不按机型复制 renderer。
短版 FCC 声明在既有受保护 `figure` 载体上声明 `hb-fcc-composition hb-fcc-statement`，复用浅灰圆角 FCC 面板；共享样式保留单栏、紧凑标题和正文，标题取消通用圆点。原稿标题、段落和标题锚点由原生 flow 承载，不增加原稿未含的 NOTE / MODIFICATION 条款；FCC 标志复用注册表 `mark/fcc` 的现有主资产，按操作者指定放在左侧，不套用完整两栏 FCC 语义实例。



开箱清单的单一语义实例是 `HB-SPECIAL-INBOX` ComponentSpec。兼容变体 `three-card-responsive` 固定保存三张有序卡，每张卡包含序号、独立 `card_N_art` 资产角色、可访问 alt 和可编辑本地化 label；`responsive-card-grid` 保存任意非空有序卡组，按顺序复用可重复的 `card_art` 资产角色。两种变体都把相邻 TIP/NOTE 的 label/body 纳入同一实例。Web adapter 支持两种变体：三卡继续等宽，动态卡片在桌面自适应、平板三列、手机单列。LaTeX 的 `HBInBoxThree`、IDML 绝对坐标 composer 和 Word 三列表格只对旧三卡变体声明 `rendered`；动态变体在注册表中逐端标为 `not-applicable`，调用这些 adapter 会显式失败，不假称完成印刷排版。卡片宽度、图高、断点、IDML 坐标和 DOCX 单元格属性属于各自 adapter，不进入 ComponentSpec。source projector 必须显式提供源 H1、非空卡片组以及相邻 TIP/NOTE label/body；缺任一项即失败，不再保留 partial-list 或页面形状 fallback。

产品概览的单一语义实例是 `HB-SPECIAL-OVERVIEW` ComponentSpec：它保存 H1 无障碍标签、`front` / `right` 两个有序视图、`front_art` / `right_art` 资产角色，以及 15 个稳定 callout 的 ID、可编辑 label/body 和源引用。JE-1000F/US 的百分比 Web 坐标、固定页 IDML 坐标、16 条引线顺序、composite locale/source mapping 与 `web_replace_key` 统一登记在版本化 [`overview_component_instances.json`](../overview_component_instances.json)，不进入语义实例。新整本 IR 按实际 `(model, region)` 解析一次实例，并把实例与 SHA-256 冻结到 metadata；冷重放不再打开实例注册表。Web adapter 支持 `annotated-live` 和 `approved-composite`，但前者只是语义 fallback：对声明 finished-figure coverage 的槽位，无字底图加 HTML/SVG 文字或引线仍是 `editable-fallback` 债务，只有 locale-matched `finished-panel` / `approved-composite` 能通过最终准入。LaTeX、IDML、Word 分别消费自己的 projection；缺失、未知、目标不匹配或 hash 被篡改的实例都会失败。

`web_manual.json` 是分层入口：shared base 只放跨目标语义，skeleton profile 放同一
产品骨架复用的 Overview / Operation / App / Charging 规则，target overlay 只选骨架、
授权能力并声明差异与覆盖闸门。`JE-1000F / US` 与 `JE-1000F / EU` 共享同一
`portable-power-station-v1` 骨架，但只有自己的目标 overlay 可以启用审批图，不能从
全局 `instance_id` 或另一个目标借用几何。EU 五语的 11 个 Overview / Operation /
Charging 槽位只接受含完整文字与引线的成品整图；无字底图加 HTML 文字/引线是已登记
且已封口的历史债务，不是允许回退的最终载体。

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
