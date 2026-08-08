# Cross-Renderer Component Boundary

Updated: 2026-08-08

> **Architecture boundary only.** This legacy filename is retained so existing
> links do not break. It is not a second style specification, component list,
> or migration roadmap.

## 1. Owning documents

- The sole human-readable style specification is
  [`STYLE_DEFINITION.md`](../../docs/renderers/contracts/STYLE_DEFINITION.md).
  It owns component vocabulary, visual intent, source structure, and the four
  renderer projections.
- The machine-readable semantic contract is
  [`manual_style.yaml`](../../docs/renderers/contracts/manual_style.yaml).
- The active migration order, evidence, and completion checklist are in
  [`style_component_contract_v2_plan.md`](../dev/style_component_contract_v2_plan.md).
- Long-term system boundaries remain in
  [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md).

Do not add component definitions, renderer values, debt lists, or execution
phases here. Update the owning document above instead.

## 2. Stable architecture boundary

Cross-renderer convergence means sharing **semantic identity, component slots,
asset roles, token roles, and page roles**. It does not mean sharing output
syntax or coordinates.

- Web, LaTeX/PDF, IDML, and Word remain independent adapters.
- Responsive Web preserves information hierarchy and visual language; it does
  not emulate fixed PDF pagination.
- PDF and IDML may use fixed geometry when it is target-scoped,
  parameterized, registered, and regression-tested.
- Word preserves component structure and editability without becoming a
  fixed-page replica.
- Renderer or platform limits are recorded as constraints; reviewed
  target/model/language differences are recorded as approved variants. The
  taxonomy and lifecycle are normative only in `STYLE_DEFINITION.md`.
- Approved Web composite assets continue to enter through the frozen,
  hash-verified asset manifest. A component contract may reference those asset
  roles but must not replace the asset-provenance pipeline.

## 3. Change routing

| Change | Owning location |
|---|---|
| Component meaning, source shape, visual invariant, four-output mapping | `STYLE_DEFINITION.md` |
| Machine binding or conformance state | `manual_style.yaml` and its validator |
| Shared fixed-page numbers | `data/layout_params.csv` |
| Renderer-specific projection | The owning Web, LaTeX, IDML, or Word adapter |
| Work order, PR evidence, completion state | `style_component_contract_v2_plan.md` |

Review this boundary only when renderer ownership or the meaning of
cross-renderer sharing changes. Component additions and migration sequencing
do not update this file.
