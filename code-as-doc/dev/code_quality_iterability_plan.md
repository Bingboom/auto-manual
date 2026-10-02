# 代码质量与可迭代性优化方案（Workstream Y）

Status: active · Owner: 夏冰 · Created: 2026-09-28 · Updated: 2026-10-02

本文件是 [`../optimization_project.md`](../optimization_project.md) Workstream Y 的
PR 级拆分和唯一勾选台账。它把 2026-09-28 全仓代码质量评估发现的 7 个问题
（CQ-1 … CQ-7）写成可执行、可验收的 checklist。

- 方案提交**不等于**实施完成：本 PR 只登记方案，不勾选任何实施项。
- 每个勾选项默认对应一个独立 PR；一个 PR 只做一件事，行为保持不变，除非条目
  明确写了行为变化。
- 与既有治理机制保持同一风格：**先建基线，只拦新增（ratchet），再逐步清存量**。
  参考 [`../../tools/check_maintainability_guardrails.py`](../../tools/check_maintainability_guardrails.py)
  的行数上限和 [`../../tools/check_language_literal_ratchet.py`](../../tools/check_language_literal_ratchet.py)
  的字面量棘轮。

## 0. 评估基线（2026-09-28，`main` @ `b84239b`）

| 维度 | 基线值 | 复测方式 |
|---|---|---|
| 规模 | `tools/` 约 17 万行、365 个条目、约 330 个顶层模块；`tests/` 约 13 万行 | `find tools -name '*.py' \| xargs wc -l` |
| 顶层前缀族 | `web_` 38、`queue_` 28、`build_` 27、`check_` 20、`word_` 15、`rtd_` 14、`sync_` 13、`cloud_doc_backport_` 13 | `ls tools/*.py \| sed 's#tools/##; s#_.*##' \| sort \| uniq -c` |
| 脚本启动代码 | 154 个文件使用 `script_bootstrap` 或 `sys.path.insert`（其中 51 个直接写 `sys.path.insert`） | `grep -rlE 'script_bootstrap\|sys.path.insert' tools \| wc -l` |
| 测试替身 | 80 个测试文件、614 处 `patch`；对门面模块的 `patch.object`：`process_review_start_queue` 71、`process_build_queue` 61 | `grep -rhoE 'patch\.object\(\s*[a-z_]+' tests \| sort \| uniq -c` |
| 门面转发 | `tools/build_docs.py` 43 个 `*_impl` 转发；`tools/process_build_queue.py` 70 个仅用于再导出的 import | `grep -c '_impl(' tools/build_docs.py` |
| 圈复杂度 | ruff `C901` 305 处；CC≥50：31 个函数，CC≥30：113 个，CC≥20：273 个；平均 5.8 | `ruff check build.py tools integrations scripts tests --select C901 --statistics` |
| ruff 启用规则 | 仅 `E722`、`F821`、`F841` | [`../../pyproject.toml`](../../pyproject.toml) |
| 潜在缺陷 | `F401` 215、`B023` 26、`B905` 45、`PLW1510` 8、`B904` 4 | `ruff check build.py tools integrations scripts --select F401,B023,B905,PLW1510,B904 --statistics` |
| 资源泄漏 | 7 处 `csv.DictReader(path.open(...))` 未关闭文件，测试中出现 `ResourceWarning` | 见 CQ-4.1 清单 |
| 类型检查 | mypy 严格模式仅覆盖 `tools/utils`（16 个文件）；约 69% 的 `def` 标注了返回类型 | `python -m mypy tools/utils` |
| 日志 | `print(` 594 处；使用 `logging` 的文件 2 个；`except Exception` 75 处 | `grep -rn '^\s*print(' tools build.py \| wc -l` |
| 测试反馈 | 4733 个测试，本地单进程约 11 分钟；环境与 lock 文件不一致时出现 17 个非代码原因的失败 | `python -m unittest` |
| 文档 | `code-as-doc/` + `user-guide/` 235 篇、约 5.1 万行；`code-as-doc/dev/` 86 篇；`optimization_project.md` 964 行 | `find code-as-doc user-guide -name '*.md' \| wc -l` |

基线中的 ruff 扩展规则统计来自临时安装的 ruff/radon，不代表 CI 当前启用了这些规则。

## 1. 总览

