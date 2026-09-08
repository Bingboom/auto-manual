# JE-3600A EU/en formal Git source

This directory is the audited, target-scoped build input for the Git-only Web
release of `JE-3600A / EU / en`, published revision `2026-05-25`.

- Authority: DingTalk delivery record `QRo3FviEOb`, its current published PDF,
  and its DVT structure source, hash-locked in `source_manifest.json`.
- Structured source: `phase2/` contains only the target rows and shared
  dictionaries needed to render the English manual.
- Artwork: complete grey operation and charging panels remain intact. The LCD
  uses a device-only source illustration plus semantic CSS/HTML tables.
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
