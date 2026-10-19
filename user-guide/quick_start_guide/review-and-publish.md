# 快速开始：Review、出包与 Publish（§2–§5、§7）

属于[快速开始指南](../quick_start_guide.md)，其索引列出全部分页。章节编号与原文一致。
示例或流程变化时更新本页，不要把新内容追加到总文件。

## 2. Build Draft Package 和 Publish 的原料分别是什么

### Build Draft Package

Build Draft Package 的原料是：

- 当前 phase2 snapshot；如果这条记录勾了 `是否强制刷新数据`，队列会先把它刷新成 Feishu 最新数据
- PR 分支代码
- PR 分支里的 [`docs/_review/`](../../docs/_review)

这表示：

- 结构化数据改动看 Feishu
- 评审文稿改动看 PR 分支里的 `_review`

`data/phase2/*.csv` 默认不进 PR；即使本地 snapshot 有变化，Build Draft Package 也不会把它当最终真源。
只有当这条记录勾了 `是否强制刷新数据`，队列才会先自动 `sync-data`，把这份目录刷新成 Feishu 当前快照。
如果这条记录没有勾这个开关，队列会直接复用当前本地 snapshot。
如果这条记录已经由 `Review Init` 回写过 `Git_ref`，后续 Build Draft Package / Publish 都应继续沿用这条分支，不要手动清空。

### Publish

Publish 的原料是：
- 当前 phase2 snapshot；如果这条记录勾了 `是否强制刷新数据`，队列会先把它刷新成 Feishu 最新数据
- `Document_link.Git_ref` 指向分支上的代码
- 该分支里的 review 内容

正式 Publish 仍然会基于这条 review / PR 分支重新构建，不复用旧的 Draft DOCX；构建完成后会上传 Publish PDF，并把 DOCX 只留在 release 目录归档。

如果 `Git_ref` 为空，才会退回当前 queue worker 所在分支；远端 worker 通常是 `main`。

## 3. 场景一：第一次把文档拉进 Review

这是一次性动作。做完后，这份文档才算正式进入 review 阶段。

### 你在表里怎么填

在 `Review Init` 表新增一行，至少填：

- `Document_ID`
- `Document_Key`
- `Build_family`
- `Lang`
- `Version`
- `Review_status = NotStarted`
- `是否进入Review = 勾选`

如果是已经在 review 里的目标，要强制按最新模板重开，也可以直接在原行再次勾选 `是否进入Review`；`Review_status` 保持 `InReview` 也会重跑。

### 系统会做什么

触发 review-init workflow：

- [`.github/workflows/feishu-start-review.yml`](../../.github/workflows/feishu-start-review.yml)

它会：

1. 同步最新 phase2 快照
2. 从最新 `main` 起 review worktree
3. 按最新模板和最新 snapshot 重新生成这个目标的 [`docs/_review/...`](../../docs/_review)
4. 如果 review 分支已存在，就强制更新到这次最新 seed；如果不存在，就新建
5. push 分支
6. 创建或复用 PR
7. 回写：
   - `Git_ref`
   - `PR_url`
   - `Review_status = InReview`
   - 清掉 `是否进入Review`

### 这一步完成后你应该看到什么

- 多维表里出现 `Git_ref`
- 多维表里出现 `PR_url`
- 仓库里已经有 PR
- 对应分支里已经有 review 内容
- 如果这次是重开 review，原来的 review 分支也会被更新成这次最新 seed

如果这一步没做，后面的 Build Draft Package 只是“构建一条记录”，不算完整的 review 流程。

## 4. 场景二：Review 过程中反复出 Build Draft Package

这是反复动作。进入 review 后，可以一直这样用。

### 你在表里怎么填

在 `Document_link` 表对应那一行填：

- `Document_Key`
- `Build_family`
- `Lang`
- `Version`
- `Workflow_action = Build Draft Package`
- `是否触发文档构建 = Y`
- `是否立即构建 = 勾选`
- `是否强制刷新数据 = 需要最新 phase2 时才勾`
- `是否上传钉钉 = 只有这次确实要传 DingTalk 时才勾`
- `DingTalk_target_node_url = 这次要上传到钉钉时可选填；填了就覆盖全局默认节点`
- `operator_union_id = 这次要按操作员切换钉钉会话时可选填；填了就优先读取该操作员的 session 文件`

### 系统会做什么

触发 Build Draft Package workflow：

- [`.github/workflows/feishu-draft-build-queue.yml`](../../.github/workflows/feishu-draft-build-queue.yml)

