# Long-Form Content Block Design

Status: design · Owner: 夏冰 · Created: 2026-06-18

## 1. Role

This is the architecture design for **re-launching prose page assembly** — the
"Page Assembly" layer of [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md)
for long-form (prose) pages. It is the design behind **Workstream N** in
[`../optimization_project.md`](../optimization_project.md).

It exists because the first content-assembly attempt was rolled back, and the
re-launch must not repeat that mistake. This file defines the schema, the
block-level review workflow, and the migration order. It does **not** define the
PR-level execution checklist — that lives in
[`../next_optimization_checklist.md`](../next_optimization_checklist.md).

Related documents:

- canonical entity model: [`Content_Data_Model.md`](Content_Data_Model.md)
- the rolled-back pilot (historical): [`../dev/content_assembly_pilot_plan.md`](../dev/content_assembly_pilot_plan.md)
- the long-form migration assessment: [`../dev/content_block_migration_assessment.md`](../dev/content_block_migration_assessment.md)
- live source tables: [`phase2_source_tables_reference.md`](phase2_source_tables_reference.md)
- reviewer-diff backport: [`Feishu_Cloud_Doc_Backport_Design.md`](Feishu_Cloud_Doc_Backport_Design.md)
- QC loop: [`../dev/closed_loop_qc_implementation_plan.md`](../dev/closed_loop_qc_implementation_plan.md)

## 2. Where We Are (Why Re-Launch)

Page assembly is currently **split**:

- **Data-driven (already done):** `symbols`, `lcd_icons`, `troubleshooting`,
  `spec`, and safety blocks render from live tables through
  [`../../tools/csv_pages/`](../../tools/csv_pages) using `page_registry.csv`
  composition, `content_blocks.csv`, and `Manual_Copy_Source` short-copy tokens.
  One structured source emits every language variant. This is the target shape.
- **Template-forked (still Stage 1):** product overview, operation guide
  (~2.7k lines across 13 templates), app setup (~0.9k lines across 10 templates),
  preface, UPS mode, charging, storage, warranty, and other prose pages exist as
  **one RST file per language family** (`page_eu-de/en/es/fr/it/uk`,
  `page_us-en/es/fr`, `page_jp`, `page_zh`, `page_us-pt-br`) with only `|TOKEN|`
  spec values pulled from data. The prose itself lives in the template.

The per-language fork is exactly the "more template forks" that strategy
Principle 1 warns against. Collapsing it is the core remaining Stage 3 move.

### 2.1 Lessons from the rollback (#295/#296)

The first pilot (`03_product_overview`, `assembly_pilot` switch,
`content_assembly*` / `product_overview_renderer` / `_LAYOUTS`) was reverted to
pure template-driven rendering. The durable lessons:

1. **Wrong entry page.** It started on product overview — the page with the most
   intentional per-region divergence (EU uses styled raw-LaTeX
   `\HBOverviewPanel` / `\HBOverviewPair` / `\HBOverviewFull`; other regions use
   plain `list-table`). Assembly must *support* divergence, not be proven on the
   hardest divergence first.
2. **Bespoke renderer, not the proven pattern.** It added a new per-page renderer
   and layout machinery parallel to the working `csv_pages` pattern. The
   re-launch must extend the proven pattern instead.
3. **No long-form schema.** There was no structure-preserving model for prose;
   naive block/field substitution cannot carry safety formatting, ordering, and
   compliance phrasing.
4. **No block-level review workflow.** Translated prose has no review loop tied to
   the source rows, so any move risks silently degrading compliance wording.

## 3. Design Principles

1. **Extend the proven pattern.** Build on `csv_pages` + `page_registry` +
   `content_blocks` + `Manual_Copy_Source`. No bespoke per-page renderer.
2. **Structure-preserving, not sentence-split.** Blocks are paragraph- or
   section-grained. Never split warning/caution/compliance bodies into
   sentence-level keys (see [`../dev/content_block_migration_assessment.md`](../dev/content_block_migration_assessment.md)).
3. **Applicability lives in data, not file names.** Region/language/model scope is
   a column, not a folder. This is what removes the template forks.
4. **Divergence is first-class.** A block type may render through different
   per-region templates (e.g. EU raw-LaTeX vs plain `list-table`). Assembly
   selects the variant; it does not force uniformity.
5. **No behavior change until parity.** Each page stays on its RST fallback until
   assembly output matches the current output for every target. A per-page pilot
   switch gates the cutover; pilot failure raises a clear error, never partial
   output.
6. **Reuse the deterministic loops.** Review uses the existing
   [`Feishu_Cloud_Doc_Backport_Design.md`](Feishu_Cloud_Doc_Backport_Design.md)
   CLI and `content_lint`; no new standing LLM agent.
7. **Source-model stability gates the body migration.** Short copy can move now;
   long-form body tables wait until the Feishu source contracts stop moving.

