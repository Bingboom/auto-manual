# 快速开始指南

Updated: 2026-04-17

这份指南只讲当前真实可用的工作方式。
核心规则只有一句：

- 结构化数据看 Feishu phase2 源表
- Start Review 看 `Review Init`；Build Draft Package 看 PR 分支里的 [`docs/_review/`](../docs/_review)
- Publish 默认看 `Document_link.Git_ref` 指向的 review / PR 分支；只有 `Git_ref` 为空时，才会退回当前 queue worker 所在分支（远端通常是 `main`）

## 1. 先分清三张表各自负责什么

### 1.1 phase2 源表

这些表是结构化数据真源：

- `Spec_Master`
- `Spec_Footnotes`
- `Spec_Notes`
- `spec_titles`
- `symbols_blocks`

你要改参数、规格、注脚、标题顺序、symbols，就改这些表。

不要把 [`data/phase2/`](../data/phase2) 当成主编辑面。
只有当 `Document_link.是否强制刷新数据 = 勾选` 时，队列才会在这次构建前执行 `sync-data`；不勾时会直接复用当前本地 snapshot。

### 1.2 Review Init 表

这张表只做 Start Review 动作：把文档拉进 review，或者强制重开并按最新模板重新 seed。

建议字段：

- `Document_ID`
- `Document_Key`
- `Build_family`
- `Lang`
- `Version`
- `Review_status`
- `是否进入Review`
- `Git_ref`
- `PR_url`
- `Initial_result`
- `Remarks`

这张表触发后，系统会按 `Document_Key` 对应的 `Model + Region` 启动 review。`Start Review` 的语义现在是“强制重开并按最新模板重新 seed”：

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
- `Document link`
- `Document link_dd`
- `data_sync`
- `构建结果`

它负责：

- `Workflow_action` 是唯一队列语义字段；强制重开 review / 重新 seed 填 `Start Review`，Review 阶段反复构建填 `Build Draft Package`，Publish 阶段填 `Publish`
- `Doc_phase` 不再参与队列路由，保持留空即可
- 把结果链接回写到表里
- `Build Draft Package` 仍把 DOCX 链接回写到 `Document link`
- `Publish` 会把主交付 PDF 链接回写到 `Document link`，并把 release 留档 DOCX 路径写回 `Document directory`
- 如果当前启用了 DingTalk mirror，且表里存在 `Document link_dd`，队列会把镜像 DingTalk 节点链接写到这个字段；`Document link` 仍保持 Feishu/wiki 主字段
- 如果当前启用了 DingTalk mirror，且表里存在 `是否上传钉钉`，这列就是行级开关：勾选才同步 DingTalk，不勾就只走 Feishu/wiki
- 如果表里没有 `是否上传钉钉`，worker 就按当前全局模式处理整行：开启 mirror 的 worker 会同步 DingTalk，Feishu-only worker 不会同步
- 如果当前启用了 DingTalk mirror，且该行还填了 `DingTalk_target_node_url`，worker 会优先同步到这个行级节点；只有该字段为空时，才回退到全局 `DINGTALK_DOCS_TARGET_NODE_URL`
- 如果该行还填了 `operator_union_id`，worker 会优先从 `AUTO_MANUAL_DINGTALK_SESSION_ROOT/<operator_union_id>.json` 读取该操作员的钉钉会话；找不到时才回退到全局 `DINGTALK_DOCS_*`
- `DingTalk_session_key` 和 `钉钉会话键` 也可以作为 `operator_union_id` 的别名；三者都会映射到同一个 session 文件名
- 如果你在表里填的是 `alice`，那就要在本机或 worker 的 session 目录里准备 `alice.json`；如果缺这个文件且也没有全局 `DINGTALK_DOCS_*`，队列会在 build 前直接失败并把原因写回 `构建结果`
- 只有当 `是否强制刷新数据 = 勾选` 时，队列才会在这次构建前刷新一次 phase2；否则直接复用当前本地 snapshot
- `data_sync` 会回写 `refreshed / skipped / failed`

## 2. Build Draft Package 和 Publish 的原料分别是什么

### Build Draft Package

Build Draft Package 的原料是：

- 当前 phase2 snapshot；如果这条记录勾了 `是否强制刷新数据`，队列会先把它刷新成 Feishu 最新数据
- PR 分支代码
- PR 分支里的 [`docs/_review/`](../docs/_review)

