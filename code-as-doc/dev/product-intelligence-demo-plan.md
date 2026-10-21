# Product Intelligence Demo — Execution Plan

Status: active
Project: Research & Intelligence, a standalone research platform incubating on this branch ([charter](research-intelligence-charter.md)). The branch never merges into `auto-manual/main`; its core moves to its own repository.
Implementation: three phases integrated, then revised event-first (Phase 4), given a hand-run collection loop (Phase 5) and made a separable package (Phase 6); local validation complete; hosted RTD verification and the loop's operator trial pending.
Branch: `feat/product-intelligence-demo`, the incubation branch. PRs target it; none merges it into `main`.
Scope: the incubation branch and the PRs stacked on it; do not modify the README positioning.

## Objective
Collect externally sourced market/policy/competitor events and push them for decisions, without letting internal product data gate them. Each event carries its sources, verification, decision question, owner and due date; a push-ready decision digest is exported every build. Approved, traceable product knowledge from Hello-Docs is an optional lens an event may ask for, shown as an appendix with candidate associations, evidence and uncertainty. This is a research surface, not an authoritative product specification.

## Phase 0 — Contract freeze (integration owner)
- [x] Review `README.md`, `AGENTS.md`, product matrix, product knowledge, market policy, publication manifest, RTD builders and tests.
- [x] Inventory authoritative sources and gaps; document the model/region/language/version selection limits.
- [x] Freeze a versioned read-only product knowledge contract and event/association contract before parallel implementation.
- [x] Define separate ownership of files and integration checkpoints; agents must not modify the same worktree simultaneously.
- [x] Ensure event evidence cannot overwrite approved product content.

Discovery, source boundaries and implementation ownership are frozen in the
[v1 contract](product-intelligence-contract.md).

## Phase 1 — Product knowledge consumer interface (Agent A)
- [x] Extract reusable read-only knowledge access without duplicating product matrix extraction or classification.
- [x] Preserve product ID, market, language, source route, publication snapshot/version, evidence kind, and missing/unknown semantics where available.
- [x] Separate facts derived from manuals, curated configuration, and capability switches.
- [x] Keep existing product matrix/knowledge page output stable; add unit and regression tests.
- [x] Document limitations: a preferred-language manual is not an exhaustive cross-market specification.

## Phase 2 — External event and association engine (Agent B)
- [x] Reuse `market_policy.py` and existing records where appropriate; no second conflicting policy source.
- [x] Model event ID, market, dates, source, verification, research question and update history.
- [x] Implement explainable association rules over Phase 1 contract: market, category, capabilities and explicit evidence.
- [x] Distinguish direct evidence, rule-based association, hypothesis and unknown.
- [x] Support negative cases and evidence changes; no automatic claims of commercial impact.
- [x] Include at least one sourced research case and an alternate case to demonstrate generality.
- [x] Add tests for non-matches, missing evidence, unverified sources and recomputation.

## Phase 3 — RTD research preview (Agent C)
- [x] Add an isolated experimental research page in existing RTD portal styling.
- [x] Display research question, event, source status, candidate products, why matched, evidence links, hypotheses, open questions, and revision history.
- [x] Ensure safe escaping, links only to real published routes, and useful fallback for missing evidence.
- [x] Wire the page to the shared contracts, not copied/static hand-maintained product facts.
- [x] Add build and UI tests; keep production manuals and workbench unaffected.

## Integration & review (integration owner)
- [x] Integrate Agents A/B/C sequentially onto this single branch; parallel work should use separate worktrees or isolated commits.
- [x] Run existing product matrix, market policy, RTD, and new tests.
- [x] Verify no changes to authoritative production content and no duplicate product master data.
- [ ] Run RTD branch build and verify page, links, evidence, and responsive display.
- [x] Test update scenario: product evidence/event change updates associations without silently rewriting historical research.
- [x] Save verified local screenshots for the existing PR.
- [ ] Post the hosted preview URL after RTD verification.
- [x] Keep PR in Draft until user reviews RTD branch preview; do not merge automatically.

