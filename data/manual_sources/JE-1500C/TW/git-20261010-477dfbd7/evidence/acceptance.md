# Local engineering acceptance — 2026-10-10

Target: **JE-1500C / TW / zh-TW**. Source SHA-256: `477dfbd75e15c4f5cf0ef1cfb16142467027b8ab272bec04dfd92371d2d4fdc0`. Verified against source physical pages 2–20; the original cover is archived separately. Source p14's unusual opening `妥產品所有防護蓋，避免清洗過程中進水。` remains verbatim.

## Results

| Gate | Result |
| --- | --- |
| Native source coverage | 326 visible native lines, 17 chapters, 115 live labels, zero unmapped words |
| Structured content | 22 LCD entries; specification rows 8/2/6/2; F0–F9; restricted-substances vector marks restored in a semantic table |
| Symbol admission | Six native glyph/caption pairs pass shape/tint/alpha comparisons; original caption PNG pixel hashes pinned |
| Resource closure | 65 HTML/CSS dependencies present; all 56 browser images loaded |
| Strict Sphinx | `-n -W --keep-going` passes |
| Browser | 1280×900, 768×1024 and 390×844: zero page overflow, broken images, label overflow/overlap/occlusion, clipped packaging copy or runtime/resource errors |
| Cold replay | 61 frozen files byte-identical; copy, artwork, source/shared CSS, theme and language-registry tampering rejected |
| Artwork history | Re-export is byte-identical and preserves rejected incomplete asset hashes; sealing/source gates refuse those hashes |
| Full logic suite | 5291 tests pass, 37 skipped, with `TMPDIR=/private/tmp` |
| Affected regression suite | 154 tests pass, 4 skipped |
| Ruff / maintainability / documentation links | Pass |

The complete drawing groups, App screen frames, source 2×2 cleaning layout, shared heading/table styles, editable App plus control and CSS caption shapes were inspected against the PDF. Dense figures deliberately use an internal horizontal scroll surface on narrow displays; they are not split into invented panels.

Receipts: [source](source_report.json), [browser](browser_report.json), [cold replay](replay_report.json). Review sheets: [desktop chapters](chapters-1280.png), [mobile chapters](chapters-390.png), [complete figures](figures.png).

## Commands

Run from the repository root; `PKG` is `data/manual_sources/JE-1500C/TW/git-20261010-477dfbd7`.

```sh
python3 "$PKG/source/seal_inputs.py"
python3 "$PKG/rebuild.py" --output "$PKG/web/zh-TW"
python3 -m sphinx -b html -n -W --keep-going "$PKG/web/zh-TW" tmp/je1500c/html-frozen
python3 "$PKG/validate_source.py" --output tmp/je1500c/html-frozen --markdown-dir "$PKG/web/zh-TW"
python3 "$PKG/validate_replay.py" --evidence-dir tmp/je1500c/cold-final
python3 "$PKG/validate_layout.py" --base-url http://127.0.0.1:8911 --evidence-dir tmp/je1500c/browser-frozen
TMPDIR=/private/tmp python3 -m unittest
TMPDIR=/private/tmp python3 -m unittest tests.test_build_script tests.test_jhp5000c_us_web_layout tests.test_manual_knowledge tests.test_lang_registry tests.test_lang_longtail_parity tests.test_rtd_portal tests.test_rtd_publication_catalog
python3 -m ruff check build.py integrations tools tests scripts
python3 -m ruff check "$PKG"
python3 tools/check_maintainability_guardrails.py
python3 tools/check_doc_link_integrity.py
python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2
```

All output/evidence directories were unused when the commands ran. Browser validation used a local server serving the strict frozen HTML. These receipts cover local engineering acceptance only. No merge/publication authority, RTD deployment receipt or production browser acceptance is claimed. No live Base, queue, source-table, `HTML_link` or online asset writes were made.
