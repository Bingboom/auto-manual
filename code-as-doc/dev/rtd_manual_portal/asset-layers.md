# 四类资产 (asset-layer pages)

Status: active (slices 1 and 2 of the four-layer portal work, 2026-11-16; REV-51, registered
in pull request #1734)

The operator maintains four layers of assets. Since step 12 of the 2026-11 redesign
(operator-approved 2026-11-16) the private portal has one page per layer, in this
priority order, as the sidebar group 资产 · 按优先级:

| # | Layer | Address | Template |
| --- | --- | --- | --- |
| 1 | 产品信息 | `/products/matrix.html` (tabs: 产品矩阵, 属性字典 `/products/attributes.html`, 产品知识 `/products/knowledge.html`) | `product_matrix.html`, `product_attributes.html`, `product_knowledge.html` |
| 2 | 内容与表现 | `/assets/content/` | `asset_content.html` |
| 3 | 视觉媒体 | `/assets/media/` | `asset_media.html` |
| 4 | 语言 | `/assets/language/` | `asset_language.html` |

`tools/rtd/asset_layers.py` builds the views (layer order, 产品信息's head, content,
language), `tools/rtd/asset_media.py` reads the media inventories, and
`tools/rtd/portal.py` (`asset_layer_pages`) yields the pages on the private
(combined) site only. A manuals-only build makes none of them, and the public
shell links none of them (`tools/rtd/site_role.py` is unchanged).

## Navigation

The private sidebar is: 首页; 资产 · 按优先级 (the four layers, each numbered);
说明书 (说明书资料库, 搜索说明书正文); 生产与方向 (说明书工作台, 系统建设); 参考
(市场与政策, 设计规范). 产品信息 opens on 产品矩阵, or on 产品知识 when the matrix is
not built, and stays current on all three of its tabs. 知识库首页's 去哪里 cards
mirror these groups; the old card ids stay (`#products` is now 资产, `#manuals`,
`#production`; 参考 is `#reference`).

No page moved address, so no redirect was needed: 产品矩阵 and 产品知识 keep their
URLs and become tabs of 产品信息. Old in-page anchors keep working:

- 说明书工作台 `#reuse`, `#library-corpus`, `#library-styles`, `#library-templates`
  now sit on a pointer row that links the three asset pages;
- 系统建设 `#language-assets` and `#tab-corpus` now hold a pointer to 语言.

## The shared anatomy

Every layer page uses `_asset_layer.html`: a head (资产 N · 共四类, the title, one
line and the build date), then six blocks with fixed ids, in this order:

| Block | id | Answers |
| --- | --- | --- |
| 规模 | `#scale` | how much, each figure with the date it was read |
| 在哪里维护 | `#maintained` | the table or repository file, and who changes it how |
| 清单 | `#inventory` | the browsable inventory |
| 被谁使用 | `#used-by` | which manuals or tools use it |
| 来源与时间 | `#sources` | origin, snapshot or build date |
| 质量与缺口 | `#gaps` | what is missing, unverified or stale |

Rules:

- No hand-set maturity status. Since slice 2 a layer's chip comes only from its
  registered ledger rows (see below).
- A figure that cannot be computed shows 待统计; a part that does not exist yet
  shows 建设中; an unreadable source shows 无数据. None of them is ever a 0 or
  an example number.
- Every figure carries its date: the snapshot's export date, or 构建时读取 with
  the build date in the head.

## What each page reads

**产品信息.** The head and the side blocks (`product_head`, `product_foot`) are
shared by the three tabs. 规模: products and models from the 产品矩阵 context, the
attribute count, the 产品知识 topic count. 产品矩阵 is the existing page with the
same data and a visible note that source links, verification and dates are being
built (the product-information base, REV-50, another window). 属性字典 lists the
attributes `tools/product_facts/attributes.json` already defines (label, key,
unit, type, the 产品类别 a gap is counted for, definition); it holds no product
value. 产品知识 is the existing page. A 待核实与冲突 tab shows as 建设中 and is not
a link: there is no data for it yet.

**内容与表现.** Shared chapters under `docs/templates/page_shared` as a chapter ×
language table; the skeletons (`skeletons_of`), the recipe files and sets under
`docs/templates/recipes`, the page-template folders; the components in
`component_registry.yaml` with the only use the site computes, the 产品总览
instances bound to models (`production_evidence.component_references`); links
to the six 设计规范 tabs for styles, which are kept only there. Use per chapter or
component is 待统计.

**视觉媒体.** `data/asset_registry.csv`: registered, finished, language-neutral and
every-model counts; a table of every row (key, type, models, regions, language,
status, the first 12 hex digits of the content hash, version) with filters for
type, model, region and language and 只看未完成 (`_static/asset-layers.js`; an
ALL row and a language-neutral row match every value). The 备注 column holds
source notes and stays off the page. The registry has no version column, which
the page states in 规模 and 质量与缺口. The shared symbol manifest: key, file,
status, whether a source is recorded, hash. **Use per symbol is computed from the
published sources without stored data:** the publish step pools each manual asset
as `_static/manual-assets/_pool/<2>/<sha256>.<ext>`, so each catalog publication's
Markdown source names the hash of every image it shows; the page counts the
language versions and editions (model × market) whose source names the symbol's
`sha256`. Without readable published sources the column says 待统计.

**语言.** The translation-memory snapshot as 系统建设 reads it (句对, 术语, approved
share, per-language pair counts, export date, 待复核 past `stale_after_days`); the
registered languages against those with pairs and those with verified
single-language Web manuals (from the catalog); `data/terminology_rules.csv`.
Pair-by-pair browsing is 建设中: the snapshot stores totals only. The block moved
here from 系统建设 › 能力与架构 › 语言资产, which keeps a pointer.

## Curated data: `asset_layers.yaml` (slice 2)

`tools/rtd_portal_assets/asset_layers.yaml`, read by `tools/rtd/asset_layer_data.py` and
assembled with the layer views by `tools/rtd/asset_pages.py`, holds everything about the
layers that is not a figure:

- **Wording, each kept once.** `umbrella` (产品技术内容资产) and `main_line` (新说明书在工作台写作，是主线；
  扩大存量说明书的网页覆盖是积累线；产品信息矩阵是第一个要补全的资产。). The operator adopted both on
  2026-11-16 (positioning §1.2); a later change is a one-line edit here. `product_value` is the operator's
  own statement of the product matrix's value (2026-11-16), shown word for word as the
  lead of the three 产品信息 pages and nowhere else, with no caption under it (operator,
  2026-11-16); the 产品矩阵 page keeps its own 建设中 note on sources, verification and
  dates. Its source is positioning §4.1.
- **Status chips from ledger rows.** Each layer lists the REV rows that belong to it.
  The rows are read as 系统建设 reads them (`system_workspace.ledger_progress`) and
  the state maps to a portal status word (`CHIP_STATUS`: all done → 已验证, any done,
  active or verifying → 建设中, all planned → 已规划). A layer with no row, or whose
  rows are all deferred, shows no chip; a REV id the ledger lacks is an authoring error
  (a build warning, and the pages fall back to no chips, no main line and the old
  capability cards). The chip shows on the layer page head, the home card and the
  系统建设 layer card, always with the rows it comes from.

  | Layer | Rows | Chip (2026-11-16) |
  | --- | --- | --- |
  | 产品信息 | REV-50, REV-52 | 已规划 |
  | 内容与表现 | REV-15, REV-41–43 | 建设中 |
  | 视觉媒体 | — | none |
  | 语言 | REV-11, REV-18, REV-35–38 | 建设中 |

  REV-51 (these pages) belongs to no single layer and is not mapped.
- **Capability regrouping.** `items` place 系统建设's capability items (`card.item`) under
  the layers; `production` keeps the other cards whole. Every item of a regrouped card
  is placed exactly once; an item keeps its own status and evidence. The old card ids
  (`#cap-language`, `#cap-content_foundation`) stay as anchors on the layer card that
  holds most of their items.
- **Staged path** (positioning §4.2): each stage quotes the positioning document; a
  stage with ledger rows carries their chip, a stage without one shows the quote only.
  The boundary quote includes 「竞品数据暂不做（操作者 2026-11-16），矩阵只收自有产品」: no
  competitor data or competitive analysis appears as a stage, planned or under way.
  `tests/test_rtd_asset_layers.py` checks the quotes word for word once §4.2 is on the
  branch.

## 知识库首页 and 系统建设 (slice 2)

- **知识库首页 「现在」** shows the four layer cards in priority order (frame B): number,
  title, chip, one line, two figures with the date they were read, where it is
  maintained and its weakest point. The figures are the layer views'
  (`asset_layers.home_cards`), never read a second way; a missing one says 待统计.
  Below, **主线** prints `main_line` with two facts: 网页覆盖 (the workbench's
  coverage, `web_progress.coverage`) and 产品信息矩阵 (the path's matrix stage chip).
  正在做 is unchanged. The former 当前主线 lane list and the four
  「已积累的可复用资产」 cards (translation corpus, images, chapters, knowledge growth) are
  gone; their readers were removed from `workspace_home.py`.
- **系统建设** opens with the approved headline (`hero.subtitle` in
  `system_workspace.yaml`). 能力与架构's capability map shows four layer cards, then
  the 生产 row (网页发布, 多格式生产, 评审回写, Agent 执行), then **长期方向**
  (`#path`). The page's wording 逐步收缩 is 退出 (operator, 2026-11-16); the dated
  2026-11-06 quote stays as said, with the positioning document cited beside it.

## Workbench and 系统建设 changes in slice 1

- 说明书工作台: the tab 资产与证据 is 生产证据 (its id stays `production-evidence`);
  the asset cards (`asset_libraries.html`, removed) became the pointer row;
  生产证据 and 快照与校验 stay. 进度 leads with coverage (see
  [web-progress.md](web-progress.md#coverage)); 审核中 and 待转 stay below it.
- 系统建设: only the 语言资产 block changed (a pointer to 语言).
- 知识库首页: its four asset cards link their asset pages (翻译语料 → 语言,
  图片素材 → 视觉媒体, 通用章节 → 内容与表现); their figures and wording are unchanged
  (the home cards and main-line wording are a later slice).

## Later slices

产品矩阵 rows as model × market from the product-information base snapshot with
sources, verification and dates (REV-50); time backfill (REV-52).

## Tests

`tests/test_rtd_asset_layers.py` (views and templates without data),
`tests/asset_layers_ui.test.mjs` (the filters), and the real-Sphinx sidebar test
in `tests/test_rtd_portal.py` (groups, numbering, the 产品信息 tabs, the six
blocks, no status chip, and that the public build links no internal page).
