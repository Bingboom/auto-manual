# EU LCD fallback source audit — 2026-09-30

Status: active — 13-table audit complete; asset remediation tracked separately.

This read-only audit covers the 13 text-only LCD tables identified in the
published EU inventory. It does not approve new illustrations, modify live
records, or alter historical snapshots. A text-only table is not automatically
an asset-loss defect: battery packs have a different display from power stations.

## Findings and disposition

| Model / published languages | Tables | Evidence | Required next action |
| --- | ---: | --- | --- |
| JE-1000H en/de/es/fr/it/uk | 6 | Frozen CSV has 27 empty figure cells; all 27 live LCD rows have downloadable PNG attachments. All files decoded and their hashes were recorded. The approved overview and frozen table correctly share number 23 for high/low temperature; live row numbering differs. | Preserve the corrected frozen numbering when binding attachments by indicator identity. Resolve the low-resolution connected-batteries attachment before sealing a new snapshot. Do not import live row numbers blindly. |
| JBP-2000B en/de/it | 3 | Both live LCD rows and frozen CSV have empty figures. The approved display artwork directly labels percentage/fault code and charging indicator. Live asset registry has screen exports. | Keep this two-entry display explanation distinct from the power-station icon catalog; use a shared text/reference variant or separately reviewed icon mapping. |
| JBP-3600A en | 1 | Frozen CSV has two empty figures. Live asset definitions and exports include screen, display panel and charging indicator; this model is not a selectable option in the live LCD table. | Assets exist outside the LCD table. Verify the intended per-row mapping; do not treat a complete labeled display panel as a standalone icon. |
| JE-3600A en/es/fr | 3 | Frozen CSV has 21 empty figures and approved per-language overview artwork. The model is not an option in the live LCD table. The filtered live LCD asset-definition inventory contains no model-specific per-indicator set. | Retain the approved overview and verify any reusable icons individually against it. No claim is made that no assets exist elsewhere online. |

## JE-1000H: numbering and quality findings

The current [approved LCD recipe](../../data/asset_recipes/manual_je1000h_eu_web.json)
binds the V2.0-2026-08-03 PDF by SHA-256. Visual inspection of its English
`lcd_map.png` shows this mapping; the downloaded live attachments were inspected
alongside it:

| Indicator | Live table number | Frozen table number | Approved overview callout |
| --- | ---: | ---: | ---: |
| High temperature | 23 | 23 | 23 |
| Low temperature | 24 | 23 | 23 (shared temperature callout) |
| Fault code | 25 | 24 | 24 |
| Output power | 26 | 25 | 25 |
| Remaining discharge time | 27 | 26 | 26 |

Earlier callouts 1–22 align semantically. The committed
`manual_sources/JE-1000H/EU/en/2.0/phase2/lcd_icons_blocks.csv` already corrects
this numbering and agrees with the approved overview. The mismatch is between
the live table and the frozen publication source, not between the published
table and its figure. Preserve the frozen number column and match attachments
by indicator identity; 27 rows must not be mistaken for 27 distinct callouts.

Connected Batteries row 21 is record `recvhBxNA2mSiw`; its Figure attachment
decodes to **43 × 34 px**, with gray background and a visible left edge. Its
SHA-256 is `b4744a483fa95db386bbb269f277a53f678279c7eda8f8cbf24a78f2b426f2a7`.
It is not suitable for immediate enlarged Web reuse. Other attachments are
available, but attachment presence alone is not visual approval.

## Live provenance and limits

All reads used the business-plane `prod` bot and Base
`LD3lb4G1ua4GOVs1vxAc9W2enje`. The LCD table is `tblW5fCuJ6YdAcND`.
Its current Model options were enumerated after the two 3600-series filters
reported missing options; no absence claim was inferred from a failed filter.

The `asset_key contains lcd` query returned 13 definitions with `has_more=false`.
The `asset_key contains lcd/` query returned seven exports with
`has_more=false`. JBP-3600A charging-indicator export `recvuCHOukPaVP` has an
attachment and hash
`e7f30b293864bc56b9eef638a3f75afbf28e05b7c923ff15edff58ef195b45ac`, matching the
[committed recipe](../../data/asset_recipes/manual_jbp3600a_eu_web.json).
Its live gate fields are empty; this audit does not promote it to approved
live-build eligibility. Git recipe approval and live-table approval remain
separate evidence.

Receipts and decoded files are retained locally in
`/tmp/eu-shared-rollout/lcd-audit/`, including `JE-1000H-downloaded.json`,
`JE-1000H-contact.png`, `live-fields.json`, `live-asset-definitions-lcd.json`
and `live-asset-exports-lcd.json`. These are audit evidence, not release inputs.


## Follow-up state — PR #1343

The original 13-table audit is complete; it does not mean 13 icon catalogs need
identical repairs. The 14-manual rollout in Hello-Docs #157 left the audited
LCD source debt intact. JE-1000H's six-locale repair is now proposed separately
in [#1343](https://github.com/Bingboom/auto-manual/pull/1343): existing attachment
bytes are bound by indicator name and the original callout numbers are retained.
The Connected Batteries image is still the original 43 × 34 px asset, explicitly
reported as resolution debt; this follow-up does not claim the audit's quality
recommendation is resolved. Local layout approval and merge/publication approval
remain separate. JBP-2000B, JBP-3600A and JE-3600A dispositions above remain open.
