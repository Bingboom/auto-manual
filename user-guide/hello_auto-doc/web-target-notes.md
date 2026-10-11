# Workflow guide: per-target Web notes

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

### JBP-3600A 欧规英文概览与 LCD

JBP-3600A EU/en 概览使用不含标题的独立正面/侧面插图，LCD 使用带引线插图和原生两列说明；见[版面修复记录](../../code-as-doc/reviews/jbp3600a-overview-lcd-20260916.md)。

HTP011（0924）英文原稿更新使用[Git-only 结构源](../../manual_sources/JBP-3600A/EU/en/README.md)，章节参考 HTP017。开关说明、间距与锁扣标注为可选择文字，时钟从底图移除后用公共 CSS 绘制。使用原有 BP 配置构建，无需写飞书；工程 PR、本地预览验收和正式上线分别确认。见[本轮原稿及验收记录](../../code-as-doc/reviews/jbp3600a-eu-en-htp011-20261002.md)。

共用时钟可识别意大利语 `3 secondi`、德语 `3 Sekunden` 和原稿的 `Drei Sekunden`，均显示 `3s`；操作说明仍保留各语原文。

冻结稿重放时，带样式的规格章节标题也进入网页目录。锁扣标签按原稿使用深底白字，手机字号至少 14px，文字留在对应图示位置。此修正产生待审基线差异，不能自动替换已确认的英文基线。

共享移动端样式为锚点跳转预留顶栏高度；直接打开章节链接或点击目录后，完整标题显示在固定顶栏下方。

本轮八语全文及桌面/手机版式已独立验收，透明符号复用后的 EN r6、FR r5、ES r3、DE/IT/UK/PT/NL/PL r2 也已完成九语差量验收；`uk` 是乌克兰语。2026-10-03 操作者授权合入上线（MA-244），登记[新批准发布源](../../manual_sources/JBP-3600A/EU/git-20261003-44b6ce61-reviewed/README.md)，保留德语警示图文配对、意语规格/线缆/保修差异及其余已审原稿异常。旧候选和历史证据不改写。九语沿用现有发布准入，八语分别登记章节及组件适用性；PR1409 的新英语继承门禁不在当前调用链内。工程 PR、Git-only 发布 PR 和 RTD 验收分阶段核验，不写在线表或队列。

### JBP-2000B 欧规英文网页

现行 V2.0 的英文网页使用独立的
[Git 结构源与构建说明](../../manual_sources/JBP-2000B/EU/en/2.0/README.md)。
先本地验收，再按已有流程提交 Read the Docs 预览；不需要写线上多维表。

Web 提示框支持 `NOTES` 标签；纯文字 LCD 说明表隐藏无对应图标的编号和空图标列。已包含在整图中的开关文字，通过插图覆盖声明移除重复显示。

For the EU charger family, the Web illustration path resolves from the selected model and region. Charger pages retain their installation components without inheriting power-station LCD or auto-resume tables.

### FridgeGuard US 英文网页文档

JE-1000E-SIL / US / en 使用用户提供的 AI 母版，走 Git-only 冻结源；
不写飞书源表或构建回执行。仍使用 `configs/config.us-en.yaml`，构建时显式
指定冻结的 `--data-root`。源文件、命令、原稿疑点与验收结果见
[录入记录](../../code-as-doc/reviews/je1000e_sil_us_en_web_intake.md)。

Web symbol legends use warning triangles for WARNING/CAUTION; NOTE/TIP remain text-only badges, using the shared localized signal-word classification.

FCC binding is content-driven for every model and region: an exact FCC heading, `hb-source-fcc` declaration, or governed FCC source filename requires `HB-SPECIAL-FCC`. A Part 15 opening declares only a headingless orphan fragment; compact statements on mixed pages with other headings remain native source content. Whole-document source assembly rejects a missing or duplicate FCC claim; completed-IR rendering and legacy fragment rendering reject absent FCC output. The existing parser still requires the opening, localized column split, measures and modification copy. Unsupported or incomplete source structure fails with its source path; it never falls back to plain text. New targets need no model allowlist or per-model FCC configuration.

