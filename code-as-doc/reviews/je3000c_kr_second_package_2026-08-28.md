# JE-3000C KR second-package build and reuse report

Date: 2026-08-28
Branch: `feat/je3000c-kr-idml-data-assembly`
Baseline: `3cfa01d5f6d76db41359a6eb088a6f601c3a11c1` (GitHub `main`)

## Goal and acceptance evidence

Rebuild the 18-page JE-3000C/KR IDML handoff from current `main` with the
existing component/composition system plus target-owned content, assets,
assembly data, and additive language-capacity tokens.

Completion requires all of the following evidence:

1. the ordinary `build.py idml` entrypoint selects the target plan;
2. production and flow IDML build with `skipped_raw=0`;
3. native InDesign finalization reports zero overset, missing font, and bad-link
   findings;
4. the ZIP is self-contained and every IDML link resolves under `Links/`;
5. all 18 pages are rendered and compared with the supplied production PDF and
   existing JE component appearance;
6. composition-instance reuse, component-code reuse, and wall-clock timing are
   reported from machine-readable evidence.

## Current-state evidence

- GitHub API resolves current `main` to `3cfa01d5`; the local Git transport
  could not refresh `origin/main`, so the build tree was updated from the
  exact #961/#962 patches and compared against a `3cfa01d5` tar snapshot.
- The primary checkout is dirty on `fix/bp-us-local-validation`; it is excluded
  from this work. This clean clone was created specifically for the second
  package.
- `main` already contains 24 shared composition types and five renderer-neutral
  `ComponentSpec` contracts. It also contains the shared JBP component work
  merged by PR #955.
- The first-package branch changes 123 files: 29 target review-data files, four
  target binding/assembly/token files, 15 target assets, but also 37 shared
  implementation files, 32 test/fixture files, two shared templates, and four
  documents. It cannot be reused as a unit.
- The real baseline command

  ```text
  python3 build.py idml --config configs/config.kr.yaml --model JE-3000C \
    --region KR --source review-asis --idml-mode both --no-clean
  ```

  stops after 0.94 s with `Review bundle not found`. Because no target assembly
  is configured, the dispatcher first attempts the historical LaTeX PDF path.

## Migration boundary

Initially copy only these target-owned inputs from the first-package branch:

- `docs/_review/JE-3000C/KR/**`;
- the 15 `je3000c_kr_*`/`cover_je3000c-ko` governed assets;
- `docs/renderers/contracts/target_assembly/je3000c_kr_v1_candidate.json`;
- the JE-3000C overview geometry instance;
- `data/layout_params.idml-je3000c-kr.csv`;
- the `(JE-3000C, KR)` bindings in `configs/config.kr.yaml`.

Do not copy shared renderers, tests, fixture rewrites, shared templates, or the
first-package finalization changes. Build failures after this data-only
migration are the evidence for any genuine shared-contract gap.

## Known contract gap to test, not assume away

The first target plan asks for three combined role signatures that `main` does
not currently register: preface+safety+maintenance, inbox+overview, and a
standalone Symbols composition. It also uses target-data namespaces for assets,
page breaks, overview, operation guidance, app layout, and compact
specifications that the current validator does not all accept.

The preferred correction is a generic target-folio/slot projection that routes
existing public component outputs into target-owned external page slots. It
must not add model, language, title, or page-number branches, and it must not
take ownership of component-internal geometry. If a smaller existing contract
already expresses the same assembly after the data migration, use it instead.

## Phases and safety nets

1. **Data-only migration.** Copy the bounded target inputs, then run the exact
   user-facing IDML command. Safety: changed-path allowlist and target-plan
   normalization.
2. **Generic contract repair, only when proven.** Add the minimum reusable
   composition/variant surface needed by the target. Safety: fail-closed plan
   tests, page-boundary tests, and no-private-helper/model-branch guardrails.
3. **Build and native package.** Time clean IDML build separately from native
   finalization and packaging. Safety: full unit suite, Ruff, maintainability,
   doc links, IDML structural validation, and native preflight.
4. **Visual and reuse audit.** Render all pages, produce comparison evidence,
   and calculate:

   ```text
   composition reuse = existing-main composition instances / all instances
   code reuse = existing-main component/renderer modules / all used modules
   ```

   Any new generic composition code is counted in the denominator and reported
   separately; target data and assets are not misreported as component code.

