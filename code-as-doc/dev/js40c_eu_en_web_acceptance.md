# JS-40C EU English Web target — implementation and acceptance

Status: engineering implementation complete; frozen-source Web package accepted
locally and ready for pull-request review. No online Base write, queue dispatch,
OSS upload, or formal Web publication is part of this change.

## Source authority

| Item | Accepted value |
| --- | --- |
| Target | `JS-40C / EU / en` |
| Product | `Jackery SolarSaga 40 Air` |
| Illustrator master | `JS-40C-eu-source.ai`, 10 pages |
| Master SHA-256 | `c5963d37311614f9fc5c9ae40c4da74a71cc53da8e36a92e60a7ff3f25854df9` |
| English body reviewed | Physical pages 3–9 |
| Frozen data root | `data/manual_sources/JS-40C/EU/en/2026-08-30/phase2/` |
| Frozen-data aggregate | `5c2bed8ff99c349a67ba01b405ec08e70d82bdef777ab724fc34d4f35138f3cf` |

The operator-designated Illustrator master is the content and figure authority
for this Git target. `source_manifest.json` records its source coordinates,
exact hash, frozen CSV hashes, and the boundary that engineering acceptance is
not formal publication.

## Composition and ownership

`JS-40C` reuses the `Solar@INTL` family through a target-specific Product Manual
Plan. Its eight slots are Safety Tips, Inbox, product views, charging
connections, angle/device use, Solar Panel Storage, Specifications, and
Warranty. It deliberately has no cover, TOC, unfolding, folding, LCD, UPS,
troubleshooting, or App slot.

The Web output keeps headings, body copy, seven Inbox labels, notes,
specification tables, and warranty cards as semantic HTML/CSS. The 18
source-owned product drawings and English-labelled panels are approved crops;
the crop recipe, registry rows, illustration manifest, and committed PNG bytes
are SHA-256 bound. Storage step text stays live HTML beside three separate
illustrations rather than being flattened into a page image.

## Acceptance checklist

- [x] Exact Illustrator master SHA-256 and 10-page identity verified.
- [x] All physical pages visually reviewed; English body mapped to pages 3–9.
- [x] Frozen source CSVs and aggregate hash replay successfully.
- [x] Eight-slot Product Manual Plan resolves byte-identically to the target manifest.
- [x] 18 approved assets resolve by exact model/region/language and hash.
- [x] Manual IR contains eight pages, seven Inbox cards, three specification compositions, one warranty-years component, and 18 finished illustrations.
- [x] Cold IR replay performs no `.rst`, `.csv`, or presentation-contract reads.
- [x] Tampered packaged artwork is rejected before rendering.
- [x] Target `check`, MyST build, and RTD-style Sphinx HTML complete successfully.
- [x] Browser pass at 1440×900 and 390×844 has no document overflow, missing image, or HTTP error; the Inbox becomes one column on mobile.
- [x] Existing `JS-100I` family target remains covered by regression tests.
- [x] Delivery remains Git-only and does not claim merge or publication.

## Local reproduction

```bash
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off AUTO_MANUAL_PRESENTATION_PROFILE=web \
python build.py md \
  --config configs/config.solar-eu-en.yaml \
  --model JS-40C --region EU --lang en \
  --data-root data/manual_sources/JS-40C/EU/en/2026-08-30/phase2

python tools/readthedocs_source.py \
  --build-root docs/_build \
  --output-dir docs/_build/rtd-js40c \
  --title "JS-40C EU English Web Acceptance"

python -m sphinx -W -b html \
  docs/_build/rtd-js40c docs/_build/rtd-js40c-html
```

The independently browsable package contains the resulting site together with
the frozen Manual IR, semantic HTML intermediate, Markdown, and desktop/mobile
screenshots. Formal publication must follow the separately authorized shared
Hello-Docs/Read the Docs release lane.
