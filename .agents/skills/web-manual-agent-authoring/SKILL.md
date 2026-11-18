---
name: web-manual-agent-authoring
description: "Prepare a governed Web package from an approved source using visual assets, shared ComponentSpec and approved TM-B. New manual drafting starts in Hello-Docs-Review."
metadata:
  owner: "Web 发布维护人"
  status: "active"
  entry: "将有权威来源的批准原稿制作成 Web 源包"
  tools: "scripts/authoring_preflight.py、ManualIR v2、ComponentSpec"
  validation: "运行 tests/test_web_manual_agent_authoring_skill.py 核对预检，再按原稿核对桌面和移动预览"
  reviewed: "2026-11-17"
  retire_when: "Web 源包、共享组件或封存契约被替换"
---

# Web Manual Agent Authoring

Prepare a Web package from an approved source using shared components, verified assets and approved corpus. New writing starts in the private review workbench. The [positioning contract §5.1](../../../code-as-doc/architecture/Hello_Docs_Positioning.md#51-网页说明书的三条路线) records the approved-draft handoff status. Source-package preparation uses these assets:

- **Visual Assets**: `04_资产*` exports governed in [`data/asset_registry.csv`](../../../data/asset_registry.csv) (`✅成品` preferred).
- **Shared Presentation**: registered [`ComponentSpec`](../../../docs/renderers/contracts/component_registry.yaml) contracts and shared stylesheets under `docs/renderers/contracts/web_*.css`.
- **Multilingual Corpus**: `Approved`-only `Translation_Memory` + `Terms` (`TM-B`) and sibling Web `manual-ir/v2` packages.

**Scope boundary**:
- Use this workflow for new Agent-authored Web packages under `manual_sources/` or `data/manual_sources/`—do **not** route new Web authoring through the legacy `sync-data` + RST template auto-build path.
- Do **not** create per-model configs (`configs/config.<model>.yaml`) or custom per-package visual CSS themes.
- Detailed command recipes, the full `HB-*` component list, and CSS allow/deny rules live in [`references/workflow-checklist.md`](references/workflow-checklist.md).

## 6-Stage End-to-End SOP

### Stage 0 — Readiness & Asset Foundation Preflight

Run the deterministic preflight before writing any IR, Markdown, or CSS:

```sh
python .agents/skills/web-manual-agent-authoring/scripts/authoring_preflight.py   --model <MODEL> --region <REGION> [--lang <LANG>] --json
```

Review the JSON/Markdown output and confirm before drafting:
1. **Sibling coverage**: same-region and cross-region `manual-ir/v2` packages for structure, wording, and `publication_eligible` status.
2. **Visual asset readiness**: matched `✅成品` assets (`reusable_asset_keys`), model-specific vs shared counts, and any `待无字化 == "TRUE"` blockers in [`data/asset_registry.csv`](../../../data/asset_registry.csv).
3. **Contract inventory**: available `docs/renderers/contracts/web_*.css` stylesheets and registered `HB-*` `ComponentSpec` IDs.

- **Exit gate**: preflight JSON saved in scratchpad; missing assets or unready `待无字化` items flagged before authoring begins.

### Stage 1 — Source Intake & Artwork Reuse Gate

Follow the [Web artwork reuse order](../../../docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md) in [`STYLE_DEFINITION.md`](../../../docs/renderers/contracts/STYLE_DEFINITION.md) (`先盘点 → 核对身份 → 直接复用 → 必要时处理文字 → 最后才提取`):

1. **Shared icons/symbols first**: bind registered LCD icons, button SVGs (`button/power`, `button/ac`, `button/dc_usb`, `button/led`), and safety symbols by semantic key before considering extraction.
2. **Sibling & model `✅成品` reuse**: reuse approved assets from [`data/asset_registry.csv`](../../../data/asset_registry.csv) across languages and regions whenever hardware and UI match (keep bytes and SHA-256 unchanged).
3. **Complete panel & App frame preservation**: preserve complete product panels and App screenshot frames intact; never slice sub-icons out of a panel or recrop solely because language or source PDF page changed.
4. **Extract only on proven gap**: record reuse/gap decisions in the target review record first; invoke [`asset-textless-extraction`](../asset-textless-extraction/SKILL.md) **only** when a genuinely net-new burned-text illustration must be extracted and enrolled.

- **Exit gate**: every planned figure slot maps to an existing `asset_key` or an explicit, operator-approved extraction ticket.

### Stage 2 — Multilingual Corpus & Terminology Precheck

Harvest existing approved translations before translating net-new sentences:

1. **Live TM-B lookup (`Approved` only)**: query `Translation_Memory` and `Terms` via [`bitable-translation-memory`](../bitable-translation-memory/SKILL.md); never promote unapproved `Draft` rows directly into production copy without human review.
2. **Sibling `ManualIR v2` harvest**: extract high-confidence aligned sentences from committed sibling `manual.ir.json` bundles:

   ```sh
   python -m tools.corpus.harvest_web_ir --model <MODEL> --region <REGION>
   ```

3. **Parameter & compliance isolation**: separate model-specific numbers (wattages, voltages, capacities, ports, weights) from reusable wording patterns, and verify regional compliance notices (FCC/IC, EU directives, PSE/KC).

- **Exit gate**: terminology glossary locked, TM-B matches and harvested sibling pairs collected, and net-new sentences isolated for translation/review.

### Stage 3 — Semantic `ManualIR v2` & Shared Component Assembly

Author package content into `manual-ir/v2` (`whole-document-components/v1` for component-bound manuals; `whole-document-flow/v1` only for compatible flow replay) under `manual_sources/<MODEL>/<REGION>/...` or `data/manual_sources/<MODEL>/<REGION>/...`:

1. **Bind registered `ComponentSpec`s**: map structured manual sections to registered IDs in [`component_registry.yaml`](../../../docs/renderers/contracts/component_registry.yaml):
   - **Compositions & callouts**: `HB-SPECIAL-OVERVIEW`, `HB-SPECIAL-INBOX`, `HB-SPECIAL-OPERATION`, `HB-SPECIAL-APP`, `HB-SPECIAL-FCC`, `HB-SPECIAL-REFERENCE-FIGURE`, `HB-CALLOUT-STRIP`.
   - **Tables & warranty**: `HB-TABLE-SPEC`, `HB-TABLE-KEY-COMBINATIONS`, `HB-TABLE-LCD-ICON`, `HB-TABLE-LCD-MODE`, `HB-TABLE-AUTO-RESUME`, `HB-TABLE-TROUBLESHOOTING`, `HB-TABLE-SYMBOL-ICON`, `HB-TABLE-SYMBOL-SIGNAL`, `HB-TABLE-REFERENCE`, `HB-WARRANTY-LEAD`, `HB-WARRANTY-SECTION`, `HB-WARRANTY-YEARS`.
2. **Enforce geometry-only local CSS**: reuse shared `docs/renderers/contracts/web_*.css` for all colors, typography, spacing, and card/callout styling. Package `source_stylesheet` CSS is strictly limited to **geometry coordinates** (marker positions, callout leader anchors, overlay bounding boxes).
3. **Zero paint/inline overrides**: never add inline `style` attributes or custom paint properties (`color`, `background*`, `border*`, `fill`, `stroke*`, `box-shadow`, `outline*`, `text-shadow`, `text-decoration-color`) enforced by [`prepared_style_audit.py`](../../../tools/web/prepared_style_audit.py).
4. **Explicit table exceptions**: if an ordinary prose table fits no `HB-TABLE-*` spec, declare it in manifest `shared_component_exceptions` (`language`, `page_id`, `kind: table`, `text_sha256`, `reason`).

- **Exit gate**: `manual.ir.json` (`manual-ir/v2`) and any geometry-only `source_stylesheet` assembled without custom theme classes.

### Stage 4 — Declarative Build, Multilingual QC & Consumption Attribution

1. **Validate IR & admission gates**: run `validate_manual_ir` / `validate_document`, shared-component admission (`component_admission` / `frozen_web_component_coverage`), and `prepared_style_audit` (`require_prepared_document_styles`) on every authored locale.
2. **Build & verify output**: render MyST/HTML through the shared Web pipeline (`tools.web.document_ir` / `tools.web.frozen_ai_web.replay_package`)—never hand-edit generated HTML.
3. **Multilingual & numeric QC**: verify zero untranslated source fragments, intact placeholders/units, and matching model parameters across locales.
4. **Record separate-unit provenance**: write sidecar attribution linking consumed `asset_key`s and `tm_record_id`s per [`workspace_production_evidence.md`](../../../code-as-doc/dev/workspace_production_evidence.md). Keep visual assets, TM sentence pairs, and `ComponentSpec` bindings in separate units—never merge them into a single blended percentage.

- **Exit gate**: zero validation/admission issues, clean HTML replay, and complete sidecar provenance.

### Stage 5 — Responsive Verification & Sealed Registration

1. **Responsive viewport verification**: inspect rendered HTML at **`1440px` desktop** and **`390x844` mobile** viewports:
   - Zero horizontal page overflow (`scrollWidth <= clientWidth`).
   - Accurate callout strip marker and leader alignment over panels.
   - Intact horizontal scrolling inside wide tables (`HB-TABLE-*`) and crisp asset rendering.
2. **Freeze & register when sealing for release**: enroll newly sealed `manual_sources/` packages in [`frozen_package_registry.py`](../../../tools/web/frozen_package_registry.py) (`register` + `check`) with operator approval reference and pinned `repo_inputs` SHA-256 hashes.

- **Exit gate**: operator confirms viewport evidence and `python -m tools.web.frozen_package_registry check` exits `0`.

## Expected Package & Provenance Layout

- Target root: `manual_sources/<MODEL>/<REGION>/<version>/web/<lang>/` (or `data/manual_sources/...`), carrying `manual.ir.json` (`schema_version: "manual-ir/v2"`), `source_manifest.json` / `frozen_source_manifest.json`, bundled `assets/` with SHA-256 pins, and optional geometry-only `source_stylesheet`.
- Provenance sidecar: record consumed `asset_key` list (`data/asset_registry.csv`), consumed `tm_record_id` list (`Translation_Memory` / `Terms`), and bound `component_id`s separately—matching the [workspace evidence contract](../../../code-as-doc/dev/workspace_production_evidence.md).
- Release freeze: register each sealed package in `data/frozen_package_registry.json` via `tools.web.frozen_package_registry` rather than leaving unpinned shared dependencies.

## Guardrails & Sibling Skill Routing

- **Never bypass the reuse gate**: do not re-screenshot PDFs or slice panel sub-icons when `✅成品` or shared icons exist.
- **Never paint in local CSS**: visual tokens belong exclusively to `docs/renderers/contracts/web_*.css` and registered `ComponentSpec` adapters.
- **Never auto-promote unapproved TM**: only `Approved` TM-B rows and verified sibling `manual-ir/v2` pairs enter production packages directly.

| Need | Route to |
| --- | --- |
| Extract & enroll a missing textless illustration | [`asset-textless-extraction`](../asset-textless-extraction/SKILL.md) |
| Query or translate terms & sentences via TM-B | [`bitable-translation-memory`](../bitable-translation-memory/SKILL.md) |
| Write approved bilingual pairs back to TM-B | [`bilingual-tm-maintenance`](../bilingual-tm-maintenance/SKILL.md) |
| Dispatch or triage Hello-Docs publish CI | [`hello-docs-pipeline-dispatch-triage`](../hello-docs-pipeline-dispatch-triage/SKILL.md) |
