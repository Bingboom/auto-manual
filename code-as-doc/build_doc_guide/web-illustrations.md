# Build guide: Web artwork, illustration manifests and composites

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

- Before selecting or extracting artwork, follow the shared
  [Web artwork reuse order](../../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则).
  Inventory existing target/shared assets and record each reuse decision in the
  target review record before any PDF/AI crop. Matching assets retain their bytes
  and source hash; language-only label changes reuse the base art. Complete
  panels retain backgrounds/frames, and App screenshots retain complete phone
  bounds. The selection record is a procedural review prerequisite, not a new
  automated build check. Validate actual bound assets at desktop/mobile widths.

- `paths.web_illustration_manifest` optionally binds one config target/language
  to finished PDF crops. A shared family config can instead use
  `paths.web_illustration_manifests`, mapping exact `Document_Key` values to
  manifest paths; an unlisted target receives no manifest, and the scalar and
  mapping forms are mutually exclusive. A `Document_Key` may instead map to a
  `language -> manifest path` mapping, which is what a merged multi-language
  book needs: the same source image basename repeats once per language block,
  so finished panels are bound per `(language, basename)` rather than by
  basename alone. A manifest whose declared `language` is absent from the
  document, or differs from the key it is filed under, fails closed. Each selected manifest freezes source
  PDF hash, page, bounding box, output
  hash and exact input image basenames. One illustrated panel can replace several
  split images; surrounding structured copy is retained. Wrong target, missing
  images, changed bytes, repeated or unused bindings fail the build. These Web
  variants preserve embedded text and never overwrite IDML textless assets.
  Every target carrying a finished-figure coverage policy must declare a
  non-empty locale set, the complete Overview/Operation/Charging slot set
  derived from its skeleton, and exactly the two accepted final states:
  `finished-panel` / `approved-composite`. `JE-1000F/EU` requires all 11 slots
  in each of EN/FR/ES/DE/IT and resolves 55/55 locale-matched full panels.
  Any `editable-fallback`, `missing`, duplicate or absent required slot stops
  IR assembly/replay unless that exact locale/slot/status is already in the
  separate versioned debt baseline. That baseline currently contains nine US
  Charging fallbacks and nine KR missing panels; new or worsening debt fails,
  and a repaired row must be deleted from the baseline in the same change.
  While a reference figure waits for its finished panel, its source art fills
  the figure width (the source's inline `:width:` no longer shrinks it).
  A target overlay may instead grant one Operation or reference slot the bounded
  `base-art-live-copy` state (today all five JE-1000F/US Operation figures and
  its Charging car figure, EN/FR/ES; LED on the target's own
  `operation/je1000f_us/led_light` art): the frozen text-free artwork is the
  only image and the source copy stays live HTML on anchors the overlay's
  `base_art_layout` declares for that exact art (`art_sha256`, bracket-arm
  `step_anchors`, optional `duration_anchor`, `prerequisite_rect` with its
  measured `prerequisite_fill` tone, `footer_x`, or a footer-panel card's
  `art_width` and `step_markers`; a reference figure declares a `panel_top` band,
  its `panel_fill` tone and one `labels` rectangle per captured source line).
  Coverage binds each such slot to its packaged asset path/hash and rejects a
  layout measured on different art, so a new art version must be re-measured
  before it ships; a mode without its exact `slot_status_overrides` grant, an
  unknown mode, or incomplete anchors stops contract loading. Details and the
  measured anchors:
  [`je1000f_us_base_art_web.md`](../dev/je1000f_us_base_art_web.md).
  Its 55 crop/page/content/source-fragment pins are recorded by
  `data/asset_recipes/manual_je1000f_eu_web_panels.json`; Italian is 11/11
  approved full panels. Text-free artwork with HTML/SVG labels or leaders is
  debt for these slots in every locale and never counts as a final carrier.
  Optional `covered_annotations` entries bind a selector and exact normalized
  source text already covered by an illustration. Only unique unchanged matches
  are consumed; changed or ambiguous copy fails. Covered copy stays in image alt
  and IR provenance. Explanatory tables and warnings stay live.

- `JBP-3600A / EU / en` uses the BP skeleton through
  [`config.bp-eu-en-web.yaml`](../../configs/config.bp-eu-en-web.yaml) and its
  [Git-only input](../../manual_sources/JBP-3600A/EU/en/README.md). HTP011 source
  wording follows the HTP017 chapter structure. The shared Operation component
  permits battery packs to omit host-only auto-resume, key-combination and LCD
  mode tables. Its opt-in `base_art_layout.duration_icon: clock` draws a CSS
  clock beside live duration text after the source glyph is removed.
  The duration reader accepts Italian `secondi`, German numeric `Sekunden`,
  and the native German phrase `Drei Sekunden`; only the decorative clock
  becomes `3s`, while the instruction retains its original wording.
  Reference labels can declare a measured `color` with their `fill`; these
  source badges retain a 0.875rem minimum and expand within the art edge on phones.
  JBP locking labels use the native dark fill and white type. Frozen MyST
  replay promotes top-level `hb-h1-pill` document headings into navigation,
  while preserving headings inside components. On mobile, shared anchor spacing
  includes Furo's sticky header height so direct links and TOC jumps show the
  complete section heading.
  The current candidate stylesheet also reserves 4rem for desktop anchor
  jumps. Mobile warranty headings participate in normal flow so wrapped titles
  reserve body space; targeted warranty headings retain their dark fill.
  The approved nine-language snapshot binds English r6 and the independently
  reviewed native versions to the actual MA-244 publication instruction in
  [the release source](../../manual_sources/JBP-3600A/EU/git-20261003-44b6ce61-reviewed/README.md).
  Native source exceptions remain explicit; prepared component applicability
  is enrolled per language. Original candidates and acceptance seals remain
  immutable. Fresh admission, strict Sphinx and cold output parity are required
  before publishing; phase2 checks do not validate these native-language bodies.
  Governed reference figures and hash-locked finished panels may coexist in
  coverage. Apply label-bearing illustration replacements before ComponentSpec
  discovery (`consume_before_presentation`) so cold replay hashes the same
  carrier. See the [source and acceptance record](../reviews/jbp3600a-eu-en-htp011-20261002.md).
- For an approved PDF artwork correction, `swap_pdf_regions` exchanges two
  equal-size, disjoint native regions on white backgrounds, inside the asset
  crop. Freeze source/output hashes and visually verify the final PNG. JBP-2000B
  JP uses this to correct reversed on/off titles according to structured source.
- `copy_pdf_region` is the one-way form: it repaints `bbox_pt` with the source
  page's own content from `other_bbox_pt` (equal size, disjoint, both inside the
  crop, read from the immutable source) and paints no background, so it can
  land on tinted art. Pair it with a text-only `redact_text_region` to re-set a
  mis-printed character from a same-font glyph on the same page. JE-2000E EU uk
  uses this for the App control-panel label the print sets as `AC1` instead of
  `AC2`; pixel-diff the result against the uncorrected crop.

