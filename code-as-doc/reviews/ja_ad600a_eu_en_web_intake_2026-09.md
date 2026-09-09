# JA-AD600A / EU / en Web intake review (2026-09)

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