LCD icon tables use the shared `HB-TABLE-LCD-ICON` four-column component. An authored `hb-lcd-icon-table` may opt into `hb-lcd-merge-number` and `hb-lcd-merge-description`: only adjacent identical number cells, or descriptions within the same number group, merge in Web output. Keep separate semantic source rows and real icon assets; do not substitute the three-column `hb-source-lcd-legend` when the source includes an icon column.

Declare a standalone LCD on/off matrix with `hb-source-lcd-mode` on its source table to bind `HB-TABLE-LCD-MODE` without activating unrelated legacy operation tables. The source contains one artwork spanning six rows and two mode groups of three actions. Use `hb-lcd-mode-portrait` for narrow, tall device artwork; the shared component then reserves three quarters of the desktop row for the table and stacks at the existing mobile breakpoint.

For source-authored grey prose/list panels, use `figure.hb-text-panel`. It shares the existing grey rounded-panel styling and survives Web Markdown conversion. Preserve source lists rather than inventing table headers.

For a standalone App download QR, declare `img.hb-source-app-qr` followed by its adjacent text-only paragraph. It binds the existing `download-qr-only` App component for any source filename, preserving copy and the shared 9rem desktop / 6rem narrow-mobile QR size. Missing copy is rejected rather than rendered as a full-width illustration.

With store badges plus a QR in the source, declare `img.hb-source-app-download` with `data-app-download` artwork bindings for `store` and `qr`, followed by the two native copy paragraphs. It binds the existing `HB-SPECIAL-APP/download` component through public IR, without a model allowlist. Reuse the approved badges and exact source QR; missing artwork or a missing native column fails intake. Use `download-qr-only` only when the source itself has no store badges. Complete two-phone / three-phone panels reuse `hb-app-add-device-phone-art` with `hb-app-phone-pair` / `hb-app-phone-trio` display variants (22rem / 36.75rem maxima, shrinking to the available width). These shared classes retain the approved display size after finished-art replacement; plain RST width hints are otherwise normalized to the Web reading width. Keep phone borders, status/footer UI and embedded step captions intact, and inherit the same component/size choices in later locales.

To separate operation copy from artwork, an `img.hb-source-operation` can declare the existing base-art operation presentation in its `data-operation` JSON attribute, followed by the native step/supporting line block. The declaration is frozen with the Operation ComponentSpec for replay without model admission. Optional `base_art_layout.supporting_anchor` contains x/y/width percentages for separate CSS speech panels; narrow screens place their text in normal flow. Preserve the source artwork hash and exact wording.

For source-bound illustration labels, `img.hb-source-reference` with `data-reference` JSON and an adjacent line block binds the existing reference ComponentSpec and base-art renderer. Keep textless artwork out of finished-panel replacement bindings: those add finished-image attributes after source hashing. The artwork is packaged by its component asset role; its anchors and source hash remain in the IR.

Figure coverage checks resolve source-declared reference artwork hashes from the frozen page ComponentSpec before falling back to a global profile entry. Missing, duplicate or invalid declared evidence still fails; the measured hash must match the packaged artwork.

Frozen external Web manuals may retain reviewed source-specific geometry through
a hash-bound presentation sheet replayed with the document. This allows an approved
safety title, warning panel and native column split to survive the manual-center
assembly. Confirm the assembled page on desktop and mobile; a standalone preview
alone does not establish the final portal layout. See the [build guide](../../code-as-doc/build_doc_guide.md).

### FridgeGuard US native FR/ES local candidate

French and Spanish use `configs/config.us-fr.yaml` / `configs/config.us-es.yaml`, target `JE-1000E-SIL`, region `US`. Their Git-only data roots are `data/manual_sources/JE-1000E-SIL/US/<lang>/git-20261002-537939d0/phase2`; edit the corresponding `docs/templates/page_fridgeguard/<lang>/` source. Build with `build.py md --lang <lang> --data-root <data-root> --staging-root <isolated-output> --skip-root-index`. Native source discrepancies and asset reuse are recorded in [the intake review](../../code-as-doc/reviews/je1000e_sil_us_fr_es_web_intake.md). Publication resumed under the operator’s 2026-10-03 “推上去 发布” authorization; release acceptance is tracked in the intake review.

Frozen Web heading inline spans remain inside MyST titles, including the shared
`hb-sold-separately` badge; use shared `h3.hb-heading-label-pair` when the native small title and availability badge have separate capsule backgrounds. Verify both the heading and its navigation link after
assembly. Key combinations use `HB-TABLE-KEY-COMBINATIONS`, with authored button
pairs and shared hold-duration clocks. Match product markings before choosing
a shared button variant; function names alone do not establish artwork reuse.