| ID | 问题 | 优先级 | 依赖 | 预估 PR 数 | 需操作者确认的门槛 |
|---|---|---|---|---|---|
| CQ-1 | `tools/` 平铺，靠文件名前缀充当包 | P2 | CQ-2 的第一批测试接缝、CQ-7.4 | 6–8 | 热点模块改名/移动（AGENTS.md §8.4）；改 `.github/workflows/**` |
| CQ-2 | 测试与模块路径强耦合，门面转发无法删除 | P1 | 无 | 4–6 | 无 |
| CQ-3 | 复杂度热点集中，只有行数上限，没有复杂度上限 | P1 | CQ-3.1 先行 | 5–7 | 无 |
| CQ-4 | 静态检查基线偏弱 | **P0** | 无 | 5–6 | 扩 mypy 路径需要改 CI workflow |
| CQ-5 | 日志、异常处理、子进程编排缺乏契约 | P1 | 无 | 4–5 | 无（不改公开 CLI 参数） |
| CQ-6 | 测试反馈慢，对环境敏感 | P1 | 无 | 4–5 | 新增测试依赖（`requirements*`）；改 CI 矩阵 |
| CQ-7 | 文档数量膨胀，状态不清 | P2 | 无 | 4–5 | 移动/改名已提交文档；修改 `AGENTS.md` |

## 2. 分项方案与 checklist

### CQ-1 包结构：把前缀族收拢为子包，统一 `python -m` 入口

**问题。** 模块边界只靠命名约定维持；154 个文件需要启动代码才能同时作为脚本和模块运行；
[`../code_style_guide.md`](../code_style_guide.md) §2 的模块边界（2026-03-17）没有覆盖
web、IDML、队列、回写这几块目前最大的代码面。

**目标。** 领域代码位于真实子包中；新代码不再加入 `tools/` 顶层；入口统一为
`python -m tools.<pkg>.<module>`；启动代码数量只减不增。

- [x] **CQ-1.1 边界文档先行。** 更新 [`../code_style_guide.md`](../code_style_guide.md) §2
  和 [`orchestration_module_map.md`](orchestration_module_map.md)，写入当前真实领域
  （build / check / queue / backport / web / rtd / word / idml / manual_ir / component_specs /
  asset）及每个领域的目标子包名。只改文档（与 CQ-7.4 同一个 PR）。
  （#1331，2026-09-30；目标子包提案见 `code_style_guide.md` §2.16）
- [ ] **CQ-1.2 顶层模块棘轮。** 在 `check_maintainability_guardrails.py` 中增加：`tools/`
  顶层 `.py` 数量与 `script_bootstrap`/`sys.path.insert` 使用数量只减不增；新增顶层模块需要在
  允许清单里写明理由。
- [ ] **CQ-1.3 试点迁移一个低耦合族。** 选 `cloud_doc_backport_*`（13 个文件，已有单向
  import 约束）迁到 `tools/backport/`。旧路径保留一个只做再导出的薄 shim，并加
  `DeprecationWarning`；[`../../AGENTS.md`](../../AGENTS.md) §3 引用的
  `python tools/cloud_doc_backport.py` 命令保持可用。**开工前需操作者确认**（热点模块移动）。
- [ ] **CQ-1.4 按族迁移其余前缀。** 每个 PR 迁一族，顺序：`queue_*` → `check_docs_*` →
  `build_docs_*` → `web_*` → `rtd_*` / `word_*`。每个 PR 同时更新 `orchestration_module_map.md`
  和热点行数上限表中的路径。
- [ ] **CQ-1.5 入口统一。** 让 `scripts/`、文档中的命令、`build.py` 的子进程调用改用
  `python -m`；确认没有调用方后删除 shim 与启动代码。**涉及 `.github/workflows/**` 的改动需操作者确认。**

**验收。** `tools/` 顶层 `.py` 数量下降 ≥50%；启动代码使用数从 154 降到只剩真正的脚本入口；
`python -m unittest` 与 `build.py check` 保持绿色；旧命令在 shim 窗口期内仍能运行。

### CQ-2 测试接缝：解耦测试与模块路径，删除门面转发

**问题。** 很多测试通过 `patch.object(process_build_queue, ...)` 这类方式替换门面模块上的名字。
为了不破坏这些 patch，拆分后的门面必须保留转发（`build_docs.py` 43 个 `*_impl`、
`process_build_queue.py` 70 个再导出）。每移动一次代码都要同时维护新旧两套路径。

**目标。** 测试替换的是"被测代码实际查找的名字"或显式注入的依赖；门面只保留真正的公开 API，
并用 `__all__` 声明。

- [x] **CQ-2.1 写下测试约定。** 在 [`../../tests/CLAUDE.md`](../../tests/CLAUDE.md)、
  [`../../tests/AGENTS.md`](../../tests/AGENTS.md) 和 [`code_review_checklist.md`](code_review_checklist.md)
  中写明：新测试不得 patch 门面的再导出名；外部边界（lark-cli、git、subprocess、时钟、网络）
  通过依赖参数注入。
  （2026-09-30，与 CQ-2.2 同一 PR）
- [x] **CQ-2.2 门面 patch 棘轮。** 在 guardrails 中统计测试对门面模块（`build_docs`、
  `process_build_queue`、`process_review_start_queue`、`cloud_doc_backport`）的 patch 次数，
  以当前值为基线，只减不增。
  （2026-09-30；`tools/check_facade_patch_ratchet.py` + `data/facade_patch_baseline.tsv`，已接入
  `check_maintainability_guardrails.py`。基线：7 个测试文件共 363 处，其中
  `test_process_build_queue.py` 203 处、`test_process_review_start_queue.py` 87 处；
  统计 `patch.object` / `patch.multiple`（按 import 别名解析）和 `patch("tools.<门面>.<名字>")`）
