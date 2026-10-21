# Product intelligence demo: discovery and v1 contracts

Status: active

This is the implementation contract for [PR #1579](https://github.com/Bingboom/auto-manual/pull/1579)
and its [execution plan](product-intelligence-demo-plan.md). It does not change
Hello-Docs positioning or the approved content production spine.

## Direction (2026-10-21)

External information is collected first and pushed for decisions; internal
product data must not gate it. An event is complete without any product data:
what happened, its sources and verification, the decision it asks for, who
decides and by when. Product association is an optional lens an event may ask
for, rendered as an appendix. A missing or broken product input degrades only
that lens; it never hides, delays or reshapes an event or its digest.

## Discovery (2026-10-20)

- The existing `tools/rtd/product_matrix.py` reads frozen publication manifests,
  selects a preferred-language manual per model, parses specification tables,
  classifies products from curated configuration and reads capability switches.
  That model-level aggregation must not become a cross-market fact source.
- `tools/rtd/product_learning.py` is a teaching surface. Its topic grouping is
  not evidence of a product capability or regulatory applicability.
- `tools/rtd/market_policy.py` validates the business snapshot under
  `docs/knowledge/market-policy/records.json`. Existing policy records are reused
  by ID; missing records stay unavailable. Event intake does not replace them.
- Engineering checkout has no frozen publication snapshot or business knowledge
  directory. Integration uses a separate copy of the clean Hello-Docs snapshot
  (observed commit `a728b1f1bf5632ed7471290c5a86041818de85da`), never a live Base query.
- Portal already separates internal combined sites from manuals-only sites.
  Experimental research is additionally opt-in and absent from public sites.

## Layer 1: external event intake (collection)

`tools.rtd.intelligence_events.load_events(knowledge_root)` reads the business file
`<knowledge_root>/external-intel/events.json`, beside `market-policy/records.json`,
and returns `schema_version: external-intel/v1`, `source` (path relative to the
knowledge root and byte SHA-256), `events`, `history` and `snapshot_id`. No file
is an empty intake; a malformed file raises `ValueError`. It reads no product data.

The file is `schema_version: external-intel-events/v1` with an `events` list.
Each entry has `id`, `title`, `kind` (policy/market/competitor), `market`,
`occurred_on`, `source_kind` and `revisions`, and optionally `product_lens`:

- `market_policy` entries name `source_record_id` and take status, summary,
  sources and boundary from that policy record; their revisions may not state
  those facts. A missing record shows as `missing`, never as intake text.
- `external_event` revisions carry `status` (verified/unverified/demand),
  `summary`, `boundary` and `sources`; verified needs an official HTTPS source.
  An unverified signal may be collected with no source.
- Every revision has `revision` (consecutive from 1), `recorded_on`, `reason`,
  `decision_question` and `review`; `decision_owner`, `decide_by`, `hypotheses`
  and `unknowns` are optional. Owner unset reads 待指派, a due date unset 未设定.
- Entry, revision, review and lens fields are allow-listed, so a revision cannot
  replace an event's identity, market or lens. The event is built field by field
  from the entry and its latest revision.

Reviewed revisions require a decision, reviewer and ISO review date. Later pending
revisions preserve earlier human judgments in history without inheriting approval.
`compare_event_snapshots(previous, current)` returns a new receipt; neither
snapshot changes and review stays pending.

## Layer 2: decision digest (push)

`tools.rtd.decision_digest.decision_digest(events, *, page, base_url="")` returns
`schema_version: external-intel-digest/v1`: one item per event, pending judgments
first, then by due date, latest record and ID. Items keep every field structured
for channel adapters (decision, verification, sources, open questions, page anchor
`#event-<id>` and an absolute URL when the site base URL is known). `text` is
CommonMark whose intake text is collapsed to one line with Markdown punctuation
escaped; unsafe source URLs are omitted. The digest contains no product data, and
building it sends nothing. Delivery (for example a Feishu card built from `items`)
is a separate, operator-run follow-up.

## Layer 3: optional product lens

`tools.product_knowledge.build_product_knowledge(root, srcdir, manifest_path,
assets, settings, catalog)` returns `schema_version: product-knowledge/v1`. The
manifest is read once through `production_evidence.publication_targets`; an
unreadable or malformed one raises `ValueError` naming only the file. Each product
is one model/region/language/publication variant with `id`, `model`, `region`,
`language`, `version`, `name`, `source` (route, manual, URL, SHA-256, build time,
Git reference and language scope), `category`, `specifications`, `capabilities`,
`relations` and `unknowns`.

A fact has `value`, `unit`, `state` (known/unknown), `source_type`, `evidence`
and `reason`; whole figures are integers. Evidence has `source_type`, `path`,
`url`, `sha256`, `locator`, `quote`; curated and registry evidence name the real
repository files and hash their bytes. `snapshot.inputs` records each input's
`path`, `base` (`repository` or `web_source`), `hash_of` (`bytes`, or
`parsed_catalog` for the catalog parsed from `index.md`) and `sha256`.
`vocabulary` lists the categories, registry columns and numeric facts a lens may
name. Warnings shared by every edition of a model appear once; any other names
the editions that raised it. Each manual is read once.

`tools.rtd.product_intelligence.product_lens_context(knowledge, events)` evaluates
only events with a `product_lens` (`catalog_markets`, `market_mapping_note`, and
a `rule` of `categories`, `required_capabilities`, `required_facts`). A rule term
missing from the vocabulary marks that lens `invalid` with its problems instead of
silently matching nothing. Associations carry `event_id`, `product_id`, status
(candidate/unknown/excluded), reasons, evidence, provenance and unknowns. Explicit
market/category/capability/evidence/verification gates replace keyword similarity;
unverified events cannot produce candidates. EU publication availability is not
proof of a country's sales or compliance. `compare_lens_snapshots` reports
knowledge, event, lens and association changes without touching either snapshot.

## Page, exports and ownership

- Intake and digest: `tools/rtd/intelligence_events.py`, `tools/rtd/decision_digest.py`,
  `tests/test_intelligence_events.py`, `tests/test_decision_digest.py`.
- Product lens: `tools/product_knowledge/`, `tools/rtd/product_intelligence.py`,
  `tests/test_product_knowledge.py`, `tests/test_product_intelligence.py`.
- Page: `tools/rtd/product_research.py`, its template/CSS/JS and Python/Node tests.
- Build: `tools/rtd/research_build.py` and the portal registration, with
  `tests/test_product_intelligence_build.py`.

The page route is `research/product-intelligence.html`, combined sites only.
Enable with Sphinx `rtd_product_intelligence_demo` or `RTD_PRODUCT_INTELLIGENCE_DEMO`
(true/false, 1/0, yes/no, on/off in any case); any other value is a configuration
error at start-up, whatever the site role. The research context is built once at
builder start, so every page links the research page only when it exists. A
malformed events file skips this page with a warning and no other page. The page
is an index of events in `decision_digest.decision_order`: each row shows market,
kind, title, decision question, owner, due date, verification and decision state,
and opens to what happened, sources, possible impact, open questions, human
judgment and revisions. The product lens is a collapsed appendix inside the event
stating whether it is not configured, unavailable, invalid or evaluated; unknown
and excluded variants are compact rows of their failing conditions. Server
rendering escapes text, validates links against actual publication routes and
prefixes element ids with `event-`. JavaScript adds quick tiles (all, pending,
judged, verified) and market, verification, decision and text filters; a deep
link opens its row.

Each build writes `_static/external-intel.v1.json`, `_static/external-intel-digest.v1.json`
and `_static/external-intel-digest.v1.md`, plus `_static/product-knowledge.v1.json`
and `_static/product-intelligence.v1.json` when a lens was computed. At HTML build
initialization only the page and these five exports are removed, so a disabled or
manuals-only rebuild in the same output directory cannot keep stale research.

No production templates, source tables, publication snapshots or GitHub workflows
are edited. No new service, crawler, graph database or dependency is required.

## Safety net and verification

1. Existing matrix/policy/portal behavior is characterized with focused tests;
   the shared helpers (`publication_targets`, `product_row`, optional review scan)
   keep the matrix and statistics pages unchanged.
2. Unit tests cover intake allow-lists, optional lenses and decision fields,
   policy joins, digest ordering and escaping, lens vocabulary problems,
   region/language boundaries, missing/false evidence and immutable history.
3. UI tests cover filtering, escaping, safe links, anchors and missing evidence.
4. Sphinx build tests cover lens unavailability, malformed events, flag errors,
   lens exports and stale-output cleanup.
5. Run Ruff, full unittest, Node tests, maintainability and documentation gates,
   and the US build check applicable to portal integration.
6. Verify the RTD project's repository, visibility and version before deploying
   a private branch preview. Report a URL only after successful build/readback.
