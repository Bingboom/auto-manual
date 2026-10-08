# JBP-1000B-SIL US native PDF Web intake

Status: active

## Discovery and execution plan

Authority: `Jackery Battery Pack-1.pdf`, SHA-256 `7afcb2a1e9e7b2011ddbfbe3ed81aa6c5ec5d196e4d9ad008208195fa06b6137`, 52 physical pages. English 4–19, French 20–35, Spanish 36–51; shared prefaces and contacts on 1–3/52. This is the FridgeGuard battery, not JBP-2000B. Preserve its native wording/specifications and installation steps.

Git-only: source-local frozen input + shared Manual IR/ComponentSpec replay. No phase2 enrollment, Base, queue or live registry writes; no publication authorization for this target. Isolated worktree preserves root tmp and all other checkouts.

Reference structure: JBP-2000B EU English chapters/components; retain this source's additional positioning/vertical/wood/concrete installation. Existing family configuration stays unchanged.

Phases: (1) inventory shared assets and source text/geometry; (2) EN semantic content and artwork via committed asset operators, strict Sphinx/cold replay, desktop/mobile visual acceptance; (3) only after EN acceptance, native FR/ES content over byte-identical neutral art; (4) source coverage, hash/geometry checks and PR validation. Source-local files under data/manual_sources/JBP-1000B-SIL/US; source recipe under data/asset_recipes. No shared renderer changes unless independently justified.

Safety net: source hash and page count, individual asset/input hashes, native text coverage census, original-vector provenance, no duplicate artwork labels, forbidden caption-frame checks, desktop/mobile image and text geometry. Rebuild outputs use unused scratch directories.

## Artwork selection before extraction

| Role | Candidates | Decision and reason | Background policy |
| --- | --- | --- | --- |
| Seven safety symbols | shared/symbols/native-v1; legacy common PNG | Inspect native glyph and transparency; reuse matching native variants; reject withdrawn legacy hashes | True transparency; no page/cell grey backdrop |
| Battery/product diagrams | jbp2000b_eu_en; je1000e_sil_us_en; supplied PDF | Different battery silhouette/thickness/connectors and installation geometry; native extraction required for product-specific art | Preserve structural panels/shading/leaders; independent text pills drawn in CSS |
| Manual/cable/brackets cards | JBP-2000B inbox candidates; native p5 | Compare actual cable/manual/stands, reuse exact candidate only | Complete object boundaries |
| FR/ES artwork | English neutral assets | Reuse byte-identical after English visual acceptance; native labels remain locale-specific | No per-language recrop |

## Source exceptions

Recover missing native PDF extraction segments against rendered text and record exact replacement. Preserve FR storage interval and ES residual English/product naming discrepancies with an explicit audit; do not silently translate or alter legal copy.

## Verification and acceptance

English layout acceptance was recorded at 2026-10-08T16:16:26Z before native French/Spanish production. Final acceptance at 1280×900 and 390×844 covers all three locales: 52 loaded images each, zero broken images, zero page horizontal overflow and no clipped live figure labels. Browser inspection covered safety glyphs, overview/LCD, power controls, positioning, vertical/wood/concrete installation, connections/charging/storage and warranty. Steps use two desktop columns and one mobile column; narrow installation-result artwork is capped at 120px. Complete product/panel/leader bounds are retained, SOLD SEPARATELY and car-note frames are CSS, and figure labels remain editable HTML. The LCD table scrolls internally on narrow screens.

All three packages share the same 52 source artwork bytes. Existing warning/WEEE assets were reused exactly. Five source-matched transparent native glyph variants were added to the shared symbol catalog once; older valid variants remain intact. Twenty-one source-bound symbol rows pass the fixed comparison gate with no threshold relaxation. Rejected legacy raster hashes are recorded and cannot return in fresh validation. The connection-note battery glyph is restored as an inline native SVG; an existing x8 glyph was rejected because its shape differs.

Native line census passes: EN 398, FR 446, ES 443. This complements visual and semantic inspection, rather than proving text placement by itself. Native defects remain documented in source/native_exceptions.json, including French 2-month storage versus English/Spanish 12 months, residual English/Spanish in the French installation copy, residual English in Spanish, and source warranty/product-naming defects. No unsolicited translation or correction was made.

Validation commands (all from this isolated worktree):

```sh
python3 -m unittest tests.test_symbol_asset_admission tests.test_caption_frame_admission tests.test_web_frozen_source_evidence
python3 -m ruff check build.py integrations tools tests scripts
python3 -m ruff check data/manual_sources/JBP-1000B-SIL/US/git-20261008-7afcb2a1/rebuild.py data/manual_sources/JBP-1000B-SIL/US/git-20261008-7afcb2a1/validate_source.py
python3 tools/check_maintainability_guardrails.py
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off AUTO_MANUAL_PRESENTATION_PROFILE=web python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US --lang en --data-root tests/fixtures/phase2 --staging-root tmp/jbp1000b-sil/fixture-regression-final --no-clean --skip-root-index
```

Targeted tests: 29 passed. The existing US/en fixture build check passed; it validates pipeline regression, not this battery's native body or phase2 enrollment. An optional JBP-2000B family check failed because the available unrelated phase2 snapshot has no matching symbols rows; no Base/snapshot changes were made. The documented fixture check replaces that unsuitable optional dataset check.

The extraction recipe reproduced all 154 artifacts (50 exports, 52 archived page PDFs, 52 previews) against pinned hashes. Intake manifest SHA-256: ec5da10a75cf717a2da3a4e99f7d36b0b7a28a674927325c1e90971bdb9da165. Recipe geometry and source artwork decisions are synchronized; frozen inputs and shared contracts are hash-bound. Three fresh cold replays, frozen byte parity, strict Sphinx, native text/artwork validation, caption-frame admission and all 21 symbol rows are checked again after the final freeze. A deliberately wrong input hash is rejected without modifying source files.

Final local previews: port 8892, /final/{en,fr,es}/manual_jbp1000bsil_us_{en,fr,es}.html. This intake is an engineering Git-only candidate. It has no merge, Hello-Docs mirror, RTD receipt or live acceptance claim.

Full canonical-temp unittest regression: 5217 tests, OK (skipped=35), 717.283 seconds. Only the test process temporary path was resolved; no host configuration changed.
