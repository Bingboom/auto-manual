# Optimization checklist: Milestone J (asset loop)

Part of the [optimization checklist](../next_optimization_checklist.md); its index lists every milestone page,
and its §1 update rules apply here. Update item status on this page and add new
items for this milestone here, not to the hub.

## 6h. Milestone J: Asset Loop — 图片与 .ai 源的单一真相

Registered 2026-07-13 (operator-approved decisions: .ai lives in the Feishu
attachment column; existing text-burned illustrations get scheduled textless
rework; temporary crops/placeholders register as explicit debt when the
publish gate lands; the maintainer registers on designers' behalf). Extends
the single-source principle to assets: the .ai file is the source, exports
are projections, and a textless base image + data-layer text makes an asset
language-neutral (the LCD-hero precedent).

- [x] PR J0: Asset census + registry (P0; done 2026-07-13)
  - Status: `done` — the initial Feishu census is retained as historical input,
    while the build-facing mirror is `data/asset_registry.csv`; the legacy table
    is not consumed by the new asset pipeline. After the registered vector
    harvest in the stacked asset PRs, the current mirror is
    **63 成品 / 3 临时替代 / 4 缺失 / 1 隔离** (the missing list IS the
    design-side request list); repo mirror `data/asset_registry.csv`;
    naming contract `<asset_key>[-<lang>].{pdf,png}`; ops guide §4.9.
- [x] PR J1: Asset resolver + publish gate (P1; done 2026-07-27)
  - Status: `done` — `build.py asset-check` validates registry exports, final
    bundle assembly resolves semantic `asset:` references after review overlay
    with target/status gates, and all 183 template image/figure directives now
    resolve through `asset:`. Resolution refuses every non-`✅成品` row
    (verified live: an unregistered key, the `⛔隔离` back cover, and the
    `🔧临时替代` warning lockup are all rejected), and `--publish` additionally
    refuses the `--allow-temporary` escape hatch.
  - The registry mirror joined `sync-data` via `tools/sync_asset_registry.py`
    (the capability-mirror pattern: pure transform + injected deps + tracked
    CSV + `derived_files` manifest entry). It is an **overlay, not a replace**:
    the Feishu `04_资产定义` table owns what an asset is and whether it may
    build (类别 / 语言维度 / 状态 / 待无字化 / 适用机型 / 适用区域 / 语言变体),
    while the repo keeps `导出物路径` and `内容哈希` (they describe committed
    bytes) plus `备注` (maintenance history; the Base's own notes are intake
    rationale, a different record). Rows are never deleted — a vanished Base
    row must not drop a registry row templates still resolve through — and the
    merged CSV is parsed back through the resolver's own loader before it is
    written, so bad Base data fails the sync instead of landing a registry the
    build would reject. Table coordinates come from the frozen
    `data/asset_base_bindings.json`, so no new GitHub secret is required.
    Live dry run against the Base: 10 managed rows, 82 in / 82 out,
    byte-identical, and a simulated Base edit propagates while the repo-owned
    columns survive.
- [ ] PR J2: .ai sources into the pipeline (P2)
  - Status: `in progress` — deterministic `asset-intake` now freezes and splits
    the JE-1000F US PDF-compatible `.ai` master into verified archive/previews,
    recipe exports, manifest/CSV, and a reproducible ZIP; its full source hash
    and verified Base record pointer are recorded in `data/asset_sources.csv`.
    The three dedicated `04_资产*` tables now exist, their live bindings are
    frozen in `data/asset_base_bindings.json`, and the AI/ZIP/manifest attachment
    round trip plus 10 definition / 142 export rows have been verified. The
    registry mirror still needs to join `sync-data`, and later native-artboard
    automation needs evidence from more than this PDF-compatible master.
  - Done when: designers' .ai files live in the registry's attachment
    column with content hashes; the one-page designer workflow (deliver →
    register → sync) is documented; optional ExtendScript batch export
    (the indesign_finalize.jsx precedent) evaluated.
- [ ] PR J3: Publish full assembly (P3)
  - Status: `in progress` — publish lineage, the publish gate and the QR
    cross-check landed; the InDesign package leg is still open.
  - Done: the release manifest gained an `assets` section
    (`tools/release_asset_lineage.py`, the I3 provenance shape) recording the
    bundle fingerprint, the registry-snapshot hash, and every registry-backed
    asset the build actually consumed with its format, content SHA, status and
    resolution source; the release CSV gained four flattened columns. `publish`
    gained a gate between the last prepare and the manifest that refuses a
    bundle which consumed a `🔧临时替代`, `❌缺失` or `⛔隔离` asset, or that
    carries no frozen lineage at all. QR assets cross-check the printed-URL
    inventory inside `asset-check` (already a CI job): an approved `二维码` row
    must declare what it encodes in `data/printed_url_manual_entries.csv`, a
    non-shippable one may not be a live printed target, and a printed target
    may not point at an unregistered asset.
  - Evidence: a real `publish` for JE-1000F/US passes the gate with 20 registry
    assets and bundle `9f7ede5431b9`, and the manifest carries the same numbers.
    The gate deliberately does **not** block `legacy-path` images — the real
    bundle still consumes 50 of them from data-generated pages, so blocking
    would stop every publish instead of surfacing debt; the count is recorded in
    the manifest so it can be ratcheted down later. **Ratcheted to zero on
    2026-07-27:** #726/#730 keyed the review overlay's 13 path references
    (two of which were stale shared images superseded by target overrides —
    operator-reviewed before flipping), and the finalizer now attributes the
    37 synced Feishu attachment images to their `feishu/*_attachments`
    collection rows as `feishu-attachment` manifest entries (per-file bytes
    recorded, collection status gates publish, RST keeps path references
    because file identity is the Feishu token). JE-1000F/US:
    `legacy_path_count=0`, `registry_asset_count=59`. The back-cover QR was
    decoded independently rather than trusted from its 备注: the approved AI
    candidate encodes `160102000404` (the master's own document number, not a
    URL), while the quarantined frozen reference encodes the older
    `160102000161`.
  - Also done: the release manifest gained an `indesign_package` section
    (`tools/release_indesign_package.py`, same collector shape) recording the
    IDML, INDD, InDesign PDF, delivery handoff zip (which already carries
    `Links/` and the font manifest from `tools/idml/delivery.py`) and both the
    finalize and parity reports with sha256, plus the preflight numbers and the
    parity verdict; the release CSV gained six columns. Finalize and parity
    artifacts now have a canonical home beside the production IDML in
    `docs/_build/<model>/<region>[/<lang>]/idml/`, documented in the ops guide.
    `publish_meta.json` gained `handoff_package_path`: the queue already copied
    the handoff zip into the release version directory, but nothing pointed at
    it. Every part is optional — InDesign finalize and parity run on an
    operator Mac, not in CI, so an unattended publish records what exists and
    marks the rest absent instead of failing.
  - Verified against a real build directory (`auto-manual-codex`): the collector
    picks up the 741 KB production IDML and the 3.2 MB `1.7_handoff.zip`, hashes
    both, and reports `complete=false` for the absent INDD and preflight.
  - Done when: an operator finalize run for JE-1000F/US is captured end to end
    (`complete=true` with `parity.accepted=true`) — currently blocked, see the
    reference-layout drift note below.
- [ ] Open finding (2026-07-27, half resolved): production IDML still cannot be
  built from a clean checkout — the remaining half needs an **operator decision**
  - `python build.py idml --idml-mode production --model JE-1000F --region US`
    fails the same-source contract with
    `source_identity.snapshot_sha256 does not match the current manual IR;
    source_identity.layout_params_sha256 does not match the current manual IR`.
  - **The layout half is fixed.** Root cause reproduced exactly: #720 refreshed
    `layout_params_sha256` and then took one more correction to
    `data/layout_params.csv` (`lang_en_idml_ups_caution_space_after`
    9.9pt -> 15.9pt) without recomputing it — reverting only that value in the
    committed CSV reproduces the pinned `046f6f5a…`. The pin agreed in #715 and
    #718, so it was a #720 regression, not a standing condition. The pin now
    describes the committed file, and `tools/check_reference_layout_pins.py`
    (its own CI job) fails on this class of drift from now on. **Still owed: the
    approved reference layout has not been re-validated against 15.9pt by a
    parity run** — that needs an operator finalize + `idml_pdf_parity.py` pass.
  - The snapshot half is not reproducible by design: `snapshot_sha256` binds the
    contract to one phase2 snapshot, and `data/phase2/` is untracked apart from
    `page_registry.csv`, so no clean checkout can reconstruct it without the
    operator's local snapshot.
  - No CI job builds production IDML, which is why nothing caught this for three
    merges; #720's own post-merge run was additionally cancelled by the merges
    that followed it. The new pin guard covers the repo-derived pins; the
    snapshot pins remain unverifiable from a checkout by design.
  - **Step-by-step procedure:
    [`dev/reference_layout_rebind_parity_runbook.md`](../dev/reference_layout_rebind_parity_runbook.md)**
    — copy-pasteable, with the release gate on `page_bindings=0` and the
    verification status of each step stated.
  - The snapshot half is what still blocks the build; the error is now only
    `source_identity.snapshot_sha256 does not match the current manual IR`.
    Note the chicken-and-egg the runbook resolves: rebinding needs a
    `manual.ir.json`, which the production export writes — but the production
    export is what the gate refuses. `--idml-mode flow` produces the IR without
    passing through that gate (verified 2026-07-27). A dry-run of the rebind
    reports `page_bindings=0 composition_map=unchanged`, so it moves the data
    snapshot identity only and touches none of the 52 page bindings.
    `tools/reference_layout_rebind.py --plan … --manual-ir … --write` is the
    intended repair, but the contract carries an `approval` block, so rebinding
    it against a freshly synced snapshot is an approval decision.
  - JP is blocked separately and for a different reason:
    `page-0002-01_meaning_of_symbols: skipped_raw=1`.

- [ ] **JE-3000C KR 的 13 幅插图没有可复现的提取路径**（2026-08-29 登记）。这
  条产线的 15 个二进制里，只有 `overview/je3000c_kr/right_art` 有配方
  (`data/asset_recipes/manual_je3000c_eu_uk_overview.json`)；其余 13 幅（operation
  ×5、charging ×3、network_pairing_panel、app ×2、overview_front、封面整页）既无
  `data/asset_recipes` 条目也无 `data/asset_sources.csv` 源行，PR #964 的提交说明
  也没有记录来源。资产登记行锁住了**已提交的字节**（哈希）与可建状态，但没人能
  从母版重新裁切这批图。收敛路径：操作者提供 KR 母版 → 登记
  `data/asset_sources.csv` 源行 → 按 `asset-textless-extraction` skill 为 12 幅
  矢量图写一份 `data/asset_recipes/manual_je3000c_kr_*.json`。同时这 14 行对飞书
  `04_资产定义` 镜像而言是 unmanaged（与 `page/jbp2000b_us/cover` 同状态，sync 不
  删除、原样放行），应在下一轮资产入库时补登。

- [ ] **多语言手册的插图是按区域分版的，不是同图换字**（2026-09-15 登记）。JE-1000H
  EU 一本 PDF 承载六个语言块，逐张像素比对后确认：**英语块画的是英标三扁脚插座
  (BS 1363)，fr/es/de/it/uk 画的是欧标圆孔 (Schuko)**；进一步地 de/it/uk 三者字节
  相同（`inbox_unit`/`inbox_cable`/`inbox_documents`/`ups` 四张），it/uk 另有三张
  相同（`charging_solar`/`charging_solar_adapter`/`lcd_map`），而 en/fr/es 三者两两
  互不相同。126 条配方条目只落成 115 张唯一图。

  风险在于这类错误**文本层完全看不出来**：若用英语底图配本地化标注，标注文字全对，
  印出来却是错的插座制式。现有的 `content_lint`、术语校验、语言纯度门都不覆盖图像
  内容。

  已有护栏：`tests/test_je1000h_eu_en_web.py::test_every_locale_binds_its_own_finished_panels`
  断言 JE-1000H 六语各自独立、非英语不得与英语同哈希。全库扫描（按
  `docs/renderers/web/assets/<model>_<region>_<lang>/` 比对）当前**无任何产线复用英语
  美术稿**。

  未收敛的部分：
  1. 该护栏是按产线写死的，只管 JE-1000H。目前有多语言成品整图的只有 `je1000h_eu`
     与 `je2000f_eu` 两条线；其余欧规多语产线（JE-2000E / JE-3000C / JE-3600A /
     JBP-2000B）的非英语路线走的是组合图而非成品整图，其底图是否带区域制式、是否
     与英语共用，尚未逐条核实。
  2. 资产登记表没有"该图画的是哪种插座制式"这一维度，`语言变体` 只记语言。没有数据
     层可供闸门判断，只能靠逐产线的哈希互斥测试。
  3. de=it=uk 的字节相同是**巧合而非规则**（恰好这几张无文字），不得据此把三者合并成
     一套；一旦某张图后续加了文字就会分叉。

- [ ] **JE-1000H EU 印刷版的六处源内容缺陷**(2026-09-15 登记,随非英语译文入库发现)。把
  PDF 六个语言块的译文抽进冻结源时逐条比对出来,均属**已印制成品**的问题,需设计/内容侧
  回退,不是本仓可自行改正的:

  1. **德语块的安全符号与文字对错了**(最严重)。`symbols_blocks` 表中,🚫扳手(禁拆解)图标
     配的文字是「Vermeiden Sie Hitze.」(避免受热),🚫火焰(禁明火)图标配的是
     「Demontieren Sie das Produkt nicht.」(请勿拆解)。其余五种语言均正确。入库时已按
     行键语义(`do_not_dismantle` / `no_open_flame`)对正,**未沿用印刷错配**。
  2. **德语与意大利语的 LCD「充电计划」整段描述印的是法语**(`lcd_icons_blocks` 第 4 行)。
     入库时留空该两格,改走 `icon_desc_en` 回落(渲染器有 `fallback_columns`),避免德/意手册
     里出现整段法语。德语该行名称印作「Ladeplan Plan」(德法混排),按原样入库。
  3. **`ENVIRONMENTAL OPERATING TEMPERATURE` 在德语和意大利语块未翻译**,印的是英文原文。
     按原样入库到 `spec_titles.title_de` / `title_it`。
  4. **意大利语与乌克兰语的商标注记里混着德语 "und"**:「USB Type-C® **und** USB-C® sono
     marchi registrati…」/「… **und** … є зареєстрованими…」。按原样入库。
  5. **乌克兰语的 WARNING 标签印成意大利语 `AVVERTENZA`**(`symbols_blocks` signal 行)。
     按原样入库。
  6. **法语概览页的额定值文字本身被截断**为「1800 W nomina」(应为 nominal)。属成品图内容,
     已随 `web/je1000h/eu/fr/overview_front` 原样入库并在配方/登记表备注。
  7. **德语加电包扩容页的警示词印成法语 `ATTENTION`**(同一页上方 UPS 段落却是正确的
     `Vorsicht`)。新建的 `targets/je1000h/07_extra_battery_de.rst` 用 `symbols_blocks` 的
     德语审定词 `VORSICHT`,**未沿用印刷错词**。

  另:乌克兰语「自发自用模式」印作「Режим самозабезпечення」,而本产线其余型号统一用
  「Автономний режим」,属同产线术语分叉。已按各自印刷原文入库,并在
  `data/capability_page_rules.csv` 给能力门补了该同义词(放宽,非收紧)。待术语侧统一。

- [x] **JE-1000H 非英语路线的页面模板骨架**(2026-09-15 登记,同日闭合)。当时六语 Web 投影
  已绿但底层有两类缺口,现均已处理:

  - `03_product_overview` / `05_operation_guide` / `12_app_setup` 的 `_placeholder` 模板里,
    标注并非硬编码而是 `|MAIN_POWER_BUTTON_LABEL|` 这类取数 token——英文残留的真因是
    `Spec_Master.csv` 尚有 15 行未填、回落成了英文。补齐后该表 53/53(乌语因一行纯数值单位
    也补齐),**五语 md 的英文标注残留全部归零(含图片 `alt` 无障碍层)**。标签取值:印在概览页
    上的 10 个用 PDF 原文(按字体权重区分标注与规格值,左栏 8 项/右栏 7 项六语完全对齐);
    `total_output` 两行未印在该页,用 JE-2000E 已审定译法与式样代入 JE-1000H 数字;
    德/意的 `dc_input` 标签在 PDF 里拆两行印,改用 JE-2000E/JE-2000F 一致的合并形态。
    全表数字序列自校验 0 处不一致。
  - `07_extra_battery` 原先回退到 `targets/je2000e/07_extra_battery.rst`(仅注释的空载体),
    页内没有图位。现按 `targets/je3600a/07_extra_battery_<lang>.rst` 先例新建了五个按语言
    模板,内容从 PDF 该小节抽取(标题/导语/4 条注意事项/3 个物品标签,抽取器先在英语上验证
    10 项逐字命中模板),五个清单加 `JE-1000H` model_override,并重新绑定 `battery_pack`——
    非英语成品整图由 19 张增至 20 张。

  遗留一小项:新模板的 `:alt:` 是**沿用 JE-3600A 已审定式样改写**的(印刷版没有 alt 文本),
  乌语那条按同结构用乌语手册自身词汇撰写,建议随下一轮语言审校一并过目。
