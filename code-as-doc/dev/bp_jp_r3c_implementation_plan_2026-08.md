# BP@JP R3c implementation plan (JBP-2000B_JP)

Date: 2026-08-31

This plan is intentionally staged from cheap and reversible checks to the
native InDesign/package proof. Every phase starts by re-reading the target
facts in `bp_jp_r3c_discovery_2026-08.md` and ends with a narrow verification
before the next phase begins.

## Phase 0 - freeze baseline and source evidence

Status: complete.

Files/evidence:

- `code-as-doc/dev/bp_jp_r3c_discovery_2026-08.md`
- `code-as-doc/dev/bp_jp_r3c_implementation_plan_2026-08.md`
- untracked local PDF text/renders under `tmp/pdfs/jbp2000b_jp_reference/`
- source-intake staging evidence under
  `reports/source_intake/JBP-2000B_JP/`

Checks:

```text
git diff --check
python tools/check_doc_link_integrity.py
```

Safety net: retain the baseline `config not found` log outside the committed
change. Do not commit scratch OCR scripts or PDF renders.

## Phase 1 - target plan, registration, and deterministic manifest

Status: complete.

Planned production files:

- `docs/manifests/product_plans/jbp2000b_jp.yaml`
- a generated target-resolved BP@JP manifest selected by
  `configs/config.bp-jp.yaml`
- `configs/config.bp-jp.yaml`
- `data/model_languages.csv`
- `data/phase2/page_registry.csv`
- tests beside `tests/test_bp_jp_skeleton.py`, config/target-resolution tests,
  and queue-resolution tests where the new exact target enters a census

Requirements:

- Product plan data is exactly `jp-v2`, optional
  `[toc, symbol_meaning, troubleshooting]`, terminal `[]`.
- The committed target manifest must be regenerated from blueprint + carrier
  catalog + region profile + product plan and verified byte-for-byte in tests.
- The config is target exact, `family_default: false`,
  `queue_requires_target_match: true`, `skeleton_family: BP`, and
  `languages: [ja]`.
- The paired host name is a substitution in config data. No renderer or recipe
  gets a model/region conditional.
- Add Japanese only to the `symbols` page registry language list; do not alter
  unrelated page ownership.

Checks:

```text
python3 -m unittest tests.test_bp_jp_skeleton tests.test_target_defaults tests.test_queue_config_resolution
python3 -m unittest tests.test_config_loader tests.test_config_pages tests.test_pilot_configs tests.test_validate_config
```

## Phase 2 - Japanese carriers and local target fixture

Status: complete. The live source approval and readback evidence is frozen
under `reports/source_intake/JBP-2000B_JP/`.

Planned production files:

- `docs/templates/page_bp/ja/` for the BP@JP carrier set
- `docs/templates/recipes/bp-jp/` for shared BP compositions only
- target rows in committed local test fixtures for specifications,
  placeholders, seven symbols, two LCD rows, and seven troubleshooting groups
- tests for page contracts, CSV rendering, identity literals, and absence of
  target branches

Requirements:

- Source prose follows the frozen HTP017 book.
- The product overview and operation pages continue through shared generated
  page contracts and recipes.
- The specification keeps Japanese `サイズ & 重量` as one displayed line and
  keeps storage temperatures in the specification composition; it does not
  create the BP@INTL storage chapter.
- Certification and the host-only compatibility sentence use shared
  `Spec_Notes` rows below the table; neither becomes target-specific page logic.
- The warranty carrier expresses three years plus two years without guessing a
  legal company name.
- Exact localized-copy payloads are emitted as review artifacts before any
  shared live row update.
- HTP017's thirteen printed troubleshooting rows are thirteen JP-only data
  rows; existing seven-row US grouping stays byte-identical.

Checks:

```text
python3 -m unittest tests.test_template_identity_literals tests.test_preface_templates
python3 -m unittest tests.test_variable_resolver tests.test_page_contracts
python3 -m unittest tests.test_csv_page_builder tests.test_csv_page_renderers
```

## Phase 3 - JP asset extraction and approval package

Status: complete. Eight approved assets are governed by
`data/asset_recipes/manual_jbp2000b_jp_assets.json` and the asset registries.

Planned files/artifacts:

- recipe data under `data/asset_recipes/` only after the source geometry is
  classified
