# BP@INTL six-language carrier provenance (2026-08)

## Scope

This record is the source and normalization ledger for Milestone M R1b. The
change prepares family-owned front matter and the `de` / `it` / `uk` body
carriers before the second target is onboarded.

R1b does not add an EU config, region profile, resolved manifest, target
assembly, asset enrollment, or live source-table row. Those remain R2 target
data and retain their operator gates.

## Approved source authority

- File: `Jackery Battery Pack 2000 User Manual (JBP-2000B) EUUK V2.0-2026-08-03.pdf`
- Material number: `16-0102-000400`
- SHA-256: `0a240f2653ab4135b354e0d697e692842027689de578a72c1c802174a644c1c6`
- Physical pages: 54
- Trim: 368.754 x 524.659 pt
- Language sequence: `en`, `fr`, `es`, `de`, `it`, `uk`
- Market ruling: EU six-language only. `uk` means Ukrainian; the filename's
  `EUUK` token is not a UK-market or UK-legal claim.

Source-page mapping:

| Carrier evidence | PDF physical pages | Printed folios |
| --- | ---: | ---: |
| Six-language preface | 2-3 | unnumbered |
| Six-language contents | 4-5 | unnumbered |
| German body | 30-37 | 25-32 |
| Italian body | 38-45 | 33-40 |
| Ukrainian body | 46-53 | 41-48 |
| EU RED declaration | 54 | unnumbered |

## Shared-data boundary

The US and EU lines pair the battery pack with the same host hardware under
different regional product names:

| Region | Full name | Short name |
| --- | --- | --- |
| US | Jackery HomePower 2000 Plus | HomePower 2000 Plus |
| EU | Jackery Explorer 2000 Plus | Explorer 2000 Plus |

The shared connection, operation, and charging carriers therefore use
`BP_HOST_PRODUCT_NAME` and `BP_HOST_PRODUCT_SHORT_NAME`. The US config binds
its existing shipped values; R2 will bind the EU names as target data. No page
or renderer checks a model, project code, or region to choose the name.

The language-specific connection-locking figures follow the same boundary:
the `de`, `it`, and `uk` carriers consume
`BP_CONNECTION_LOCKING_ASSET_DE`, `BP_CONNECTION_LOCKING_ASSET_IT`, and
`BP_CONNECTION_LOCKING_ASSET_UK`. R1b defines the carrier contract only; R2
must bind those values to enrolled assets when it adds the EU target assembly.

## Recorded source normalizations

The source PDF remains the authority for wording and sequence, but four
obvious cross-language residues are not promoted into family components:

1. German TOC `PANTALLA LCD` is normalized to the German body heading
   `LCD-ANZEIGE`.
2. Italian TOC `SICHERHEITSVORKEHRUNGEN BEI DER` is normalized to
   `PRECAUZIONI DI SICUREZZA`.
3. Italian TOC/body `COME SI USA` is normalized to the semantic chapter title
   `COLLEGAMENTI`; the blueprint slot remains `connections`.
4. Italian operation copy `ucita` is normalized to `uscita`.

The Ukrainian warranty page contains a German `Umtausch` heading and exchange
paragraph. It is replaced by the operator-approved HTE154/HTE152 Ukrainian
variant already represented in the shared corpus:

- heading: `Обмін`
- first sentence begins: `Jackery замінить (за рахунок Jackery)`

This is an approved sibling-source substitution, not inferred translation.

## Snippet decision

Only the Italian long-storage advisory is registered as a new
`battery_long_storage_advisory` variant. It is byte-exact with the existing
Italian corpus copy. The approved German and Ukrainian BP paragraphs differ
from their host-manual copies, so they remain explicit in their BP carriers
and are not registered by similarity.

## R1b acceptance contract

- `de`, `it`, and `uk` each provide all 8 family body carriers.
- The six-language preface and contents use the existing preface/TOC
  composition macros and contain no target ID or project code.
- The synthetic six-language plan resolves from the existing
  `skeleton_id=bp-intl`.
- The frozen JBP-US resolved manifest remains SHA-256
  `94e7276ab3f20bbd804eb66864b360dd5780c886b3d29ed5377161162da5cc8b`.
- Base/head JBP-US prepared `page/` and `generated/` trees are byte-identical.
- No `JBP-2000B_EU` or `HTP017` branch is added under `tools/` or
  `docs/renderers/`.
