# 网页说明书进度 (deliverables tab)

Status: active

Since 2026-10-19 the 交付物 tab of 说明书工作台 (`/workspace/deliverables/`) shows
Web manuals only (operator: 「这个交付物 我现在 只想看 网页文档」). The operator is
converting manuals to the Web until the catalog is complete enough, so the tab
opens with progress: what is online, per market, and what is still to convert.
Then comes 语言版本明细, collapsed, which lists every language version (see
[Deliverables page](knowledge-pages.md#deliverables-page)).

Since 2026-10-23 it also shows the manuals still in review, from the 审核稿 table
of the same Base, and links back to the Feishu rows (operator: 「既要有网页文档
也要有审核稿的数据 带多维表跳转链接」).

`tools/rtd/web_progress.py` builds the view, `tools/rtd/web_reviews.py` reads the
审核稿 rows, `web_progress.html` renders it, and `_static/web-progress.js` draws
the timeline and filters the matrix.

## What the section shows

- **Counts.** 审核中 (drafts in the 审核稿 table, with the open 待研发确认 questions
  and the last update), 已上线型号 (with its categories), 待转市场版本, 语言未齐 and
  内容已核对 (checked / language versions).
- **审核中.** One row per 审核稿 table row, newest first: model and product name,
  market and language, version, update date, status, 待研发确认, and links to the
  draft and its review page (the private review site, login needed) and to the
  row in Feishu. The section title links to the table. 网页说明书 and 语言版本 stay in the page summary
  above the tabs, which owns them.
- **上线进度.** For each day the catalog grew, the cumulative language versions,
  market versions (model × region) and models. A running total holds its value
  until the next day that adds to it, so the lines are steps. Hover shows the
  day's additions.
- **各市场进度.** One bar per market: market versions with every language the
  market has online (语言齐全), versions short of that (语言未齐), 审核中 and 待转.
- **覆盖矩阵.** One row per model with a Web manual, one column per market.
  A cell shows the languages it has against the languages that market has
  online, for example 1/9. It links to the English page, or to the first
  language when there is no English. 旧版 marks a `legacy_unspecified` route,
  whose language scope is still to be checked. A blue version number marks a
  draft in review and opens it: alone when the market has no Web manual yet
  (it is then not counted as 待转), beside the chip when a newer draft of an
  online edition is in review. Models that so far only have drafts head the
  matrix as 审核中（未上线）. A 审核稿 row whose 市场 is not a known market stays
  in the 审核中 list only. 待转 marks a market with active SKUs and no Web manual
  or draft. A blank cell means the market has no active SKU.
  Categories come from the model prefix: JE and JHP are 电源主机, JBP is 扩容电池,
  JS is 太阳能板, and anything else is 配件. A select filters by category, and a
  checkbox keeps only rows with 待转, 审核中 or 语言未齐.
- **语言版本明细.** Each language version's 飞书 link opens its row in the 网页文档 table.

Markets follow the SKU codes and the Feishu table: EU editions cover the UK and
US editions cover Canada (the table's 欧英规 and 美规). KR, AU and BR appear once
a published model has active SKUs there.

## Sources

| Part | Source | Read |
| --- | --- | --- |
| Online language versions, counts, bars, cells | `docs/publish/publish_manifest.json` | build time, always current |
| 审核中, 待转, 内容已核对, 上线进度, 飞书 links | `web_progress_snapshot.json`, the `web_progress` domain in `source_registry.yaml` | committed snapshot |

The snapshot holds only:

- `checked`: the routes whose 内容是否核对 box is ticked in the 网页文档 table of
  the 发布文档管理 Base;
- `sold`: for each model with a Web manual, the markets of the active SKUs
  that its 网页文档 rows link in 规格型号, skipping 停用, 禁用, 作废, 样品 and 假机 SKUs;
- `timeline`: the first day each current language version appeared in the
  publish manifest's first-parent git history. A renamed legacy route counts
  from its old name;
- `reviews`: every row of the 审核稿（工作台输出） table with a 型号 —
  `tools/rtd/web_reviews.py` reads 型号, 商品名称, 市场 (mapped to a market by
  `market_names` in `web_progress.json`), 语言, 当前版本, 更新日期 (the tenant's
  UTC+8 day), 状态, 待研发确认, 审核稿 and 审核页, and keeps the row's record id;
- `records` and `feishu`: the 网页文档 row of each route and the two tables'
  addresses, built from `$FEISHU_PUBLISHED_DOCS_URL`. A row link is the table
  address plus `&record=<record id>`.

No SKU code or project code leaves Feishu, and the full candidate list of
models without a Web manual stays off this page: the snapshot is committed to
a public repository and the SKU table also lists products that are not yet
released. The 审核稿 rows are the exception the operator chose on 2026-10-23:
they show models that are not yet published. `reviews`, `records` and `feishu`
are optional, so the committed baseline in `tools/rtd_portal_assets/` carries
none of them; they arrive with the first refreshed snapshot.

A missing or unsound snapshot removes only 审核中, 待转, 已核对 and the timeline, with a
Sphinx warning; the rest renders from the manifest. A snapshot older than the
domain's `stale_after_days` (7) shows 待复核.

## Refreshing

Hello-Docs **Workspace Data Refresh** refreshes it every day at 07:17 Beijing time
(cron `17 23 * * *` UTC); **Run workflow** with `web_progress` refreshes it at once.
The 网页文档 table has no completion receipt, unlike the Word and print batches,
so this source runs on a schedule (operator, 2026-10-19). The job:

- checks out `main` with its full history (`fetch-depth: 0`, `filter: blob:none`), so
  the timeline can date every language version;
- runs `python tools/workspace_refresh.py refresh web_progress`, which reads the
  tables named by the Hello-Docs secrets `FEISHU_PUBLISHED_DOCS_BASE_TOKEN`,
  `FEISHU_PUBLISHED_DOCS_WEB_TABLE_ID` and `FEISHU_PUBLISHED_DOCS_REVIEW_TABLE_ID`
  with the bot, after checking them against the `web_progress` and
  `web_progress_reviews` identities in `workspace_refresh_sources.json`, and
  builds the Feishu links from `FEISHU_PUBLISHED_DOCS_URL` (the Base's address,
  `https://<tenant>.feishu.cn/wiki/<node>`). The snapshot's source identity stays
  the 网页文档 binding, so snapshots from before the 审核稿 table still match;
- writes `docs/knowledge/workspace-data/web_progress_snapshot.json` and opens or
  updates the content PR `chore/workspace-web_progress`, like the other sources.
  Nothing is merged automatically, and an unchanged read makes no commit.

A missing secret, a shallow clone, a missing column or a ticked row without a
Web manual link fails the run and keeps the last snapshot; the failure opens one
`Workspace data update: web_progress` issue. Freshness shows as 网页进度快照 in the
page's 数据更新时间, and Workspace Data Verify checks its hash like the others.

By hand, from a full clone with lark-cli signed in:

```bash
python -m tools.rtd.web_progress export --cli-bin "lark-cli --profile prod" --as bot
python -m tools.rtd.web_progress check
```

`export` is read-only and takes the same tables from `$FEISHU_PUBLISHED_DOCS_BASE_TOKEN`,
`$FEISHU_PUBLISHED_DOCS_WEB_TABLE_ID` and `$FEISHU_PUBLISHED_DOCS_REVIEW_TABLE_ID`, and
the link address from `$FEISHU_PUBLISHED_DOCS_URL` (`--review-table-id` and `--base-url`;
either empty leaves its part out); `--history-repo` and `--ref` choose the
history to date from (default: this checkout at `HEAD`).
