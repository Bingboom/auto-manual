# RTD manual-center entrance

## Discovery and implementation plan

Operator accepted the local card/search design and requested RTD implementation,
with **EU temporarily the default**, on 2026-09-12. Region options remain
US / EU / UK. EU and UK share existing EU publications; no UK copy is created.

Verified baseline: engineering main `ff5e3556`; RTD listens to Hello-Docs/main
and renders frozen `docs/publish/web` with Sphinx/Furo. The frozen config does
not load engineering extensions. Editing only the assembler would not update
already published snapshots. The live index has 21 entries (US 1, EU 20).

Implementation phases:

1. Add a root-only Sphinx portal extension, a catalog adapter over the existing
   frozen index, and the accepted responsive template/styles. No live requests
   or body duplication. Keep ordinary links usable without JavaScript.
2. Enable the extension in both RTD build paths, without modifying frozen
   sources, GitHub workflows, review content, dependencies or public build CLI.
3. Test EU default, shared EU/UK links, search, missing-language states, safe
   assets/URLs, existing non-portal regions and unchanged manual rendering.
   Run syntax/lint, targeted and full unit tests, guardrails, link check, the
   build quality check, then real Sphinx baseline/new builds of the same frozen
   corpus. Only the home and portal-specific static files may differ.
4. PR in auto-manual, gate-on-green only with current authorization, mirror to
   Hello-Docs, and verify the actual RTD page. Do not call a local build online.

Non-goals: independent twelve-language publication storage, new translations,
IR/print changes, online Base writes, product facts, and advertising removal.
Existing bundled languages remain accessible through their original manual.
Only verified independent locale links may be enabled; do not construct URLs
by replacing a language suffix. Product illustrations come from each frozen
manual's packing-list product asset; missing packing-list images may use an explicit model/market artwork fallback;
unconfigured cards remain model-only.

The root template keeps an EthicalAds placement for RTD. No CSS hides platform
advertisements. Other markets remain accessible in an all-publications fallback
even though the primary dropdown is limited to US/EU/UK.

## Catalog validation during a build

The frozen publication catalog is validated once per Sphinx build and reused
by page rendering and the search-index writer. This avoids re-reading all
publication evidence for every generated page. Validation still fails closed;
no content or evidence checks are skipped. The cache belongs to the Sphinx
application, is prepared before parallel writers start, and is cleared on both
successful and failed builds so later builds revalidate their inputs.

Local verification on the Hello-Docs `2818de85` frozen snapshot (2026-09-20):
207 source documents took about 214 seconds before the change and 6.7 seconds
afterwards. All 219 output HTML files were byte-identical. Of 1,103 output files
excluding doctrees, only `.buildinfo` and its hash in `manual-deployment.json`
differed because the isolated test used an explicit knowledge-directory override.
These are local measurements, not a Read the Docs runtime guarantee.

## Personal workspace entry

The manual-center root remains independent. The portal extension also builds
`/workspace/` as a neutral Chinese entry page for two separately maintained
personal interfaces:

- **AI 分享** opens the bundled beginner-facing AI sharing package at
  `/ai-share/00_打开分享.html`.
- **工作资料** opens the manual library for product, region, language
  and manual-content search.

The sharing package is owned by **Hello-Docs** under
`docs/knowledge/ai-share/`; it must not be committed to auto-manual.
The extension reads that directory and copies it into the RTD HTML output.
For isolated local previews, set the Sphinx config `rtd_knowledge_dir` to the
Hello-Docs knowledge directory. HTML pages retain their `noindex,nofollow` metadata.
The engineering sync preserves both `docs/publish/` and `docs/knowledge/`.
Deploy that sync protection before merging content into Hello-Docs main.
Maintain sharing content through a Hello-Docs content PR; keep templates and
build code in auto-manual.
Relative links between the main share, demonstrations, reference pages and SVG
figures therefore keep working without another host. The two interfaces share
the RTD project's visibility settings; the workspace path is navigation, not a
separate access-control boundary.

