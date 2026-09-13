# JE-1000F EU/UK English and French Web input candidate

Released-PDF authority: V2.0 EU-UK, 2026-06-18. This shared snapshot supports
two separate language builds; `en-fr` is a storage label, not a build locale.
It is not a published release or approval of the other language columns.

The source inventory and provenance are in `source_manifest.json`. Reviewed
RST is retained under `docs/_review/JE-1000F/EU`; use `review-asis`, not runtime
templates, to preserve reviewed button labels and app setup instructions.
The historical review manifest is retained as imported provenance, not proof
of the current release version or freshness of its file hashes.

Only target-matching/shared CSV rows and referenced assets are included.
The composite manifest contains 22 approved EU panels (11 per locale), with
embedded localized text. Specifications, LCD mode and other semantic tables
remain HTML, not screenshots. No online table or queue is required.

PDF-backed normalizations in this candidate:

- Remove the extra AC-input bypass line from EN/FR reviewed specification
  carriers and the isolated specification data; it is absent on PDF physical
  pages 19 and 36. Keep the actual bypass-output row and its footnote.
- Add the PDF's exact EN/FR bypass-output footnote to the scoped snapshot.
  The old shared snapshot had it bound to other models only.
- Retain already approved 6.5 A AC output, 4000-cycle life, and 0 C minimum
  charging temperature. Historical row IDs/version columns remain source
  identifiers; the released-PDF version is 2.0, not the old row version 1.0.

Build each locale with the existing family single-language configuration
(both inherit the shared EU single-language base; no new config is added):

```sh
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off AUTO_MANUAL_PRESENTATION_PROFILE=web \
python3 build.py check --config configs/config.eu-en.yaml \
  --model JE-1000F --region EU --lang en --source review-asis \
  --data-root manual_sources/JE-1000F/EU/en-fr/2.0/phase2 \
  --staging-root /tmp/je1000f-eu-en-verification
```

Repeat with `configs/config.eu-fr.yaml`, `--lang fr` and a different staging
root. Do not use the merged `config.eu.yaml`: its source index includes a
French preface absent from the accepted single-language preview.
Then run `build.py md`
with the same inputs, assemble RTD source below that staging build root, and
run strict Sphinx. Release identity must use the verified locale,
not infer it only from a filename. Immutable language evidence, visual checks and
the business release PR remain required before production publication.
