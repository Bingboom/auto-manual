# 快速开始指南

Updated: 2026-10-23

这份指南讲按需使用的飞书队列评审、构建与发布，只写当前真实可用的工作方式。
资料写作的主线在资料开发工作台 Hello-Docs-Review，见[工作台说明](../mirrors/Hello-Docs-Review/README.md)。
核心规则只有一句：

- 结构化数据看 Feishu phase2 源表
- Start Review 看 `Review Init`；Build Draft Package 看 PR 分支里的 [`docs/_review/`](../docs/_review)
- Publish 默认看 `Document_link.Git_ref` 指向的 review / PR 分支；只有 `Git_ref` 为空时，才会退回当前 queue worker 所在分支（远端通常是 `main`）

查询已发布欧规产品信息：现有钉钉 BlockClaw 启用后可问“JE-2000F 欧规 USB-C
输出功率是多少？”，或用 `/manual-query JE-2000F USB-C输出` 查原文章节。
首次启用见[欧规说明书查询](../code-as-doc/dev/eu_manual_query.md#activation-on-the-existing-gateway)。

## 本指南怎样分页

本文保留核心规则、§6 你平时到底该改哪里和 §9 一句话规则，其余章节按原编号原样放在
`quick_start_guide/` 下的分页里。只打开任务需要的那一页；示例或流程变化时更新所属分页，
新增分页时在下表加一行，不要把内容追加到本文。

| 章节 | 页面 | 什么时候读 |
| --- | --- | --- |
| §1 | [`tables.md`](quick_start_guide/tables.md) | 弄清 phase2 源表、Review Init、Document_link 和图片资产三张表各管什么 |
| §2–§5、§7 | [`review-and-publish.md`](quick_start_guide/review-and-publish.md) | 在表里发起 Start Review、Build Draft Package 或 Publish：原料、怎么填、系统做什么、该看到什么，以及三条飞书自动化 |
| §2.1、§9.5 | [`openclaw.md`](quick_start_guide/openclaw.md) | 使用 OpenClaw 的 Phase 2 自然语言入口或 Phase 1 操作入口 |
| §8 | [`short-checklists.md`](quick_start_guide/short-checklists.md) | 照最短清单操作：首次进 Review、继续出包、正式 Publish 与 Web Publish、方案 2 InDesign 复刻、BP candidate 构建 |
| §10 | [`updates-and-local-checks.md`](quick_start_guide/updates-and-local-checks.md) | 查 2026-04 之后的更新，或某个目标的本地验收示例（合并配置单语、加电包日语、SolarSaga、FridgeGuard、SlimPower H1 等） |

## 6. 你平时到底该改哪里

### 要改结构化数据

去改 Feishu phase2 源表：

- `规格参数明细`
- `页面占位参数`
- `Spec_Footnotes`
- `Spec_Notes`
- `Manual_Copy_Source`
- `symbols_blocks`

### 要改 Build Draft Package 文稿

去改 PR 分支里的：

- [`docs/_review/`](../docs/_review)

### 不要再把这里当主编辑面

- [`data/phase2/`](../data/phase2)

它现在只是构建时使用的本地物化快照；只有你勾了 `是否强制刷新数据`，队列才会先把它刷新到最新。
不是 Build Draft Package / Publish 的人工主编辑面。

Publish 成功时，实际参与构建的这份快照会随版本归档到
`reports/releases/<model>/<region>/<lang>/versions/<version>/snapshot/`。
同一版本只能复用完全相同的快照；不要手改归档，也不要用后来同步的
`data/phase2` 覆盖它。

版本发布完成后，用清单做一次历史重建验收：

```bash
python build.py release-rebuild-verify \
  --manifest reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json
```

该命令要求当前工具链与发布清单完全一致，并在临时 worktree 中用清单记录的
Git SHA 和归档 snapshot 重建 DOCX、Markdown、PDF。三者必须逐字节 SHA-256
一致；默认报告写到对应 `versions/<version>/rebuild_verification.json`。

### 本地自测先隔离生成物

本地跑 `check`、`diff-report`、`release-manifest`、`publish` 或手动消费 queue 时，优先加：

- `python scripts/local_build.py check|diff-report|release-manifest|publish ...`

这样生成的 `docs/_build`、`reports/version_tracking`、`reports/releases` 会落到 `.tmp/staging/` 下，不会污染源码工作区。
`review` 不支持这个参数，因为它本来就要 seed 仓库里的 [`docs/_review/`](../docs/_review)。

## 9. 一句话规则

- 改数据：去改 Feishu
- 进 Review：走 `Review Init`
- 出 Build Draft Package：走 PR 分支 + `_review`
- 做 Publish：走 `Document_link` + `Git_ref` 指向的 review / PR 分支
