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

The current v11 structure produces:

- 18/18 matched physical pages;
- Manual IR with 18 pages, 143 blocks, and `skipped_raw=0`;
- production and flow IDML;
- 153 stories and 18 spreads;
- target-correct `USB-C 100W` copy, matching the supplied PDF;
- a cover PDF whose one used Illustrator replacement-character mapping is
  corrected to a space with zero 300 dpi pixel change;
- Hangul runs routed to the latest-main `Noto Sans KR` family while retaining
  the shared InDesign fallback to installed `Arial Unicode MS`.

Machine-readable results are in
[`je3000c_kr_second_package_metrics_2026-08-28.json`](je3000c_kr_second_package_metrics_2026-08-28.json).

## Component reuse

The denominator for composition reuse is the 13 unique `composition_id`
instances, not the 18 source-page rows (several source pages intentionally
feed one composition).

| Metric | Reused | Total | Reuse |
| --- | ---: | ---: | ---: |
| Composition instances whose type existed on `main` | 10 | 13 | 76.9% |
| Manual-IR semantic component instances using an existing contract | 16 | 16 | 100.0% |
| Executed IDML implementation modules byte-identical to `main` | 95 | 117 | 81.2% |
| Executed IDML modules with `main` provenance (unchanged + extended) | 115 | 117 | 98.3% |

The three new generic composition types are
`preface_safety_maintenance`, `symbols`, and `inbox_overview`. The ten reused
types are `front_cover`, `lcd`, `operation`, `ups_charging`,
`charging_methods`, `storage_troubleshooting`, `specifications`, `warranty`,
`app`, and `back_cover`.

The 16 semantic component instances are 13 `notice` blocks plus one each of
`safetywarning`, `inbox`, and `lcdmode`. No JE-3000C-specific ComponentSpec was
added. The only two wholly new executed IDML modules are target-neutral helpers
for real asset aspect ratios and governed Overview asset-role resolution;
20 existing modules were extended additively. The exact module list and trace
command are recorded in the metrics JSON.

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

For the current v11 source, five consecutive user-facing builds took
`1.90, 2.07, 1.73, 1.75, 1.74` seconds: median `1.75 s`, mean `1.838 s`.
Every run met 18/18 pages, 143 blocks, `skipped_raw=0`, 153 stories, and 18
spreads.

Earlier native-finalizer observations were 32-34 seconds from a cold InDesign
start and 5-6 seconds when warm, but those runs stopped at PDF export and have
`success=false`; they are not reported as successful finalization time. Their
native-v7 PDF is also older than the current v11 IDML. The operator's latest
screenshot confirms that the exported warning still came from that old v7
document, not v11. A current-source PDF/X-4 timing remains pending the v11
export.

## Delivery package

Generated artifacts remain outside Git:

- `JE-3000C_KR_second-package_v11.idml`, SHA-256
  `4c4fc8d740c95de72d0e42a7abe9bbd4a90b398aa644e800f96987a9f3a7d53f`;
- `JE-3000C_KR_second-package_v11_handoff.zip`, SHA-256
  `0c71569f74e0d92508a82933a300296513fb97b0d6481862e5f123387a49f68d`.

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
  native text.

The mandatory generic US `build.py check` reaches config and layout validation
but is environment-blocked because this isolated worktree has no
`data/phase2/Spec_Master.csv`; target identity therefore cannot resolve
`JE-1000F_US`. This is recorded separately from the accepted KR target build.

Still required before calling the package final:

- install `Noto Sans KR` for exact intended typography, or record the shared
  finalizer's explicit fallback to the installed `Arial Unicode MS`;
- operator export of v11 through InDesign;
- verify no PDF/X-4 missing-glyph warning;
- PDF/X-4/XMP/OutputIntent inspection;
- current-source native overset/font/link preflight;
- render and compare all 18 pages, with focused review of pages 3, 4, 8, 14,
  and 18.
