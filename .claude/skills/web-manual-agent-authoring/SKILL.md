---
name: web-manual-agent-authoring
description: Author and batch-build governed Web manuals directly from visual assets (asset_registry.csv), shared semantic components (ComponentSpec + web_*.css), and approved multilingual corpus (TM-B + sibling ManualIR v2). Trigger phrases include Agent 开发说明书, 新建 Web 说明书, 开发网页说明书, 批量 Web 手册开发, 基于内容资产开发说明书, author a Web manual, build a new manual_sources Web package.
argument-hint: "[model] [region] [language]"
---

# Web Manual Agent Authoring (Claude Code entry)

Read and follow `.agents/skills/web-manual-agent-authoring/SKILL.md` and
`.agents/skills/web-manual-agent-authoring/references/workflow-checklist.md`.
The shared skill owns the 6-stage SOP, artwork reuse gate, `ManualIR v2`
component assembly rules, and preflight script; do not duplicate them here.

Claude Code specifics:

- Start every authoring run with the Stage 0 preflight script:

  ```sh
  python .agents/skills/web-manual-agent-authoring/scripts/authoring_preflight.py     --model <MODEL> --region <REGION> [--lang <LANG>] --json
  ```

- Keep scratch intermediates in the session scratchpad outside the repo; commit
  only governed `manual_sources/` (or `data/manual_sources/`) deliverables,
  provenance sidecars, and `data/frozen_package_registry.json` updates when
  sealing for release.
- Hand built previews (`1440px` / `390x844` screenshots or HTML bundles) to the
  operator for acceptance before sealing or updating live Feishu records.
