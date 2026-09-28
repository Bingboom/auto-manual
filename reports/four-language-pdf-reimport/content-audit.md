# Fresh PDF content audit

## Evidence and acceptance boundary

This is a native-text/semantic-flow audit of `uk`, `pt`, `nl`, and `pl`, completed
against the actual-art candidate `/tmp/four-native-complete-4`. Its source
packages are `source/web/{uk,pt,nl,pl}` and its strict-Sphinx output is
`html/{language}/manual_je1000f_eu_{language}.html`. The initial synthetic-art
checks described below were followed by actual HTML, image-slot, provenance,
and native-source checks. Browser evidence is recorded separately by the
parent in `browser-final-verification.json`: candidate 4 Overview passed all
four languages at 390/768/1024/1280 px without callout overlap, clipping or
horizontal overflow; App v5 labels passed in all four desktop languages and
Dutch mobile. Production publication remains a separate gate.

- PDF: `HTE153-nine-language-native-text-check.pdf`, 161 physical pages,
  SHA-256 `39f90f96c5825e835358a82329b8e36a40e6f9b59fccde9bb46f4ba81fe5b469`.
- AI: `HTE153-EU-9国语言-0923.ai`, SHA-256
  `c38415f5c2d96832119105d963737a10901e470f70c5e7518ef6404f83625eb2`.
- The audit re-ran `load_pdf_book` through `PdfBook`, applied the checked
  same-position glyph recovery and explicit downstream corrections, assembled
  neutral IR, and read the public `render_document_fragments` result.
- Source geometry and fresh records were also checked against
  `fresh-source/{uk,pt,nl,pl}.json`. Those stored snapshots retain the original
  LCD word fragments; the current `PdfBook` records exact word-joining repairs
  in its runtime provenance. No OCR or screenshot reading was used.

| Language | Native body pages | Chapters | Positioned fields | LCD rows | Fault rows | Spec groups |
| --- | --- | --- | --- | --- | --- | --- |
| uk | 93–109 | 13 | 209 | 26 | 11 | 4 |
| pt | 110–126 | 13 | 209 | 26 | 11 | 4 |
| nl | 127–143 | 13 | 209 | 26 | 11 | 4 |
| pl | 144–160 | 13 | 209 | 26 | 11 | 4 |

The 26 LCD rows represent indicators 1–25, with two distinct rows for indicator
22. App prose includes download, 2.1–2.5, binding/Wi-Fi/Bluetooth notices,
unbind, and 4.1–4.3. Warranty retains its scope/local-law note, five sections,
and standard/extended 3+2 year cards. Inbox, Overview, five Operations, App,
symbols, specifications and warranty enter registered shared components; the
body has no printed Contents chapter.

## Native text accounting

The first check compared every corrected PDF text block with its chapter's
public-rendered text using NFKC-normalized word/number multisets. A second check
compared complete chapter multisets, which catches repeated labels that a
simple substring search would miss. This is a text-preservation check, not a
proof that captions occupy the correct visual positions.

- Safety, Symbols, UPS, Charging, Storage, Troubleshooting, Specifications and
  Warranty had no unaccounted missing native words/numbers in the initial
  synthetic-art render. Approved Ukrainian source-language correction is
  accounted for independently of exact-string matching.
- Inbox's printed card indices 2/3 are omitted while all three card labels and
  the tip remain live text. They are enumeration marks, not missing products.
- LCD diagram index repetitions differ from the 26-row live legend. Five exact
  print-line-wrap repairs (one Ukrainian, four Dutch) are represented in
  provenance; no unmatched definition body was found.
- App's small duplicate 2.x diagram annotations and two `1000` UI display
  strings are not independent prose fields. The native instructions remain
  live; faithful screen/model artwork still requires actual-art verification.
- The Portuguese LCD-mode `continuame nte` to `continuamente` normalization is
  the existing approved word-wrap correction. Dutch DC→AC label corrections
  and the Ukrainian source-language erratum must be checked using the approved
  corrections, not accepted as unexplained missing words.

### Consumed operation regions: closed in the actual candidate

| Role | Native page (uk/pt/nl/pl) | Consumption rectangle | Accounting |
| --- | --- | --- | --- |
| Main power | 98/115/132/149 | `[140,75,350,190]` | On/off instructions and standby/App supporting copy preserved. Printed `3s` duplicate is an art/step marker, to verify against final art. |
| AC output | 98/115/132/149 | `[25,280,350,380]` | Prerequisite and on/off instructions preserved. |
| DC/USB output | 99/116/133/150 | `[25,50,350,125]` | Prerequisite and on/off instructions preserved; surrounding USB-C cautions remain outside consumption. |
| Energy saving | 100/117/134/151 | `[220,75,345,145]` | **Closed:** native AC/CA/`Змінний струм` and the localized toggle label are visible in the energy-saving component. |
| LED | 100/117/134/151 | `[25,215,345,340]` | **Closed:** native LIGHT label (`СВІТЛО`/`LUZ`/`LAMP`/`ŚWIATŁO`) and the SOS marker are visible in the LED component. |

The energy toggle labels are Ukrainian `Увімкнення/вимкнення`, Portuguese
`Ligar/Desligar`, Dutch `Aan/Uit`, and Polish `Wł./wył.`. A label's occurrence in
some other paragraph does not establish coverage of its diagram location.
All five actual operation components use `base-art-live-copy`, each with one
independent image and native live text. The final candidate check located every
repaired label inside its intended component, not elsewhere in the chapter.
Main-power and energy-saving timing markers display `3s`; the complete native
instructions retain their localized timing wording. LED steps use bulb/SOS
markers in place of the printed diagram's redundant 1/2/3 enumeration.

### Source identity gates

