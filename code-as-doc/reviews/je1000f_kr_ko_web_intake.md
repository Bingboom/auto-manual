# JE-1000F KR Korean Git-only Web intake

Status: active

Candidate Web source for operator review, requested 2026-10-26 through the
workbench session. The supplied KR print PDF (document control number
16-0102-000362, project HTE153 / HTE1531000A-KR-JAK, issue V0.1) is the sole
content authority. No live-table reads or writes, queue rows, merge or
publication. Package:
[`manual_sources/JE-1000F/KR/ko/git-20261026-21e693cc`](../../manual_sources/JE-1000F/KR/ko/git-20261026-21e693cc/README.md).

## Route

The existing JE-1000F KR data-driven print/Word line keeps its manifest. A
JE-100C-style `page_manifests` override would also swap that line's print and
Word manifest, so this target follows the JE-3000C KR prepared-document
package instead: frozen `source/document.json`, shared components only,
`rebuild.py` replay, registered in `data/frozen_package_registry.json`. No
config, phase2, template or CI target change.

## Pages

| PDF page | Content | Web |
| --- | --- | --- |
| 1 | Factory drawing sheet (V0.1, 130×185mm, 2026-7-21) | excluded |
| 2 | Cover: title, model, 국내전용, customer email, greeting | excluded (JE-3000C KR precedent); operator to confirm |
| 3–19 | Printed pages 01–17 | included, 15 Web sections |
| 20 | Blank | excluded |
| 21 | QR-only back cover | excluded |

## OCR and transcription

The PDF is fully outlined. Text was transcribed from 4× renders and re-read
against 4× crops page by page. Tesseract 5.3.4 `kor+eng` output is kept under
the package `ocr/` as independent evidence: 1,742 of its 1,764 Hangul tokens
(98.75%) occur in the transcription, and all 22 misses are OCR misreads
(노줄은→노출은, 리틈→리튬, 중전→충전, …). Source wording, spacing and suspected
errors are kept verbatim.

## Asset selection before extraction

| Slot | Candidates inspected | Decision |
| --- | --- | --- |
| Inbox unit / cable | JE-1000F JP (three Type-A outlets, JP plug) | New KR crops |
| Inbox document | JP `inbox-documents.svg` | Reuse byte-for-byte |
| Overview front / right | EU composites (English labels), JP (Japanese, JP unit) | New crops with Korean labels, complete panels |
| LCD map | JP `pdf-lcd-overview.svg`, EU V2.0 `lcd_map.png` (both differ in frame and leader layout) | New crop; table native |
| LCD icons | JP shared LCD icons; JE-3000C KR row 11 | Reuse 25 JP icons; row 11 uses the JE-3000C KR “8.8 H” icon (JP file shows “88H”) |
| Symbols | Shared symbol catalog | Reuse seven variants; source-bound admission against p4 |
| Operation, energy-saving, LED, UPS, AC wall, car panels | EU composites (English text) | New crops keeping rounded frames, grey fill and leader lines |
| Solar direct / adapter | EU V2.0 composites (product labels only) | Reuse byte-for-byte |
| App badges, 2.1/2.2 phones | JE-3000C KR | Reuse byte-for-byte |
| App QR, button map, 2.3–2.5 phones | JE-3000C KR (different QR, device “3000”), EU (“1000”) | New crops (KR prints “1500 Ultra” screens) |

Totals: 38 reused files, 17 new crops. Hashes and clip rectangles are in the
package `source/asset_decisions.json`.

## Suspected source errors (kept verbatim, operator to decide)

- p6 LCD ⑥ TOU: `끄기:` where every other row uses the state word `꺼짐:`.
- p7 LCD ㉒ low temperature: `작동됩습니다` (typo for `작동됩니다`).
- p7 LCD ⑮⑯⑱⑳㉑: status prefixes not bold in print; the Web bolds all
  prefixes per the corpus status-word contract (formatting only).
- p8/p9/p12 prerequisite pills use 전제 조건 / 사전 조건 / 필수 조건; p8 power
  panel says 꺼짐 where AC/DC panels say 끄기 (inside artwork).
- p11 LCD 화면: `잠시 켜기` vs `상시 켜짐(…)`; the second auto-off cell repeats
  `화면이 자동으로 꺼집니다.`
- p13 비상 충전 모드: stray `*` after `깜박입니다.`
- p15 F7 step 2: `태양열 패널` (solar thermal) and `작동 전압`, while p14 asks
  for the panel's 개방 회로 전압(Voc); F8 `Jackery고객 지원` lacks a space.
- p16 cycle life `6000회` differs from the EU V2.0 edition (4,000 cycles).
- p19 App screenshots show a “1500 Ultra” device.
- Sentence-final periods are not followed by a space throughout (typesetting).

## Reference edition

The review compares the KR candidate with the JE-1000F EU English Web
edition, built locally from its frozen source
(`manual_sources/JE-1000F/EU/en-fr/2.0`, `build.py md --config
configs/config.eu-en.yaml --source review-asis`), because the production site
requires sign-in.

## Local verification

- Package replay: frozen inputs and shared pins verified, shared-style
  admission passes with no declared exceptions; cold replay reproduces the
  same Markdown and IR; a corrupted panel is rejected.
- Symbol admission: seven rows bound to p4 glyph drawings and caption pixels,
  maximum mean channel error 0.019.
- Strict Sphinx `-W -D language=ko` build passes.
- Browser at 1280px and 390px: all 70 images load, no page-level horizontal
  overflow; the LCD table scrolls inside its shared container as in JE-3000C KR.
- Repository checks are listed in the PR.
