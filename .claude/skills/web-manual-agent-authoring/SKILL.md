---
name: web-manual-agent-authoring
description: "Prepare a governed Web package from an approved source using visual assets, shared ComponentSpec and approved TM-B. New manual drafting starts in Hello-Docs-Review."
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
