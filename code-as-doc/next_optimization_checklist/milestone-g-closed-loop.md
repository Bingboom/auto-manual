# Optimization checklist: Milestone G (business closed-loop engineering)

Part of the [optimization checklist](../next_optimization_checklist.md); its index lists every milestone page,
and its §1 update rules apply here. Update item status on this page and add new
items for this milestone here, not to the hub.

## 6e. Milestone G: Business Closed-Loop Engineering

Milestone status: `done`
Milestone completed: `2026-07-02`
Milestone target: `2026-07`
Milestone note: PR-level breakdown of the 2026-07-02 business closed-loop
analysis (main line: spec intake → source tables → build → revision →
**reflow**; capability lines: TM pre-translation hit rate, PDF review
annotation). The central finding: revision reflow (G1/G2) and TM corpus growth
are one loop — `revision_ledger` records reviewer corrections but nothing
reconciles them (`verdict` stays `PENDING`) and no route feeds accepted
sentence pairs into `Translation_Memory`. Suggested order: G1 → G3 → G7 → G0 →
G2 → G6 → G4 → G5; G0 is the prerequisite for G2 (route-layer changes land in
the split modules, not the 1380-line CLI). G2's live apply and G4 need operator
decisions where marked.
**Operator grant (2026-07-02):** PRs in this milestone may be merged by the
executing agent when the full matching validation set is green; the grant
expires when G1–G7 are done. Each PR updates its item status here in the same
change.

- [x] PR G0: Split `cloud_doc_backport_cli.py` (args / commands / orchestration)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: 1380-line conductor → `args` (422, argparse + arg-interpretation
    helpers) / `commands` (497, single-command runners) / `orchestration`
    (802, review-branch + baseline + PR flow) / `cli` (222, `main` + the
    compatibility re-export hub). One-way imports (`args` ← `commands` /
    `orchestration` ← `cli`); facade unchanged. One deviation from "tests pass
    unchanged": 39 test patches targeted `cloud_doc_backport_cli.*` seams
    whose call sites moved — retargeted to `cloud_doc_backport_orchestration.*`
    (patching a re-export never intercepted the real call). Also lands the G1
    tail: the orchestration baseline flow feeds the revision ledger
    best-effort (`AUTO_MANUAL_REVISION_LEDGER_PATH`; `off` disables; tests
    isolated via setUpModule).
  - Target files:
    - [`../tools/cloud_doc_backport_cli.py`](../../tools/backport/cli.py)
    - [`../tools/check_maintainability_guardrails.py`](../../tools/check_maintainability_guardrails.py)
  - Done when:
    - argparse definitions, per-command run functions, and multi-step orchestration (review-branch / baseline / PR opening) live in separate modules with one-way imports
    - `cloud_doc_backport.py` facade re-exports stay compatible (existing tests pass unchanged)
    - each new module enters the guardrail list; the old 1400-line threshold is replaced by per-module thresholds

- [x] PR G1: Ledger reconcile trigger + similarity verdict (工程①)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: the trigger is a local piggyback, not CI — the ledger is a local
    artifact under `reports/revision_ledger/` that no workflow can see, so
    every `ingest` (each backport round) now auto-reconciles the previous
    rounds' pending rows (`--no-reconcile` opts out), and `reconcile --auto`
    resolves merge metadata (commit / date / author / `(#PR)`) from git.
    Verdicts gained a similarity layer (best-window partial ratio, threshold
    0.90, min needle 12 chars) over exact containment; `stats` now reports
    `reflow_rate`. Auto-ingest wiring into the backport orchestration lands
    with G0.
  - Target files:
    - [`../tools/revision_ledger.py`](../../tools/revision_ledger.py)
  - Done when:
    - reconcile runs automatically each backport round, so ledger rows leave `PENDING` without a human remembering
    - `classify_verdict` uses similarity matching; punctuation/line-break edits no longer misclassify
    - reflow rate (non-PENDING rows / total) is computable from the ledger

- [x] PR G2: Ledger → TM route (工程②)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: no new write path was built — `tm-candidates` projects accepted
    review-route rows into the suggestion shape the **existing** gated TM
    write path already consumes, and `tm-apply` drives
    `translation_memory_sync.apply_translation_suggestions` (human-approval
    hashes, exact-or-abstain resolution by old target text, GET-verified
    idempotent writes; dry-run unless `--write --tm-binding`). Candidates
    whose old translation is not in the TM abstain and stay visible for the
    manual `bilingual-tm-maintenance` flow. Which base `--tm-binding` names is
    the G4 decision.
  - Target files:
    - [`../tools/revision_ledger.py`](../../tools/revision_ledger.py)
  - Done when:
    - accepted revision deltas that rewrite translated prose emit TM pair candidates (source sentence, target sentence, provenance, confidence)
    - candidates are reviewable and only reach live `Translation_Memory` after operator approval
    - reviewer-corrected sentence pairs stop being lost after each review round