- [ ] **CQ-2.3 为队列处理器引入依赖对象。** 为 `process_build_queue` /
  `process_review_start_queue` 引入一个小的 `QueueDeps` dataclass（外部客户端、git 执行器、
  时钟），默认值为真实实现；按测试文件逐个迁移。每个 PR 迁一个测试文件，不改运行行为。
  - [x] 依赖对象骨架（#1362，2026-10-02）：`QueueDeps`（client factory、command runner、Git worktree
    prepare/remove）传入现有 session/build callback，review-start 接受已有 `ReviewStartRuntimeDeps`；
    默认值在调用时按门面名查找，运行行为不变。
  - [x] 时钟接缝（2026-10-02）：`process_queue_record_group` 增加 `clock` 参数（默认 `utc_now`），开始时间、认领到期和构建时间都取自它；`QueueDeps.clock` 可在单次运行中替换。核对后 `queue_claims.py`、`queue_bound_records.py`、`queue_session.py` 不读时钟，`queue_transitions` 已接受 `now=`
  - [ ] 按测试文件迁移门面 patch：
    - [x] `QueueDeps` 增加 11 个可选的单次运行覆盖项（会话预检、链接绑定、身份、快照同步、构建、产物目标、钉钉镜像、产物发布、云文档导入/收尾），`test_process_build_queue.py` 203 → 70、`test_process_build_queue_routing.py` 29 → 25，合计 363 → 226（2026-10-02，用脚本按 AST 机械改写，测试断言不变）
    - [x] `process_review_start_queue`：直接调用 `process_review_start_queue()` 的 9 个测试块改为传 `deps=replace(default_review_start_deps(), ...)`（已有 `ReviewStartRuntimeDeps`，8 个字段），87 → 21，合计 226 → 160（2026-10-02）
    - [x] `build_docs` 门面：`test_build_docs_review_compat.py` 改为直接调用 `build_docs_bundle.prepare_manual_bundle` 并显式传入协作者，只留 1 处检查门面自身转发的 patch，22 → 1，合计 160 → 139（2026-10-02）。`test_target_resolution.py` 的 6 处 patch 的是 `build_docs` 自己定义的函数，属于在查找处 patch，保留
    - [x] 内部再次查找的名字：`QueueDeps` 增加 `resolve_wiki_destination`、`upload_word_to_drive`、`move_drive_file_to_wiki`，设置后产物目标与发布两个服务改在 `FacadeOverrides`（替换了这些名字的门面）上运行；`build_document_for_task` 的测试改为直接调用 `queue_build_execution.build_document_for_task` 并显式传入协作者，发布与 wiki 目标的测试改为把 `FacadeOverrides` 作为 `module` 传给服务。`test_process_build_queue.py` 70 → 17，合计 139 → 86（2026-10-02）
    - [x] `test_process_build_queue_routing.py`：配置路径规则改为直接调用 `queue_config_resolution.resolve_config_path_for_task(repo_root=..., config_loader=...)`，不再 patch 门面的 `ROOT` / `load_config`；另加 1 个测试检查门面转发仓库根和加载器，25 → 3，合计 86 → 64，达到 ≤73 目标（2026-10-02）
    - [ ] 余下 64 处（目标 ≤73 已达成，可继续下调）：review-start 21、`test_process_build_queue.py` 17（`ROOT`、`_run_lark_cli_json` 等）、`test_web_publish_queue.py` 15、`test_target_resolution.py` 6（在查找处 patch，保留）、routing 3、其余 2
- [x] **CQ-2.4 删除无人使用的转发。** 某个 `*_impl` 转发或再导出在测试和代码中都没有引用时，
  将其删除，并把门面的公开名写入 `__all__`。先做 `tools/build_docs.py`，再做
  `tools/process_build_queue.py`。
  - [x] 2026-10-02：`build_docs.py` 删去 7 个无人引用的转发/别名（`render_csv_pages`、`_language_label`、
    `_effective_variants_for_current`、`_resolve_variant_target_page`、`_variant_key`、`_variant_priority` 及随之无用的导入），
    补 `__all__`（46 个公开名）；`process_build_queue.py` 删去 16 个无人引用的再导出（核对了函数内的延迟导入、`module.<名字>` 与
    `queue_dep(..., "<名字>")` 的动态查找核对），补 `__all__`（95 个公开名）。其余 `*_impl` 转发都在为测试或服务
    注入门面上的协作者，仍有引用，按本项规则保留；验收里“43 → 0”需要把这些注入改为显式依赖对象，留给后续。
