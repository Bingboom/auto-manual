# 快速开始指南

Updated: 2026-04-03

这份指南只讲当前真实可用的工作方式。
核心规则只有一句：

- 结构化数据看 Feishu phase2 源表
- Draft 看 PR 分支里的 [`docs/_review/`](../docs/_review)
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
队列构建前会自动 `sync-data`，所以本地和远程都会重新从 Feishu 拉最新快照。

### 1.2 Review Init 表

这张表只做一次性动作：把文档拉进 review。

建议字段：

- `Document_ID`
- `Document_Key`
- `Lang`
- `Version`
- `Review_status`
- `是否进入Review`
- `Git_ref`
- `PR_url`
- `Initial_result`
- `Remarks`

这张表触发后，系统会按 `Document_Key` 对应的 `Model + Region` 启动 review：

1. 先检查 `main` 是否已经提交过这个目标对应的 review 根目录
2. 如果已经有旧 review 内容，就拒绝重复创建，并回写：
   - `Initial_result = 不允许重复创建`
   - `Remarks = 如需强制刷新内容，请在vs通过相关git命令操作，具体详见文档quick_start_guide.md.`
3. 如果没有旧 review 内容，才创建或复用 review 分支
4. seed `docs/_review`
5. 创建或复用 PR
6. 回写 `Git_ref`
7. 回写 `PR_url`
8. 把 `Review_status` 改成 `InReview`

`Review Init` 这条链默认直接复用 `Document_link` 的表 / 视图绑定，所以 GitHub 侧继续用 `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` 和 `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID` 即可，不需要单独再配一组 `REVIEW_INIT_*` secrets。

### 1.3 Document_link 表

这张表只做“反复构建文档”。

关键字段：

- `Document_Key`
- `Lang`
- `Version`
- `Git_ref`
- `Doc_phase`
- `是否触发文档构建`
- `是否立即构建`
- `Document directory`
- `Document link`
- `构建结果`

它负责：

- `Doc_phase = Draft` 时出 Draft 文档
- `Doc_phase = Publish` 时出 Publish 文档
- 把结果链接回写到表里

## 2. Draft 和 Publish 的原料分别是什么

### Draft

Draft 的原料是：

- Feishu phase2 最新数据
- PR 分支代码
- PR 分支里的 [`docs/_review/`](../docs/_review)

这表示：

- 结构化数据改动看 Feishu
- 评审文稿改动看 PR 分支里的 `_review`

如果你在 PR 里直接改 [`data/phase2/*.csv`](../data/phase2)，Draft 队列不会把它当最终真源。
因为构建前会先自动 `sync-data`，把这份目录刷新成 Feishu 当前快照。
如果这条记录已经由 `Review Init` 回写过 `Git_ref`，后续 Draft / Publish 都应继续沿用这条分支，不要手动清空。

### Publish

Publish 的原料是：
- Feishu phase2 最新数据
- `Document_link.Git_ref` 指向分支上的代码
- 该分支里的 review 内容

如果 `Git_ref` 为空，才会退回当前 queue worker 所在分支；远端 worker 通常是 `main`。

## 3. 场景一：第一次把文档拉进 Review

这是一次性动作。做完后，这份文档才算正式进入 review 阶段。

### 你在表里怎么填

在 `Review Init` 表新增一行，至少填：

- `Document_ID`
- `Document_Key`
- `Lang`
- `Version`
- `Review_status = NotStarted`
- `是否进入Review = 勾选`

### 系统会做什么

触发 review-init workflow：

- [`.github/workflows/feishu-start-review.yml`](../.github/workflows/feishu-start-review.yml)

它会：

1. 同步最新 phase2 快照
2. 先检查 `main` 是否已经提交过这个目标对应的 review 根目录
3. 如果旧 review 已提交，则拒绝重复创建，并回写：
   - `Initial_result = 不允许重复创建`
   - `Remarks = 如需强制刷新内容，请在vs通过相关git命令操作，具体详见文档quick_start_guide.md.`
4. 如果旧 review 不存在，才创建或复用 review 分支
5. 生成这个目标的 [`docs/_review/...`](../docs/_review)
6. push 分支
7. 创建或复用 PR
8. 回写：
   - `Git_ref`
   - `PR_url`
   - `Review_status = InReview`
   - 清掉 `是否进入Review`

### 这一步完成后你应该看到什么

- 多维表里出现 `Git_ref`
- 多维表里出现 `PR_url`
- 仓库里已经有 PR
- 对应分支里已经有 review 内容
- 如果 `main` 已经提交过这个目标对应的 review 根目录，多维表会回写 `Initial_result = 不允许重复创建`

如果这一步没做，后面的 Draft 只是“构建一条记录”，不算完整的 review 流程。

## 4. 场景二：Review 过程中反复出 Draft

这是反复动作。进入 review 后，可以一直这样用。

### 你在表里怎么填

在 `Document_link` 表对应那一行填：

- `Document_Key`
- `Lang`
- `Version`
- `Doc_phase = Draft`
- `是否触发文档构建 = Y`
- `是否立即构建 = 勾选`

### 系统会做什么

触发 Draft workflow：

- [`.github/workflows/feishu-draft-build-queue.yml`](../.github/workflows/feishu-draft-build-queue.yml)

