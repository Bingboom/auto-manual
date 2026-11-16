# 四类资产 (asset-layer pages)

Status: active (slice 1 of the four-layer portal work, 2026-11-16; registered as REV-51 in
pull request #1734)

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

- No maturity status on the page. A layer's status will come from registered
  ledger rows (REV-51); a hand-set chip is not allowed.
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

## Workbench and 系统建设 changes in the same slice

- 说明书工作台: the tab 资产与证据 is 生产证据 (its id stays `production-evidence`);
  the asset cards (`asset_libraries.html`, removed) became the pointer row;
  生产证据 and 快照与校验 stay. 进度 leads with coverage (see
  [web-progress.md](web-progress.md#coverage)); 审核中 and 待转 stay below it.
- 系统建设: only the 语言资产 block changed (a pointer to 语言).
- 知识库首页: its four asset cards link their asset pages (翻译语料 → 语言,
  图片素材 → 视觉媒体, 通用章节 → 内容与表现); their figures and wording are unchanged
  (the home cards and main-line wording are a later slice).

## Later slices

知识库首页 cards and wording; 系统建设's headline, capability map and staged path;
产品矩阵 rows as model × market from the product-information base snapshot with
sources, verification and dates (REV-50); time backfill (REV-52); the layer status
chips from registered ledger rows.

## Tests

`tests/test_rtd_asset_layers.py` (views and templates without data),
`tests/asset_layers_ui.test.mjs` (the filters), and the real-Sphinx sidebar test
in `tests/test_rtd_portal.py` (groups, numbering, the 产品信息 tabs, the six
blocks, no status chip, and that the public build links no internal page).
