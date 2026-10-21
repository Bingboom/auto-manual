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
- `intake_record_id` (optional, unique, `rec…`) names the Feishu table row an
  event is synced from; it is carried to the event and the digest item as the
  row link, and is absent from hand-written events.
- A synced revision optionally carries `intake_judgment_sha256`, the canonical
  SHA-256 of the observed judgment triple (or null when the cells are empty).
  This input marker is not approval and is not exported as public review metadata;
  it prevents an unchanged stale judgment from approving a later fact version.

Reviewed revisions require a decision, reviewer and ISO review date. Later pending
revisions preserve earlier human judgments in history without inheriting approval.
`compare_event_snapshots(previous, current)` returns a new receipt; neither
snapshot changes and review stays pending. `events_snapshot(payload, knowledge_root)`
builds the same snapshot from file bytes, and `encode_intake(document)` gives the
bytes a document is written as, so a sync candidate hashes as it will be committed.

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

## Collection loop: table sync and group push (hand-run)

`tools.rtd.intelligence_sync` reads the Feishu 外部情报 table, one row per event,
through `workspace_snapshot.complete_rows` (complete pages or nothing); a table
missing any column of `COLUMNS` raises `TableShapeError`. It never writes the
table. `merge(previous, rows, *, today, policy_ids=None)` returns a new intake
document and a report, leaving both inputs unchanged:

- A row's event is the one bound to its record (`intake_record_id`), else the
  event with the row's 事件ID when it is hand-written or its row is gone
  (adopted with its history), else a new event with that ID or `ev-` plus ten
  hex digits of the record ID's SHA-256. Event ID, source kind and policy record
  are fixed once synced.
- A revision is appended only when the row's facts (decision fields; status,
  summary, boundary and sources for an external event) or its judgment changed.
  It is dated `today` (the sync date, China Standard Time) and its reason is the
  row's 变更说明 when that changed, else a default. Title, kind, market and
  occurrence date update the entry without a revision; rows never touch
  `product_lens`.
- A new complete judgment counts only when its 复核日期 is on or after the
  latest factual revision. Review-only syncs do not move that date or expire an
  accepted judgment. Unchanged judgment cells never approve changed facts, even
  on the same day; the observed input hash keeps later retries pending. An
  explicit edit to the judgment, reviewer or review date reconfirms it (the date
  gate still applies). Clearing all three cells and syncing before refilling
  them is also an explicit new judgment. Legacy revisions remain readable.
- The report names each row's change (`added`, `revised`, `judged`, `reopened`,
  `relabelled`) and counts `unchanged`. A row that cannot be used is a `problem`
  and its event keeps its last state; a stale judgment or a policy ID missing
  from `policy_ids` is a `notice`; an event whose row is gone is kept and listed
  in `gone`. An invalid previous intake, or a `today` before its newest
  revision, raises `ValueError`.

`tools.rtd.intelligence_push.post_content(digest, *, today, record_url, page_url,
report)` builds one Feishu post from the digest `items`: pending events grouped
overdue, due within seven days, then the rest (at most `MAX_LISTED`, text cut at
`MAX_TEXT`), the judgments a sync recorded and the rows to fix. Intake text is
only ever a literal text element. Only validated HTTPS URLs become links, and a
row link is the operator's `record_url` with a checked record ID. It returns
`None` when nothing is pending and the report is empty. `send` runs `lark-cli im
+messages-send --msg-type post` with an idempotency key derived from chat,
content and day; its receipt names no chat.

`python -m tools.rtd.intelligence_loop sync|push` is the hand-run entry: `sync`
is a dry run unless `--write`, and `--push` sends right after a written sync (it
only prints after a dry run). Transport errors carry the command line, so only
their type is printed. Configuration comes from flags or `FEISHU_EXTERNAL_INTEL_*`
and `EXTERNAL_INTEL_SITE_URL`; nothing secret is written to a file. No workflow
runs the loop yet; scheduling it is a separate, approved workflow change.

`tools.rtd.intelligence_delivery` persists a single pending message per knowledge
checkout under `~/.cache/auto-manual/external-intel/<checkout-hash>/pending.json`
(root override: `EXTERNAL_INTEL_STATE_DIR`), outside the business content tree.
Before replacing events.json or sending, it atomically saves the exact message,
original day/key/snapshot, candidate intake and expected parent hash. Only a hash
of chat/profile/identity is kept; raw transport configuration is not persisted.
Message links and intake remain business data and belong only in this local
runtime cache, never an artifact published or committed to Hello-Docs.

A retry first recovers the saved candidate when the file still matches its
expected parent, then replays the saved message with its original key; it never
rereads the table or rebuilds the report first. Another destination/profile or a
newer operator edit stops the retry without overwriting or sending. A nonempty
message acknowledgment clears the pending file; failure or missing acknowledgment
retains it. `push --dry-run` previews it without writing; `push` or
`sync --write --push` resumes it. Run sync again after recovery for newer rows.
Feishu's idempotency window is one hour; retries beyond it can duplicate a send
whose acknowledgment was lost, even with the same saved key.

## Page, exports and ownership

- Intake and digest: `tools/rtd/intelligence_events.py`, `tools/rtd/decision_digest.py`,
  `tests/test_intelligence_events.py`, `tests/test_decision_digest.py`.
- Product lens: `tools/product_knowledge/`, `tools/rtd/product_intelligence.py`,
  `tests/test_product_knowledge.py`, `tests/test_product_intelligence.py`.
- Page: `tools/rtd/product_research.py`, its template/CSS/JS and Python/Node tests.
- Build: `tools/rtd/research_build.py` and the portal registration, with
  `tests/test_product_intelligence_build.py`.
- Loop: `tools/rtd/intelligence_sync.py`, `tools/rtd/intelligence_push.py`,
  `tools/rtd/intelligence_loop.py`, `tools/rtd/intelligence_delivery.py`, with `tests/test_intelligence_sync.py`,
  `tests/test_intelligence_push.py` and `tests/test_intelligence_loop.py`.

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
are edited; the loop reads its own table and sends one group message per run. No
new service, crawler, graph database or dependency is required.

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