- [x] **CQ-2.5 门面瘦身收尾。** 更新热点行数上限（只下调）和 `orchestration_module_map.md`。
  （2026-10-02：`build_docs.py` 上限 860 → 830，`process_build_queue.py` 650 → 565；模块图写明 `__all__` 与删除前的动态查找核对）

**验收。** `build_docs.py` 的 `*_impl` 转发从 43 个降到 0 个（保留的公开名全部列入 `__all__`）；
门面 patch 次数较基线下降 ≥80%；全量测试绿色。

### CQ-3 复杂度：加复杂度棘轮，按规则表重写头部校验函数

**问题。** 31 个函数 CC≥50，最高的 `_validate_composition_data` 达到 213。现有 guardrails
只限制文件行数：函数可以在文件总行数不变的情况下持续变复杂。

**目标。** 新函数 CC 不超过 20；存量函数只降不升；CC≥50 的函数减到 10 个以内。

- [x] **CQ-3.1 复杂度棘轮。** 用 CI 已安装的 ruff（`--select C901 --output-format json`，
  `max-complexity = 20`）生成基线文件，以 `文件 + 函数名 → 当前复杂度` 为键。guardrails
  拦截"新增超限函数"和"存量函数复杂度上升"；复杂度下降时要求在同一个 PR 里刷新基线。
  （#1318，2026-09-29；实现改用标准库 `ast` 计算，结果与 radon 一致，不依赖 ruff 的 JSON 输出，
  基线在 `data/complexity_baseline.tsv`，由 `check_maintainability_guardrails.py` 执行）
- [x] **CQ-3.2 头部校验函数改成规则表**（每个函数一个 PR，改之前先补特征测试，
  固定现有错误信息列表；改后错误文本逐字不变）：
  - [x] `tools/idml/target_assembly_plan.py::_validate_composition_data`（213）
    （2026-10-01；先提交特征测试 `tests/test_idml_composition_data_characterization.py`：从目标装配契约冻结 77 页
    composition_data，生成 8440 个确定性变异，按页哈希问题列表或异常；覆盖 328/337 条语句、90/92 处问题。
    再用脚本机械拆分：13 个按组件类型的校验函数 + `_COMPOSITION_VALIDATORS`（键集合 → 校验函数）分派表，
    问题文本逐字不变。主函数复杂度 213 → 12；拆出的 `specifications` 42、`lcd` 35、`app` 25 记入基线，待后续再拆）
  - [x] `tools/validate_config.py::validate`（138）（#1357，2026-10-01；按配置段拆分，文件内最高
    `_validate_sync` 42、`_validate_paths` 37）
  - [x] `tools/idml/reference_layout_plan.py::validate_approved_reference_plan`（107）（#1355，2026-10-01；
    文件内最高 `_validate_reference_pages` 28）
  - [x] `tools/config_pages.py::parse_config_pages`（87）（#1363、#1377，2026-10-01/02；文件内最高
    `_parse_generated_page` 27）
  - [x] `tools/manual_ir/validate.py::_payload_issues`（71）（#1361，2026-10-01；文件内最高
    `_validate_embedded_overview` 27）
- [x] **CQ-3.3 `main()` 拆成子命令处理函数。** `tools/lang_asset_sweep.py`（71）、
  `tools/bitable_schema.py`（71）、`tools/export_idml.py`（68）：按子命令拆成独立处理函数，
  参数解析保持不变。
  - [x] `lang_asset_sweep.py`（#1356，2026-10-01；`_cmd_sweep` 29）
  - [x] `bitable_schema.py`（#1360，2026-10-01；最高 `apply` 31）
  - [x] `export_idml.py`（2026-10-02）：`main` 只解析参数并分派 `_cmd_check` / `_cmd_flow` / `_cmd_reference`；正式导出的有状态单遍流程从嵌套闭包改为 `tools/idml/reference_export.py::ReferenceExport` 的方法（`render_page` 再拆为数据页、内容页、FCC/收货清单页、符号页、流式页几个方法，两处重复的安全符号页合并为一个方法），最高复杂度 68 → 19；`export_idml.py` 604 → 178 行，热点上限下调到 230
- [ ] **CQ-3.4 渲染与变换热点随改随降。** `transform_web_fragment`（93）、
  `structural_findings`（92）、`promote_reference_figures`（87）、
  `_parse_spec_master_sections`（85）、`extract_page`（81）：不单独立项；业务 PR 改到这些函数时，
  必须顺带降低复杂度（由 CQ-3.1 的棘轮保证不会升高）。
  - 2026-10-02 操作者确认改为主动清理（CC≥50 的函数 24 → ≤10，分批进行，每个函数用新旧实现的差分验证行为不变）：
    - [x] C 批（解析/加载）：`resolve_manifest_asset` 72 → 4、`load_web_document` 68 → 35、
      `ordered_pages` 59 → 36、`_extract_raw_latex` 75 → 28（宏到块改为规则表）

**验收。** CQ-3.1 在 CI 中生效；CC≥50 的函数从 31 个降到 ≤10 个；CQ-3.2 列出的 5 个函数都降到
≤40，特征测试全部通过。

