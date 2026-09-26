# REV-39 公共语义边界发现（迁移计划 P1）草稿

- 台账：REV-39（IR 共享线，状态 planned）。迁移计划：PR #1083 中的 `code-as-doc/dev/manual_ir_production_migration_debt_plan_2026-09.md` §6 P1（该 PR 未合入）。
- 基线：auto-manual `804cede46bf3a9d6e4bc986eff9242ad96aad755`（origin/main）；业务面样本：Hello-Docs `publish@6f0cf82e`（2026-09-25）。
- 状态：草稿，供操作者决定。本稿只读取证，不启动 P2，不改代码、数据、配置或发布。

## 要点

1. 今天只有网页端生产并消费整本 ManualIR v2（`manual-ir/v2`，projection `whole-document-components/v1`）。生产和消费在同一次 `build.py md` 进程里完成；生产代码中没有从 `manual.ir.json` 冷重放的入口（只在测试里做），队列网页发布暂存时还会丢掉这个文件。
2. IDML 有自己的生产者：每次从准备好的 RST bundle 重建 `manual-ir/v1`，读的是 LaTeX 分支。Word 和 PDF 不用 IR：Word 逐页、PDF 经 Sphinx 整本重新解析 RST bundle。
3. v2 包在网页专属处理之后才冻结：只含 html 分支、网页成品图（被图覆盖的标注已删除，文字只留在 img alt）和网页呈现提示。印刷分支里的语义（安全页信号图标、LaTeX 目录、规格 USB-C 拆行）以及 IDML 需要的无字底图与可编辑标注都不在包里。
4. 各端用文件名模式或英文标题识别页面和组件。试点用 slot 文件名（`toc`、`box_contents_ja`、`specifications_ja`、`warranty_ja`），已有几处静默不生效：Word 规格表重建与 Inbox 投影、网页 JP 保修与符号组件（文件名不命中），PDF 日文保修页（只认英法西标题）。
5. 包的来源信息不足：`snapshot_sha256` 为空，`layout_params_sha256` 是常量，ComponentSpec 的 `source_ref` 带绝对构建路径并进入内容哈希，callout 识别词表和网页 CSS 不冻结。
6. 试点 JBP-2000B/JP 目前没有冻结源：没有 review 包、没有 `manual_sources` 快照、没有网页发布；2026-09-05 的网页收口用的是 `tests/fixtures/phase2`。按目前能看到的分支，队列的 review 通道对试点跑不通。
7. JE-1000F/US 的 IDML 批准计划钉的是 `manual-ir/v1` 内容哈希；IDML 改读 v2 包后必然失配，需要正式重绑，属审批事项。
8. 建议试点单元：`troubleshooting_ja` 加 `specifications_ja`（IDML 中是同一组合，第 10 页），再补一页带富文本和素材引用的页面（候选见 §5）。
9. 按四类（语义事实、内容结构、呈现提示、渲染器决策）归类后，今天的包既混进了渲染器决策（成品图替换、标题转大写、LCD 分段），又缺语义事实和内容结构（页面角色、标注指向、封底文案、印刷分支的信号键）；见 §3 表后。

## 1. 范围与方法

- 基线提交：`804cede46bf3a9d6e4bc986eff9242ad96aad755`（origin/main）。计划 §10 记录的核查基线是 `ff5e3556`；本稿按 `804cede4` 重新追踪，不沿用计划中的行号。
- 追踪的输出端（五份只读追踪报告；起草时对关键 path:line 在 worktree 中做了抽查）：
  - 网页：`AUTO_MANUAL_PRESENTATION_PROFILE=web build.py md`、队列 web_publish 通道、Hello-Docs 发布树组装、RTD 渲染。
  - IDML：`build.py idml` 的 production、flow、handoff，以及发布队列的交付 zip。
  - Word：`build.py word` 的 bundle 来源（现有配置都选 `word_source: bundle`）、Draft 队列的飞书导入。
  - PDF：`build.py pdf` 的 `pdf_mode=latex`（Sphinx LaTeX 加 XeLaTeX）。
  - 另有一份 IR 类型盘点：ManualSource、ManualIR、ComponentSpec、组件注册表、主题、PagePlan、发布证据。
- 未追踪：`pdf_mode=word`（DOCX 经 Word 转 PDF）；Windows Word COM 分支只记录存在；普通 HTML（Sphinx html）只作为网页校验产物提到；Hello-Docs 工作流内部。
- 试点：JBP-2000B/JP/ja（`configs/config.bp-jp.yaml`）。回归：JE-1000F/US（`configs/config.us.yaml`，已登记批准版式计划）。
- 方法：沿实际入口读代码、配置、契约和模板，记录 path:line；读 `tests/fixtures/phase2` 了解试点数据形状；用 `git show` 和 `git ls-tree` 读 Hello-Docs 发布树里的已发布包。没有运行任何构建、pandoc、Sphinx、XeLaTeX 或 InDesign，没有读写飞书。worktree 里的 `data/phase2` 只有被跟踪的 `page_registry.csv`，活镜像不在场，依赖活数据的结论标为"未知"。
- 用语：文中"推断"指由几段代码合起来推出、没有运行或目检过的结论；"未知"指要构建或活数据才能判断；追踪报告之间结论不一致处在表中注明"报告分歧"。
- 本稿覆盖 P1 交付物中的输入/输出契约表（§3）、调用路径迁移清单（§4）和试点建议（§5）。P1 另要求"代表性冻结包样例"和"试点差异表"，两者都要实际构建，本稿没有产出。现成可读的样本是已发布的 JBP-2000B/EU/en `manual.ir.json`：15 页、77 个块、19 个素材引用、18 个 ComponentSpec（callout 5 个且 language 都是 `und`，保修 7 个，规格 4 个，Inbox 与故障排除各 1 个），`snapshot_sha256` 为空，`bundle_root` 是 `/private/tmp/...` 下的临时路径。

## 2. 各输出端现有调用链

每端按 源选择 → 解析 → 组装 → 渲染 → 文件输出 列出。bundle 物化与定稿是四端共用的一段，只在 2.1 里详列。

### 2.1 网页

