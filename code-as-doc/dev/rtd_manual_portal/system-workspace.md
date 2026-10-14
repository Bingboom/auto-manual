# RTD portal: system workspace page

Status: active · Part of the [RTD manual-center entrance](../rtd_manual_portal.md); its index lists the
other portal surfaces. Add new notes for this surface here, not to the hub.

## System workspace page

The 「当前工作」 tab keeps the existing `#tab-progress` anchor and owns current
priorities, completion counts, ledger progress and next actions. Its metrics
appear only in this panel. 「系统演变」 owns the historical stages, reasons for
change, long-term directions and cross-cutting maintenance history. The two
panels remain directly accessible through the shared tabs without repeating a
current-state overview or navigation-hint paragraphs. The evolution introduction
shows only its title and narrative; update metadata and provenance are available
under 「入口与数据来源」.

The 「系统架构」 tab (`#tab-architecture`) reads optional `architecture` from
the same marked history summary as System Evolution. Each node has a status
and repository evidence; malformed architecture follows the evolution fallback,
while older summaries without this optional field remain readable.
The drawing binds nodes by stable ID rather than array order; missing diagram
nodes follow the same malformed-history fallback.
A semantic SVG draws the enterprise input, shared content and capability platform, human and
agent access, documents, derived corpus and capabilities. The existing enterprise
path expands into business tables (product information, content modules,
specifications, multilingual content and business review), then validation and
traceable snapshots. Planned PLM/ERP synchronization and field mapping enter
these tables. The shared core is labelled 「auto-manual」:
content authority and reusable Shared IR form its foundation, while document
production, professional file processing and content queries are its capabilities.
Content Authority, Assembly, Renderers and Publish describe the document-production
path within this platform. Git-native originals and approved assets remain content
sources alongside tables; the diagram does not require every manual to start in
Bitable. The drawing uses short node labels and a shared solid/dashed legend;
definitions, detailed responsibilities and evidence remain in native disclosures, which
hold the capability/skill/hook evidence and planned MCP scope. Shared IR is
consistently labelled 「Shared IR（共享底稿）」 in the system view and evolution.
PLM/ERP integration and MCP exposure remain planned, with dashed borders and
explicit labels. MCP adapts protocols to capability interfaces, outside core
services. Its planned artwork workflow retains human approval before Apply and
verification afterward. Existing Bot/skills/query access is listed separately.
Human output and derived machine output share the production system; current
corpus extraction is HTML compatibility, not universal IR-native generation.
Existing capabilities name actual repository skills for file pretranslation,
AI-file diagnosis/renumbering, PDF QC annotations, backport and builds. Hook
entries distinguish Claude PostToolUse configuration from Git pre-push scripts
that require core.hooksPath activation. The installed PDF multilingual audit
skill is explicitly local, outside mirror distribution. The 产品知识 and 市场与政策
pages are knowledge-base pages for product readers and are not part of this
architecture view. Future access and
cross-format IR directions extend the existing stages without fabricated dates;
review-experience accumulation remains the knowledge-feedback direction.


The 「系统演变」 tab (`#tab-evolution`, individual stages at
`#evolution-<id>`) describes how the manual workspace evolved from its first
deterministic build through reusable style components, published content,
machine consumption and future knowledge feedback. It reads top-down: a month-scaled overview
(stages with optional `start`/`end` as `YYYY-MM`; every bar, tick and the
updated-on line share one scale, an open end fades, an undated stage shows as a
dashed label), then the optional `chapters`, each a question the system had to
answer, holding its stages. Each stage shows its principle; the account and
evidence stay in native disclosure. Chapters must place every stage exactly once;
without `chapters` the stages render as one flat list. Maintenance and refactoring
close the story as 「支撑全程」 below the chapters, covering repeated work
throughout system construction; September governance is one round.
The parser still accepts legacy optional `now` rows, but the page does not
render that duplicate current-state overview. Stage status labels remain on
the timeline to distinguish completed milestones from work that continues.
The optional `crosscutting` list shares the stage fields and evidence validation.
IDs must be unique across both lists; existing `#evolution-engineering` links
now resolve to the signpost.
Its only curated source is
[`system_evolution_history.md`](../../architecture/system_evolution_history.md):
the formal history and its marked `system-evolution/v1` YAML summary live
in that same file. `source_registry.yaml` registers the `evolution` authority;
`tools/rtd/system_evolution.py` reads that file at build time. The mirror carries
it with the engineering tree. No generated HTML or second timeline is maintained.

Maintenance contract:

- Update historical facts and their commit/PR/acceptance evidence first, then
  revise the public summary in the same file and match both update dates.
- `recorded` displays 「已完成」 and means that stage capability formed; it does not assert universal
  coverage or completion of an entire workstream. `ongoing` displays 「持续开展」
  for established work that continues to be maintained and improved.
  `in_progress` means current
  construction, including IDML print trial production, and `planned` identifies the
  future direction. The current most mature chain is Web document production and
  maintenance. Whole-document Web reuse exists and its IR continues to improve
  as manuals are ingested. Cross-format consumption of the same frozen package
  remains a later extension; review-experience reuse is a separate future stage
  that still needs its trial scope
  and execution plan; it is not part of the IR-sharing implementation.
  Existing partial IR sharing is not represented as absent. Machine generation remains explicitly
  `html_compatibility` until an IR-native path is accepted.
- Historical quantities carry observation dates and a defined scope; they are
  not current dashboard totals. The strategy owns future boundaries, the roadmap
  and ledger own execution state, and the optimization log owns detailed changes.
- Public stage periods, timeline and architecture cutoffs, narrative dates and
  operator-confirmation labels use month precision. Record-update, snapshot,
  freshness and build timestamps retain their original precision. Exact source
  evidence dates remain in the authoritative records.
