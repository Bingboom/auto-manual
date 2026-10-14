# RTD portal: manual center home, catalog and search

Status: active · Part of the [RTD manual-center entrance](../rtd_manual_portal.md); its index lists the
other portal surfaces. Add new notes for this surface here, not to the hub.

## Discovery and implementation plan

Operator accepted the local card/search design and requested RTD implementation,
with **EU temporarily the default**, on 2026-09-12. The current region options
are US / EU / UK / CN / JP. CN and JP retain independent market bindings;
EU and UK share existing EU publications, and EU remains the default.
Chinese (`zh`, 简体中文) and Japanese (`ja`, 日本語) labels are registered for
verified publications. Registering these labels does not publish a manual or
create a language URL; unavailable editions remain disabled.

Verified baseline: engineering main `ff5e3556`; RTD listens to Hello-Docs/main
and renders frozen `docs/publish/web` with Sphinx/Furo. The frozen config does
not load engineering extensions. Editing only the assembler would not update
already published snapshots. The live index has 21 entries (US 1, EU 20).

Implementation phases:

1. Add a root-only Sphinx portal extension, a catalog adapter over the existing
   frozen index, and the accepted responsive template/styles. No live requests
   or body duplication. Keep ordinary links usable without JavaScript.
2. Enable the extension in both RTD build paths, without modifying frozen
   sources, GitHub workflows, review content, dependencies or public build CLI.
3. Test EU default, shared EU/UK links, search, missing-language states, safe
   assets/URLs, existing non-portal regions and unchanged manual rendering.
   Run syntax/lint, targeted and full unit tests, guardrails, link check, the
   build quality check, then real Sphinx baseline/new builds of the same frozen
   corpus. Only the home and portal-specific static files may differ.
4. PR in auto-manual, gate-on-green only with current authorization, mirror to
   Hello-Docs, and verify the actual RTD page. Do not call a local build online.

Non-goals: independent twelve-language publication storage, new translations,
IR/print changes, online Base writes, product facts, and advertising removal.
Existing bundled languages remain accessible through their original manual.
Only verified independent locale links may be enabled; do not construct URLs
by replacing a language suffix. Product illustrations come from each frozen
manual's packing-list product asset; missing packing-list images may use an explicit model/market artwork fallback;
unconfigured cards remain model-only.

The root template keeps an EthicalAds placement for RTD. No CSS hides platform
advertisements. Other markets remain accessible in an all-publications fallback
for markets outside the primary US/EU/UK/CN/JP dropdown. The footer derives
its market list from the same settings, and CN/JP display their own market notes.

## Page layout

Every portal page (manual library root, 知识库首页, 产品知识, 市场与政策, 系统建设, 说明书工作台, 设计规范, 系统数据, 产品矩阵)
shares one site shell from `tools/rtd_portal_assets/_site_shell.html` and
`_static/site-shell.css`. The public manual library passes `internal=false` to
both shell macros: its sidebar contains only 说明书资料库 and 搜索说明书正文,
and its top bar keeps the breadcrumb and region selector. It has no internal
knowledge links or 知识库 / 说明书资料库 switch. Internal pages add three groups
after 说明书: 知识库 (首页), 产品与市场 (产品知识, 产品矩阵, 市场与政策) and
说明书生产 (说明书工作台, 系统建设, 设计规范, 系统数据 — 系统数据 stays last as a
pointer page to 说明书工作台「数据统计」 until it is removed), plus the switch. Their breadcrumb section is 知识库,
and 工作资料 is only the brand. The root keeps 工作资料 as title, crumb and footer,
and renders byte-identically in both roles. Every sidebar entry is a page and carries
`aria-current="page"` on that page; 分享资料 and 最近更新 are sections of the
知识库首页 (`workspace/index.html#shares`, `#updates`), not sidebar entries.
Optional entries follow the same rules as before: 系统建设, 设计规范, 系统数据 and
产品矩阵 only when their context builds (each computed once per build and shared
with the sidebar). Page stylesheets style only what
sits inside `.app-content`; the brand accent is the shared `--brand` orange.
The Furo search page and manual pages keep their theme.

