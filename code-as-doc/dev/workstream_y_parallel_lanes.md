# Workstream Y 多 agent 并行执行方案

Status: done · Owner: 夏冰 · Created: 2026-10-01 · Closed: 2026-10-02

本文件把 [`code_quality_iterability_plan.md`](code_quality_iterability_plan.md)（下称"计划台账"）
里本轮可推进的条目拆成 8 条泳道；无交叉的任务可并行，交叉文件按明确的所有权交接串行。
计划台账仍是唯一勾选处；本文件只规定"谁改哪些文件、怎么证明做完、怎么避免互相冲突"。

本文件不设时间限制，按第 4 节顺序尽快推进。复核基点为 2026-10-01 的
`origin/main` @ `d3f7f880b6317b3b302c8c3237c4bb58f92d9597`（#1349、#1350 均已合入）。
该点 CC≥50 的函数仍有 31 个；类型检查、lint 和生命周期数字的统计口径见对应泳道。

## 1. 所有泳道共用的规则（每个 agent 必读）

把本节和对应泳道一节一起贴给 agent 作为任务说明。

1. **先读** [`../../AGENTS.md`](../../AGENTS.md)，其规则优先于本文件。分支用
   `scripts/start_branch.sh <type>/<area>-<topic>` 创建，类型只能是
   `feat/fix/refactor/docs/chore`，不加 `claude/`、`codex/` 前缀。
2. **一个 PR 只做一件事**：一个函数、一个文件族或一个子包。diff 超过约 600 行（不含
   测试夹具和基线文件）就拆。
3. **只改本泳道"拥有的文件"。** 需要改别的泳道的文件时停下，在 PR 正文 "Follow-up"
   里记下，不要顺手改。认领时列出本批具体文件和对应测试；文件族不是扩大到未列文件的授权。
   文件锁覆盖开发中、已打开而未合入或关闭的 PR；交接须由原拥有者明确释放，接手者同步 main。
4. **不改以下文件**（由收尾 PR 统一处理）：`code_quality_iterability_plan.md`、
   `code_optimization_log.md`、`optimization_project.md`、本文件。PR 正文写明对应
   CQ 编号，便于收尾时勾选。唯一终局例外：第 3 节 G 的 CQ-7.5 在所有实施 PR
   合入或关闭后可修改 `optimization_project.md`、`code_optimization_log.md`。
5. **共享文件例外**：本泳道变更所需的棘轮基线（`data/complexity_baseline.tsv`、`data/broad_except_baseline.tsv`、
   `data/facade_patch_baseline.tsv`）只能用对应工具的 `update` 子命令重写，
   不手改。合并 main 时基线冲突一律：取 main 的版本 → 重新运行 `update` → 审查差异 → 重跑检查。
   不得借重新生成基线接受存量指标上升；新增拆分函数按 A 的验收规则审查。
   G 可用 `python tools/check_doc_lifecycle.py update` 更新 `data/doc_lifecycle_baseline.txt`。
   `pyproject.toml` 的 ruff 配置节归 D、mypy 配置节归 F；涉及该共享文件的提交须串行协调，
   同步前一提交后再改自己的配置节，不改依赖或 workflow。
6. **行为不变是默认要求。** 错误文本、退出码、CLI 参数、输出格式逐字不变；
   公开 CLI 参数、`requirements*`、`.github/workflows/**`、`data/phase2/**` schema
   一律不碰（需要时停下问操作者）。
7. **不碰线上**：不写飞书、不发布、不触发队列。
8. **开 PR 前按根 `AGENTS.md` §8.5 通过全部适用门禁**，其要求优先于下面的迭代命令。
   Python 逻辑变更至少运行：

   ```bash
   python -m ruff check build.py integrations tools tests scripts
   python tools/check_maintainability_guardrails.py
   python -m unittest                 # 全量；fast 和相关模块测试不能替代
   python -m tests.run_fast
   python -m unittest tests.test_<被改模块相关>
   ```

   本轮 Python 逻辑变更要求全量、快速层和相关模块测试均通过；迭代时可先跑快速层及相关模块，
   开 PR 前仍须补齐全部门禁。
   改了 `code-as-doc/**` 或 `user-guide/**` 再加 `python tools/check_doc_link_integrity.py`。
   类型、构建、质量门禁、diff-report 或发布追踪相关改动，补跑根规则对应的命令；纯文档改动按文档门禁验证。
   环境用 `scripts/setup_dev_env.sh` 建的 `.venv`（Python 3.12 + `requirements.lock`），并激活后运行。
   `ruff`、`mypy`、`coverage` 等开发工具仅装入该环境，记录版本；不修改依赖文件来满足本轮检查。
