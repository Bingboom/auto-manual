# RTD portal: workspace entry and knowledge-base pages

Status: active · Part of the [RTD manual-center entrance](../rtd_manual_portal.md); its index lists the
other portal surfaces. Add new notes for this surface here, not to the hub.

## Personal workspace entry

The manual library root (说明书资料库) remains independent. The portal extension
also builds `/workspace/` (知识库 · 首页) as the knowledge-base entry page. Its
2026-11 design (an operator-approved design canvas) answers, from top to bottom,
what has built up and can be reused, what is being done now, and where to go:

- The page header gives the web manuals' positioning in one line (the `tagline`
  of `web_manual_value.yaml`).
- **现在** (`#now`, `tools/rtd/workspace_home.py`) opens with 「已积累的可复用资产」:
  four cards, each the amount built up so far and how much of it can be reused
  now. Every figure is read from the source that owns it; an unreadable source
  shows its card as 无数据 and never fails the build.
  - 翻译语料: the translation-memory snapshot as 系统建设 shows it (句对, 术语,
    languages, approved share); links to the 语言资产 tab.
  - 图片素材: `data/asset_registry.csv`: finished assets, the share without
    language-specific text (语言维度 中立) and those every model uses (适用机型
    ALL); links to the workbench 数据统计 (`#statistics`, in its 交付物 tab), where the
    registry is listed.
  - 通用章节: the shared chapter templates under `docs/templates/page_shared`,
    counted per page and language, with the warranty, troubleshooting, charging
    and storage chapters named.
  - 产品知识: the topics in `product_knowledge.json`, with a growth line drawn
    from each topic's `added` date; the line is left out while any topic lacks
    one.

  Below the cards, 当前主线 lists the 系统建设 focus lanes marked `now` (titles
  only) and 正在做 shows 系统建设's own list (`focus.doing` in
  `system_workspace.yaml`), so the two pages always agree; without the 系统建设
  page neither shows. `tools/rtd_portal_assets/workspace_home.yaml` (schema v2)
  holds only the note beside the cards and refuses a `doing` list of its own. A
  malformed `workspace_home.yaml` fails the build.
- **去哪里** (`#doors`) has one card per sidebar group after 首页: 说明书
  (说明书资料库, 搜索说明书正文), 产品与市场 (产品知识, 产品矩阵, 市场与政策) and
  说明书生产 (说明书工作台, 系统建设, 设计规范). Each entry carries its sidebar
  icon and one line on what is there. A link shows only when its sidebar entry
  does, so it never points to a page this build skipped, and the cards carry no
  counts. The sidebar test in `tests/test_rtd_portal.py` pins the cards to the
  sidebar's groups and order. Under the cards, **分享资料** (`#shares`) is one
  link to the bundled beginner-facing AI sharing package at
  `/ai-share/00_打开分享.html`.
- **定位与价值** (`#value`) holds the four theme cards, each with its status, one
  sentence and its facets with status marks (a facet's note is its row's
  tooltip), under a legend of the marks used; see
  [网页说明书的定位与价值](web-manual-value.md).
- **最近更新** (`#updates`) lists dated changes, one line each (`YYYY-MM-DD`,
  page · title, the note cut to fit), from
  `tools/rtd_portal_assets/knowledge_updates.yaml`
  (`tools/rtd/knowledge_updates.py` reads it): the newest 5 entries whose page
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

The shared shell (`_site_shell.html`) draws one line icon set (24 grid, 1.75
stroke, round caps, `currentColor`); pages import its `icon()` macro, and a path
marked `ic-accent` is the one detail a page may tint (the home's entry cards
do). 首页 opens the internal sidebar without a group label. Knowledge pages set
`body.app.kb`, which re-tints the shell tokens and the `workspace.css` page
tokens to the 2026-11 palette: a cool ground (`#f3f6fa`), white cards and a
terracotta accent (`#a64e24`). The 说明书资料库 pages keep the brand orange. The
numbers use the system font stack; no web font is loaded.

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
to the manual center. In the combined role the manual-center homepage links into
the workspace only through the shared shell and the 定位与价值 band; in the
public role it links nowhere internal. The system page lives inside it. The sharing package is an
optional entry. Without `ai-share/00_打开分享.html`, the 知识库首页
(`workspace/index.html`) hides its 分享资料 link (`#shares`)
and the 最近更新 rows (`#updates`) that link to the package. Nothing else changes.
分享资料 and 最近更新 are sections of the 知识库首页, not sidebar entries: the
sidebar lists pages only, so each entry is marked current on its own page.

