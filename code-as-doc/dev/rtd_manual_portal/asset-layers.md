# 四类资产 (asset-layer pages)

Status: active (slices 1 and 2 of the four-layer portal work, 2026-11-16; REV-51, registered
in pull request #1734; front cleanup 2026-11-17)

The operator maintains four layers of assets. Step 12 of the 2026-11 redesign
(operator-approved 2026-11-16) gave each layer a page on the private portal. The
front cleanup (operator review 2026-11-17: the front is for product colleagues,
not for maintainers) split them into front pages and maintenance pages:

| Layer | Address | Template | Where |
| --- | --- | --- | --- |
| 产品信息 | `/products/matrix.html` | `product_matrix.html` | 资产 (front) |
| 产品知识 | `/products/knowledge.html` | `product_knowledge.html` | 资产 (front) |
| 语料库 (was 语言) | `/assets/language/` | `asset_language.html` | 资产 (front) |
| 视觉媒体 | `/assets/media/` | `asset_media.html` | 知识资产 (front) |
| 内容与表现 | `/assets/content/` forwards to 设计规范 | — (not shown; operator: 「这个 不用放出来呀」) | — |
| 视觉媒体's inventory | `/workspace/design/#assets-inventory` | `_media_inventory.html` (folded at the foot of 设计规范 › 图标与素材) | 设计规范 (maintenance) |

`tools/rtd/asset_layers.py` builds the views (layer order, content, media,
language), `tools/rtd/asset_media.py` reads the media inventories, and
`tools/rtd/asset_pages.py` (`asset_layer_pages`, called by `tools/rtd/portal.py`)
yields the pages on the private (combined) site only. A manuals-only build makes
none of them, and the public shell links none of them (`tools/rtd/site_role.py`
is unchanged).

## Navigation

The private shell (`_site_shell.html`, layout of 2026-11-17, operator: 顶部四大导航 + 左侧上下文目录 +
中间内容区) has four main sections in the top bar, and the left list holds the current section's pages only:

| Top bar | Left list | First page |
| --- | --- | --- |
| 知识资产 | 资产总览, 产品信息, 产品知识, 说明书资料库, 语料库, 视觉媒体, 市场与政策 | 知识资产 (`workspace/index.html`) |
| 工作台 | 说明书工作台 | 说明书工作台 |
| Agent 能力 | 系统建设 (its tools, skills and agent operations) | 系统建设 |
| 设计规范 | 设计规范 | 设计规范 |

The layout image shows the 知识资产 list only. The lists of 工作台, Agent 能力 and 设计规范 were proposed as
defaults and confirmed by the operator on 2026-11-17 (「都按建议」, in the orchestrating session: 工作台 =
说明书工作台, Agent 能力 = 系统建设, 设计规范 = 设计规范 + 内容与表现, and 内容与表现 was then taken off the site; 视觉媒体's inventory folded into 设计规范 ›
图标与素材 when 视觉媒体 became a page for colleagues — operator: 「按这个改」, so no page duplicates another), and the shell as built (「先这样吧」); the canvas's colours are not used, the
site keeps its own palette. A page's section is declared once, in the `site_sections` table of
`_site_shell.html`: a `list` entry is a left entry, an `also` entry belongs to the section without one, and
`under` names the left entry it sits beneath. A key in no section selects no section and gets
`app-nav-unassigned`, which the tests reject.

Since the operator's reference layout of 2026-11-18 (「我想调成这种布局」, 「你就看布局 数据按实际的来」, 「小字去掉」) the
top bar is white with a hairline: the brand (a dark mark with the book glyph, the wordmark and an accent full stop),
the sections as plain text (the current one darker, with an accent bar on the bar's bottom edge), and a search
field at the right. The field is a plain GET form to 搜索说明书正文 (`?q=`, which the search page reads), so it works
without JavaScript; "/" focuses it unless the reader is typing elsewhere (`site_script`), and below 640px it folds
to its icon, which opens the search page. The former Agent icon opened the same page as the Agent 能力 section and
was dropped; the section stays. The current left entry is a light accent pill. `资产总览` (`workspace/index.html`) is the first left entry of 知识资产 and opens with a 3-figure summary capsule (收录机型, 正式说明书, 覆盖语种) above a unified 3×2 card grid covering all six 知识资产 pages (`front_summary` and `front_cards` in `tools/rtd/asset_pages.py`), where each card's secondary badge shows concise counts (such as `<n> 个市场 · <m> 语种` for 说明书资料库) and never enumerates market or language codes. The search page is reached from the top bar, not the left list; it sits under 说明书资料库, which it highlights. The breadcrumb (工作资料 / section / page;
工作资料 / 知识资产 / 说明书资料库 / 搜索说明书正文 for the search page) is kept for screen readers only; the crumb row still
carries a page's own tools (说明书资料库's 区域). 产品信息's tab pages (产品矩阵, 产品档案, 产品对比, 参数表) are `also`
entries `under` 产品信息, so their crumb reads 工作资料 / 知识资产 / 产品信息 / <tab>. An address naming a folded block
(`#assets-inventory`) opens it (`_static/design-system.js`). Below 420px wide the four sections keep one row. On a phone the top bar takes two rows (menu, brand and search, then the
sections) and the left list opens from the menu button. The pages keep their content. 产品信息 links 产品知识 when the matrix is not built.