| 阶段 | 职责 | 位置 |
| --- | --- | --- |
| 入口 | `AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md --config configs/config.bp-jp.yaml --model JBP-2000B --region JP [--lang ja]`，经 build_docs 子进程进入 Markdown 导出，再进 `build_word_bundle_html` 的 Web 分支 | `tools/build_dispatch.py:253-262`；`tools/build_entry_commands.py:52-125`；`tools/build_docs_export.py:242-432`；`tools/build_docs_artifacts.py:161-189`；`tools/markdown_bundle.py:166-186`；`tools/word_bundle_html.py:357-554` |
| 入口（队列） | web_publish 通道依次跑 check、md、html，固定 `--source review` 与 web 呈现剖面，然后暂存到 `reports/releases` | `tools/queue_build_execution.py:330-365`；`tools/queue_outputs.py:600-677` |
| 源选择 | 目标来自 family config 与解析后的 BP@JP manifest（13 个 slot，语言 ja）；config 同时指定网页成品图清单和 IDML 候选装配计划 | `configs/config.bp-jp.yaml:14-15,42,54`；`docs/manifests/manual_bp-jp-jbp2000b.yaml:6-73` |
| 源选择 | web 剖面加 `--lang` 时，先物化全语言冻结源再投影成单语 RST bundle；否则走普通 `prepare_manual_bundle` | `tools/build_docs_export.py:54-75` |
| 源选择 | 数据根：`--data-root` 优先，否则 `data/phase2`（gitignore 的活镜像）；auto、review、review-asis 会叠加 `docs/_review/<model>/<region>`，review 与 review-asis 找不到时报错；main 上没有 JBP-2000B/JP 的 review 包 | `tools/data_snapshot.py:350-379`；`tools/build_docs_bundle.py:163-227` |
| 解析 | bundle 物化（四端共用）：模板、CSV 渲染器、draft_v1 配方；RST 替换符与 `{{ copy: }}` 替换、能力段裁剪、语言块裁剪、素材路径改写；slot 页命名为 `slot_id.rst` | `tools/gen_index_bundle_page_render.py:66-298`；`tools/gen_index_bundle_plan.py:53-73` |
| 解析 | CSV 渲染器在同一页里写 LaTeX 分支和 HTML 分支；规格 HTML 分支先建临时 ComponentSpec 再输出 raw HTML | `tools/csv_pages/renderers_troubleshooting.py:103-201`；`tools/csv_pages/renderers_spec.py:43-152` |
| 解析 | bundle 定稿：暂存 phase2 附件，按素材登记表解析 `asset:` 并写 asset_usage 与登记快照，计算 bundle 指纹 | `tools/build_docs_bundle.py:252-296`；`tools/bundle_asset_finalize.py:286-495` |
| 解析 | 每页读一次源字节：`.. only::` 按 `{html, model_*, region_*, lang_*}` 选分支，拆开保修容器，docutils html5（report_level 5，错误不报）；顶级标题只在 `=` 下划线时补回 h1；另做一次 doctree 解析取 operation_panel_copy | `tools/web_document_source.py:231-237`；`tools/word_bundle_html_only.py:14-22`；`tools/word_bundle_html.py:76-127,248-278`；`tools/web_document_source.py:42-76` |
| 组装 | 页面筛选：按 `cover*`、`00_toc*`、`99_back_cover*` 排除（`toc.rst` 不命中，留下）；CSV 页只声明 troubleshooting 与 lcd_icons 两种角色 | `tools/word_bundle_html.py:391-438`；`tools/web_presentation.py:247-279`；`docs/renderers/contracts/web_presentation/shared_base.json:9-16` |
| 组装 | Word-friendly 改写（网页也跑）：信号词表格改成 callout 表并拼 lockup；词表读仓库 `data/phase2`，缺失时读 `tests/fixtures/phase2`；XML 解析失败时原样返回 | `tools/web_document_source.py:237`；`tools/word_bundle_html_rewrite.py:681-696`；`tools/signal_words.py:46-61` |
| 组装 | 冻结前的网页处理：`normalize_web_source_fragment`（前言语言清单删除、自动恢复表与组合键表，JP 都不触发）、text_corrections、按 (语言, 文件名) 换成品图并删除被覆盖的标注（JP：9 张成品图替换 13 张源图，删除 7 处标注） | `tools/web_document_source.py:79-96,211-297`；`tools/web_presentation.py:1351-1383`；`docs/renderers/web/jbp2000b_jp_illustrations.json` |
| 组装 | 组件发现：用 HTML 选择器认领 LCD、故障排除、符号、保修、操作、FCC、Inbox、规格（每个 `h2.hb-spec-section` 一个）、callout；JP 得到故障排除、规格、callout、Inbox；符号、LCD（纯文字表）、保修、总览、操作页保持中立 flow | `tools/manual_ir/whole_document_components.py:121-534`；`docs/renderers/contracts/web_presentation/target_overlays.json:366-377` |
| 组装 | 素材按内容哈希打包到 `assets/ir/<sha256>/`，呈现文件到 `assets/<stem>_<sha12>`；其余 HTML 编成 manual-flow/v2，class、style、`data-*` 存进 presentation 提示；写信封并 `write_manual_ir` | `tools/web_document_source.py:187-205,298-378`；`tools/manual_ir/flow.py:147-252` |
| 渲染 | 同进程重放：在冻结的注册表与主题下校验素材哈希，按 component_id 分发网页 adapter，已规范化的包跳过 `transform_web_fragment`；`stage_fragment_assets` 仍以 docs/ 与仓库根为搜索根 | `tools/word_bundle_html.py:460-469`；`tools/web_document_ir.py:64-178` |
| 渲染 | 渲染后生成 web_figure_coverage，写回 IR 并重写 `manual.ir.json` | `tools/word_bundle_html.py:474-476` |
| 渲染 | 拼 `manual_bundle.html`；Pandoc（myst 或 commonmark_x）转 MyST，受保护的图、callout、行内控件、语言导航先换占位再还原；`--resource-path` 含仓库 docs/ 与仓库根；写 conf.py 与 index.md，CSS 从 `docs/renderers/contracts` 拼接 | `tools/word_bundle_html.py:516-553`；`tools/markdown_bundle.py:194-297`；`tools/web_stylesheets.py:10-38` |
| 渲染（并行） | `html` 动作用 Sphinx 直接渲染 RST bundle，作为封存的校验产物，不经 IR | `tools/build_docs_export.py:334-354` |
| 文件输出 | `docs/_build/JBP-2000B/JP/md/`（不带 `--lang` 时；config 不把语言放进输出路径）：`manual_jbp2000b_jp.md`、`manual.ir.json`、`manual_bundle.html`、`assets/`、conf.py、index.md、`_static/web_manual.css` | `tools/build_docs_artifacts.py:177-185`；`configs/config.bp-jp.yaml:15` |
| 文件输出 | 队列暂存到 `reports/releases/.../web/md` 时只复制 Markdown、assets/、conf.py、index.md；Git-only 组装在文件存在时复制 `manual.ir.json` 与 `manual_bundle.html`，再从存放的 MyST 重建 `docs/publish/web` | `tools/queue_outputs.py:28-44,648-656`；`tools/publish_branch_assembly.py:125-185` |
| 文件输出 | RTD 用 Sphinx、myst_parser、tools.rtd_portal 渲染存放的 MyST，页面语言与方向取自 publish_meta | `hello-docs/publish:.readthedocs.yaml:19-21`；`tools/rtd_portal.py:141-233` |

补充事实：

- 生产代码中 `render_document_fragments` 只有 `tools/word_bundle_html.py:469` 一处调用（同进程）；冷进程重放只在测试里做（`tests/test_web_document_ir.py:526-547`）。
- 下游不读 IR：Pandoc 读 `manual_bundle.html`；`markdown_bundle` 打开 `manual.ir.json` 只为判断 projection（`tools/markdown_bundle.py:210-218`）；RTD 渲染 MyST。
- Hello-Docs `publish@6f0cf82e` 的 54 个网页目标中只有 5 个带 `manual.ir.json`（JBP-2000B/EU/en、JBP-3600A/EU/en、JE-2000E/EU/en、JE-3000C/EU/en、JE-500A/EU/en）；JE-1000F/US 三个语言都没有，JBP-2000B/JP 不在发布树。
- 队列 web_publish 通道对试点跑不通：它固定 `--source review`，找不到 review 包就报错（`tools/build_docs_bundle.py:222-227`）；main 上没有 JBP-2000B/JP 的 review 包，本地远端跟踪引用里也没有 `review/JBP-2000B-JP` 分支（未查询远端实时分支）。

### 2.2 IDML

| 阶段 | 职责 | 位置 |
| --- | --- | --- |
| 入口 | `python build.py idml --config configs/config.bp-jp.yaml --model JBP-2000B --region JP [--idml-mode production/flow/both] [--lang ja]`：先起 build_docs.py 只准备 bundle，再起 `tools/export_idml.py` | `tools/build_dispatch.py:283-348`；`tools/export_idml.py:126-600` |
| 入口（队列） | publish 阶段在 `build.py publish` 之后跑 `build.py idml --no-clean --idml-mode both`（review 或 review-asis），再打交付 zip | `tools/queue_build_execution.py:283-329,503-531`；`tools/idml/delivery.py:234-372` |
| 源选择 | 已登记批准计划的目标默认 review-asis，其余默认 runtime；有批准计划或配置了候选装配计划时只准备 rst，否则先出 LaTeX PDF 供测量回落。试点：runtime 加 rst；JE-1000F/US（config.us.yaml）：review-asis 加 rst | `tools/build_dispatch.py:309-329`；`configs/config.bp-jp.yaml:54`；`docs/renderers/contracts/reference_layout_registry.json:4-21` |
| 源选择 | 页面清单同网页（manifest 13 个 slot）；内容来自 `data/phase2` 活镜像（worktree 里只有 page_registry.csv）；JBP-2000B 的 `manual_sources` 只有 EU/en/2.0 | `docs/manifests/manual_bp-jp-jbp2000b.yaml:6-73`；`.gitignore:38-39`；`manual_sources/JBP-2000B/EU/en/2.0/source_manifest.json` |
| 解析 | 同一套 bundle 物化与定稿（见 2.1） | 同 2.1 |
| 解析 | 对准备好的 bundle 再解析一次，得到 manual-ir/v1：页序取 index.rst 的 include；标签 `{latex, idml, region_*, model_*, category_*}` 加 `lang_<页面语言>`；手写 RST 子集解析器、raw LaTeX 宏解码、数据组件解码；未知 raw LaTeX 丢弃并计入 skipped_raw | `tools/idml/ir_projection.py:471-492`；`tools/manual_ir/prepared_rst.py:124-203`；`tools/idml_rst_extract.py:160-434`；`tools/idml/data_components.py:39-242` |
| 组装 | IR 闸门：`validate_manual_ir`、`same_source_issues`（规格、LCD、符号、TOC、封底载荷必须齐）、`asset_resolution_issues`；任一失败返回 1。TOC 与封底检查按文件名 `00_toc.rst`、`99_back_cover.rst` 触发，试点的 `toc.rst` 不触发 TOC 检查 | `tools/idml/ir_projection.py:441-492`；`tools/export_idml.py:153-171` |
| 组装 | 页面计划优先级：批准计划、配置的候选装配、组件目标、LaTeX PDF 测量。试点用候选装配，按页数、顺序、source_ref、语言、文件名角色核对 IR；内容哈希只记录不校验 | `tools/idml/ir_projection.py:495-535`；`tools/idml/target_assembly_plan.py:1114-1333` |
| 组装 | 把 IR 投影回旧 writer 输入：`project_pages` 压成 (kind, 文本)，data 块只留 operation_panel_copy；`spec_page_data` 等按文件名前缀（含 slot 名别名）取类型化数据；页面角色再从文件名推断 | `tools/idml/ir_projection.py:78-205`；`tools/export_idml.py:173-219` |
| 渲染 | 按源顺序分发组合：候选计划的特殊组合走 shared_page 组合器；封面按命名找成品 PDF；目录、保修、其余正文走主循环 | `tools/export_idml.py:334-531`；`tools/idml/target_assembly_render.py:12-31,196-648` |
| 渲染 | 试点第 10 页：故障排除与规格同页，规格四节合成一组且标题为空，两栏在 246pt 处分开 | `docs/renderers/contracts/target_assembly/jbp2000b_jp_v1_candidate.json:183-215`；`tools/idml/shared_page.py:1103-1169` |
| 渲染 | 收尾：目录按源载荷原样打印页码，页脚页码取 renderer_page_plan；输出页数必须等于计划的 12 页；试点没有封底 | `tools/export_idml.py:544-571`；`tools/idml/ir_projection.py:563-606` |
| 文件输出 | `docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml`（带 `--lang` 时在 `.../JP/ja/idml/`）、`latex_page_plan.json`、`manual.ir.json`（生产渲染不回读；只有 handoff 读它取 skipped_raw 计数，另有计划脚手架与重绑工具读取）、Document fonts/；只做结构自检 | `tools/export_idml.py:572-580`；`tools/idml/ir_sidecar.py:53-65`；`tools/idml/export_paths.py:7-32` |
| 文件输出 | flow 与 both 模式：`flow_md` 用另一套标签再解析 bundle 得到 Markdown，`flow_idml` 再解析这份 Markdown 得到 `manual.flow.idml`；both 还写 handoff 报告 | `tools/export_idml.py:581-591`；`tools/idml/flow_md.py:78-100`；`tools/idml/flow_idml.py:153-179`；`tools/idml/design_handoff.py:35-147` |
| 文件输出 | 发布交付 zip：取最后一个 `manual_*.idml`，链接改写到 Links/，带 flow、报告、参考 PDF、字体；组装代码不引用 `manual.ir.json` | `tools/queue_build_execution.py:503-531`；`tools/idml/delivery.py:234-372` |

