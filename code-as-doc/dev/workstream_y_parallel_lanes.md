# Workstream Y 多 agent 并行执行方案

Status: active · Owner: 夏冰 · Created: 2026-10-01

本文件把 [`code_quality_iterability_plan.md`](code_quality_iterability_plan.md)（下称"计划台账"）
里剩余的条目拆成 8 条**互不重叠的泳道**，每条泳道可以整段交给一个 agent 独立执行。
计划台账仍是唯一勾选处；本文件只规定"谁改哪些文件、怎么证明做完、怎么避免互相冲突"。

数字均取自 2026-10-01 的 `origin/main`（#1349 已合入，#1350 待合入）。

## 1. 所有泳道共用的规则（每个 agent 必读）

把本节和对应泳道一节一起贴给 agent 作为任务说明。

1. **先读** [`../../AGENTS.md`](../../AGENTS.md)，其规则优先于本文件。分支用
   `scripts/start_branch.sh <type>/<area>-<topic>` 创建，类型只能是
   `feat/fix/refactor/docs/chore`，不加 `claude/`、`codex/` 前缀。
2. **一个 PR 只做一件事**：一个函数、一个文件族或一个子包。diff 超过约 600 行（不含
   测试夹具和基线文件）就拆。
3. **只改本泳道"拥有的文件"。** 需要改别的泳道的文件时停下，在 PR 正文 "Follow-up"
   里记下，不要顺手改。
4. **不改以下文件**（由收尾 PR 统一处理）：`code_quality_iterability_plan.md`、
   `code_optimization_log.md`、`optimization_project.md`、本文件。PR 正文写明对应
   CQ 编号，便于收尾时勾选。
5. **棘轮基线**（`data/complexity_baseline.tsv`、`data/broad_except_baseline.tsv`、
   `data/facade_patch_baseline.tsv`）只能用对应工具的 `update` 子命令重写，
   不手改。合并 main 时基线冲突一律：取 main 的版本 → 重新运行 `update` → 提交。
6. **行为不变是默认要求。** 错误文本、退出码、CLI 参数、输出格式逐字不变；
   公开 CLI 参数、`requirements*`、`.github/workflows/**`、`data/phase2/**` schema
   一律不碰（需要时停下问操作者）。
7. **不碰线上**：不写飞书、不发布、不触发队列。
8. **推送前本地必须通过**（缺一不开 PR）：

   ```bash
   python -m ruff check build.py integrations tools tests scripts
   python tools/check_maintainability_guardrails.py
   python -m tests.run_fast            # 迭代用；开 PR 前改动模块的测试必须全绿
   python -m unittest tests.test_<被改模块相关>
   ```

   改了 `code-as-doc/**` 或 `user-guide/**` 再加 `python tools/check_doc_link_integrity.py`。
   环境用 `scripts/setup_dev_env.sh` 建的 `.venv`（Python 3.12 + `requirements.lock`），
   否则会出现与 CI 不一致的假失败。
9. **PR 正文必须给出证据**：棘轮数字 before → after（复杂度、broad except、facade patch、
   mypy 错误数），实际运行过的命令。按 `.github/pull_request_template.md` 填写。
10. **不自行合并。** 由操作者合并，或由操作者在
    [`merge_authorizations.md`](merge_authorizations.md) 登记批量授权后按 gate-on-green 合入。

## 2. 泳道总览

| 泳道 | 内容 | CQ | 拥有的文件 | 预计 PR 数 | 风险 |
| --- | --- | --- | --- | --- | --- |
| A1 | 配置校验函数改规则表 | 3.2 | `tools/validate_config.py`、`tools/config_pages.py` 及其测试 | 2 | 中 |
| A2 | IDML / IR 校验函数改规则表 | 3.2 | `tools/idml/reference_layout_plan.py`、`tools/manual_ir/validate.py` 及其测试 | 2 | 中 |
| B | `main()` 拆成子命令处理函数 | 3.3 | `tools/lang_asset_sweep.py`、`tools/bitable_schema.py`、`tools/export_idml.py` 及其测试 | 3 | 低 |
| C | 队列依赖对象，削减门面 patch | 2.3 | `tools/process_build_queue*.py`、`tools/process_review_start_queue*.py`、`tests/test_process_*queue*.py`、`tests/test_build_docs_review_compat.py`、`tests/test_web_publish_queue.py`、`tests/test_target_resolution.py` | 4–6 | 高 |
| D | broad except 审计 + `B905` 审计 | 5.3、4.4 | 第 3 节 D 列出的文件族（排除其它泳道的文件） | 6–8 | 低 |
| E | 剩余 `print` → 日志 | 5.2 延续 | 第 3 节 E 列出的文件族 | 5–7 | 低 |
| F | mypy 严格范围扩大（先清错，后接入） | 4.5 | `tools/csv_pages/**`、`tools/component_specs/**`、`tools/manual_ir/**`（`validate.py` 除外） | 3–4 | 低 |
| G | 文档生命周期补状态 + 路线图瘦身 | 7.3、7.5 | `code-as-doc/**`（第 1 节第 4 条列出的文件除外） | 2–3 | 很低 |

