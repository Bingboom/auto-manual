# Private review-draft site (审核稿)

Status: active (2026-10-21; issue register and row sync 2026-10-25)

Hello-Docs-Review is the private document workbench: agents write there with the
mirrored infrastructure, the business data, the templates and the corpus, and
people review the result. Writing is the main production route; data-and-template
builds are used on demand.

Review drafts (审核稿) — for example the JHP-3600C JP draft made with the
[`manual-review-draft`](../../../.agents/skills/manual-review-draft/SKILL.md) skill —
carry unreleased content: unpublished regional editions, R&D values and open
questions. auto-manual and Hello-Docs are both **public** repositories, so the
drafts never enter either of them. They live in the private workbench repository
and are served by a private Read the Docs project. Promoting an approved draft
into Hello-Docs publication and traceability as an approved original is planned,
not built.

The Feishu 审核稿（工作台输出） table, one row per draft line (model, product
name, market, version, date, status, the 待研发确认 count and the links here),
is different: the operator chose on 2026-10-23 to show it on the public
说明书工作台 交付物 tab, unpublished models included, so its rows reach
Hello-Docs with the `web_progress` snapshot (see
[网页说明书进度](web-progress.md)). The drafts and their open questions stay here;
the row is derived from the draft by the [Feishu row sync](#feishu-row-sync),
which writes only whitelisted fields.

## Topology

| Piece | Where | Owner |
| --- | --- | --- |
| Drafts | `Bingboom/Hello-Docs-Review` (private) → `docs/review-drafts/<MODEL>/<REGION>/` (working draft) and its `milestones/<version>/` | the operator, through commits on that repository |
| Site code | `tools/rtd/review_site.py`, `tools/rtd_portal_assets/review_drafts_layout.html` (shell), `review_drafts.html` (overview), `review_draft_line.html` (line page), `_static/review-drafts.css` (auto-manual) | auto-manual PRs |
| Code sync | `sync-hello-docs.yml` job `sync-review` → [`scripts/sync_mirror.sh`](../../../scripts/sync_mirror.sh), keeping `docs/review-drafts` | automatic on every auto-manual `main` push |
| Landing page | [`mirrors/Hello-Docs-Review/README.md`](../../../mirrors/Hello-Docs-Review/README.md), installed as the repository's `README.md` by the same sync (`MIRROR_README`) | auto-manual PRs |
| Hosting | a private Read the Docs project built from `Hello-Docs-Review/main` | the operator (RTD dashboard) |
| Entry | 说明书工作台 → 工作入口 → 构建与发布 → 「审核稿（私有）」 | `review_site` in `manual_workbench.html` |

The mirror sync uses the same composition as Hello-Docs: the auto-manual tree
plus the paths the mirror owns. Both mirror jobs refuse a source tree that
contains `docs/publish`, `docs/knowledge` or `docs/review-drafts`, so a draft
committed to auto-manual by mistake stops both syncs instead of reaching the
public Hello-Docs. That refusal comes after the merge, so the maintainability
guardrails also fail any auto-manual PR that tracks one of those paths; a pushed
PR branch is already public, which is why drafting sessions keep the public
repositories read-only (below). Without the `REVIEW_DOCS_SYNC_TOKEN` secret the
`sync-review` job only logs a notice; the Hello-Docs sync never depends on it.

## Build

`.readthedocs.yaml` builds `docs/publish/web` when it exists (Hello-Docs).
Otherwise, when `docs/review-drafts` exists (Hello-Docs-Review), it runs:

```sh
python -m tools.rtd.review_site docs/review-drafts "$READTHEDOCS_OUTPUT/html"
```

This writes `index.html` (the 审核稿 overview), one page per line at
`<MODEL>/<REGION>.html`, the two stylesheets, and the drafts at their repository
paths (`<MODEL>/<REGION>/…`, milestones under `<MODEL>/<REGION>/milestones/<version>/`).
No Sphinx, no live data. The pages have `noindex,nofollow`, but that is not access
control: privacy comes from the private repository and the private RTD project.

Every copied draft page — the working draft and each milestone — gets a
「← 审核稿总览」 link back to the overview, through a path relative to the output
root (`../../index.html` from a working draft, `../../../../index.html` from a
milestone). It joins the draft's toolbar button group (`div.controls` or
`div.toolbar-actions`) as its first child and takes the draft's button style;
a page without one gets a small self-styled bar right after `<body>`, hidden
in print. A page that already has a `class="to-overview"` element is left as
it is. Only the output is changed; the source drafts keep their bytes.

## A draft line

Each model/region is one **working draft**, edited in place, plus the milestone
versions frozen beside it:

```text
docs/review-drafts/JHP-3600C/JP/
  draft.json                       current version, status, open R&D questions
  manual_jhp3600c_jp_en_draft.html the working draft
  assets/, registers, new-translation-summary.json
  milestones/
    v0.62/                         a frozen copy; its draft.json names the milestone
```

`draft.json`:

