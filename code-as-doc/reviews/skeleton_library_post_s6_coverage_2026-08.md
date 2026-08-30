# Skeleton library post-S6 coverage re-baseline (R0, 2026-08)

Status: `ready_for_review`

Branch: `docs/milestone-m-r0-coverage-rebaseline`

Scope: read-only evidence reconciliation plus one operator-approved additive
`Document_key` master-data write. No specification, placeholder, localized-copy,
asset-registry, review-derivative, or generated-output write was performed.

This report is the R0 evidence package for the post-S6 scale-proof checklist in
[`next_optimization_checklist.md`](../next_optimization_checklist.md). The
authoritative 58-row machine-readable ledger is
[`skeleton_library_post_s6_coverage_2026-08.csv`](skeleton_library_post_s6_coverage_2026-08.csv).

## 1. Three metrics that must not be mixed

| Metric | Strict R0 definition | Current result |
| --- | --- | --- |
| `structurally_reconstructable` | The corpus chapter tree can be reconstructed from its skeleton cell plus reusable modules and product/region differences. At most one recorded overlay is allowed; an outlier is `no`. | **55/58 = 94.8%** |
| `pipeline_buildable` | The exact target resolves uniquely and the committed source data makes the current `main` `build.py check` target pass. A config or a historical successful row is not enough. | **4/58 = 6.9%** |
| `delivery_validated` | Four renderers plus native InDesign/package checks have recorded acceptance evidence for the same target. Native-only or historical build evidence is not enough. | **2/58 = 3.4%** |

Current pipeline PASS targets, deduplicated by `Document_Key`:

- `JBP-2000B_US`
- `JE-1000F_EU`
- `JE-1000F_JP`
- `JE-1000F_US`

Current delivery-validated targets:

- `JBP-2000B_US`, supported by
  [`jbp2000b_us_local_validation_2026-08.md`](jbp2000b_us_local_validation_2026-08.md)
  and
  [`jbp2000b_us_s6_reconciliation_2026-08.md`](jbp2000b_us_s6_reconciliation_2026-08.md)
- `JE-1000F_US`, supported by
  [`style_component_contract_v2_plan.md`](../dev/style_component_contract_v2_plan.md)
  and
  [`idml_three_target_font_portability_discovery_2026-08-29.md`](idml_three_target_font_portability_discovery_2026-08-29.md)

JE-3000C KR is not counted as delivery-validated: its native IDML evidence does
not include the complete four-renderer acceptance set, and it is not one of the
frozen 58 independent corpus manuals.

## 2. Reconciliation result

The frozen corpus closes exactly once at **58 manuals / 22 SKUs**. The ledger
contains 58 unique `corpus_id` values and 58 unique corpus slugs. Live target
identity is exact for 23 manuals and remains `needs_review` for 35; no missing
identity was inferred from filename or model similarity.

| SKU | Manuals | Structural | Pipeline | Delivery | Exact live identity | `needs_review` identity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HTE110 | 2 | 0 | 0 | 0 | 0 | 2 |
| HTE118 | 3 | 2 | 0 | 0 | 0 | 3 |
| HTE119 | 1 | 1 | 0 | 0 | 0 | 1 |
| HTE132 | 3 | 3 | 0 | 0 | 0 | 3 |
| HTE133 | 1 | 1 | 0 | 0 | 0 | 1 |
| HTE139 | 4 | 4 | 0 | 0 | 2 | 2 |
| HTE140 | 5 | 5 | 0 | 0 | 1 | 4 |
| HTE147 | 1 | 1 | 0 | 0 | 1 | 0 |
| HTE150 | 1 | 1 | 0 | 0 | 0 | 1 |
| HTE151 | 2 | 2 | 0 | 0 | 1 | 1 |
| HTE152 | 4 | 4 | 0 | 0 | 3 | 1 |
| HTE153 | 7 | 7 | 3 | 1 | 7 | 0 |
| HTE154 | 4 | 4 | 0 | 0 | 3 | 1 |
| HTE156 | 4 | 4 | 0 | 0 | 0 | 4 |
| HTE157 | 1 | 1 | 0 | 0 | 0 | 1 |
| HTE158 | 2 | 2 | 0 | 0 | 1 | 1 |
| HTE159 | 3 | 3 | 0 | 0 | 1 | 2 |
| HTE162 | 3 | 3 | 0 | 0 | 0 | 3 |
| HTP007 | 1 | 1 | 0 | 0 | 0 | 1 |
| HTP011 | 1 | 1 | 0 | 0 | 0 | 1 |
| HTP015 | 2 | 2 | 0 | 0 | 0 | 2 |
| HTP017 | 3 | 3 | 1 | 1 | 3 | 0 |
| **Total** | **58** | **55** | **4** | **2** | **23** | **35** |