补充事实：

- IDML 有 IR，但生产者不同：每次从准备好的 RST bundle 重建 manual-ir/v1。`tools/idml` 不 import 网页的 `web_document_source` 或 `whole_document_components`，两端不共享 IR 实例。
- 拿到 IR 之后渲染仍直接读外部：页面文件（取语言，`tools/idml/page_identity.py:10-19`）、目录模板回落（`tools/idml/ir_projection.py:149-168`）、按命名找封面（`tools/idml/page_placed.py:34-84`）、`data_root/_attachments`（LCD 与符号图标，`tools/idml/ir_projection.py:213-228`）、按基名搜图（`tools/idml/primitives.py:174-189`）、bundle 的 asset_usage 清单（`tools/idml/asset_slots.py:23-30`）、信号词 CSV、仓库里的注册表与主题、layout CSV、计划与总览契约。
- ComponentSpec 只在抽取或渲染时临时建来做校验，不存进 v1。

### 2.3 Word

| 阶段 | 职责 | 位置 |
| --- | --- | --- |
| 入口 | `python build.py word --config configs/config.bp-jp.yaml --model JBP-2000B --region JP`：走默认处理器；`--source` 为 auto 或 review 时先做 review 参数预同步；再起 build_docs.py `--formats word` | `tools/build_dispatch.py:253-262`；`tools/build_runtime.py:152-169`；`tools/build_entry_commands.py:52-124` |
| 入口（队列与发布） | Draft：check、word、md 都用 `--source review`（这里的 md 是 document 剖面，不经 IR）；publish：word 用 review 或 review-asis | `tools/queue_build_execution.py:241-282`；`tools/build_publish.py:86-101` |
| 源选择 | config：`word_source: bundle`、参考文档 `docs/templates/word_template/template.docx`、标题模板；`include_lang_in_output_path: false` 且未传 `--lang` 时 bundle lang 为空；layout_params 只在开头校验，Word 不用 | `configs/config.bp-jp.yaml:15,26-30`；`tools/build_docs_artifacts.py:108-158`；`tools/build_docs_entry.py:47-54` |
| 解析 | 同一套 bundle 物化与定稿（见 2.1） | 同 2.1 |
| 解析 | 逐页读 RST 调 `_convert_rst_fragment_to_html`：同一个 only 选择器（`lang_*` 只在 bundle lang 已设时加入）、docutils html5；`safety_*` 页有 raw HTML 时只取 raw HTML；`spec_*` 页在 document 剖面下重解析并用新建的 ComponentSpec 重画 | `tools/word_bundle_html.py:478-499,281-320` |
| 组装 | Word-friendly 改写（callout 表、lockup）；FCC 与 Inbox 投影只在文件名匹配 `*01_fcc`、`*02_whats_in_the_box` 时触发，契约不带目标加载；图片按页面目录、docs/、仓库根查找并复制到 `word/assets/`；记录页元数据（文件名推断的角色、首段文字） | `tools/word_bundle_html.py:322-354,500-513`；`tools/word_inbox_component.py:31-41` |
| 渲染 | 非 Windows：`pandoc --from=html --to=docx --metadata title= --resource-path <word 目录>:<docs>:<仓库根> --reference-doc`；Windows：Word COM，失败或 zip 无效时回落 pandoc | `tools/word_bundle_docx.py:88-140,228-258` |
| 文件输出 | DOCX 后处理：嵌入外链图片；把 pandoc 样式映射到参考样式（`safety_`、`spec_` 前缀的页保留样式，按首段文字找页边界）；强制大纲级别；可复现归一化。输出 `docs/_build/JBP-2000B/JP/word/manual_jbp2000b_jp.docx` | `tools/word_bundle_docx.py:259-262`；`tools/word_bundle_docx_styles.py:15-50` |
| 文件输出（Draft） | 构建出的 .docx 导入飞书两次：可编辑评审稿（授予编辑权）和冻结基线 `<名称>_基线YYYYMMDD`；回写工具之后对这两份做差异 | `tools/queue_group_processing.py:375-420` |

补充事实：

- Word 不生产也不读 ManualIR。同一文件里的 IR 代码只在 web 剖面运行；Word 调用 `build_word_bundle_html` 时不传剖面（`tools/word_bundle_docx.py:238-244`）。
- 组件语义每次从中间 HTML 重新推出，用完即弃；DOCX 里没有 source_ref。
- 试点的 slot 文件名让几处按文件名触发的 Word 处理静默不生效：规格表重建与 DOCX 规格样式（`specifications_ja.rst` 不以 `spec_` 开头）、Inbox 投影（`box_contents_ja`）、目录角色（`toc.rst` 归为 STANDARD）。JE-1000F/US 用 `spec_en.rst` 等旧名，这些处理会生效。

### 2.4 PDF（LaTeX）

| 阶段 | 职责 | 位置 |
| --- | --- | --- |
| 入口 | `python build.py pdf --config configs/config.bp-jp.yaml --model JBP-2000B --region JP`：走默认处理器（含 review 预同步），build_docs.py `--formats pdf`；pdf_mode 默认 latex | `tools/build_dispatch.py:253-262`；`tools/build_docs_artifacts.py:192-244` |
| 入口（发布与 IDML 回落） | publish 在 word 之后用 `--no-clean` 跑 pdf；没有批准计划也没有候选装配的目标，`build.py idml` 先跑这条链供测量页计划（试点与回归目标都不走） | `tools/build_publish.py:98-101`；`tools/build_dispatch.py:320-329` |
| 源选择 | 同 Word；`--clean` 会删掉整个 `docs/_build/JBP-2000B/JP`；web 剖面加 `--lang` 时 LaTeX 也会吃网页语言投影 bundle | `tools/build_docs_io.py:59-100`；`tools/build_docs_export.py:54-75` |
| 解析 | 同一套 bundle；index.rst 在 LaTeX 分支加隐藏标题并按顺序 include 所有页 | `tools/gen_index_bundle_plan.py:239-268` |
| 解析 | `sphinx-build -b latex <bundle>/rst ... -t model_jbp_2000b -t region_jp -t lang_ja -t category_bp`；不传 language，生成的 conf.py 也不设 | `tools/build_docs_export.py:356-369`；`tools/build_docs_io.py:103-143`；`tools/build_docs_theme.py:16-47`；`tools/gen_index_bundle_materialize.py:125-147` |
| 组装 | doctree-resolved 扩展：一行 notice 表改成 HBCallout（带 ComponentSpec）；两列、第二行首格为 F0 的表改成故障排除组件；保修只认 en、fr、es 标题 | `docs/conf_base.py:15-19`；`docs/renderers/latex/hb_latex_callouts.py:13-28`；`docs/renderers/latex/hb_latex_data_tables.py:70-108`；`docs/renderers/latex/hb_latex_warranty.py:9-14` |
| 渲染 | Sphinx LaTeX writer 出 `manual_demo.tex`；按基名平铺复制图片；`patch_latex_fonts` 注入字体、按 ja 装日文 CJK 字体、在整份 .tex 上替换易碎字符；XeLaTeX 跑 3 遍 | `tools/build_docs_export.py:78-159,370-379`；`tools/patch_latex_fonts.py:29-33,88-100,350-358`；`tools/utils/tex_utils.py:11-18` |
| 文件输出 | `docs/_build/JBP-2000B/JP/pdf/manual_jbp2000b_jp.pdf`；release-manifest 记录 PDF sha256、工具链、快照和素材谱系 | `tools/build_docs_artifacts.py:213-225`；`tools/release_manifest_service.py:213-262` |

