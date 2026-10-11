# Build guide: Web Publish, frozen sources and the RTD portal

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

Frozen external Web sources can bind a source-local presentation sheet in Manual IR
metadata as `source_stylesheet: {path, sha256}`. `replay_package` requires that file
to remain inside the package with matching bytes and emits its CSS in the document's
MyST HTML style block. This preserves reviewed source geometry when the aggregate
portal selects its own global stylesheet. Historical packages without the declaration
keep their existing output. Freeze the CSS input and renderer hashes; reject changed,
missing, escaped or HTML-containing stylesheets. Verify both standalone and aggregate
desktop/mobile pages, since a standalone target's `conf.py` does not configure the portal.


Fresh external frozen symbol tables require source-bound asset admission before evidence sealing.
The actual symbol rows must pass native PDF glyph and real transparency checks, including RGBA
rectangles; name/meaning matching alone is insufficient. See the
[Web artwork contract](../../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)
for fields, outlined-caption review and the fixed pixel tolerance. Existing sealed receipts keep their
original verification. Asset-intake supports unchanged retained native vectors as SVG, preserving
group opacity; SVG cannot use fill overrides or stroke suppression.

生产完成触发、冻结快照审核与线上哈希确认见 [工作台数据持续更新](../dev/workspace_data_refresh.md)。

