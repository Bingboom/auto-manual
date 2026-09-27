# JBP-3600A EU/en formal Git source

This directory is the reviewed, target-scoped build input for the Git-only Web
release of `JBP-3600A / EU / en`, version `2.0`.

- Authority: the current published manual `V2.0-2026-08-04` and the matching
  Illustrator source identified in [`source_manifest.json`](source_manifest.json).
- Structured source: [`phase2/`](phase2) contains only the target rows plus the
  shared dictionaries required to render them.
- Artwork: source-derived, hash-locked panels remain in the repository renderer
  asset tree and are bound by the recipe and illustration manifest named in
  `source_manifest.json`.
- Live systems: this source has no live Bitable or build-queue dependency.

Build it with:

```text
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md \
  --config configs/config.bp-eu-en-web.yaml \
  --model JBP-3600A --region EU --lang en \
  --data-root manual_sources/JBP-3600A/EU/en/phase2 \
  --staging-root <fresh-root>
```

## Specification page per print (2026-09-27)

The operator ruled that values, structure and labels follow the print, with the
house formatting kept, so capacity and dimensions keep their house spacing. On
PDF page 11 the IEC row reads `IEC Code` / `IFpR41/136[14S4P]M/-20+40/90`; it
was `Secondary Li-ion Battery` / `IEC: …`, and its row key is now `iec_code`.
Both DC expansion rows now sit in one `INPUT/OUTPUT PORTS` section as
`DC Expansion Port (Input)` and `DC Expansion Port (Output)`; they were
`DC Input` and `DC Output` in two sections. The fix is in
`phase2/Spec_Master.csv` and `phase2/spec_titles.csv`;
`phase2/Localized_Copy.csv` and `phase2/Manual_Copy_Source.csv` carry the merged
title, with the fr/es/de/it wording from PDF pages 19/27/35/43. This print has no
uk block, so the uk cell reuses the JBP-2000B print's `ВХІДНІ/ВИХІДНІ ПОРТИ`.
`source_manifest.json` re-locks the four files.