The workspace itself exists in every portal build: the manual center always
links to it, and the system page lives inside it. The sharing package is an
optional entry. Without `ai-share/00_打开分享.html`, the workspace hides the
share navigation link, card, search box and update line, and the system page
hides its share link. Nothing else changes. With the package present, both
pages are byte-identical to the earlier behaviour.

Rollback: revert the portal extension's RTD activation and rebuild. Frozen
content, QR aliases and nested manual URLs are unchanged.

## System workspace page

`/workspace/system/` (系统建设) opens with the current focus: the lanes being
ordered by delivery priority, each with its next action and ledger progress.
Stage acceptance follows immediately; corpus statistics, capabilities and evidence
remain available further down the page. The page is built at RTD time from
frozen inputs only. The build never contacts Feishu or GitHub; browser version
checks read only the already-published same-origin receipt.

- `tools/rtd_portal_assets/system_workspace.yaml` is the curated status
  contract: focus lanes, capability cards, production-flow links, gate labels
  and entry links. It is maintained in auto-manual and reaches Hello-Docs
  through the mirror.
- `docs/publish/publish_manifest.json` is the source of the publication counts.
  It uses the REV-04 caliber: a book is one model × region, and language
  editions are counted separately.
- The execution ledger named by `now_next.source` supplies REV statuses, the
  gate composition and each lane's progress. The page reads them and never
  restates a REV status.
- The skeleton blueprints under `docs/manifests/skeletons/*/blueprint.yaml`
  say which product families already generate their manual structure from a
  skeleton. The mirror carries them, so RTD reads the same files.