```json
{"model": "JHP-3600C", "region": "JP", "language": "ja", "version": "v0.69",
 "date": "2026-10-21", "status": "待母语审校", "html": "manual_jhp3600c_jp_en_draft.html",
 "milestone": "", "summary": "研发答复已回填", "tools_sha": "1a2b3c4",
 "issues": "issues.json", "decisions": "decisions.json"}
```

- The working draft sits at `<model>/<region>/` and a milestone at
  `<model>/<region>/milestones/<version>/`, matching the manifest; the version
  looks like `v0.69` and milestones sort numerically.
- A `draft.json` anywhere else — a `<version>/` copy beside the working draft,
  the old one-directory-per-version layout, a milestone with no working draft —
  fails the build. Versions do not pile up as directories; intermediate versions
  are commits.
- A milestone's `milestone` names it (首个完整稿, 研发答复回填 …); the working
  draft leaves it empty.
- `html` names a file in that directory; symbolic links anywhere in the draft
  fail the build.
- `tools_sha` is **required** on the working draft: the auto-manual commit the
  draft was made with, 7–40 lowercase hex characters
  (`git -C <auto-manual> rev-parse --short HEAD`). Milestones frozen before the
  rule are exempt; a milestone that carries one must carry a valid one. The
  line page shows it.
- `issues` (optional) names the line's issue register and `decisions`
  (optional) its operator-decision list — see below. Both are relative paths
  inside the line directory: no absolute path, no `..`, no symbolic link on the
  way, and the target must be a regular file.
- 新增翻译量 comes from the package's own `new-translation-summary.json`
  (units and words, counted on the US English).
- 待研发确认 is the length of `rd_open`, the questions still open with R&D.
  With an issue register `rd_open` is **derived** from it and `draft.json` may
  omit it; if present it must equal the derived list, or the build fails naming
  the file. Without a register `rd_open` stays hand-written in `draft.json`.

Every build error names the offending file.

## Issue register

`issues.json` (schema `review-issues/1`) is the single place a line's open
questions are written; the site and the Feishu row are derived from it.

```json
{"schema": "review-issues/1", "issues": [
  {"id": "R04", "title": "Solar input range", "kind": "rd", "status": "open", "topic": "solar-input",
   "question": "Does the 12–60 V range of the previous generation apply?",
   "adoption": {"decision": "keep the previous-generation sentence", "by": "operator", "date": "2026-10-24"}},
  {"id": "L02", "title": "Warning label wording", "kind": "language", "status": "confirmed",
   "resolution": {"by": "native reviewer", "date": "2026-10-24", "evidence": "review round 2"}}
]}
```

| Field | Rule |
| --- | --- |
| `id`, `title` | non-empty; `id` unique in the register |
| `kind` | `rd`, `language`, `compliance`, `design` or `content` — who owns the answer |
| `status` | `open`, `confirmed` or `dropped` |
| `topic` | optional slug (`solar-input`) shared by lines of the same model that ask the same question |
| `question` | optional text |
| `adoption` | optional `{decision, by, date}` (ISO date): what the draft carries and who decided |
| `resolution` | `{by, date, evidence}`, required unless `status` is `open` |

Extra fields are allowed; projects keep their own columns.

- **Adoption is not confirmation.** `adoption` is a content decision: an
  operator may decide the draft carries the previous-generation text. `status`
  says whether the owner — R&D for `rd`, the native reviewer for `language`, … —
  has answered. An adoption never changes `status`; only the owner's answer,
  recorded as `resolution`, does. Never close an R&D item on an operator
  adoption: the content is adopted, its technical applicability is still open.
- `dropped` means the question no longer applies; it still needs a resolution.
- Each open `rd` item becomes one 待研发确认 line, in file order:
  `"<id> <title>：<question>"` (full-width colon), or `"<id> <title>"` without a
  question. Open items of the other kinds are 其他待确认, grouped on the line
  page as 语言审校 / 合规 / 设计 / 内容.

`decisions.json` is a JSON list of the line's operator decisions; each has an
`id` (`D01`, `D02` …, unique), `title`, `adopted`, an ISO `date` and a
`status`, plus any extra fields (request, source_type, evidence,
superseded_by …). The line page shows the count and links the file.

## Cross-line topics

Lines of the same model often ask R&D the same question. When working drafts
of one model carry the same `topic` and it is `open` in one line and
`confirmed` in another, the build prints `WARNING <model> topic <topic>: …`
and each affected line page lists it under 「跨稿线待同步」. It is a warning,
not an error: each line has one writer, and one line's writer must not be
blocked by another line. `dropped` items are exempt. The next writer of either
line settles it — copies the answer with its evidence, or reopens the item —
or notes it in the review notes.

The overview has one row per line (current version, date, status, volume, the
number of open R&D questions, 其他待确认 — the open non-R&D items, "—" for a line
without a register — and milestones). The sidebar groups the lines by model;
each line's page shows the working draft, its tools_sha and decision count, the
full 待研发确认 and 其他待确认 lists, any cross-line warnings and the milestone
table.

## Feishu row sync