### CQ-4 静态检查基线：先修真实缺陷，再分批加 lint 规则（优先级最高）

**问题。** ruff 只开了 3 条规则；存在文件句柄泄漏和循环闭包引用循环变量（`B023`）这类潜在缺陷；
`F401` 里有相当一部分是门面的有意再导出（`process_build_queue.py` 70、`diff_report.py` 25、
`csv_pages/renderers.py` 21），不能直接 `--fix`。

**目标。** CI 的 ruff 规则集包含 `F`（全部）、`B023`、`B904`、`PLW1510`；mypy 严格模式覆盖更多子包。

- [x] **CQ-4.1 修复 7 处未关闭的文件句柄**（改用 `with path.open(...) as fh:`）：
  - `tools/idml/loaders.py:48`、`:63`、`:103`、`:134`、`:261`
  - `tools/check_docs_lang_parity.py:84`
  - `tools/printed_url_inventory.py:89`

  验收：相关测试不再出现 `ResourceWarning`。（#1322，2026-09-29）
- [x] **CQ-4.2 逐个审查 26 处 `B023`**（`plain_markdown_site.py` 5、`diff_report_fields_rows.py` 5、
  `review_support.py` 4、`web_document_source.py` 2、`web_document_ir.py` 2、
  `readthedocs_source.py` 2、`publish_asset_pool.py` 2，另外 4 个文件各 1 处）。真实缺陷用默认参数
  绑定修复并补测试；确认无害的写明 `# noqa: B023` 和理由。完成后把 `B023` 加入 `select`。
  （#1322，2026-09-29；`tools/` 下 24 处逐个核对均为误报，已逐处注明理由；`tests/**` 按文件豁免 `B023`）
- [x] **CQ-4.3 处理 `F401`。** 门面的有意再导出改成显式形式（写入 `__all__`，或用
  `import x as x`）；其余用 `ruff --fix` 清理。完成后把整个 `F` 规则族加入 `select`。
  与 CQ-2.4 协调：两边都会碰门面文件，同一个门面只在一个 PR 里改。
  （#1322，2026-09-29；`tools/process_build_queue.py` 通过 `_service_module()` 被辅助模块在运行时
  读取，静态分析看不到，暂按文件豁免 `F401`，留到 CQ-2.4 删除转发时处理）
- [x] **CQ-4.4 小批量补齐高价值规则。** `B904`（4）、`PLW1510`（8，`subprocess.run` 显式传
  `check=`）；`B905`（45，给 `zip` 加 `strict=`）要先确认每处长度确实应该相等，再决定是否启用。
  每条规则要么清零后加入 `select`，要么用 `per-file-ignores` 记录基线后加入。
  - [x] `B904`、`PLW1510` 清零并加入 `select`（2026-09-30）。实际扫描范围含 `tests/`、`scripts/`，
    共 5 处 `B904`、39 处 `PLW1510`；所有调用都按原行为显式写 `check=False`（默认值不变，零行为变化）。
  - [x] `B905` 清零并加入 `select`（2026-10-02）：64 处逐一判断——长度在附近已校验或同源构造的 28 处改 `strict=True`；
    `zip(a, a[1:])` 的 5 处改 `itertools.pairwise`；外部数据（lark-cli 行可能短于字段表）、版式输入、源数据长度不保证的 31 处
    写 `strict=False` 并在上一行注明原因，保留原有截断行为。先前的计数棘轮随之删除。
- [x] **CQ-4.5 扩大 mypy 严格范围。** 在 `pyproject.toml` 为 `tools.manual_ir.*`、
  `tools.component_specs.*`、`tools.csv_pages.*` 逐个增加严格 override。**CI 命令目前固定为
  `python -m mypy tools/utils`，扩大检查路径需要改 workflow，须操作者确认。**
  - [x] 计数棘轮（2026-10-02，操作者确认改 workflow）：`tools/check_mypy_ratchet.py` +
    `data/mypy_untyped_baseline.tsv`，按文件统计三个子包内 `mypy --disallow-untyped-defs` 错误（不计导入的
    包外文件；`--no-site-packages`，本地结果与 CI 一致），在 `type-check` job 运行，mypy 锁定 2.3.1。
    基线 22 个文件 68 处（manual_ir 29、component_specs 18、csv_pages 21）。本轮业务合入曾使错误回升，#1375、#1379 修回。
  - [x] 三个子包清零（68 → 0，2026-10-02）：只补注解、`cast`、改名消除变量复用，`component_specs` 各 `parse_*_html` 的组件返回类型由 `object` 收紧为 `ComponentSpec`，无运行行为变化；`pyproject.toml` 为三个子包加 `disallow_untyped_defs` override，基线清空后由 mypy 棘轮在 CI `type-check` job 保持为 0

