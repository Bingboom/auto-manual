# JHP-1000A / US / en — source-alignment correction

Operator instruction, 2026-11-03: 「一个一个修 复核通过 就打钩」, following the 32-record attachment-to-Web audit. This first correction is limited to JHP-1000A, record `reczz28SlRGJh40c` in table `tbljbjaXaTD6V9PO`.

The original attachment is unchanged: `JHP-1000A-US-en-V2.pdf`, SHA-256 `cb256e64ddf9a998f4717e3ec2b038b9ef7711572f7d9b752667f1d6e64077c1`. The 2026-10-28 edition and its release approval remain immutable. This new edition inherits its verbatim transcription, model facts, source concerns and approved Web adaptations.

## Corrections

- PDF physical page 8 (printed 05): expand the LCD-map crop to `[40,52,313,230]`. Original numbered labels 10, 11, 24 and 25 and their leaders are complete. No drawing is recreated.
- PDF physical page 13 (printed 10): restore the four original `+` separators as native text between the paired button drawings.
- Desktop key-combination table: remove the 44rem minimum width in this edition's geometry stylesheet above 760px; retain the three columns, button artwork, all operation text and mobile horizontal scrolling.

## Validation and acceptance

Local source, reconstruction and browser checks passed as recorded under `evidence/`. On 2026-11-03 the operator authorized this batch to merge and publish each manual after all checks pass: “授权本批逐本全绿后合入上线”. MA-381 records that conditional authority; this is delegated agent verification, not a claim that the operator personally inspected these renders. Published-route acceptance and the Feishu checkbox remain pending. Mark `复核` only after the corrected published route has passed readback.

The original `derive_assets.py`, `refresh_manifest.py` and `rebuild.py` remain unchanged. `build_content.py` restores only the missing literal `+` in each button pair. Run `refresh_manifest.py`, then `rebuild.py --output <unused-directory>`; store the verified output under `web/en` and run `refresh_manifest.py frozen`. Run the existing JHP-1000A validation suite against this edition as well as the historical edition. The package README owns this target-only correction; no global workflow or CLI behavior changes.
