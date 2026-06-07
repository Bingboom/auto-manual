# Requirements: Closed-Loop QC Agent (闭环质检 Agent)

Status: **requirements draft** · Owner: 夏冰 · Drafted: 2026-06-07
Scope of this file: *what* the agent must do and *why*. Implementation design is a
follow-up (a separate proposal once these requirements are agreed).

## 0. One-liner

A dedicated agent that **closes the manual-quality loop**: it builds the manual,
checks the result against **two QC bases** — the codified content rules and a
human-submitted *built-vs-desired* review diff (a Word comparison doc **or** a
revised Feishu cloud doc) — back-ports the gaps to the **source
of truth**, re-verifies, and **marks QC status directly in Feishu**. Quality is
caught and fixed at source, continuously, instead of by eye at release.

## 1. Background & motivation

The manual is produced from Feishu source tables + Translation Memory + per-language
templates (data model: [`phase2_source_tables_reference.md`](phase2_source_tables_reference.md)).
Historically, content defects were found **late and by eye** on the built `.docx`
(2026-06-07 examples: LCD status words not bold; an Italian line still reading `On:`).

Two complementary quality signals already exist, but are run ad-hoc by a human:

- **Codified rules** — `tools/content_lint.py` (PR #335): automated, proactive, but
  only covers what has been turned into a rule.
- **Human reviewer diff** — a *built-vs-desired* comparison the reviewer expresses
  **either** as a **Word** doc (tracked-changes / 对比稿; 夏冰 has sent three rounds of
  these for JE-2000F EU) **or** by revising a **Feishu cloud doc** directly. Catches
  taste, completeness, and desired-vs-built gaps that rules cannot — but is manual and
  reactive, and its fixes must be back-ported via the
  [`manual-revision-backport`](../../.agents/skills/manual-revision-backport/SKILL.md) skill.

The agent makes this a **standing, repeatable loop** and marks results in Feishu so
editors act at the source. Crucially, the two bases **converge over time**: recurring
diff-doc findings get **codified into new content-lint rules** (capture-as-check), so
the automated base grows and the reviewer diffs shrink.

## 2. Goals

1. One agent runs the whole loop for a target: **build → QC (both bases) → back-port
   gaps to source → re-verify → mark QC in Feishu**.
2. **Delivery is never blocked by QC** — the Word always builds; QC annotates.
3. Every recurring diff-doc finding becomes a codified rule, so quality automation
   compounds (advances the system toward Stage 3 of
   [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md): repo as the
   deterministic *build + validation* engine).

## 3. QC bases (质检依据)

### 依据 A — 现有规则 (rule-based, automated)
- Engine: `tools/content_lint.py` (PR #335) — status-word consistency, English
  residue, slot-key collision, spec↔overview drift (WARN), TM duplicate — plus its
  roadmap rules (template multilingual lint, controlled-vocab/ref integrity,
  translation coverage). Rules catalogue: `content_quality_rules.md` (PR #335).
- Runs against the **exported snapshot** → deterministic.
- **Output:** structured findings `{table, row/record, lang, rule, severity, detail}`.

### 依据 B — 评审差异 (diff-based, human-submitted)
The reviewer expresses the gap between the **built** document and the **desired**
document through **either of two input channels**; both normalize to the same
discrepancy list and feed the identical downstream loop:

- **B1 — Word diff / comparison docx.** A tracked-changes or side-by-side 对比稿
  (the 3-round V3 kind 夏冰 has provided), parsed locally from the `.docx`.
- **B2 — Feishu revised cloud doc (飞书修订版云文档).** The reviewer revises directly
  in a Feishu cloud document (suggestion-mode edits / comments / a revised version);
  the agent **reads the revisions via `lark-cli`** (Feishu CLI) and extracts them —
  no manual export step. (Exact read mechanism — suggestions vs comments vs
  version-diff endpoint — is a design-phase choice; see §10.6.)

- **Engine (shared by B1 & B2):** the
  [`manual-revision-backport`](../../.agents/skills/manual-revision-backport/SKILL.md)
  flow — extract each discrepancy, **diff against current source (don't transcribe)**,
  map it to its source location (a repo template **or** a Feishu phase2 table), and
  surface model/region/sibling scope.
- **Output:** per-discrepancy `{source location, proposed fix, confidence,
  auto-applicable vs needs-human-decision}` — identical shape regardless of input channel.

> The two bases are complementary: **A** is the proactive net (cheap, runs every
> build); **B** is the reactive net (the human's eye for what isn't yet a rule). The
> agent runs both and, over time, promotes **B** findings into **A** rules.

## 4. Agent responsibilities (能力)

1. **Build** — trigger an online-first build for a target via the existing queue
   (`process_build_queue` / `queue-execute`); produce the deliverable Word.
2. **Rule QC** — run `content_lint` on the synced snapshot; collect findings.
3. **Diff QC** — ingest the reviewer diff via **either channel** — a Word comparison
   docx (B1) **or** a revised Feishu cloud doc read through `lark-cli` (B2) — then
   extract + map discrepancies to source.
4. **Reconcile / back-port** — apply **mechanical / high-confidence** fixes at source
   (Feishu rows via `lark-cli`; templates via a PR); **flag** terminology / scope /
   taste decisions for the human (never auto-decide those).
5. **Verify** — re-sync + re-build + re-run `content_lint` → confirm zero residuals
   (the skill already ships a `scan_residuals.py` for this).
6. **Mark in Feishu** — write QC status back to Feishu (see §6).
7. **Capture-as-check** — when a diff-doc finding recurs or generalizes, **propose a
   new `content_lint` rule** so it becomes automated next round.

## 5. Workflow (the loop)

```text
  [trigger: OpenClaw command / schedule / reviewer uploads a diff Word]
        │
        ▼
   BUILD (queue, online-first) ─────────────► deliverable Word (delivered to Feishu)
        │                                            (delivery never blocked by QC)
        ▼
   QC base A: content_lint on snapshot ─┐
   QC base B: parse diff Word → map ────┤
        │                               ▼
        │                        reconcile findings
        ▼                               │
   auto-apply mechanical fixes ◄────────┤
   flag human decisions ───────────────┘
        │
        ▼
   VERIFY: re-sync + re-build + re-lint  ──► zero residuals?
        │
        ▼
   MARK in Feishu (per-row QC status / QC report)  ──►  editors fix remaining at source
        │
        └───── recurring diff finding → propose new content_lint rule (capture-as-check) ──┐
                                                                                            │
   (next round: the automated base is bigger, the reviewer diff is smaller) ◄──────────────┘
```

## 6. Feishu QC marking (质检标识)

Two surfaces, can be combined:

- **A. Per-row QC field (recommended — closes the loop):** add `质检状态` (single-select
  ✅ pass / ⚠️ warn / ❌ fail) + `质检说明` (which rule / language / from rule-base or
  diff-doc) to the content tables. Editors see, per row, exactly what to fix — mirrors
  the existing `参数填写` / `多语言复核` checkboxes.
- **B. QC report table (history / trend):** one row per finding — `row-link · rule ·
  severity · source(rule|diff) · build-version · timestamp`. Good for tracking quality
  over releases.
- **(optional) C. Mark the output Word:** highlight the problem spans in the delivered
  `.docx` via the `docx-highlight-changes` skill — for reviewers.

**Mapping gap to resolve:** `content_lint` currently works on the CSV snapshot (no
`record_id`). Writing marks back to Feishu requires mapping each finding to its Feishu
`record_id` — either carry `record_id` in the snapshot, or re-resolve by key at
write-back time.

## 7. Build ↔ QC decoupling (answers "会不会影响交付")

- The build that produces the Word is **independent** of QC. QC is a **non-blocking
  annotator by default** — a red QC result does **not** stop delivery.
- Whether QC becomes a **gate** (block on severity X) is a **configurable policy** the
  operator owns, not a default. Default: `FAIL` marks + reports, `WARN` marks only,
  nothing blocks.

## 8. Relationship to existing components

| Component | Role in the agent |
|---|---|
| `tools/content_lint.py` (PR #335) | QC base A engine |
| `manual-revision-backport` skill | QC base B engine (diff → source mapping) |
| [`phase2_source_tables_reference.md`](phase2_source_tables_reference.md) | the map for "where does this map to" |
| build queue (`process_build_queue` / `queue-execute`) + `integrations/openclaw/` | execution + trigger surface |
| [`spec_overview_value_dedup_proposal.md`](spec_overview_value_dedup_proposal.md) | removes the drift class structurally (fewer QC findings) |
| `docx-highlight-changes` skill | optional output-marking (§6C) |

## 9. Inputs / Outputs

- **Inputs:** target (model / region / langs); an optional review diff via **either**
  channel — a Word comparison docx (B1) **or** a revised Feishu cloud doc read through
  `lark-cli` (B2); the codified rules + the live source (Feishu / TM / templates).
- **Outputs:** built Word (delivered to Feishu); QC marks in Feishu (§6); a QC report
  (both bases); source fixes (direct Feishu writes for data, a PR for templates);
  a list of flagged human decisions; proposed new rules.

## 10. Open decisions (待确认)

1. **Marking surface:** per-row field (A) / report table (B) / both. Adding a Feishu
   field is a **schema change → requires explicit confirmation**, and a choice of
   *which* content tables get it.
2. **Auto-fix policy:** which diff-doc change classes auto-apply vs always-flag
   (terminology / scope / taste are always human).
3. **Severity policy:** does `WARN` get marked? does any severity ever gate delivery?
4. **Trigger model:** OpenClaw chat command, schedule, reviewer-upload, or all.
5. **Agent runtime placement:** a repo skill orchestrating the steps, an OpenClaw-side
   agent, or the queue itself — and how the diff input (a Word file path **or** a
   Feishu doc token) is handed to it.
6. **Feishu revision read mechanism (channel B2):** which Feishu surface the agent
   reads revisions from via `lark-cli` — suggestion-mode edits, comments, or a
   version-to-version block diff — and how a revised Feishu doc is identified /
   registered for a given target.

## 11. Phased delivery (incremental, low-risk first)

- **P0** — `content_lint --json` (machine-consumable output). *No schema change.*
- **P1** — QC report table (B) + write **rule-based** findings to it (read-only
  marking; proves the write-back path).
- **P2** — diff ingestion for **both** channels (B1 Word docx **and** B2 Feishu doc via
  `lark-cli`) → a normalized mapping report (no auto-write; human reviews the map).
- **P3** — back-port auto-apply (mechanical only) + per-row Feishu QC field (A).
  *Schema change — gated on §10.1.*
- **P4** — capture-as-check (diff finding → proposed rule) + scheduled live-source run.

## 12. Non-goals

- Not replacing human terminology / taste judgment — those are **flagged**, not auto-decided.
- Not blocking delivery by default.
- Not editing generated outputs or the synced CSVs — **fix at source only**.
- Not (yet) a general CMS workflow engine — scoped to the QC loop.

## 13. Acceptance criteria

Given a target and (optionally) a reviewer diff — a Word docx **or** a revised Feishu
cloud doc — one agent run produces:

1. the deliverable Word (built, delivered to Feishu);
2. a QC report covering **both** bases;
3. mechanical fixes applied at source (Feishu writes / a template PR) and re-verified
   to **zero residuals**;
4. the remaining items **flagged** with their source location and a proposed fix;
5. **QC marks in Feishu** reflecting the per-row status;
6. for any recurring diff finding, a **proposed new content-lint rule**.

## 14. References

- Data model: [`phase2_source_tables_reference.md`](phase2_source_tables_reference.md)
- Long-term layers / stages: [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md)
- Drift's structural fix: [`spec_overview_value_dedup_proposal.md`](spec_overview_value_dedup_proposal.md)
- Reviewer-diff back-port flow: [`manual-revision-backport` skill](../../.agents/skills/manual-revision-backport/SKILL.md)
- Execution roadmap: [`optimization_project.md`](../optimization_project.md)
- QC base A (rules + lint): `tools/content_lint.py` and `code-as-doc/content_quality_rules.md` — **PR #335** (not yet merged; link once landed).
