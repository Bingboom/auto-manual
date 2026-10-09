# JBP-1000B-SIL / US Git-only Web candidate

The 52-page `Jackery Battery Pack-1.pdf` is authoritative. English uses physical pages 4–19, French 20–35, Spanish 36–51; prefaces use the corresponding language on p2 and contacts use p52. No printed revision is supplied, so `git-20261008-7afcb2a1` identifies this engineering intake rather than inventing an official manual version.

The JBP-2000B shared battery-manual structure governs headings, safety tables, inbox, LCD glossary, callouts, specification tables and warranty. This source adds its own FridgeGuard positioning and vertical/wood/concrete installation content. Each locale has 18 chapters and the same ComponentSpec inventory. English desktop/mobile acceptance was recorded before native French and Spanish production; the final three-language verification is recorded in `source/<locale>/acceptance.json`.

`source/<locale>/content.json` is editable semantic text, including figure captions. `web/<locale>` is the frozen Manual IR/MyST/Sphinx candidate. All three consume the same 53 artwork files. Five native safety glyph variants were added once to the shared symbol catalog; existing warning/WEEE bytes were reused. Independent caption frames remain CSS, diagram labels remain live text, and installation pictures retain full native panel bounds. The small LCD face markings, product logos and document-cover print remain illustrative art. None is substituted with a different model's picture.

## Rebuild and validate

Run from the repository root, using new output directories:

```sh
SOURCE=data/manual_sources/JBP-1000B-SIL/US/git-20261008-7afcb2a1
python3 "$SOURCE/rebuild.py" --language en --output tmp/jbp1000b-en-replay
python3 "$SOURCE/validate_source.py" --language en --output tmp/jbp1000b-en-replay
python3 -m sphinx -q -b html -W --keep-going tmp/jbp1000b-en-replay tmp/jbp1000b-en-site
python3 "$SOURCE/validate_source.py" --language en --output tmp/jbp1000b-en-site
```

Repeat with `fr` and `es`. Replay refuses changed source/input/repository hashes and existing output directories. Validation checks visible native line coverage, ordered FF actions, artwork hashes, withdrawn raster exclusion and byte parity with the frozen package. It permits only the explicit English FCC reading-order repair. This line census complements semantic/visual inspection; it does not independently prove sentence placement or detect outlined text.

The extraction recipe is `data/asset_recipes/manual_jbp1000b_sil_us_native.json`. Replay it with `tools/asset_intake.py`, the original PDF and source key `manual/jbp1000b-sil/us/git-20261008`, to a new scratch output root. Outputs are hash-pinned; no live asset registry promotion is performed. `symbol_asset_admission` binds every native symbol-table row to its caption pixels, original glyph paths, transparency and a named shared variant. The caption-frame admission checks the car note fill; full border/panel inspection remains visual.

`source_manifest.json` pins source inputs, repository contracts and three locale roots for the existing frozen-Web evidence/publishing path. This candidate creates no Base/queue/phase2/HTML_link writes and does not claim a merge or deployment. Publication receipts require the actual committed Git ref at release time.

## Native differences retained

`source/native_exceptions.json` lists the source issues for review. In particular French p33 says **2 months** where English/Spanish say **12 months**. French p27 contains an English preparation heading and Spanish step 4; Spanish p42 step 1 is English. Spanish positioning/connections name FridgeGuard twice, and its interpretation-rights body repeats the original-buyer restriction. These remain native copy, not new translations or corrections.

The native preface uses the shared `hb-preface-heading`, `hb-preface-region` and `hb-preface-prose` presentation classes: US IMPORTANT, FR IMPORTANT and ES IMPORTANTE retain native text, a transparent heading and compact prose. The validator covers all five native preface blocks, including its title/region block, and requires the correct leading heading instead of relying on prose coverage alone.

FCC is bound to the existing HB-SPECIAL-FCC ComponentSpec: native opening/NOTE copy on the left, interference measures/MODIFICATION on the right; mobile follows left then right. Its compact mark-above-copy geometry is source-local CSS. The original transparent FCC SVG is added once to the shared catalog after the existing raster fails the matte check. The validator requires the component, mark, four list measures and two bold native labels.

LCD indicator artwork uses a 4.5rem native-aspect display box with a 14% icon column and reduced horizontal cell padding. This source-local geometry keeps stacked readouts readable in all three locales and preserves internal mobile table scrolling. No artwork is recropped.

The power figure and its existing Note ComponentSpec share a native-power-panel flow group. CSS draws the complete rounded frame and desktop inset Note; On/Off labels and instructions use compact source rectangles. The existing shared stacked mobile-label treatment keeps long instructions readable inside the same outer frame. All artwork bytes remain unchanged.

LCD screen On/Off uses the existing HB-TABLE-LCD-MODE/two-state-three-action component with two merged three-row state cells, grey state/action columns and the shared rounded grid. Source-local portrait geometry stretches the unchanged native illustration to the table height on desktop; mobile stacks it above the internally scrollable table. All native text stays editable.

The vertical-stand opening keeps a native plain heading with its chapter navigation, an editable preparation caption inside the unchanged native prep artwork, and an unframed result picture spanning the left heading/intro/preparation. The existing HB-SPECIAL-REFERENCE-FIGURE base-art-live-copy renderer owns caption placement; source-local geometry stacks the two images on mobile and preserves native aspect ratios.

Vertical-stand steps 1–3 each occupy a full-width row in EN/FR/ES, preserving editable native words and original artwork dimensions/aspect ratios. Desktop/mobile browser acceptance confirms three equal-width stacked cards with no page overflow.

Wall-mount headings use the native plain treatment; the title/introduction and introduction/subheading gaps are compact (about 6px and 10px). EN/FR/ES desktop/mobile validation retains chapter navigation and confirms wrapped headings without horizontal overflow.
