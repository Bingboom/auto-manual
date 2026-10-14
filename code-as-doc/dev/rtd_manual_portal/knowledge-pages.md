# RTD portal: workspace entry and knowledge-base pages

Status: active · Part of the [RTD manual-center entrance](../rtd_manual_portal.md); its index lists the
other portal surfaces. Add new notes for this surface here, not to the hub.

## Personal workspace entry

The manual library root (说明书资料库) remains independent. The portal extension
also builds `/workspace/` (知识库 · 首页) as the knowledge-base entry page, in one
column from top to bottom:

- The page header links to the manual library (labelled 说明书资料库) for
  product, region, language and manual-content search.
- **Entry cards** in the sidebar's two groups after 知识库: 产品与市场
  (`#products`: 产品知识, 产品矩阵, 市场与政策) and 说明书生产 (`#production`:
  说明书工作台, 系统建设, 设计规范). A card has the sidebar entry's glyph
  and label and one line on what the page holds, and shows only when its sidebar
  entry does, so it never links to a page this build skipped. Cards carry no
  counts; those stay on their own pages. The sidebar test in
  `tests/test_rtd_portal.py` pins the cards to the sidebar's groups and order.
- **分享资料** (`#shares`) holds the share card for the bundled
  beginner-facing AI sharing package at `/ai-share/00_打开分享.html`.
- **最近更新** (`#updates`) lists dated changes, `YYYY-MM-DD · title / note`, from
  `tools/rtd_portal_assets/knowledge_updates.yaml`
  (`tools/rtd/knowledge_updates.py` reads it): the newest 8 entries whose page
  this build made, newest first, ties in file order. The date is the change's
  merge day, as `git log --date=short` shows the squash commit on main, and each
  entry cites `pr:<repo>#<n>` as evidence for reviewers (not shown). The list is
  curated because no build-time source carries per-page change dates: snapshot
  and manifest dates measure freshness, which 说明书工作台 and 系统建设 already
  show. An entry without a valid (unquoted) date reads 日期未记录 and sorts last;
  one with an unknown page, an empty title or note, or a bad anchor is dropped.
  Both log `Knowledge home update skipped`, and the build date is never shown
  instead. An unreadable file leaves 暂无更新记录。 A PR that adds a knowledge
  page, or changes one in a way readers should notice, adds its entry there.

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
figures therefore keep working without another host. The workspace, sharing
package and manual library share the RTD project's visibility settings; the
workspace path is navigation, not a separate access-control boundary.

The workspace exists in every combined portal build; knowledge pages link back
to the manual center, but the manual-center homepage does not link into the
workspace. The system page lives inside it. The sharing package is an
optional entry. Without `ai-share/00_打开分享.html`, the 知识库首页
(`workspace/index.html`) hides its 分享资料 section (`#shares`, the share card)
and the 最近更新 rows (`#updates`) that link to the package. Nothing else changes.
分享资料 and 最近更新 are sections of the 知识库首页, not sidebar entries: the
sidebar lists pages only, so each entry is marked current on its own page.

Rollback: revert the portal extension's RTD activation and rebuild. Frozen
content, QR aliases and nested manual URLs are unchanged.

## Public manuals project (site role)

One frozen `docs/publish/web` source can feed two Read the Docs projects, so
the manuals can be public while the knowledge base stays internal. Each
project selects its half with the `RTD_SITE_ROLE` environment variable (Sphinx
config `rtd_site_role`); `.readthedocs.yaml` is shared and unchanged.

| `RTD_SITE_ROLE` | Builds | Intended project |
| --- | --- | --- |
| unset or `combined` | everything: manual center, manuals, short aliases, search, `/workspace/`, knowledge pages, `/ai-share/` | the existing private project (`ht-docs-ht-manuals`) |
| `manuals` | manual center, manuals, short aliases, search, `manual-knowledge.json`, deployment receipt; no `/workspace/`, `/products/`, `/market/` or `/ai-share/` output, and no internal sidebar data is built | a second project whose `latest` version is set to Public |

