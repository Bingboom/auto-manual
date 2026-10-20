# Product intelligence demo: discovery and v1 contracts

Status: active

This is the implementation contract for [PR #1579](https://github.com/Bingboom/auto-manual/pull/1579)
and its [three-phase plan](product-intelligence-demo-plan.md). It does not change
Hello-Docs positioning or the approved content production spine.

## Discovery (2026-10-20)

- The existing `tools/rtd/product_matrix.py` reads frozen publication manifests,
  selects a preferred-language manual per model, parses specification tables,
  classifies products from curated configuration and reads capability switches.
  That model-level aggregation must not become a cross-market fact source.
- `tools/rtd/product_learning.py` is a teaching surface. Its topic grouping is
  not evidence of a product capability or regulatory applicability.
- `tools/rtd/market_policy.py` validates the business snapshot under
  `docs/knowledge/market-policy/records.json`. Existing policy records are reused
  by ID; missing records stay unavailable. Research recipes do not replace them.
- Engineering checkout has no frozen publication snapshot. Integration uses a
  separate copy of the clean Hello-Docs snapshot (observed commit
  `a728b1f1bf5632ed7471290c5a86041818de85da`), never a live Base query.
- Portal already separates internal combined sites from manuals-only sites.
  Experimental research is additionally opt-in and absent from public sites.

## Phase 1: read-only product knowledge

`tools.product_knowledge.build_product_knowledge(root, srcdir, manifest, assets,
settings, catalog)` returns JSON-serializable data. `root` is the engineering
repository, `srcdir` the frozen Web source, `manifest` its parsed manifest,
`assets` portal assets, `settings` parsed settings and `catalog` validated
publication catalog. Inputs are never written.

Top-level: `schema_version: product-knowledge/v1`, `content_sha256`, `snapshot`,
`products`, `warnings`. Hashes are deterministic and cover source inputs.
Each product is one model/region/language/publication variant:

- `id`, `model`, `region`, `language`, `version`, `name`;
- `source`: route, manual, URL, SHA-256, build time, Git reference and language scope;
- `category`: curated positioning; `specifications`: named numeric/text facts;
- `capabilities`: existing registry column names, scoped to the same region;
- `relations`: explicitly evidenced companion references; `unknowns`.

A fact has `value`, `unit`, `state` (known/unknown), `source_type`, `evidence`
and `reason`. Evidence has `source_type`, `path`, `url`, `sha256`, `locator`,
`quote`. Source types are `published_manual`, `curated_configuration` and
`capability_registry`. Missing is `null`, not false. Explicit registry false
remains registry evidence, not a statement quoted from a manual. Printed
revision and technical snapshot identity retain their distinct meanings.

## Phase 2: downstream research

`tools.rtd.product_intelligence.research_context(knowledge, knowledge_root,
*, cases_path=None)` returns `schema_version: product-intelligence/v1`,
`snapshot_id`, `knowledge_snapshot_id`, `events`, `associations`, `history`.
Cases contain event intake or existing policy IDs and research rules, never
copied product master data. The pure evaluator consumes Phase 1 only.

An event preserves ID, revision, geographic scope, dates, evidence, verification,
research question and review status. An association carries `event_id`,
`product_id`, status (candidate/unknown/excluded), reasons, evidence, hypotheses
and unknowns. Reasons label rule inference separately from direct evidence.
Explicit market/category/capability/evidence gates replace keyword similarity.
EU publication availability is not proof of a country's sales or compliance.
Unverified events cannot produce verified candidate claims. No output asserts
commercial impact, grid compatibility or legal eligibility.

Recomputation uses input/result fingerprints. Prior research and human decisions
remain distinct from current computed results; a simulation cannot impersonate
a past approval. Case metadata records pending human review and follow-up questions.
Reviewed revisions require a decision, reviewer and ISO review date. Later pending
revisions preserve earlier human judgments in history without inheriting approval.

## Phase 3 and integration ownership

- A: `tools/product_knowledge/`, `tests/test_product_knowledge.py`.
- B: `tools/rtd/product_intelligence.py`, event/rule helpers, research recipes,
  `tests/test_product_intelligence.py`.
- C: `tools/rtd/product_research.py`, its template/CSS/JS and Python/Node tests.
- Integration owner: portal registration, common shell/home links, JSON exports,
  integration tests, documentation, PR and preview verification.

Each worker uses its own managed worktree. Commits are integrated into the one
existing branch `feat/product-intelligence-demo`; PR #1579 remains Draft.
No production templates, source tables, publication snapshots or GitHub workflows are
edited. No new service, crawler, graph database or dependency is required.

The page route is `research/product-intelligence.html`. Enable with Sphinx
`rtd_product_intelligence_demo` or `RTD_PRODUCT_INTELLIGENCE_DEMO=1`, only on
`combined` sites. Page adapter:
`research_page_context(knowledge, research) -> dict`. Server rendering escapes
text and validates links against actual publication routes. JavaScript adds
filters, while the evidence remains readable without JavaScript.
At HTML build initialization, only the demo's page and two exports are removed.
This prevents stale research from surviving a disabled or manuals-only rebuild
in the same output directory; other output files are left intact.

## Safety net and verification

1. Existing matrix/policy/portal behavior is characterized with focused tests.
2. New unit tests cover region/language boundaries, missing/false evidence,
   unverified events, non-matches, source changes and immutable history.
3. UI tests cover filtering, escaping, safe links and missing evidence.
4. Run Ruff, full unittest, Node tests, maintainability and documentation gates,
   and the US build check applicable to portal integration.
5. Build a copied frozen publication snapshot with the branch's portal, verify
   page/JSON/evidence links and screenshots, and compare existing surfaces.
6. Verify the RTD project's repository, visibility and version before deploying
   a private branch preview. Report a URL only after successful build/readback.
