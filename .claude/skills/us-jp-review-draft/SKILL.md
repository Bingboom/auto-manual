---
description: Produce or continue a reference-based review draft in US→US English or US→JP Japanese mode. Reuse the reference structure and wording, fill target-spec parameters, keep suggestions and uncertainty in review notes, and deliver a versioned local package.
when_to_use: Trigger phrases include 美规英文审核稿, 参考稿复用, US-US, US-JP, 基于美规输出日规说明书, 日规审核稿, 规格回填, 统计新增翻译量, 参考与目标内容对照.
argument-hint: "[reference manual] [target spec sheet] [existing draft, if any]"
---

# US → US / US → JP Review Draft (Claude Code entry)

Read and follow `.agents/skills/us-jp-review-draft/SKILL.md`, then only the
mode-specific reference it selects. The shared skill owns the procedure,
evidence rules and scripts; do not duplicate them here.

Claude Code specifics:

- In US→JP mode, run the per-chapter alignment described in the shared
  `references/alignment-audit.md` with the Agent tool when that audit is needed.
  Keep each group scoped to its input files and rubric. Do not run JP-specific
  translation counts on a US→US English draft.
- Hand drafts, xlsx and previews to the operator with SendUserFile. Feishu
  upload and private review-site publication require the user's request and
  follow the shared skill's read-back and publication rules.
- Keep generated drafts and scratch work outside the engineering repository.
