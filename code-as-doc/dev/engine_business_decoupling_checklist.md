# auto-manual 引擎与型号业务数据解耦清单

Status: proposed · Owner: 夏冰 · Created: 2026-11-16

- 本文是**提案草稿**，尚未开始执行。执行状态不记在本文里，要先登记台账行；登记在哪份台账尚未决定（§7 第 7 项），候选是[执行台账](manual_revitalization_execution.md)的 REV 行或[优化路线图](../optimization_project.md)。目前**没有登记任何行**。
- 来源：操作者 2026-11-16 在飞书写的《auto-manual 引擎与硬件型号业务记录彻底解耦重构清单》（四个阶段、17 项）。本文把它收进仓库，并按下面的审查结果修订。
- 核对基线：main `66709a9f`。
- 2026-11-16 操作者决定：`site/` 退役（§7 第 2 项）。
- 方法：2026-11-16 对 main 做只读核对（`git ls-tree`、读代码与工作流），未运行任何构建或测试；另外参考了 [PR #1724](https://github.com/Bingboom/auto-manual/pull/1724)（阶段一的首个实现，未合入）的审查与原型实验，并对两个真实镜像的当前 head 做了同步空跑（只比较组成的文件树，不推送）。
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
4. **移动文件不会把它从历史里去掉。** 文件从 main 删除后，仍在 auto-manual 的 git 历史中可见。是否改写历史是另一项决定（见 §7 第 6 项），本清单不默认执行。

## 3. 归属矩阵

“审查”列标 ✚ 的行是原清单遗漏、由审查补上的；标 ✎ 的行是原清单已有但事实或处置被修订的。✚ 行的“归属”是审查的建议，尚未经操作者确认（§7 第 8 项）。

| 路径 | 现状（main `66709a9f`） | 归属 | 说明 | 审查 |
| --- | --- | --- | --- | :---: |
| [`manual_sources/`](../../manual_sources) | 28,989 个文件，73 个型号目录加 `shared/` | Hello-Docs | 冻结源包；Hello-Docs-Review 只把本地冻结包当回退语料 | ✎ |
| [`data/manual_sources/`](../../data/manual_sources) | 5,949 个文件 | Hello-Docs | 第二个冻结包根目录，[`frozen_package_registry.py`](../../tools/web/frozen_package_registry.py) 也扫描它 | ✚ |
| [`data/`](../../data) 业务表 | 冻结包注册表、型号能力/语言、产品信息、资产注册与来源、型号专用版式参数、标签来源、[`data/phase2/`](../../data/phase2) | Hello-Docs | 原地不动，见下方 `data/` 目录清单（§7 第 1 项） | ✎ |
| [`data/`](../../data) 代码质量基线 | 8 项：7 个文件（broad_except、complexity、top_level_module、facade_patch、mypy_untyped、language_literal、doc_lifecycle）加 [`known_warnings/`](../../data/known_warnings) | auto-manual | 由各自 `tools/check_*_ratchet.py`、[`check_doc_lifecycle.py`](../../tools/check_doc_lifecycle.py) 与 [`warning_ratchet.py`](../../tools/warning_ratchet.py) 读取，不是 [`check_maintainability_guardrails.py`](../../tools/check_maintainability_guardrails.py) | ✎ |
| [`data/asset_recipes/`](../../data/asset_recipes)、[`asset_evidence/`](../../data/asset_evidence)、[`asset_promotions/`](../../data/asset_promotions) | 80 / 10 / 2 个文件 | Hello-Docs | 资产配方（79 份单本说明书配方加 1 份 schema）、证据与推广记录 | ✚ |
| [`configs/`](../../configs) | 31 个 `config.*.yaml`，30 个点名真实型号，14 个设置 `default_model`；[`config-bases/`](../../configs/config-bases) 为通用基类 | 分层 | 基类与 demo 留工程面；型号实例下沉。`configs/profiles`、`configs/targets` 目前不存在 | ✎ |
| [`bitable_schema/`](../../bitable_schema) | 5 个文件；`business_base_manifest.json` 是字段结构但绑定具体业务实例；[`seed/`](../../bitable_schema/seed) 是一个小 CSV | 分层 | 纯字段契约留工程面，实例绑定与种子下沉 | ✎ |
| [`reports/`](../../reports) | 434 个文件；`reports/releases` 未跟踪 | Hello-Docs | 型号审计与版本追踪 | ✎ |
| [`review_sync_json/`](../../review_sync_json)（2 个文件）与 [`review_sync_out.txt`](../../review_sync_out.txt)，共 3 个已跟踪文件 | 唯一写入和读取方是 [`review-branch-sync-check.yml`](../../.github/workflows/review-branch-sync-check.yml) 的作业，它从不提交，另外还写 `review_sync_issue_body.md`；没有 ignore 规则覆盖这些文件名 | 无 | 误提交物，无需迁移：删除并写入 `.gitignore` | ✎ |
| [`site/`](../../site) | 2 个已跟踪文件：[`site/review-preview/README.md`](../../site/review-preview/README.md) 与只有表头的 [`site/review_preview_links.csv`](../../site/review_preview_links.csv)，没有读取方 | 退役 | 操作者 2026-11-16 决定。删除两个文件，不进任何镜像列表。`site/review-preview/dist`、`site/publish-latest/dist` 是打包工具 [`build_review_preview.py`](../../tools/process_docs/build_review_preview.py)、[`build_publish_latest_site.py`](../../tools/process_docs/build_publish_latest_site.py) 的未跟踪输出；CI 作业 `package-review-preview`（[`review-preview.yml`](../../.github/workflows/review-preview.yml)）写前者，不读 `site/` 下任何已跟踪文件。打包器是独立功能，是否一并退役另议 | ✎ |
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

### `data/` 目录清单

main 上 `data/` 有 40 个直接条目、6,082 个文件，约 1.69 GB。

| 类别 | 条目 | 文件数 | 说明 |
| --- | --- | ---: | --- |
| 引擎 | 7 个代码质量基线；[`known_warnings/`](../../data/known_warnings)（2，第八个基线，[`warning_ratchet.py`](../../tools/warning_ratchet.py) 读取）；[`source_table_contracts/`](../../data/source_table_contracts)（1，源表结构契约）；[`layout_params.csv`](../../data/layout_params.csv)、[`layout_params.idml-compact.csv`](../../data/layout_params.idml-compact.csv)（共用版式默认值）；[`capability_page_rules.csv`](../../data/capability_page_rules.csv)、[`terminology_rules.csv`](../../data/terminology_rules.csv)（按能力或语言、不按型号的规则）；`AGENTS.md`、`CLAUDE.md` | 16（约 175 KB） | 留工程面，搬出 `data/` |
| 混合 | [`phase2/`](../../data/phase2)（1 个已跟踪文件 `page_registry.csv`，通用行；旁边的业务快照已被 gitignore）；[`frozen_package_registry.json`](../../data/frozen_package_registry.json)（每个业务包一行，随包走；漂移键指向引擎契约文件）；[`asset_recipes/`](../../data/asset_recipes)（79 份单本配方加 1 份 schema） | 82 | 逐项拆分 |
| 业务 | [`manual_sources/`](../../data/manual_sources) 5,949；资产注册与证据（[`asset_registry.csv`](../../data/asset_registry.csv)、`asset_sources.csv`、`asset_evidence/`、`asset_promotions/`、`asset_base_bindings.json`）15；型号能力、语言与四份已知例外清单 6；其他业务表（交付映射、目录对账白名单、两份印刷网址清单、[`label_sources/`](../../data/label_sources) 5 个文件、一份单型号版式叠加表）10 | 5,980 | 归 Hello-Docs，原地不动 |
| 无读取方 | `asset_generation_candidates.csv`、`check.csv`、`config/lang_density.csv`、`product_info.csv`（空） | 4 | 删除前再确认一次 |

`data/business` 在 main 上没有任何地方使用。目前只有 phase2 快照（`--data-root`）、`paths.docs_dir` 和 `paths.layout_params_csv` 能指向仓外；`data/` 下其他内容都通过 [`path_utils.py`](../../tools/utils/path_utils.py) 的 `Paths.data_dir` 固定在仓库根下。

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
- **建议列表。** Hello-Docs 的 overlay = `manual_sources`、`data/manual_sources`、`reports`、`configs/targets`、`bitable_schema/business`。Hello-Docs-Review 不设 overlay：它不读冻结包（见阶段二前提 4），上游删除应继续传到它，它也就不会留下过期副本。`data/business` 不用（§7 第 1 项），`site/review-preview` 不用（`site/` 退役），`review_sync_json` 不进任何列表（误提交物）。源仓禁入列表 = 严格 keep 路径，不变。
- **切换方式。** 整条路径 P 的切换是一个 auto-manual PR：删除 P，把 P 从 overlay 移到 keep，加入禁入列表和 [`MIRROR_OWNED_PATHS`](../../tools/check_maintainability_guardrails.py)。子目录的切换只需在上游删除它；但子目录切换后默认没有防回流检查，若它被重新加回上游会覆盖下游副本，整条路径切换后才由禁入列表拦住。
- **已知代价。** 上游删除的文件会留在下游，直到在下游手动删除；某文件仍在上游时，镜像里对它的修改会被覆盖——所以每条路径同一时刻只能有一个写入方。
- **真实镜像空跑（2026-11-16）。** 对两个镜像当前 head 做了 12 次空跑（2 个镜像 × 3 种方案：现有脚本、#1724、overlay 原型 × 2 种源状态）。用今天的源，三种方案组成的树完全相同，两个镜像都与 main 同步，overlay 路径下没有镜像独有文件。模拟上游新增、修改和删除一个包后：#1724 既不把新增也不把修改送到 Hello-Docs，并在 Hello-Docs-Review 删掉该包、在 Hello-Docs 保留；原型送达新增和修改，并保留被删的包。上面的列表是在这些空跑之后改的，实现时须重新空跑。
- **空跑要求。** 合并前后各做一次同步空跑，比较下游文件清单，证明没有下游删除。提案允许从 PR 分支启动空跑（不从 main 运行时强制为空跑），因此合并前就能对真实镜像检查。
- 第 1 项中的 `data` 不保护整个 `data/`，也不新建 `data/business`；目前只把 `data/manual_sources` 放进 overlay。

### 阶段二：拆分混合目录、下沉业务资产

原清单各项：

1. 把代码质量基线迁入 `tools/guardrails/baselines/` 并更新读取常量。
2. 新建 `examples/demo_product/` 合成夹具：虚构型号 `DEMO-100`，双语种、基础参数 CSV、最小 RST 模板、样例图标、冻结包结构；虚构品牌主体与保留域名 `example.com` 的联系方式。
3. 确认 Hello-Docs 完整持有冻结源包与业务注册表后，从 auto-manual 删除这些文件，只留 Schema 校验定义。
4. 拆分 [`bitable_schema/`](../../bitable_schema)：留纯字段契约，实例清单、TM 清单、种子迁到 Hello-Docs，并复查 [`.gitleaks.toml`](../../.gitleaks.toml) 中不再需要的豁免项。
5. 清理报告与审校残留：`reports` 迁 Hello-Docs，`review_sync_json` 与 `site` 预览清单迁 Hello-Docs-Review，删除 `review_sync_out.txt` 并写入 `.gitignore`。

审查后的修订：

- **分两部分。** 无损准备（可以现在开始）：第 1、2 项，第 4 项的拆分设计，第 5 项中删除误提交物和 `site/`。删除（有前提）：第 3 项、第 4 项的迁移、第 5 项中 `reports` 的迁移。
- **第 1 项**：基线共 8 个（7 个文件加 `known_warnings/`），读取方是 6 个 `tools/check_*_ratchet.py`、`check_doc_lifecycle.py` 的 `DEFAULT_BASELINE` 与 `warning_ratchet.py`，不是 `check_maintainability_guardrails.py`。`tools/guardrails/` 目前不存在。
- **`data/` 的拆法（建议）。** 业务数据保持现有相对路径不动；把引擎文件搬出 `data/`（8 个基线、`source_table_contracts/`、`layout_params.csv`、`layout_params.idml-compact.csv`、`capability_page_rules.csv`、`terminology_rules.csv`、`data/AGENTS.md`、`data/CLAUDE.md`）；之后整个 `data/` 就是一条业务路径，可以一次切换；不新建 `data/business`。理由：给业务路径改名会改变冻结包注册表的键、钉住记录和审核稿里记下的出处路径，而引擎部分只有 16 个小文件。
- **第 3 项范围补全**：还包括 `data/manual_sources`、`docs/renderers/web/assets` 中被钉住的型号文件、`data/asset_*`、`docs/manifests`、`docs/templates/targets`、`target_assembly`、`reference_layout` 等矩阵新增行。
- **第 5 项**：`site/` 退役，删除它的两个已跟踪文件，无需迁移。同步检查的三个输出文件同样无需迁移，删除后在 `.gitignore` 加三行：`/review_sync_json/`、`/review_sync_out.txt`、`/review_sync_issue_body.md`。
- **任何删除之前必须先落地的前提：**
  1. 工作区根接口（阶段三第 2 项），引擎能从外部仓读数据。
  2. 业务仓的 PR 承接冻结包注册表检查、钉住漂移检查、资产检查和型号测试。现状：工作流文件会同步到镜像（没有排除 `.github`）；镜像里的 PR 目前只跑 [`manual-validation.yml`](../../.github/workflows/manual-validation.yml) 的 `secret-scan` 和 `business-content`，后者按仓库限定在两个镜像，只检出文档内容目录；注册表检查、reference-layout 钉住、资产检查和单元测试只在 auto-manual 运行。建议沿用 `business-content` 的先例：在 manual-validation.yml 里加按仓库限定的作业，让这些检查在 Hello-Docs 自己的 PR 中运行。
  3. 合成夹具（本阶段第 2 项）就位，且 manual-validation 已改指它（阶段四第 4 项）。否则删掉 `manual_sources` 或 `data/frozen_package_registry.json` 会打断护栏作业、大部分相关测试、asset-check 和钉住检查。
  4. Hello-Docs-Review 的语料来源明确。现状：它的站点构建只读 `docs/review-drafts`（[`.readthedocs.yaml`](../../.readthedocs.yaml)、[`review_site.py`](../../tools/rtd/review_site.py)）；manual-review-draft 技能在 `docs/review-drafts` 的稀疏克隆上工作，auto-manual 与 Hello-Docs 以只读方式挂载，语料是模板、在线翻译记忆、在线表格和已发布页面，本地冻结包只作回退；每份草稿自带参考稿副本；有 18 个草稿文件提到冻结包路径，都只是出处说明。建议 Review 不保留冻结包副本；切换时把技能的语料路径指向 Hello-Docs。
  5. 切换当次同步修改发布路由：现在新 Web 说明书先提交到 auto-manual（包与注册表同一 PR），再向 Hello-Docs 开只含 `docs/publish` 的 PR（[input-paths.md](web_publish_pipeline/input-paths.md) §2.2、[two_plane_map.md](../../user-guide/two_plane_map.md)、AGENTS.md §8.5），以及 manual-review-draft 技能中的语料路径说明。

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

1. **现在即可并行开始（全部无损）：** 阶段一 overlay 改造与空跑；阶段二第 1 项（基线迁移）、第 2 项（合成夹具）、删除误提交物（同步检查的三个输出文件与 `site/` 的两个文件）；阶段三第 2 项（工作区根接口）；阶段四第 2 项（扩展字面量护栏，先以基线模式）。
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

## 7. 决定与建议

标"待确认"的行是审查的建议，经操作者确认后才成为决定。

| # | 事项 | 状态 | 建议或决定 | 依据 |
| --- | --- | --- | --- | --- |
| 1 | `data/` 的拆法 | 待确认 | 不新建 `data/business`；业务数据原地不动，引擎文件搬出 `data/` | 引擎部分只有 16 个小文件，业务路径改名会改变注册表键、钉住和审核稿出处路径 |
| 2 | `site` | 已决定（操作者，2026-11-16） | 退役：删除两个已跟踪文件，不进任何镜像列表；打包器是否退役另议 | 两个文件无读取方；预览输出是未跟踪的打包产物 |
| 3 | 同步检查的误提交输出 | 待确认 | 删除三个文件并加三行 ignore | 唯一读写方是同步检查作业，它从不提交 |
| 4 | Review 的语料 | 待确认 | Review 不保留冻结包副本，不设 overlay | 站点只读 `docs/review-drafts`；技能以在线语料为主，本地冻结包只作回退 |
| 5 | 业务面 PR 的 CI | 待确认 | 放在 Hello-Docs 自己的 PR 里：在 manual-validation.yml 加按仓库门槛的业务数据作业；Hello-Docs 是私有仓，作业要精简 | 镜像 PR 现在只跑 `secret-scan` 与 `business-content`，后者已是按仓库门槛的先例 |
| 6 | 历史 | 待确认 | 不原地改写历史；解耦完成后从清理后的树新建公开的引擎仓，现仓转私有留档；在那之前是否先转私有由操作者按数据敏感度决定（私有仓的 Actions 用量计入套餐额度） | 原地改写会让现有 PR、克隆和镜像同步记录失效，已被抓取的副本也收不回 |
| 7 | 台账 | 待确认 | 登记为 [optimization_project.md](../optimization_project.md) §6 的新工作流（下一个可用字母），本文作为计划文档；给 17 项编号；完成时在 [code_optimization_log.md](../code_optimization_log.md) 顶部加记录 | 该文件自称仓库级执行路线图，§6 的工作流有 `Status:` 行，Workstream Y 是先例；REV 台账只管当前盘活计划 |
| 8 | ✚ 行的归属 | 待确认 | 按矩阵。三行待定的建议：`docs/_build` 的已跟踪产物随业务数据走，是否取消跟踪届时再定；`code-as-doc/reviews` 中以型号命名的记录随业务数据走，其余留工程面；合并授权登记留工程面 | 均为审查建议 |

## 8. 与原清单的差异

1. 阶段一改用 overlay 路径——keep 路径对 auto-manual 仍在写的目录会冻结下游。
2. overlay 只给 Hello-Docs——Hello-Docs-Review 不读冻结包，上游删除应继续传到它。
3. 阶段一不保护整个 `data`，目前只把 `data/manual_sources` 放进 overlay——基线等引擎文件留工程面，原清单阶段一与矩阵矛盾。
4. 不新建 `data/business`，业务数据原地不动——改名会改变注册表键、钉住和审核稿出处路径。
5. `review_sync_json` 不进保护列表——它是误提交的 CI 输出，直接删除并 ignore。
6. `site` 退役（操作者决定）——原清单阶段一给 Hello-Docs、矩阵给 Hello-Docs-Review，而两个已跟踪文件没有读取方。
7. 矩阵新增 `data/manual_sources` 等 13 行，并补 `data/` 目录清单——合计约 8,270 个文件被遗漏。
8. 基线为 8 个，读取方是 ratchet 模块、`check_doc_lifecycle.py` 与 `warning_ratchet.py`——原清单写的是 `check_maintainability_guardrails.py`。
9. 阶段二拆为无损准备与删除，并列出五个前提——否则删除会打断护栏、测试、asset-check 和钉住检查。
10. 写明镜像 CI 现状：镜像 PR 只跑 `secret-scan` 与 `business-content`——注册表、钉住、资产检查和单元测试须先在业务仓 PR 中运行。
11. 阶段二删除时修改发布路由和技能语料路径——当前新 Web 说明书先提交 auto-manual。
12. 阶段三第 2 项提前——它是删除的前提。
13. 阶段四第 1 项：`.githooks` 没有禁入列表——实际的 PR 检查是 `MIRROR_OWNED_PATHS`，需同步扩充。
14. 阶段四第 2 项：扩展现有字面量护栏——`collect_web_target_literal_failures` 已存在。
15. 阶段四第 4 项提前到夹具之后——它是删除的前提。
16. `Makefile` 只有 `CONFIG`——原清单称它硬编码了 `--data-root`。
17. 新增验收与回滚——原清单没有。
18. 新增"移动不清除历史"的说明——历史处理需要单独决定。
19. 清单项去掉复选框——状态归台账。
20. 不在本文列出具体型号代码、品牌主体、联系方式和业务表标识——本仓是公开仓。

## 修订记录

| 日期 | 基线 | 变更 |
| --- | --- | --- |
| 2026-11-16 | main `66709a9f` | 初版：收入操作者清单，按只读审查与 PR #1724 审查修订 |
| 2026-11-16 | main `66709a9f` | 标明审查建议的部分（✚ 行归属、验收与回滚）、台账未定、子目录切换与回滚的限制 |
| 2026-11-16 | main `66709a9f` | 记录 `site/` 退役决定；补 `data/` 目录清单、第八个基线、真实镜像空跑；overlay 只给 Hello-Docs、不用 `data/business`；修正镜像 CI 与 Review 语料现状；§7 改为决定与建议表 |