它会：

1. workflow 由默认分支承载
2. 执行 `process-build-queue --workflow-action build-draft-package`
3. 只有当 `是否强制刷新数据 = 勾选` 时，队列才先执行一次 `sync-data`
4. 再按 `Document_link.Git_ref` fetch 对应的 review / PR 分支到临时 worktree
5. 然后基于那条分支里的 `_review` 构建 Build Draft Package Word 和 Markdown
6. 如果当前启用了 DingTalk mirror 且 `是否上传钉钉 = 勾选`，就同步 DingTalk；如果同时填了 `DingTalk_target_node_url`，优先同步到该行节点；否则退回全局默认 DingTalk 节点；未勾选则只保留 Feishu/wiki 上传；如果表里没有 `是否上传钉钉`，则按当前 worker 的全局模式决定是否同步
7. 回写：
   - `开始构建时间`
   - `构建结果`
   - `data_sync`
   - `Document directory`
   - `飞书云文档`
   - `基线文档`
   - `Document link_dd（仅启用 DingTalk mirror 且字段存在时）`

### Build Draft Package 最容易配错的地方

1. `Git_ref` 必须指向当前 review / PR 分支，不能留空
2. GitHub dispatch 的 `ref` 应该是 `main`，不是 PR 分支
3. `queue_record_id` 必须是真实 record id，不能写成字符串 `<record_id>`
4. `是否触发文档构建` 必须是 `Y`
5. 只有 `是否立即构建` 勾选但没有 `Y`，不会构建

## 5. 场景三：Review 完成，进入 Publish

这是正式发布动作。

### 你在表里怎么填

在 `Document_link` 表对应那一行填：

- `Workflow_action = Publish`
- `是否触发文档构建 = Y`
- `是否立即构建 = 勾选`
- `是否强制刷新数据 = 需要最新 phase2 时才勾`
- `是否上传钉钉 = 只有这次确实要传 DingTalk 时才勾`
- `DingTalk_target_node_url = 这次要上传到钉钉时可选填；填了就覆盖全局默认节点`
- `operator_union_id = 这次要按操作员切换钉钉会话时可选填；填了就优先读取该操作员的 session 文件`

### 系统会做什么

触发 Publish workflow：

- [`.github/workflows/feishu-build-queue.yml`](../../.github/workflows/feishu-build-queue.yml)

它会：

1. workflow 可以由默认分支承载
2. 执行 `process-build-queue --workflow-action publish`
3. 只有当 `是否强制刷新数据 = 勾选` 时，队列才先执行一次 `sync-data`
4. 如果 `Document_link.Git_ref` 有值，队列会先 fetch 这条分支，并在临时 worktree 中按这条分支执行 `build.py publish`（内部会跑 `check -> diff-report -> word -> pdf -> md -> release-manifest`）
5. 如果当前启用了 DingTalk mirror 且 `是否上传钉钉 = 勾选`，就同步 DingTalk；如果同时填了 `DingTalk_target_node_url`，优先同步到该行节点；否则退回全局默认 DingTalk 节点；未勾选则只保留 Feishu/wiki 上传；如果表里没有 `是否上传钉钉`，则按当前 worker 的全局模式决定是否同步
6. 回写：
   - `开始构建时间`
   - `构建结果`
   - `data_sync`
   - `Document directory（release 留档 DOCX 路径）`
   - `idml_file（设计交付 ZIP 的知识库链接）`
   - `Document link_dd（仅启用 DingTalk mirror 且字段存在时；镜像同一份设计交付 ZIP）`

印刷 Publish 不再构建或部署网页。网页使用独立的
[`feishu-web-publish-queue.yml`](../../.github/workflows/feishu-web-publish-queue.yml)：

