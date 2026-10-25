---
description: Produce or continue a reference-based manual review draft (审核稿); currently US→US English and US→JP Japanese modes. Reuse the reference structure and wording, fill target-spec parameters, keep suggestions and uncertainty in review notes, and deliver a versioned local package.
when_to_use: Trigger phrases include 审核稿, 出审核稿, review draft, 美规英文审核稿, 参考稿复用, US-US, US-JP, 基于美规输出日规说明书, 日规审核稿, 规格回填, 统计新增翻译量, 参考与目标内容对照, 改审核稿, 继续修改审核稿, 私有审核仓库.
argument-hint: "[reference manual] [target spec sheet] [existing draft, if any]"
---

# Manual Review Draft (Claude Code entry)

Read and follow `.agents/skills/manual-review-draft/SKILL.md`, then only the
mode-specific reference it selects. The shared skill owns the procedure,
evidence rules and scripts; do not duplicate them here.

Claude Code specifics:

- In US→JP mode, run the per-chapter alignment described in the shared
  `references/alignment-audit.md` with the Agent tool when that audit is needed.
  Keep each group scoped to its input files and rubric. Do not run JP-specific
  translation counts on a US→US English draft.
- Hand drafts, xlsx and previews to the operator with SendUserFile. Feishu
  upload and private review-site publication require the user's request and
  follow the shared skill's read-back and publication rules; a requested change
  to a draft that lives in Hello-Docs-Review is that request.
- In a cloud session, attach `Bingboom/Hello-Docs-Review` with `add_repo`
  (push access) before the sparse clone the shared skill describes. A drafting
  session needs only read access to auto-manual and Hello-Docs: attach them
  read-only and never push draft content to either public repository.
- Follow the shared skill's 并行写稿与隔离 rules: one writer per draft line,
  `git pull --rebase` on a rejected push, never force-push, and record
  `tools_sha` in `draft.json`.
- Keep the line's issue register and decisions file current each round
  (shared `references/review-records.md`). After pushing, sync the Feishu row
  from an auto-manual checkout. In a cloud session configure lark-cli once from
  the environment's app credentials, then run the sync (dry run first):

  ```sh
  printf %s "$FEISHU_APP_SECRET" | lark-cli config init --app-id "$FEISHU_APP_ID" --app-secret-stdin --brand feishu
  python -m tools.rtd.review_table_sync <clone>/docs/review-drafts --line <MODEL>/<REGION>
  python -m tools.rtd.review_table_sync <clone>/docs/review-drafts --line <MODEL>/<REGION> --write
  ```

  Report the read-back lines (`record_id field=value`) to the operator.
- Keep generated drafts and scratch work in the session scratchpad, outside
  auto-manual; only the working draft goes into Hello-Docs-Review's
  `docs/review-drafts/`.