这表示：

- 结构化数据改动看 Feishu
- 评审文稿改动看 PR 分支里的 `_review`

如果你在 PR 里直接改 [`data/phase2/*.csv`](../data/phase2)，Build Draft Package 不会把它当最终真源。
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

## 2.1 OpenClaw Phase 2 自然语言入口怎么接

如果你要让 OpenClaw 在飞书里按自然语言去操作这套流程，推荐固定成两个确定性入口：

1. 查状态或查记录时，先查表定位唯一目标行：
   - `python build.py queue-query --config config.us.yaml --query-text "查 JE-1000F_US_0.3 的 Build Draft Package" --json`
   - 如果要先让 OpenClaw 看结构化 dry-run 结果，再走下一步：`python build.py queue-resolve-action --config config.us.yaml --query-text "发布 JE-1000F_US_0.3" --json`
2. 要真正执行时，直接走一条确定性命令：
   - `python build.py queue-execute --config config.us.yaml --query-text "请帮我构建 JE-1000F_US_en_0.3，并返回 Build Draft Package 记录。只返回 record_id、Git_ref、构建结果、Document link。"`
   - 如果这条命令最终会命中 `Workflow_action = Publish`，要额外带上 `--confirm-publish`
3. 只有在排查问题或需要人工拆步骤时，再手动触发控制层：
   - `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch <start-review|build-draft> <record_id>`
   - `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch publish <record_id> confirm`
4. 如果要直接接飞书 IM 消息入口，而不是通过 OpenClaw 命令面板：
   - 本机直连、不要服务器中转时：启动 `python build.py listen-message-control --config config.us.yaml`
   - 这种模式走的是 `lark-cli event +subscribe` 的长连接；飞书应用里要先把 `im.message.receive_v1` 事件加上并发布
   - 如果同一台机器还要保留旧 app 的本地 `lark-cli` 配置，先设置 `FEISHU_IM_LARK_CLI_HOME=单独目录`，再在那个目录下初始化新 app 的 `lark-cli` 配置
   - 它仍然只处理这套文档控制层支持的动作和状态问题，例如 `开始 review ...`、`帮我生成 ... 草稿`、`发布 ...`、`为什么 ... 构建失败`
   - 如果你要的是公网 callback / 多实例 / 长期托管，再改用下面的 webhook adapter
   - 启动 `node integrations/openclaw/feishu-im-webhook-adapter/server.mjs`
   - 如果部署在长期运行的 ECS 上，改用 [`../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/`](../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/) 里的 wrapper 和 `systemd` unit 模板，不要长期靠手工 `nohup`
   - 把 Feishu 事件订阅指向这个 adapter 的 callback URL
   - 如果飞书事件订阅启用了加密模式，给 adapter env 增加 `FEISHU_IM_ENCRYPT_KEY`

这样做的目的只有一个：

- 不让自然语言入口凭空猜 `record_id`
- 不让自然语言入口临场拼“查表 -> dispatch -> 等待 -> 回读”的步骤
- 仍然以 Feishu 队列表为唯一真源
- 如果一句话里已经给了完整 `Document_ID`，例如 `JE-1000F_US_0.3`，解析器会优先把它当成精确 `Document_ID`，而不是拆成猜测的 `Build_family` 或 `Lang`
- 解析器现在也支持空格写法，例如 `帮我生成 JE-1000F US 0.3 草稿`、`开始 review JE-1000F us-merged`、`为什么 JE-1000F US 0.3 构建失败`

当前 Phase 2 控制层仍然只把下面这个字段当主交付链接：

- `Document link`

其中 Build Draft Package 场景下这里通常是 DOCX 链接，Publish 场景下这里会回写 PDF 链接。

如果当前启用了 DingTalk mirror，worker 还会在表里额外写：

- `Document link_dd`

但 `queue-query / queue-execute / OpenClaw` 仍以 `Document link` 为主返回字段；Publish 时也就是返回 PDF URL。

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

- [`.github/workflows/feishu-start-review.yml`](../.github/workflows/feishu-start-review.yml)

它会：

1. 同步最新 phase2 快照
2. 从最新 `main` 起 review worktree
3. 按最新模板和最新 snapshot 重新生成这个目标的 [`docs/_review/...`](../docs/_review)
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

- [`.github/workflows/feishu-draft-build-queue.yml`](../.github/workflows/feishu-draft-build-queue.yml)

