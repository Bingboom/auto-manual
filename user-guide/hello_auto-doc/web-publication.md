# Workflow guide: Web publication contract

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

外部冻结稿的符号表在封存前自动核对真实透明度和权威 PDF 的原始图形。
共用文件名、符号含义一致或文件有 alpha 通道，都不能代替准入；转曲说明仍需逐行视觉核对。
字段和边界见 [Web 素材规则](../../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)。

说明书工作台首页优先展示生产概览、资产引用、回流复用缺口与交付风险。使用“口径与证据”查看来源时间、去重和对象；活动尚未记录不能读作 0。Word/印刷包链接仍在交付矩阵，操作导航移至“工作入口、系统健康与架构”，运行失败和待处理任务入口保留在首页。参考 [工作台统计契约](../../code-as-doc/dev/workspace_production_evidence.md)。

网页备注若出现双层项目符号，应核对冻结源中的表格结构；若出现深底深字，应同时核对引用块背景和文字颜色。修复后须分别检查桌面、窄屏与深色主题；本地预览不代表 RTD 已发布。
This file replaces `Template_maintenance_and_using_guide.md`.
It documents the current build layout, maintenance rules, the review bundle layer under [`docs/_review/<model>/<region>/`](../../docs/_review), and the current review-first publishing flow.
It is the current workflow and editing-surface guide.
It is not the full maintainer command reference; use [`../code-as-doc/build_doc_guide.md`](../../code-as-doc/build_doc_guide.md) for command semantics.

## Web 发布现行契约

本节收拢历次发布改动累积下来的现行约定。单个型号的一次性修复记录不进本节，放文末的型号专项或 [`code-as-doc/reviews/`](../../code-as-doc/reviews)。

### 网页配图先复用，再提取

每次网页化先盘点目标已有素材、同型号同区域其他语言素材与共享附件，核对图中
型号、接口、参数、App 界面和语言。内容一致就直接复用；只有外部文字变化时，
复用底图并调整原生标签。新增语言或新 PDF 不构成重裁理由。

确实缺图、清晰度不足或图形有差异时，先在目标审查记录填写
[选材记录表](../../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)，
说明查过什么以及为何不能复用，再提取。完整大图保留灰底、圆角、外框和引线；
App 截图保留手机顶部状态栏及四边。透明底要求只用于 LCD／状态图标、独立按钮符号等小图，
不按显示尺寸判断；完整大图缩小显示也不去底。

交付时核对实际绑定文件的来源与哈希，并检查桌面、手机中的裁切、标签位置及重复
编号。上述是执行和审查顺序，尚不代表构建程序会自动发现裁切或去底错误。

### 单语身份、语言切换与手册中心

单语网页顶部通过语言切换栏显示当前语言，正文开头重复的独立语言名称不再显示；冻结源文件不变。

