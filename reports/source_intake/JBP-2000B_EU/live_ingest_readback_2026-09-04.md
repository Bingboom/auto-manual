# Live ingest readback: JBP-2000B_EU (2026-09-04)

Written to the live source tables after the operator's 「按正确值 去写 / 后三这种不一致 你就按一致的去写」.

## What was written

| table | table_id | records | live before | live after |
| --- | --- | ---: | ---: | ---: |
| 内容源_规格参数明细 | `tblPUFJqt2uGGvTT` | 11 | 0 | 11 |
| 内容源_页面占位参数 | `tblEhqJVXiyKtnwq` | 9 | 0 | 9 |

Purely additive — both tables held zero `JBP-2000B_EU` rows before, verified live
against a positive control (`JBP-2000B_US` returned 11 and 9). Nothing was replaced
or deleted. `Document_key_link` resolves to `recvtNbSrFZXfL`, the pre-existing
主数据_Document_key record; the `document_key` formula computes `JBP-2000B_EU` and
`region` computes `EU` on every row.

## Payload shape correction

The plan stored link fields as bare id strings (`["recvtNbSrFZXfL"]`). The live
records carry `[{"id": "..."}]`, and `+field-list` confirms all three are `link`
type. A single-record probe was written first and read back by record id to prove
the link resolved before the remaining records went in.

## House-style corrections applied before the write

32 cells, every one justified by the unanimous wording of the EU siblings that
share the battery pack's numbers. 26 of the 32 corrected values are byte-identical
to a string already shipping in the table; the other 6 share its skeleton with the
battery pack's own numbers.

| row | field | before | after |
| --- | --- | --- | --- |
| Capacity | en | `2048 Wh (40 Ah/51.2 V ⎓)` | `2048 Wh (40 Ah / 51.2 V ⎓)` |
| Capacity | fr | `2048 Wh (40 Ah/51,2 V ⎓)` | `2048 Wh (40 Ah / 51,2 V ⎓)` |
| Capacity | es | `2048 Wh (40 Ah/51,2 V ⎓)` | `2048 Wh (40 Ah / 51,2 V ⎓)` |
| Capacity | de | `40 Ah / 51,2 V ⎓ (2048 Wh)` | `2048 Wh (40 Ah / 51,2 V ⎓)` |
| Capacity | uk | `2048 Вт-год (40 A-год/51,2 В ⎓)` | `2048 Вт-год (40 А-год / 51,2 В ⎓)` |
| Weight | de | `Ca. 14,8 kg` | `Etwa 14,8 kg` |
| Dimensions | en | `36.5 × 25.5 × 19.1 cm` | `36.5 x 25.5 x 19.1 cm` |
| Dimensions | fr | `36,5 × 25,5 × 19,1 cm` | `36,5 x 25,5 x 19,1 cm` |
| Dimensions | es | `36,5 × 25,5 × 19,1 cm` | `36,5 x 25,5 x 19,1 cm` |
| Dimensions | de | `36,5 × 25,5 × 19,1 cm` | `36,5 x 25,5 x 19,1 cm` |
| Dimensions | it | `36,5 × 25,5 × 19,1 cm` | `36,5 x 25,5 x 19,1 cm` |
| Cycle Life | it | `6000 cycles to 70%+ capacity` | `6000 cicli con capacità residua superiore al 70%` |
| Charge Temperature | en | `-10°C to 45°C` | `-10 °C to 45 °C` |
| Charge Temperature | fr | `-10°C à 45°C` | `-10 °C à 45 °C` |
| Charge Temperature | es | `-10°C a 45°C` | `-10 °C a 45 °C` |
| Charge Temperature | de | `-10°C und 45°C` | `von -10 °C bis 45 °C` |
| Discharge Temperature | en | `-10°C to 45°C` | `-10 °C to 45 °C` |
| Discharge Temperature | fr | `-10°C à 45°C` | `-10 °C à 45 °C` |
| Discharge Temperature | es | `-10°C a 45°C` | `-10 °C a 45 °C` |
| Discharge Temperature | de | `-10°C und 45°C` | `von -10 °C bis 45 °C` |
| Storage Temperature [1 month] | en | `-20°C to 45°C (0-60%RH)` | `-20 °C to 45 °C (0-60 % RH)` |
| Storage Temperature [1 month] | fr | `-20°C à 45°C (0-60% HR)` | `-20 °C à 45 °C (0-60 % HR)` |
| Storage Temperature [1 month] | de | `-20 °C bis 45 °C (0–60 % rL)` | `von -20 °C bis 45 °C (0–60 % rF)` |
| Storage Temperature [1 month] | uk | `від -20 °C до 45 °C (0-60% RH)` | `від -20 °C до 45 °C (0-60 % RH)` |
| Storage Temperature [3 months] | en | `0°C to 45°C (0-60%RH)` | `0 °C to 45 °C (0-60 % RH)` |
| Storage Temperature [3 months] | fr | `0°C à 45°C (0-60% HR)` | `0 °C à 45 °C (0-60 % HR)` |
| Storage Temperature [3 months] | de | `0 °C bis 45 °C (0–60 % rL)` | `von 0 °C bis 45 °C (0–60 % rF)` |
| Storage Temperature [3 months] | uk | `від 0 °C до 45 °C (0-60% RH)` | `від 0 °C до 45 °C (0-60 % RH)` |
| Storage Temperature [12 months] | en | `0°C to 25°C (0-60%RH)` | `0 °C to 25 °C (0-60 % RH)` |
| Storage Temperature [12 months] | fr | `0°C à 25°C (0-60% HR)` | `0 °C à 25 °C (0-60 % HR)` |
| Storage Temperature [12 months] | de | `0 °C bis 25 °C (0–60 % rL)` | `von 0 °C bis 25 °C (0–60 % rF)` |
| Storage Temperature [12 months] | uk | `від 0 °C до 25 °C (0-60% RH)` | `від 0 °C до 25 °C (0-60 % RH)` |