它会：

1. workflow 由默认分支承载
2. 执行 `process-build-queue --workflow-action build-draft-package`
3. 只有当 `是否强制刷新数据 = 勾选` 时，队列才先执行一次 `sync-data`
4. 再按 `Document_link.Git_ref` fetch 对应的 review / PR 分支到临时 worktree
5. 然后基于那条分支里的 `_review` 构建 Build Draft Package Word
6. 如果当前启用了 DingTalk mirror 且 `是否上传钉钉 = 勾选`，就同步 DingTalk；如果同时填了 `DingTalk_target_node_url`，优先同步到该行节点；否则退回全局默认 DingTalk 节点；未勾选则只保留 Feishu/wiki 上传；如果表里没有 `是否上传钉钉`，则按当前 worker 的全局模式决定是否同步
7. 回写：
   - `开始构建时间`
   - `构建结果`
   - `data_sync`
   - `Document directory`
   - `Document link`
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

- [`.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml)

它会：

1. workflow 可以由默认分支承载
2. 执行 `process-build-queue --workflow-action publish`
3. 只有当 `是否强制刷新数据 = 勾选` 时，队列才先执行一次 `sync-data`
4. 如果 `Document_link.Git_ref` 有值，队列会先 fetch 这条分支，并在临时 worktree 中按这条分支执行 `build.py publish`（内部会跑 `check -> diff-report -> word -> pdf -> release-manifest`）和 `build.py html --source review`
5. 如果当前启用了 DingTalk mirror 且 `是否上传钉钉 = 勾选`，就同步 DingTalk；如果同时填了 `DingTalk_target_node_url`，优先同步到该行节点；否则退回全局默认 DingTalk 节点；未勾选则只保留 Feishu/wiki 上传；如果表里没有 `是否上传钉钉`，则按当前 worker 的全局模式决定是否同步
6. 回写：
   - `开始构建时间`
   - `构建结果`
   - `data_sync`
   - `Document directory（release 留档 DOCX 路径）`
   - `Document link（主交付 PDF 链接）`
   - `Document link_dd（仅启用 DingTalk mirror 且字段存在时；镜像同一份 Publish PDF）`
7. 把最新 publish HTML 刷新到 Vercel；如果 `Document_link` 里有 `HTML_link` 字段，workflow 会把这次 deploy 返回的 Vercel URL 再回写到该字段。如果表里还有 `RTD_link`，并且 GitHub 仓库变量 `AUTO_MANUAL_RTD_URL` 已配置，workflow 也会把稳定的 Read the Docs 入口写回去。GitHub Actions summary 里的 Vercel URL 可能会被脱敏打星，原始链接以 `HTML_link`、`publish_meta.json` 和 `openclaw-run-metadata` 为准

### 远端 GitHub worker 想支持 DingTalk 还要配什么

- GitHub Secrets 至少要有：
  - `DINGTALK_DOCS_A_TOKEN`
  - `DINGTALK_DOCS_XSRF_TOKEN`
  - `DINGTALK_DOCS_COOKIE`
- 还要显式加一个 GitHub Actions repository variable：
  - `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER = dingtalk_alidocs_session`
- `DINGTALK_DOCS_TARGET_NODE_URL` 现在只是远端默认节点，可留空
- 如果这行已经填了 `DingTalk_target_node_url`，远端 worker 会优先用这一行的节点，不依赖默认节点

Publish 不直接复用旧 Build Draft Package 产物，但为了保证正式文档与当前评审内容一致，应继续沿用同一条 review / PR 分支的 `Git_ref`；正式回写给业务侧的主链接是 PDF，DOCX 只保留在 release 目录里做留档。

## 6. 你平时到底该改哪里

### 要改结构化数据

去改 Feishu phase2 源表：

- `Spec_Master`
- `Spec_Footnotes`
- `Spec_Notes`
- `spec_titles`
- `symbols_blocks`

### 要改 Build Draft Package 文稿

去改 PR 分支里的：

- [`docs/_review/`](../docs/_review)

### 不要再把这里当主编辑面

- [`data/phase2/`](../data/phase2)

它现在只是构建时使用的本地物化快照；只有你勾了 `是否强制刷新数据`，队列才会先把它刷新到最新。
不是 Build Draft Package / Publish 的人工主编辑面。

### 本地自测先隔离生成物

本地跑 `check`、`diff-report`、`release-manifest`、`publish` 或手动消费 queue 时，优先加：

- `python scripts/local_build.py check|diff-report|release-manifest|publish ...`

这样生成的 `docs/_build`、`reports/version_tracking`、`reports/releases` 会落到 `.tmp/staging/` 下，不会污染源码工作区。
`review` 不支持这个参数，因为它本来就要 seed 仓库里的 [`docs/_review/`](../docs/_review)。

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

## 8. 最短操作清单

### 如果你要第一次进入 Review

1. 在 `Review Init` 表新增一行
2. 勾 `是否进入Review`
3. 等系统回写 `Git_ref` 和 `PR_url`

### 如果你要继续出 Build Draft Package

1. 在 Feishu 改 phase2 数据
2. 在 PR 分支改 `_review`
3. 在 `Document_link` 里设：
   - `Workflow_action = Build Draft Package`
   - `是否触发文档构建 = Y`
   - `是否立即构建 = 勾选`
   - `是否强制刷新数据 = 只有这次确实要拉最新 phase2 时才勾`

### 如果你要正式 Publish

1. 确认当前 review / PR 分支内容已准备好
2. 确认 `Document_link.Git_ref` 仍指向这条 review / PR 分支
3. 在 `Document_link` 里设：
   - `Workflow_action = Publish`
   - `是否触发文档构建 = Y`
   - `是否立即构建 = 勾选`
   - `是否强制刷新数据 = 只有这次确实要拉最新 phase2 时才勾`
4. 等队列回写 `Document directory`（DOCX 留档路径）、`Document link`（PDF 链接）；如果表里有 `HTML_link`，还会看到最新 Vercel HTML 链接；如果表里有 `RTD_link` 且 `AUTO_MANUAL_RTD_URL` 已配置，还会看到稳定的 Read the Docs 入口

## 9. 一句话规则

- 改数据：去改 Feishu
- 进 Review：走 `Review Init`
- 出 Build Draft Package：走 PR 分支 + `_review`
- 做 Publish：走 `Document_link` + `Git_ref` 指向的 review / PR 分支

## 9.5 OpenClaw Phase 1 操作入口

如果你们已经把 OpenClaw 作为统一控制层接到 Feishu，上面的三条自动化也可以直接换成 OpenClaw 命令入口：

- `/start-review <review_init_record_id>`
- `/build-draft <document_link_record_id>`
- `/publish <document_link_record_id> confirm`
- `/manual-status [run_id|last]`

注意：

- OpenClaw 只负责统一入口和状态查询，不直接执行仓库里的 `build.py`
- 真正的远端执行仍然是 `main` 上的 GitHub worker
- OpenClaw dispatch 现在会额外带一个 `openclaw_dispatch_nonce`，worker 完成后也会上传 `openclaw-run-metadata`，这样状态查询可以稳定追踪到同一次手动触发
- 如果同一批 `en / es / fr` Build Draft Package 行在很短时间内连续触发，OpenClaw 现在会复用一个共享 draft queue worker，而不是给每个语言各发一条会互相竞争的 GitHub queue run
- 插件包路径是 [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer)

## 10. 2026-04 更新

- `Review Init` 和 `Document_link` 现在都是先按 `Build_family` 路由，再决定是否按 `Document_Key` 合并；只有像 `us-merged` 这类启用了 `queue_by_document_key` 的 family，才会把同一个 `Document_Key` 的多行合成一次 review / build。
- US 的 `config.us.yaml` 现在是合并多语言入口，会产出一个合并 `en + fr + es` 的 Word：`docs/_build/<model>/US/word/manual_<model>_us.docx`。
- 队列表建议直接填写 `Build_family`：`us-merged` / `us-en` / `us-es` / `us-fr` / `jp-ja` / `cn-zh`；`Lang` 现在只保留为兼容字段，不再是主路由字段。
- 合并 US 流程请填 `Build_family = us-merged`，`Lang` 可以留空；单语言流程请填对应单语言 family，`Lang` 只填一个语言值即可。
- 这条合并 US 流程不再要求法语、西语分别先创一份独立初稿 review bundle。
- `Spec_Master` 里由 `Source_lang` 定义 source language；`*_source` 内容必须有，其他语言列在 CSV 驱动内容里可以为空，系统会自动回退到 source language 文本。
