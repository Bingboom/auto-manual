# 基于「网页共享 IR + 多维表无字底图」生成 InDesign（`.idml` / `.indd`）—— 迁仓后三阶段落地实施计划

Status: proposed · on hold since 2026-11-24 · Created: 2026-11-23 · Updated: 2026-11-25

> **暂挂期间不启动本计划的 Day 0 及以后各步。** 重启条件（任一满足即由夏冰复评，见[执行台账 REV-39](manual_revitalization_execution.md#rev-39)）：REV-20 或 REV-40 开工、操作者启动共享层收敛、一次共享修改因缺少公共语义契约而无法可控地传到已冻结的整本包、出现没有现存 `.ai` 母版的新产品线，或多语种重排成为明显的人力瓶颈。
>
> - **决定**：2026-11-24 操作者决定印刷交付改走网页文档加直接修改现存 `.ai` 印刷母版，本计划暂挂、当前零研发投入；2026-11-25 评审确认，记录见[台账第 3 节决定表](manual_revitalization_execution.md)，REV-20、REV-26、REV-40 同步暂缓。
> - **印刷主线**：按审核稿或语料直接修改现存 `.ai` 印刷母版（[REV-55](manual_revitalization_execution.md#rev-55)），工作规则是原位改文字，刀版、出血与版面不动。网页文档仍按各自路线交付（含 `REV-48` 审核稿转网页候选）。
> - **本计划定位**：保留为远期技术储备与契约参考；下文是 2026-11-23 制定的方案，正文未按暂挂改写。

- **制定基线**：`origin/main` @ `0e7844f6e41c05b21c574dd52fa14ed28723cd75`（`#1809` 合入后）
- **前置审计依据**：`eval_20261122_ir_to_indesign.md`（2026-11-22 只读基线审计报告）
- **备选架构设计目标（启用后适用）**：**「基于 网页文档 + 多维表存底图 的方式 出 InDesign」**
  1. **网页文档（`manual.ir.json` / `manual-ir/v2` → `v2.1`）** = **唯一内容、结构与多语种活文字源**（包含章节正文、提示框、规格表、以及插图对应的多语种引线词条文字；**Git 仓内不重复塞入 `.ai` / 矢量 `.pdf` / 无字印刷底图大文件**）。
  2. **飞书多维表上传无字底图** = **唯一「无字底图（`.ai` / 矢量 `.pdf` / ≥300 DPI 无字底图）」存储、审批与映射中心**（底层表结构与字段契约见 §2.1；通过 `asset_key` / `web_replace_key` / Web 图 `content_sha256` 映射到 `text_policy="textless"` 的印刷导出附件，构建时按 SHA-256 拉取至本地缓存，绝不污染 Git）。
  3. **InDesign 合成器（`tools/idml/from_manual_ir.py`）** = **读取「网页文档活文字与语义结构」+ 从「多维表本地 SHA-256 缓存拉取无字底图」→ 自动叠放可编辑多语种引线/标签文本框 → 合成自包含 `.idml` → macOS K7 主机（`Adobe InDesign 2026 21.0.1.6`）输出 `.indd` 与 `PDF/X-4`**。
- **挂起红线与启用前置条件**：在重新立项启用本备选路线前，所有新模块（`--from-ir` / `from_manual_ir.py` 等）保持暂缓建设；既有 `build.py idml`（旧 `v1` RST→IDML）、`build.py web-package`、`ir-qc` 保持全绿。若未来触发启用，需严格遵守 `tools/check_maintainability_guardrails.py` 上限（`build.py <= 761`、`tools/export_idml.py <= 230`、`tools/idml/primitives.py <= 300`、`tools/idml/styles.py <= 220`、`tools/idml/package.py <= 160`）、`tools/utils/path_utils.py` 路径构造规范及 `tools/check_mypy_ratchet.py` 严格类型门禁。

---

## 1. 目标架构边界与「迁仓后环境对齐」前置检查清单（Day 0）

### 1.1 「网页活文字 + 多维表底图 → InDesign」双平面协同边界

```text
  ┌──────────────────────────────────────────┐        ┌───────────────────────────────────────────┐
  │       Git 仓：网页文档源平面              │        │     飞书「文档构建」Base (LD3lb4G1ua4GOVs1vxAc9W2enje)    │
  │  manual_sources/.../web/<lang>/          │        │  - 04_资产源文件 (tblsXlZx61Ff5pQC): .ai/.pdf 整本母版  │
  │  → manual.ir.json (manual-ir/v2 / v2.1)  │        │  - 04_资产定义   (tblWilXeN5FXPraC): asset_key ↔      │
  │  只存：                                   │        │    web_replace_key / text_policy / pin_layout_json       │
  │   • 章节正文 / 列表 / 表格 / 警示框        │        │  - 04_资产导出物 (tblavT0dcjZGK9DR): export_file 唯一   │
  │   • 19 类 HB-* ComponentSpec             │        │    附件池（web-composite 给网页；print+textless 给印刷）│
  │   • 多语种引线词条文字 + base_art_layout%  │        └─────────────────────┬─────────────────────┘
  │   • 轻量语义键 (asset_key/web_replace_key)│                              │
  │  (不塞无字印刷底图大文件进 Git)            │                              ▼ (build 时按需拉取 + SHA-256 校验)
  └─────────────────────┬────────────────────┘                [本地 Git 忽略缓存目录]
                        │                                     .cache/idml_base_art/<sha256[:2]>/<sha256>.pdf
                        └───────────────┬──────────────────────────────────┘
                                        ▼
                       [tools/idml/from_manual_ir.py + ir_asset_bridge.py]
                        • 解析网页活文字与排版语义 (manual-flow/v2 + ComponentSpec)
                        • 从缓存获取无字矢量底图 (.pdf/.ai/300DPI .png)
                        • 按 base_art_layout / overview_component_instances / pin_layout_json
                          在无字底图上方叠放独立解锁顶层 TextFrame + 原生矢量引线
                        • 复用 Cat A/E 底座 (styles / package / inline_text / params / delivery)
                                        ▼
                       [自包含 .idml + *_handoff.zip (Links/ + Document fonts/)]
                                        │
                        (内网 SMB / GitLab Runner / 队列传递，只传打包产物)
                                        ▼
                       [macOS K7 主机：Adobe InDesign 2026 (21.0.1.6)]
                        tools/indesign_finalize.py + tools/idml/indesign_finalize.jsx
                                        │ (导入 .idml -> 保存 .indd -> post_reopen 溢出/缺字/断链巡检)
                                        ▼
                       [.indd + PDF/X-4 (Japan Color 2001 Coated) + finalize_report.json]
```

### 1.2 Day 0 迁仓后环境对齐检查清单（全部通过方可启动 PR 1.1）

| 检查项 | 具体前置条件与配置要点 | 验证命令 / 验收标准 | 阻塞说明 |
|---|---|---|---|
| **D0-1 内网 GitLab 三仓与 CI 就位** | `auto-manual`、`Hello-Docs`、`Hello-Docs-Review` 迁移完成；`.gitlab-ci.yml` 对齐 `.github/workflows/manual-validation.yml` 核心门禁（`ruff`、`mypy`、`check_maintainability_guardrails`、`check_doc_link_integrity`、`check_reference_layout_pins`、`asset-check`、`web-ir-checks`、`tests.run_fast`）。 | 在 GitLab Runner / 本地执行：<br>`python -m ruff check build.py integrations tools tests scripts`<br>`python -m tools.check_maintainability_guardrails`<br>`python -m tools.check_mypy_ratchet check`<br>`python -m tests.run_fast --all` | 未对齐护栏门禁会导致热文件超限或类型回归合入主干。 |
| **D0-2 Python 3.12+ 构建环境** | 统一使用 Python `3.12`（对齐 CI），按 `requirements.lock` 安装 `pyyaml`、`beautifulsoup4`、`lxml`、`pymupdf`（PyMuPDF `1.28.0` / MuPDF `1.29.0`，用于配方与矢量核验）、`pillow`、`ruff`、`mypy==2.3.1`。 | `python3 --version` ≥ 3.12；<br>`python build.py ir-qc --ir-command audit --all-ir --max-warnings 422` 退出码 `0`。 | macOS 系统自带 Python 3.9 缺 `TypeAlias` 会直接报错。 |
| **D0-3 飞书 `04_资产*` 三表读取与缓存权限** | 构建机与 CI Runner 可访问飞书开放平台；`lark-cli` 已登录且具备 `文档构建` Base（`base_token="LD3lb4G1ua4GOVs1vxAc9W2enje"`，见 `data/asset_base_bindings.json`）中 `04_资产源文件`（`tblsXlZx61Ff5pQC`）、`04_资产定义`（`tblWilXeN5FXPraC`）、`04_资产导出物`（`tblavT0dcjZGK9DR`）读权限与附件下载权限；本地及 CI `.gitignore` 已排除 `.cache/idml_base_art/`（建议配 GitLab Runner cache）。 | `python -m tools.web.external_source_store check`<br>用 `lark-cli base +record-download-attachment` 对 `recvpvE4YHA8rW` 试拉取 `04_资产源文件` 或 `04_资产导出物` 一份附件并核对 SHA-256 一致。 | 缺此通道则 Stage 2 无法从多维表拉取无字底图；Stage 1 仅靠已有样例验证。 |
| **D0-4 K7 macOS InDesign 主机对齐与传送通道** | 至少 1 台（推荐按 [`indesign_second_host_runbook.md`](indesign_second_host_runbook.md) 配齐 2 台）macOS 主机锁定安装 **`Adobe InDesign 2026 21.0.1.6`**（见 `tools/idml/indesign_version_pin.json`）、`poppler`（`pdfinfo`/`pdftoppm`）、授权 `Gilroy` 商业字体（`AUTO_MANUAL_LOCAL_GILROY_DIR`）；打通 GitLab Runner / 工作站 ↔ K7 的 `*_handoff.zip` 投递与 `finalize_report.json` 回传路径。 | 在 K7 主机运行：<br>`python build.py doctor`<br>`python -m tools.indesign_finalize --check-host` 报匹配；并用既有样本跑通 `--idml ... --indd ... --pdf ... --report ...`。 | 无 K7 通道则无法生成原生 `.indd` 与做 `post_reopen` 溢出实测。 |
| **D0-5 离线字体与印刷 ICC 配置** | 确认仓内 `fonts/idml_portable/`（`HBManualSansJP-Regular.ttf` 等）完整随仓拉取；K7 InDesign 装齐 `PDF/X-4:2008 (Japan)` 导出预设与 `Japan Color 2001 Coated` ICC 描述文件。 | `python build.py asset-check --config configs/config.us.yaml --model JE-1000F --region US` 退出码 `0`。 | 缺字体或 ICC 预设将导致 `PDF/X-4` 预检拦截。 |

---

## 2. 「飞书多维表存底图 + 网页活文字」核心数据契约与工作流（落地前定稿）

> **核心审计发现（`origin/main` 已具备 95% 的多维表字段与同步模式）**：
> 仓内 [`data/asset_base_bindings.json`](../../data/asset_base_bindings.json)、[`bitable_schema/business_base_manifest.json`](../../bitable_schema/business_base_manifest.json) 与 [`tools/sync_web_composites.py`](../../tools/sync_web_composites.py) 已经建好了 **Base `LD3lb4G1ua4GOVs1vxAc9W2enje` 下的三张 `04_资产*` 表**及附件下载/SHA-256 校验基础设施，**不需要重建新表**！目前唯一欠缺的是：现行同步代码（`sync_web_composites.py`、`sync_asset_registry.py`）只服务于 Web 组合图与 7 列元数据，尚未对 **`artifact_kind="print"` + `text_policy="textless"` 的印刷无字底图** 打通拉取、缓存和到 `manual.ir.json` 的四级反查解析。

### 2.1 三张 `04_资产*` 表的职责边界、现有字段实况与最小字段增补建议

| 多维表名称与冻结 ID | 在本架构中的角色定位 | 已冻结的关键字段（`origin/main` 实测直接复用） | 最小 Schema 增补评估（**可选，不强制阻塞**） |
|---|---|---|---|
| **`04_资产源文件`**<br>`table_id="tblsXlZx61Ff5pQC"`<br>`view_id="vewZcSuiUo"` | **整本设计源文件总库**（`.ai` / 可编辑母版 PDF 源档案，用于溯源与配方批量榨取） | `source_key` (`fldlfvU5xL`), `source_kind` (`fldpHUzuJf`), `source_format` (`fldyTORf4q`), `source_scope_model`/`region`/`lang`, `source_file` **附件** (`fld7mKmLck`), `asset_package` **附件** (`fldo1DsEnC`), `manifest_file` **附件** (`fldgLFumZC`), `source_sha256` (`fldRPZ0gfJ`), `archive_status` (`flduowSU6p`: `待校验`/`已归档`/`隔离`) | **0 改动**（字段已 100% 完备；现有 `data/asset_sources.csv` `55` 条记录中多条已带该表直链）。 |
| **`04_资产定义`**<br>`table_id="tblWilXeN5FXPraC"`<br>`view_id="vew0gl8yYS"` | **逻辑资产主档 & 网页 ↔ 印刷无字底图绑定枢纽**（网页用图与印刷无字底图共享同一行 `asset_key`） | • 身份与网页映射：`asset_key` (`fldrnL0cQA`), **`web_replace_key` (`fldWQ5ktWG`)**, `override_for` (`fldJp29f3p`)<br>• 文字策略与状态：`category` (`fld565X3hJ`), `language_dimension` (`fldrED1SWb`: `中立`/`按语言`), **`text_policy` (`fld1aQJEhS`: `textless` / `numeric-only` / `fixed-product-markings` / `localized-full-page` / `localized-composite` / `shared-composite`)**, **`textless_pending` (`fld3YAsCu7`)**, `status` (`fldMhgSQj7`: `✅成品`/`🔧临时替代`/`❌缺失`/`⛔隔离`), `gate_status`, `build_eligible`, `visual_review_required`<br>• 适用域与母版关联：`model_scope`, `region_scope`, `language_variants`, `source_key` (`fld3NoyDxB`), `source_record` (`fldCZgaR8F`), `source_page`, `source_crop`, `preview` 缩略图 (`fldGtEpu8Y`, **严禁作构建输入**) | **建议新增 1 个多行文本字段 `pin_layout_json`（可选）**：当某个旧网页图在 `manual.ir.json` 中未自带 `base_art_layout`、也未入 `overview_component_instances.json` 时，可直接在该行存标准归一化框/引线 JSON（schema 兼容 `base_art_layout`：`labels: [{line, rect: [x%, y%, w%, h%], leader_pts?, fill?, color?}]`），无需改业务代码或重编网页包。 |
| **`04_资产导出物`**<br>`table_id="tblavT0dcjZGK9DR"`<br>`view_id="vewHmmr2Pn"` | **唯一单图附件交付入口**（一物一行，`export_file` 存成品图或无字底图实体文件） | • 唯一附件：**`export_file` (`fldaVpvPXr`)**<br>• 分类与双端路由：**`artifact_kind` (`fldbEDyEYw`)** — 已有 **`print`**、**`web-composite`**、**`web-shared`**、**`web-target`**、**`semantic-export`**、**`word`**、**`preview`**、**`archive-page`**；**`format` (`fldBl4UUXI`)** — 已有 **`pdf` / `png` / `jpg` / `jpeg` / `svg` / `webp`**；**`text_policy` (`fldpSHpb4n`)**（文本框，填 `textless`/`numeric-only`/`fixed-product-markings` 等）<br>• 关联与校验：`asset_key` (`fldTT2y0yq`), `asset_record` (`fldA2vhgTZ` 关联定义表), `source_record`, `locale`, `web_locale` (`en`/`fr`/`es`/`shared`), `content_sha256` (`fldojPSPK5`), `source_fragment_sha256`, `size_bytes`, `像素尺寸`, `透明通道`, `对账结果`, `gate_status` (`approved`/`temporary`/`pending`/`quarantine`/`archive`), `build_eligible`, `visual_review_required` | **可选微调 `format` 单选字段加 `"ai"`**：`export_file` 附件本身可存 `.ai`，但当前 `format` 枚举只含 `pdf/png/jpg/jpeg/svg/webp`。**最佳实践是约定设计师导出「Illustrator 单图矢量 `.pdf`」（CMYK/矢量轮廓，InDesign 原生支持最佳），此时 0 改动即可用 `format="pdf"`**；如确需直接上传单图 `.ai`，在 `format` 下拉加一个 `"ai"` 选项即可。 |

### 2.2 设计师 / 操作者「上传与维护无字底图」两条标准路径

1. **路径 A（日常精修单图上传 —— 设计师最轻量路径，零 Git 提交流程）**
   - **步骤 1（切无字底图）**：设计师在 Illustrator / InDesign 中关闭文字与引线图层，另存/导出单裁切框尺寸的 **矢量 `.pdf`**（首选，不失真且保留专色/CMYK；其次 300+ DPI 透明背景无字 `.png`）。
   - **步骤 2（在 `04_资产定义` 确认身份）**：定位或新建对应 `asset_key` 行（如 `overview/front_controls`、`operation/je1000f_eu/main_power`、`connections/jbp2000b/jp/stacking_guidance`），确保填好 `web_replace_key`（如有对应网页插图槽位，如 `product-overview.front`、`operation.main-power`、`reference.charging-car`）、`model_scope`、`region_scope`，在无字底图就位后把 `textless_pending` 置为 `FALSE`。
   - **步骤 3（在 `04_资产导出物` 上传附件并放行）**：新增或更新一条导出物行：
     - `export_key`：`print::<model>_<region>::<asset_key>`（命名空间独立于现有 `registry::`、`web-composite/`）；
     - `asset_record`：关联回 `04_资产定义` 对应记录（同步填 `asset_key`）；
     - `export_file`：上传无字矢量 `.pdf`（或 300+ DPI 无字 `.png`）；
     - 路由字段：`artifact_kind = "print"`、`format = "pdf"`（或 `"png"`）、`text_policy = "textless"`（或 `"numeric-only"` / `"fixed-product-markings"`）、`web_locale = "shared"`、`locale = "und"`；
     - 门禁字段：`gate_status = "approved"`、`build_eligible = TRUE`、`visual_review_required = FALSE`（`content_sha256` 可由人工填入或由同步校验工具自动回填校验）。
2. **路径 B（整本设计母版配方批量榨取 —— 复用 `tools/asset_intake.py`）**
   - 整本 `.ai`/可编辑 PDF 归档至 `04_资产源文件.source_file`，通过 `data/asset_recipes/<model>_*.json` 中的 `crop` + `redact_text` + `remove_if_touched` + `drop_leader_strokes` 确定性剥离标注文字和旧引线，批量产出的 `outputs[].format == "pdf"`（`text_policy="textless"`）经 `tools/asset_pipeline/base_reconcile.py` 批量上传至 `04_资产导出物` 并经 12× 图对账审批。

### 2.3 网页文档（`manual.ir.json`）怎么关联无字底图与多语种活文字

为同时盘活**仓库既有 `330` 份 `manual.ir.json`** 与 **后续新建网页文档**，确立以下双向契约：

1. **网页文档侧的黄金准则（不放重资产，只放活文字 + 语义键 + 可选相对坐标）**：
   - **新建/重编网页手册（`tools/web/document_source.py` & `tools/component_specs/`）**：
     - 凡属「图+多语种引线/标签」的组件（`HB-SPECIAL-OVERVIEW`、`HB-SPECIAL-OPERATION`、`HB-SPECIAL-REFERENCE-FIGURE`），在 Web 构建执行 `apply_illustration_replacement()` / `_consume_covered_annotations()` 前，**必须将 `asset_key`（优先）或 `web_replace_key`、全部多语种活词条（`captions` / `steps` / `callouts`）及归一化百分比坐标 `base_art_layout`（如有）完整写入 `ComponentSpec.slots` / `metadata` 并序列化进 `manual.ir.json`**；
     - 即使网页 HTML 出于浏览效果在 `assets/` 里展示的是预合成 Web 小图（`web-composite` PNG），**活文字列表与结构化槽位在 `manual.ir.json` 中绝不被删丢**；
     - 常规流程内 `image` 节点（如按钮图标、连接示意图）在 `ManualIR v2.1`（或允许 `flow` 附加元信息）中可选携带 `asset_key`，Git 仓 `web/<lang>/assets/` 只存轻量 Web PNG/SVG，**严禁向 Git 提交任何印刷级 `.ai` 或无字 `.pdf` 底图**（受 `tools/web/external_source_store.py` Raw Binary Ratchet 护栏强制拦截）。
   - **已封存的 `330` 份历史 `manual.ir.json`（恪守 `N4` 原则，0 原地修改）**：
     - 保持文件字节与 `content_sha256` 原封不动；其中如 `JA-AD600A/EU` 等采用 `base-art-live-copy` 或已保留 `carrier_flow`（`image` + `.line` 文本行列表）的 `manual.ir.json` 已天然拥有活文字与 `web_replace_key`；其余采用整图 PNG 的历史包则通过下方的 **4 级反查链**自动溯源至多维表无字底图。

2. **IDML 合成器解析无字底图的 4 级确定性路由链（`tools/idml/ir_asset_bridge.py`）**
   针对 `manual.ir.json` 中的每一张图片或组件视觉引用，按严格优先级匹配 `data/print_base_manifest.json`（由飞书 `04_资产*` 同步生成，纯元数据索引，无二进制）：
   - **Tier 1 — 语义 `asset_key` / `asset:<key>` 直连**（优先）：直接命中 `04_资产定义[asset_key]`；
   - **Tier 2 — `web_replace_key` + 目标作用域 `(model, region)` 映射（Web↔Print 核心桥梁）**：从 `ComponentSpec.metadata["web_replace_key"]`（如 `product-overview.front`、`operation.main-power`、`reference.charging-car`）反查 `04_资产定义.web_replace_key`，再结合 `model_scope` / `region_scope` / `override_for` 唯一锁定 `asset_key`；
   - **Tier 3 — 网页图片字节 `sha256` 逆向查表（兼容 `330` 份历史 IR）**：计算 `manual.ir.json` 引用的本地 PNG/SVG 的 SHA-256 → 在 `04_资产导出物.content_sha256`（或 `data/asset_registry.csv`）中检索该成品图属于哪个 `asset_key` → **同 `asset_key` 跳转检索其印刷无字导出物**；
   - **选取印刷无字导出物附件规则（同 `asset_key` 下过滤）**：
     - 筛选 `04_资产导出物`：`gate_status == "approved"` AND `build_eligible == True` AND `artifact_kind == "print"`（兼容旧库 `web-shared` 纯矢量 `.svg` 图标）AND `text_policy in {"textless", "numeric-only", "fixed-product-markings"}`；
     - 排序权重：**矢量 `.pdf`（首选） > 原生 `.ai` > 矢量 `.svg` > ≥300 DPI 无字 `.png`**；
     - 校验并命中本地 SHA-256 缓存 `.cache/idml_base_art/<sha256[:2]>/<sha256>.<ext>`（本地不存在则经 `lark-cli` 下载并立即校验 `content_sha256`，随后由 `build_delivery_package()` 拷贝重命名至 `Links/`）；
   - **Tier 4 — 安全拦截与降级边界（Fail-Closed for Dirty Web PNGs）**：
     - 对图标/纯装饰矢量 `.svg` 或定义已确认 `text_policy == "textless"` 且 ≥300 DPI 的图，允许直接链接缓存/包内高分图；
     - 对 **带有烘焙文字的 Web 成品 PNG（`text_policy` 为 `localized-composite`/`shared-composite`，或 <300 DPI 低分图且无对应 `print`+`textless` 记录）**，Stage 1 原型期输出警示与占位链接以便先看整体流排版，**Stage 2 起严格 fail-closed 拦截并生成《待美工上传无字底图清单（按 `asset_key` / `web_replace_key` 分组）》，美工仅需在飞书 `04_资产导出物` 传好图、重跑同步与编译即可放行**。

3. **无字底图 + 网页活文字的 3 种自动叠加模式**
   - **模式 1（`HB-SPECIAL-OVERVIEW` — 整机正反面引线总览）**：从 `manual.ir.json` 抽取多语种 `callouts` 文本，从 `docs/renderers/contracts/overview_component_instances.json` 取目标 `idml` 精确 `pt` 坐标（`art_rect`、`callouts[].rect`、`align`、`leader` 折线点），直接复用 `tools/idml/page_overview.py` 生成底层锁框底图 + 独立图层可编辑文本框 + `0.3pt` 矢量引线。
   - **模式 2（`HB-SPECIAL-REFERENCE-FIGURE` 与 `HB-SPECIAL-OPERATION` — `base_art_layout` / `pin_layout_json` 归一化映射）**：给定无字底图在 IDML 页面中的放置框 `(art_x, art_y, art_w, art_h)`（单位 `pt`），将 `ComponentSpec.metadata.base_art_layout`（或来自多维表 `04_资产定义.pin_layout_json`）中的 `%` 百分比坐标映射为精确 `pt` 坐标（`x_pt = art_x + x%*art_w/100`，`y_pt = art_y + y%*art_h/100`），并可选配白色/浅灰背景遮罩块（`fill`）与原生矢量引线（`leader_pts`），随后调用 `tools/idml/components/oppanel.py::_editable_text_frame()` 把 `manual.ir.json` 的多语种词条以独立解锁顶层文本框叠加到底图上方。
   - **模式 3（整页锁定型图，如合规封面/已本地化整页 PDF）**：若 `text_policy == "localized-full-page"`，按 `(asset_key, language)` 直接取对应语种的矢量 `.pdf` 原样置入页面框，不额外叠字。

---

## 3. 现有模块复用地图（精确到文件与目录级）

基于对 `tools/idml/`（`125` `.py` / `40,041` LOC）、`tools/component_specs/`（`48` 文件）、`tools/manual_ir/`（`22` 文件 / `4,310` LOC）、`tools/asset_pipeline/`（`9` 文件）及 `tools/web/` 的 AST 与引用审计，全仓模块按如下策略处置：

| 处置策略 | 模块 / 文件路径 | 规模与职责 | 在「网页 + 多维表底图 → IDML」方案中的用法与边界 |
|---|---|---|---|
| **直接复用（Reuse As-Is）** | `tools/idml/package.py`, `writer.py` | 147 + 413 LOC；ZIP OCF 规范、`designmap_xml()`、`add_spread_chain()`、`IdmlWriter` 宿主 | 直接作为最终 `.idml` 物理打包与 Spread 生成核心；注意锚定子故事 `st_anchor_` 必须反序置于宿主之后。 |
| **直接复用（微调解耦）** | `tools/idml/styles.py`, `style_resources.py`, `style_names.py`, `paragraph_style_attrs.py`, `app_text_styles.py` | ~615 LOC；生成 `Styles.xml`/`Graphic.xml`/`Fonts.xml`/`Preferences.xml` | 复用全部印刷样式与色板定义；仅需把 `styles.py` 对 `loaders.normalize_lang` 的导入切至 `tools.lang_registry.canonical_language` 以解除旧 loader 耦合。 |
| **直接复用（微调解耦）** | `tools/idml/primitives.py`, `inline_text.py`, `character_metrics.py`, `line_metrics.py`, `table_borders.py`, `page_objects.py`, `story_frames.py`, `asset_geometry.py`, `corner_radii.py`, `stable_ids.py`, `params.py` | ~3,100 LOC；`psr()`、`cell()`、`image_cell_content()`、`path_geometry()`、CJK/Hangul/Symbol 字族自动切分、字符宽估算、`layout_params.csv` 解析 | 新编译器直接调用 `primitives`、`inline_text.character_ranges()`、`page_objects`；注意不要调 `primitives.clean_text()`（旧正则删 RST 标记，IR v2 已是干净语义文本）。 |
| **直接复用（100% 零改动）** | `tools/idml/check.py` (`check_idml`), `delivery.py` (`build_delivery_package`), `font_family.py`, `font_assets.py`, `pdf_parity_visual.py`, `indesign_finalize.jsx`, `indesign_finalize_batch.jsx`, `indesign_version_pin.json`, `tools/indesign_finalize.py`, `tools/indesign_finalize_jobs.py`, `tools/release_indesign_package.py` | ~2,750 LOC；IDML XML/字体检查、收集外链进 `Links/` 并打包 `Document fonts/` + `*_handoff.zip`、K7 ExtendScript 落盘 `.indd` 与 `PDF/X-4` | **完全输入无关**，尤其 `build_delivery_package()` 天然兼容把 `.cache/idml_base_art/` 下的本地绝对文件 URI (`file://...`) 收集去重并重写为相对 `file:Links/<name>` 收进送印便携包。 |
| **直接复用（多维表附件拉取参照与基座）** | `data/asset_base_bindings.json`, `tools/sync_web_composites.py`, `tools/web/composite_manifest.py`, `tools/web/external_source_store.py`, `tools/asset_pipeline/extract.py`, `base_reconcile.py` | 业务 Base 坐标、`export_file` 下载 + `content_sha256` 原子落盘校验、`lark-cli` 封装、`pymupdf` 无字剥离引擎 | `sync_print_base_art.py` 完全复用 `sync_web_composites.py` 与 `external_source_store.py` 的原子下载与 SHA-256 校验范式，面向 `artifact_kind="print"` + `text_policy="textless"` 同步 `data/print_base_manifest.json` 索引与按需本地缓存。 |
| **直接复用（几何/参数基座）** | `data/layout_params.csv` (`1,103` 行), `data/layout_params.idml-compact.csv`, `data/layout_params.idml-je3000c-kr.csv`, `docs/renderers/contracts/overview_component_instances.json`, `tools/web/base_art_reference.py`, `tools/web/base_art_operation.py` | 印刷尺寸/字号/语言 token；6 组 Overview 双端坐标；`base_art_layout` 校验与分割算法 | `params.load_layout_params()` 直接复用；`base_art_operation._split_summary` / `base_art_reference` 逻辑模式可对照用于 IDML 活文字标签抽取与坐标转换。 |
| **增量扩展（Extend）** | `tools/idml/components/__init__.py` (`REGISTRY`), `tools/idml/components/base.py` (`RenderContext`), `oppanel.py`, `reference_figure.py`, `spec_tables.py`, `prose_table.py`, `native_marker.py`, `page_toc.py`, `page_folio.py`, `page_placed.py`, `page_overview.py`, `data_stories.py` | 底层绘制与 `17` 个已注册 IDML 组件渲染器 | `RenderContext.resolve_bundle_image()` 挂接 `ir_asset_bridge.py` 解析本地多维表底图缓存；扩展 `oppanel._editable_text_frame()` 与 `reference_figure.py` 支持 `base_art_layout` / `pin_layout_json` `% → pt` 叠字；补齐剩余 4 类表与跨行/跨列 `RowSpan`/`ColumnSpan`、4N 折手补白。 |
| **增量扩展（IR 与 Sync 入口）** | `tools/manual_ir/{model,flow,validate,document}.py`, `tools/component_specs/*_adapters.py`, `tools/web/document_source.py`, `tools/sync_asset_registry.py`, `tools/build_cli.py`, `tools/build_dispatch.py` | Shared IR 契约、19 类 `idml_*` 适配器、Web 组装与 CLI | `tools/component_specs/` 补全 `signal_key`、参考图与不扁平 `HB-TABLE-SPEC` 投影；`document_source.py` 保留语义 `asset_key`/`web_replace_key` 与活标注；`build_dispatch.py` 挂载 `--from-ir`。 |
| **绕过并最终退役（Bypass → Stage 3 Retire）** | `tools/manual_ir/prepared_rst.py`, `tools/idml_rst_extract*.py`, `tools/idml/ir_sidecar.py`, `tools/idml/ir_projection.py` (`v1`), `reference_export.py`, `prose_flow.py`, `shared_page.py`, `latex_page_plan.py`, `loaders.py`, `flow_md.py`, `target_assembly_plan.py`, `reference_layout_plan.py` | ~`13,600` LOC（Cat B + Cat C）；依赖 RST 目录、Sphinx `.. only::`、LaTeX 页码测量及 CSV 裸读 | Stage 1–2 **完全不动**，保障旧 `build.py idml` 零回归；Stage 3 全线切入共享 IR 后分批退役瘦身，同时推进清理 `2.41 GiB` Git 仓历史冗余二进制。 |

---

## 4. Stage 1（第 1–2 周）：单型号原型样张跑通（PoC）

**核心验证目标**：在不触碰 `330` 份历史 `manual.ir.json` 与不改动旧版 `build.py idml` 的前提下，证明「**网页 `manual.ir.json (v2)` 活文字 + 飞书多维表抽样底图拉取缓存 → 程序化合成 `.idml` → K7 InDesign 落盘 `.indd` + PDF**」端到端闭环可跑通。

### 4.1 试点目标选型与理由

| 候选目标 | 仓内既有 `manual.ir.json` (`v2`) | 既有印刷几何与测试资产 | 试点分工与推荐理由 |
|---|---|---|---|
| **`JE-3000C/KR` (`ko`)** | **已有**<br>`manual_sources/JE-3000C/KR/ko/git-20261021-78316033/web/ko/manual.ir.json` | `target_assembly/je3000c_kr_v1_candidate.json` + `overview_component_instances.json` (`je3000c-kr-v1`) + `data/layout_params.idml-je3000c-kr.csv` | **首选主试点**：零前置构建门槛，直接消费仓内已有 `v2` IR；涵韩文/符号混排（验证 `NanumGothic` 切分）、Spec/LCD/Symbols/Troubleshooting/Overview，体量精炼，K7 反馈周期极短。 |
| **`JBP-2000B/EU` (`fr/de/es/...`)** | **已有**<br>`manual_sources/JBP-2000B/EU/.../web/*/manual.ir.json`（16 份） | `target_assembly/jbp2000b_eu_v1_candidate.json` + `data/layout_params.idml-compact.csv` | **拉丁多语补测试点**：验证 `compact` 紧凑开本参数叠加与欧规法/德/西长句自动流转。 |
| **`JE-1000F/US` (`en`)** | **可由 `build.py md` 现生成**<br>（源码在 `docs/_review/JE-1000F/US`） | **全仓唯一已批准 58 页参考合约** `reference_layout/je1000f_us_v2_20260605.json` + `je1000f-us-v1` + 已归档母版 `recvpvE4YHA8rW` | **黄金对照标尺**：在 Stage 1 后半程用于核对“新 IR→IDML”与“旧 58 页已批稿”的内容零丢失，并率先验证 `overview/front_controls` 从多维表拉取无字底图 + 叠字还原！ |

### 4.2 Slice-by-Slice PR 计划（Stage 1：4 个小颗粒 PR）

> **Guardrail 红线**：不向 `tools/export_idml.py`（上限 `230` LOC）、`build.py`（上限 `761` LOC）、`tools/idml/primitives.py`（上限 `300` LOC）堆业务逻辑；所有新编译代码写入独立新模块（单文件 < `400` LOC），全量标注 Python 3.12 类型并通过 `mypy`。

#### PR 1.1：`feat(idml): add ManualIR v2 flow-to-IDML Story/Spread compiler prototype`
- **新增文件**：
  - `tools/idml/from_manual_ir.py`（主编译编排器，~340 LOC）
  - `tools/idml/ir_flow_emitter.py`（`manual-flow/v2` AST 递归发射器，~280 LOC）
  - `tests/test_idml_from_manual_ir.py`
- **核心实现**：
  1. `compile_manual_ir_to_idml(ir_path: Path, out_idml: Path, *, layout_params_csv: Path | None = None, layout_param_overlays: tuple[Path, ...] = (), asset_resolver: AssetResolver | None = None) -> IdmlCompileSummary`：
     - 调用 `tools.manual_ir.read_manual_ir(ir_path)` 与 `tools.manual_ir.document.validate_document(ir)`；校验 `ir.schema_version == V2_SCHEMA_VERSION`。
     - 通过 `tools.idml.params.load_layout_params()` 加载 `data/layout_params.csv` 及目标 overlay，初始化 `IdmlWriter(params, model=ir.model, region=ir.region, language=ir.language)`。
  2. `ir_flow_emitter.py` 遍历 `ir.pages` → `block.payload`（`manual-flow/v2` 全部节点类型）：
     - `heading (level=1..6)` → `HB H1` / `HB Title L2` / `HB Title L3`；
     - `paragraph` / `quote` / `preformatted` → `HB Body`；递归渲染行内富文本 `strong` / `emphasis` / `superscript` / `subscript` / `link` / `line_break` / `text`，文本叶子通过 `inline_text.character_ranges()` 完成 CJK/Hangul/Symbol 安全分段；
     - `list` / `list_item` → `HB List` / `HB Sublist`（尊重 `ordered`/`start`）；
     - `image` / `figure` → 通过注入的 `asset_resolver` 解析图片路径（Stage 1 允许默认 fallback 到 `ir_path.parent / node["source"]`），调 `primitives.image_cell_content()` + `components.base.figure_paragraph()` 置入链接矩形；
     - `table` → 抽取表头与行矩阵，调用 `table_borders.component_table_xml()` 输出可编辑原生表格（Stage 1 对 `row_span`/`column_span` 先打警告并铺平，Stage 2 补齐跨格）。
  3. 按 `ManualPage` 切分 Story，使用 `package.pages_for_height()` 与 `package.add_spread_chain()` 连续生成 Spread 链；落地 `.idml` 后调用 `font_assets.provision_document_fonts()` 与 `check.check_idml()` 验证 0 结构错误。
- **验收**：单测构造含韩文/中文/加粗/上下标/表格/图片的 `v2` IR JSON，输出 `.idml` 且 `check_idml()` 返回空错 list。

#### PR 1.2：`feat(idml): wire existing ComponentSpec adapters into ManualIR v2 IDML compiler`
- **新增/修改文件**：
  - `tools/idml/ir_component_bridge.py`（~260 LOC）
  - 修改 `tools/idml/ir_flow_emitter.py`（遇到 `node["kind"] == "component"` 时委派给 `ir_component_bridge.dispatch_component_spec()`）
  - `tests/test_idml_ir_component_bridge.py`
- **核心实现**：
  1. 优先复用 `tools/component_specs/` 中已输出对齐 `tools/idml/components/__init__.py::REGISTRY` 的 **7 组适配器**（共覆盖库内半数以上实例化组件）：
     - `HB-CALLOUT-STRIP` → `adapters.idml_notice_payload(spec)` → `REGISTRY["notice"]`
     - `HB-SPECIAL-FCC` → `fcc_adapters.idml_fcc_payload(spec)` → `REGISTRY["fcc"]`
     - `HB-SPECIAL-INBOX` → `inbox_adapters.idml_inbox_payload(spec)` → `REGISTRY["inbox"]`
     - `HB-SPECIAL-OPERATION` → `operation_adapters.idml_operation_payload(spec)` → `REGISTRY["oppanel"]`
     - `HB-TABLE-LCD-MODE` → `lcd_mode_adapters.idml_lcd_mode_payload(spec)` → `REGISTRY["lcdmode"]`
     - `HB-WARRANTY-LEAD` / `HB-WARRANTY-SECTION` / `HB-WARRANTY-YEARS` → `warranty_adapters.idml_warranty_payload(spec)` → 对应 `REGISTRY["warrantylead"|"warrantysection"|"warrantyyears"]`（同步发射 `following_blocks`）
     - `HB-TABLE-SPEC` → `spec_table.idml_spec_table_rows(spec)` → `primitives.spec_table()`
  2. 对 Stage 1 暂未接入原生绘制的组件（`HB-SPECIAL-OVERVIEW`、`HB-SPECIAL-REFERENCE-FIGURE`、`HB-TABLE-LCD-ICON`、`HB-TABLE-TROUBLESHOOTING`、`HB-TABLE-SYMBOL-*`、`HB-SPECIAL-APP`、`HB-TABLE-KEY-COMBINATIONS`、`HB-TABLE-AUTO-RESUME`、`HB-TABLE-REFERENCE`）：**优先递归发射其 `carrier_flow`**；无 `carrier_flow` 时用其现有投影函数转为通用可编辑表格——**保证 100% 不丢网页文字、不向版面漏出任何 JSON 字段名**。
- **验收**：编译真实的 `JE-3000C/KR` `manual.ir.json`，所有 `HB-*` 组件正确渲染或完整保留文字，`check_idml()` 零报错。

#### PR 1.3：`feat(cli,idml): expose build.py idml --from-ir with Bitable prototype base-art hook & handoff packaging`
- **新增/修改文件**：
  - `tools/idml/ir_asset_bridge_lite.py`（Stage 1 轻量试跑资产桥，~140 LOC：支持接受一份 `--print-base-map <json>` 或按需通过 `tools.web.external_source_store` 从飞书拉取样本无字底图放进 `.cache/idml_base_art/`，未命中时暂由 IR 包内路径兜底并在报告标记 `[fallback-web-art]`）
  - 修改 `tools/build_cli.py` & `tools/build_dispatch.py`（为 `idml` 增加 `--from-ir <path>`、`--asset-cache-dir`、`--print-base-map` 可选参数；在 `_dispatch_idml_action()` 中检测 `--from-ir` 时直接走 `from_manual_ir.py` + `tools/idml/delivery.py::build_delivery_package()` 生成 `*_handoff.zip`，**完全绕过旧 `build.py rst/pdf` 与 `tools/export_idml.py`**）
  - 修改 `tools/utils/path_utils.py`（增加 `idml_base_art_cache_of(base)` 路径 helper，不硬编码缓存路径片段）
  - `tests/test_build_idml_from_ir_cli.py`
- **核心实现**：
  - 典型试跑命令：`python build.py idml --config configs/config.kr.yaml --from-ir manual_sources/JE-3000C/KR/ko/git-20261021-78316033/web/ko/manual.ir.json`
  - 输出落在隔离目录 `docs/_build/<MODEL>/<REGION>/<lang>/idml_from_ir/`：包含 `.idml`、`Document fonts/`、`*_handoff.zip`（`Links/` 中同时验证写入真实从多维表拉取来的本地缓存底图）及 `ir_compile_report.json`（清单列出已命中多维表底图、暂用 Web 图兜底的插图与回退 `carrier_flow` 组件清单）。
- **验收**：对 `JE-3000C/KR`、`JBP-2000B/EU` 生成完整 `*_handoff.zip`，`build_delivery_package()` 报 `missing == []`；手动给 `JE-1000F/US` 接上从 `04_资产导出物`/`recvpvE4YHA8rW` 拉下的 1–2 张 `overview` 样本矢量底图验证可顺利打包进 `Links/`。

#### PR 1.4：`test(idml): K7 host prototype verification on JE-3000C/KR & JE-1000F/US`
- **操作与验收（沉淀测试证据，无核心功能扩张）**：
  1. 将 `JE-3000C/KR` 的 `*_handoff.zip` 投递至 K7 macOS 主机运行 `python -m tools.indesign_finalize --idml ... --indd ... --pdf ... --report ...`。
  2. 对 `JE-1000F/US` 先执行 `build.py md --source review-asis --config configs/config.us-en.yaml` 生成其 `manual.ir.json (v2)`，再执行 `build.py idml --from-ir ...` 送 K7 产出 `.indd` + 样张 PDF，与已批准的 `je1000f_us_v2_20260605.json`（58 页）逐章节交叉对比内容完整度。
  3. 沉淀试跑验证报告至 `code-as-doc/tests/` 并同步更新目录索引以通过 `check_doc_link_integrity`。

### 4.3 Stage 1 退出门槛（Exit Gate）
1. `ruff`、`mypy`、`check_maintainability_guardrails`、`check_doc_link_integrity`、`tests.run_fast --all` 全部绿灯，**旧 `build.py idml` 测试零退化**；
2. 至少 1 个原生共享 IR 型号（`JE-3000C/KR`）和 1 个对照型号（`JE-1000F/US` / `JBP-2000B/EU`）通过 `build.py idml --from-ir` 生成 `.idml` 且 `check_idml()` 返回 **`0` 错误**；
3. 在 **macOS K7 Adobe InDesign 2026 (`21.0.1.6`)** 上免人工修改一键打开 `.idml`、生成 `.indd` 并导出 PDF：**`0` XML 结构错误、`0` 断链（`bad_links == []`）、全部正文章节/警示框/表格活文字 100% 落地**，且至少验证过 1 张从飞书多维表下载缓存的无字矢量底图成功进入 `.indd` 链接（本阶段允许尚存部分组件需等 Stage 2 上原生叠字、存在可跟踪页数/溢流差距）。

---

## 5. Stage 2（累计第 3–5 周）：多维表底图全自动解析、活文字引线叠放与印刷版式补齐（试产可用 / `REV-40` 验收）

Stage 2 彻底打通 **「网页共享 IR（只存文本与结构）+ 飞书多维表（唯一无字底图库）」** 的生产级联动，完成审计缺口 ①–④ 闭环，满足小批量新机种试产（对应台账 `REV-39` 与 `REV-40` `JBP-2000B/JP`）。

### 5.1 Slice-by-Slice PR 计划（Stage 2：5 个 PR）

#### PR 2.1：`feat(assets,idml): sync Bitable print base-art index (04_资产*) & build SHA-256 local cache resolver`
- **核心设计（零二进制进 Git！）**：
  - **新增 `tools/sync_print_base_art.py`**（严格复用 `tools/sync_web_composites.py` 与 `tools/web/external_source_store.py` 模式）：
    1. 连接 `文档构建` Base (`LD3lb4G1ua4GOVs1vxAc9W2enje`)，拉取 `04_资产定义` (`tblWilXeN5FXPraC`) 与 `04_资产导出物` (`tblavT0dcjZGK9DR`)；
    2. 生成轻量纯文本 JSON 清单 **`data/print_base_manifest.json`**（`schema_version="print-base-manifest/v1"`，可与 `build.py sync-data` 同步或独立命令 `build.py sync-print-assets` 触发），**只记录元数据、SHA-256、飞书 `record_id` / `file_token` 与反查索引，不把任何 `.pdf`/`.ai`/`.png` 写入 Git**：
       - 每条 `asset_key` 索引：关联的 `web_replace_key`、`override_for`、`model_scope`、`region_scope`、`text_policy`、`pin_layout_json`（如存在）、**关联的 Web 图哈希集合 `known_web_sha256s`**（来自同 `asset_key` 下的 `web-composite`/`web-target`/`web-shared` 导出物及 `asset_registry.csv`）、以及 **已批可印刷无字出口列表 `print_exports`**（筛选 `artifact_kind=="print"`、`gate_status=="approved"`、`build_eligible==True`、`text_policy in {"textless","numeric-only","fixed-product-markings"}`，记录 `export_record_id`、`file_token`、`format`、`content_sha256`、`size_bytes`）；
  - **升级 `tools/idml/ir_asset_bridge.py`**（完整替代 Stage 1 临时 hook，~260 LOC）：
    1. 实现 **2.3 节确立的 4 级解析链**：`asset_key` → `web_replace_key + (model, region)` → Web 图 `content_sha256` 逆向查表 → 分级兜底或 fail-closed 报错；
    2. 缓存拉取：命中后检查 `.cache/idml_base_art/<sha256[:2]>/<sha256>.<ext>`，缺失或哈希不符时自动调用 `lark-cli base +record-download-attachment` 原子写临时文件再校验 `content_sha256`（若仅有 `04_资产源文件` 母版与 `data/asset_recipes/` 而缺导出行，支持本地现场调 `tools/asset_pipeline/extract.py` 生成临时矢量 `.pdf` 至 `.cache/` 并报警告提示美工入库）；
    3. 按 `format` 优先级选出矢量 `.pdf` → `.ai` → `.svg` → ≥300 DPI 无字 `.png`，向 `RenderContext.resolve_bundle_image()` 返回缓存绝对路径供 `build_delivery_package()` 统一封入 `Links/`。
  - **更新网页 IR 装配层（`tools/web/document_source.py`、`tools/component_specs/reference_figure.py`、`tools/manual_ir/{model,flow,validate}.py`）**：
    - 升级至 **`manual-ir/v2.1`**（向下 100% 兼容 `v2`，严守 `N4` 决意 **不改已封存 `330` 份历史包**）：允许流内 `image` 节点可选附加 `asset_key` 字段；在 `document_source.py` 执行 `apply_illustration_replacement()` / `_consume_covered_annotations()` 前，先将原图 `asset_key`/`web_replace_key`、多语种 `captions` 活词条及 `base_art_layout` 百分比坐标完整留存进 `ComponentSpec`（遵循 `N3` 决定，且 **绝不将无字印刷大文件写入 Git `manual_sources/`/`web/` 包**）。
- **验收**：运行 `sync_print_base_art.py` 产出纯文本 `data/print_base_manifest.json`（Git 增量零二进制）；运行 `build.py idml --from-ir` 自动拉取多维表矢量 `.pdf` 底图入本地缓存并封入 `Links/`；对缺无字底图的带字 Web PNG 精确输出《待上传无字底图清单（含 `asset_key` / `web_replace_key`）》。

#### PR 2.2：`feat(component_specs,idml): overlay editable localized callouts onto textless base art & wire all 19 HB-* specs`
- **目标**：实现核心的 **「多维表无字底图 + 网页文档活文字 → InDesign 可编辑引线叠放」**，同时扫平全库 `30.6%` (`3,767/12,301`) `projection-only` 组件与表格适配器断点。
- **新增/修改文件**：
  - `tools/idml/ir_callout_overlay.py`（~260 LOC）：实现通用坐标引擎，将 `HB-SPECIAL-REFERENCE-FIGURE` / `HB-SPECIAL-OPERATION` 在 `base_art_layout`（或来自多维表 `04_资产定义.pin_layout_json`）中的 `[x%, y%, w%, h%]` 与 `leader_pts` 百分比几何确定性换算为 IDML 置入底图框内的真实 `pt` 坐标，支持白底/浅灰矩形防撞遮罩（如有）与 `0.3pt` 矢量引线，再调用 `oppanel._editable_text_frame()` 把网页 IR 活文字发成独立顶层可编辑 `TextFrame`（解锁可微调）。
  - `tools/idml/ir_component_bridge.py` & `tools/idml/components/__init__.py`：
    - **`HB-SPECIAL-OVERVIEW`**：从网页 IR 抽取活 `callouts` 词条 + `overview_component_instances.json` `idml` 精确几何 + 多维表 `print/textless` 底图，直连 `tools/idml/page_overview.py` 渲染引擎；
    - **`HB-SPECIAL-OPERATION` & `HB-SPECIAL-REFERENCE-FIGURE`**：从网页 IR 抽取活 `steps`/`captions` + 多维表 `print/textless` 底图 + `ir_callout_overlay.py` 叠放可编辑引线；
    - 接线 `HB-TABLE-LCD-ICON`、`HB-TABLE-TROUBLESHOOTING`、`HB-TABLE-SYMBOL-SIGNAL`、`HB-TABLE-SYMBOL-ICON` 直连 `idml_manual_table_payload()` 与 `data_stories.py`（`add_lcd_story`/`add_trouble_story`/`add_symbols_story`）；
    - 按 `N4` 将 `HB-TABLE-SYMBOL-SIGNAL` 升级至 **`component-spec/v2`** 新增 `signal_key` 槽位（`tools/component_specs/manual_tables.py` + `manual_table_adapters.py`），根除按本地化文本猜图标的问题；
    - 升级 `tools/component_specs/spec_table.py`（新增 `idml_spec_table_payload()` 保留 `label_rowspan` 与 `references` 脚注）与 `tools/idml/spec_tables.py`（生成真实 IDML `RowSpan="{n}"` 与底部 `HB Spec Note`）；
    - 接齐 `HB-SPECIAL-APP`、`HB-TABLE-KEY-COMBINATIONS`、`HB-TABLE-AUTO-RESUME` 与 `HB-TABLE-REFERENCE`，同步刷新 `docs/renderers/contracts/component_registry.yaml` 的 `idml.capability` 为 `rendered`。
- **验收**：全 19 类 `HB-*` 组件在试点包内 100% 原生出稿；`HB-SPECIAL-OVERVIEW` / `OPERATION` / `REFERENCE-FIGURE` 在 K7 InDesign 打开后，**底图为只读链接矢量 `.pdf`，全部引线标签皆为独立可选中/修改的多语种活文字图层**；`HB-TABLE-SPEC` 还原真实跨行合并格与脚注。

#### PR 2.3：`feat(idml): flow multi-span tables, inline anchored images, and native vector glyph runs`
- **修改/新增文件**：
  - `tools/idml/ir_table_emitter.py`（~240 LOC）& `tools/idml/ir_flow_emitter.py`：完整实现 `manual-flow/v2` 的 `table_head`（`HeaderRowCount`）、`column_group`/`column.span`（精确按比例算列宽 `pt`）、`table_cell.row_span`（`RowSpan="{n}"`）、`table_cell.column_span`（`ColumnSpan="{n}"`）与矩阵占用跳格，消除全库 `133` 处跨行与 `119` 处跨列表格截断；
  - `tools/idml/ir_flow_emitter.py`：支持段落/列表/表格单元格内的 **行内嵌入 `image` 节点**（覆盖全库 `2,820` 处内联图标），同样经 `ir_asset_bridge.py` 优先拉矢量图标并生成 `AnchoredObjectSetting AnchoredPosition="InlinePosition"` 内联矩形框；
  - `tools/idml/components/native_marker.py` & `tools/idml/inline_text.py`：对纯文本流内的 **`⎓`（`4,767` 次，按 `STYLE_DEFINITION.md` L102–106）、`※`（`689` 次原生矢量）、`①`–`⑲`（`638+` 次）、`⚠`（`210` 次）、`●`（`145` 次）** 统一启用共享原生矢量框 + 受控字体切分，与旧 `v1` 产线保持一致。
- **验收**：对含跨格表格、行内图、特殊符号的样张跑 K7 `indesign_finalize.py`，`missing_glyphs`（`.notdef` / `U+FFFD`）严格为 **`0`**。

#### PR 2.4：`feat(idml,ir): print PagePlan, editable cover/back-cover, dynamic TOC, and 4N signature padding`
- **目标**：补全 `STYLE_DEFINITION.md` L149 指出的 Web IR 省略页面语义（封面、封底、目录、页眉页脚/页码起始规则、4N 骑马钉折手），而不破坏网页构建轻量化。
- **修改/新增文件**：
  - `tools/manual_ir/model.py` & `tools/web/document_source.py`：在 `ManualIR v2.1` `metadata["print_contract"]`（可选字段）及 target YAML 配置中接入：真实 `layout_params_sha256` 校验开关、封面/封底语义槽位与多维表 `asset_key`（如 `page/<model>_<region>/cover`）、目录页开启开关与 `front_matter_roles`（跳过封面/前言，正文第 1 页起编页码 `01`）、章节强制分页面 `DEDICATED_SECTION_ROLES`、装订折手模数 `signature_multiple: 4`；
  - `tools/idml/ir_print_front_back.py`（~280 LOC）& `tools/idml/from_manual_ir.py`：
    - 复用 `page_placed.py`、`page_toc.py`、`page_folio.py`：从多维表缓存置入矢量封面 PDF、合成可编辑封底（地址/官网/QR 矢量链接来自多维表 `asset_key`）、前置动态 TOC 并绑定实际 Spread 页码；
    - 实现 **`pad_to_4n_signature()`**：若启用 `signature_multiple == 4`，自动在封底之前插补标准无页脚空白页（`PageTemplateRole.NO_FOOTER`），确保物理总页数严格 `N % 4 == 0` 且封底恒为末页（`4k`）。
- **验收**：生成全套封面+目录+正文+空白补白页+封底的 `.idml`，总页数为 4 的倍数，目录页码与物理 Spread 精确对应，封面/封底无页脚。

#### PR 2.5：`feat(idml): K7 overset-feedback loop & REV-40 JBP-2000B/JP trial delivery`
- **目标**：打通页面高度精算与 K7 溢出自动回调，完成 `REV-40` 试产闭环。
- **修改/新增文件**：
  - `tools/idml/ir_pagination.py`（~220 LOC）：联合 `character_metrics.py`、`line_metrics.py`、`spec_tables.measured_spec_table_height()` 预估章节 Spread 需求；支持读取 K7 吐出的 `finalize_report.json` 中 `overset_stories` 明细，按章节扩展链接 `TextFrame` 页数并二次出包；
  - 落实 `REV-40` 试点（`manual_sources/JBP-2000B/JP/ja/<version>` 按 `manual_ir_p1_decisions_2026-11.md` A1/A9 建包，其无字底图经 `04_资产导出物` 入库），完成纯 `manual.ir.json (v2.1) + 飞书多维表底图 → .idml → .indd → PDF/X-4` 试产交付。
- **验收**：`JBP-2000B/JP` 与 `JE-3000C/KR` 均脱离旧 RST/CSV 独立产出送印包，K7 预检零断链、零缺字、零未处理溢出。

### 5.2 Stage 2 退出门槛（Exit Gate）
1. 试产机种（`JBP-2000B/JP` `REV-40` 试点 + `JE-3000C/KR`）完全断开 `docs/templates/` RST 与 `data/phase2/*.csv` 直接解析，仅依赖 **网页 `manual.ir.json (v2.1)` + 飞书 `04_资产*` 多维表同步缓存** 一键产生成套 `*_handoff.zip`；
2. Git 仓库内**零新增大体积 `.ai` / 无字印刷 `.pdf`**，`data/print_base_manifest.json` 仅为轻量索引，`.cache/idml_base_art/` 按 SHA-256 严格校验下载命中；
3. K7 `tools/indesign_finalize.py` 汇报 **全绿灯**：`missing_fonts == []`、`bad_links == []`、`missing_glyphs == []`、`overset_stories == []`、`pdf_export_validation.pass == True`（`PDF/X-4` + `Japan Color 2001 Coated`）；
4. 全部需翻译的插图在 K7 打开 `.indd` 后均呈现为「**底层不可编辑矢量无字底图 + 顶层可自由修改移动的多语种引线文本框**」，物理页数满足 `4N` 折手规则，获设计师签审放行。

---

## 6. Stage 3（累计第 6–10 周）：多语种规模化投产、历史包媒体瘦身与旧栈退场

### 6.1 Slice-by-Slice PR 计划（Stage 3：4 个 PR）

#### PR 3.1：`feat(idml): EU 9-language & CJK overflow tuning + batch finalize/parity harness`
- **工作内容**：
  - 将 Stage 2 能力推广至 EU 9 语合订本/单语本（EN/FR/ES/DE/IT/NL/PL/PT/UK，吸收 1.3×–1.5× 拉丁字符膨胀）与 JP/KR/ZH-TW；
  - 依据 `data/layout_params.csv` 的 `332` 个 `lang_*` token 架构，补充 `nl`/`pl`/`pt`/`uk`/`ko` 专属字号、行距、表格边距覆写（禁止任何语言硬编码分支）；
  - 接入 `tools/indesign_finalize_jobs.py` + `tools/idml/indesign_finalize_batch.jsx`（单次唤醒 InDesign 批跑全语种目录）与 `tools/idml/pdf_parity_visual.py`（300 DPI RGB MAD ≤ 0.008 / 像素差异率 ≤ 0.040 自动化视觉回归）。

#### PR 3.2：`refactor(web,assets): converge 171 custom-script frozen packages & migrate 2.41 GiB Git static media to Bitable`
- **工作内容**：
  - 根据 `build.py web-package --package-command inventory` 实测，分批把 **`171` 个依赖自定义脚本（`rebuild.py`/`render.py`）的冻结包**迁移至声明式 `ManualIR v2.1` 组装（当前仅 `16 / 267` 为 `declarative_ready`），并清理 **`5` 组双根碰撞**（`JE-2000F/JP`、`JHP-3000D/US`、`JHP-3600A/US`、`JHP-3600C/US`、`JHP-5000C/US`）；
  - **彻底落实「多维表唯一存底图」的仓内瘦身策略**：把所有现存无字底图及高频复用大图统一登记进 `04_资产定义` + `04_资产导出物` 并在 `manual.ir.json` 中切换为语义 `asset_key` / `web_replace_key` 引用，分批解耦清洗 `manual_sources/` 与 `data/manual_sources/` 下的 `26,441` 个 / `2.41 GiB` 冗余静态媒体文件。

#### PR 3.3：`fix(ir-qc): burn down 389 untranslated_english_residue & 33 callout warnings`
- **工作内容**：
  - 基于 `build.py ir-qc --ir-command audit --all-ir` 清单，联动 TM-B 与人工核校清零 **`68` 个带告警 IR 包中的 `389` 条英文残留**与 **`24` 条 `callout_severity_mismatch` + `9` 条 `unknown_callout_severity`**；
  - 将 CI `--max-warnings 422` 棘轮逐批压降直至 `--strict`（`0` errors, `0` warnings），杜绝英文未译文本流入高昂的印刷排版与打样环节。

#### PR 3.4：`chore(idml): deprecate & retire legacy prepared_rst -> manual-ir/v1 IDML stack`
- **前置条件**：全部在役型号完成共享 IR (`v2.1`) + 多维表底图 → IDML 生产闭环验证，并获操作者签字批准退役。
- **工作内容**：
  - 将 `build.py idml` 默认后端切换为共享 IR 编译器（保留 `--legacy-rst` 临时退路一个发布窗口后再移除）；
  - 归档并清理旧 `v1` 打印紧耦合代码（Cat C `17` 文件 / `6,560` LOC + Cat B 废弃编排器 ~`6,300` LOC：如 `prepared_rst.py`、`idml_rst_extract*.py`、`ir_projection.py`、`ir_sidecar.py`、`latex_page_plan.py` 等），净减 **`13,000+` LOC** 历史债务；
  - 日落 `.github/workflows/` / `.gitlab-ci.yml` 下挂载于 `LEGACY_TEMPLATE_QUEUE_ENABLED` 的 8 条旧模板队列 workflow，解除 `data/frozen_package_registry.json` 的旧版冻结限制，并同步更新 `AGENTS.md`、`code-as-doc/` 与 `user-guide/two_plane_map.md`。

### 6.2 Stage 3 退出门槛（Exit Gate）
1. 主力 EU / US / JP / KR 多语产品线全部由 **「一份 `manual.ir.json (v2.1)` 网页活文字文档 + 飞书 `04_资产*` 无字底图库」** 单源驱动网页发布与印刷 `.idml`/`.indd` 导出；
2. `build.py ir-qc --all-ir --strict` 零错误零警告通过；`web-package inventory` 自定义脚本清零（归档历史冷库除外）；
3. K7 批处理线（`indesign_finalize_batch.jsx`）可无人值守批量产齐多语 `.indd` + `PDF/X-4` 并通过视觉及印刷预检门禁；旧 RST→IDML 管线正式退场。

---

## 7. 风险矩阵与回滚预案

| 风险编号 | 风险描述与触发条件 | 影响面 | 工程缓解措施（Mitigation） | 立即回滚预案（Rollback） |
|---|---|---|---|---|
| **R1 多维表底图缺失或与网页 `sha256` 失配（历史包命中率仅 `6.12%`）** | 老机种在 `04_资产导出物` 尚无 `artifact_kind="print"` + `text_policy="textless"` 记录，或历史 `330` 份 IR 中的 PNG 经过重压缩导致哈希对不上。 | Stage 2 试产缺少无字矢量底图，或停留在带字 Web 栅格图。 | ① 4 级解析链优先用 `asset_key` / `web_replace_key` 绕开文件哈希脆性，实在无 key 再用 `sha256`；② Fail-Closed 主动吐出《待补录底图清单（带原网页预览链接与 `web_replace_key`）》，设计师直接在飞书 `04_资产导出物` 上传附件即可修复，无需开发者改代码、无需提交 Git；③ 整本母版在 `04_资产源文件` 时支持靠 `data/asset_recipes/` 自动切图入缓存。 | 未补齐多维表无字底图的老机种暂时继续使用旧 `build.py idml`（不传 `--from-ir`），原有发版路径零阻断。 |
| **R2 引线标注坐标与无字底图产生偏移** | 网页采用 `base_art_layout` 百分比或 `04_资产定义.pin_layout_json` 时，若设计师重导无字底图改了裁剪边距（crop box），原坐标会偏移。 | InDesign 打开后文字框与底层图形对齐错位。 | ① 严格沿用 `tools/web/figure_coverage.py` 与 `base_art_reference.py` 的强绑定契约：坐标结构必须带 `art_sha256` 与实际拉取的底图哈希校对一致，哈希变更未重标坐标立即 fail-closed 报错；② 印刷合成的每一个标注都是 **独立解锁的顶层 `TextFrame` + 独立矢量 `GraphicLine`**，即便临时微偏，设计师在 K7/本地 InDesign 中也可直接拖动微调。 | 紧急单图可暂时在 `*_handoff.zip` 内由设计师按 `designer_checklist.md` 微调 `.indd` 文本框位置交付，不影响上游正文。 |
| **R3 内网离线 / 飞书 API 限流或权限中断** | 内网 GitLab Runner 频繁并发下载多个大尺寸 `.ai`/`.pdf` 底图导致构建变慢或受 Feishu 速率限制。 | CI 构建耗时增加或偶发下载失败。 | ① `.cache/idml_base_art/<sha256[:2]>/<sha256>.<ext>` 按内容哈希永久内容寻址，同一版本底图全机终身只下一次；② 构建前支持 `--offline-cache-only` 模式，在已有完整缓存的 Runner 上 100% 离线出 `.idml`。 | 切换到已预热完整缓存的本地工作站跑 `build.py idml --from-ir` 生成 `*_handoff.zip` 后手工投递 K7。 |
| **R4 多语种文本膨胀导致 `overset` 与版本漂移** | 欧规法/德/西/波兰语较英文长 30%–50%，静态估算与 K7 真实排字仍有偏差；或 K7 擅自升级 InDesign 导致脚本异常。 | `.indd` 出现文字溢出红框或字体替换。 | ① PR 2.5 引入 K7 `finalize_report.json` → `ir_pagination.py` 自动增页反馈环，优先在 `data/layout_params.csv` 的 `lang_*` token 微调行距字号；② 按 [`indesign_second_host_runbook.md`](indesign_second_host_runbook.md) 双机同锁 `Adobe InDesign 2026 21.0.1.6` 且运行前强制 `--check-host`。 | 通过 K7 手工在 `.indd` 拉开链接帧并保存（或对特定页面配置显式分页覆盖），`--legacy-rst` 旧路径可随时接管保底交付。 |
| **R5 护栏文件超限与历史 `330` 份 IR 哈希破坏** | 直接修改热文件（`build.py`/`export_idml.py`/`primitives.py`）超限，或篡改 `v2` 字段定义破坏 `330` 份冻结 `content_sha256`。 | 静态门禁卡死 PR 或 Read the Docs 线上全部校验报红。 | ① 所有新编译、同步与叠加代码均落于独立新模块（`< 400` LOC），每次提交前必跑 `check_maintainability_guardrails` 与 `check_mypy_ratchet`；② 遵循 `N4` 原则，所有新增字段走 **`manual-ir/v2.1`** / **`component-spec/v2`** 向下兼容版本，绝不改写已封存的 `330` 份 JSON。 | `git revert` 独立切片 PR 即可干净移除，主线 `web-package` 与旧 `idml` 产线全程零侵入。 |
