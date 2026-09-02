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

Status: complete. All three entrypoints exit 0 against the **live-synced**
`data/phase2` mirror, and the cross-target regression ladder is green.

Required commands, as run:

```text
python3 build.py check --config configs/config.bp-jp.yaml --model JBP-2000B --region JP   # exit 0
python3 build.py all   --config configs/config.bp-jp.yaml --model JBP-2000B --region JP   # exit 0, 0 ERROR/Traceback
python3 build.py idml  --config configs/config.bp-jp.yaml --model JBP-2000B --region JP   # exit 0
```

Real-data prerequisite, now satisfied: these ran without `--data-root`. The
committed mirror carried zero `JBP-2000B_JP` rows, so the entrypoints only
passed against `tests/fixtures/phase2` and the branch's green tests proved
nothing about the production data path. `build.py sync-data` was run with the
host's phase2 credentials and the mirror now carries the 17 `JBP-2000B_JP`
`Spec_Master` rows, matching the 17/17 staging readback in
`reports/source_intake/JBP-2000B_JP/source_data_approval_2026-08-31.json`.
`data/phase2/*` is gitignored, so the sync leaves no repo footprint.

Measurement provenance: every number below was taken on a tree carrying the
`lang_jp_` prefix fix, i.e. the state this branch is on now that that fix has
landed. It matters because the alternative — the `lang_ja_` spelling — makes the
seven measured Japanese rows unreachable and silently substitutes the shared
Latin fallbacks. The built IDML is the proof: its inbox card frames measure
145.0pt and the content frames 119.0pt, and it contains no 108.0/82.0 fallback
frame at all.

Four-renderer reconciliation. Each entrypoint cleans the output directory, so
the artefacts were measured per run rather than all at once:

| Renderer | Result |
| --- | --- |
| LaTeX/PDF | 4,061,645 bytes, **15 pages**, 0 missing-glyph findings (U+FFFD / .notdef) |
| Word | 6,110,910 bytes |
| HTML | 48,396 bytes |
| IDML | 116,826 bytes, **12 `<Page>` elements across 12 spreads** |

Assembly identity: `target={model: JBP-2000B, region: JP, languages: [jp]}`,
`status=candidate`, `production_eligible=false`, `physical_page_count=12`,
13 declared pages. Page plan `physical=12 matched=13/13 (100.0%) placed=0`;
IR `pages=13 blocks=79 skipped_raw=0`.

PDF fonts embed `HBManualSansJP-Regular` and `NotoSansJP` (Regular, Medium,
Bold, DemiLight) alongside the Gilroy identity faces. IDML declares
`HB Manual Sans JP (OTF)`, `Noto Sans Symbols`, `Noto Sans Symbols2`.

The 15-page PDF against 12 IDML pages is expected, not a defect: the LaTeX
projection paginates on its own, while the twelve-page ledger is the InDesign
assembly contract. Phase 6's acceptance gate is 12/12 on the native result.

Cross-target regressions, all `exit 0` / `[check] OK` on the same synced
mirror:

```text
python3 build.py check --config configs/config.bp-us.yaml --model JBP-2000B --region US
python3 build.py check --config configs/config.ja.yaml    --model JE-1000F  --region JP
python3 build.py check --config configs/config.us.yaml    --model JE-1000F  --region US
```

Two host-environment findings from this round, neither blocking but both worth
knowing before anyone repeats the sync:

- `FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID` points at the build-queue table
  (`Document_ID`, `钉钉上传节点`, `Git_ref_check`) in both local env files, so
  `sync-data` exports 0 rows and would blank `data/model_capabilities.csv`.
  Restored by hand here; the env value needs a fix at the source.
- The exporter writes 11 `asset_registry` note fields unquoted where the
  committed file quotes them. Values are byte-identical once parsed, so this is
  cosmetic churn; also restored rather than shipped.

## Phase 6 - native InDesign and twelve-page visual acceptance

Status: in progress. **The operator ran native InDesign on 2026-09-01 and
reported that the styling does not yet meet the final acceptance standard.**
The specific findings are on the operator's host and are not reproduced here.

The three "zero" measurements previously recorded in this section — zero
overset stories, zero overset table cells, zero missing-font findings — are
**stale and must not be relied on**. They predate #985, #989 and #992, and the
last two changed exactly the things they measured: #989 rerouted the data
stories through the shared font sink, and #992 restored the `lang_jp_` prefix,
which moves the inbox card from 108.0pt to a measured 145.0pt and changes the
warranty lead and body baseline. Overset is a function of that geometry.
Overset cannot be re-measured off-host: `tools/indesign_finalize.py::_overset_pages`
reads a report produced by the JSX **inside** InDesign, so only a native run
can settle it.

What the pipeline side can prove was re-measured on the current bytes, and is
recorded below so the next native round starts from facts rather than from the
stale trio. A fresh native run, PDF/X export, and the twelve-page visual ledger
are still required.

### Pipeline-side mechanical acceptance (current bytes, no InDesign)

Measured against the same checks recorded for JBP-2000B_US in
[`../reviews/jbp2000b_us_s6_reconciliation_2026-08.md`](../reviews/jbp2000b_us_s6_reconciliation_2026-08.md)
so the two targets stay comparable.