补充事实：

- PDF 路径完全不用 ManualIR。ComponentSpec 只在两处临时使用：callout 在 doctree 阶段，规格行在 CSV 渲染阶段；都不持久化。
- 注册表声明的其他 LaTeX adapter 在生产中没有调用者；三个手册表格 adapter（IDML、LaTeX、Word 各一）只在 `tests/test_component_spec_manual_tables.py:193-195` 被调用。

## 3. 输入/输出契约表（草稿）

说明：

- "ManualIR v2 里是否已有"按网页现有的整本包判断（`manual-ir/v2`，`whole-document-components/v1`）。IDML 自己的 v1 IR 不算；IDML 列写的是它今天怎样从 v1 取用。
- 归类按四类（操作者 2026-09-25 的建设思路），一项里有几类时分开写：
  - 语义事实：说明书说了什么，如文字、数值、信号词、语言、素材身份。各端必须一致。
  - 内容结构：内容怎样组织，如页序与页面角色、标题层级、列表、表格、组件、锚点、块身份。各端必须一致。
  - 呈现提示：不改变含义、各端可用可不用的提示，如列宽、class、主题。
  - 渲染器决策：只属于某一端的决定，如物理分页、页码、几何、字体、素材变体、字符的替代写法。
  - 另记“来源信息”：source_ref、哈希、快照，不是说明书内容，是包的身份与出处，随包走。
  - 上一版的“公共语义”等于语义事实加内容结构，“输出端”等于呈现提示加渲染器决策。每项归类是本稿的建议，冻结时逐行确认。
- 表中"报告分歧"指追踪报告对该项是否属输出端结论不同（报告按上一版的两类写）；"未知""未涉及"按报告原样保留。

