# Architecture Documentation Map

Updated: 2026-06-06

Use this directory for architecture and integration boundaries.
Not every file here is equally current.

## 1. Active Architecture Docs

- [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md)
  - long-term strategy and stable architectural principles
- [`Hello_Docs_Architecture.md`](Hello_Docs_Architecture.md)
  - current repository component map and ownership split
- [`Control_Orchestration_Strategy.md`](Control_Orchestration_Strategy.md)
  - current control/orchestration strategy for OpenClaw, Feishu IM, deferred manual agents, queue commands, and GitHub workers
- [`Feishu_Source_DingTalk_Sink_Plan.md`](Feishu_Source_DingTalk_Sink_Plan.md)
  - active DingTalk artifact-sink plan while Feishu remains the source and queue system
- [`Content_Data_Model.md`](Content_Data_Model.md)
  - future canonical content-model direction
- [`Output_Publishing_Strategy.md`](Output_Publishing_Strategy.md)
  - current output and publishing strategy for HTML, Word, PDF, Markdown, RTD, and Feishu cloud docs

## 2. Archive

These files are kept only for implementation history and earlier design context.
They live under [`archive/`](archive/) so the top-level architecture directory
stays focused on current boundaries.

- [`archive/Feishu_Message_OpenClaw_Control_Plan.md`](archive/Feishu_Message_OpenClaw_Control_Plan.md)
  - superseded by the consolidated OpenClaw plan and current repo docs
- [`archive/OpenClaw_Phase2_Natural_Language_Plan.md`](archive/OpenClaw_Phase2_Natural_Language_Plan.md)
  - superseded by the consolidated OpenClaw plan and current implementation
- [`archive/OpenClaw_Control_Layer_Plan.md`](archive/OpenClaw_Control_Layer_Plan.md)
  - detailed OpenClaw control-layer plan replaced by the consolidated control/orchestration strategy
- [`archive/Manual_Agent_Orchestration_Strategy.md`](archive/Manual_Agent_Orchestration_Strategy.md)
  - detailed Manual Agent strategy replaced by the consolidated control/orchestration strategy
- [`archive/DingTalk_Build_Writeback_Plan.md`](archive/DingTalk_Build_Writeback_Plan.md)
  - broader provider-migration plan kept as background only
- [`archive/DingTalk_Phase0_Spike_Checklist.md`](archive/DingTalk_Phase0_Spike_Checklist.md)
  - archived spike checklist for the earlier DingTalk investigation
- [`archive/HTML_PDF_Component_Convergence.md`](archive/HTML_PDF_Component_Convergence.md)
  - replaced by the consolidated output publishing strategy
- [`archive/MyST_Markdown_Feishu_Cloud_Doc_Publish_Plan.md`](archive/MyST_Markdown_Feishu_Cloud_Doc_Publish_Plan.md)
  - replaced by the consolidated output publishing strategy

## 3. Rule

- Prefer one active document per active architecture topic.
- Do not revive archived plans as if they were current requirements.
- If an active architecture boundary changes, update this map in the same PR.
