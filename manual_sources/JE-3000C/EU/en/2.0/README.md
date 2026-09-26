# JE-3000C EU/en formal Git source

This directory is the audited, target-scoped build input for the Git-only Web
release of `JE-3000C / EU / en`, version `2.0`.

- Authority: the current published `V2.0-2026-07-31` EUUK manual identified in
  [`source_manifest.json`](source_manifest.json).
- Structured source: [`phase2/`](phase2) contains the target rows and shared
  dictionaries required to render the English manual.
- Artwork: the deterministic extraction recipe is hash-locked through
  `source_manifest.json`. Operation and charging panels retain their complete
  grey frames and image-owned text; the LCD mode remains a device-only
  illustration beside a semantic CSS/HTML table.
  The App recipe is hash-locked the same way: its one quarantined panel, the
  App connect-result screens from PDF page 21, serves the fr/es/de/it/uk
  routes built from this source; English keeps its own approved panel.
- Live systems: this source has no live Bitable or build-queue dependency.

Build it with:

```text
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off \
AUTO_MANUAL_PRESENTATION_PROFILE=web \
python build.py md \
  --config configs/config.eu-en.yaml \
  --model JE-3000C --region EU --lang en \
  --data-root manual_sources/JE-3000C/EU/en/2.0/phase2 \
  --staging-root <fresh-root>
```

Control-panel button names (2026-09-24): the three `CONTROLS` label rows of
`phase2/Spec_Master.csv` (`main_power_button`, `dc_usb_power_button`,
`ac_power_button`) carried only the English source value, so the fr/es/de/it/uk
routes printed "POWER Button", "DC / USB Power Button" and "AC Power Button" in
the Product Overview, energy-saving, UPS and App pages. Their `Value_fr` …
`Value_uk` cells now hold each language block's printed names (PDF pages
36/52/68/84/100), and `source_manifest.json` re-locks the file. English is
unchanged.

App add-device figure (2026-09-24): the fr/es/de/it/uk routes bind their own language block's crop of
the App screens plus this model's control-panel box (`app_asset_recipe`, re-bound
alone in `source_manifest.json`); see the intake review addendum of the same date.

Recipe gate (2026-09-25): the three English App panels in `asset_recipe` are quarantined as App UI;
`source_manifest.json` rebinds the recipe hash. Pages are unchanged.

Translated cells (2026-09-25): the fr/es/de/it/uk columns of the specification,
storage, overview-callout and standby/auto-off rows of `phase2/Spec_Master.csv`
and of footnote ② in `phase2/Spec_Footnotes.csv` were empty, so the fr–uk routes
printed English there. They now hold each language block's printed text from
this source's V2.0-2026-07-31 PDF; defects use reviewed wording, and the Spanish
PV value takes the 2026-09-15 revision's correction (see the intake review
addendum of the same date). `source_manifest.json` re-locks both files.

Block figures (2026-09-25): the fr/es/de/it/uk routes bind their own language
block's figures (15 crops each in `asset_recipe`; the fr–uk blocks draw EU
sockets, the English block UK sockets) instead of the shared JE-1000F art; see
the intake review addendum of the same date. `source_manifest.json` re-locks
the web recipe.
