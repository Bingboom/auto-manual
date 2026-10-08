# JE-100C KR Korean Git-only intake

Status: active

Operator-approved Web source (2026-10-07, “提交发布”; MA-270). User-supplied V0.3-Q PDF is the sole content authority; no live-table reads/writes or publication. Physical page 1 (cover) and 13 (removed packaging page) are excluded. Pages 2–12 are included. Source is outlined, so Apple Vision OCR was verified against page renders; OCR JSON is evidence, not the authored source.

## Asset selection before extraction

| Slot | Existing candidates | Decision and evidence | Boundary |
| --- | --- | --- | --- |
| Inbox unit/cable/manual | je100c_eu_en/inbox_*.png | Reuse byte-for-byte: same housing, USB-C cable and document pictogram | No new crop |
| Symbol icons / LCD icons | je100c_eu_shared/ | Reuse semantic symbols, not English descriptions; Korean descriptions stay native | Preserve existing transparent icons |
| Overview | je100c_eu_en/overview.png and EU locale overview SVGs | New crop: Korean labels and KR source has side strap callout, unlike English text | Entire figure excluding live heading and footnote |
| LCD maps | je100c_eu_en/lcd_interface_*.png and EU locale lcd*.svg | New source map crops: KR interface 1 displays 888W/00.1H, existing English map 0W/99.9H; exact source maps retained as a group | Map only; glossary remains native |
| Output/energy panels | je100c_eu_en/operation_*.png | New crop: complete source panels carry Korean instructions | Include full rounded frame, exclude section heading and separate notices |
| LCD device drawing | je100c_eu_en/operation_lcd.png | Reuse same DISPLAY artwork, housing and orientation | Instructions remain a native table |
| AC/solar/car panels | je100c_eu_en/charging_*.png and EU locale assets | New crop: Korean embedded captions; retain KR drawing and whole panel | Full panels, no section headings or adjacent warnings |

## Source wording retained

Physical p6 labels the F8 fault icon “남은 배터리 용량”. The operator approved correcting the Web label and image alt text to “오류 코드” (fault code). Original PDF remains unchanged. No EU safety, warranty or technical values are substituted.

## Local verification

- Shared KR config target check: passed, with missing capability-row and source-terminology warnings preserved for review.
- Real Pandoc Git-only Markdown build and Sphinx `-W -D language=ko`: passed.
- Browser: all 37 images loaded; native notices, five specification tables and LCD descriptions retained; ten main sections; cover and physical page 13 excluded.
- Source and generated illustration SHA-256 records are in the candidate source manifest.
- No live-table write, publication, merge or production-admission claim.
- JE-100C EU shared-component regression: 7 tests passed. Documentation link/lifecycle check: passed.
- 64 source/asset hashes verified; all nine crops reproduced byte-for-byte from source PDF.
- Browser responsive check at 1280px and 390px: no horizontal document overflow, no missing images.

## LCD operation artwork correction

Operator requested removal of the inherited partial frame. The reused EU operation_lcd.png contained a left frame fragment. Replaced it with a KR source p8 crop of device, hand and DISPLAY callout only; the native HTML owns the complete outer frame and table. Crop coordinates and hashes are locked in the illustration/source manifests.

## Publication preparation

Operator authorized submission/publication; MA-270 scopes engineering and Git-only release. The portal now registers KR and 한국어 so the target is discoverable after its snapshot merges. Family-manifest fold includes the Korean target as an explicit JE-100C diff. The Git-only release receipt binds check/Markdown/HTML source identity and passes cold IR replay and asset-tamper rejection.