同时开 4–6 个 agent 即可；优先顺序 **C → A1 → A2 → F → B → D → E → G**
（C 收益最大、周期最长，最先开；G、E 最机械，可以填空闲）。

**启动前置**：A1、A2 等 #1350 合入后再开（它改了 `data/complexity_baseline.tsv`
和特征测试写法，A 泳道要沿用）。

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
`tools/manual_ir/validate.py` 在 A2 完成前归 A2，F 泳道跳过它。

### B · `main()` 拆成子命令处理函数（CQ-3.3）

- `tools/lang_asset_sweep.py::main`（71）
- `tools/bitable_schema.py::main`（71）
- `tools/export_idml.py::main`（68）

每个文件一个 PR：参数解析一字不改，每个子命令拆成 `_cmd_<name>(args) -> int`，
`main` 只负责解析和分派。先加一个测试：对每个子命令用 `--help` 和最小参数跑一遍，
固定退出码与 stdout/stderr（会写线上的子命令只测到参数校验失败分支，不连线上）。
这三个文件里的 `B905` 和 `print` 也归 B 泳道（顺带处理，规则见 D、E）。

### C · 队列依赖对象，削减门面 patch（CQ-2.3）

现状：门面 patch 共 363 处——`test_process_build_queue` 203、
`test_process_review_start_queue` 87、`test_process_build_queue_routing` 29、
`test_build_docs_review_compat` 22、`test_web_publish_queue` 15、
`test_target_resolution` 6、`test_build_review_preview` 1。

1. **第一个 PR**：在 `tools/process_build_queue.py`（及 review-start 门面）引入
   `QueueDeps` dataclass（外部客户端、git 执行器、时钟、子进程运行器），默认值为
   真实实现；处理函数增加 `deps: QueueDeps | None = None` 参数。运行行为不变，
   不迁任何测试。
2. **之后每个 PR 迁一个测试文件**（或 `test_process_build_queue` 的一个 TestCase 类）：
   把 `patch.object(process_build_queue, ...)` 换成传入假 `QueueDeps`，或改为 patch
   实际查找名字的模块。迁完运行
   `python tools/check_facade_patch_ratchet.py update`。
3. 不改 `queue_*` 的业务逻辑；发现 bug 记 Follow-up。

验收：门面 patch 从 363 降到 ≤73（−80%）；全量测试绿色；`process_build_queue.py`
行数不升。此泳道冲突面最大，同一时间只允许一个 agent。

### D · broad except 审计 + `B905` 审计（CQ-5.3、CQ-4.4）

broad except 现有 89 处 / 56 个文件，按族各开一个 PR：
`verify_web_deployment`（4）、`queue_group`（4）、`asset_pipeline`（4）、
`integrations/product_voc`（4）、`publish_branch`（3）、`ops_catalog`（3）、
`indesign`（3）、`delivery`（3）、`csv_pages`（3，与 F 协调：D 先做）、
`tools/build_*`（5）、`tools/idml`（5）、其余零散文件合并一个 PR。

每处归入三类之一并在 PR 正文列表说明：

- **顶层边界**（CLI / 服务循环最外层）：保留，确认有 `log.exception` 或等价诊断；
- **可收窄**：改成具体异常类型（`OSError`、`ValueError`、`subprocess.CalledProcessError` …），
  必须有测试覆盖被收窄后的路径；
- **吞错 bug**：不在本泳道修行为，记 Follow-up。