The independent code review reproduced an unapproved erratum replacement:
changing `source/errata.json` previously changed rendered Ukrainian copy while
retaining the unchanged historical source-manifest hash. The intake now checks
every recipe JSON it actually reads against the historical manifest's exact
SHA-256 and byte size, including errata and figure geometry. It does not open
historical artwork. The old-copy poisoning test explicitly re-pins its test
geometry fixture and still verifies that wording comes only from the fresh PDF.

The artwork binding must also carry `text_source: {filename, sha256}` matching
the input PDF before extraction starts. A missing binding, wrong filename, or
wrong digest fails before any candidate is created. The fresh technical version
is propagated into the frozen manifest and must differ from the old source's
version. The 20 intake/Web/document/glyph tests passed after these fixes, and
Ruff passed on the changed implementation and tests.

### Unconsumed charging captions

The complete four-language Charging chapter word/number comparison had no
missing source tokens. The following short captions were explicitly checked;
they must not be swallowed by later reference-image replacement:

| Caption | Native pages (uk/pt/nl/pl) | Current flow |
| --- | --- | --- |
| AC cable connection sentence | 103/120/137/154 | Native text retained after the wall-charging reference event. |
| Emergency charging mode subtitle | 103/120/137/154 | Retained as native text; no bitmap is used as its authority. |
| `SolarSaga 200 × 2` | 103/120/137/154 | Retained as native text (Dutch y≈414; other locales y≈400–406). |
| `SolarSaga 100 Air × 4` | 104/121/138/155 | Retained as native text at y≈165. |
| Car cable sold-separately note | 104/121/138/155 | Retained as native text at y≈365–366. |
| Vehicle label | 104/121/138/155 | Retained: `Автомобіль`, `Veículo`, `Voertuig`, `Pojazd`, y≈401. |

The early car-charging safety bullets on pages 105/122/139/156 remain in the
Charging chapter until the Storage heading. No charging reference currently
declares a text-consumption rectangle.

## Final candidate 4 result

The actual four-language HTML audit found no unaccounted missing or duplicated
native prose or specification values after the approved errata and documented
word-wrap repairs. The source chapter multiset comparison also checked added
tokens, so duplicated paragraphs would fail this accounting. Introduction
matches after its established language-marker/front-matter normalization and
the Ukrainian `support.jack-\nery.com` line-wrap repair. EU-declaration text
matches its native source word/number multiset exactly.
The body retains 13 chapters in order, with no printed Contents chapter.

Remaining text-node differences are explicitly accounted for:

- Inbox indices 1/2/3 are represented by the ordered cards and their
  `data-item-number` values; all labels and the tip remain live.
- LCD's printed 1–25 diagram indices are present in the inspected independent
  LCD image. The live legend has 26 rows because indicator 22 has two entries.
- The App result image visibly retains both `1000` device-model strings.
  Small duplicate 2.x diagram annotations are omitted; every numbered native
  2.1–2.5 instruction remains live once.
- Printed LED enumeration becomes semantic step markers, and `3 s`/`3 с`
  timing marks become `3s` while instructions remain intact.
- Ukrainian/Portuguese superscript specification footnote 1 is separated from
  its preceding word in HTML; its number and word are both retained.
- Dutch `Symbool`/`Betekenis` column headings are repeated for the two separate
  shared symbol tables. No description or instruction is duplicated.

Each language has five independent operation-image slots and six reference
slots (LCD plus UPS/four charging references). Inbox, Overview and App retain
their independent artwork/live-copy slots. All HTML image paths exist and
match the packaged asset bytes. Cold public rendering from each frozen IR has
the same complete text multiset as its corresponding Sphinx HTML. All 175
source-manifest entries pass SHA-256 and byte-size verification, and each
frozen IR's `source_records_sha256` matches its packaged fresh-source JSON.
No host-specific `/Users/` or `/private/tmp/` paths occur in IR metadata.
All 209 positioned-field raw hashes per language (836 total) were re-extracted
from the live PDF and matched. The 17 native page-text records per language
also match live PDF extraction. Each HTML has the expected 26 LCD legend rows
and 11 troubleshooting rows.

The final candidate source tree and the repository copy at
`manual_sources/JE-1000F/EU/nine-language/git-20260928-c38415f5-native-ir/four-language`
have identical file sets and all 176 files match byte-for-byte (175 inventoried
inputs plus the manifest). The complete source chapter word/number deltas are
unchanged from the initially accepted accounting after the Overview and App v5
layout changes. Machine-readable evidence is in `content-audit-final.json`.

Final candidate source-manifest SHA-256:
`3c16f58fa673d90c38355afc49839f5230edacee5538906d5aa640725994e62a`.

| Language | Actual HTML SHA-256 | Frozen IR SHA-256 |
| --- | --- | --- |
| uk | `793d0e90c5461281f57736cb6efbc84722d0ef57d1002f7308b15eab2954bae1` | `8cbfbd5d75b4660eff7fe2cfc6c2db4d5cefdb089934ccf29bd885308525a67d` |
| pt | `31124bec661bf2f58d01c48dc6d93a6243f512f774461d6e06b87a43d8994d5c` | `9af311d1e1b9f182117a3625c9c0d51c26da51493d4d16ee7fb2bc2b550e3307` |
| nl | `630ab453db3f1544372aa5ef0d99b7ba044de6124f2286199db9c74a0437f178` | `d9eed5f37ca3818acf5afbcb2183c501a45299991f362095ef4c80085caba550` |
| pl | `f3ba2c5d6b10dbd94397e989ec4bf9cfaaf53659358cc1490116f2442a41c0de` | `2584ee2f74aced5956b10c433499c7c26eb60217c11dd23096c122ea051dd169` |

Desktop/mobile layout against the English shared structure and final live
publication are separate acceptance steps; this text/structure audit does not
substitute for them.
