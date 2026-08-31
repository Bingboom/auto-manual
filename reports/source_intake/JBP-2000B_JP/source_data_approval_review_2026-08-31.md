# JBP-2000B_JP source-data approval review

Reference: HTP017 JP PDF, physical page 10 / printed page 08, SHA-256
`f7830bf9fb96d9a3e36737bad5196bbfac2d262eaef642f3406fe77eecd02b0b`.

## Gate status

- Operator approval was recorded and the scoped write was executed on
  2026-08-31 with the business-plane `prod/bot` identity.
- Staging: 17/17 rows corrected where required, `確認=TRUE`, and read back from
  the same records.
- Formal source: 11/11 specification rows and 6/6 placeholder rows created and
  read back.
- Specification notes: 2/2 records created and read back.
- The exact record IDs and ingest result are frozen in
  `source_data_approval_2026-08-31.json` under `write_evidence`.

## Corrections to the 17-row staging package

Eight existing direct-evidence rows differed from the printed source. The new
values preserve HTP017 rather than inheriting JE-1000F JP typography:

| Row | Correction |
| --- | --- |
| `cell_chemistry` | `LiFePO₄` → `LiFePO4` |
| `cycle_life` | `70%` → `70％` |
| `weight` | `サイズ＆重量` → `サイズ & 重量`; restore the space in `約 14.8kg` |
| input expansion port | full-width parentheses → source ASCII parentheses; restore the space in `最大 75A` |
| output expansion port | full-width parentheses → source ASCII parentheses; restore the space in `最大 75A` |
| charging temperature | `℃` → source `°C` form |
| discharging temperature | `℃` → source `°C` form |
| storage temperature | restore `1 年間` / `3 ヶ月` / `1 ヶ月` and source `°C` form |

The remaining nine rows are unchanged. The complete corrected set is in
`spec_intake_staging_review.md`.

## Two omitted specification-page source records

These appear below the specification table in HTP017 and were written as
shared `Spec_Notes` data rather than a target-specific renderer branch:

1. `認証：UN38.3`
2. `本製品はJackery ポータブル電源 2000 Plus 専用となります。他の機器には接続しないでください。`

The full fields, exact live-write scope, and same-record readback are in
`source_data_approval_2026-08-31.json`.

## Executed approval boundary

The completed write was limited to:

1. correcting and reading back the eight listed staging rows;
2. promoting the corrected 11 specification + 6 placeholder rows;
3. creating the two listed `Spec_Notes` rows;
4. reading back every created or updated record.

It did not authorize any unrelated asset, legal-entity, or build-queue write.
Localized-copy and asset approvals were executed as separately evidenced
scopes.