`B905`（`zip` 未写 `strict=`）现有 62 处，最多的是 `tools/idml/components/key_combinations.py`（5）、
`notice.py`（4）。逐处判断：长度必然相等 → `strict=True`（需有测试走到）；
有意截断 → `strict=False` 并加一行注释说明。全部清零后把 `B905` 加入
`pyproject.toml` 的 ruff `select`（最后一个 PR）。

收尾后运行 `python tools/check_broad_except_ratchet.py update`。不碰 A1/A2/B/C/F 拥有的文件。

### E · 剩余 `print` → 日志（CQ-5.2 延续）

现存约 580 处 `print`。按族各一个 PR，从大到小：`bitable_*`（44）、`idml/`（21）、
`source_*`（20）、`ops_catalog_*`（14）、`spec_master_*`、`indesign_*`、`diff_*`、
`bitable_content_*`、`asset_*`（各约 12）、`release_*`、`patch_latex_*`、`content_*`、
`backport_*`、`write_publish_html_*`（各约 10）。

规则（见 `tools/utils/log.py` 文档字符串）：

- 只迁**进度/诊断行**，用 `get_logger("<component>")`，错误类诊断用 `stream="stderr"`；
- **命令结果**（数据行、报告、`--json` 输出）和转发的子进程输出保持 `print`；
- 每个 PR 至少一个测试证明：`AUTO_MANUAL_LOG_LEVEL=WARNING` 时结果输出仍然完整
  （参照 `tests/test_queue_resolve_action.py` 中的
  `test_run_prints_json_result_even_when_log_level_hides_info`）。

不碰 B 泳道的 `bitable_schema.py` 和 D 泳道当前 PR 正在改的文件。

### F · mypy 严格范围扩大（CQ-4.5）

当前 `--disallow-untyped-defs` 错误数：`tools/csv_pages` 29、`tools/component_specs` 87、
`tools/manual_ir` 125。顺序：csv_pages → component_specs → manual_ir（A2 完成后）。

1. 每个子包一个（或两个）PR：只补类型注解、`TypedDict`、`cast`，**零运行行为变化**；
   不加 `# type: ignore`，必须加时逐处说明。
2. 本地 `python -m mypy --strict tools/<pkg>` 清零后，在 `pyproject.toml` 加该子包的
   严格 override。
3. **CI 检查路径**（`.github/workflows/**` 里的 `mypy tools/utils`）**不改**；
   三个子包都清零后，由操作者确认再单独开 workflow PR。

### G · 文档生命周期补状态 + 路线图瘦身（CQ-7.3、CQ-7.5）

1. 缺状态行的存量文档约 174 篇：按目录分 2–3 个 PR 补
   `Status: proposed | active | done | archived | superseded-by <link>`。
   判断依据：文档内容对应的功能是否仍在代码中、最近修改时间、是否有后继文档。
   拿不准的标 `active` 并在 PR 正文列出，由操作者判断。补完后基线文件同步删行。
2. 在 [`../README.md`](../README.md) §5 列出 `archived` 文档。**只标状态、不移动文件。**
3. CQ-7.5：把 `optimization_project.md` §4 "Recently Completed" 迁到
   `code_optimization_log.md`，§4 只留指针，目标 ≤600 行。此项会碰第 1 节第 4 条的
   保留文件，**放到第 4 天、其它泳道都停止开新 PR 之后**再做。

## 4. 四天节奏

| 天 | 安排 |
| --- | --- |
| 第 1 天 | 开 C（第一个 PR：`QueueDeps` 骨架）、A1/A2 的特征测试网、F 的 csv_pages、G 第一批。低风险、建立证据。 |
| 第 2–3 天 | A1/A2 拆函数；C 按测试文件迁移；B、D、E 并行铺开。每晚操作者批量审合一次，各 agent 第二天先合并 main 再继续。 |
| 第 4 天 | 不再开新的高风险 PR。各泳道只处理评审意见和冲突；G 做 CQ-7.5；最后由一个 agent 开**收尾 PR**：勾选计划台账、写 `code_optimization_log.md`、刷新本文件状态为 `done`。 |

## 5. 不在本方案内

- CQ-1.3–1.5 包结构迁移（大面积改路径，与所有泳道冲突，单独排期）；
- CQ-2.4/2.5 门面转发删除（依赖 C 完成）；
- CQ-6.4 并行测试框架选型（涉及依赖变更）；
- 任何飞书写入、发布、队列操作、依赖版本或 workflow 变更。
