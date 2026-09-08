# JBP-2000B EU English Web source, version 2.0

Authority: the current published EUUK booklet, V2.0-2026-08-03, linked and hashed
in [source_manifest.json](source_manifest.json). This is a Git-only source; no
online source-table or build-queue write is required.

The English preface (PDF page 2), body (6–13), and EU tail (54) feed the BP
structured source and public semantic IR. Printed covers, contents and folios
are not Web body sections. Specifications, symbols, LCD explanations,
troubleshooting, Inbox and warnings remain shared components. Finished labeled
illustrations are rendered directly from the same PDF, with no text removal.
The illustration manifest records each one-based source page, crop in top-left
PDF points, and output SHA256. PNGs use PyMuPDF RGB rendering at scale 4.

The existing BP dictionaries supplied the CSV schema and reusable labels.
Target values were checked against the published booklet, including all 20
specification/page-value rows, seven error codes and two LCD descriptions.
Global unrelated troubleshooting rows were excluded. Symbol copy is the
published English copy; attachment aliases are local to this snapshot.

```sh
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md \
  --config configs/config.bp-eu-en.yaml --model JBP-2000B --region EU --lang en \
  --data-root manual_sources/JBP-2000B/EU/en/2.0/phase2 \
  --staging-root /tmp/jbp2000b-eu-web
python -m sphinx -b html \
  /tmp/jbp2000b-eu-web/docs/_build/JBP-2000B/EU/en/md /tmp/jbp2000b-eu-html
```

RTD publication follows the existing reviewed Git release handoff. Building
locally does not prove that the production preview has been published.
