# REV-39 草稿 §6 A1–A9 答复与四项新增决定（2026-11）

Status: done · Owner: 夏冰 · Created: 2026-11-15

- 本记录的 `done` 只表示答复已记完；台账 [REV-39](manual_revitalization_execution.md#rev-39) 状态仍为 `deferred`，未重启。
- 草稿：[PR #1278](https://github.com/Bingboom/auto-manual/pull/1278)（未合入）中的 `code-as-doc/dev/manual_ir_p1_boundary_2026-09.md`，基线 `804cede4`，2026-09-25。
- 核对基线：main `66709a9f`。
- 决定：操作者夏冰，2026-11-15，在与 Claude 的工作会话中。
- 方法：Claude 对 main `66709a9f` 做三轮只读核对后逐项提出建议答复；未运行任何构建。操作者对四个新问题分别答复「指 InDesign 直接读网页那份结构化文件」「开始成为正式通道」「第 3 条要设正式字段」「给组件结构加版本」，对 A1–A9 及其七个子项答复「都按建议」。

## 用途与边界

- 只记录草稿 §6 A 组（1–9）的答复和今天代码引出的四个新问题的答复。
- 不重启 REV-39，不启动 P2，不冻结任何契约；台账状态、暂缓说明和重启条件不变。
- 不改代码、数据、配置、测试或发布。下文"后续事项"列出决定所蕴含的工作，都不在本记录内执行。
- 草稿的 30 行契约表与 §6 原文不在此复制，以 #1278 为准。

## A1–A9 的决定

**A1 试点冻结源。** 问：沿用 `tests/fixtures/phase2`，还是新建 `manual_sources/JBP-2000B/JP` 快照？
- 决定：新建 JBP-2000B 日规的数据快照包 `manual_sources/JBP-2000B/JP/ja/<版本>`，照 `manual_sources/JBP-2000B/EU/en/2.0`（phase2 CSV 加附件，登记进 `data/frozen_package_registry.json`）的做法；不沿用 `tests/fixtures/phase2`。
- 子项 a：以日规候选拼版约定已引用的那份日规 V2.0 印刷稿为准。
- 子项 b：试点不另开审核分支，发布走已有文档的 Git-only 路径。
- 依据：main 上没有 `manual_sources/JBP-2000B/JP`，也没有 `docs/_review/JBP-2000B`；`manual_sources/JBP-2000B/EU/en/2.0` 含 `phase2/` 与 `source_manifest.json`，已登记。Git-only 事务要求同一 PR 内登记包（`code-as-doc/dev/web_publish_pipeline/input-paths.md` §2.2，约 79–97 行）。

**A2 回归基线。** 问：JE-1000F/US 用基线提交上的 review-asis 输入重建，还是以已发布 v2.5 MyST 为准？
- 决定：JE-1000F/US 用审核层原样（review-asis）重建，要求重建出的投影源文件逐文件哈希与已发布 v2.5 的 language_projection_receipt 记录一致，并核对 MyST 与 v2.5 等价，然后把这次重建（含 `manual.ir.json`）作为网页基线；IDML 基线保持已批准版式计划钉住的 manual-ir/v1 内容哈希。
- 以后另需操作者批准、本次未定：哪个提交算基线；IDML 改读 v2 包后的正式重绑。
- 依据：main 上没有 `manual_sources/JE-1000F/US`；已批准版式计划钉 `manual-ir/v1` 与内容哈希（`docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json` 约 838–841 行）。

**A3 公共组装位置。** 问：在 `.. only::` 分支解析之前从 CSV 与配方数据组装，还是同时保留两个分支？
- 决定：仍从 RST bundle 组装；内容条件（型号、区域、语言、品类、能力）只解一次；语义不再按输出标签（html、latex、idml）选分支，每个语义组件以中立的 `raw:: manual-ir` 载荷随源文件走，载荷由 ComponentSpec 序列化；html 与 latex 分支降为各端的呈现；网页专属处理（成品图替换、删除被覆盖标注、标题转大写、Word-friendly 改写）移入网页 adapter；逐页迁移，先做试点页。
- 子项 c：审核层的 RST 允许带这种载荷，回写工具不写这些载荷。
- 子项 d：试点涉及的组件，网页改为读载荷而不是按 HTML 选择器识别，这些页的网页输出重定一次基线。
- 依据：网页在网页专属处理后冻结 html 分支（`tools/web/document_source.py` `load_web_document`），组件按 HTML 识别（`tools/manual_ir/whole_document_components.py` `discover_registered_components`）；IDML 以 `latex` 加 `idml` 标签从 prepared bundle 建 `manual-ir/v1`（`tools/manual_ir/prepared_rst.py` 约 149–157 行；`tools/idml/ir_projection.py` `build_same_source_ir`）。

**A4 只在 LaTeX 分支的内容。** 问：安全页信号键与图标、LaTeX 目录、USB-C 按功率拆行、封面图、目录页码算语义事实或内容结构（进共享包），还是渲染器决策（留在 LaTeX adapter）？
- 决定：进共享包——安全信号词的键、图标身份、目录条目（由标题推出）、封面素材身份；留在印刷端 adapter——目录页码、图片文件格式的选择、USB-C 按功率拆行（做成一个具名的共享投影函数供印刷端调用）。
- 子项 e：网页不改成按功率拆行显示。
- 依据：信号键今天只在 LaTeX 宏 `\HBSymbolSignalRow[key]` 里（`tools/csv_pages/renderers_symbols.py` 约 535–539 行；`tools/idml/data_components.py` 约 178 行）；IDML 目录条目取自标题、页码取自页面计划（`tools/idml/page_toc.py`；`tools/idml/ir_projection.py` 约 141–146 行）。

**A5 素材变体。** 问：公共包是否必须同时带网页成品图和 IDML 无字底图，并保留被网页覆盖的标注原结构？
- 决定：包里两种图都带；标注文字及其顺序是语义事实，放在受约定管理的槽位；无字底图与成品图各有登记键与哈希；标注坐标留在各端自己的约定里（网页 `base_art_layout`，IDML `figure_callouts`）；删除被成品图覆盖的标注这一步移入网页 adapter。
- 子项 f：第一轮不为连接页的 9 张图做无字化，第二个单元再定。
- 依据：JBP-2000B/JP 仍用成品图并删除被覆盖标注（`configs/config.bp-jp.yaml` 约 42 行 → `docs/renderers/web/jbp2000b_jp_illustrations.json`；删除见 `tools/web/document_source.py` 约 79–95 行 `_consume_covered_annotations`）。

**A6 source_ref 相对化。** 问：source_ref 是否相对化？绝对路径进入块哈希，需写明兼容办法。
- 决定：新包的 ComponentSpec `source_ref` 必须是相对 bundle 的路径，加一条校验规则强制；旧包保持冻结，下次修订时重建；`source_ref` 是否移出参与哈希的内容本次不动。
- 依据：块哈希只覆盖 `{kind, payload}`（`tools/manual_ir/builder.py` 约 77 行；`tools/manual_ir/validate.py` 约 383 行），ComponentSpec 的 `source_ref` 在 payload 内，因而参与哈希；850 个绝对路径值分布在 47 个包里。

**A7 语言标识。** 问：包里用 `ja` 还是 `jp`？归一放在包里还是 adapter？
- 决定：包里用 `ja`；转成 `jp` 只在 IDML adapter 里做，经 `tools/lang_registry.py`。
- 子项 g：不改写日规候选拼版约定，匹配时比较规范码。
- 依据：`tools/lang_registry.py` 约 130–146 行定义代码 `ja`、别名与列后缀含 `jp`；IDML 仍归一到 `jp`（`tools/idml/loaders.py` `normalize_lang`）；候选约定 `docs/renderers/contracts/target_assembly/jbp2000b_jp_v1_candidate.json` 写 `jp`，`tools/idml/target_assembly_plan.py` 约 1377 行按字符串相等比较。

**A8 冻结包边界。** 问：沿用 md 目录（MyST、素材、IR），还是新的产物？队列网页发布是否保留 `manual.ir.json` 与 `manual_bundle.html`？
- 决定：沿用现有按语言的 md 目录作为网页冻结包；两条通道（队列暂存与 Git-only 组装）都保留 `manual.ir.json`；`manual_bundle.html` 可选。结合 N1：IDML 读的就是这个包里的 v2 IR；两端共用同一份 phase2 快照只是第一个台阶。
- 依据：队列暂存复制 `manual.ir.json`（`tools/build_queue/outputs.py` 约 36 行）；Git-only 组装在存在时复制它与 `manual_bundle.html`（`tools/publish_branch_assembly.py` 约 142 行）。

**A9 试点补充页。** 问：试点补充素材页选 A（`connections_ja`）还是 B（`symbol_meaning_ja`）？
- 决定：第一轮加 B `symbol_meaning_ja`；A `connections_ja` 作为第二个单元；第一轮不强制覆盖富文本与素材引用。

## 新增四项决定

- **N1** REV-40 的"同一份冻结整本包"指 IDML 直接读网页那份 v2 结构化文件（`manual.ir.json`），不是仅共用数据快照。
- **N2** 中立的 `raw:: manual-ir` 载荷成为正式通道。今天只在一处使用：`docs/templates/page_jp/toc.rst` 在 `.. only:: idml` 下带 `raw:: manual-ir`（kind `toc`）；网页只读 `operation_panel_copy` 一种（`tools/web/document_source.py` 约 42–75 行）。
- **N3** 图上的标注文字设为 HB-SPECIAL-REFERENCE-FIGURE 的正式槽位，不论网页显示的是成品图还是无字底图。今天 778 个该组件只在 `metadata.embedded_labels` 里留有烤进图里的标注文字。
- **N4** 组件结构变化（例如给 HB-TABLE-SYMBOL-SIGNAL 加信号键）用给组件结构加版本的办法处理，不走漂移记录；旧冻结包保持原版本与哈希，读取端两种版本都要认。

## 草稿之后已变化的事实

以下相对草稿基线 `804cede4` 已变，按 main `66709a9f` 核对；计数取自 `manual_sources` 与 `data/manual_sources` 下的 328 个 `manual.ir.json`，其中含同一本书的多个快照版本。

- 冻结包已有登记：两类（phase2 数据根快照，如 `manual_sources/JBP-2000B/EU/en/2.0`；以及 `web/<lang>/…` 布局的纯网页包），`data/frozen_package_registry.json` 登记 265 个；未登记的包使维护性检查失败（`tools/web/frozen_package_registry.py` 顶部说明）。
- IR 已保留：队列暂存与 Git-only 组装都复制 `manual.ir.json`；生产代码可从存储的 IR 重放（`tools/web/frozen_ai_web.py` `replay_package`；`tools/web/component_admission.py`）。Hello-Docs 镜像 2026-11-09 时 210 个网页目标中 185 个带 `manual.ir.json`（未复核，本次未读镜像）。
- 队列 `web_publish` 通道仍传 `source="review"`（`tools/build_queue/build_execution.py` 约 359 行）；IDML 接受 `--data-root`（`tools/build_dispatch.py` 约 339 行）。
- 符号页改按声明的页面角色认领（`tools/word/bundle_html.py` 约 424–431 行）。
- 中立载荷通道已存在于日规目录页（见 N2）。
- HB-TABLE-SYMBOL-SIGNAL 行只有 label / show_icon / meaning，没有信号键（`docs/renderers/contracts/component_registry.yaml` 该条目；`tools/component_specs/manual_tables.py` 约 189–194 行）。存储包中约 201 个该组件（未复核：本次换一种计数口径得 231）。
- source_ref：页级与块级引用均为相对路径；ComponentSpec 的 `source_ref` 共 12,215 个（未复核：换口径得 12,223），其中 850 个为绝对路径，分布在 2026-10 及以前构建的 47 个包；没有校验强制相对路径。
- 语言：存储包只用 `ja`，没有 `jp`；53 个 HB-CALLOUT-STRIP 的语言为 `und`（未复核：换口径得 150）。
- 参考图：3,438 个 HB-SPECIAL-REFERENCE-FIGURE 中 1,236 个用 `base-art-live-copy`（`tools/web/base_art_reference.py`），其中日文 294 个。

## 后续事项

以下由上述决定蕴含，不在本记录内执行，各自开工时另按台账规则指派：

1. 设计组件结构版本机制（先核对登记表现在是否支持按组件加版本，本次未核实）。
2. 网页端读取全部种类的中立载荷，并把日规目录载荷移出仅 IDML 的分支。
3. 给信号词表组件加信号键槽位。
4. 给参考图组件加标注文字正式槽位。
5. 新增 source_ref 相对路径校验。
6. IDML 匹配时比较规范语言码。
7. 制作 JBP-2000B 日规数据快照包并登记。
8. JE-1000F/US 基线重建与哈希核对。
9. IDML 改读 v2 后对已批准版式计划的正式重绑（审批事项）。
10. REV-20 验收清单。

## 未决与未核实

- 草稿 §6 的 B 组（10–16）与 C 组（17–18）未答。
- `prepared-document` 来源标签是否拆分。
- `approved_composite` 角色是否保留（196 个同时带两种角色的组件里两者是同一文件；计数未复核）。
- `base_art_layout` 的坐标是否应移出共享元数据。
- 日规 toc 页在网页端是否产生空页（需要构建确认）。
- 语言为 `und` 的警示条组件在新版本里取什么值。

## 修订记录

| 日期 | 内容 |
| --- | --- |
| 2026-11-15 | 初稿。记录操作者对草稿 §6 A1–A9（含七个子项）与四个新问题的答复；核对基线 main `66709a9f`，只读，未运行构建；REV-39 保持 deferred。 |
