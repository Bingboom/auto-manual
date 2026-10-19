# JE-1500C / TW / zh-TW — native PDF Web candidate

This Git-only package converts the supplied Traditional Chinese manual into selectable HTML through the shared Manual IR, ComponentSpec, Web theme and Sphinx pipeline. It is an engineering candidate; merge and publication require separate operator authorization.

## Source and boundary

| Field | Verified source |
| --- | --- |
| Product | Jackery Explorer 1500 Ultra 不斷電式電源供應器（UPS） |
| Model / market / language | JE-1500C / TW / zh-TW |
| PDF | `Jackery Explorer 1500 Ultra 說明書-20260923.pdf` |
| SHA-256 | `477dfbd75e15c4f5cf0ef1cfb16142467027b8ab272bec04dfd92371d2d4fdc0` |
| Physical pages | 20; Web p2–20, cover p1 archived in `source/print-cover.json` |
| Metadata title | `16-0102-000487 HTE1181500A-TW-JAK 竖版说明书 A0` |
| Printed version | Unknown; not inferred from filename or metadata |

There are 17 native chapters, 115 editable figure labels, 22 LCD entries, four specification grids and F0–F9 troubleshooting. The Taiwan restricted-substances declaration is a semantic table. The original source, text/geometry provenance, artwork decisions and hash-pinned shared inputs are retained. No phase2 target enrollment or live Base, queue, source-table, `HTML_link` or online asset writes are involved.

## Artwork and copy

- Inventory and compare shared glyphs before extraction. Three existing symbols and nine LCD glyphs are reused. Three exact native symbol variants are proposed under the shared Git manifest; native LCD differences are recorded in `source/lcd_provenance.json`.
- Export complete original drawing groups with native clipping and occluders through the shared asset pipeline. Preserve the source's 2×2 cleaning composition and full App screenshot frames. Dense diagrams scroll horizontally on narrow screens.
- Draw 10 independent caption shapes in CSS; their geometry and removed paths are recorded in `source/caption_frames.json`. Figure copy remains editable HTML. Physical device markings, screenshot UI and native cleaning A/B markings remain original artwork.
- `source/asset_decisions.json` rejects superseded incomplete artwork hashes. Sealing and source validation refuse those hashes; re-export preserves rejection history.
- PDF private-use digit glyphs are recovered as 0–9 with native evidence in `source/glyph_recoveries.json`.
- Source p14 begins `妥產品所有防護蓋，避免清洗過程中進水。`; it is preserved verbatim and recorded in `source/source_anomalies.json`.

## Offline replay and validation

Run from the repository root with unused output/evidence directories. `web/zh-TW/` is generated output; change the reviewed source inputs and regenerate instead of editing it.

```sh
PKG=data/manual_sources/JE-1500C/TW/git-20261010-477dfbd7
python3 "$PKG/rebuild.py" --output /private/tmp/je1500c-tw-replay
python3 -m sphinx -b html -n -W --keep-going \
  /private/tmp/je1500c-tw-replay /private/tmp/je1500c-tw-html
python3 "$PKG/validate_source.py" --output /private/tmp/je1500c-tw-html \
  --markdown-dir /private/tmp/je1500c-tw-replay
python3 "$PKG/validate_replay.py" --evidence-dir /private/tmp/je1500c-tw-cold
python3 "$PKG/validate_layout.py" --base-url http://127.0.0.1:8910 \
  --evidence-dir /private/tmp/je1500c-tw-browser
```

Serve the strict HTML output for browser validation. The browser gate checks 1280, 768 and 390 px, image loading, label ink, overlap, occlusion and card clipping. Source validation checks native visible-line coverage, figure label order, table values, symbol admission and full HTML/CSS resource closure.

After intentional source changes, run `source/seal_inputs.py` before rebuilding. The manifest binds package inputs and shared implementation/styles; `evidence/` is verification output and is excluded from input binding. Cold replay must match the frozen package byte for byte and reject changed copy, artwork, source/shared CSS, theme and language registration.

See [acceptance evidence](evidence/acceptance.md). Local rendering and engineering checks do not prove RTD deployment or production visual acceptance.