Rollback: revert the portal extension's RTD activation and rebuild. Frozen
content, QR aliases and nested manual URLs are unchanged.

## Public manuals project (site role)

One frozen `docs/publish/web` source can feed two Read the Docs projects, so
the manuals can be public while the knowledge base stays internal. The role
is resolved by `tools/rtd/site_role.py` from the `RTD_SITE_ROLE` environment
variable (Sphinx config `rtd_site_role`) and the building project;
`.readthedocs.yaml` is shared and unchanged.

| Role | Builds | Who builds it |
| --- | --- | --- |
| `combined` | everything: manual center, manuals, short aliases, search, `/workspace/`, knowledge pages, `/ai-share/` | on Read the Docs, only a project listed in `PRIVATE_RTD_PROJECTS` (today the private `ht-docs-ht-manuals`), when `RTD_SITE_ROLE` is unset or `combined`; local builds by default |
| `manuals` | manual center, manuals, short aliases, search, `manual-knowledge.json`, deployment receipt; no `/workspace/`, `/products/`, `/market/` or `/ai-share/` output, and no internal sidebar data is built | every other Read the Docs project, with or without `RTD_SITE_ROLE=manuals` (the public `ht-docs-ht-user-manuals` sets it); any build with `RTD_SITE_ROLE=manuals` |

The rule fails closed (2026-11-04). Until then an unset variable meant
`combined`, and the public project, created without the variable, served the
whole knowledge base until `RTD_SITE_ROLE=manuals` was added and it rebuilt.
Now a project missing from the list builds the manuals only, and
`RTD_SITE_ROLE=combined` on it fails the build. Adding a private project is a
reviewed PR to `PRIVATE_RTD_PROJECTS`. Each build logs `RTD site role: …` with
the reason.

The role decides what a build contains, not who can open it. That is each
project's Privacy level in Read the Docs: keep the private project's versions
Private.

The home page's 定位与价值 band switches its copy with the role, and its internal
page is built only in the combined role; see
[网页说明书的定位与价值](web-manual-value.md).

Any other `RTD_SITE_ROLE` value fails the build. Absolute URLs (canonical, `hreflang`,
`og:url`, alias canonical) use the serving project's
`READTHEDOCS_CANONICAL_URL`, which Read the Docs sets per project and version
(custom domains included); `site_base_url` in the portal settings is the
fallback for local builds. Each project therefore gets its own canonical root
without a per-project settings file, and the public domain can be chosen
later without a code change.

Check a new project's first build before setting its version to Public.
Knowledge pages in the combined site keep linking to the manuals inside the
same private site.

## Deliverables page

