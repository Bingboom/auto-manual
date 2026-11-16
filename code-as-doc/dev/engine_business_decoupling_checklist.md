# auto-manual 引擎与型号业务数据解耦清单

Status: proposed · Owner: 夏冰 · Created: 2026-11-16

- 本文是**提案草稿**，尚未开始执行。执行状态不记在本文里，要先登记台账行；登记在哪份台账尚未决定（§7 第 7 项），候选是[执行台账](manual_revitalization_execution.md)的 REV 行或[优化路线图](../optimization_project.md)。目前**没有登记任何行**。
- 来源：操作者 2026-11-16 在飞书写的《auto-manual 引擎与硬件型号业务记录彻底解耦重构清单》（四个阶段、17 项）。本文把它收进仓库，并按下面的审查结果修订。
- 核对基线：main `66709a9f`。
- 方法：2026-11-16 对 main 做只读核对（`git ls-tree`、读代码与工作流），未运行任何构建或测试；另外参考了 [PR #1724](https://github.com/Bingboom/auto-manual/pull/1724)（阶段一的首个实现，未合入）的审查与原型实验。
- 本文只写清单本身。不改代码、数据、配置、测试或工作流；下文每一项都要单独开 PR 执行。

## 1. 为什么做

**根因（来自原清单）。** 跨仓单向同步 [`sync-hello-docs.yml`](../../.github/workflows/sync-hello-docs.yml) 每次都会用 auto-manual 的内容覆盖镜像仓中 keep 路径以外的一切。Hello-Docs 只保护 `docs/publish`、`docs/knowledge`，Hello-Docs-Review 只保护 `docs/review-drafts`。为了不被冲掉，真实型号的冻结源包、资产注册表、区域配置和审校追踪文件只能提交到公开的工程仓。

**规模（main `66709a9f`）。**

| 范围 | 文件数 | 体积 |
| --- | ---: | ---: |
| 全仓（已跟踪） | 41,466 | 约 5.40 GB |
| 引擎代码（`build.py`、`tools`、`integrations`、`scripts`） | 960 | 约 9.5 MB |
| 原清单矩阵点名的路径 | 29,477（71.1%） | 约 3.12 GB |
| 矩阵遗漏的业务耦合路径 | 约 8,270（19.9%） | 约 2.15 GB |

**三个仓库的角色。** 见 [Hello_Docs_Positioning.md](../architecture/Hello_Docs_Positioning.md) §1.1 与 [two_plane_map.md](../../user-guide/two_plane_map.md)：auto-manual 是工程面（引擎、模板、工具），Hello-Docs 是业务面（发布与业务数据），Hello-Docs-Review 是私有资料开发工作台（审核稿）。解耦的目标是让工程仓只留引擎和脱敏样例，型号业务数据各归其位。

## 2. 原则

1. **任何时刻每条路径只有一个写入方。** 迁移期内由 auto-manual 写的路径，镜像里不改；切换后由镜像写的路径，auto-manual 不再出现。
2. **下游副本和它的检查到位之前，上游不删。** 删除依赖的 CI、测试、语料来源都要先在接收仓跑通。
3. **删除之前的步骤一律无损。** 只加保护、加接口、加夹具、加检查，不移走任何业务文件。
4. **移动文件不会把它从历史里去掉。** 文件从 main 删除后，仍在 auto-manual 的 git 历史中可见。是否改写历史是另一项决定（见 §7），本清单不默认执行。

## 3. 归属矩阵

“审查”列标 ✚ 的行是原清单遗漏、由审查补上的；标 ✎ 的行是原清单已有但事实或处置被修订的。✚ 行的“归属”是审查的建议，尚未经操作者确认（§7 第 8 项）。

| 路径 | 现状（main `66709a9f`） | 归属 | 说明 | 审查 |
| --- | --- | --- | --- | :---: |
| [`manual_sources/`](../../manual_sources) | 28,989 个文件，73 个型号目录加 `shared/` | Hello-Docs | 冻结源包；Hello-Docs-Review 把它当语料读 | ✎ |
| [`data/manual_sources/`](../../data/manual_sources) | 5,949 个文件 | Hello-Docs | 第二个冻结包根目录，[`frozen_package_registry.py`](../../tools/web/frozen_package_registry.py) 也扫描它 | ✚ |
| [`data/`](../../data) 业务表 | 冻结包注册表、型号能力/语言、产品信息、资产注册与来源、型号专用版式参数、标签来源、[`data/phase2/`](../../data/phase2) | Hello-Docs | 具体子路径与下游位置待定（§7） | ✎ |
| [`data/`](../../data) 代码质量基线 | 7 个文件：broad_except、complexity、top_level_module、facade_patch、mypy_untyped、language_literal、doc_lifecycle | auto-manual | 由各自 `tools/check_*_ratchet.py` 与 [`check_doc_lifecycle.py`](../../tools/check_doc_lifecycle.py) 的 `DEFAULT_BASELINE` 读取，不是 [`check_maintainability_guardrails.py`](../../tools/check_maintainability_guardrails.py) | ✎ |
| [`data/asset_recipes/`](../../data/asset_recipes)、[`asset_evidence/`](../../data/asset_evidence)、[`asset_promotions/`](../../data/asset_promotions) | 80 / 10 / 2 个文件 | Hello-Docs | 型号资产配方、证据与推广记录 | ✚ |
| [`configs/`](../../configs) | 31 个 `config.*.yaml`，30 个点名真实型号，14 个设置 `default_model`；[`config-bases/`](../../configs/config-bases) 为通用基类 | 分层 | 基类与 demo 留工程面；型号实例下沉。`configs/profiles`、`configs/targets` 目前不存在 | ✎ |
| [`bitable_schema/`](../../bitable_schema) | 5 个文件；`business_base_manifest.json` 是字段结构但绑定具体业务实例；[`seed/`](../../bitable_schema/seed) 是一个小 CSV | 分层 | 纯字段契约留工程面，实例绑定与种子下沉 | ✎ |
| [`reports/`](../../reports) | 434 个文件；`reports/releases` 未跟踪 | Hello-Docs | 型号审计与版本追踪 | ✎ |
| [`review_sync_json/`](../../review_sync_json)（2 个文件）与 [`review_sync_out.txt`](../../review_sync_out.txt) | CI 作业的临时输出，误提交 | 无 | 无需迁移：删除并写入 `.gitignore` | ✎ |
| [`site/`](../../site) | 2 个文件（README 与一个 CSV） | 待定 | 原清单前后矛盾（§7） | ✎ |
| [`Makefile`](../../Makefile) | 只设 `CONFIG ?= configs/config.us.yaml`，没有 `--data-root` | auto-manual | 默认改指 demo | ✎ |
| [`feishu-build-queue.yml`](../../.github/workflows/feishu-build-queue.yml) | 默认 config 与 data-root 指向真实数据 | auto-manual | 改为变量注入 | |
| [`tools/`](../../tools) 门户与 UI 推广 | [`app_ui_promotion.py`](../../tools/app_ui_promotion.py) 有型号特判；[`tools/rtd_portal_assets/`](../../tools/rtd_portal_assets) 含 16 个快照文件 | auto-manual | 特判改为读业务面声明表；快照随数据下沉 | ✎ |
| [`config.toml`](../../config.toml) | 本地 CLI 参数，无业务内容 | 本地 | 可改为 `config.toml.example` | |
| [`docs/_build/`](../../docs/_build) | 234 个已跟踪的构建产物 | 无 / Hello-Docs | 生成物；先确认是否有人依赖再处置 | ✚ |
| [`docs/renderers/web/assets/`](../../docs/renderers/web/assets) | `shared/` 之外 986 个型号文件，另有 64 个 `*_illustrations.json` | Hello-Docs | 冻结包钉住这些文件，须与冻结包同批迁移 | ✚ |
| [`docs/_review/`](../../docs/_review) | 241 个文件 | Hello-Docs | 审校派生物；删除/改名须操作者确认（AGENTS.md §8.7） | ✚ |
| [`docs/manifests/`](../../docs/manifests) | 132 个文件 | Hello-Docs | 型号清单 | ✚ |
| [`docs/templates/targets/`](../../docs/templates/targets) | 41 个文件 | Hello-Docs | 型号目标模板 | ✚ |
| [`target_assembly/`](../../docs/renderers/contracts/target_assembly)、[`reference_layout/`](../../docs/renderers/contracts/reference_layout) | 4 个 / 1 个文件 | Hello-Docs | 后者受 reference-layout-pins CI 作业把关 | ✚ |
| [`target_overlays.json`](../../docs/renderers/contracts/web_presentation/target_overlays.json) | 型号登记表 | 分层 | 现有字面量护栏读取它，须先给护栏换数据源 | ✚ |
| [`code-as-doc/reviews/`](../reviews) | 526 个文件，458 个以型号命名 | 待定 | 审查记录；与历史决定一并处理 | ✚ |
| [合并授权登记](merge_authorizations.md)与[归档](merge_authorizations_archive.md) | 条目涉及具体型号的 PR | 待定 | 流程文件留工程面；已有条目与历史决定一并处理 | ✚ |
| [`tests/`](../../tests) | 108 个以真实型号/区域命名的测试模块；116 个测试读取 `manual_sources`；真实型号夹具（[`tests/fixtures/phase2`](../../tests/fixtures/phase2)、[`idml_golden`](../../tests/fixtures/idml_golden)） | 分层 | 引擎测试改用合成夹具；型号测试随数据迁到业务仓 CI | ✚ |
| 工作流与 AGENTS.md 验证命令 | 默认指向真实型号 | auto-manual | 改指 demo（阶段四） | ✚ |

## 4. 四个阶段

### 阶段一：改造跨仓同步边界（前置安全垫）

原清单各项：

1. 扩充 Hello-Docs 的镜像保留路径，加入 `manual_sources`、`data`、`configs/targets`、`reports`、`bitable_schema/business`、`site`。
2. 扩充 Hello-Docs-Review 的保留路径，加入 `review_sync_json`、`site/review-preview`。
3. 同步更新 [`mirrors/`](../../mirrors) 下两份 README，列出工程面只读目录与业务面自治目录。
4. 给 [`scripts/sync_mirror.sh`](../../scripts/sync_mirror.sh) 加 `--dry-run` 并补单元测试，验证上游删除某子目录时下游完好。

审查后的修订：

- **keep 语义不适合迁移期。** 实验确认：把 `manual_sources`、`reports` 列为 keep 路径后，镜像副本整体胜出；从合并起，auto-manual 在这些路径下新增的内容都到不了 Hello-Docs，而 auto-manual 此时仍是唯一写入方。keep 路径的实际行为是"首次写入胜出，之后冻结"。
- **改用 overlay（叠加）路径。** 单独设一张过渡期 overlay 列表，语义为文件级并集、源仓胜出：上游新增和修改照常传播；只在镜像存在的文件保留；上游删除不删下游。严格的"镜像胜出"只留给 auto-manual 从不写的路径（`docs/publish`、`docs/knowledge`、`docs/review-drafts`）。原型已用临时 git 仓验证（21 个测试）。
- **建议列表。** overlay（两个镜像相同）= `manual_sources`、`reports`、`data/business`、`configs/targets`、`bitable_schema/business`、`site/review-preview`；源仓禁入列表 = 严格 keep 路径，不变。`review_sync_json` 不进任何列表（误提交物，见阶段二）。
- **切换方式。** 整条路径 P 的切换是一个 auto-manual PR：删除 P，把 P 从 overlay 移到 keep，加入禁入列表和 [`MIRROR_OWNED_PATHS`](../../tools/check_maintainability_guardrails.py)。子目录的切换只需在上游删除它；但子目录切换后默认没有防回流检查，若它被重新加回上游会覆盖下游副本，整条路径切换后才由禁入列表拦住。
- **已知代价。** 上游删除的文件会留在下游，直到在下游手动删除；某文件仍在上游时，镜像里对它的修改会被覆盖——所以每条路径同一时刻只能有一个写入方。
- **空跑要求。** 合并前后各做一次同步空跑，比较下游文件清单，证明没有下游删除。
- 第 1 项中的 `data` 改为 `data/business`（或 §7 决定的具体子路径），不保护整个 `data/`，因为基线文件留在工程面。

### 阶段二：拆分混合目录、下沉业务资产

原清单各项：

1. 把代码质量基线迁入 `tools/guardrails/baselines/` 并更新读取常量。
2. 新建 `examples/demo_product/` 合成夹具：虚构型号 `DEMO-100`，双语种、基础参数 CSV、最小 RST 模板、样例图标、冻结包结构；虚构品牌主体与保留域名 `example.com` 的联系方式。
3. 确认 Hello-Docs 完整持有冻结源包与业务注册表后，从 auto-manual 删除这些文件，只留 Schema 校验定义。
4. 拆分 [`bitable_schema/`](../../bitable_schema)：留纯字段契约，实例清单、TM 清单、种子迁到 Hello-Docs，并复查 [`.gitleaks.toml`](../../.gitleaks.toml) 中不再需要的豁免项。
5. 清理报告与审校残留：`reports` 迁 Hello-Docs，`review_sync_json` 与 `site` 预览清单迁 Hello-Docs-Review，删除 `review_sync_out.txt` 并写入 `.gitignore`。

审查后的修订：

- **分两部分。** 无损准备（可以现在开始）：第 1、2 项，第 4 项的拆分设计，第 5 项中删除误提交物。删除（有前提）：第 3 项、第 4 项的迁移、第 5 项中 `reports` 与 `site` 的迁移。
- **第 1 项**：基线共 7 个，读取方是 6 个 `tools/check_*_ratchet.py` 与 `check_doc_lifecycle.py` 的 `DEFAULT_BASELINE`，不是 `check_maintainability_guardrails.py`。`tools/guardrails/` 目前不存在。
- **第 3 项范围补全**：还包括 `data/manual_sources`、`docs/renderers/web/assets` 中被钉住的型号文件、`data/asset_*`、`docs/manifests`、`docs/templates/targets`、`target_assembly`、`reference_layout` 等矩阵新增行。
- **第 5 项**：`review_sync_json/` 与 `review_sync_out.txt` 无需迁移，直接删除并 gitignore。
- **任何删除之前必须先落地的前提：**
  1. 工作区根接口（阶段三第 2 项），引擎能从外部仓读数据。
  2. 业务仓有 PR 触发的 CI，承接冻结包注册表检查、钉住漂移检查和型号测试。目前两个镜像都没有 PR 触发的验证（[`manual-validation.yml`](../../.github/workflows/manual-validation.yml) 及同类作业只在 auto-manual 运行）。
  3. 合成夹具（本阶段第 2 项）就位，且 manual-validation 已改指它（阶段四第 4 项）。否则删掉 `manual_sources` 或 `data/frozen_package_registry.json` 会打断护栏作业、大部分相关测试、asset-check 和钉住检查。
  4. Hello-Docs-Review 有稳定的语料来源（审核稿和 manual-review-draft 技能读取冻结包）。
  5. 切换当次同步修改发布路由：现在新 Web 说明书先提交到 auto-manual（包与注册表同一 PR），再向 Hello-Docs 开只含 `docs/publish` 的 PR（[input-paths.md](web_publish_pipeline/input-paths.md) §2.2、[two_plane_map.md](../../user-guide/two_plane_map.md)、AGENTS.md §8.5）。

### 阶段三：配置分层与工作区接口

原清单各项：

1. 两层配置：`config-bases/` 升级为纯引擎 profile；`default_model`、`targets`、品牌与联系方式替换项剥离到 Hello-Docs 的 `configs/targets/`。
2. 给 [`build.py`](../../build.py) 与 [`build_execution.py`](../../tools/build_queue/build_execution.py) 加 `--workspace-root`（或环境变量 `AUTO_MANUAL_WORKSPACE_ROOT`），统一指向外部业务仓的数据、源包和配置目录。
3. `Makefile` 默认改指 demo 配置，README 快速开始改用 `DEMO-100`；构建队列工作流改读仓库变量。
4. 门户与 UI 推广模块的型号特判改为读业务面的产品信息表与 `model_aliases.yaml`。

审查后的修订：

- 第 2 项是阶段二所有删除的前提，应最先开始。路径解析须遵守 AGENTS.md §3：落在 [`build_paths.py`](../../tools/build_paths.py)，路径段由 `path_utils` 构造，不另建平行模块。
- 第 1 项：`configs/profiles`、`configs/targets` 目前都不存在；31 个配置中 14 个设 `default_model`，迁移时逐个列清单。
- 第 3 项：`Makefile` 现在只有 `CONFIG`，没有 `--data-root`；README 改动须符合 AGENTS.md §5 的 README 规则。
- 第 4 项：`model_aliases.yaml` 目前不存在，需要先定义格式；`tools/rtd_portal_assets` 中 16 个快照文件随数据下沉。

### 阶段四：防回流护栏与发布契约

原清单各项：

1. 扩充源仓禁入路径：在同步工作流的 `SOURCE_FORBIDDEN_PATHS` 和本地钩子中加入 `manual_sources`、`reports`、`review_sync_json`、`configs/targets`、`review_sync_out.txt`。
2. 在可维护性护栏中新增型号与品牌字面量扫描，只允许 `DEMO-*` 出现在 `examples/` 与 `tests/`，设为必过门禁。
3. 在 `AGENTS.md` / `CLAUDE.md` 写入路由规则：型号业务任务不在 auto-manual 开分支，转到 Hello-Docs 或 Hello-Docs-Review。
4. manual-validation 的端到端构建全部改指 `examples/demo_product/`；[`pyproject.toml`](../../pyproject.toml) 补版本元数据，改用带 SemVer 的引擎 Release 触发下游升级。

审查后的修订：

- 第 1 项：[`.githooks/`](../../.githooks) 目前**没有**禁入路径列表。PR 时的检查是 `check_maintainability_guardrails.py` 的 `MIRROR_OWNED_PATHS`；禁入列表与 `MIRROR_OWNED_PATHS` 必须一起扩充（见阶段一的切换方式），是否另加钩子另议。路径按切换逐条加入，不一次全加。
- 第 2 项：字面量护栏已经存在（`collect_web_target_literal_failures`，读 `target_overlays.json`）。应扩展它而不是另建；`target_overlays.json` 下沉后要给它换数据源。可沿用 ratchet 基线方式逐步收紧，避免一次性阻断。
- 第 3 项：修改 `AGENTS.md` / `CLAUDE.md` 需走 config-review（AGENTS.md §7）。
- 第 4 项：是阶段二删除的前提（前提 3），应与夹具同时推进，不必等到最后。

## 5. 执行顺序

1. **现在即可并行开始（全部无损）：** 阶段一 overlay 改造与空跑；阶段二第 1 项（基线迁移）、第 2 项（合成夹具）、删除误提交物；阶段三第 2 项（工作区根接口）；阶段四第 2 项（扩展字面量护栏，先以基线模式）。
2. 夹具就位后：阶段四第 4 项（manual-validation 改指 demo）、阶段三第 3 项（默认配置）。
3. 业务仓 PR 触发 CI 建好（承接冻结包注册表、钉住漂移和型号测试）后，且 Hello-Docs-Review 语料来源确定后：才可做阶段二的删除，按路径逐条切换。
4. 每条路径切换的同一 PR：删除上游、overlay→keep、加入禁入列表与 `MIRROR_OWNED_PATHS`、修改发布路由文档。
5. 全部切换后：阶段三第 1、4 项收尾；阶段四第 3 项（Agent 路由规则）；引擎版本发布制。

## 6. 验收与回滚

本节由审查补充，原清单没有；具体门槛待操作者确认。

| 阶段 | 验收（可检查） | 回滚 |
| --- | --- | --- |
| 一 | 合并前后的同步空跑均无下游删除；auto-manual 在 overlay 路径新增的文件出现在镜像；镜像独有文件保留；Web 发布流程不变 | revert 工作流列表改动 |
| 二（准备） | 基线迁移后各 ratchet 检查与 `check_doc_link_integrity` 通过；合成夹具能独立跑通 doctor/check | revert 对应 PR |
| 二（删除） | 被删路径在业务仓存在且其 CI 通过；auto-manual 的 manual-validation 全绿；同步后镜像副本完整 | 在 auto-manual revert 切换 PR（恢复上游副本，路径回到 overlay）。下游副本没有被删；但镜像若已在该路径下有新提交，须先把这些改动带回上游，否则下次同步会被上游旧副本覆盖 |
| 三 | `--workspace-root` 指向外部目录时构建结果与仓内路径一致；`configs/` 中无 `default_model` 指向真实型号 | revert；旧的仓内相对路径保留为默认回退直到全部切换 |
| 四 | 字面量护栏在 `tools/`、`build.py`、`configs/`、`integrations/` 中无未豁免命中；manual-validation 在零业务数据下全绿；禁入路径出现时 PR 失败 | revert 护栏或把命中加入基线 |

## 7. 待操作者决定

1. `data/` 下哪些子路径算业务数据，下游放在 `data/business` 还是保持现有位置。
2. `site` 归 Hello-Docs 还是 Hello-Docs-Review，或改为 CI 构建期产物。
3. 是否在上游直接删除 `review_sync_json/` 与 `review_sync_out.txt`。
4. Hello-Docs-Review 是否保留一份冻结包副本作为语料，还是从 Hello-Docs 读。
5. 业务面 PR 的 CI 放在哪里（Hello-Docs 自己的工作流，还是由 auto-manual 跨仓触发）。
6. 历史：保持原样、改写历史，或其他方案。
7. 是否为四个阶段登记台账行，登记在哪份台账（执行台账的 REV 行，或优化路线图）。
8. 矩阵中 ✚ 行（审查补上的路径）的归属是否按建议。

## 8. 与原清单的差异

1. 阶段一改用 overlay 路径——keep 路径对 auto-manual 仍在写的目录会冻结下游。
2. 阶段一保护 `data/business` 而非整个 `data`——基线文件留工程面，原清单阶段一与矩阵矛盾。
3. `review_sync_json` 不进保护列表——它是误提交的 CI 输出，直接删除。
4. `site` 归属列为待定——原清单阶段一给 Hello-Docs，矩阵给 Hello-Docs-Review。
5. 矩阵新增 `data/manual_sources` 等 13 行——合计约 8,270 个文件被遗漏。
6. 基线为 7 个，读取方是 ratchet 模块与 `check_doc_lifecycle.py`——原清单写的是 `check_maintainability_guardrails.py`。
7. 阶段二拆为无损准备与删除，并列出五个前提——否则删除会打断护栏、测试、asset-check 和钉住检查。
8. 阶段二删除时修改发布路由——当前新 Web 说明书先提交 auto-manual。
9. 阶段三第 2 项提前——它是删除的前提。
10. 阶段四第 1 项：`.githooks` 没有禁入列表——实际的 PR 检查是 `MIRROR_OWNED_PATHS`，需同步扩充。
11. 阶段四第 2 项：扩展现有字面量护栏——`collect_web_target_literal_failures` 已存在。
12. 阶段四第 4 项提前到夹具之后——它是删除的前提。
13. `Makefile` 只有 `CONFIG`——原清单称它硬编码了 `--data-root`。
14. 新增验收与回滚——原清单没有。
15. 新增"移动不清除历史"的说明——历史处理需要单独决定。
16. 清单项去掉复选框——状态归执行台账。
17. 不在本文列出具体型号代码、品牌主体、联系方式和业务表标识——本仓是公开仓。

## 修订记录

| 日期 | 基线 | 变更 |
| --- | --- | --- |
| 2026-11-16 | main `66709a9f` | 初版：收入操作者清单，按只读审查与 PR #1724 审查修订 |
| 2026-11-16 | main `66709a9f` | 标明审查建议的部分（✚ 行归属、验收与回滚）、台账未定、子目录切换与回滚的限制 |
