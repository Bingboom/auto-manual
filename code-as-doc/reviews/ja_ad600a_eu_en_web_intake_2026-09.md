# JA-AD600A / EU / en Web intake review (2026-09)

Status: active

## Scope and authority

- Target: `JA-AD600A / EU / en / Web`.
- Source authority: operator-designated DingTalk PDF node `Gl6Pm2Db8D39waXaU9LzewOeJxLq0Ee4`.
- Source file: `Jackery_DC-DC_Charger_User_Manual_JA-AD600A_EUUK_V2.0_2026-05-29.pdf`.
- Source SHA-256: `72da87b9a88f3029a144f11f44fd1270e6e991977cf5ca3deb6be53656e544d9`.
- Physical PDF: 88 pages; English manual body is physical pages 4–17 (printed pages 01–14).
- Illustration master: user-supplied PDF-compatible Illustrator 30.7 file `16-0102-000322 HTO814A-US JP EU-JAK 说明书 RoHS REACH.ai`, 15 pages, SHA-256 `d89f145176c0c8ca10fa8c81768718ee32d52cb7a41a17b318df559a38e4f385`.
- Front cover, blank page, contents, printed page numbers, and non-English pages are not Web body content.
- No DingTalk live-table writes, queue dispatch, IDML, or Japanese work are part of this change.

The checked-in source snapshot is `data/manual_sources/ja_ad600a_eu_en/source_manifest.json`. It binds the PDF authority, target manifest, Product Manual Plan, structured copy, six CSV inputs, asset recipe, and illustration manifest by SHA-256.

## Shared architecture

`configs/config.charger-eu-en.yaml` remains the only family configuration. The target-specific difference is data:

- `docs/manifests/product_plans/ja_ad01a_eu.yaml` selects the existing compact charger slots.
- `docs/manifests/product_plans/ja_ad600a_eu.yaml` selects disclaimer, dimensions, important safety, FAQ, installation, and warranty slots.
- Tokenized page and illustration manifest paths resolve at build time from `{model}`.
- `charger-v1` supplies charger presentation ownership. JA-AD600A adds five installation figures; it does not inherit portable-power-station LCD, UPS, App, or auto-resume assumptions.

## Component and asset ownership

Native Web content owns headings, paragraphs, lists, compatibility/status tables, callouts, FAQ, and warranty copy. Source artwork is used only where the illustration itself carries necessary spatial meaning.

| Source page | Web component | Ownership |
|---|---|---|
| PDF 5 / AI 3 | specifications + dimensions | Native spec table; complete AI-source dimension figure |
| PDF 6 / AI 4 | inbox + overview | Nine responsive cards with clean item-only AI crops; complete product overview figure |
| 7–8 | safety, compatibility, power state | Native copy, tables, and warning callout |
| 9 | FAQ | Native searchable copy |
| PDF 10 / AI 8 | installation diagram | Complete gray installation frame and legend |
| 11–12 | safety and pre-installation | Native copy and warning callout |
| 13 | wiring | Complete three-frame art + adjacent native steps |
| 14 | vehicle-body mounting | Complete four-frame art + adjacent native steps |
| 15 | modification-panel mounting | Complete three-frame art + adjacent native steps |
| PDF 16 / AI 14 | connection + daily use + FCC | Complete connection art; other content remains native |
| 17 | warranty | Shared warranty cards with one 2-year period |

The approved artwork recipe archives all 15 Illustrator pages and exports 16 target-scoped PNGs. A cold AI-source replay produced 46 artifacts: 15 page archives, 15 previews, and 16 exports. Every export is hash-locked in the recipe, registry, and illustration manifest. The DingTalk PDF remains the authority for native Web copy and specifications.

## Source normalization and known debt

- Source line wraps and soft hyphenation were normalized for Web prose.
- The obvious source spelling `Phillios screwdriver` was corrected to `Phillips screwdriver`.
- The source FAQ Q4 contains the phrase `If the voltage of is higher`. It is retained to avoid inventing an engineering correction; source-owner clarification remains editorial debt.
- Inbox cable and fuse exports remove AI layout labels, letter markers, and separator lines because those labels are native Web card copy; the complete object drawings remain intact.
- There is no LCD, UPS, App, or troubleshooting-table debt for this charger. Those power-station capabilities are not applicable and are explicitly exempted.

## Publication boundary

Local build, Sphinx output, localhost preview, pushed branch, opened pull request, and green CI are separate evidence. None proves merge, centralized Hello-Docs publication, or live table update. Formal publication remains an operator-owned post-merge step.

## Main integration

The target uses the shared Web illustration path resolver, including `{model}` / `{region}` expansion. The charger skeleton explicitly disables inherited LCD and auto-resume table contracts with null values; optional component discovery respects those declarations. Both JA-AD01A and JA-AD600A build through the same shared IR entrypoint. Full regression and current-main CI are required before merging.

## 2026-10-07 English source-layout correction

Operator authority is now `HTO814-EU-9国语言-0924 (1).ai`, SHA-256
`65297e68dbd6c811c5a34bb38a589ef8939b3a9eed6113ef305b60125cffb348`.
English printed 01–14 maps to physical 3–16. The prior source and immutable
16-export recipe remain evidence for unchanged reused illustrations.

