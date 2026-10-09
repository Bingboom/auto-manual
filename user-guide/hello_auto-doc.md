# Hello Auto Doc


外部冻结稿的符号表在封存前自动核对真实透明度和权威 PDF 的原始图形。
共用文件名、符号含义一致或文件有 alpha 通道，都不能代替准入；转曲说明仍需逐行视觉核对。
字段和边界见 [Web 素材规则](../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)。

说明书工作台首页优先展示生产概览、资产引用、回流复用缺口与交付风险。使用“口径与证据”查看来源时间、去重和对象；活动尚未记录不能读作 0。Word/印刷包链接仍在交付矩阵，操作导航移至“工作入口、系统健康与架构”，运行失败和待处理任务入口保留在首页。参考 [工作台统计契约](../code-as-doc/dev/workspace_production_evidence.md)。

网页备注若出现双层项目符号，应核对冻结源中的表格结构；若出现深底深字，应同时核对引用块背景和文字颜色。修复后须分别检查桌面、窄屏与深色主题；本地预览不代表 RTD 已发布。
This file replaces `Template_maintenance_and_using_guide.md`.
It documents the current build layout, maintenance rules, the review bundle layer under [`docs/_review/<model>/<region>/`](../docs/_review), and the current review-first publishing flow.
It is the current workflow and editing-surface guide.
It is not the full maintainer command reference; use [`../code-as-doc/build_doc_guide.md`](../code-as-doc/build_doc_guide.md) for command semantics.

Updated: 2026-09-20

### Where to look next

For the current JP / US family difference boundary, use [`../code-as-doc/manual_family_guide.md`](../code-as-doc/manual_family_guide.md).
For the complete IR → Web build/replay acceptance target, including JBP-2000B
Japanese PDF illustrations, see [`ir_document_closeout.md`](../code-as-doc/dev/ir_document_closeout.md).
For onboarding new external Markdown manuals into templates, use [`../code-as-doc/dev/manual_template_intake_checklist.md`](../code-as-doc/dev/manual_template_intake_checklist.md).
For Codex-assisted Markdown-to-template intake, use [`../.agents/skills/markdown-rst-template-intake/SKILL.md`](../.agents/skills/markdown-rst-template-intake/SKILL.md).
For Codex-assisted TM-first manual rewrite or translation that must preserve Markdown structure, use [`../.agents/skills/manual-rewrite-with-tm/SKILL.md`](../.agents/skills/manual-rewrite-with-tm/SKILL.md).

---

## Web 发布现行契约

本节收拢历次发布改动累积下来的现行约定。单个型号的一次性修复记录不进本节，放文末的型号专项或 [`code-as-doc/reviews/`](../code-as-doc/reviews)。

### 网页配图先复用，再提取

每次网页化先盘点目标已有素材、同型号同区域其他语言素材与共享附件，核对图中
型号、接口、参数、App 界面和语言。内容一致就直接复用；只有外部文字变化时，
复用底图并调整原生标签。新增语言或新 PDF 不构成重裁理由。

确实缺图、清晰度不足或图形有差异时，先在目标审查记录填写
[选材记录表](../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)，
说明查过什么以及为何不能复用，再提取。完整大图保留灰底、圆角、外框和引线；
App 截图保留手机顶部状态栏及四边。透明底要求只用于 LCD／状态图标、独立按钮符号等小图，
不按显示尺寸判断；完整大图缩小显示也不去底。

交付时核对实际绑定文件的来源与哈希，并检查桌面、手机中的裁切、标签位置及重复
编号。上述是执行和审查顺序，尚不代表构建程序会自动发现裁切或去底错误。

### 单语身份、语言切换与手册中心

单语网页顶部通过语言切换栏显示当前语言，正文开头重复的独立语言名称不再显示；冻结源文件不变。

