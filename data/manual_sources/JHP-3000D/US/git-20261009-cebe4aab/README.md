# JHP-3000D / US Git-only Web candidate

The authoritative source is the 58-page `Jackery HomePower 3000 User Manual.pdf`, SHA-256 `cebe4aab0a65d5fb2c36bb1867cdb6497e2a6db5251c46c61a33a530b862cf27`. English uses physical pages 4–21, French 22–39, Spanish 40–57; each uses its own preface on p2 and contacts on p58. No printed revision is available. `git-20261009-cebe4aab` identifies this engineering snapshot, not an official paper-manual version. French and Spanish are native source copy, not newly translated text.

JE-2000E supplies the shared power-station structure and components for headings, safety symbols, FCC, inbox, LCD tables, callouts, specification tables, warranty and App download. All 16 native chapters are retained. JHP-3000D product facts and US hardware remain bound to this PDF: 3072 Wh, TT-30R and four 20A sockets, native controls, source LCD numbering and charging illustrations.

`source/<language>/content.json` holds editable semantic copy and rich live figure captions. `source/intake.py` and `source/native.py` regenerate these documents from recorded native word selections; rerunning intake replaces the semantic documents. `source/<language>/coverage.json` records source pages, rectangles, native word IDs and copy roles. `web/<language>` is the frozen Manual IR/MyST/Sphinx package. Source edits must keep the ComponentSpec slots and rich carriers consistent before explicit manifest refresh and rebuild.

The three languages reuse one active art set. Existing LCD icons, buttons, cable/document artwork, FCC mark and complete App phone frames are copied byte-identically with provenance in `source/asset_decisions.json`. Six safety glyphs reuse the shared catalog. One person-circle reading glyph is acquired once after all existing variants fail the fixed native glyph/tint/alpha comparison, then shared across all three languages. Standalone symbols have true transparency. Other model/region illustrations are not substituted for JHP-3000D hardware.

Thirteen native panels retain complete source geometry, shading, leaders and device markings. External wording is live HTML. Independent caption capsules, the speech-bubble tail and outer operating frames are removed from base art and rebuilt with CSS. Phone edges and embedded screenshot counters remain complete. Dense diagrams preserve source grouping at readable scale on a contained horizontal scroll surface on small screens; the page itself does not overflow. Images keep their native aspect ratio. `source/presentation.css` owns only source geometry; shared styles own headings, tables, callouts, warranty and responsive components.

## Rebuild and validate

Run from the repository root with unused output directories:

```sh
SOURCE=data/manual_sources/JHP-3000D/US/git-20261009-cebe4aab
PYTHONDONTWRITEBYTECODE=1 python3 "$SOURCE/rebuild.py" --language en --output tmp/jhp3000d-en-replay
python3 -m sphinx -n -W --keep-going -b html tmp/jhp3000d-en-replay tmp/jhp3000d-site/en
python3 "$SOURCE/validate_source.py" --language en --output tmp/jhp3000d-site/en
```

Repeat for `fr` and `es`. Replay refuses changed source/repository hashes and existing output directories. Validation checks final visible native lines, complete ordered App steps 2.1–2.5, the editable native add-button plus glyph, native language badges, 26 LCD entries, four specification grids (7/2/7/2 rows), 13 ReferenceFigure components, 61 live labels, exact image hashes and rejection of withdrawn source-specific assets. The line census complements visual/source reading-order review; hidden/ARIA copy cannot satisfy it.

Serve the three HTML directories and run the browser gate (requires Playwright Chromium):

```sh
python3 -m http.server 8895 --directory tmp/jhp3000d-site
python3 "$SOURCE/validate_layout.py" --base-url http://127.0.0.1:8895 --evidence-dir tmp/jhp3000d-browser-evidence
```

The gate checks 1280×900, 768×1024 and 390×844, loaded images, actual text ink inside figure panels, inter-label overlaps, inbox-card clipping and JavaScript errors. It captures source sections and native figures for visual review. Formal final acceptance is recorded in `source/<language>/acceptance.json`. Cold replay must match every frozen package file; source, art and stylesheet tampering must fail.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 "$SOURCE/validate_replay.py" --evidence-dir tmp/jhp3000d-cold-replay
```

This starts a fresh Python process per locale and checks every output byte. Hash-rejection cases mutate only disposable source/repository copies, covering native copy, art, source CSS, shared CSS and the shared theme.

The shared asset pipeline recipe is `data/asset_recipes/manual_jhp3000d_us_native.json`; use `tools/asset_intake.py` with source key `source/manual_jhp3000d_us_native` and the original PDF, writing to an unused scratch root. Pipeline PDFs and PNG previews are under `source/art` and `source/previews`; `source/svg_derivations.json` binds the active SVGs to those text-free PDFs. Bare-art and all four edge comparisons use Chromium SVG against native PDF rendering at 12×. MuPDF's SVG reader misrenders the nested transformed zoom-circle clips in the AC/solar/car SVGs; native PDF/PNG and Chromium agree. Do not replace verified art based on that SVG-reader preview.

## Native differences retained

`source/native_exceptions.json` records the original language differences, including English TOU/Discharge Timer in FR/ES, French energy labels in English, French/Spanish specification wording and USB-label differences, a French first-charge sentence in ES, the Spanish warranty unit `ÑOS`, locale-specific App instructions and the missing ES UPS-body 10ms sentence. `Double to 8A Max` remains the native low-voltage DC input value. No presumed spelling, translation or technical corrections are added.

`source/visual_text_recovery.json` documents outlined EN/FR/ES preface badges and the inline circular App plus glyph. App paragraphs follow native step order; note introductions precede their bullets. The extraction-object order is not the reading order.

## Git-only boundary

`source_manifest.json` pins every source input, shared dependency and designated locale root for the existing frozen-Web evidence path. This native target is not enrolled in phase2 or print. The fixture-backed JE-1000F US `build.py check` is a shared-family repository regression only; source-specific body/figure/table, strict Sphinx, admission and browser checks validate this target.

No online Base, queue, asset registry or HTML_link writes are performed. No merge or deployment is claimed. Release receipts must use the actual committed source Git ref and the shared `seal_frozen_web_evidence` API; publication remains a separate authorized transaction.