手册中心卡片可按型号/市场指定说明书原图，补齐缺图或替换带编号边框的装箱图；参见[目录缩略图](../../code-as-doc/dev/rtd_manual_portal.md#accessory-catalog-artwork-2026-09-15)。

手册中心首页按“用电需求”分组：随身供电、通用电器供电、可扩容储能、专用场景备电，配套产品单独一栏，并随所选区域隐藏没有说明书的分组。归类是产品定位，维护在 `tools/rtd_portal_assets/settings.json` 的 `navigation` 表里；新上线的型号如果没写进表，会先显示在“其他说明书”，把它加到对应分组即可。能力比较和兼容查询要等有确认过的数据表再加。规则见[手册中心说明](../../code-as-doc/dev/rtd_manual_portal.md)。

手册中心会将同型号/市场的多语发布分组为一张卡；旧出版物的单语身份未验证不等于没有该语言，参见[语言切换规则](../../code-as-doc/dev/rtd_locale_navigation.md)。合并多语言 Web 文档不再在开头生成语言胶囊条，语言统一用手册中心的下拉框切换。
未发布语言禁用；旧混语手册保留“当前发布版”，不标成已经完成的单语翻译。
手册中心支持 US/EU/UK/CN/JP 区域筛选，默认仍为 EU；中规、日规独立筛选，中文和日文分别显示“简体中文”“日本語”。只有冻结清单中已经发布且具有相应身份凭据的语言页面才能启用。现有 `cn-zh` / `jp-ja` 整本家族的 Web Publish 任务应将 `Lang` 留空，由家族固定为中文／日文；不要套用欧规单语家族的显式 `Lang` 填法。

知识库侧栏的“系统建设”页（`/workspace/system/`）先列“当前重点”：先完成网页发布与维护闭环；语料复用与 SSOT 同期支撑，再做 IR 代表试点、骨架与覆盖扩展，多 Agent 按需后置。每条线的数字取自发布清单、语料快照和骨架定义，进度取自执行台账。下面先看阶段门验收，再看语言资产、能力地图和生产流程连接。各项状态写在 `tools/rtd_portal_assets/system_workspace.yaml`，每条都要附证据；当前重点由操作者决定，改动时一并更新。修改该文件走 auto-manual PR，提交前运行 `python -m tools.rtd.system_workspace check`。页面公开可见，只写可公开的内容。页内“语言资产”块只展示翻译记忆库的汇总计数，不含语料原文；语料批次完成后使用 Workspace Data Refresh 刷新；已接入的本机 TM 写回批次可用包装器自动触发，见 [数据持续更新与补刷](../../code-as-doc/dev/workspace_data_refresh.md)。快照会保留往月的汇总数，页面显示与上期的对比。图中各语言的百分比是语料库句对覆盖（该语言有译文的句对占记忆库全部句对的比例），不是说明书翻译完成率。页内“技能与钩子”列出 Agent 可调用的技能和自动运行的钩子，未登记的技能和没有测试的钩子会标出来；新增技能时记得在 AGENTS.md（Codex）或 `.claude/skills/README.md`（Claude）登记。页面底部的“数据来源”表列出每类数字以哪里为准、多少天算过期、取不到时显示什么，这些统一登记在 `tools/rtd_portal_assets/source_registry.yaml`；新增数据来源或改过期天数，只改这一个文件。规则见[系统建设页](../../code-as-doc/dev/rtd_manual_portal.md#system-workspace-page)。

“系统架构”标签（`/workspace/system/#tab-architecture`）展示人的入口、AI 能力入口与企业数据入口，围绕同一套可信内容和文档生产体系。现有多维表展示产品信息、内容模块、规格参数、多语言内容及业务维护与评审，经数据校验与快照进入 auto-manual；系统共用多维表、Git 原稿和批准素材，以及 Shared IR（共享底稿）与样式组件，支持文档生产、专业文件处理和内容查询。内容权威、组装、渲染与发布是其中的文档生产链路。MCP 与 PLM／ERP 同步及字段映射接入用虚线及“未来方向”标注；当前 Agent／Bot 单独列出。MCP 仅作为规划中的协议适配层，正式图稿修改保留人工批准。Shared IR（共享底稿）的 Web 整本与样式复用已有基础，机读语料目前仍从已发布 HTML 派生；已有基础按现有文件预翻译、AI 图稿与页码处理、PDF 标注、回写及构建技能列出，钩子标明触发与启用条件。架构视图也读取原有演进史摘要，不另建台账。

“当前工作”标签（原“建设进度”，链接仍为 `/workspace/system/#tab-progress`）集中显示
当前重点、完成数量、台账进度和下一步安排；进度数字随该标签显示。
“系统演变”标签记录历史阶段与变化原因，再接续未排期的长期方向，不重复展示当前状态概览。
持续维护与重构单独显示为
贯穿全过程的横向路标，保留多轮历史记录。可展开查看阶段与路标的变化、原则和
依据，直接链接为 `/workspace/system/#tab-evolution`。正式记录及页面摘要共同维护在
[系统演进史](../../code-as-doc/architecture/system_evolution_history.md)，随工程 PR、镜像
和 RTD 构建更新。历史数字附观察日期；“持续开展”表示已有基础并继续维护改进，“建设中”和“未来方向”不算已验收能力。当前最成熟的是 Web 文档链条，IDML 印刷版仍按试生产展示。
“开始建设可复用的样式组件”记录早期起点；“Shared IR（共享底稿）：Web 整本复用”记录已实现的 Web 整本复用及持续完善，Shared IR（共享底稿）扩展到更多格式仍是后续扩展。“积累审核经验，支持后续编写”独立列项，具体试点和执行安排仍需确定。
修改记录后先通过系统建设页检查，再核对桌面／手机版面；发布后另核验线上版本。
页面里的时间轴、阶段、经过说明和确认日期统一显示到月；记录更新、数据快照、复核和构建时间保留原有精度。


系统建设页随 auto-manual/main 合入，经 Hello-Docs 镜像同步和 RTD 成功构建后更新。在“入口与数据来源”内展开“页面版本与更新”，可查看本次站点构建的提交版本与时间；页首和演变引言只保留主要内容。已打开的页面每分钟及重新切回时检查已发布版本，发现更新可点“刷新到新版本”，阅读中不会强制跳页。同步或构建失败时仍显示旧快照，不代表 main 已上线。语料等飞书数据仍需按原流程导出、审核并提交快照，页面刷新不会读取活表。

侧栏的“设计系统”（`/workspace/design/`）汇总说明书网页版的颜色、字体和组件，以及“图标与素材”和“印刷规格”两个分页：数值和组件预览在每次 RTD 构建时直接读取仓库当前的 `web_manual.css`，素材从共享素材目录和清单列出，印刷规格读 `data/layout_params.csv`；样式、素材或参数改动合入并发布后页面自动更新。说明文字维护在 `tools/rtd_portal_assets/design_system/`。

侧栏的“说明书工作台”（`/workspace/deliverables/`，沿用原交付物地址）从“结构化数据 + 模板与骨架”进入构建和多格式输出。点击地图节点，可找到飞书业务源表、语料库、资产、模板骨架、构建记录与对应操作指引；飞书入口需登录并具备权限，点击工作台入口本身不会触发构建。首页先提供常用工作入口，再用交付总量、交付入口条形图和三类资产关系图呈现重点；生产投入与回流再利用简要显示状态及入口。完整工作地图、交付矩阵和统计证据默认折叠，点击对应入口展开。资产部分按语料库、样式库、模板与骨架提供数量、维护入口和采用情况；登记量与配置引用不能当作成品使用量，缺少记录时明确标注。随后保留各型号的网页手册、印刷交付包（IDML + PDF）和 Word 云文档矩阵，按型号分组、每个区域一行，可以按型号、区域筛选，手机端可横向滚动。网页手册的链接随发布自动更新；印刷交付包和 Word 云文档的链接来自飞书文档构建表的快照，Word／印刷包交付写回并读回成功后，队列每批刷新一次并创建内容 PR。审核合入后还须完成 Workspace Data Verify，才能确认线上更新；补做统一使用 Workspace Data Refresh。飞书链接要登录飞书才能打开，但链接地址在公开页上可见。规则见[交付物页](../../code-as-doc/dev/rtd_manual_portal.md#deliverables-page)。

### 发布候选、撤回与恢复

Web 发布候选按型号/市场/语言隔离，并保留旧链接重定向，见[契约](../../code-as-doc/dev/web_locale_publication_identity.md)。
组装资源池同时处理图片和 Markdown 内嵌 CSS 的 `url(...)` 引用，保留背景图、遮罩图的原始字节及逻辑资产身份。视觉检查须覆盖这些 CSS 图形；图片元素全部加载不代表全部资源已加载，正式上线仍以冻结资源回执核验为准。
冻结发布源同时保留独立源包与整站组装副本，源清单容量上限为 768 MiB；网页输出及线上取回仍限 512 MiB，单文件 32 MiB、文件数 10,000 和哈希校验不变。发布前的整站 Sphinx 检查须加载 `myst_parser,tools.rtd.portal`，同时验证知识导出和部署凭据生成。

已有外部原稿的 Git-only 新语种网页发布，也要把每种语言标为 `single`，用冻结源清单与实际 Git 提交、MyST、图片和验证 HTML 生成[单语发布凭据](../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction)；现有 `build.py check` 只作旧构建目标的回归检查，不代表验证了这些新语正文。
原稿章节与历史 phase2 稿不同的，按原稿 SHA-256 登记独立的共享组件准入映射；仍须逐语核对原文、共用底图与桌面／手机页面。原稿中的语言混用保留并记录勘误，不自行翻译补齐。

JE-1000F/EU 新增四语从提供的可编辑 PDF 重新读取文字，以原 AI 核对缺字，保留已批准勘误。维护时通过[共享 IR 接入工具](../../code-as-doc/dev/four_language_shared_ir_alignment.md)生成新候选包，采用英文网页的公共包装清单、总览、操作、App 和表格组件；正文不放印刷目录或表格截图。太阳能接线图中的型号/数量标注和车充图中的车辆标注保持为图框内可选中的文字，不能作为图外正文；桌面按原稿留白定位，窄屏在同一灰色图框内保持可读。配图须匹配原稿中的型号、插座和参数，资产清单未解决的项会阻止生成候选；历史 `build_web.py` 和截图保留作追溯证据。该步骤生成本地候选，尚需工程 PR、发布 PR 和 RTD 验收，不会自动发布，也不等于完成飞书语料入库或印刷产线注册。

JE-2000F/E 与上述候选共用 `manual-ir/v2`、ComponentSpec 和 Web 渲染器；各型号、语种的章节、图文、表格和 App 控件位置由[目标本地布局与原稿证据](../../code-as-doc/dev/je2000_eu_new_locales_ir_adapters_2026-09.md)绑定。候选 `manual.ir.json` 若记录未完成的 `pending_source_review`，Web 发布证据封装会拒绝它；待原稿勘误获批并清空待审项后才能进入正式发布。复用前言须在绑定及每段文字中保留操作人批准记录，获批后重建才会去掉待审提示；这不等同于 PR 合入或 RTD 上线。 操作图的文字锚点须对照各型号、语种自身原稿校准，并核验引线、圆圈和前提提示框完整；图下说明不能影响图内文字定位。
Git-only [撤回与恢复](../../code-as-doc/dev/web_publication_withdrawal.md) 必须指定型号/市场/语言/版本、原因、负责人和恢复快照；
缺少输入不会删除已发布手册，已撤回版本不能由普通发布重试重新进入目录。操作先验证本地候选，再走发布 PR 和实际部署回执。
旧记录的语言字段不等于正文单语；门户分组已有工程支持，真实多语上线仍须完成内容与 RTD 验收。

### 语言投影与发布凭据

Web profile 配合显式 `--lang` 现在会[冻结完整配置语言源并生成规范单语投影](../../code-as-doc/dev/web_language_projection.md)：
`check`、Markdown 和 HTML 使用同一份所选语言 RST。显式语言的 Web 队列构建还会
[核对并封存三步凭据](../../code-as-doc/dev/web_language_release_evidence.md)，绑定型号、市场、
语言、版本、Git_ref 及 Markdown/HTML 产物；凭据缺失或内容变化会阻止该版本被接受为单语发布。
共享配置选法语时，版本目录也使用法语，不落到配置的第一个语言下。旧的不可变版本不补写凭据，
需重新构建新版本。工作流、线上表、审稿源不变；凭据通过不等于翻译正确或已经在 RTD 上线。
发布组装会原样保留已生成的 `manual.ir.json` 和 `manual_bundle.html`，不再遗漏凭据中
记录的辅助文件；旧版本没有这些文件时仍可组装。未知文件不会被静默加入或从校验中排除。

### 发布健康、反馈与统计

Web 冻结产物可使用[只读健康报告](../../code-as-doc/dev/manual_operations_health_report.md)
检查本地页面/资源。该报告不会访问线上表、确认部署或收集访客数据。
需要探测已发布链接时使用[线上HTTP检查](../../code-as-doc/dev/manual_operations_online_health.md)；
它只读冻结目录并发起有上限的HEAD请求，不把200响应当作版本发布确认。

夏冰（GitHub `Bingboom`）负责发布健康与手册反馈，每次发布后检查本地资源、
线上可访问性和实际部署版本。已验证单语页面提供售后邮箱 `hello@jackery.com`
入口（出货手册已印的官方地址）和可复制的型号/市场/语言/版本/页面上下文；
读者自行提交问题，页面不会自动发送。GitHub Issues 转为内部/经销商分诊渠道。
处理流程见[手册中心说明](../../code-as-doc/dev/rtd_manual_portal.md)。首次响应 3 个工作日内，
不创建定时任务或常驻服务。访问统计经无 cookie 的 Cloudflare Web Analytics 采集（2026-09-15 起启用，
站点 `ht-doc.readthedocs.io`；令牌是公开站点标识非密钥），不采集访客身份；
清空 `analytics_beacon_token` 即完全关闭、页面回到字节等同。

### 页面元数据与对外链接

已验证单语页面的 `<title>`、描述、canonical、hreflang、OG 元数据全部由冻结发布身份
构建期派生（不许手填）；换域名时只改 portal 设置里的 `site_base_url` 一处。
根别名是可计数的印刷/QR 入口层：构建期自动加 noindex 与指向嵌套规范页的 canonical，
统计开启时转发前留出 beacon 发送窗口（约 0.2–2.5 秒）。对外链接规范：印刷/QR 用根别名，
`HTML_link` 登记与站内导航用嵌套规范页，市场/客服签名用门户首页，不发第四种链接。

### 产线盘活与入口整合

后续发布入口整合及中长期工作见[产线盘活与演进方案](../../code-as-doc/manual_production_revitalization_plan.md)。
后续每次执行先读[执行台账](../../code-as-doc/dev/manual_revitalization_execution.md)，按依赖领取 REV-ID，结束时回写证据及下一步；台账尚未接入自动调度。
本轮先复核新旧站点和历史链接，具体检查见[入口整合要求](../../code-as-doc/dev/web_publish_pipeline.md#31-hosting-convergence-and-legacy-entry-review)。
保留已有 D1–D4 决策；方案登记不表示已迁移、已开通月报或已获在线写入授权。
停止旧站独立更新与保留 `publish` 候选分支可以同时成立；历史版本链接不静默改指最新版。

### 插图、成品图与 IR 包

Web inserts finished illustrations with their embedded text; IDML's textless
variants remain separate. Packaging lists retain the shared `HB-SPECIAL-INBOX`
component, including live numbers, labels and notes. Only explicitly matched
annotations already embedded in a finished figure disappear from the visual
page; explanatory copy remains live. Every new Web `manual.ir.json` also reports
Overview, Operation and Charging coverage under
`metadata.web_figure_coverage`, so finished panels, approved composites,
editable fallbacks and missing artwork are reviewable without inspecting two
manifest formats separately. The local fixture preview is not a published or
content-approved manual; source/PDF differences are tracked in that record.
New whole-document Web packages use `manual-ir/v2` neutral flow/rich-text nodes;
historical `manual-ir/v1` packages remain replayable. Eighteen ComponentSpec types
are embedded, including Operation, Auto Resume, Key Combinations, LCD Mode, the three Warranty shapes, LCD
Icons, Troubleshooting, both Symbols tables, App and governed Reference Figures.
The package freezes the component registry, theme, target presentation contract
and resolved Overview instance; cold replay does not read RST/CSV or rerun the
old DOM projector. Representative-package tests project every embedded instance
through the registered Web, LaTeX, IDML and Word adapters. This is shared semantic
and adapter-entry proof; responsive Web and fixed-page outputs still own different
geometry and are not expected to be pixel- or pagination-identical.
For JE-1000F, Overview, Operation and Charging use localized crops with their
visible labels and leader lines intact—including Operation `On` / `Off`,
prerequisites and action copy. Do not feed those slots textless exports. In every
locale, including EU Italian, “textless base art + localized HTML/SVG text or
leader lines” is `editable-fallback` debt; only locale-matched `finished-panel`
or `approved-composite` artwork can close it. EU Italian is currently 11/11
approved full panels. The LCD screen-mode block is the exception: keep only the
market-correct product/display artwork as an image and render its six-row
explanation table in HTML.
The one other exception is contract-granted, not a fallback: all five
JE-1000F/US Operation figures (main power, AC output, DC/USB output, energy
saving, LED light) and its Charging car figure (EN/FR/ES) use
`base-art-live-copy`, the frozen text-free art with the source copy as live HTML
on anchors measured for that exact art hash.
Changing that art (for example
approving the textless AC candidate) stops the Web build until the anchors are
re-measured and the hash updated; copy changes still go through the source
templates. See
[`je1000f_us_base_art_web.md`](../../code-as-doc/dev/je1000f_us_base_art_web.md).
