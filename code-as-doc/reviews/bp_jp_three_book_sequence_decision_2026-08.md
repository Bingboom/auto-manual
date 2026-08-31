# BP@JP three-book sequence decision (R3a, 2026-08)

## 1. Decision

The three shipped Japanese battery-pack books stay in one `BP@JP` skeleton
cell. They do not justify a second product skeleton and they must not be
forced into `BP@INTL`.

The cell needs two data-owned order profiles:

- `jp-v2` is the canonical base, proven jointly by HTP015 and HTP017;
- `jp-v1` is the legacy house-style version used by HTP007. It moves
  `specifications` to the opening and the safety carrier to the terminal
  position, and uses the older warranty component.

This is not a target exception. `house_style_version` already owns order
profile and safety placement in the approved architecture. A model-, title-,
filename-, or page-number-specific branch would violate that contract.

HTP017 `JBP-2000B_JP` remains the first implementation target. Its exact live
identity already exists, its 12-page book exercises the `jp-v2` core without
the HTP015-only mounting chapter, and its product-neutral JBP-2000B assets can
reuse the seven repository rows scoped `ALL` after a separate asset review.

R3a is report-only. It creates no skeleton, config, region profile, manifest,
template, asset enrollment, source-table row, or approved reference-layout
binding.

## 2. Frozen source evidence

The page-level evidence is recorded in the
[42-page physical ledger](bp_jp_three_book_sequence_decision_2026-08.csv).
All three PDFs were visually inspected from rendered pages; text extraction
was used only as a secondary heading/copy check.

| Corpus member | Project / cover model | PDF pages | Page size | Illustrator producer | SHA-256 |
| --- | --- | ---: | --- | --- | --- |
| HTP015 Japanese | HTP015 / `JBP-1000B-WH` | 20 | 368.787 x 524.692 pt | Illustrator 30.6 | `3aa6c0039b413716274089e5335dc2ce5853264dca4d7b0a6e5e110b6b0b302c` |
| HTP007 Japanese | HTP007 / `JBP-5000A` | 10 | 368.754 x 524.659 pt | Illustrator 26.0 | `cdd40510647f7d45a80f58eccddba32754346edeaede760c993ca6670af6bfc8` |
| HTP017 Japanese | HTP017 / `JBP-2000B` | 12 | 368.754 x 524.659 pt | Illustrator 30.1 | `f7830bf9fb96d9a3e36737bad5196bbfac2d262eaef642f3406fe77eecd02b0b` |

The corpus audit's raw topic rows were rechecked against the physical pages.
Two normalization details matter for the skeleton decision:

1. HTP007's final `使用上のご注意` is the safety carrier in a different
   position, not a second safety topic that should coexist with
   `safety_info`.
2. Battery recycling copy exists in all three books. HTP015 and HTP017 absorb
   it into the symbol/safety composition; HTP007 mounts it under the opening
   specifications. It is a JP fragment with a version-owned mount point, not
   an independent blueprint chapter.

## 3. Physical sequence comparison

### 3.1 JP v2 members

HTP015 and HTP017 share the same semantic spine:

`cover -> toc -> safety_info -> symbol_meaning -> box_contents ->
product_overview -> lcd_display -> operation -> [installation] ->
connections -> charging -> troubleshooting -> specifications -> warranty ->
[back_cover]`

Square brackets are product/terminal selections, not required topics.

| Surface | HTP015, 20 pages | HTP017, 12 pages | Ruling |
| --- | --- | --- | --- |
| Opening | cover, TOC, front safety, symbols | same | canonical `jp-v2` opening |
| Product core | box, overview, LCD, operation | same | required BP@JP core |
| Mounting | six-page installation/vertical-mounting sequence | absent | optional product feature; `vertical_stand_mounting` stays absorbed into `installation` |
| Connections/charging | both present in the same order | same | required BP@JP core |
| Fault/spec tail | troubleshooting then specifications | same; co-page on PDF p10 | canonical `jp-v2` tail order |
| Warranty | `保証について`, three years plus two-year extension | same component and policy | `jp-v2` warranty variant |
| Terminal | QR-only p20 | no separate terminal page | target assembly choice, not region-wide truth |