**验收。** `pyproject.toml` 的 ruff `select` 至少包含 `E722, F, B023, B904, PLW1510`；CI 绿色；
测试输出中没有 `ResourceWarning`；mypy 严格模式覆盖 ≥4 个子包。

### CQ-5 可观测性与编排契约

**问题。** 594 处 `print` 和 2 个使用 `logging` 的文件，意味着无人值守的队列/发布运行只能靠
stdout 前缀排查问题；75 处 `except Exception` 的处理方式各不相同；`build.py` 通过手工拼接命令行
参数、用子进程调用 `tools/*.py`，两边的参数契约只在运行时才会暴露错误。

**目标。** 输出格式不变，但能按级别过滤、能统一重定向；每处宽泛的异常捕获都有明确分类；
`build.py` 构造的每条子命令都有测试证明被调用脚本能解析。

- [x] **CQ-5.1 引入日志工具模块。** 新增 `tools/utils/log.py`，对 `logging` 做一层很薄的封装，
  沿用现有的 `[prefix] LEVEL message` 格式（现有依赖 stdout 断言的测试保持通过）；
  支持通过 `AUTO_MANUAL_LOG_LEVEL` 设置级别。纳入 mypy 严格范围（`tools.utils.*`）。
  （#1330，2026-09-30；消息原样输出，级别和输出流由调用处选择：`get_logger(name)` 写 stdout，
  `get_logger(name, stream="stderr")` 对应原来的 `print(..., file=sys.stderr)`；输出流在写入时才查找，
  `redirect_stdout` 照常捕获）
- [x] **CQ-5.2 先迁移无人值守路径。** `process_build_queue`、`queue_*`、`cloud_doc_backport_*`
  的 `print` 改用 `log`；每个 PR 迁一族，输出文本逐字不变。
  进度：review-start 队列（`process_review_start_queue*.py`，12 处；2 处转发 git 原始输出的保留 `print`）
  随 CQ-5.1 一起迁移（#1330）。
  构建队列（`process_build_queue_main.py`、`process_build_queue_services.py`、`queue_*.py`，
  10 个文件 28 处，组件名 `build-queue`，#1334，2026-09-30）；保留 `print` 的：转发子进程原始输出的 2 处、
  写入调用方注入的 `stderr` 参数的 5 处、经门面 `module.sys.stderr` 输出的 1 处。
  随后修正：命令结果（`queue query` / `queue execute` / `queue resolve-action` 的行、报告或
  `--json` 输出）不是日志，改回 `print`（#1335），否则把 `AUTO_MANUAL_LOG_LEVEL` 调到 `WARNING` 以上会吞掉结果。
  迁移规则：只迁移进度/诊断行，命令结果和转发的子进程输出保留 `print`。
  回写（`cloud_doc_backport_commands.py`、`cloud_doc_backport_orchestration.py`，组件名
  `cloud-doc-backport`，#1337，2026-09-30）：只迁移 stderr 上的 21 处诊断行（报错、GATE FAIL、跳过提示）；
  stdout 上的 `WROTE`/`BRANCH`/`APPLIED`/JSON 汇总是命令结果，PR 创建失败时的手工操作指引
  （`PR_CREATE_FAILED`…`PR_BODY`）也是结果，均保留 `print`。
  其余 `tools/` 的 stderr 诊断行（2026-10-02）：25 个文件 46 处 `print(<字面量>, file=sys.stderr)` 改为
  `get_logger(<前缀>, stream="stderr")`，文本逐字不变；含 WARN 的用 `warning`，沙箱写入提示用 `info`，其余报错用 `error`。
  保留 `print` 的：回写的 `COMPARE`/`PR_TITLE`/`PR_BODY` 手工指引、`flow_dashboard` 的 `WROTE` 路径（命令结果），
  转发子进程输出或多参数的调用、`scripts/` 下的钩子与接收器，可直接 `python tools/<x>.py` 运行、不依赖 `tools` 包的 9 个独立脚本（加入 `tools.utils.log` 导入会让它们在 CI 里找不到包），以及 `spec_master_rebuild.py` 的 1 处（迁移会超出热点行数上限）。
  stdout 上其余约 500 处 `print` 绝大多数是命令结果（报告、JSON、路径），按上面的规则不迁移。
- [x] **CQ-5.3 审计 75 处 `except Exception`。** 分三类：顶层边界（保留，改成 `log.exception`
  以保留堆栈）、可收窄（改成具体异常类型）、吞掉错误（改为重新抛出或记录后报错）。
  在 guardrails 中加计数棘轮，只减不增。
  - [x] 计数棘轮（2026-10-01；`tools/check_broad_except_ratchet.py` + `data/broad_except_baseline.tsv`，
    已接入 `check_maintainability_guardrails.py`；扫描 `build.py`、`tools/`、`scripts/`、`integrations/`，
    基线 56 个文件 89 处，含 `except BaseException` 与包含二者的元组）
  - [x] 逐族审计分类（顶层边界 / 可收窄 / 吞掉错误）
    - [x] `csv_pages`（#1358，2026-10-01；89 → 86）
    - [x] 其余 86 处一次审完（2026-10-02）：棘轮不再计入已审计的处理器——函数体以 `raise` 结尾（清理后重抛或包装后重抛，27 处），或 `except` 行带 `# noqa: BLE001 - <理由>`（CLI 入口、逐行批处理、尽力而为的旁路、诊断探针，51 处，含原有 6 处）；8 处收窄为具体异常（`build_dispatch`、`build_doctor` 格式化、`flow_dashboard` / `toolchain_provenance` / `derived_surface_push_check` 的子进程、`plistlib`、`validate_layout_params` 两处数值解析）。基线 86 → 0，此后任何未审计的宽泛处理器都会使门禁失败