新增 Web 底图的独立说明框必须与说明文字一起移除，由共享 CSS 绘制；复用旧图也需先检查裸底图。新冻结候选封装会检查已声明 ReferenceFigure 填充文字框区域的底图哈希和真实像素，拒绝残留的对比色空框；同色、仅轮廓或未声明框仍须视觉核验。完整面板、产品表面与 App UI 按角色保留。详见[共用取图规范](../../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)。

原稿标题条内型号使用共享 `hb-heading-model`，整行图标警告使用
`HB-CALLOUT-STRIP/warning` 的 `hb-source-warning-lockup` 声明；图内说明通过
ReferenceFigure 源坐标保留在图内，不能移为图后段落。具体样式声明见
[原稿标题型号与完整警告框](../../docs/renderers/contracts/STYLE_DEFINITION.md#原稿标题型号与完整警告框)。

PACKAGE LIST 的配件名称与 “Sold separately” 应为可编辑网页文字，分组外框及标签框由共享 CSS 绘制。使用现有匹配配件图和通用文档图标；新语言沿用同一套图片，只替换原稿标签。退役整图不可再次绑定，缩略封面细节的省略须在原稿覆盖记录中说明。

原稿里单独成行的深色圆角提示应保留为可选取的独立正文段落，使用共享 `hb-prose-pill`，不要拼入前段或转换为标题。

原稿放在图内的说明，应保留在图内；桌面沿用原稿位置，手机可在同一灰色图框内排为可读说明，不能重复放在图外。

FCC Web 正文左右高度明显失衡时，可在现有 FCC 组件外声明共享 `hb-fcc-balanced-flow` 容器。桌面使用自动平衡的两栏文字流，FCC 标志左浮动并允许文字在其下方续排；手机回到单栏。DOM 保持开场、NOTE 正文、措施列表和 MODIFICATION 的原文顺序；不改 ComponentSpec 的印刷分栏点，也不按机型复制 renderer。

JA-AD600A/EU 英文的五张说明图已分离需要翻译的文字，采用共用底图加原生标签；尺寸、单位、固定铭刻和 A–F 对应编号保留。各语替换文字时复用同一底图，详见[共用底图复核](../../docs/renderers/contracts/STYLE_DEFINITION.md#ja-ad600a-eu-共用底图复核)。

JBP-3600A EU 九语的正视图、左视图采用同一显示尺寸上限（25rem、34rem），保留各语图片原稿和比例，窄屏内按可用宽度缩放。

新鲜冻结 Web 的符号准入仍逐行核对原稿哈希、字形、透明边缘、共享资产和说明像素。原稿中的换行断词可在 `symbol_asset_admission.locales.<lang>` 对应行声明 `caption_linebreak_joins`（例如 `independiente-\nmente`）；每个声明必须匹配说明矩形内一次精确的字母断词，仅合并该处换行，不能忽略行内连字符或其他文字差异。JE-3600A 批次 1465 的西语与意语修订见[修订验证记录](../../code-as-doc/reviews/je3600a_eu_1465_web_backport.md)。


SlimPower H1（JE-1000E-WH / JP / ja）使用[批准的日文冻结源](../../manual_sources/JE-1000E-WH/JP/ja/git-20261008-efb663e3-no-cover-reviewed/README.md)，保留原候选与原稿文字、图框和安全符号。按操作者“封面 不要放进去网页版里面啊”，新 Web 版本从安全说明开始，印刷封面仅保留在原稿与来源存档；其余 16 章逐字节保持。`approval.json` 绑定原稿哈希、已审候选及独立章节/组件要求；回放前先验证批准身份，再通过共享 Manual IR / ComponentSpec 输出。日规沿用现有区域准入，不登记 phase2 或提升全局资产。正式发布仍按 Git-only 单语凭据、Hello-Docs 生成式发布 PR、RTD 回执/资源和桌面手机逐段核验，打印版本未知时保持未知。

JBP-1000B-WH / JP / ja 的 [Web 版式版本](../../manual_sources/JBP-1000B-WH/JP/ja/git-20261009-3aa6c003-web-layout/README.md) 由包内 `derive_web_layout.py` 从已批准原生包机械派生，原生包与其发布凭据保持不变。按操作者“全部修，一次做完”“封面和目录 不用体现在web版面上”并参照 JE-1000F 日文 Web：导航与印刷目录 12 章一致，二级内容不再升为章，原稿并排的安装步骤合为整行图（跨面板插图完整），标签字号按原稿 pt 与面板宽度生成；日文措辞与 `*_text` 字段不变，由单元测试比对可见文字。操作者于 2026-10-09 审阅对比图后指示“上线提交发布”，`approval.json` 绑定全部 `source/` 输入哈希；工程 PR 由操作者审核合入，合入后在实际 main 提交上封存 Git-only 发布证据并提交 Hello-Docs 发布 PR。

JA-AD500A-SIL / JP / ja（Jackery DC Input Module）的 [Web 版式候选](../../manual_sources/JA-AD500A-SIL/JP/ja/git-20261009-ac3a1f82-web-layout/README.md) 由包内 `derive_web_layout.py` 从已批准包 `git-20261008-ac3a1f82-reviewed`（MA-272）机械派生，已批准包与其发布凭据保持不变。沿用 JBP-1000B-WH JP 的规则：印刷封面标识行不进入 Web，页面从「お買い上げありがとうございます。」开始，导航即印刷的五个章节条；粗体、原稿换行、灰色面板与胶囊由页面局部 `source/presentation.css`（IR `source_stylesheet`）和 RST 标记实现，共享组件与共享 CSS 不改；同梱品说明书插图由共享资产管线重裁补全右边框，其余插图逐字节不变。日文措辞不变，由单元测试证明可见文字（含顺序）= 批准文字 − 封面行。操作者确认以仓库这份 PDF 为准、欢迎语保留、不加图标，审阅逐页对照后于 2026-10-09 指示“上线提交发布”；`approval.json` 绑定全部 `source/` 与 `assets/` 输入哈希。工程 PR 由操作者审核合入，合入后在实际 main 提交上封存 Git-only 发布证据并提交 Hello-Docs 发布 PR。

JHP-5000C / US（英、法、西）的 [Web 版式候选](../../data/manual_sources/JHP-5000C/US/git-20261010-051169dd-web-layout/README.md) 由包内 `derive_web_layout.py` 从已批准包 `git-20261009-051169dd`（MA-279）机械派生，已批准包与其发布凭据保持不变。按操作者“继续调一下 这个的版面”并三语一起改，沿用 JBP-1000B-WH JP 的规则：印刷封面与目录不进入 Web，三语导航均为印刷目录的 14 章。安全须知复用线上模板手册（如 JE-1000E-SIL）已发布的双栏结构：`hb-safety-instruction` 风险横幅、左栏顶部的 `hb-safety-lead` WARNING 引导框和按印刷分栏的 `manual-two-col-table`，样式全部来自共享 `web_safety_components.css`；DANGER 图文组合与胶囊标题复用共享三角符号；信号词表、LCD 图标表、LCD SCREEN 表、故障码、编号注意、保修段落、逐行规格值、® 位置、误吞警示与封底联系卡均按原稿重建。法语、西语中几何与英语不同的插图改用本语种页面的原稿面板，每种语言的 Web 只携带本语种引用的图稿。可见文字 = 批准文字 + 逐条登记的原稿恢复（英 9、法 9、西 16，见包内 `source/differences.md`），由单元测试证明；原稿自身的错语种与错拼按印刷保留并列出。操作者于 2026-10-10 审阅三语逐章对照（印刷页、电脑网页、手机）后指示“上线提交发布”，并要求安全须知改为线上现成的双栏版式（已复用，不另写样式），审阅渲染后确认“提交发布”；`approval.json` 绑定除 `web/` 外全部包内输入哈希；工程 PR 由操作者审核合入，合入后在实际 main 提交上逐语封存 Git-only 发布证据并提交 Hello-Docs 发布 PR。

台湾原生 Git-only Web 原稿使用 `zh-TW`（别名 `zh_tw` / `zh-Hant`），显示为繁體中文。共享语言注册将它设为 `sync_enabled=False`，与简体 `zh` 分开；离线整本 Manual IR 回放不会新增在线同步字段。