## Non-goals

- no Feishu/source-table writes;
- no edits or cleanup in the dirty primary checkout;
- no production/approved promotion of the candidate plan;
- no model-specific renderer or one-off config;
- no deletion of old first-package or generated artifacts;
- no commit of `_build`, `output`, `tmp`, PDF, INDD, IDML, or ZIP artifacts.

## Implemented outcome

The ordinary `build.py idml` entrypoint now resolves JE-3000C/KR through the
family config's target map. The target contributes review RST, governed
assets, one target assembly contract, one target layout-token overlay, and one
Overview geometry instance. Shared code gained three target-neutral
composition signatures and reusable validators/rendering variants; it contains
no `JE-3000C`, `KR`, or `ko` branch.

The current v13 structure produces:

- 18/18 matched physical pages;
- Manual IR with 18 pages, 143 blocks, and `skipped_raw=0`;
- production and flow IDML;
- 153 stories and 18 spreads;
- target-correct `USB-C 100W` copy, matching the supplied PDF;
- a cover PDF whose one used Illustrator replacement-character mapping is
  corrected to a space with zero 300 dpi pixel change;
- Hangul runs routed to the latest-main `Noto Sans KR` family while retaining
  the shared InDesign fallback to installed `Arial Unicode MS`.
- a recipe-governed, textless right-side Overview vector extracted from the
  operator-supplied PDF-compatible Illustrator master rather than a screenshot.

Machine-readable results are in
[`je3000c_kr_second_package_metrics_2026-08-28.json`](je3000c_kr_second_package_metrics_2026-08-28.json).

## Component reuse

The denominator for composition reuse is the 13 unique `composition_id`
instances, not the 18 source-page rows (several source pages intentionally
feed one composition).

| Metric | Reused | Total | Reuse |
| --- | ---: | ---: | ---: |
| Composition instances whose type existed on `main` | 10 | 13 | 76.9% |
| Cross-renderer `ComponentSpec` instances using a contract from `main` | 19 | 19 | 100.0% |
| IDML component-registry instances using a renderer from `main` | 16 | 16 | 100.0% |
| Executed IDML implementation modules byte-identical to `main` | 95 | 117 | 81.2% |
| Executed IDML modules with `main` provenance (unchanged + extended) | 115 | 117 | 98.3% |

The three new generic composition types are
`preface_safety_maintenance`, `symbols`, and `inbox_overview`. The ten reused
types are `front_cover`, `lcd`, `operation`, `ups_charging`,
`charging_methods`, `storage_troubleshooting`, `specifications`, `warranty`,
`app`, and `back_cover`.

The 19 formal cross-renderer `ComponentSpec` projections are 13
`HB-CALLOUT-STRIP`, four `HB-TABLE-SPEC`, one `HB-SPECIAL-INBOX`, and one
`HB-SPECIAL-OVERVIEW`; all four contract IDs already exist on `main`. Separately,
the 16 Manual-IR component blocks dispatched by the IDML-only registry are 13
`notice` blocks plus one each of `safetywarning`, `inbox`, and `lcdmode`; all four
renderer kinds also already exist on `main`. This distinction avoids calling
the IDML-only `safetywarning` and `lcdmode` renderers formal `ComponentSpec`
contracts. No JE-3000C-specific component contract or renderer was added. The
only two wholly new executed IDML modules are target-neutral helpers for real
asset aspect ratios and governed Overview asset-role resolution; 20 existing
modules were extended additively. The exact module list and trace command are
recorded in the metrics JSON.

## Time evidence

All wall-clock timestamps below use `America/Los_Angeles`. They do not claim
continuous active engineering effort.

| Milestone | Time |
| --- | ---: |
| Baseline command on untouched `main` failed as expected | 0.94 s |
| Clone created → first 18-page structural IDML (`skipped_raw=2`) | 32m 41s |
| Target data created → first structural IDML | 27m 28s |
| Clone created → first gate-clean IDML (`skipped_raw=0`) | 36m 07s |
| Target data created → first gate-clean IDML | 30m 54s |

For the v11 source, five consecutive user-facing builds took
`1.90, 2.07, 1.73, 1.75, 1.74` seconds: median `1.75 s`, mean `1.838 s`.
Every run met 18/18 pages, 143 blocks, `skipped_raw=0`, 153 stories, and 18
spreads. The v12 semantic-regression build took `2.08 s`; the v13 build with
the approved Illustrator-derived Overview asset took `2.31 s` and met the
same structural gates.

