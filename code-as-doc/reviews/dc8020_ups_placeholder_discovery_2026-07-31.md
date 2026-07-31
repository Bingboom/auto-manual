# DC Input Connector and UPS Transfer-Time Placeholder Discovery

Date: 2026-07-31

Scope: Workstream W / Stage 5 item 5(a)

## Finding

The eight shared-language charging-method templates repeat the model-specific
DC input connector name four times each. The eight shared-language UPS
templates also own the product transfer time as literal prose. Seven languages
use `10 ms`; Ukrainian uses the localized `10 мс` spelling.

These values belong to the existing `Spec_Master` page-value path rather than
to reusable prose. Two semantic rows cover the concepts without introducing
legacy `tpl_*` bindings:

- `Page=charging_methods`, `Row_key=dc_input_connector`, `Slot_key=value`
  resolves to `|DC_INPUT_CONNECTOR|`.
- `Page=ups_mode`, `Row_key=ups_transfer_time`, `Slot_key=value` resolves to
  `|UPS_TRANSFER_TIME|`.

The UPS cautions that explain the product does not support `0 ms` switching
are not transfer-time values. They remain authored prose in this slice.

Japanese and Chinese templates are independent target-specific pages and are
outside the shared-copy scope named by the approved plan. They remain
unchanged.

## Implementation

1. Add fixture-only page-value rows for the complete US and EU targets and a
   dedicated minimal fixture for pt-BR and KR.
2. Replace only the `DC8020` connector spans and the one positive UPS transfer
   time in each shared-language template.
3. Extend the charging page contract and add an UPS page contract so missing
   semantic rows fail closed.
4. Characterize all sixteen resolved templates against their pre-migration
   SHA-256 values.

## Safety properties

- Resolved RST remains byte-identical in every affected language.
- No zero-millisecond caution, structured LCD row, spec row, Product Overview
  value, asset, layout parameter, or reference-layout contract is changed.
- No production Feishu/Base row is written by this PR.
- Production `页面占位参数` seed and subsequent `diff-report` evidence remain
  the operator-controlled F6 follow-up.

## Verification ladder

- Targeted placeholder, contract, and fixture tests.
- Ruff and full unittest.
- Maintainability guardrails and documentation link integrity.
- US, EU, and JP fixture-root checks.
