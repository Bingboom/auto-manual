# Closed-Loop Status And Gaps

Updated: 2026-06-28

Inventory of the system's loops (source↔output, dev↔prod), what is closed, and the
remaining gaps — recorded so they can be optimized incrementally rather than all at once.
Companion to [`architecture/System Evolution Strategy.md`](../architecture/System%20Evolution%20Strategy.md)
and [`optimization_project.md`](../optimization_project.md).

The whole system is a **multi-loop architecture around one source of truth (Feishu
Bitable)**, with a shared write spine on every loop that mutates the source:
`exact-or-abstain · human-gated (R9) · drift-guarded · idempotent`. The core content
loop is mature; the frontier is the two content-loop ends (intake/backport recall) and
the dev→prod **Bitable** promotion (code already auto-mirrors).

## Loop inventory

| loop | mechanism | status |
| --- | --- | --- |
| Code dev→prod (`auto-manual` → `Hello-Docs`) | `sync-hello-docs.yml` | ✅ CI-automated |
| Build / review / publish + queue writeback | `feishu-*-queue.yml`, `feishu-start-review.yml` | ✅ CI-automated |
| Content round-trip (source → build → review → **backport** → source) | `cloud_doc_backport*` + `source_table_sync` (sidecar + value-index + drift guard) | ✅ closed; return-end has a human tail (see D) |
| Intake (spec sheet → structured → 入库) | `source_intake*` + `bitable_schema` rule library + completeness gate | ✅ closed; low autonomy (see D) |
| **Bitable structure dev→prod** | `tools/bitable_schema.py` `export`/`apply`/`parity` | 🟡 tooling ready; prod apply manual, drift now alerted daily in CI (E) |
| **Bitable reference data dev→prod** | manual seed import (runbook) | 🔴 manual, not idempotent (see C) |
| Validation / QC | `check` (hard) + `content_lint`/`normalize`/`schema_drift` (advisory) | 🟡 partly advisory |

## Gaps (optimize incrementally)

### B. Tenant parity check — ✅ DONE
`bitable_schema parity --source-base <dev> --target-base <prod>` reports what the prod
tenant lacks/diverges (missing tables/fields, drift), read-only, exits non-zero on
divergence. Closes the biggest blind spot (silent dev↔prod structure drift). **Next:
run it on a schedule / in CI** (overlaps E).

### C. Reference-data dev→prod is manual — TODO (high)
Only *structure* auto-syncs. Config tables whose rows must match across tenants — the
rule library (`规格书字段映射规则`), and dictionaries (`参数名`, `Document_key`) — are
seeded by hand and the import isn't idempotent. **Closes by:** a `seed-export` /
`seed-import` (upsert-by-business-key, idempotent) for the small set of reference tables,
committed seeds riding the code mirror.

### A. No unified promotion — TODO (high)
A feature that adds code + a table + seed + an env var lands in 4–5 separate manual
steps (PR-merge → mirror → `apply` → seed → wire env). **Closes by:** one `promote`
that, given a target tenant, runs `apply` + reference-`seed-import` + prints the env
delta, gated by `parity` before/after. Bundles {structure + reference data + env} into
one dev→prod step (code already rides `sync-hello-docs`).

### E. Prod side is manually triggered — 🟡 parity alert DONE; apply-on-promotion still manual
The **read-only half is closed**: [`.github/workflows/feishu-schema-parity.yml`](../../.github/workflows/feishu-schema-parity.yml)
runs `parity` daily (+ `workflow_dispatch`), scoped to production tables (ignores the dev
`99_*` scratch/experiment tables + `QC_Report`/`数据表`), and **fails only when prod is
missing a table/field** dev defines (`--fail-on missing`; drift is reported but not
alerted, since the dev tenant may legitimately carry extra/dirty select options). On a
miss it opens/updates a `[schema-drift]` issue; on green it auto-closes it. The dev bot
already reads prod cross-tenant, so the only new secret is `FEISHU_PHASE2_PROD_BASE_TOKEN`
(absent → the job no-ops with a "not configured" summary). **Still open:** the *write*
half — an apply-on-promotion job would need prod **write** creds in CI; weigh the security
tradeoff first (today prod writes go through the operator's device-flow `--profile prod`).

### D. Content-loop recall has a human tail — TODO (incremental)
- **Intake (entry):** rule-driven auto-resolve ~33–38%; new-row CREATE + dictionary
  governance are semi-manual. **Closes by:** growing the rule library (port/temp
  value rules) + a governed new-`Row_key`/`Document_key` step.
- **Backport (return):** `lang` is derived only from the doc-name token (empty → Class D
  silently falls back to a heuristic); changed-cell selection picks the first unique
  cell; cross-sibling identical values abstain; Class-R prose abstains on text
  duplicated across headings. **Closes by:** derive `lang` from `document_key`→`Source_lang`;
  diff-aware changed-cell selection; doc-scoped value index; section-aware prose match.

## Recommended order

`B (done) → E parity-alert (done) → C → A → E apply-on-promotion → D (ongoing)`.

B removed the silent-drift blind spot; E's read-only parity alert now runs it daily in
CI; C+A make dev→prod a single safe promotion; E's write half (apply-on-promotion) and
D (the two content-loop ends) are the remaining maturation.
