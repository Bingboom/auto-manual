# JE-3000C EU English Web intake — 2026-09

## Scope and authority

- Target: `JE-3000C / EU / en`, Web manual only.
- Current authority: `Jackery Explorer 3000 User Manual (JE-3000C)-EUUK-V2.0-2026-07-31.pdf`, DingTalk node `a9E05BDRVQ6mQG3GhyyglLX9J63zgkYA`.
- Source lock: 102 pages; SHA-256 `55fee5a2f7538e58ebce17fc2bcfe3b0e4a8959233251961f6122ef7f420602d`; English body on physical pages 6–21 and EU declaration on physical page 102.
- Requirement record: Base `YndMj49yWjP03jNjCDojvAQdJ3pmz5aA`, table `97v7518`, record `FBHsOuFTMQ`; read only. It identifies HTE156 / E3000V2 / material `160102000382`, status `已定稿`, and the same formal source node.
- No calibration or version comparison was performed. The current PDF governs visible copy, parameters, ordering, and illustrations.

## Structure and reuse boundaries

The target snapshot uses the public phase2 schema and the existing EU English shared carriers. The existing `JE-3000C_PH` rows were used only as a structural starting point for the same hardware model; every voltage, frequency, current, power, temperature, port count, and product label used by the EU target was audited against the current EUUK PDF. Non-target parameters are not inherited.

Shared components remain responsible for safety, warning/callout treatment, inbox layout, LCD icon table, UPS, charging, storage, troubleshooting, specification, warranty, App setup, and EU regulatory copy. Target-local templates are limited to Overview and Operations because JE-3000C has no LED light or emergency charging section and its source order differs from the family default.

## Source-to-Web mapping

| Source pages | Web carrier | Treatment |
| --- | --- | --- |
| 6–7 | Safety, Symbols, Inbox | shared semantic components; current-source product/cable/manual object crops |
| 8 | Product Overview | two complete annotated source panels; duplicate live tables are exact-bound and consumed |
| 9–10 | LCD Display | current device display map plus 26 semantic description rows numbered 1–25; number 21 covers both temperature rows |
| 11–13 | Operations | complete grey-frame source panels; duplicate image-owned copy is exact-bound and consumed |
| 13 | LCD mode and output resume | device-only LCD crop beside an HTML/CSS semantic table; output-resume comparison remains a semantic table |
| 14 | UPS | shared carrier with current 10 ms / 12 A facts and current-source full panel |
| 15–16 | Charging | current-source full grey panels for AC, solar, and car charging; no emergency charging section |
| 17–19 | Storage, troubleshooting, specifications, warranty | shared semantic components with current-source values and `F0`–`FE` rows |
| 20–21 | App setup | current-source download, add-device/control, and connection-result panels inside the shared carrier |
| 102 | EU compliance | shared EU regulatory carrier |

## Asset provenance

`data/asset_recipes/manual_je3000c_eu_web.json` defines 18 deterministic 12x crops from the locked source. The approved replay produced 222 artifacts: 102 page PDFs, 102 previews, and 18 target exports. Every export has an expected SHA-256. Operation and charging panels retain their complete grey frames and image-owned text. No whole-page screenshot is used. The LCD mode crop deliberately excludes the source table.

The source and export records are registered locally in `data/asset_sources.csv` and `data/asset_registry.csv`. No live Base write, source upload, OSS archive, or centralized publication was performed.

## Dependency and delivery boundary

This branch is stacked on `feat/web-je2000f-eu-en` / PR #1082 because it consumes that target-aware Web illustration resolver and semantic LCD/auto-resume presentation work. PR #1085 (JE-2000E) and PR #1086 (JE-1000H, itself based on #1082) are sibling Web-target efforts and may overlap shared fixtures or the EU family manifest; they are not content sources for this target. The PR must remain unmerged until dependency review and normal CI complete.

Local build, localhost preview, and green checks are engineering evidence only. They do not mean the PR is merged or that a formal public Web route has been published.

## Main integration

The target now integrates the merged EU Web baseline. Shared fixture CSVs retain complete logical records when combining target additions, including quoted multiline symbol descriptions; this preserves the existing JP and US consumers. The final integration is validated against the current main and the full test suite before merge.