- Fixed PDF-like Web panels are selected through the versioned [`web-composite-manifest/v1`](../../tests/fixtures/phase2/web_composite_manifest.json) snapshot. The live Base is only the control/intake plane: `04_资产定义.web_replace_key` identifies the governed HTML component, while one approved `04_资产导出物` row supplies exactly one `export_file`, its `web_locale`, `content_sha256`, and `source_fragment_sha256`. `sync-data` downloads approved bytes to `_attachments/web_composites/`; materialization verifies and copies target-matching bytes to `_assets/web_composites/` and includes the staged manifest in the bundle fingerprint. The Web contract contains semantic keys and locale mappings only, never live Base tokens or static artwork paths.
- For JE-1000F Web assets, Overview, Operation and Charging composites are localized PDF crops (`text_policy=localized-full-page`) and must keep their visible labels, including Operation `On` / `Off` and prerequisite/action copy. The LCD screen-mode component is hybrid instead: use the UK or continental product/display artwork plus the live six-row HTML table. A new region should extend the versioned Overview instance and override stable IDs/locales rather than copy its geometry; composite resolution uses the materialized language, and coverage provenance is `asset_key + locale + SHA-256`.
- Locale lookup is exact first and permits only `shared` as fallback. No approved match preserves the editable/searchable semantic HTML so compatibility output remains intelligible, but a governed finished-figure slot records that state as `editable-fallback` debt; it does not satisfy final coverage. Multiple matches, a missing/extra attachment, an unapproved buildable row, attachment hash drift, or source-fragment drift stops the build. Section headings remain outside composite images. FCC, What's in the Box, Symbols, LCD, tables, warnings, and App add-device remain editable HTML components and do not enter this replacement manifest.

