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
The composite manifest contains 55 approved EU panels (11 per locale for
EN/FR/ES/DE/IT), with embedded localized text, plus one `locale=shared` App
connect-result panel: all five language blocks of the PDF print the same
English App screens (PDF physical page 22 in the EN block). Specifications,
LCD mode and other semantic tables remain HTML, not screenshots. No online
table or queue is required.

PDF-backed normalizations in this candidate:

- Remove the extra AC-input bypass line from EN/FR reviewed specification
  carriers and the isolated specification data; it is absent on PDF physical
  pages 19 and 36. Keep the actual bypass-output row and its footnote.
- Add the PDF's exact EN/FR bypass-output footnote to the scoped snapshot.
  The old shared snapshot had it bound to other models only.
- Retain already approved 6.5 A AC output, 4000-cycle life, and 0 C minimum
  charging temperature. Historical row IDs/version columns remain source
  identifiers; the released-PDF version is 2.0, not the old row version 1.0.
- The EN/FR PDF parity pass restores the safety accessory condition, LCD
  mapping and charging description, 12 A maximum qualifier, troubleshooting
  wording, App step 2.5, separate USB-C rating rows and PDF section order.
  It removes the extra battery-disposal row and the unsupported Output Resume
  default/App instruction. See [PDF parity notes](pdf_parity_notes.md).

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

ES/DE/IT build from the same data root with their `config.eu-<lang>.yaml`
and `--source review`, not `review-asis`: their reviewed LCD pages fail the
`review-asis` LCD-table validation (row 20). Use `review`, not the default
`auto`, for all three release actions. Under `auto`, `check` skips the review
sync that `md` runs, so the check, md and html language-projection captures
differ and staging refuses them. On 2026-09-24 the `review` build matched the
published 2026-09-14 ES/DE/IT pages except for the App connect-result figure,
which now uses the shared panel.

App screenshots (2026-09-24): the reviewed promotion `je1000f-eu-app-ui-v1`
(#1252) resolves `asset:app/add_device` and `asset:app/connect_result` to the
EU print's own screens for JE-1000F/EU. The EN page and the EN/FR generated
drafts already used those URIs. The FR/ES/DE/IT/UK pages (p31/p46/p61/p76/p91)
and the DE/ES/IT/UK generated drafts pointed at the shared JP-market
screenshots through raw `common_assets/app/*.png` paths; they now use the same
URIs, matching Hello-Docs #125 on `review/JE-1000F-EU`, and
`source_manifest.json` re-locks those nine files. The visible Web App panels
are unchanged; the connect-result figure's hidden semantic image becomes the
EU export in all five languages.
