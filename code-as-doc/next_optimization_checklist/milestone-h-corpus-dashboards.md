# Optimization checklist: Milestone H (corpus-driven templates and three-flow dashboards)

Part of the [optimization checklist](../next_optimization_checklist.md); its index lists every milestone page,
and its §1 update rules apply here. Update item status on this page and add new
items for this milestone here, not to the hub.

## 6f. Milestone H: Corpus-Driven Template Optimization + Three-Flow Dashboards

Milestone status: `pending`
Milestone target: `after 2-3 live review rounds`
Milestone note: registers the Milestone H proposal from the 2026-07-02
three-flows analysis (operator-approved 2026-07-03). The template flow is the
last one-way leg — templates feed every build but nothing feeds templates.
Suggested order: H1 → H2 → H3. H1 needs no live-round data and can start any
time; H2 waits for the revision ledger to accumulate 2–3 real review rounds;
H3 closes with the dashboards.
**Scope note (2026-07-03):** the "查客服答案" capability (manual-content Q&A
with cited sources, plus its two metrics 客服问题命中率 / 带来源答案比例) is
deliberately **NOT** part of this milestone — it is recorded below as a
separate workstream candidate, to be sized after live rounds and the
stock-manual-onboarding evaluation.

- [ ] PR H1: Template-sentence ↔ corpus reconciliation lint (工程 H1)
  - Status: `pending`
  - Target files:
    - new `tools/template_corpus_lint.py` (or a `content_lint` extension)
    - [`../tools/revision_ledger.py`](../../tools/revision_ledger.py) (candidate emission reuses the G2 shape)
  - Done when:
    - translatable template sentences are scanned against the live TM: missing translations emit TM intake candidates (same approval shape as `tm-candidates`); drifted wording emits a flag report
    - the 模板句语料覆盖率 metric has a baseline number
    - first missing-translation candidates reach the human approval queue

- [ ] PR H2: Ledger recurrence miner → template proposals (工程 H2)
  - Status: `pending`
  - Note: needs 2–3 live review rounds of ledger data before results are meaningful
  - Target files:
    - [`../tools/revision_ledger.py`](../../tools/revision_ledger.py) (`template-candidates` subcommand)
  - Done when:
    - accepted/edited rows cluster by normalized machine text; the same-direction correction hitting ≥N targets with template-origin source (reuse the family-identical check) projects a `template_sync_proposal` draft
    - the first corpus-driven template fix is applied by a human through the existing Workstream Q runbook
    - the 模板复发修正率 metric is computable

- [x] PR H3: Three-flow dashboards — ops face + value face (工程 H3, scope expanded 2026-07-03; done 2026-07-03)
  - Status: `done` — `tools/flow_dashboard.py report` emits both faces
    (markdown + json under `reports/flow_dashboard/`) with monthly buckets;
    `pdf_annotate` appends a run ledger (`--backfill-summary` for history);
    the two template-flow metrics correctly show `no_data` until H1/H2 land.
    First real run immediately surfaced an actionable signal: reflow rate 0%
    because landed deltas were never stamped `accepted` in the ledger.
  - Note: expanded from the original five-metric health report into a
    **two-face dashboard**. Ops face (system health, for the operator):
    reflow rate, TM hit rate, second-revision rate, template recurrence rate,
    template-sentence corpus coverage. Value face (output proof, for
    stakeholders): audited-PDF count, model/region/language coverage counts,
    stale/duplicate/drift findings count, revision-reflow counts, TM candidate
    counts, and the time-saved-per-manual narrative metric (needs an operator
    baseline estimate of the pre-system manual effort). Start recording
    immediately even where today's value is zero — a metric without history
    cannot show a trend. Includes a small run ledger for `pdf_annotate`
    (mirroring `tools/tm_hit_rate.py`) so the audited-PDF count has a data
    source.
  - Target files:
    - new aggregator tool under `tools/`
    - [`../tools/pdf_annotate.py`](../../tools/pdf_annotate.py) (run-ledger append)
  - Done when:
    - one command emits both dashboard faces from existing artifacts (ledger / hit-rate ledger / content_qc reports / configs / catalog)
    - monthly trend review is possible for every metric that has history

### Workstream candidate (recorded, not scheduled): 查客服答案

Manual-content Q&A with cited sources — answer product questions from the
built manuals (catalog + TM + built HTML/PDF), always with a source reference.
Carries its own two metrics: 客服问题命中率 and 带来源答案比例. Natural
downstream of stock-manual onboarding (content must be in the system before it
can be cited). Size it as its own workstream after Milestone H and the
stock-onboarding pilot; do not let it slip into an "entry-point polish" PR.
