# Released PDF content parity and authority debt

Authority: V2.0 EU-UK-2026-06-18, SHA-256
`0b4424aff74b3feee08208b1fc0e1d3dde0d2400315ccb72475f6cb2b4d11cfe`.
English physical pages 6–22; French physical pages 23–39.

## Correction scope

- EN 6 / FR 23: restore the PDF's accessory recommendation/sale safety condition.
- EN 7 / FR 24: omit the battery/accumulator disposal row absent from this
  release; restore the French no-smoking/open-flame instruction.
- EN 9–10 / FR 26–27: restore LCD table mapping, English low-battery threshold,
  French quiet-charging description and full ASI label. The original LCD map
  is already correct and is retained, not re-extracted.
- EN 14 / FR 31: place LCD screen before Output Resume and key combinations;
  remove the unsupported disabled-by-default/App activation statement.
- EN 18 / FR 35: restore the imperial F6 clearance and USB-only F9 instruction.
- EN 19 / FR 36: restore the DC8020 12 A maximum qualifier and separate native
  USB-C 30 W / 100 W rows; localize the French temperature and cycle-life labels.
- EN 20: restore the warranty interpretation wording.
- EN 22 / FR 39: restore App step number 2.5.

The reviewed RST carriers are the authoritative build surface for this
candidate (`review-asis`). Frozen CSV values are aligned where the correction
is locale-specific. Shared CSV row identifiers, asset filenames and other
language columns remain historical source identifiers, not printed numbering
or approval of other locales. In particular, LCD displayed numbering belongs
to the reviewed table; do not regenerate it from the historical CSV numbers.

## Authority-side inconsistencies retained

- EN 10 / FR 27 print `22` for both High Temperature and Low Temperature.
  The reviewed table preserves the duplicate; do not invent a new sequence.
- FR 27 labels row 20 `Indicateur de Batterie Faible` despite describing a
  discharge timer. Preserve the released label pending an approved source
  revision. This is not evidence that the device has a second low-battery
  function.
- Obvious non-semantic PDF typos (for example `PPress`, `LED Lignt`, duplicated
  `5.`, and `ssimultanément`) are not deliberately introduced into Web copy.

These notes record source provenance and known debt, not completed RTD
publication. Fresh builds, rendered content checks and immutable final-ref
evidence remain release gates. No online source-table changes are made by
this correction.