手册中心卡片可按型号/市场指定说明书原图，补齐缺图或替换带编号边框的装箱图；参见[目录缩略图](../code-as-doc/dev/rtd_manual_portal.md#accessory-catalog-artwork-2026-09-15)。

手册中心首页按“用电需求”分组：随身供电、通用电器供电、可扩容储能、专用场景备电，配套产品单独一栏，并随所选区域隐藏没有说明书的分组。归类是产品定位，维护在 `tools/rtd_portal_assets/settings.json` 的 `navigation` 表里；新上线的型号如果没写进表，会先显示在“其他说明书”，把它加到对应分组即可。能力比较和兼容查询要等有确认过的数据表再加。规则见[手册中心说明](../code-as-doc/dev/rtd_manual_portal.md)。

手册中心会将同型号/市场的多语发布分组为一张卡；旧出版物的单语身份未验证不等于没有该语言，参见[语言切换规则](../code-as-doc/dev/rtd_locale_navigation.md)。
未发布语言禁用；旧混语手册保留“当前发布版”，不标成已经完成的单语翻译。
手册中心支持 US/EU/UK/CN/JP 区域筛选，默认仍为 EU；中规、日规独立筛选，中文和日文分别显示“简体中文”“日本語”。只有冻结清单中已经发布且具有相应身份凭据的语言页面才能启用。现有 `cn-zh` / `jp-ja` 整本家族的 Web Publish 任务应将 `Lang` 留空，由家族固定为中文／日文；不要套用欧规单语家族的显式 `Lang` 填法。

知识库侧栏的“系统建设”页（`/workspace/system/`）先列“当前重点”：先完成网页发布与维护闭环；语料复用与 SSOT 同期支撑，再做 IR 代表试点、骨架与覆盖扩展，多 Agent 按需后置。每条线的数字取自发布清单、语料快照和骨架定义，进度取自执行台账。下面先看阶段门验收，再看语言资产、能力地图和生产流程连接。各项状态写在 `tools/rtd_portal_assets/system_workspace.yaml`，每条都要附证据；当前重点由操作者决定，改动时一并更新。修改该文件走 auto-manual PR，提交前运行 `python -m tools.rtd.system_workspace check`。页面公开可见，只写可公开的内容。页内“语言资产”块只展示翻译记忆库的汇总计数，不含语料原文；语料批次完成后使用 Workspace Data Refresh 刷新；已接入的本机 TM 写回批次可用包装器自动触发，见 [数据持续更新与补刷](../code-as-doc/dev/workspace_data_refresh.md)。快照会保留往月的汇总数，页面显示与上期的对比。图中各语言的百分比是语料库句对覆盖（该语言有译文的句对占记忆库全部句对的比例），不是说明书翻译完成率。页内“技能与钩子”列出 Agent 可调用的技能和自动运行的钩子，未登记的技能和没有测试的钩子会标出来；新增技能时记得在 AGENTS.md（Codex）或 `.claude/skills/README.md`（Claude）登记。页面底部的“数据来源”表列出每类数字以哪里为准、多少天算过期、取不到时显示什么，这些统一登记在 `tools/rtd_portal_assets/source_registry.yaml`；新增数据来源或改过期天数，只改这一个文件。规则见[系统建设页](../code-as-doc/dev/rtd_manual_portal.md#system-workspace-page)。

“系统架构”标签（`/workspace/system/#tab-architecture`）展示人的入口、AI 能力入口与企业数据入口，围绕同一套可信内容和文档生产体系。现有多维表展示产品信息、内容模块、规格参数、多语言内容及业务维护与评审，经数据校验与快照进入 auto-manual；系统共用多维表、Git 原稿和批准素材，以及 Shared IR（共享底稿）与样式组件，支持文档生产、专业文件处理和内容查询。内容权威、组装、渲染与发布是其中的文档生产链路。MCP 与 PLM／ERP 同步及字段映射接入用虚线及“未来方向”标注；当前 Agent／Bot 单独列出。MCP 仅作为规划中的协议适配层，正式图稿修改保留人工批准。Shared IR（共享底稿）的 Web 整本与样式复用已有基础，机读语料目前仍从已发布 HTML 派生；已有基础按现有文件预翻译、AI 图稿与页码处理、PDF 标注、回写及构建技能列出，钩子标明触发与启用条件。架构视图也读取原有演进史摘要，不另建台账。

“当前工作”标签（原“建设进度”，链接仍为 `/workspace/system/#tab-progress`）集中显示
当前重点、完成数量、台账进度和下一步安排；进度数字随该标签显示。
“系统演变”标签记录历史阶段与变化原因，再接续未排期的长期方向，不重复展示当前状态概览。
持续维护与重构单独显示为
贯穿全过程的横向路标，保留多轮历史记录。可展开查看阶段与路标的变化、原则和
依据，直接链接为 `/workspace/system/#tab-evolution`。正式记录及页面摘要共同维护在
[系统演进史](../code-as-doc/architecture/system_evolution_history.md)，随工程 PR、镜像
和 RTD 构建更新。历史数字附观察日期；“持续开展”表示已有基础并继续维护改进，“建设中”和“未来方向”不算已验收能力。当前最成熟的是 Web 文档链条，IDML 印刷版仍按试生产展示。
“开始建设可复用的样式组件”记录早期起点；“Shared IR（共享底稿）：Web 整本复用”记录已实现的 Web 整本复用及持续完善，Shared IR（共享底稿）扩展到更多格式仍是后续扩展。“积累审核经验，支持后续编写”独立列项，具体试点和执行安排仍需确定。
修改记录后先通过系统建设页检查，再核对桌面／手机版面；发布后另核验线上版本。
页面里的时间轴、阶段、经过说明和确认日期统一显示到月；记录更新、数据快照、复核和构建时间保留原有精度。


系统建设页随 auto-manual/main 合入，经 Hello-Docs 镜像同步和 RTD 成功构建后更新。在“入口与数据来源”内展开“页面版本与更新”，可查看本次站点构建的提交版本与时间；页首和演变引言只保留主要内容。已打开的页面每分钟及重新切回时检查已发布版本，发现更新可点“刷新到新版本”，阅读中不会强制跳页。同步或构建失败时仍显示旧快照，不代表 main 已上线。语料等飞书数据仍需按原流程导出、审核并提交快照，页面刷新不会读取活表。

侧栏的“说明书工作台”（`/workspace/deliverables/`，沿用原交付物地址）从“结构化数据 + 模板与骨架”进入构建和多格式输出。点击地图节点，可找到飞书业务源表、语料库、资产、模板骨架、构建记录与对应操作指引；飞书入口需登录并具备权限，点击工作台入口本身不会触发构建。首页先提供常用工作入口，再用交付总量、交付入口条形图和三类资产关系图呈现重点；生产投入与回流再利用简要显示状态及入口。完整工作地图、交付矩阵和统计证据默认折叠，点击对应入口展开。资产部分按语料库、样式库、模板与骨架提供数量、维护入口和采用情况；登记量与配置引用不能当作成品使用量，缺少记录时明确标注。随后保留各型号的网页手册、印刷交付包（IDML + PDF）和 Word 云文档矩阵，按型号分组、每个区域一行，可以按型号、区域筛选，手机端可横向滚动。网页手册的链接随发布自动更新；印刷交付包和 Word 云文档的链接来自飞书文档构建表的快照，Word／印刷包交付写回并读回成功后，队列每批刷新一次并创建内容 PR。审核合入后还须完成 Workspace Data Verify，才能确认线上更新；补做统一使用 Workspace Data Refresh。飞书链接要登录飞书才能打开，但链接地址在公开页上可见。规则见[交付物页](../code-as-doc/dev/rtd_manual_portal.md#deliverables-page)。

### 发布候选、撤回与恢复

Web 发布候选按型号/市场/语言隔离，并保留旧链接重定向，见[契约](../code-as-doc/dev/web_locale_publication_identity.md)。
组装资源池同时处理图片和 Markdown 内嵌 CSS 的 `url(...)` 引用，保留背景图、遮罩图的原始字节及逻辑资产身份。视觉检查须覆盖这些 CSS 图形；图片元素全部加载不代表全部资源已加载，正式上线仍以冻结资源回执核验为准。
冻结发布源同时保留独立源包与整站组装副本，源清单容量上限为 768 MiB；网页输出及线上取回仍限 512 MiB，单文件 32 MiB、文件数 10,000 和哈希校验不变。发布前的整站 Sphinx 检查须加载 `myst_parser,tools.rtd.portal`，同时验证知识导出和部署凭据生成。

已有外部原稿的 Git-only 新语种网页发布，也要把每种语言标为 `single`，用冻结源清单与实际 Git 提交、MyST、图片和验证 HTML 生成[单语发布凭据](../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction)；现有 `build.py check` 只作旧构建目标的回归检查，不代表验证了这些新语正文。
原稿章节与历史 phase2 稿不同的，按原稿 SHA-256 登记独立的共享组件准入映射；仍须逐语核对原文、共用底图与桌面／手机页面。原稿中的语言混用保留并记录勘误，不自行翻译补齐。

JE-1000F/EU 新增四语从提供的可编辑 PDF 重新读取文字，以原 AI 核对缺字，保留已批准勘误。维护时通过[共享 IR 接入工具](../code-as-doc/dev/four_language_shared_ir_alignment.md)生成新候选包，采用英文网页的公共包装清单、总览、操作、App 和表格组件；正文不放印刷目录或表格截图。太阳能接线图中的型号/数量标注和车充图中的车辆标注保持为图框内可选中的文字，不能作为图外正文；桌面按原稿留白定位，窄屏在同一灰色图框内保持可读。配图须匹配原稿中的型号、插座和参数，资产清单未解决的项会阻止生成候选；历史 `build_web.py` 和截图保留作追溯证据。该步骤生成本地候选，尚需工程 PR、发布 PR 和 RTD 验收，不会自动发布，也不等于完成飞书语料入库或印刷产线注册。

JE-2000F/E 与上述候选共用 `manual-ir/v2`、ComponentSpec 和 Web 渲染器；各型号、语种的章节、图文、表格和 App 控件位置由[目标本地布局与原稿证据](../code-as-doc/dev/je2000_eu_new_locales_ir_adapters_2026-09.md)绑定。候选 `manual.ir.json` 若记录未完成的 `pending_source_review`，Web 发布证据封装会拒绝它；待原稿勘误获批并清空待审项后才能进入正式发布。复用前言须在绑定及每段文字中保留操作人批准记录，获批后重建才会去掉待审提示；这不等同于 PR 合入或 RTD 上线。 操作图的文字锚点须对照各型号、语种自身原稿校准，并核验引线、圆圈和前提提示框完整；图下说明不能影响图内文字定位。
Git-only [撤回与恢复](../code-as-doc/dev/web_publication_withdrawal.md) 必须指定型号/市场/语言/版本、原因、负责人和恢复快照；
缺少输入不会删除已发布手册，已撤回版本不能由普通发布重试重新进入目录。操作先验证本地候选，再走发布 PR 和实际部署回执。
旧记录的语言字段不等于正文单语；门户分组已有工程支持，真实多语上线仍须完成内容与 RTD 验收。

### 语言投影与发布凭据

Web profile 配合显式 `--lang` 现在会[冻结完整配置语言源并生成规范单语投影](../code-as-doc/dev/web_language_projection.md)：
`check`、Markdown 和 HTML 使用同一份所选语言 RST。显式语言的 Web 队列构建还会
[核对并封存三步凭据](../code-as-doc/dev/web_language_release_evidence.md)，绑定型号、市场、
语言、版本、Git_ref 及 Markdown/HTML 产物；凭据缺失或内容变化会阻止该版本被接受为单语发布。
共享配置选法语时，版本目录也使用法语，不落到配置的第一个语言下。旧的不可变版本不补写凭据，
需重新构建新版本。工作流、线上表、审稿源不变；凭据通过不等于翻译正确或已经在 RTD 上线。
发布组装会原样保留已生成的 `manual.ir.json` 和 `manual_bundle.html`，不再遗漏凭据中
记录的辅助文件；旧版本没有这些文件时仍可组装。未知文件不会被静默加入或从校验中排除。

### 钉钉查询欧规产品信息

在已启用查询功能的 BlockClaw 中，直接问“JE-2000F 欧规 USB-C 输出功率是多少？”
或“JE-2000F 节能模式怎么关闭？”。机器人读取已发布说明书，回答应附型号、EU、
版本和原文章节链接。型号不明确会先确认；未找到依据会说明未命中。
默认检索英文来源，用中文解释；旧版语言范围未验证时会明确标记。

固定入口 `/manual-query JE-2000F USB-C输出` 返回章节链接和检索片段；完整操作
请继续提问或打开原文。所有已发布 EU 版本自动随 RTD 构建进入索引；新增型号无需
单独配置。图片目前仅使用已有 alt 文字，复杂接线图仍需查看原文。
现有机器人只需更新控制插件并设置站点地址，具体见
[启用与验收](../code-as-doc/dev/eu_manual_query.md#activation-on-the-existing-gateway)。

### 发布健康、反馈与统计

Web 冻结产物可使用[只读健康报告](../code-as-doc/dev/manual_operations_health_report.md)
检查本地页面/资源。该报告不会访问线上表、确认部署或收集访客数据。
需要探测已发布链接时使用[线上HTTP检查](../code-as-doc/dev/manual_operations_online_health.md)；
它只读冻结目录并发起有上限的HEAD请求，不把200响应当作版本发布确认。

夏冰（GitHub `Bingboom`）负责发布健康与手册反馈，每次发布后检查本地资源、
线上可访问性和实际部署版本。已验证单语页面提供售后邮箱 `hello@jackery.com`
入口（出货手册已印的官方地址）和可复制的型号/市场/语言/版本/页面上下文；
读者自行提交问题，页面不会自动发送。GitHub Issues 转为内部/经销商分诊渠道。
处理流程见[手册中心说明](../code-as-doc/dev/rtd_manual_portal.md)。首次响应 3 个工作日内，
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

后续发布入口整合及中长期工作见[产线盘活与演进方案](../code-as-doc/manual_production_revitalization_plan.md)。
后续每次执行先读[执行台账](../code-as-doc/dev/manual_revitalization_execution.md)，按依赖领取 REV-ID，结束时回写证据及下一步；台账尚未接入自动调度。
本轮先复核新旧站点和历史链接，具体检查见[入口整合要求](../code-as-doc/dev/web_publish_pipeline.md#31-hosting-convergence-and-legacy-entry-review)。
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
[`je1000f_us_base_art_web.md`](../code-as-doc/dev/je1000f_us_base_art_web.md).
---

## 1. Environment Setup

Before running any build, review, check, or publish command, prepare the local environment in the repository root.

### 1.1 Python Environment

The quickest way to get the environment CI uses is the setup script. It finds the
Python version pinned in `pyproject.toml`, builds `.venv` from it, installs
`requirements.lock`, and runs `python -m tools.env_preflight --strict`, which exits
non-zero while anything still differs from CI:

```bash
scripts/setup_dev_env.sh                 # macOS / Linux; --python BIN, --venv DIR, --recreate
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_dev_env.ps1   # -Python, -Venv, -Recreate
```

To set it up by hand instead:

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

The dependency install step is mandatory.
Do not skip `python -m pip install -r requirements.txt` or `python3 -m pip install -r requirements.txt` when preparing a fresh environment.

To reproduce the exact environment a release was built with (or to avoid
rendering drift on a long-lived checkout), install from the pinned snapshot
instead: `pip install -r requirements.lock`. Regenerate the lock only on an
intentional dependency change (`pip freeze --exclude-editable`, keep the file
header). `python build.py doctor` prints the effective toolchain versions
(Python packages, xelatex, pandoc, InDesign when present), and every release
manifest embeds the same record under a `toolchain` key — a published PDF can
always name the environment that produced it. `doctor` also reports drift
against the pinned runtime (`env.python`, from `pyproject.toml`) and
`requirements.lock` (`env.lock`) as advisory `WARN` rows; run
`python -m tools.env_preflight` for the same report without a config (`--strict`
exits 1 on any `WARN`). A local
`python -m unittest` run prints the `WARN` rows once before the first test,
so environment-only failures are named up front; it is silent when the
environment matches CI and `AUTO_MANUAL_ENV_PREFLIGHT=0` turns it off.

For fixed-layout PDF work, edit the shared LaTeX component or its
data/layout_params.csv values instead of drawing borders directly in page
RST. Titles (H1 bars), capsule subbars, safety boxes, FCC panels, inbox
cards, tip strips, rounded table frames, symbol tables with controlled
symbol continuations, app steps, and app notices are reusable objects; page
RST supplies their text and image arguments. Body WARNING, CAUTION, NOTE, and TIP label/body tables are mapped
to the same rounded callout family automatically for LaTeX PDF output.
The visible label itself always comes from the page RST / source table. The
renderer does not change `TIP` to `TIPS` (or create any other fallback word),
and a missing label stops the LaTeX/IDML handoff instead of silently inventing
copy.

### 1.2 External Tools

- PDF export requires `xelatex`.
- Word export requires `pandoc` on macOS / Linux and on non-Word-COM paths.
- If the target uses a Word reference template such as the bundle flow, install `pandoc 3.9.0.2` or newer. The bundle exporter now auto-selects a compatible installed `pandoc` when multiple versions are present, and older versions can emit an invalid `/word/media/` content-type override that makes Microsoft Word repair the generated `.docx`.
- The Python dependencies in [`requirements.txt`](../requirements.txt) include the Sphinx theme and build libraries used by the current workflow.

If you want Gilroy only on your own machine for PDF preview, set `AUTO_MANUAL_LOCAL_GILROY_DIR` to the extracted font folder before running `pdf` or `publish`.
That folder must contain `gilroy-regular-3.otf`, `gilroy-bold-4.otf`, `Gilroy-LightItalic-12.otf`, and `Gilroy-ExtraBoldItalic-10.otf`.
If the env var is not set, or the folder is incomplete, the build keeps the normal shared fallback fonts and CI does not change.

If you only need the exact command semantics for one export path, use [`../code-as-doc/build_doc_guide.md`](../code-as-doc/build_doc_guide.md) as the authoritative reference.

### 1.3 DingTalk Wukong MCP Bridge

The version-controlled Wukong bridge lives at
[`agent/wukong-bridge/`](../agent/wukong-bridge). Do not maintain a second
untracked source copy under a home-directory `wukong-bridge` folder. Point the
MCP registration at the checked-in `server.py`, keep authentication in the
external `lark-cli` profile, and keep runtime jobs/exports under the external
state directory described in the bridge README.

For KR source intake, Wukong must pass an explicit sibling target to both
`intake_stage` and `intake_commit`. Staging validates canonical English source
text and the sibling identity
`Page + Row_key + Slot_key + Section + Line_order`; formal intake additionally
requires complete coverage of both `规格参数明细` and `页面占位参数`. A successful
partial staging response is not a complete target: inspect
`coverage_missing_rows`, finish the missing structures, review every value in
Base, and use the existing checkbox plus explicit-chat approval gates before
formal intake. Full configuration and the current contract version are in
[`agent/wukong-bridge/README.md`](../agent/wukong-bridge/README.md).

InDesign export has two handoff modes. The default production path creates the
component-heavy native/editable IDML from one deterministic `manual.ir.json`
and the shared layout-token contract; `latex_page_plan.json` remains a
same-source trace. Flow mode (`python3 build.py idml --idml-mode flow ...`)
creates semantic Markdown plus an editable continuous-story IDML, style map,
source trace, and asset manifest for a designer-owned template workflow. Both
are generated outputs, never new content sources.

Document-profile Markdown preserves a plain, three-item inventory such as the
JP inbox as its authored text table and following notes. It does not require
the images and tip table used by illustrated inbox cards. Illustrated cards
retain their image/label/tip validation. The prepared-bundle IR adapter preserves
complete signal-word definition tables as tables, including the JP definitions
of warning, caution, note and tip; individual warning callouts retain their
existing validation.
The JP symbols page's boxed introductory title and both paragraphs are also
preserved as editable IDML text. The previous single skipped-block debt is
closed for this runtime source; this does not replace native InDesign checks
for page layout, overset, fonts and links.

The measured JP fallback now lets the final operation table flow into the
existing page chain and sizes specification shells from their actual cells.
The `℃` character stays unchanged and uses a bundled font containing its glyph.
After `build.py idml`, still run native save/reopen and inspect the exported
PDF: an IDML with no overset can still have missing glyphs at PDF export.
See the [JE-1000F JP repair record](../code-as-doc/reviews/je1000f_jp_native_overflow_2026-09.md)
for the current acceptance state and remaining content debts.

For a single-language family such as `configs/config.ja.yaml`, you do not need
to repeat `--lang ja`: `build.py idml` forwards the config's sole language to
the exporter. On a multilingual family, add `--lang` when exporting only one
language; otherwise the existing whole-family/default behavior is preserved.

Production mode also checks assembly coverage. Current source pages are mapped
to target-neutral semantic roles before composition. If the command prints an
`assembly coverage` warning, the listed new or renamed page was preserved with
the ordinary editable-prose fallback, but it has no reviewed assembly role yet.
Update the shared role table and its regression test before release; do not add
a model/region-specific filename exception.

The BP family now has three exact-target configs. `JBP-2000B_US + us-merged`
selects `configs/config.bp-us.yaml`; `JBP-2000B_EU + eu-merged` selects
`configs/config.bp-eu.yaml`; `JBP-2000B_JP + jp-ja` selects
`configs/config.bp-jp.yaml`. The JP config has `family_default: false`, so MAIN
JP remains on `configs/config.ja.yaml`. The EU target contains
`en/fr/es/de/it/uk`, where
`uk` is Ukrainian, not a UK-market selector. It uses the paired host display
name `Jackery Explorer 2000 Plus`; only the US target uses
`Jackery HomePower 2000 Plus`; JP uses
`Jackery ポータブル電源 2000 Plus`. Keep those distinctions in target
substitutions and assets, not in page-renderer conditions. The EU and JP IDML
plans remain candidates until their separate promotion workflows approve them.

The production handoff's `production/source_trace.json` also records the
`skipped_raw_blocks` count from `manual.ir.json`. For ordinary/fallback targets
this remains report-only. For an approved-reference target, the approved plan
freezes `idml_contract.max_skipped_raw`, and production export stops if the
current count exceeds that baseline.

Strict Manual IR validation also stops on an unregistered build, manifest, or
page language. Approved-reference production runs this check automatically;
ordinary/fallback IDML keeps the existing permissive behavior. Add a language
to the shared registry instead of relying on the English fallback. Registered
aliases such as `jp` and `pt_br` are accepted.

For Japanese, Korean, or Chinese editable text, the IDML exporter writes
explicit script-aware font runs instead of letting those characters inherit
Gilroy. Korean uses the bundled SIL-OFL `NanumGothic` face. Japanese and
LaTeX use the bundled static TrueType `HBManualSansJP-Regular.ttf`
(`HB Manual Sans JP (OTF)` in InDesign, OpenTypeTT). Its project-unique family
and PostScript identity prevent a host `Noto Sans JP (OTF)` from shadowing the
packaged face after close/reopen. The `(OTF)` suffix is InDesign's normalized
CJK family spelling, not a dependency on a host CFF font; the same
hash-verified face travels with the designer package. Chinese continues to
use the separate `idml_font_family_cjk` renderer token. Font routing is not a
layout parameter, so changing a portable font does not require a
reference-layout rebind when geometry, content bindings, and composition stay
unchanged.

Editable symbol runs are cross-platform too. The `※` reference mark is a native
IDML vector, so reopening the saved INDD does not depend on a document font.
Warranty-year `3` / `2` values remain editable white ASCII digits inside native
black circular badges, preserving the approved appearance without relying on
host-specific `❸` / `❷` glyphs. The year unit and the warranty subtitle below
it share one component-owned x anchor, so `Standard Warranty` and
`Extended Warranty` stay left-aligned with their localized `YEARS` labels.
`Noto Sans` owns ordinals and subscript digits; `Noto Sans Symbols` owns DC and
circled labels 1-20; `Noto Sans Symbols2` owns the filled-circle fallback and
editable `☎ / ✉ / ◉` contact icons. Final assembly for
both approved-reference and target-assembly targets uses native vector heading
markers, and LCD labels 21-27 serialize as `(21)`-`(27)`. The exporter copies
the declared SIL-OFL files beside the IDML under `Document fonts/`, so raw
designer packages no longer depend on `Segoe UI Symbol`, `Yu Gothic`, or
`Noto Sans KR` being installed on the opening host.

The exporter also budgets Japanese, Korean, and Chinese wrapping by Unicode
East Asian Width instead of treating every character as a 0.52-em Latin
glyph. Fullwidth characters receive a full-em budget while ambiguous-width
characters stay narrow so CI and the design Mac agree. This reduces late
overset surprises, but it is still a deterministic estimate: the designer
must complete native InDesign preflight and page parity before release.

The production Meaning of Symbols page also remains editable. Its WARNING,
CAUTION, NOTE, and TIP badges use a linked white warning icon plus ordinary
InDesign label text, rather than a flattened language-specific badge image.
The safety-tail panels use the approved dark triangle, and the symbol-grid
icon size and columns come from shared layout tokens, so English, French, and
Spanish follow the same component definition.
The symbol-page copy and TOC language headers come from the shared language
registry's IDML language packs. Reference-bound spacing override rows are read
for the registry's `layout_override_languages()` set — the governed languages
plus lines in active layout tuning, currently adding Korean — while
`governed_languages()` (English, French, Spanish) still gates
approved-reference flow behavior such as fixed heights and reference offsets.
A tuning language's override rows take effect as they land, but its flow
behavior stays measured/fallback until its reference layout is approved, so
adding translation metadata still does not silently apply an unapproved
physical layout.
The LaTeX safety dispatcher uses the registered warning label for every
language passed to `HBApplyLang`, including the long-tail languages, instead of
silently retaining `WARNING`.

In production IDML operation panels, Prerequisite, standby, On, and Off are
separate unlocked text frames placed above the linked illustration. Designers
may select, edit, and move each frame for alignment without editing the image;
copy corrections still belong in the source and must be rebuilt, apart from
the explicitly approved target-scoped App display-variant binding described
below. Energy Saving
also exposes its two grey-box paragraphs, On/Off, 3s, and action instruction as
top-layer frames. LED exposes its grey-box lead, 1/2/3, SOS, and three step
instructions separately; their linked art and native shape underlays remain
below the text. LCD SCREEN likewise exposes two state, six action, and six
description frames above its left-side illustration and grid. KEY COMBINATION
uses linked button/clock graphics while every header, caption, plus sign,
duration, operation, and function remains a separate movable text frame across
English, French, and Spanish. One shared layout-token style owns its geometry
and typography; only the governed French/Spanish height, indent, and gap values
are locale overrides. The renderer emits all of those text frames last so they
stay above the artwork and remain individually editable.

Approved Charging figures use the same top-layer rule for AC and vehicle
captions. The exact App reference composition applies to the English, French,
and Spanish App Setup sources: Store/QR and result-screen crops remain linked
art, while step numbers, pairing-panel labels, and notes are separate movable
text frames. Pairing-panel labels come from the Product Overview's stable
`main_power`, `dc_usb`, and `ac` slots, then use the reviewed per-language App
display variants stored in the approved plan; they are not guessed from the
next paragraph. Only an exact duplicate three-line label block is removed, so
Spanish step 2.3 remains ordinary editable prose. The shared `AppFigureStyle`
owns overlay sizing for all three languages, and approved builds fail when a
required source role, display variant, asset, or style token is missing. These
presentation variants do not change the source/IR content hash; every label
remains unlocked and editable in the top layer.
The same approved plan explicitly lists these source pages under
`idml_contract.editable_components.app_add_device.page_owners`. That list
drives both hidden App-asset packaging and production composition, so a page
that is absent, belongs to another language, or comes from a draft contract
cannot silently enter the reference layout.

For the approved-PDF replica of `JE-1000F / US / en+fr+es` (方案 2), production
mode must resolve the
[`reference layout registry`](../docs/renderers/contracts/reference_layout_registry.json)
and the
[`JE-1000F US V2.0 contract`](../docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json).
That contract is bound to the 58-page
`Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf` with SHA-256
`e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2`
and `368.787 × 524.692 pt` page geometry. The physical structure is front
matter 1–3, English 4–21, French 22–39, Spanish 40–57, and back cover 58. Its
52 source references are bound by composition across all 58 pages. Missing or
mismatched enforced content/assembly/style identity, source/hash drift,
unclassified prose without an exact exception, or page-count drift is a hard
failure; the build must not silently use fuzzy PDF matching. The v2 contract
keeps the global phase2 snapshot hash as non-blocking provenance, so unrelated
table refreshes do not invalidate an unchanged target manual.
The same rule applies if the contract file is still approved but its registry
entry is missing: the build stops and names the orphaned contract. Only a target
with no approved contract may use measured-LaTeX fallback pagination.

The English single-language manual `JE-1000F / US / en` is a pilot component
target of that contract: when its source pages match the approved contract,
`build.py idml` prints `COMPONENT TARGET OK (pilot)` and composes the registered
LCD, Overview, Charging, Storage+Troubleshooting, Warranty and main-power pages
instead of the measured LaTeX layout. If the log shows
`COMPONENT TARGET INERT`, the content differs from the reviewed pages (each
drifted page is listed); the IDML falls back to the ordinary layout. Do not edit
hashes by hand: refresh the contract with the rebind commands below after
review. Details:
[`idml_component_targets.md`](../code-as-doc/dev/idml_component_targets.md).

When a source refresh changes mutable style/provenance identity without changing
the approved content or semantic/physical assembly, use the rebind command
instead of editing one hash or removing the registry entry. It is a dry-run
unless `--write` is present:

```bash
python3 -m tools.reference_layout_rebind \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json>
python3 -m tools.reference_layout_rebind \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json> \
  --write
```

For a read-only summary of all registered contracts, run
`python3 -m tools.reference_layout_rebind --all-registered --manual-ir
<manual.ir.json>`. Batch mode never writes; keep `--write` limited to an
explicit single-plan command after review.

For a v2 plan, the ordinary command validates that semantic content, assembly,
source order, page languages, and physical composition remain unchanged. It
refreshes only the mutable non-content identities and every page's source
digest, then atomically replaces the plan. Review the dry-run summary and Git
diff before building. A v1 plan has no assembly pin, so v1-to-v2 migration is
an identity change and cannot use the ordinary route.

A content/assembly change, including v1-to-v2 migration, is rejected unless an
operator has first verified the final Manual IR's source-reference order,
language mapping, `skipped_raw` allowance, semantic page roles, physical page
count, and composition map. After recording that decision, use the explicit
approval route in dry-run mode first. The existing flag name is retained for
CLI compatibility:

```bash
python3 -m tools.reference_layout_rebind \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json> \
  --approve-content-change \
  --approved-by "<operator>" \
  --approved-at "<RFC3339>" \
  --approval-method "<recorded review evidence>"
# Repeat the same command with --write only after reviewing the candidate.
```

The three approval fields are mandatory and are stored in the contract.
`--all-registered` cannot approve identity changes or write plans. Source order,
languages, and physical composition remain immutable even on the approved
identity-change route. v1 migration does not auto-populate
`allowed_unclassified_source_refs`; unclassified pages require a separately
reviewed layout decision.
The layout-parameter identity follows ordered `key`/`value`/`unit` semantics;
line-ending, blank-row, and comment-column edits do not create contract drift,
but a real token value, unit, or order change does.

The role boundary is strict:

- source owners correct copy, translation, specifications, legal text, table
  structure, and asset identity in Feishu/source tables, templates, review/TM,
  or the asset registry, then rebuild;
- the build creates native text, headings, tables, callouts, Product Overview,
  and back-cover objects/stories; illustrations remain governed linked assets;
- the designer may adjust frame geometry, explicit page breaks, asset fitting,
  and limited tracking, but may not turn INDD into a second content source;
- the approved reference PDF may be used only on a non-printing comparison
  layer. Visible whole-page body/back-cover PDF placement is forbidden; a
  contract-approved finished-art front cover is the narrow exception.

Use `asset:<asset_key>` (for example `asset:operation/ac_output`) for governed
illustrations. Only approved PNG/JPG/JPEG/SVG/PDF exports matching model,
region, and language may resolve. The `.ai` file is an immutable source archive,
not a renderer fallback. Missing, ambiguous, quarantined, stale, or
hash-mismatched assets block assembly. Keep `asset_usage_manifest.json`,
`asset_registry_snapshot.csv`, and `bundle_manifest.json`; a `legacy-path`
entry alone does not prove that an asset is governed.
The US front-panel extension is the
`overview/je1000f_us/front_controls` override behind the shared
`overview/front_controls` key. It resolves only for JE-1000F/US; the common
Word-template PNG remains the base asset for other targets.
The grey pairing panel is the approved
`controls/je1000f_us/network_pairing_panel` recipe export. Because the reviewed
App promotion binds the complete recipe SHA, changing that recipe requires a
new reviewer decision and a passing `asset-check --json`; operators must not
patch the hash alone.

The provisioned design Mac runs `tools/indesign_finalize.py` to create the INDD
and PDF, with zero overset/missing-font/missing-glyph/bad-link findings and
PDF/X-4 using `Japan Color 2001 Coated` / `JC200103`. The finalizer scans the
exported PDF for visible `U+FFFD` and `.notdef` glyphs, including text retained
inside placed PDF graphics; rasterized or outlined art remains part of visual
review. It then runs
`tools/idml_pdf_parity.py` against the approved PDF (the historical
`--latex-pdf` flag name does not mean the newly built LaTeX PDF here) and the
approved contract. All 58 pages are compared at 300 dpi as fixed
`1537 × 2187` RGB rasters with the approved ICC profile, 1 px blur, per-page
RGB MAD `≤ 0.008`, changed-pixel ratio `≤ 0.040`, and changed-channel threshold
`16`. Any failing page fails the run; averages cannot hide it.

Keep `Document fonts/` beside the generated INDD. Before exporting the final
PDF, the finalizer saves the INDD, closes it, reopens it, recomposes it, and
rechecks fonts, overset stories/cells, links, page count, and story count. The
`indesign-preflight/v2` report records this under `post_reopen`; a first-open
green result is no longer sufficient.

For Japanese documents the portable-font rebind preserves each character's
declared Regular/DemiLight/Medium/Bold face; an unavailable requested face stops
finalization. The report records counts under `portable_font_rebinds[].style_counts`.
Keep frozen inputs and native evidence outside the target build directory before
running another `build.py idml` or `check`, because preparation cleans that target.
The [JP twelve-page acceptance record](../code-as-doc/reviews/bp_jp_r3c_native_validation_2026-09.md)
shows the package hashes, actual native results and explicitly retained debt.

For a multi-target design handoff, run
`python -m tools.indesign_finalize --jobs <manifest.json>` with one explicit
PDF preset, output intent, output condition, and PDF/X level on every job.
The batch writes an aggregate report, isolates one failed InDesign job from
the others, and lists IDML directories whose InDesign package is incomplete.
Jobs with the same `application` value are finalized sequentially inside one
InDesign/ExtendScript invocation; each document still gets its own INDD, PDF,
preflight report, close step, and failure result.

Delivery requires all 52/52 source identities, all used asset hashes/scopes,
58-page geometry, native-object/no-whole-page-shortcut checks, preflight, print
contract, and every page-level visual check to pass. The latest parity report
must say `accepted=true`. This guide describes that acceptance contract; it
does not claim the current IDML/INDD/PDF has already passed. Copyable commands
are in the
[`Approved-PDF native InDesign replica` section](../code-as-doc/build_doc_guide.md#approved-pdf-native-indesign-replica-option-2).

Write the finalize and parity artifacts **next to the production IDML**, in
`docs/_build/<model>/<region>[/<lang>]/idml/` — `<stem>.indd`,
`<stem>_indesign.pdf`, `finalize_report.json` and `parity_report.json`. That is
the only location `release-manifest` looks in, so artifacts left in a scratch
directory are simply not recorded. (The second-host verification run in
[`indesign_second_host_runbook.md`](../code-as-doc/dev/indesign_second_host_runbook.md)
is the deliberate exception: it writes to a temp dir precisely because it must
not touch the repo.) The manifest's `indesign_package` section then records the
IDML, INDD, InDesign PDF, handoff zip and both reports with sha256, plus the
preflight numbers and the parity verdict; `complete` is true only when the
IDML, INDD, InDesign PDF, handoff zip and finalize report are all present. An
automated publish with no finalize run records what exists and marks the rest
absent rather than failing. The JSON keeps native page/overset counts under
`indesign_package.preflight`; the CSV mirrors them in
`indesign_preflight_page_count` and
`indesign_preflight_overset_stories` for dashboards. Blank means “not reported”
and `0` means a verified zero, so a partial legacy report cannot look clean by
accident.

Use `python3 build.py idml --idml-mode both ...` when design also needs the
paired flow handoff folder: it keeps the production IDML and adds
`production/manual.production.idml`, the flow folder,
`missing_assets_report.md`, `designer_checklist.md`, and `layout_feedback.md`.

For reference-layout-registered targets, the IDML command's default
`--source auto` resolves to the frozen `review-asis` bundle so production and
flow use the approved page assembly. Explicit `runtime`, `review`, or
`review-asis` remains unchanged; unregistered targets still default to
runtime.

`review-asis` preserves the committed review page bytes, but the prepared
bundle always applies the target's current language registry. If a historical
merged review index still includes a language that this model no longer ships,
the build removes those out-of-scope page includes and their generated page
copies by their explicit `\HBApplyLang{...}` declarations, rejecting paths
that escape the generated bundle, and trims the matching block from shared
multi-language pages. A fully recognized `English / French / ...` language
catalogue on that shared page is trimmed to the same scope. It does not edit
`docs/_review`, infer language from filenames or translated headings, or relabel
the stale page as another locale.

The merged Web manual turns that resolved language order into a top jump bar.
Each pill uses the language's native name and jumps to the first page of that
language; the old plain-text language catalogue is therefore not shown twice.
This is automatic for any whole-document Web build with at least two declared
languages, so a new target does not add model-specific HTML or CSS. On phones
the pills scroll inside the bar without widening the page; print output hides
the bar. A single-language manual keeps its previous output unchanged.

Publish queue runs use `--idml-mode both` automatically and upload a single
designer delivery zip (`manual_..._publish_<version>_handoff.zip`) instead of
the bare `.idml`: it bundles the production IDML with its image links
rewritten to a packaged `Links/` folder, the flow outputs, the handoff
reports, a fonts manifest, the bundled SIL-OFL fonts under `Document fonts/`,
and the reference PDF; the zip's knowledge-base link is what lands in the
queue row's `idml_file` field.
If `AUTO_MANUAL_LOCAL_GILROY_DIR` is set on the build machine, licensed Gilroy
files from that folder are added to the same directory. Gilroy remains a
commercial operator-provisioned font; the repository does not redistribute it.
The checklist opens the versioned IDML at the zip root. Package link failures
are reported in `missing_assets_report.md`; unresolved semantic source/flow
references remain available separately in `source_asset_resolution_report.md`.
Before handoff, extract the final delivery ZIP, confirm its package link report
has zero missing assets and that the generated reference crops plus pairing
panel are under `Links/`, then run native InDesign finalization on that exact
root IDML. A valid ZIP or structural IDML check is not native preflight.

When a queue row carries `Git_ref`, the worker uses the current `origin/main`
for build code and overlays `docs/_review/` from that review ref. This keeps
merged renderer fixes in Publish output even when the worker's local `main`
branch is stale.

GitHub note:

- pull requests are gated by the `Manual Validation` workflow
- after merge, `main` runs the same validation workflow again
- feature-branch pushes are not expected to run a second duplicate `push` validation pass
- `Manual Validation` now includes smoke checks for `diff-report` and `release-manifest` in addition to the existing validation jobs
- the shared GitHub-hosted Feishu worker setup now installs `pandoc` from the official release action instead of `apt-get`, and it reuses pip/npm download caches, so remote queue runs are less likely to spend 10+ minutes waiting on slow dependency downloads before the actual build starts
- `Manual Validation` now also runs `python -m tools.check_maintainability_guardrails` as a low-noise guard against the main orchestration and validation hotspots growing back into giant files
- that guard also applies a reviewed language-literal ratchet: language tables may shrink, but new literal tables must be explicitly reviewed in the baseline diff
- the same guard applies a per-function complexity ratchet (`data/complexity_baseline.tsv`): new functions stay at complexity 20 or below, recorded ones may only get simpler, and a simplification is locked in by rerunning `python -m tools.check_complexity_ratchet update`
- the same guard counts test patches on facade modules (`data/facade_patch_baseline.tsv`): tests should patch the module that looks a name up, so the count may only fall; a drop is locked in with `python -m tools.check_facade_patch_ratchet update`
- the same guard counts broad exception handlers (`except Exception` / `except BaseException`, `data/broad_except_baseline.tsv`): new code catches the specific exception, so the count may only fall; a drop is locked in with `python -m tools.check_broad_except_ratchet update`. A deliberate boundary re-raises or names its reason with `# noqa: BLE001 - <reason>` on the `except` line; the baseline is now empty
- the same guard lists `tools/` top-level modules and files with script bootstrap code (`data/top_level_module_baseline.tsv`): put new code in a subpackage and run it with `python -m tools.<pkg>.<module>`; a new top-level module needs `python -m tools.check_top_level_module_ratchet update --allow NAME=REASON`, and a removal is locked in with `update`
- ruff `B905` requires `strict=` on every `zip()`: use `strict=True` when the lengths must match, or `strict=False` with a `# zip(strict=False): <reason>` comment when truncation is intended
- CI's `type-check` job counts untyped-def mypy errors in `tools/manual_ir`, `tools/component_specs` and `tools/csv_pages` (`data/mypy_untyped_baseline.tsv`); annotate new functions there, and after fixing errors run `python -m tools.check_mypy_ratchet update` (with `mypy==2.3.1` installed)
- `build.py check` also compares duplicated RST and raw HTML list text so renderer-specific copies cannot silently drift from the source wording
- `build.py check` also renders every prepared FCC page with the target language in both document and web profiles. A missing FCC opening line block, an unregistered localized right-column marker, or a runtime filename remap that loses language context now fails during `check`, before Word generation.
- `build.py check` also enforces capability -> chapter consistency: [`../data/model_capabilities.csv`](../data/model_capabilities.csv) mirrors the 文档构建表 feature checkboxes (refreshed by `sync-data` when `FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID` is set — it is a tracked file like `page_registry.csv`, so the git diff is the review surface for capability changes; duplicate build-table rows collapse to one mirror row), and [`../data/capability_page_rules.csv`](../data/capability_page_rules.csv) maps each capability to a required/forbidden bundle page or in-page section regex. A target with `UPS功能=TRUE` must carry `06_ups_mode`; one with `加电包扩容=FALSE` must not carry an extra-battery page. Targets without a capability row emit a non-blocking `CAPABILITY_ROW_MISSING` warning unless listed in [`../data/capability_known_missing.csv`](../data/capability_known_missing.csv); capability page selection remains fail-open. Each rule's enforcement is toggled per direction in the rules CSV (`required_when_true` / `forbidden_when_false`), so noisy rules stay recorded but inert until their wording is unified. The Feishu 文档构建 base carries a mirror rules table for visibility; the repo CSVs are the consumed source.
- `sync-data` derives the capability mirror header from the ordered `capability` values in `capability_page_rules.csv`, so a new rule does not require a separate Python registration list.
- Manifest pages can carry a `capability:` key (the capability field name): at bundle-plan time the assembler keeps or drops the entry per target using the same capability mirror, so one family manifest declares the page superset and each model auto-selects its chapters. All 24 current `06_ups_mode` entries across the 17 family manifests—including JP, KR, EU, US, AU, pt-BR, and CN—declare `UPS功能`; `manual_us.yaml` additionally maps `07_extra_battery` to `加电包扩容`. Targets without a capability row keep every page. New family manifests must preserve these annotations and refresh the checked-in family diff carrier.
- When one model needs a different placeholder-backed page layout but the family page order stays the same, that `generated_page` may use `model_overrides.<MODEL>.recipe` and/or `.template`. This is a narrow layout exception: other models still resolve the shared paths, and product/spec values remain in phase2 source tables.
- **Languages are per model, not per family.** A family config's `build.languages` is the union across that region's models — `configs/config.eu.yaml` lists six because the EU line carries Ukrainian templates, while JE-1000F does not ship Ukrainian. [`../data/model_languages.csv`](../data/model_languages.csv) (`Document_key,Project,languages,notes`, languages `;`-separated) narrows the family list per `<MODEL>_<REGION>` at bundle-plan time, dropping that language's pages **and** its generated data pages (`spec_uk.rst`, `symbols_uk.rst`, …). Never delete a language from the family config to fix one model: the models that do ship it would lose it too. Resolution intersects while preserving the family's order, so the config still owns ordering. It is fail-open like the capability gate — no row keeps every family language — and it is a tracked CSV, so the git diff is the review surface.
- Prefaces carry every family language *inside one file*, which page selection cannot narrow. Those manifest entries declare `lang_blocks: true` and the assembler drops the out-of-scope blocks (`**FR IMPORTANT**` headers, `\HBLangTagLine{XX}` in `raw:: latex`), keeping page-structure macros. The annotation is required, not inferred, because `**IT ...**` is ordinary bold text elsewhere. This replaces forking a template per language line (`00_preface_single_language.rst` was the hand-made version of exactly this trim). A trimmed target also gets a `MANUAL_LANGUAGE_SCOPE` derived from its real languages, so the cover line stops advertising a language the book no longer contains.
- JE-1000F US en/fr/es is the document-output exception: its three `manual_us-single-*.yaml` manifests intentionally keep the trilingual preface for IDML/Word/PDF. Their configs use `build.web_language_block_pages` instead, so only the Web en/fr/es routes remove the two foreign `IMPORTANT` blocks.
- A committed `docs/_review` derivative is per `(model, region)` and shared by a region's merged and single-language configs, so it holds the merged book's languages. The trim runs again on the overlaid bundle copy — `docs/_review` itself is never rewritten, and the merged build is unaffected because all its languages are in scope.
- New `check` codes: `LANG_SCOPE_UNSHIPPED_LANGUAGE` (a scope row disjoint from the family the config declares — today `configs/config.eu-uk.yaml` with its inherited JE-1000F/EU default target, which ships no Ukrainian) and `LANG_SCOPE_FOREIGN_SCRIPT` (a bundle page carrying a dropped language's script, which catches leakage that has neither a `_<lang>` filename suffix nor a language tag). The per-language contract / generated-page / identity / parity collectors all see the narrowed set, so a model shipping five of six family languages no longer fails on the sixth's missing source data.
- `Review Preview Package` is the separate packaging path when you need to share rendered review HTML with design
- that workflow now runs a lighter smoke packaging pass with `--skip-word` and verifies the packaged preview files before upload

Git branch hygiene note:

- after one PR is merged or closed, start the next change with `powershell -ExecutionPolicy Bypass -File scripts/start_branch.ps1 <type>/<area>-<topic>` on Windows or `./scripts/start_branch.sh <type>/<area>-<topic>` on mac/Linux so the new branch comes from the latest `origin/main`; use a change-type prefix such as `feat/`, `fix/`, `refactor/`, or `docs/`, never an agent-name prefix
- enable the repo-managed pre-push guard with `git config core.hooksPath .githooks`
- that guard now runs through the shared [`../scripts/git_branch_guard.py`](../scripts/git_branch_guard.py) core instead of a bash-only hook, and the repo also ships [`.githooks/pre-push.cmd`](../.githooks/pre-push.cmd) plus [`.githooks/pre-push.ps1`](../.githooks/pre-push.ps1) as Windows-native companion launchers
- that guard blocks pushes from branches that do not contain the latest `origin/main`; bypass only when intentional with `git push --no-verify`. `review/*` and `backport/*` branches, and pushes to remotes other than `origin` such as `hello-docs`, are exempt
- if OpenClaw on your local machine needs to report branch state or switch to an existing branch from a Feishu chat flow, use [`../scripts/openclaw_git_guard.py`](../scripts/openclaw_git_guard.py) instead of exposing raw Git commands; it only supports `status` and safe `switch --pull`, and it refuses non-generated dirty worktrees
- OpenClaw / Feishu IM can now answer read-only product-manual inventory questions from the `发布文档管理` Base view before falling back to queue resolution. Use phrases like `查 JE-2000F 的说明书链接`, `查询各产品的说明书`, or `获取说明书总览信息`; build-copy phrases such as `输出JE-1000F的所有欧规说明书文案` still go through the existing Build Draft queue path.
- if you need to keep `main` open while editing one or more review branches in parallel, use the repo worktree flow in [`../code-as-doc/dev/git_worktree_guide.md`](../code-as-doc/dev/git_worktree_guide.md); on Windows, prefer worktree paths under your current user such as `C:\Users\<you>\Documents\cms2docs\worktrees\...` instead of another user's home directory

---

## 2. Source of Truth

The manual system now has four layers, but they are used at different stages.

1. Template seed layer
   - [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
   - [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
   - [`docs/manifests/*.yaml`](../docs/manifests)
   - Responsibility: reusable page structure, headings, shared prose, and initial draft layout
   - Some templates intentionally duplicate prose across normal RST and renderer-specific branches such as `.. raw:: html` or `.. raw:: latex`; when changing wording, treat the RST list as the source wording and keep renderer-specific copies aligned
   - Template-maintenance Feishu cloud docs can be compared with `python -m tools.backport.cloud_doc diff --template ...` and then planned with `python -m tools.backport.cloud_doc apply-template --report ...`; the apply step is dry-run by default and only writes guarded template prose replacements when `--write` is supplied. It does not write Feishu source tables or review bundles.

2. Data layer
   - preferred snapshot root [`data/phase2/`](../data/phase2)
   - [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
   - [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
   - [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
   - [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)
   - [`data/spec_master_value_repairs.csv`](../data/spec_master_value_repairs.csv) — tracked dormant known-value repairs consumed by the spec repair pass
   - [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)
   - [`data/phase2/lcd_icons_blocks.csv`](../data/phase2/lcd_icons_blocks.csv)
   - [`data/phase2/Manual_Copy_Source.csv`](../data/phase2/Manual_Copy_Source.csv)
   - [`data/phase2/Localized_Copy.csv`](../data/phase2/Localized_Copy.csv)
   - [`data/phase2/Status_Words.csv`](../data/phase2/Status_Words.csv)
   - [`data/phase2/troubleshooting_blocks.csv`](../data/phase2/troubleshooting_blocks.csv)
   - [`data/phase2/Variable_Defaults.csv`](../data/phase2/Variable_Defaults.csv)
   - [`data/phase2/Variable_Lang_Overrides.csv`](../data/phase2/Variable_Lang_Overrides.csv)
   - [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv)
   - Responsibility: model-specific parameters, spec content, symbols content, troubleshooting content, LCD status-word matching, and placeholder values
   - When a valid phase2 snapshot exists, build/review/publish flows default to `data/phase2`; explicit `--data-root` still overrides that default.
   - A phase2 snapshot is valid for automatic default use only when `snapshot_manifest.json` records the complete core table set from one sync run: `spec_master`, `spec_footnotes`, `spec_notes`, `symbols_blocks`, `troubleshooting`, `lcd_icons`, `variable_defaults`, `variable_lang_overrides`, and `manual_copy_source`, plus derived `row_key_mapping`, `spec_titles.csv`, `Localized_Copy.csv`, and `Status_Words.csv`. Partial `sync-data --table ...` refreshes are still useful for focused checks, but use explicit `--data-root` when building from them.
   - For queue-driven builds, Feishu phase2 tables remain the structured-data source of truth. `data/phase2` is the gitignored materialized snapshot refreshed before build, not the daily authoring surface or a mirror-repo code difference.
   - GitHub `Manual Validation` uses the committed fixture snapshot under [`../tests/fixtures/phase2`](../tests/fixtures/phase2) so CI stays deterministic after `data/phase2` became gitignored; local live builds should still sync into `data/phase2`. The stable US/JP checks remain, and `tools/ci_check_targets.py` now derives an additional check target from every `configs/config*.yaml`. A target whose fixture snapshot lacks its `document_key` is reported as `SKIP`, not coverage; the coverage formula is `PASS/(PASS+SKIP+FAIL)` and `.github/ci_check_targets_skip_baseline.json` carries two no-increase ratchets, `skip_count` and `fail_count`. The Stage 1 observation lane reports the already-recorded FAIL rows without blocking, but a **new** FAIL fails the lane, as does a new SKIP. Without the FAIL ratchet, `--observation` let a target slide from `PASS` to `FAIL` with the job still green, so only `check-en` and `check-jp` were really gating anything. The repo-maintained [`../data/phase2/page_registry.csv`](../data/phase2/page_registry.csv) is the one tracked exception because `sync-data` reads it as the page-structure input on every run, including fresh checkouts.
   - GitHub `Nightly Render` is the credential-free daily rendering sentinel. It doctors every target discovered from `configs/config*.yaml`, then builds and validates the JE-1000F US English production IDML from `tests/fixtures/phase2`; manual dispatch uses the same committed fixture inputs. A failure points to either the exact config doctor row or the pilot IDML check instead of waiting for the next designer handoff to expose renderer drift.
   - To refresh one CI fixture target from the local mirror, first run `python -m tools.data.snapshot fixture-refresh --document-key <MODEL_REGION> --source-root data/phase2 --fixture-root tests/fixtures/phase2` as a dry-run, then repeat with `--write` after review. The command merges only the selected `document_key` (and shared rows), preserves unrelated targets, copies referenced attachments, and updates manifest hashes; it does not replace the whole fixture snapshot.
   - `Bingboom/auto-manual` is the code source of truth. Its `sync-hello-docs.yml` workflow mirrors the `main` engineering tree one-way into `Bingboom/Hello-Docs` while preserving the business-owned `Hello-Docs/main:docs/publish/**` subtree; it composes Git objects without re-adding a checked-out tree that could rewrite file blobs through line-ending attributes and fails if auto-manual ever starts owning `docs/publish`. Configure `HELLO_DOCS_SYNC_TOKEN` only in the source repo, keep `Hello-Docs` Feishu/OpenClaw bindings in that repo's own GitHub Secrets / Variables, and leave `FEISHU_BUILD_QUEUE_PAUSED=true` in the mirror repo until those bindings are ready. That pause variable is scoped to mirror Feishu runtime workflows and does not pause source repo behavior.
   - Copy [`../scripts/hello_docs_binding.env.example`](../scripts/hello_docs_binding.env.example) to a gitignored local file such as `.tmp/hello-docs-binding/env.sh`, fill the alternate Feishu values there, run `scripts/configure_hello_docs_binding.sh --env-file .tmp/hello-docs-binding/env.sh --dry-run`, then rerun without `--dry-run` to write the values into `Hello-Docs`; add `--include-optional` when the env file also has mirror-only Feishu IM / OpenClaw adapter values, and add `--unpause` only after the audit should allow Feishu runtime workflows to run.
   - Before unpausing `Hello-Docs`, run `scripts/audit_hello_docs_binding.sh --report-only`; it reports source/mirror tree parity, missing GitHub Secret names (including the model-capabilities table binding), mirror variables, and optional Feishu IM / OpenClaw entries without printing secret values. The daily Feishu schema sensor treats `文档构建表`/`数据入库表` and `02_文档构建`/`01_数据入库` as documented old-base/business-base aliases, and treats the retired `Document link` as replaced by `基线文档`/`飞书云文档`, so it does not request duplicate schema.
   - For spec data authoring, edit `规格参数明细` for `Page=specifications` rows and `页面占位参数` for non-spec page placeholders. `sync-data --table spec_master` now reads those two source tables through the pinned source views and writes the local `Spec_Master.csv` read model.
   - When changing the online source-table structure, update the machine-readable source-table contract [`../data/source_table_contracts/phase2_source_tables.json`](../data/source_table_contracts/phase2_source_tables.json) in the same PR as the human reference docs. It records each table's source key, snapshot file, intake target, writable fields, and source-record-index mapping so intake/backport/writeback skills do not rely on memory. `python -m tools.schema_drift --payload tests/fixtures/schema_drift/passing_payload.json` validates this contract in CI.
   - For first-pass intake from a structured spec/manual Markdown or Feishu cloud doc, run `python -m tools.data.source_intake run --input <spec.md-or-doc-url> --document-key <MODEL_REGION> --source-lang en --data-root data/phase2 --out reports/source_intake/<run-id>`. This produces reviewable source-table candidates and existing-row change requests; it does not create new online rows or bypass the human-approved source-table writer. Continue with `source_intake.py approve`, `source_intake.py apply`, and `source_intake.py verify` to record the P4-P7 closure; `apply` is dry-run unless `--write --table-binding TABLE=BASE:TABLE_ID` is supplied. Use [`../code-as-doc/dev/source_intake_mvp_checklist.md`](../code-as-doc/dev/source_intake_mvp_checklist.md) as the staged checklist.
   - For repeated spec-sheet onboarding, do not assemble dozens of staging rows by hand. Run `source_intake.py spec-extract` with a real sibling reference, then `source_intake.py stage-plan --spec-candidates <...> --spec-sibling <...> --placeholder-sibling <...> --overrides <target-differences.json> --document-key <MODEL_REGION> --localized-lang <lang>`. The second command clones both sibling structures, rejects ambiguous/missing logical rows, carries localized fields with changed source values, marks inherited-but-unconfirmed rows, and writes one review file plus a lark-cli `create_records` payload without touching Feishu. With exports ready, the mechanical repeat-run target is 3–5 minutes before human review; staging write/readback and formal source-table promotion remain approval-gated. See [`.agents/skills/spec-sheet-structured-intake/SKILL.md`](../.agents/skills/spec-sheet-structured-intake/SKILL.md).
   - After changing either spec source table, run `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --table spec_master` for the normal snapshot refresh, or `python build.py spec-master-rebuild --config configs/config.ja.yaml --expect-spec-rows 157 --expect-placeholder-rows 222` for a focused rebuild; add `--write-back` only when the merged source data should update the legacy Feishu total table.
   - `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2` refreshes the frozen snapshot from Feishu/Lark using the local `lark-cli` login and the CLI's `base` record listing flow; it also reports source columns missing from the phase2 schema as non-blocking `MISSING_COLUMNS` warnings in `snapshot_manifest.json` and the command output
   - `python -m tools.content_lint --data-root data/phase2 --json --write-report` runs the local content-QC observation step against that snapshot and writes `reports/content_qc/<run-id>/findings.json` plus `report.md`; fix findings in the Feishu source tables or Translation Memory, not in the generated CSV/report files. This command does not write Feishu QC rows, resolve live `record_id`s, or block Word delivery beyond its own `FAIL` exit code.
   - `configs/config.eu.yaml` now represents the live `EU` region-family row as `Build_family = eu-merged`, reads `JE-1000F / EU` specs from the shared split spec source tables, and is the config that blank-`Lang` queue rows should resolve to
   - `configs/config.eu-en.yaml`, `configs/config.eu-fr.yaml`, and `configs/config.eu-es.yaml` are the explicit English, French, and Spanish EU single-language surfaces when you want one language family at a time; `configs/config.pt-br.yaml` follows the same single-language pattern for Brazil Portuguese
   - `configs/config.au-en.yaml` is the Australia (`AU`) single-language English surface (`Build_family = au-en`); it inherits the EU single-language base, builds the `JE-1000F / AU` target, and uses the Australia-specific warranty contact `hello.aus@jackery.com`. Its safety/安规 page is forked to `docs/templates/page_au-en/safety_en.rst` (copied from EU) via manifest `docs/manifests/manual_au-en.yaml`, while product-overview/operation-guide pages and shared pages still reuse the EU/shared templates. The AU manifest uses `docs/templates/page_shared/en/00_preface_single_language.rst`; keep that English-only component separate from the merged US `00_preface.rst`, whose EN/FR/ES language-tag blocks are invalid in a single-language AU bundle
   - phase2 table/view bindings now live in env names such as `FEISHU_PHASE2_LCD_ICONS_TABLE_ID` / `FEISHU_PHASE2_LCD_ICONS_VIEW_ID`; keep mirror-repo tenant differences in env or GitHub Secrets instead of committed config
   - `python build.py validate --config ...` now catches missing phase2 table base-token/table-id bindings and page-manifest languages that are not listed in `build.languages`
   - the LCD icons page is table-driven from `lcd_icons_blocks.csv`; `figure` attachments sync into `data/phase2/_attachments/lcd_icons/` and render as the LCD table image column, while symbols `Figure` attachments sync into `data/phase2/_attachments/symbols/` and render through `symbols_blocks.csv`; symbol signal structure lives in `symbols_blocks.csv` as `block_type=signal_row`; reusable short copy such as LCD / Symbols page titles, table headers, Symbols signal labels / meanings, Product overview labels, and spec titles is authored in `Manual_Copy_Source.csv`, translated from Translation Memory rows tagged `manual_copy`, and rendered from generated `Localized_Copy.csv` / `spec_titles.csv`; the US Spanish, French, and Brazilian Portuguese Product Overview templates now resolve their seven page/panel/part labels from the existing `product_overview.*` keys, while the EU raw-LaTeX Product Overview pages remain unchanged; image alt text is derived from existing titles, `symbol_key`, or generated signal labels; LCD status-word bolding reads `Status_Words.csv` exported from Translation Memory rows marked `是否为 status word=Y`; LCD `{{VARIABLE_KEY}}` placeholders resolve through `Variable_Defaults.csv`, then language-specific substitutions come from `Variable_Lang_Overrides.csv`
   - for variable defaults, keep `Model_key` as the text model selector when the Base `Model` field is a linked record; linked model fields can export as record ids and are not stable enough for build matching
   - `python build.py translation-memory --config configs/config.us.yaml --model JE-1000F --region US --query-text "USB-C 100W Port" --lang fr --table spec-master` reads the same snapshot as a compact multilingual memory lookup, which is useful when OpenClaw or a maintainer needs terminology grounded in the current Base content before translating copy
   - `python3 .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "Always follow these basic precautions when using this product." --source-lang en --target-lang fr --format prompt` is the higher-priority sentence-pair lookup when you already maintain a dedicated translation memory table in Feishu Base; on chat surfaces, treat it as background wording memory and answer with the translation itself instead of a narrated lookup step. The script keeps a short local cache for repeat lookups; use `--no-cache` only when you need a forced refresh.
   - For Taiwan Traditional Chinese, use `--source-lang zh --target-lang zh-TW`; the live Base stores Simplified Chinese in `zh` and Taiwan Traditional Chinese in `zh-TW`.
   - `python3 .agents/skills/manual-rewrite-with-tm/scripts/rewrite_markdown_with_tm.py input.md --target-lang de --use-feishu-term-source -o output.de.md` is the batch rewrite path when a full Markdown page or manual must follow TM wording, keep headings, tables, lists, and image links stable, and preserve unmatched source text as `==...==` instead of silently paraphrasing it
   - during that refresh, `Spec_Master.csv Slot_key` is normalized back to plain tokens like `front.label` when the source table stores markdown-link wrappers
   - the sync also resolves full field names through Base field metadata, so long columns like `Row_label_footnote_refs` do not disappear when the CLI view output abbreviates them
   - when `spec_master` is refreshed from the split source tables, linked-record style footnote refs like `{"id":"rec..."}` are converted to `Footnote_id` values before `Spec_Master.csv` is written
   - when one target references a `Footnote_id` that is missing only in its own region but exists as one unambiguous sibling-region row for the same model, validation and rendering now reuse that fallback definition instead of stopping the build immediately
   - the sync does not auto-fix bad `Is_Latest` data; if a latest row is wrong, keep it wrong in the snapshot and let validation stop the build
   - `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run` is the recommended first check on a new machine; it reports missing `lark-cli`, missing `FEISHU_PHASE2_*` bindings, and the `FEISHU_TRANSLATION_MEMORY_BASE_TOKEN` binding used for generated manual copy before any API fetch
   - `build.py` auto-loads `~/.auto-manual-phase2.env` (when that file exists) into the environment at startup, so the `FEISHU_PHASE2_*` / `FEISHU_TRANSLATION_MEMORY_*` bindings no longer need a manual `source` before `sync-data` or review — keep the secrets in that `$HOME` file (never committed). It never overrides a variable you already exported in your shell, and `AUTO_MANUAL_PHASE2_ENV_FILE` can point it at a different path
   - on Windows, the default `sync.phase2.cli_bin: lark-cli` is resolved to the installed shim automatically, so the normal shared config still works
   - when `spec_master` is part of that refresh, the command also regenerates [`../data/phase2/row_key_mapping.csv`](../data/phase2/row_key_mapping.csv) while preserving existing manual `Row_key` and `Remark` entries when possible
   - for future app-only DingTalk provider research, [`../tools/dingtalk/spike_cli.py`](../tools/dingtalk/spike_cli.py) is the manual Phase 0 smoke helper; it gets an App-Only token by default, then lets you supply the exact DingTalk list/update/upload endpoints for the chosen product without changing the current queue runtime
   - [`../tools/dingtalk/auth.py`](../tools/dingtalk/auth.py) now wraps the verified App-Only token flow behind `DINGTALK_CLIENT_ID`, `DINGTALK_CLIENT_SECRET`, and `DINGTALK_CORP_ID`, and [`../tools/dingtalk/workspace.py`](../tools/dingtalk/workspace.py) can already extract a target docs node ID from a standard `alidocs.dingtalk.com/i/nodes/...` URL
   - `python build.py process-review-start-queue --config configs/config.us.yaml --data-root .tmp/review-start/phase2` is the Start Review bridge: it reads `sync.phase2.review_init` rows where `是否进入Review` is checked and `Workflow_action` maps to `Start Review`, resolves the exact model/region target from `Document_Key`, and combines it with the language-range `Build_family` plus optional `Lang`. For example, both `JBP-2000B_US` and an ordinary US host row use `Build_family=us-merged`; the exact target selects `configs/config.bp-us.yaml` for JBP and `configs/config.us.yaml` for the host. The worker groups only the rows whose resolved config enables `build.queue_by_document_key`, syncs a fresh phase2 snapshot, always reseeds `docs/_review` from the latest `origin/main` template/data state, force-updates the review branch when it already exists, creates or reuses the PR, then writes the same `Git_ref`, `PR_url`, `Review_status=InReview`, and cleared `是否进入Review` state back to every row in that routed group
   - Start Review only starts when `Document_Key` is a non-empty `<MODEL>_<REGION>` value, `是否进入Review` is checked, and `Workflow_action` maps to `Start Review`
 - `Start Review` now means "force restart and reseed from the latest template". Existing committed `docs/_review/<model>/<region>/` content on `main` is no longer a duplicate guard, and re-checking `是否进入Review` on an `InReview` row will restart the review seed flow
 - **Print-only pages must live in the manifest, not in a hand-edited review index.** The seeded index is generated from the page manifest, so review-index includes with no manifest entry silently lose their references on every reseed — the page files stay in `page/` but leave the built book, and the target then fails the same-source IDML gate at Publish (incidents: 2026-08-13/14 reseeds → runs 31767694706, 31779053321). The JE-1000F/US print book's `00_toc.rst` and `99_back_cover.rst` are therefore declared in `manual_us.yaml` with `ordinal_neutral: true`: reseeds regenerate them deterministically, and the annotation keeps every later duplicate page's positional `pNN_` file name (e.g. `p22_01_fcc.rst`) unchanged — those names are pinned by the committed review branch and by the approved reference-layout contract's `source_ref` list. Never hand-add an include to a seeded index as a durable fix; declare the page in the manifest instead
 - [`../.github/workflows/feishu-start-review.yml`](../.github/workflows/feishu-start-review.yml) is the `main`-owned remote review-init worker that performs the same review-start flow from GitHub Actions after a Feishu workflow dispatch
 - review PRs created by that trusted Feishu Start Review worker automatically approve their `Manual Validation` and `Review Preview Package` checks; ordinary external pull requests still use GitHub's approval gate
 - `python build.py queue-query --config configs/config.us.yaml --queue-scope all --task-id "JE-1000F_US_0.3_Build Draft Package" --json` is the recommended local Phase 2 lookup before a natural-language OpenClaw action; it resolves the exact Feishu row and returns the `record_id`, `Task_id`, `Workflow_action`, `Git_ref`, `构建结果`, and the phase-aware `delivery_kind / delivery_url / delivery_ready` contract
 - `python build.py queue-resolve-action --config configs/config.us.yaml --query-text "发布 JE-1000F_US_0.3" --json` is the structured dry-run resolver for the control layer; it returns the bounded `action_name`, `resolution_status`, confirmation requirement, and matched row fields before any dispatch happens
 - for a fixed "现在库里构建了多少文档" lookup, run `python build.py queue-query --config configs/config.us.yaml --queue-scope document-link --result-contains success --limit 200 --json` and the same command with `configs/config.ja.yaml`, then count rows whose `normalized_workflow_action` is `draft` or `publish`; natural-language asks such as `当前所有已构建文档链接` now resolve to the same successful `Document_link` surface with a larger default limit
 - inside this repo, the OpenClaw-backed assistant is named **BlockClaw** because it works with content blocks; treat it as the default document-build operator that helps you build, review, publish, inspect queue rows, and explain failures for `auto-manual`, with translation and copy work acting as supporting helpers
 - `python build.py translation-memory --config configs/config.us.yaml --model JE-1000F --region US --query-text "USB-C 100W Port" --lang fr --table spec-master` is the repo-local terminology lookup that pairs well with OpenClaw translation asks; it keeps the prompt small by returning matched multilingual rows instead of dumping raw CSV tables
 - for one-shot sentence translation, prefer `bitable-translation-memory`; for whole-page or whole-file rewrite jobs that must preserve Markdown structure or unmatched-source fallback, pair it with `manual-rewrite-with-tm`
 - [`../integrations/openclaw/feishu-im-webhook-adapter/`](../integrations/openclaw/feishu-im-webhook-adapter/) is the repo-external Feishu IM webhook adapter for this control layer; it receives Feishu text messages, calls `queue-resolve-action|queue-query|queue-execute`, and replies back into the same Feishu thread
 - cloud-doc review backport is **not** an IM/BlockClaw capability — its LLM target-resolution is too uncertain for chat. Run it from Claude Code / Codex / a terminal via `python -m tools.backport.cloud_doc run-review-branch ...` (see the backport step below and AGENTS.md §3)
 - the adapter reads optional local-only profile files from `.openclaw/` for private aliases, reply phrasing, and Feishu message reaction choices; keep personal memory, real chat samples, and custom wording there instead of committing them to remote
 - set `FEISHU_IM_ENABLE_MESSAGE_REACTIONS=true` only after the Feishu app has message reaction permission; reactions are best-effort, the initial received-stage reaction defaults to `Get`, and the same-thread text reply remains the reliable status surface
 - when the live desktop entrypoint is the installed OpenClaw gateway rather than the repo adapter, run [`../integrations/openclaw/scripts/patch_openclaw_feishu_received_reaction.mjs`](../integrations/openclaw/scripts/patch_openclaw_feishu_received_reaction.mjs) before `openclaw gateway` starts; it adds the native Feishu `Get` reaction directly inside the `im.message.receive_v1` handler, before agent reasoning, table lookup, or build dispatch; it supports both the legacy bundled-`dist/` install and the OpenClaw ≥ 2026.6 `@openclaw/feishu` plugin layout under `~/.openclaw/npm/projects/openclaw-feishu-*/`
 - `python build.py listen-message-control --config configs/config.us.yaml` is the no-server local Feishu IM entry for the same control layer; it listens to `im.message.receive_v1` through `lark-cli` and replies in-thread without exposing a public callback URL
 - if the same machine must keep the old Feishu app for local phase2 operations, set `FEISHU_IM_LARK_CLI_HOME` before starting `listen-message-control`; that makes the new app use its own isolated `lark-cli` home instead of rewriting the default `~/.lark-cli`
 - for a long-lived ECS host, use the adapter `systemd` deployment assets under [`../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/`](../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/); the wrapper script sources the same `env.sh` you already use for manual startup
 - the same `queue-query --query-text` parser also understands `Task_id` strings such as `JE-1000F_US_0.3_Build Draft Package`, spaced asks like `帮我生成 JE-1000F US 0.3 草稿`, document-key-only review asks like `review JE-1000F_EU`, `开始 review JE-1000F us-merged`, and `为什么 JE-1000F US 0.3 构建失败`; if it can derive an exact `Task_id`, that selector takes priority
 - OpenClaw can also resolve config-scoped batch Draft asks such as `输出JE-1000F的所有欧规说明书文案`, `构建JE-1000F的所有欧规说明书文案`, `基于配置构建JE-1000F的欧规`, or the implicit-all form `构建JE-1000F的欧规说明书文案`; it maps `欧规` into a `Task_id` prefix like `JE-1000F_EU_`, keeps only `Build Draft Package` rows with `是否触发文档构建` enabled, and dispatches those rows by Feishu `record_id`. Draft and print Publish share a Document_link record concurrency slot; Web Publish uses one global publish-branch transaction slot. `是否强制刷新数据` remains the print/draft row-level input, while Web Publish always refreshes approved assets.
 - GitHub Actions artifacts are short-lived inspection/handoff copies rather than another archive: Draft/Start Review/Web Publish verification/preview/OpenClaw outputs keep 7 days, and selective print Publish release outputs keep 14 days. Formal print files live in the release tree; the Web candidate lives on `Hello-Docs/publish` and the production snapshot lives under `Hello-Docs/main:docs/publish/`; the nightly phase2 backup keeps its separate 90-day restore window.
 - exact OpenClaw Build Draft Package / Publish dispatches require the selected row's `是否触发文档构建` to be enabled; unchecked rows fail fast instead of launching a GitHub run that exits without output.
 - status-like asks such as `草稿包好了没`, `这个跑完了吗`, or `这个到哪了` resolve as status checks even when they mention draft/publish wording; pronoun follow-ups can reuse the last resolved `record_id` from the local adapter state, but build/trigger/rerun requests always resolve fresh from the current Feishu table instead of appending a remembered `record_id`
 - retry-style asks such as `补跑英语和法语`, `补构建法语`, or `重试这个` are treated as Build Draft Package intent; the adapter reuses only safe context such as model, market, version, and Git_ref, then resolves fresh queue rows instead of reusing the previous `record_id`
 - `queue-query` and `queue-resolve-action` accept `--langs en,fr` for bounded multi-language selection; natural-language asks can also use the registered Chinese/English aliases such as `英语`, `法语`, `西语`, `德语`, `意语`, and `日语`. Display labels and query aliases come from `tools/lang_registry.py`, so new language coverage is added at the registry rather than in each consumer. The fake `xx` end-to-end probe verifies that the same registry row flows through sync, localized copy, content lint, queue query, and preview labels; reference-bound IDML registration remains separately approved.
 - `tools/manifest_lint.py --json` provides a report-only page-manifest inventory check. It reports orphan manifests, invalid/missing sources, and language-set drift between each config and its manifest; it does not alter build or approval gates.
 - `tools/manifest_family.py` provides the non-mutating family-manifest pilot. Its `diff` command writes a deterministic JSON-Pointer carrier and its `roundtrip` command applies that carrier in memory and checks canonical manifest bytes; it does not rewrite source manifests or change build assembly.
 - `tools/manifest_family.py fold --index docs/manifests/family/index.yaml` validates the full fold inventory: 2 anchor manifests plus 15 carriers cover all 17 current manifest files. `--write` refreshes only the JSON carriers and remains explicit.
 - The `Manifest Regenerate and Diff Guardrail` workflow runs the fold check for manifest/config changes, so a manually edited generated YAML fails CI when its carrier no longer rebuilds the same canonical bytes.
 - `queue-query`, `queue-resolve-action`, and `queue-execute` accept `--fresh-since <iso-or-epoch>` so status replies can distinguish this-run writeback from older row results; Document_link JSON rows include `freshness_status`, `result_built_at`, `result_is_fresh`, and `build_started_at`
 - `queue-query --json` includes `matched_count`, `returned_count`, `limit`, and `truncated`; if a broad query hits the default limit, treat `truncated=true` as an incomplete answer and re-run with narrower filters or a higher `--limit`
 - broad latest-link asks such as `构建好的文档链接发我` return successful latest-version rows per `Document_Key`, while inventory asks such as `当前所有已构建文档链接` keep all successful rows up to the larger inventory limit
 - batch delivery replies in Feishu IM are sent as one status summary plus one message per `delivery_url`; short follow-ups such as `发` or `发一下` reuse the previous batch context and resend those phase-aware links instead of flattening them into one plain-text block
 - adapter conversation memory is never the build truth source: `这个好了没` re-reads Feishu by `record_id`, and if a remembered row has been deleted or moved, BlockClaw reports it as not found and clears that context instead of replaying the old row
 - `python build.py queue-execute --config configs/config.us.yaml --query-text "请帮我构建 JE-1000F_US_en_0.3，并返回 Build Draft Package 记录。只返回 record_id、Git_ref、构建结果和 delivery_url。"` is the recommended deterministic execution entry for natural-language OpenClaw build asks; it resolves the Feishu row, dispatches the matching `main`-owned workflow, waits for completion, and then re-reads the Feishu row before returning the final fields plus `accepted_at`, `run_id`, `run_url`, and `freshness_status`. OpenClaw must not first run local `check` / `word` / `sync-data` or inspect `data/phase2/*.csv`; the remote worker owns the row's `是否强制刷新数据` behavior.
 - if the GitHub run finishes but the Feishu row still only has a pre-dispatch `FAILED` or `SUCCESS`, OpenClaw reports `freshness_status=stale_result` or `writeback_pending` instead of treating that old row value as the current run result
 - a local observation gap is never reported as an action failure: once GitHub accepts a dispatch, a transient `status`/poll error, a `control-layer ... fetch failed`, or a wait-deadline timeout makes `queue-execute` defer to the authoritative Feishu/Base writeback (`freshness_status`) instead of raising — it reports a failure only when the GitHub run reaches a genuine terminal failure **and** the row is still not fresh; `/manual-status` likewise returns the last known run state plus an `observation_error` line rather than erroring out, because the remote run keeps going regardless of whether the local poller could read it back
 - builds report results on an accept-first lifecycle, never by holding the chat turn open: the dispatch reply and `/manual-status` carry `state: accepted|processing|completed|failed` plus a `note:` pointing back to `status last`, so an in-flight run reads as `任务正在处理中` (not a failure). On the Feishu IM adapter a single-record build replies "已受理（处理中）" immediately, dispatches with `--no-wait`, and does **not** poll; progress is delivered **on demand** — when you re-ask "这个好了没", the adapter reads the authoritative state at that moment (a fresh Base writeback wins → `已完成`/`失败`; otherwise it reads the live GitHub run once via the remembered `run_id` → 仍在跑=`处理中`, run 已失败但未写回=`失败`, run 完成但结果未落表=`处理中`) and answers 处理中/已完成/失败. Single read per question, not polling
 - against the Feishu message control plan, the repo now has the full repo-local Phase 2 stack: query, deterministic execute, structured failure replies, explicit Publish confirmation, and a standalone Feishu IM webhook adapter are all live. Encrypted callback support and ECS deployment assets are now repo-owned; the remaining gaps are shared state and a stable named ingress rollout.
 - if you keep using `trycloudflare.com`, only the process restart becomes stable; the callback URL itself still changes after a tunnel restart. For a stable URL, switch the same adapter to a named Cloudflare Tunnel or another fixed HTTPS ingress
 - if `queue-execute` resolves `Workflow_action = Publish`, add `--confirm-publish`; otherwise it now stops before dispatch
 - repo-local OpenClaw dispatch no longer treats `adm-zip` as a required local install just to send a Build Draft Package or Publish dispatch from ECS; metadata artifact parsing is now best-effort, so missing package installs degrade status detail instead of blocking dispatch
 - when a `Start Review` worker fails before Feishu writeback, the worker now writes a structured failure summary into `openclaw-run-metadata`; OpenClaw status and `queue-execute` surface that summary directly, for example `缺少 JE-1000F_CN 的规格数据，无法进入 review。`
 - `queue-execute` treats a `Start Review` row that already has `Review_status=InReview` and `Git_ref` as completed and returns the current row without dispatching another Action; otherwise OpenClaw dispatches `start-review`, `build-draft`, and `publish` with the resolved Feishu `record_id` so the GitHub run and final writeback stay tied to that exact queue row
 - if the Start Review workflow is dispatched with one explicit `record_id` but the GitHub worker cannot re-read that row as pending from the current Feishu view, that run now emits a structured failure summary instead of ending as a silent success; if the row is already `InReview`/`ReadyForPublish` with `Git_ref`, the duplicate dispatch is treated as an idempotent success even when `Workflow_action` has already advanced to a later stage (e.g. `Build Draft Package`)
 - for a multi-target build (several targets at once, or one model across regions), use `queue-execute --allow-multiple`. It validates every matching row, runs the same warning-only target-bound asset preflight for each Draft/Publish row, then starts one batch worker run per queue action with the exact eligible record set, so the third pending target cannot be silently lost or accidentally replaced by another pending row. The command returns a per-record JSON report (`matched_count` / `dispatched_count` / `skipped_count` / `error_count` + `results` with `record_id`/`run_id`/`status`/`reason`/`asset_preflight`); all dispatched rows from one action share the same `run_id`. It is accept-first (no completion wait). Report only rows returned as `dispatched` (with a `run_id`) as actually started — never infer "已进队" from the trigger flag — and ask for a complete target name (e.g. `JE-1000F_CN_1.3`, not `JE-1000F_CN`) when a version is missing
- `python build.py process-build-queue --config configs/config.us.yaml` is the optional Feishu task-table bridge: it reads the historically named `sync.phase2.document_link` binding where `是否触发文档构建 = Y`, first writes and verifies a two-hour `claim_token` lease in `构建结果`, writes `开始构建时间` when that field exists, resolves the config from the exact `Document_Key` target plus language-range `Build_family` and optional `Lang`, groups only the rows whose resolved config enables `build.queue_by_document_key`, runs `sync-data` only when that row group has `是否强制刷新数据 = true`, builds Draft rows as `check -> word -> md`, upgrades Publish rows to `check -> diff-report -> word -> pdf -> md -> idml`, and uses phase-aware delivery fields: Draft imports the built Word `.docx` into editable `飞书云文档` plus frozen `基线文档`, Publish uploads the designer handoff ZIP and writes its knowledge-base link to `idml_file`, and Web Publish records a pending `HTML_link` registration (the actual write happens post-merge, see below). It also writes the local DOCX release path into `Document directory`, optionally writes `Document link_dd` for a mirror, writes a timestamped status into `构建结果`, writes the refresh result into `data_sync`, clears `是否强制刷新数据`, and flips the trigger back to `已构建` on success. The retired `Document link` field is not an upload-success signal.
   - for `build.queue_by_document_key` configs, Draft rows with a non-empty `Lang` are grouped by `Document_Key + normalized Lang`; `br` / `pt-br` normalizes to `pt-BR`, and the selected language is passed to build/check/validate/bundle/output resolution. `configs/config.pt-br.yaml` is now a single-language entrypoint, so Brazil Portuguese draft rows should use `Build_family = pt-br` with `Lang=br` or `Lang=pt-BR` instead of adding an English companion row.
   - when a row group starts, `构建结果` is first written as `RUNNING | ... started_at=... | claim_token=... | claim_expires_at=...`; the worker bypasses the pending view to read every row back and only the matching unexpired token continues. Active leases are skipped, expired leases can be retried, and final `SUCCESS` / `FAILED` writeback releases the lease. This is a verified lease because Feishu upsert has no compare-and-swap; workflow-level concurrency is maintained separately.
   - if that queue row has a `Version`, Build Draft Package DOCX/Markdown names use `manual_<model>_<region>_<lang>_<Version>.docx|md`, while Publish queue release artifact names use `manual_<model>_<region>_<lang>_publish_<Version>.docx|pdf|md`; Draft exposes the imported `飞书云文档`, while Publish exposes the packaged designer handoff through `idml_file`
   - the frozen baseline (`基线文档`, a second import of the same Word `.docx`, used only for backport render-vs-render diffing) is imported with a `_基线<YYYYMMDD>` name suffix (e.g. `manual_je1000f_us_en_0.1_基线20260706`), so it is distinguishable in the review-doc wiki node from the editable `飞书云文档`, which keeps the base name
- Within one `process-build-queue` invocation, a successful forced phase2 sync is memoized per config/data-root pair; later groups reuse that snapshot, while a failed sync is not memoized and remains retryable.
- `Workflow_action = Build Draft Package` rows must carry `Git_ref`; queue builds seed a temporary worktree from the latest `origin/main`, then overlay only the active `docs/_review/<model>/<region>` target from that review branch. Sibling targets remain exactly as they are on `main`, so one review branch cannot dirty or replace another target during queue Publish.
- 对已登记 approved reference-layout 的目标，Print Publish 的检查、DOCX、PDF、Markdown 和 IDML 全部读取同一份 `review-asis` 冻结内容。勾选「是否强制刷新数据」仍会刷新并归档 phase2 snapshot、供资产解析使用，但不会在 Publish 阶段把最新线上字段回写进已审核页面。若确实要发布新的线上文案，先同步或重新播种 review、完成版面复核并显式重批 content contract，再触发 Publish。未登记批准合同的目标继续使用原有 `review` 参数同步。
  - on a local worker, if a same-named local `Git_ref` branch already exists, the queue uses that local branch directly so you can verify and upload review updates before pushing them
  - if GitHub is briefly unstable but that same `origin/<Git_ref>` or local branch is already cached on the worker, the queue will reuse the cached ref and continue building from the intended review branch
   - queue rows use `Workflow_action` only: `Start Review` to force restart/reseed review branches, `Build Draft Package` for review-stage rebuilds, `Publish` for print release artifacts, and `Web Publish` for the responsive RTD manual; leave `Doc_phase` blank. For Start Review, `Document_Key` is enough; if the table exposes `Task_id`, use `Document_ID + "_" + Workflow_action` mainly for versioned build/publish rows.
   - if `Document_Key` is a linked Base field, OpenClaw uses `Task_id` as the stable Start Review selector and then checks `是否进入Review` plus `Workflow_action=Start Review`
   - when review-init reuses the shared `Document_link` view, each worker consumes only its own action; Web Publish cannot be consumed by the print Publish worker
   - Build Draft Package outputs stay under the current repo [`../docs/_build/`](../docs/_build) tree by default; pass `--staging-root <dir>` or set `AUTO_MANUAL_STAGING_ROOT=<dir>` to isolate generated `docs/_build`, `reports/version_tracking`, and `reports/releases` under that root instead
- `Build_family` only expresses the queue row's language range: `us-merged`, `eu-merged`, `us-en`, `eu-en`, `us-es`, `us-fr`, `pt-br`, `jp-ja`, or `cn-zh`. Product/skeleton identity comes from `Document_Key`; target-specific configs declare the accepted row language family through `build.language_family`. `Lang` remains optional compatibility/narrowing data.
- merged US/EU Start Review, Draft, and Publish rows should use `Build_family = us-merged` / `eu-merged` and may leave `Lang` blank; single-language rows should use the matching language family such as `us-en` / `eu-en` / `us-fr` / `us-es` / `pt-br`. JBP does not use a special Base value: `JBP-2000B_US + us-merged` resolves the BP skeleton by exact target.
- config policy for `build.queue_by_document_key`: enable it for merged whole-book families that intentionally produce one shared manual across multiple languages, such as today's `us-merged`, `eu-merged`, and future `cn-merged`; keep it disabled for single-language families such as `us-en`, `eu-en`, `us-fr`, `us-es`, `pt-br`, `jp-ja`, `cn-zh`, or future `eu-de` / `eu-fr`, which should continue to run one queue row per `record_id`
   - print Publish stages IDML/LaTeX/DOCX/PDF/ZIP/Markdown under the Git-ignored runtime tree [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases), delivers formal files through Feishu or short-lived GitHub Actions artifacts, and does not deploy HTML or commit those generated files. Web Publish always refreshes approved Web assets, seals MyST plus verification HTML under `versions/<version>/web/` and immutable metadata at `versions/<version>/web_publish_meta.json`, then atomically updates `latest/web/publish_meta.json`. Exact retries leave the seal untouched; drift fails before queue success. It then freezes only Web source/assets in the `Hello-Docs/publish:docs/publish/` candidate and opens or updates a `docs/publish/**`-only PR into `Hello-Docs/main`; the deterministic RTD route is recorded as a pending registration, and [`web-publish-receipt.yml`](../.github/workflows/web-publish-receipt.yml) writes it to `HTML_link` only after that PR merges and the live deployment verifies; see the [`OPS-04a local seal contract`](../code-as-doc/dev/ops_04a_web_version_seal.md).
   - After a Git-only publication reaches RTD, the [deployment receipt check](../code-as-doc/dev/rtd_deployment_receipt.md) compares the exact frozen source and served HTML/assets. The portal Sphinx build emits the receipt automatically; checking it needs no queue or online-table write. Its internal cache probes avoid stale or optimized CDN responses, and incomplete transfers are retried within fixed limits; original asset hashes must still match. Formal publication-link writeback remains a separate action.
   - [`../scripts/process_build_queue.ps1`](../scripts/process_build_queue.ps1) is the Windows automation wrapper for that queue bridge; it restores the local Node/npm path plus the saved `FEISHU_PHASE2_*` user env vars, then writes logs into [`../.tmp/process-build-queue/`](../.tmp/process-build-queue) and forwards extra queue args such as `--dry-run` or `--record-id`
   - the queue code lives in [`../tools/build_queue/`](../tools/build_queue) since CQ-1.4; run it as `python -m tools.build_queue.process_build_queue …` from the repo root (or through `build.py` / the wrapper scripts)
   - [`../scripts/process_build_queue_feishu.ps1`](../scripts/process_build_queue_feishu.ps1) is the one-click Feishu-only queue entry on Windows; it fixes the primary upload target to Feishu/wiki
   - the DingTalk AliDocs mirror-upload chain was retired on 2026-07-02 (its one-click queue entry, session-upload CLI, and setup guide were removed); Feishu/wiki is the only artifact upload target
   - `python build.py listen-build-queue --config configs/config.us.yaml` is the push-based immediate-build listener: after the Feishu app has the `drive.file.bitable_record_changed_v1` event enabled, it subscribes the table and keeps the long connection on the same current user identity, then triggers `process-build-queue` immediately when `Document_link` rows are checked in `是否立即构建`
   - [`../scripts/listen_build_queue.ps1`](../scripts/listen_build_queue.ps1) is the Windows wrapper for that listener; it restores the local Node/npm path plus the saved `FEISHU_PHASE2_*` user env vars and writes logs into [`../.tmp/build-queue-listener/`](../.tmp/build-queue-listener)
  - [`../.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml) is the `main`-owned remote print Publish worker. [`../.github/workflows/feishu-web-publish-queue.yml`](../.github/workflows/feishu-web-publish-queue.yml) is the independent business-plane Web worker; it serializes writes to the generated `Hello-Docs/publish` candidate and maintains the scope-guarded PR into `main`.
   - its XeLaTeX/CJK apt downloads are cached by runner OS, architecture, and the checked-in `.github/texlive-apt-packages.txt` package-set hash; every run summary shows cache hit/miss plus install time. Use the boolean `texlive_smoke_only` dispatch input to run the deterministic PDF/cache acceptance path without selecting or changing any Feishu queue row.
   - if you want remote immediate builds, create a Feishu workflow whose combined condition is `是否触发文档构建 = Y` and `是否立即构建 = true`, then dispatch the workflow matching `Workflow_action`; the queue still only builds rows whose trigger field is `Y`
 - that remote bot flow requires the Feishu app/bot to have read access to the phase2 source tables and write access to the `Document_link` table; otherwise it can detect pending rows but cannot write back `开始构建时间` or `构建结果`
 - give the user/bot identity edit/container permission on the review-doc wiki parent node if the imported Draft cloud doc must land there; otherwise `飞书云文档` keeps the import URL and the status records the best-effort move warning
 - `python build.py md` and queue Markdown outputs reuse the Word bundle HTML path; the exporter prefers native MyST when Pandoc provides it and otherwise emits MyST-compatible CommonMark with pipe tables. Each generated `md` directory carries `conf.py`, `index.md`, and local `assets/`; RTD then uses `tools/readthedocs_source.py` to assemble the selected target directories into one catalog source under `docs/_build/rtd/`.
 - if you also want the remote GitHub Draft/Publish workers to mirror to DingTalk, configure GitHub Secrets `DINGTALK_DOCS_A_TOKEN`, `DINGTALK_DOCS_XSRF_TOKEN`, and `DINGTALK_DOCS_COOKIE`, then explicitly set the GitHub Actions repository variable `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session`; `DINGTALK_DOCS_TARGET_NODE_URL` is optional and only acts as the remote default target
 - when DingTalk mirror sync is enabled, Feishu still remains the queue control plane and canonical writeback surface; `Document link_dd` is supplemental mirror writeback and never replaces the phase-aware `delivery_url`
 - when Feishu is primary and DingTalk is only the mirror, mirror target/session errors no longer abort the whole row; the queue still writes the Feishu result and records the DingTalk problem as `dingtalk_sync=failed`
 - if the row also has `是否上传钉钉`, that checkbox becomes the row-level DingTalk gate: checked rows also sync DingTalk, unchecked rows stay on the normal Feishu/wiki path for that run
 - if the table does not have `是否上传钉钉`, the worker follows the current global worker mode for that whole row
 - if that checked row also has `DingTalk_target_node_url`, the worker uploads to that row-level target first; if it is blank, the worker falls back to the global `DINGTALK_DOCS_TARGET_NODE_URL` when present
 - if the row also has `operator_union_id`, the worker can resolve a per-operator DingTalk session file from `AUTO_MANUAL_DINGTALK_SESSION_ROOT` before falling back to the global browser-session envs
 - `DingTalk_session_key` and `钉钉会话键` are accepted as aliases for `operator_union_id`; if a row uses `alice`, the worker expects `<session_root>/alice.json`
 - if a DingTalk-enabled row points at a missing per-operator session or there is no usable global DingTalk session, the queue now fails that row before build starts and writes the missing-session reason back to `构建结果`
 - `钉钉上传节点` is accepted as a compatibility alias, but prefer `DingTalk_target_node_url` for new tables
 - for OpenClaw Phase 2, use `delivery_ready` as the completion predicate and return `delivery_url` with `delivery_kind`: Draft=`飞书云文档`, Publish=`idml_file`, Web Publish=`HTML_link`. `Document link` / `document_link` is retired and must never be used to infer Draft upload status; `Document link_dd` remains optional supplemental mirror writeback
 - **delivery outbox (DingTalk hand-off)**: set `AUTO_MANUAL_DELIVERY_OUTBOX_ROOT` on a worker to have every successful Publish also drop its artifacts into `<root>/<job_id>/` together with one `delivery_manifest.json`. With the variable unset the whole path is inert, so nothing changes for workers that do not deliver. Point it at an ignored directory outside the git tree — the repo ignores `/output/`, so `output/outbox` inside either checkout works
 - the drop covers Publish only (a Draft's deliverable is the Feishu cloud doc, and Web Publish has no artifact sink) and carries the print PDF, handoff zip, Word, and Markdown; `latex/` and `html/` render trees are deliberately excluded
 - the queue reports the outcome in `构建结果` next to `dingtalk_sync=*`: `delivery_outbox=ok` plus `delivery_outbox_job=<job id>`, `delivery_outbox=skipped` when that target is not mapped for DingTalk delivery (a normal state, not a fault), or `delivery_outbox=failed` plus `delivery_outbox_error=<reason>` when a mapped target could not be dropped. A delivery problem never fails the row: the artifact has already reached the knowledge base by then
 - which targets are delivered is a data contract, [`data/dingtalk_delivery_map.csv`](../data/dingtalk_delivery_map.csv): one row per `(model, region)` mapping to the DingTalk 项目代码 + 安规 + the 文案语言 set that region's book covers. Publish rows leave `Lang` blank and produce one whole-book bundle, so the map is deliberately keyed by region rather than by language. Add a row only after checking the 安规/语言 values against the live base
 - the manifest is immutable build output and carries `delivery_key`, a digest over target + version + artifact hashes. The delivery agent owns progress (its own `status.json` beside the manifest) and must dedupe on `delivery_key`: a rebuild legitimately produces a second job, and a runner that loses its queue claim mid-publish can leave a job whose row was never written
 - operator housekeeping: consumed job directories are not reclaimed automatically, and a second Publish of the same target/version inside the same second is refused rather than overwritten. Clear delivered jobs periodically — they hold full PDFs and zips
  - that queue worker reuses the same phase2 env-bound table/view configuration as `sync-data`; it additionally needs `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` plus `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`, auto-derives the current wiki destination from the same base when possible, and optionally accepts `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` to force a different parent wiki node
   - [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv) remains repo-maintained; `sync-data` copies it into isolated `--data-root` snapshots such as `.tmp/review-start/phase2`
   - page selection/applicability and [`data/layout_params.csv`](../data/layout_params.csv) remain repo-maintained inputs
   - Safety intro pages are maintained in [`docs/templates/page_*/safety_*.rst`](../docs/templates); the standalone user maintenance instructions page is maintained in shared templates such as [`docs/templates/page_shared/en/01_user_maintenance_instructions.rst`](../docs/templates/page_shared/en/01_user_maintenance_instructions.rst) and is included immediately before `symbols`; JP keeps the detailed safety warnings in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst). The old `content_blocks.csv` safety source has been removed from the active repo flow
   - `Spec_Footnotes.csv` now holds only reusable spec footnote definitions; `Footnote_order` controls the rendered superscript marker order and `Footnote_id` is referenced from `Spec_Master.csv`
   - CSV/PDF and IDML use one shared footnote-marker rule: comma-separated IDs retain their order and repeated IDs print once. Existing language fallback and target selection remain unchanged.
   - `Spec_Footnotes.csv` and `Spec_Notes.csv` both carry a `Type` field from the Feishu source; keep it explicit as `Footnote` or `Note` so downstream renderers do not infer type from the visible text
   - `Spec_Notes.csv` holds bottom-of-spec notes that are not tied to superscript references, such as trademark statements
   - `Spec_Footnotes.csv` and `Spec_Notes.csv` now match rows by `Region` + `Model`; `project_code` / `项目代码` is no longer used there either
   - when one spec page renders both bottom notes and bottom footnotes, the final output order follows the template named by the `spec` row of the `page_registry.csv` the build reads (each frozen `manual_sources/.../phase2` source carries its own; `data/phase2/page_registry.csv` serves every live target): the default [`docs/templates/spec_template.rst`](../docs/templates/spec_template.rst) puts the notes (such as the ※ trademark note) first, and [`docs/templates/spec_template_footnotes_first.rst`](../docs/templates/spec_template_footnotes_first.rst) puts the footnotes first, for sources whose approved print does. Only the Web and the Word bundle (which takes its trailer order from the HTML) follow that choice; the PDF and IDML output is the same for both
   - `Spec_Master.csv` uses `Row_label_source`, `Param_source`, and `Value_source` as the shared source-language columns; `Source_lang` stores that source-language code explicitly, for example `en`, `ja`, and `zh`, and code no longer infers it from `Region`
   - `Spec_Master.csv` now starts with `spec_row_key`; `document_key` is still the target dimension, but not the unique row key
   - Specification rows sharing `Row_key` retain their distinct localized labels and label footnotes. Equal labels remain multiline groups; differing labels are separate rows ordered by `Line_order` within that group. Keep the released manual's port names in the source instead of relying on inferred wattage labels.
   - `document_key` is a derived helper column and may use either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`
   - `Line_order` is required for spec rebuilds: use `1` for one-line rows and `1`, `2`, `3`, ... for multi-line values
   - the solar-panel input range in the eight shared-language charging-method pages comes from `页面占位参数`: use `Page=charging_methods`, `Row_key=pv_input_range`, `Slot_key=value`, and preserve the approved language-specific dash/spacing exactly; the template token is `|PV_INPUT_RANGE|`. The current JE-1000F US/EU/AU/KR and JE-1500D pt-BR rows were F6-approved, seeded, and read back on 2026-07-31; a future target still needs its own exact-value approval plus post-sync `diff-report`
   - the connector name in those charging pages uses `Page=charging_methods`, `Row_key=dc_input_connector`, `Slot_key=value` and token `|DC_INPUT_CONNECTOR|`; the shared UPS transfer time uses `Page=ups_mode`, `Row_key=ups_transfer_time`, `Slot_key=value` and token `|UPS_TRANSFER_TIME|`. Keep localized units in the value and keep the separate `0 ms` incompatibility caution as prose. The same five current document keys were seeded in the 2026-07-31 F6 batch; never blindly clone their values into a new target
   - `Row_label_en`, `Param_en`, and `Value_en` are no longer supported; rename them to `*_source`
   - `Row_label_footnote_refs`, `Param_footnote_refs`, and `Value_footnote_refs` store comma-separated `Footnote_id` values; do not handwrite `①②③` into visible spec text
   - `symbols_blocks.csv` uses `Market`, `Model`, and `Source_lang`; it does not use `Region`; use `Market=Global` when one symbols row is shared across markets
   - `symbols_blocks.csv` uses `image_path` for the icon asset referenced by each symbols-table row; phase2 sync fills it from the Base `Figure` attachment when present
   - `symbols_blocks.csv` can also use `Is_Latest` and `Market` as row conditions: rows marked false are skipped, and `Market` must include the current build region such as `US` or `EU`
   - use `block_type=table_row` for the normal symbol/meaning grid; use `block_type=signal_row` for signal metadata, with rendered `symbol_key` values `warning`, `caution`, `note`, and `tips`, plus labels such as `danger` that Word/HTML rewrite should recognize
   - `order` values must be unique within each symbols table section; normal symbols rows are sorted and split evenly into two columns, so the old `column_group` field has been removed

3. Review working layer
   - [`docs/_review/<model>/<region>/index.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/page/*.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/generated/<model>/*.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/manifest.json`](../docs/_review)
   - [`docs/_review/<model>/<region>/overrides/**`](../docs/_review)
   - Responsibility: target-specific review editing, Git review, revision history, final release source after review starts
   - Accepted Feishu cloud-doc revisions back-port through `python -m tools.backport.cloud_doc run-review-branch --doc-name <doc name> --cloud-doc <url>` (equivalently `python -m tools.backport.cloud_doc …`; the code lives in `tools/backport/`) — the blessed path: it resolves the review branch, diffs the cloud-doc against a **render baseline** (so deltas are the reviewer's real edits, not RST-source noise), and with `--write --push` applies only Class R prose and opens a draft PR into the review branch. The older `run-review --doc-url ... --source-path docs/_review/...` diffs against the RST source and is now **guarded**: a `--write` against an `.rst` baseline is refused and steered to `run-review-branch` unless `--allow-rst-baseline` is set. The runners write diff/apply/run reports and are dry-run by default. Add `--write` only after reviewing the apply report; write mode patches guarded review prose, runs residual verification, and marks the run `PR_READY` only when the review source changed and verification passed. Data-like deltas stay report-only and also get `cloud_doc_backport_source_table_suggestions.md` with candidate source tables and operator steps. Use `python -m tools.backport.cloud_doc open-pr --manifest reports/cloud_doc_backport/<run-id>/cloud_doc_backport_run.json` only after `PR_READY`; it commits the changed `_review` source to a draft PR and leaves local reports out of the commit.
   - you do not have to remember the backport: the daily [`../.github/workflows/backport-reminder.yml`](../.github/workflows/backport-reminder.yml) sentinel compares every InReview cloud doc against its committed render baseline and opens/updates a `[backport-reminder]` issue while un-backported edits exist (report-only; running the backport advances the baseline and the issue closes itself)
   - the operator-facing playbook for the whole closed loop (revision ledger commands, TM harvest approval, sentinel handling, annotated PDFs, first-run checklist) is [`./closed_loop_ops_guide.md`](./closed_loop_ops_guide.md)

   - Cloud-doc backport strips Feishu highlight tags before writing reports, keeps image-only/token-only changes out of source-table suggestions, resolves page-value rows to `Page_Placeholders_Source` when the phase2 value index and record sidecar identify the row, and requires human semantic review for output/button terminology swaps. If GitHub rejects automatic PR creation after the branch push, use the printed compare link and PR body to create the draft PR manually.

4. Runtime build layer
   - [`docs/_build/<model>/<region>/rst/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/html/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/word/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/pdf/**`](../docs/_build)
   - [`docs/index.rst`](../docs/index.rst)
   - Responsibility: generated bundle plus final outputs

Rules:

- Before review starts, use template/data to create the first draft.
- To move one document into review automatically, trigger the review-init flow first; that flow creates the branch, seeds `docs/_review`, and opens the PR.
- After review starts, use [`docs/_review/...`](../docs/_review/) as the daily editing surface for that target.
- Edit templates only when the change should be shared by multiple manuals.
- For manually maintained parallel-language template pages, keep one source-language template as the structure owner and update the derived-language templates in the same change when shared headings, section order, placeholder sets, includes, or `.. only::` model gates change.
- Current example: if `charging.rst` changes in the source-language family template, keep the same battery-pack `.. only:: model_je_2000e` block boundary in the corresponding derived-language templates instead of updating only one language.
- Edit CSV when product parameters change.
- Treat [`docs/_build/...`](../docs/_build/) as generated runtime output.
- Keep region-family differences explicit where they are real: spec data, certification text, unit conventions, and `meaning_of_symbols` stay family-specific.
- When design needs to review layout or page effect, share a review handoff workspace built from `_review`, not the raw `.rst`.
- when that workspace is packaged for review sharing, let GitHub Actions build the package first and keep it as an artifact
- Read the Docs renders the frozen Web Publish catalog from `Hello-Docs/main:docs/publish/web/` after the generated publish PR is merged; it does not replace review-preview packaging or formal print release outputs
- designers should start from the workspace root, then pick a family, model, and language before opening the rendered manual or family diff page
- the workspace root now keeps the primary review actions plus a compact document-identity card with product name, manual title, model, region, and language
- the packaged preview now also includes model-scoped `downloads/<family>/<model>/<lang>/review-manual.docx`, `downloads/<family>/<model>/change-report.xlsx`, the raw diff CSV files, and `generated/workspace.json`
- families without `_review` content are hidden, so the preview only shows available families
- the packaged `changes/index.html` now opens a family hub first, and each family hub fans out to model-specific change pages
- if the target branch already has an open pull request, each new push to that PR branch will rerun `Review Preview Package` automatically when the changed files match the workflow paths
- after that workflow finishes, download the uploaded artifact when you need the packaged review workspace; it is no longer pushed to Vercel automatically
- if there is no open pull request yet, trigger `Review Preview Package` manually from the `Actions` tab

---

## 3. Current Build Pipeline

The cross-platform entrypoint is [`build.py`](../build.py).
It wraps [`tools/build/docs.py`](../tools/build/docs.py), which still drives the actual build logic.
If you need the fixed `US/en + US/es + US/fr + JP/ja` export set, use [`../scripts/build_us_jp_manuals.ps1`](../scripts/build_us_jp_manuals.ps1) as a thin wrapper over [`../scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py).

Current flow:

1. `python build.py sync-data|process-build-queue|message-control-dry-run|rst|html|word|pdf|all|idml|review|check|asset-check|asset-intake|sync-review|publish|diff-report|release-manifest|handoff|preview|fast|doctor`
1. `python build.py listen-message-control --config configs/config.us.yaml`
2. [`tools/build/docs.py`](../tools/build/docs.py) validates config and layout params
3. target `model` and `region` are resolved from CLI or `build.targets`
4. `product_name` is resolved from the active snapshot root, defaulting to [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv); explicit `--data-root` still overrides the default
5. CSV-backed pages are generated by [`tools/csv_page_build.py`](../tools/csv_page_build.py)
6. [`tools/gen_index_bundle.py`](../tools/gen_index_bundle.py) materializes the runtime bundle
7. the runtime bundle is written to [`docs/_build/<model>/<region>/rst/`](../docs/_build)
8. if source mode is `auto` or `review` and a review bundle exists, review content is overlaid onto the runtime bundle
9. after frozen attachment aliases are staged, the asset finalizer scans the final `index.rst` include closure, resolves semantic `asset:` references for the exact model/region/language, rewrites final bundle-relative paths, and freezes the bundle's asset evidence
10. [`docs/index.rst`](../docs/index.rst) is refreshed to point at all existing bundle roots
11. `html`, `word`, and `pdf` outputs are built from the prepared bundle when requested
12. `python build.py review` seeds [`docs/_review/<model>/<region>/`](../docs/_review) from the runtime bundle when review starts; semantic asset identities are restored from the runtime rewrite provenance before review files are written
13. `python build.py sync-review` refreshes parameter-driven review files from the runtime bundle without replacing the whole review bundle
14. `python build.py check` runs config/layout validation, prepares the bundle, and scans for bundle issues
15. `python build.py asset-check` validates the image-asset registry and resolves approved exports for renderer imports; `--allow-temporary` is diagnostic/operator inspection for `asset-check` only, while normal bundle assembly always rejects temporary, missing, and quarantined semantic assets; `--publish` is the stricter registry-wide status gate; `--refresh` dry-runs a machine recomputation of materialized SHA-256 values and requires explicit `--write` for an atomic registry update, with missing/malformed exports failing closed
    - editable `.ai` deliveries stay out of Git; the maintainer follows [`closed_loop_ops_guide.md` §4.9.2](closed_loop_ops_guide.md#492-ai-交付与登记一页流程) for hash-first duplicate detection, upload to the dedicated Base asset-source table, and download verification; the legacy illustration table is not a fallback
    - sensitive App/QR candidates remain quarantined after extraction; a registry row may declare `source=reviewed-promotion:<promotion_id>` only when its JSON contract under `data/asset_promotions/` still matches the reviewer decision, exact target scope, source AI/reference PDF/recipe/evidence identities, all candidate/output bytes, and deterministic composition by full SHA-256. During the carrier migration, the Python compatibility shadow is read in parallel and exact parity plus the whole-contract SHA-256 are required; any drift fails closed without a legacy-image fallback. Contracts are per target: `je1000f-us-app-ui-v1` covers JE-1000F/US en/fr/es and `je1000f-eu-app-ui-v1` covers JE-1000F/EU en/fr/es/de/it/uk with the EU print's own App screens; pages must reference `asset:app/add_device` / `asset:app/connect_result` (review pages with raw `common_assets/app/*.png` paths keep the shared JP-market images)
16. `python build.py asset-intake --asset-source-key <key> --asset-source-file <master.ai> --asset-recipe <recipe.json> --asset-output-root <new-dir>` freezes and verifies a PDF-compatible Illustrator source, then writes cleaned page archives/previews, recipe exports, `manifest.json`, `artifacts.csv`, and a deterministic ZIP into a new isolated directory
    - this action is package-only: it does not edit the source/worktree/registry/Base, and it fails closed on source/runtime/hash/path/private-marker drift; upload and promotion remain explicit reviewed steps in the three new `04_资产*` tables
17. `python -m tools.process_docs.build_review_preview` packages review HTML, diff-report HTML/CSV/XLSX, and optional review Word output for design sharing
18. `python build.py diff-report` exports review diffs, defaulting to the resolved target review root
19. `python build.py release-manifest` writes release traceability JSON / CSV for one explicit target; add `--version <version>` to freeze and bind the exact phase2 input under that release version
20. `python build.py preview` materializes one exact page selector under a preview-only output root
21. `python build.py fast` materializes a runtime-only draft without export

Important:

- `python build.py rst` only materializes the RST bundle.
- `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2` is the explicit local refresh step for Feishu/Lark content; build commands default to a valid phase2 snapshot when one exists and only fetch online data when you run `sync-data`.
- `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run` is the safest readiness probe for a new machine because it checks the local CLI/env prerequisites before attempting the real sync.
- `python build.py process-build-queue --config configs/config.us.yaml` is the explicit local consume-and-build step for the Feishu `Document_link` task table; it never runs implicitly from `sync-data`, `check`, or `publish`.
- static legal/support placeholders such as `WARRANTY_EMAIL` and `LEGAL_COMPANY_NAME` are injected from `build.rst_substitutions` in the active config; keep US values in US configs and override EU / pt-BR values there instead of hardcoding region-specific names in shared templates.
- `python build.py message-control-dry-run --message "publish JE-1000F us-merged from branch feature/review-123"` is a maintainer-only Phase 0 helper for the planned Feishu message plus OpenClaw control layer; it returns structured JSON only and does not dispatch GitHub workflows or write back any Feishu fields yet.
- `python build.py listen-message-control --config configs/config.us.yaml` is the matching no-server runtime entry: it keeps one local Feishu IM long connection through `lark-cli`, supports the same bounded action set as the webhook adapter, and is the recommended path when you want one local machine to receive Feishu app messages and trigger remote GitHub Actions directly
- when you need the same machine to keep the old local Feishu app unchanged, initialize the new app under `FEISHU_IM_LARK_CLI_HOME` first and then start `listen-message-control`; that isolates the new app's `lark-cli` config from the default home used by the old app
- when the queue row carries `Git_ref`, that queue step keeps the latest `main` code/toolchain and overlays only `docs/_review` from the named review branch; queue Draft/Publish builds treat `Git_ref` as review content, not as an alternate worker/toolchain branch.
- `python build.py word`, `python build.py html`, and `python build.py pdf` all prepare the RST bundle first.
- `python build.py all` runs `html`, `word`, and `pdf` after the same prepare step.
- RST may reference an approved asset by identity, for example `.. image:: asset:operation/ac_output`. Raw LaTeX may too: `\includepdf{asset:…}` takes the PDF export; `\begin{HBLcdModeTable}{asset:…}`, the image arguments of `\HBInBoxThree{asset:…}{label}…` and `\includegraphics{asset:…}` take the PNG export. Legacy basenames in those macros stay as written. Bundle finalization accepts only PNG/JPG/JPEG/SVG/PDF exports; `.ai` is archive input and is never a renderer fallback.
- PDF-compatible Illustrator masters are extracted through `tools/asset_intake.py` and a committed `data/asset_recipes/*.json` contract. Use `retain_vector_drawings` only when the wanted illustration and burned labels are separate source drawing groups: declare ascending source indices, explicit fill overrides and stroke suppressions, review the quarantine render at 12x, then pin the approved output hash. The operator is exclusive after `crop` and fails closed on an out-of-range/non-intersecting group or an unsupported vector item; it is not a coordinate whiteout mechanism.
- Each finalized bundle contains `asset_usage_manifest.json`, `asset_registry_snapshot.csv`, and `bundle_manifest.json`. `registry-uri` means the bytes came from the frozen approved registry export; `review-override` keeps the `asset_key` while recording the explicit override bytes; `legacy-path` means a path-based image was staged and accounted for but has not yet been migrated under registry status/scope control.
- Shared templates (`docs/templates/`) are bulk-migrated to `asset:` — every `common_assets` image and raw-HTML `src` now resolves through the registry, so status/scope/hash gating applies to all of them; write new template image references as `asset:<asset_key>`, not as file paths. `legacy-path` accounting remains for any reference that has not (or cannot) be keyed.
- `release-manifest` carries an `assets` section: the bundle fingerprint, the registry-snapshot hash, and every registry-backed asset the build actually consumed (key, format, content SHA, status, resolution source); the release CSV gains `assets_registry_count`, `assets_legacy_path_count`, `assets_bundle_sha256` and `assets_registry_snapshot_sha256`. `publish` runs an asset gate after the last prepare and before the manifest, so a bundle that consumed a `🔧临时替代`, `❌缺失` or `⛔隔离` asset — or that carries no frozen lineage — fails before anything is released. The gate does not block `legacy-path` images — references with no registry attribution at all — but their count is recorded so the debt stays visible; JE-1000F US reached zero. Synced Feishu attachment images (`_attachments/lcd_icons`, `_attachments/symbols`) are attributed to their `feishu/*_attachments` collection rows as `feishu-attachment` entries: each manifest row records the exact bytes that shipped, the collection row's registry status gates publish for the whole column, and the RST keeps its path reference (file identity is the Feishu token, so these are never keyed per file).
- Queue Publish also freezes the complete manifest-backed phase2 root under `reports/releases/<model>/<region>/<lang>/versions/<version>/snapshot/`. The release JSON/CSV points to this archive instead of the mutable live root and records `snapshot_sha256`, source-manifest revision, freeze time, target matrix, commit-derived `SOURCE_DATE_EPOCH`, and the DOCX/Markdown/PDF byte-equivalence contract. When `Git_ref` supplies the approved review content, the same reproducibility record binds its exact review commit, active target path, and tree SHA. The publish-entry gate first verifies the complete overlaid file set and every Git blob. Approved-reference targets then keep those page bytes unchanged as `review-asis`; unregistered targets may still perform the historical review-parameter sync. Deterministic target-asset staging may mutate generated files inside the subtree, and the late manifest binds the already verified source tree instead of treating those build products as new source. The clean gate remains active outside the one target subtree, and an absent or changed verified tree SHA fails closed. Keep the archive for the full release lifetime; same-version retries may reuse byte-identical data, but changing the binding or editing archived bytes fails closed. Run `python build.py release-rebuild-verify --manifest <manifest.json>` on the recorded toolchain to rebuild in a disposable worktree at the recorded Git SHA, restore the bound review overlay, and compare all three SHA-256 values; its default evidence is `versions/<version>/rebuild_verification.json`.
- A versioned release manifest also records one stable `release_tag` covering
  model, region, every build language, and version. Preview it with
  `python -m tools.release_tag --manifest <manifest.json>`; only after artifact
  acceptance and `release-rebuild-verify` pass should an operator repeat the
  command with `--write --push`. Existing tags cannot be silently rebound to a
  different commit or manifest. Vercel rollback, prior Word/PDF re-delivery,
  historical rebuild, and the operator-owned timed-drill sheet are documented
  in [`closed_loop_ops_guide.md`](closed_loop_ops_guide.md#410-发布标记与回滚k14).
- A product/market export keeps its own key and declares `override_for=<shared asset_key>` in `data/asset_registry.csv`; do not narrow or overwrite the shared row. The same shared template URI then resolves to that export only for the matching model/region/language. No match falls back to the shared row; multiple matches stop the build.
- `sync-data` refreshes `data/asset_registry.csv` from the `04_资产定义` table as a **derived file**, alongside `model_capabilities.csv`. It is an overlay, not a replace: the Base owns 类别 / 语言维度 / 状态 / 待无字化 / 适用机型 / 适用区域 / 语言变体, while the repo keeps `导出物路径` and `内容哈希` (they describe committed bytes) and `备注` (maintenance history — the Base's notes are intake rationale, kept separately). Rows are never deleted, so an asset dropped from the Base leaves its registry row standing rather than silently breaking templates that resolve it; the git diff of the CSV is the review surface. Table coordinates come from the frozen [`data/asset_base_bindings.json`](../data/asset_base_bindings.json) unless `FEISHU_PHASE2_ASSET_DEFINITIONS_TABLE_ID` is set, so no extra secret is needed. A Base value the resolver would reject fails the sync instead of landing in the registry.
- The Feishu archive/write contract permits only the three separately created `04_资产源文件`, `04_资产定义`, and `04_资产导出物` tables; their live binding is frozen in [`data/asset_base_bindings.json`](../data/asset_base_bindings.json), and the JE-1000F US master is the first source whose AI/ZIP/manifest attachments passed download hash verification. If those tables are inaccessible, stop and leave the source pointer empty; do not read, write, or fall back to the old illustration or staging intake table.
- build actions except `fast` clean the current target output first; on Windows, close File Explorer, browser, Word, or PDF windows opened under [`docs/_build/`](../docs/_build) before rerunning, or use `--no-clean` for an in-place rebuild.
- `python scripts/local_build.py check|diff-report|release-manifest|publish ...` keeps generated verification/build outputs under `.tmp/staging/docs/_build`, `.tmp/staging/reports/version_tracking`, and `.tmp/staging/reports/releases` without making the operator remember `--staging-root`.
- `review` does not accept `--staging-root` because it seeds the real repo `docs/_review`, so it is intentionally excluded from `scripts/local_build.py`.
- `python build.py review` prepares a runtime draft from template/data, then seeds review only if review does not already exist.
- `python build.py review --refresh-review` intentionally replaces an existing review bundle from template/data.
- `python build.py sync-review` is the safe path after snapshot data changes during review.
- review builds auto-run the same parameter sync before `html`, `word`, `pdf`, and `publish`, so parameter lines stay current without overwriting the rest of the review prose. `check` does **not**: it validates the review surface as committed, because it is the command the pre-PR checklist prescribes and a validation run should not rewrite tracked files under `docs/_review`. Ask for the refresh explicitly with `check --refresh-review` (or `check --source review`).
- the parameter sync only refreshes a placeholder line that still matches its template's shape. If a reviewer edited anything else on that line — the surrounding wording, or the indentation — the line is left alone and its parameters go stale, rather than the edit being reverted to the template's text. `python -m tools.check_review_branch_sync` is the notice path for a shared-source change an open review branch still has to pick up.
- a target review manifest may declare exact `page/*.rst` or `generated/*.rst` files in `sync_preserve_paths`; those paths remain byte-stable during automatic or manual `sync-review`, and each skip is written to `last_sync_preserved_files`. Remove the declaration before intentionally refreshing that page.
- when a single-language build targets a merged review branch and only `docs/_review/<model>/US/` or `docs/_review/<model>/EU/` exists, that auto sync falls back to the merged review root instead of silently skipping the refresh, then remaps the shared-family review pages onto the requested single-language page order before export.
- if you intentionally want one review page replaced from runtime, keep using `sync-review --page-file <file>`; if you need the whole review bundle replaced, use `review --refresh-review`.
- single-language US English review targets still use `docs/_review/<model>/US/en/`, Brazil Portuguese review targets use `docs/_review/<model>/pt-BR/pt-BR/`, and single-language EU review targets still use `docs/_review/<model>/EU/<lang>/`, but the merged `configs/config.us.yaml` / `configs/config.eu.yaml` queue/review flows use the shared roots `docs/_review/<model>/US/` and `docs/_review/<model>/EU/`.
- for that merged US flow, `Spec_Master.Source_lang` / `*_source` values are required, while CSV-driven non-source language columns may be blank because runtime lookup falls back to the source-language text automatically.
- for the recommended new flow, sync Feishu/Lark into [`data/phase2/`](../data/phase2) first; once a valid snapshot exists, `rst`, `check`, `diff-report`, `release-manifest`, and `publish` default to it, while explicit `--data-root` still overrides the source root.
- `build.py validate` checks config/layout even on a fresh clone without `data/phase2`; pass `--data-root tests/fixtures/phase2` when you want the full Spec_Master content validation without syncing live Feishu data.
- `build.py new-line --config <config> --dry-run` is the Stage 3
  read-only onboarding plan. It resolves the config inheritance chain, target
  identity, manifest pages, and template/recipe references, then reports
  `new-line-scaffold/v1`, `whitelist_diff`, and the F6-blocked
  `data/phase2` source surface. `--write` requires explicit
  `--output-config` and `--output-manifest` paths, optionally creates a
  target-local review override scaffold with `--asset-override-root`,
  refreshes only the committed fixture through `fixture-refresh`, and automatically runs the
  normal `build.py check` gate. It never writes production `data/phase2`
  or Feishu source tables; those remain a separately approved F6 operation.
- `build.py new-line --seed-plan --config <config> --model <model> --region
  <region>` is the zero-write F6 seed plan. It reports the target
  `Document_key` row, page-placeholder clone candidates, and the local
  source-table field-create helper. If multiple same-model source documents
  exist, pass `--seed-source-document-key <key>`; otherwise the plan reports
  `needs_input` instead of guessing. The command does not call Feishu or write
  `data/phase2`; row/field creation still requires the separately approved F6
  write path.
- `python build.py check`, `word`, `html`, and `pdf` use `source=auto` by default, so they build from `_review` once review exists.
- `python build.py publish` uses review content only, then runs `check -> diff-report -> word -> pdf -> md -> release-manifest` as one formal release command.
- for both `Publish` and `Web Publish`, keep `Document_link.Git_ref` pointed at the active review branch. Print artifacts and responsive Web output are separate builds but must resolve the same approved content revision.
- 单语 `Web Publish` 行明确填写 `Lang` 和匹配的单语 `Build_family`（例如 `en/eu-en`、`fr/eu-fr`），每语独立记录；不要把带 Lang 的 Web 行放入 merged family。Print Publish 仍保持整本、Lang 留空。版本号和线上队列写入仍需确认；`HTML_link` 由 `web-publish-receipt.yml` 在发布 PR 合入且部署核验通过后写回（构建时只记 pending），登记时点即已核验上线，但后续漂移仍由每日 `verify-web-deployment.yml` 独立探测。见[队列契约](../code-as-doc/dev/web_publish_locale_queue.md)。
- `python build.py handoff` now generates a minimal handoff package under [`docs/_handoff/`](../docs): it resolves explicit baseline/current inputs, loads supported `rst/html` inputs, generates rule-based add/delete/replace records, copies referenced draft images into `draft/assets/`, and writes `draft/manual.md`, `draft/manual.docx`, optional `draft/manual.html`, `changes/change_log.csv`, `changes/change_log.xlsx`, `changes/change_summary.md`, `handoff/design_handoff.md`, and `manifest.json`. It does not yet provide final page mapping or advanced semantic change classification.
- `.\scripts\build_us_jp_manuals.ps1 --model <MODEL> --formats html,word,pdf` is the one-command wrapper for the fixed four-language export pack.
- `.\scripts\build_us_jp_manuals.ps1 --model <MODEL> --build-action validate --languages en,fr` runs one explicit `build.py` action across the selected matrix targets instead of deriving actions from `--formats`.
- `.\scripts\build_us_jp_manuals.ps1 --model <MODEL> --formats html --open-html` builds the selected HTML set and opens the generated HTML entry pages.
- `check` now catches stale foreign model names, unresolved placeholders, missing assets, and contract-required spec keys / page-value selectors / assets.
- review overrides only overlay `overrides/_assets/**`, `overrides/_static/**`, and `overrides/renderers/**` into the runtime bundle.

---

## 4. Materialized Bundle Layout

For a target such as `JE-1000F / US`, the working bundle now lives here:

- [`docs/_build/JE-1000F/US/rst/index.rst`](../docs/_build/JE-1000F/US/rst/index.rst)
- [`docs/_build/JE-1000F/US/rst/page/*.rst`](../docs/_build/JE-1000F/US/rst/page)
- [`docs/_build/JE-1000F/US/rst/generated/JE-1000F/*.rst`](../docs/_build/JE-1000F/US/rst/generated/JE-1000F)
- [`docs/_build/JE-1000F/US/rst/conf.py`](../docs/_build/JE-1000F/US/rst/conf.py)
- [`docs/_build/JE-1000F/US/rst/conf_base.py`](../docs/_build/JE-1000F/US/rst/conf_base.py)
- [`docs/_build/JE-1000F/US/rst/_static/**`](../docs/_build/JE-1000F/US/rst/_static)
- [`docs/_build/JE-1000F/US/rst/renderers/**`](../docs/_build/JE-1000F/US/rst/renderers)
- `docs/_build/JE-1000F/US/rst/asset_usage_manifest.json` — every semantic, review-override, and legacy image consumer plus rewrite provenance
- `docs/_build/JE-1000F/US/rst/asset_registry_snapshot.csv` — the exact registry bytes used for this bundle
- `docs/_build/JE-1000F/US/rst/bundle_manifest.json` — final file records plus `bundle_sha256` over the RST closure, config, support trees, and asset sidecars

This is the generated bundle consumed by Sphinx, HTML export, Word export, and PDF export.
It is not the editing surface. After review starts, `_review/...` is overlaid onto this bundle before publish.

---

## 5. Git Tracking Rule for Review Bundles

The current repo allows two Git-visible surfaces:

- [`docs/_build/**/**/rst/**`](../docs/_build) is no longer ignored
- [`docs/_review/**`](../docs/_review) is emitted as a review-first snapshot
- sibling outputs such as [`docs/_build/**/**/html/**`](../docs/_build), `word/**`, and `pdf/**` remain build artifacts

This gives you two benefits:

1. You can commit generated review bundles per target and keep reviewable history.
2. You can export Git diffs for a single model or region as CSV and HTML reports.

What this does not change:

- `_build/.../rst/**` is still regenerated on the next build.
- `_review/.../**` is now the durable review-editing surface for that target once review starts.
- `python build.py review --refresh-review` is the only path that intentionally replaces the existing review content from template/data.

Recommended use:

1. Seed the target review bundle once with `python build.py review --config ...`
2. Edit [`docs/_review/<model>/<region>/**`](../docs/_review)
3. Build preview/final outputs with `check/html/word/pdf`
4. Commit the resulting review bundle
5. Use `python build.py diff-report ...` when you need a table-style change export

For the current maintainer branch model, pull request rules, and GitHub protection settings, use [`../code-as-doc/dev/git_branching_guide.md`](../code-as-doc/dev/git_branching_guide.md).

---

## 5. Which Files You Should Edit

Edit these when the change should be shared across products or when creating the first draft:

- [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
- [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)

Parallel-language template rule:

- `docs/templates/page_us-en/*.rst` is the current source-language structure owner for manually maintained US prose templates.
- `docs/templates/page_us-es/*.rst` and `docs/templates/page_us-fr/*.rst` are derived-language counterparts and must be updated in the same round when the source-language page changes shared section structure or `.. only::` gating.
- JP currently has only `ja`, so there is no second JP derived-language template to mirror today, but any future JP derived-language page should follow the same rule.
- before adding a new Markdown manual into the template library, fill out [`../code-as-doc/dev/manual_template_intake_checklist.md`](../code-as-doc/dev/manual_template_intake_checklist.md) so section mapping and placeholder rules are decided before page edits start.

Edit these when safety/spec parameters change:

- [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)
- [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
- [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)

Edit these when a safety intro page needs copy/layout changes:

- edit [`docs/templates/page_us-en/safety_en.rst`](../docs/templates/page_us-en/safety_en.rst), [`docs/templates/page_us-fr/safety_fr.rst`](../docs/templates/page_us-fr/safety_fr.rst), or [`docs/templates/page_us-es/safety_es.rst`](../docs/templates/page_us-es/safety_es.rst) for US safety intro changes
- edit [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst) when the Japanese safety intro page needs copy or layout changes
- edit [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst) when the detailed Japanese safety warnings need changes

Edit these during target review and final polish:

- [`docs/_review/<model>/<region>/index.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/page/*.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/generated/<model>/*.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/_assets/**`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/_static/**`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/renderers/**`](../docs/_review)

Do not use these as the primary authoring source:

- [`docs/_build/<model>/<region>/rst/page/*.rst`](../docs/_build)
- [`docs/_build/<model>/<region>/rst/generated/<model>/*.rst`](../docs/_build)
- [`docs/_build/<model>/<region>/rst/index.rst`](../docs/_build)
- [`docs/index.rst`](../docs/index.rst)

You may commit `_review/...` for review history because it is now the target editing surface after review starts.

---

## 6. How Safety and Spec Pages Work

Safety intro pages are now maintained as fixed RST templates and then materialized into the bundle.
The standalone user maintenance instructions page lives in shared templates and is included before the `symbols` page.

For FridgeGuard Web safety pages, EN/FR/ES reuse the same risk banner, warning lead, SVG icons and compact two-column styles. Keep each native source's wording. Desktop review must check aligned left edges and visible triangles; phone review must check that the stacked columns fill the content width. Maintain the shared [safety style contract](../docs/renderers/contracts/STYLE_DEFINITION.md#1011-例外模板自带双分支的页安全页fcc), rather than adjusting each language separately.

Primary inputs:

- [`docs/templates/page_us-en/safety_en.rst`](../docs/templates/page_us-en/safety_en.rst)
- [`docs/templates/page_us-fr/safety_fr.rst`](../docs/templates/page_us-fr/safety_fr.rst)
- [`docs/templates/page_us-es/safety_es.rst`](../docs/templates/page_us-es/safety_es.rst)
- [`docs/templates/page_shared/en/01_user_maintenance_instructions.rst`](../docs/templates/page_shared/en/01_user_maintenance_instructions.rst)
- [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst)

JP manual note:

- [`docs/manifests/manual_jp.yaml`](../docs/manifests/manual_jp.yaml) includes [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst) directly
- edit that template when the JP safety intro page must change
- the detailed JP warning content remains in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst)
- the old `content_blocks.csv` safety source has been removed from the active repo flow

Generated bundle output:

- materialized page include: [`docs/_build/<model>/<region>/rst/page/safety_<lang>.rst`](../docs/_build)

Symbols content is generated from:

- [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv)
- [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)

`symbols_blocks.csv` notes:

- use one `table_row` per symbols-table entry
- use `signal_row` entries for warning/caution/danger/note/tip signal structure; the signal token (`symbol_key`), target scope, order, and optional icon asset stay in `symbols_blocks.csv`. Visible signal labels and meanings are authored in `Manual_Copy_Source.csv`, translated through Translation Memory rows tagged `manual_copy`, and rendered from generated `Localized_Copy.csv`; legacy `label_*` and `aliases_*` columns are compatibility mirrors for old variants and rewrite detection only
- use `Market` and `Model` to target symbols rows; `symbols_blocks.csv` does not use `Region`
- use `Source_lang` for the row's source-language code, for example `en` or `ja`
- use `Market=Global` when one row should be shared across markets
- `image_path` stores the RST image reference path for that icon
- keep `symbol_key` stable so renderer alt text and layout metadata still resolve correctly; do not duplicate `copy_type=alt_text` rows in `Localized_Copy.csv`

Troubleshooting content is generated from:

- [`data/phase2/troubleshooting_blocks.csv`](../data/phase2/troubleshooting_blocks.csv)
- [`docs/templates/**/10_troubleshooting.rst`](../docs/templates/page_shared/en/10_troubleshooting.rst)

`troubleshooting_blocks.csv` notes:

- maintain the online TROUBLESHOOTING Base table, then run `python build.py sync-data --config configs/config.us.yaml --table troubleshooting --data-root data/phase2`
- use `Region`, `Model`, and `Is_latest` to select active rows; blank placeholder records are ignored
- keep page title, intro, table headers, widths, and header-row settings in each language's `10_troubleshooting.rst`
- keep error-code rows and corrective-measure copy in the TROUBLESHOOTING Base table; the RST template exposes `{{ troubleshooting_rows_rst }}` where those rows are inserted
- localized corrective text lives in per-language `corrective_measures_<lang>` columns; the current snapshot set is `corrective_measures_en/fr/es/pt-BR/br/de/it/ukr/jp/zh/ko`. A new output language adds its column in the Base table first, then reaches the snapshot through `sync-data`

Spec content is generated from:

- [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- optional [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
- optional [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
- optional [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)

Generated bundle output:

- [`docs/_build/<model>/<region>/rst/generated/<model>/spec_<lang>.rst`](../docs/_build)
- materialized page include: [`docs/_build/<model>/<region>/rst/page/spec_<lang>.rst`](../docs/_build)

[`Spec_Master.csv`](../data/phase2/Spec_Master.csv) remains the build-time read model for spec sections, rows, and page-value placeholder records.
In Feishu, maintain those rows through `规格参数明细` and `页面占位参数`, then refresh the local snapshot with `sync-data --table spec_master` or a focused `spec-master-rebuild`.

---

## 7. Placeholder Rules

Core placeholders resolved from [`Spec_Master.csv`](../data/phase2/Spec_Master.csv):

- `|PRODUCT_NAME|`
- `|PRODUCT_NAME_BOLD|`
- `|PRODUCT_SHORT_NAME|`
- `|PRODUCT_SHORT_NAME_BOLD|`
- `|MODEL_NO|`

Resolution source:

- `product_name` comes from `Row_key=product_name`
- `model_no` comes from `Row_key=model_no`
- `PRODUCT_SHORT_NAME` is derived from `PRODUCT_NAME`

`Spec_Master.csv` `Page` note:

- `Page` can be a comma-separated list
- use `Product overview` for Product overview-only page-value rows such as front/side-view callouts
- use `Product overview, specifications,` when the same row is intentionally shared by both pages
- `Row_label_source`, `Param_source`, and `Value_source` should store the row's source-manual text
- `Source_lang` should store the normalized source-language code for the row, such as `en`, `ja`, or `zh`; do not expect code to infer it from `Region`
- `document_key` should be either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`
- `Row_order` is now the explicit row order inside each `document_key + Page + Section`; `Line_order` only controls the order of multiple lines inside one logical row
- `Line_order` is required; single-line rows use `1`
- generated `spec_titles.csv section_order` can hold the default order for visible spec sections, but a filled `Spec_Master.csv Section_order` overrides it
- `project_code` / `项目代码` is no longer used in `Spec_Master.csv`; choose rows by `Region` + `Model`
- when a build target is passed in document-key style such as `JE-1000F_JP` or `JE-1000F-JP`, the spec lookup normalizes it back to the base model `JE-1000F` and still uses the explicit `Region`, so a `JP` target continues to read `JP` rows
- source-language rows must keep their actual source text in `Row_label_source`, `Param_source`, and `Value_source`

For page-value rows, `Row_key` now keeps only the concept itself. Human editing should happen through `Slot_key`.

Examples:

- `Row_key=main_power_button`, `Slot_key=label` -> `|MAIN_POWER_BUTTON_LABEL|`
- `Row_key=ac_input`, `Slot_key=side.spec` -> `|SIDE_AC_INPUT_SPEC|`
- `Row_key=battery_pack_name`, `Slot_key=value` -> `|BATTERY_PACK_NAME|`

Derived behavior:

- non-empty placeholders also get `..._BOLD`
- placeholders ending in `_LABEL` also get `..._LOWER`
- multi-line page-value rows produce suffixed placeholders such as `|EXAMPLE_KEY_2|`

---

## 8. Build Commands

Cross-platform entrypoint:

```powershell
python build.py doctor --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py doctor --data-plane --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2
python build.py rst
python build.py review
python build.py check
python build.py sync-review
python build.py publish
python build.py release-manifest
python build.py preview --config configs/config.us-en.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py html
python build.py word
python build.py pdf
python build.py all
```

Config scope rule:

- [`configs/config.us.yaml`](../configs/config.us.yaml): shared EN / US template-family config
- [`configs/config.us-en.yaml`](../configs/config.us-en.yaml): canonical US English single-language review / CI / explicit review-preview landing target
- [`configs/config.ja.yaml`](../configs/config.ja.yaml): shared JP template-family config
- [`configs/config.zh.yaml`](../configs/config.zh.yaml): shared CN zh template-family config using [`docs/manifests/manual_zh.yaml`](../docs/manifests/manual_zh.yaml)
- [`configs/config.kr.yaml`](../configs/config.kr.yaml): shared KR ko template-family config for `JE-1000F_KR` and `JE-2000E_KR`, using [`docs/manifests/manual_kr.yaml`](../docs/manifests/manual_kr.yaml)
- [`configs/config.eu.yaml`](../configs/config.eu.yaml): shared EU merged template-family config using [`docs/manifests/manual_eu.yaml`](../docs/manifests/manual_eu.yaml)
- [`configs/config.eu-en.yaml`](../configs/config.eu-en.yaml), [`configs/config.eu-fr.yaml`](../configs/config.eu-fr.yaml), [`configs/config.eu-es.yaml`](../configs/config.eu-es.yaml), [`configs/config.eu-de.yaml`](../configs/config.eu-de.yaml), [`configs/config.eu-it.yaml`](../configs/config.eu-it.yaml), and [`configs/config.eu-uk.yaml`](../configs/config.eu-uk.yaml): explicit EU single-language configs using [`../docs/manifests/manual_eu-en.yaml`](../docs/manifests/manual_eu-en.yaml) plus the corresponding [`../docs/manifests/manual_eu-single-*.yaml`](../docs/manifests) stacks
- [`configs/config.solar-eu-en.yaml`](../configs/config.solar-eu-en.yaml): exact `JS-100I / EU / en` and `JS-40C / EU / en` Web entrypoint using the reusable [`Solar@INTL` skeleton](../docs/manifests/skeletons/solar-intl/blueprint.yaml). JS-100I uses five Inbox cards plus unfolding/folding; JS-40C uses seven Inbox cards plus Solar Panel Storage. Both use frozen phase2 specifications and target-bound English figures; this config is not a fallback for portable-power-station targets.
- [`configs/config.solar-eu-multilingual.yaml`](../configs/config.solar-eu-multilingual.yaml): JS-100I / EU 的 `fr/es/de/it/uk/pt/nl/pl` Git 源候选；逐语指定 `--lang` 和匹配的 `added-locales/2026-09-28/phase2/<lang>` 数据目录。沿用太阳能板 RST/CSV、manual-ir/v2 和共用 Web 组件。英语保留原结构数据，操作图拆分为原生透明插图并配可选中文本，手机参数表在容器内换行。荷兰语 `OPMERKING`、波兰语 `Uwaga` 以原文进入共用提示条；各语言发布前必须通过组件适用性及保修原文哈希检查。[来源、勘误与本地验收](../code-as-doc/reviews/js100i_eu_nine_language_2026-09.md) 不代表已发布、已写 Base 或已晋升插图资产。
- [`configs/config.us-en.yaml`](../configs/config.us-en.yaml), [`configs/config.us-es.yaml`](../configs/config.us-es.yaml), [`configs/config.us-fr.yaml`](../configs/config.us-fr.yaml), and [`configs/config.pt-br.yaml`](../configs/config.pt-br.yaml) now inherit their shared single-language US defaults from [`../configs/config-bases/us-single-language-base.yaml`](../configs/config-bases/us-single-language-base.yaml); keep common single-language build defaults there and keep language-specific page order in [`../docs/manifests/manual_us-single-en.yaml`](../docs/manifests/manual_us-single-en.yaml), [`../docs/manifests/manual_us-single-es.yaml`](../docs/manifests/manual_us-single-es.yaml), [`../docs/manifests/manual_us-single-fr.yaml`](../docs/manifests/manual_us-single-fr.yaml), and [`../docs/manifests/manual_pt-br.yaml`](../docs/manifests/manual_pt-br.yaml)
- [`configs/config.us-en.yaml`](../configs/config.us-en.yaml) additionally sets `md_output` so its Markdown / Web artefact stays `manual_je1000f_us`, the stem the published `JE-1000F/US/en/md/` page already uses; its Word and PDF artefacts keep the inherited `_en` suffix, and `config.us-fr.yaml` / `config.us-es.yaml` keep the inherited `_fr` / `_es` suffix on every artefact. See [`code-as-doc/dev/web_publish_locale_queue.md`](../code-as-doc/dev/web_publish_locale_queue.md) for why a published locale route cannot be renamed
- the current maintained baseline target is `JE-1000F` across these active config families, including `JE-1000F / US`, `JE-1000F / EU`, and `JE-1000F / JP`
- do not create a new config only because the model changed; pass `--model` and `--region` instead
- create a new config only when the page stack, template family, or output conventions are genuinely different

Useful target-scoped examples:

```powershell
python build.py doctor --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py rst --config configs/config.ja.yaml
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US --refresh-review
python build.py sync-review --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py publish --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.zh.yaml --model JE-2000E --region CN
python build.py check --config configs/config.kr.yaml --model JE-2000E --region KR
python build.py rst --config configs/config.us.yaml
python build.py word --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py pdf --config configs/config.ja.yaml --model JE-2000F --region JP
```

Source mode examples:

```powershell
python build.py rst --config configs/config.ja.yaml --model JE-1000F --region JP --source runtime
python build.py word --config configs/config.ja.yaml --model JE-1000F --region JP --source review
```

Source mode meaning:

- `auto`: use `_review` if it exists, otherwise use template/data runtime draft
- `runtime`: ignore `_review` and build from template/data
- `review`: require `_review` and build from it

PR preview note:

- when a PR changes `docs/_review/<model>/<region>/`, GitHub review-preview derives that exact target from the diff and uses the same target-aware config matching as Start Review/Draft/Publish; for example, `JBP-2000B / US` uses `configs/config.bp-us.yaml`, while ordinary US host targets keep the MAIN config
- when a PR changes the zh manual family under `docs/templates/page_zh/`, `docs/templates/recipes/zh/`, or `docs/manifests/manual_zh.yaml`, the preview tool still selects the config-derived CN runtime target automatically, while packaging every existing review model
- `python -m tools.process_docs.build_review_preview` can omit `--config` when `--model` and `--region` identify a declared target; it can omit all three in CI-style runs and infer the target from the changed review bundle or existing review tree. Keep `--config configs/config.us-en.yaml` when you explicitly want the US English single-language target
- the Vercel review-preview fallback derives those family configs and its first fallback target by scanning `configs/config*.yaml`; it is used only when `PREVIEW_MODEL` / `PREVIEW_REGION` and the review tree do not provide a target

`publish` behavior:

- requires explicit `--model` and `--region`
- requires an existing `_review/<model>/<region>/`
- exports revision reports to [`reports/version_tracking/<model>/<region>/`](../reports/version_tracking) by default
- writes a release manifest to [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../reports/releases)
- queue-driven `Workflow_action=Publish` stages the formal DOCX, PDF, Markdown, IDML outputs, and designer handoff ZIP under [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases), then writes the uploaded handoff ZIP URL to `idml_file`; it does not build a Draft cloud doc or HTML
- queue-driven `Workflow_action=Web Publish` forces live asset sync, renders web-profile MyST/HTML, advances the `Hello-Docs/publish:docs/publish/` candidate, and opens or updates its `docs/publish/**`-only PR into `main`; after a human merges that PR, `web-publish-receipt.yml` verifies the live deployment and writes the canonical nested RTD page (for example `https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us.html`) to `HTML_link`; the short root alias (for example `/manual_je1000f_us.html`) remains the printed/QR entry layer, and the queue does not upload or overwrite IDML/PDF/DOCX outputs
- an authorized Git-only Web release takes reviewed, committed sources and `source_manifest.json` through exact-ref checks, Web MyST, strict Sphinx, release metadata, and the same publish assembler. It reads or writes no online tables and creates no queue row. Its durable proof is the source and Hello-Docs commits, hashes, manifests, RTD build commit, canonical routes and aliases; see the [Git-only transaction](../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction)

`preview` behavior:

- requires explicit `--model`, `--region`, and `--page`
- `--page` must match one exact page selector
- writes to [`docs/_build/<model>/<region>/preview/<page>/rst/`](../docs/_build)
- does not rewrite root [`docs/index.rst`](../docs/index.rst)

RTD catalog behavior:

- RTD builds the frozen `docs/publish/web/` catalog from `Hello-Docs/main`. The generated `publish` branch is only a release candidate; `review/*` is only a build input, and neither branch is merged wholesale. The review/fixture command in [`.readthedocs.yaml`](../.readthedocs.yaml) is only the bootstrap fallback before the first snapshot.
- PDF-like fixed figure panels use a separate, approval-gated Web composite chain. In `04_资产定义`, `web_replace_key` names the component. In `04_资产导出物`, upload exactly one image to `export_file`, select the registered output `web_locale` (for example `en`, `fr`, `es`, `de`, `it`, or explicitly `shared`), fill both the file and source-fragment SHA-256 values, then set both the definition and export to `gate_status=approved`, `build_eligible=true`, and `visual_review_required=false`. `artifact_kind` must be `web-composite`.
- Choose the carrier per component. JE-1000F Product Overview, its five Operation panels and its four Charging panels use `text_policy=localized-full-page`: crop the PDF panel with localized labels intact, including Operation `On` / `Off`, prerequisites and instructions. The LCD screen-mode block does not use a full-table screenshot; it combines the correct UK or continental hardware/display artwork with the shared six-row HTML table. Specifications, troubleshooting, LCD-icon glossary and Warranty stay live HTML components.
- Reuse target geometry through [`overview_component_instances.json`](../docs/renderers/contracts/overview_component_instances.json): a child instance uses `extends`, and stable-`id` lists merge by `id`, so a new region normally overrides only `target`, market artwork keys and locale declarations. The materialized document language selects the composite; page-number filename patterns are compatibility fallback only. Coverage resolves duplicate bytes safely with `asset_key + locale + SHA-256`.
- `sync-data` downloads only those approved rows into `_attachments/web_composites/` and writes `web_composite_manifest.json`. The next Web materialization selects by `web_replace_key + model + region + locale`, verifies the bytes and the current semantic source fragment, and replaces the governed figure plus its associated copy while leaving the section title live. With no approved match it keeps the searchable HTML fallback. Ambiguous rows, missing attachments, or either hash mismatch stop the build.
- After a local or queue Web build, inspect `manual.ir.json -> metadata.web_figure_coverage`. `finished-panel` is the approved whole-panel illustration path; `approved-composite` is the approved component override; `editable-fallback` is searchable semantic rendering but remains finished-art debt; `missing` means the slot still lacks approved localized artwork. Approved rows include the packaged path and SHA-256. The report never promotes assets. A coverage policy must list the complete locale/slot matrix and accepts only `finished-panel` / `approved-composite`. Existing exceptions live in [`figure_debt_baseline.json`](../docs/renderers/contracts/web_presentation/figure_debt_baseline.json) as exact locale/slot/status rows; new or worsening debt fails, while a repaired row must delete its now-stale baseline entry. EU has no exception, so Italian textless art plus HTML/SVG text or leaders fails the build. LCD Mode and the other native HTML tables are outside this finished-art matrix.
- [`web_manual.json`](../docs/renderers/contracts/web_manual.json) is only the Web presentation stack entry. The loader resolves `shared base → skeleton profile → target overlay`: shared semantic components are written once, a skeleton owns reusable Overview/Operation/App/Charging shape, and `(model, region)` overlays contain only capability grants, required artwork coverage and real differences. Mapping values merge recursively, lists with stable `id` values merge by `id`, and ordinary lists replace as a whole. A new figure-capable target must provide a complete zero-debt coverage policy; only pre-existing rows may appear in the separate ratcheted debt baseline. Unknown targets receive no figure grant; duplicate targets, unknown skeletons, bad schemas and paths escaping the contract directory fail closed. A whole-document Web IR freezes its resolved target contract, selected layer IDs, component registry, theme and target-matched Overview instance, so source-free replay never reopens those registries.
- A local live freeze for the queue-driven path must use the business-plane HT-Docs bot, not another bot belonging to the same user. `sync-data` uses the active lark-cli profile; on the maintained Mac, first verify `lark-cli --profile prod whoami --as bot`, temporarily select profile `prod`, keep `FEISHU_PHASE2_IDENTITY=bot`, and restore the previous profile after the sync. The identity flag chooses bot versus user, while the profile chooses the Feishu application/tenant. This does not apply to a Git-only release whose recorded inputs are committed and whose authorized scope prohibits online reads and writes.
- RTD itself has no Feishu credentials. The queue-driven path uses the HT-Docs bot to freeze verified attachments and their manifest into Git first; the Git-only path starts from reviewed Git inputs. RTD consumes the resulting immutable snapshot in either case. `tests/fixtures/phase2` remains a CI/bootstrap fixture.
- To show **ordinary hand-written Markdown** in the same web-manual style — a single note or a whole folder rendered as one site with a sidebar — run [`tools/plain_markdown_site.py`](../tools/plain_markdown_site.py): `python -m tools.plain_markdown_site --source <file-or-folder> --output-dir <site-out> --title "My Docs"`. For a backlog of existing documents, swap `--source` for `--manifest inventory.csv` (columns `source,title,section,order`; `section` becomes a sidebar group). No Feishu table is involved — this lane has no publish state to govern, so a CSV inventory (or just the folder tree) is the right level. Broken image paths inherited from wherever a document used to live are repointed automatically by filename. Legacy tables are upgraded on the way in: a headerless label/value pipe table becomes the manual's real spec-table markup (grey `<th>` label column, merged labels, `^(①)` superscripts, bordered wrapper) instead of rendering with the phantom empty header row a converter leaves behind — a plain pipe table cannot express any of that, which is why an untouched one looks nothing like the published table. Callout boxes that a cloud editor flattened into a header-only table are restored as callouts, tables whose first data row was captured as the header are un-headered, in-table `### SECTION` rows split a spec table into one block per section, and `^①^`/`V~oc~` become real superscripts — measured on a real HTE153 export: 17 malformed tables down to 1, 16 callouts and 4 spec blocks recovered. The conversion writes an **intermediate Markdown** form rather than HTML: `--to-intermediate DIR` gives you a reviewable file of `{callout}` / `{spec-table}` / `{lcd-mode}` / `{comparison}` / `{manual-table}` directives (tables it cannot classify stay pipe tables with a comment naming the candidates), and rendering that directory is a plain `--source` run that compiles the directives deterministically. Add `--download-images` to localize artwork hosted on a cloud editor. Use `--keep-tables` to opt out of the conversion, and `components/COOKBOOK.md` in the exported bundle when a document needs a component the shape alone cannot imply. The output directory is self-contained, so you can zip it or hand it over as-is. This is a preview/sharing lane only: it refuses to write into `docs/_build`, `reports/releases` or `docs/publish`, and it cannot put anything on the RTD site, which only renders the Web Publish snapshot. Plain Markdown gets the prose styling (typography, paper card, headings, table panels, images); the `hb-*` figure/spec/LCD components need pipeline-generated markup and will not appear. Do not try to "downgrade" a generated manual `.md` into plain Markdown with `pandoc -t gfm-raw_html`: measured on `JE-1000F / US`, that silently drops roughly a third of the visible text plus 26 images and 38 tables, because constructs that plain Markdown cannot express are discarded rather than degraded.
- 中间态里可写的 8 个指令、单元格能用的行内标记子集、类型化 option 和 strict 排错，见 [`md_site_guide.md`](md_site_guide.md)。存量转换的两条命令也在那份里。
- Web Publish enables `AUTO_MANUAL_PRESENTATION_PROFILE=web`. Normal `build.py md`, print Publish, IDML and DOCX exports keep the default `document` profile.
- the web profile skips `cover*`, `00_toc*`, and `99_back_cover*`. JE-1000F / US opens directly at the `IMPORTANT` content in `00_preface`; if the source still carries the merged-language inventory line, Web hides it. A valid reseeded US review page may already start with the governed bold `IMPORTANT` marker and is accepted as-is, while an unrelated leading block still stops the build. Targets without that explicit preface contract—including JE-1000F / EU—start at the first included manifest page instead of inheriting the US rule.
- For a short category manual with a different real first chapter, declare the allowed filename pattern(s) in `build.web_entry_source_patterns` (for example `safety_tips*`). The Web build rejects an empty declaration or a first page outside that list; do not add an empty preface just to satisfy the entry check.
- A variable-card Inbox remains the same semantic component but uses the `responsive-card-grid` variant and an ordered repeated artwork role. It is currently supported only by responsive Web; LaTeX, IDML and Word fail explicitly instead of claiming five-card print support. The existing three-card variant and all four of its renderers remain unchanged.
- For targets listed in [`web_manual.json`](../docs/renderers/contracts/web_manual.json) (currently `JE-1000F / US` and `JE-1000F / EU`), Product Overview becomes one `HB-SPECIAL-OVERVIEW` semantic instance with two views, two asset roles and 15 ordered live callouts. [`overview_component_instances.json`](../docs/renderers/contracts/overview_component_instances.json) keeps the US geometry in `je1000f-us-v1`; the EU instance extends it and overrides only target, the front artwork key and EN/FR/ES/DE/IT locale bindings. A view uses centered locale-matched approved PDF artwork only when an exact manifest entry matches; otherwise its complete searchable HTML/SVG labels and text-free art remain visible as a semantic fallback. The crop excludes the FRONT/RIGHT heading so theme changes still control it. WHAT'S IN THE BOX is one `HB-SPECIAL-INBOX` semantic instance: three ordered cards each carry their number, image asset role, accessible alt and editable localized label, followed by the same instance's editable TIP label/body. The Web adapter renders equal rounded cards with even outer alignment and a responsive full-width TIP strip; LaTeX, IDML and Word keep their own layout geometry without rasterizing the labels. App Setup renders store badges and QR as distinct shared images, centers each in its own column and keeps both descriptions as live HTML. Step 2.1 uses the themeable plus while preserving its localized screen-reader label. The add-device panel combines one shared PDF-derived two-phone artwork, with 2.1/2.2 positioned inside the image, and shared text-free device-control art with three localized RST button labels as visible HTML. The approved control art keeps the full grey panel and leader lines; CSS places only localized labels in its reserved zones. Operation and Charging figures use centered locale-matched crops with embedded labels when approved, and otherwise preserve their live localized semantic composition. The App connect-result panel uses one shared PDF-derived three-phone image with 2.3/2.4/2.5 embedded. Reference artwork never contains the section heading, and surrounding non-panel instructions remain live HTML. JE-1000F/EU now requires and resolves all 55 EN/FR/ES/DE/IT Overview/Operation/Charging slots as source-PDF-faithful composites; the build rejects fallback, missing, duplicate or absent required slots. The former DE/IT text-free-art-plus-HTML-label path remains documented only as paid debt, not as final delivery. Specifications, Warranty, LCD, Troubleshooting and Symbols remain native HTML. Ordinary standalone RST images fill the responsive content width, remain centered and preserve aspect ratio. Unlisted targets retain ordinary source HTML until their own presentation is validated and added to the contract.
- The generated MyST source keeps `assets/` beside the manual and its generated Sphinx config copies that directory under the same URL prefix. For local acceptance, build the generated directory with Sphinx and verify zero broken images at desktop and 375 px; `manual_bundle.html` alone is an intermediate conversion artifact, not the published-page acceptance surface.
- Shared multi-target Web families may tokenise `paths.page_manifest` and `paths.web_illustration_manifest` with `{model}`/`{region}`. Validation resolves the configured default target, while each explicit build resolves the requested target; keep target differences in manifests, Product Manual Plans, copy, and assets instead of adding one config per model.
- `JBP-3600A / EU / en` engineering builds use [`config.bp-eu-en-web.yaml`](../configs/config.bp-eu-en-web.yaml) and the source/acceptance record at [`jbp3600a_eu_en_web_intake_2026-09.md`](../code-as-doc/reviews/jbp3600a_eu_en_web_intake_2026-09.md). In the authorized three-target Git-only batch, its reviewed Git source, `source_manifest.json`, asset hashes and acceptance evidence are the release authority, so no live Base row is created or read back. A later queue-driven publication remains a separate input path with its normal online-record requirements.
- `JE-2000F / EU / en` uses the shared [`config.eu-en.yaml`](../configs/config.eu-en.yaml) with a target-selected Web illustration manifest rather than a per-model config. Its frozen branch source, PDF crop recipe, hashes and verification record live under [`manual_sources/JE-2000F/EU/en/2.0/`](../manual_sources/JE-2000F/EU/en/2.0) and [`je2000f_eu_en_web_intake_2026-09.md`](../code-as-doc/reviews/je2000f_eu_en_web_intake_2026-09.md). The build is Git-only and uses `AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off`; it does not prove a live Base write or a public release.
- `JE-2000F / EU` also builds as the merged six-language EU book through [`config.eu.yaml`](../configs/config.eu.yaml). Finished figure crops are bound per language; All six languages each carry 11 finished panels cut from the same published EU/UK PDF at the same bounding boxes, offset 16 pages per language block. Covered-annotation selectors are resolved per page, not per document, so Ukrainian's repeated `section-N` ids — Cyrillic headings do not slugify — stay unique where it matters. A few French and Spanish annotations are omitted because those languages split the same copy into a different number of line blocks than English does; that figure's copy then stays visible below the panel.
- `JE-2000F / EU` additionally publishes as five single-language routes through [`config.eu-fr.yaml`](../configs/config.eu-fr.yaml) and its `es` / `de` / `it` / `uk` siblings, the same Git-only shape the EU English route already uses: one target entry, one illustration manifest bound per config, and the frozen source under `manual_sources/JE-2000F/EU/en/2.0/phase2`, whose `Spec_Master.csv` already carries every language's values. Each route builds 11 finished panels. The App setup result figure in every language is one shared panel cut from the English block's page 21; its recipe stays quarantined as App UI (see [`web_publish_pipeline.md`](../code-as-doc/dev/web_publish_pipeline.md)). The merged six-language book cannot go through the Feishu Web Publish queue: that lane fails closed with `Git_ref … does not contain review content`, because it renders the active target from `review/JE-2000F-EU`, which was seeded in July and never takes later `main` updates.
- `JE-3000C / EU` builds all six languages from the frozen source under [`manual_sources/JE-3000C/EU/en/2.0/phase2`](../manual_sources/JE-3000C/EU/en/2.0/phase2): English through `config.eu-en.yaml`, fr/es/de/it/uk through the single-language configs. Each fr–uk route binds a one-entry illustration manifest: the App setup result figure, one shared panel cut at 12x from the English block's page 21, whose recipe stays quarantined as App UI. English keeps its own approved App panels.
- `JE-2000E / EU` follows the same shape from [`manual_sources/JE-2000E/EU/en/2.0/phase2`](../manual_sources/JE-2000E/EU/en/2.0/phase2). Each fr–uk route binds a two-entry illustration manifest: the App add-device screens (2.1/2.2) and connection result (2.3–2.5), shared panels cut at 12x from the English block's pages 23–24 with quarantined App recipes. The add-device figure of every route is instead each language block's own crop of the screens plus the control-panel box, with the printed button labels; the page's four label lines move into the figure's alt text. The Ukrainian print labels the AC2 button `AC1`, so the uk crop re-sets that one character from the print's own glyphs (accepted by the operator on 2026-09-27). The German and Italian pages name the main and DC/USB buttons as their print blocks do (`POWER-Taste`, `Pulsante CC / USB`).
- `JE-3600A / EU / en` follows the same shared-config selection path. Its published-source locks, deterministic crop recipe, frozen phase2 input and LCD device-art-plus-semantic-table rule live under [`manual_sources/JE-3600A/EU/en/2026-05-25/`](../manual_sources/JE-3600A/EU/en/2026-05-25) and [`je3600a_eu_en_web_intake_2026-09.md`](../code-as-doc/reviews/je3600a_eu_en_web_intake_2026-09.md). It is also Git-only with `AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off`; localhost output is review evidence, not publication. Its en, fr and es routes share one App connect-result panel cut at 12x from the English block's page 22 (quarantined App recipe): the English manifest carries it as an extra entry, and fr/es bind one-entry manifests through their single-language configs.
- App add-device figure on `JE-2000F / EU` (all six routes), `JE-3000C / EU` (fr–uk) and `JE-3600A / EU` (en/es/fr): each route binds its own language block's crop of the 2.1/2.2 screens plus the model's control-panel box with the printed button labels (quarantined App recipes), instead of generic screens over the JE-1000F/US control-panel drawing. The page's button-label lines move into the figure's alt text.
- `JAAC-WHE-100-EUA1 / EU / en` uses [`config.charger-eu-en.yaml`](../configs/config.charger-eu-en.yaml) with the `accessory-v1` Product Manual Plan. Its Web body is limited to the source-backed Inbox, native specification table/notes, and two complete English how-to panels; it intentionally has no LCD, UPS, App, charger-only, or warranty pages. The Git-frozen AI, same-manual association for `收纳小推车`, and acceptance checklist are recorded in [`jaac_whe100_eu_en_web_intake_2026-09.md`](../code-as-doc/reviews/jaac_whe100_eu_en_web_intake_2026-09.md).
- `JE-2000E / EU / en` follows the same shared-config route. Its current-paper
  snapshot, 12× source-crop recipe, target-selected Web illustration manifest,
  and hash locks live under [`manual_sources/JE-2000E/EU/en/2.0/`](../manual_sources/JE-2000E/EU/en/2.0), with the source comparison recorded in
  [`je2000e_eu_en_web_intake_2026-09.md`](../code-as-doc/reviews/je2000e_eu_en_web_intake_2026-09.md).
  The formal EU PDF visibly names the product `Jackery Explorer 2000 Plus`
  even though its DingTalk file title uses `HomePower 2000 Plus`; keep that
  source-level distinction and never substitute JE-2000F artwork or values.
- Web Inbox preserves an optional source TIP; a source without TIP renders cards only. Word/default intake remains strict.
- FCC is rendered from the localized RST as a searchable two-column card with the FCC mark, normalizes locale-specific trailing copy, uses one component-owned spacing token for paragraphs and measure items, and becomes one column on phones. Its H1 stays available to the page outline and RTD navigation but is visually hidden, so readers see only the FCC content card. H1 bars, generic tables, governed table frames, and FCC use one shared border-box component-band width, keeping their left/right edges aligned. Each localized MEANING OF SYMBOLS warning-definition table is rebuilt as semantic searchable HTML with the PDF's full dark grid and dark warning badges; the four labels and descriptions stay localized live text and source inline widths do not reach final HTML. The following safety-symbol matrix is rendered from the same localized RST as two independent rounded Symbol/Meaning tables, matching the PDF's left-six/right-five structure so a long right-side description does not stretch the paired left row. On desktop both panels share the same outer height and aligned top/bottom borders; phones stack the two tables. The LCD icon page remains a searchable four-column HTML table: `On` / `Blink` / `Off` line-blocks stay on separate lines; the rounded frame and every row/column rule mirror the PDF hierarchy; number/icon/name cells are lightly filled; compact number badges are centered in the first column; and phones use horizontal scrolling instead of crushing the copy.

The prepared Web Inbox now passes its three cards and optional internal TIP
through public IR before figure protection. Source language and target context
are preserved; malformed card/tip rows or inconsistent IR fail before partial output is applied.
Rich text, links, image references and existing EN/FR/ES appearance are retained.
This does not admit new targets into the approved figure contract or change
Word/IDML output. Other composite figure callouts remain separate work.

For new whole-document Web builds, Inbox is no longer a temporary page-level
IR detour. Inbox, Overview, FCC, Specifications, Callout, governed Operation,
hybrid LCD Mode, Warranty, LCD Icons, Troubleshooting, both Symbols tables,
App and governed Reference Figure
instances are written once into ordered `manual-ir/v2` flow
and replayed from those embedded specs. Their source projectors run only while
assembling a new package; opening or publishing the frozen package does not
reparse RST/CSV or rediscover those eighteen component types from HTML. Historical
packages remain supported. German `JAHRE` and Italian `ANNI` use the same
component-owned 3/2 numeric badge adapter; compact Korean `3년` / `2년` headings
are parsed by that same language-neutral warranty component. Operation instances
are embedded only when the resolved target overlay grants figures; other product
skeletons keep their distinct operation panels as neutral editable flow until a
matching overlay grants them, rather than inheriting JE-1000F's
five-panel geometry. LCD and Symbols icon collections use
one repeatable, ordered asset role, so every row remains bound to the correct
packaged image. LCD, Troubleshooting and Symbols remain editable native tables,
not screenshots. App download, its inline control, and add-device panels retain
their localized copy and role-bound shared artwork in the same ComponentSpec.
Each Reference Figure retains its complete semantic fallback; an approved
composite additionally records target replace key, locale, packaged asset key,
content SHA-256 and source-fragment SHA-256. Exact-locale figures never fall
back to another language. The live semantic composition prevents broken output,
but for a finished-figure coverage slot it remains `editable-fallback` debt and
cannot pass unless that exact pre-existing row is in the ratcheted baseline.

Prepared Web FCC also passes through public IR. Its opening copy, measures,
column split and mark binding can be replayed without reopening the source page.
Invalid semantic data or an inconsistent mark binding stops the transform before
partial output. Existing EN/FR/ES copy, paragraph normalization, figure admission
and Word/IDML output are unchanged; this does not change legal text or approve
an additional region.

The signal-word legend also uses public IR while retaining its localized labels
and rich meaning cells. Malformed final labels, ambiguous tables or unsupported
row spans fail before the source table is partly changed. Existing EN/FR/ES
output and surrounding symbol-pair tables are preserved; no additional target
is admitted by this change.

The adjacent icon/meaning table now follows the same public IR boundary while
keeping its left-six/right-five panels. Invalid icon bindings, row spans or
nonempty unused cells stop before partial output. Images, rich meaning cells
and EN/FR/ES whole-page output are preserved; the existing signal legend and
target-admission rules are unchanged.

LCD semantics now come from the assembly planner's `lcd_icons` CSV page identity
or an explicit `hb-lcd-icon-table` declaration, rather than a filename or US
figure grant. Renamed slots and JP targets use the same four-column projection;
ordinary undeclared tables stay ordinary. RST and standalone `{lcd-icons}` MyST
share validation: exactly four unspanned cells, one icon, and nonempty number,
name and description. Malformed rows fail instead of being padded or truncated.
Status line breaks, inline emphasis, lists, icon sources and row order remain
authored content. The scrollable table can also receive keyboard focus; artwork
approval rules remain unchanged.

App download's store and QR columns also consume public IR. Both live copy
columns, links/emphasis, the original semantic image and artwork bindings survive
serialized replay. Invalid or ambiguous source content stops before changing the
page. The download, inline-control, and add-device variants now enter the frozen
whole-document IR as one registered App component family.

The App add-device inline button also consumes public IR. Its localized
accessible name and surrounding sentence, emphasis, links and images survive
replay; ambiguous or incomplete labels fail before changing the page. Existing
three-language output and Pandoc protection remain unchanged. Governed Charging
and App reference panels use the registered Reference Figure family described
above; missing composites remain visible semantic fallbacks but do not count as
finished artwork.

- The LCD screen-mode panel remains searchable HTML while matching the template's rounded illustration-plus-table composition across EN/FR/ES. The AC/DC Auto Resume matrix also remains searchable HTML with equal-width columns, a light left column, white right column, dark full-grid rules, and a true two-row Battery SOC cell. On phones each compact table scrolls inside its own frame instead of widening the page.
- The EN/FR/ES Troubleshooting table remains searchable HTML with the PDF's rounded dark frame, full grid, 14% light error-code column, and 86% white corrective-measures column. F6/F7 actions keep their source line breaks through Pandoc. The four Specifications tables use a matching protected 31%/69% label/value grid and preserve row-spanning labels; the web transform removes the authored bullet glyph so the shared heading theme shows one section dot rather than two, and raises both governed `①` references as semantic superscripts. Both table types scroll inside their own frame on phones.
- Warranty remains searchable shared HTML independently of the approved-figure target list. JE-1000F US keeps EN/FR/ES, while JE-1000F EU also inherits the same number-badge component for EN/FR/ES/DE/IT (`YEARS`, `ANS`, `AÑOS`, `JAHRE`, `ANNI`) without copying page CSS or target code. Both the current shared-template form (`warranty-lead` / `warranty-section` semantic containers) and an older flat review page are accepted; only those governed containers are unwrapped before HTML conversion so their nested headings are retained. The two opening paragraphs form the PDF-like rounded notice and local-law note; all six localized H2 headings stay theme-controlled and appear as floating dark labels on rounded cards. Five sections are ordinary copy cards, while Warranty Period is rebuilt from the source table as localized 3-year/2-year columns at approximately 61%/39% on desktop and one column on phones. The source 50/50 table geometry is removed, but email links, exclusions and every localized paragraph remain live content. `figure_targets` still controls target-specific Overview/Operation/Charging geometry and approved composite admission; this shared warranty inheritance does not grant artwork reuse.
- RTD also applies the shared IDML-derived responsive theme: brand-dark title bars, compact heading levels, rounded tables and warning/note groups, consistent spacing, and proportional images. A browser with licensed Gilroy installed uses it; other browsers use the declared system fallbacks. The site intentionally reflows on phones and does not claim the fixed page count or exact pagination of IDML/INDD.
- The web export protects each semantic callout before Pandoc and restores it afterward. WARNING, DANGER, CAUTION, and NOTE therefore keep one shared class structure, one light rounded visual treatment, and the theme's approximately 16% label / 84% body desktop split; every callout on a page shares one label-column width, sized to the page's widest label, so localized labels never break mid-word and the first-column boundary stays aligned. Pandoc does not add a 50/50 `colgroup` or an empty header row. On phones the same component stacks vertically.
- Web tables keep words whole and stay inside their frames. On desktop the Troubleshooting, LCD, Auto Resume, and key-combination tables fit the reading column without a scrollbar; only narrower screens scroll inside the table frame. Long localized warning badges (fr `AVERTISSEMENT`, uk `ПОПЕРЕДЖЕННЯ`) widen the MEANING OF SYMBOLS label column instead of overflowing, and the Troubleshooting code header wraps at spaces. On phones table columns grow to fit their longest word; the only exception is a raw HTML table (no scroll frame) on screens narrower than 520 px, which may still split a word so that it is not cut off at the page edge.
- Scientific subscripts and specification superscripts are protected across the same Pandoc step, so source notation such as ``V\ :sub:`oc``` renders as semantic `V<sub>oc</sub>` and governed `①` references render as `<sup>①</sup>` in every language rather than showing literal inline Markdown notation.
- Web Publish first materializes target-scoped `md` directories, then assembles `docs/publish/web/` as the homepage catalog without rewriting the repo-root [`docs/index.rst`](../docs/index.rst). The assembler also writes one collision-checked root alias named from each manual stem; it forwards to the nested model/region page with a relative target and serves as the countable printed/QR entry. The URL persisted in `HTML_link` is the canonical nested page itself, and it is written by [`web-publish-receipt.yml`](../.github/workflows/web-publish-receipt.yml) only after the publish PR merges and the deployment verifies (idempotent write with same-record readback). A pre-push three-dot diff guard permits only `docs/publish/**` in the production PR. A daily [`verify-web-deployment.yml`](../.github/workflows/verify-web-deployment.yml) run independently re-verifies every published target against the live RTD site (frozen bytes plus the expected project slug) and opens a sentinel issue on drift or wrong-site deployment.
- RTD is the responsive Web presentation surface; it is not the release authority for IDML, LaTeX, PDF, DOCX or formal print Markdown
- The [RTD manual center](../code-as-doc/dev/rtd_manual_portal.md) adds product cards, model/name search and US/EU/UK filtering at build time over the frozen index. EU is temporarily the default; EU and UK reuse the same EU publications and links, with no duplicate source or release. All published manuals remain available through ordinary links, including without JavaScript. The portal does not create missing translations or independent language URLs; the current publication retains all its existing bundled languages. Verified single-language pages expose the operator-selected GitHub Issues channel with locally copied frozen page context; legacy pages retain their current behavior. Other pages keep their current Furo/manual styles.

`fast` behavior:

- equivalent to a runtime-only `rst --prepare-only --no-clean`
- useful for template or placeholder debugging without export steps

`sync-review` behavior:

- first refreshes the runtime bundle from template/data
- then updates only data-driven review files by default
- does not replace ordinary review prose pages unless you explicitly name them with `--page-file`
- skips exact target-local paths declared by the review bundle's `manifest.json` `sync_preserve_paths`, including paths explicitly named with `--page-file`; only relative `.rst` files under `page/` or `generated/` are accepted
- data-driven means:
  - all generated CSV pages
  - all materialized `spec_*` / `safety_*` pages
  - all template pages whose source contains placeholders such as `|PRODUCT_NAME|` or `|MAIN_POWER_BUTTON_LABEL|`
  - cover pages generated from title/product identity
- generated cover pages still feed PDF/LaTeX output, but HTML now opens directly on the first manual content section instead of a blank cover-style landing screen
- manual HTML preview also suppresses most default Furo sidebar / TOC chrome, stays in a continuous reading flow instead of browser-side fake pagination, regenerates a lightweight left outline from the manual headings, and renders generic headings, copy width, figure presentation, ordinary table spacing, and the multilingual preface notice in a restrained neutral manual-reader style while keeping dedicated component layouts such as `SPECIFICATIONS`, so the result feels like a manual reader instead of a documentation site
- review-preview workspace manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout

Shared-source propagation audit (read-only):

```powershell
python -m tools.check_review_branch_sync --base origin/main --remote origin --json
```

- the ledger reads every live `review/*` branch manifest, so legacy
  `review/id-*` names do not need to encode model or region
- each row binds one affected branch to one changed shared-source file and is
  either `merge_params_safe` or `needs_human`
- `merge_params_safe` is a narrow proof: the change is confined to stable
  placeholder-bearing lines and the reviewer has not edited text outside those
  placeholders on the same line
- unresolved branch refs/manifests, non-parameter files, structural changes,
  ambiguous derivative mapping, and same-line reviewer edits abstain as
  `needs_human`; the command never modifies or syncs a branch

Equivalent lower-level examples:

```powershell
.\.venv\Scripts\python.exe tools\build_docs.py --config configs/config.us-en.yaml --model JE-1000F --region US --prepare-only
.\.venv\Scripts\python.exe tools\build_docs.py --config configs/config.us-en.yaml --model JE-1000F --region US --formats word --no-open
```

Word styling note:

- the US English Word path now reapplies the `reference_en.docx` heading, table, and default paragraph styling after DOCX generation, while leaving the generated `safety` and `spec` pages as-is
- Word output now also normalizes image relationships to embedded media before the final DOCX post-processing step, which improves Feishu and other third-party preview compatibility for image-backed tables
- the exporter preserves `manual_bundle.html` unchanged for traceability, but
  removes only `<main ...>` wrapper tags in a temporary Pandoc input. This keeps
  all page children and component order while preventing an earlier empty
  `<main></main>` from making the generated DOCX body empty; the temporary file
  is deleted after conversion

---

## 9. Version Tracking and Diff Export

Because [`docs/_review/**`](../docs/_review) is now the preferred review surface, you can keep cleaner RST history per target.

Recommended everyday workflow:

1. Pick the target you want to track.
2. Seed the review bundle once for that target.
3. Commit the review bundle as a Git baseline.
4. Edit the review bundle for normal review rounds.
5. If parameters changed in CSV, run `sync-review`.
6. Rebuild preview outputs from that review bundle and commit again.
7. Run `publish` for the formal release output, or run `diff-report` separately when needed.

### 9.1 First-Time Baseline

Use this when a target has never been tracked in Git before.

Example baseline:

```powershell
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
git add docs/_review/JE-1000F/US
git commit -m "Add JE-1000F US review baseline"
```

What this means:

- `review` prepares [`docs/_build/<model>/<region>/rst/**`](../docs/_build) from template/data
- then it seeds [`docs/_review/<model>/<region>/**`](../docs/_review)
- the commit becomes the starting point for future report comparisons

### 9.2 Daily Update Flow

After the baseline exists, the normal update loop is:

```powershell
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py word --config configs/config.us-en.yaml --model JE-1000F --region US
git add docs/_review/JE-1000F/US
git commit -m "Update JE-1000F US manual"
```

Recommended rule:

- `_review` is now the normal authoring source after review starts
- if a round also changed shared template/data, commit those with `_review`
- use `review --refresh-review` only when intentionally reseeding from the shared seed layer
- use `sync-review` after parameter changes in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) so review keeps up with regenerated values

### 9.3 Which `tracked-root` to Use

Use the tracked root that matches the scope you want to compare:

- one model across all tracked regions:
  [`docs/_review/JE-1000F`](../docs/_review/JE-1000F)
- one model and one region:
  [`docs/_review/JE-1000F/US`](../docs/_review/JE-1000F/US)
- temporary runtime-only comparison:
  [`docs/_build/JE-1000F`](../docs/_build/JE-1000F)

Recommended default:

- prefer `_review`
- use `_build` only for temporary debugging when you have not emitted a review bundle yet

Example report export for one model:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F --from-ref HEAD~1 --to-ref HEAD --include-initial-adds
```

Example report export for one region:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F/US --from-ref HEAD~3 --to-ref HEAD
```

### 9.4 How to Compare Two Specific Commits

If you want to compare a baseline commit with the latest manual state:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F/US --from-ref <old_commit> --to-ref <new_commit>
```

Examples:

- compare the previous commit to the current one:
  `--from-ref HEAD~1 --to-ref HEAD`
- compare the baseline commit to current head:
  `--from-ref a1b2c3d --to-ref HEAD`
- compare two tags or branches:
  `--from-ref release/v1 --to-ref release/v2`

Default outputs:

- [`reports/version_tracking/JE-1000F/US/*_files.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_files.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_pages.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_pages.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_fields.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_fields.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_index.html`](../reports/version_tracking/JE-1000F/US)
- legacy report path aliases remain available as [`reports/version_tracking/JE-1000F/US/*.csv`](../reports/version_tracking/JE-1000F/US) and `*.html`

Use `--report-dir` if you want a different output folder.

Useful option:

- `--include-initial-adds`
  The default report already hides one-time initial baseline Added rows. Use this only when you want to see the full first-import churn.

Automatic behavior:

- if the tracked subtree does not exist at `from-ref` but exists at `to-ref`, the report now shows an explicit note that this is an initial baseline and all Added rows are expected
- by default, the generated reports keep the note but suppress those initial Added rows
- if you pass `--include-initial-adds`, those initial Added rows are kept in the generated reports

### 9.5 Which Report to Open First

Open order:

1. `*_index.html`
2. `*_fields.html`
3. `*_pages.html`
4. `*_files.html`

Why:

- `index` gives the report homepage and target jump links
- `fields` is usually the most useful review view because it shows rendered value changes and source back-mapping
- `pages` is the next best rollup when you want page-level impact
- `files` is best when you need raw file churn, insertions, and deletions

What each report means:

- `files`: which tracked `.rst` files changed, plus insertions and deletions
- `pages`: page-level rollup with `fields_changed` counts
- `fields`: structured field/value changes extracted from list-tables and `Label: Value` lines
  For generated `spec_*.rst` pages, the report now also tries to fill `source_row_key`, `source_section_key`, `source_line_order`, and `source_csv_line` from [`Spec_Master.csv`](../data/phase2/Spec_Master.csv).
  For template-based pages such as `03_product_overview`, `05_operation_guide`, and `12_app_setup`, the report also tries to back-map changed field text to matching page-value rows by comparing rendered values against resolved placeholders.
  `fields.html` now includes built-in filters for `model`, `region`, `page_key`, `source_row_key`, `change_type`, plus a full-text search box.
- `index`: homepage that links `files/pages/fields` together and provides target-level jump links with filters pre-applied

### 9.6 How to Read `fields` Back-Mapping

Important columns in `*_fields.csv` and `*_fields.html`:

- `field_key`: the rendered field label found in the RST content
- `old_value` / `new_value`: the rendered before/after values
- `source_row_key`: the matched source row in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- `source_section_key`: the matched source section in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- `source_line_order`: the matched source line order for multiline rows
- `source_csv_line`: the original CSV line number
- when a field label itself changes, the diff now first tries to pair old/new rows through stable source back-mapping before falling back to rendered label text, so placeholder/spec renames are more likely to show up as one `M` row with both `old_value` and `new_value`

Interpretation rule:

- if `source_row_key` is filled, the report found a source row match
- if it is blank, the row is still useful as a rendered text diff, but the source mapping was not reliable enough to fill automatically

### 9.7 Typical Review Example

For a normal JE-1000F US review cycle:

```powershell
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.eu-en.yaml --model JE-1000F --region EU
git add docs/_review/JE-1000F/US
git commit -m "Refresh JE-1000F US manual"
python build.py publish --config configs/config.us-en.yaml --model JE-1000F --region US
```

Then:

1. open [`reports/version_tracking/JE-1000F/US/*_index.html`](../reports/version_tracking/JE-1000F/US)
2. click the `JE-1000F/US` target link
3. open `fields`
4. filter `source_row_key` when you want to inspect one spec or placeholder family

### 9.8 Common Mistakes

- Comparing `_build` after a fresh clean without rebuilding the same target first
- Running `review --refresh-review` without realizing it will replace the current review bundle
- Changing parameter CSV data during review and forgetting to run `sync-review`
- Forgetting that `check/html/word/pdf` now use review content by default once review exists
- Committing only `_review` when the round also changed shared template or CSV logic
- Reading `files.html` first and missing the more useful field-level diff in `fields.html`

---

## 10. Page Contracts

The repo now supports page contract checks under:

- [`docs/templates/contracts/03_product_overview.yaml`](../docs/templates/contracts/03_product_overview.yaml)
- [`docs/templates/contracts/05_operation_guide.yaml`](../docs/templates/contracts/05_operation_guide.yaml)
- [`docs/templates/contracts/12_app_setup.yaml`](../docs/templates/contracts/12_app_setup.yaml)

Current scope:

- contracts are matched by source template path from `config.pages`
- `check` validates required placeholders, spec row keys, page-value selectors, and required assets
- `required_assets` accepts both existing path values and `asset:<asset_key>`; `check` and materialization share the same model/region/language-bound resolver, so semantic scope/status decisions cannot drift between the two stages
- current coverage includes `03_product_overview`, `05_operation_guide`, and `12_app_setup`
- the active US and JP template families can each declare their own required placeholder sets
- contracts can be scoped by `allowed_languages`, `allowed_regions`, and `allowed_models`

Current contract keys:

- `required_placeholders`
- `required_spec_keys`
- `required_page_values`
- `required_assets`
- `allowed_languages`
- `allowed_regions`
- `allowed_models`

Why this matters:

- a page can fail early when required page-value bindings are missing
- fallback values in [`conf_base.py`](../docs/conf_base.py) no longer hide missing product-specific spec data
- new model onboarding becomes easier to validate before Word/PDF export

---

## 11. Common Pitfalls

### 11.1 Editing the wrong layer

Before review starts:

- edit template/data

After review starts:

- edit [`docs/_review/<model>/<region>/**`](../docs/_review)

Never edit:

- [`docs/_build/<model>/<region>/rst/**`](../docs/_build)

Use template/data only for shared reusable changes or intentional reseeding.

### 11.2 `?` appears in output

This is usually caused by dirty page-value rows in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv), not by the template structure itself.

### 11.3 Old model names survive in the new manual

This usually means one of these happened:

- a template still contains hard-coded model text
- `product_name` in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) was not updated
- the wrong `config`, `model`, or `region` was used

`check` now reports this as `STALE_IDENTITY_LITERAL`.
If a foreign model mention is intentional, add it to `checks.allowed_foreign_identity_literals` in the config.

### 11.4 Hard-coded title in config

If `build.word_title` is fixed to an old model name, the generated Word title will stay wrong even if `PRODUCT_NAME` is correct.
Prefer a placeholder-based title such as:

```yaml
word_title: "|PRODUCT_NAME| User Manual"
```

---

## 12. Verification Checklist

After changing templates or CSV values, verify at least the following:

1. `python build.py check --config ...` succeeds
2. `python build.py doctor --config ... --model ... --region ...` reports no blocking errors for the current Word/PDF path
3. the target bundle appears under [`docs/_build/<model>/<region>/rst/`](../docs/_build)
4. the review bundle appears under [`docs/_review/<model>/<region>/`](../docs/_review)
5. generated pages contain no unresolved placeholders such as `|PRODUCT_NAME|`
6. generated pages contain no stale model names from older products
7. safety and spec still resolve from the intended source, including the JP template-backed safety page and the remaining CSV-backed generated pages
8. the expected `.docx`, `.html`, or `.pdf` file is generated when requested
9. `publish` or `release-manifest` produced a JSON / CSV record under [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../reports/releases); a versioned Publish also produced an immutable `versions/<version>/snapshot/release_snapshot_identity.json` and the manifest points to that archive
10. `python build.py release-rebuild-verify --manifest <manifest.json>` reports `status=passed` for the versioned release on its recorded toolchain

Useful checks:

```powershell
Select-String -Path docs\_build\JE-1000F\US\rst\page\*.rst -Pattern '\|[A-Z0-9_]+\|'
Select-String -Path docs\_build\JE-1000F\US\rst\page\*.rst -Pattern '\?'
git status --short -- docs/_review/JE-1000F/US
```

---

## 13. One-Sentence Rule

Templates and CSV create the first draft.
[`docs/_review/**`](../docs/_review) becomes the target editing source after review starts.
[`docs/_build/**/**/rst/**`](../docs/_build) remains the runtime publish bundle behind the final outputs.
## Start Review, Build Draft Package, Publish

- `process-build-queue` no longer runs `sync-data` unconditionally; it now refreshes phase2 only when `Document_link.是否强制刷新数据 = true`.
- `Document_link.data_sync` is the writeback field for that decision: `refreshed`, `skipped`, or `failed`.
- `sync-review` now also refreshes `generated_page` placeholder files under `page/*.rst`, so forced-refresh queue builds update the final rendered page text instead of keeping stale review placeholder content.
- `build.py check --source review` validates the rows needed to identify the target and render generated-page recipe inputs, plus footnotes referenced by those inputs, but retired `Spec_Master` rows and unreferenced `Spec_Footnotes` definitions that the review bundle does not consume no longer block Build Draft Package.
- `Workflow_action=Build Draft Package`, `Workflow_action=Publish`, and `Workflow_action=Web Publish` are the build actions.
- queue routing only looks at `Workflow_action`: use `Start Review`, `Build Draft Package`, `Publish`, or `Web Publish`, and keep `Doc_phase` blank.
- `feishu-draft-build-queue.yml` is the Build Draft Package worker on `main`; dispatch it on `main`, and let `Document_link.Git_ref` decide which review branch gets fetched and built.
- `feishu-start-review.yml` is the Start Review worker on `main`; dispatch it on `main` so review-init always uses the latest worker definition.
- `feishu-build-queue.yml` is the Publish-stage worker on `main`; dispatch it on `main`, and let `Document_link.Git_ref` decide the review-branch source when present.
- `feishu-web-publish-queue.yml` is the Web Publish worker on `Hello-Docs/main`; it writes the generated `publish` candidate, validates that its PR diff contains only `docs/publish/**`, opens or updates `publish -> main`, and writes the RTD link. It never merges the selected `review/*` branch.
- if your team uses OpenClaw as the operator entrypoint, install the repo package under [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer) and use `/start-review`, `/build-draft`, `/publish`, `/web-publish`, and `/manual-status` instead of hand-calling the GitHub API.
- the OpenClaw bridge does not move `build.py`, Feishu secrets, or queue writeback out of GitHub Actions. It only dispatches the existing workers on `main` and tracks them through `openclaw_dispatch_nonce` plus the `openclaw-run-metadata` artifact.
- OpenClaw dispatches `start-review`, `build-draft`, `publish`, and `web-publish` with the resolved Feishu `record_id`; both publish actions require explicit confirmation.


JP IDML screenshot checks: safety icons must appear as images, energy-saving
thresholds must show their resolved values, and recovery conditions must stay
in the correct table column. Literal `.. image::`, `:alt:`, `:width:` or unresolved
substitution names are failed output, even when the package has no overset.
Keep the package version with each screenshot; see the
[JP review record](../code-as-doc/reviews/je1000f_jp_native_overflow_2026-09.md).

JP IDML uses its manifest-declared Japanese TOC payload with dynamically
collected headings; the TOC is excluded from non-IDML builders. Its
`front_matter_roles: ["cover", "toc"]` declaration controls both the TOC slot
and fallback folios, so the first body page is 01. An explicit renderer page
plan still owns its physical folios. Front-matter metadata alone does not
create a reference-layout sidecar. Final story reflow and TOC page accuracy
must be checked in InDesign screenshots of the identified candidate package.

The six approved JE-1000F/JP illustrations resolve through scoped registry
overrides. Product engravings and logos remain; added manual annotations are
removed. Other targets retain their existing asset resolution. Local approved
files are usable for review while dedicated asset-Base archival remains
pending write permission; local hash checks do not prove online archival.

`build.py idml` now prints `[export-idml] STORY SPANS`: each prose story's
allocated page chain, with the height estimate shown in brackets whenever the
two differ. A story allocated more pages than its content composes into is
what produces blank body pages, so read this line before asking for another
screenshot round. Under the measured-LaTeX fallback plan an unmatched source
between two anchors no longer donates its pages to the preceding story, and
Warranty and App Setup are kept in separate linked chains so the App section
starts its own page instead of continuing under the warranty tail.

Under a measured fallback plan a story's chain is never longer than its own
content needs. LaTeX and the IDML writer compose at different densities, so an
anchor distance that is longer than the composed section used to leave trailing
empty frames — blank body pages. Targets with an approved reference or target
assembly plan are unaffected. When a section now runs out of room, InDesign
marks it as overset rather than printing a blank page; that is the intended
trade, so check the red overset markers after a rebuild.
Prepared-source integrity: a declared page include that is missing or is not a
file now stops source discovery with the index and source path. Registered
prose macros need complete arguments; unsupported content around recognized
macros increments `skipped_raw` and fails strict Manual IR validation. A valid
macro no longer hides adjacent unsupported copy. Existing language/tag
selection and successful payload formats remain unchanged.

IDML handoff validates the source `manual.ir.json` before copying artifacts or
writing reports. Missing IR is explicitly unavailable; corrupt IR is an error,
not a zero-skipped report. This IDML integrity path remains on its existing v1
producer and does not by itself consume the Web whole-document v2 flow or
certify native JP layout. See the
[shared-source plan](../code-as-doc/dev/latex_indesign_same_source_plan.md) for remaining consumer and parser boundaries.


Web 规格表已接入公共 IR 校验，构建命令不变。Web 构建会保留规格中的链接、强调、
换行和脚注，不再借用 Word 的纯文本抽取重建。任何声明规格表不合法时，本次规格
转换整体失败，避免只转换前半页。新整本 Web 包已把规格 ComponentSpec 写入 v2
中立 flow，并从冻结 IR 直接重放；Word/LaTeX/IDML 的整本入口和 JP 原生排版仍需
分别验收。


LCD 图标表和故障排除表也已接入同一条公共 IR 消费路径，主构建与独立 Markdown
站点共用，命令不变。图标替代文字、列表、链接、图注和表头仍来自原文；同一批
表格中有一张不合法时，整批转换失败，不留下半页已转换的结果。这仍是表格级
组件接入；整本 v2 flow 已建立，其他组件和四端 adapters 尚未全部迁移。


独立 Markdown 的 `{spec-table}` 也已复用公共规格表 IR，不再单独计算合并行和
拼装表格。参数标题继续用作组件标签，不增加可见标题；上下标和空标签续行保留，
裸圆圈脚注编号使用统一上标样式。规格表、LCD、故障排除三类表格已在两种 Web
入口接通；它们写入整本 v2 IR 并由四端共享消费仍是后续组件刀。


生成 Web 的警告／提示框在 Pandoc 转换前后也已通过公共 IR 交接，构建命令不变。
框内原文、链接、列表和图片保持原样；IR 损坏或声明的标签／正文结构不完整时构建
失败。已整体保护的复合插图内提示框仍待迁移；整本 Web 的 v2 flow 底座已完成，
但复合组件和 JP 原生版式仍需独立验收。


独立 Markdown 的 `{callout}` 也已接入同一个公共 IR 消费器。正文仍由 Sphinx
处理，内部链接、图片、列表和强调保留；自定义标签的 `:variant:` 与配置语言会
一起进入校验。提示框内嵌表格或其他提示框暂不受共享契约支持，会带来源位置报错，
不会截断后继续输出。命令和编辑位置不变。

### JBP-3600A 欧规英文概览与 LCD

JBP-3600A EU/en 概览使用不含标题的独立正面/侧面插图，LCD 使用带引线插图和原生两列说明；见[版面修复记录](../code-as-doc/reviews/jbp3600a-overview-lcd-20260916.md)。

HTP011（0924）英文原稿更新使用[Git-only 结构源](../manual_sources/JBP-3600A/EU/en/README.md)，章节参考 HTP017。开关说明、间距与锁扣标注为可选择文字，时钟从底图移除后用公共 CSS 绘制。使用原有 BP 配置构建，无需写飞书；工程 PR、本地预览验收和正式上线分别确认。见[本轮原稿及验收记录](../code-as-doc/reviews/jbp3600a-eu-en-htp011-20261002.md)。

共用时钟可识别意大利语 `3 secondi`、德语 `3 Sekunden` 和原稿的 `Drei Sekunden`，均显示 `3s`；操作说明仍保留各语原文。

冻结稿重放时，带样式的规格章节标题也进入网页目录。锁扣标签按原稿使用深底白字，手机字号至少 14px，文字留在对应图示位置。此修正产生待审基线差异，不能自动替换已确认的英文基线。

共享移动端样式为锚点跳转预留顶栏高度；直接打开章节链接或点击目录后，完整标题显示在固定顶栏下方。

本轮八语全文及桌面/手机版式已独立验收，透明符号复用后的 EN r6、FR r5、ES r3、DE/IT/UK/PT/NL/PL r2 也已完成九语差量验收；`uk` 是乌克兰语。2026-10-03 操作者授权合入上线（MA-244），登记[新批准发布源](../manual_sources/JBP-3600A/EU/git-20261003-44b6ce61-reviewed/README.md)，保留德语警示图文配对、意语规格/线缆/保修差异及其余已审原稿异常。旧候选和历史证据不改写。九语沿用现有发布准入，八语分别登记章节及组件适用性；PR1409 的新英语继承门禁不在当前调用链内。工程 PR、Git-only 发布 PR 和 RTD 验收分阶段核验，不写在线表或队列。

### JBP-2000B 欧规英文网页

现行 V2.0 的英文网页使用独立的
[Git 结构源与构建说明](../manual_sources/JBP-2000B/EU/en/2.0/README.md)。
先本地验收，再按已有流程提交 Read the Docs 预览；不需要写线上多维表。

Web 提示框支持 `NOTES` 标签；纯文字 LCD 说明表隐藏无对应图标的编号和空图标列。已包含在整图中的开关文字，通过插图覆盖声明移除重复显示。

For the EU charger family, the Web illustration path resolves from the selected model and region. Charger pages retain their installation components without inheriting power-station LCD or auto-resume tables.

### Manual Center 内容检索

产品优化建议通过右下角按钮打开弹窗，关闭后保留已填内容。
产品优化建议入口与内容检索、售后反馈、访问统计分别配置。访客在网页填写，
由独立接收接口交给机器人写入专用飞书多维表，不要求访客登录飞书。
本机 OpenClaw `main`（HT-Docs）已被指定为 Mac agent。接收服务负责入库，
OpenClaw 负责入库后的分析；分析结果先供人工审核。未验证公网接收地址前不启用线上入口。
2026-09-25 起线上入口已关闭：试运行用的临时隧道失效，提交送不到，已清空接收地址；换成验证过的长期地址后再开启。
配置、数据边界和联调步骤见 [产品 VOC](../code-as-doc/dev/product_voc.md)。

首页以紧凑产品列表呈现已发布手册；同一关键词框同时检索型号、章节及
正文（含文字表格），结果可直接进入对应章节。地区、类别及语言筛选适用
于产品和正文结果；语言未核验的历史发布不冒充单语版本。图片内没有对应
正文的文字暂不纳入检索。静态索引随 RTD 构建生成，无需配置搜索服务。
直接打开 `/search.html` 时会先显示搜索框和提示；提交后仍使用 Sphinx 原有
`q` 参数、静态索引和结果列表，不新增外部搜索服务。
实现与边界见 [Manual Center](../code-as-doc/dev/rtd_manual_portal.md)。

说明书资料库只提供说明书查找和阅读，不放知识库链接。按操作者的最新发布选择，“产品知识”“市场与政策”“产品案例”在同一个 RTD 项目公开发布，无需登录，通过直达链接访问；相应内容已录入飞书知识库多维表。产品知识用列表结合典型电气示意解释实际产品；市场与政策按“政策变化 → 原理解释 → 产品影响”阅读，可筛选国家、主题、核实状态和关键词。页面不展示原始资料截图或整理过程，原始截图也不复制到网站；当前内容通过审核后的快照发布，尚未接入多维表自动同步。数据边界见[市场与政策](../code-as-doc/dev/rtd_manual_portal.md#市场与政策)。

说明书中心和 AI 分享作为两个独立界面维护；`/workspace/` 是两者的个人内容
入口。AI 分享稿及其演示、配图和参考资料保存在 Hello-Docs 的
`docs/knowledge/ai-share/`，不放进 auto-manual。随同一次 RTD 构建发布到
`/ai-share/`。两个界面共用 RTD 项目的可见性设置。AI 分享是可选入口：分享包缺失时，
`/workspace/` 和系统建设页照常生成，只是不显示分享入口。

RTD 生成整站时会在本轮构建内复用已校验的目录，避免每生成一页都重复扫描
所有说明书；下次构建仍重新校验，说明书内容与发布检查保持不变。见
[目录构建校验](../code-as-doc/dev/rtd_manual_portal.md#catalog-validation-during-a-build)。

四语原生网页的标题、前言分段、安全警告框与质保卡片沿用英文版公共组件。LCD 显示序号、图标、名称和说明四列；App 截图下保留 2.1–2.5 编号。标注线密集的产品前/右视图使用对应语言成品图，正文和表格仍可选择、搜索。

Native PDF LCD intake preserves semantic status lines and bold status prefixes in the existing `HB-TABLE-LCD-ICON` component. The verified uk/pt/nl/pl paragraph boundaries also separate App setup and retained-setting notes; printed line wrapping is not copied into Web layout. Numbered troubleshooting measures each start a new line; the emergency-charging lead retains its bold emphasis. Shared reference-figure captions follow the artwork, matching the App 2.1–2.2 captions. Source wording, governed icons and historical frozen versions remain unchanged.

产品前／右视图的小标题使用图片外的原生网页文字。四语成品图只保留插图、参数与标注线；冻结绑定 `overview_finished_panels` 的 `captions_embedded: false` 恢复可见标题，旧版 `true` 仍隐藏重复标题。导出时按源 PDF 坐标排除标题，保留来源哈希及已批准勘误，不改写历史冻结版本。

自动恢复条件使用共享 `HB-TABLE-AUTO-RESUME`：两列表头，左侧 3 条、右侧 4 条，中间左格跨两行。四语原生 PDF 录入通过 ComponentSpec 调用既有 Web 表格渲染器；标题和引言在表外，条件为可选文字，不以列表或截图替代。新版本保留全部图片及已审勘误。

交流充电图的源稿裁区必须包含完整外框和左右下圆角。说明文字继续作为网页正文；移除图内重复说明时只剥离文字，不删除背景、产品线条或边框。四语共用图修复须一起重建并核对其余图文不变。

太阳能接线图若自带外框和留白，外层底色须与留白对齐，避免生成双重灰边。太阳能板可复用，整张主机接线图仍须核对型号与插座／接口版本；不能仅按语言一致就跨地区替换。

按键组合表由共享 `HB-TABLE-KEY-COMBINATIONS` 承载三列表头和操作行，通过 `manual-ir/v2` 的 ComponentSpec 直接复用英文 Web 表格渲染：深色圆角边框、40/25/35 列宽、首列灰底及正文常规字重。原生 PDF 的操作文案取文字区域，排除时钟图旁重复的时长标记；不改动句内时长或功能内容。

Charging reference diagrams reuse the shared live-label component: captions occur once and note pills use HTML/CSS over artwork without baked text or white pills. Other portable power stations may reuse the component with their own verified device/interface artwork. See [the JE-2000 intake and regression record](../code-as-doc/dev/je2000_eu_new_locales_ir_adapters_2026-09.md).

## 欧规网页共享组件防回退

新型号、地区或语言录入也遵循同一套[图文分工规则](../docs/renderers/contracts/STYLE_DEFINITION.md#新录入网页的图文分工)：文字和承载它的灰/白框用 HTML/CSS；底图保留完整主机、线缆、放大圆和实际外框。密集引线概览图、App 界面、二维码及产品铭刻按各自例外保留。四语已有测试不替代中规等新入口的组件绑定、哈希和桌面/窄屏验收。

新发布的欧规／英规候选包必须携带 IR，并符合已登记的章节、共享组件及变体要求。删除组件、旁车文件或扩大遗留例外会阻止发布。新增型号／语言要先登记适用章节；历史 App 整图和 LCD 降级不会算作已复用。历史发布仍可回放，详见[共享组件准入与迁移](../code-as-doc/dev/prepared_component_admission.md)。

维护旧版网页表格时，在源 RST 中声明共享表格类型，重新构建整本；不要直接修改生成 HTML。纯文字 LCD 说明保留原编号（包括空编号），不自动补图标。多语质保开场可有多段，顺序和段落边界必须保留。定义见 [共享样式](../docs/renderers/contracts/STYLE_DEFINITION.md#authored-text-references-hb-table-reference)。

旧 RST 手册的共享样式也须核验实际章节绑定。JE-3000C 欧规五语与 JE-1000H 欧规英语的操作表沿用同一组自动恢复、LCD 模式和组合键组件，原文和图片保持源稿所有权。代码修复不自动改变已发布冻结版本：需重新构建、核验并发布。进度与剩余范围见 [EU shared-component rollout](../code-as-doc/dev/eu_shared_component_rollout_2026-09.md)。

### 新增语言的共享样式检查

新增原生 PDF 语言沿用同一组共享组件；译文、型号参数和对应地区的图片由源稿决定，表格、质保卡片、操作区和 App 的版式由共享组件负责。现在导入/冷重放与发布封存会检查章节所需组件是否真的存在。报错 `shared component coverage failed` 时，根据提示的章节和组件 ID 补绑定，不能用普通表格或截图绕过。密集标注整图保留已批准的引用图方式。

验收新增语言时，逐语检查图内提示框是否遮住按钮圆图或引线，以及手机换行后是否越界。节能图只应有一个时钟，源稿 App 步骤编号若仅在截图下出现，应保留这一结构。修复提取范围和图文绑定后生成新的候选预览；既有语言的冻结版本保持不变。

指定沿用源稿完整配件排版时，应保留虚线框、配件标题与“单独销售”徽标的相对位置，
不能把徽标文字当成第四个普通标题。对应语言成品参考图保留图内文字，另提供检索和
读屏文本，不重复显示图外标题；该排图内文字需回源稿修改，不是独立 HTML 文字框。
充电、UPS、扩容等完整大图也应保留原稿灰底、白色说明区和圆角边框；透明底规则
仅用于 LCD／状态图标、独立按钮符号等小图，不用于完整面板。

共享代码更新后，旧的冻结手册不会自动迁移。每次修复需列出受影响语言、生成新冻结版本、检查桌面/手机并重新发布；验收应打开正式 RTD 路由。检查通过表示组件覆盖完整，仍需核验译文、参数、地区图片和实际版面。技术边界见[共享组件准入](../code-as-doc/dev/web_publish_pipeline.md#native-multilingual-shared-component-admission)。

JE-1000H EU LCD 图标表（2026-09-30）：六语共用同一组冻结图标引用，并通过
`HB-TABLE-LCD-ICON` 保留编号、状态分行和加粗。发布门禁已取消六个纯文字表例外，
改为要求真实 LCD 组件；缺图不能再静默退回纯文字。素材记录见
[`lcd_icon_provenance.json`](../manual_sources/JE-1000H/EU/en/2.0/lcd_icon_provenance.json)。
连接电池包的现有小图仍是清晰度待办，未重新裁图或变更线上源表。

新原生 PDF 的 LCD 表对相邻同编号条目（如高温／低温）保留两条独立图标、名称和说明，但编号只显示一次并跨行居中。该布局由冻结 ComponentSpec 的 `number_cell_layout: span-adjacent-equal` 声明；未声明的历史冻结版本维持原样，编号不跨非相邻行合并。

日规等审核稿中的纯文字装箱清单，Web 整本 IR 将完整的三项无图清单映射为 `HB-TABLE-REFERENCE/plain-inventory`，复用公共表格样式，保留原有注意事项和强调。带图片或紧邻提示表的清单仍按 `HB-SPECIAL-INBOX` 校验，缺图会阻止发布；不补入其他地区的图片。

JE-1000F/JP 的 Web 展示契约保留日规质保的 7 个正文章节与原有换行，不强制生成欧规年限卡片；旧 App 的“控制面板图 + 三段按钮名称”通过明确的源图绑定进入共享 App 组件，按钮标签保持日文并按 AC/DC 语义定位。

Web 操作图只保留一层实际外框。源图已有浅灰圆角框时，不再叠加网页边框；原稿图内的前提说明仍在图内左上方，用可选择文字和 CSS 胶囊承载。

Web App 的编号步骤标题按原稿保留大小写，与步骤正文左边线对齐，不额外显示圆点。重新生成的候选包采用共享样式，旧冻结包需单独更新并检查预览。

中规审核源也支持三项无图项目列表：复用 `plain-inventory` 并保留列表强调和外部备注。独立 LCD 模式图后紧邻的四列表（首列全部为空、三项表头和六行动作）保留原图与表头，映射至 `HB-TABLE-REFERENCE/lcd-actions`；非空占位列或结构变化拒绝导入。显式绑定的 App 双图之间若有一张纯文字备注表，共享面板将其保留在面板后方，备注仍独立进入共享提示组件，不被图片或标签吞掉。

通用 LCD／状态图标及 POWER、AC、DC/USB、LIGHT 按钮图先按功能语义复用现有共用素材（Web 按钮图使用透明 SVG），不从各语言 PDF 重裁带底色的小图；仅在共用素材缺失或有明确机型差异时才提取。仅上述 LCD／状态图标、独立按钮符号等小图默认透明底，移除其外围单元格底色和边框；保留符号、按键面和丝印。大图面板保留灰底、圆角、外框和引线，不能套用小图规则。普通图采用无字底图加原生文字，表格保持原生 HTML，密集引线图不重复显示图内文字。规则见[共用图标优先](../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)。

JE-2000F/CN 沿用 `configs/config.zh.yaml` 中规共享配置与现有审核源；预览、发布按审核稿原样构建。

新增 JE-3000C/EU 葡语、荷语、波语沿用现有六语网页的公共 IR 和组件。
图中标签从各语原稿的坐标范围读取，保持可选文字；同一个 PDF 文本块里的多个标签
也分别绑定，避免漏用共享图文组件。安全提示的标签在原生读取顺序首尾均能识别，
正文只显示一次。技术事实矛盾记录为待确认，预览可以打开，但发布封存会阻止该语种。
范围、来源和验收见[三语录入记录](../reports/je3000c-eu-three-language/README.md)。

### 原生 RST 提示框的 Web 保留

Native RST `note`, `tip`, `warning`, `caution` and `danger` directives pass through the existing `HB-CALLOUT-STRIP` component before Pandoc. Their explicit body boundary, rich paragraphs and lists survive Markdown/Sphinx export; adjacent prose stays outside the box. Docutils titles such as `Caution!` retain their displayed punctuation and registered semantic variant. This also applies to the shared Word HTML adapter.

PDF 对照修正时，表头、圈号、图标、提示标签和说明文字都以操作员提供的原稿为准。
不要补写滚动提示或把购买提示改成 NOTE。LCD 图标表可分别声明有编号四列或
无编号三列；设备图与操作表、保修卡片等原稿组合使用受保护的 RST 容器，
需在实际 Sphinx 页面检查桌面和手机显示。独立设备图应排除误截的表格边框；充电等完整成图应保留原稿的灰底、分区、
圆角及图内标签。保留设备、手指、引线及产品标记，并单独记录来源、页码、裁切范围和哈希。


JE-100C/EU 的 Web 本地源现支持英文及新增法、西、德、意、乌、葡、荷、波，共九语。
按语种选择 `configs/config.eu-<lang>.yaml`，复用英文冻结包中的产品身份数据，
正文和插图由各自语言的原稿及修订记录绑定；[示例命令与来源边界](../code-as-doc/build_doc_guide.md#je-100ceu-nine-language-web-source)。
乌、葡、荷、波的旧版 AC 充电等差异已按操作者指示对齐新版英文，原始来源和修订依据均保留。
葡语代码为 `pt`，区别于巴西葡语 `pt-BR`。本地构建通过不等于线上发布；
正式发布仍走既有审核、冻结快照、Hello-Docs 和 RTD 流程。

### 原生 PDF 的已确认勘误

原生语言导入的 `source/errata.json` 可为已确认条目登记 `native_bindings`：源哈希、确认记录、来源页码、精确字段路径以及修改前后全文。适配器在共享组件构造前应用，原始提取证据保留；原文或来源不匹配即失败。文字勘误涉及带标注的概览图时，须同时修正图内文字并重锁资产哈希；清空待确认状态不能代替实际修正。

冻结 PDF 参数表的语义换行由 `source/target_layout.json` 各语言的 `specifications.value_breaks` 声明（`group`、从零开始的 `row`、唯一匹配的 `before`）。例如车充／PV 共用单元格在 `PV:` 前换行；源文字和已批准勘误先保持完整匹配，再投影为共享 IR 的 `line_break`，不恢复印刷版所有折行、不拆出额外表格行。更新时创建新的冻结版本，旧版本保持不变。

HTP011 英文无图标 LCD 说明通过共享 `lcd_descriptions_template.rst` 显式绑定
`HB-TABLE-REFERENCE/lcd-descriptions`，保留名称／说明两列及原稿文字；
发布封存直接校验组件，不再依赖该目标旧 LCD 表的内容哈希例外。

Intake preparation: [source-copy work packets and shared-art review](../code-as-doc/dev/manual_intake_assistance.md) enumerate pending work without approving a baseline or publishing.

共用图确认清单可通过 `tools.manual_intake_assist art-review --selections` 导入；
太阳能保留型号/数量标识，车充文字用 HTML/CSS，操作与按键图片不纳入共用库。
图标按原稿中匹配的符号复用，独立图标须真实透明底。

### FridgeGuard US 英文网页文档

JE-1000E-SIL / US / en 使用用户提供的 AI 母版，走 Git-only 冻结源；
不写飞书源表或构建回执行。仍使用 `configs/config.us-en.yaml`，构建时显式
指定冻结的 `--data-root`。源文件、命令、原稿疑点与验收结果见
[录入记录](../code-as-doc/reviews/je1000e_sil_us_en_web_intake.md)。

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
alone does not establish the final portal layout. See the [build guide](../code-as-doc/build_doc_guide.md).

### FridgeGuard US native FR/ES local candidate

French and Spanish use `configs/config.us-fr.yaml` / `configs/config.us-es.yaml`, target `JE-1000E-SIL`, region `US`. Their Git-only data roots are `data/manual_sources/JE-1000E-SIL/US/<lang>/git-20261002-537939d0/phase2`; edit the corresponding `docs/templates/page_fridgeguard/<lang>/` source. Build with `build.py md --lang <lang> --data-root <data-root> --staging-root <isolated-output> --skip-root-index`. Native source discrepancies and asset reuse are recorded in [the intake review](../code-as-doc/reviews/je1000e_sil_us_fr_es_web_intake.md). Publication resumed under the operator’s 2026-10-03 “推上去 发布” authorization; release acceptance is tracked in the intake review.

Frozen Web heading inline spans remain inside MyST titles, including the shared
`hb-sold-separately` badge; use shared `h3.hb-heading-label-pair` when the native small title and availability badge have separate capsule backgrounds. Verify both the heading and its navigation link after
assembly. Key combinations use `HB-TABLE-KEY-COMBINATIONS`, with authored button
pairs and shared hold-duration clocks. Match product markings before choosing
a shared button variant; function names alone do not establish artwork reuse.


新增 Web 底图的独立说明框必须与说明文字一起移除，由共享 CSS 绘制；复用旧图也需先检查裸底图。新冻结候选封装会检查已声明 ReferenceFigure 填充文字框区域的底图哈希和真实像素，拒绝残留的对比色空框；同色、仅轮廓或未声明框仍须视觉核验。完整面板、产品表面与 App UI 按角色保留。详见[共用取图规范](../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)。

原稿标题条内型号使用共享 `hb-heading-model`，整行图标警告使用
`HB-CALLOUT-STRIP/warning` 的 `hb-source-warning-lockup` 声明；图内说明通过
ReferenceFigure 源坐标保留在图内，不能移为图后段落。具体样式声明见
[原稿标题型号与完整警告框](../docs/renderers/contracts/STYLE_DEFINITION.md#原稿标题型号与完整警告框)。

PACKAGE LIST 的配件名称与 “Sold separately” 应为可编辑网页文字，分组外框及标签框由共享 CSS 绘制。使用现有匹配配件图和通用文档图标；新语言沿用同一套图片，只替换原稿标签。退役整图不可再次绑定，缩略封面细节的省略须在原稿覆盖记录中说明。

原稿里单独成行的深色圆角提示应保留为可选取的独立正文段落，使用共享 `hb-prose-pill`，不要拼入前段或转换为标题。

原稿放在图内的说明，应保留在图内；桌面沿用原稿位置，手机可在同一灰色图框内排为可读说明，不能重复放在图外。

FCC Web 正文左右高度明显失衡时，可在现有 FCC 组件外声明共享 `hb-fcc-balanced-flow` 容器。桌面使用自动平衡的两栏文字流，FCC 标志左浮动并允许文字在其下方续排；手机回到单栏。DOM 保持开场、NOTE 正文、措施列表和 MODIFICATION 的原文顺序；不改 ComponentSpec 的印刷分栏点，也不按机型复制 renderer。

### 学习产品知识

从知识页的侧栏进入“产品知识”，或直接打开 `/products/knowledge.html`，无需登录。选择知识标签、型号和区域，阅读一句解释、实际用途与常见误区，并展开对应产品的说明书入口。说明书首页不提供此入口。操作和兼容性按对应地区的说明书执行。维护方式见[手册中心说明](../code-as-doc/dev/rtd_manual_portal.md)。

产品知识页按列表结合原理图阅读。选择“AC 输出与负载”，再选择地区与型号，可查看单口与合计功率、启动负载、输出规格、保护和备电路径；具体参数和操作通过对应说明书核对。

AC 知识页的典型电气示意可用于学习开关桥、滤波、插座并联和切换触点。HomePower 3600 Pro Max 的备电案例单独列出：120/240V 分相、供电模式限制、ATS/MTS 与主机级联，来源链接指向正式发布的 Read the Docs 说明书；教学图不作为实际安装接线图。

JA-AD600A/EU 英文的五张说明图已分离需要翻译的文字，采用共用底图加原生标签；尺寸、单位、固定铭刻和 A–F 对应编号保留。各语替换文字时复用同一底图，详见[共用底图复核](../docs/renderers/contracts/STYLE_DEFINITION.md#ja-ad600a-eu-共用底图复核)。

仅含一段声明的 FCC 可用 `hb-fcc-composition hb-fcc-statement` 复用完整 FCC 的浅灰圆角面板和紧凑正文，保持单栏和原稿内容；完整 FCC 的 NOTE / MODIFICATION 不应补入短声明。原生 H2 标题保留在 section 中，正文和左侧共用 FCC 标志由既有受保护 figure 通过原生 flow 输出；共享 CSS 将它们排在同一面板中。


短版 FCC 的标题/正文/标志排版由共享 `web_fcc_statement.css` 承载，接入既有样式组装列表；完整 FCC 样式保持原模块，不提高维护性行数上限。

JBP-3600A EU 九语的正视图、左视图采用同一显示尺寸上限（25rem、34rem），保留各语图片原稿和比例，窄屏内按可用宽度缩放。


SlimPower H1（JE-1000E-WH / JP / ja）使用[批准的日文冻结源](../manual_sources/JE-1000E-WH/JP/ja/git-20261008-efb663e3-reviewed/README.md)，保留原候选与原稿文字、图框和安全符号。`approval.json` 绑定原稿哈希、已审候选及独立章节/组件要求；回放前先验证批准身份，再通过共享 Manual IR / ComponentSpec 输出。日规沿用现有区域准入，不登记 phase2 或提升全局资产。正式发布仍按 Git-only 单语凭据、Hello-Docs 生成式发布 PR、RTD 回执/资源和桌面手机逐段核验，打印版本未知时保持未知。