9. **PR 正文必须给出证据**：棘轮数字 before → after（复杂度、broad except、facade patch、
   mypy 错误数），实际运行过的命令。按 `.github/pull_request_template.md` 填写。
10. **不自行合并。** 由操作者合并，或由操作者在
    [`merge_authorizations.md`](merge_authorizations.md) 登记明确覆盖该 PR 的授权后按 gate-on-green 合入。
    本次「1353你审核觉得ok就允许合入」只覆盖 #1353 方案文档 PR；Workstream Y 实现 PR
    默认仍无合入授权，不因方案获准而自动获得。

## 2. 泳道总览

| 泳道 | 内容 | CQ | 拥有的文件 | 预计 PR 数 | 风险 |
| --- | --- | --- | --- | --- | --- |
| A1 | 配置校验函数改规则表 | 3.2 | `tools/validate_config.py`、`tools/config_pages.py` 及其测试 | 2 | 中 |
| A2 | IDML / IR 校验函数改规则表 | 3.2 | `tools/idml/reference_layout_plan.py`、`tools/manual_ir/validate.py` 及其测试 | 2 | 中 |
| B | 按实际命令、模式或职责阶段拆分 `main()` | 3.3 | `tools/lang_asset_sweep.py`、`tools/bitable_schema.py`、`tools/export_idml.py` 及其测试 | 3 | 低 |
| C | 队列依赖对象，削减门面 patch | 2.3 | `tools/process_build_queue*.py`、`tools/process_review_start_queue*.py`、`tests/test_process_*queue*.py`、`tests/test_build_docs_review_compat.py`、`tests/test_web_publish_queue.py`、`tests/test_target_resolution.py` | 4–6 | 高 |
| D | broad except 审计 + `B905` 审计 | 5.3、4.4 | 第 3 节 D 列出的文件族；csv_pages 三文件临时例外见 D，其余排除其它泳道文件 | 6–8 | 低 |
| E | 剩余 `print` → 日志 | 5.2 延续 | 第 3 节 E 列出的文件族；与 D 相交的族待 D 全部 PR 释放后接手 | 5–7 | 低 |
| F | mypy 严格范围扩大（先审计边界，再在范围内清错） | 4.5 | `tools/csv_pages/**`（待 D 交接）、`tools/component_specs/**`、`tools/manual_ir/**`（`validate.py` 及其测试待 A2 交接） | 3–4，越界依赖待裁定 | 中 |
| G | 文档生命周期补状态 + 路线图瘦身 | 7.3、7.5 | `code-as-doc/**`（保留文件仅在终局例外下修改）；生命周期基线按共享规则生成 | 2–3 | 很低 |

本次执行最多同时使用 **6 个子代理**，由主协调分派；使用子代理机制，不使用 `create_session`，
也不声称 8 条泳道各有独立容器。每个写入任务使用独立 checkout/worktree，遵守文件交接。
当前先推进 **A1、A2、B** 实现；C、F 先只读审计并暂停其待裁定部分，D、E、G 按空位与交接启动。

**启动前置已满足**：#1350 已合入，A1、A2 从上述 main 基点或更新的 main 开始，
沿用它的特征测试写法；F 的 csv_pages、manual_ir 另须满足 D、A2 的交接条件。

## 3. 各泳道任务说明

### A1 · 配置校验函数改规则表（CQ-3.2）

目标函数（每个函数一个 PR）：

- `tools/validate_config.py::validate`（复杂度 138）
- `tools/config_pages.py::parse_config_pages`（87）

做法沿用 #1350：

