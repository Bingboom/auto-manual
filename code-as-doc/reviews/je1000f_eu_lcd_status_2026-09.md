# LCD status typography correction
Confirmed clean reusable checkout, local tree equals remote main 4da8ac44 / 8812323c.
Git transport previously hangs; create a local branch on tree-equivalent base and use authenticated Git Data API.
Root cause: frozen_pdf_lcd._pair flattens description into a plain paragraph.
Native PDF pages 96/113/130/147 confirm localized status starts, App setup notes and retention notes.
Existing RST LCD formatter already bolds leading status labels but is a different adapter; retain existing ComponentSpec/public table rendering.
Plan: bounded native adapter markup using source-verified locale boundaries, tests of actual rendered table, fresh immutable four-language freeze, word/assets/full-book parity and browser QA, engineering + publish all-green PR flow.
Non-goals: text changes, images, CSS, other languages, live tables, historical releases.
Validation: Ruff, focused and full unittest, guardrails, docs links, US fixture check, four strict Sphinx builds and cold replay, RTD preflight, four-only publication scope and live verification.

The status labels and App/retention/calibration paragraph starts are verified against the native PDF and all four frozen source records. Dutch Knipperend is normalized to bold as requested, including where the source PDF lacks its font weight. No copy is translated or rewritten.

## Validation evidence

Four strict Sphinx builds pass. Each book has 26 LCD rows, 23 bold status prefixes and 28 semantic breaks. All extracted source JSON files and full body words equal the previous release. After excluding only LCD description cells, the entire main DOM equals the previous release. All 57 image assets per language are byte-identical. Cold IR replay reproduces each Markdown file exactly. Polish browser screenshot confirms separate status lines and computed weight 700.

All four browser pages at 390 px have document width 390 px, 23 status labels at font weight 700 and three separate Wi-Fi lines. No CSS changes. Full RTD portal preflight succeeds; four-target publication scope audit preserves 54 other targets and old five-language version 2.7.

Full regression: Ran 4803 tests in 696.030s; OK (22 skipped). Ruff, maintainability guardrails, documentation links and US fixture build check all pass.

## Additional operator feedback before release

Emergency-charging lead must be bold (all four PDF headings verified; Ukrainian title shares a block with body). F6/F7 numbered troubleshooting steps need separate lines, without splitting decimal measurements. App 2.3/2.4/2.5 captions must follow the image as 2.1/2.2 already do. Add source-adapter formatting and correct shared reference semantic/caption DOM order; preserve CSS and all image bytes. Expand parity exclusions only to these three approved structures; repeat relevant/full validation before updating #1324.

Expanded validation: four strict builds and exact cold replay pass. All four original source JSON files, full body words and image bytes remain identical. Full DOM differs only in LCD descriptions, F6/F7 measure cells, the emergency-charging lead and App result caption order (intertag whitespace ignored). Native PDF pages 103/120/137/154 all explicitly use Gilroy-Bold for the emergency lead. Polish browser verifies weight 700, F6 five lines/F7 three lines, and captions geometrically below the image.