`/workspace/deliverables/` (说明书工作台) is the production navigation surface.
The stable URL is retained. The page counts Web manuals only (operator, 2026-11-09:
「飞书云文档的交付不纳入统计了 现在只统计网页文档的」). Since the 2026-11 redesign the title
carries one chip per shown snapshot (语料, 网页进度: its date, and its state when not
有效; `workspace_freshness.SHOWN`) and a link to 系统建设「数据来源」. Below it four
Web-manual totals share one card: 网页说明书 with the books per region and 语言版本
with the published languages (the publish manifest), 审核中 and 待转 (the 网页进度
snapshot, dated). Then the **常用入口** strip: the structured production data
(产品与规格, 文案与变量, 翻译与术语, 插图资产) and the Git-native manual sources
(冻结发布源, 评审稿, 来源声明), from `_work_links.html`. Three tabs follow: **进度**
(网页说明书进度, open by default), **交付物** (the coverage matrix and
[数据统计](#数据统计)) and **资产与证据** (the asset cards, the evidence table and
快照与校验, see [生产与复用证据](../workspace_production_evidence.md)); see
[Page layout](manual-center.md#page-layout).

The work map **Content Authority → Source Binding → Assembly / IR → Human +
Machine Surface** (工作入口, `manual_workbench.html`) moved to 系统建设「能力与架构」
(`#work-map`); the 常用入口 strip links there as 全部工作入口. Either content
authority (structured sources or a Git-native manual source) passes through source
binding into assembly, which derives both surfaces. Selecting a node reveals its
work destinations, operating guides and next step. The system workspace remains
the capability/progress view; this page links to it.

The page's stylesheet and script links carry `?v=<content hash>`
(`deliverables.asset_versions`), as the system page's carry the revision: the
files keep their names, so an unversioned link lets a browser or the CDN style a
new page with an old stylesheet (2026-10-23, the 审核中 table showed unstyled).

Each fact has one page. This page owns what is published or in production
now, so the 网页说明书 key metric carries the books per region (欧规 n · 美规 n,
largest first, labelled by the system contract's `focus.regions`); 系统建设
shows no publication count and links here. 系统建设 owns the corpus and
skeleton totals: the 语料库 and 模板与骨架 cards keep their maintenance links and
adoption status and point to 系统建设「语言资产」
(`#tab-corpus`) and 「骨架扩展」 (`#lane-skeletons`). The snapshot chips keep the
`data-workspace-source` freshness marks that Workspace Data Verify reads;
资产与证据「快照与校验」 (`#snapshots`) lists each snapshot's date, state, hash and
update run and links the registry's rules (系统建设「数据来源」, `#sources`). The
pointers show only when the system page is built.

`tools/rtd_portal_assets/manual_workbench.html` owns the curated navigation links
(their shared destinations, also used by the 常用入口 strip, are in `_work_links.html`),
using business destinations from `user-guide/two_plane_map.md` and the README's
existing authoritative guides. Templates/configuration link to auto-manual;
business Actions and PRs link to Hello-Docs. Feishu links require the user's
existing access. This is navigation only: it does not launch jobs, access live
APIs, invent per-target review links or duplicate capability status. Changes to
business coordinates must update the authoritative topology and this entry map.

All links and panels are rendered at build time. `manual-workbench.js` only
switches the selected panel, using native buttons and `aria-pressed`; without
JavaScript, every panel stays visible. Styling is scoped to the workbench and
reuses the workspace shell. The delivery totals link to `#deliverables`, the
交付物 tab that holds the matrix.

The 进度 and 交付物 tabs show Web manuals only (2026-10-19). 进度 is
网页说明书进度, described on [its own page](web-progress.md); 交付物 opens with its
coverage matrix (step 8 of the 2026-11 redesign, `web_progress_matrix.html`): one line
per converted model, its code and 商品简称, grouped by the 说明书资料库's categories
(`web_progress.regroup` over `portal_navigation.library_view`, drafts-only models
first). A row opens its language versions underneath: per market, each language as
its display code (en-US …) and short version (a Git package's date, `1027`), linked
to its page, with its 网页文档 row in Feishu; then its review versions and the
markets still 待转. This replaces the former 语言版本明细 table. Category chips, a
model or 简称 search and 只看还有待办 filter the rows; without a filter each group
shows its first five rows until 显示全部 (`web-progress.js`; without JavaScript
every row shows and no detail opens). Product names come from the manual center.

The Feishu snapshot below feeds no page since 2026-11-09: the workbench no
longer counts the Word 云文档 and 印刷交付包 deliveries, nor shows the snapshot's
date or alerts on its age. It stays refreshable until the operator retires it,
and Workspace Data Verify still compares its hash in the deployment receipt but
no longer looks for its chip on the page. Its links stay in the snapshot: the
operator chose on 2026-09-25 to list them (「直接放飞书链接」), the site can be
made public at any time, and only https Feishu or Lark links are accepted.

### Refreshing the Feishu snapshot

RTD never reads Feishu, so the two Feishu formats come from
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

- Without a publish manifest, 网页说明书进度 says 发布清单当前不可读 and the
  coverage matrix is left out; with an empty one the matrix says
  发布清单里还没有网页说明书.
- The Feishu snapshot is not read for the page, so an unsound or old one
  changes nothing there; `check` still reports it.
- The page always renders. Every knowledge page lists it first under 说明书生产,
  and the 知识库首页 links to it from its 说明书生产 group too.

### 数据统计

数据统计 (`#statistics`, the last section of the 交付物 tab) holds what the 系统数据 page
counted, as five cards counted at build time (step 8 of the 2026-11 redesign):
`tools/rtd/system_data.py` builds the context once per build and the page receives
it as `statistics`. Per model, the coverage matrix above is the place to look, so
the tab has no region or model filter.

- **Rows are read at build time.** `tools/rtd/system_data.py` reads
  `docs/publish/publish_manifest.json` (one row per published Web route, as the
  交付物 tab reads it), `data/model_capabilities.csv`,
  `data/model_languages.csv`, the RST page count under
  `docs/_review/<model>/<region>` and `data/asset_registry.csv` (category,
  status without its leading mark, model, region). Nothing is snapshotted or
  committed for the tab; a data change appears on the next RTD build.
- **Cards:** 按区域 and 按语言 (语言版本 per region and per language, largest
  first, languages as display codes, the eight largest drawn and the rest listed),
  最近发布 (the six newest routes; the full table of every route opens under the
  cards, searchable and sortable by `_static/system-data.js`), 能力覆盖率 (each
  capability's share of the published targets, `coverage`) and 素材登记 (registry
  entries by status, 隔离 and 缺失 marked, and by category). The bars are plain
  elements; no chart is drawn in the browser and no JSON block is embedded.
- **Published models only.** The capability coverage counts the targets of models
  with at least one published 说明书 (`published_targets`, which reads the
  models off `production_evidence.publication_facts`): every region of such a
  model stays, and an unpublished model drops out. The 产品矩阵 page shows a
  model's switches in its product's detail; the coverage card links there.
- **Asset counts are registry entries.** 素材登记 counts the rows of
  `data/asset_registry.csv`, not deduplicated artwork; the 资产与证据 tab's
  Artwork Assets stays Not tracked yet.
- **Without JavaScript** every card and the full table (newest first) still render;
  only the search box stays hidden.
- **Failure:** without a readable publish manifest the publication cards and the
  capability coverage show 无数据 (the published models are unknown) and the
  素材登记 card still renders; with an empty one, 发布清单里还没有网页说明书. A CSV missing a column,
  a capability value other than `TRUE`/`FALSE`, a target key that is not
  `<model>_<region>`, or an asset row without status, model or region leaves the
  tab with 机型能力表或素材登记表不可读，构建日志有告警 and the Sphinx warning
  `Workbench statistics show no data`; the rest of the page renders.
  `tests/test_rtd_system_data.py` fails first; the table script has Node tests in
  `tests/system_data_ui.test.mjs`.

## Design system page

`/workspace/design/index.html` (设计规范; URL, template and module keep the
design-system name) shows the manual's visual rules in six tabs: 概览, 颜色, 字体,
组件, 图标与素材 and 印刷规格. It is listed under 说明书生产; the public manual
library does not link to it.

- **Pictures first (the 2026-11 layout).** A cover in the manual's own warm
  near-black carries the lead, the four outputs and the version line, with a
  sample page rising from its bottom edge. Five figures follow: colours, type
  styles, components, assets and the HB-* semantic styles of
  `docs/renderers/contracts/manual_style.yaml`. 概览 then has four numbered
  blocks, built by `tools/rtd/design_overview.py`:
  - 01 视觉基础: one card per `foundations` entry. The template draws it
    (`foundation_art`) with the live colours (`--m-*` on `<main>`, from the
    colours that carry a `key`) and the live font stack.
  - 02 组件: the `showcase.components` previews, the same iframe documents as
    the 组件 tab. Each is laid out 720px wide, where the widest table fits,
    and `_static/design-system.js` scales it to its card. A card links to its
    component.
  - 03 图标与素材: the `showcase.icons` files from the gallery, with each
    group's count.
  - 04 风格与写法: `style`, `principles`, the `foundations` rules in a
    collapsed `<details>`, and `usage`.

  Layout follows the page container (`container: ds`): two columns below 880px
  of content, one below 600px.
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
  from, what 概览 shows and the preview markup live in
  `tools/rtd_portal_assets/design_system/` (`content.yaml` with
  `schema_version: 2`, `previews/<id>.html`, `print_page.html`, `print_page.css`).
  Previews may use only `asset:<group>/<file>` art and `slot:<w>:<h>:<label>`
  placeholders: no remote, data or absolute URLs. The print preview may use only
  tokens the table defines.
- **Drift fails closed.** The build fails the page, and
  `tests/test_rtd_design_system.py` fails first, when any of these happen:
  - a selector, a component's `requires` class or an asset no longer exists;
  - an asset note names a file or key that no longer exists;
  - a shown or copied file carries a hash the symbol manifest has withdrawn;
  - a print key, a print colour's screen token, or a token the print preview
    uses is gone;
  - a `foundations` id the template does not draw, a colour `key` the drawings
    use, or a showcased component, file or asset group is gone
    (`tests/test_rtd_design_overview.py`).

  A failed page is skipped with a Sphinx warning and its sidebar entry
  disappears, rather than showing stale rules. Additions, such as a new symbol
  or a new CSV row, do not fail; they appear in the gallery, or wait for a
  label in `content.yaml`.

## System data page

The standalone 系统数据 page and its sidebar/home entries have been removed.
Its statistics live in 说明书工作台 [数据统计](#数据统计) (the 交付物 tab), and its
工程规模 in 系统建设「能力与架构」 (see
[Engineering scale](system-workspace.md#engineering-scale)).

In combined builds, `/workspace/data/` and `/workspace/data/index.html` still
serve a minimal `moved_page.html` compatibility redirect. It uses
`location.replace` to open `../deliverables/index.html#statistics`, preserving
the complete query string (including `region`, `model`, encoding and repeated
parameters). Old fragments are replaced by `#statistics` so the tab opens.
Since 2026-11-09 the tab has no filters, so a carried `region` or `model`
selects nothing; the redirect still passes the query string unchanged.
The visible target link is updated before navigation; without JavaScript it
remains a clickable, unfiltered fallback. The redirect has no site shell or
data dependency and is built even if statistics are unavailable. The manuals
role emits neither the redirect nor any workspace pages. Historical update
entries now link directly to the workbench statistics tab; the retired
`system-data` update-page key is removed.

## Product matrix page

`/products/matrix.html` (产品矩阵) lays out the products the published Web
manuals describe, grouped the way the 网页文档 table groups them (2026-11
redesign). It is listed under 产品与市场, after 产品知识; the public manual
library does not link to it.

- **Products and their classes.** One product is one 商品简称 of the
  [产品分类 snapshot](#产品分类-snapshot). A model whose 商品简称 ends in a
  `variant_marks` word of `product_matrix.json` (沙金色, 云上白, 红十字) is that
  product's colour edition (`E1000V2沙金色` joins `E1000V2`, and the card shows
  「+沙金色」); a model the snapshot records as sharing another model's pages
  (`pages_of`: JE-1000F-SG on the JE-1000F US pages) joins as a row that links
  those pages. The product's name, capacity and tier come from its lead model
  (own pages first, then the most markets). A 通用指南 of the snapshot is no
  product and has no card (see Detail). A published model the snapshot does
  not list goes under a 其他 tab with a Sphinx warning.
- **Read at build time.** `tools/rtd/product_matrix.py` reads the publish
  manifest (each model's markets, languages and routes), then one published
  manual per model: English first, then `language_order` and `region_order`.
  From the specification table after its SPECIFICATIONS / 仕様 / 规格 / 規格
  heading (a `<th>`/`<td>` table, or the source-layout `spec-row` lists; a label's
  trailing colon is dropped) it takes capacity (also `Internal Battery`), AC
  rated and surge output (a Total row wins over the largest single port; a
  `Total Output` row counts only when it states a surge figure), cycle life,
  weight, solar STC power, IP rating, output power and an expansion port, as the
  manual prints them. Names come from the manual-center catalog without the
  model code or the manual-type suffix (`names` overrides). Capability switches
  come from `data/model_capabilities.csv`. Nothing else is snapshotted.
- **Layout.** A tab per 产品类别 in the snapshot's order (counts of products),
  each a grid of 产品系列 rows × the 容量档 its products use (the snapshot's
  `capacity_tiers` order: 1度以下 … 5度电, the 项目号 table's values, since
  2026-11-09); a category where no product has a 容量档 (太阳能板, 配件) has one
  产品 column whose cards sit side by side in a grid (`is-flat`), and a tiered category gets a 容量未注明 column only when a product
  lacks one. A 容量档 the manual's stated capacity does not fit (「X度电」 more than a
  quarter off X kWh, or 「X度以下」 at X kWh or more) is a Sphinx warning, so a
  wrong table value shows in the build. A card shows
  the name, the 商品简称 (GTM reads products by it) with the capacity, a letter
  per market (`markets`: 美 欧 日 中 台 韩) and any colour edition.
- **Detail.** Clicking a card opens its product's detail directly under its
  series row: the 商品简称, category · series · model count, then a row per model
  with its 型号, 简称, the figures some model states (容量, AC 额定 / 峰值,
  太阳能功率, 输出, 防护, 重量, 扩展口, 说明; a column every model lacks is left
  out) and a link per market (`美规 ↗`, the English page first; the tooltip lists
  the languages). A shared-pages row reads 「与 JE-1000F 共用美规说明书」.
  Below: 功能 from the first model in the capability table (switches on in every
  region, 部分市场 with the regions in the tooltip, then 不支持), and 搭配: what
  the product's manuals name, and the other products whose manuals name it
  (「DC-DC Charger 的说明书写到「Explorer 1000 v2」」), and 相关指南: each 通用指南
  whose 适用产品 lists one of the product's models, with a link per market the
  guide is published in (「太阳能连接指南 日规」). Under 600px of container
  width each model stacks as a labelled list.
- **Curated config.** `product_matrix.json` holds what neither the manuals nor
  the snapshot state: `markets`, `variant_marks`, `names`, `notes`
  (accessory one-liners, the 说明 column), `capability_labels` and `pairings`
  (partners a manual names). A pairing item shows only while the manual's text
  still contains its `match` text (or its label); it links to a product only
  through its `product` key (that product's 商品简称), never by its label alone,
  since 「Explorer 1000 Plus」 may mean either generation. `lines`,
  `accessories` and `assign` stay for 产品知识 (`positioning_groups`); an
  `evidence` assignment whose quote has left its manual still warns here.
- **JavaScript** (`_static/product-matrix.js`) turns the tab links into a
  switch, opens and closes a detail under its row (a second click on the card
  closes it), and keeps the open product or category in the URL hash, so
  `#p-E1000V2` or `#cat-accessory` links open them. Without it every category
  shows stacked and a card's link opens its detail through `:target`. Node tests:
  `tests/product_matrix_ui.test.mjs`.
- **Failure:** without a readable publish manifest or a usable 产品分类 snapshot
  the page and its links are skipped (the portal already warned about the
  snapshot). A config with an unknown group, an open tier shape, markets without a
  letter or label, or empty variant marks, or a malformed capability CSV, skips
  the page with a Sphinx warning. An unlisted model, an unreadable manual or a
  pairing the manual no longer names is a Sphinx warning while the page still
  renders. `tests/test_rtd_product_matrix.py` covers the parsing, grouping,
  details and the rendered page.

### 产品分类 snapshot

`tools/rtd/product_catalog.py` reads the 网页文档 and 项目号 tables of the
发布文档管理 Base (`$FEISHU_PUBLISHED_DOCS_BASE_TOKEN`,
`$FEISHU_PUBLISHED_DOCS_WEB_TABLE_ID`; the 项目号 table is found by its name, or
pass `--project-table-id` / `$FEISHU_PUBLISHED_DOCS_PROJECT_TABLE_ID`)
read-only and writes `tools/rtd_portal_assets/product_catalog.json`
(`hello-docs-product-catalog/v2`, the `product_catalog` domain of
`source_registry.yaml`, 待复核 after 30 days):

```bash
python -m tools.rtd.product_catalog refresh --cli-bin "lark-cli --profile prod" --dry-run
python -m tools.rtd.product_catalog refresh --cli-bin "lark-cli --profile prod"
python -m tools.rtd.product_catalog check
```

- **Where a product is classified.** Since 2026-11-09 a product is classified
  once, on its row of the 项目号 table: 产品类别 (single select: 便携储能 / 家庭备电 /
  加电包 / 太阳能板 / 配件), 产品系列 (single select whose options each category
  uses its own of: 标准 / Plus / PlusV2 / Pro / ProMax / Ultra / 卫士 / 充电宝 for
  储能; SolarSaga / SolarSaga Air; 充电与输入 / 连接与配电 / 保护与搬运 for 配件;
  标准 for 加电包) and 容量档 (1度以下 … 5度电, empty for 太阳能板 and 配件; the
  产品矩阵 columns, snapshot schema v3). Each 网页文档 row
  names its 项目号; its 产品类别, 产品系列 and 容量档 columns are lookups of that row.
  The old per-row single select stays as 产品系列（迁移备份）, unread.
- **文档类型** (网页文档 single select): 产品说明书 (also when blank), 通用指南 or
  快速指南. A guide's 型号 is its document code, the first segment of its route,
  and it has no 项目号; 适用产品 (text) lists the model codes it covers. A 通用指南
  belongs to no one product (`JS-CONNECTION-GUIDE`, older codes such as `PTB101`
  included); a 快速指南 is one product's separate quick guide and names that
  product (`JA-CK01A-BK-QG` → `JA-CK01A-BK`; the full 取扱説明書 38-0001-000777 and
  the クイックガイド 38-0001-000845 are two documents).
- `categories`: the 项目号 table's 产品类别 options in their order, each with the
  产品系列 options its models use, in that field's order. Reorder options in
  Feishu to reorder both pages.
- `models`: every model a 产品说明书 row's 型号 cell lists, with the row's 类别, 系列
  and the 商品简称 at the same position of its 商品简称 cell
  (`JE-1000F, JE-1000F-SG` ↔ `E1000V2,E1000V2沙金色`). A model listed after the
  first one, without rows of its own, also records `pages_of` and the routes it
  shares.
- `guides`: each guide by its code, with its `kind`, 商品简称, routes and
  `applies_to` (the 适用产品 models, in order). The 说明书资料库 shows the 通用指南
  in a group after the categories, and a product card whose model a 通用指南 of
  the same market covers says 「相关指南：太阳能连接指南」; a 快速指南 has no card
  of its own, and its product's card links it as 「快速指南」. The 产品矩阵 lists both
  under the products they cover, the 快速指南 first.
- A manual row without a 类别 or 系列 is skipped and printed; rows that disagree
  about a model or a guide, a 型号 and 商品简称 cell of different lengths, a link
  to another model's route, a guide whose link does not open its own route, a
  文档类型 other than the three, a 快速指南 without 适用产品, or a value outside the options fail the refresh and
  keep the previous snapshot. Only 型号, 商品简称, 产品类别, 产品系列, 超链接, 文档类型
  and 适用产品 are read; the 项目号 only joins the tables inside Feishu and, like a
  SKU, never reaches the snapshot, which sits in a public repository.
- Classifying a model, or renaming a series, is a 项目号 table edit (operator
  confirmation and a read-back, per the lark-cli Bitable rules) followed by a
  refresh PR. The 2026-11-06 snapshot came from the operator-approved fill of
  all 206 rows plus the three JP rows the operator added the same day for
  JA-CK01A-BK, JA-CK01A-BK-QG and JS-CONNECTION-GUIDE (209 rows, 69 models;
  便携电源 / 家庭备电 / 扩容电池 / 太阳能板 / 配件). On 2026-11-09 the operator
  moved classification to the 项目号 table (60 projects) and approved the field
  changes above, written with a read-back of both tables; the refreshed snapshot
  has 67 models (便携储能 46 / 家庭备电 3 / 加电包 5 / 太阳能板 4 / 配件 9) and one
  通用指南. The 网页文档 table then had no row for JA-CK01A-BK-QG (208 rows); the
  operator chose to record it as a 快速指南 of JA-CK01A-BK and approved its row
  (read back the same day; 209 rows), so every published
  model or guide is classified.

## 产品知识

产品知识（产品案例是其末节）、市场与政策都与说明书共用同一个 RTD 项目（2026-10-06 定为同项目发布）。2026-10-13 起 Hello-Docs 转为私有仓库，站点改由 Read the Docs for Business 托管于 `https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/`，访问需要登录并具备项目权限；页面路径须带 `/en/latest/` 前缀，例如 `/en/latest/products/knowledge.html`。知识库可以跳转到说明书，说明书首页、侧栏和顶部不提供知识库入口；分享知识页直达链接给有权限的人。

`/products/knowledge.html` 提供围绕已发布产品的最少必要技术知识，按标签、型号和区域筛选。通用功能原理、常见误区与阅读提示维护在 `tools/rtd_portal_assets/product_knowledge.json`。每项写入 `added`（首次发布日期，YYYY-MM-DD）；知识库首页的增长线读取它，有一项缺少时只显示主题数。适用产品取产品矩阵模块的定位层（`tools/rtd/product_matrix.py` 的 `positioning_groups`）：`settings.json` 的 `navigation` 分组（说明书资料库已改按产品分类分组，`navigation` 只留作这层定位）加上 `product_matrix.json` 的产品线与 `assign`（备电线的说明书证据句在产品矩阵构建时核对，原文不再出现只给出警告），导航未收录的已发布型号因此也有对应知识，型号选择只列出至少有一项知识的产品。`product_matrix.json` 缺失或格式有误时，知识页只用 `navigation` 分组并给出 Sphinx 警告，条目引用的其他分组（如 `homebackup`）按空组处理并在警告中列出，构建不中断。每项的说明书入口只从当前冻结发布目录取得，优先现有英文页，缺少英文时使用实际可用语言，不拼接或猜测型号路径。区域选择与说明书资料库共用浏览器 `localStorage` 的 `hello-docs.manual-portal.region`（按区域名，如 UK 仍显示为 UK、筛选共用的 EU 说明书）：任一页选过的区域，两页下次都从它打开；“全部区域”只在本页，记在 `hello-docs.manual-portal.region-all`，直到在任一页再选具体区域；词条链接为显示被隐藏词条而清除的区域不记住；没有有效记录（首次访问、存储被清除或禁用、记录已不是选项）时用配置的默认区域。覆盖测试见 `tests/product_knowledge_ui.test.mjs`。

通用知识不构成某型号内部电路、芯片或跨产品兼容性的认定，也不把教程中的算例当作产品实测。标签和型号过滤只控制阅读范围；技术值、操作和兼容条件仍以对应地区说明书为准。未启用 JavaScript 时全部知识条目与来源链接可读。工程面的模板、交互和课程词条与业务面的 `docs/knowledge/**` 个人分享文章分别维护。

页面（2026-11 改版）先给两张图，再给词条卡：“先看懂能量怎样流动”把来源 → 充电转换 → 电池 → 逆变/直流转换 → 设备画成一行，扩容挂在电池下，旁路走在下方，每个环节标出对应主题的条数，点击即按该主题筛选并跳到列表；“按主题找”每个主题一张卡，列出其下词条的短名（标题全角冒号前的部分），点短名直达词条，词条被筛选隐藏时先清除主题与型号，仍不可见再清除区域。手机宽度下主题卡只留标题与条数。词条卡把示意与原理、产品应用、易混淆点和来源放在一起：一般示意由 `diagram_nodes` 生成 HTML 步骤链；`_knowledge_diagram.html` 里手绘的 SVG 示意占更宽的图列；写了 `circuit` 的词条（须是 `_static` 中已有的 `circuit-*.svg`，否则构建报错）把电路图放在正文上方，按标注可读的尺寸显示，可点开原图。每卡列出当前区域的说明书，超过 8 本时其余收进“+N”；区域选“全部”时说明书名后标出区域。示意图不代表某型号内部电路。

AC 教学电路图（H 桥与 LC 滤波、插座并联、联锁切换）只用于逆变器、多口合计与 UPS 三条讲电路的词条。低压升压、隔离、体二极管与接地等未展开，不能当成实际产品原理图。JHP-3600C US 的备电案例在词条之后，按四个问题排列，每题旁边是对应的电路图或说明书中的关键数值；来源链接与知识条目一样从冻结发布目录取得，目录中没有 JHP-3600C/US 时整段不显示；分相、旁路、ATS/MTS 与级联条件按说明书描述。

## 市场与政策

`/market/policy.html` 与产品知识并列，记录“政策变化 → 原理解释 → 产品影响”。页面（2026-11 改版）先放每个主题一张卡（主题名、条数、一句说明，以及每个国家一个标签，标签上的圆点标出核实状态，点标签直达该国第一条），下面一行说明状态圆点；再按主题分组，每条记录收成一行（国家、标题、时间、状态），点开才显示三段（第一段对业务需求写“需求变化”）、适用边界，以及适用范围、时间、相关产品知识与出处。页面不再设筛选；“全部展开”需要 JavaScript，链接到某条记录（`#记录 id`）时该条自动展开。主题划分写在 `tools/rtd_portal_assets/market_policy_themes.yaml`（`hello-docs-market-themes/v1`）：快照只带标签，记录归入第一个列出其任一标签的主题；没有主题认领的记录显示在“其他”并给出 Sphinx 警告，此时把它的标签加进该文件；`cross_region`（跨地区）不计入“国家和地区”数。该文件格式有误时构建失败。每条记录显示适用地区和时间；“政策要点已核实”只表示政策事实已查官方出处，产品影响单独标注为分析判断。官方出处以简短参考链接呈现；页面不展示原始资料截图、整理流程或核对过程说明，未经核实的信息仍保留状态标识。

工程面的 `tools/rtd/market_policy.py` 读取业务内容目录下的 `market-policy/records.json`（`schema_version: 1`）。默认业务目录为 Hello-Docs 的 `docs/knowledge/`，本地预览可用 `rtd_knowledge_dir` 指向临时目录。该快照及原始截图不放入 auto-manual；当前未接入飞书多维表，也不在线读取飞书。

记录保留 `id`、国家/地区、标题、时间、`verified`/`unverified`/`demand` 状态、标签、变化、原理、影响和核对日期；可选 `boundary` 记录必要的适用条件，不填时页面不显示该段；`sources` 保存出处类型、标题、HTTPS 链接和核对范围，但页面只展示标题与链接。已核实记录至少需要一条官方出处，`demand` 只代表业务需求依据，其第一段显示“需求变化”。未核实线索和业务需求可用非空 `evidence_note` 保存录入依据，该字段不在页面显示，也不能代替已核实政策的官方出处。`knowledge` 关联产品知识锚点。锚点不是 `tools/rtd_portal_assets/product_knowledge.json` 中现有的条目 id 时，构建给出注明记录与锚点的 Sphinx 警告，但不因此失败。可选 `flow`、`image` 和 `image_alt` 不在页面渲染；源图只参与本地审阅校验，构建不复制到网站，本次业务快照不上传原始截图。缺少快照显示空页；记录无效则构建失败。未启用 JavaScript 时全部记录与参考链接仍可读。
