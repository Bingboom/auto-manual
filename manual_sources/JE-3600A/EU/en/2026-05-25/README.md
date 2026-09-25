# JE-3600A EU/en formal Git source

This directory is the audited, target-scoped build input for the Git-only Web
release of `JE-3600A / EU / en`, published revision `2026-05-25`.

- Authority: DingTalk delivery record `QRo3FviEOb`, its current published PDF,
  and its DVT structure source, hash-locked in `source_manifest.json`.
- Structured source: `phase2/` contains only the target rows and shared
  dictionaries needed to render the English manual.
- Artwork: complete grey operation and charging panels remain intact. The LCD
  uses a device-only source illustration plus semantic CSS/HTML tables. The
  App recipe is hash-locked through `source_manifest.json` as well: its one
  quarantined panel, the App connect-result screens from PDF page 22, serves
  the en, fr and es routes built from this source.
- Live systems: this source has no live Bitable or build-queue dependency.

Build it with:

```text
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off \
AUTO_MANUAL_PRESENTATION_PROFILE=web \
python build.py md \
  --config configs/config.eu-en.yaml \
  --model JE-3600A --region EU --lang en \
  --data-root manual_sources/JE-3600A/EU/en/2026-05-25/phase2 \
  --staging-root <fresh-root>
```

Control-panel button names (2026-09-24): the three `CONTROLS` label rows of
`phase2/Spec_Master.csv` carried only the English source value, so the fr/es
routes printed "Power Button", "USB Power Button" and "AC Power Button" in the
App page. Their `Value_fr`, `Value_es`, `Value_de` and `Value_it` cells now hold
each language block's printed names (PDF pages 38/55/72/89; only fr/es are
published), and `source_manifest.json` re-locks the file. English is unchanged.

App add-device figure (2026-09-24): the en/es/fr routes bind their own language block's crop of
the App screens plus this model's control-panel box (`app_asset_recipe`, re-bound
together with the English illustration manifest in `source_manifest.json`); see the intake review addendum of the same date.

Translated cells (2026-09-25): the fr/es columns of the LCD, troubleshooting,
specification, storage, standby-duration, spec-note and footnote rows were
empty, so the fr/es routes printed about 70 English segments and omitted the
notes. They now hold each language block's printed text. The cells are split by
the pages' ruling lines; the English rows' structure is kept, and print defects
use reviewed cross-model wording (see the intake review addendum of the same
date). `source_manifest.json` re-locks the five files; English is unchanged.
