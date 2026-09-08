# JE-2000F EU/en formal Git source

This directory is the audited, target-scoped build input for the Git-only Web
release of `JE-2000F / EU / en`, version `2.0`.

- Authority: the current published V2.0 manual and the review-branch source
  identified in [`source_manifest.json`](source_manifest.json).
- Structured source: [`phase2/`](phase2) contains the target rows and shared
  dictionaries required to render the English manual.
- Artwork: source-derived, hash-locked panels are bound through the extraction
  recipe and Web illustration manifest named in `source_manifest.json`.
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