1. **先补特征测试网**，单独一个提交：冻结真实输入（`configs/*.yaml` 全量），
   用确定性变异（删字段、改类型、空值、越界值）生成数千个变体，把每个变体的
   输出（含异常 `!Type: msg`）哈希写入 `tests/fixtures/<name>_golden.json`，
   测试支持 `--update` 重新生成。语句覆盖率 ≥95%（用 `coverage` 量出来写进 PR）。
2. **再拆函数**，一个提交：按配置段拆成 `_validate_<section>(...) -> list[str]`，
   主函数用分派表 / 顺序调用；测试网逐字节不变。
3. `python tools/check_complexity_ratchet.py update`，PR 写明 before → after。

验收：主函数 ≤20；拆出的子函数如仍 >20 进基线，但每个 < 原值的一半；特征网通过。

### A2 · IDML / IR 校验函数改规则表（CQ-3.2）

- `tools/idml/reference_layout_plan.py::validate_approved_reference_plan`（107）
- `tools/manual_ir/validate.py::_payload_issues`（71）

做法、验收同 A1。真实输入从 `docs/` 下已批准的 reference plan 与
`tools/manual_ir` 现有测试夹具中收集；不新增仓库外依赖。
`tools/manual_ir/validate.py` 及其对应测试在该函数 PR 合入 main、A2 明确释放之前归 A2；
F 同步 main 并确认交接后方可接手。开 PR、agent 结束或某个测试通过均不算交接。

### B · 按实际命令、模式或职责阶段拆分 `main()`（CQ-3.3）

- `tools/lang_asset_sweep.py::main`（71）
- `tools/bitable_schema.py::main`（71）
- `tools/export_idml.py::main`（68）

每个文件一个 PR，按实际结构拆分：`bitable_schema` 有子命令，`export_idml` 按
`--check` / `--mode flow/pages` 等模式处理，`lang_asset_sweep` 是单一 sweep，按职责阶段拆分。
参数解析和业务行为保持不变；不得把整个 `main` 改名为 `_cmd_sweep` 来只降低入口指标。
PR 同时报入口和最大新增 handler 的复杂度及 before → after，证明职责得到拆分。
不额外要求所有 handler ≤20；超限项遵守棘轮及本次拆分的逐项审查。
先固定 `--help`、各命令/模式的最小输入、退出码和 stdout/stderr；会写线上的路径只测
参数校验失败或注入假外部边界，不连线上。这三个文件里的 `B905` 和 `print` 仍归 B，
仅在行为等价已证实时顺带处理（规则见 D、E），否则记 Follow-up，不混入行为改变。

### C · 队列依赖对象，削减门面 patch（CQ-2.3）

现状：门面 patch 共 363 处——`test_process_build_queue` 203、
`test_process_review_start_queue` 87、`test_process_build_queue_routing` 29、
`test_build_docs_review_compat` 22、`test_web_publish_queue` 15、
`test_target_resolution` 6、`test_build_review_preview` 1。

队列门面共 334 处（203 + 87 + 29 + 15）；其余 29 处属于 `build_docs`，不是队列依赖对象
自动覆盖的范围。`test_build_review_preview` 的 1 处未纳入 C 所有权，保留为后续项；
不得为凑指标扩大文件范围。

1. **先核查已有接缝**：复用 `tools/process_review_start_queue_runtime.py` 的
   `ReviewStartRuntimeDeps`；不再为 review-start 另造重复依赖容器。build 侧需要的新 helper
   只能放在已拥有的 `tools/process_build_queue*.py` 范围内，保留既有门面兼容路径。
2. **可先做不含时钟的首 PR**：限定为外部客户端、git、子进程运行器以及已有 deps 的
   接缝；默认实现保持现有查找行为，原测试继续通过，新接缝补相应注入验证。
   不迁整批旧测试，不声称时钟已完成。
3. **时钟部分暂停，等待操作者范围裁定**：完整时钟注入会触及当前不归 C 的
   `tools/queue_group_processing.py`、`tools/queue_claims.py`、`tools/queue_bound_records.py`。
   它们仍不属于 C 已授权文件范围；未经操作者裁定不扩大 C 权限。
   `sleep` 是等待函数，不是当前时间/时钟接缝。