| 语义项 | 今天的权威来源 | ManualIR v2 里是否已有 | 网页 | IDML | Word | PDF | 归类 | 丢信息风险 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 页面清单、顺序与页面身份 | 解析后的 manifest（13 个 slot，文件名取 `slot_id.rst`）；有 review 包时以其 index.rst 为准 | 部分：`page_id` 与 `source_ref` 都是文件名，metadata 有 `page_slots`、`page_declarations`；无物理页与 page_role | 规划器给语言和 slot；按 `cover*`、`00_toc*`、`99_back_cover*` 排除，`toc.rst` 留下；只声明 troubleshooting、lcd_icons 两种角色 | v1 用 `page-NNNN-<stem>` 与 `page/<文件>`；角色按文件名推断；候选计划按 source_ref 绑定组合；`spec_`、`lcd_icons_`、`symbols_` 有 slot 名别名 | 只留 source_path 与首段文字；DOCX 不带页面身份 | 所有页 include 进单一 docname `index` | 内容结构：逻辑顺序、slot、页面角色；语义事实：页面语言；渲染器决策：物理页 | 各端按文件名模式认角色，slot 改名后静默失效（例：Word 规格与 Inbox、网页保修与符号组件） |
| 条件内容（`.. only::`、能力段、语言块） | 模板与 CSV 渲染器里的 `.. only::`；`data/model_capabilities.csv`；物化时的语言块裁剪 | 无：冻结前已按 `{html, model_*, region_*, lang_*}` 选定；能力段与语言块在物化时删除，包内不记录删了什么 | 标签 `{html, model, region, lang}` | `{latex, idml, region, model, category, lang_<页面语言>}`，语言拼作 jp；flow 模式另一套（无 idml 与 category，用 CLI 语言） | 与网页同一函数；`lang_*` 只在 bundle lang 已设时加入（试点默认不设）；无 `category_*` | Sphinx `-t` 的 model、region、lang、category 加 builder 标签，语言拼作 lang_ja | 语义事实：内容条件（型号、区域、语言、品类、能力）的取舍，在公共组装里一次定下；渲染器决策：输出条件（latex、html、idml）；今天两者共用一种指令（报告分歧：Word 报告记为输出端，PDF 报告记为非输出端） | 四端标签集合不同；现有模板没有 `category_` 与 `lang_` 分支，问题潜伏 |
| 标题层级 | 模板 RST 标题；规格页标题由 CSV 渲染器写成 raw HTML（`h1.hb-h1-pill`、`h2.hb-spec-section`）和 raw TeX；目录标题是 raw TeX | 有（flow heading） | 顶级标题只在 `=` 下划线时补回 h1；Pandoc 去掉 id | 自写解析器按下划线字符定级（`~` 与 `^` 都成 h3），不保留嵌套 | docutils 路径同网页；DOCX 映射 dingding-heading1/2/3 并强制大纲级别 | Sphinx 节；规格与目录标题走 raw TeX，不进 doctree | 内容结构：层级；语义事实：标题文字；渲染器决策：网页把规格节标题转大写（今天已写进包，见规格表行） | 规格节标题：网页转大写，IDML 试点四节合一且标题为空 |
| 正文段落 | 模板正文（物化时已替换）；review 覆盖（试点无） | 有；`.. only:: latex` 内容和未知指令不进包（docutils report_level 5 静默） | flow 段落转 Pandoc 段落 | body 块；不认识的 `..` 行跳过 | pandoc 段落，正文样式清回参考默认 | Sphinx 段落；之后整份 .tex 做字符替换（见"特殊字符"行） | 语义事实：文字；内容结构：段落与顺序 | 网页冻结前删除被图覆盖的标注（JP 7 处，文字只留在 img alt）；美规前言首段语言清单在冻结前删除 |
| 行内富文本（粗体、上下标、链接、带类 span） | RST 行内标记；写成 raw TeX 的 CSV 文本（已转义） | 部分：flow 有 strong、emphasis、sup、sub、link；class、style、data 在 presentation 提示；组件槽位不统一（故障排除、LCD、符号存 `*_html` 与 `*_text`，规格、callout、Inbox 只存纯文本，格式只在 carrier_flow） | 用 carrier 与 HTML 渲染；Pandoc 只保护 sub、sup 与 add-device span，其他带样式 span 被拍平 | v1 存带 RST 标记的字符串，渲染时解析粗体与 :sub:、:sup:；数据组件经 `_text` 解码后粗体、上下标变纯文本（LCD 状态前缀按 `preserve_strong` 保留粗体） | pandoc runs；class 丢失 | Sphinx inline；CSV 驱动的 raw TeX 组件里 RST 标记不解释 | 内容结构：粗体、上下标、链接（上下标改变含义，哪一端都不能丢）；呈现提示：class 与 style（报告分歧：网页报告记为输出端） | 包里只给 `*_text` 时印刷端和 Word 丢格式；给 `*_html` 时非网页端要再解析 HTML |
| 列表 | RST 列表 | 有（flow list、list_item，含 ordered、start） | ul、ol 转 Markdown 列表；callout 另存纯文本 items | 用项目符号字符编码在文本里，嵌套压成两级，不认 `*`、`+` | pandoc 列表；嵌套修复启发式只匹配英文 | itemize、enumerate；callout 内嵌套压平 | 内容结构：有序或无序、起始编号、嵌套层级 | 低；IDML 与 PDF callout 丢嵌套层级 |
| 普通表格（含表头声明） | 模板 list-table（`:header-rows:`、`:widths:`、`:class:`）；符号、LCD 的 CSV 渲染器 | 有（行、格、表头、跨行跨列；列宽作呈现样式）；`:header-rows: 0` 的表头存成普通行 | 未受保护的表经 Pandoc 变 pipe table 或 Pandoc 自己的 HTML | 忽略 `:header-rows:`、`:widths:`、`:class:`；writer 把第 0 行当表头 | DOCX 用 tableHeader 或 TableGrid；声明 0 行表头时 DOCX 没有表头行 | tabulary 或 longtable；部分表按形状改成组件 | 内容结构：行、格、表头、跨行跨列；呈现提示：列宽、表格 class | 表头规则四端不一致（按位置、按声明、按 thead 或首行） |
| 故障排除表（试点章节） | `troubleshooting_blocks.csv`（按 Is_latest、Region、Model 过滤，取 `corrective_measures_jp`，空时逐格回落 en）写入 `docs/templates/page_jp/10_troubleshooting.rst`（`:header-rows: 0`，表头写成数据行） | 有：HB-TABLE-TROUBLESHOOTING（按页面声明认领；表头取首行；行存 code、measures 的 html 与 text） | 按 ComponentSpec 的 `*_html` 直接画表，Pandoc 以 figure 保护 | 不用 ComponentSpec，从通用 IR 表重建（第 0 行作表头）；与规格同放第 10 页 | 普通表，无表头行；注册表 word 绑定为 projection-only，没有投影代码运行 | 两列、第二行首格为 F0、且有 longtable 类或表头含 ERROR 时改成 HBTroubleshootingTable，否则退回普通 longtable，不报警 | 语义事实：代码与处理措施文字；内容结构：组件、行序、表头 | CSV 的 No. 与记录身份在渲染时丢弃；日文格为空时静默用英文；表头只靠位置识别 |
| 规格表（试点章节） | `Spec_Master.csv`（document_key JBP-2000B_JP）加 spec_titles、Spec_Notes、Spec_Footnotes，经 collect_spec_content 在同一页里写 LaTeX 分支（spectable 宏）和 HTML 分支 | 部分：每个 `h2.hb-spec-section` 从 HTML 分支重新抽一个 HB-TABLE-SPEC；标题转大写；多行值拼成带换行的字符串 | 以 carrier 标记渲染，ComponentSpec 只做一致性核对 | 从 LaTeX 宏解码：`_text` 只认一小组宏（①②、`~`、•、换行，粗体与上下标转纯文字），词表外的字母型宏变空白（①② 以外的圈号若以宏出现会变空白），`\_`、`\#` 这类非字母转义原样留下反斜杠；试点四节合一、标题为空 | 只有文件名以 `spec_` 开头才重建 Word 规格表；试点 `specifications_ja.rst` 不触发，网页形态的表直接进 pandoc | raw TeX 直出，规格页前后强制换页 | 语义事实：参数名、值、单位；内容结构：节、行、组件；渲染器决策：网页标题转大写、IDML 四节合一；USB-C 按功率拆行待定（§6 问题 4） | Row_key、Slot_key、记录 id 丢失；USB-C 按功率拆行只在 LaTeX 分支做（试点无此行，回归目标有） |
| 规格脚注与备注 | `Spec_Footnotes.csv`、`Spec_Notes.csv`、Spec_Master 的 `*_footnote_refs`；标记是追加在文字后的圈号字形 | 部分：规格表外的普通段落；note 与 footnote 的区分只在 presentation 提示（`data-spec-trailer-kind`） | 普通段落，靠 class 区分 | 两类都写成 `HBTypeSpecNote`，并入一个平列表 | 普通段落 | 圈号映射到 HBSpecMarker 宏，备注放在表后 | 语义事实：备注与脚注文字；内容结构：note 与 footnote 的区分、标记与脚注的对应；呈现提示：标记的字形 | 标记与脚注只靠字形对应；IDML 与 PDF 丢 note 与 footnote 的区分 |
| 警告与提示框（callout） | 模板里带粗体信号词的两列表（如 `**ご注意**`）；识别词表读仓库 `data/phase2`（缺失时读 `tests/fixtures/phase2`）的 symbols_blocks 与 Localized_Copy，加静态映射，不随 `--data-root` | 有：HB-CALLOUT-STRIP（label、variant、body、items）加 carrier_flow；language 为 `und` | 改写成 manual-callout-table 后认领；渲染时返回 carrier 表 | 旧 notice 结构经 ComponentSpec 校验后丢弃；variant 按打印标签推断 | 改写成 callout 表；DOCX 设宽度与边框 | doctree 阶段识别，选 HBWarningBlock、HBCautionBlock、HBNoteBlock 或 HBTipBlock；language 取 Sphinx 配置（未设） | 语义事实：信号词、级别与正文，识别结果应冻结；内容结构：callout 组件与内含列表；渲染器决策：框样式（报告分歧：网页报告记为输出端） | 识别依赖未冻结、未记录的词表；网页和 Word 的 XML 解析失败时静默不改写；多行标签表不转换。夹具的日文信号词为 警告、ご注意、備考、ヒント、危険，`注意` 能否识别取决于活数据（未知） |
| 安全信号词表与符号说明页 | `01_safety.rst`：带图标和信号键的表只在 `.. only:: latex` 的 raw TeX 里，`not latex` 分支是纯文字表；符号页由 `symbols_blocks.csv` 渲染成两个分支 | 部分：JP 两页都是中立表格（`symbol_meaning_ja` 不命中 `symbols_*`，也没有声明角色）；图标与信号键不在包内 | 中立表格，无图标 | 从 LaTeX 宏解码 symbol_signals 与 symbol_icons；图标在渲染时从 `data_root/_attachments/symbols` 解析 | 纯文字表，无图标 | raw HBSymbol 宏；图片按基名，不经素材登记表 | 语义事实：信号键、图标身份、说明文字；内容结构：表格行；两个手写分支的归属待定（§6 问题 4） | 两个手写分支会漂移；网页和 Word 丢图标 |
| LCD 表 | `lcd_icons_blocks.csv` 等 CSV；主图 `asset:lcd/lcd_map`（JBP 覆盖为 lcd/jbp2000b/screen） | 部分：JP 为 lcd-text-only 表，不生成 HB-TABLE-LCD-ICON；主图被网页成品图替换 | 中立表加成品图 | 行号改写成圈号；与操作页同放第 6 页 | `not latex` 分支的表 | raw HBLcdIconTable，CSV 渲染时已按换页分段 | 语义事实：图标身份与含义文字；内容结构：行与编号；渲染器决策：编号样式、按换页分段（分段今天写进了共享 bundle） | 分页决定写进了共享 bundle；IDML 图标读活数据根 |
| 包装清单（Inbox） | `02_whats_in_the_box.rst`（3 张登记素材图、粗体名称、`注意` 表与 ※） | 有：HB-SPECIAL-INBOX（按 `box_contents_*` 语义模式认领） | 组件渲染，用登记表的单品图 | 与产品总览同一组合（第 5 页，带总览实例几何） | 只认 `*02_whats_in_the_box`，试点不命中，保留为图片表 | 普通表格 | 语义事实：品名与注意文字；内容结构：卡片组件；渲染器决策：IDML 与总览同组合 | 卡片名称是拍平的文本；Word 丢卡片结构 |
| 保修页 | `11_warranty.rst`（warranty-lead 容器、warranty-section 类、编号列表） | 部分：JP 为中立 flow（`*11_warranty` 不命中 `warranty_ja`，JP overlay 没有覆盖；EU overlay 另加了 `warranty_en`） | 中立段落 | semantic 块转成保修组件；块内素材不计入 asset_refs | 容器在解析前拆掉，class 丢失 | 只认 WARRANTY、GARANTIE、GARANTÍA 标题，`保証について` 按普通节渲染 | 语义事实：保修文字；内容结构：保修组件、节与编号列表 | 三套识别规则各自为政；JP 在网页和 PDF 都没组件化 |
| 插图与素材变体 | `.. image:: asset:<key>` 经 `data/asset_registry.csv` 在定稿时解析（写 asset_usage 与登记快照）；phase2 附件；网页成品图清单 `docs/renderers/web/jbp2000b_jp_illustrations.json`（9 张 PDF 裁切带字图） | 部分：只有网页变体（成品图替换源图，被替换的次要源图删除，被覆盖的标注删入 alt），按内容哈希打包；没有登记键、scope、locale 策略、登记快照 | 成品图，重放时校验哈希 | 按 bundle 内路径或基名查找；需要无字底图加可编辑标注 | 不读 asset_usage，重新在页面目录、docs/、仓库根下查找；找不到时原样保留，不报错 | 登记解析不指定格式，按 png、jpg、jpeg、svg、pdf 取第一个存在的，所以嵌入 PNG；raw TeX 里的图不经登记表 | 语义事实：素材身份（登记键）与角色；渲染器决策：变体选择（网页成品图、IDML 无字底图、文件格式）（报告分歧：网页、PDF 报告记为输出端，IDML、Word 报告记为非输出端） | 从现包无法重建 IDML 所需的无字图与活标注；被覆盖的标注文字只剩 alt |
| 插图尺寸与图内标注几何 | RST `:width:`；候选装配的 composition_data（image_role、figure_callouts 相对坐标）；`overview_component_instances.json` | 无（宽度只作呈现样式） | 宽度样式，渲染后读图补宽高；JP 为 `figures:false`，不用图几何 | 组合器读计划与契约 | 宽度转属性 | px 宽度 | 语义事实：标注文字；内容结构：标注指向哪个部件；呈现提示：宽度；渲染器决策：标注坐标与图内几何 | 标注锚点带语义（哪条文字指哪个部件），目前只在 IDML 契约里 |
| 封面 | manifest `cover_pdf asset:page/cover`，覆盖行 page/jbp2000b_jp/cover（有 PDF 和 PNG 导出） | 无（`cover*` 被网页排除） | 不出 | 不用 IR 素材，按命名找 `cover_jbp2000b-ja.pdf`，缺时回落 `-en` | HTML 分支只有标题文字，封面图不进 DOCX；DOCX 标题元数据为空 | `\includepdf` 放置 | 语义事实：封面素材身份；渲染器决策：放置（报告分歧：Word 报告记为非输出端） | IDML 在语言缺失时静默用英文封面 |
| 封底文案（只涉及回归目标） | IR 封底载荷、批准计划的 `idml_contract.back_cover`、代码里的区域 profile；试点没有封底 | 无（`99_back_cover*` 被网页排除） | 不出 | 计划里的地址、电话、联系行覆盖源文案 | 报告未涉及 | 报告未涉及 | 语义事实：地址、电话、联系行（今天住在几何契约和代码里） | 回归比较时文案来源不一致 |
| 目录与页码 | `00_toc.rst`：LaTeX 分支的 HBToc 宏与 `not latex` 分支的列表表，两处都手写页码 | 部分：`toc.rst` 不被排除，HTML 分支的列表表作为普通内容进包（推断，未目检网页）；LaTeX 目录载荷不在包内 | 实际导航是 Furo 侧栏与 index.md toctree；印刷页码可能出现在网页上（未目检） | 按源载荷原样打印页码，页脚页码取页计划；试点第 2 页单栏 | 渲染列表表，不生成目录域；`toc.rst` 归为 STANDARD | HBToc 宏；页码是字面值，不是 pageref | 内容结构：条目与顺序；渲染器决策：页码 | 两份手写副本会漂移；页码与实际分页不绑定 |
| 锚点与交叉引用 | docutils 节 id；RST 标签和 `:ref:`（试点模板里没有） | 部分：flow 有 anchor 字段 | Pandoc 写出时去掉 id，MyST 重新生成 | 标签跳过，`:ref:` 原样留字，不生成超链接 | 每页单独发布，id 在各页重复；页边界靠首段文字匹配 | 在单一 doctree 内解析；书签存在但没有引用 | 内容结构：锚点与引用关系 | 没有稳定锚点；页首文字变化会让 Word 页样式匹配静默失效 |
| 语言标识 | config `build.languages [ja]`、manifest 页 lang、`data/model_languages.csv`；每页前置 raw `\HBApplyLang{ja}` | 有：页 language 为 `ja`，metadata 有 declared_languages；callout 组件为 `und` | `<html lang>` 过不了 Pandoc；RTD 从 publish_meta 取语言 | 从页面文件的 `\HBApplyLang` 读出并归一成 `jp`；候选计划也写 `jp` | `<html lang>` 取 bundle 语言或唯一的配置语言；页面语言可从路径推断 | `-t lang_ja`；Sphinx language 未设；日文字体按 ja 安装 | 语义事实 | `ja` 与 `jp` 两种写法；语言靠 TeX 宏正则和路径推断 |
| 产品名与参数值 | Spec_Master 占位与配方 field_map（row_key、value_role）；config `rst_substitutions`（如 BP_HOST_PRODUCT_NAME）；conf_base 替换；Localized_Copy 的 `{{ copy: }}` | 部分：只有替换后的文字 | 只见文字 | 只见文字 | 只见文字 | 只见文字 | 语义事实：值；来源信息：参数键与记录来源 | 参数键与记录来源丢失，追溯和回写只能靠文字匹配 |
| 特殊字符（⎓、※、₄） | CSV 值与模板原文（试点夹具的规格值含 ⎓，同梱品页含 ※） | 有（保存原字符） | 原字符 | 报告未涉及 | 报告未涉及 | `patch_latex_fonts` 在整份 .tex 上把 ⎓ 换成 `" DC "`、※ 换成 `"*"`、₄ 换成 `\textsubscript{4}` | 语义事实：字符；渲染器决策：替代写法（要记录） | PDF 读者看到的文字与源不同，且没有任何清单记录 |
| source_ref 与块身份 | 物化后的文件名（`slot_id.rst`）与绝对 bundle 路径；IR 构建器分配块 id | 部分：页级 source_ref 是文件名；块级是 `<文件>#block-N`（按位置）；ComponentSpec 的 source_ref 是 `<绝对路径>#<种类>-N`，并进入块哈希 | 重放时用 source_path 推断 figure 契约目标、查找残留素材 | v1 用 `page/<文件>#block-N`；IDML 对象用 writer id，没有到源的映射 | 不带；临时 ComponentSpec 用 `word:spec:*`、`word:html:*` | callout 的 source_ref 是 `index:<行号>`，不唯一 | 内容结构：块身份；来源信息：source_ref | 同一内容在不同构建根下哈希不同（已发布 JBP-2000B/EU/en 包里是 `/private/tmp/...`）；插入一块后后面的位置 id 全部移位 |
| 来源与哈希 | sync-data 的 snapshot_manifest.json、bundle_manifest.json、定稿指纹、release manifest | 部分：页 source_sha256；bundle_sha256 是页哈希的哈希（与 bundle_manifest 里的不是一个值）；snapshot_sha256 为空；layout_params_sha256 是常量 `f5ae099a…`；metadata 不进 content_sha256；渲染后写回 web_figure_coverage | 重放时校验素材哈希；发布收据封存 RST 闭包和 md、html 清单，不含 IR | v1 有真实的快照、layout、样式哈希；批准计划按内容、样式、layout 绑定；候选计划只记录不校验 | 不读；DOCX 不带哈希 | 不读；release-manifest 记录 PDF sha256 和素材谱系 | 来源信息（包信封） | 数据快照、登记快照、CSS、pandoc、Sphinx、MyST 版本都不在包里 |
| 组件注册表、主题与网页呈现契约 | `docs/renderers/contracts/component_registry.yaml`（16 个组件）、`manual_theme.yaml`、`web_manual.json` 与 `web_presentation/*.json` | 有：注册表、主题连同 sha256 冻结，读取时复核；web_contract 冻结，其哈希记为 style_contract_sha256，读取时只查格式不复核 | 重放在冻结的注册表与主题上下文里分发组件 | 渲染时读仓库里的注册表与主题（ComponentSpec 只作校验） | 渲染时读仓库里的注册表、主题和不带目标的网页契约 | LaTeX 扩展 import 仓库里的 tools | 内容结构：组件注册表（定义有哪些组件）；呈现提示：主题；渲染器决策：web_contract（报告分歧：网页报告整项记为输出端） | 注册表中 word 只有 3 个组件是 rendered，其余 13 个是 projection-only；注册表写 rendered 不等于生产路径消费包；网页 CSS 不冻结 |
| 页面计划与几何 | PagePlan（`tools/page_plan`）；IDML 候选装配（12 页，candidate，production_eligible false）；`data/layout_params.csv` 加 idml-compact 叠加；离线生成的 `params.tex` | 无（没有 PagePlan，layout 哈希是常量） | 不适用 | 计划绑定 IR 的页数、顺序、source_ref、语言、文件名角色；输出页数必须是 12 | 页角色从文件名算出后没人读；两份参考 docx 都没有页眉页脚部件 | TeX 流加硬换页；不读 PagePlan，不用 IDML 叠加参数 | 渲染器决策（逻辑顺序见第一行） | 试点 IDML 把故障排除和规格排在同一页，LaTeX 让规格单独成页；两端分页各自推导，本来就会不同 |
| 字体、参考 docx 与样式 | `docs/renderers/latex/fonts.tex`、`HBManualSansJP-Regular.ttf`、环境变量 `AUTO_MANUAL_LOCAL_GILROY_DIR`；Word 参考 docx；IDML 字体供给 | 无 | `web_manual.css`（md 时和 RTD 组装时各从仓库拼一次） | provision_document_fonts；交付 zip 带字体 | `template.docx`（试点）、`reference_en.docx`（回归）；样式 id 与字号写死在 Python | 复制仓库 fonts.tex，按 ja 装 CJK 字体，可选本机 Gilroy | 渲染器决策 | 依赖主机和环境变量，不在 bundle 哈希里 |
| 只在印刷分支出现的内容 | `.. only:: latex` 的 raw TeX：目录宏、安全页信号行（图标与 variant）、规格 spectable、LCD 表 | 无（docutils 之前被 html 分支选择器丢掉） | 看不到 | 数据组件主要从这里解码 | 看不到 | 直接渲染 | 待定（§6 问题 4）：报告没有统一结论，Word 报告把它列为需操作者决定的问题 | 共享包只取 html 分支则印刷端缺语义；只取 latex 分支则缺网页专用文案 |

