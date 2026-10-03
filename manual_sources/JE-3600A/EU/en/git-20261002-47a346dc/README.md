# JE-3600A / EU / English — Git-only Web candidate

This candidate transcribes `HTE139-EU-9国说明书-0924.ai` into the existing
`manual-ir/v2 → ComponentSpec → shared Web renderer` pipeline. It is an
engineering review candidate, with `publication_eligible: false`.

- Product: Jackery Explorer 3600 Plus, JE-3600A, EU, English.
- Source: 161 physical pages; English preface p2, body p8–24, shared regulatory
  content p161. SHA-256:
  `47a346dcfec4966ac98fbe1426e4f2b89cf54a964e4d1baf2ad9c7b02dc78043`.
- No live Bitable/queue dependency, source-table writes, merge or publication.
- The historical `../2026-05-25` package and existing model configuration stay
  unchanged. This directory is the new version's reviewable Git artifact.

## Contents and replay

- `source/text-ledger.json`: native rectangles/raw text and explicit visual
  transcription of outlined copy.
- `source/native-pages.json`: native text and block coordinates for source review.
- `source/chapters.json`: 16 prepared chapters, with neutral flow and registered
  component bindings. `source/normalization-notes.json` explains reading-order
  recovery and layout-only labels.
- `asset_recipe.json`, `assets_manifest.json`: source hashes, crops, exact shared
  asset reuse and redaction decisions. The small ×5 LCD icon has its own
  retained-path recipe and transparent export; the CE/contact QR export settings
  are in the manifest. Frames, device shading, engravings, phone UI and leaders
  are preserved. External native text becomes live copy; five explanatory gray
  boxes in four operation panels are removed at the operator's request. The two
  standalone clocks are removed from the art and drawn with CSS beside the live
  long-press instructions.
- `web/en/manual.ir.json`: frozen public IR, shared component registry/theme,
  target artwork geometry and shared stylesheet hashes.
- `web/en/manual_je3600a_eu_en.md`: deterministic shared-renderer output.
- `source/validation.json` and `source/browser-audit.json`: verification receipts.

From the repository root, replay from Git inputs only:

```sh
python3 - <<'PY'
from pathlib import Path
from tools.frozen_ai_web import replay_package
replay_package(Path('manual_sources/JE-3600A/EU/en/git-20261002-47a346dc/web/en'))
PY
python3 -m sphinx -W --keep-going -b html \
  manual_sources/JE-3600A/EU/en/git-20261002-47a346dc/web/en \
  reports/je3600a-native/preview
python3 -m http.server 18963 --bind 127.0.0.1 \
  --directory reports/je3600a-native/preview
```

Open `http://127.0.0.1:18963/manual_je3600a_eu_en.html`. Replay needs neither the
original AI file nor live business data. Source re-extraction requires the exact
AI file and its pinned SHA-256.

## Reuse and source differences

| Area | Shared structure reused | JE-3600A source binding |
| --- | --- | --- |
| Inbox, symbols, LCD | Existing semantic tables/cards/icons | 23 LCD rows; numbers 4 and 18 each span two rows; ×5 battery indicator |
| Operations | Shared Operation, reference figure, LCD mode and key-combination components | USB/AC prerequisites are native paragraphs above the artwork; main-power/energy panels retain live reference labels and CSS clocks. Explanatory gray boxes and baked clock glyphs are removed; devices, button circles and frames remain intact |
| Connections/charging | Shared base-art reference figure | Five battery packs maximum, 200 mm ventilation, EU sockets and this source's cable topology |
| Specifications | Shared spec tables | 3584 Wh; 3600 W rated / 7200 W surge; 100 A expansion input and 60 A output |
| Warranty/App | Shared warranty and App components | 3+2 years; source phone UI and live captions; positioned selectable control labels |
| Regulatory back | Shared reference figure and native text | Shenzhen Hello Tech manufacturer/address, original CE/contact QR |

The opening chapter is `IMPORTANT`; the product name remains in site metadata
and navigation. All eight Symbols pictograms reuse existing clean shared artwork
byte-for-byte, with source paths and hashes in `assets_manifest.json`. The first
six use the shared phase2 Symbols attachments frozen with JE-2000F/EU; battery
separate collection uses common `symbols/weee2.png` (no bottom bar), and product
WEEE uses common `symbols/weee.png` (with bottom bar). All eight have transparent
backgrounds; the older JE-3600A snapshot's cell-background crops are not selected.

JE-2000E supplied the shared chapter/component pattern, not product facts.
No automatic-output-restore table appears in this English source and none was
invented. This is a prepared-document intake because some source copy is outlined
and was visually transcribed; it does not claim native publication admission.

## Review evidence