The three that were defects rather than style, all in the German column:

1. `-10°C und 45°C` — `und` is *and*, not a range. All 8 German temperature rows
   on EU siblings write `von X bis Y`.
2. Capacity `40 Ah / 51,2 V ⎓ (2048 Wh)` — that is the **Italian** word order.
   German puts Wh first on 4/4 siblings; JE-2000F EU's German is byte-identical
   to the corrected value.
3. Storage `(0–60 % rL)` — the German abbreviation for relative humidity is `rF`
   (relative Feuchte) on 3/3 siblings, and the leading `von` was missing.

Ukrainian capacity was taken whole from JE-2000F EU, the numeric and symbol twin;
note its `А` is Cyrillic U+0410 (ампер-година), where the plan had a Latin `A`.

## Acceptance

- `sync-data`: `Spec_Master` 1064 → 1084 rows (+20, exactly the records written).
- `build.py idml --config configs/config.bp-eu.yaml --model JBP-2000B --region EU`
  now succeeds: **54 spreads** (matching the 54-page EU master), 76/76 pages matched,
  530 stories, 11 spec rows. It previously failed at target identity resolution.
- Every corrected string is present in the built `manual.ir.json`, and every
  pre-correction defect (`-10°C und 45°C`, `Ca. 14,8 kg`, `rL`) is absent from it.

## Not done in this round

The same plan also stages 7 EU troubleshooting rows, 1 JBP/EU-scoped `weee2` symbol
row, and de/it/ukr patches to 2 existing LCD rows. Those were out of the scope the
operator named (the `Spec_Master` rows) and remain unwritten. The build resolves 11
troubleshooting rows without them, so they are not blocking.

The plan's own two review flags stand: the Italian `cycle_life` English residue was
resolved here by reusing the reviewed Italian already on 3/3 EU siblings (approved
wording, not a new translation); the Spanish F1/F2 vs F8/FE error-code anomaly
belongs to the troubleshooting rows and is untouched.
