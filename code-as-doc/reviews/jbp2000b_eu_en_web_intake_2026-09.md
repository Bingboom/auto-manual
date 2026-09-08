# JBP-2000B EU/en Web intake

Baseline: `d1b12bf8686941b5e79d9b507d7cc991da3427b9`.
Target: JBP-2000B / EU / en, published V2.0-2026-09-08.

## Scope and checklist

- [x] Read current demand list; choose the published edition as authority.
- [x] Download and hash the published PDF; identify English pages 2, 6–13, 54.
- [x] Visually inspect body pages and extract 11 finished, labeled panels.
- [x] Freeze target data and reusable dictionaries in a Git source snapshot.
- [x] Preserve all seven published fault codes and two LCD explanations.
- [x] Preserve 6000-cycle rating, 200 mm clearance, stacking precautions and exchange-only warranty.
- [x] Build through the existing BP manifest, structured source and shared IR.
- [x] Keep Inbox, specifications, symbols, warnings and fault tables semantic.
- [x] Check desktop/mobile image loading and horizontal overflow.
- [ ] Engineering PR reviewed and merged.
- [ ] Publish frozen Web output to the Read the Docs preview and verify its URL.

The single-English config extends the existing BP/EU family. Existing six-language
and JBP-3600A single-English configurations and source carriers are unchanged.
The English publication variants reuse the available BP carriers; EU connection
and warranty copy have dedicated region carriers to preserve this published
edition without changing the other target's approved wording.

## Source mapping

| PDF page | Source / shared component |
| --- | --- |
| 2 | English preface, language-filtered |
| 6 | BP safety; four signal words and eight symbol rows |
| 7 | Three Inbox cards; complete labeled overview |
| 8 | LCD table, labeled LCD and two operation figures |
| 9–10 | Connections and labeled clearance/locking figures; seven fault codes |
| 11 | AC/solar charging via Explorer 2000 Plus, EU illustrations |
| 12 | Storage; structured specifications |
| 13 | EU exchange warranty, 3+2 years |
| 54 | EU declaration and manufacturer |

The authoritative source and per-file inventory are in
[the source manifest](../../manual_sources/JBP-2000B/EU/en/2.0/source_manifest.json).
Line wrapping, punctuation and existing component section formatting may differ
from paper. No old/new edition comparison, live Bitable write, IDML change,
OSS upload or public-link generation is part of this intake.

## Local acceptance (2026-09-08)

- `build.py check` passed for the new config, target and frozen data root.
- Real `build.py md` and Sphinx HTML builds passed.
- All 11 finished panel SHA256 values match the images packaged in HTML.
- Chromium at 1440 and 375 px: 19 images loaded, zero broken images, document
  scroll width equals viewport width. Shared wide tables retain their scroll container.
- 55 configuration/template tests passed (`test_config_loader`, `test_config_pages`,
  `test_pilot_configs`, `test_validate_config`, `test_template_identity_literals`,
  `test_preface_templates`). No Python implementation changes.
- Documentation link integrity and maintainability guardrails passed.

This is local engineering acceptance, not a claim of RTD publication.

## Source revision, 2026-09-08

The user supplied a newer V2.0 PDF before this intake was merged. It now owns
the source manifest and illustration hashes; the earlier source hash is retained
as superseded provenance. This is an update to the structure source, not an
edit to generated HTML or a live-table backport.

- English preface: adds compatibility with Explorer 2000 Plus and Explorer 1000 Plus.
- Operation: host naming becomes “the portable power station”.
- Connections: new opening sentence and portable-power-station terminology.
- Charging: updated AC and solar instructions and warning wording.
- All eleven finished panels were rendered again from the new PDF using recorded crops.
- Existing other-language and other-target carriers were not modified.

The same target quality check, 55 tests, real Sphinx build and browser acceptance
were rerun for this source revision. Production publication remains pending.
