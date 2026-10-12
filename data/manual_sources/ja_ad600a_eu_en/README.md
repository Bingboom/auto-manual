# JA-AD600A EU English Web source, version 2.0

This directory is the Git-only structured input for `JA-AD600A / EU / en`. The
authority (the DingTalk V2.0-2026-05-29 PDF and the Illustrator artwork source),
the build inputs and every file hash are recorded in
[`source_manifest.json`](source_manifest.json); the intake review is
[`ja_ad600a_eu_en_web_intake_2026-09.md`](../../../code-as-doc/reviews/ja_ad600a_eu_en_web_intake_2026-09.md).

```sh
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md \
  --config configs/config.charger-eu-en.yaml --model JA-AD600A --region EU --lang en \
  --data-root data/manual_sources/ja_ad600a_eu_en \
  --staging-root <fresh-root>
```

Specification heading (2026-09-27): the operator ruled that values, structure
and labels follow the print, with the house formatting kept. The print heads the
table `2. TECHNICAL SPECIFICATIONS` (PDF page 5); the Web headings drop printed
section numbers. `Spec_Master.csv` now carries `TECHNICAL SPECIFICATIONS` in a
`page_title_source` cell on its first row. The spec renderer reads that column
as the page title, so the heading changes for this model only. The other rows
gain an empty cell. `source_manifest.json` re-locks the file and the snapshot
digest.

Still open: the print sets the thirteen rows as one table with no sub-heading,
but the Web page shows `GENERAL` above it. The spec renderer gives every table
a heading, and no data field removes it, so this needs a renderer change and an
operator decision.
