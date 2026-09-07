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
