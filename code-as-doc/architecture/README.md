# Architecture Documentation Map

Updated: 2026-08-11

Use this directory for architecture and integration boundaries.
Not every file here is equally current.

## 1. Active Architecture Docs

- [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md)
  - long-term strategy and stable architectural principles
- [`system_evolution_history.md`](system_evolution_history.md)
  - retrospective narrative of how the system actually evolved (kernel + ten
    rings, dated); the backward-looking counterpart of the Strategy doc
- [`Hello_Docs_Architecture.md`](Hello_Docs_Architecture.md)
  - current repository component map and ownership split
- [`Product_Data_Base_Architecture.md`](Product_Data_Base_Architecture.md)
  - current business architecture for product, market-version, material-demand,
    manual-task, and change governance in the upstream Product Data Base
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
- [`Review_Branch_Propagation_Design.md`](Review_Branch_Propagation_Design.md)
  - approved K15/Workstream V forward-propagation contract for pinned review derivatives, classify-or-abstain bump PRs, migration, and lag measurement; bounded implementation slices are now registered
- [`HTML_PDF_Component_Convergence.md`](HTML_PDF_Component_Convergence.md)
  - stable cross-renderer ownership boundary only; the sole human style
    specification is
    [`STYLE_DEFINITION.md`](../../docs/renderers/contracts/STYLE_DEFINITION.md),
    and active migration evidence lives in
    [`style_component_contract_v2_plan.md`](../dev/style_component_contract_v2_plan.md)
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