Old addresses keep working:

- `/products/attributes.html` (the former 属性字典 tab) is a moved page
  (`moved_page.html`) that forwards to `/products/matrix.html#matrix`, or to
  `/products/knowledge.html#knowledge-list` when the matrix is not built;
- 说明书工作台 `#reuse`, `#library-corpus`, `#library-styles`, `#library-templates`
  sit on a pointer row that links the asset pages;
- 系统建设 `#language-assets` and `#tab-corpus` hold a pointer to 语料库.

## Front pages

Every page outside 维护 is a title, at most one short line, then content. It shows
no attribute keys, data types, file paths, repository or tool names, ledger or
authorization numbers, hashes, snapshot names, 建设中 / 已规划 chips, tabs to
unbuilt parts, or provenance and refresh small print. A figure keeps one date
(截至 …). `front.css` holds their shared head, figure row and bar list.

- **产品信息** opens on **产品矩阵** (`product_matrix.html`, step 13, REV-53): the
  title, `<n> 款产品 · 更新于 <date>`, then the matrix read from the product-information
  snapshot; see [knowledge-pages.md](knowledge-pages.md#product-matrix-page). The
  former 规模, 在哪里维护, 被谁使用, 来源与时间 and 质量与缺口 blocks, the kicker, the
  chips, the sub-labels and the page-foot provenance are gone, and so are the
  属性字典 tab and page and the 待核实与冲突 placeholder. The operator's value statement
  is shown on no page (2026-11-17).
- **产品知识** (`product_knowledge.html`): the title, one line, then the topics and
  cases. See [knowledge-pages.md](knowledge-pages.md).
- **语料库** (`asset_language.html`, `language_view`): the title, one line
  (已批准的术语和标准句，多语言对照 · 更新于 <date>), three figures (句对, 术语, 语言) and a
  table per language (语言, 句子 with a bar, 术语). The table lists the languages with pairs or terms, and the
  语言 figure is the number of rows it lists. Languages are named as the manual
  library names them (`settings.json` `language_labels`); a corpus language whose
  translation-memory code differs carries the library's code as `manual` in
  `system_workspace.yaml` (`corpus_view` `counts`, `terms`).
  With a snapshot that carries `approved_by_language` in both blocks (schema
  `hello-docs-tm-corpus/v1.1`, see [system-workspace.md](system-workspace.md#language-assets-block)) the page shows
  approved entries only (`corpus_view` `approved_only`): the 句对 and 术语 figures are the approved counts, the table
  shows each language's approved pairs and terms and lists only languages with at least one, and the
  其中 … 已批准 lines go; the 知识资产 card shows the same approved pair figure. A `v1` snapshot renders as before
  (all entries, with how many are approved). 系统建设's tiles keep the whole corpus.
  Beside the table (below it on a phone), **Agent 怎样用这份语料库** (`#agent-uses`; operator,
  2026-11-17: 「这种可以用」) lists the three uses the operator works with today: agents edit Feishu cloud docs and
  Illustrator (`.ai`) files from the corpus, calling the repository's code themselves, with one example ask. The
  first draft followed the skill files (Word pre-translation, Markdown rewrite, write-back); the operator said those
  are no longer how the work is done. The skill entries now distinguish these on-request deliverables from direct editing ([REV-54](../manual_revitalization_execution.md#rev-54)).
  Change this wording with the operator, not from the skill files. The counts are pairs, never a
  percentage that could read as manual localization completion. Without a
  readable snapshot the page says 暂时没有可显示的语料数字. The terminology rules, the
  Web-manual language list and the staleness note left the page.
- **市场与政策** lost its count and review-date pills in the head; its line reads
  `<n> 条资料 · 更新于 <date>`. 产品知识's line reads `<n> 个知识点 · 更新于 <date>`, and its
  page-foot disclaimer is gone.

## 视觉媒体 (front)

`asset_media.html` (`asset_media.front_view`) is for colleagues: the title, one line (说明书里共用的图标和插图 ·
更新于 <build date>), a count per type, then the shared icons and illustrations as tiles, filtered by type and
searched by meaning (`_static/media-front.js`, `tests/media_front_ui.test.mjs`). A tile opens a larger view with
its type and, for a symbol the published manuals show, 用于 <n> 本说明书. The tiles are the 图标与素材 gallery of
the 设计规范 page (`design_assets.asset_gallery`) and its published copies under `workspace/design/assets/`;
a caption is the gallery note up to its first colon. No keys, hashes, paths, statuses or numbered blocks. Without
the design page the page says 暂时没有可显示的素材. The page's former section anchors (`#scale` … `#gaps`,
`#registry`, `#symbols`) forward to `workspace/design/index.html#assets-inventory`.

## The shared anatomy (maintenance pages)

视觉媒体's inventory (`_media_inventory.html`, the former 视觉媒体 page's body, using `_asset_layer.html`'s blocks) is
folded as 素材登记与共用符号明细 (`#assets-inventory`) at the foot of 设计规范 › 图标与素材, beside the gallery and
rules it counts. It holds six blocks with fixed ids, in this order:

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

**内容与表现** is no longer built: its address forwards to 设计规范, and its view
(`asset_layers.content_view`, with the chapter and component readers only it used)
was removed on 2026-11-17.

**视觉媒体's inventory.** `data/asset_registry.csv`: registered, finished, language-neutral and
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

## Curated data: `asset_layers.yaml` (slice 2)

`tools/rtd_portal_assets/asset_layers.yaml`, read by `tools/rtd/asset_layer_data.py` and
assembled with the layer views by `tools/rtd/asset_pages.py`, holds everything about the
layers that is not a figure:

- **Wording, each kept once.** `umbrella` (产品技术内容资产) and `main_line` (新说明书在工作台写作，是主线；
  扩大存量说明书的网页覆盖是积累线；产品信息矩阵是第一个要补全的资产。). The operator adopted both on
  2026-11-16 (positioning §1.2); a later change is a one-line edit here. `product_value` is the operator's
  own statement of the product matrix's value (2026-11-16; positioning §4.1). It is shown
  on no page (operator, 2026-11-17: 「我写的那段价值定位不用显示在页面上」); the data file
  keeps it, but no code loads it. `tests/test_rtd_asset_layers.py` and the full build in
  `tests/test_rtd_portal.py` read it from the file and check that no page shows it. Since the front cleanup `main_line` is
  no longer shown on 知识库首页; 系统建设 keeps its own 当前主线.
- **Status chips from ledger rows.** Each layer lists the REV rows that belong to it.
  The rows are read as 系统建设 reads them (`system_workspace.ledger_progress`) and
  the state maps to a portal status word (`CHIP_STATUS`: all done → 已验证, any done,
  active or verifying → 建设中, all planned → 已规划). A layer with no row, or whose
  rows are all deferred, shows no chip; a REV id the ledger lacks is an authoring error
  (a build warning, and the pages fall back to no chips, no main line and the old
  capability cards). Since the front cleanup the chip shows only on the 系统建设 layer
  card and the 维护 layer pages, always with the rows it comes from; front pages and
  知识库首页 show none.

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

## 知识库首页 and 系统建设

- **资产总览 / 知识库首页** (front cleanup, 2026-11-17; overview of 2026-11-18): the title 知识资产 and the line
  「让产品信息和生产资料持续积累、关联和复用。」 with the summary capsule (`asset_pages.front_summary`): 收录机型 (产品矩阵's
  model count), 正式说明书 (published Web manuals, model × market) and 覆盖语种 (the publish manifest's language
  count from `deliverables.publication_languages`, the same figure 说明书工作台 shows as 发布语言; no fallback to the
  corpus; 暂无 when the manifest is unreadable or a target names no language). Then six cards (`#now`;
  `asset_pages.front_cards`), each with an icon, an arrow, its name, one sentence naming only what its page holds
  (语料库 says 已批准 only when its figure counts approved pairs), one figure (暂无 when unreadable) and a count
  badge; the figure's date is only the badge's tooltip. The cards of a row share their row tracks (CSS subgrid), so
  dividers and figures line up when a badge wraps. With a share package, 分享资料 (`#shares`) follows. No status
  chips, eyebrows, footnotes or ledger references. The slice-2
  主线, 正在做, 定位与价值 statuses and 最近更新 left the page; 正在做 and 当前主线 stay on
  系统建设. The modules that fed them (`workspace_home.py`, `knowledge_updates.py`) and
  `workspace_home.yaml` were removed on 2026-11-17; `knowledge_updates.yaml` stays as the dated record
  `source_registry.yaml` names, read by no code.
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
`tests/asset_layers_ui.test.mjs` and `tests/media_front_ui.test.mjs` (the filters), and the real-Sphinx sidebar test
in `tests/test_rtd_portal.py` (each page's section, left list and breadcrumb, an
unplaced page selecting no section, the moved 属性字典 address, the front pages without chips or small print, the six blocks
in 设计规范's #assets-inventory, the 内容与表现 address forwarding to 设计规范, 视觉媒体 absent from the public build, and that the public build links no internal page);
`tests/test_rtd_site_shell.py` (placement of every page key, crumbs, optional sections, the public shell, 资产总览
first in 知识资产, the search form); `tests/test_rtd_workspace_home.py` (the home cards); `tests/test_rtd_review_site.py` (the review site's
top bar).