Any other value fails the build. Absolute URLs (canonical, `hreflang`,
`og:url`, alias canonical) use the serving project's
`READTHEDOCS_CANONICAL_URL`, which Read the Docs sets per project and version
(custom domains included); `site_base_url` in the portal settings is the
fallback for local builds. Each project therefore gets its own canonical root
without a per-project settings file, and the public domain can be chosen
later without a code change.

Set the public project's version to Public only after its first `manuals`
build succeeds: before that, the project has no pages to expose, and an
unset role would publish the internal pages. Knowledge pages in the combined
site keep linking to the manuals inside the same private site.

## Deliverables page

`/workspace/deliverables/` (说明书工作台) is the production navigation surface.
The stable URL is retained. Below the hero, the key-metric row (网页说明书,
语言版本, Word 云文档, 印刷交付包) sits above four tabs: **交付物** (the
deliverables matrix, open by default), **数据统计** (see [数据统计](#数据统计)),
**工作入口** and **生产与资产**; see
[Page layout](manual-center.md#page-layout). The 工作入口 tab draws the work map
**Content Authority → Source Binding → Assembly / IR → Human + Machine Surface**:
either content authority (structured sources or a Git-native manual source)
passes through source binding into assembly, which derives both surfaces.
Selecting a node reveals its work destinations, operating guides and next step.
The 生产与资产 tab holds the production evidence. The system workspace remains
the capability/progress view; this page links to it.

Each fact has one page. This page owns what is published or in production
now, so the 网页说明书 key metric carries the books per region (欧规 n · 美规 n,
largest first, labelled by the system contract's `focus.regions`); 系统建设
shows no publication count and links here. 系统建设 owns the corpus and
skeleton totals: the 语料库 and 模板与骨架 cards and the asset ledger keep their
maintenance links and adoption status and point to 系统建设「语言资产」
(`#tab-corpus`) and 「骨架扩展」 (`#lane-skeletons`). The 数据更新时间
disclosure keeps both snapshot freshness spans that Workspace Data Verify reads
and links the registry's rules (系统建设「数据来源」, `#sources`). The pointers
show only when the system page is built.

`tools/rtd_portal_assets/manual_workbench.html` owns the curated navigation links,
using business destinations from `user-guide/two_plane_map.md` and the README's
existing authoritative guides. Templates/configuration link to auto-manual;
business Actions and PRs link to Hello-Docs. Feishu links require the user's
existing access. This is navigation only: it does not launch jobs, access live
APIs, invent per-target review links or duplicate capability status. Changes to
business coordinates must update the authoritative topology and this entry map.

All links and panels are rendered at build time. `manual-workbench.js` only
switches the selected panel, using native buttons and `aria-pressed`; without
JavaScript, every panel stays visible. Styling is scoped to the workbench and
reuses the workspace shell. The key-metric cards link to `#deliverables`, the
交付物 tab that holds the matrix.

In the 交付物 tab, the delivery data is grouped by model, with one row per
region and one column per format:

| Column | What it links to | Source |
| --- | --- | --- |
| 网页手册 | each language edition's page on this site | `docs/publish/publish_manifest.json`, read at build time |
| 印刷交付包 (IDML + PDF) | the Publish handoff ZIP in the Feishu wiki | the build table's `idml_file` column, through the snapshot |
| Word 云文档 | the Draft Word output, imported as a Feishu cloud doc | the build table's `飞书云文档` column, through the snapshot |

- Each cell holds one chip per language, with its version. 整本 marks a
  whole-book document that carries all its languages in one file.
- The PDF has no link of its own: it ships inside the handoff ZIP, and the
  publish tree refuses PDF files.
- Two selects filter the table by model and by region. On a phone, the table
  remains a matrix in a keyboard-focusable horizontal scroll region, with the
  region column pinned. Long version identifiers wrap instead of widening the page.
- Product names come from the manual center. A model that the manual center
  does not list shows its code only. The build table's own product names are
  not used, because some of them are wrong or empty.

The Feishu links open only for signed-in Feishu users, but anyone who can open
this page sees their addresses. The operator chose this on 2026-09-25
(「直接放飞书链接」), while the site was public. Since 2026-10-13 the site has
been private (Read the Docs for Business), but the operator can make it public
at any time, so treat these addresses as published. The page accepts only
https links on a Feishu or Lark host.

### Refreshing the Feishu snapshot

RTD never reads Feishu, so the two Feishu columns come from
`tools/rtd_portal_assets/deliverables_snapshot.json`, the snapshot of the
source registry's `deliverables_feishu` domain. Refresh it through a PR
after new Draft or Publish builds:

```bash
python -m tools.rtd.deliverables export --cli-bin "lark-cli --profile prod" --as bot
python -m tools.rtd.deliverables check
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
- A snapshot older than the `deliverables_feishu` domain's `stale_after_days`
  in `source_registry.yaml` shows 待复核, and
  `check` warns about it.
- The page always renders. Every knowledge page lists it first under 说明书生产,
  and the 知识库首页 links to it from its 说明书生产 group too.

### 数据统计

The 数据统计 tab (`#statistics`, after 交付物) holds what the 系统数据 page
counted: what the repository holds about the manuals, narrowed by region and
model. `production_statistics.html` renders it from the context that
`tools/rtd/system_data.py` builds once per build; the page receives it as
`statistics`, a separate key because this page's own `regions` and `models`
have another shape. The tab loads `_static/system-data.js` and
`_static/system-data.css`.

- **Rows are read at build time.** `tools/rtd/system_data.py` reads
  `docs/publish/publish_manifest.json` (one row per published Web route, as the
  交付物 tab reads it), `data/model_capabilities.csv`,
  `data/model_languages.csv`, the RST page count under
  `docs/_review/<model>/<region>` and `data/asset_registry.csv` (category,
  status without its leading mark, model, region). Nothing is snapshotted or
  committed for the tab; a data change appears on the next RTD build.
- **Cards:** headline counts (models with Web manuals and their regions,
  languages, targets with review pages, asset registry entries and their 成品
  share; 网页说明书 and 语言版本 stay in the key-metric row above the tabs);
  发布 (a model × language matrix, per-language and per-region bars and the
  sortable, searchable publication table, all counted in 语言版本, one table row
  per route); 机型能力 (the target × capability matrix and each capability's
  coverage); 素材 (registry entries by status, category and model).
- **Published models only.** The 机型能力 cards list the targets of models
  with at least one published 说明书 (`published_targets`, which reads the
  models off `production_evidence.publication_facts`): every region of such a
  model stays, and an unpublished model drops out. On the 2026-10-12 manifest
  29 of 37 targets (9 of 16 models) remain. The 产品矩阵 page's 功能矩阵 is not
  filtered; it still lists every model of the capability table.
- **Asset counts are registry entries.** 素材登记 counts the rows of
  `data/asset_registry.csv`, not deduplicated artwork; the 生产与资产 tab's
  Artwork Assets stays Not tracked yet.
- **Filters are client-side.** The rows travel as one JSON block
  (`<` escaped) and `_static/system-data.js` filters and counts them. A region
  dropdown, a model dropdown and clicks on a model (matrix rows, capability
  rows, asset bars, table rows) or a region bar narrow every card; clicking the
  same item again clears it. The selection is kept in the URL query
  (`?region=EU&model=JE-1000F#statistics`). An asset whose model or region is
  `ALL` counts under every model or region. The headline counts are distinct
  models, regions and languages, so a repeated route counts once; 语言版本 and
  说明书 stay with the key-metric row, which takes them from
  `production_evidence.publication_facts`, the counting every page shares (see
  [System workspace](system-workspace.md)).
  The script fills only the tab's own counts. The tab is hidden at load, so
  its charts first draw at a 260px fallback; a `ResizeObserver` on the panel
  redraws them when the tab opens or its width changes.
- **Without JavaScript** the whole-repository counts and the publication table
  still render; the charts show a note instead.
- **Failure:** without a readable publish manifest the 发布 cards show 无数据,
  and so do the 机型能力 cards (无数据：发布清单当前不可读，无法确定已发布型号), since
  the published models are unknown; the other cards still render. A CSV
  missing a column, a capability value other than `TRUE`/`FALSE`, a target key
  that is not `<model>_<region>`, or an asset row without status, model or
  region leaves the tab with 机型能力表或素材登记表不可读，构建日志有告警 and the
  Sphinx warning `Workbench statistics show no data`; the rest of the page
  renders. `tests/test_rtd_system_data.py` fails first. The counting functions
  have Node tests in `tests/system_data_ui.test.mjs`.

## Design system page

`/workspace/design/index.html` (设计规范; URL, template and module keep the
design-system name) shows the manual's visual rules in six tabs: 概览, 颜色, 字体,
组件, 图标与素材 and 印刷规格. It is listed under 说明书生产; the public manual
library does not link to it.

- **Values are live.** At build time `tools/rtd/design_system.py` reads the
  stylesheet that `tools/web/stylesheets.py` assembles
  (`tools/rtd/design_system_css.py`). Colours, contrast ratios, type sizes and
  the 760px overrides come from the declarations of named selectors. A small
  line under the counts gives the versions in use: the stylesheet's SHA-256 and
  the print table's token hash. A stylesheet change appears on the next RTD
  build without editing the page.
- **Previews are live.** Each component preview is an iframe document that
  loads that same stylesheet, copied to `/workspace/design/web_manual.css`, and
  wraps its markup in `#furo-main-content`. Art is copied from the repository's
  shared asset folders, and per-target art is a labelled placeholder SVG. Frames
  size themselves to their content (`_static/design-system.js`); without
  JavaScript they keep their declared height.
- **The asset library is live.** `tools/rtd/design_assets.py` lists the 图标与素材
  groups from the shared symbol and button manifests
  (`docs/renderers/web/assets/shared/{symbols,buttons}/manifest.json`), the
  shared LCD folder, and named files from the Word and LaTeX asset folders. The
  files are copied to `/workspace/design/assets/<group>/`; each tile shows the
  file's format, size, PNG dimensions and alpha channel, or the colours an SVG
  uses.
- **Print values are live.** `tools/rtd/design_print.py` reads
  `data/layout_params.csv` through `tools.render_contract.load_layout_tokens`:
  page geometry, type sizes and leading, CMYK swatches and component geometry.
  It shows base values only: `lang_*` density overrides and the IDML overlay
  tables a config may add are not applied. The base tokens are also written as
  CSS custom properties to `/workspace/design/print/tokens.css` for an
  actual-size odd-page preview (`print/page.html`). Weights are not in the
  table; the LaTeX modules and IDML styles own them.
- **Notes are data.** The Chinese text, the selectors and keys each value comes
  from and the preview markup live in `tools/rtd_portal_assets/design_system/`
  (`content.yaml`, `previews/<id>.html`, `print_page.html`, `print_page.css`).
  Previews may use only `asset:<group>/<file>` art and `slot:<w>:<h>:<label>`
  placeholders: no remote, data or absolute URLs. The print preview may use only
  tokens the table defines.
- **Drift fails closed.** The build fails the page, and
  `tests/test_rtd_design_system.py` fails first, when any of these happen:
  - a selector, a component's `requires` class or an asset no longer exists;
  - an asset note names a file or key that no longer exists;
  - a shown or copied file carries a hash the symbol manifest has withdrawn;
  - a print key, a print colour's screen token, or a token the print preview
    uses is gone.

  A failed page is skipped with a Sphinx warning and its sidebar entry
  disappears, rather than showing stale rules. Additions, such as a new symbol
  or a new CSV row, do not fail; they appear in the gallery, or wait for a
  label in `content.yaml`.

## System data page

The standalone 系统数据 page and its sidebar/home entries have been removed.
Its statistics live in the 说明书工作台 tab [数据统计](#数据统计), and its
工程规模 in the 系统建设 tab 工具与工程规模 (see
[Engineering scale](system-workspace.md#engineering-scale)).

In combined builds, `/workspace/data/` and `/workspace/data/index.html` still
serve a minimal `moved_page.html` compatibility redirect. It uses
`location.replace` to open `../deliverables/index.html#statistics`, preserving
the complete query string (including `region`, `model`, encoding and repeated
parameters). Old fragments are replaced by `#statistics` so the tab opens.
The visible target link is updated before navigation; without JavaScript it
remains a clickable, unfiltered fallback. The redirect has no site shell or
data dependency and is built even if statistics are unavailable. The manuals
role emits neither the redirect nor any workspace pages. Historical update
entries now link directly to the workbench statistics tab; the retired
`system-data` update-page key is removed.

## Product matrix page

`/products/matrix.html` (产品矩阵) lays out the products the published Web
manuals describe. It is listed under 产品与市场, after 产品知识; the
public manual library does not link to it.

- **Read at build time.** `tools/rtd/product_matrix.py` reads the publish
  manifest (each model's markets, languages and routes), then one published
  manual per model: English first, then `language_order` and `region_order` in
  `tools/rtd_portal_assets/product_matrix.json`. From the table after its
  SPECIFICATIONS / 仕様 / 规格 / 規格 heading it takes capacity, AC rated and
  surge output (a Total row wins over the largest single port), cycle life,
  weight, solar STC power, IP rating and output power, as the manual prints
  them. Names come from the manual-center catalog without the model code or the
  manual-type suffix; product lines come from the `navigation` groups in
  `settings.json`; capability switches from `data/model_capabilities.csv`.
  Nothing is snapshotted; a published manual change appears on the next build.
- **Curated config.** `product_matrix.json` holds only what no manual states:
  the lines and accessory groups (navigation ids, or a new title), `assign` for
  models the navigation does not list (shown with *), `tiers` (capacity
  columns), `names` and `notes` overrides, `companions` (products without a
  manual of their own, cited from another manual) and `pairings` (partners a
  manual names). A companion or pairing partner is shown only while the cited
  manual's text still contains its `match` text (or its label).
- **Backup lines need the manual's words.** A line marked `"evidence": true`
  (家庭备电, 专用场景备电) takes an assigned model only as
  `{"line": ..., "evidence": "<quote>"}`, and only while the model's source
  manual contains that quote (case and spacing ignored). The card tooltip shows
  the manual sentence. A product name is never the reason: HomePower 3000 and
  HomePower 3600 Plus describe UPS like any power station but no home backup, so
  they sit under 通用电器供电 and 可扩容储能. When a quote disappears, the model
  moves to 其他 with a Sphinx warning. Navigation-listed models (FridgeGuard in
  专用场景备电) are the operator's own grouping and need no quote.
- **Operator decisions win over wording.** A manual sentence is necessary, not
  sufficient: HomePower 5000 Plus carries a Smart Home Backup System guide, but
  the operator ruled on 2026-10-13 that it is not a backup product, so it sits
  under 可扩容储能. `{"same_as": "<model>"}` places one product sold in another
  market where the operator placed it: SlimPower H1 (JE-1000E-WH, JP) is
  FridgeGuard (JE-1000E-SIL, US) under another name, so it follows FridgeGuard
  into 专用场景备电. `same_as` must name a navigation-listed model and takes no
  line of its own; it is for one product's market versions, never for products
  that merely share a platform.
- **Sections:** headline counts (models with Web manuals, with 共 N 本网页说明书 ·
  M 个语言版本 from `production_evidence.publication_facts`; power stations and
  batteries; accessories; 更多型号持续维护中 when the capability
  table has models without a Web manual), a market filter, the line × capacity
  grid, accessory groups, the capability matrix (all / some / no regions), the
  sortable spec table, pairings and data sources.
- **JavaScript** (`_static/product-matrix.js`) only dims what a market has no
  Web manual for and sorts the spec table; without it every product shows and
  the filter stays hidden. Node tests: `tests/product_matrix_ui.test.mjs`.
- **Failure:** without a readable publish manifest the page and its links are
  skipped quietly (the bootstrap build has none). A config naming an unknown
  group or tier shape, or a malformed capability CSV, skips the page with a
  Sphinx warning. A model with no group, an unreadable manual, a missing
  capacity or a pairing the manual no longer names is a Sphinx warning while
  the page still renders (an unplaced model is listed under 其他).
  `tests/test_rtd_product_matrix.py` covers the parsing and the rules.

## 产品知识

产品知识（产品案例是其末节）、市场与政策都与说明书共用同一个 RTD 项目（2026-10-06 定为同项目发布）。2026-10-13 起 Hello-Docs 转为私有仓库，站点改由 Read the Docs for Business 托管于 `https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/`，访问需要登录并具备项目权限；页面路径须带 `/en/latest/` 前缀，例如 `/en/latest/products/knowledge.html`。知识库可以跳转到说明书，说明书首页、侧栏和顶部不提供知识库入口；分享知识页直达链接给有权限的人。

`/products/knowledge.html` 提供围绕已发布产品的最少必要技术知识，按标签、型号和区域筛选。通用功能原理、常见误区与阅读提示维护在 `tools/rtd_portal_assets/product_knowledge.json`。适用产品取产品矩阵的定位层（`tools/rtd/product_matrix.py` 的 `positioning_groups`）：首页 `navigation` 分组加上 `product_matrix.json` 的产品线与 `assign`（备电线的说明书证据句只在产品矩阵页核对），导航未收录的已发布型号因此也有对应知识，型号选择只列出至少有一项知识的产品。`product_matrix.json` 缺失或格式有误时，知识页只用 `navigation` 分组并给出 Sphinx 警告，条目引用的其他分组（如 `homebackup`）按空组处理并在警告中列出，构建不中断。每项的说明书入口只从当前冻结发布目录取得，优先现有英文页，缺少英文时使用实际可用语言，不拼接或猜测型号路径。

通用知识不构成某型号内部电路、芯片或跨产品兼容性的认定，也不把教程中的算例当作产品实测。标签和型号过滤只控制阅读范围；技术值、操作和兼容条件仍以对应地区说明书为准。未启用 JavaScript 时全部知识条目与来源链接可读。工程面的模板、交互和课程词条与业务面的 `docs/knowledge/**` 个人分享文章分别维护。

产品知识采用纵向列表，每项将可访问的 SVG 功能示意与原理、产品应用、限制和来源放在一起；AC 输出单独说明共享功率、启动冲击、输出匹配、升功率、保护与旁路切换。示意图不代表某型号内部电路。

AC 教学图使用可访问的静态 SVG 电气示意：H 桥、LC 滤波、并联负载和联锁切换。低压升压、隔离、体二极管与接地等未展开，不能当成实际产品原理图。JHP-3600C US 的备电案例独立呈现，来源链接与知识条目一样从冻结发布目录取得，目录中没有 JHP-3600C/US 时整段不显示；分相、旁路、ATS/MTS 与级联条件按说明书描述。

## 市场与政策

`/market/policy.html` 与产品知识并列，用纵向列表记录“政策变化 → 原理解释 → 产品影响”。国家、主题、资料状态和关键词可组合筛选。每条记录显示适用地区和时间；“政策要点已核实”只表示政策事实已查官方出处，产品影响单独标注为分析判断。官方出处以简短参考链接呈现；页面不展示原始资料截图、整理流程或核对过程说明，未经核实的信息仍保留状态标识。

工程面的 `tools/rtd/market_policy.py` 读取业务内容目录下的 `market-policy/records.json`（`schema_version: 1`）。默认业务目录为 Hello-Docs 的 `docs/knowledge/`，本地预览可用 `rtd_knowledge_dir` 指向临时目录。该快照及原始截图不放入 auto-manual；当前未接入飞书多维表，也不在线读取飞书。

记录保留 `id`、国家/地区、标题、时间、`verified`/`unverified`/`demand` 状态、标签、变化、原理、影响和核对日期；可选 `boundary` 记录必要的适用条件，不填时页面不显示该段；`sources` 保存出处类型、标题、HTTPS 链接和核对范围，但页面只展示标题与链接。已核实记录至少需要一条官方出处，`demand` 只代表业务需求依据，其第一段显示“需求变化”。未核实线索和业务需求可用非空 `evidence_note` 保存录入依据，该字段不在页面显示，也不能代替已核实政策的官方出处。`knowledge` 关联产品知识锚点。锚点不是 `tools/rtd_portal_assets/product_knowledge.json` 中现有的条目 id 时，构建给出注明记录与锚点的 Sphinx 警告，但不因此失败。可选 `flow`、`image` 和 `image_alt` 不在页面渲染；源图只参与本地审阅校验，构建不复制到网站，本次业务快照不上传原始截图。缺少快照显示空页；记录无效则构建失败。未启用 JavaScript 时全部记录与参考链接仍可读。
