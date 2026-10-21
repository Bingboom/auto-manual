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
| Drafts | `Bingboom/Hello-Docs-Review` (private) → `docs/review-drafts/<MODEL>/<REGION>/<version>/` | the operator, through commits on that repository |
| Site code | `tools/rtd/review_site.py`, `tools/rtd_portal_assets/review_drafts.html`, `_static/review-drafts.css` (auto-manual) | auto-manual PRs |
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

This writes `index.html` (the 审核稿 list), the two stylesheets and every kept
draft under `drafts/<MODEL>/<REGION>/<version>/`. No Sphinx, no live data. The
list page has `noindex,nofollow`, but that is not access control: privacy comes
from the private repository and the private RTD project.

## A draft version directory

Each version directory is the finished draft package plus `draft.json`:

```json
{"model": "JHP-3600C", "region": "JP", "language": "ja", "version": "v0.69",
 "date": "2026-10-21", "status": "待母语审校", "html": "manual_jhp3600c_jp_en_draft.html",
 "milestone": "", "summary": "研发答复已回填", "rd_open": ["50Hz／60Hz 出厂默认值与切换方法"]}
```

- The directory path must be `<model>/<region>/<version>` from the manifest; the
  version looks like `v0.69` and sorts numerically.
- `html` names a file in that directory; symbolic links anywhere in the draft
  fail the build.
- 新增翻译量 comes from the package's own `new-translation-summary.json`
  (units and words, counted on the US English).
- 待研发确认 is the length of `rd_open`, the questions still open with R&D.
- `milestone` labels a kept older version (首个完整稿, 研发答复回填 …).

Each model/region row shows its newest version; older kept versions sit under
「保留的历史版本」. Keep the newest version plus milestones; superseded
in-between versions stay in git history and in the Feishu zips.

## Turning the entry on

The workbench entry stays hidden while `review_site` is empty. After the RTD
project exists, set `{% set review_site = '<project URL>' %}` in
`tools/rtd_portal_assets/manual_workbench.html`. Only the URL is public.

## Checks

`python -m unittest tests.test_rtd_review_site tests.test_sync_hello_docs_workflow`.
