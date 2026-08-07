# Auto-Manual

**一份源头，产出每个市场的说明书。**
*One source of truth — every market's manual, in every format.*

Auto-Manual 是说明书的自动化产线。产品数据、文案、术语和插图各自只维护一份，
一次构建，同源产出印刷 PDF、可编辑 DOCX、InDesign 设计稿和响应式网页手册——
七个市场家族，每一本都可评审、可追溯、可复现。

- **改一处，处处生效** —— 规格与文案的修改从源表流向所有语言和格式，不再逐份手改
- **同源多格式** —— 全部交付物出自同一个冻结构建包，文案、规格、法务内容永不分叉
- **评审有闭环** —— 云文档评审意见按归属自动回流源头；每次发布绑定提交、快照和哈希，可逐字节重建

> 这份 README 只承载三件事：工作流路线图、快速上手、导航地图。完整命令参考在
> [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md)。

## 工作流全景 Roadmap

主路径：从受治理的内容源，到冻结、可评审、多格式的成品手册。图中青色阶段属于
工程面（auto-manual），紫色阶段跨入业务发布面（Hello-Docs）。

![Auto-Manual workflow roadmap](docs/readme-assets/auto-manual-roadmap.svg)

> 第一次接触本项目时，请先沿编号主路径阅读。图底部的质量门禁是各阶段的
> 验收条件，不是最后才做的可选清理项。

### 1. 治理内容源

先明确目标的 **型号、区域、语言和执行平面**，再到真正拥有该信息的源头修改：

| 信息类型 | 唯一事实源 |
| --- | --- |
| 产品信息、规格参数、页面占位值 | 飞书 phase2 源表（列语义见 [`hello_auto-doc.md`](user-guide/hello_auto-doc.md) 的 Source of Truth 节） |
| 可复用的说明书文案和页面结构 | [`docs/templates/`](docs/templates) |
| 已确认的术语和句对 | TM-B `Translation_Memory` |
| 正式插图及其导出物 | 飞书 `04_资产*` 表和本地资产注册表 |
| 评审开始后的目标专属修改 | [`docs/_review/`](docs/_review) |

不要把 [`docs/_build/`](docs/_build) 当作编辑源。生成文件是验证证据和交付物，
不是长期维护的内容源。三条阶段铁律：评审开始前，从模板和数据播种草稿；评审开始
后，改 `_review`；永远不要把 `_build` 当源头。

正式插图在页面 RST 中按语义身份引用已批准的注册表导出物，不写渲染器路径：

```rst
.. image:: asset:operation/ac_output
```

### 2. 冻结输入

`sync-data` 把选定的飞书记录和附件固化到 Git 忽略的 `data/phase2/` 快照中。
配置文件和 `document_key` 将快照绑定到具体目标；页面清单定义页面组合，资产清单
和构建包清单则通过哈希绑定实际使用的文件字节。

进入下一阶段前，确认：

- 配置解析出的型号、区域和语言与任务目标一致
- phase2 快照包含目标记录和必需附件
- 每个正式 `asset:` 引用都能解析到已批准的导出物
- 准备好的构建包已记录输入清单和 `bundle_sha256`

测试和 CI 使用已提交、可复现的样例快照
[`tests/fixtures/phase2/`](tests/fixtures/phase2)，不依赖实时读取飞书。

### 3. 构建与检查

[`build.py`](build.py) 是统一入口，`JE-1000F`（US/JP）是长期维护的烟测基线。
最小 US/EN 验证路径如下（`config.us-en.yaml` 是 CI 同款的单语 US 配置；
`config.us.yaml` 是 en/fr/es 三语合订家族）：

```bash
python build.py doctor --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py doctor --data-plane --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2
python build.py check  --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
```