4. **之后每个 PR 迁一个测试文件**（或 `test_process_build_queue` 的一个 TestCase 类）：
   把 `patch.object(process_build_queue, ...)` 换成注入假依赖，或改为 patch
   实际查找名字的模块。迁完运行
   `python tools/check_facade_patch_ratchet.py update`。
5. 不改 `queue_*` 的业务逻辑；发现 bug 记 Follow-up。剩余 `build_docs` patch 若需要
   修改 C 未拥有的实现文件，也先列为待裁定，不挪到另一个错误的 patch 位置隐藏计数。

验收目标：门面 patch 从 363 降到 ≤72（下降至少 80%）；全量测试绿色；时钟未完成时不得勾选
完整 CQ-2.3。门面行数不升须通过真实模块边界改善实现，不压缩空白凑行数；若原范围内无法
同时满足，报告待裁定，不删除仍被使用的转发。此泳道同一时间只允许一个 agent。

### D · broad except 审计 + `B905` 审计（CQ-5.3、CQ-4.4）

broad except 现有 89 处 / 56 个文件，按族各开一个 PR：
`verify_web_deployment`（4）、`queue_group`（4）、`asset_pipeline`（4）、
`integrations/product_voc`（4）、`publish_branch`（3）、`ops_catalog`（3）、
`indesign`（4：`indesign_finalize.py` 3、`indesign_finalize_jobs.py` 1）、`delivery`（3）、
`csv_pages`（3，D 先做，交接后 F 接手）、
`tools/build_*`（5）、`tools/idml`（5）、其余零散文件合并一个 PR。

`csv_pages` 临时归 D 的仅为基线中的三个文件：`tools/csv_pages/builder.py`、
`tools/csv_pages/renderers_safety.py`、`tools/csv_pages/renderers_spec_parser.py`。D 的该审计 PR
合入或关闭并明确释放后，F 同步 main 接手该包；交接前 F 的 csv_pages 写入暂停。
关闭 PR 不代表审计完成，未完成项须随交接列明。

D/E 相交文件族严格按 D → E 串行：包括已列范围中相交的 `idml/`、`ops_catalog_*`、
`indesign_*`、`asset_*` / `asset_pipeline`、`source_*`、`write_publish_html_*` 等实际文件。
先列明该族的具体文件；D 该族全部 PR 合入或关闭并释放后 E 才接手，锁覆盖所有未结 PR。
“其余零散文件”先列实际路径并核对所有者，不能据此自动扩到所有未列文件。

每处归入三类之一并在 PR 正文列表说明：

- **顶层边界**（CLI / 服务循环最外层）：保留，确认有 `log.exception` 或等价诊断；
- **可收窄**：改成具体异常类型（`OSError`、`ValueError`、`subprocess.CalledProcessError` …），
  必须有测试覆盖被收窄后的路径；
- **吞错 bug**：不在本泳道修行为，记 Follow-up。

`B905`（`zip` 未写 `strict=`）全检查范围（含 tests）有 62 处，其中生产范围
`build.py integrations tools scripts` 有 50 处。最多的是 `tools/idml/components/key_combinations.py`（5）、
`notice.py`（4）。逐处判断：长度必然相等 → `strict=True`（需有测试走到）；
有意截断 → `strict=False` 并加一行注释说明。不能证明长度不变量或行为等价时列 Follow-up。
跨泳道的命中项由原拥有者处理；D 不越界。全检查范围清零且 B 等相关 PR 已合入后，
协调 F 的配置提交，再把 `B905` 加入 `pyproject.toml` 的 ruff `select`（最后一个 PR）。

收尾后运行 `python tools/check_broad_except_ratchet.py update`。除上述 csv_pages 三文件临时例外，
不碰 A1/A2/B/C/F 拥有的文件；这些文件的未审计异常须列为遗留，不声称已完成全仓审计。

### E · 剩余 `print` → 日志（CQ-5.2 延续）