- [x] **CQ-5.4 子进程命令契约测试。** 对 `build.py` 中每个 `*_command(args) -> list[str]` 构造器，
  增加一个测试：把生成的参数列表交给目标脚本的 `parse_args` 解析，必须成功。不改任何公开 CLI 参数。
  （2026-09-30；`tests/test_build_command_contracts.py`：13 个构造器、35 组参数组合，Python 子命令交给
  目标脚本的 `parse_args`，`listen-message-control` 交给 Node 的 `parseLocalListenerArgs`；另有一条覆盖检查，
  `build.py` 新增 `*_command` 而没有契约用例时失败）

**验收。** 队列与回写路径 `print` 清零；`except Exception` 数量下降 ≥50%，其余全部带分类注释；
CQ-5.4 的测试覆盖 `build.py` 里所有子进程命令构造器。

### CQ-6 测试反馈：更快、对环境不敏感

**问题。** 全量测试单进程约 11 分钟；环境与 lock 文件不一致时，会以 17 个分散的失败形式暴露，
而不是给出一条明确的环境提示。已观察到的原因：Python 3.11 与要求的 3.12 不一致；缺少 `jinja2`；
PyMuPDF 1.28.2 与配方要求的 1.28.0 不一致；一个黄金文件中的几何浮点数对比。

**目标。** 环境不符时先给出一条清晰的诊断；本地有一个 3 分钟以内的快速测试层；CI 仍然跑全量。

- [x] **CQ-6.1 环境预检。** 在 `build.py doctor`（[`../../tools/build_doctor.py`](../../tools/build_doctor.py)）
  中增加检查：Python 版本，以及 `requirements.lock` 中对精确版本敏感的包（PyMuPDF 等）。
  每次 `python -m unittest` 开始时（`tests/__init__.py`）打印同一份检查的 `WARN` 行，
  先说明环境差异，再出现那批分散的失败；环境与 CI 一致时不输出，`AUTO_MANUAL_ENV_PREFLIGHT=0`
  可关闭。原计划在 `setUpModule` 里报一条环境错误，但那样会把同一模块里本可通过的测试也变成
  错误，所以改为开头提示，不改变任何测试结果。**CI 中这类测试照常执行，不允许用 skip 让测试变绿。**
  （doctor 与独立命令：#1319，2026-09-29；测试开头提示：#1329，2026-09-30）
- [x] **CQ-6.2 开发环境安装脚本。** 新增 `scripts/setup_dev_env.sh` / `.ps1`：检查 Python 3.12，
  并从 `requirements.lock` 安装依赖；在 [`../../ONBOARDING.md`](../../ONBOARDING.md) 加入这一步。
  （#1344，2026-09-30；Python 版本读自 `pyproject.toml` 的 pin，装完跑新增的 `tools/env_preflight.py --strict`，
  有任何 `WARN` 即退出码 1。在本容器实测：Python 3.12 + lock 的新 `.venv` 报告全部 `OK`）
- [x] **CQ-6.3 测试分层。** 给需要真实 Sphinx 子进程、IDML 黄金对比的慢测试加标记
  （例如统一的 `slow` 基类或装饰器）；新增 `make test-fast`，本地只跑快速层。CI 的全量
  `python -m unittest` 不变。
  （2026-09-30；按模块而不是逐个测试标记：`tests/slow_modules.txt` 列出 27 个实测慢测试合计 ≥4s 的模块，
  `python -m tests.run_fast`（`make test-fast`）把其余模块分批放到并行进程里跑，只用标准库。
  实测（4 CPU，Python 3.12 + lock）：单进程全量 879s；并行全量 251s；快速层 4435 个测试 171s）
- [ ] **CQ-6.4 并行执行。** 评估两种方案：`pytest` + `pytest-xdist`（兼容 unittest 写法，
  但属于新增依赖，**需操作者确认**），或按模块在 CI 中分片（改 workflow，**需操作者确认**）。
  先用数据说明收益，再决定。