The extra eight HTP015 pages are explainable: seven pages carry the optional
installation/mounting sequence, and one is the QR-only terminal page. Both
books already use two warranty pages. The user journey is not a new skeleton.

### 3.2 JP v1 member

HTP007's physical order is:

`cover -> specifications -> box_contents -> product_overview -> lcd_display ->
operation -> connections -> charging -> warranty -> safety_info`

It is not a pure Boolean deletion from the `jp-v2` line: specifications move
from the tail to the opening and safety moves from the opening to the terminal
position. The warranty title and policy also differ (`保証サービス`, five
years, `株式会社 Jackery Japan`) from the newer three-plus-two-year component.

Those differences match the architecture's `house_style_version` ownership:
order profile, safety-block placement, and warranty/legal convention. HTP007
therefore stays `BP@JP@jp-v1`; it does not create a sixth skeleton cell.

## 4. Superset and Boolean-removal result

The nine-slot intersection across all three books is:

`cover`, `box_contents`, `product_overview`, `lcd_display`, `operation`,
`connections`, `charging`, `specifications`, `warranty`.

The corpus-proven BP@JP slot universe adds required `safety_info` plus five
selectable semantics: `toc`, `symbol_meaning`, `installation`,
`troubleshooting`, and the terminal `back_cover` form. `safety_info` is
required semantically but its position/carrier variant is version-owned; the
other five are optional assembly choices.

| Semantic | Blueprint/plan ownership | Evidence |
| --- | --- | --- |
| `cover` | required front slot | 3/3 |
| `toc` | optional front slot | HTP015/HTP017 only |
| `safety_info` | required; order/carrier selected by `house_style_version` | front in v2, terminal in v1 |
| `symbol_meaning` | optional body slot | HTP015/HTP017 only |
| `box_contents` | required body slot | 3/3 |
| `product_overview` | required body slot | 3/3 |
| `lcd_display` | required body slot | 3/3 |
| `operation` | required body slot | 3/3 |
| `installation` | optional product-feature slot | HTP015 only; includes absorbed vertical mounting |
| `connections` | required body slot | 3/3 |
| `charging` | required body slot | 3/3 |
| `troubleshooting` | optional body slot | HTP015/HTP017 only |
| `specifications` | required; order selected by `house_style_version` | tail in v2, opening in v1 |
| `warranty` | required; copy/legal variant selected by `house_style_version` | 3/3, two policy variants |
| `back_cover` | optional target terminal selection | HTP015 only |

`battery_recycling` is a mounted JP fragment and does not enter the slot
universe. `preface_important`, `storage`, `ups_mode`, `extra_battery`, and
`regulatory_compliance` have no BP@JP book-level evidence and must not be
copied from `BP@INTL`.

The only stable semantic co-page group across all three members is
`[lcd_display, operation]`. Other same-page combinations vary with page budget
and remain layout evidence rather than composition constraints.

## 5. Generic mechanism gaps before BP@JP data

The current three-layer resolver cannot truthfully encode this decision:

1. It accepts one linear blueprint order only; there is no data carrier for a
   `house_style_version` order profile.
2. `requirement: optional` is explicitly rejected because the product plan
   has no opt-in/opt-out semantics.
3. `terminal_slots` is region-profile-owned. The three books prove that two
   targets in JP can select different terminal forms, so a single JP region
   profile cannot decide this truthfully.
4. The current capability table has no wall/vertical-installation fact. All
   JBP-2000B_JP capability values are false, so using one of them as a proxy
   would corrupt business meaning.

R3b must close these as target-neutral plan mechanics before committing a
BP@JP manifest:

- add a version/order-profile carrier keyed by declared house-style version;
- implement product-plan selection for optional slots, including target
  terminal selection, without a model or region branch;
- represent HTP015 installation with a truthful product feature binding, not
  an unrelated existing capability;
- keep emitted slot IDs stable across both order profiles and prove that
  existing BP@INTL US/EU resolution is byte-identical.

If the mechanism needs resolver code, it is the mechanism-first part of R3b.
The later `JBP-2000B_JP` target PR must contain target data only.

## 6. Live identity and source readiness

