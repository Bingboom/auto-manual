# IDML App Page Ownership Discovery — 2026-07-31

## Scope

Workstream W, Stage 4a item 13 replaces the target-named
`is_je1000f_us_*` App-page predicates with approved-contract ownership. The
change must preserve the current JE-1000F/US English, French, and Spanish
production composition while making a future approved target opt in through
data rather than a Python branch.

## Current boundary

- `tools/idml/asset_contracts.py` hardcodes model, region, governed languages,
  and the `12_app_setup_placeholder` stem in two predicates.
- `tools/bundle_asset_finalize.py` calls that predicate before Manual IR and
  the normalized reference plan exist, so the same branch decides whether the
  two hidden native-IDML assets are frozen into the bundle.
- `tools/idml/prose_flow.py` and `tools/idml/reference_story_flow.py` call the
  plan variant to enable App figure promotion, the approved page split, and
  App story-frame allowances.
- The approved reference contract already owns the exact target, source-page
  order/language, and the `editable_components.app_add_device` contract, but it
  does not currently name which source pages own that component.
- Existing tests prove the old target/stem branch fails closed, but they also
  encode the JE-1000F/US name and therefore cannot prove that a new approved
  target works without a code edit.

## Contract shape

Add an ordered `page_owners` list beneath
`idml_contract.editable_components.app_add_device`. Each value is an exact
`pages[].source_ref` already covered by the approved plan. Validation requires
the list to equal the source pages that contain the Add Device image, including
language order. The field is ownership metadata only: it does not change
`composition_id`, physical page range, source identity, asset identity, or
geometry.

The finalized-bundle path resolves the exact registered target contract from
`reference_layout_registry.json` and passes it to the native asset requirement
resolver. The renderer path consumes the same approved contract carried by the
normalized page plan. Both paths match exact source refs plus the contracted
page language; neither infers ownership from model, region, localized title,
or filename regex.

## Safety net first

1. Replace target-named predicate tests with contract fixtures that prove:
   - the three current App source refs own the component;
   - a synthetic model/region owns a differently named page without Python
     changes;
   - missing, malformed, unapproved, wrong-language, and unowned-page inputs
     fail closed;
   - asset freezing and prose promotion consume the same ownership decision.
2. Add approved-plan validation tests for missing, duplicate, unknown, and
   out-of-order App owners.
3. Add a maintainability regex that rejects target-scoped IDML page-predicate
   identifiers such as `is_je1000f_us_app_reference_page` under `tools/idml`.

## Implementation plan

1. Add generic registered-contract lookup and component-page ownership helpers
   in `tools/idml/asset_contracts.py`.
2. Validate `app_add_device.page_owners` against Manual IR in
   `tools/idml/control_labels.py`.
3. Route bundle finalization, prose promotion/page splitting, and reference
   story placement through the generic helpers.
4. Add the three current source refs to the approved JE-1000F/US contract.
5. Update the IDML module map and operator-facing contract notes, then record
   the Workstream W maintenance entry.
6. Run targeted tests, Ruff when available, the full unit suite,
   maintainability/doc-link checks, the JE-1000F/US check build, and
   `git diff --check`.

## Non-goals

- No reference-layout rebind or source/hash mutation.
- No page-binding, composition, page-count, asset-byte, or geometry change.
- No generalized page-role/assembly coverage table; that is Stage 4a item 14.
- No ExtendScript batch-loop work; Stage 4a item 12 remains design-Mac gated.