### Asset inventory before extraction

| Figure / slot | Candidates inspected | Identity / decision | Reason for extraction | Boundary policy |
| --- | --- | --- | --- | --- |
| Dimensions, inbox objects, overview, installation overview, connection | `docs/renderers/web/assets/ja_ad600a_eu_en/`, other target registries, `manual_sources/`, shared/template assets | Same JA-AD600A/EU ports, dimensions and English figure labels; reuse unchanged bytes | Not applicable | Complete diagrams and original backgrounds retained; inbox object labels restored as native copy |
| Wiring fuse / battery / ACC | Existing `wiring_steps.png` and shared/template assets | Aggregate artwork matches source but no separate per-step exports exist | Native 1–3 copy must stay beside the corresponding complete frame; aggregate panel cannot express this geometry | Current AI physical p12, each rounded frame retained in full including washers, notes and connector labels |
| Vehicle-body clearance / marking / drilling / fixing | Existing `secure_vehicle_body.png` and shared/template assets | Same product and steps; no individual frame assets | Separate 1–4 step/art bindings are required | Current AI physical p13; full gray artwork and frame edges retained |
| Panel marking / drilling / fixing | Existing `secure_modification_panel.png` and shared/template assets | Same mounting hardware; no individual frame assets | Separate 1–3 step/art bindings are required | Current AI physical p14; each complete panel retained |
| Status device | Existing overview/inbox art and shared assets | Existing objects do not show the lit green status lamp in the source | Missing source-authored lamp-location figure | Current AI physical p7 product-only region, no cell/page background |
| Warning triangle | `shared/symbols/native-v1/symbol_warning_triangle.svg` | Semantic warning triangle matches; reuse unchanged shared neutral-gray glyph | Not applicable | Transparent common symbol |
| Four lamp states | Shared LCD/button/symbol manifests and asset registry | No matching lamp glyph; native semantic CSS pills express the simple green/red/outlined shapes without per-language crops | No bitmap extraction | Shared source-declared roles, textual state preserved; blinking indicated statically without motion |

This is an English local source repair. Source FAQ Q4 and Interpretation Rights
remain flagged editorial debt; neither is guessed or silently rewritten.

The three former aggregate installation illustrations remain unchanged in the
manifest's `superseded_illustrations` inventory. They are not active bindings;
all 12 installation diagram/step assets remain required by figure coverage.
The shared warning icon is hash-pinned with `allow_reuse: true` for three
authored occurrences; no check is bypassed.

## 2026-10-07 shared wiring bases and editable labels

| Panel | Candidates inspected | Decision and source | Background / frame policy |
| --- | --- | --- | --- |
| Fuse assembly | Current wiring_fuse.png, aggregate wiring_steps.png, same-target and shared assets | Existing candidates bake seven English captions into pixels; no matching neutral base exists. Extract current AI physical p12 crop [195,119,346,261], SHA-256 65297e68dbd6c811c5a34bb38a589ef8939b3a9eed6113ef305b60125cffb348. | Preserve full rounded panel, inset clip groups, hardware, arrows, invariant 1/2 identifiers and fixed product markings. Omit caption paths 1438/1439 and native text; recreate two frames and seven captions in shared CSS / ReferenceFigure. |
| ACC cable splice | Current wiring_acc.png, aggregate panel, same-target and shared assets | No matching neutral panel; current AI physical p12 crop [195,402,346,498] has three native spans making two captions. | Native span-only redaction, graphics/images preserved, original gray inset and all four edges retained. |

This local correction uses an independent extraction recipe and the existing shared IR / ReferenceFigure component. The immutable sixteen-asset recipe, original step recipe, original PNGs and registry remain unchanged. Nine locales share the bases; only English labels are integrated in this turn. No Base/queue/registry writes or publication.

Compound PDF fill/stroke SVG paths differ only by explicit internal closure at an already closed subpath. The extractor compares these no-op closures while retaining both original source paths, transforms, clipping and opacity groups unchanged. A focused compound-path test covers the source failure.

Final local verification: the independent recipe exports the fuse SVG and ACC PNG/PDF plus a native ACC SVG companion. The fuse SVG retains 571 reviewed source drawings and the source SVG shading image (including its original transform/clip); it excludes only two independent frames and native captions. ACC label-only redaction keeps all 1,478 page drawing records, path topology, colors and coordinates exactly unchanged. The normalized crop PDF has minor renderer/rounding differences at 12x (mean maximum-channel difference 0.61, 2,091 of 1,964,024 non-label pixels over 16, maximum 25), after vector parity was confirmed.

Nine labels are captured as native ReferenceFigure copy (seven fuse, two ACC). Selection, measured bounds, source coordinates, shared base hashes and zero page overflow pass at 390/640/641/800/1280/1460 CSS pixels. The original twelve required installation slots remain mandatory: two now use live reference labels; none is exempted. Source text, source QA debt, registry and immutable source export recipes remain unchanged.

Actual Pandoc and strict Sphinx builds passed. Full repository regression: 5,214 tests, 35 existing skips, all remaining tests passed across 474 modules in four process shards. Ruff, maintainability guardrails and doc links passed. English preview and separately editable SVG text layers were visually checked on desktop/mobile. No merge, publication or live-table write was performed.
