# JS-100I EU English Web source, version 2.0

This directory is the Git-only structured input for `JS-100I / EU / en`. The
published V2.0-2026-04-01 PDF and the Illustrator master are the authority; their
hashes, the build inputs and the snapshot digest are recorded in
[`source_manifest.json`](source_manifest.json).

```sh
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md \
  --config configs/config.solar-eu-en.yaml --model JS-100I --region EU --lang en \
  --data-root data/manual_sources/JS-100I/EU/en/2.0/phase2 \
  --staging-root <fresh-root>
```

Specification heading (2026-09-27): the operator ruled that values, structure
and labels follow the print, with the house formatting kept. The print heads
the page `TECHNICAL PARAMETERS` (PDF page 11). `phase2/Spec_Master.csv` now
carries it in a `page_title_source` cell on its first row. The spec renderer
reads that column as the page title, so the heading changes for this model
only. The other rows gain an empty cell. The `TECHNICAL PARAMETERS` rows in the
JS-100F and JS-200E `spec_titles.csv` stay inert: the renderer looks up only
`SPECIFICATIONS` there, and changing that lookup would also retitle those two
models, which have no approved print. `source_manifest.json` re-locks the file
and the snapshot digest.

Still open, because no data field can express them:

- the print's product sub-heading `● JACKERY SOLARSAGA 100 AIR`, which groups
  `BASIC INFORMATION` and `ELECTRICAL DATA`; the renderer has one heading level
  per table;
- the order of the STC, BNPI and bracket notes, which the print sets between
  `ELECTRICAL DATA` and `MULTIFUNCTIONAL ADAPTER`; the renderer places notes
  after the last table.

Both need a renderer change and an operator decision.