进包规则（建议，冻结时确认）：语义事实和内容结构必须在共享包里，各端读同一份；呈现提示可以随包走，但哪一端都不能靠它判断含义；渲染器决策不进共享包，放在各端 adapter、PagePlan 或 target assembly 里。不为了统一把所有东西塞进 IR。

按这条规则，上表里今天的包有两类偏差：

1. 渲染器决策已写进共享包或共享 bundle：网页成品图替换与被覆盖标注删除（正文段落、插图与素材变体两行）、规格节标题转大写（规格表行）、LCD 按换页分段（LCD 行）、渲染后写回的 `web_figure_coverage`（来源与哈希行，§6 问题 11）。
2. 语义事实或内容结构不在包里，或各端各自重新推导：页面角色（第一行，各端只好按文件名或英文标题猜，所以 slot 改名后静默失效）；条件内容删了什么（条件内容行）；note 与 footnote 的区分只在呈现提示里（规格脚注行）；标注文字指向哪个部件只在 IDML 契约里（插图尺寸行）；封底文案在几何契约和代码里（封底文案行）；callout 的识别结果网页冻结了，但识别词表没有冻结，Word、IDML、PDF 还各自重新识别（callout 行）；印刷分支里的信号键、图标和目录条目（安全页、目录、只在印刷分支三行，待 §6 问题 4）。

