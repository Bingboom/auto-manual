# 网页说明书进度 (deliverables tab)

Status: active

Since 2026-10-19 the 交付物 tab of 说明书工作台 (`/workspace/deliverables/`) shows
Web manuals only (operator: 「这个交付物 我现在 只想看 网页文档」). The operator is
converting manuals to the Web until the catalog is complete enough, so the tab
opens with progress: what is online, per market, and what is still to convert.
Then comes 语言版本明细, collapsed, which lists every language version (see
[Deliverables page](knowledge-pages.md#deliverables-page)).

`tools/rtd/web_progress.py` builds the view, `web_progress.html` renders it, and
`_static/web-progress.js` draws the timeline and filters the matrix.

## What the section shows

- **Counts.** 已上线型号 (with its categories), 待转市场版本, 语言未齐 and 内容已核对
  (checked / language versions). 网页说明书 and 语言版本 stay in the page summary
  above the tabs, which owns them.
- **上线进度.** For each day the catalog grew, the cumulative language versions,
  market versions (model × region) and models. A running total holds its value
  until the next day that adds to it, so the lines are steps. Hover shows the
  day's additions.
- **各市场进度.** One bar per market: market versions with every language the
  market has online (语言齐全), versions short of that (语言未齐), and 待转.
- **覆盖矩阵.** One row per model with a Web manual, one column per market.
  A cell shows the languages it has against the languages that market has
  online, for example 1/9. It links to the English page, or to the first
  language when there is no English. 旧版 marks a `legacy_unspecified` route,
  whose language scope is still to be checked. 待转 marks a market with active
  SKUs and no Web manual. A blank cell means the market has no active SKU.
  Categories come from the model prefix: JE and JHP are 电源主机, JBP is 扩容电池,
  JS is 太阳能板, and anything else is 配件. A select filters by category, and a
  checkbox keeps only rows with 待转 or 语言未齐.

Markets follow the SKU codes and the Feishu table: EU editions cover the UK and
US editions cover Canada (the table's 欧英规 and 美规). KR, AU and BR appear once
a published model has active SKUs there.

## Sources

| Part | Source | Read |
| --- | --- | --- |
| Online language versions, counts, bars, cells | `docs/publish/publish_manifest.json` | build time, always current |
| 待转, 内容已核对, 上线进度 | `web_progress_snapshot.json`, the `web_progress` domain in `source_registry.yaml` | committed snapshot |

The snapshot holds only:

- `checked`: the routes whose 内容是否核对 box is ticked in the 网页文档 table of
  the 发布文档管理 Base;
- `sold`: for each model with a Web manual, the markets of the active SKUs
  that its 网页文档 rows link in 规格型号, skipping 停用, 禁用, 作废, 样品 and 假机 SKUs;
- `timeline`: the first day each current language version appeared in the
  publish manifest's first-parent git history. A renamed legacy route counts
  from its old name.

No SKU code, project code or unpublished model leaves Feishu. The snapshot is
committed to a public repository and shown on the site, and the SKU table
also lists products that are not yet released. The full candidate list of
models without a Web manual therefore stays off this page.

A missing or unsound snapshot removes only 待转, 已核对 and the timeline, with a
Sphinx warning; the rest renders from the manifest. A snapshot older than the
domain's `stale_after_days` (7) shows 待复核.

## Refreshing

Run this from a full clone of Hello-Docs (`git fetch --unshallow` if needed),
with lark-cli signed in:

```bash
python -m tools.rtd.web_progress export --cli-bin "lark-cli --profile prod" --as bot
python -m tools.rtd.web_progress check
```

`export` is read-only. It reads the 网页文档 table named by
`$FEISHU_PUBLISHED_DOCS_BASE_TOKEN` and `$FEISHU_PUBLISHED_DOCS_WEB_TABLE_ID`, and
the history of `docs/publish/publish_manifest.json` at `--ref` (default `HEAD`)
in `--history-repo` (default this checkout). A shallow clone, a missing column
or a ticked row without a Web manual link fails the export, and the previous
snapshot stays. It writes the snapshot only when its content changes; commit
it through a PR. The workflow-driven Workspace Data Refresh does not run this
export yet.
