# JE-500A EU/en frozen Git source

This directory freezes the structured Web input for `JE-500A / EU / en` from
the user-selected PDF-compatible Illustrator master. The source artboard hash,
English panel range, extraction recipe, illustration manifest, and committed
CSV bytes are locked in `source_manifest.json`. No live Bitable read is needed
to reproduce the target build.

Build the Web route with:

```text
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off \
AUTO_MANUAL_PRESENTATION_PROFILE=web \
python build.py md \
  --config configs/config.eu-en.yaml \
  --model JE-500A --region EU --lang en \
  --data-root manual_sources/JE-500A/EU/en/2.0/phase2 \
  --staging-root <fresh-root>
```

UPS warning (2026-09-27): `docs/templates/page_je500a_eu-en/06_ups_mode.rst`
gains a UPS WARNING (data servers and medical devices; life-safety,
infrastructure and business-critical equipment; pacemaker wearers) before the
CAUTION, and a fourth CAUTION bullet (one unit directly on a wall outlet, no
cascade). The operator ruled on 2026-09-27 that this page takes the blocks the
shared UPS template gained (「也加上」), although this model's own V2.0-2026-06-09
print does not carry them. The wording is the English block of the JE-3000C EUUK
V2.0-2026-09-15 print (PDF pages 14-15), with `outlet. Do` for the printed
`outlet.Do`, and it follows this page's admonition markup. For now only the Web
and Word show it: the blocks sit under `.. only:: not latex`, and the previous
CAUTION follows unchanged under `.. only:: latex`. No file of this source
changes; see the intake review addendum of the same date.