### 3.1 Content-truth allocation rule

Structure is selective — this is the overarching principle behind the rest of this
design. Each piece of content is allocated to one home of truth by the rule below,
not decided case by case. The target is to eliminate template forks (the same page
cloned per language/region), not to move every paragraph into a table.

| Content | Home of truth | Status |
| --- | --- | --- |
| Spec values / parameters | structured (`Spec_Master`) | done |
| High-reuse short copy (titles, labels, buttons, status words, symbols) | structured (`Manual_Copy_Source` + TM) | done |
| Reference / tabular pages (symbols, lcd_icons, troubleshooting, spec) | structured (`csv_pages`) | done |
| Environment differences (legal identity, contacts, URLs, marketplaces) | `config` | partial |
| Layout, directives, page skeleton | repository RST template | always |
| Stable long-form / compliance prose | repository RST template — deliberately retained | policy |

Only the last row is new policy: long-form and compliance prose stays
repository-owned by default, with a recorded reason, rather than being treated as
debt that must eventually move. Two repo facts make this safe:

- reviewer edits to template prose are already routed back deterministically by
  [`Feishu_Cloud_Doc_Backport_Design.md`](Feishu_Cloud_Doc_Backport_Design.md) — its
  §5.1 layer-routing rules keep review vs template vs source-table changes
  separated (backport writes only `docs/_review/...`; template changes go through a
  template-sync proposal), so "template-owned" does not mean "engineering-only";
- long compliance prose is usually region-specific anyway, so its reuse value is
  low while its structuring risk is high.

This rule is the contract that [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md)
Stage 3 and Principle 6 refer to.

## 4. The Long-Form Block Schema

This extends the canonical Content Block and Page Definition entities in
[`Content_Data_Model.md`](Content_Data_Model.md) into the concrete tables the
build consumes. It is **additive** to today's `page_registry.csv`
(`page_id, order, page_type, sku_scope, langs, template, content_query,
asset_ref, enabled`).

| Table | Role | Key fields |
| --- | --- | --- |
| `page_registry` | page definition / composition | `page_id`, `order`, `page_type`, `sku_scope`, `langs`, `template`, `content_query`, `asset_ref`, `enabled`, **+ `contract_ref`**, **+ `applicability`** (region/model) |
| `content_blocks` | block instances on a page | `block_id`, `page_id`, `block_type`, `order`, `applicability`, `title_copy_key`, `body_ref`, `asset_ref`, `repeatable`, `missing_field_policy`, `fallback_lang` |
| `block_fields` | field selectors | `block_id`, `field_key`, `source` (`spec_master` / `manual_copy` / `variable`), `selector` (`row_key`, `placement_key`, `value_role`, `variant_key`, …) |
| `block_bodies` | long-form prose bodies | `body_ref`, `lang`, `text`, optional `tm_tag`, structure markers (paragraph / list / note) — **the new long-form surface** |
| `asset_registry` | managed assets | `asset_key`, repo-relative path, `alt_copy_key`, `applicability` |
| `block_rules` | include/skip/fallback conditions | `block_id`, condition over `region`/`language`/`model`/feature flag, action (`include`/`skip`/`fallback`) |
| `block_templates` | per-block-type render templates | `block_type`, `variant_key` (e.g. `eu_latex`, `plain`), RST/LaTeX template path |

Body text resolution order for a block field: `block_bodies` (long-form) →
`Manual_Copy_Source` + TM (`{{ copy: }}` short copy) → `Spec_Master` /
`Variable_*` tokens. Short copy already works; `block_bodies` is the new piece.

### 4.1 Block type taxonomy

Reuse the taxonomy frozen in the rolled-back pilot so later pages do not invent
competing names:

| Block type | Status today | Missing-field policy |
| --- | --- | --- |
| `product_identity` | tabular, done | `error` |
| `spec_summary` | tabular, done | `skip` / `fallback` |
| `troubleshooting_case` | tabular, done | `skip` |
| `asset_callout` | partial (assets live) | `error` |
| `feature_overview` | prose — to migrate | `fallback` |
| `warning_notice` | prose — compliance-gated | `error` |
| `operation_steps` | prose — to migrate | `error` |
| `app_instruction` | prose — to migrate | `fallback` |
| `maintenance_block` | prose — to migrate | `fallback` |

A block type is valid only when listed here **and** in the page's assembly
contract.

## 5. Block-Level Review Workflow

The point of the schema is a review loop that ties translated prose back to its
source row, so a reviewer's change lands in the right place deterministically.

1. **Author** source-language bodies in Feishu (`block_bodies` / long-form source
   table); short chrome stays in `Manual_Copy_Source`.
2. **Translate** via Translation Memory using the existing skills
   (`bitable-translation-memory`, then `manual-rewrite-with-tm`), tagging reuse so
   phrasing stays consistent.