现存约 580 处 `print`。按族各一个 PR，从大到小：`bitable_*`（44）、`idml/`（21）、
`source_*`（20）、`ops_catalog_*`（14）、`spec_master_*`、`indesign_*`、`diff_*`、
`bitable_content_*`、`asset_*`（各约 12）、`release_*`、`patch_latex_*`、`content_*`、
`backport_*`、`write_publish_html_*`（各约 10）。

规则（见 `tools/utils/log.py` 文档字符串）：

- 只迁**进度/诊断行**，用 `get_logger("<component>")`；保留原 stdout/stderr 通道、文本和默认格式。
  原来写 stderr 的用 `stream="stderr"`，原来写 stdout 的错误也保留 stdout；
- **命令结果**（数据行、报告、`--json` 输出）和转发的子进程输出保持 `print`；
- 每个 PR 证明默认日志级别下文本、换行和输出通道等价；无法证明的行保留并记 Follow-up。
  另至少一个测试证明：`AUTO_MANUAL_LOG_LEVEL=WARNING` 时结果输出仍然完整
  （参照 `tests/test_queue_resolve_action.py` 中的
  `test_run_prints_json_result_even_when_log_level_hides_info`）。

不碰 B 等其它泳道的文件；D/E 相交的文件族须按 D 节完成整族交接，不能只避开 D 正在编辑的文件。

### F · mypy 严格范围扩大（CQ-4.5）

上述 main 基点、mypy 2.3.1 的完整命令输出（包含导入路径诊断）如下，两个口径不得混用：

| 包 | `python -m mypy --disallow-untyped-defs tools/<pkg>` | `python -m mypy --strict tools/<pkg>` |
| --- | --- | --- |
| `csv_pages` | 29 | 35 |
| `component_specs` | 87 | 129 |
| `manual_ir` | 125 | 183 |

`component_specs` 与 `manual_ir` 存在双向导入，不能假定三个包各自独立清零。先只读审计
导入边界，按路径区分包内、其它已拥有范围和范围外诊断；不得为修导入错误自动扩文件权限。
csv_pages 等 D 交接，manual_ir 等 A2 对应 PR 合入并交接；未满足前只能审计。

目前已发现的范围外候选文件如下，**仅供操作者裁定，不是新增白名单**。
计数来自各命令诊断，同一诊断可在多个命令出现，不得相加作为新的总数：

| 候选文件 | 错误数 |
| --- | --- |
| `tools/page_manifest.py` | 3 |
| `tools/signal_words.py` | 1 |
| `tools/idml/data_components.py` | 1 |
| `tools/idml/loaders.py` | 8 |
| `tools/idml_rst_extract.py` | 1 |
| `tools/render_contract.py` | 5 |
| `tools/rst_inline.py` | 4 |
| `tools/web_composite_presentation.py` | 3 |
| `tools/web_figure_coverage.py` | 2 |
| `tools/web_presentation_contract.py` | 3 |

另有 A2 当前持有的 `tools/manual_ir/validate.py` 2 处错误，必须等待原定交接。

1. 每个子包一个（或两个）PR：只补类型注解、`TypedDict`、`cast`，**零运行行为变化**；
   只改已拥有且已交接的范围；不加 `# type: ignore` 或 `follow_imports = "skip"` 掩盖错误。
2. 完整 `python -m mypy --strict tools/<pkg>` 因范围外依赖不能清零时，将对应条目标为
   **等待操作者范围裁定**，列出路径和错误；不提前加 strict override，不声称 CQ-4.5 已完成。
   真正清零后，与 D 串行协调 `pyproject.toml` 提交，才加入该包的完整严格配置。
   当前 `tools.utils.*` 只开启部分严格选项，不计作完整 `--strict` 覆盖；完成声明须使用同一口径。
3. **CI 检查路径**（`.github/workflows/**` 里的 `mypy tools/utils`）**不改**；
   三个子包都清零后，由操作者确认再单独开 workflow PR。

### G · 文档生命周期补状态 + 路线图瘦身（CQ-7.3、CQ-7.5）

