# JS-100I_EU formal business-input review

Status: exact additive plan prepared; no live write has been authorized or
performed. The machine-readable plan is
[`formal_business_input_plan.json`](formal_business_input_plan.json).

## Authority and identity

- Published catalog record: `rec27BPMtc8kJl`, JS-100I, 欧英规, EN, PVT,
  latest, V2.0. Its canonical manual is
  [Jackery SolarSaga 100 Air User Manual V2.0-2026-04-01](https://alidocs.dingtalk.com/i/nodes/lyQod3RxJK3XrMnMUONl9pAxJkb4Mw9r?utm_scene=team_space).
- Published PDF: English body physical pages 4–12; SHA-256
  `cec27af653d9f5da11d641e2431ddc0b71ced186bbadfd9594fa8cd9c96e1596`.
- PDF-compatible Illustrator master: `371JNuMVqZ.ai`, 10 pages; SHA-256
  `5d7ded6ba7810505cfb4c91b128a71cbef16a0e11aae720cdbd887559224b96a`.
- Business-plane product record: `recvg5TR1QpQPq` (`JS-100I`, 光伏板,
  Jackery SolarSaga 100 Air), linked to project `recvg5UGmRb9bV`
  (`HTS006`). EU region record: `recvg5S7r6OdTt`.
- The current published version is authoritative. No old/new comparison is
  proposed.

## Live pre-write result

All reads used the business base `LD3lb4G1ua4GOVs1vxAc9W2enje` with an
explicit bot identity. The current target counts are:

| Target | Table | Count |
| --- | --- | ---: |
| Document key `JS-100I_EU` | `tbltnkDIdwiDOP7d` | 0 |
| Specifications | `tblPUFJqt2uGGvTT` | 0 |
| Page placeholders | `tblEhqJVXiyKtnwq` | 0 |
| Spec notes | `tblgJCepw4JvbMbH` | 0 |
| Asset source | `tblsXlZx61Ff5pQC` | 0 |
| Asset definitions | `tblWilXeN5FXPraC` | 0 |
| Asset exports | `tblavT0dcjZGK9DR` | 0 |
| Build queue | `tblbnRHjpJeCVTtj` | 0 |

This is an additive intake. It must not replace or delete any live record.

## Exact proposed increments

1. Create one Document_key dimension record from the existing product and EU
   region links. Read back formula `Document_key=JS-100I_EU` and project code
   `HTS006` before continuing.
2. Reuse the existing English row-key records for `product_name`, `model_no`,
   and `weight`; create the 18 missing solar-specific row keys listed in the
   JSON plan, then query every key to prevent duplicates.
3. Create exactly 21 specification records from the hash-pinned
   `tests/fixtures/js100i_eu_en_phase2/Spec_Master.csv`. Create zero page
   placeholders: Solar@INTL's non-specification body is structural RST and does
   not consume placeholder rows.
4. Add `JS-100I` to the `Spec_Notes.Model` option set through the
   engineering-plane old-base → promote route, then create the three exact STC,
   BNPI, and design-load notes in the plan. Directly changing the new-base
   field definition is forbidden.
5. Create one asset-source record, upload the AI source, deterministic package,
   and manifest, then create 13 definitions and 33 exports (10 archive pages,
   10 previews, 13 semantic Web exports). No operation targets legacy asset
   table `tblxFBWaDG4OYhqu`.
6. Only after the shared queue-routing blocker is fixed and mirrored, create an
   inert Web Publish build record for version `2.0`, Git ref
   `review/JS-100I-EU`, blank `Lang`, and force-refresh enabled. Leave the
   trigger blank so the coordinating task controls publication order.

The source rows preserve the approved five-card Inbox, Safety Tips as the
first chapter, and STC/BNPI semantics. They add no LCD, UPS, App, or portable
power-station-only chapter.

## Deterministic asset package

Running the committed asset pipeline twice against the master and recipe
produced identical results:

| Evidence | Result |
| --- | --- |
| Recipe SHA-256 | `45755c66d4d98ec356d120b5dd14a535b9633c17191e90de0285fd1bb8910c14` |
| Artifact count | 33 |
| `artifacts.csv` SHA-256 | `c4ca2f9e114340098d2a9225f254c71e6cd37aaed39d8762cda9df9d12c8cd2d` |
| `manifest.json` SHA-256 | `87c9be492c71d172aeb559d89650e269b78484172b5986d09d1d8a7cf8e7c7f1` |
| `asset-package.zip` SHA-256 | `d3f56e541c5522548066991026dd375925264a41678884b540c6a8786d726a1b` |
| Semantic export comparison | 13/13 byte-identical to committed Web assets |

The semantic crops intentionally retain English in-figure copy. They are not
textless derivatives.

## Mandatory readback after approval

- Query the target before every phase again; abort if any count changed.
- Read back the new Document_key record and every new row-key record by
  `record_id`.
- Read back all 21 spec rows and all 3 note rows; report each `record_id`, key,
  and value. Formula/lookup fields must be non-empty.
- Read back the asset-source record and confirm non-empty file tokens for
  `source_file`, `asset_package`, and `manifest_file`. Re-download all three and
  compare SHA-256 before accepting `archive_status=已归档`.
- Read back all 13 asset definitions and 33 export records. Definition/source
  links must resolve; every semantic export must have
  `content_sha256=expected_sha256`.
- Read back the inert build row. Its formulas must be
  `Document_ID=JS-100I_EU_2.0`,
  `Task_id=JS-100I_EU_2.0_Web Publish`, project `HTS006`, and
  `Build_family=eu-merged`; the build trigger must remain blank.

## Minimal approval request

Approval can be given by number after reviewing the JSON plan:

1. `批准 1` — Document_key + 18 row-key dimensions + 21 specs + 3 notes,
   including the old-base `Spec_Notes.Model` option promotion.
2. `批准 2` — one asset source with three attachments + 13 definitions + 33
   exports.
3. `批准 3` — create the inert build row only after the shared queue-routing
   fix has passed its stated acceptance tests and reached Hello-Docs main.

Each approved batch is followed by the full same-record readback above. No
unapproved batch is implied by this report.
