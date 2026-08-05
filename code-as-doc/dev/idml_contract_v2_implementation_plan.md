# IDML approved-layout contract v2 implementation plan

Date: 2026-08-05

Discovery evidence:
[`idml_contract_v2_discovery_2026-08-05.md`](../reviews/idml_contract_v2_discovery_2026-08-05.md)

## Phase 1 — characterization tests

Files:

- `tests/test_reference_layout_plan.py`
- `tests/test_reference_layout_rebind.py`
- `tests/test_export_idml.py`
- `tests/test_pdf_parity_contract.py`

Acceptance:

- v1 strict behavior is explicitly retained.
- v2 provenance drift, enforced-scope drift, assembly role drift, and approved
  prose fallback have failing tests before implementation.

## Phase 2 — compatibility and identity scopes

Files:

- `tools/idml/reference_layout_plan.py`
- `tools/idml/reference_layout_rebind.py`
- `tools/idml/pdf_parity_contract.py`
- `tools/check_reference_layout_pins.py`

Acceptance:

- v1 remains readable.
- v2 uses `content`, `assembly`, `style`, and `provenance` scopes.
- provenance mismatch does not activate or invalidate a v2 plan.
- public CLI flags and normalized page-plan interface remain compatible.

## Phase 3 — approved assembly hard gate

Files:

- `tools/idml/page_roles.py`
- `tools/idml/reference_layout_plan.py`
- `tools/export_idml.py` only if the plan-level gate cannot provide the full
  production context without duplicating routing logic.

Acceptance:

- every approved source page has an explicit semantic role;
- exact source-ref exceptions are schema-validated and default to none;
- ordinary unapproved targets retain the historical prose fallback.

## Phase 4 — migrate the approved target and document operations

Files:

- `docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json`
- `docs/renderers/contracts/STYLE_DEFINITION.md`
- `code-as-doc/build_doc_guide.md`
- `user-guide/hello_auto-doc.md`

Acceptance:

- reference PDF, page count, page order, languages, and composition fields are
  byte-for-byte unchanged apart from the identity-schema migration.
- the migration records the existing snapshot digest as provenance.
- operator-facing docs explain which changes require reapproval.

## Phase 5 — verification and delivery

Commands, cheapest first:

1. `python3 -m ruff check` on touched Python/tests.
2. targeted unittest modules.
3. `python3 -m unittest`.
4. `python3 -m ruff check build.py integrations tools tests scripts`.
5. `python3 tools/check_maintainability_guardrails.py`.
6. `python3 tools/check_reference_layout_pins.py`.
7. `python3 tools/check_doc_link_integrity.py`.
8. production `build.py idml` for JE-1000F US using `review-asis`.

Build outputs and local ignored phase2 snapshots remain outside Git.
