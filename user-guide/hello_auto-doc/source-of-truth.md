# Workflow guide: source-of-truth layers and what to edit

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

## 2. Source of Truth

The manual system now has four layers, but they are used at different stages.

1. Template seed layer
   - [`docs/templates/page_us-en/*.rst`](../../docs/templates/page_us-en)
   - [`docs/templates/page_jp/*.rst`](../../docs/templates/page_jp)
   - [`docs/manifests/*.yaml`](../../docs/manifests)
   - Responsibility: reusable page structure, headings, shared prose, and initial draft layout
   - Some templates intentionally duplicate prose across normal RST and renderer-specific branches such as `.. raw:: html` or `.. raw:: latex`; when changing wording, treat the RST list as the source wording and keep renderer-specific copies aligned
   - Template-maintenance Feishu cloud docs can be compared with `python -m tools.backport.cloud_doc diff --template ...` and then planned with `python -m tools.backport.cloud_doc apply-template --report ...`; the apply step is dry-run by default and only writes guarded template prose replacements when `--write` is supplied. It does not write Feishu source tables or review bundles.

 - `tools/manifest_lint.py --json` provides a report-only page-manifest inventory check. It reports orphan manifests, invalid/missing sources, and language-set drift between each config and its manifest; it does not alter build or approval gates.
 - `tools/manifest_family.py` provides the non-mutating family-manifest pilot. Its `diff` command writes a deterministic JSON-Pointer carrier and its `roundtrip` command applies that carrier in memory and checks canonical manifest bytes; it does not rewrite source manifests or change build assembly.
 - `tools/manifest_family.py fold --index docs/manifests/family/index.yaml` validates the full fold inventory: 2 anchor manifests plus 15 carriers cover all 17 current manifest files. `--write` refreshes only the JSON carriers and remains explicit.
 - The `Manifest Regenerate and Diff Guardrail` workflow runs the fold check for manifest/config changes, so a manually edited generated YAML fails CI when its carrier no longer rebuilds the same canonical bytes.

