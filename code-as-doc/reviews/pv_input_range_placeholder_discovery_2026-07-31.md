# PV Input Range Placeholder Discovery

Date: 2026-07-31

Scope: Workstream W / Stage 5 item 4(a)

## Finding

The solar-charging warning in eight shared-language templates owns the same
safety-critical PV input range as literal prose. The affected templates are
English, French, Spanish, Brazilian Portuguese, German, Italian, Ukrainian,
and Korean. Their punctuation and spacing differ by language, so the source
value must preserve each current byte sequence rather than normalize it.

The existing Spec_Master page-value path already supports a semantic row with
`Row_key=pv_input_range` and `Slot_key=value`. It resolves that row to
`|PV_INPUT_RANGE|`; no new `tpl_*` compatibility binding or renderer behavior
is required.

Japanese and Chinese templates contain independently localized range text but
are outside the eight-copy scope named by the approved plan. They remain
unchanged in this slice.

## Implementation

1. Add fixture-only page-value rows for the US, EU, pt-BR, and KR target
   families, preserving all eight current localized values exactly.
2. Replace only the literal range span in each shared-language template with
   `|PV_INPUT_RANGE|`.
3. Add a page contract that requires both the runtime placeholder and its
   semantic page-value row.
4. Characterize all eight resolved templates against their pre-migration
   SHA-256 values.

## Safety properties

- Resolved RST remains byte-identical in every affected language.
- Missing source data fails closed through the page contract and unresolved
  placeholder checks.
- No production Feishu/Base row is written by this PR.
- No JP/CN template, layout parameter, IDML composition, approved reference
  layout, asset, or public CLI is changed.
- The production `页面占位参数` seed and subsequent diff-report remain the
  operator-controlled F6 step recorded in the scaling plan.

## Verification ladder

- Targeted placeholder, contract, and fixture tests.
- Ruff and full unittest.
- Maintainability guardrails and documentation link integrity.
- US and JP fixture-root baseline checks, plus affected family checks where
  the committed fixture has a complete target.