## Phase 4 — Event-first decoupling (2026-10-21)
Review direction: external information is collected first and pushed for decisions; it must not be constrained by internal products.
- [x] Move event intake to the business knowledge directory (`external-intel/events.json`, schema `external-intel-events/v1`); the engineering repository keeps only the test fixture.
- [x] Make the product rule an optional `product_lens`; events need no categories, capability names or catalog markets to be collected.
- [x] Add decision fields (`decision_question`, optional `decision_owner`, `decide_by`) and make hypotheses/unknowns optional.
- [x] Export an event-only decision digest (JSON + CommonMark) every build; delivery stays an operator-run follow-up.
- [x] Lay the page out as an event index in digest order: one row per event (market, kind, title, decision, owner, due date, states) that opens to its details, quick tiles over the filters, no slogan or explanatory header; the lens is a collapsed appendix inside the event with not-configured/unavailable/invalid/evaluated states and compact rows for unknown/excluded variants.
- [x] Degrade only the lens when product inputs fail; skip only this page when the events file is malformed; validate the flag once at start-up.
- [x] Fix review findings: revision allow-lists, real evidence paths and byte hashes, per-edition warnings, whole-number facts, lens vocabulary checks, anchor prefixes, shared manifest/row helpers, one read per manual, generic `preview/*` RTD rule that forces the flag off elsewhere.

## Phase 5 — Hand-run collection loop (2026-10-21)
Operator decisions: collect in a Feishu table; push to a Feishu group on workdays, right after a sync; capture decisions in the table; everything, decisions included, goes to Hello-Docs; no workflow change in this step. (2026-10-22: the storage choice is reopened; where the platform keeps its data is an open decision in the charter.)
- [x] Sync the 外部情报 table read-only into `events.json` as append-only revisions bound by `intake_record_id`; hand-written events are adopted by ID.
- [x] Count a judgment only when its 复核日期 is on or after the revision it judges; keep an unusable row's event at its last state and report it; never delete an event because its row is gone.
- [x] Push the digest as one Feishu post built from `items` (literal text, validated links): overdue, due within seven days, other pending, judgments recorded and rows to fix. Dry run by default; `--write --push` writes then sends.
- [ ] Live integration before Bingboom/auto-manual#1585 merges, as the bot on a test table and group: table read, judgment round trip, push with read-back and the Markdown view ([runbook and record](../tests/external_intel_live_integration_2026-10.md)).
- [ ] Operator trial on the real table after that merge: create the table, give the bot read access and group membership, run a dry run, then `--write --push`. Where `events.json` is committed waits on the charter's storage decision.
- [ ] Schedule the loop on workdays (workflow, content PR, push after sync): a separately approved workflow change.

## Phase 6 — Separable package (2026-10-21)
Operator direction: the demo must later be easy to decouple and run on its own. Reviewed `nashsu/llm_wiki` for ideas; it is GPL-3.0, so only its design may be borrowed, never its code.
- [x] Move intake, digest, sync, push and CLI into `tools/intel/`: standard library and relative imports only, with its own lark-cli transport, table reader and policy reader. Feishu calls, policy records and the date are passed in.
- [x] Keep the research page, Sphinx build, product lens and the portal's stricter policy reader in the host; the RTD build passes `market_context` records to the package.
- [x] Guard it: an import scan of the package and its tests, a run of a copy with nothing else from this repository on the path, and checks of the package's parallel readers and page route against the host's.
- [x] Prove behavior unchanged: CLI outputs, the written intake and the five research exports and page are byte-identical before and after on the same real input.
- [x] Borrow from llm_wiki, first step: a generated Markdown view (`python -m tools.intel wiki`) with `index.md`, `overview.md`, `log.md`, event and market pages, and `purpose.md`/`schema.md` templates that people own. It opens in Obsidian and llm_wiki, is byte-stable for an unchanged intake and has a `--check` mode.
- [ ] Next llm_wiki steps, each its own change: rule-based health checks folded into the push, then LLM-drafted intake that a person confirms.

