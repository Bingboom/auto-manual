# Product Intelligence Demo — Execution Plan

Status: Draft / implementation not started
Branch: `feat/product-intelligence-demo`
Scope: three phases, one integration branch, one PR; do not modify the README positioning or merge to main until reviewed.

## Objective
Consume approved, traceable product knowledge from Hello-Docs and connect it to externally sourced market/policy/competitor events. Present candidate product associations, evidence, uncertainty, hypotheses, and research revisions on an RTD preview page. This is a research surface, not an authoritative product specification.

## Phase 0 — Contract freeze (integration owner)
- [ ] Review `README.md`, `AGENTS.md`, product matrix, product knowledge, market policy, publication manifest, RTD builders and tests.
- [ ] Inventory authoritative sources and gaps; document the model/region/language/version selection limits.
- [ ] Freeze a versioned read-only product knowledge contract and event/association contract before parallel implementation.
- [ ] Define separate ownership of files and integration checkpoints; agents must not modify the same worktree simultaneously.
- [ ] Ensure event evidence cannot overwrite approved product content.

## Phase 1 — Product knowledge consumer interface (Agent A)
- [ ] Extract reusable read-only knowledge access without duplicating product matrix extraction or classification.
- [ ] Preserve product ID, market, language, source route, publication snapshot/version, evidence kind, and missing/unknown semantics where available.
- [ ] Separate facts derived from manuals, curated configuration, and capability switches.
- [ ] Keep existing product matrix/knowledge page output stable; add unit and regression tests.
- [ ] Document limitations: a preferred-language manual is not an exhaustive cross-market specification.

## Phase 2 — External event and association engine (Agent B)
- [ ] Reuse `market_policy.py` and existing records where appropriate; no second conflicting policy source.
- [ ] Model event ID, market, dates, source, verification, research question and update history.
- [ ] Implement explainable association rules over Phase 1 contract: market, category, capabilities and explicit evidence.
- [ ] Distinguish direct evidence, rule-based association, hypothesis and unknown.
- [ ] Support negative cases and evidence changes; no automatic claims of commercial impact.
- [ ] Include at least one sourced research case and an alternate case to demonstrate generality.
- [ ] Add tests for non-matches, missing evidence, unverified sources and recomputation.

## Phase 3 — RTD research preview (Agent C)
- [ ] Add an isolated experimental research page in existing RTD portal styling.
- [ ] Display research question, event, source status, candidate products, why matched, evidence links, hypotheses, open questions, and revision history.
- [ ] Ensure safe escaping, links only to real published routes, and useful fallback for missing evidence.
- [ ] Wire the page to the shared contracts, not copied/static hand-maintained product facts.
- [ ] Add build and UI tests; keep production manuals and workbench unaffected.

## Integration & review (integration owner)
- [ ] Integrate Agents A/B/C sequentially onto this single branch; parallel work should use separate worktrees or isolated commits.
- [ ] Run existing product matrix, market policy, RTD, and new tests.
- [ ] Verify no changes to authoritative production content and no duplicate product master data.
- [ ] Run RTD branch build and verify page, links, evidence, and responsive display.
- [ ] Test update scenario: product evidence/event change updates associations without silently rewriting historical research.
- [ ] Post preview URL and screenshots in PR when actually available.
- [ ] Keep PR in Draft until user reviews RTD branch preview; do not merge automatically.

## Parallel execution contract
Agent A owns product knowledge contract + extraction tests. Agent B owns event/association module + tests. Agent C owns RTD templates/assets + UI tests. Integration owner alone changes shared builders/registration and resolves contracts. A minimal contract must be agreed first; B/C can implement against fixtures while A completes.

## Preview deployment
Build RTD from `feat/product-intelligence-demo` using a separate preview version/project configuration where available. The existing RTD project may be private; do not change project visibility, production default branch, or public routes to expose the demo. A GitHub branch by itself does not automatically create a working RTD preview URL. Document the verified URL after the build succeeds.

## Out of scope
Crawling at scale, autonomous agents in production, Feishu writeback, graph databases, automated product specification edits, unverified sales forecasts, and changing Hello-Docs core positioning.