- Stage flows and the feedback direction render as text lists; details and
  evidence use native disclosure. The existing shell handles tabs, keyboard
  navigation and deep links. Without JavaScript all panels remain readable.
- Missing or malformed history shows the registered fallback in this tab while
  keeping other panels usable; `python -m tools.rtd.system_workspace check`
  reports an authoring error. Unknown status, duplicate stage IDs, missing
  evidence, unsafe paths, malformed fences and date mismatch are rejected.
  Text is escaped, not executed as HTML.


`/workspace/system/` (系统建设) opens on 当前工作 with the current focus: the lanes being
ordered by delivery priority, each with its next action and ledger progress.
Stage acceptance follows immediately; corpus statistics, capabilities and evidence
remain available in their respective tabs. The page is built at RTD time from
frozen inputs only. The build never contacts Feishu or GitHub; browser version
checks read only the already-published same-origin receipt.

- `tools/rtd_portal_assets/system_workspace.yaml` is the curated status
  contract: focus lanes, capability cards, production-flow links, gate labels
  and entry links. It is maintained in auto-manual and reaches Hello-Docs
  through the mirror.
- `docs/publish/publish_manifest.json` is the source of the publication counts.
  They use the REV-04 caliber, which is the vocabulary of the whole site: a
  说明书 (unit 本) is one model × region and a 语言版本 (unit 个) is one
  model × region × language. A repeated route, version or rebuild of one
  identity counts once, and 份 is never a unit for language versions.
  `publication_facts` in `tools/rtd/production_evidence.py` is the single
  count: this page, 说明书工作台, 系统数据 and 产品矩阵 all take their figures
  from it, and the 系统数据 filters recount the same identities in the browser.
  This page's `publication_facts(path)` only reads the manifest and wraps it;
  its `editions` key is the deduplicated `variants`.
- The execution ledger named by `now_next.source` supplies REV statuses, the
  gate composition and each lane's progress. The page reads them and never
  restates a REV status.
- The skeleton blueprints under `docs/manifests/skeletons/*/blueprint.yaml`
  say which product families already generate their manual structure from a
  skeleton. The mirror carries them, so RTD reads the same files.
- The agent skills under `.agents/skills` and `.claude/skills`, the Claude Code
  hooks in `.claude/settings.json` and the steps of `.githooks/pre-push` feed
  the skills and hooks block; see [Skills and hooks](#skills-and-hooks).
- `git ls-files` lists the checkout's tracked files for the 工程规模 block; see
  [Engineering scale](#engineering-scale).
- `tools/rtd_portal_assets/source_registry.yaml` is the source registry. For
  every data domain on the page, it records where the fact is decided, how it
  is read, how fresh it must be and what shows without it. The page takes its
  snapshot names, freshness limits and fallback text from it, and lists it
  as 数据来源; see [Source registry](#source-registry).

The page is built only by the combined RTD project, which also serves the
manuals; the manuals-only public project leaves it out (see
[site role](knowledge-pages.md#public-manuals-project-site-role)). Since
2026-10-13 the combined site has been private (Read the Docs for Business,
login required), but the operator can make it public at any time, and
`noindex` is not access control. The contract and the page therefore hold only
publishable facts. Gap narratives and resource needs belong to the Feishu
internal page, not this file. The sidebar lists it under 说明书生产 only when
the page was built.

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
  - `publications`: 网页说明书 (books) and their 语言版本 from the publish
    manifest;
  - `regions`: books per region (`books_by_region`), labelled by `focus.regions`;
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

`tools/rtd/workspace_revision.py` stamps the HTML and
`_static/system-workspace-revision.json` with the same checkout SHA and UTC build
time. On RTD the SHA belongs to the Hello-Docs checkout, not auto-manual/main.
The system page's 「页面版本与更新」 disclosure sits inside 「入口与数据来源」;
it no longer occupies the page header.
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
python -m tools.rtd.system_workspace corpus-export
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

A snapshot older than the `stale_after_days` of the `corpus` domain in
`source_registry.yaml` shows 待复核. The registry also names the snapshot file. An
unreadable or malformed snapshot shows 无数据 for this block only, with a
Sphinx warning; the rest of the page still renders. `check` reports both
cases.

### Skills and hooks

The 技能与钩子 block lists what agents can call and what runs automatically.
It is read from the tree at build time (`tools/rtd/system_tooling.py`), and
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

### Engineering scale

The 工程规模 block (`#codebase`) follows 技能与钩子 in the 工具与工程规模 tab.
At build time `tools/rtd/system_tooling.py` lists the checkout with
`git ls-files` and counts the lines of every tracked `.py`, `.md`, `.rst`,
`.yaml`/`.yml` and `.csv` file per top-level directory and file type, as an
editor counts them. Root files count as (根目录); links and listed files missing
from disk (a sparse checkout) are skipped. Nothing is snapshotted or committed
for it; a change appears on the next RTD build.

- The block draws the 10 directories with the most lines as server-rendered
  bars split by file type, one fixed colour per type, measured against the
  largest directory; the totals below the bars cover the whole repository.
- Git history (branches, commits) is not shown: RTD clones shallowly, so it is
  not reliable at build time; `git ls-files` lists every tracked file in a
  shallow clone too.
- Without git, or outside a checkout, the block shows 无数据 with the
  registry's `codebase` fallback; the rest of the page still renders.

### Source registry

`tools/rtd_portal_assets/source_registry.yaml` registers each data domain the
workspace pages show, once. It is REV-44, the single source of truth for where
each fact comes from; the design is in
[ssot_source_registry_design.md](../ssot_source_registry_design.md). Each domain
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
- The system page lists every domain under 数据来源, with each
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
python -m tools.rtd.system_workspace check
python -m tools.rtd.system_workspace check --online
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
