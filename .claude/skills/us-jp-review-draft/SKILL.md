---
description: Produce or continue a JP (日规) review draft (审核稿/审阅稿) from the published US English manual — US structure as master, reuse existing Japanese corpus (whole sentences or halves), mark the rest as green new translation and count it, fill JP spec-sheet and R&D values in purple, audit US↔JP coverage, apply the JP web-manual style, deliver a versioned zip (optionally to the Feishu wiki).
when_to_use: Trigger phrases include 基于美规输出日规说明书, 日规审核稿, 日规审阅稿, 继续改日规草稿 (Feishu wiki zip), 需新增翻译量, 日规和美规内容是否对应, 按日规说明书样式调整, 研发答复回填. US→JP only.
argument-hint: "[US RTD url] [Feishu wiki link of the draft]"
---

# US → JP Review Draft (Claude Code entry)

The procedure, rules and scripts live in the shared skill — read and follow
`.agents/skills/us-jp-review-draft/SKILL.md` and the reference files it names.
Do not duplicate them here.

Claude Code specifics:

- Run the per-chapter US↔JP alignment (`references/alignment-audit.md`) with the
  Agent tool, several groups in parallel in the background, each briefed with
  only its group files and the rubric.
- Hand drafts, xlsx and previews to the operator with SendUserFile; upload to the
  Feishu wiki only when the operator asks in this conversation.
- Keep scratch work (downloads, version directories, screenshots) in the session
  scratchpad, not in the repository.