- package-only extraction output in a task-specific scratch/output directory
- before/after review pairs and a JP asset approval manifest
- registry CSV/live rows only after per-asset operator approval

Requirements:

- Prefer text stripping with graphics preservation; escalate operators only
  when the vector structure proves it necessary.
- Verify every candidate at twelve-times zoom.
- Keep cover/full-page treatment separate from reusable text-free operation
  art.
- Perform the hash three-place sync and same-record attachment readback only
  after approval.

Checks:

```text
python3 -m unittest tests.test_asset_recipe tests.test_asset_registry
python3 -m unittest tests.test_asset_intake
```

## Phase 4 - candidate IDML target assembly

Status: complete as a candidate. The twelve-page assembly remains
`production_eligible=false` pending the final native/visual gate.

Planned production files:

- `docs/renderers/contracts/target_assembly/jbp2000b_jp_v1_candidate.json`
- any target-neutral component-instance data required by existing shared
  composition types
- candidate assembly/config tests and target projection tests

Requirements:

- Twelve physical pages must map to the R3a printed-page ledger.
- Reuse existing composition types; new geometry is target assembly data.
- The two HTP017 co-page facts not globally semantic (box contents + overview,
  troubleshooting + spec) live in candidate assembly composition mapping, not
  the skeleton resolver.
- Candidate state remains non-production.

Checks:

```text
python3 -m unittest tests.test_idml_target_assembly_plan tests.test_idml_target_assembly_render tests.test_idml_target_assembly_scaffold
```

## Phase 5 - real entrypoint and four-renderer reconciliation

Status: in progress. `build.py check` and production IDML are green at
12 pages, 13/13 source pages matched, and zero skipped raw blocks. The final
`build.py all` plus cross-target regression ladder remains Phase 7 work.

Required commands:

```text
python3 build.py check --config configs/config.bp-jp.yaml --model JBP-2000B --region JP
python3 build.py all --config configs/config.bp-jp.yaml --model JBP-2000B --region JP
python3 build.py idml --config configs/config.bp-jp.yaml --model JBP-2000B --region JP
```

The four renderers are LaTeX/PDF, Word, HTML, and IDML. Record actual page
counts, source/assembly identity, glyph/font checks, and any renderer-specific
warnings. Run the US and MAIN JP regressions after the target passes.

## Phase 6 - native InDesign and twelve-page visual acceptance

Status: in progress. Shared Connections and Troubleshooting+Specifications
geometry now reopen with zero overset stories and zero overset table cells.
The bundled Japanese static TTF also reached zero missing-font findings before
the current locked-host interruption. A fresh native run, PDF/X export, and
the twelve-page visual ledger are still required.

Artifacts:

- packaged IDML opened, saved, and exported in native InDesign
- native preflight report
- twelve-page reference-versus-built contact sheet and per-page findings ledger
- final native PDF

Acceptance:

- 12/12 physical pages present and ordered correctly.
- Japanese glyphs, symbols, DC marks, numeric warranty badges, page numbers,
  and subscripts are legible with no missing-font substitution.
- Shared compositions align to the reference at first-pass production quality;
  remaining measured deviations are documented and repaired at the shared
  component or target-assembly data layer.

## Phase 7 - clean-room package, PR, merge, and checklist backfill

Status: pending Phase 6 completion.

Required validation ladder:

```text
python -m ruff check build.py integrations tools tests scripts
python -m unittest
python -m mypy tools/utils
python tools/check_maintainability_guardrails.py
python tools/check_doc_link_integrity.py
python build.py check --config configs/config.bp-jp.yaml --model JBP-2000B --region JP
python build.py check --config configs/config.bp-us.yaml --model JBP-2000B --region US
python build.py check --config configs/config.ja.yaml --model JE-1000F --region JP
```

Package from a clean worktree/clone, verify the ZIP contains the IDML package,
native PDF, font/asset links allowed by policy, manifest, checksums, and visual
evidence, then open a PR into `auto-manual/main`. MA-023 may merge the R3c PR
only after every check is green, no review requests changes, no thread remains
unresolved, and all source/legal/asset approvals used by the result are proven.
After merge, refresh PR #974 from `main` and backfill R3c evidence; #974 remains
Draft for later checklist phases.