- [x] **CQ-6.5 黄金文件浮点数稳定化。** 几何类黄金对比改为按固定精度取整或给出容差
  （先处理 `tests.test_idml_symbols_panel` 的三语言视觉契约）。
  （2026-10-01；根因是 Python 3.12 的 `sum()` 改为补偿求和，同一布局在 3.11 得 `117.89999999999999`、
  3.12 得 `117.9`。两个符号面板黄金对比改为比较前把浮点数取整到 6 位小数，黄金文件不变；3.11 与 3.12 均通过。
  其余环境类失败（缺 `jinja2`、PyMuPDF 版本）由 CQ-6.2 的安装脚本解决，不是浮点问题）

**验收。** 环境不符时 `build.py doctor` 给出单条明确诊断；`make test-fast` 在本地 ≤3 分钟；
CI 全量测试时长下降 ≥40%（若采纳 CQ-6.4）。

### CQ-7 文档治理：生命周期标记、归档、控制入口文档体积

**问题。** `code-as-doc/dev/` 有 86 篇、`reviews/` 有约 80 篇带日期的调研和计划文档，很多没有
状态标记，读者分不清哪些仍然有效；`optimization_project.md` 已有 964 行；`AGENTS.md` §7 的技能
清单很长，每个 AI 会话都要把它读进上下文。

**目标。** 每篇计划/调研文档都有状态；已完成的文档可以一眼识别；入口文档保持精简。

- [x] **CQ-7.1 生命周期约定。** 在 [`../code-as-doc.md`](../code-as-doc.md) 中规定：`dev/` 与
  `reviews/` 下的计划/调研文档首部必须有
  `Status: proposed | active | done | archived | superseded-by <link>`。（#1320，2026-09-29）
- [x] **CQ-7.2 状态检查棘轮。** 扩展 [`../../tools/check_doc_link_integrity.py`](../../tools/check_doc_link_integrity.py)
  或新增一个检查：以当前缺少状态行的文档为基线，新文档必须带状态行。
  （#1320，2026-09-29；评审中收紧：`superseded-by` 必须带替代文档的链接）
- [x] **CQ-7.3 补状态并建索引。** 为存量文档补状态行，在 [`../README.md`](../README.md) §5 列出已归档
  文档。第一步只标状态、不移动文件；如需移动到 `code-as-doc/archive/`，**另开 PR 并经操作者确认**
  （由链接检查保证没有断链）。
  - [x] 补状态行：`reviews/`（#1354）、`dev/`（#1359），基线 174 → 5（2026-10-01）
  - [x] 剩余 5 篇（2026-10-02），基线清空；`../README.md` §5 已列出全部标为 archived 的文档
- [x] **CQ-7.4 刷新边界文档。** 更新 `code_style_guide.md` §2 与 `orchestration_module_map.md`
  （与 CQ-1.1 同一个 PR）。（#1331，2026-09-30；同时补登 phase 1 新增的三个辅助模块）
- [x] **CQ-7.5 精简路线图。** 把 `optimization_project.md` §4 "Recently Completed" 迁到
  [`../code_optimization_log.md`](../code_optimization_log.md)，§4 只保留指针；目标 ≤600 行。
  （2026-10-02：§4 与 12 个已完成工作流 A–H、J、R、W、X 原文移入日志"Archived roadmap sections"一节，994 → 572 行）
- [x] **CQ-7.6 精简 `AGENTS.md` §7。** 把每个技能的长描述移到技能索引，§7 只保留一行名称和
  触发条件。**修改 `AGENTS.md` 需要走 `config-review` 技能，并经操作者确认。**（#1321，2026-09-29）

**验收。** `dev/` 与 `reviews/` 下的文档 100% 带状态行，并由 CI 检查；`optimization_project.md`
≤600 行；`AGENTS.md` 的行数下降，且原有规则一条不少。

## 3. 推荐执行顺序

每一阶段内部的条目互不依赖，可以并行开 PR；阶段之间按顺序推进。

1. **第一阶段：低成本、零行为风险。** CQ-4.1 → CQ-4.2 → CQ-4.3、CQ-3.1、CQ-6.1、CQ-7.1/7.2、
   CQ-1.1/CQ-7.4。
2. **第二阶段：建立接缝。** CQ-2.1–2.3、CQ-5.1–5.4、CQ-3.2、CQ-6.2/6.3/6.5、CQ-4.4。
3. **第三阶段：结构迁移（需确认）。** CQ-2.4/2.5 → CQ-1.2–1.5、CQ-4.5、CQ-6.4、CQ-7.3/7.5/7.6。

## 4. 更新规则

- 开始一项：在对应 PR 描述中写明条目 ID（例如 `CQ-4.1`）。
- 完成一项：在本文件勾选，并在条目后追加 `（#PR，YYYY-MM-DD）`。
- 基线数字只在"复测"时整体刷新，并写明刷新日期和 commit，不做零散修改。
- 一个 CQ 分项全部完成后，在 [`../code_optimization_log.md`](../code_optimization_log.md)
  追加维护记录（AGENTS.md §5）；7 项全部完成后，把 Workstream Y 标记为 done。
