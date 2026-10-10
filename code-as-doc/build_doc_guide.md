# Windows Build Guide

Updated: 2026-08-17

This file is the maintainer-facing Windows and PowerShell build guide.
The current cross-platform entrypoint is [`build.py`](../build.py).
For the fixed four-language release pack, use [`../scripts/build_us_jp_manuals.ps1`](../scripts/build_us_jp_manuals.ps1) or [`../scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py).

## How to use this guide

This page is an index. Open only the topic page your task needs; each page is
small enough to read whole. When behavior changes, update the owning topic page
(and this table if a page is added or renamed) instead of adding notes here.

| Topic page | Read it when |
| --- | --- |
| [`commands.md`](build_doc_guide/commands.md) | you need what a `build.py` action or flag does, typical command lines, or the diff report |
| [`config-and-manifests.md`](build_doc_guide/config-and-manifests.md) | you pick or change a config family, page manifest or skeleton, the mirror sync setup, or a phase2 snapshot rule |
| [`windows-flow.md`](build_doc_guide/windows-flow.md) | you run validate → runtime draft → review → refresh → build from review on Windows/PowerShell |
| [`review-preview-and-release.md`](build_doc_guide/review-preview-and-release.md) | you package a review preview for design, publish a final Word release, or need the output directory layout |
| [`data-sync-and-intake.md`](build_doc_guide/data-sync-and-intake.md) | you work on `sync-data`, source-table bindings, `spec-master-rebuild`, source intake, or translation-memory lookups |
| [`backport.md`](build_doc_guide/backport.md) | you back-port reviewer edits from a Feishu cloud doc with `python -m tools.backport.cloud_doc` |
| [`assets.md`](build_doc_guide/assets.md) | you work on the image-asset registry, `asset-check`, `asset-intake`, reviewed promotion or `asset:` references |
| [`queues.md`](build_doc_guide/queues.md) | you touch Start Review / Build Draft Package / Publish rows, queue workers, release staging or the Feishu workflows |
| [`integrations.md`](build_doc_guide/integrations.md) | you work on OpenClaw/BlockClaw dispatch, the Feishu IM adapter, DingTalk helpers or the Wukong MCP bridge |
| [`ci-and-guardrails.md`](build_doc_guide/ci-and-guardrails.md) | you change `Manual Validation`, a ratchet or guardrail, or the branch-safety tooling |
| [`quality-gates.md`](build_doc_guide/quality-gates.md) | `check` reports terminology, capability, language-parity or language-scope findings |
| [`troubleshooting.md`](build_doc_guide/troubleshooting.md) | a build fails with a known message, or you want the list of common mistakes |
| [`idml-reference-layouts.md`](build_doc_guide/idml-reference-layouts.md) | you work on the production IDML path, approved reference-layout plans or component targets |
| [`idml-finalize-and-parity.md`](build_doc_guide/idml-finalize-and-parity.md) | you run IDML flow mode, InDesign finalize, PDF parity, or work on IDML handoff and fallback chains |
| [`web-publish-and-rtd.md`](build_doc_guide/web-publish-and-rtd.md) | you work on Web Publish, frozen sources and receipts, Read the Docs, or the portal and workspace pages |
| [`web-rendering.md`](build_doc_guide/web-rendering.md) | you change the Web profile export, MyST/HTML rendering, CSS, tables, callouts or the plain-Markdown preview |
| [`web-public-ir.md`](build_doc_guide/web-public-ir.md) | you change a Web component that consumes public ManualIR (specs, LCD, troubleshooting, callouts, FCC, App) |
| [`web-illustrations.md`](build_doc_guide/web-illustrations.md) | you select, crop or bind Web artwork: reuse order, illustration manifests, PDF regions, composites |
| [`web-component-admission.md`](build_doc_guide/web-component-admission.md) | you admit prepared or native Web components for EU/UK targets, or preserve source-authored layouts |
| [`web-target-notes.md`](build_doc_guide/web-target-notes.md) | you work on a Web target listed there (JE-100C/EU, FridgeGuard US, SlimPower H1, JBP-1000B-WH, JA-AD500A-SIL …) |

For user-facing review workflow details, read:

- [`user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
- [`user-guide/quick_start_guide.md`](../user-guide/quick_start_guide.md)

For onboarding new external Markdown manuals into the template library, use:

- [`dev/manual_template_intake_checklist.md`](./dev/manual_template_intake_checklist.md)
- [`.agents/skills/markdown-rst-template-intake/SKILL.md`](../.agents/skills/markdown-rst-template-intake/SKILL.md) for the repo-local Codex workflow that maps Markdown manuals into the current RST template and recipe layout
- [`.agents/skills/manual-rewrite-with-tm/SKILL.md`](../.agents/skills/manual-rewrite-with-tm/SKILL.md) for TM-first structured Markdown/manual rewrite that preserves layout and highlights unmatched source text

For planned publication-outlet consolidation and medium/long-term ownership, see
the [manual revitalization plan](manual_production_revitalization_plan.md).
Use the [hosting convergence review](dev/web_publish_pipeline.md#31-hosting-convergence-and-legacy-entry-review)
for old/new URL and version mapping, release-site evidence and recovery checks.
These are planning/manual acceptance requirements; no new command, automated
gate, hosting change or online write is introduced by the documentation update.
