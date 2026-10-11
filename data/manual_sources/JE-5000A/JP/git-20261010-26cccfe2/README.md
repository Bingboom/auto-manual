# JE-5000A / JP / ja Git-only Web candidate

The authoritative file is the 24-page Japanese `Jackery ポータブル電源 5000 Plus 取扱説明書.pdf`, SHA-256 `26cccfe203b43a346743a0db7bf1757bb8f9c1e10aa716fe5aa5dbe1b58a48f8`. The cover identifies JE-5000A. Body physical pages 3–23 correspond to printed pages 01–21; cover p1, printed contents p2 and back cover p24 remain archived in the original PDF. The printed version is unknown. The engineering snapshot name does not assert a paper revision.

The fourteen native chapters retain their source order: specifications, inbox, product overview, LCD, operation, troubleshooting, UPS, battery-pack connection, charging, safety, precautions, disclaimer, App and warranty. Native Japanese copy is retained, including source questions such as the reference to `2000` in the handle precaution and repeated `℃` in the operating-temperature text. JP 100V/200V hardware and Japanese App screens are not replaced with US artwork.

`source/native_pages.json` retains positioned text and stable native line IDs. `source/ja/coverage.json` classifies all 789 body lines without overlap or omissions, including the fixed product/UI markings and excluded printed folios. Its 481 live selections are checked in actual rendered text; PDF classification alone is not visual acceptance. The inline App add-device plus is reconstructed as HTML/CSS and its source drawing IDs are recorded. Exterior figure labels, specification/LCD/combination/fault tables, notices, safety text and warranty copy are selectable HTML.

## Artwork and presentation

The shared Manual IR, component registry, Web theme and existing host structure own headings, inbox, LCD catalogue, key combinations, reference/specification tables and notices. There is no new model config or renderer. `source/presentation.css` contains native figure geometry and source table proportions only. Full diagrams stay grouped. Dense diagrams and the LCD image/table pair preserve their source relationship on a contained horizontal scrolling surface on narrow screens.

`source/asset_decisions.json` records the asset search, exact variant check, reuse/extraction reason, source path and hash. Twenty-three LCD indicators reuse the reviewed JHP-5000C transparent SVGs unchanged; the Japanese self-generation indicator differs and is acquired from this source. Japanese safety symbols and compatible buttons reuse the shared transparent variants. The native grounding/DC marking, region-specific hardware, connection panels, book and App screenshots are acquired once. Frozen copies remain byte-identical with their recorded shared sources.

`source/figures.json` and `asset_recipe.json` bind exact page rectangles and vector drawing indices. Crops retain device contours, complete phone edges, leaders, cables and magnification circles. Adjacent heading bullets and neighboring panels are excluded by object role. Independent caption shapes are absent from the base artwork and restored by CSS, including the power-panel speech-bubble tail. Product/button printing and App screen UI remain fixed source artwork; `SolarSaga 200 × 6` is an exterior live label. New extracts remain quarantined: there is no asset-registry promotion or online enrollment.

## Replay and validation

Run from the repository root with unused output directories:

```sh
JE_SOURCE=data/manual_sources/JE-5000A/JP/git-20261010-26cccfe2
PYTHONDONTWRITEBYTECODE=1 python3 "$JE_SOURCE/rebuild.py" --output tmp/je5000a-replay/ja
python3 -m sphinx -n -W --keep-going -b html tmp/je5000a-replay/ja tmp/je5000a-site/ja
python3 "$JE_SOURCE/validate_source.py" --output tmp/je5000a-site/ja
python3 -m http.server 8927 --bind 127.0.0.1 --directory tmp/je5000a-site
python3 "$JE_SOURCE/validate_layout.py" --base-url http://127.0.0.1:8927 --evidence-dir tmp/je5000a-browser
PYTHONDONTWRITEBYTECODE=1 python3 "$JE_SOURCE/validate_replay.py" --evidence-dir tmp/je5000a-cold
```

`source/ja/content.json` is the editable semantic source; `web/ja` is the frozen MyST/Manual IR/Sphinx bundle. Source and shared dependency hashes are pinned in `source_manifest.json`. After reviewed source edits, regenerate the frozen bundle in a scratch directory, replace this candidate's `web/ja`, then run `refresh_manifest.py`. Never silently update a historical snapshot or refresh hashes to bypass a failed check.

The browser gate checks 1280×900, 768×1024 and 390×844: actual image/font readiness and nonblank artwork, page overflow, caption ink bounds, overlaps/occlusion, local table and ancestor clipping, duplicate IDs, visible native text, inbox labels and resource/script errors. Figure and chapter screenshots are used for source comparison. `source/ja/acceptance.json` records local visual acceptance. Cold replay compares every frozen file and rejects source, artwork and stylesheet/theme mutations on disposable copies.

The fixture-backed `python3 build.py check --config configs/config.ja.yaml --model JE-1000F --region JP --data-root tests/fixtures/phase2 --staging-root tmp/je5000a-family` checks the shared JP family only. It does not certify the native JE-5000A body; the source, strict Sphinx, browser and cold-replay gates do.

## Scope and release boundary

Only JE-5000A / JP / ja is converted in this change. JBP-5000A is the separate next task. No phase2 or print target is enrolled, and no Feishu/Base, queue, source-table, HTML_link or online asset write is performed. This is a draft engineering candidate with `publication_eligible: false`; merge and online publication require separate authorization. Local acceptance does not prove CI or a deployed release. The root checkout's existing tmp and other worktrees are preserved.