1. 生命周期检查有 174 篇不合规，其中 152 篇缺少 Status，另 22 篇的现有状态不合规。
   按目录分 2–3 个 PR 补充或修正
   `Status: proposed | active | done | archived | superseded-by <link>`。
   判断依据：文档内容对应的功能是否仍在代码中、最近修改时间、是否有后继文档。
   拿不准的标 `active` 并在 PR 正文列出，由操作者判断。补完后仅用
   `python tools/check_doc_lifecycle.py update` 重写基线，并检查移除条目与本次改动一致。
2. 在 [`../README.md`](../README.md) §5 列出 `archived` 文档。**只标状态、不移动文件。**
3. CQ-7.5：把 `optimization_project.md` §4 "Recently Completed" 迁到
   `code_optimization_log.md`，§4 只留指针，目标 ≤600 行。此项会碰第 1 节第 4 条的
   保留文件，是第 1 节第 4 条的明确终局例外，**放到所有实施 PR 合入或关闭并释放后**再做。

## 4. 执行顺序（不设时间限制，尽快完成）

1. **本轮启动**：先推进 A1、A2、B。C、F 当前先只读审计、报告待裁定边界；C 不含时钟的
   首 PR 仅可按 C 节原有范围推进，完整时钟继续暂停。D、E、G 按最多 6 个子代理的空位和
   文件交接启动；C 同一时间只能有一个 agent。F 的 csv_pages 不抢在 D 交接前写入。
2. **滚动推进**：每条泳道按本节列表顺序连续开 PR；每合入一批，仍在进行的泳道先合并
   main（基线冲突按第 1 节第 5 条处理）再继续。交叉族仅在前一拥有者全部相关 PR 合入或关闭并
   明确释放后交接；完成或暂停的代理释放名额。实现 PR 的合入仍等待其独立授权。
3. **收尾**：所有泳道 PR 合入或关闭后，才做 G 泳道的 CQ-7.5（它会改保留文件），
   然后由一个 agent 开**收尾 PR**：按实际完成项勾选计划台账、写 `code_optimization_log.md`，
   明确列出暂停、关闭而未完成以及第 5 节未覆盖条目。
   只有本轮任务均完成或明确转交后才能把本方案标为 `done`；这不等于整个 Workstream Y 完成。

## 4.1 本轮结果（2026-10-02 收尾）

本方案执行完毕并关闭；**这不等于 Workstream Y 完成**，剩余项回到计划台账。

| 指标 | 起点（10-01） | 收尾 | 
| --- | --- | --- |
| 复杂度 ≥50 的函数 | 32 | 25 |
| 缺状态行的文档 | 174 | 5 |
| broad except | 89 | 86 |
| 门面 patch | 363 | 363 |
| `zip()` 无 `strict=`（B905） | 62 | 64（已加棘轮） |
| mypy untyped-def（三个子包，含包外导入） | 125 / 87 / 29 | 115 / 82 / 29（包内计数 119，已加棘轮） |
| `print` | ~580 | 568 |

已合入：A1 #1357 #1363 #1377；A2 #1355 #1361；B #1356 #1360；C #1362（骨架）；D #1358；
F #1375 #1379；G #1354 #1359；收尾（本 PR）加 B905、mypy 两个棘轮。

关闭未合入（落后 main 16 个提交，收益小于同步成本，需要时从最新 main 重开）：
#1365（F component_specs 类型）、#1366（D ops_catalog 异常审计）、#1368（E release 诊断日志）。

遗留（回到计划台账）：C 时钟接缝与门面 patch 迁移；B `export_idml`；D 其余 broad except 族与 B905 清零；
E 其余 `print` 族；F mypy 清零与严格 override；G 剩余 5 篇与 CQ-7.5。

## 5. 不在本方案内

- CQ-1.2 顶层模块棘轮，本轮未分配，保留为未完成项；
- CQ-1.3–1.5 包结构迁移（大面积改路径，与所有泳道冲突，单独排期）；
- CQ-2.4/2.5 门面转发删除（依赖 C 完成）；
- CQ-6.4 并行测试框架选型（涉及依赖变更）；
- 任何飞书写入、发布、队列操作、依赖版本或 workflow 变更。