The first successful current-source native finalization was v12 at `59.12 s`.
The v13 finalization also passed with 18 pages, 153 stories, zero overset,
missing fonts, missing glyphs, and bad links. Both used the pinned InDesign
`21.0.1.6` host and the PDF/X-4 / Japan Color 2001 Coated / JC200103 print
contract. `Noto Sans KR` is not installed on this host, so the shared finalizer
recorded a deterministic `Arial Unicode MS` substitution; the final PDF glyph
gate still reports zero findings.

## Illustrator-derived Overview asset

The supplied
`16-0102-000382 说明书 HTE1563000A-EU UK-JAK RoHS REACH.ai` is a
19-page PDF-compatible Illustrator master with SHA-256
`c7a43b6e77003c3e5e4bd772ea7a8df7c0938c9992b494b045e54970e0c00557`.
Page 5 contains 426 vector drawing groups and no embedded raster image. The
approved recipe keeps groups `372-391` (complete chassis and port structure),
excludes group `371` and `392-395` (external leaders), and excludes groups
`396-425` (outlined English labels). The formal pipeline output is entirely
vector, has no extractable text, and has SHA-256
`ad9c45dd8b7fc3de49f849fbcbac89e9d3ba4be0e4a2ca896fb7cddd05645936`.
At 12x it matches the operator-confirmed KR-derived candidate in fill, stroke,
line width, and all 20 corresponding drawing groups; maximum geometry delta is
`0.003 pt`.

## Delivery package

Generated delivery artifacts remain outside Git:

- `JE-3000C_KR_second-package_v13.idml`, SHA-256
  `f2e5ac73e8d4ecf10884086605a226d103a7c2dd84a4dbe8d5ac0fc469f9fdf2`;
- `JE-3000C_KR_second-package_v13_handoff.zip`, SHA-256
  `23f6ea9f5c2c351a4437261c37d1b5edcd0e810168849da2c6f877af324c31e4`;
- finalized INDD, SHA-256
  `b04b311db5f611ff31206d6bd77adef200bf84ecf2200efdec3d1c7314a4c06a`;
- finalized PDF/X-4, SHA-256
  `1ca9ca83c921503e573f7112788135491e057802c12874c3e682fba7a4c7667d`.

The ZIP has 118 entries: production and flow IDML, 103 assets under `Links/`,
the reference PDF, flow/source reports, checklist, and fonts manifest. All 109
link URI occurrences resolve to the 103 packaged assets; zero remain absolute
or unresolved. Font binaries are intentionally not redistributed.

## Validation status

Completed on the current source:

- five consecutive accepted latest-main-equivalent `build.py idml` runs;
- `python3 tools/export_idml.py --check ...`;
- 18/18 target-assembly and `skipped_raw=0` gates;
- target-copy gate: `USB-C 100W` present, 140W branch absent;
- self-contained ZIP link audit: 0 nonportable, 0 unresolved;
- cover `qpdf --check`, text extraction, and 300 dpi pixel-parity check;
- full `python3 -m unittest -q`, Ruff, maintainability guardrails, and doc-link
  validation;
- shared list-table indentation parsing with a KR multi-bullet notice
  regression, without changing the target RST;
- exported-PDF missing-glyph gate for visible `U+FFFD` and `.notdef` glyphs;
  the old native-v7 negative control reports nine findings across placed and
  native text, while v13 reports zero;
- all 18 v13 PDF pages rendered with Poppler and visually compared against the
  supplied KR production PDF; focused checks passed for Symbols p3, Overview
  p4, Operation p7-p8, and Specifications p14;
- v13 native preflight and PDF/X-4/XMP/OutputIntent validation passed.

The mandatory generic US `build.py check` reaches config and layout validation
but is environment-blocked because this isolated worktree has no
`data/phase2/Spec_Master.csv`; target identity therefore cannot resolve
`JE-1000F_US`. The same command with `--data-root tests/fixtures/phase2`
passes, separating the missing local live-data snapshot from code behavior.
This is recorded separately from the accepted KR target build.

Residual handoff note: install `Noto Sans KR` before editing if exact intended
Korean typography is required. The delivered PDF is accepted with the recorded
`Arial Unicode MS` fallback and zero missing-glyph findings.
