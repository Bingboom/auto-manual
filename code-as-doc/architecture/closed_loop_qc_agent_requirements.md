# Requirements: Closed-Loop QC Agent (闭环质检 Agent)

Status: **requirements baseline** · Owner: 夏冰 · Drafted 2026-06-07, revised same day after a multi-perspective evaluation + a live B2 feasibility spike.
Scope of this file: *what* the agent must do and *why*, plus the contracts settled in review. The active implementation rollout lives in [`../dev/closed_loop_qc_implementation_plan.md`](../dev/closed_loop_qc_implementation_plan.md).

## 0. One-liner

A dedicated **standing agent service** (a new, always-on LLM-agent runtime orchestrating skills) that **closes the manual-quality loop**: triggered by a Feishu message carrying a link to a **revision-accepted Feishu cloud doc**, it builds the manual, checks it against **two QC bases** (codified content rules + the reviewer's built-vs-desired diff), **routes each revision to its source** — repo templates / the `docs/_review` bundle via a human-merged PR, and the source bitable as a **suggestion (never a silent write)** — and marks QC status in Feishu. Quality is caught and fixed at source, continuously, instead of by eye at release.

## 1. Background & motivation

The manual is produced from Feishu source tables + Translation Memory + per-language templates (data model: [`phase2_source_tables_reference.md`](phase2_source_tables_reference.md)). Historically, content defects were found **late and by eye** on the built `.docx` (2026-06-07 examples: LCD status words not bold; an Italian line still reading `On:`).

Two complementary quality signals exist, run ad-hoc by a human today:

- **Codified rules** — `tools/content_lint.py` (PR #335): automated, proactive, but only covers what has been turned into a rule.
- **Human reviewer diff** — the *built-vs-desired* comparison a reviewer produces. Catches taste, completeness, and desired-vs-built gaps that rules cannot; reactive; its fixes are back-ported via the [`manual-revision-backport`](../../.agents/skills/manual-revision-backport/SKILL.md) skill.

The agent makes this a **standing, repeatable loop** and marks results in Feishu so editors act at the source. The two bases **converge over time**: recurring diff findings get **codified into new content-lint rules** (capture-as-check), so the automated base grows and reviewer diffs shrink — advancing Stage 2 → Stage 3 of [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md) (repo as the deterministic *build + validation* engine).

## 2. Goals

1. One agent runs the loop for a target: **build → QC (both bases) → route revisions to source → re-verify → mark QC in Feishu**.
2. **Delivery is never blocked by QC** — the Word always builds; QC annotates (gating is an opt-in policy, not a default).
3. Every recurring diff finding becomes a codified rule (capture-as-check), so quality automation compounds.

## 3. QC bases (质检依据)

### 依据 A — codified rules (automated)
- Engine: `tools/content_lint.py` + `content_quality_rules.md` (**PR #335**) — status-word consistency, English residue, slot-key collision, spec↔overview drift (WARN), TM duplicate, + roadmap rules.
- Runs against the **exported snapshot** → deterministic.
- **Current state (honest):** the tool today prints human text and returns 0/1; it has **no `--json` and emits no `record_id`** (it reads CSV snapshots that drop record_id). A stable machine output `{table, record_id, lang, rule, severity, detail}` is **P0 build work**, not existing behavior.

### 依据 B — review diff (human-submitted) — **B2 is the primary channel**

The reviewer expresses the built-vs-desired gap through one of two channels; both normalize to the same discrepancy list `{location, old, new}` and feed the identical downstream routing.

**B2 — Feishu revision-accepted cloud doc (PRIMARY).**
- Input: a Feishu **message carrying the doc link**. The doc must be **revision-accepted** (suggestions applied, or directly edited) so the content is the final intended text.
- Read via `lark-cli`: `docs +fetch --doc "<link>"` returns the doc as markdown; extraction = **semantic diff** (normalize away `lark-*` tags, word-level compare) against a baseline.
- **Why primary:** the ingress is the lightest — a link is *text*, so it rides the existing Feishu text adapter (only a small URL-extractor to add). The reviewer never leaves Feishu.
- Boundary: this QC channel uses the **Review Doc Backport** path from
  [`Feishu_Cloud_Doc_Backport_Design.md`](Feishu_Cloud_Doc_Backport_Design.md).
  Template-maintenance cloud docs use the sibling **Template Doc Backport** path
  and are not themselves a QC base.

**B1 — Word tracked-changes docx (FALLBACK).**
- Extraction is trivial — `extract_docx_changes.py` reads explicit `w:ins`/`w:del`, no semantic diff, no accept step.
- **But the ingress is heavy:** the reviewer must produce a Word file and send it as a Feishu *file* message — which the adapter **drops today** (text-only, see §5.1) — requiring new file-receive + Drive-download code. Use B1 only when a Word tracked-changes file already exists.

### 3.1 B2 — empirically verified (2026-06-07 live spike)

Run against a real revision-accepted Feishu doc:
- `docs +fetch` returns the full doc as markdown (~52 K chars, structure + bold preserved). ✓
- **Pending** suggestion-mode edits are **merged into the content as plain text with no structure** — `docs +fetch` and the `docx/v1/.../blocks` API both show the suggested text as ordinary runs with **no insert/delete markers** (no `underline`/`strikethrough` style flags); the `drive .../comments` API returns **0** (suggestions are not comments). So pending suggestions are **not** cleanly machine-extractable → **accept-first is required**.
- After the reviewer **accepts**: the content is clean (a replaced word's old text is gone — verified `environment.` count 2→1), and a normalized **word-level diff cleanly extracted the revision**: *at "…human health and the", replace `environment.` → `修订2`*. ✓

→ **B2 recipe (settled): accept revisions → `docs +fetch` → semantic (tag-stripped, word-level) diff vs baseline → revision list.** Baseline = a `docs +fetch` snapshot taken at review hand-off (same markdown format, cleanest), or the build's own output (works with the normalizer).

## 4. Agent responsibilities (能力)

1. **Build** — trigger an online-first build for the target via the existing queue; produce the deliverable Word.
2. **Rule QC** — run `content_lint` (once it emits JSON) on the synced snapshot.
3. **Diff QC** — ingest the review diff: B2 `docs +fetch` + semantic diff (primary), or B1 docx tracked-changes (fallback).
4. **Route & reconcile** — map each revision to its source and act per §5.2: mechanical/high-confidence template fixes → a PR; everything else → flag; the source bitable → **suggestion only**.
5. **Verify** — re-sync + re-build + re-run `content_lint`; for base-B fixes, run `scan_residuals.py` against templates + a fresh source dump → confirm zero residuals.
6. **Mark in Feishu** — write QC status back (see §6).
7. **Capture-as-check** — when a diff finding recurs/generalizes, **propose a new `content_lint` rule** (as a human-merged PR, never an auto-merged code edit).

## 5. Workflow (the loop)

```text
  [trigger: Feishu message with a link to a revision-accepted Feishu doc]
        │
        ▼
   BUILD (queue, online-first) ─────────────► deliverable Word (delivered to Feishu)
        │                                            (delivery never blocked by QC)
        ▼
   QC base A: content_lint(--json) on snapshot ─┐
   QC base B: docs +fetch → semantic diff ──────┤
        │                                        ▼
        │                                route each revision (§5.2)
        ▼                                        │
   template fix → PR  ◄──────────────────────────┤
   bitable change → suggestion ◄─────────────────┤
   anything uncertain → flag for human ◄──────────┘
        │
        ▼
   VERIFY: re-sync + re-build + re-lint / scan_residuals  ──► zero residuals?
        │
        ▼
   MARK in Feishu (per-row QC status / QC report)  ──►  editors confirm remaining at source
        │
        └── recurring finding → propose new content_lint rule (capture-as-check, as a PR) ──┐
                                                                                            │
   (next round: automated base bigger, reviewer diff smaller) ◄──────────────────────────────┘
```

### 5.1 Trigger & execution model (via the existing OpenClaw control layer)

**The QC workflow is a NEW system to develop — agentic, run on a standing agent service.** It is an **LLM agent orchestrating skills**, NOT an in-chat reasoning loop, and **NOT the deterministic `build.py` pipeline** (which is mechanical: sync→assemble→render, no LLM). Three tiers:

1. **Trigger — the existing thin OpenClaw control layer** ([`integrations/openclaw/`](../../integrations/openclaw), [`OpenClaw_Control_Layer_Plan.md`](OpenClaw_Control_Layer_Plan.md)): receives the Feishu message, resolves the `质检/QC` action + the typed `doc_token` (or `file_token`), and **hands off** to the QC agent service. Stays pure trigger + status-reply — no heavy work inside OpenClaw (the Plan's §11 boundary).
2. **Execution — a NEW standing QC agent service (this requirement's core deliverable — "develop QC workflow (new)").** An **always-on LLM agent runtime** (e.g. Claude Agent SDK) that orchestrates *skills* (`manual-revision-backport`, `content_lint`, `docx-highlight-changes`) + `lark-cli` + `git`/`gh` to: `docs +fetch` the doc → semantic-diff → **map each revision to its source, decide mechanical-vs-flag, open the template PR, propose the bitable suggestions, mark QC in Feishu**. This is **judgment work (LLM reasoning)** — a different *kind* of thing from `build.py`. Persistent (not CI-ephemeral) per operator decision.
3. **Deterministic helpers it calls:** `build.py` (build), `content_lint` (rule QC), the skill scripts (`extract_docx_changes.py`, `scan_residuals.py`), `lark-cli` (read / propose), `git`/`gh` (PR).

**Build vs reuse — the honest line** (the trigger *spine* is mostly reusable; the **standing agent service is the net-new core**):

| Reuse (verified present) | Build (net-new) |
|---|---|
| OpenClaw adapter **text** path + action resolution (`detect_action` → `queue-resolve-action`); the dispatch/handoff mechanism (`cli.mjs` / `github-client`) | **The standing QC agent service** — an always-on LLM-agent runtime orchestrating the skills (the core new system) |
| Bitable **field write-back** (`write_publish_html_link.py` pattern) | A `质检/QC` action + **doc-link URL extractor**; the **OpenClaw → QC-service handoff** |
| **Drive media download** (`sync_data.py` GET `/drive/v1/medias/{token}/download`) → makes the B1 file fallback buildable | `content_lint --json` + record_id; the **B2 fetch + semantic-diff** extractor + the skill orchestration |

**Sender authorization (required precondition):** the adapter today filters only bot-origin / empty / missing-@-mention — there is **no operator allowlist**. The QC action newly grants *open-PR* and *Feishu-write* (QC marks / suggestions) power, so triggering QC **must** be gated by a Feishu `open_id` allowlist (夏冰 / approved editors), enforced **before** action resolution / hand-off. This is a requirement, not an implementation detail.

### 5.2 Per-source routing (how each revision is merged)

Each extracted revision maps to its **source type** (the `manual-revision-backport` logic), and is routed accordingly:

| Revision lands in… | Merge target | How |
|---|---|---|
| **Template-driven** content (operation guide / safety / prose) | `docs/templates/<lang>/`, **or `docs/_review/…` if the target is already in review** (AGENTS.md §2) | **open a PR** (human-merged; agent never self-merges) |
| **Data-driven** content (spec values / LCD / footnotes — from the bitable) | the **source bitable** | **propose a suggestion** (not a silent write); for an in-review target, the operator accepts → `sync-review` re-pulls it into the bundle |

The agent must detect the target's **review state** to choose `docs/templates` vs `docs/_review`.

### 5.3 Skills & tools the QC workflow orchestrates

The standing QC agent service is an LLM runtime; its "work" **is** invoking these repo **skills** (`.agents/skills/`, registered in AGENTS.md §7) and **tools**. This is the explicit inventory the workflow depends on.

**Skills (the agentic building blocks):**

| Skill | Role in the QC loop | When invoked |
|---|---|---|
| **`manual-revision-backport`** | **CORE.** Map each revision to its source (repo template vs Feishu phase2 table), **diff against current source (don't transcribe)**, surface model/region/sibling scope, verify zero residuals. Ships `extract_docx_changes.py` (B1 Word tracked-changes extraction) and `scan_residuals.py` (the verify step). | every run (QC base B) |
| **`bitable-translation-memory`** | Terminology / sentence-pair lookup when a revision touches localized text — so a proposed bitable suggestion uses the **canonical** term, consistent with the Translation Memory. | when a revision affects translated content |
| **`bilingual-tm-maintenance`** | Write a corrected translation back to the live `Translation_Memory` (+ maintenance / audit logs) when the fix should become the canonical pair — keeps QC base A's TM-driven rules fed. | when a correction should update the TM |
| **`docx-highlight-changes`** | Optional output-marking: highlight the corrected spans in the delivered `.docx` so the reviewer sees exactly what changed (§6 option C). | optional, on the built docx |
| **`manual-rewrite-with-tm`** | Secondary: a structure-preserving chunk rewrite reusing TM phrasing, when a revision is large rather than a point edit. | rare / large rewrites |

**Tools (deterministic, not skills):** `content_lint.py` (QC base A), `build.py` (build the manual), `lark-cli` (`docs +fetch`, comments, bitable read / propose), `git` / `gh` (open the PR).

**B2 extraction note:** `manual-revision-backport`'s *extraction* script (`extract_docx_changes.py`) is **docx-only (B1)**. The **B2 (Feishu) channel's extraction is the net-new `docs +fetch` + semantic-diff** (§3.1); its output then feeds the **same** skill's mapping / scope / verify logic. So B2 **reuses the skill's judgment half and builds the extraction half**.

## 6. Feishu QC marking (质检标识)

- **A. Per-row QC field (recommended):** `质检状态` (✅/⚠️/❌) + `质检说明` on content rows — editors see per-row what to fix (mirrors `参数填写`/`多语言复核`).
- **B. QC report table:** one row per finding (`row-link · rule · severity · source · build-version · timestamp`) for history/trend.
- **Prerequisite — `record_id` resolution (hard dependency):** `content_lint` reads CSV snapshots that drop `record_id`, so per-row marking must re-derive the live record. Rule: **exact-or-abstain** — zero or multiple key-matches → flag as needs-human, never guess a row. Prefer carrying `record_id` into the snapshot at sync time; require **GET-verify-after-write** before a mark counts as applied.

## 7. Build ↔ QC decoupling

The build that produces the Word is **independent** of QC. QC is a **non-blocking annotator by default** — a red QC result does not stop delivery. Gating (block on severity X) is a **configurable policy the operator owns**. Default: `FAIL` marks + reports, `WARN` marks only, nothing blocks.

## 8. Relationship to existing components

| Component | Role |
|---|---|
| `tools/content_lint.py` (PR #335) | QC base A engine |
| `manual-revision-backport` skill | QC base B engine (diff → source mapping) |
| [`phase2_source_tables_reference.md`](phase2_source_tables_reference.md) | the map for "where does this revision map to" |
| build queue (`process_build_queue`/`queue-execute`) + `integrations/openclaw/` | **trigger + hand-off** surface (the *execution* is the new standing QC agent service, §5.1) |
| **standing QC agent service** (NEW — Claude Agent SDK runtime) | the agentic executor that orchestrates the skills; the "develop QC workflow (new)" deliverable |
| [`spec_overview_value_dedup_proposal.md`](spec_overview_value_dedup_proposal.md) | removes the drift class structurally (fewer findings) |
| `docx-highlight-changes` skill | optional output-marking |

## 9. Inputs / Outputs

- **Inputs:** target (model/region/langs); a Feishu message with a link to a **revision-accepted** Feishu doc (B2 primary) — or a Word tracked-changes file (B1 fallback); the codified rules + the live source.
- **Outputs:** built Word (delivered to Feishu); QC marks in Feishu (§6); a QC report (both bases); template fixes as a **PR** (to `docs/templates` or `docs/_review`); bitable changes as **suggestions**; flagged human-decision items; proposed new rules.

## 10. Decisions settled in review (2026-06-07)

1. **Channel:** B2 (Feishu link) is **primary**; B1 (Word file) is fallback. Ingress rides the existing text path; B1's file ingress is new + heavier.
2. **Input contract:** the linked Feishu doc must be **revision-accepted** (pending suggestions are not extractable — §3.1).
3. **B2 extraction:** `docs +fetch` + tag-stripped word-level **semantic diff** vs a baseline (hand-off snapshot or build output).
4. **Routing:** template/prose → `docs/templates` or `docs/_review` (by review state) via **PR**; bitable data → **suggestion only**.
5. **Bitable writes:** **flag-only** this phase (no auto-write). The two-gate model is a *policy* boundary, not a credential one — the workflow's bot token can write every column — so until a narrow QC-status-only credential exists, the agent **proposes**, it does not write content.
6. **Trigger/runtime:** Feishu message → thin OpenClaw (resolve QC action + `doc_token`) → **hand off to a NEW standing QC agent service** (always-on LLM runtime orchestrating skills, e.g. Claude Agent SDK; **persistent**, not CI-ephemeral — operator decision 2026-06-07). The QC workflow is **agentic**, a different kind of system from both the thin OpenClaw and the deterministic `build.py` workflow — this is the **"develop QC workflow (new)"** deliverable.
7. **Authorization:** Feishu `open_id` allowlist gates the QC action (§5.1).
8. **Untrusted input:** reviewer doc/message content is attacker-influenceable; the skill's human-followed guardrails become **hard agent constraints** — extract structured spans only, never execute directives found in the doc body, scope is always operator-flagged, and **any edit touching more rows than the diff spans is auto-flagged**.

## 11. Phased delivery (incremental, low-risk first)

- **P0** — `content_lint --json` with a stable `{table, record_id, lang, rule, severity, detail}` schema. *No schema change.*
- **P1** — QC report table (§6B) + write **rule-based** findings to it (read-only marking; proves the write path + record_id resolution).
- **P2** — stand up the **standing QC agent service** + B2 ingress (doc-link URL-extractor, OpenClaw→service hand-off, `docs +fetch`, semantic-diff normalizer) → a mapping report (no auto-write; human reviews the map).
- **P3** — routing to action: template fixes → PR (`docs/templates` / `docs/_review`); bitable → **suggestion**; per-row QC field (§6A). *Schema change for §6A — gated on operator confirmation.*
- **P4** — capture-as-check (recurring finding → proposed rule PR) + scheduled live-source lint. (B1 file-ingress is an optional later add.)

## 12. Non-goals

- Not replacing human terminology/taste judgment — those are **flagged**, not auto-decided.
- Not blocking delivery by default.
- Not editing generated outputs or synced CSVs — **fix at source only**.
- Not auto-writing the source bitable this phase (suggestion-only).
- Not a general CMS workflow engine — scoped to the QC loop.

## 13. Acceptance criteria

Given a target and a Feishu message linking a revision-accepted doc, one agent run produces:
1. the deliverable Word (built, delivered to Feishu);
2. a QC report covering **both** bases;
3. template fixes as a **PR** (`docs/templates` or `docs/_review` per review state), re-verified to **zero residuals**;
4. bitable changes as **suggestions** (no silent writes) + remaining items **flagged** with source location + proposed fix;
5. **QC marks in Feishu** (record_id resolved exact-or-abstain);
6. for any recurring finding, a **proposed new content-lint rule** (as a PR).

## 14. Open design questions (state the principle now; mechanics → design proposal)

- **Auto-fix taxonomy / confidence:** principle = flag-only default, auto-write disabled until an explicit "mechanical" allowlist (e.g. accent fixes, rule-corroborated residue swaps) is defined; terminology/scope/taste always human.
- **Conflict precedence:** A-rule vs B-diff on one row, or two diff findings on a shared/derived value → default human-flag, never auto-pick; report distinguishes "already-converged" from "fixed".
- **Idempotency / re-run:** dedupe on `target + build-version + finding-hash`; reuse an open PR vs duplicates; upsert marks; debounce concurrent runs via the existing dispatch nonce.
- **Failure / rollback:** build-fail → report + skip diff-QC; capture pre-edit value as a reversible record for any write; reconcile "agent re-syncs" with operator-gated `sync-data`.
- **No source match:** a genuinely new revision maps to no row → always human-flagged with nearest anchor, never auto-created (consider `--draft-placeholders`).
- **Verification contract:** base A re-lints to zero FAIL; base B is verified by `scan_residuals.py` (needs a curated OLD-term list), **not** by content_lint.
- **Semantic-diff robustness:** the normalizer must handle all page types (tables, line-blocks, multi-lang) and Feishu-md ⇄ build-md format differences; fetch is non-deterministic, so compare normalized text, never raw lines.
- **Multi-lang unit-of-work:** one run = one model/region across all shipped langs; per-(lang, table/template) findings rolled into one report; operator scope confirmation before any source write.

## 15. References

- Data model: [`phase2_source_tables_reference.md`](phase2_source_tables_reference.md)
- Long-term layers / stages: [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md)
- Drift's structural fix: [`spec_overview_value_dedup_proposal.md`](spec_overview_value_dedup_proposal.md)
- Reviewer-diff back-port flow: [`manual-revision-backport` skill](../../.agents/skills/manual-revision-backport/SKILL.md)
- Feishu cloud-doc backport routing:
  [`Feishu_Cloud_Doc_Backport_Design.md`](Feishu_Cloud_Doc_Backport_Design.md)
- Control-layer plan: [`OpenClaw_Control_Layer_Plan.md`](OpenClaw_Control_Layer_Plan.md)
- Execution roadmap: [`optimization_project.md`](../optimization_project.md)
- Implementation rollout: [`closed_loop_qc_implementation_plan.md`](../dev/closed_loop_qc_implementation_plan.md)
- QC base A (rules + lint): `tools/content_lint.py` and `code-as-doc/content_quality_rules.md` — **PR #335** (link once merged).
