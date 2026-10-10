# JE-3600A / EU batch 1465 Web backport

Status: active

The shipped Spanish Web headings still contain French copy, and the Italian F0–F6 table still contains German measures. Batch 1465's delivered corrected AI/PDF supplies the reviewed replacements. New immutable `1465-20261010-r1` packages under the existing Spanish and Italian source directories carry these edits; seven other languages and every historical package remain unchanged. No print pagination or reviewer color is transferred.

## Exact source and scope

- Original source: `HTE139-EU-9国说明书-0924.ai`, SHA-256 `47a346dcfec4966ac98fbe1426e4f2b89cf54a964e4d1baf2ad9c7b02dc78043`, 161 physical pages. Exact original bytes are included in each revised package for independent fresh symbol admission. Git stores the identical two copies as one blob.
- Baseline: `git-20261005-47a346dc`. The affected baseline Markdown was compared byte-for-byte to Hello-Docs main `3036ab31557e49cf467550b624ddbfce59ac1382`'s frozen published sources.
- Delivered revision: `JE-3600A_修正版_竖版.pdf`; semantic selections confirmed at physical pages 45/49/51/88. Printed pages 38/42/44/81 are evidence only, not Web routing keys. The candidate index's printed p7 is not a reliable page mapping.
- Original native capture ledgers retain historical text as provenance. Corrected `source/chapters.json`, the shared Manual IR assembler and replay own candidate content. `source/1465-errata.json` records every exact old/new semantic delta.
- Existing source manifests declare `live_bitable_dependency=false`. No live Base write, re-seed, review-branch edit or direct `docs/publish` write belongs to this Git-only source correction.

## Text corrections

| Language | Target | Old | New |
| --- | --- | --- | --- |
| es | LCD chapter and operation heading; corresponding accessibility labels | AFFICHAGE LCD | PANTALLA LCD |
| es | Connections heading | CONNEXIONS | CONEXIONES |
| it | F0/F1/F2/F3 | Starten Sie das Gerät neu. | Riavviare il prodotto. |
| it | F4 | German discharge-load measure | Collega il prodotto ai carichi per scaricare la batteria fino a quando il guasto scompare. |
| it | F5 | German solar/AC charging measure | Caricare il prodotto tramite pannelli solari o una presa a muro CA fino a quando l'errore non scompare. |
| it | F6 | Five German steps | The five delivered Italian steps, retaining the 20 cm clearance and electrical-grid / sunlight / idle / restart sequence. |

F7/F8/F9/FA/FC, all fault code ordering, and all non-target text remain exact. Spanish accessibility copy changes include the corresponding governed source-fragment hash recalculation. Tables and labels remain native HTML / semantic components.

## Authorized symbol admission repair

Fresh sealing rejected both the unmodified baseline and text candidates because the historical packages lack source-bound symbol admission. The operator authorized this additional repair. Both locales now carry eight ordered bindings to original native symbol rows (es physical 43, it physical 77), source caption rectangles/pixel hashes, complete native glyph drawing selections and existing shared transparent asset keys. Glyph positions differ by locale; each uses its actual source geometry.

| Symbol | Existing shared variant | Decision |
| --- | --- | --- |
| symbol-warning_triangle.png | `warning/outline-triangle-tinted` | Byte-identical reuse; old raster retained as superseded evidence. |
| symbol-read_manual.png | `read-manual/book-information` | Byte-identical reuse; old raster retained as superseded evidence. |
| symbol-do_not_dismantle.png | `do-not-dismantle/screwdriver-prohibited` | Byte-identical reuse; old raster retained as superseded evidence. |
| symbol-no_open_flame.png | `no-open-flame/fire-match-prohibited` | Byte-identical reuse; old raster retained as superseded evidence. |
| symbol-keep_away_from_children.png | `keep-away-from-children/adult-child-prohibited` | Byte-identical reuse; old raster retained as superseded evidence. |
| symbol-li_ion.png | `li-ion/recycle-li-ion` | Byte-identical reuse; old raster retained as superseded evidence. |
| symbol-battery_disposal.png | `battery-weee/crossed-bin-no-bar` | Byte-identical reuse; old raster retained as superseded evidence. |
| symbol-weee.png | `weee/crossed-bin-bar` | Byte-identical reuse; old raster retained as superseded evidence. |

All sixteen rows pass the fixed glyph comparison tolerance (0.02), original-file hashing, caption-pixel comparison, shared-catalog byte binding and transparent margin checks. No new glyph, shared catalog edit, live asset registry promotion or comparison tolerance change is introduced. `assets_manifest.json` and `source/symbol_asset_decisions.json` retain the old source/hash and mark its former raster use `superseded-do-not-reuse`. Non-symbol artwork bytes and stylesheet remain unchanged.

The Spanish battery-disposal caption contains the printed split `independiente-\nmente`. Its approved native intake already joins this into `independientemente`. The source row now declares precisely that fragment in `caption_linebreak_joins`. Admission accepts a declared fragment only if it contains an actual line-ending word split and occurs exactly once inside the hash-bound source caption. Inline hyphens, missing/duplicate declarations, unmatched fragments and residual word differences are rejected. Caption pixel hashing and complete native vector reconstruction remain mandatory. A real-PDF regression exercises both acceptance and these rejection paths.

## Verification and release boundary

- 14 symbol-admission unit tests pass, including the real-PDF linebreak regression and existing glyph/caption/source/shared-catalog tamper rejection tests.
- Full repository unittest, lint, maintainability guardrails and documentation links: results will be recorded before draft PR creation.
- Spanish and Italian strict Sphinx `-W` builds pass; fresh shared-component and sixteen symbol-row admissions pass.
- Both packages cold-replay deterministically, seal successfully, and verify their sealed source/Markdown/HTML evidence. Initial local receipts identify an uncommitted candidate and will be resealed against the source commit before review.
- Desktop 1280px and mobile 390px: no broken images or document overflow; eight symbol rows preserved. The narrow troubleshooting table retains the existing horizontally scrollable, keyboard-focusable semantic component. Screenshots inspect shared symbols and Italian troubleshooting. Local evidence remains below `/private/tmp/1465-web-backport/JE-3600A-evidence/`.
- Historical `build.py check --config configs/config.eu-en.yaml --model JE-3600A --region EU --data-root manual_sources/JE-3600A/EU/en/2026-05-25/phase2` passed. This regression does not validate revised native language prose.

These source packages and local previews are release candidates. Human engineering PR review/merge, mirror sync, controlled generated `publish → main` release PR, human publication merge and RTD receipt/live readback are still required. The task does not self-merge or claim that the website is corrected.