`doctor` 检查环境和目标，`check` 执行质量门禁，`review` 创建目标评审面。
JP、多语言、新产线、资产接入和矩阵构建等操作，见下方
[按主题跳转](#topic-index) 与 [`build_doc_guide.md`](code-as-doc/build_doc_guide.md)。

### 4. 评审与回写

评审开始后，`docs/_review/<model>/<region>` 下的冻结派生稿负责承载目标专属修改。
数据驱动的更新优先使用 `sync-review`，不要随意刷新或覆盖已经评审的文案；评审侧
覆盖物只允许放在 `overrides/_assets/`、`overrides/_static/` 或
`overrides/renderers/` 之下。

按照内容归属将评审意见写回正确源头：

| 评审发现 | 回写位置 |
| --- | --- |
| 仅当前目标使用的文案或版式调整 | `docs/_review/...` |
| 多目标共用的可复用文案 | 修改模板，再同步到进行中的评审 |
| 规格参数或页面占位值 | 通过审批门禁（F6）写入飞书源表 |
| 插图或资产修正 | 资产接入/晋级流程及资产注册表 |

回写评审云文档时，使用能够解析评审分支的标准入口，不要猜测本地文件路径：

```bash
python tools/cloud_doc_backport.py run-review-branch \
  --doc-name <doc-name> --cloud-doc <url>
```

先执行 dry-run。确认报告后使用 `--write` 应用；只有需要向已解析的评审分支创建
草稿 PR 时才添加 `--push`。

### 5. 生成多格式输出

所有格式都消费同一个准备完成的构建包。PDF 是固定版式参考，DOCX 用于编辑交换，
IDML 是可编辑的设计交付，HTML 提供响应式展示，Markdown 和 ZIP 用于交换与发布。

各输出适配器可以采用不同的分页和排版方式，但不能私自分叉文案、规格、法务内容、
术语或资产身份。生成可编辑的 InDesign 交付包时：

```bash
python build.py idml \
  --config configs/config.us.yaml --model JE-1000F --region US \
  --source review-asis
```

生成文件保留在 `docs/_build/` 或发布报告目录中。发现问题时，应在对应的内容源或
评审层修正，再重新构建。批准复刻目标的验收是逐页视觉比对：在最新 parity 报告
显示 `accepted=true` 之前，不要交付 IDML/INDD/PDF。

### 6. 发布与追踪

发布流程从工程面跨入业务面：

1. `auto-manual/main` 单向同步到 `Hello-Docs/main`。
2. 业务面的 Web Publish 队列组装冻结的 `docs/publish/` 候选快照。
3. 受范围门禁保护的 `publish → main` PR 只携带已评审的 Web 快照。
4. Read the Docs 基于合入后的 Git 快照构建，不实时读取飞书。
5. Worker 将在线 URL 和最终状态回写到原始记录。

代码修改只发生在 `auto-manual`，不要直接修改 Hello-Docs 的工程树。只有源提交、
生成产物、发布 URL 和飞书回读结果全部一致，发布才算完成。响应式 Web 输出是
评审内容的纯展示投影：普通 CLI/队列构建保持默认 `document`（印刷）profile，
IDML、DOCX、PDF 和正式 Markdown 不受影响，细节见
[`web_publish_pipeline.md`](code-as-doc/dev/web_publish_pipeline.md)。

## 各交接点的质量门禁

- **确认范围后再写入：** 写入前确认型号、区域、语言、仓库、Base 和目标记录。
- **保证哈希和清单完整：** 冻结复现构建所需的准确内容、资产和工具链输入。
- **完成视觉与内容评审：** 检查结构、文案、链接、表格、资产及各格式的专属呈现。
- **回读实时状态：** 核对最终提交、产物、URL 和飞书字段；成功触发任务不等于验收通过。

## Recurring terms

Six internal terms the rest of the documentation uses without ceremony:

- **phase2** — the second-stage structured-data plane. The Feishu phase2
  source tables are the authoring source of truth; `sync-data` materializes
  them into the gitignored local snapshot `data/phase2/`, which is the
  default build/review/publish input (`--data-root` still overrides it). CI
  and tests use the frozen sample copy in
  [`tests/fixtures/phase2/`](tests/fixtures/phase2).
- **F6** — the operator-gated approval step for writes to the production
  Feishu source tables. Tools and agents only propose change requests and
  dry-runs; the operator personally executes the approved write, and every
  write is followed by a read-back of the same record.
- **build queue** — the Feishu build table that drives remote Draft /
  Publish: an operator arms a row, the queue worker consumes it, builds, and
  writes the result back to that row. Queue semantics live in
  [`build_doc_guide.md`](code-as-doc/build_doc_guide.md).
- **Manual IR** — `manual.ir.json`, the normalized content tree projected
  from the prepared bundle (templates + data). Production IDML renders from
  this frozen representation; the LaTeX PDF renders from the same prepared
  bundle (same source), with `latex_page_plan.json` retained as a trace.
- **fail-closed** — the default gate semantics here: when a validation,
  hash, or contract check fails, the build stops. Nothing silently falls
  back to an older or fuzzier value.
- **two planes / two Bases** — auto-manual is the engineering plane bound to
  the engineering Feishu Base; the
  [`Bingboom/Hello-Docs`](https://github.com/Bingboom/Hello-Docs) mirror is
  the business plane with its own Base bindings (`main` syncs one-way via
  [`sync-hello-docs.yml`](.github/workflows/sync-hello-docs.yml)). Read
  [`user-guide/two_plane_map.md`](user-guide/two_plane_map.md) before
  reasoning about which repo or Base an operation touches.

## Where to start

- **New maintainer** → [`ONBOARDING.md`](ONBOARDING.md): two-plane topology,
  what-runs-where, and the golden-path drill that certifies a hand-over.
- **Daily operation** →
  [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md) (workflow
  and source-of-truth rules) and
  [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md)
  (happy-path example).
- **AI agent windows (Claude Code / Codex)** → [`CLAUDE.md`](CLAUDE.md)
  auto-loads the shared rules in [`AGENTS.md`](AGENTS.md); Codex reads
  `AGENTS.md` directly. Start every task with
  `scripts/start_branch.ps1 <type>/<area>-<topic>` (macOS/Linux:
  `./scripts/start_branch.sh`); multi-window rules are in `AGENTS.md` §8.
- **Command semantics** →
  [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md).
- **Long-term direction** →
  [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md)
  — platform strategy is defined there, not in this repo's working docs.

## Topic index

Everything beyond the roadmap's main path is topic-shaped — jump straight to
the owning section of
[`build_doc_guide.md`](code-as-doc/build_doc_guide.md):

| Topic | Entry points |
| --- | --- |
| CI sweep over every config target; fixture snapshot refresh | `tools/ci_check_targets.py`, `tools/data_snapshot.py fixture-refresh` |
| Asset control plane: approved exports, intake, promotion, quarantine | `build.py asset-check`, `build.py asset-intake` |
| New model / region / line scaffolding | `build.py new-line` (dry-run by default); skill [`new-region-line`](.agents/skills/new-region-line/SKILL.md) |
| Editable InDesign handoff and production IDML export | `build.py idml`; publish handoffs are portable ZIPs with relinked `Links/` |
| Approved-PDF native replica (“方案 2”); a target without an approved reference layout contract falls back to the measured-LaTeX page plan | reference layout contracts, `tools/reference_layout_rebind.py`, `tools/indesign_finalize.py`, [`STYLE_DEFINITION.md`](docs/renderers/contracts/STYLE_DEFINITION.md) |
| Content QC over the current snapshot | `tools/content_lint.py` |
| Cloud-doc backport (reviewer edits → repo) | `tools/cloud_doc_backport.py run-review-branch` — the blessed path for in-review docs |
| Structured spec / manual-table intake | `tools/source_intake.py run / approve / apply / verify` |
| Queue-driven Draft / Publish; release verification and tags | `build.py process-build-queue`, `build.py release-rebuild-verify`, `tools/release_tag.py` |
| Manifest inventory and family-manifest fold | `tools/manifest_lint.py`, `tools/manifest_family.py` |
| Fixed US + JP release matrix | `scripts/build_us_jp_manuals.py` (pass `--languages` for a subset) |

One standing rule: build requests arriving through OpenClaw (the Feishu-side
dispatch agent) or Feishu IM go through the adapter's `queue-resolve-action`
→ `queue-execute` and are consumed by the remote queue worker, which syncs
its own fresh snapshot. A local `check` against `data/phase2/*.csv` is
therefore not a valid preflight. Details:
[`integrations/openclaw/feishu-im-webhook-adapter/README.md`](integrations/openclaw/feishu-im-webhook-adapter/README.md).

## Document map

Use the document that owns the topic:

- maintainer doc index and ownership map: [`code-as-doc/README.md`](code-as-doc/README.md)
- current business logic overview and invariants: [`code-as-doc/business_logic_overview.md`](code-as-doc/business_logic_overview.md)
- current maintainer command reference: [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md)
- current JP / US family difference boundary: [`code-as-doc/manual_family_guide.md`](code-as-doc/manual_family_guide.md)
- current Git branching and GitHub protection rules: [`code-as-doc/dev/git_branching_guide.md`](code-as-doc/dev/git_branching_guide.md)
- current responsive Web Publish and Read the Docs flow: [`code-as-doc/dev/web_publish_pipeline.md`](code-as-doc/dev/web_publish_pipeline.md)
- legacy Vercel latest-publish implementation reference: [`code-as-doc/dev/vercel_review_preview_guide.md`](code-as-doc/dev/vercel_review_preview_guide.md)
- current user workflow and editing rules: [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md)
- happy-path example: [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md)
- closed-loop operations playbook (release tags and rollback, `.ai` handoff, sentinels): [`user-guide/closed_loop_ops_guide.md`](user-guide/closed_loop_ops_guide.md)
- two-plane repo / Base topology: [`user-guide/two_plane_map.md`](user-guide/two_plane_map.md)
- architecture doc index: [`code-as-doc/architecture/README.md`](code-as-doc/architecture/README.md)
- current repository component map: [`code-as-doc/architecture/Hello_Docs_Architecture.md`](code-as-doc/architecture/Hello_Docs_Architecture.md)
- AI agent operating rules (Claude / Codex / future agents): [`AGENTS.md`](AGENTS.md), with [`CLAUDE.md`](CLAUDE.md) as the Claude Code entrypoint and directory-level `AGENTS.md` files as the Codex local maps
- Codex scaffolding and architecture audit: [`code-as-doc/reviews/codex_scaffolding_discovery.md`](code-as-doc/reviews/codex_scaffolding_discovery.md)
- Codex skill migration plan: [`code-as-doc/reviews/codex_scaffolding_implementation_plan.md`](code-as-doc/reviews/codex_scaffolding_implementation_plan.md)
- current OpenClaw bootstrap: [`agent/BOOTSTRAP.md`](agent/BOOTSTRAP.md)
- current OpenClaw integration package: [`integrations/openclaw/README.md`](integrations/openclaw/README.md)
- repo-local translation memory skill for OpenClaw-assisted multilingual work: [`.agents/skills/bitable-translation-memory/SKILL.md`](.agents/skills/bitable-translation-memory/SKILL.md)
- repo-local Feishu DOCX preprocessing skill for TM-backed source/target language conversion: [`.agents/skills/lark-tm-translation-preprocess/SKILL.md`](.agents/skills/lark-tm-translation-preprocess/SKILL.md)
- repo-local TM-first manual rewrite skill for structured Markdown/manual translation work: [`.agents/skills/manual-rewrite-with-tm/SKILL.md`](.agents/skills/manual-rewrite-with-tm/SKILL.md)
- future canonical content model: [`code-as-doc/architecture/Content_Data_Model.md`](code-as-doc/architecture/Content_Data_Model.md)
- long-term strategy and stable architecture boundaries: [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md)
- repo-level execution roadmap: [`code-as-doc/optimization_project.md`](code-as-doc/optimization_project.md)

## Key directories

- [`build.py`](build.py): top-level CLI entrypoint
- [`configs/`](configs): shared family configs with config-base inheritance, covering the US, EU, JP, CN, AU, KR, and pt-BR families
- [`tools/`](tools): orchestration, rendering, validation, diff, and release helpers
- [`scripts/`](scripts): branch wrappers, local-build helpers, and queue service scripts
- [`docs/manifests/`](docs/manifests): page-stack manifests for manifest-driven manual families
- [`docs/templates/`](docs/templates): shared seed templates
- [`docs/_review/`](docs/_review): target-specific review layer
- [`docs/_build/`](docs/_build): runtime bundles and export outputs
- `data/phase2/`: gitignored Feishu-synced CSV snapshots; only the repo-maintained [`data/phase2/page_registry.csv`](data/phase2/page_registry.csv) stays tracked because `sync-data` reads it as input
- [`data/source_table_contracts/phase2_source_tables.json`](data/source_table_contracts/phase2_source_tables.json): the machine-readable source-table contract; update it when the online source-table structure changes
- [`tests/fixtures/phase2/`](tests/fixtures/phase2): committed fixture snapshot used only by CI/tests, not by live authoring
- [`tests/`](tests): automated regression coverage
- [`reports/`](reports): revision reports and release evidence; `reports/releases/` is gitignored, and queue Publish ships deliverables to Feishu or short-lived Actions artifacts instead of committing them
- [`integrations/`](integrations): OpenClaw and Feishu adapter packages
- [`.readthedocs.yaml`](.readthedocs.yaml): Read the Docs build config for the generated MyST manual catalog

## Maintenance rules

When command behavior, workflow ownership, or architecture boundaries change:

- update the owning document in the same change, and avoid restating the
  same rules in multiple docs
- **keep this README a roadmap and a map**: it changes only when the stable
  workflow topology, an entry point, a navigation pointer, or an
  editing-surface rule changes. Behavior and contract details go to the
  owning document (`build_doc_guide.md`, `hello_auto-doc.md`,
  `web_publish_pipeline.md`, …) with at most a one-line pointer here. Treat
  a README beyond ~350 lines as documentation debt.
- keep `python tools/check_maintainability_guardrails.py` green when
  touching the guarded hotspot files, and keep the PR checklist honest: if a
  helper boundary moves, update the module map in the same change
- keep history in
  [`code-as-doc/code_optimization_log.md`](code-as-doc/code_optimization_log.md),
  not in the current guides