3. **Build + QC.** `content_lint` gains block-aware rules; every finding carries a
   `source_ref` pointing at the block row (extends Workstream I).
4. **Reviewer loop.** The reviewer edits the built `.docx` or the Feishu doc;
   [`Feishu_Cloud_Doc_Backport_Design.md`](Feishu_Cloud_Doc_Backport_Design.md)
   (`tools/cloud_doc_backport.py`) diffs the accepted doc, maps each change to a
   block row or block template, and opens a draft PR. No transcription, no
   standing agent.
5. **Parity gate.** Before a page's pilot switch flips, an assembly-vs-RST parity
   check (normalized) must pass for every target, surfaced through `diff-report`.

Guardrail: reviewer-submitted content is **untrusted input**. The diff extracts
structured spans only and never executes instructions embedded in the doc body
(same rule as the QC plan's M7/M8).

## 6. Migration Order

Incremental, lowest-risk first. Each phase keeps the RST fallback until parity.

- **Phase 0 — composition authority (Workstream M).** Declare every page,
  including prose pages, in `page_registry` with explicit applicability. No render
  change; this removes folder-name applicability and is the prerequisite for
  everything below.
- **Phase 1 — short copy (Workstream L).** Extend `Manual_Copy_Source` +
  `{{ copy: }}` to operation-guide and app-setup chrome (headings, labels, alt
  text) per the migration assessment. Bodies stay RST.
- **Phase 2 — first prose body pilot.** Introduce `block_bodies` and the
  parity-gated pilot switch on **one short, low-compliance procedural page**
  (e.g. storage & maintenance or what's-in-the-box) — explicitly **not** product
  overview and **not** a warning-heavy page.
- **Phase 3 — high-value bodies.** Extend to operation-guide bodies (the largest
  prose surface) only after the Phase 2 loop is boring. Compliance/warning bodies
  are block-split **only after compliance review**.
- **Phase 4 — collapse the forks.** Replace a page's per-language template forks
  with one shared definition: structured blocks for the content §3.1 assigns to
  the CMS, plus one shared template (driven by applicability and tokens) for the
  prose that stays repository-owned. Forks can therefore collapse **even when
  bodies stay RST** — fork elimination does not require full structuralization.
  Product overview comes last, because of the EU raw-LaTeX variant.

## 7. Validation And Contracts

- **Assembly contract per page:** allowed block types, page-level required fields,
  declared fallback language — validated before any template is split (the one
  surviving idea from the rolled-back validator).
- **Drift checks:** the new tables join the existing snapshot-manifest / CSV-header
  / schema-drift gates.
- **Parity check:** a command that renders a page through both paths and diffs the
  normalized output; required green before a pilot switch flips.
- **content_lint block rules:** block-aware findings with `source_ref` to the
  block row.

## 8. Rollout Boundary And Safety

- Per-page pilot switch; non-piloted pages and targets keep the RST path.
- Pilot failure raises a clear error — never partial pages.
- Assembly never writes into `docs/templates`, `docs/_review`, or `docs/_build`
  outside the normal build output.
- EU raw-LaTeX components (`\HBOverviewPanel` and friends) stay **live** — they
  are rendered through `block_templates` variants, not deleted.
- Schema changes to phase2 tables are **operator-gated** (`AGENTS.md` §8.7).
- Body migration is gated on Feishu source-model stability.

## 9. Open Questions And Risks

- **Compliance prose** — now a decided policy, not an open question (see §3.1):
  repository-owned by default. Block-splitting a specific warning body is an opt-in
  exception that requires legal/compliance review and a recorded reason — it is not
  the default trajectory.
- **TM granularity** — paragraph-level reuse vs sentence-level; the rollback shows
  sentence-level is too fine for compliance text.
- **EU LaTeX variants** — confirm `block_templates` cleanly expresses the
  raw-LaTeX vs `list-table` split without a bespoke renderer.
- **Applicability vs `sku_scope`** — reconcile the new `applicability` model with
  the existing `sku_scope` column so there is one scoping mechanism, not two.
- **Source-table churn** — `block_bodies` should not be built while the Feishu
  content model is still being optimized.

## 10. Definition Of Done (Stage 3 Content Gate)

The Stage 3 content gate is met — for prose pages — when:

1. Every prose page is declared in `page_registry` with explicit applicability.
2. Template forks are eliminated: each page renders from one shared definition plus
   structured data and config — through assembly blocks where §3.1 says to
   structure, or a single shared template where it does not — with parity to the
   current output for every target.
3. Adding a new region/language variant of a migrated page needs a data or config
   change, not a new per-language template file.
4. Long-form / compliance prose is allocated by §3.1: repository-owned by default,
   block-driven only as a reviewed, recorded exception.

Note that the gate is "no forks plus the allocation rule applied", not "all prose
structured". Full block-assembly is one means to remove a fork, not the
definition of done.