### Web illustration family paths

`paths.web_illustration_manifest` accepts `{model}` and `{region}` through the shared build-path resolver. It remains mutually exclusive with the Document_Key mapping `paths.web_illustration_manifests`. A skeleton without LCD or auto-resume tables explicitly sets those inherited operation contracts to `null`; shared Web rendering then omits those inapplicable components.

四语原生 PDF 导入按模板的 H1/H2 层级投影章节和子标题；前言提示与段落、安全警告框、LCD 四列图标表、质保卡片及 App 步骤编号均通过共享 IR/ComponentSpec 渲染。密集引线的产品前/右视图复用对应语言成品图，同时保留 IR 语义文案、来源和哈希；正文和表格继续使用原生 HTML。

新增语言继续复用上述管线。LCD 行可显式选择多数行重叠提取，App 可显式声明编号只在截图下出现的步骤；默认行为不变，仍校验原稿编号。文字提取框不能直接当作网页提示框宽度，须逐语言检查遮图和手机换行；节能操作组件自带时钟时，底图不得重复保留。字段说明见[原生适配契约](../dev/je2000_eu_new_locales_ir_adapters_2026-09.md)。

经指定保留完整原稿样式的大图面板可使用目标已启用的 `source-finished-panel`，
并明确绑定 `captions_embedded: true`、`language`、原稿页码和素材哈希。未声明时仍保留
原有图外标题。原生提取的标题保留为检索/读屏文本，
不再另绘等宽标题列；语言或页码不匹配会阻止构建。此方式保留图内文字，
不提供图内逐项 HTML 编辑，也不替代普通无字插图、正文或表格的原生 HTML。
大图面板只按完整边界裁取，灰底、白色说明区、圆角框及徽标随原稿保留，不能套用
独立图标去底规则；见[大图与独立插图的边界](../../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)。

Native PDF LCD intake preserves semantic status lines and bold status prefixes in the existing `HB-TABLE-LCD-ICON` component. The verified uk/pt/nl/pl paragraph boundaries also separate App setup and retained-setting notes; printed line wrapping is not copied into Web layout. Numbered troubleshooting measures each start a new line; the emergency-charging lead retains its bold emphasis. Shared reference-figure captions follow the artwork, matching the App 2.1–2.2 captions. Source wording, governed icons and historical frozen versions remain unchanged.

产品前／右视图的小标题使用图片外的原生网页文字。四语成品图只保留插图、参数与标注线；冻结绑定 `overview_finished_panels` 的 `captions_embedded: false` 恢复可见标题，旧版 `true` 仍隐藏重复标题。导出时按源 PDF 坐标排除标题，保留来源哈希及已批准勘误，不改写历史冻结版本。

自动恢复条件使用共享 `HB-TABLE-AUTO-RESUME`：两列表头，左侧 3 条、右侧 4 条，中间左格跨两行。四语原生 PDF 录入通过 ComponentSpec 调用既有 Web 表格渲染器；标题和引言在表外，条件为可选文字，不以列表或截图替代。新版本保留全部图片及已审勘误。

交流充电图的源稿裁区必须包含完整外框和左右下圆角。说明文字继续作为网页正文；移除图内重复说明时只剥离文字，不删除背景、产品线条或边框。四语共用图修复须一起重建并核对其余图文不变。

太阳能接线图若自带外框和留白，外层底色须与留白对齐，避免生成双重灰边。太阳能板可复用，整张主机接线图仍须核对型号与插座／接口版本；不能仅按语言一致就跨地区替换。

按键组合表由共享 `HB-TABLE-KEY-COMBINATIONS` 承载三列表头和操作行，通过 `manual-ir/v2` 的 ComponentSpec 直接复用英文 Web 表格渲染：深色圆角边框、40/25/35 列宽、首列灰底及正文常规字重。原生 PDF 的操作文案取文字区域，排除时钟图旁重复的时长标记；不改动句内时长或功能内容。
