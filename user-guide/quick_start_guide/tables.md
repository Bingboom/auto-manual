# 快速开始：三张表各自负责什么（§1）

属于[快速开始指南](../quick_start_guide.md)，其索引列出全部分页。章节编号与原文一致。
示例或流程变化时更新本页，不要把新内容追加到总文件。

## 1. 先分清三张表各自负责什么

### 1.1 phase2 源表

这些表是结构化数据真源：

- `规格参数明细`: 只维护 `Page=specifications` 的规格行
- `页面占位参数`: 维护 `Product overview / operation_guide / storage / ups_mode` 的页面占位行
- `Spec_Master`: 本地构建读取用 read model，由 `sync-data --table spec_master` 或 `spec-master-rebuild` 从上面两张源表生成，不作为人工维护的第三张源表
- `Spec_Footnotes`
- `Spec_Notes`
- `Manual_Copy_Source`: reusable short copy and spec titles; `spec_titles.csv` is generated from it plus tagged Translation Memory
- `symbols_blocks`
- `TROUBLESHOOTING` / `troubleshooting_blocks`

你要改参数、规格、页面占位值、注脚、标题顺序、symbols，就改对应源表。
改完两张 spec 源表后，常规刷新运行：

```bash
python3 build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --table spec_master
```

只想重建 `Spec_Master.csv` 时，运行：

```bash
python3 build.py spec-master-rebuild --config configs/config.ja.yaml --expect-spec-rows 157 --expect-placeholder-rows 222
```

需要把源表合并结果写回旧 Feishu 总表时，才加 `--write-back`。
两张源表里的 `source_row_key` 是公式主键列，维护行内容和顺序字段即可，不要手填 key。
`Row_key` 也是 lookup 列，来自 `参数名.Row_key`；新增或更换参数概念时，先维护/选择 `Row_key_link`。
两张源表不再维护 `Model` / `Region`；rebuild 会从 `document_key` 自动生成给本地 read model 使用。

如果原始输入是一份规格书、Word 说明书转出的结构化 Markdown，或飞书云文档里的规格/文案表，先用 source intake 做候选沉淀：

```bash
python3 -m tools.data.source_intake run --input <spec.md-or-doc-url> --document-key <MODEL_REGION> --source-lang en --data-root data/phase2 --out reports/source_intake/<run-id>
python3 -m tools.data.source_intake approve --report reports/source_intake/<run-id>/source_intake_source_table_change_request.json --approve <delta_hash> --out reports/source_intake/<run-id>
python3 -m tools.data.source_intake apply --report reports/source_intake/<run-id>/source_intake_source_table_change_request.json --approval reports/source_intake/<run-id>/source_intake_approval.json --out reports/source_intake/<run-id>
python3 -m tools.data.source_intake verify --candidates reports/source_intake/<run-id>/source_intake_candidates.json --change-request reports/source_intake/<run-id>/source_intake_source_table_change_request.json --approval reports/source_intake/<run-id>/source_intake_approval.json --apply-report reports/source_intake/<run-id>/source_intake_apply.json --check-command "sync-data=python3 build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --table spec_master" --check-command "build=python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US" --out reports/source_intake/<run-id>
```

`apply` 默认只做 dry-run 计划；只有人工确认后显式加 `--write --table-binding TABLE=BASE:TABLE_ID`，才会写线上 Feishu 源表。新增行仍先停在候选/人审层，不自动创建线上记录。

如果输入是产品规格书，而且已经有同产品或同区域 sibling，默认走重复入库快速通道，不再手工组装几十行：

```bash
python3 -m tools.data.source_intake spec-extract --input <spec.pdf> --rules <rules.json> --document-key <MODEL_REGION> --region <REGION> --reference <sibling-spec.json> --out reports/source_intake/<run-id>
python3 -m tools.data.source_intake stage-plan --spec-candidates reports/source_intake/<run-id>/spec_intake_candidates.json --spec-sibling <sibling-spec.json> --placeholder-sibling <sibling-placeholders.json> --overrides <target-differences.json> --document-key <MODEL_REGION> --localized-lang <lang> --out reports/source_intake/<run-id>
```

`stage-plan` 只克隆 sibling 结构并应用目标差异，输出评审文件和一个 `create_records` 批量 payload，不写飞书。它会拒绝模糊规则匹配、sibling 结构缺行以及未配对的本地化值。输入就绪后，机械步骤目标是 3–5 分钟；后续暂存表回读、人工确认和正式源表写入仍是硬门禁。

JE-2000E 韩规目标复用共享 KR/ko 家族配置；源表确认入库并同步后，用下面的目标命令验收：

```bash
python3 build.py check --config configs/config.kr.yaml --model JE-2000E --region KR
```

