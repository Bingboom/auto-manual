# Hello Auto Doc

Updated: 2026-09-20

### Where to look next

For the current JP / US family difference boundary, use [`../code-as-doc/manual_family_guide.md`](../code-as-doc/manual_family_guide.md).
For the complete IR → Web build/replay acceptance target, including JBP-2000B
Japanese PDF illustrations, see [`ir_document_closeout.md`](../code-as-doc/dev/ir_document_closeout.md).
For onboarding new external Markdown manuals into templates, use [`../code-as-doc/dev/manual_template_intake_checklist.md`](../code-as-doc/dev/manual_template_intake_checklist.md).
For Codex-assisted Markdown-to-template intake, use [`../.agents/skills/markdown-rst-template-intake/SKILL.md`](../.agents/skills/markdown-rst-template-intake/SKILL.md).
For Codex-assisted TM-first manual rewrite or translation that must preserve Markdown structure, use [`../.agents/skills/manual-rewrite-with-tm/SKILL.md`](../.agents/skills/manual-rewrite-with-tm/SKILL.md).

---

## How to use this guide

This page is an index. Open only the topic page your task needs; each page is
small enough to read whole. When a workflow changes, update the owning topic page
(and this table if a page is added or renamed) instead of adding notes here.

| Topic page | Read it when |
| --- | --- |
| [`web-publication.md`](hello_auto-doc/web-publication.md) | you publish or maintain Web manuals: artwork reuse, single-language identity, candidates, withdrawal, language projection, health, metadata |
| [`environment-setup.md`](hello_auto-doc/environment-setup.md) | you set up Python, the lock-pinned environment, LaTeX/pandoc or local fonts |
| [`integrations.md`](hello_auto-doc/integrations.md) | you use or change BlockClaw/OpenClaw dispatch and queries, the Feishu IM adapter, DingTalk lookups or the Wukong bridge |
| [`idml-and-indesign.md`](hello_auto-doc/idml-and-indesign.md) | you build or hand off IDML/INDD, finalize in InDesign, or work on approved reference-layout targets |
| [`ci-and-checks.md`](hello_auto-doc/ci-and-checks.md) | you need what `Manual Validation`, the guardrails and `check` gates enforce, or the branch hygiene rules |
| [`source-of-truth.md`](hello_auto-doc/source-of-truth.md) | you decide which layer to edit (templates, data, `_review`, `_build`), or need the bundle layout and Git tracking rules |
| [`data-layer.md`](hello_auto-doc/data-layer.md) | you work with the phase2 snapshot, source tables, `sync-data`, CI fixtures, spec intake or translation memory |
| [`spec-safety-and-placeholders.md`](hello_auto-doc/spec-safety-and-placeholders.md) | you edit spec/footnote/symbols CSV rules, safety or spec pages, or placeholder resolution |
| [`queues-and-delivery.md`](hello_auto-doc/queues-and-delivery.md) | you run or debug Start Review / Build Draft Package / Publish rows, queue workers, DingTalk delivery or artifacts |
| [`build-pipeline.md`](hello_auto-doc/build-pipeline.md) | you need the end-to-end `build.py` pipeline steps and the important behavior notes for each action |
| [`build-commands.md`](hello_auto-doc/build-commands.md) | you need copy-paste commands, config scope, source modes, or `publish`/`preview`/`fast`/`sync-review` behavior |
| [`web-publish-and-rtd.md`](hello_auto-doc/web-publish-and-rtd.md) | you work on the RTD catalog, Web composites, per-target Web configs, Manual Center search or the knowledge pages |
| [`web-rendering-and-ir.md`](hello_auto-doc/web-rendering-and-ir.md) | you change how Web components render through public IR (Inbox, FCC, LCD, troubleshooting, warranty, callouts, tables) |
| [`version-tracking.md`](hello_auto-doc/version-tracking.md) | you set up diff baselines, compare commits, or read the diff reports |
| [`checklists-and-pitfalls.md`](hello_auto-doc/checklists-and-pitfalls.md) | you need page contracts, common pitfalls, the verification checklist or the one-sentence rule |
| [`eu-web-components.md`](hello_auto-doc/eu-web-components.md) | you add an EU language or maintain shared Web components (LCD, tables, notices, errata) without regressions |
| [`web-target-notes.md`](hello_auto-doc/web-target-notes.md) | you work on a Web target listed there (JBP-3600A, JBP-2000B, FridgeGuard US, JA-AD600A, SlimPower H1, JBP-1000B-WH, JA-AD500A-SIL …) |