## 4. 调用路径迁移清单

### 4.0 共同前提

- 公共组装要放在输出专属处理之前（计划 §5、P2）。今天唯一的整本生产者 `load_web_document`（`tools/web_document_source.py:98-378`）排在网页处理之后：成品图替换、覆盖标注删除、Word-friendly 改写都发生在冻结前。切换前要先定公共组装从哪一层取内容（§6 问题 3），并把网页专属处理挪进网页 adapter。
- 迁移目标上的旧入口改为明确失败并用禁源测试覆盖；非迁移目标保持原路径。计划 P2 要求遇到不支持的内容明确失败，不静默回退旧解析器。
- 冻结包要带上今天在渲染时才读的外部输入：callout 识别词表、网页 CSS、素材变体与角色、页面计划的绑定键；做不到的要登记为 adapter 固定依赖并记录版本。
- 复用现有 PagePlan 与 target assembly，不另建 planner（P1 退出条件）。

### 4.1 网页

- 当前入口：`build.py md`（web 剖面）进入 `build_word_bundle_html` 的 Web 分支，生产与消费在同一进程（`tools/word_bundle_html.py:441-476`）。
- 切换点：把生产 `load_web_document`（`tools/web_document_source.py:98-378`）与消费 `render_document_fragments`（`tools/web_document_ir.py:162-178`）拆开。消费侧改为 `render_document_fragments(read_manual_ir(<包>/manual.ir.json), package_root=<包>)`，Web 分支只接收包路径。
- 迁移目标上停用（消费进程内不再运行）：`_publish_rst_fragment_to_html`、`_extract_raw_html_blocks`、`_rewrite_word_friendly_fragment`、`normalize_web_source_fragment`、`operation_panel_copy`、`discover_registered_components`。这些是源侧函数，归入公共组装或被公共组装取代。`_convert_rst_fragment_to_html` 的 web 剖面分支（`tools/word_bundle_html.py:281-354`）已不在整本路径上，其他调用者在 P6 登记。
- 同时处理：`stage_fragment_assets` 的 docs/ 与仓库根搜索根（`tools/web_document_ir.py:158`）和 Pandoc 的 `--resource-path`（`tools/markdown_bundle.py:194-200`）限制到包内；CSS 冻结或登记为 adapter 依赖；`html` 校验动作（Sphinx 渲染 RST）是否改为从包生成，需要决定；队列暂存保留 `manual.ir.json`（`tools/queue_outputs.py:28-44`）。

### 4.2 IDML

- 当前入口：`build.py idml` 先跑 build_docs `--prepare-only`（rst），再跑 `tools/export_idml.py`，后者在 `tools/export_idml.py:153-171` 调 `build_same_source_ir`。
- 切换点：`tools/export_idml.py:153-171`。改为读冻结包（manual-ir/v2 flow 与 ComponentSpec），在 IDML adapter 里转成现有组合器的输入（SpecPageData、TroublePageData、LCD 与符号行等，今天由 `tools/idml/ir_projection.py:78-438` 从 v1 生成）。页面计划的绑定键（候选计划写 `page/<文件>.rst` 与 `jp`）要和包里的页身份（文件名与 `ja`）对上。
- 迁移目标上停用：`load_prepared_rst_source`（`tools/manual_ir/prepared_rst.py:124-203`）、`idml_rst_extract.extract_page` 及 LaTeX 宏解码、`data_components` 的 `_text` 与数据组件解码；渲染期直接读源的点：`page_identity.page_language`（读页面文件）、`toc_page_data` 的文件回落、`_asset_path` 回落到数据根附件、`primitives` 按基名搜图、`asset_slots` 读 asset_usage、`page_placed` 按命名找封面、信号词表默认路径。
- 同时处理：flow 模式（`flow_md` 再解析 bundle，`flow_idml` 再解析 Markdown）是否继续独立存在；JE-1000F/US 的批准计划钉 `manual-ir/v1` 与内容哈希（`docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json:838-853`），换成 v2 包必然失配，需要正式重绑，属操作者审批；IDML 验收要在 InDesign 中实际打开（REV-40 依赖 REV-20）。

### 4.3 Word

- 当前入口：`build.py word` 经 `build_word_artifact` 调 `export_word_from_bundle`（`tools/word_bundle_docx.py:228-263`），再进 `build_word_bundle_html` 的 document 分支逐页读 RST（`tools/word_bundle_html.py:478-499`）。
- 切换点：`tools/word_bundle_html.py:478-499` 的逐页循环。改为 Word adapter 从包的 flow 与 ComponentSpec 生成 Word 友好 HTML（或直接生成 DOCX）。DOCX 后处理里按文件名前缀和首段文字定位页面的逻辑（`tools/word_bundle_docx_styles.py:26,32` 等）改为读包里的页面角色与组件身份。
- 迁移目标上停用：`_convert_rst_fragment_to_html` 的 document 分支、`_publish_rst_fragment_to_html`、`_extract_spec_word_data` 与 `render_spec_word_html` 的重解析、`_rewrite_word_friendly_fragment` 的 callout 识别、`transform_word_fcc_html`、`transform_word_inbox_html`、以 docs/ 和仓库根为搜索根的图片查找。
- 同时处理：Draft 的飞书导入与回写依赖 DOCX 结构（两次导入后做渲染对渲染的差异，`tools/queue_group_processing.py:375-420`），DOCX 结构一变就影响回写；`word_source: html` 与 `word_source: latex` 两种模式没有配置在用，P4 要定支持范围；Windows Word COM 分支的输出与 pandoc 不同。

### 4.4 PDF（LaTeX）与普通 HTML

- 当前入口：`build.py pdf` 进入 `ensure_latex`（`tools/build_docs_export.py:356-380`），Sphinx 以 bundle 目录为源。普通 HTML 同样由 `ensure_html` 以 bundle 为源（`tools/build_docs_export.py:334-354`）。
- 切换点：`ensure_latex` 与 `ensure_html` 的 `src_dir=bundle.bundle_dir`。改为由 LaTeX/HTML adapter 从包生成的临时 RST、doctree 或 TeX（计划 §5 允许这类载体）。
- 迁移目标上停用：Sphinx 对原 bundle 的解析；CSV 渲染器的 LaTeX 分支（规格、LCD、符号）和模板里的手写 LaTeX 分支（目录、安全页信号表），改为 adapter 模板读包里的语义；doctree 启发式（`hb_latex_callouts` 的标签识别、`hb_latex_data_tables._classify_table`、`hb_latex_warranty` 的英法西标题匹配）改为按 ComponentSpec 分发；`_copy_attachment_images_for_latex` 的基名平铺复制改为取包内素材。
- 同时处理：`patch_latex_fonts` 的字符替换是在 PDF 端改写读者可见文字，应在 adapter 中声明并记录；Sphinx 的 `language` 未设；P5 要等公共契约稳定后再启动。

## 5. 试点章节与回归目标

### 5.1 试点目标现状（JBP-2000B/JP/ja）

- 配置：`configs/config.bp-jp.yaml`（语言 ja；输出路径不带语言；`word_source: bundle`；网页成品图清单；IDML 候选装配计划）。manifest 13 个 slot（`docs/manifests/manual_bp-jp-jbp2000b.yaml:6-73`）。
- 冻结源：在 `804cede4` 和本地远端跟踪引用中核对（未查询远端实时分支）：没有 `docs/_review/JBP-2000B/JP`；`manual_sources/JBP-2000B` 下只有 EU/en；未见 `review/JBP-2000B-JP` 分支；Hello-Docs `publish@6f0cf82e` 没有 JBP-2000B/JP 网页。2026-09-05 的网页收口用的是 `tests/fixtures/phase2`（`code-as-doc/dev/ir_document_closeout.md`）。
- 已有网页 IR：收口记录的本地构建为 12 个源页（13 个 slot 去掉封面）、19 张图片、9 组 PDF 带字整图。该包不在发布树，之后生产者又改过（v2 flow、嵌入组件），不能当现行基线。
- IDML：候选装配 12 页，candidate，production_eligible false；参考 PDF 为 HTP017 日规 V2.0（sha256 `f7830bf9…`）。

### 5.2 建议试点章节

主单元：`troubleshooting_ja` 加 `specifications_ja`。理由：

1. 计划 P1 优先故障排除或规格表。
2. IDML 候选计划把这两页排进同一组合 `jp_troubleshooting_specifications`（第 10 页），IDML 端不能只取其一，两页一起才是一个能在 InDesign 里验收的单元。
3. 两页都由 CSV 驱动，都是日文：故障排除的日文在本地化列 `corrective_measures_jp`（夹具中 en 列为空），规格的日文在 Spec_Master 源列 `Value_source`（这些行的 Source_lang 就是 ja）。这里按"非英文"理解"非源语言文本"；如要求"本地化列"意义上的非源语言，只有故障排除满足。
4. 网页 v2 已有 HB-TABLE-TROUBLESHOOTING 与 HB-TABLE-SPEC，IDML、PDF 各有对应组合或组件，差异能按页、按行逐项定位。
5. 不涉及总览几何。