不要把 [`data/phase2/`](../../data/phase2) 当成主编辑面；它是 gitignored 本地 snapshot，每个镜像仓应从自己的 Feishu Base 生成。唯一入库的例外是 [`page_registry.csv`](../../data/phase2/page_registry.csv)（仓库维护的页面结构输入，`sync-data` 每次运行都要读取）。
只有当 `Document_link.是否强制刷新数据 = 勾选` 时，队列才会在这次构建前执行 `sync-data`；不勾时会直接复用当前本地 snapshot。

### 1.2 Review Init 表

这张表只做 Start Review 动作：把文档拉进 review，或者强制重开并按最新模板重新 seed。

建议字段：

- `Document_Key`（必填，例如 `JE-1000F_EU`）
- `Document_ID`（可选；Start Review 不需要版本号）
- `Build_family`（语言范围，例如 `us-merged`；不填写产品或骨架类型）
- `Lang`（可选）
- 语言显示标签和 `queue-query` 的语言别名统一从 `tools/lang_registry.py` 读取；新增语言时只维护注册表及其 aliases，查询仍兼容既有中英文别名。
- `Version`（可选）
- `Review_status`
- `是否进入Review`
- `Git_ref`
- `PR_url`
- `Initial_result`
- `Remarks`

这张表触发后，系统会按 `Document_Key` 对应的 `Model + Region` 启动 review。`Start Review` 的语义现在是“强制重开并按最新模板重新 seed”：

真正会启动 review 的行必须同时满足：`Document_Key` 非空、`是否进入Review` 已勾选、`Workflow_action = Start Review`。
如果 `Document_Key` 是多维表关联字段，OpenClaw 会用 `Task_id` 稳定定位这行，再检查勾选和 `Workflow_action`。

1. 同步最新 phase2 snapshot
2. 从最新 `main` 起 review worktree
3. 不管旧 review 分支是否存在，都按最新模板/数据重新 seed `docs/_review`
4. 如果 review 分支已存在，就强制更新那条分支到这次最新 seed
5. 创建或复用 PR
6. 回写 `Git_ref`
7. 回写 `PR_url`
8. 把 `Review_status` 改成 `InReview`
9. 清掉 `是否进入Review`

额外规则：

- `Review_status` 不再是 Start Review 的门槛；只要再次勾选 `是否进入Review` 且 `Workflow_action = Start Review`，系统就会重开
- `main` 上已经存在旧的 `docs/_review/<model>/<region>/` 内容，也不会再阻止 Start Review

`Review Init` 这条链默认直接复用 `Document_link` 的表 / 视图绑定，所以 GitHub 侧继续用 `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` 和 `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID` 即可，不需要单独再配一组 `REVIEW_INIT_*` secrets。

### 1.3 Document_link 表

这张表只做“反复构建文档”。

关键字段：

- `Document_Key`
- `Build_family`
- `Lang`
- `Version`
- `Git_ref`
- `Workflow_action（必填；Start Review / Build Draft Package / Publish 三选一）`
- `Doc_phase（留空；队列只认 Workflow_action）`
- `是否触发文档构建`
- `是否立即构建`
- `是否强制刷新数据`
- `是否上传钉钉`
- `DingTalk_target_node_url`
- `operator_union_id`
- `Document directory`
- `飞书云文档`
- `基线文档`
- `idml_file`
- `HTML_link`
- `Document link_dd`
- `data_sync`
- `构建结果`

它负责：

