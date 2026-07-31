# IDML East Asian Width Estimation Discovery — 2026-07-31

## Decision

Workstream W / Stage 5 item 11 replaces the renderer's duplicated
`len(text) / (0.52 × point size)` estimates with one deterministic contract in
`tools/idml/line_metrics.py`.

The build remains independent of workstation font files. Narrow characters
retain each call site's existing average-width ratio, Unicode East Asian Width
`W` and `F` characters occupy one em, combining marks occupy zero width, and
ambiguous-width (`A`) characters remain narrow. Keeping `A` narrow prevents a
host locale or font substitution from changing generated geometry.

## Consolidated Consumers

The shared estimator now serves:

- production story and flow-story height budgeting;
- Meaning of Symbols row balancing and continuation fitting;
- warning, tail-warning, FCC, operation-panel, and emphasis components;
- LCD row allocation and editable LCD/key-combination panels;
- troubleshooting-table word wrapping and H1/prerequisite width fitting.

Components with shipped-font-specific metrics, such as the exact Gilroy
callout-width table, remain specialized. They were not generic `0.52` line
estimates and changing them would erase reviewed optical calibration.

## Compatibility Evidence

- Narrow-only text preserves the former integer character capacity exactly.
- Unit tests prove fullwidth/Han weighting, combining-mark handling, explicit
  line breaks, deterministic ambiguous-width behavior, and higher CJK story
  budgets for equal character counts.
- English, French, Japanese, and Korean composed golden IDML packages remain
  byte-for-byte unchanged: the localized fixture copy does not cross a current
  page or fixed-row threshold, while future longer copy now receives the
  correct conservative budget.
- No layout parameter, page binding, font resource, or reference-layout plan
  changes. Existing Latin approved references therefore need no rebind.

## Boundary

This is a deterministic preflight estimate, not native font shaping. InDesign
finalize and parity review remain authoritative. Stage 5 item 12 separately
adds the real Japanese smoke export and recorded `check_idml` acceptance.