| Check | Result |
| --- | --- |
| Physical pages = assembly contract | 12 = 12 |
| Source page match | 13/13 (100.0%) |
| Trim size | 368.787 x 524.693 pt (130.10 x 185.10 mm) |
| Package shape | 12 spreads / 84 stories |
| Content loss | `skipped_raw = 0` |
| Filenames rendered as body text | 0 |
| Linked assets | 31 collected into the handoff package, 0 missing |
| Delivery package | builds clean: 7,373,480 bytes, 50 entries, trace trio present |
| Fonts requested by the IDML | `Gilroy`, `HB Manual Sans JP (OTF)`, `Noto Sans Symbols`, `Noto Sans Symbols2` |
| `Arial Unicode MS` host-font fallback | absent — #989 holds |

### The font finding, which bears directly on styling acceptance

All **72** style definitions in the package declare `Gilroy` as their base
font, and the Japanese runs override to `HB Manual Sans JP (OTF)` at run level.
Measured on the current package:

- 255 runs carry the Japanese override; **0 CJK runs fall back** to a font
  without CJK coverage, so #989's sink is complete for Japanese text.
- **202 runs inherit the style default, i.e. Gilroy.** They are the brand and
  Latin/numeral content: `Jackery` (30), the bullet `•` (24), `2000 Plus` (12),
  page numbers (`03`/`04`/`08`), units (`AC`, `DC`, `LCD`, `36.8V-57.6V`) and
  list ordinals.

`Gilroy` is commercially licensed (Radomir Tinkov) and is **deliberately not
shipped** in `Document fonts/` — `STYLE_DEFINITION.md` §8.1 records the policy,
and the package's own `fonts_manifest.md` lists it as commercial while the other
four families ship under OFL. A host without Gilroy installed therefore
substitutes it silently, and the visible signature is specific: Japanese body
text renders correctly while the brand name, product name, bullets, page
numbers and every unit and numeral change typeface.

### Reference comparison — the deviation is Japanese weight

The operator supplied the shipped book, so the twelve-page comparison has now
been done on the pipeline side and is recorded in
[`../reviews/bp_jp_reference_vs_built_2026-09.md`](../reviews/bp_jp_reference_vs_built_2026-09.md).

Page count and geometry match (12 = 12; 368.754 vs 368.787 pt is mm-to-point
rounding), and content is complete — 6,879 reference characters against 6,644
built, with every per-page difference explained. The table of contents is
content-identical, all ten entries and page numbers, its apparent 1,226-character
gap being dot leaders the reference sets literally and the build sets as a
leader tab.

**The real deviation is weight.** The shipped book sets Japanese in four faces —
Regular 2,926 characters, DemiLight 2,004, Medium 1,509, Bold 356, plus
NotoSansCJKjp-Bold 77 — so **57% of Japanese characters are non-Regular**. The
build emits `HB Manual Sans JP (OTF)` for all 255 Japanese runs and every one
resolves to Regular; `Document fonts/` ships exactly one Japanese face. Measured,
zero runs even request Bold or Medium, so this is not a missing-file problem: the
pipeline does not vary Japanese weight at all. Every heading, emphasis, table
header and lead the reference sets in Medium or Bold renders at body weight, which
flattens the hierarchy at every level simultaneously.

That is a pipeline gap rather than a finishing-layer item — closing it needs the
remaining Noto Sans JP weights provisioned under the `HB Manual Sans JP` family
with the paragraph styles selecting them, and cannot be repaired by hand at layout
time without abandoning the shared component styles.

A secondary deviation: in the shipped book Gilroy is an accent used for 43
characters in the whole book and page numbers are Japanese face
(`01` is NotoSansJP-Regular 6.0 pt), while the build leaves 293 runs inheriting
Gilroy.

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

Status: pending Phase 6 completion. The validation ladder and the package
mechanics have been pre-run so that nothing but the visual gate stands between
Phase 6 passing and this phase closing.

Required validation ladder — **all eight green on 2026-09-01**:

```text
python -m ruff check build.py integrations tools tests scripts          # exit 0
python -m unittest                                                      # 3338 tests, OK (skipped=5)
python -m mypy tools/utils                                              # no issues in 14 files
python tools/check_maintainability_guardrails.py                        # OK, 62 hotspot files
python tools/check_doc_link_integrity.py                                # 147 files, 1623 links, 0 broken
python build.py check --config configs/config.bp-jp.yaml --model JBP-2000B --region JP   # exit 0
python build.py check --config configs/config.bp-us.yaml --model JBP-2000B --region US   # exit 0
python build.py check --config configs/config.ja.yaml --model JE-1000F --region JP       # exit 0
```

The handoff package was also built ahead of the gate, from
`build.py idml --idml-mode both` output: 7,373,480 bytes, 50 entries, 31 linked
assets collected with none missing, four OFL font files bundled, and all seven
reports present including the `source_trace.json` / `designer_checklist.md` /
`missing_assets_report.md` trio. It is a dry run, not the deliverable: the real
package must be built from a clean worktree and must carry the native PDF and
visual evidence that Phase 6 has not yet produced.

One packaging fact is worth stating before the clean-room reopen, because it
will otherwise look like a package defect: the ZIP intentionally does **not**
contain `Gilroy`, so a clean-room host without it licensed and installed will
substitute on open. See the font finding in Phase 6.

Package from a clean worktree/clone, verify the ZIP contains the IDML package,
native PDF, font/asset links allowed by policy, manifest, checksums, and visual
evidence, then open a PR into `auto-manual/main`. MA-023 may merge the R3c PR
only after every check is green, no review requests changes, no thread remains
unresolved, and all source/legal/asset approvals used by the result are proven.
After merge, refresh PR #974 from `main` and backfill R3c evidence; #974 remains
Draft for later checklist phases.
