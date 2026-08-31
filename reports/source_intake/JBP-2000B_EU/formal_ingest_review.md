# Formal ingest review: JBP-2000B_EU

- Writes are blocked until the operator says `入库`.
- Region: EU; languages: en/fr/es/de/it/uk (`uk` = Ukrainian, not UK market).
- Paired host display name: `Jackery Explorer 2000 Plus`; US remains `Jackery HomePower 2000 Plus`.
- Create: 11 specs + 9 placeholders + 1 scoped weee2 + 7 EU troubleshooting rows.
- Update: 2 existing JBP LCD rows, only the de/it/ukr fields.
- Existing EU spec/placeholder rows are both zero, so this is additive; no row is replaced or deleted.

## Review flags

1. **needs_review** — Italian `cycle_life` is English in the source PDF. It remains exactly `6000 cycles to 70%+ capacity` and `多语言复核=TRUE`.
2. **source anomaly** — Spanish troubleshooting uses F1/F2 while five other language blocks use F8/FE. The new EU rows use the shared EU code identities F8/FE and the source's exact Spanish contact-support sentence.
3. `weee2` is a new JBP/EU-scoped row. The existing shared row is not modified, so US resolution cannot regress.

## Acceptance after approval

- Full per-record readback for every source-table create/update.
- Confirm the new weee2 attachment has a non-empty file token.
- `sync-data`, JBP EU check/build, 54-page PDF/IDML build, Mac InDesign native finalize, and JBP US regression.
