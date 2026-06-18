# Architecture Documentation Map

Updated: 2026-06-07

Use this directory for architecture and integration boundaries.
Not every file here is equally current.

## 1. Active Architecture Docs

- [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md)
  - long-term strategy and stable architectural principles
- [`Hello_Docs_Architecture.md`](Hello_Docs_Architecture.md)
  - current repository component map and ownership split
- [`OpenClaw_Control_Layer_Plan.md`](OpenClaw_Control_Layer_Plan.md)
  - active OpenClaw control-layer architecture and current repo status
- [`Feishu_Source_DingTalk_Sink_Plan.md`](Feishu_Source_DingTalk_Sink_Plan.md)
  - active DingTalk artifact-sink plan while Feishu remains the source and queue system
- [`Content_Data_Model.md`](Content_Data_Model.md)
  - future canonical content-model direction
- [`Long_Form_Content_Block_Design.md`](Long_Form_Content_Block_Design.md)
  - re-launch design for prose page assembly (long-form block schema + block-level review workflow); backs Workstream N
- [`closed_loop_qc_agent_requirements.md`](closed_loop_qc_agent_requirements.md)
  - requirements baseline for the closed-loop QC agent that combines content-lint rules, reviewer diff Word back-porting, and Feishu QC marking
- [`Feishu_Cloud_Doc_Backport_Design.md`](Feishu_Cloud_Doc_Backport_Design.md)
  - source-of-truth routing design for Feishu cloud document backport flows: in-review final docs and template maintenance docs
- [`HTML_PDF_Component_Convergence.md`](HTML_PDF_Component_Convergence.md)
  - output-convergence notes for current rendering work
- [`MyST_Markdown_Feishu_Cloud_Doc_Publish_Plan.md`](MyST_Markdown_Feishu_Cloud_Doc_Publish_Plan.md)
  - target architecture for MyST Markdown publish output, Read the Docs hosting, and Feishu cloud document import

## 2. Archived Or Superseded Plans

These files are kept only for implementation history and earlier design context.

- [`Feishu_Message_OpenClaw_Control_Plan.md`](Feishu_Message_OpenClaw_Control_Plan.md)
  - superseded by the consolidated OpenClaw plan and current repo docs
- [`OpenClaw_Phase2_Natural_Language_Plan.md`](OpenClaw_Phase2_Natural_Language_Plan.md)
  - superseded by the consolidated OpenClaw plan and current implementation
- [`DingTalk_Build_Writeback_Plan.md`](DingTalk_Build_Writeback_Plan.md)
  - broader provider-migration plan kept as background only
- [`DingTalk_Phase0_Spike_Checklist.md`](DingTalk_Phase0_Spike_Checklist.md)
  - archived spike checklist for the earlier DingTalk investigation

## 3. Rule

- Prefer one active document per active architecture topic.
- Do not revive archived plans as if they were current requirements.
- If an active architecture boundary changes, update this map in the same PR.