The candidate passed strict IR validation, deterministic Markdown replay, all
packaged asset hashes, strict Sphinx, 113 targeted shared-component/presentation tests, and the
repository maintainability guardrails. Browser checks cover 1440×1000 and
390×844, 56 loaded image elements, 23 LCD rows, correct rowspans, zero missing
images, page errors or document overflow. Wide semantic tables remain horizontally
scrollable on mobile; reaching their last columns was checked. Mobile long figure
labels follow the shared renderer's readable stacked treatment.

All 15 newly cropped/redacted panels match the source outside removed native text
and explicitly approved background-removal regions at 4×. Their four edges are
byte-identical to the source at 12×. Detailed receipts are in
`source/artwork-pixel-audit.json` and `source/artwork-edge-audit.json`.
`source/artwork-background-removal-audit.json` separately verifies the five gray
boxes and two standalone clocks removed from power, USB, AC and energy-saving
artwork: no pixels changed outside the scoped rectangles, no dark device strokes
changed outside the approved clock regions, and the removal
interiors are pure white at 12×. The existing recipe's `whiteout` operator covers
whole identified boxes surrounded by white canvas; it does not select by color
or reconstruct the device. Source drawing indices and geometry are recorded in
`assets_manifest.json`. Older same-model assets contain the same boxes and are
therefore unsuitable for unchanged reuse.
Local complete chapter screenshots are retained in
`reports/je3600a-native/browser-final-{1440,390}`; their digests are in the browser
receipt. Local Python versions differ from `requirements.lock`; no dependencies
were changed. No production Python logic or build commands change. The shared App heading
CSS preserves source case and removes inherited heading padding; this candidate
freezes the regenerated stylesheet. Full logic/build-behavior suites are not
applicable to these source and stylesheet changes.

The introduction and Symbols correction was rechecked in the in-app browser at
both sizes. `source/browser-audit.json` retains the initial full-manual audit and
adds the correction checks and screenshot digests under `review_correction`.
Current correction screenshots are `reports/je3600a-native/review-*.png`.

The gray-box correction is checked separately under `operation_background_review`
in the browser receipt at both sizes. USB and AC prerequisite text remains
selectable above the figures without a capsule overlay. The four operation
panels, IMPORTANT heading and shared Symbols were rechecked; local screenshots
are `reports/je3600a-native/operation-background-*.png`.
The two decorative clocks use CSS circles and border-drawn hands inside the
shared reference figure's existing rich captions. They follow the long-press
copy on desktop and mobile, are hidden from assistive technology, and require
no image asset, SVG, JavaScript or target stylesheet.

The source-style correction is recorded under `style_restoration_review` at both
sizes. All 16 chapters are peer H1 sections using the shared dark title band;
subsections use H2, keeping the App numbering exception inside the App chapter.
Three rich H2 headings retain their stable anchors and use selectable
`SOLD SEPARATELY` badges. The first-charge reminder uses a matching capsule,
`Green energy first:` is bold, and the storage prose/list share one rounded
light-gray panel. These source decorations use existing neutral-flow HTML
presentation hints and shared color tokens; no renderer or stylesheet is forked.
The three editorial parentheses around `SOLD SEPARATELY` are removed to match
the native standalone badges. All words, technical values, chapter order,
native text ledger and artwork remain unchanged. Local screenshots are
`reports/je3600a-native/style-*.png`.

The final Specifications/Warranty/App check is recorded under
`spec_warranty_app_review`. The three chapter bands and six dark warranty labels
were rechecked at both widths. All seven App numbered headings align their text
with the chapter's left edge; the shared rule removes inherited H3 padding and
preserves source case. Step 2.2 retains native bold `POWER` and `Icon Flashed`.
The store badges and QR code load within their columns and stay centered above
their copy. No assets or wording change. Local screenshots are
`reports/je3600a-native/final-sections-*.png`.

Main-power On/Off correction is recorded under `main_power_alignment_review`.
Both titles and their separate instruction lines reuse the shared Operation text
classes, matching USB typography. The title centers bind to the native p13
bracket arms at y=93.5104 and 119.0554 pt, with one common left edge at x=263 pt.
The CSS clock follows the long-press instruction, so it cannot indent the Off
title. At mobile width the same text classes remain readable below the artwork.
Only the two editorial On/Off colons become block boundaries; all words, source
facts, the native text ledger and all artwork stay unchanged. Local screenshots
are `reports/je3600a-native/power-alignment-{1440,390}.png`.

## Source errata awaiting product review

1. P2 English preface/TOC carries “US” although this source and target are EU.
   The source banner is recorded, and this candidate retains the EU identity.
2. P14 energy-saving paragraph says “AC or DC output” although the operation
   chapter describes USB output. Native wording is preserved.
3. P20 FA remedy refers to “both units” without a corresponding two-unit
   connection procedure in the English source. Native wording is preserved.

These are review notes, not silently approved source corrections. Publication,
other languages and default-target replacement require a subsequent decision.
