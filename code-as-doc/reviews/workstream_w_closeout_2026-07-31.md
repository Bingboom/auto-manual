# Workstream W close-out evidence — 2026-07-31

## Authorization and scope

The operator released the remaining implementation gates with:

> 814批准：Stage4全部放心；Stage5全量放行

This authorized the remaining Stage 4 acceptance and all Stage 5 gated work,
including the F6 production seed. It does not manufacture field evidence: the
first timed K14 rollback drill and the next real product-line onboarding KPI
remain operator-owned measurements.

## Engineering audit

- Audit baseline: `main` at `f380c85d5c98db57c5e6274ab5567e0d972ef90d`.
- The Stage 0–5 implementation list in
  [`../architecture/scaling_execution_plan.md`](../architecture/scaling_execution_plan.md)
  is fully checked and all registered engineering slices through PR #837 are
  merged.
- PR #814 carries the accepted two-document design-Mac evidence for Stage 4a.
- The Stage 4 Nightly Render manual dispatch succeeded:
  <https://github.com/Bingboom/auto-manual/actions/runs/30651069369>.
- Stage 5 item 13 merged through PR #837; its 17 remote checks passed.

The plan-order implementation map is complete. PR numbers are intentionally
not always monotonic because gated items landed after their prerequisites:

| stage | planned slices | merged PRs in plan order |
| --- | ---: | --- |
| Stage 0 | 8 | #749, #750, #751, #752, #753, #754, #755, #756 |
| Stage 1 | 7 | #757, #758, #759, #760, #761, #762, #763 |
| Stage 2 | 13 | #764, #765, #766, #767, #768, #769, #770, #771, #772, #773, #774, #775, #776 |
| Stage 3 | 13 | #777, #778, #779, #780, #782, #783, #784, #785, #786, #787, #788, #789, #791 |
| Stage 4a | 18 | #817, #792, #793, #794, #795, #796, #797, #798, #799, #800, #801, #814, #803, #804, #805, #818, #820, #821 |
| Stage 4b | 3 | #826, #827, #830 |
| Stage 5 | 14 | #831, #832, #833, #811, #812, #810, #807, #808, #809, #834, #835, #836, #837, #806 |

That is 76 planned slices, all merged. Interleaved repair PRs are supporting
fixes and are not used as substitutes for any numbered plan item.

## F6 production seed

Table: the env-bound Feishu `页面占位参数` table. Direct links to document,
row dictionary, and slot dictionary records were resolved and verified before
write; no display labels or record IDs were guessed.

The three existing US rows were preserved:

| document | row | record ID |
| --- | --- | --- |
| JE-1000F US | `ups_transfer_time` | `recvqXoEHsuyS9` |
| JE-1000F US | `pv_input_range` | `recvqXoF31XLga` |
| JE-1000F US | `dc_input_connector` | `recvqXoFrhr0C9` |

Twelve missing rows were created after a zero-collision dry run:

| document | `pv_input_range` | `dc_input_connector` | `ups_transfer_time` |
| --- | --- | --- | --- |
| JE-1000F EU | `recvqZQMQl2VrE` | `recvqZQMQlkqdo` | `recvqZQMQlWcMl` |
| JE-1000F AU | `recvqZQMQlbzHJ` | `recvqZQMQlkjJd` | `recvqZQMQlpvIx` |
| JE-1000F KR | `recvqZQMQlTHDP` | `recvqZQMQl7U1p` | `recvqZQMQlKrIo` |
| JE-1500D pt-BR | `recvqZQMQlSnDV` | `recvqZQMQlkLaX` | `recvqZQMQljvuM` |

Immediate readback confirmed the raw direct links. A second readback after
Feishu formula/lookup recalculation verified all derived document, row, and
slot fields. The final projection covered 12 created records × 27 fields with
zero mismatches. US was also re-read and no duplicate US row was created.

## Post-sync verification

- Fresh isolated `sync-data --table spec_master`: 865 `Spec_Master.csv` rows.
- Previous Spec_Master SHA-256:
  `96a96387a1106db16eaa67f3bd69888312eee88fb1ca86338ca5f61fa007d9b9`.
- Synchronized Spec_Master SHA-256:
  `27bde21c034fc0509d50826359072bd34200d476337af53a745bf35a252f46bf`.
- Snapshot manifest file SHA-256:
  `725b1bcf57db431ac976709d6f1c51a8644a4cabd5630102a5422229fe4e9f30`.
- The fresh snapshot contains exactly 15 expected semantic rows across
  US/EU/AU/KR/pt-BR.
- The official migration-range `diff-report` covered the 16 expected templates
  (eight languages × charging/UPS) and the synchronized fixture scope, with no
  unrelated template file.

Target checks against the fresh snapshot:

| target | result |
| --- | --- |
| JE-1000F US | pass |
| JE-1000F EU | pass |
| JE-1000F AU | pass |
| JE-1000F KR | all three new placeholder gaps cleared; four pre-existing `CAPABILITY_CONTENT_MISSING` findings remain |
| JE-1500D pt-BR | all three new rows present; five pre-existing source rows remain missing |

The KR findings are AC/DC output resume, LED light, emergency charging, and
quiet charging. The pt-BR missing rows are `product_name`, `model_no`,
`main_power_button`, `dc_usb_power_button`, and `ac_power_button`. They are
separate target-readiness debt, not failed writes from this F6 batch.

No generated build output, synchronized phase2 snapshot, or local environment
file is committed by this close-out change.