The 系统建设 and 说明书工作台 pages share two more shell components: a key-metric
row (`.kpi-row`) and page tabs (`.page-tabs` /
`.tab-panel`, wired by `site_script()`). Tabs are anchors over panels, so
without JavaScript every panel shows; any in-page link or URL hash that
points inside a panel opens that panel. 系统建设 tabs: 当前工作, 系统架构,
能力与流程, 语言资产, 工具与工程规模, 系统演变, 数据来源. The unfolded
stage gates form the metric row inside 当前工作; other tabs do not repeat it.
A pointer below the row leads to 说明书工作台, which owns the publication counts.
说明书工作台 tabs: 交付物 (the deliverables matrix, open by
default), 数据统计, 工作入口, 生产与资产, with web manuals (books per region beneath),
language editions, Word and print counts as the metric row. The 工作入口 tab draws the content-authority map (`manual_workbench.html`)
and states current maturity rather than a target architecture:
CONTENT AUTHORITY 当前内容权威源 offers two alternatives, 01 结构化内容源
(规格 · 文案 · 语料 · 资产) or 02 Git 原生说明书源 (RST · MyST · Components ·
Frozen Source, the authority for many web manuals today); SOURCE BINDING says
each manual variant declares exactly one current authority (文档构建表
`Git_ref`, or `source_manifest.json` on the Git-only path); ASSEMBLY / IR
组装与语义层 holds the production rules (Skeleton · Template · Components),
model / region / language assembly and Manual IR at its current coverage —
templates are rules, not a content source; HUMAN SURFACE 人读面 (Web · Word ·
IDML / PDF) and MACHINE SURFACE 机读面 (JSON · MD) are siblings derived from
the declared authority and never maintain their own body text. The 机读面 panel
states that `manual-knowledge.json` is currently extracted from published HTML
as a compatibility path, not the target. The machine card carries the same fact as a status badge
(当前：HTML-derived · Compatibility); when the corpus is generated from
Assembly / Shared IR instead, change the badge to IR-native · Same-source. The panel's coverage tiles (versions, fresh vs receipt, generation mode, revisions, callout severity, images without alt) are filled at view time by `_static/machine-surface-stats.js` from the deployed `machine_surface_manifest.json` and `manual-deployment.json`, because the manifest is written after pages render; without JS or either file the panel keeps a note and the download link. Build times, snapshot dates and hashes sit in
the collapsed 页面版本与更新 / 数据更新时间 disclosure.

Inside the shell the root page has these bounded zones on one container width
(`.wrap`, 1200px):

1. **Search hero** (light grey band): title and the cross-manual search box.
   People who already own a product search the model here.
2. **按用电需求找说明书**: one tile per power need (随身供电 / 通用电器供电 /
   可扩容储能 / 专用场景备电) with a one-line scenario and the products that
   have a manual in the selected region; a tile with none there is hidden.
   A tile click filters the catalog to that need.
3. **Filter toolbar** (sticky below the top bar): 全部, one chip per need and
   配套产品, plus the language filter. Chips without a manual in the selected
   region are hidden; a hidden active chip falls back to 全部.
4. **Catalog**: region heading and count, then one section per need, then
   「配套产品」 with one section per kind (扩容电池 / 太阳能补能 / 充电器 /
   连接配件 / 保护与搬运), each with a responsive card grid. Sections with no
   visible card after filtering are hidden.
5. **Footer** (light grey band), which also holds the Read the Docs ad placement.

The need and accessory groups are product positioning, curated in
`settings.json` → `navigation` (`needs` rows with `id`, `title`, `note`,
`models`; `ecosystem` rows with `id`, `title`, `models`); the build never infers
them. `tools/rtd/portal_navigation.py` rejects a model listed twice, a duplicate
or non-lower-case id, or a row without title/models, and fails the build. Card
order inside a group follows the table. A published model the table does not
list yet appears under 「其他说明书」 instead of disappearing; add it to the right
row. Capability comparison and compatibility lookup are deliberately absent until
a confirmed data source exists. Without `navigation` the page falls back to one
section per product type (`便携储能` / `加电包` / `太阳能板` / `配件`).

Cards show the product image, model, edition, a language summary (first
published language plus the count; the full list is in the tooltip) and a
version label. Build identifiers are not shown raw: `git-YYYYMMDD-…` reads as
`构建 YYYY-MM-DD`, other `git-…` values as `开发构建`, and `candidate` as
`候选版`; the raw value stays in the tooltip. Template and styles live in
`tools/rtd_portal_assets/manual_portal.html` and `_static/portal.css`.

## Catalog validation during a build

The frozen publication catalog is validated once per Sphinx build and reused
by page rendering and the search-index writer. This avoids re-reading all
publication evidence for every generated page. Validation still fails closed;
no content or evidence checks are skipped. The cache belongs to the Sphinx
application, is prepared before parallel writers start, and is cleared on both
successful and failed builds so later builds revalidate their inputs.

