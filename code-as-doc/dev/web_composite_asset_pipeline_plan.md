# Web Composite Asset Pipeline — Discovery and Implementation Plan

Date: 2026-08-01

## Outcome

An operator uploads an approved localized or shared artwork file to
`04_资产导出物.export_file`. `sync-data` freezes the attachment and a deterministic
manifest into the phase2 snapshot. Web rendering resolves that manifest by stable
component key and locale, and replaces the governed figure plus its associated copy
without putting the section heading inside the image.

ReadTheDocs consumes the committed fixture snapshot; it never needs live Feishu
credentials.

## Discovery

- The live business Base is `文档构建`
  (`LD3lb4G1ua4GOVs1vxAc9W2enje`, revision 39).
- The new asset chain is limited to `04_资产源文件`, `04_资产定义`, and
  `04_资产导出物`. The legacy `05_内容源_插图资产表` remains history-only.
- `04_资产导出物` currently has 142 records: 59 archive pages, 59 previews, and
  24 semantic exports. No record currently has an `export_file` attachment.
- `sync-data` mirrors only `04_资产定义` into `data/asset_registry.csv`; it does
  not fetch `04_资产导出物.export_file`.
- The Web renderer currently selects composite artwork from static paths in
  `docs/renderers/contracts/web_manual.json`.
- The current approved demo has nine logical Web composite components and 25
  physical files:
  - product overview front/right: three locales each;
  - main power, AC output, DC/USB output, energy saving, LED light: three locales each;
  - car charging: three locales;
  - app connect result: one shared file.
- App add-device remains a separate semantic component: shared text-free art plus
  live localized HTML labels. FCC, Symbols, LCD, What's in the Box, and other
  editable HTML components are not composite replacements.
- ReadTheDocs builds from a bare clone using `tests/fixtures/phase2`; it has no
  Feishu credentials.

## Contracts

1. `04_资产定义` owns logical identity, target scope, locale policy, approval,
   and `web_replace_key`.
2. `04_资产导出物` owns one physical export per row. A buildable Web row must
   have `artifact_kind=web-composite`, `gate_status=approved`,
   `build_eligible=true`, one attachment, a `web_locale`, and the attachment
   SHA-256 plus the governed source-fragment SHA-256. `web_locale` is a
   dedicated single-select (`en`, `fr`, `es`,
   `shared`); the older free-text `locale` remains a read-only compatibility
   fallback for snapshots created before this field existed.
3. Exact locale wins; `shared` is the only fallback.
4. Zero approved match leaves the semantic HTML figure and copy intact.
5. Multiple approved matches, a missing approved attachment, or a hash mismatch
   fails the sync/build instead of choosing silently.
6. The section title is never consumed by the composite component.
7. Original semantic image/copy remains in the HTML for accessibility when a
   composite image is displayed.
8. A materialized bundle freezes both the selected artwork bytes and the exact
   Web composite manifest; the bundle fingerprint includes them.

## Non-goals

- Do not alter IDML rendering or make IDML consume raster Web composites.
- Do not move ordinary RST images into the new export table.
- Do not rasterize FCC, Symbols, LCD, What's in the Box, tables, warnings, or the
  app add-device live-label component.
- Do not make ReadTheDocs contact Feishu during a build.
- Do not introduce a second asset registry or a page-specific renderer framework.

## Implementation Phases

### Phase 1 — safety net and pure manifest logic

- Add unit coverage for definition/export normalization, approval gates,
  locale resolution, duplicate rejection, missing attachment rejection, and
  hash verification.
- Add a versioned `web-composite-manifest/v1` loader and resolver.

### Phase 2 — snapshot synchronization and bundle freezing

- Fetch the two frozen `04_资产*` table bindings through the existing source
  adapter.
- Download approved attachments under
  `data/phase2/_attachments/web_composites/` and generate
  `data/phase2/web_composite_manifest.json`.
- Stage target-matching assets into a materialized bundle under
  `_assets/web_composites/`; include the staged manifest in the bundle hash.

### Phase 3 — Web rendering

- Replace static artwork paths with stable `web_replace_key` plus locale/source
  pattern mappings.
- Resolve artwork from the frozen bundle manifest in `transform_web_fragment`.
- Preserve semantic fallback and accessibility content when no approved export
  exists.

### Phase 4 — live Base promotion

- Add `web_replace_key` to `04_资产定义`.
- Add `source_fragment_sha256` and the dedicated `web_locale` single-select to
  `04_资产导出物`; add `web-composite` to `artifact_kind` and localized/shared
  composite options to `04_资产定义.text_policy`.
- Create nine logical asset records and 25 physical export records, upload the
  current approved files, then read back every record and attachment token.

### Phase 5 — reproducible Web and ReadTheDocs build

- Run live `sync-data`, verify every downloaded SHA-256, and rebuild the full
  JE-1000F/US Web manual.
- Freeze only the Web composite manifest and attachments into the tracked RTD
  phase2 fixture.
- Run the full repository validation ladder and update the existing Web PR.

## Verification Ladder

1. `python3 -m ruff check build.py integrations tools tests scripts`
2. targeted Web composite, sync, Web presentation, and Markdown tests
3. `python3 -m unittest`
4. `python3 -m mypy tools/utils`
5. `python3 tools/check_maintainability_guardrails.py`
6. `python3 tools/check_doc_link_integrity.py`
7. `python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US`
8. Web Markdown/Sphinx build from the committed RTD fixture
9. PR checks and the post-merge ReadTheDocs build