The current config-derived check matrix returned `PASS=12`, `SKIP=5`,
`FAIL=2`. Multiple config entries can resolve to the same `Document_Key`, so
the 12 raw PASS invocations reduce to four independently proven corpus targets.

## 3. Why the old 15/58 number stays historical

The 2026-08-20 **15/58** figure was a pre-S6 design-era pipeline-reach estimate:
it classified manuals by the then-known production/config surface. It did not
require every counted manual to have an exact live identity, current committed
source rows, a current `build.py check` PASS, and delivery evidence.

R0 deliberately uses stricter observable gates. Therefore:

- retain 15/58 as the dated Phase A estimate;
- use **4/58** only for current strict `pipeline_buildable`;
- use **2/58** only for current strict `delivery_validated`;
- never report an inferred 16/58 after S6.

These values measure different things and must not be used as a trend line.

## 4. Live readback and reproducibility

All Base reads used `lark-cli 1.0.78`, profile `prod`, identity `bot`, full
pagination (`--limit 200` plus offsets), and field-order consistency checks.
The recount was read-only. After the operator approved the R0 target ruling,
one additive `Document_key` row was created and read back; no row was updated
or deleted.

| Live table surface | Rows read |
| --- | ---: |
| `Document_key` | 33 |
| build table | 30 |
| specifications | 420 |
| page placeholders | 627 |
| new asset sources | 1 |
| asset definitions | 19 |
| asset exports | 167 |

The structural baseline is reproduced by:

```bash
python3 code-as-doc/architecture/corpus_audit_2026-08/stats.py
```

The current pipeline baseline was reproduced through the repository's
config-derived target matrix and recorded as:

```text
PASS=12 SKIP=5 FAIL=2
```

Ledger identity matching is intentionally narrow: live `项目代码 == SKU`, a
unique region suffix, and an exact returned `Document_key`. Zero or multiple
matches become `needs_review`.

## 5. Confirmed second BP@INTL target: verified facts and rulings

### 5.1 Source authority inspected

The corpus candidate is HTP017, product **Jackery Battery Pack 2000**, model
**JBP-2000B**, material number **16-0102-000400**. The inspected source is:

```text
Jackery Battery Pack 2000 User Manual (JBP-2000B) EUUK V2.0-2026-08-03.pdf
SHA-256 0a240f2653ab4135b354e0d697e692842027689de578a72c1c802174a644c1c6
54 pages; 368.754 x 524.659 pt; PDF 1.6
Creator: Adobe Illustrator 30.4 (Windows)
```

Every inspected page carries Illustrator `PieceInfo`, so the PDF is an
Illustrator-editable source carrier. A full indexed filename search under the
local Downloads, Desktop and Documents roots found no separate `.ai` file.
The operator approved this PDF as the EU source authority on 2026-08-30.

The committed `data/asset_registry.csv` is not empty for this model: it contains
**21 finished JBP-2000B entries**, split into **7 `ALL`-region neutral assets**
and **14 US-scoped assets**. R2 may reuse the seven neutral assets under their
existing scope, but it must not relabel US covers, language composites,
connection diagrams or QR assets as EU. The live asset
source/definition/export tables contain no JBP master or EU enrollment. The
remaining R2 gate is therefore EU source enrollment plus a 54-page delta-asset
completeness check, not a claim that JBP has no reusable assets.

The six printed language blocks are `en`, `fr`, `es`, `de`, `it`, `uk` in that
order. Here `uk` is the ISO language code for **Ukrainian**, not evidence of a
United Kingdom market scope.

### 5.2 Warranty and legal evidence

All six warranty pages visibly show the same commercial term:

- **3 years standard warranty** (36 months)
- **2 years extended warranty**
- extension contact: `hello.eu@jackery.com`

The final page contains an EU RED declaration for JBP-2000B with Bluetooth and
Wi-Fi under Directive 2014/53/EU. It names only:

```text
MANUFACTURER: SHENZHEN HELLO TECH ENERGY CO., LTD.
F2-3, Bldg. 7, Jiaanda Science and technology industrial park factory,
the east side of Huafan Road, Tongsheng Community, Dalang Street,
Longhua District, Shenzhen, Guangdong, China
+86 400 668 9293 · sales@hello-tech.com · www.hello-tech.com
```

No UK responsible person, UKCA declaration, or separate EU responsible person
was found in the 54-page source. The operator ruled this target **EU
six-language only** on 2026-08-30; `uk` remains the Ukrainian language code and
no United Kingdom market claim or UK legal carrier belongs in this target.