设计系统 `/workspace/design/index.html` 由同一 portal 在构建时读取 `tools/web/stylesheets.py` 拼装的 `web_manual.css`，生成颜色、字体与组件预览；“图标与素材”分页列出共享素材清单与目录里的文件，“印刷规格”分页读取 `data/layout_params.csv`。说明与预览标记维护在 `tools/rtd_portal_assets/design_system/`，见 [RTD portal](../dev/rtd_manual_portal.md#design-system-page)。

系统数据 `/workspace/data/index.html` 在构建时读取发布清单 `docs/publish/publish_manifest.json`、`data/model_capabilities.csv`、`data/model_languages.csv`、`docs/_review/` 与 `data/asset_registry.csv`，汇总已发布网页说明书、机型能力和素材注册情况，页面内可按区域和机型筛选；见 [RTD portal](../dev/rtd_manual_portal.md#system-data-page)。

说明书工作台 `/workspace/deliverables/index.html` 由现有 RTD portal 构建时聚合发布目录、交付与语料快照、组件定义与明确目标绑定。首页采用结论优先布局：常用工作入口、生产规模及交付入口条形图、三类资产关系图、投入与回流简况；完整列表、工作地图和统计证据折叠展示，锚点导航自动展开目标；配置引用不等于实际消费。指标口径、来源时间、SHA-256 和对象列表可展开核验。无事件历史时显示 Not tracked yet，读取失败显示 Unavailable；详见 [工作台统计契约](../dev/workspace_production_evidence.md)。

Web 引用块在深色站点主题下仍使用配对的浅底深字；源稿要求左侧灰标签、右侧白正文时，可在 `manual-callout-table` 上使用 `hb-callout-label-shaded`。已发布内容的结构勘误须更新冻结源并重新发布，修改模板本身不会改变线上快照。
JBP-3600A EU/en 概览使用不含标题的独立正面/侧面插图，LCD 使用带引线插图和原生两列说明；见[版面修复记录](../reviews/jbp3600a-overview-lcd-20260916.md)。

Verified single-language pages omit a duplicate plain leading language label at render time; the locale switcher and frozen source remain intact.

JBP-3600A EU/en 装箱清单使用纯插图，边框与编号由 Web 组件生成；见[修复与发布边界](../reviews/jbp3600a-inbox-artwork-20260915.md)。

RTD catalog cards may use explicit model/market artwork overrides or a static illustration fallback when packing-list artwork is missing; see [catalog artwork](../dev/rtd_manual_portal.md#accessory-catalog-artwork-2026-09-15).

RTD [locale navigation](../dev/rtd_locale_navigation.md) consumes only frozen publication
metadata; it does not query live data during a Sphinx build.
Legacy metadata means separate-language identity is unverified, not that its
language content is absent or unpublished; the current manual remains reachable.

Web publication staging now uses [locale-safe identity](../dev/web_locale_publication_identity.md)
and candidate validation. Public build flags and workflow dispatch are unchanged.
Git-only [withdrawal and restoration](../dev/web_publication_withdrawal.md) operate
on an explicit copied publication target; missing input never removes a target.
Withdrawn versions require explicit verified restoration before ordinary retry.

Optional local release artifact preflight:
[Manual operations health report](../dev/manual_operations_health_report.md).
For an explicit read-only network pass over the frozen catalog, see
[HTTP health checks](../dev/manual_operations_online_health.md). No queue or live-table write is performed.
Exact frozen-source/served-asset identity can be checked with the
[Git-only deployment receipt](../dev/rtd_deployment_receipt.md), emitted by the
existing frozen Sphinx portal build. Reads use an internal unique cache probe and
bounded retries for incomplete transport; served source and asset hashes remain
exact. Frozen-source inventory has a separate 768 MiB storage budget; served output and fetched-byte budgets remain 512 MiB. This check performs no link writeback. The aggregate preflight must load `myst_parser,tools.rtd.portal` so it exercises the same knowledge export and deployment receipt callbacks as RTD.

Web profile plus an explicit `--lang` uses the
[frozen language projection](../dev/web_language_projection.md): it keeps the complete
configured-language source bundle and gives `check`, Markdown, and HTML one canonical
single-language RST input. Existing commands are reused. Explicit-language Web
queue builds now [seal and verify release evidence](../dev/web_language_release_evidence.md)
after `check -> md -> html`; workflow dispatch and online-table behavior are unchanged.
Only a new evidence-bound version can claim `single`; do not retrofit sealed releases.
Publication staging preserves optional generated `manual.ir.json` and
`manual_bundle.html` sidecars byte-for-byte alongside Markdown, because the
sealed inventory covers them. Unknown files are not silently copied or ignored
by evidence verification; print artifacts and symlinks remain prohibited.

Frozen Web source storage is bounded separately from served output and network
inventories. The [Git-only release contract](../dev/web_publish_pipeline.md#22-git-only-transaction)
sets the 1 GiB source budget and retains the output, per-file and file-count limits.

RTD renders the frozen Web snapshot with the root-only portal extension:
`python -m sphinx -b html -D extensions=myst_parser,tools.rtd.portal <frozen-web-source> <html-output>`.
The default region is temporarily EU; EU/UK resolve to the same frozen EU
publications. Nested manuals and QR aliases retain their existing rendering.
The manual library exposes only manual navigation; product knowledge,
market/policy notes and product cases use direct knowledge-page links in the same
public RTD project. These pages do not require login.
The consumer-facing feedback channel is the after-sales mailbox
`hello@jackery.com` (a plain `mailto:` entry in the `feedback_channels`
portal setting); GitHub Issues stays the internal/dealer triage board.
Verified single-language pages expose frozen publication context for local
copying; they do not append context, tokens or user identity to channel URLs.
Xia Bing (`Bingboom`) owns feedback and checks local artifacts, HTTP
accessibility and the deployed revision after every publication. First
response within 3 business days; this configuration creates no scheduled
service.
Visit analytics is opt-in through the `analytics_beacon_token` portal setting
(default `""` = off, byte-identical pages); a configured token enables the
cookieless Cloudflare Web Analytics beacon without collecting user identity.
Verified single-language pages also get derived head metadata (title,
description, canonical, hreflang, OG) computed from frozen publication
identity; `site_base_url` in the portal settings is the one origin switch.
Root aliases carry noindex/canonical and, when analytics is on, a short
forward delay so printed/QR entries are countable as alias-path pageviews.
See [RTD manual center](../dev/rtd_manual_portal.md) for scope and rollback.

Product improvement collection opens in a modal dialog from a compact floating
button. It is a separate opt-in form and append-only bot
receiver, not an RTD-hosted backend or the support mailbox. Keep it off until
the Mac receiver and HTTPS path are verified; see [product VOC](../dev/product_voc.md).
The designated local OpenClaw `main` agent handles a separate post-intake
analysis step; model availability does not determine whether a submission was stored.

Web Publish / Read the Docs note:

- `Review Preview Package` uploads the review-preview workspace as a GitHub artifact only
- [`.github/workflows/feishu-build-queue.yml`](../../.github/workflows/feishu-build-queue.yml) owns print Publish only; it no longer builds a Vercel candidate or writes `HTML_link`
- [`.github/workflows/feishu-web-publish-queue.yml`](../../.github/workflows/feishu-web-publish-queue.yml) runs only on the Hello-Docs business plane, consumes `Workflow_action=Web Publish`, pushes frozen sources to the `Hello-Docs/publish:docs/publish/` candidate, rejects any PR diff outside `docs/publish/**`, and opens or updates `publish -> main`; after the merge, [`web-publish-receipt.yml`](../../.github/workflows/web-publish-receipt.yml) verifies the live deployment and writes the deterministic canonical nested RTD page (for example `https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us.html`) to `HTML_link`; the root-level alias (for example `/manual_je1000f_us.html`) stays the countable printed/QR entry layer and is no longer the registered value
- [`.github/workflows/verify-web-deployment.yml`](../../.github/workflows/verify-web-deployment.yml) is the independent daily cross-check, also on the Hello-Docs business plane: [`tools/verify_web_deployment_targets.py`](../../tools/verify_web_deployment_targets.py) runs the full deployment-receipt verification (frozen-source bytes plus the expected `readthedocs-project-slug`) for every target in `docs/publish/publish_manifest.json`, so a wrong-site deployment or later link drift fails the run and opens the `web-deployment-verify` sentinel issue
- An authorized Git-only Web release uses committed source plus `source_manifest.json`, exact-ref `check`/Web MyST/strict Sphinx evidence, real release metadata, and the same assembler against a candidate copied from current `Hello-Docs/main:docs/publish/**`. It creates no queue or online-table writes. Both input paths use the same `docs/publish/**`-only PR and RTD outlet; Git-only completion is proven by commits, hashes, metadata, and real URLs instead of `HTML_link` readback. See [`dev/web_publish_pipeline.md`](../dev/web_publish_pipeline.md#22-git-only-transaction)
- Web Publish verification artifacts expire after 7 days; the generated `publish` branch is the durable candidate and `Hello-Docs/main:docs/publish/**` is the production snapshot. Print Publish artifacts retain their 14-day CI inspection window, and the nightly phase2 backup retains 90 days
- [`.readthedocs.yaml`](../../.readthedocs.yaml) builds `docs/publish/web/` when the frozen Web Publish snapshot exists on `main`. Its review/fixture command is only a bootstrap fallback before the first merged snapshot
- RTD builds from a bare clone with no Feishu credentials. The project listens to `Hello-Docs/main`; it renders the PR-merged MyST source and never runs live `sync-data`
- `review/*` remains a build-input branch. Never merge it into `main`; the only Web release PR is the generated `publish -> main` PR containing only `docs/publish/**`
- full transaction, branch and rollback contracts: [`dev/web_publish_pipeline.md`](../dev/web_publish_pipeline.md)

- After a reviewed live-Base change, approve the Web export rows and dispatch Web Publish with the HT-Docs bot. The worker freezes the exact manifest and attachments in Git before RTD can render them. `tests/fixtures/phase2` remains a CI/bootstrap fixture, not the production intake path
- to add a target to the catalog, prepare its review branch and presentation contract, then Web Publish it. The assembler preserves prior targets and rebuilds the aggregate catalog without another hardcoded `.readthedocs.yaml` command
- Web Publish sets `AUTO_MANUAL_PRESENTATION_PROFILE=web`; print Publish, local document exports and DOCX retain the default `document` profile

- Web Publish runs [`../tools/readthedocs_source.py`](../../tools/readthedocs_source.py) indirectly through the publish-branch assembler, producing one link-only root index, collision-checked root alias pages named from each manual stem, and mirrored image assets under `docs/publish/web/_static/manual-assets/`. Each alias forwards relatively to the nested canonical page so the same frozen source works with or without RTD's `/en/latest` prefix.
- [`../tools/publish_asset_pool.py`](../../tools/publish_asset_pool.py) pools image sources and inline CSS `url(...)` references in the assembled Markdown, including background/mask graphics that have no `<img>` element. Quoted and unquoted local URLs retain their query/fragment suffix; external, absolute and data URLs and logical artwork identity attributes remain unchanged. Its before/after reference fingerprint includes those CSS assets, so deleting a still-referenced native safety glyph fails assembly. Frozen source packages stay unchanged; image-element counts alone cannot establish complete resource loading.
- do not point RTD at the repo-root [`../docs/`](../../docs) tree; `docs/publish/web/` is the frozen Sphinx source, while `docs/publish/sources/web/` retains each target's original MyST bundle
- The manual-center selector includes US/EU/UK/CN/JP with independent CN/JP bindings and `zh`/`ja` labels; only verified frozen language links are enabled. EU remains the default. For the existing whole-book `cn-zh` / `jp-ja` queue families, leave `Lang` blank: their configured language is already fixed, and they do not use language-scoped output paths.
- RTD is the Web Publish presentation surface; it is not the release authority for formal IDML, LaTeX, PDF, DOCX or print Markdown outputs

Manual Center 的 HTML 构建会从已发布手册生成静态章节检索索引，先于部署
回执封存执行；无需单独启动后端。维护入口及检索范围见
[RTD Manual Center](../dev/rtd_manual_portal.md)。

冻结 `publish/web` 的成功 HTML 构建还会导出全部欧规说明书的
`manual-knowledge.json`，并由同轮 `manual-deployment.json` 封存其哈希。
导出按章节保留表格坐标、步骤和警告，去除样式及导航；现有 BlockClaw 插件通过
`manual_search` / `manual_section` 只读查询，引用原文并绑定同一发布快照。
启用配置、更新与撤下行为及图片文字边界见[欧规说明书查询](../dev/eu_manual_query.md)。

同一个构建还会生成 `/workspace/` 个人内容入口，并从 Hello-Docs 的
`docs/knowledge/ai-share/` 读取分享包，复制到
`/ai-share/`。说明书中心与 AI 分享保持为两个独立界面，入口页只负责在两者之间
导航。分享包是可选的：缺失时 `/workspace/` 与系统建设页照常生成，只隐藏分享入口。
系统建设页的「当前工作」标签集中展示任务优先级、完成数量、台账进度和下一步安排，
保留原有 `#tab-progress` 链接。「系统演变」展示历史阶段、变化原因和未排期的长期方向，
另以贯穿全过程的横向路标记录多轮维护与重构，不重复展示当前状态概览与任务进度。
样式组件化起点与随网页手册积累完善的整本 IR 共享分开记录；Web 整本复用已实现，
跨格式共用整本包仍待扩展，审核经验积累独立列项。历史正文及同源 YAML 摘要只维护在
[`architecture/system_evolution_history.md`](../architecture/system_evolution_history.md)，
RTD 构建经来源登记读取，不手改网页。摘要区分已完成、持续开展、建设中和未来方向；
历史数字带日期，页面中的历史叙述与阶段日期统一精确到月；记录更新、数据快照和构建时间保留原有精度。
合入与线上验收分别记录。维护后运行
`python -m tools.rtd.system_workspace check`，详见
[系统建设页契约](../dev/rtd_manual_portal.md#system-workspace-page)。

两个界面共用 RTD 项目的可见性设置，详见
[Personal workspace entry](../dev/rtd_manual_portal.md#personal-workspace-entry)。

同一构建还生成 `/workspace/system/` 系统建设页：状态来自
`tools/rtd_portal_assets/system_workspace.yaml`，数量来自
`docs/publish/publish_manifest.json`，阶段门进度来自执行台账。“当前工作”内的“当前重点”按
配置里的 `focus.lanes` 列出“交付主线 / 同期支撑 / IR 试点 / 稳定后扩展 / 按需后置”，数字取自发布清单、语料快照和
`docs/manifests/skeletons/*/blueprint.yaml`，进度取自各线列出的阶段门或台账行。
“系统架构”标签（`/workspace/system/#tab-architecture`）展示人的入口、AI 能力入口与企业数据入口，围绕同一套可信内容和文档生产体系。现有多维表展示产品信息、内容模块、规格参数、多语言内容及业务维护与评审，经数据校验与快照进入 auto-manual；系统共用多维表、Git 原稿和批准素材，以及 Shared IR（共享底稿）与样式组件，支持文档生产、专业文件处理和内容查询。内容权威、组装、渲染与发布是其中的文档生产链路。MCP 与 PLM／ERP 同步及字段映射接入用虚线及“未来方向”标注；当前 Agent／Bot 单独列出。MCP 仅作为规划中的协议适配层，正式图稿修改保留人工批准。Shared IR（共享底稿）的 Web 整本与样式复用已有基础，机读语料目前仍从已发布 HTML 派生；已有基础按现有文件预翻译、AI 图稿与页码处理、PDF 标注、回写及构建技能列出，钩子标明触发与启用条件。架构视图也读取原有演进史摘要，不另建台账。

修改状态配置后运行 `python -m tools.rtd.system_workspace check`（加 `--online` 可再核对 PR 与链接）。
构建同时生成页面版本回执 `_static/system-workspace-revision.json`。「入口与数据来源」内可展开「页面版本与更新」，页首与演变引言不再显示版本信息及辅助跳转提示。main 经镜像同步、RTD 成功构建后，已打开页面会检测已发布版本并提供刷新入口；提交版本属于 RTD 构建仓库，不能把镜像成功当作线上更新成功。详见 [Published version and refresh](../dev/rtd_manual_portal.md#published-version-and-refresh)。
页内“语言资产”块优先读取 Hello-Docs `docs/knowledge/workspace-data` 汇总快照，工程快照作为迁移基线。
资产批次完成后复用 `python -m tools.rtd.system_workspace corpus-export` 的读取逻辑，通过 Workspace Data Refresh 导出并提交内容 PR；
导出会把往月汇总数带进快照的 `history`，页面据此显示与上期的对比。
柱状图是语料库句对覆盖（各语言有译文的句对占记忆库全部句对的比例），不是说明书翻译完成率，页面在图下写明。
页内“技能与钩子”块在构建时读取 `.agents/skills`、`.claude/skills`、`.claude/settings.json` 与 `.githooks/pre-push`，
按重点线列出技能，标出未登记的技能和没有测试的钩子；`check` 对这些缺口给出警告。
各数据的来源、快照、多少天算过期和取不到时的显示，统一登记在 `tools/rtd_portal_assets/source_registry.yaml`，系统建设页和交付物页都从这里读取，系统建设页底部公开列出“数据来源”表；详见
[Source registry](../dev/rtd_manual_portal.md#source-registry)。
状态配置写错时构建只跳过该页并输出警告，不影响手册站点；详见
[System workspace page](../dev/rtd_manual_portal.md#system-workspace-page)。

同一构建还生成 `/workspace/deliverables/` 说明书工作台：首页提供常用工作入口、生产规模图表、三类资产管理入口与投入/回流简况。“更多工作入口”折叠区保留“结构化数据 + 模板与骨架 → 构建与发布 → 多格式交付物”地图，点击节点可查看业务工作位置、使用指引与下一步。链接配置集中在 `tools/rtd_portal_assets/manual_workbench.html`，业务位置以双平面地图为准；页面只负责导航，不直接执行构建或写入飞书。下方交付物矩阵按型号分组、每个区域一行，汇总网页手册、印刷交付包（IDML + PDF）和 Word 云文档的链接；手机端保留矩阵并横向滚动。网页链接在构建时从发布清单生成；另外两列来自飞书文档构建表的快照 `tools/rtd_portal_assets/deliverables_snapshot.json`，正式交付写回并读回成功后每批自动刷新一次，候选数据通过 Hello-Docs 内容 PR 审核；手动補做统一使用 Workspace Data Refresh。飞书链接需要登录才能打开，但地址在公开页上可见。详见 [Deliverables page](../dev/rtd_manual_portal.md#deliverables-page)。

RTD 构建中的说明书目录与发布证据每轮校验一次，由页面生成及搜索索引复用；
构建结束或失败后清除缓存，下次构建仍重新校验。见
[目录构建校验](../dev/rtd_manual_portal.md#catalog-validation-during-a-build)。
