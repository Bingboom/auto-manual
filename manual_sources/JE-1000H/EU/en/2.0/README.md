# JE-1000H EU/en formal Git source

This directory is the audited, target-scoped build input for the Git-only Web
release of `JE-1000H / EU / en`, version `2.0`.

- Authority: `Jackery Explorer 1000 Plus User Manual (JE-1000H) EUUK
  V2.0-2026-08-03.pdf`, SHA-256
  `07e9ac4b9faabd0852f61702df06f2837caa952c2fa28151b599ad930b1c0bcc`.
- Structured source: [`phase2/`](phase2) contains the English target rows and
  shared dictionaries required for the build. It has no live Bitable dependency.
- Artwork: 20 target-local Web images are extracted by the hash-locked recipe.
  Text-bearing panels retain their complete source frame; the LCD uses a source
  numbered overview image beside a searchable semantic HTML/CSS table.
- Publication boundary: this Git source and its local preview are not a Web
  publication, merge, or live asset-register update.

Build it with:

```text
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off \
AUTO_MANUAL_PRESENTATION_PROFILE=web \
python build.py md \
  --config configs/config.eu-en.yaml \
  --model JE-1000H --region EU --lang en \
  --data-root manual_sources/JE-1000H/EU/en/2.0/phase2 \
  --staging-root <fresh-root>
```