- The agent skills under `.agents/skills` and `.claude/skills`, the Claude Code
  hooks in `.claude/settings.json` and the steps of `.githooks/pre-push` feed
  the skills and hooks block; see [Skills and hooks](#skills-and-hooks).
- `tools/rtd_portal_assets/source_registry.yaml` is the source registry. For
  every data domain on the page, it records where the fact is decided, how it
  is read, how fresh it must be and what shows without it. The page takes its
  snapshot names, freshness limits and fallback text from it, and lists it
  publicly as 数据来源; see [Source registry](#source-registry).

The page is public, on the same RTD project as the manuals. `noindex` is not
access control, so the contract holds only publishable facts. Gap narratives
and resource needs belong to the Feishu internal page, not this file. The
workspace sidebar shows the entry only when the page was built.

### Current focus

The operator decides the focus. Since 2026-09-26 the sequence is:

1. Web publication and real maintenance: REV-07 → REV-09 → G1 acceptance → G2 pilot.
2. Corpus reuse and SSOT support that work concurrently. REV-18 checks actual
   translation hits/corrections; source authority, writers, approvers and frozen
   release inputs are established as real data needs arise.
3. Shared IR: settle REV-39 boundaries, then accept a representative REV-40 target
   and its dependencies before expansion. IDML acceptance does not block Web.
4. Expand skeletons and coverage once production and maintenance are stable.
5. Multi-agent work remains a design reference, reconsidered only after persistent
   handoff or concurrency bottlenecks. It is absent from the current-work list.

This page order does not rewrite ledger statuses or claim those gates are complete.
Each lane in `focus.lanes` declares:

- `id`, `title`, optional `goal` and `action`, and
  `horizon: now | support | next | later | deferred`;
- `card`: the capability card it links to. That card, and every gate the lane
  lists, carries the lane's tag further down the page;
- `items`: capability items shown with their status inside the lane;
- `metrics`, computed at build time:
  - `publications`: books and language editions from the publish manifest;
  - `regions`: books per region, labelled by `focus.regions`;
  - `corpus`: sentence pairs, terms and approved share from the corpus snapshot;
  - `skeletons`: blueprints per family, in `focus.skeleton_families` order, with
    未建 for a declared family that has none;
- progress: `gates` (ids from `now_next.gates`), `revs` (ledger rows, ranges
  allowed), or both. A lane with neither shows 尚未入执行台账, except a deferred
  design reference, which intentionally carries no execution progress.

A source that cannot be read shows 无数据 for that figure, never zero. The focus
block carries evidence like any other entry, and it goes stale with
`verified_on`, so re-confirm it with the operator at each re-check.

Cards and gates outside the focus can set `fold: true`. They then render in a
collapsed 其他能力 or 其他阶段门 group at the end of their section.

### Published version and refresh

Every main merge already triggers the engineering mirror into Hello-Docs/main;
RTD then rebuilds the page from that checkout. No second scheduler or browser
GitHub token is needed. A successful mirror is not evidence of successful RTD
publication: diagnose the mirror run first, then the RTD build and served page.
If the mirror is current but RTD has no build for that commit, inspect Hello-Docs
Settings → Webhooks → Recent deliveries. Redeliver only the failed main-push
notification (for example an HTTP 502), then verify the resulting RTD build SHA,
success and served page. A webhook returning 200 is only trigger acceptance.

`tools/rtd_workspace_revision.py` stamps the HTML and
`_static/system-workspace-revision.json` with the same checkout SHA and UTC build
time. On RTD the SHA belongs to the Hello-Docs checkout, not auto-manual/main.
The page displays that identity. Its JS probes only the same-origin deployed
receipt on entry, every minute while visible, and on returning to the tab.
A different, later-built receipt offers **刷新到新版本**, preserving the URL anchor
and adding a version query to avoid a stale cached page. It does not interrupt
reading automatically. Older receipts, malformed responses, timeouts and offline
states never trigger navigation; the current snapshot remains readable. JS/CSS
URLs include the checkout version. This check confirms the deployed page version,
not that the deployed version has caught up with GitHub main.

Ledger, tooling and skeleton changes appear on the next successful build.
Capability claims still require curated evidence. Corpus/Feishu counts remain
frozen snapshots and only change after their reviewed export is committed;
a main merge does not read live tables or automatically approve capabilities.

### Language assets block

The page also shows the translation memory's scale and per-language coverage:
sentence pairs, terms, languages covered, the approved share, and one bar per
language. Each bar is corpus coverage: the sentence pairs that carry a
translation in that language, as a share of all sentence pairs in the memory.
It is not manual localization completion, and the page says so under the
chart; online manuals per language belong to the web lane. The numbers come from `tools/rtd_portal_assets/system_workspace_corpus.json`,
an aggregate snapshot that holds counts only, never corpus text. The build
never reads Feishu. Refresh the snapshot monthly through a PR:

```bash
python tools/rtd_system_workspace.py corpus-export
```

The command reads the live TM base (`$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN`)
and writes the snapshot next to the contract. It is read-only. Pass
`--cli-bin "lark-cli --profile prod" --as bot` for the bot lane. The contract's
`corpus.languages` list fixes the languages counted and their labels; a column
missing from either table fails the export instead of counting zero.

Each export carries the earlier months forward in `history`: one headline per
month (sentence pairs, terms, approved), oldest first, up to 24 months. The
page compares the current figures with the latest of them. A second export in
the same month replaces that month's figures. If the snapshot being replaced
cannot be read or is malformed, the export stops, so history is never dropped.
A language added to the contract later does not block the carry.

A snapshot older than the `stale_after_days` of the source registry's `corpus`
domain (45) shows 待复核. The registry also names the snapshot file. An
unreadable or malformed snapshot shows 无数据 for this block only, with a
Sphinx warning; the rest of the page still renders. `check` reports both
cases.

### Skills and hooks

The 技能与钩子 block lists what agents can call and what runs automatically.
It is read from the tree at build time (`tools/rtd_system_tooling.py`), and
none of it is hand-listed.

- **Skills**: one row per skill directory, merging the Codex copy
  (`.agents/skills/<name>/SKILL.md`) and the Claude Code copy
  (`.claude/skills/<name>/SKILL.md`). The row shows the first sentence of the
  frontmatter `description`; the full text is the tooltip.
  - A Codex copy needs frontmatter `name` equal to its directory.
  - A Claude copy may omit `name`, because Claude Code uses the directory name.
  - Every copy needs a `description`.
- **Registration**: a Codex copy must be linked from `AGENTS.md` §7, and a
  Claude copy must be listed in `.claude/skills/README.md`. Unregistered copies
  show 未登记.
- **Lanes**: `tooling.skill_lanes` in the contract maps skills to focus lanes,
  and an empty list shows that the lane has no skill yet. Unmapped skills are
  listed under 其他技能.
- **Hooks**:
  - Claude Code hooks come from `.claude/settings.json`, and git hooks from the
    steps of `.githooks/pre-push`. An `exec` step blocks the push (拦截); the
    others only advise (提醒).
  - A hook counts as tested when `tests/test_<script>.py` exists. Its purpose is
    the first line of the script's module docstring.
  - Git hooks run only where `core.hooksPath` points at `.githooks`, and the
    page says so.

`check` warns about unregistered copies, frontmatter gaps, missing hook scripts
and hooks without tests. A lane mapping that names a missing skill is an error.

### Source registry

`tools/rtd_portal_assets/source_registry.yaml` registers each data domain the
workspace pages show, once. It is REV-44, the single source of truth for where
each fact comes from; the design is in
[ssot_source_registry_design.md](ssot_source_registry_design.md). Each domain
records:

| Field | Meaning |
| --- | --- |
| `authority` | where the fact is decided: a `file:<repo>:<path>` ref, or text, such as a Feishu table named by its environment variable (never a token) |
| `read` | `build` (read at build time) or `snapshot` (a committed JSON file) |
| `snapshot`, `refresh` | the snapshot next to the registry, and the read-only command that rewrites it |
| `stale_after_days` | a snapshot's age limit, or an entry review cycle, after which the page shows 待复核 |
| `fallback` | what the page shows when the source cannot be read |
| `used_by` | the page blocks that show the fact |

- The system page and the deliverables page take snapshot names, freshness
  limits and fallback text from the registry. None of them is written in page
  code or in the status contract any more.
- The system page lists every domain publicly under 数据来源, with each
  snapshot's date, and 待复核 once a snapshot is past its limit.
- `check` fails on an unsound registry, an unregistered page domain, or a
  `file:auto-manual:` authority that does not exist. It warns about a stale or
  unreadable snapshot.
- An unsound registry is an authoring error. The system page drops out with a
  Sphinx warning, and the deliverables page shows its Feishu columns as 无数据.
- Agents look a fact's authority up here instead of keeping their own copy.
  Multi-agent dispatch (REV-45) builds on this.

### Status rules

- One vocabulary: `available`, `validated`, `in_progress`, `planned`,
  `blocked`, `retired`, `no_data`, defined in the contract. Flow links also
  carry `mode: automated | manual`.
- Every entry carries evidence: `pr:<repo>#<n>`, `file:<repo>:<path>`,
  `url:<https-url>`, `rev:REV-nn=<ledger status>` or
  `ack:<who> <YYYY-MM-DD>「quote」`. An operator ack is never the only evidence.
- `planned` must cite a REV row. Ideas that are not registered do not go on the
  page.
- A card may not claim more than its weakest implemented item (`available`,
  `validated` or `in_progress`). It may be set lower by hand.
- `retired` entries are removed, not shown.
- The contract text states no quantities; `check` warns when it does.

### Drift and failure behaviour

- Drift still renders. A cited file that no longer exists, a REV whose ledger
  status moved, or an entry older than the review cycle of the source
  registry's `capabilities` domain (30 days) shows **待复核**, with the reason
  as a tooltip.
- An authoring error drops only this page, with a Sphinx warning. Examples are
  an unknown status, a card above its ceiling, broken evidence syntax, a gate
  REV that the ledger does not name, or an unsound source registry. The manual site keeps building, and
  the sidebar hides the entry.

### Maintaining the contract

Edit the YAML in an auto-manual PR. Update `verified_on` when you re-check the
entries, then run:

```bash
python tools/rtd_system_workspace.py check
python tools/rtd_system_workspace.py check --online
```

The first command works offline and checks the rules, evidence files, REV ids
and drift. `--online` also confirms that cited PRs are merged and that URLs
answer 200.

Offline, `file:hello-docs:` refs resolve only inside a tree that carries
`docs/publish`; `--online` checks them against Hello-Docs `main` instead.
The unit suite runs the offline check against the shipped
contract, so deleting a cited file fails CI in the same PR. A moved REV status
is only a warning: the page shows 待复核 until the contract is re-checked.

Verification (2026-09-24): full Sphinx builds of Hello-Docs `main` `3dededf7`
(54 language editions, 22 books) were made with and without this change. They
differ in exactly two added files, `workspace/system/index.html` and
`_static/system-workspace.css`, and in three changed files:

- `workspace/index.html`: the one sidebar line;
- `manual-deployment.json`: entries for those files;
- `.buildinfo`: the config hash.

230 of 231 HTML pages are byte-identical, and neither build emits a warning.

Verification (2026-09-25, focus lanes): full builds of Hello-Docs `main`
`9745093a` (1,195 files) with `main` `367bd444` and with this change differ in
four files: `workspace/system/index.html`, `_static/system-workspace.css`,
their entries in `manual-deployment.json`, and the `.buildinfo` config hash.
The hash moves because the two trees sit at different paths. 231 of 232 HTML
pages are byte-identical, and neither build emits a warning.

Rollback: revert the change. The workspace entry, manual URLs and QR aliases
are unaffected.

## Deliverables page

`/workspace/deliverables/` (交付物) gathers the links to what the pipeline has
delivered in one table. It is grouped by model, with one row per region and one
column per format:

| Column | What it links to | Source |
| --- | --- | --- |
| 网页手册 | each language edition's page on this site | `docs/publish/publish_manifest.json`, read at build time |
| 印刷交付包 (IDML + PDF) | the Publish handoff ZIP in the Feishu wiki | the build table's `idml_file` column, through the snapshot |
| Word 云文档 | the Draft Word output, imported as a Feishu cloud doc | the build table's `飞书云文档` column, through the snapshot |

- Each cell holds one chip per language, with its version. 整本 marks a
  whole-book document that carries all its languages in one file.
- The PDF has no link of its own: it ships inside the handoff ZIP, and the
  publish tree refuses PDF files.
- Two selects filter the table by model and by region. On a phone, each region
  becomes a card with the formats stacked.
- Product names come from the manual center. A model that the manual center
  does not list shows its code only. The build table's own product names are
  not used, because some of them are wrong or empty.

The Feishu links open only for signed-in Feishu users, but their addresses are
public on this page. The operator chose this on 2026-09-25 (「直接放飞书链接」).
The page accepts only https links on a Feishu or Lark host.

### Refreshing the Feishu snapshot

RTD never reads Feishu, so the two Feishu columns come from
`tools/rtd_portal_assets/deliverables_snapshot.json`, the snapshot of the
source registry's `deliverables_feishu` domain. Refresh it through a PR
after new Draft or Publish builds:

```bash
python tools/rtd_deliverables.py export --cli-bin "lark-cli --profile prod" --as bot
python tools/rtd_deliverables.py check
```

`export` is read-only. It reads two tables in the base named by
`$FEISHU_PHASE2_BASE_TOKEN`:

- the build table, `$FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID`;
- the Document_key table, `$FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID` (the
  model-capabilities table is the Document_key table).

It keeps the highest version for each model, region, language and format. It
skips rows without a resolvable key or without a Feishu link. A missing column
fails the export instead of silently dropping a format.

### Failure behaviour

- Without a publish manifest, the web column is empty and the page says
  发布清单当前不可读.
- An unreadable or unsound snapshot empties the two Feishu columns only, with a
  Sphinx warning.
- A snapshot older than the registry's limit (45 days) shows 待复核, and
  `check` warns about it.
- The page always renders. The workspace and system pages link to it from their
  sidebars, and the workspace's 最近更新 list links to it too.

## Maintenance surface

Product improvement suggestions use an independent opt-in `product_voc_endpoint`
and narrow bot receiver; see [product VOC](product_voc.md). This is not the
documentation issue channel below. RTD only builds the form; it never reads
Feishu credentials or runs the receiver.

- `tools/rtd_portal.py` reads explicit frozen index links and only existing
  local packing-list product assets. It does not scrape the live website.
- `tools/rtd_portal_assets/settings.json` owns the temporary default, entrance
  bindings, category-prefix presentation rules and twelve planned labels.
  These category rules are navigation hints, not new product master data.
- `.readthedocs.yaml` activates the extension for frozen and bootstrap builds.
  This is needed for old frozen configs as well as future publications.
- The portal template renders real links before JavaScript; scripts only enhance
  filtering and the language dialog. The search template keeps Sphinx's native
  result container and scripts, and adds a visible query form so a direct visit
  to `/search.html` is usable before a query is present. Alias and manual bodies
  remain unchanged.
- Feedback is configured by `feedback_channels` in
  `tools/rtd_portal_assets/settings.json`. The consumer-facing channel is the
  after-sales mailbox `hello@jackery.com` already printed in shipped manuals
  (growth-plan decision D2); [GitHub Issues](https://github.com/Bingboom/auto-manual/issues)
  remains the internal/dealer triage board and is no longer linked on manual
  pages. Setting the list to `[]` disables the block. Channels are
  fixed HTTPS URLs without query strings, fragments or credentials, or a
  single plain `mailto:` address without headers or extra recipients. When
  enabled, a single-language page shows frozen model/region/language/version
  and relative page context for the user to copy; it never sends context or
  adds user identity to a link. The visible text block remains the no-JS
  fallback.
- Optional visit analytics is configured by `analytics_beacon_token` in
  `tools/rtd_portal_assets/settings.json` and defaults to `""` (off,
  byte-identical output). A configured token must be 32 lowercase hex
  characters and enables the cookieless Cloudflare Web Analytics beacon on
  the portal root and single-language manual pages; the token is the only
  payload, and the beacon collects no cookies or user identity under the
  operator's Cloudflare account. Growth-plan decision D1 selected this
  channel; activation is a separate settings change once the operator
  creates the Web Analytics site and provides its token. Activated
  2026-09-15 for the `ht-doc.readthedocs.io` Web Analytics site (custom
  domain deferred): the committed token is that site's public identifier,
  embedded verbatim in every rendered page by design — not a Cloudflare
  API credential. Token self-service: Cloudflare → Analytics → Web
  Analytics → Manage site → Install JS Snippet. Collection starts after
  the next RTD publish; verify by viewing page source for the beacon and
  the Web Analytics dashboard for visits.
- Page head metadata is derived, never hand-written: on verified
  single-language pages the extension sets a search-legible `<title>`
  (product name, model, market, language), meta description, Open Graph
  tags, canonical and a self-inclusive `hreflang` group — all computed from
  the frozen publication identity and the catalog's `language_options`.
  Absolute URLs come from `site_base_url` in the portal settings (a bare
  HTTPS origin; empty omits canonical/hreflang/og:url) — this is the single
  switch to flip when the custom domain lands. The portal home gets
  canonical/OG through its own template; legacy pages and the title of any
  page without a verified identity stay byte-identical via the shadow
  `page.html`'s fallback to the theme block.
- Root aliases are the countable print/QR entry layer (growth-plan L2).
  At build time every alias page gets `noindex` plus a canonical link to its
  nested route; when the analytics beacon is configured, the generated
  instant forward becomes a short beacon send window (JS navigates ~200ms
  after load, hard cap 2.5s, no-JS meta refresh at 4s, visible link
  unchanged) so the alias pageview is recorded. Reading attribution in Web
  Analytics: root-level `manual_*` paths ≈ printed/QR entries, nested
  `MODEL/REGION/...` paths ≈ web navigation and search. With analytics off
  the alias keeps its instant forward; an unrecognized alias body shape is
  left unchanged.
- Tabular traffic reads: `python tools/cwa_report.py --days 7` prints the
  taxonomy totals (print/QR alias entries, in-site manual routes, portal
  home) and a top-pages table from the Web Analytics GraphQL API. It needs
  `CLOUDFLARE_API_TOKEN` (Account Analytics: Read), `CLOUDFLARE_ACCOUNT_ID`
  and `CLOUDFLARE_SITE_TAG` in the environment. The site tag is the Web
  Analytics site's own id — the `siteTag` parameter in the dashboard URL,
  NOT the page beacon token. Read-only; the dashboard stays untouched.
- Outbound link policy (链接归一): print/QR and the persisted `HTML_link`
  records use the root alias; in-site navigation and search engines use the
  nested canonical route; marketing and support signatures point at the
  portal home. Do not hand out a third link shape.

## Feedback and publication checks

The operator has assigned Xia Bing (GitHub `Bingboom`, verified with
`gh api user`) to handle manual feedback and check publication health after
each release. The event triggers a manual check, not a new scheduled service.
First response within 3 business days (growth-plan decision D4, 2026-09-15);
a resolution SLA remains unassigned.

On a verified single-language page with a version, the reader copies the
visible model, market, language, version and relative page context, then opens
GitHub Issues and submits the problem and expected result. Submission requires
the reader's GitHub access and an explicit action; opening the link or copying
context sends nothing. Legacy pages without verified single-language identity
keep their existing behavior and do not receive the feedback block.

Xia Bing records receipt in the Issue, locates the source, links the approved
fix PR and subsequent release commit, verifies the deployed revision and
health checks, and replies in the Issue with the result and final page URL.
Keep those links as the feedback closure evidence. Configuration alone is not
a completed real feedback round; it does not create an Issue or send a reply.
Use the [local health](manual_operations_health_report.md) and
[HTTP health](manual_operations_online_health.md) runbooks after each release.

Current implementation is the entrance slice only. The language dialog keeps
the existing publication available and does not enable invented locale URLs.
Independent locale storage and real locale links remain a separate milestone.

## Local verification

GitHub channel activation (2026-09-13): 42 existing feedback, portal, catalog
and health tests pass. Strict Sphinx over the actual 23-publication frozen
snapshot shows the configured Issue link and all five context fields on both
verified single-language pages; all 21 legacy pages omit the feedback block.
This is local HTML verification, not browser, deployment or real-feedback
closure evidence. Ruff, maintainability and documentation link checks pass.

- `python3 -m unittest`: 3,975 tests run, OK, 22 skipped.
- Portal + RTD source targeted tests: 8 run, OK; real Sphinx fixture builds
  preserve all three manual pages and three QR aliases byte-for-byte, and leave
  the entire source tree unchanged.
- Ruff, maintainability guardrails, JS syntax and documentation links passed.
- `build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
  --data-root tests/fixtures/phase2` passed. The initial command without an
  explicit data root stopped on the intentionally absent local phase2 snapshot;
  no live-data sync was performed.
- Production corpus comparison passed on Hello-Docs snapshot
  `70bb408a059b8bd5f0c666b9d153354fb856f66a`: 1,028 files fetched and checked
  against their Git blob hashes; all source files remain unchanged after both
  Sphinx builds. Of 66 HTML pages, only `index.html` changes; the other 65 are
  byte-identical. The catalog has 21 publications (US 1, shared EU/UK 20).
- Actual RTD rollout is tracked in the implementing PR; local parity is not an
  online acceptance claim.

## Directory and keyword search (2026-09-13)

The local redesign uses compact product rows and a shared keyword box for product
identity and manual body content. `tools/rtd_portal_search.py` indexes canonical
rendered publications after HTML generation, before deployment receipts are sealed.
The index is a same-site static JavaScript asset, so it needs no remote search
service. Matches require every query token and prioritize model and heading matches.
Section results carry the existing rendered anchors, publication language identity
and version; region, category and language filters apply to both result types.
Legacy language scopes remain explicitly unverified. Illustration-only text is
excluded; the index does not claim OCR coverage. Results initially show twelve
sections and can be expanded. The operator accepted the local preview for deployment on 2026-09-13.
Deployment uses the existing engineering mirror and RTD build; manual source
publication, online tables and OSS uploads are outside this change.

The Furo `/search.html` route also has a server-rendered landing form. A bare
visit therefore shows an actionable query field instead of an empty content
panel; submitting it uses the existing `q` parameter and Sphinx search index.

## Product hub rollback — 2026-09-15

The operator requested that main return to the manual-only directory and
keyword search. #1144 is reverted; the complete product hub remains on remote
branch `codex/product-hub-preserved-20260915` at `9306967b`. This rollback
preserves all other product/localization changes and does not modify frozen
publish inputs. Restoring the hub later requires a separate explicit release.

## Accessory catalog artwork (2026-09-15)

JA-CA05B/EU and JA-CA3SA/EU have no packing-list image for the portal to
select. Their existing manual illustrations are bundled byte-for-byte as
portal-only static assets, selected by `product_image_fallbacks` in
`tools/rtd_portal_assets/settings.json`. A native packing-list image takes
precedence; unconfigured models and other markets keep the existing fallback.

| Catalog target | Source illustration | SHA-256 |
| --- | --- | --- |
| JA-CA05B/EU | `docs/renderers/web/assets/ja_ca05b_eu_en/connector_reference.png` | `f343a96eb9aefba55b0bc890a0a6b0f16d361da2a7cb36a640e2e9f8cab48ded` |
| JA-CA3SA/EU | `docs/renderers/web/assets/ja_ca3sa_eu_en/main_ports.png` | `d8786487be9c5b7810bfb1544f277b5cbde5dca3759f09b3500000f4ecc82b77` |

No image generation, cropping, manual-body edits or source-table writes are
needed. These are diagram thumbnails, with the source labels intact. The
Sphinx portal static path copies both images on a normal RTD rebuild; no
frozen manual snapshot needs to be rewritten. Remove the relevant mapping
to return a card to its previous model-only presentation.

### Explicit product artwork

`product_image_overrides` selects exact model/market artwork ahead of a native
packing-list image. Each entry has `src`; optional `view_box`, `width`, and
`height` display a bounded SVG viewport of the unchanged source image.
Removing an override restores native-image / configured-fallback precedence.

- JBP-3600A/EU: the operator-provided *Jackery Battery Pack 3600 User Manual
  (JBP-3000A) EUUK V2.0-2026-08-04.pdf*, page 1. Despite the filename, the cover
  identifies JBP-3600A. PDF SHA-256:
  `084dd4517feddcd9b77da10415a2787ec4427f882a7b819160725fdff679ccfe`.
  Render the original vector artwork at 4x using the top-left PDF-point box
  `(78, 176, 291, 317)`; output `jbp-3600a.png` SHA-256:
  `fb4c99e52945b2753fb405c4ae254804433169861b710fc089df86404fa2c49f`.
- JS-100F/EU: byte-identical copy of
  `docs/renderers/web/assets/js100f_eu_en/solar_panel_connector.png` (SHA-256
  `5a9d559d420ebecc9314ec8e515f11e35e4d29a6453a5dec5d143ab311e0663e`).
  The viewport `24 27 320 145` shows the upper panel only, excluding the second
  panel, connector, and power station. The source dimensions are 1248 x 328.

These overrides affect homepage presentation only, not manual content or
frozen publication snapshots.