Read-only Base queries were repeated on 2026-08-30 PT with
`lark-cli 1.0.78 --profile prod --as bot`. No record was written.

| Item | Live/read-only result |
| --- | --- |
| Document-key master | 33 rows, revision 183 |
| HTP017 JP identity | `JBP-2000B_JP`, record `recvp853V2kywb` |
| Linked model / region | model `recvg5TR1QLqKu`; JP region `recvg5S7r6Jskl` |
| Project lookup | `HTP017` |
| Linked build rows | none |
| Specification rows for `JBP-2000B_JP` | 0 |
| Placeholder rows for `JBP-2000B_JP` | 0 |
| HTP015 JP identity | absent from the complete 33-row master read; keep `needs_review` |
| HTP007 JP identity | absent from the complete 33-row master read; keep `needs_review` |
| `model_languages.csv` | no `JBP-2000B_JP` row |

The live asset registry has 72 rows and zero JBP/HTP-scoped records. The
repository snapshot is intentionally ahead of that table: it contains 32
JBP-2000B rows (7 `ALL`, 14 US, 11 EU). Only the seven `ALL` rows are initial
JP reuse candidates. JP cover, connection/locking, charging, and terminal QR
art have not been enrolled or approved.

The three local source PDFs are usable layout/asset authorities, but R3a does
not convert that availability into registry approval.

## 7. Product, host, warranty, and legal evidence

| Project | Product display name in source | Paired host wording in source | Warranty/legal evidence |
| --- | --- | --- | --- |
| HTP015 | `Jackery Battery Pack`; model `JBP-1000B-WH` | `Jackery SlimPower H1` | `保証について`; 3 years + 2-year extension; Japan-only; support `jackery.jp@jackery.com` |
| HTP007 | `Jackery Battery Pack 5000 Plus`; model `JBP-5000A` | `Jackery ポータブル電源 5000 Plus` | `保証サービス`; 5 years; names `株式会社 Jackery Japan`; support `jackery.jp@jackery.com` |
| HTP017 | `Jackery Battery Pack 2000`; model `JBP-2000B` | `Jackery ポータブル電源 2000 Plus` | same v2 3+2 component as HTP015; Japan-only; support `jackery.jp@jackery.com` |

The HTP017 Japanese source wording is the authority for its host display
name. The EU/US `Explorer 2000 Plus` versus `HomePower 2000 Plus` ruling does
not authorize replacing the Japanese wording.

R3c still needs operator confirmation of the exact production product name,
legal entity field, warranty component version, and asset set before any live
source or asset write.

## 8. R3b/R3c handoff

### R3b: mechanism and skeleton data

1. Land the target-neutral order-profile and optional product-plan mechanism.
2. Add `skeletons/bp-jp/{blueprint.yaml,slot_templates.yaml}` with the slot
   universe above and one JP region profile for language/legal carrier facts.
3. Encode `jp-v2` and `jp-v1` as declared data profiles; do not duplicate
   blueprints.
4. Resolve synthetic plans for all three audited books and rerun the
   Boolean-removal/ordering assertions.
5. Prove BP@INTL US/EU manifests and existing MAIN JP defaults unchanged,
   including the known `target_defaults` ambiguity gate.

### R3c: first target and native reconciliation

1. Confirm the HTP017 production name/legal/warranty inputs.
2. Stage, present, and separately approve Japanese specification,
   placeholder, localized-copy, and asset rows; perform same-record readback
   for every live write.
3. Add only target registration, `ja` language/assembly data, necessary
   approved assets, and candidate target-assembly data.
4. Build the 12-page target through all four renderers, native InDesign,
   visual comparison, and clean-room ZIP reopen.
5. Keep the result `candidate` until approved reference-layout promotion is
   separately authorized.

## 9. No-target-logic and rollback evidence

- R3a adds only this Markdown report and its CSV ledger.
- No hit for `JBP-2000B_JP`, HTP015, HTP007, or JP page numbers is added under
  `tools/` or `docs/renderers/`.
- No Feishu/Base record, asset-registry record, source snapshot, config,
  manifest, template, build output, or reference-layout contract is changed.
- Removing the two R3a evidence files reverts the entire slice.
