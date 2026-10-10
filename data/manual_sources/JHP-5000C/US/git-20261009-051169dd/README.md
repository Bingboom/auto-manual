# JHP-5000C / US Git-only Web candidate

The authoritative source is the 76-page `Jackery HomePower 5000 Plus.pdf`, SHA-256 `051169dd15831f5670ada665146c3499e71e415c092a379fd782578bb517c26a`. English uses physical pages 4–27, French 28–51 and Spanish 52–75. Each locale uses its native preface on p2 and shared contacts on p76. The native translations are retained. `git-20261009-051169dd` is the engineering snapshot identity; no paper revision is claimed.

The candidate retains 23 chapters, including the AC ESS installation guide, HomePower host, JBP-5000A battery pack, JA-TS02A Smart Transfer Switch, their specification tables and all three packaging groups. Product facts remain bound to the source: 5040 Wh, 7200 W maximum / 14400 W surge, 120 V / 240 V split phase, up to five battery packs, and five standard warranty years plus two paid extension years. No phase2 or print target is enrolled.

The established power-station Web structure and shared components own headings, signal/symbol and LCD tables, FCC, inbox, notices, combinations, specifications, warranty and App download. `source/presentation.css` owns only native diagram geometry. Complete native figure groups retain device surfaces, leaders, zoom circles and phone frames. Exterior captions are editable HTML. Each filled caption frame groups every native line into one live block across PDF text blocks; `source/caption_frames.json` binds its locale page, drawing and rectangle. Independent caption plates, tails and operating outlines are removed from the base art and drawn with CSS. Dense figures preserve their arrangement on a contained scrolling surface on narrow screens.

All three locales reuse one device/connection artwork set, safety icons, native LCD variants and buttons. The FR/ES power panels reuse the English SVG unchanged except for translating its two existing clock paths to native duration anchors; `source/relocate_duration.py` and `duration_provenance.json` record the derivation without recropping. The FR/ES car panels retain their native device/vehicle placement and native panel height; the white footnote capsule is removed from every base image and drawn by CSS. The four FR/ES App add/result panels preserve native localized UI differences; an English screenshot is not substituted for a translated source screen. Five safety symbols copy checked shared variants unchanged. Two reuse existing glyph paths with the native dark-gray tint, and the native explosion variant is acquired once after the previous shape still fails the fixed glyph comparison. These three variants are available in the shared static catalog as local candidates. Their old variants remain valid for their own source; rejected hashes cannot satisfy this candidate. No live asset-registry promotion occurs.

The 26 LCD rows use their source-specific outlines, stroke thickness, native tint and fixed markings. A review of 59 unique transparent existing candidates rejected the prior semantic-only substitutions. `source/lcd_provenance.json` records the source rectangles, drawing indices, closest candidate and comparison error. Native LCD glyphs are extracted once and reused by all three locales. The source gate and `validate_lcd.py` reject obsolete hashes and independently reconstruct every glyph in Chromium, where the original SVG clipping is supported. Names precede their regular-weight explanatory notes in source reading order.

`source/asset_decisions.json` records searches, reuse decisions, source differences and hashes before extraction. `data/asset_recipes/manual_jhp5000c_us_native.json` runs through the shared asset pipeline. `source/restore_markings.py` retains exact outlined physical printing on the small inbox book; exterior card labels remain live. `source/physical_markings.json` binds its raw/final hashes. SVG export preserves original fill/stroke paths, transforms, clipping and embedded image references, including the solar-cell mesh.

`source/<language>/content.json` is editable semantic copy with ComponentSpecs and rich carriers. `coverage.json` records complete native words, PDF rectangles, source page numbers and copy roles. `source/intake.py` regenerates these files. `source/refresh_manifest.py` rebinds reviewed source inputs and source-bound symbol references; rerun it only after reviewing edits. `web/<language>` is the frozen Manual IR/MyST/Sphinx package.

## Rebuild and validation

Run from the repository root, using unused output/evidence directories:

```sh
JHP_SOURCE=data/manual_sources/JHP-5000C/US/git-20261009-051169dd
PYTHONDONTWRITEBYTECODE=1 python3 "$JHP_SOURCE/rebuild.py" --language en --output tmp/jhp5000c-replay/en
python3 -m sphinx -n -W --keep-going -b html tmp/jhp5000c-replay/en tmp/jhp5000c-site/en
python3 "$JHP_SOURCE/validate_source.py" --language en --output tmp/jhp5000c-site/en
PYTHONDONTWRITEBYTECODE=1 python3 "$JHP_SOURCE/validate_lcd.py" --output tmp/jhp5000c-site/en --evidence-dir tmp/jhp5000c-lcd
```

Repeat for `fr` and `es`. Replay refuses changed authoritative PDF, semantic copy, artwork, source/shared styles and repository dependencies. The source gate checks visible native lines, 26 LCD entries, twelve specification grids with ordered fields/values, 27 source figure groups, every live caption, App add-button recovery, native language badges, consumed asset hashes and chapter/navigation IDs. Hidden or ARIA-only text cannot satisfy visible-copy coverage.

```sh
python3 -m http.server 8898 --bind 127.0.0.1 --directory tmp/jhp5000c-site
python3 "$JHP_SOURCE/validate_layout.py" --base-url http://127.0.0.1:8898 --evidence-dir tmp/jhp5000c-browser
PYTHONDONTWRITEBYTECODE=1 python3 "$JHP_SOURCE/validate_replay.py" --evidence-dir tmp/jhp5000c-cold-replay
```

The browser gate uses 1280×900, 768×1024 and 390×844, waits for fonts and actual image readiness, checks page overflow, text ink bounds, label overlaps, opaque caption plates covering other live ink, inbox clipping and JavaScript errors, and captures sections/figures for source comparison. Final visual acceptance is recorded in each locale's `acceptance.json`. Cold replay compares every frozen file and rejects mutations in five input classes using disposable copies.

The fixture-backed `build.py check --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2 --staging-root <scratch>` is a shared-family regression. It does not certify this native target; the source, symbol, strict Sphinx, browser and replay gates do.

## Native differences retained

`source/native_exceptions.json` records native spelling and cross-language residue: `Onine UPS`, Explorer naming in the AC ESS text, French danger/control/availability wording in Spanish and Portuguese LCD terms. These are source-content questions, not silently corrected translations.

## Git-only boundary

This candidate performs no live Base, build-queue, source-table, asset-registry or HTML_link writes. No merge or online release is authorized by this conversion request. Publication requires a separate target-specific authorization and the shared frozen-Web sealing/release path; authorization for JHP-3000D does not cover JHP-5000C.