- [x] PR G3: TM hit-rate ledger (工程③)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: `Matcher` counts sentence-level units attempted vs matched (tiny
    texts excluded); the run report gains `units_total` / `units_matched` /
    `hit_rate`, and every run best-effort appends to
    `reports/tm_hit_rate/ledger.jsonl` via the new stdlib-only
    `tools/tm_hit_rate.py` (`ingest` idempotent by run fingerprint; `stats`
    reports overall + per-language-pair rates; legacy counter-less reports are
    reported separately, never averaged in). The baseline number materializes
    with the first operator preprocess run after merge.
  - Target files:
    - [`../.agents/skills/lark-tm-translation-preprocess/scripts/preprocess_lark_docx_with_tm.py`](../../.agents/skills/lark-tm-translation-preprocess/scripts/preprocess_lark_docx_with_tm.py)
    - [`../tools/tm_hit_rate.py`](../../tools/tm_hit_rate.py)
  - Done when:
    - each preprocess run appends its per-run stats (matched units / total units, by language pair and document) to a cumulative hit-rate ledger under `reports/`
    - a baseline hit-rate number exists so G2/G4 improvements are measurable

- [x] PR G4: TM base convergence (工程④)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: operator decision (2026-07-02): **B — the env-token base — is the
    canonical write base**; the A/wiki mirror (`X3O8…`/`LUIc…`/`tbl6gK…`) is a
    read-only archive. One config point: `$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN`,
    tables resolved by NAME inside it. Converged: the TM query script no longer
    silently falls back to the A wiki token (missing binding now fails loudly;
    `--wiki-token` remains for explicit archive reads), the docx-preprocess
    script's TM defaults switched from hardcoded A coordinates to env-first +
    by-name table resolution, `bilingual-tm-maintenance` (the write skill) now
    targets the canonical base with an explicit do-not-write archive note, and
    the four docs describing A as live carry convergence banners. Data
    migration/backfill of any rows unique to A is operator work outside this PR.
  - Done when:
    - exactly one TM base accepts writes; skills and scripts resolve it from one config point
    - the retired mirror is marked read-only/archived and no skill defaults to it

- [x] PR G5: PDF annotation renderer MVP (工程⑤)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: `tools/pdf_annotate.py` (PyMuPDF, new `requirements.txt` dependency)
    searches each finding's evidence text on the built PDF and writes a
    highlight + note (severity / rule / message / `source_ref` / suggested
    action / fix-at-the-source pointer); unlocatable findings degrade to a
    page-1 summary note — no misplaced highlights. `content_lint` itself was
    untouched (its findings.json is consumed as-is). New skill
    `pdf-annotate-qc` registered in AGENTS.md §7 as the PDF counterpart of
    `docx-highlight-changes`. Known limitation: two-column layouts can defeat
    text search; those findings degrade to the summary note.
  - Target files:
    - [`../tools/pdf_annotate.py`](../../tools/pdf_annotate.py)
    - [`../.agents/skills/pdf-annotate-qc/SKILL.md`](../../.agents/skills/pdf-annotate-qc/SKILL.md)
  - Done when:
    - `content_lint` findings render as highlight + comment annotations on the built PDF (pymupdf text search; page-level fallback when text location fails)
    - each annotation names the source location (table/slot or template) so the reviewer can route the fix
    - output is a sidecar `*_annotated.pdf`; the shipped PDF is untouched

- [x] PR G6: Backport reminder sentinel (工程⑥)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: content comparison instead of timestamps — `tools/backport_reminder.py`
    compares every InReview doc's live text (lark-cli fetch) against the
    committed render baseline on its review branch (read via `git show`, no
    worktree), in the same normalized text space the backport diffs in. Any
    difference (or a missing baseline) means un-backported edits, and the
    alert clears exactly when a backport advances the baseline — no N-day
    heuristic needed, and no dependency on an unverified doc-meta API.
    Daily workflow `backport-reminder.yml` (02:00 UTC) opens/updates/closes
    the `[backport-reminder]` issue, same pattern as schema-parity; reuses
    the build-queue secrets and `feishu-common-setup`. 2026-07-02 follow-up:
    the repo guard copied from parity was wrong for this workflow — reviews
    happen on the business plane (Hello-Docs mirror), so the sentinel now runs
    in both repos, each against its own bound base.
  - Target files:
    - [`../tools/backport_reminder.py`](../../tools/backport/reminder.py)
    - `.github/workflows/backport-reminder.yml`
  - Done when:
    - a review cloud doc with un-backported edits opens/updates a reminder issue (report-only, no auto-backport)
    - the issue closes itself once the backport lands

- [x] PR G7: Intake completeness gate default-on (工程⑦)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: `spec-extract` now errors (exit 2, no outputs written) when
    `--reference` is absent unless `--skip-completeness` is passed explicitly.
    The second done-when was verified already true in current code — no change
    needed: `enrich_candidates_with_snapshot` escalates multi-match business
    keys to `needs_review` (operation + status + warning), and extract-side
    warnings already force `needs_review` status; the original screening claim
    ("ambiguous only warns") was stale.
  - Target files:
    - [`../tools/source_intake.py`](../../tools/data/source_intake.py)
  - Done when:
    - `spec-extract` without `--reference` fails loudly unless `--skip-completeness` is passed explicitly (no silent skip)
    - ambiguous snapshot keys require review instead of warning