### 5.3 Source defect found by visual inspection

Physical page 53, the Ukrainian warranty page, contains an untranslated German
`Umtausch` heading and German exchange paragraph. The text layer also carries
the residue. The source is therefore suitable as an editable layout/asset
authority but is not clean six-language copy authority without a correction or
an explicit accepted-source ruling.

The correction does not need to be invented or machine-translated. The shipped
HTE154 JE-2000F EU/UK book (SHA-256
`6b4af85236ccfee0f4d24ad55ee8b24684d023982b5da216023d4f716f183f3d`), physical
page 99, and the HTE152 JE-2000E EU/UK book carry the same warranty exchange
meaning in a visually verified Ukrainian component:

```text
Обмін
Jackery замінить (за рахунок Jackery) будь-який продукт Jackery, який не працює
протягом відповідного гарантійного періоду через дефект матеріалів або
виготовлення. Заміна отримує залишок гарантійного терміну оригінального продукту.
```

The operator approved this source-backed replacement on 2026-08-30. R2 must
reuse the shared warranty composition and substitute this Ukrainian component;
it must not preserve the German residue or add target-specific warranty logic.

### 5.4 Live identity state

Live readback now finds:

- `JBP-2000B_US`: exact target, 11 specification rows, 9 placeholder rows, one
  successful build row;
- `JBP-2000B_JP`: target exists, no specification or placeholder rows;
- `JBP-2000B_CN`: target exists, no specification or placeholder rows;
- `JBP-2000B_EU`: exact target, no specification, placeholder, or build row.

The operator-approved additive create returned `record_id=recvtNbSrFZXfL`.
Same-record readback confirmed:

```text
Document_key = JBP-2000B_EU
项目代码 = HTP017
Model = recvg5TR1QLqKu
Region = recvg5S7r6OdTt (EU)
```

The full table moved from 32 to 33 rows and contains exactly one
`JBP-2000B_EU` record. Formula and lookup fields were not written directly.

## 6. Re-prioritized M0-M9 ownership

| Old item | R owner | Priority | Evidence-backed blocker / order reason |
| --- | --- | --- | --- |
| M5 full BP family | R1-R3 | P0 | Exact EU identity, source and market scope are closed; R1 must now prove the shared BP@INTL contract before R2 adds target data. |
| M8 compliance fragments | R1/R5e/R6 | P0 | The EU book adds `regulatory_compliance`; the family-level EU carrier and signed-fragment governance remain unresolved. UK is out of scope. |
| M9 data quality / PH / reverse gaps | R0/R5f/R6 | P0 | 35 corpus identities remain `needs_review`; the approved Ukrainian replacement must be applied during EU intake. |
| M0 ordinal/naming | R4a | P1 | Stable identity is required before legacy capability removal can stop renumbering `pNN_` sources. |
| M1 language blocks | R4b | P1 | Parameterization must follow stable names and must prove EU six-language, US three-language, and one-language books. |
| M2 App capability semantics | R5a | P1 | Operator must define TRUE/FALSE/unknown before capability gating; unknown cannot silently mean FALSE. |
| M3 MAIN@JP truth | R5b | P2 | Repair after naming/language migration while preserving the shipped no-duplicate opening. |
| M4 MAIN@CN truth | R5c | P2 | Opening/back-tail, conformity certificate, and JE-2000E/CN known-red state remain unresolved. |
| M7 contract tiering | R5d | P2 | Requires BP family evidence before category/capability/region tiering can reclaim the JE-300E fork safely. |
| M6 `page_registry` authority | R6 | P3 / exit | It must be last: encoding known-wrong legacy manifests earlier would make the registry authoritative for incorrect truth. |

Execution order remains:

```text
R0 -> R1a -> R1b -> R2 -> R3a -> R3b -> R3c -> R4a -> R4b -> R5a-R5f -> R6
```

## 7. R0 gate decision

R0 exit conditions are satisfied:

1. 58/58 corpus rows and 22/22 SKU groups reconcile exactly once;
2. M0-M9 have explicit R owners, priorities and blockers;
3. the next target is exactly `JBP-2000B_EU`, with same-record live readback;
4. the Illustrator-editable 54-page PDF is the approved EU source authority;
5. the target is EU six-language only and makes no UK market claim;
6. warranty is 3-year standard plus 2-year extended, and the sibling-sourced
   Ukrainian exchange replacement is approved.

R0 is ready for operator review and merge through PR #975. R1a starts from the
latest `main` only after that PR lands; R1b and R2 remain gated behind R1a.
