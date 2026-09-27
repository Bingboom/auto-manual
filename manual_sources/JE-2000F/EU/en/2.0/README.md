# JE-2000F EU/en formal Git source

This directory is the audited, target-scoped build input for the Git-only Web
release of `JE-2000F / EU / en`, version `2.0`.

- Authority: the current published V2.0 manual and the review-branch source
  identified in [`source_manifest.json`](source_manifest.json).
- Structured source: [`phase2/`](phase2) contains the target rows and shared
  dictionaries required to render the English manual.
- Artwork: the original extraction recipe plus the operator-approved corrective
  full-frame recipe are hash-locked through `source_manifest.json`. Eleven
  panels retain their complete grey frame and image-owned text boxes; the LCD
  mode remains a device-only illustration beside a semantic CSS/HTML table.
  The App recipe is hash-locked the same way: its one quarantined panel, the
  App connect-result screens from PDF page 21, is shared by all six languages.
- Live systems: this source has no live Bitable or build-queue dependency.

Build it with:

```text
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off \
AUTO_MANUAL_PRESENTATION_PROFILE=web \
python build.py md \
  --config configs/config.eu-en.yaml \
  --model JE-2000F --region EU --lang en \
  --data-root manual_sources/JE-2000F/EU/en/2.0/phase2 \
  --staging-root <fresh-root>
```

App add-device figure (2026-09-24): all six routes bind their own language block's crop of
the App screens plus this model's control-panel box (`app_asset_recipe`, re-bound
together with the English illustration manifest in `source_manifest.json`); see the intake review addendum of the same date.

Specification tables (2026-09-27): values, structure and labels follow the
print; formatting keeps the house rules. The fr/es/de/it/uk tables now give
4000 cycles, the 3 × AC outputs without `10 A max.`, and the bypass output at
`2200 W max.` (PDF pages 34/50/66/82/98). The it capacity reads
`2048 Wh (40 Ah / 51,2 V ⎓)`, in the printed order. The en DC8020 line says
`Car:` (PDF pages 18 and 8), and the fr labels read `N° modèle` and
`3 × Sortie CA` (PDF page 34). Three print defects use the reviewed wording:
de `Ladetemperatur` and it `Temperatura di scarica`, which the print's own
charging notes use (PDF pages 63 and 79), and the de headings
`EINGANGSANSCHLÜSSE` / `AUSGANGSANSCHLÜSSE`, which the JE-1000H and JE-3600A
EU prints set. The cells are in `phase2/Spec_Master.csv`,
`phase2/spec_titles.csv` and `phase2/Localized_Copy.csv`, and
`source_manifest.json` re-locks all three; see the intake review addendum of the
same date.
