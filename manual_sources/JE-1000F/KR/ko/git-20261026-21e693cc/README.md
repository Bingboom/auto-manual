# JE-1000F KR Korean Web candidate

Source: `source/original.pdf`, the unmodified 21-page KR manual print file
`16-0102-000362 说明书 HTE1531000A-KR-JAK RoHS REACH q.pdf` (SHA-256 in
`source_manifest.json`), downloaded from the Feishu wiki file node supplied by
the operator. This is a Git-only Web **candidate** for operator review: no
merge, publication or online-table write is implied.

The Web body covers PDF pages 3–19 (17 manual pages, printed 01–17). Page 1 is
the factory drawing sheet and page 20 a blank padding page. The cover (page 2)
and the QR-only back cover (page 21) are excluded by the operator's decision in
the workbench session (2026-10-26, “封面和封底都不收”). All excluded pages stay
in the PDF. The existing
JE-1000F KR print/Word line (`configs/config.kr.yaml`, `manual_kr.yaml`) is not
touched; this package is a prepared-document source like the JE-3000C KR
package.

The PDF has no text layer. Korean text was transcribed from 4× page renders and
checked line by line; Tesseract `kor+eng` output is retained under `ocr/` as
evidence only (98.75% of its Hangul tokens occur in the transcription; every
miss is an OCR misread, see `validation/content-audit.json`). Source wording is
kept verbatim, including suspected source errors; those are listed in
`source_manifest.json` under `suspected_source_errors_pending_operator` and are
not corrected.

## Replay

From the repository root, using the project Python environment:

```sh
python manual_sources/JE-1000F/KR/ko/git-20261026-21e693cc/rebuild.py --output /tmp/je1000f-kr-ko-source
python -m sphinx -W --keep-going -D language=ko -b html /tmp/je1000f-kr-ko-source /tmp/je1000f-kr-ko-html
python -m http.server 18854 --bind 127.0.0.1 --directory /tmp/je1000f-kr-ko-html
```

Preview: `http://127.0.0.1:18854/manual_je1000f_kr_ko.html`. Both output
directories must be new. The assembler verifies frozen inputs and shared-code
pins before writing, runs the prepared-document shared-style audit and replays
the package. `web/ko` holds the serialized IR, Markdown, shared CSS/scaffold
and local assets.

## Artwork

`source/asset_inventory.json` records the JE-1000F JP/EU and JE-3000C KR
candidates inspected first; `source/asset_decisions.json` records each reuse or
crop with hashes and PDF-point clip rectangles. 38 files are reused
byte-for-byte (EU solar panels, JE-3000C store badges and 2.1/2.2 phones, JP
document icon and LCD icons, seven shared symbols); 17 panels with Korean
labels or KR-only screenshots are new crops that keep their complete rounded
frames, grey backgrounds and leader lines. Seven symbol rows are bound to the
p4 glyph drawings and caption pixels in `symbol_asset_admission`.

## Printed block → shared component

| Printed block (PDF page) | Shared component / flow |
| --- | --- |
| Preface, safety, maintenance, storage, UPS and charging prose (3, 12–15) | headings, paragraphs, lists |
| 경고 / 주의 / 참고 strips (3, 8–15, 19) | `HB-CALLOUT-STRIP` warning / caution / note |
| Signal labels and pictogram symbols (4) | `HB-TABLE-SYMBOL-SIGNAL`, `HB-TABLE-SYMBOL-ICON` with source-bound shared symbols |
| 패키지 목록 cards and tip (4) | `HB-SPECIAL-INBOX` three-card |
| Front / right overview (5) | `HB-SPECIAL-REFERENCE-FIGURE` approved source crops |
| LCD map and 25-number table (6–7) | reference figure + `HB-TABLE-LCD-ICON` |
| Operation, energy-saving, LED, UPS, charging panels (8–14) | `HB-SPECIAL-REFERENCE-FIGURE` complete panels |
| LCD 화면 table (11) | `HB-TABLE-LCD-MODE` two-state/three-action with device artwork |
| 키 조합 table (11) | `HB-TABLE-KEY-COMBINATIONS` three-column (button pictograms as names) |
| 문제 해결 table (15) | `HB-TABLE-TROUBLESHOOTING` |
| 사양 tables (16) | four `HB-TABLE-SPEC` groups |
| 보증 lead, cards and year badges (17) | `HB-WARRANTY-LEAD`, `HB-WARRANTY-SECTION`, `HB-WARRANTY-YEARS` |
| App download, + control, phones, button map (18–19) | `HB-SPECIAL-APP` download / inline-control, reference figures with live step captions |

No block needed a declared plain-table exception; `shared_component_exceptions` is empty.