3. Review working layer
   - [`docs/_review/<model>/<region>/index.rst`](../../docs/_review)
   - [`docs/_review/<model>/<region>/page/*.rst`](../../docs/_review)
   - [`docs/_review/<model>/<region>/generated/<model>/*.rst`](../../docs/_review)
   - [`docs/_review/<model>/<region>/manifest.json`](../../docs/_review)
   - [`docs/_review/<model>/<region>/overrides/**`](../../docs/_review)
   - Responsibility: target-specific review editing, Git review, revision history, final release source after review starts
   - Accepted Feishu cloud-doc revisions back-port through `python -m tools.backport.cloud_doc run-review-branch --doc-name <doc name> --cloud-doc <url>` (equivalently `python -m tools.backport.cloud_doc …`; the code lives in `tools/backport/`) — the blessed path: it resolves the review branch, diffs the cloud-doc against a **render baseline** (so deltas are the reviewer's real edits, not RST-source noise), and with `--write --push` applies only Class R prose and opens a draft PR into the review branch. The older `run-review --doc-url ... --source-path docs/_review/...` diffs against the RST source and is now **guarded**: a `--write` against an `.rst` baseline is refused and steered to `run-review-branch` unless `--allow-rst-baseline` is set. The runners write diff/apply/run reports and are dry-run by default. Add `--write` only after reviewing the apply report; write mode patches guarded review prose, runs residual verification, and marks the run `PR_READY` only when the review source changed and verification passed. Data-like deltas stay report-only and also get `cloud_doc_backport_source_table_suggestions.md` with candidate source tables and operator steps. Use `python -m tools.backport.cloud_doc open-pr --manifest reports/cloud_doc_backport/<run-id>/cloud_doc_backport_run.json` only after `PR_READY`; it commits the changed `_review` source to a draft PR and leaves local reports out of the commit.
   - you do not have to remember the backport: the daily [`../.github/workflows/backport-reminder.yml`](../../.github/workflows/backport-reminder.yml) sentinel compares every InReview cloud doc against its committed render baseline and opens/updates a `[backport-reminder]` issue while un-backported edits exist (report-only; running the backport advances the baseline and the issue closes itself)
   - the operator-facing playbook for the whole closed loop (revision ledger commands, TM harvest approval, sentinel handling, annotated PDFs, first-run checklist) is [`./closed_loop_ops_guide.md`](../closed_loop_ops_guide.md)

   - Cloud-doc backport strips Feishu highlight tags before writing reports, keeps image-only/token-only changes out of source-table suggestions, resolves page-value rows to `Page_Placeholders_Source` when the phase2 value index and record sidecar identify the row, and requires human semantic review for output/button terminology swaps. If GitHub rejects automatic PR creation after the branch push, use the printed compare link and PR body to create the draft PR manually.

4. Runtime build layer
   - [`docs/_build/<model>/<region>/rst/**`](../../docs/_build)
   - [`docs/_build/<model>/<region>/html/**`](../../docs/_build)
   - [`docs/_build/<model>/<region>/word/**`](../../docs/_build)
   - [`docs/_build/<model>/<region>/pdf/**`](../../docs/_build)
   - [`docs/index.rst`](../../docs/index.rst)
   - Responsibility: generated bundle plus final outputs

Rules:

- Before review starts, use template/data to create the first draft.
- To move one document into review automatically, trigger the review-init flow first; that flow creates the branch, seeds `docs/_review`, and opens the PR.
- After review starts, use [`docs/_review/...`](../../docs/_review/) as the daily editing surface for that target.
- Edit templates only when the change should be shared by multiple manuals.
- For manually maintained parallel-language template pages, keep one source-language template as the structure owner and update the derived-language templates in the same change when shared headings, section order, placeholder sets, includes, or `.. only::` model gates change.
- Current example: if `charging.rst` changes in the source-language family template, keep the same battery-pack `.. only:: model_je_2000e` block boundary in the corresponding derived-language templates instead of updating only one language.
- Edit CSV when product parameters change.
- Treat [`docs/_build/...`](../../docs/_build/) as generated runtime output.
- Keep region-family differences explicit where they are real: spec data, certification text, unit conventions, and `meaning_of_symbols` stay family-specific.
- When design needs to review layout or page effect, share a review handoff workspace built from `_review`, not the raw `.rst`.
- when that workspace is packaged for review sharing, let GitHub Actions build the package first and keep it as an artifact
- Read the Docs renders the frozen Web Publish catalog from `Hello-Docs/main:docs/publish/web/` after the generated publish PR is merged; it does not replace review-preview packaging or formal print release outputs
- designers should start from the workspace root, then pick a family, model, and language before opening the rendered manual or family diff page
- the workspace root now keeps the primary review actions plus a compact document-identity card with product name, manual title, model, region, and language
- the packaged preview now also includes model-scoped `downloads/<family>/<model>/<lang>/review-manual.docx`, `downloads/<family>/<model>/change-report.xlsx`, the raw diff CSV files, and `generated/workspace.json`
- families without `_review` content are hidden, so the preview only shows available families
- the packaged `changes/index.html` now opens a family hub first, and each family hub fans out to model-specific change pages
- if the target branch already has an open pull request, each new push to that PR branch will rerun `Review Preview Package` automatically when the changed files match the workflow paths
- after that workflow finishes, download the uploaded artifact when you need the packaged review workspace; it is no longer pushed to Vercel automatically
- if there is no open pull request yet, trigger `Review Preview Package` manually from the `Actions` tab

## 4. Materialized Bundle Layout

For a target such as `JE-1000F / US`, the working bundle now lives here:

- [`docs/_build/JE-1000F/US/rst/index.rst`](../../docs/_build/JE-1000F/US/rst/index.rst)
- [`docs/_build/JE-1000F/US/rst/page/*.rst`](../../docs/_build/JE-1000F/US/rst/page)
- [`docs/_build/JE-1000F/US/rst/generated/JE-1000F/*.rst`](../../docs/_build/JE-1000F/US/rst/generated/JE-1000F)
- [`docs/_build/JE-1000F/US/rst/conf.py`](../../docs/_build/JE-1000F/US/rst/conf.py)
- [`docs/_build/JE-1000F/US/rst/conf_base.py`](../../docs/_build/JE-1000F/US/rst/conf_base.py)
- [`docs/_build/JE-1000F/US/rst/_static/**`](../../docs/_build/JE-1000F/US/rst/_static)
- [`docs/_build/JE-1000F/US/rst/renderers/**`](../../docs/_build/JE-1000F/US/rst/renderers)
- `docs/_build/JE-1000F/US/rst/asset_usage_manifest.json` — every semantic, review-override, and legacy image consumer plus rewrite provenance
- `docs/_build/JE-1000F/US/rst/asset_registry_snapshot.csv` — the exact registry bytes used for this bundle
- `docs/_build/JE-1000F/US/rst/bundle_manifest.json` — final file records plus `bundle_sha256` over the RST closure, config, support trees, and asset sidecars

This is the generated bundle consumed by Sphinx, HTML export, Word export, and PDF export.
It is not the editing surface. After review starts, `_review/...` is overlaid onto this bundle before publish.

---

## 5. Git Tracking Rule for Review Bundles

The current repo allows two Git-visible surfaces:

- [`docs/_build/**/**/rst/**`](../../docs/_build) is no longer ignored
- [`docs/_review/**`](../../docs/_review) is emitted as a review-first snapshot
- sibling outputs such as [`docs/_build/**/**/html/**`](../../docs/_build), `word/**`, and `pdf/**` remain build artifacts

This gives you two benefits:

1. You can commit generated review bundles per target and keep reviewable history.
2. You can export Git diffs for a single model or region as CSV and HTML reports.

What this does not change:

- `_build/.../rst/**` is still regenerated on the next build.
- `_review/.../**` is now the durable review-editing surface for that target once review starts.
- `python build.py review --refresh-review` is the only path that intentionally replaces the existing review content from template/data.

Recommended use:

1. Seed the target review bundle once with `python build.py review --config ...`
2. Edit [`docs/_review/<model>/<region>/**`](../../docs/_review)
3. Build preview/final outputs with `check/html/word/pdf`
4. Commit the resulting review bundle
5. Use `python build.py diff-report ...` when you need a table-style change export

For the current maintainer branch model, pull request rules, and GitHub protection settings, use [`../code-as-doc/dev/git_branching_guide.md`](../../code-as-doc/dev/git_branching_guide.md).

---

## 5. Which Files You Should Edit

Edit these when the change should be shared across products or when creating the first draft:

- [`docs/templates/page_us-en/*.rst`](../../docs/templates/page_us-en)
- [`docs/templates/page_jp/*.rst`](../../docs/templates/page_jp)

Parallel-language template rule:

- `docs/templates/page_us-en/*.rst` is the current source-language structure owner for manually maintained US prose templates.
- `docs/templates/page_us-es/*.rst` and `docs/templates/page_us-fr/*.rst` are derived-language counterparts and must be updated in the same round when the source-language page changes shared section structure or `.. only::` gating.
- JP currently has only `ja`, so there is no second JP derived-language template to mirror today, but any future JP derived-language page should follow the same rule.
- before adding a new Markdown manual into the template library, fill out [`../code-as-doc/dev/manual_template_intake_checklist.md`](../../code-as-doc/dev/manual_template_intake_checklist.md) so section mapping and placeholder rules are decided before page edits start.

Edit these when safety/spec parameters change:

- [`data/phase2/symbols_blocks.csv`](../../data/phase2/symbols_blocks.csv)
- [`data/phase2/Spec_Master.csv`](../../data/phase2/Spec_Master.csv)
- [`data/phase2/Spec_Footnotes.csv`](../../data/phase2/Spec_Footnotes.csv)
- [`data/phase2/spec_titles.csv`](../../data/phase2/spec_titles.csv)

Edit these when a safety intro page needs copy/layout changes:

- edit [`docs/templates/page_us-en/safety_en.rst`](../../docs/templates/page_us-en/safety_en.rst), [`docs/templates/page_us-fr/safety_fr.rst`](../../docs/templates/page_us-fr/safety_fr.rst), or [`docs/templates/page_us-es/safety_es.rst`](../../docs/templates/page_us-es/safety_es.rst) for US safety intro changes
- edit [`docs/templates/page_jp/safety_ja.rst`](../../docs/templates/page_jp/safety_ja.rst) when the Japanese safety intro page needs copy or layout changes
- edit [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../../docs/templates/page_jp/01_meaning_of_symbols.rst) when the detailed Japanese safety warnings need changes

Edit these during target review and final polish:

- [`docs/_review/<model>/<region>/index.rst`](../../docs/_review)
- [`docs/_review/<model>/<region>/page/*.rst`](../../docs/_review)
- [`docs/_review/<model>/<region>/generated/<model>/*.rst`](../../docs/_review)
- [`docs/_review/<model>/<region>/overrides/_assets/**`](../../docs/_review)
- [`docs/_review/<model>/<region>/overrides/_static/**`](../../docs/_review)
- [`docs/_review/<model>/<region>/overrides/renderers/**`](../../docs/_review)

Do not use these as the primary authoring source:

- [`docs/_build/<model>/<region>/rst/page/*.rst`](../../docs/_build)
- [`docs/_build/<model>/<region>/rst/generated/<model>/*.rst`](../../docs/_build)
- [`docs/_build/<model>/<region>/rst/index.rst`](../../docs/_build)
- [`docs/index.rst`](../../docs/index.rst)

You may commit `_review/...` for review history because it is now the target editing surface after review starts.
