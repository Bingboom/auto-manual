# Private review-draft site (审核稿)

Status: active (2026-10-21)

Review drafts (审核稿) — for example the JHP-3600C JP draft made with the
[`us-jp-review-draft`](../../../.agents/skills/us-jp-review-draft/SKILL.md) skill —
carry unreleased content: unpublished regional editions, R&D values and open
questions. auto-manual and Hello-Docs are both **public** repositories, so the
drafts never enter either of them. They live in a third, private mirror and are
served by a private Read the Docs project.

## Topology

| Piece | Where | Owner |
| --- | --- | --- |
| Drafts | `Bingboom/Hello-Docs-Review` (private) → `docs/review-drafts/<MODEL>/<REGION>/` (working draft) and its `milestones/<version>/` | the operator, through commits on that repository |
| Site code | `tools/rtd/review_site.py`, `tools/rtd_portal_assets/review_drafts_layout.html` (shell), `review_drafts.html` (overview), `review_draft_line.html` (line page), `_static/review-drafts.css` (auto-manual) | auto-manual PRs |
| Code sync | `sync-hello-docs.yml` job `sync-review` → [`scripts/sync_mirror.sh`](../../../scripts/sync_mirror.sh), keeping `docs/review-drafts` | automatic on every auto-manual `main` push |
| Hosting | a private Read the Docs project built from `Hello-Docs-Review/main` | the operator (RTD dashboard) |
| Entry | 说明书工作台 → 工作入口 → 构建与发布 → 「审核稿（私有）」 | `review_site` in `manual_workbench.html` |

The mirror sync uses the same composition as Hello-Docs: the auto-manual tree
plus the paths the mirror owns. Both mirror jobs refuse a source tree that
contains `docs/publish`, `docs/knowledge` or `docs/review-drafts`, so a draft
committed to auto-manual by mistake stops both syncs instead of reaching the
public Hello-Docs. Without the `REVIEW_DOCS_SYNC_TOKEN` secret the `sync-review`
job only logs a notice; the Hello-Docs sync never depends on it.

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
 "milestone": "", "summary": "研发答复已回填", "rd_open": ["50Hz／60Hz 出厂默认值与切换方法"]}
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
- 新增翻译量 comes from the package's own `new-translation-summary.json`
  (units and words, counted on the US English).
- 待研发确认 is the length of `rd_open`, the questions still open with R&D.

The overview has one row per line (current version, date, status, volume, the
number of open questions and milestones). The sidebar groups the lines by model;
each line's page shows the working draft, the full 待研发确认 list and the
milestone table.

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

- **Through an agent** (`us-jp-review-draft` skill, step 12): one instruction
  is one version number and one commit. The agent rewrites the working draft in
  place, updates `draft.json` (version, date, status, summary, `rd_open`), the
  change log and `review.zh.md`, commits to `Hello-Docs-Review/main` and pushes.
- **By hand**: edit the working draft's HTML in place (GitHub web editor or a
  local checkout), keep the colour classes, update `date` and `summary` in
  `draft.json`, and commit to `main`.
- **Earlier versions**: every version is a commit —
  `git log -- docs/review-drafts/<MODEL>/<REGION>` lists them and
  `git show <commit>:<path>` recovers one. Freeze a milestone only when the
  operator names one: copy the working draft (without `milestones/`) to
  `milestones/<version>/` and set its `milestone`. Delete a milestone directory
  when it is no longer needed; it stays in git history.
- **Preview before pushing**: `python -m tools.rtd.review_site docs/review-drafts _site`
  and open `_site/index.html`.

The repository's own `docs/review-drafts/README.md` is the editors' guide
(colour classes and the edit checklist).

## Checks

`python -m unittest tests.test_rtd_review_site tests.test_sync_hello_docs_workflow`.