## Phase 7 — Repository decoupling (2026-10-22)
Operator decision: Research & Intelligence is a standalone research platform incubating on this branch, which never merges into `auto-manual/main`. The [charter](research-intelligence-charter.md) holds the rules, who owns each part and the migration route. This plan ends at the route's step 2, finishing Bingboom/auto-manual#1585; the later steps are tracked in the charter.

## Parallel execution contract
Agent A owns product knowledge contract + extraction tests. Agent B owns event/association module + tests. Agent C owns RTD templates/assets + UI tests. Integration owner alone changes shared builders/registration and resolves contracts. A minimal contract must be agreed first; B/C can implement against fixtures while A completes.

## Local acceptance (2026-10-20, before Phase 4)

These results and captures describe the product-first layout that Phase 4 replaced.

- Frozen business input: `a728b1f1bf5632ed7471290c5a86041818de85da`;
  138 publication variants across 12 language tags.
- Two sourced cases produce 6 candidates, 46 unknowns and 224 exclusions.
  The Netherlands candidates are EU variants; the US candidate is a US variant.
  Most unknowns reflect the existing extractor's limited non-English coverage,
  not a finding that those products lack the capability.
- Both JSON exports bind the same knowledge fingerprint. Every local evidence
  link in the rendered research page resolves to an existing output.
- A simulation removes output-power evidence only from a copied US knowledge
  record: its association becomes unknown, while the prior result/history stays
  unchanged and human review remains pending.
- Browser checks cover market filtering, zero results, reset, the matching
  published manual, and mobile navigation/layout with no horizontal overflow.
  Review captures: [desktop](../reviews/product-intelligence-demo/desktop.jpg)
  and [mobile](../reviews/product-intelligence-demo/mobile.jpg).
  These show the local build, not a hosted RTD deployment.
- Tests also rebuild the same output directory with the demo disabled and with
  the public manuals role; the three research artifacts disappear and unrelated
  files remain.
- Validation passed: full unittest (5,664 tests, 67 skipped, canonical
  `TMPDIR=/private/tmp` on macOS), final focused suite (54 tests), all Node UI
  tests (42), full Ruff, maintainability guardrails, document links, and
  `build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
  --data-root tests/fixtures/phase2`.

## Preview deployment
RTD enables the demo only for `preview/*` branches and forces it off for every other version, `latest` included. The preview carrier must also carry `docs/knowledge/external-intel/events.json` (seeded from `tests/fixtures/external_intel/events.json`); without it the page shows its empty state.
Build RTD from `feat/product-intelligence-demo` using a separate preview version/project configuration where available. The existing RTD project may be private; do not change project visibility, production default branch, or public routes to expose the demo. A GitHub branch by itself does not automatically create a working RTD preview URL. Document the verified URL after the build succeeds.

The existing private RTD project is bound to `Bingboom/Hello-Docs`, not the
engineering repository. A preview carrier may combine the exact engineering
commit and the frozen business snapshot on `preview/product-intelligence-1579`
in the Hello-Docs mirror. That GitHub repository is public; the RTD project's
private access is a separate setting. Generated research HTML/JSON are not
committed to the carrier. It is a deployment artifact, not another implementation
PR; record both source commits and enable the demo only on that carrier. Do not
change either repository's `main`, the RTD default version or project visibility.

Hosted verification remains pending: the signed-in Chrome session became
unavailable because the Mac is locked. No successful RTD build or hosted preview
URL is claimed until the operator unlocks it and the branch build is read back.

## Out of scope
Crawling at scale, autonomous agents in production, Feishu writeback, graph databases, automated product specification edits, unverified sales forecasts, and changing Hello-Docs core positioning.