1. 在同一条 `Document_link` 记录选择 `Workflow_action = Web Publish`，保留已审核的 `Git_ref`，并把构建触发改回 `Y`
2. 在 `04_资产导出物` 确认所需 `export_file` 已选择语言、hash 正确且审核通过
3. Web worker 强制拉取最新 phase2 和图文资产，按 web profile 执行 `check -> md -> html`
4. workflow 把冻结 MyST 增量提交到 `Hello-Docs/publish:docs/publish/` 候选目录，范围门禁确认没有其它路径后自动创建或更新 `publish -> main` PR
5. 审核并合入这个仅含 `docs/publish/**` 的 PR；不要合入 `review/*` 分支。`main` 的 push 才触发 Read the Docs 构建
6. PR 合入后，[`web-publish-receipt.yml`](../../.github/workflows/web-publish-receipt.yml) 等待并核验 RTD 部署（冻结源指纹 + 逐字节 + 项目 slug），核验通过才把嵌套 canonical 页面（例如 `https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/JE-1000F/US/en/md/manual_je1000f_us.html`）幂等写回 `HTML_link`（写后同记录回读）；根级短地址（例如 `/manual_je1000f_us.html`）仍由发布源自动生成并转向 canonical 页面，留作印刷/QR 入口层，不需要为每个型号手工创建 RTD Redirect。成功验收还要确认 `main` 的 manifest、RTD 构建 commit、`Web Publish Receipt` run 绿和 `HTML_link` 线上页面；登记失败重跑该 workflow，不要重发整本

### 远端 GitHub worker 想支持 DingTalk 还要配什么

- GitHub Secrets 至少要有：
  - `DINGTALK_DOCS_A_TOKEN`
  - `DINGTALK_DOCS_XSRF_TOKEN`
  - `DINGTALK_DOCS_COOKIE`
- 还要显式加一个 GitHub Actions repository variable：
  - `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER = dingtalk_alidocs_session`
- `DINGTALK_DOCS_TARGET_NODE_URL` 现在只是远端默认节点，可留空
- 如果这行已经填了 `DingTalk_target_node_url`，远端 worker 会优先用这一行的节点，不依赖默认节点

### 想让产物自动进钉钉交付 outbox 还要配什么

- 只要一个环境变量：`AUTO_MANUAL_DELIVERY_OUTBOX_ROOT`，指向一个 git 之外的目录（仓库已 ignore `/output/`，所以 `output/outbox` 可直接用）。不设这个变量整条链路静默不动，其它 worker 行为完全不变
- 配好后每次成功 Publish 会在 `<root>/<job_id>/` 落一份产物（PDF / handoff zip / DOCX / Markdown）加一个 `delivery_manifest.json`，交给交付 agent 消费；`latex/`、`html/` 渲染目录不进 outbox
- `构建结果` 会多一条注记：`delivery_outbox=ok`（附 `delivery_outbox_job=<job id>`）、`delivery_outbox=skipped`（该目标没在 [`../data/dingtalk_delivery_map.csv`](../../data/dingtalk_delivery_map.csv) 里，属正常状态）、或 `delivery_outbox=failed`（附原因）。投递侧出问题不会把已经上传成功的构建行判失败
- 哪些目标会投递看那张映射表：按 `(型号, 区域)` 一行，对应钉钉的项目代码 + 安规 + 该区域整本覆盖的文案语言集合。Publish 行的 `Lang` 必须留空、产出的是一本多语合订本，所以映射按区域而不是按语言
- 验收单个 drop：`python -m tools.delivery_outbox --manifest <root>/<job_id>/delivery_manifest.json`
- 已消费的 job 目录不会自动回收（里面是完整 PDF 和 zip），要定期清理；同一目标同一版本同一秒内重复 Publish 会被拒绝而不是覆盖

Publish 不直接复用旧 Build Draft Package 产物，但为了保证正式文档与当前评审内容一致，应继续沿用同一条 review / PR 分支的 `Git_ref`；正式回写给业务侧的主链接是 PDF，DOCX 只保留在 release 目录里做留档。

## 7. 飞书自动化应该分成三条

### 自动化 1：进入 Review

条件建议：

- `是否进入Review = 勾选`
- `Review_status = NotStarted`

动作：

- 调 GitHub `feishu-start-review.yml`
- `ref` 应该固定用 `main`

### 自动化 2：构建 Build Draft Package

条件建议：

- `Workflow_action = Build Draft Package`
- `是否触发文档构建 = Y`
- `是否立即构建 = 勾选`

动作：

- 调 GitHub `feishu-draft-build-queue.yml`
- `ref` 应该固定用 `main`
- 真正的构建源以 `Document_link.Git_ref` 为准，而且 Build Draft Package 行不能缺这个字段

### 自动化 3：构建 Publish

条件建议：

- `Workflow_action = Publish`
- `是否触发文档构建 = Y`
- `是否立即构建 = 勾选`

动作：

- 调 GitHub `feishu-build-queue.yml`
- `ref` 应该固定用 `main`
- workflow 由 `main` 承载，但真正的构建源以 `Document_link.Git_ref` 为准
- 要保证正式 Publish 和当前 review 一致，就让 `Git_ref` 保持指向当前 review / PR 分支