Local verification on the Hello-Docs `2818de85` frozen snapshot (2026-09-20):
207 source documents took about 214 seconds before the change and 6.7 seconds
afterwards. All 219 output HTML files were byte-identical. Of 1,103 output files
excluding doctrees, only `.buildinfo` and its hash in `manual-deployment.json`
differed because the isolated test used an explicit knowledge-directory override.
These are local measurements, not a Read the Docs runtime guarantee.

## Directory and keyword search (2026-09-13)

The local redesign uses compact product rows and a shared keyword box for product
identity and manual body content. `tools/rtd/portal_search.py` indexes canonical
rendered publications after HTML generation, before deployment receipts are sealed.
The index is a same-site static JavaScript asset, so it needs no remote search
service. Matches require every query token and prioritize model and heading matches.
Section results carry the existing rendered anchors, publication language identity
and version; region, category and language filters apply to both result types.
Legacy language scopes remain explicitly unverified. Illustration-only text is
excluded; the index does not claim OCR coverage. Results initially show twelve
sections and can be expanded. The operator accepted the local preview for deployment on 2026-09-13.
Deployment uses the existing engineering mirror and RTD build; manual source
publication, online tables and OSS uploads are outside this change.

The Furo `/search.html` route also has a server-rendered landing form. A bare
visit therefore shows an actionable query field instead of an empty content
panel; submitting it uses the existing `q` parameter and Sphinx search index.

## Product hub rollback — 2026-09-15

The operator requested that main return to the manual-only directory and
keyword search. #1144 is reverted; the complete product hub remains on remote
branch `codex/product-hub-preserved-20260915` at `9306967b`. This rollback
preserves all other product/localization changes and does not modify frozen
publish inputs. Restoring the hub later requires a separate explicit release.

## Accessory catalog artwork (2026-09-15)

JA-CA05B/EU and JA-CA3SA/EU have no packing-list image for the portal to
select. Their existing manual illustrations are bundled byte-for-byte as
portal-only static assets, selected by `product_image_fallbacks` in
`tools/rtd_portal_assets/settings.json`. A native packing-list image takes
precedence; unconfigured models and other markets keep the existing fallback.

| Catalog target | Source illustration | SHA-256 |
| --- | --- | --- |
| JA-CA05B/EU | `docs/renderers/web/assets/ja_ca05b_eu_en/connector_reference.png` | `f343a96eb9aefba55b0bc890a0a6b0f16d361da2a7cb36a640e2e9f8cab48ded` |
| JA-CA3SA/EU | `docs/renderers/web/assets/ja_ca3sa_eu_en/main_ports.png` | `d8786487be9c5b7810bfb1544f277b5cbde5dca3759f09b3500000f4ecc82b77` |

No image generation, cropping, manual-body edits or source-table writes are
needed. These are diagram thumbnails, with the source labels intact. The
Sphinx portal static path copies both images on a normal RTD rebuild; no
frozen manual snapshot needs to be rewritten. Remove the relevant mapping
to return a card to its previous model-only presentation.

### Explicit product artwork

`product_image_overrides` selects exact model/market artwork ahead of a native
packing-list image. Each entry has `src`; optional `view_box`, `width`, and
`height` display a bounded SVG viewport of the unchanged source image.
Removing an override restores native-image / configured-fallback precedence.

- JBP-3600A/EU: the operator-provided *Jackery Battery Pack 3600 User Manual
  (JBP-3000A) EUUK V2.0-2026-08-04.pdf*, page 1. Despite the filename, the cover
  identifies JBP-3600A. PDF SHA-256:
  `084dd4517feddcd9b77da10415a2787ec4427f882a7b819160725fdff679ccfe`.
  Render the original vector artwork at 4x using the top-left PDF-point box
  `(78, 176, 291, 317)`; output `jbp-3600a.png` SHA-256:
  `fb4c99e52945b2753fb405c4ae254804433169861b710fc089df86404fa2c49f`.
- JS-100F/EU: byte-identical copy of
  `docs/renderers/web/assets/js100f_eu_en/solar_panel_connector.png` (SHA-256
  `5a9d559d420ebecc9314ec8e515f11e35e4d29a6453a5dec5d143ab311e0663e`).
  The viewport `24 27 320 145` shows the upper panel only, excluding the second
  panel, connector, and power station. The source dimensions are 1248 x 328.

These overrides affect homepage presentation only, not manual content or
frozen publication snapshots.
