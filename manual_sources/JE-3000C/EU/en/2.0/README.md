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