- `Workflow_action` 是唯一队列语义字段；强制重开 review / 重新 seed 填 `Start Review`，Review 阶段反复构建填 `Build Draft Package`，Publish 阶段填 `Publish`
- `Doc_phase` 不再参与队列路由，保持留空即可
- 按阶段回写结果链接：Draft=`飞书云文档`，Publish=`idml_file`，Web Publish=`HTML_link`
- `Build Draft Package` 通过 `lark-cli drive +import --type docx` 导入可编辑飞书云文档并写回 `飞书云文档`；同时把第二份冻结导入写入 `基线文档`，供 backport 对比
- `Publish` 把设计交付 ZIP 的知识库链接写入 `idml_file`，并把 release 留档 DOCX 路径写回 `Document directory`
- 如果当前启用了 DingTalk mirror，且表里存在 `Document link_dd`，队列会把镜像 DingTalk 节点链接写到这个字段；它不是主交付判据
- 如果当前启用了 DingTalk mirror，且表里存在 `是否上传钉钉`，这列就是行级开关：勾选才同步 DingTalk，不勾就只走 Feishu/wiki
- 如果表里没有 `是否上传钉钉`，worker 就按当前全局模式处理整行：开启 mirror 的 worker 会同步 DingTalk，Feishu-only worker 不会同步
- 如果当前启用了 DingTalk mirror，且该行还填了 `DingTalk_target_node_url`，worker 会优先同步到这个行级节点；只有该字段为空时，才回退到全局 `DINGTALK_DOCS_TARGET_NODE_URL`
- 如果该行还填了 `operator_union_id`，worker 会优先从 `AUTO_MANUAL_DINGTALK_SESSION_ROOT/<operator_union_id>.json` 读取该操作员的钉钉会话；找不到时才回退到全局 `DINGTALK_DOCS_*`
- `DingTalk_session_key` 和 `钉钉会话键` 也可以作为 `operator_union_id` 的别名；三者都会映射到同一个 session 文件名
- 如果你在表里填的是 `alice`，那就要在本机或 worker 的 session 目录里准备 `alice.json`；如果缺这个文件且也没有全局 `DINGTALK_DOCS_*`，队列会在 build 前直接失败并把原因写回 `构建结果`
- 只有当 `是否强制刷新数据 = 勾选` 时，队列才会在这次构建前刷新一次 phase2；否则直接复用当前本地 snapshot
- `data_sync` 会回写 `refreshed / skipped / failed`

### 1.4 图片资产三张新表与构建引用

图片资产不写进 phase2 内容表。业务 Base
`LD3lb4G1ua4GOVs1vxAc9W2enje` 的唯一允许合同是另建三张独立新表：
`04_资产源文件`、`04_资产定义`、`04_资产导出物`。旧插图表只保留历史，
新链路不读取、不写入，也不在权限失败时回退过去。三张表的真实 table/view/field
绑定见 [`data/asset_base_bindings.json`](../../data/asset_base_bindings.json)；若这些新表
无权限，归档步骤停止，`source_pointer` 保持为空，也不改走入库 staging 表。

RST 中获批资产可按稳定身份引用：

```rst
.. image:: asset:operation/ac_output
```

构建会在 review 覆盖完成后按当前 model/region/language 解析注册表，只接受
PNG/JPG/JPEG/SVG/PDF 成品；`.ai`、临时、缺失和隔离资产都不会通过 `asset:`
进入 bundle。
App/QR 等敏感候选即使已拆图也继续保持隔离。只有 `data/asset_promotions/`
中的受审契约完整绑定审核人、时间、目标 scope、AI/PDF/recipe/evidence、输入输出
完整 SHA 和确定性组合规则时，注册表才接受
`source=reviewed-promotion:<promotion_id>`。目标或任一字节漂移都会硬失败，且不会
回退到同名共享旧图。
最终 bundle 写出 `asset_usage_manifest.json`、`asset_registry_snapshot.csv` 和带
`bundle_sha256` 的 `bundle_manifest.json`。现有旧路径图片仍可构建，但只记为
`legacy-path`；这表示已记账，不表示已受注册表门控。共享模板已经批量迁移到
`asset:`。产品/区域专用导出物使用独立 key，并在注册表以
`override_for=<共享 key>` 声明窄范围覆盖；不要缩窄或替换共享行。

网页版整块图文插入是同三张表上的最后一层，不替换普通 `asset:` 图片链：

1. `04_资产定义` 填稳定 `web_replace_key`，并完成 scope 与审核。
2. `04_资产导出物` 每个物理文件一行：`artifact_kind=web-composite`，在
   `export_file` 上传一张图片，选择 `web_locale`，填写 `content_sha256` 和
   `source_fragment_sha256`，审核通过后勾选 `build_eligible`。
3. 在获批的 `Document_link` 行选择 `Workflow_action=Web Publish`，保留已审核的 `Git_ref`。独立语言页使用匹配的单语 `Build_family` 和显式 `Lang`（如 `eu-en/en`），每语单独一行；不要使用 merged family 携带 Lang。版本及队列操作确认后才触发独立 Web worker；[队列契约](../../code-as-doc/dev/web_publish_locale_queue.md)列出了尚未释放的上线门禁。
4. Web worker 使用 HT-Docs bot 强制执行 `sync-data`，再按
   `web_replace_key + model + region + locale` 自动替换整块 figure 与关联文字；章节
   标题不进入图片。没有合格导出时保留可编辑 HTML，重复匹配或哈希漂移直接失败。

Read the Docs 不在线读取飞书。Web Publish 先把线上审核后的 manifest、附件与 MyST
冻结到 `Hello-Docs/publish:docs/publish/` 候选目录，自动创建或更新只包含
`docs/publish/**` 的 `publish -> main` PR；人工审核合入后，RTD 只消费 `main` 快照。
`review/*` 只提供构建内容，不能整分支合入 `main`。