The 审核稿（工作台输出） row of a line is derived from its working draft, never
typed by hand. After pushing a draft, run from an auto-manual checkout:

```sh
python -m tools.rtd.review_table_sync <clone>/docs/review-drafts --line <MODEL>/<REGION>          # dry run
python -m tools.rtd.review_table_sync <clone>/docs/review-drafts --line <MODEL>/<REGION> --write
```

- Defaults: `--base-token` from `$FEISHU_PUBLISHED_DOCS_BASE_TOKEN`;
  `--table-id` from `$FEISHU_PUBLISHED_DOCS_REVIEW_TABLE_ID`, else the table
  name 审核稿（工作台输出）; `--site-url` is the `review_site` URL set in
  `manual_workbench.html`; `--cli-bin lark-cli`, `--as bot`. No table id is
  committed.
- The drafts are loaded with the site's own checks; an invalid draft fails.
- A line matches the one row whose 审核页 link ends in `/<MODEL>/<REGION>.html`
  and whose 型号 is the model. No row: create it by hand (型号, 商品名称, 市场,
  语言 and the 审核页 link), then rerun — the tool never creates rows. Several
  rows, or a different 型号: error.
- **Owned fields**, the only ones ever written: 当前版本 = version; 更新日期 =
  date; 状态 = status; 待研发确认 = the number of open R&D questions; 审核稿 =
  a link titled `<MODEL> <REGION> <version> 审核稿` to the draft on the site;
  审核页 = a link titled `<MODEL> <REGION> 审核页` to the line page
  `<site>/<MODEL>/<REGION>.html`. 型号, 商品名称,
  市场 and 语言 are identity fields set when the row is created; every other
  column belongs to someone else.
- **Public whitelist and leak check.** The row reaches the public Hello-Docs
  through the daily `web_progress` snapshot, so only the owned fields are
  written, and a line whose `draft.json` `nameplate_model` or `sales_model`
  appears (case-insensitive) in the row's 型号, 商品名称, 市场, 语言, 当前版本,
  状态 or a link — current or planned — fails and nothing is written for it. A
  code contained in the public model code itself is not treated as secret.
- Dry run (default) prints `field: current → planned` per line. `--write`
  writes only the changed fields (no write when nothing changed), waits ~2 s,
  reads the record back, prints `record_id field=value` for every owned field
  and exits 1 on any mismatch. Exit 0 when every line is clean.

## Workbench entry

The private site is the Read the Docs project 「Review-doc lib」
(<https://ht-docs-review-doc-lib.readthedocs-hosted.com/>, single version, no
`/en/latest/`). It clones `Hello-Docs-Review` over SSH with a read-only deploy key
and rebuilds on every push through a GitHub incoming webhook. The workbench entry
reads that URL from `review_site` in `tools/rtd_portal_assets/manual_workbench.html`;
an empty value hides it. Only the URL is public.

## Writing and editing drafts

The private repository is where drafts are written; the review site is how they
are read. Only `docs/review-drafts/` belongs to the private repository — every
other path is overwritten by the next mirror sync, so never edit code there.

- **Through an agent** (`manual-review-draft` skill, “版本、上传与发布”): one instruction
  is one version number and one commit. The agent rewrites the working draft in
  place, updates `draft.json` (version, date, status, summary, `tools_sha`), the
  issue register (or `rd_open` on a line without one), the decisions file, the
  change log and `review.zh.md`, commits to `Hello-Docs-Review/main`, pushes and
  syncs the Feishu row (above).
- **In parallel** (operator decision 2026-10-23): one writer per draft line at
  a time; a writer changes only its own line's directory; a rejected push is
  rebased and retried, and stops if the remote changed the same line, never
  force-pushed; a drafting session keeps auto-manual and Hello-Docs read-only;
  `draft.json` records `tools_sha`, the auto-manual commit the draft was made
  with. The skill's 并行写稿与隔离 section holds the full rules, including how a
  line is claimed.
- **By hand**: edit the working draft's HTML in place (GitHub web editor or a
  local checkout), keep the colour classes, update `date`, `summary` and
  `tools_sha` in `draft.json` (and the issue register when a question changes),
  and commit to `main`.
- **Earlier versions**: every version is a commit —
  `git log -- docs/review-drafts/<MODEL>/<REGION>` lists them and
  `git show <commit>:<path>` recovers one. Freeze a milestone only when the
  operator names one: copy the working draft (without `milestones/`) to
  `milestones/<version>/` and set its `milestone`. Delete a milestone directory
  when it is no longer needed; it stays in git history.
- **Preview before pushing**: `python -m tools.rtd.review_site docs/review-drafts _site`
  and open `_site/index.html`. A sparse clone (only `docs/review-drafts`, the
  way agents check the repository out) has no tool code: run the same command
  from an auto-manual checkout against `<clone>/docs/review-drafts`.

The repository's own `docs/review-drafts/README.md` is the editors' guide
(colour classes and the edit checklist).

## Checks

`python -m unittest tests.test_rtd_review_site tests.test_rtd_review_table_sync tests.test_sync_hello_docs_workflow`.
