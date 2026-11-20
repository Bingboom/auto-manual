# Merge Authorizations (gate-on-green registry)

Status: active

The single source of truth for **who may merge what without waiting for the operator's per-PR review**. Default remains AGENTS.md §8.6: agents do not self-merge. A self-merge is allowed only when a **live entry in the table
below covers the PR** and the gate-on-green protocol passes. Chat authority alone is not enough: when the operator grants an authorization in chat, the
agent's FIRST action is to record it here (this file is the durable form —
session memory is not), then act on it.

Decided by the operator on 2026-07-30 (four picks: all-checks-green
definition; branch-pattern + PR-list scoping; parity line stays live; the P0
skill batch #738–#742 stays operator-reviewed).

## Gate-on-green protocol

An authorized PR may be merged only when ALL of the following hold:

1. **Every check is green** — `gh pr checks <N> --watch` until settled, then
   verify each listed check is `pass`. This includes **non-required** checks,
   and `pending`/`queued` is NOT green (a PR was once merged on a pending
   check; a non-required secret-scan once caught a real finding — both are
   why "required checks only" was rejected).
2. **No changes-requested review and no unresolved review threads.**
3. **The PR is covered by a live table entry** (branch pattern or explicit PR
   number). Doubt about coverage = not covered; fall back to waiting.

Then: `gh pr merge <N> --squash --delete-branch`. If the line's workflow
requires it (e.g. an in-review target consuming the change), trigger the
matching rebuild/republish after merge.

Red path: pull the failing job's log, diagnose, fix or report — never merge
partially green, never re-run checks blindly to "wash" a real failure.

## Grant / revoke flow

- **Grant**: operator states the scope in chat → agent adds a row at the top of
  the live table below (the next free `MA-nnn` from
  `python tools/next_registry_id.py ma`, which counts main, the
  [archive](merge_authorizations_archive.md), open PRs and the checkout; scope,
  grant quote + date, expiry condition) → the entry is live once pushed.
  Time-boxed grants name their milestone/date; standing grants say "until revoked".
  Where `gh` cannot run, the tool reads open PRs from the GitHub API. Two windows
  asking at once can still get the same number: the maintainability guardrails
  then fail the PR that merges second, which renumbers its row before merging.
- **Revoke / expire**: operator says so, or the expiry condition is met →
  flip 状态 to 已失效 in the next touch of this file and, in the same commit,
  move the row unchanged to the top of the first table in the
  [archive](merge_authorizations_archive.md). Expired entries stay there as
  history; never delete rows.

## Registry

Live rows only (状态 生效); add new rows at the top. Expired rows, the gate-decision
addenda and per-grant notes live in the [archive](merge_authorizations_archive.md):
grep it by `MA-nnn` when you need one; do not read it whole.

| ID | Scope | Grant | Expiry | Status |
| --- | --- | --- | --- | --- |
| MA-476 | 仅本会话 JE-1000F / CN / zh（物料55060100034，同原稿SHA256 `7132a5ff27529c9edd60b501d147ade477445c3942a57008a7c8019fdc149b56`）发布验收修复：工程分支 `fix/web-je1000f-cn-published-phone-size` 将既有App手机图组26rem几何限制从图片文件名选择器改为共享组件稳定的 `data-reference-id` 选择器，封装新的不可变 `git-20261119-7132a5ff-dx2-layout-r1` 源包、冻结登记及验收证据；随后仅本目标的 Hello-Docs `publish -> main` 修复发布。沿用操作者原发布指令和已审阅的缩图要求；不改变正文、原稿、图片字节、共享运行时、workflow或线上飞书数据。允许按需同步main，在每个PR全部适用检查成功（含非必需，pending不算绿；按仓库守卫预期跳过项除外）、无changes-requested或未解决评审线程后squash合入并删除head；继续核验镜像、RTD精确提交、标准/兼容入口、资源与实际缩图尺寸。 | 「推上去提交发布」2026-11-20；同次上线验收发现资源池哈希改名使已审阅的App缩图样式失效，此项为完成该指令的必要修复 | 本目标修复发布和线上验收完成，或操作者撤销 | 生效（推送后生效） |
| MA-475 | 仅本会话 JE-1000F / CN / zh（物料55060100034，原PDF SHA256 `7132a5ff27529c9edd60b501d147ade477445c3942a57008a7c8019fdc149b56`）网页版发布：工程分支 `feat/web-je1000f-cn-dx2` 的源包、已确认的第15页两处改字、完整灰框SVG、App缩图/图注及封底排版、来源/组件/资产准入与冻结登记、发布验收记录；随后仅该目标的 Hello-Docs `publish -> main` 发布PR。允许按需同步最新main、完成本目标封存和发布检查，在每个PR全部适用检查成功（含非必需项，pending/queued不算绿）、无changes-requested或未解决评审线程后squash合入并删除head；随后核验镜像、RTD部署提交、标准入口、根别名、资源和桌面/手机显示。发布以本次已审阅Git源包为权威，Git-only执行，不创建队列行；仅按操作者随后明确确认新增本次原稿到04_资产源文件source_file（同SHA去重、上传后回读和下载哈希核验）及登记已确认EFUP10到Git公共素材，除此之外不写线上飞书源表或资产表；不含其它目标、workflow、依赖、公开CLI或schema改动。 | 「推上去提交发布」2026-11-20；随后确认「允许归档这份原稿（推荐）」「确认图标，继续发布（推荐）」 | 本目标发布和线上验收完成，或相关PR关闭，或操作者撤销 | 生效（推送后生效） |
| MA-474 | 仅本会话 PR #1802（head `chore/types-expand-web-rtd-mypy-gate`，「chore(types): expand strict mypy gate to Web-first core packages」，含本登记），不含其它：清理并消除 `tools/corpus`、`tools/product_matrix_base`、`tools/manual_knowledge`、`tools/rtd`、`tools/web` 的全部 `mypy --disallow-untyped-defs` 报错（`tools/web_publish` 仓库内无此包目录），将以上 5 个包纳入 `pyproject.toml`（`[[tool.mypy.overrides]]`）与 `tools/check_mypy_ratchet.py`（`PACKAGES`）强类型门禁（共 8 个包、0 基线报错），更新 `data/mypy_untyped_baseline.tsv`、`tests/test_mypy_ratchet.py` 与 `code-as-doc/build_doc_guide/ci-and-guardrails.md`，并在 `data/frozen_package_registry.json` 为固定 `tools/web/*.py` 的 65 个冻结包登记 `keep-frozen`（`--minutes 0`，零运行时／输出变更）。允许按需同步／变基至最新 `origin/main` 并在最终 head 全部适用检查成功（含非必需项，pending/queued 不算绿；工程仓库按守卫预期跳过的 `business-content` 除外）、无 changes-requested 或未解决评审线程后 squash 合入、回读 `main` SHA 并核验 `Sync Hello-Docs Mirror` 同步成功。不含其它 PR、线上飞书写入、依赖版本或 Base schema 改动。编号说明：main 已至 MA-473，按 `python -m tools.next_registry_id ma` 取 MA-474。 | 「确认授权 1802 合入」2026-11-19T21:47:46-08:00（操作者针对 PR #1802 下达 `gate-on-green` 授权） | PR #1802 合入回读 main SHA 且核验 `Sync Hello-Docs Mirror` 成功，或 PR 关闭，或操作者撤销 | 生效（推送后生效） |
| MA-473 | 仅本会话 PR #1801（head `chore/ci-upgrade-actions-node24-clone-depth`，「chore(ci): upgrade GitHub Actions to Node 24 and trim full clones」，含本登记），不含其它：将 `.github/workflows/*.yml` 与 `.github/actions/*/action.yml` 全部官方 Actions 升至原生 Node 24 主版本（`actions/checkout@v7`、`actions/setup-python@v7`、`actions/setup-node@v7`、`actions/cache@v6`、`actions/upload-artifact@v7`、`actions/github-script@v9`，`pandoc/actions/setup@v1` 保持不变）、将 `sync-hello-docs.yml` 4 处 checkout 改为 `fetch-depth: 1` 并更新 `scripts/sync_mirror.sh` 使用无父快照束 `refs/sync/snapshot`、为只读历史校验流（`verify-web-deployment.yml`、`web-publish-receipt.yml`、`workspace-data-verify.yml`、`review-branch-sync-check.yml`）在 `fetch-depth: 0` 下补充 `filter: blob:none`，以及同步更新对应 workflow 单测与 CI 文档。允许按需同步／变基至最新 `origin/main` 并在最终 head 全部适用检查成功（含非必需项，pending/queued 不算绿；工程仓库按守卫预期跳过的 `business-content` 除外）、无 changes-requested 或未解决评审线程后 squash 合入、回读 `main` SHA 并核验 `Sync Hello-Docs Mirror` 同步成功及 0 条 Node 20 告警。不含其它 PR、线上飞书写入、依赖或 Base schema 改动。编号说明：main 已至 MA-472，按 `python -m tools.next_registry_id ma` 取 MA-473。 | 「授权合入」2026-11-19T19:27:13-08:00（操作者针对 PR #1801 下达 `gate-on-green` 授权） | PR #1801 合入回读 main SHA 且核验 `Sync Hello-Docs Mirror` 成功，或 PR 关闭，或操作者撤销 | 生效（推送后生效） |
| MA-472 | 仅本会话以下两项 Item 3C PR，按顺序，不含其它：① PR #1799（head `feat/cli-wire-web-ir-commands`，「feat(cli): wire web-package, ir-qc, and ir-export into build.py」，含本登记）：将 `tools/web/package_build.py`、`tools/web/ir_qc.py` 与 `tools/manual_knowledge/ir_export.py` 经子包 facade 接入 `build.py`（`web-package`、`ir-qc`、`ir-export`）及对应单测与文档；② PR #1800（head `ci/validation-add-web-ir-checks`，「ci(validation): add web-ir-checks job to Manual Validation」）：在 `.github/workflows/manual-validation.yml` 新增 `web-ir-checks` 作业并更新 `tests/test_manual_validation_workflow.py`、`tests/test_business_content.py` 及 CI 文档。允许两单按需同步／变基至最新 `origin/main` 并先将 `#1800` 切换为 `--base main` 后依次在各自最终 head 全部适用检查成功（含非必需项，pending/queued 不算绿；工程仓库按守卫预期跳过的 `business-content` 除外）、无 changes-requested 或未解决评审线程后顺序 squash 合入、回读 `main` SHA 并核验 `Sync Hello-Docs Mirror` 同步成功。不含其它 PR、线上飞书写入、依赖或 Base schema 改动。编号说明：main 已至 MA-471，按 `python -m tools.next_registry_id ma` 取 MA-472。 | 「授权 gate-on-green 依次合入 #1799 与 #1800（先合 #1799，再将 #1800 自动切回 --base main 跑绿合入）」2026-11-19T02:30:11-08:00（操作者直接下达 `gate-on-green` 授权） | #1799 与 #1800 均合入回读 main SHA 且核验 `Sync Hello-Docs Mirror` 成功，或任一 PR 关闭，或操作者撤销 | 生效（推送后生效） |
| MA-471 | 仅本会话以下两项 auto-manual 仓库治理 PR，按顺序，不含其它：① PR #1797（head `docs/archive-expired-merge-authorizations`，「docs(governance): archive expired MA rows from active registry」，含本登记）：将 89 条已失效／已消费的 `MA-*` 行（`MA-470` 至 `MA-179` 含 `MA-248`/`MA-260`/`MA-259`/`MA-280`）移入 `code-as-doc/dev/merge_authorizations_archive.md` 并保留 2 条常设授权（`MA-160`、`MA-002`），将 `merge_authorizations.md` 降至 61 行；② PR #1798（head `chore/untrack-generated-docs-build`，「chore(repo): stop tracking generated outputs under docs/_build」）：`.gitignore` 简化为 `docs/_build/` 并从 Git HEAD 移除全部 234 个已追踪的 `docs/_build/` 生成产物（`157.61 MiB`）。允许各 PR 在需要时以普通合并或变基同步最新 main 并补必要验证；各自最终 head 全部适用检查成功（含非必需项，pending/queued 不算绿；工程仓库按守卫预期跳过的 `business-content` 除外）、无 changes-requested 或未解决评审线程后依次 squash 合入并删除远端 head、回读 main SHA，随后核验 `Sync Hello-Docs Mirror` 同步成功且三仓库（`auto-manual`、`Hello-Docs`、`Hello-Docs-Review`）`main` 均不再包含 `docs/_build/` 文件。不含其它 PR、线上飞书多维表写入、workflow、依赖、公开 CLI 或 schema 改动。编号说明：main 已至 MA-470，按 `python -m tools.next_registry_id ma` 取 MA-471。 | 「授权」2026-11-18T23:05:21-08:00（操作者针对 3A #1797 与 3B #1798 下达 `gate-on-green` 授权） | #1797 与 #1798 均合入回读 main SHA 且核验 `Sync Hello-Docs Mirror` 在三仓库清理 `docs/_build/` 完成，或任一 PR 关闭，或操作者撤销 | 生效（推送后生效） |
| MA-160 | 登记表清账 PR 的常设授权：操作者要求清账（如「清一次登记表」）时开出的 PR，只把失效条件已满足、或操作者已在对话中裁定失效的授权行的状态格改为「已失效（…）」，每行写明依据（所列 PR 的 squash SHA、线上核验结果或裁定原话）；不增删行、不改任何行的其他格、不改登记表以外的文件。每个此类 PR 须最终 head 包含最新 main、全部检查成功（含非必需项，pending 不算绿）、无 changes-requested 或未解决评审线程后，由 Claude 按本行 squash merge。本行同时覆盖 PR #1263（`docs/registry-expire-157-158`，**含本登记行**：把 MA-158 改为已失效并新增本行；MA-157 已由其窗口在 #1262 改为已失效）。**不含**：新增授权或改动授权范围（新的授权仍须操作者在对话中给出并单独登记）、为关闭单独一行而主动开 PR（仍按 MA-029 在下次触碰时顺带改）、`.github/workflows/**`、依赖、公开 CLI 或 Base schema 变更。 | 「加常设授权，等 CI 跑完你合入」2026-09-25（答复 Claude 为只改状态格、不增删行的清账 PR 设常设授权的提议；此前「清一次登记表」） | 操作者撤销 | 生效（推送后生效） |
| MA-002 | IDML 参考版式对齐（parity）线：`fix/idml-*`、`feat/idml-*` 分支，及提交题头 `fix(idml)`/`feat(idml)` 的对齐类 PR | 「授权你绿了自合」2026-07-10；2026-07-30 操作者确认仍生效 | 操作者撤销 | 生效 |