夹具数据形状（`tests/fixtures/phase2`）：

- 故障排除：JBP-2000B/JP 13 行（F0 到 F9、FA、FC、FF），日文列全有、en 列为空，都是单行（`tests/fixtures/phase2/troubleshooting_blocks.csv:149-161`）。
- 规格：4 节 11 行（`tests/fixtures/phase2/Spec_Master.csv:427-437`），1 个多行值（保存温度），2 个值含 ⎓；Spec_Notes 2 条（`認証：UN38.3` 与专用说明），Spec_Footnotes 0 条。

这个单元会暴露的差异（见 §3）：表头规则（`:header-rows: 0`）；PDF 故障排除组件依赖首行为 F0（夹具满足）；规格节标题（网页转大写、IDML 合并置空、PDF 保留）；note 与 footnote 的区分；⎓ 在 PDF 被改成 " DC "；Word 规格表重建因文件名不触发；IDML 从 LaTeX 宏解码规格（夹具没有③以上标记，不会触发该损失）；源 No. 与 Row_key 不在包内。故障排除"日文格为空时回落英文"的路径在夹具里不会走到，要验证需另造用例。

缺口：按夹具数据，这两页没有行内富文本，也没有素材引用；P1 要求覆盖富文本和一处素材引用。补充页候选：

- A. `connections_ja`（IDML 自成组合 `jp_connections`，第 7 到 8 页，composition_data 只有 layout_variant 与 image_role）：正文含参数替换（BP_HOST_PRODUCT_NAME），两个 `**ご注意**` callout（粗体标签加列表），5 张登记素材图。网页把它们换成 3 张成品图：clearance、stacking 不删标注；locking 合并 3 张源图并删掉 2 处标注（"ロック""ロック解除"）。能直接检验计划 §5 的"同一素材角色、各端不同冻结变体、不删公共文字"。代价是两个物理页、多张图。
- B. `symbol_meaning_ja`（IDML 自成组合 `jp_symbols_icons`，第 4 页，无 composition_data）：CSV 驱动的表格加 phase2 图标附件。网页目前是中立表格，IDML 图标读活数据根。规模最小，但网页端先要决定是否组件化（§6 问题 14），富文本情况未知。
- C. `box_contents_ja`（3 张登记图、粗体、`注意` 表与 ※）：IDML 把它和产品总览排在同一组合（第 5 页，带总览实例几何），与计划"不从复杂总览几何开始"冲突，不建议作首个单元。

建议：主单元加 A；如需压缩范围改用 B。由操作者定（§6 问题 9）。

### 5.3 回归目标 JE-1000F/US

- 输入：`configs/config.us.yaml`；已登记批准计划（en、fr、es，`docs/renderers/contracts/reference_layout_registry.json:4-21`），IDML 用 review-asis、只准备 rst（`tools/build_dispatch.py:309-324`）；批准计划钉 `manual-ir/v1` 内容哈希及样式、layout 哈希（`je1000f_us_v2_20260605.json:838-853`）。
- review 包：`docs/_review/JE-1000F/US`。manifest 生成于 2026-08-14（git_sha `938f9051`），其中 Spec_Master 路径是 Hello-Docs CI 临时路径，最近一次参数同步在 2026-09-23（`docs/_review/JE-1000F/US/manifest.json:2-3,98-104`）。
- 已发布网页：v2.5（en、es、fr），git_ref `review/JE-1000F-US`，2026-09-24 构建；发布包没有 `manual.ir.json`。
- 与试点不同的行为：前言语言清单删除、自动恢复表与组合键表规范化、operation_panel_copy、已批准 composite、figure coverage 强制；页面用旧名（`spec_en.rst`、`troubleshooting_en.rst`），Word 规格路径会生效；bundle 里 en、fr、es 三语同书。
- 注意事项：被跟踪的 `docs/_build/JE-1000F/US/rst/index.rst:27` 仍写 `page/10_troubleshooting.rst`，与 review 包的 `page/troubleshooting_en.rst`（`docs/_review/JE-1000F/US/index.rst:37`）不一致，构建会原地改写这些被跟踪文件；`--source auto` 的 word 与 pdf 会先做 review 参数预同步并改写 `docs/_review`；不带 `--skip-root-index` 会改写 `docs/index.rst`。回归产物应放在独立目录。
- 比较方法（草案）：每种格式对照自身的冻结基线（计划 §7），不做跨格式一致；网页先证明 review-asis 重建与已发布 v2.5 MyST 等价，再以此为基线。

## 6. 待操作者决定的问题

A. 启动 P2 之前要定：

1. 试点冻结源：沿用 `tests/fixtures/phase2`（快照清单生成于 2026-05-31），还是新建 `manual_sources/JBP-2000B/JP` 快照？没有冻结源时，队列 review 通道对试点跑不通。
2. 回归基线：JE-1000F/US 用基线提交上的 review-asis 输入重建，还是以已发布 v2.5 MyST 为准？已发布包没有 IR。
3. 公共组装的位置：在 `.. only::` 分支解析之前、直接从 CSV 与配方数据组装，还是同时保留两个分支？今天网页冻结 html 分支，IDML 解码 latex 分支，两个分支内容不完全相同（USB-C 拆行、安全页图标、目录宏）。
4. 只在 LaTeX 分支的内容（安全页信号键与图标、LaTeX 目录、USB-C 按功率拆行、封面图、目录页码）算语义事实或内容结构（进共享包），还是渲染器决策（留在 LaTeX adapter）？
5. 素材变体：公共包是否必须同时带网页成品图和 IDML 无字底图，并保留被网页覆盖的标注原结构？JP 有 7 处，其中总览的 2 处是 Spec_Master 标签。计划 §5 倾向保留完整文字与素材角色。
6. source_ref 是否相对化？绝对路径进入块哈希，改动会改变所有现有 v2 包的哈希，计划 §5 要求写明兼容办法。账本 IR-D05 的"verified(Web)：稳定 source_ref"要按此复核。
7. 包里的语言标识用 `ja` 还是 `jp`？归一放在包里还是 adapter？
8. 冻结包的边界：沿用 md 目录（MyST、素材、IR），还是新的产物？队列网页发布是否保留 `manual.ir.json` 与 `manual_bundle.html`？
9. 试点补充素材页选 A（`connections_ja`）还是 B（`symbol_meaning_ja`）？

B. 可在 P2 期间定：

10. callout 识别词表、网页 CSS、注册表与主题怎么冻结：放进包里，还是登记为 adapter 固定依赖并记录版本？
11. `web_figure_coverage`（渲染后写回 IR）留在网页元数据里，还是移出共享包？
12. 表头规则：`:header-rows: 0` 的日文故障排除表，公共语义按声明还是按位置取表头？
13. 是否需要行级来源（飞书 record_id、Row_key、Slot_key、故障排除 No.）进 ComponentSpec？目前没有消费者要求。
14. JP 的符号页、保修页是否组件化？会改变现有网页输出，需要另行授权。
15. 重放是否固定并记录 pandoc、Sphinx、MyST 版本？今天 pandoc 版本不记录，`requirements.lock` 固定了 Sphinx 8.2.3、myst-parser 4.0.1、docutils 0.21.2。
16. JP 网页出现印刷目录页码（推断）是否可以接受？需要一次目检确认。

C. 后续阶段（P4、P5）：

17. Word 迁移范围：只迁 `word_source: bundle`？Windows Word COM 分支是否保留？DOCX 结构变化对飞书回写的影响怎么验收？
18. PDF 的字符替换（⎓ 换 " DC " 等）保留为 adapter 行为，还是改字体方案？

需要构建或活数据才能回答的未知项：

- docutils 的标题提升、report_level 5 静默、ElementTree 解析回落，是否让试点丢了内容；
- 活数据中的 `注意`、`説明` 等标签能否被识别为 callout；
- 活数据中试点故障排除是否以 F0 开头、日文列是否填满；
- pandoc 是否把 `manual-page-break` 转成 DOCX 分页、是否写入语言；
- Sphinx language 默认 en 对日文 PDF 的实际影响。

## 修订记录

| 日期 | 内容 |
| --- | --- |
| 2026-09-25 | 初稿。基线 `804cede4`，只读追踪四个输出端与 IR 类型，未运行构建。 |
| 2026-09-25 | 核对：25 条关键说法交独立 agent 对照代码复核，24 条确认；1 条有误（IDML `_text` 解码范围，`tools/idml/data_components.py:48-63`），已改正规格表行与行内富文本行的 IDML 列。另抽查三条（网页 IR 只有一处生产调用、发布树 5 个目标带 `manual.ir.json`、已发布包 `snapshot_sha256` 为空），均成立。 |
| 2026-09-25 | 按操作者的建设思路，把 §3 的归类从两类改成四类（语义事实、内容结构、呈现提示、渲染器决策，另记来源信息），在表后加进包规则和按四类看出的两类偏差；§6 问题 4 改用四类措辞。只改归类和说明，表中其他各列不变。 |