它会：

1. checkout 你指定的 PR 分支
2. 执行 `process-build-queue --doc-phase draft`
3. 队列内部先自动 `sync-data`
4. 再自动 `sync-review`
5. 然后基于当前分支的 `_review` 构建 Draft Word
6. 回写：
   - `开始构建时间`
   - `构建结果`
   - `Document directory`
   - `Document link`

### Draft 最容易配错的地方

1. `ref` 必须是 PR 分支，不是 `main`
2. `queue_record_id` 必须是真实 record id，不能写成字符串 `<record_id>`
3. `是否触发文档构建` 必须是 `Y`
4. 只有 `是否立即构建` 勾选但没有 `Y`，不会构建

## 5. 场景三：Review 完成，进入 Publish

这是正式发布动作。

### 你在表里怎么填

在 `Document_link` 表对应那一行填：

- `Doc_phase = Publish`
- `是否触发文档构建 = Y`
- `是否立即构建 = 勾选`

### 系统会做什么

触发 Publish workflow：

- [`.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml)

它会：

1. workflow 可以由默认分支承载
2. 执行 `process-build-queue --doc-phase publish`
3. 队列内部先自动 `sync-data`
4. 如果 `Document_link.Git_ref` 有值，队列会先 fetch 这条分支，并在临时 worktree 中按这条分支执行 `build.py publish` 和 `build.py html --source review`
5. 回写：
   - `开始构建时间`
   - `构建结果`
   - `Document directory`
   - `Document link`
6. 把最新 publish HTML 刷新到 Vercel

Publish 不直接复用旧 Draft 产物，但为了保证正式文档与当前评审内容一致，应继续沿用同一条 review / PR 分支的 `Git_ref`。

## 6. 你平时到底该改哪里

### 要改结构化数据

去改 Feishu phase2 源表：

- `Spec_Master`
- `Spec_Footnotes`
- `Spec_Notes`
- `spec_titles`
- `symbols_blocks`

### 要改 Draft 文稿

去改 PR 分支里的：

- [`docs/_review/`](../docs/_review)

### 不要再把这里当主编辑面

- [`data/phase2/`](../data/phase2)

它现在只是构建前自动刷新的物化快照。
不是 Draft / Publish 的人工主编辑面。

## 7. 飞书自动化应该分成三条

### 自动化 1：进入 Review

条件建议：

- `是否进入Review = 勾选`
- `Review_status = NotStarted`

动作：

- 调 GitHub `feishu-start-review.yml`

### 自动化 2：构建 Draft

条件建议：

- `Doc_phase = Draft`
- `是否触发文档构建 = Y`
- `是否立即构建 = 勾选`

动作：

- 调 GitHub `feishu-draft-build-queue.yml`
- `ref` 必须是 PR 分支

### 自动化 3：构建 Publish

条件建议：

- `Doc_phase = Publish`
- `是否触发文档构建 = Y`
- `是否立即构建 = 勾选`

动作：

- 调 GitHub `feishu-build-queue.yml`
- workflow 可以由默认分支承载，但真正的构建源以 `Document_link.Git_ref` 为准
- 要保证正式 Publish 和当前 review 一致，就让 `Git_ref` 保持指向当前 review / PR 分支

## 8. 最短操作清单

### 如果你要第一次进入 Review

1. 在 `Review Init` 表新增一行
2. 勾 `是否进入Review`
3. 等系统回写 `Git_ref` 和 `PR_url`

### 如果你要继续出 Draft

1. 在 Feishu 改 phase2 数据
2. 在 PR 分支改 `_review`
3. 在 `Document_link` 里设：
   - `Doc_phase = Draft`
   - `是否触发文档构建 = Y`
   - `是否立即构建 = 勾选`

### 如果你要正式 Publish

1. 确认当前 review / PR 分支内容已准备好
2. 确认 `Document_link.Git_ref` 仍指向这条 review / PR 分支
3. 在 `Document_link` 里设：
   - `Doc_phase = Publish`
   - `是否触发文档构建 = Y`
   - `是否立即构建 = 勾选`
4. 等队列回写 `Document directory`、`Document link`，并确认 Vercel 最新页面已刷新

## 9. 一句话规则

- 改数据：去改 Feishu
- 进 Review：走 `Review Init`
- 出 Draft：走 PR 分支 + `_review`
- 做 Publish：走 `Document_link` + `Git_ref` 指向的 review / PR 分支

## 10. 2026-04 更新

- `Review Init` 现在按 `Document_Key` 合并处理；同一个 `Document_Key` 就算有多条不同 `Lang` 的行，也只会创建一次 review 分支和 PR，然后把同一组 `Git_ref` / `PR_url` / `Review_status` 回写到这一组行里。
- US 的 `config.us.yaml` 现在是合并多语言入口，会产出一个合并 `en + fr + es` 的 Word：`docs/_build/<model>/US/word/manual_<model>_us.docx`。
- 这条合并 US 流程不再要求法语、西语分别先创一份独立初稿 review bundle。
- `Spec_Master` 里由 `Source_lang` 定义 source language；`*_source` 内容必须有，其他语言列在 CSV 驱动内容里可以为空，系统会自动回退到 source language 文本。
